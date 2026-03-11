import os
import torch
import threading
from transformers import AutoTokenizer, AutoModelForCausalLM
from config.constants import MODEL_PATH, MAX_CONTEXT_CHARS, MAX_NEW_TOKENS

class ModelService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.tokenizer = None
            self.model = None
            self.generate_lock = threading.Lock()
            self.chat_history = {}
            self.initialized = True
            self._load_model()
    
    def _load_model(self):
        print("🚀 加载 Qwen1.5-1.8B-Chat 模型")
        
        try:
            print("🔍 CUDA 可用性检测")
            use_cuda = torch.cuda.is_available()

            if use_cuda:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
                print(f"✅ GPU: {gpu_name} | 显存: {gpu_mem:.2f} GB")
            else:
                print("⚠️ CUDA 不可用，将使用 CPU（极慢，不推荐）")

            print("📦 加载 tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                MODEL_PATH,
                trust_remote_code=True
            )

            print("🧠 加载模型...")
            
            if use_cuda:
                print("使用 GPU 模式（半精度 float16）...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    MODEL_PATH,
                    dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            else:
                print("使用 CPU 模式（无量化）...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    MODEL_PATH,
                    dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )

            self.model.eval()
            self.model.config.use_cache = True

            print("✅ 模型加载完成")
            print(f"📍 模型设备: {next(self.model.parameters()).device}")
            if use_cuda:
                print(f"💾 显存占用: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

        except Exception as e:
            import traceback
            print("❌ 模型加载失败")
            traceback.print_exc()
            self.model = None
            self.tokenizer = None
    
    def generate_response(self, prompt, user_id):
        if self.model is None or self.tokenizer is None:
            return "模型未正确加载，请检查服务器日志。"

        with self.generate_lock:
            try:
                # 1. 维护结构化的对话历史 (List of Dict)
                if user_id not in self.chat_history or not isinstance(self.chat_history[user_id], list):
                    self.chat_history[user_id] = []
                
                messages = self.chat_history[user_id]
                messages.append({"role": "user", "content": prompt})

                # 2. 使用官方模板构建输入字符串 (Qwen 必须包含 <|im_start|> 等标记)
                # tokenize=False 返回处理好的字符串，add_generation_prompt 引导模型开始回答
                input_text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )

                # 3. 编码并移动到设备
                inputs = self.tokenizer([input_text], return_tensors="pt").to(self.model.device)

                # 4. 执行生成
                with torch.inference_mode():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=MAX_NEW_TOKENS,
                        repetition_penalty=1.1,
                        temperature=0.6,
                        top_p=0.85,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                # 5. 精准提取回复部分（跳过输入 tokens 的长度）
                input_ids_len = inputs.input_ids.shape[1]
                response_ids = outputs[0][input_ids_len:]
                response = self.tokenizer.decode(response_ids, skip_special_tokens=True).strip()

                # 6. 更新历史（限制对话轮数，防止 Token 爆炸）
                if response:
                    messages.append({"role": "assistant", "content": response})
                    # 仅保留最近 5 轮完整对话（10 条记录）
                    if len(messages) > 10:
                        self.chat_history[user_id] = messages[-10:]
                
                return response or "（模型未生成有效内容）"

            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    torch.cuda.empty_cache()
                    return "显存不足，请重试或清空历史。"
                return f"推理错误: {str(e)}"
    
    def is_busy(self):
        return self.generate_lock.locked()
    
    def clear_chat_history(self, user_id):
        self.chat_history.pop(user_id, None)

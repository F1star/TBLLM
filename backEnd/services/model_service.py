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
                history = self.chat_history.get(user_id, "")
                full_prompt = (history + prompt)[-MAX_CONTEXT_CHARS:]

                inputs = self.tokenizer(
                    full_prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                ).to(self.model.device)

                with torch.inference_mode():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=MAX_NEW_TOKENS,
                        temperature=0.6,
                        top_p=0.85,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id
                    )

                decoded = self.tokenizer.decode(
                    outputs[0],
                    skip_special_tokens=True
                )

                response = decoded[len(full_prompt):].strip()

                self.chat_history[user_id] = (
                    full_prompt + response
                )[-MAX_CONTEXT_CHARS:]

                return response or "（模型未生成有效内容）"

            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    torch.cuda.empty_cache()
                    return "显存不足，请稍后重试或清空对话。"
                return f"推理错误: {str(e)}"
    
    def is_busy(self):
        return self.generate_lock.locked()
    
    def clear_chat_history(self, user_id):
        self.chat_history.pop(user_id, None)

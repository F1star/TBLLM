import threading
import logging
from datetime import datetime

# 尝试导入torch，如果失败则设置为None
try:
    import torch
    TORCH_AVAILABLE = True
except Exception as e:
    print(f"[Warning] 无法导入torch: {e}")
    torch = None
    TORCH_AVAILABLE = False

# 尝试导入transformers，如果失败则设置为None
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"[Warning] 无法导入transformers: {e}")
    AutoModelForCausalLM = None
    AutoTokenizer = None
    TRANSFORMERS_AVAILABLE = False

from config.constants import (
    MAX_CONTEXT_CHARS, MAX_NEW_TOKENS, ORIGINAL_MODEL_PATH, FINETUNED_MODEL_PATH,
    USE_ADVANCED_AGENT, AGENT_MAX_ITERATIONS, AGENT_VERBOSE
)
from services.agent_service import AgentService
from services.chat_service import ChatService

# 尝试导入AdvancedAgent，如果失败则使用原版
try:
    from services.advanced_agent import AdvancedAgent, AdvancedAgentFactory, CompatibleAgentService
    from services.agent_tools_enhanced import EnhancedToolFactory
    ADVANCED_AGENT_AVAILABLE = True
except ImportError as e:
    ADVANCED_AGENT_AVAILABLE = False
    logging.warning(f"AdvancedAgent不可用，将使用原版AgentService: {e}")

# 设置日志
logger = logging.getLogger(__name__)


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
        if not hasattr(self, "initialized"):
            self.tokenizer = None
            self.model = None
            self.agent_service = None
            self.generate_lock = threading.Lock()
            self.initialized = True
            self._load_model()

    def _load_model(self):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 加载本地模型从: {ORIGINAL_MODEL_PATH}")

        # 检查必要的库是否可用
        if not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] torch或transformers不可用，跳过模型加载")
            self.model = None
            self.tokenizer = None
            return

        try:
            # 先尝试使用CPU加载，避免内存不足问题
            use_cuda = torch.cuda.is_available()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CUDA 可用: {use_cuda}")

            # 优先使用CPU以避免内存问题
            force_cpu = False  # 不强制使用CPU，尝试使用CUDA
            if use_cuda and not force_cpu:
                device = "cuda"
                dtype = torch.float16
                device_map = "auto"
            else:
                device = "cpu"
                dtype = torch.float32
                device_map = "cpu"

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 使用设备: {device}, 精度: {dtype}")

            from peft import PeftModel

            # 1️⃣ 加载 tokenizer（始终用 base model 的）
            self.tokenizer = AutoTokenizer.from_pretrained(
                ORIGINAL_MODEL_PATH,
                trust_remote_code=True,
            )

            # 2️⃣ 加载 base model
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 加载基础模型...")

            base_model = AutoModelForCausalLM.from_pretrained(
                ORIGINAL_MODEL_PATH,
                dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

            # 3️⃣ 如果有 LoRA，就加载
            if FINETUNED_MODEL_PATH:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 加载LoRA权重: {FINETUNED_MODEL_PATH}")
                self.model = PeftModel.from_pretrained(base_model, FINETUNED_MODEL_PATH)
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未使用LoRA，直接使用基础模型")
                self.model = base_model

            # 4️⃣ 设置推理模式
            self.model.eval()
            self.model.config.use_cache = True

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型加载完成")        

            # 根据配置选择Agent服务
            if USE_ADVANCED_AGENT and ADVANCED_AGENT_AVAILABLE:
                try:
                    self.agent_service = self._create_advanced_agent()
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已启用AdvancedAgent服务")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AdvancedAgent创建失败，回退到原版AgentService: {str(e)}")
                    self.agent_service = AgentService(
                        tokenizer=self.tokenizer,
                        model=self.model,
                        max_new_tokens=MAX_NEW_TOKENS,
                    )
            else:
                self.agent_service = AgentService(
                    tokenizer=self.tokenizer,
                    model=self.model,
                    max_new_tokens=MAX_NEW_TOKENS,
                )
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 使用原版AgentService")
        except Exception:
            import traceback
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型加载失败!")
            traceback.print_exc()
            self.model = None
            self.tokenizer = None
            self.agent_service = None

    def _create_advanced_agent(self):
        """
        创建单AdvancedAgent实例，包含所有工具。
        通过工具 setter 控制每次调用实际可用的工具（未设置 ID 的工具返回空数据）
        """
        from services.local_llm import LocalChatLLM

        llm = LocalChatLLM(
            tokenizer=self.tokenizer,
            model=self.model,
            max_new_tokens=MAX_NEW_TOKENS
        )

        # 创建工具实例（后续通过 setter 注入 user_id / session_id）
        from services.agent_tools_enhanced import FileSummaryTool, SessionHistoryTool, AllSessionsHistoryTool
        self._file_summary_tool = FileSummaryTool()
        self._session_history_tool = SessionHistoryTool()
        self._all_history_tool = AllSessionsHistoryTool()

        # 单Agent，包含所有工具
        tools = [
            self._file_summary_tool,
            self._session_history_tool,
            self._all_history_tool,
        ]

        advanced_agent = AdvancedAgent(
            llm=llm,
            tools=tools,
            max_iterations=AGENT_MAX_ITERATIONS,
            verbose=AGENT_VERBOSE
        )

        return CompatibleAgentService(advanced_agent)

    def generate_response(self, prompt, user_id, session_id=None):
        if self.model is None or self.tokenizer is None or self.agent_service is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型未加载，无法生成响应")
            return "模型未正确加载，请检查后端日志。"

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 生成聊天响应 - 用户ID: {user_id}, 会话ID: {session_id}, 提示: {prompt[:50]}...")
        with self.generate_lock:
            try:
                # 对话场景：仅设置当前会话历史工具，其他工具无 context 返回空数据
                if hasattr(self, '_session_history_tool'):
                    self._session_history_tool.set_user_id(int(user_id))
                    self._session_history_tool.set_session_id(session_id)

                history = ChatService.get_recent_chats(int(user_id), limit=10, session_id=session_id)
                history_text = self._format_history(history, current_prompt=prompt)
                response = self.agent_service.chat(
                    message=prompt,
                    chat_history=history_text,
                )
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 聊天响应生成完成，长度: {len(response)} 字符")
                return response or "模型未生成有效内容。"
            except RuntimeError as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 推理运行时错误: {str(e)}")
                if "out of memory" in str(e).lower():
                    torch.cuda.empty_cache()
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已清理CUDA缓存")
                    return "显存不足，请重试或减少上下文。"
                return f"推理错误: {str(e)}"
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent 推理异常: {str(e)}")
                return f"Agent 推理错误: {str(e)}"

    def generate_chat_stream(self, prompt, user_id, session_id=None):
        """
        流式生成聊天响应，绕过 Agent ReAct 循环直接使用 LLM 生成。
        Yields:
            str: 每次 yield 一个 token 片段
        """
        if self.model is None or self.tokenizer is None:
            yield "模型未正确加载，请检查后端日志。"
            return

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] generate_chat_stream - 用户ID: {user_id}, 会话ID: {session_id}, 提示: {prompt[:50]}...")
        with self.generate_lock:
            try:
                # 获取历史对话
                history = ChatService.get_recent_chats(int(user_id), limit=10, session_id=session_id)
                history_text = self._format_history(history, current_prompt=prompt)
                if not history_text:
                    history_text = "暂无历史对话。"

                # 构建简洁的对话 prompt（使用 AgentService 验证过的格式）
                if history_text and history_text != "暂无历史对话。":
                    chat_prompt = f"""你是一个友好的AI助手，名叫智评小助手。请简洁地直接回答用户的问题。

历史对话：
{history_text}

用户：{prompt}
助手："""
                else:
                    chat_prompt = f"""你是一个友好的AI助手，名叫智评小助手。请简洁地直接回答用户的问题。

用户：{prompt}
助手："""

                # 不使用 apply_chat_template，直接传入纯文本 prompt
                inputs = self.tokenizer([chat_prompt], return_tensors="pt").to(self.model.device)

                from transformers import TextIteratorStreamer
                streamer = TextIteratorStreamer(
                    self.tokenizer, skip_prompt=True, skip_special_tokens=True
                )

                generation_kwargs = dict(
                    input_ids=inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    streamer=streamer,
                    max_new_tokens=MAX_NEW_TOKENS,
                    do_sample=True,
                    temperature=0.3,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

                import threading
                thread = threading.Thread(
                    target=self.model.generate,
                    kwargs=generation_kwargs,
                )
                thread.start()

                full_response = ""
                for token in streamer:
                    full_response += token
                    yield token

                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] generate_chat_stream - 流式生成完成，总长度: {len(full_response)}")

            except RuntimeError as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 流式推理运行时错误: {str(e)}")
                if "out of memory" in str(e).lower():
                    torch.cuda.empty_cache()
                yield f"\n[生成错误: 显存不足，请重试]"
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 流式推理异常: {str(e)}")
                yield f"\n[生成错误: {str(e)}]"

    def generate_evaluation(self, chat_history_text, file_context_text, user_id=None, deep_mode=False):
        if self.model is None or self.tokenizer is None or self.agent_service is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型未加载，无法生成评估")
            raise ValueError("模型未正确加载，请检查后端日志。")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 生成能力评估 - 聊天历史长度: {len(chat_history_text)}, 文件上下文长度: {len(file_context_text)}, 用户ID: {user_id}, 深度思考: {deep_mode}")
        with self.generate_lock:
            try:
                # 评估场景：仅设置全部会话历史工具和文件总结工具
                if user_id is not None:
                    if hasattr(self, '_all_history_tool'):
                        self._all_history_tool.set_user_id(int(user_id))
                    if hasattr(self, '_file_summary_tool'):
                        self._file_summary_tool.set_user_id(int(user_id))

                result = self.agent_service.evaluate(
                    chat_history=chat_history_text,
                    file_context=file_context_text,
                    deep_mode=deep_mode,
                )
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 评估完成 - 逻辑: {result.get('logic_score')}, 创造力: {result.get('creativity_score')}, 表达: {result.get('expression_score')}, 知识: {result.get('knowledge_score')}")
                return result
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 评估过程异常: {str(e)}")
                raise

    def generate_professional_assessment(self, assessment_text, cohort):
        """生成专业测评评估"""
        if self.model is None or self.tokenizer is None or self.agent_service is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型未加载，无法生成专业测评评估")
            raise ValueError("模型未正确加载，请检查后端日志。")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 生成专业测评评估 - 评估文本长度: {len(assessment_text)}, 组别: {cohort}")
        with self.generate_lock:
            try:
                result = self.agent_service.professional_assess(
                    assessment_text=assessment_text,
                    cohort=cohort,
                )
                skill_scores = result.get('skill_scores', {})
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 专业测评完成 - 技能数: {len(skill_scores)}, 综合: {result.get('overall_score')}")
                return result
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 专业测评过程异常: {str(e)}")
                raise


    def is_busy(self):
        return self.generate_lock.locked()

    def clear_chat_history(self, user_id):
        return None

    def _format_history(self, chats, current_prompt=None):
        if not chats:
            return "暂无历史对话。"

        filtered_chats = list(chats)
        if (
            current_prompt
            and filtered_chats
            and filtered_chats[0].role == "user"
            and filtered_chats[0].content == current_prompt
        ):
            filtered_chats = filtered_chats[1:]

        if not filtered_chats:
            return "暂无历史对话。"

        ordered_chats = list(reversed(filtered_chats))
        return "\n".join(
            f"{chat.role}: {chat.content[:MAX_CONTEXT_CHARS]}" for chat in ordered_chats
        )

    def optimize_question_text(self, question_text):
        """
        优化问题描述

        参数:
            question_text: 原始问题文本

        返回:
            optimized_text: 优化后的问题文本
        """
        # 如果模型不可用，返回模拟优化文本
        if self.model is None or self.tokenizer is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型不可用，返回模拟优化文本")
            return f"[模拟优化] {question_text} (此优化文本为模拟数据，实际使用时需要加载模型)"

        try:
            prompt = f"""请优化以下问卷问题的描述，使其更加清晰、易懂，适合中学生理解：

原始问题: {question_text}

优化要求:
1. 保持问题的原意不变
2. 使语言更加简洁明了
3. 适合中学生的理解水平
4. 如果问题中有专业术语，用更通俗的语言解释
5. 优化后的长度不应显著增加

请只返回优化后的问题文本，不要添加其他内容。"""

            with self.generate_lock:
                inputs = self.tokenizer(prompt, return_tensors="pt")
                if self.model.device.type == "cuda":
                    inputs = inputs.to("cuda")

                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=MAX_NEW_TOKENS,
                        do_sample=True,
                        temperature=0.7,
                        pad_token_id=self.tokenizer.eos_token_id,
                    )

                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

                # 提取优化后的问题文本
                # 移除prompt部分，只保留生成的文本
                if prompt in response:
                    optimized_text = response.replace(prompt, "").strip()
                else:
                    # 如果prompt不在response中，尝试找到问题部分
                    lines = response.split('\n')
                    for i, line in enumerate(lines):
                        if "优化后的问题" in line or "优化版本" in line:
                            if i + 1 < len(lines):
                                optimized_text = lines[i + 1].strip()
                                break
                    else:
                        # 如果找不到，使用最后一行
                        optimized_text = lines[-1].strip() if lines else question_text

                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 问题优化完成: {question_text[:50]}... -> {optimized_text[:50]}...")
                return optimized_text

        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 优化问题时出错: {e}")
            # 如果优化失败，返回原始文本
            return question_text

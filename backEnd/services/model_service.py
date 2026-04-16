import threading
import logging
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config.constants import (
    MAX_CONTEXT_CHARS, MAX_NEW_TOKENS, MODEL_PATH,
    USE_ADVANCED_AGENT, AGENT_MAX_ITERATIONS, AGENT_VERBOSE
)
from services.agent_service import AgentService
from services.chat_service import ChatService

# 尝试导入AdvancedAgent，如果失败则使用原版
try:
    from services.advanced_agent import AdvancedAgent, AdvancedAgentFactory, CompatibleAgentService
    from services.agent_tools_enhanced import EnhancedToolFactory
    from services.rag_service import RAGService
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
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 加载本地模型从: {MODEL_PATH}")

        try:
            use_cuda = torch.cuda.is_available()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CUDA 可用: {use_cuda}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                MODEL_PATH,
                trust_remote_code=True,
            )

            model_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
            }
            if use_cuda:
                model_kwargs.update({"torch_dtype": torch.float16, "device_map": "auto"})
            else:
                model_kwargs.update({"torch_dtype": torch.float32, "device_map": "cpu"})

            self.model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, **model_kwargs)
            self.model.eval()
            self.model.config.use_cache = True
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型加载成功，设备: {self.model.device}")

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
        创建AdvancedAgent实例

        Returns:
            AdvancedAgent兼容包装器
        """
        from services.local_llm import LocalChatLLM
        from services.rag_service import RAGService

        # 创建LocalChatLLM实例
        llm = LocalChatLLM(
            tokenizer=self.tokenizer,
            model=self.model,
            max_new_tokens=MAX_NEW_TOKENS
        )

        # 创建基础工具集（这里暂时不传入用户ID，实际使用时需要根据用户动态创建）
        tools = EnhancedToolFactory.create_basic_tools()

        # 创建AdvancedAgent
        advanced_agent = AdvancedAgent(
            llm=llm,
            tools=tools,
            max_iterations=AGENT_MAX_ITERATIONS,
            verbose=AGENT_VERBOSE
        )

        # 使用兼容性包装器
        return CompatibleAgentService(advanced_agent)

    def generate_response(self, prompt, user_id, session_id=None):
        if self.model is None or self.tokenizer is None or self.agent_service is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型未加载，无法生成响应")
            return "模型未正确加载，请检查后端日志。"

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 生成聊天响应 - 用户ID: {user_id}, 会话ID: {session_id}, 提示: {prompt[:50]}...")
        with self.generate_lock:
            try:
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

    def generate_evaluation(self, chat_history_text, file_context_text):
        if self.model is None or self.tokenizer is None or self.agent_service is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型未加载，无法生成评估")
            raise ValueError("模型未正确加载，请检查后端日志。")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 生成能力评估 - 聊天历史长度: {len(chat_history_text)}, 文件上下文长度: {len(file_context_text)}")
        with self.generate_lock:
            try:
                result = self.agent_service.evaluate(
                    chat_history=chat_history_text,
                    file_context=file_context_text,
                )
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 评估完成 - 逻辑: {result.get('logic_score')}, 创造力: {result.get('creativity_score')}, 表达: {result.get('expression_score')}, 知识: {result.get('knowledge_score')}")
                return result
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 评估过程异常: {str(e)}")
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

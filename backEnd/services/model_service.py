import threading

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config.constants import MAX_CONTEXT_CHARS, MAX_NEW_TOKENS, MODEL_PATH
from services.agent_service import AgentService
from services.chat_service import ChatService


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
        print("Loading local model from:", MODEL_PATH)

        try:
            use_cuda = torch.cuda.is_available()
            self.tokenizer = AutoTokenizer.from_pretrained(
                MODEL_PATH,
                trust_remote_code=True,
            )

            model_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
            }
            if use_cuda:
                model_kwargs.update({"dtype": torch.float16, "device_map": "auto"})
            else:
                model_kwargs.update({"dtype": torch.float32, "device_map": "cpu"})

            self.model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, **model_kwargs)
            self.model.eval()
            self.model.config.use_cache = True
            self.agent_service = AgentService(
                tokenizer=self.tokenizer,
                model=self.model,
                max_new_tokens=MAX_NEW_TOKENS,
            )
        except Exception:
            import traceback

            traceback.print_exc()
            self.model = None
            self.tokenizer = None
            self.agent_service = None

    def generate_response(self, prompt, user_id):
        if self.model is None or self.tokenizer is None or self.agent_service is None:
            return "模型未正确加载，请检查后端日志。"

        with self.generate_lock:
            try:
                history = ChatService.get_recent_chats(int(user_id), limit=10)
                history_text = self._format_history(history, current_prompt=prompt)
                response = self.agent_service.chat(
                    message=prompt,
                    chat_history=history_text,
                )
                return response or "模型未生成有效内容。"
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    torch.cuda.empty_cache()
                    return "显存不足，请重试或减少上下文。"
                return f"推理错误: {str(e)}"
            except Exception as e:
                return f"Agent 推理错误: {str(e)}"

    def generate_evaluation(self, chat_history_text, file_context_text):
        if self.model is None or self.tokenizer is None or self.agent_service is None:
            raise ValueError("模型未正确加载，请检查后端日志。")

        with self.generate_lock:
            return self.agent_service.evaluate(
                chat_history=chat_history_text,
                file_context=file_context_text,
            )

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

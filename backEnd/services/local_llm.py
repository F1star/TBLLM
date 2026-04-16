from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import torch
from langchain_core.language_models.llms import LLM


class LocalChatLLM(LLM):
    tokenizer: Any = None
    model: Any = None
    max_new_tokens: int = 256
    temperature: float = 0.6
    top_p: float = 0.85
    repetition_penalty: float = 1.1

    @property
    def _llm_type(self) -> str:
        return "local_transformers_chat"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty,
        }

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> str:
        if self.model is None or self.tokenizer is None:
            raise ValueError("Local model is not loaded")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] LocalChatLLM._call - 提示长度: {len(prompt)}, max_new_tokens: {kwargs.get('max_new_tokens', self.max_new_tokens)}")

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个严谨的本地智能体。请严格遵循 ReAct 输出格式。"
                    "如果已经能够回答，就直接给出 Final Answer。"
                ),
            },
            {"role": "user", "content": prompt},
        ]

        input_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer([input_text], return_tensors="pt").to(self.model.device)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] LocalChatLLM._call - 开始生成，输入长度: {inputs.input_ids.shape[1]}")

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_new_tokens", self.max_new_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                top_p=kwargs.get("top_p", self.top_p),
                repetition_penalty=kwargs.get(
                    "repetition_penalty", self.repetition_penalty
                ),
                do_sample=kwargs.get("temperature", self.temperature) > 0,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        input_length = inputs.input_ids.shape[1]
        response_ids = outputs[0][input_length:]
        response = self.tokenizer.decode(response_ids, skip_special_tokens=True).strip()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] LocalChatLLM._call - 生成完成，响应长度: {len(response)}")

        if stop:
            for token in stop:
                if token and token in response:
                    response = response.split(token)[0].strip()

        return response

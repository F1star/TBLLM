from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Optional

from langchain_core.prompts import PromptTemplate

from services.local_llm import LocalChatLLM


CHAT_PROMPT = PromptTemplate.from_template(
    """你是一位友好的教育评估助手，名叫"智评小助手"。你需要与用户进行自然、友好的对话，同时引导用户进行能力评估。

历史对话：
{chat_history}

用户问题：
{input}

要求：
1. 直接输出给用户的回复内容。
2. 不要输出任何中间推理过程或标签。
3. 如果历史对话与当前问题无关，可以忽略历史。
4. 回答保持自然、简洁、准确。"""
)


EVALUATION_PROMPT = PromptTemplate.from_template(
    """你是一个教育场景的评估智能体。
你会收到两类候选上下文：
1. 历史对话
2. 文件解析内容

你的任务：
1. 自行判断是否需要使用历史对话。
2. 自行判断是否需要使用文件解析内容。
3. 只输出最终评估 JSON，不输出解释过程。

候选历史对话：
{chat_history}

候选文件解析内容：
{file_context}

请从以下四个维度对用户进行 0-100 的整数评分：
1. logic_score：逻辑思维
2. creativity_score：创造力
3. expression_score：表达能力
4. knowledge_score：知识广度

输出要求：
1. 只输出一个 JSON 对象。
2. JSON 必须包含字段：
logic_score, creativity_score, expression_score, knowledge_score, overall_score, feedback
3. overall_score 为四项平均分取整。
4. feedback 给出简短、具体的评价建议。"""
)


class AgentService:
    def __init__(self, tokenizer, model, max_new_tokens: int = 256):
        self.llm = LocalChatLLM(
            tokenizer=tokenizer,
            model=model,
            max_new_tokens=max_new_tokens,
        )

    def chat(self, message: str, chat_history: str) -> str:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.chat - 消息长度: {len(message)}, 历史长度: {len(chat_history)}")
        prompt = CHAT_PROMPT.format(
            input=message,
            chat_history=chat_history or "暂无历史对话。",
        )
        response = self.llm.invoke(prompt).strip()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.chat - 响应长度: {len(response)}")
        return response

    def evaluate(self, chat_history: str, file_context: str) -> dict:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 聊天历史长度: {len(chat_history)}, 文件上下文长度: {len(file_context)}")
        prompt = EVALUATION_PROMPT.format(
            chat_history=chat_history or "暂无历史对话。",
            file_context=file_context or "暂无文件内容。",
        )
        response = self.llm.invoke(prompt, max_new_tokens=512, temperature=0.2).strip()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 原始响应长度: {len(response)}")
        parsed = self._extract_json(response)
        if parsed is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - JSON解析失败: {response[:200]}")
            raise ValueError(f"评估结果解析失败: {response[:200]}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 解析成功 - 逻辑: {parsed.get('logic_score')}, 创造力: {parsed.get('creativity_score')}, 表达: {parsed.get('expression_score')}, 知识: {parsed.get('knowledge_score')}")
        return parsed

    def _extract_json(self, text: str) -> Optional[dict]:
        cleaned = re.sub(r"```json\s*|\s*```", "", text).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        brace_count = 0
        start = -1
        for index, char in enumerate(cleaned):
            if char == "{":
                if brace_count == 0:
                    start = index
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start != -1:
                    candidate = cleaned[start : index + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        continue
        return None

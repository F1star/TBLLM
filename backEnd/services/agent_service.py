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

PROFESSIONAL_ASSESSMENT_PROMPT = PromptTemplate.from_template(
    """你是一个专业的教育评估专家，正在分析学生在专业测评中的表现。

以下是学生在专业测评中的回答记录：
{assessment_text}

学生组别：{cohort}

请根据学生的回答内容，评估其社会与情感技能。

请以以下格式输出评估结果（不要输出JSON，直接输出文本格式）：

技能评估结果（百分制）：
- 责任感: <分数>分（<等级>）
- 同理心: <分数>分（<等级>）
- 成就动机: <分数>分（<等级>）
- 乐观: <分数>分（<等级>）
- 社交能力: <分数>分（<等级>）
- 自我效能: <分数>分（<等级>）
- 坚持: <分数>分（<等级>）
- 信任: <分数>分（<等级>）
- 合作: <分数>分（<等级>）
- 好奇心: <分数>分（<等级>）
- 创造力: <分数>分（<等级>）
- 抗压能力: <分数>分（<等级>）
- 活力: <分数>分（<等级>）
- 自我控制: <分数>分（<等级>）
- 情绪控制: <分数>分（<等级>）
- 包容: <分数>分（<等级>）
- 自信/主张: <分数>分（<等级>）

综合评价：
<对学生表现的综合评价文字，指出优点和改进方向>

注意：
1. 每个技能的分数范围为0-100分
2. 等级分类：很高（>=80分）、较高（60-79分）、中等（40-59分）、较低（20-39分）、很低（<20分）
3. 请根据学生的回答内容和所属组别（{cohort}）进行客观评分
4. 确保输出完整的17项技能评分"""
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

    def evaluate(self, chat_history: str, file_context: str, **kwargs) -> dict:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 聊天历史长度: {len(chat_history)}, 文件上下文长度: {len(file_context)}")
        prompt = EVALUATION_PROMPT.format(
            chat_history=chat_history or "暂无历史对话。",
            file_context=file_context or "暂无文件内容。",
        )
        response = self.llm.invoke(prompt, max_new_tokens=1024, temperature=0.2).strip()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 原始响应长度: {len(response)}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 原始响应内容: {response[:500]}")
        parsed = self._extract_json(response)
        if parsed is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - JSON解析失败: {response[:200]}")
            raise ValueError(f"评估结果解析失败: {response[:200]}")
        # 兼容模型可能输出的不同字段名（如 logical_score 而非 logic_score）
        field_aliases = {
            'logic_score': ['logical_score'],
            'creativity_score': [],
            'expression_score': [],
            'knowledge_score': [],
            'overall_score': [],
        }
        for standard_key, aliases in field_aliases.items():
            if parsed.get(standard_key) is None:
                for alias in aliases:
                    if parsed.get(alias) is not None:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 字段映射: {alias} -> {standard_key} = {parsed[alias]}")
                        parsed[standard_key] = parsed[alias]
                        break
        # 确保所有分数字段不为None，避免null值入库变成0
        score_keys = ['logic_score', 'creativity_score', 'expression_score', 'knowledge_score', 'overall_score']
        for key in score_keys:
            if parsed.get(key) is None:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.evaluate - 警告: {key} 为null，已设为0")
                parsed[key] = 0
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

    def _parse_skill_assessment(self, text: str) -> dict:
        """
        解析技能评估文本格式为结构化数据

        预期格式:
            技能评估结果（百分制）：
            - 技能名: 分数分（等级）
            ...

            综合评价：
            文本...

        Returns:
            {
                'skill_scores': {'技能名': 分数, ...},
                'overall_score': 平均分,
                'feedback': '综合评价文本'
            }
        """
        skill_scores = {}

        # 解析 "- 技能名: 分数分（等级）" 模式
        pattern = r"- (.+?):\s*([\d.]+)分"
        for match in re.finditer(pattern, text):
            skill_name = match.group(1).strip()
            try:
                score = float(match.group(2))
                score = max(0, min(100, score))  # 限制在0-100
                skill_scores[skill_name] = score
            except ValueError:
                continue

        # 提取综合评价
        feedback = ""
        eval_match = re.search(r"综合评价[：:]\s*([\s\S]+)", text)
        if eval_match:
            feedback = eval_match.group(1).strip()

        # 计算综合得分（所有技能的平均分）
        overall_score = sum(skill_scores.values()) / len(skill_scores) if skill_scores else 0

        result = {
            'skill_scores': skill_scores,
            'overall_score': round(overall_score, 1),
            'feedback': feedback,
        }

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService._parse_skill_assessment - "
              f"解析到 {len(skill_scores)} 个技能评分, 综合得分: {result['overall_score']}")

        return result

    def professional_assess(self, assessment_text: str, cohort: str) -> dict:
        """专业测评评估"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.professional_assess - 评估文本长度: {len(assessment_text)}, 组别: {cohort}")
        prompt = PROFESSIONAL_ASSESSMENT_PROMPT.format(
            assessment_text=assessment_text or "暂无回答记录。",
            cohort=cohort or "未知组别",
        )
        response = self.llm.invoke(prompt, max_new_tokens=1024, temperature=0.2).strip()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.professional_assess - 原始响应长度: {len(response)}")

        # 解析技能评估文本格式
        result = self._parse_skill_assessment(response)

        if not result['skill_scores']:
            # 降级方案：尝试JSON解析（兼容旧格式）
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.professional_assess - 文本解析未找到技能, 尝试JSON回退")
            parsed = self._extract_json(response)
            if parsed:
                skill_scores = {}
                for key, value in parsed.items():
                    if isinstance(value, (int, float)) and 0 <= value <= 100:
                        skill_scores[key] = value
                if skill_scores:
                    result['skill_scores'] = skill_scores
                    result['overall_score'] = round(sum(skill_scores.values()) / len(skill_scores), 1)
                result['feedback'] = parsed.get('feedback', result['feedback'])
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.professional_assess - JSON回退解析到 {len(skill_scores)} 个评分")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.professional_assess - 解析失败, 响应前200字符: {response[:200]}")
                raise ValueError(f"专业测评结果解析失败: {response[:200]}")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AgentService.professional_assess - 解析完成 - 技能数: {len(result['skill_scores'])}, 综合: {result['overall_score']}")
        return result


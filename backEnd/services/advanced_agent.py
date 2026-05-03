"""
高级Agent服务 - 基于LangChain的完整Agent实现

这个模块提供了基于LangChain AgentExecutor的完整Agent系统，
支持ReAct模式、工具调用、记忆管理等功能。

设计目标：
1. 与现有AgentService保持接口兼容
2. 支持逐步迁移，通过配置开关选择使用哪个Agent
3. 提供更强大的工具调用和推理能力
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import BaseMemory
from langchain.tools import BaseTool
from langchain_core.agents import AgentAction, AgentFinish

from services.local_llm import LocalChatLLM

# 设置日志
logger = logging.getLogger(__name__)


class LenientReActParser(ReActSingleInputOutputParser):
    """容错版 ReAct 解析器，自动修正常见格式问题"""

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        # 中文标签 → 英文
        text = text.replace('思考：', 'Thought:')
        text = text.replace('行动：', 'Action:')
        text = text.replace('行动输入：', 'Action Input:')
        text = text.replace('观察：', 'Observation:')
        text = text.replace('最终回答：', 'Final Answer:')
        # 修正大小写问题（大小写不敏感替换）
        text = re.sub(r'(?im)^\s*Action\s+Input\s*:', 'Action Input:', text)
        text = re.sub(r'(?im)^\s*Action\s*:', 'Action:', text)
        text = re.sub(r'(?im)^\s*Final\s+Answer\s*:', 'Final Answer:', text)
        return super().parse(text)


class AdvancedAgent:
    """高级Agent服务，基于LangChain AgentExecutor实现"""

    def __init__(
        self,
        llm: LocalChatLLM,
        tools: List[BaseTool],
        memory: Optional[BaseMemory] = None,
        max_iterations: int = 5,
        verbose: bool = False,
        handle_parsing_errors: bool = True,
    ):
        """
        初始化AdvancedAgent

        Args:
            llm: LocalChatLLM实例
            tools: 工具列表
            memory: 记忆系统（可选）
            max_iterations: 最大迭代次数（工具调用次数）
            verbose: 是否输出详细日志
            handle_parsing_errors: 是否处理解析错误
        """
        self.llm = llm
        self.tools = tools
        self.memory = memory or ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        self.max_iterations = max_iterations
        self.verbose = verbose

        # 创建ReAct提示模板（针对中文优化）
        self.react_prompt = self._create_react_prompt()

        # 创建Agent和AgentExecutor
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.react_prompt,
            output_parser=LenientReActParser(),
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            handle_parsing_errors=handle_parsing_errors,
            return_intermediate_steps=False,  # 不返回中间步骤，简化输出
        )

        logger.info(f"AdvancedAgent初始化完成，包含{len(tools)}个工具")

    def _create_react_prompt(self) -> PromptTemplate:
        """创建针对中文优化的ReAct提示模板"""

        template = """你是一个名为"智评小助手"的教育评估助手，专门帮助青少年进行能力评估。
你具有以下能力：
1. 使用工具获取信息（时间、文档、评估等）
2. 进行逻辑推理和分析
3. 提供友好、有帮助的回答
4. 引导用户进行能力评估对话

你必须严格按照以下格式进行推理，注意英文标签的大小写必须完全一致：

Thought: 你需要考虑用户的问题，决定是否需要使用工具
Action: 你要使用的工具名称（必须来自可用工具列表）
Action Input: 工具的输入参数（必须是JSON格式）
Observation: 工具返回的结果
...（这个 Thought/Action/Action Input/Observation 循环可以重复多次）
Thought: 我现在有足够的信息可以回答用户的问题了
Final Answer: 给用户的最终回答

可用工具：
{tools}

工具名称：{tool_names}

重要规则：
1. "Action Input:" 的 Input 首字母 I 必须大写
2. Action: 后面只能跟可用工具列表中的工具名称
3. 工具不需要 user_id 参数，系统会自动识别
4. 如果工具调用失败，重新尝试不同的参数，最多尝试3次
5. 如果已经能够直接回答，就直接给出 Final Answer

历史对话：
{chat_history}

用户问题：{input}

{agent_scratchpad}

严格按照上述格式回答。现在开始：
"""

        return PromptTemplate.from_template(template)

    def chat(self, message: str, chat_history: Optional[str] = None) -> str:
        """
        处理用户消息，使用Agent进行回复

        Args:
            message: 用户消息
            chat_history: 历史对话文本（可选）

        Returns:
            Agent的回复
        """
        try:
            # 准备输入参数
            inputs = {
                "input": message,
            }

            # 如果有提供历史对话，更新记忆
            if chat_history:
                # 这里可以优化，将历史对话加载到记忆中
                # 目前简单处理：如果提供了历史，将其作为上下文的一部分
                # 实际实现可能需要更复杂的记忆管理
                pass

            # 执行Agent
            result = self.agent_executor.invoke(inputs)

            # 提取回复
            response = result.get("output", "")
            if not response:
                logger.warning("Agent未生成有效回复")
                return "抱歉，我暂时无法回答这个问题。"

            # 清理回复，移除可能的中间步骤痕迹
            cleaned_response = self._clean_response(response)

            logger.debug(f"Agent回复: {cleaned_response[:100]}...")
            return cleaned_response

        except Exception as e:
            logger.error(f"Agent执行错误: {str(e)}", exc_info=True)
            return f"处理消息时出错: {str(e)}"

    def evaluate(
        self,
        chat_history: str,
        file_context: str,
        deep_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        评估用户能力

        Args:
            chat_history: 历史对话文本
            file_context: 文件上下文
            deep_mode: 是否启用深度思考（True=ReAct循环，False=直接LLM）

        Returns:
            评估结果字典
        """
        if deep_mode:
            return self._evaluate_react(chat_history, file_context)
        else:
            return self._evaluate_simple(chat_history, file_context)

    def _evaluate_simple(self, chat_history: str, file_context: str) -> Dict[str, Any]:
        """直接 LLM 评估，绕过 ReAct"""
        simple_prompt = f"""你是一个教育场景的评估智能体。

历史对话：
{chat_history or "暂无历史对话。"}

文件内容：
{file_context or "暂无文件内容。"}

请从以下四个维度对用户进行0-100的整数评分：
1. logic_score：逻辑思维
2. creativity_score：创造力
3. expression_score：表达能力
4. knowledge_score：知识广度

请以JSON格式返回评分结果，格式如下：
{{
    "logic_score": 分数,
    "creativity_score": 分数,
    "expression_score": 分数,
    "knowledge_score": 分数,
    "overall_score": 平均分,
    "feedback": "简要的反馈意见"
}}

注意：
- 所有分数必须是0-100之间的整数
- overall_score为四个维度的平均分
- feedback应该包含具体的改进建议
"""
        try:
            response = self.llm.invoke(
                simple_prompt,
                max_new_tokens=1024,
                temperature=0.2
            ).strip()

            parsed = self._extract_json(response)
            if parsed is None:
                logger.error(f"评估 JSON 解析失败: {response[:200]}")
                raise ValueError(f"评估结果解析失败: {response[:200]}")

            score_keys = ['logic_score', 'creativity_score', 'expression_score', 'knowledge_score', 'overall_score']
            for key in score_keys:
                if parsed.get(key) is None:
                    logger.warning(f"评估结果中 {key} 为 null，已设为 0")
                    parsed[key] = 0

            return parsed
        except Exception as e:
            logger.error(f"评估过程出错: {str(e)}", exc_info=True)
            raise

    def _evaluate_react(self, chat_history: str, file_context: str) -> Dict[str, Any]:
        """使用 ReAct 循环评估用户能力"""
        # 清除之前对话的记忆，避免干扰
        self.clear_memory()

        eval_input = f"""你需要对一个学生的综合能力进行评估。

【背景参考】
对话历史摘要：{chat_history[:1500] if chat_history else "暂无"}
文件内容摘要：{file_context[:1500] if file_context else "暂无"}

请严格按照以下步骤执行：
步骤1：使用 all_history 工具获取该学生的所有会话历史（工具不需要任何参数，直接调用即可）。
步骤2：使用 file_summary 工具获取该学生上传的文件内容（工具不需要任何参数，直接调用即可）。
步骤3：综合所有信息，从四个维度评分（0-100的整数）：
- logic_score：逻辑思维能力
- creativity_score：创造力
- expression_score：表达能力
- knowledge_score：知识广度
步骤4：overall_score 为四项平均分取整，feedback 给出简短评价建议。

最终只输出一个 JSON 对象，格式如下：
{{
    "logic_score": 分数,
    "creativity_score": 分数,
    "expression_score": 分数,
    "knowledge_score": 分数,
    "overall_score": 平均分,
    "feedback": "评价和建议"
}}

重要：工具调用不需要 user_id、student_id、files 等参数，直接传入空字符串即可。
注意：必须先使用工具获取信息，不能凭空评分。"""

        try:
            result = self.agent_executor.invoke({"input": eval_input})
            response = result.get("output", "")

            logger.info(f"评估原始响应: {response[:300]}")

            # 直接用 _extract_json 从原始输出中提取 JSON
            parsed = self._extract_json(response)
            if parsed is None:
                # 如果直接没找到，尝试清理后再次提取
                cleaned = self._clean_response(response)
                parsed = self._extract_json(cleaned)

            if parsed is None:
                logger.error(f"评估 JSON 解析失败: {response[:200]}")
                raise ValueError(f"评估结果解析失败: {response[:200]}")

            score_keys = ['logic_score', 'creativity_score', 'expression_score', 'knowledge_score', 'overall_score']
            for key in score_keys:
                if parsed.get(key) is None:
                    logger.warning(f"评估结果中 {key} 为 null，已设为 0")
                    parsed[key] = 0

            return parsed

        except Exception as e:
            logger.error(f"评估过程出错: {str(e)}", exc_info=True)
            raise

    def _clean_response(self, response: str) -> str:
        """清理Agent回复，移除可能的中间步骤标记"""
        # 移除英文"Final Answer:"标签及其之前的内容
        if "Final Answer:" in response:
            response = response.split("Final Answer:")[-1].strip()
        # 兼容中文标签
        if "最终回答：" in response:
            response = response.split("最终回答：")[-1].strip()

        # 移除其他可能的过程标记（中英文）
        markers = ["思考：", "行动：", "行动输入：", "观察：", "Thought:", "Action:", "Action Input:", "Observation:"]
        for marker in markers:
            if marker in response:
                # 只保留最后一个标记之后的内容
                parts = response.split(marker)
                response = parts[-1].strip()

        return response.strip()

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON"""
        import re

        cleaned = re.sub(r"```json\s*|\s*```", "", text).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 尝试提取第一个完整的JSON对象
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
                    candidate = cleaned[start:index + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue

        return None

    def add_tool(self, tool: BaseTool):
        """动态添加工具"""
        self.tools.append(tool)
        # 需要重新创建Agent以包含新工具
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.react_prompt,
            output_parser=LenientReActParser(),
        )
        self.agent_executor.agent = self.agent
        logger.info(f"添加新工具: {tool.name}")

    def clear_memory(self):
        """清除记忆"""
        if self.memory:
            self.memory.clear()
            logger.info("记忆已清除")


class AdvancedAgentFactory:
    """AdvancedAgent工厂类，简化创建过程"""

    @staticmethod
    def create_from_model_service(
        model_service,
        tools: List[BaseTool],
        **kwargs
    ) -> AdvancedAgent:
        """
        从现有的ModelService创建AdvancedAgent

        Args:
            model_service: ModelService实例
            tools: 工具列表
            **kwargs: 传递给AdvancedAgent的额外参数

        Returns:
            AdvancedAgent实例
        """
        if not model_service or not model_service.agent_service:
            raise ValueError("ModelService未正确初始化")

        # 从ModelService获取LLM
        llm = model_service.agent_service.llm

        # 创建AdvancedAgent
        agent = AdvancedAgent(llm=llm, tools=tools, **kwargs)

        return agent

    @staticmethod
    def create_default_tools():
        """创建默认工具集（占位符，实际实现需要具体工具）"""
        # 这里返回空列表，实际实现将在后续步骤中添加
        return []


# 兼容性包装器，保持与现有AgentService相似的接口
class CompatibleAgentService:
    """
    兼容性包装器，提供与现有AgentService相同的接口，
    但内部使用AdvancedAgent
    """

    def __init__(self, advanced_agent: AdvancedAgent):
        self.advanced_agent = advanced_agent

    def chat(self, message: str, chat_history: str) -> str:
        """兼容chat方法"""
        return self.advanced_agent.chat(message, chat_history)

    def evaluate(self, chat_history: str, file_context: str, deep_mode: bool = False) -> dict:
        """兼容evaluate方法"""
        return self.advanced_agent.evaluate(chat_history, file_context, deep_mode=deep_mode)

    def professional_assess(self, assessment_text: str, cohort: str) -> dict:
        """兼容professional_assess方法 - 直接使用原始的AgentService"""
        # 创建原始的AgentService来处理专业测评
        from services.agent_service import AgentService
        from services.local_llm import LocalChatLLM
        llm = self.advanced_agent.llm
        raw_agent = AgentService(
            tokenizer=llm.tokenizer if hasattr(llm, 'tokenizer') else None,
            model=llm.model if hasattr(llm, 'model') else None,
            max_new_tokens=llm.max_new_tokens if hasattr(llm, 'max_new_tokens') else 1024,
        )
        return raw_agent.professional_assess(assessment_text, cohort)
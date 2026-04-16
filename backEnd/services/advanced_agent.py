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
from typing import Any, Dict, List, Optional, Union

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import BaseMemory
from langchain.tools import BaseTool

from services.local_llm import LocalChatLLM

# 设置日志
logger = logging.getLogger(__name__)


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
            prompt=self.react_prompt
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

        # 系统提示 - 定义Agent的角色和能力
        system_prompt = """你是一个名为"智评小助手"的教育评估助手，专门帮助青少年进行能力评估。
你具有以下能力：
1. 使用工具获取信息（时间、文档、评估等）
2. 进行逻辑推理和分析
3. 提供友好、有帮助的回答
4. 引导用户进行能力评估对话

请使用以下格式进行思考：

思考：你需要考虑用户的问题，决定是否需要使用工具
行动：你要使用的工具名称
行动输入：工具的输入参数
观察：工具返回的结果
...（这个思考/行动/观察循环可以重复多次）
思考：我现在有足够的信息可以回答用户的问题了
最终回答：给用户的最终回答

工具列表：
{tools}

请严格遵循上述格式。如果已经能够直接回答，就直接给出最终回答。
"""

        # 完整提示模板
        template = f"""{system_prompt}

历史对话：
{{chat_history}}

用户问题：{{input}}

你必须在"思考："、"行动："、"行动输入："、"观察："、"最终回答："这些标签后提供内容。
现在开始：
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
        file_context: str
    ) -> Dict[str, Any]:
        """
        评估用户能力（兼容现有接口）

        Args:
            chat_history: 历史对话文本
            file_context: 文件上下文

        Returns:
            评估结果字典
        """
        # 注意：评估功能可能需要专门的工具或不同的Agent配置
        # 这里先实现一个兼容版本，后续可以优化

        # 创建评估专用的提示
        evaluation_prompt = f"""你是一个教育场景的评估智能体。

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
            # 使用LLM直接生成评估结果（简化实现）
            response = self.llm.invoke(
                evaluation_prompt,
                max_new_tokens=512,
                temperature=0.2
            ).strip()

            # 解析JSON响应
            result = self._extract_json(response)
            if result is None:
                logger.error(f"评估结果解析失败: {response[:200]}")
                raise ValueError(f"评估结果解析失败: {response[:200]}")

            return result

        except Exception as e:
            logger.error(f"评估过程出错: {str(e)}", exc_info=True)
            raise

    def _clean_response(self, response: str) -> str:
        """清理Agent回复，移除可能的中间步骤标记"""
        # 移除"最终回答："标签及其之前的内容
        if "最终回答：" in response:
            response = response.split("最终回答：")[-1].strip()

        # 移除其他可能的过程标记
        markers = ["思考：", "行动：", "行动输入：", "观察："]
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
            prompt=self.react_prompt
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

    def evaluate(self, chat_history: str, file_context: str) -> dict:
        """兼容evaluate方法"""
        return self.advanced_agent.evaluate(chat_history, file_context)
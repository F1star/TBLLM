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
            return_intermediate_steps=True,
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
            try:
                react_evidence = self._collect_evidence_with_react(
                    chat_history,
                    file_context,
                )
                return self._evaluate_simple(
                    chat_history,
                    file_context,
                    tool_context=react_evidence,
                )
            except Exception as e:
                logger.warning(
                    f"ReAct证据收集失败，回退到程序化证据收集: {str(e)}"
                )
                return self._evaluate_simple(
                    chat_history,
                    file_context,
                    include_tool_context=True,
                )

        return self._evaluate_simple(
            chat_history,
            file_context,
            include_tool_context=False,
        )

    def _evaluate_simple(
        self,
        chat_history: str,
        file_context: str,
        include_tool_context: bool = False,
        tool_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """直接 LLM 评估，确保最终输出稳定 JSON。"""
        if tool_context is None:
            tool_context = self._collect_evaluation_tool_context() if include_tool_context else "未启用补充工具上下文。"
        simple_prompt = f"""你是一个教育场景的评估智能体。

历史对话：
{chat_history or "暂无历史对话。"}

文件内容：
{file_context or "暂无文件内容。"}

补充上下文：
{tool_context}

请从以下四个维度对用户进行0-100的整数评分：
1. logic_score：逻辑思维
2. creativity_score：创造力
3. expression_score：表达能力
4. knowledge_score：知识广度

请只返回一个合法 JSON 对象，不要输出 Thought、Action、Final Answer、Markdown 代码块或解释文字。格式如下：
{{
    "logic_score": 分数,
    "creativity_score": 分数,
    "expression_score": 分数,
    "knowledge_score": 分数,
    "overall_score": 平均分,
    "feedback": "80到160字的单段中文反馈"
}}

注意：
- 所有分数必须是0-100之间的整数
- overall_score为四个维度的平均分取整
- feedback必须是单行字符串，不要换行，不要使用项目符号，不要包含未转义的英文双引号
- 如果证据很少，应降低分数并在反馈中说明依据有限
"""
        try:
            response = self.llm.invoke(
                simple_prompt,
                max_new_tokens=512,
                temperature=0.1,
                system_prompt=(
                    "你是教育评估模型。你必须只输出一个合法 JSON 对象，"
                    "不要输出 ReAct、Thought、Action、Final Answer 或 Markdown。"
                ),
            ).strip()

            parsed = self._extract_json(response)
            if parsed is None:
                logger.error(f"评估 JSON 解析失败: {response[:200]}")
                raise ValueError(f"评估结果解析失败: {response[:200]}")

            return self._normalise_evaluation_result(parsed)
        except Exception as e:
            logger.error(f"评估过程出错: {str(e)}", exc_info=True)
            raise

    def _collect_evaluation_tool_context(self) -> str:
        """程序化调用评估需要的工具，避免 ReAct 污染结构化输出。"""
        context_blocks = []
        for tool_name in ("all_history", "file_summary"):
            tool = next((item for item in self.tools if item.name == tool_name), None)
            if tool is None:
                continue
            try:
                result = tool.run("")
                if result:
                    context_blocks.append(f"【{tool_name}】\n{str(result)[:1500]}")
            except Exception as e:
                logger.warning(f"评估补充工具 {tool_name} 调用失败: {str(e)}")

        if not context_blocks:
            return "暂无补充上下文。"
        return "\n\n".join(context_blocks)

    def _collect_evidence_with_react(self, chat_history: str, file_context: str) -> str:
        """用受控 ReAct 收集评估证据，不让小模型自由输出 Action。"""
        self.clear_memory()

        available_tool_names = {tool.name for tool in self.tools}
        required_tools = ("all_history", "file_summary")
        missing_tools = [tool_name for tool_name in required_tools if tool_name not in available_tool_names]
        if missing_tools:
            raise ValueError(f"ReAct缺少必要工具: {', '.join(missing_tools)}")

        trace_blocks: List[str] = []
        evidence_blocks = [
            f"【当前会话证据】\n{chat_history or '暂无历史对话。'}",
            f"【当前文件证据】\n{file_context or '暂无文件内容。'}",
        ]

        all_history = self._run_controlled_react_step(
            tool_name="all_history",
            tool_input="",
            thought="需要先查看用户全部历史对话，补充当前会话之外的表现证据。",
            trace_blocks=trace_blocks,
        )
        evidence_blocks.append(f"【all_history 观察】\n{self._clip_observation(all_history, 1500)}")

        file_summary = self._run_controlled_react_step(
            tool_name="file_summary",
            tool_input="",
            thought="需要查看用户上传文件和摘要，补充文件中的学习计划、知识表现和反思证据。",
            trace_blocks=trace_blocks,
        )
        evidence_blocks.append(f"【file_summary 观察】\n{self._clip_observation(file_summary, 1500)}")

        if "retrieve_documents" in available_tool_names:
            query = self._build_retrieval_query(chat_history, file_context)
            retrieved = self._run_controlled_react_step(
                tool_name="retrieve_documents",
                tool_input=query,
                thought="需要使用本地向量检索补充系统知识库和用户文档片段，提高评估依据的准确性。",
                trace_blocks=trace_blocks,
            )
            evidence_blocks.append(f"【retrieve_documents 观察】\n{self._clip_observation(retrieved, 1500)}")
        else:
            trace_blocks.append(
                "Thought: 当前Agent没有 retrieve_documents 工具，只能基于历史和文件摘要进行评估。"
            )

        raw_evidence = "\n\n".join(evidence_blocks)
        evidence = self._summarise_react_evidence(raw_evidence)

        if not evidence:
            raise ValueError("ReAct未返回有效证据摘要")

        logger.info("受控ReAct证据收集完成:\n%s\nFinal Evidence完整摘要: %s", "\n".join(trace_blocks), evidence)
        return f"【ReAct证据摘要】\n{evidence[:2500]}"

    def _run_controlled_react_step(
        self,
        tool_name: str,
        tool_input: str,
        thought: str,
        trace_blocks: List[str],
    ) -> str:
        """执行一个受控 ReAct 工具步骤，并记录 Thought/Action/Observation。"""
        tool = next((item for item in self.tools if item.name == tool_name), None)
        if tool is None:
            raise ValueError(f"ReAct工具不存在: {tool_name}")

        trace_blocks.append(f"Thought: {thought}")
        trace_blocks.append(f"Action: {tool_name}")
        trace_blocks.append(f"Action Input: {tool_input!r}")

        result = str(tool.run(tool_input) or "").strip()
        observation = self._clip_observation(result, 500).replace("\n", " ")
        trace_blocks.append(f"Observation: {observation}")
        return result

    def _clip_observation(self, text: str, max_chars: int) -> str:
        """截断工具观察并显式标注，避免日志看起来像内容没生成完。"""
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        if len(cleaned) <= max_chars:
            return cleaned
        clipped = cleaned[:max_chars].rstrip()
        last_punctuation = max(clipped.rfind(mark) for mark in "。！？；.!?;")
        if last_punctuation >= max_chars // 2:
            clipped = clipped[:last_punctuation + 1]
        return f"{clipped}...[日志截断，完整内容已进入证据汇总]"

    def _build_retrieval_query(self, chat_history: str, file_context: str) -> str:
        """生成简短检索词，避免把复杂 JSON 传给检索工具。"""
        source = f"{chat_history or ''} {file_context or ''}"
        candidates = []
        for term in ("逻辑思维", "创造力", "表达能力", "知识广度", "学习表现", "能力评价"):
            if term in source:
                candidates.append(term)
        if not candidates:
            candidates = ["青少年能力评价", "学习表现", "表达能力"]
        return " ".join(candidates[:4])

    def _summarise_react_evidence(self, raw_evidence: str) -> str:
        """把工具观察压缩成证据摘要；失败时返回规则摘要，保证ReAct链路成功收束。"""
        prompt = f"""请把以下评估证据压缩成一段完整的中文证据摘要。只总结证据，不要评分，不要输出JSON，不要写Thought/Action/Observation。

{raw_evidence[:5000]}

要求：
- 说明对话证据、文件证据、证据不足点。
- 150到260字。
- 只输出一个自然段，不要标题、编号、项目符号或“证据摘要：”这类开头。
- 最后必须用句号、问号或感叹号自然收尾。
- 不要编造原文没有的信息。"""

        try:
            response = self.llm.invoke(
                prompt,
                max_new_tokens=320,
                temperature=0.1,
                system_prompt="你只负责整理评估证据摘要，不评分，不输出JSON，不输出ReAct格式。",
            ).strip()
            response = self._strip_react_trace(self._clean_response(response))
            response = self._normalise_evidence_summary(response)
            if response and "logic_score" not in response and "Thought:" not in response:
                return response
        except Exception as e:
            logger.warning(f"ReAct证据摘要生成失败，使用规则摘要: {str(e)}")

        return self._fallback_evidence_summary(raw_evidence)

    def _fallback_evidence_summary(self, raw_evidence: str) -> str:
        compact = re.sub(r"\s+", " ", raw_evidence or "").strip()
        if not compact:
            return "当前可用证据较少，仅能依据有限对话和文件内容进行保守评估。"
        return self._normalise_evidence_summary(
            f"已通过ReAct工具收集当前会话、历史对话、文件摘要和本地向量检索片段作为评估依据。主要证据片段显示：{compact[:420]}"
        )

    def _normalise_evidence_summary(self, text: str) -> str:
        """整理证据摘要形态，避免标题/列表和未收尾句子。"""
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        cleaned = re.sub(r"^(?:\d+[.、]\s*)?(?:评估)?证据摘要[:：]\s*", "", cleaned)
        cleaned = re.sub(r"^\s*[-*]\s*", "", cleaned)
        cleaned = re.sub(r"(?:^|\s)[-*]\s+", "；", cleaned)
        cleaned = cleaned.strip(" `")
        if not cleaned:
            return ""
        if cleaned[-1] not in "。！？.!?":
            last_punctuation = max(cleaned.rfind(mark) for mark in "。！？.!?")
            if last_punctuation >= 80:
                cleaned = cleaned[:last_punctuation + 1]
            else:
                cleaned += "。"
        return cleaned

    def _evaluate_react(self, chat_history: str, file_context: str) -> Dict[str, Any]:
        """兼容旧调用：ReAct只收集证据，最终评分仍走直接 JSON 评估。"""
        react_evidence = self._collect_evidence_with_react(chat_history, file_context)
        return self._evaluate_simple(
            chat_history,
            file_context,
            tool_context=react_evidence,
        )

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

    def _strip_react_trace(self, text: str) -> str:
        """移除可能泄漏的 ReAct 过程标签，保留最终证据文本。"""
        if not text:
            return ""

        cleaned = text
        for final_marker in ("Final Answer:", "最终回答："):
            if final_marker in cleaned:
                cleaned = cleaned.split(final_marker)[-1]

        cleaned = re.sub(
            r"(?ims)^\s*(Thought|Action|Action Input|Observation)\s*:.*?(?=^\s*(Thought|Action|Action Input|Observation|Final Answer)\s*:|\Z)",
            "",
            cleaned,
        )
        cleaned = re.sub(
            r"(?m)^\s*(思考|行动|行动输入|观察)\s*：.*$",
            "",
            cleaned,
        )
        return cleaned.strip()

    def _extract_used_tool_names(self, intermediate_steps: List[Any]) -> List[str]:
        """从 LangChain intermediate_steps 中提取已调用工具名。"""
        used_tools: List[str] = []
        for step in intermediate_steps:
            action = step[0] if isinstance(step, (list, tuple)) and step else step
            tool_name = getattr(action, "tool", None)
            if tool_name:
                used_tools.append(str(tool_name))
        return used_tools

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON"""
        import re

        cleaned = self._clean_response(text or "")
        cleaned = re.sub(r"```json\s*|\s*```", "", cleaned).strip()

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

        repaired = self._extract_loose_evaluation_json(cleaned)
        if repaired is not None:
            return repaired

        return None

    def _extract_loose_evaluation_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从不严格 JSON 的模型输出中尽力提取评估字段。"""
        if not text:
            return None

        result: Dict[str, Any] = {}
        for key in (
            "logic_score",
            "creativity_score",
            "expression_score",
            "knowledge_score",
            "overall_score",
        ):
            match = re.search(
                rf'["\']?{key}["\']?\s*[:：]\s*([0-9]+(?:\.[0-9]+)?)',
                text,
            )
            if match:
                number = float(match.group(1))
                result[key] = int(round(number)) if key != "overall_score" else number

        feedback_match = re.search(r'["\']?feedback["\']?\s*[:：]\s*["\']?([\s\S]+)', text)
        if feedback_match:
            feedback = feedback_match.group(1)
            feedback = re.sub(r"```[\s\S]*$", "", feedback)
            feedback = re.sub(r'["\']?\s*}\s*$', "", feedback.strip())
            feedback = feedback.replace("\r", " ").replace("\n", " ")
            result["feedback"] = re.sub(r"\s+", " ", feedback).strip()

        if result:
            return result
        return None

    def _normalise_evaluation_result(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """校验并补齐评估结果字段，保证入库字段稳定。"""
        score_keys = [
            "logic_score",
            "creativity_score",
            "expression_score",
            "knowledge_score",
        ]

        overall = parsed.get("overall_score")
        for key in score_keys:
            value = parsed.get(key)
            if value is None and overall is not None:
                value = overall
            if value is None:
                logger.warning(f"评估结果中 {key} 缺失，已设为 0")
                value = 0
            parsed[key] = max(0, min(100, int(round(float(value)))))

        parsed["overall_score"] = int(round(sum(parsed[key] for key in score_keys) / len(score_keys)))
        feedback = parsed.get("feedback") or "暂无反馈。"
        parsed["feedback"] = re.sub(r"\s+", " ", str(feedback)).strip()
        return parsed

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

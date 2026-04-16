"""
增强版Agent工具系统

提供多种工具供AdvancedAgent使用，包括：
1. 时间工具
2. 计算工具
3. 文档检索工具
4. 评估调用工具
5. 会话管理工具
6. 教育专用工具
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from langchain_core.tools import BaseTool, StructuredTool
from langchain.tools import tool

from services.rag_service import RAGService
from services.chat_service import ChatService
from services.evaluation_service import EvaluationService
from services.session_service import SessionService
from db_models.chat_history import ChatHistory


class TimeTool(BaseTool):
    """获取当前时间工具"""

    name: str = "get_current_time"
    description: str = (
        "获取当前日期和时间。"
        "当用户询问时间、日期、今天、现在等问题时使用。"
        "输入参数可以是空字符串或任何与时间相关的查询。"
    )
    args_schema: Optional[Type] = None

    def _run(self, query: str = "") -> str:
        """执行工具"""
        now = datetime.now()
        return now.strftime("%Y年%m月%d日 %H:%M:%S")

    async def _arun(self, query: str = "") -> str:
        """异步执行工具"""
        return self._run(query)


class CalculatorTool(BaseTool):
    """计算器工具"""

    name: str = "calculator"
    description: str = (
        "执行数学计算。支持加减乘除、幂运算、平方根等。"
        "输入应该是一个数学表达式，如：'2 + 2', 'sqrt(16)', '3 * (4 + 5)'。"
        "不支持变量或复杂函数。"
    )
    args_schema: Optional[Type] = None

    def _run(self, expression: str) -> str:
        """执行计算"""
        try:
            # 安全地评估数学表达式
            result = self._safe_eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"

    async def _arun(self, expression: str) -> str:
        """异步执行计算"""
        return self._run(expression)

    def _safe_eval(self, expression: str) -> float:
        """安全地评估数学表达式"""
        # 清理表达式
        expr = expression.strip()

        # 定义允许的函数和常量
        allowed_names = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'pow': pow,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'pi': math.pi,
            'e': math.e,
        }

        # 编译和评估表达式
        code = compile(expr, '<string>', 'eval')

        # 检查允许的名称
        for name in code.co_names:
            if name not in allowed_names:
                raise ValueError(f"不允许的名称: {name}")

        return eval(code, {"__builtins__": {}}, allowed_names)


class DocumentRetrievalTool(BaseTool):
    """文档检索工具"""

    name: str = "retrieve_documents"
    description: str = (
        "检索用户上传的文档中与查询相关的内容。"
        "当用户询问文档内容、文件信息、资料查询时使用。"
        "输入是查询语句，输出是相关文档片段。"
    )
    args_schema: Optional[Type] = None

    def __init__(self, rag_service: RAGService, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.rag_service = rag_service
        self.user_id = user_id

    def _run(self, query: str) -> str:
        """执行文档检索"""
        try:
            # 使用RAGService检索相关文档
            context = self.rag_service.build_context(
                query=query,
                user_id=self.user_id,
                top_k=3
            )

            if not context or context == "未检索到可用文档上下文。":
                return "未找到相关文档。"

            # 简化输出，避免过长
            if len(context) > 1000:
                context = context[:1000] + "...(内容截断)"

            return f"找到相关文档：\n{context}"

        except Exception as e:
            return f"文档检索错误: {str(e)}"

    async def _arun(self, query: str) -> str:
        """异步执行文档检索"""
        return self._run(query)


class EvaluationCallTool(BaseTool):
    """评估调用工具"""

    name: str = "call_evaluation"
    description: str = (
        "调用评估服务对用户进行能力评估。"
        "当用户要求评估、需要评分、想了解自己的能力水平时使用。"
        "输入可以是空字符串或具体的评估请求。"
    )
    args_schema: Optional[Type] = None

    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id

    def _run(self, request: str = "") -> str:
        """执行评估调用"""
        try:
            # 获取用户的最近对话历史
            recent_chats = ChatService.get_recent_chats(self.user_id, limit=10)

            # 格式化历史对话
            history_text = "\n".join(
                f"{chat.role}: {chat.content}"
                for chat in recent_chats[-5:]  # 最近5条对话
            ) if recent_chats else "暂无历史对话。"

            # 调用评估服务
            # 注意：这里简化实现，实际可能需要更多上下文
            result = EvaluationService.evaluate_user(
                user_id=self.user_id,
                chat_history=history_text,
                file_context=""  # 暂时不使用文件上下文
            )

            if not result:
                return "评估失败，请稍后重试。"

            # 格式化评估结果
            scores = [
                f"逻辑思维: {result.logic_score}分",
                f"创造力: {result.creativity_score}分",
                f"表达能力: {result.expression_score}分",
                f"知识广度: {result.knowledge_score}分",
                f"综合评分: {result.overall_score}分",
            ]

            feedback = f"\n反馈建议: {result.feedback}"

            return "评估结果：\n" + "\n".join(scores) + feedback

        except Exception as e:
            return f"评估调用错误: {str(e)}"

    async def _arun(self, request: str = "") -> str:
        """异步执行评估调用"""
        return self._run(request)


class SessionManagerTool(BaseTool):
    """会话管理工具"""

    name: str = "manage_session"
    description: str = (
        "管理聊天会话。可以查看会话列表、切换会话、清除会话等。"
        "输入可以是'list'查看会话列表，'clear'清除当前会话等。"
    )
    args_schema: Optional[Type] = None

    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id

    def _run(self, command: str = "") -> str:
        """执行会话管理命令"""
        command = command.strip().lower()

        try:
            if command == "list" or command == "查看会话":
                # 获取用户的所有会话
                sessions = ChatService.get_user_sessions(self.user_id)

                if not sessions:
                    return "您还没有创建任何会话。"

                session_list = []
                for session in sessions:
                    # 获取会话中的消息数量
                    message_count = ChatService.get_session_message_count(session.id)
                    session_list.append(
                        f"- 会话 {session.id}: {session.name or '未命名'} "
                        f"({message_count}条消息, 创建于 {session.created_at})"
                    )

                return "您的会话列表：\n" + "\n".join(session_list)

            elif command == "clear" or command == "清除":
                # 清除当前会话的历史（这里简化处理）
                # 实际实现可能需要指定会话ID
                ChatService.clear_user_history(self.user_id, session_id=None)
                return "对话历史已清除。"

            elif command.startswith("switch") or command.startswith("切换"):
                # 切换会话（这里简化处理）
                # 实际实现需要解析会话ID
                return "切换会话功能需要指定会话ID，例如：'switch 1'"

            else:
                return (
                    "可用命令：\n"
                    "- 'list' 或 '查看会话': 查看所有会话\n"
                    "- 'clear' 或 '清除': 清除当前会话历史\n"
                    "- 'switch <id>' 或 '切换 <id>': 切换到指定会话"
                )

        except Exception as e:
            return f"会话管理错误: {str(e)}"

    async def _arun(self, command: str = "") -> str:
        """异步执行会话管理"""
        return self._run(command)


class EducationAssessmentTool(BaseTool):
    """教育评估专用工具"""

    name: str = "education_assessment"
    description: str = (
        "教育场景专用评估工具。"
        "提供针对青少年的能力评估建议、学习建议、成长规划等。"
        "输入可以是具体的问题，如'如何提高逻辑思维'、'创造力训练方法'等。"
    )
    args_schema: Optional[Type] = None

    def _run(self, question: str) -> str:
        """提供教育评估建议"""
        # 基于问题类型提供不同的建议
        question_lower = question.lower()

        if any(word in question_lower for word in ["逻辑", "思维", "推理"]):
            return (
                "逻辑思维提升建议：\n"
                "1. 练习逻辑推理题和数学题\n"
                "2. 学习编程，培养结构化思维\n"
                "3. 阅读哲学和科学类书籍\n"
                "4. 参与辩论活动，锻炼论证能力\n"
                "5. 玩策略类游戏，如象棋、围棋"
            )

        elif any(word in question_lower for word in ["创造", "创新", "想象力"]):
            return (
                "创造力培养建议：\n"
                "1. 尝试艺术创作，如绘画、写作、音乐\n"
                "2. 进行头脑风暴练习\n"
                "3. 学习设计思维方法\n"
                "4. 接触不同领域的知识，激发跨界灵感\n"
                "5. 保持好奇心，多问'为什么'和'如果'"
            )

        elif any(word in question_lower for word in ["表达", "沟通", "语言"]):
            return (
                "表达能力提升建议：\n"
                "1. 多阅读优秀文学作品\n"
                "2. 练习写作，从日记开始\n"
                "3. 参加演讲或朗诵活动\n"
                "4. 学习结构化表达（结论先行，分点论述）\n"
                "5. 录制自己的讲话，回听改进"
            )

        elif any(word in question_lower for word in ["知识", "学习", "掌握"]):
            return (
                "知识广度拓展建议：\n"
                "1. 建立跨学科知识体系\n"
                "2. 定期阅读科普书籍和文章\n"
                "3. 观看高质量纪录片\n"
                "4. 参与讨论组或读书会\n"
                "5. 将所学知识教给他人（费曼学习法）"
            )

        else:
            return (
                "青少年综合能力发展建议：\n"
                "1. 保持均衡发展，不要偏科\n"
                "2. 培养自主学习能力\n"
                "3. 注重实践应用，学以致用\n"
                "4. 建立成长型思维，勇于尝试\n"
                "5. 保持身心健康，合理安排时间"
            )

    async def _arun(self, question: str) -> str:
        """异步提供教育评估建议"""
        return self._run(question)


class EnhancedToolFactory:
    """增强版工具工厂"""

    @staticmethod
    def create_basic_tools() -> List[BaseTool]:
        """创建基础工具集"""
        return [
            TimeTool(),
            CalculatorTool(),
        ]

    @staticmethod
    def create_user_tools(
        user_id: int,
        rag_service: Optional[RAGService] = None
    ) -> List[BaseTool]:
        """创建用户专用工具集"""
        tools = [
            TimeTool(),
            CalculatorTool(),
            EducationAssessmentTool(),
        ]

        # 添加需要RAG服务的工具
        if rag_service:
            tools.append(
                DocumentRetrievalTool(
                    rag_service=rag_service,
                    user_id=user_id
                )
            )

        # 添加评估和会话管理工具
        tools.extend([
            EvaluationCallTool(user_id=user_id),
            SessionManagerTool(user_id=user_id),
        ])

        return tools

    @staticmethod
    def create_all_tools(
        user_id: int,
        rag_service: Optional[RAGService] = None
    ) -> List[BaseTool]:
        """创建所有可用工具"""
        return EnhancedToolFactory.create_user_tools(user_id, rag_service)


# 使用@tool装饰器的简化版本（如果需要）
@tool
def get_current_time_tool(query: str = "") -> str:
    """获取当前时间的简化工具版本"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@tool
def simple_calculator_tool(expression: str) -> str:
    """简化计算器工具"""
    try:
        # 只支持简单的四则运算
        # 注意：实际使用需要更安全的方法
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"
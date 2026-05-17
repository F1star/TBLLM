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

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Type

from pydantic import PrivateAttr
from langchain_core.tools import BaseTool, StructuredTool
from langchain.tools import tool

from services.rag_service import RAGService
from services.chat_service import ChatService
from services.evaluation_service import EvaluationService
from services.session_service import SessionService
from db_models.chat_history import ChatHistory


def _clean_history_content(content: str) -> str:
    """清理历史消息中曾经泄露的括号式内部说明。"""
    text = re.sub(r"\s+", " ", content or "").strip()
    if not text:
        return ""

    meta_terms = (
        "根据用户的输入", "提供相应的答案", "如果学生", "不需回答", "无需回答",
        "请礼貌", "系统", "提示", "备注", "内部", "写作意图", "对话策略",
    )
    term_pattern = "|".join(re.escape(term) for term in meta_terms)
    text = re.sub(rf"（[^（）]{{0,160}}(?:{term_pattern})[^（）]{{0,160}}）", "", text)
    text = re.sub(rf"\([^()]{{0,160}}(?:{term_pattern})[^()]{{0,160}}\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _clip_text(text: str, max_chars: int) -> str:
    """截断展示文本，明确标出省略，避免日志/证据看起来像半句话。"""
    cleaned = _clean_history_content(text)
    if len(cleaned) <= max_chars:
        return cleaned
    clipped = cleaned[:max_chars].rstrip()
    last_punctuation = max(clipped.rfind(mark) for mark in "。！？；.!?;")
    if last_punctuation >= max_chars // 2:
        clipped = clipped[:last_punctuation + 1]
    return f"{clipped}...[已截断]"


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




class DocumentRetrievalTool(BaseTool):
    """文档检索工具"""

    name: str = "retrieve_documents"
    description: str = (
        "检索用户上传的文档中与查询相关的内容。"
        "当用户询问文档内容、文件信息、资料查询时使用。"
        "输入是查询语句，输出是相关文档片段。"
    )
    args_schema: Optional[Type] = None
    _rag_service: RAGService = PrivateAttr()
    _user_id: int = PrivateAttr(default=0)

    def __init__(self, rag_service: RAGService, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self._rag_service = rag_service
        self._user_id = user_id

    def set_user_id(self, user_id: int):
        """设置当前用户ID，用于复用同一个Agent工具实例。"""
        self._user_id = user_id

    def _run(self, query: str) -> str:
        """执行文档检索"""
        try:
            # 使用RAGService检索相关文档
            context = self._rag_service.build_context(
                query=query,
                user_id=self._user_id,
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
    _user_id: int = PrivateAttr(default=0)

    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self._user_id = user_id

    def _run(self, request: str = "") -> str:
        """执行评估调用"""
        try:
            # 获取用户的最近对话历史
            recent_chats = ChatService.get_recent_chats(self._user_id, limit=10)

            # 格式化历史对话
            history_text = "\n".join(
                f"{chat.role}: {chat.content}"
                for chat in recent_chats[-5:]  # 最近5条对话
            ) if recent_chats else "暂无历史对话。"

            # 调用评估服务
            # 注意：这里简化实现，实际可能需要更多上下文
            result = EvaluationService.evaluate_user(
                user_id=self._user_id,
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
    _user_id: int = PrivateAttr(default=0)

    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self._user_id = user_id

    def _run(self, command: str = "") -> str:
        """执行会话管理命令"""
        command = command.strip().lower()

        try:
            if command == "list" or command == "查看会话":
                # 获取用户的所有会话
                sessions = ChatService.get_user_sessions(self._user_id)

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
                ChatService.clear_user_history(self._user_id, session_id=None)
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


class FileSummaryTool(BaseTool):
    """获取已上传文件信息并进行总结"""

    name: str = "file_summary"
    description: str = (
        "获取用户已上传的文件列表和内容摘要。"
        "当用户询问上传了哪些文件、文件内容是什么、文件总结时使用。"
        "输入可以是空字符串获取全部文件概要，或指定具体问题来筛选文件内容。"
    )
    args_schema: Optional[Type] = None
    _user_id: int = 0

    def set_user_id(self, user_id: int):
        """设置用户ID"""
        self._user_id = user_id

    def _run(self, query: str = "") -> str:
        """获取文件信息并总结"""
        try:
            from services.file_service import FileService
            from config.settings import db

            files = FileService.get_user_files(self._user_id)
            if not files:
                return "您还没有上传任何文件。"

            lines = []
            for f in files:
                file_info = f"- {f.filename}（上传于 {f.upload_time.strftime('%Y-%m-%d %H:%M') if hasattr(f.upload_time, 'strftime') else f.upload_time}）"
                lines.append(file_info)

                # 解析文件内容并生成摘要
                try:
                    text = FileService.parse_file(f.filepath, self._user_id)
                    if text and len(text) > 20:
                        # 取前200字作为摘要
                        summary = _clip_text(text.replace('\n', ' '), 220)
                        lines.append(f"  摘要：{summary}")
                    else:
                        lines.append("  摘要：文件内容为空或无法解析")
                except Exception as e:
                    lines.append(f"  摘要：读取失败（{str(e)}）")

            return "您已上传的文件：\n" + "\n".join(lines)

        except Exception as e:
            return f"获取文件信息失败: {str(e)}"

    async def _arun(self, query: str = "") -> str:
        """异步执行"""
        return self._run(query)


class SessionHistoryTool(BaseTool):
    """获取当前会话的聊天历史"""

    name: str = "session_history"
    description: str = (
        "获取当前会话的聊天历史记录。"
        "当用户询问之前说了什么、需要回顾对话内容时使用。"
        "输入可以是空字符串获取完整历史，或指定查询关键词筛选相关对话。"
    )
    args_schema: Optional[Type] = None
    _user_id: int = 0
    _session_id: Optional[int] = None

    def set_user_id(self, user_id: int):
        self._user_id = user_id

    def set_session_id(self, session_id: Optional[int]):
        self._session_id = session_id

    def _run(self, query: str = "") -> str:
        """获取当前会话的聊天历史"""
        try:
            history = ChatService.get_user_history(self._user_id, session_id=self._session_id)
            if not history:
                return "当前会话暂无聊天记录。"

            lines = []
            for msg in history[-30:]:  # 最近30条
                role = "用户" if msg["role"] == "user" else "AI助手"
                content = _clip_text(msg.get("content", ""), 420)
                if content:
                    lines.append(f"{role}: {content}")

            result = "\n".join(lines)
            prefix = f"当前会话历史（共{len(history)}条）：\n"
            if query and len(query) > 2:
                # 简单关键词筛选
                filtered = [l for l in lines if query.lower() in l.lower()]
                if filtered:
                    result = "\n".join(filtered)
                    prefix = f"与「{query}」相关的会话历史（共{len(filtered)}条）：\n"
                else:
                    return f"未找到与「{query}」相关的对话内容。"

            return prefix + result

        except Exception as e:
            return f"获取会话历史失败: {str(e)}"

    async def _arun(self, query: str = "") -> str:
        return self._run(query)


class AllSessionsHistoryTool(BaseTool):
    """获取用户所有会话的全部聊天历史"""

    name: str = "all_history"
    description: str = (
        "获取用户所有会话的全部聊天历史记录。"
        "当需要全面了解用户的所有对话、进行综合评估时使用。"
        "输入可以是空字符串获取全部历史，或指定查询关键词。"
    )
    args_schema: Optional[Type] = None
    _user_id: int = 0

    def set_user_id(self, user_id: int):
        self._user_id = user_id

    def _run(self, query: str = "") -> str:
        """获取所有会话的聊天历史"""
        try:
            history = ChatService.get_user_history(self._user_id)
            if not history:
                return "暂无任何会话的聊天记录。"

            # 按会话ID分组
            from collections import defaultdict
            sessions: dict = defaultdict(list)
            for msg in history:
                raw_sid = msg.get("session_id")
                sid = str(raw_sid) if raw_sid is not None else "未分组"
                sessions[sid].append(msg)

            lines = []
            total = len(history)
            user_total = sum(1 for msg in history if msg.get("role") == "user")
            lines.append(f"用户共有 {len(sessions)} 个会话，总计 {total} 条消息，其中用户消息 {user_total} 条。以下仅列出用户侧证据。\n")

            # 按数字排序（会话ID），"未分组"排最后
            def sort_key(sid):
                try:
                    return (0, int(sid))
                except ValueError:
                    return (1, sid)

            for sid, msgs in sorted(sessions.items(), key=lambda x: sort_key(x[0])):
                user_msgs = [msg for msg in msgs if msg.get("role") == "user"]
                if not user_msgs:
                    continue
                session_label = f"会话 {sid}" if sid != "未分组" else "未分组历史"
                lines.append(f"【{session_label}】（用户消息{len(user_msgs)}条）")
                for msg in user_msgs[-10:]:  # 每个会话最近10条用户消息
                    content = _clip_text(msg.get("content", ""), 260)
                    if content:
                        lines.append(f"  用户: {content}")
                lines.append("")

            result = "\n".join(lines)

            if query and len(query) > 2:
                filtered = [l for l in lines if query.lower() in l.lower()]
                if filtered:
                    result = "\n".join(filtered)
                else:
                    return f"未找到与「{query}」相关的对话内容。"

            return result

        except Exception as e:
            return f"获取全部会话历史失败: {str(e)}"

    async def _arun(self, query: str = "") -> str:
        return self._run(query)


class EnhancedToolFactory:
    """增强版工具工厂"""

    @staticmethod
    def create_basic_tools(file_summary_tool: Optional[FileSummaryTool] = None) -> List[BaseTool]:
        """创建基础工具集"""
        tools: List[BaseTool] = []
        if file_summary_tool:
            tools.append(file_summary_tool)
        else:
            tools.append(FileSummaryTool())
        return tools

    @staticmethod
    def create_user_tools(
        user_id: int,
        rag_service: Optional[RAGService] = None
    ) -> List[BaseTool]:
        """创建用户专用工具集"""
        tools = [
            FileSummaryTool(),
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

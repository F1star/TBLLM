from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from langchain_core.tools import StructuredTool

from services.rag_service import RAGService


class AgentToolFactory:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service

    def build_tools(self, user_id: int, file_ids: Optional[Iterable[int]] = None):
        def get_current_time(query: str = "") -> str:
            """返回当前本地时间。适合处理时间、日期、今天、现在等问题。"""

            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def retrieve_user_documents(query: str) -> str:
            """检索用户已上传文档中与问题最相关的内容，供智能体回答时参考。"""

            return self.rag_service.build_context(
                query=query,
                user_id=user_id,
                file_ids=file_ids,
                top_k=3,
            )

        return [
            StructuredTool.from_function(get_current_time),
            StructuredTool.from_function(retrieve_user_documents),
        ]

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, List, Optional

from services.file_service import FileService


class RAGService:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def retrieve(
        self,
        query: str,
        user_id: int,
        file_ids: Optional[Iterable[int]] = None,
        top_k: int = 3,
    ) -> List[dict]:
        files = self._resolve_files(user_id, file_ids)
        if not files:
            return []

        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        scored_chunks = []
        for file in files:
            content = FileService.parse_file(file.filepath, user_id)
            for index, chunk in enumerate(self._split_text(content)):
                score = self._score_chunk(chunk, query_terms)
                if score <= 0:
                    continue
                scored_chunks.append(
                    {
                        "file_id": file.id,
                        "filename": file.filename,
                        "chunk_index": index,
                        "score": score,
                        "content": chunk,
                    }
                )

        scored_chunks.sort(key=lambda item: item["score"], reverse=True)
        return scored_chunks[:top_k]

    def build_context(
        self,
        query: str,
        user_id: int,
        file_ids: Optional[Iterable[int]] = None,
        top_k: int = 3,
    ) -> str:
        chunks = self.retrieve(query, user_id, file_ids=file_ids, top_k=top_k)
        if not chunks:
            return "未检索到可用文档上下文。"

        return "\n\n".join(
            f"[文件: {item['filename']} | 分片: {item['chunk_index']}]\n{item['content']}"
            for item in chunks
        )

    def _resolve_files(self, user_id: int, file_ids: Optional[Iterable[int]]) -> List:
        if file_ids:
            files = []
            for file_id in file_ids:
                file = FileService.get_file_by_id(int(file_id), user_id)
                if file:
                    files.append(file)
            return files
        return FileService.get_user_files(user_id)

    def _split_text(self, text: str) -> List[str]:
        normalized = re.sub(r"\s+", " ", text or "").strip()
        if not normalized:
            return []

        if len(normalized) <= self.chunk_size:
            return [normalized]

        chunks = []
        step = max(self.chunk_size - self.chunk_overlap, 1)
        for start in range(0, len(normalized), step):
            chunk = normalized[start : start + self.chunk_size].strip()
            if chunk:
                chunks.append(chunk)
            if start + self.chunk_size >= len(normalized):
                break
        return chunks

    def _tokenize(self, text: str) -> List[str]:
        return [token for token in re.findall(r"[\w\u4e00-\u9fff]+", text.lower()) if token]

    def _score_chunk(self, chunk: str, query_terms: List[str]) -> float:
        chunk_terms = self._tokenize(chunk)
        if not chunk_terms:
            return 0.0

        counts = Counter(chunk_terms)
        score = 0.0
        for term in query_terms:
            if term in counts:
                score += counts[term] / math.sqrt(len(chunk_terms))
        return score

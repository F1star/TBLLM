from __future__ import annotations

import math
import re
import logging
from collections import Counter
from datetime import datetime
from typing import Iterable, List, Optional, Dict, Any, Tuple

from config.constants import USE_VECTOR_RETRIEVAL, RAG_TOP_K, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP
from services.file_service import FileService

# 尝试导入VectorStore，如果失败则使用降级方案
try:
    from services.vector_store import get_vector_store, Document
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    logging.warning("VectorStore不可用，将使用关键词检索模式")

# 设置日志
logger = logging.getLogger(__name__)


class RAGService:
    # 系统用户ID（用于存储系统级文献）
    SYSTEM_USER_ID = 0
    def __init__(self, chunk_size: int = RAG_CHUNK_SIZE, chunk_overlap: int = RAG_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 向量检索相关
        self.use_vector_retrieval = USE_VECTOR_RETRIEVAL and VECTOR_STORE_AVAILABLE
        if self.use_vector_retrieval:
            try:
                self.vector_store = get_vector_store()
                logger.info("RAGService已启用向量检索模式")
            except Exception as e:
                logger.error(f"向量存储初始化失败，将使用关键词检索: {str(e)}")
                self.use_vector_retrieval = False
        else:
            self.vector_store = None
            logger.info("RAGService使用关键词检索模式")

    def retrieve(
        self,
        query: str,
        user_id: int,
        file_ids: Optional[Iterable[int]] = None,
        top_k: int = RAG_TOP_K,
    ) -> List[dict]:
        """
        检索相关文档片段，支持向量检索和关键词检索两种模式

        Args:
            query: 查询文本
            user_id: 用户ID
            file_ids: 指定的文件ID列表（可选）
            top_k: 返回结果数量

        Returns:
            文档片段列表，每个片段包含文件信息和相关性分数
        """
        # 如果启用向量检索且向量存储可用，尝试使用向量检索
        if self.use_vector_retrieval and self.vector_store:
            try:
                vector_results = self._retrieve_with_vectors(query, user_id, top_k)
                if vector_results:
                    logger.debug(f"向量检索返回 {len(vector_results)} 个结果")
                    return vector_results
                else:
                    logger.debug("向量检索未返回结果，回退到关键词检索")
            except Exception as e:
                logger.warning(f"向量检索失败，回退到关键词检索: {str(e)}")

        # 回退到关键词检索
        return self._retrieve_with_keywords(query, user_id, file_ids, top_k)

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

    def _retrieve_with_vectors(
        self,
        query: str,
        user_id: int,
        top_k: int = RAG_TOP_K
    ) -> List[dict]:
        """
        使用向量存储进行语义检索
        同时搜索系统用户（ID=0）和当前用户的向量存储，使系统文档对所有用户可见

        Args:
            query: 查询文本
            user_id: 用户ID
            top_k: 返回结果数量

        Returns:
            文档片段列表
        """
        try:
            all_chunks = []

            # 搜索当前用户的向量存储
            user_results = self.vector_store.search(
                user_id=user_id,
                query=query,
                top_k=top_k
            )

            # 搜索系统用户的向量存储（系统文档）
            if user_id != self.SYSTEM_USER_ID:
                system_results = self.vector_store.search(
                    user_id=self.SYSTEM_USER_ID,
                    query=query,
                    top_k=top_k
                )
            else:
                system_results = []  # 如果当前用户就是系统用户，避免重复搜索

            # 处理当前用户的结果
            for i, (document, similarity) in enumerate(user_results):
                metadata = document.metadata
                file_id = metadata.get("file_id", "unknown")
                filename = metadata.get("filename", "未知文件")
                chunk_index = metadata.get("chunk_index", i)

                all_chunks.append({
                    "file_id": file_id,
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "score": similarity * 100,  # 转换为百分制分数
                    "content": document.content,
                    "retrieval_method": "vector",
                    "source": "user"  # 标记来源
                })

            # 处理系统用户的结果
            for i, (document, similarity) in enumerate(system_results):
                metadata = document.metadata
                file_id = metadata.get("file_id", "unknown")
                filename = metadata.get("filename", "未知文件")
                chunk_index = metadata.get("chunk_index", i)

                all_chunks.append({
                    "file_id": file_id,
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "score": similarity * 100,  # 转换为百分制分数
                    "content": document.content,
                    "retrieval_method": "vector",
                    "source": "system"  # 标记来源
                })

            if not all_chunks:
                return []

            # 按分数排序
            all_chunks.sort(key=lambda item: item["score"], reverse=True)

            # 去重：基于文件ID和分片索引去除重复片段
            unique_chunks = []
            seen_keys = set()
            for chunk in all_chunks:
                key = f"{chunk['file_id']}_{chunk['chunk_index']}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_chunks.append(chunk)

            # 取前top_k个结果
            result_chunks = unique_chunks[:top_k]
            logger.debug(f"向量检索到 {len(result_chunks)} 个相关片段（用户: {user_id}，系统: {self.SYSTEM_USER_ID}）")
            return result_chunks

        except Exception as e:
            logger.error(f"向量检索失败: {str(e)}")
            return []

    def _retrieve_with_keywords(
        self,
        query: str,
        user_id: int,
        file_ids: Optional[Iterable[int]] = None,
        top_k: int = RAG_TOP_K,
    ) -> List[dict]:
        """
        使用关键词匹配进行检索（原检索逻辑）

        Args:
            query: 查询文本
            user_id: 用户ID
            file_ids: 指定的文件ID列表（可选）
            top_k: 返回结果数量

        Returns:
            文档片段列表
        """
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
                        "retrieval_method": "keyword"
                    }
                )

        scored_chunks.sort(key=lambda item: item["score"], reverse=True)
        logger.debug(f"关键词检索到 {len(scored_chunks[:top_k])} 个相关片段")
        return scored_chunks[:top_k]

    def add_documents_to_vector_store(
        self,
        user_id: int,
        file_id: int,
        filename: str,
        text_content: str
    ) -> bool:
        """
        将文档内容添加到向量存储

        Args:
            user_id: 用户ID
            file_id: 文件ID
            filename: 文件名
            text_content: 文本内容

        Returns:
            是否成功
        """
        if not self.use_vector_retrieval or not self.vector_store:
            logger.warning("向量存储不可用，跳过文档添加")
            return False

        try:
            # 准备元数据
            metadata = {
                "user_id": user_id,
                "file_id": str(file_id),  # 转换为字符串以确保类型一致性
                "filename": filename,
                "source": "file_upload",
                "added_at": datetime.now().isoformat()
            }

            # 准备文档
            documents = self.vector_store.prepare_documents_for_user(
                user_id=user_id,
                text=text_content,
                metadata=metadata
            )

            # 添加到向量存储
            doc_ids = self.vector_store.add_documents(
                user_id=user_id,
                documents=documents
            )

            logger.info(f"已将文件 {filename} (ID: {file_id}) 添加到用户 {user_id} 的向量存储，共 {len(doc_ids)} 个片段")
            return True

        except Exception as e:
            logger.error(f"文档添加到向量存储失败: {str(e)}")
            return False

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

    def delete_file_from_vector_store(self, user_id: int, file_id: int) -> bool:
        """
        从向量存储中删除指定文件的所有文档片段

        Args:
            user_id: 用户ID
            file_id: 文件ID

        Returns:
            是否成功
        """
        if not self.use_vector_retrieval or not self.vector_store:
            logger.warning("向量存储不可用，跳过文件删除")
            return False

        try:
            # 搜索该文件的所有文档片段
            # 注意：这里需要VectorStore支持按元数据过滤搜索
            # 目前我们假设VectorStore的search方法支持filter_metadata参数
            results = self.vector_store.search(
                user_id=user_id,
                query="",  # 空查询，只用于过滤
                top_k=1000,  # 设置一个较大的值，确保获取所有片段
                filter_metadata={"file_id": str(file_id)}
            )

            if not results:
                logger.info(f"向量存储中未找到文件 {file_id} 的文档片段")
                return True

            # 提取文档ID
            doc_ids = []
            for document, similarity in results:
                doc_ids.append(document.id)

            # 批量删除
            success = self.vector_store.delete_documents(user_id, doc_ids)
            if success:
                logger.info(f"已从向量存储中删除文件 {file_id} 的 {len(doc_ids)} 个文档片段")
            else:
                logger.warning(f"向量存储删除文档片段失败")

            return success

        except Exception as e:
            logger.error(f"从向量存储删除文件时发生错误: {str(e)}")
            return False

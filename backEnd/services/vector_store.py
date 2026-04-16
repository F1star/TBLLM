"""
向量存储服务 - 基于ChromaDB的文档向量化存储和检索

这个模块提供了基于ChromaDB向量数据库的文档存储和语义检索功能，
支持中文文本的嵌入向量生成和相似度检索。

主要功能：
1. 文档向量化存储
2. 语义相似度检索
3. 用户隔离的数据管理
4. 持久化存储
"""

from __future__ import annotations

import os
import shutil
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config.constants import (
    VECTOR_STORE_PATH,
    EMBEDDING_MODEL_NAME,
    CHROMA_COLLECTION_NAME,
    RAG_TOP_K,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP
)

# 设置日志
logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档数据类"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class VectorStore:
    """向量存储服务"""

    def __init__(
        self,
        persist_directory: str = VECTOR_STORE_PATH,
        embedding_model_name: str = EMBEDDING_MODEL_NAME,
        collection_name: str = CHROMA_COLLECTION_NAME
    ):
        """
        初始化向量存储服务

        Args:
            persist_directory: 持久化存储目录
            embedding_model_name: 嵌入模型名称
            collection_name: ChromaDB集合名称
        """
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model_name
        self.collection_name = collection_name

        # 创建存储目录
        os.makedirs(persist_directory, exist_ok=True)

        # 初始化嵌入模型（惰性加载）
        self._embedding_model = None

        # 初始化ChromaDB客户端
        self._chroma_client = None
        self._collection = None

        logger.info(f"VectorStore初始化完成，存储路径: {persist_directory}")

    @property
    def embedding_model(self) -> SentenceTransformer:
        """获取嵌入模型（惰性加载）"""
        if self._embedding_model is None:
            try:
                logger.info(f"加载嵌入模型: {self.embedding_model_name}")
                self._embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info("嵌入模型加载完成")
            except Exception as e:
                logger.error(f"嵌入模型加载失败: {str(e)}")
                raise
        return self._embedding_model

    @property
    def chroma_client(self) -> chromadb.Client:
        """获取ChromaDB客户端"""
        if self._chroma_client is None:
            try:
                self._chroma_client = chromadb.Client(
                    Settings(
                        persist_directory=self.persist_directory,
                        anonymized_telemetry=False
                    )
                )
                logger.debug("ChromaDB客户端初始化完成")
            except Exception as e:
                logger.error(f"ChromaDB客户端初始化失败: {str(e)}")
                raise
        return self._chroma_client

    @property
    def collection(self) -> chromadb.Collection:
        """获取或创建集合"""
        if self._collection is None:
            try:
                # 尝试获取现有集合，不存在则创建
                self._collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "用户文档向量存储"}
                )
                logger.debug(f"集合 '{self.collection_name}' 已就绪")
            except Exception as e:
                logger.error(f"集合获取/创建失败: {str(e)}")
                raise
        return self._collection

    def get_user_collection(self, user_id: int) -> chromadb.Collection:
        """
        获取用户专属的集合（用户隔离存储）

        Args:
            user_id: 用户ID

        Returns:
            ChromaDB集合实例
        """
        collection_name = f"{self.collection_name}_user_{user_id}"
        try:
            return self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "description": f"用户 {user_id} 的文档向量存储",
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"用户集合获取/创建失败: {str(e)}")
            raise

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        为文本列表创建嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        if not texts:
            return []

        try:
            # 使用sentence-transformers生成嵌入向量
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=False,
                normalize_embeddings=True
            )

            # 转换为列表格式
            embeddings_list = embeddings.tolist()
            logger.debug(f"为 {len(texts)} 个文本创建了嵌入向量")
            return embeddings_list

        except Exception as e:
            logger.error(f"嵌入向量创建失败: {str(e)}")
            raise

    def add_documents(
        self,
        user_id: int,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        添加文档到向量存储

        Args:
            user_id: 用户ID
            documents: 文档列表
            batch_size: 批处理大小

        Returns:
            文档ID列表
        """
        if not documents:
            return []

        try:
            collection = self.get_user_collection(user_id)

            # 准备数据
            ids = []
            texts = []
            metadatas = []

            for doc in documents:
                ids.append(doc.id)
                texts.append(doc.content)
                metadatas.append(doc.metadata)

            # 分批添加
            doc_ids = []
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]

                # 创建嵌入向量
                batch_embeddings = self.create_embeddings(batch_texts)

                # 添加到集合
                collection.add(
                    embeddings=batch_embeddings,
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )

                doc_ids.extend(batch_ids)
                logger.debug(f"添加了 {len(batch_ids)} 个文档到用户 {user_id} 的向量存储")

            logger.info(f"成功添加 {len(doc_ids)} 个文档到用户 {user_id} 的向量存储")
            return doc_ids

        except Exception as e:
            logger.error(f"文档添加失败: {str(e)}")
            raise

    def search(
        self,
        user_id: int,
        query: str,
        top_k: int = RAG_TOP_K,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        语义搜索文档

        Args:
            user_id: 用户ID
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤器

        Returns:
            文档和相似度得分列表
        """
        try:
            collection = self.get_user_collection(user_id)

            # 创建查询嵌入向量
            query_embedding = self.create_embeddings([query])[0]

            # 执行查询
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )

            # 解析结果
            documents = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    doc_id = results["ids"][0][i] if results["ids"] else f"result_{i}"
                    content = results["documents"][0][i]
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0

                    # 转换距离为相似度得分（距离越小，相似度越高）
                    similarity = 1.0 / (1.0 + distance) if distance > 0 else 1.0

                    document = Document(
                        id=doc_id,
                        content=content,
                        metadata=metadata,
                        embedding=None  # 不返回嵌入向量以节省内存
                    )
                    documents.append((document, similarity))

            logger.debug(f"用户 {user_id} 的查询 '{query[:50]}...' 返回 {len(documents)} 个结果")
            return documents

        except Exception as e:
            logger.error(f"文档搜索失败: {str(e)}")
            return []

    def delete_documents(self, user_id: int, document_ids: List[str]) -> bool:
        """
        删除文档

        Args:
            user_id: 用户ID
            document_ids: 文档ID列表

        Returns:
            是否成功
        """
        try:
            collection = self.get_user_collection(user_id)
            collection.delete(ids=document_ids)
            logger.info(f"从用户 {user_id} 的向量存储中删除了 {len(document_ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"文档删除失败: {str(e)}")
            return False

    def get_collection_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取集合统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        try:
            collection = self.get_user_collection(user_id)
            count = collection.count()

            return {
                "user_id": user_id,
                "collection_name": collection.name,
                "document_count": count,
                "metadata": collection.metadata
            }
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {str(e)}")
            return {}

    def clear_user_data(self, user_id: int) -> bool:
        """
        清除用户的所有向量数据

        Args:
            user_id: 用户ID

        Returns:
            是否成功
        """
        try:
            collection_name = f"{self.collection_name}_user_{user_id}"
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"已清除用户 {user_id} 的所有向量数据")
            return True
        except Exception as e:
            logger.error(f"清除用户数据失败: {str(e)}")
            return False

    def text_splitter(self, text: str, chunk_size: int = RAG_CHUNK_SIZE,
                     chunk_overlap: int = RAG_CHUNK_OVERLAP) -> List[str]:
        """
        中文友好的文本分割器

        Args:
            text: 输入文本
            chunk_size: 块大小
            chunk_overlap: 块重叠大小

        Returns:
            文本块列表
        """
        if not text:
            return []

        # 简单的中文文本分割（可按句子或标点分割）
        sentences = []
        current_sentence = ""

        for char in text:
            current_sentence += char
            # 中文句子结束标点
            if char in {'。', '！', '？', '\n', '；', '，'} and len(current_sentence) >= 50:
                sentences.append(current_sentence.strip())
                current_sentence = ""

        if current_sentence:
            sentences.append(current_sentence.strip())

        # 如果句子分割效果不好，按字符长度分割
        if not sentences or max(len(s) for s in sentences) > chunk_size * 2:
            sentences = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]

        # 清理空字符串
        sentences = [s for s in sentences if s.strip()]

        return sentences

    def prepare_documents_for_user(
        self,
        user_id: int,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: int = RAG_CHUNK_SIZE,
        chunk_overlap: int = RAG_CHUNK_OVERLAP
    ) -> List[Document]:
        """
        为用户准备文档（文本分割和元数据添加）

        Args:
            user_id: 用户ID
            text: 原始文本
            metadata: 基础元数据
            chunk_size: 块大小
            chunk_overlap: 块重叠大小

        Returns:
            文档列表
        """
        # 分割文本
        chunks = self.text_splitter(text, chunk_size, chunk_overlap)

        documents = []
        for i, chunk in enumerate(chunks):
            # 为每个块创建唯一ID
            doc_id = f"user_{user_id}_doc_{metadata.get('file_id', 'unknown')}_chunk_{i}"

            # 复制并扩展元数据
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "created_at": datetime.now().isoformat()
            })

            documents.append(Document(
                id=doc_id,
                content=chunk,
                metadata=chunk_metadata
            ))

        return documents


# 单例模式
_vector_store_instance = None

def get_vector_store() -> VectorStore:
    """获取VectorStore单例实例"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
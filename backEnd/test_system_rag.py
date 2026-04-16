#!/usr/bin/env python3
"""
测试系统文档RAG检索功能
"""

import sys
import os
import logging

# 设置日志级别
logging.basicConfig(level=logging.WARNING)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import RAGService
from services.vector_store import get_vector_store

def test_system_document_retrieval():
    """测试系统文档检索"""
    print("测试系统文档RAG检索...")

    # 创建RAGService实例
    rag_service = RAGService()

    # 检查向量检索是否可用
    print(f"use_vector_retrieval: {rag_service.use_vector_retrieval}")
    print(f"vector_store: {rag_service.vector_store}")

    if not rag_service.use_vector_retrieval or not rag_service.vector_store:
        print("警告: 向量检索不可用，跳过测试")
        return

    print(f"向量检索模式: {'已启用' if rag_service.use_vector_retrieval else '未启用'}")
    print(f"系统用户ID: {RAGService.SYSTEM_USER_ID}")

    # 检查向量存储统计信息
    try:
        vector_store = get_vector_store()
        system_stats = vector_store.get_collection_stats(RAGService.SYSTEM_USER_ID)
        print(f"系统用户集合统计: {system_stats}")

        user_stats = vector_store.get_collection_stats(1)  # 用户ID=1的集合（应该为空）
        print(f"用户1集合统计: {user_stats}")
    except Exception as e:
        print(f"获取集合统计失败: {e}")

    # 测试查询（模拟用户ID=1）
    test_queries = [
        "青少年",
        "创新能力",
        "社会情感能力",
        "测评技术",
        "测量指标",
    ]

    for query in test_queries:
        print(f"\n查询: '{query}'")
        try:
            # 直接使用向量检索，避免数据库依赖
            results = rag_service._retrieve_with_vectors(query, user_id=1, top_k=3)

            if not results:
                print("  未找到相关文档")
                continue

            for i, result in enumerate(results):
                source = result.get('source', 'unknown')
                print(f"  结果 {i+1} (来源: {source}):")
                print(f"    文件: {result['filename']}")
                print(f"    分片: {result['chunk_index']}")
                print(f"    分数: {result['score']:.2f}")
                print(f"    内容预览: {result['content'][:100]}...")

        except Exception as e:
            print(f"  检索失败: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n测试完成")

if __name__ == "__main__":
    test_system_document_retrieval()
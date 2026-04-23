#!/usr/bin/env python3
"""
将系统级文献添加到RAG向量存储

这个脚本扫描./data/目录下的PDF文件，将其内容添加到向量存储中，
作为系统级文献供所有用户检索使用。

用法:
    python add_system_docs.py
"""

import os
import sys
import logging
from pathlib import Path

# 项目根目录
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent  # backEnd/
PROJECT_ROOT = BACKEND_DIR.parent  # 项目根目录

# 添加backEnd目录到Python路径
sys.path.insert(0, str(BACKEND_DIR))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_system_documents():
    """添加系统文档到向量存储"""

    # 基础路径
    base_dir = PROJECT_ROOT  # 项目根目录
    data_dir = base_dir / "data"

    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return False

    # 查找PDF文件（只扫描data目录根目录，不包含子目录）
    pdf_files = []

    # 查找data目录根目录下的所有PDF文件
    for ext in ['*.pdf', '*.PDF']:
        pdf_files.extend(list(data_dir.glob(ext)))

    # 去除重复（不同大小写可能被视为不同文件）
    # 使用文件路径的绝对路径进行去重
    unique_files = {}
    for pdf_file in pdf_files:
        abs_path = str(pdf_file.absolute())
        # 使用小写路径作为键，避免大小写重复
        key = abs_path.lower()
        if key not in unique_files:
            unique_files[key] = pdf_file

    pdf_files = list(unique_files.values())

    if not pdf_files:
        logger.warning(f"在 {data_dir} 中未找到PDF文件")
        return False

    logger.info(f"找到 {len(pdf_files)} 个PDF文件")

    # 导入服务（在这里导入以避免循环依赖）
    try:
        from services.file_service import FileService
        from services.rag_service import RAGService
        from config.constants import USE_VECTOR_RETRIEVAL
    except ImportError as e:
        logger.error(f"导入服务失败: {e}")
        return False

    # 检查向量检索是否启用
    if not USE_VECTOR_RETRIEVAL:
        logger.warning("向量检索未启用 (USE_VECTOR_RETRIEVAL=False)，跳过添加系统文档")
        return False

    # 创建RAGService实例
    rag_service = RAGService()

    if not rag_service.use_vector_retrieval:
        logger.warning("RAGService未启用向量检索，跳过添加系统文档")
        return False

    # 系统用户ID（0表示系统用户）
    SYSTEM_USER_ID = 0

    success_count = 0
    fail_count = 0

    for pdf_file in pdf_files:
        try:
            logger.info(f"处理文件: {pdf_file.name}")

            # 生成文件ID（使用文件路径的哈希值）
            file_id = abs(hash(str(pdf_file))) % 1000000

            # 解析文件内容
            logger.debug(f"解析文件内容: {pdf_file}")
            text_content = FileService.parse_file(str(pdf_file), user_id=None)

            if not text_content or text_content.startswith("解析") and "失败" in text_content:
                logger.warning(f"文件解析失败或内容为空: {pdf_file.name}")
                fail_count += 1
                continue

            # 添加到向量存储
            logger.debug(f"添加到向量存储，文件ID: {file_id}")
            success = rag_service.add_documents_to_vector_store(
                user_id=SYSTEM_USER_ID,
                file_id=file_id,
                filename=pdf_file.name,
                text_content=text_content
            )

            if success:
                logger.info(f"成功添加: {pdf_file.name}")
                success_count += 1
            else:
                logger.warning(f"添加失败: {pdf_file.name}")
                fail_count += 1

        except Exception as e:
            logger.error(f"处理文件 {pdf_file.name} 时发生错误: {str(e)}")
            fail_count += 1

    # 打印统计信息
    logger.info(f"处理完成: 成功 {success_count}, 失败 {fail_count}, 总计 {len(pdf_files)}")

    if success_count > 0:
        logger.info("系统文档已成功添加到向量存储。")
        logger.info(f"系统用户ID: {SYSTEM_USER_ID}")
        logger.info("注意: 目前系统文档仅对系统用户可见。")
        logger.info("如需对所有用户可见，需要修改RAGService的检索逻辑。")
        return True
    else:
        logger.error("未成功添加任何文档")
        return False

def main():
    """主函数"""
    print("开始添加系统文档到RAG向量存储...")
    print("=" * 60)

    try:
        success = add_system_documents()

        print("=" * 60)
        if success:
            print("[SUCCESS] 系统文档添加完成")
            return 0
        else:
            print("[FAILED] 系统文档添加失败")
            return 1

    except Exception as e:
        print(f"[ERROR] 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
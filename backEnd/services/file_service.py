import os
import logging
import PyPDF2
from docx import Document
from config.settings import db, SECRET_KEY
from db_models.file import File
from cryptography.fernet import Fernet
import base64
import hashlib

# 尝试导入RAGService，用于向量存储集成
try:
    from services.rag_service import RAGService
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAGService不可用，文件向量存储功能将禁用")

logger = logging.getLogger(__name__)

class FileService:
    @staticmethod
    def _get_user_key(user_id):
        # 使用用户ID和SECRET_KEY生成用户专属密钥
        key_material = f"{SECRET_KEY}:{user_id}".encode()
        hashed = hashlib.sha256(key_material).digest()
        return base64.urlsafe_b64encode(hashed)
    
    @staticmethod
    def _encrypt_file(filepath, user_id):
        key = FileService._get_user_key(user_id)
        fernet = Fernet(key)
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        encrypted_data = fernet.encrypt(data)
        
        with open(filepath, 'wb') as f:
            f.write(encrypted_data)
    
    @staticmethod
    def _decrypt_file(filepath, user_id):
        key = FileService._get_user_key(user_id)
        fernet = Fernet(key)
        
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        
        with open(filepath, 'wb') as f:
            f.write(decrypted_data)
    
    @staticmethod
    def save_uploaded_file(file, user_id, upload_folder):
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)

        # 加密文件
        FileService._encrypt_file(filepath, user_id)

        new_file = File(
            filename=file.filename,
            filepath=filepath,
            user_id=user_id
        )
        db.session.add(new_file)
        db.session.commit()

        # 尝试将文件内容添加到向量存储
        FileService._add_file_to_vector_store(new_file.id, user_id, file.filename, filepath)

        return new_file
    
    @staticmethod
    def parse_file(filepath, user_id=None):
        ext = os.path.splitext(filepath)[1].lower()
        
        # 如果提供了user_id，说明文件是加密的，需要先解密
        if user_id:
            FileService._decrypt_file(filepath, user_id)
        
        try:
            if ext == '.pdf':
                result = FileService._parse_pdf(filepath)
            elif ext == '.docx':
                result = FileService._parse_docx(filepath)
            elif ext == '.txt':
                result = FileService._parse_txt(filepath)
            else:
                result = f"不支持的文件格式: {ext}"
        finally:
            # 如果提供了user_id，解析完成后重新加密
            if user_id:
                FileService._encrypt_file(filepath, user_id)
        
        return result
    
    @staticmethod
    def _parse_pdf(filepath):
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text.append(page.extract_text())
                return '\n'.join(text)
        except Exception as e:
            return f"解析PDF失败: {str(e)}"
    
    @staticmethod
    def _parse_docx(filepath):
        try:
            doc = Document(filepath)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            return f"解析Word失败: {str(e)}"
    
    @staticmethod
    def _parse_txt(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"解析文本失败: {str(e)}"
    
    @staticmethod
    def get_user_files(user_id):
        return File.query.filter_by(user_id=user_id).order_by(File.upload_time.desc()).all()
    
    @staticmethod
    def get_file_by_id(file_id, user_id):
        return File.query.filter_by(id=file_id, user_id=user_id).first()
    
    @staticmethod
    def _add_file_to_vector_store(file_id, user_id, filename, filepath):
        """将文件内容添加到向量存储"""
        if not RAG_AVAILABLE:
            return

        try:
            # 解析文件内容
            text_content = FileService.parse_file(filepath, user_id)

            # 检查解析结果是否是有效文本（不是错误消息）
            if not text_content or text_content.startswith("解析") and "失败" in text_content:
                logger.warning(f"文件解析失败或内容为空，跳过向量存储添加: {filename}")
                return

            # 创建RAGService实例并添加文档
            rag_service = RAGService()
            success = rag_service.add_documents_to_vector_store(
                user_id=user_id,
                file_id=file_id,
                filename=filename,
                text_content=text_content
            )

            if success:
                logger.info(f"文件 {filename} 已成功添加到向量存储")
            else:
                logger.warning(f"文件 {filename} 添加到向量存储失败")

        except Exception as e:
            logger.error(f"添加文件到向量存储时发生错误: {str(e)}")

    @staticmethod
    def _delete_file_from_vector_store(file_id, user_id):
        """从向量存储中删除文件的所有文档片段"""
        if not RAG_AVAILABLE:
            return

        try:
            # 创建RAGService实例
            rag_service = RAGService()

            # 调用RAGService的删除方法
            success = rag_service.delete_file_from_vector_store(user_id, file_id)
            if success:
                logger.info(f"已从向量存储中删除文件 {file_id} 的所有文档片段")
            else:
                logger.warning(f"从向量存储删除文件 {file_id} 的文档片段失败")

        except Exception as e:
            logger.error(f"从向量存储删除文件时发生错误: {str(e)}")

    @staticmethod
    def delete_file(file_id, user_id):
        file = FileService.get_file_by_id(file_id, user_id)
        if not file:
            return False

        # 从向量存储中删除文档片段
        FileService._delete_file_from_vector_store(file_id, user_id)

        # 删除文件
        if os.path.exists(file.filepath):
            os.remove(file.filepath)

        # 删除数据库记录
        db.session.delete(file)
        db.session.commit()
        return True

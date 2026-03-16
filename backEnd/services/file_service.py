import os
import PyPDF2
from docx import Document
from config.settings import db, SECRET_KEY
from db_models.file import File
from cryptography.fernet import Fernet
import base64
import hashlib

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
    def delete_file(file_id, user_id):
        file = FileService.get_file_by_id(file_id, user_id)
        if not file:
            return False
        
        # 删除文件
        if os.path.exists(file.filepath):
            os.remove(file.filepath)
        
        # 删除数据库记录
        db.session.delete(file)
        db.session.commit()
        return True

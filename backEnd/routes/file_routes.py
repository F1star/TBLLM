import os
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.file_service import FileService

UPLOAD_FOLDER = 'uploads'

@jwt_required()
def upload_file():
    uid = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        uploaded_file = FileService.save_uploaded_file(file, int(uid), UPLOAD_FOLDER)
        
        parsed_text = FileService.parse_file(uploaded_file.filepath, int(uid))
        
        return jsonify({
            'file_id': uploaded_file.id,
            'filename': uploaded_file.filename,
            'upload_time': uploaded_file.upload_time.isoformat(),
            'parsed_text': parsed_text[:500] + '...' if len(parsed_text) > 500 else parsed_text
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_required()
def get_user_files():
    uid = get_jwt_identity()
    
    files = FileService.get_user_files(int(uid))
    
    return jsonify([{
        'id': f.id,
        'filename': f.filename,
        'upload_time': f.upload_time.isoformat()
    } for f in files]), 200

@jwt_required()
def get_file_content(file_id):
    uid = get_jwt_identity()
    
    file = FileService.get_file_by_id(file_id, int(uid))
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    parsed_text = FileService.parse_file(file.filepath, int(uid))
    
    return jsonify({
        'file_id': file.id,
        'filename': file.filename,
        'content': parsed_text
    }), 200

@jwt_required()
def download_file(file_id):
    uid = get_jwt_identity()
    
    file = FileService.get_file_by_id(file_id, int(uid))
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    # 确保使用绝对路径
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 回到backEnd目录
    back_end_dir = os.path.dirname(base_dir)
    # 构建正确的文件路径
    file_path = file.filepath
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(file_path):
        file_path = os.path.join(back_end_dir, file_path)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on disk'}), 404
    
    # 解密文件
    FileService._decrypt_file(file_path, int(uid))
    
    try:
        # 读取文件内容到内存
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 重新加密文件
        FileService._encrypt_file(file_path, int(uid))
        
        # 使用make_response发送文件内容
        from flask import make_response
        response = make_response(file_content)
        # 使用简单的Content-Disposition格式，只保留文件名的ASCII部分
        import re
        # 只保留ASCII字符和常见标点
        safe_filename = re.sub(r'[^\x00-\x7F]+', '_', file.filename)
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        response.headers['Content-Type'] = 'application/octet-stream'
        return response
    except Exception as e:
        # 确保文件被重新加密
        if os.path.exists(file_path):
            FileService._encrypt_file(file_path, int(uid))
        return jsonify({'error': str(e)}), 500

@jwt_required()
def delete_file(file_id):
    uid = get_jwt_identity()
    
    success = FileService.delete_file(file_id, int(uid))
    if not success:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({'message': 'File deleted successfully'}), 200

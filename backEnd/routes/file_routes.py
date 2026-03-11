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

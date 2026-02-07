from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.model_service import ModelService
from services.chat_service import ChatService

model_service = ModelService()

@jwt_required()
def chat():
    data = request.get_json()
    print(f"收到的请求数据: {data}")
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'error': '消息不能为空'}), 400

    uid = get_jwt_identity()
    print(f"用户 ID: {uid}")
    
    user_chat = ChatService.add_chat(int(uid), 'user', msg)
    
    reply = model_service.generate_response(msg, uid)
    print(f"生成的回复: {reply}")
    
    assistant_chat = ChatService.add_chat(int(uid), 'assistant', reply)
    
    return jsonify({'response': reply, 'chat_id': assistant_chat.id})

@jwt_required()
def clear_chat():
    model_service.clear_chat_history(get_jwt_identity())
    uid = get_jwt_identity()
    ChatService.clear_user_history(int(uid))
    return jsonify({'message': '对话已清空'})

@jwt_required()
def get_chat_history():
    uid = get_jwt_identity()
    history = ChatService.get_user_history(int(uid))
    return jsonify(history)

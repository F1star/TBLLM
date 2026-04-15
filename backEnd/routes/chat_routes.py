from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.chat_service import ChatService
from services.model_service import ModelService

model_service = ModelService()


@jwt_required()
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"error": "消息不能为空"}), 400

    uid = int(get_jwt_identity())
    ChatService.add_chat(uid, "user", msg)

    reply = model_service.generate_response(msg, uid)
    ChatService.add_chat(uid, "assistant", reply)

    return jsonify({"response": reply})


@jwt_required()
def clear_chat():
    uid = int(get_jwt_identity())
    model_service.clear_chat_history(uid)
    ChatService.clear_user_history(uid)
    return jsonify({"message": "对话已清空"})


@jwt_required()
def get_chat_history():
    uid = int(get_jwt_identity())
    history = ChatService.get_user_history(uid)
    return jsonify(history)

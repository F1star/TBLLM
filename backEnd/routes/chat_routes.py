from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.chat_service import ChatService
from services.model_service import ModelService

model_service = ModelService()


@jwt_required()
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    session_id = data.get("session_id")  # 可为None，表示不关联到会话（旧方式）

    if not msg:
        return jsonify({"error": "消息不能为空"}), 400

    uid = int(get_jwt_identity())

    # 添加用户消息
    ChatService.add_chat(uid, "user", msg, session_id=session_id)

    # 生成AI回复
    reply = model_service.generate_response(msg, uid, session_id=session_id)

    # 添加AI回复
    ChatService.add_chat(uid, "assistant", reply, session_id=session_id)

    return jsonify({"response": reply, "session_id": session_id})


@jwt_required()
def clear_chat():
    uid = int(get_jwt_identity())
    data = request.get_json() or {}
    session_id = data.get('session_id', None)

    model_service.clear_chat_history(uid)
    ChatService.clear_user_history(uid, session_id=session_id)

    if session_id:
        return jsonify({"message": "会话对话已清空"})
    else:
        return jsonify({"message": "对话已清空"})


@jwt_required()
def get_chat_history():
    uid = int(get_jwt_identity())
    session_id = request.args.get('session_id', type=int)  # 可选

    if session_id is not None:
        # 返回特定会话的消息
        history = ChatService.get_user_history(uid, session_id=session_id)
    else:
        # 返回未关联到任何会话的消息（旧历史）
        history = ChatService.get_unassigned_chats(uid)

    return jsonify(history)

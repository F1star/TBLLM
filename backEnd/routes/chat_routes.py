from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import datetime

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
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat - 用户ID: {uid}, 消息: {msg[:50]}..., 会话ID: {session_id}")

    # 添加用户消息
    ChatService.add_chat(uid, "user", msg, session_id=session_id)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat - 用户消息已保存")

    # 生成AI回复
    reply = model_service.generate_response(msg, uid, session_id=session_id)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat - AI回复生成完成，长度: {len(reply)}")

    # 添加AI回复
    ChatService.add_chat(uid, "assistant", reply, session_id=session_id)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat - AI回复已保存")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat - 请求完成")
    return jsonify({"response": reply, "session_id": session_id})


@jwt_required()
def clear_chat():
    uid = int(get_jwt_identity())
    data = request.get_json() or {}
    session_id = data.get('session_id', None)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] clear_chat - 用户ID: {uid}, 会话ID: {session_id}")

    model_service.clear_chat_history(uid)
    ChatService.clear_user_history(uid, session_id=session_id)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] clear_chat - 聊天历史已清空")

    if session_id:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] clear_chat - 会话对话已清空")
        return jsonify({"message": "会话对话已清空"})
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] clear_chat - 对话已清空")
        return jsonify({"message": "对话已清空"})


@jwt_required()
def get_chat_history():
    uid = int(get_jwt_identity())
    session_id = request.args.get('session_id', type=int)  # 可选
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_chat_history - 用户ID: {uid}, 会话ID: {session_id}")

    if session_id is not None:
        # 返回特定会话的消息
        history = ChatService.get_user_history(uid, session_id=session_id)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_chat_history - 返回特定会话历史，记录数: {len(history)}")
    else:
        # 返回未关联到任何会话的消息（旧历史）
        history = ChatService.get_unassigned_chats(uid)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_chat_history - 返回未关联历史，记录数: {len(history)}")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_chat_history - 请求完成")
    return jsonify(history)

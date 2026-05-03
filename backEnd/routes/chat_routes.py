from flask import jsonify, request, Response, stream_with_context
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


@jwt_required()
def chat_stream():
    """流式对话 - SSE 方式返回 token，无 session_id 时自动创建会话"""
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not msg:
        return jsonify({"error": "消息不能为空"}), 400

    uid = int(get_jwt_identity())

    # 无会话时自动创建
    session_name = None
    if not session_id:
        from services.session_service import SessionService
        session_name = msg[:30] + '...' if len(msg) > 30 else msg
        session = SessionService.create_session(uid, session_name)
        session_id = session.id
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat_stream - 自动创建会话: ID={session_id}, 名称={session_name}")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat_stream - 用户ID: {uid}, 消息: {msg[:50]}..., 会话ID: {session_id}")

    # 保存用户消息（此时已有 session_id）
    ChatService.add_chat(uid, "user", msg, session_id=session_id)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat_stream - 用户消息已保存")

    def generate():
        full_response = ""
        try:
            # 新创建的会话才推送 session_created 事件
            if session_name:
                yield f"event: session_created\ndata: {session_id}|{session_name}\n\n"
            for token in model_service.generate_chat_stream(msg, uid, session_id=session_id):
                full_response += token
                yield f"data: {token}\n\n"
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat_stream - 流式生成异常: {str(e)}")
            yield f"data: [生成错误: {str(e)}]\n\n"
        finally:
            # 流结束后保存 AI 回复到数据库
            if full_response.strip():
                ChatService.add_chat(uid, "assistant", full_response.strip(), session_id=session_id)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] chat_stream - AI回复已保存，长度: {len(full_response.strip())}")

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

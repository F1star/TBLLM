from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.session_service import SessionService


@jwt_required()
def get_sessions():
    """获取用户的所有会话列表"""
    user_id = int(get_jwt_identity())
    sessions = SessionService.get_user_sessions(user_id)
    return jsonify(sessions)


@jwt_required()
def create_session():
    """创建新会话"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    name = data.get('name', '').strip()

    if not name:
        # 如果没有提供名称，使用默认名称
        name = "新会话"

    session = SessionService.create_session(user_id, name)
    return jsonify(session.to_dict()), 201


@jwt_required()
def update_session(session_id):
    """更新会话信息（如标题）"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': '会话名称不能为空'}), 400

    session = SessionService.update_session(session_id, user_id, name)
    if not session:
        return jsonify({'error': '会话不存在或无权访问'}), 404

    return jsonify(session.to_dict())


@jwt_required()
def delete_session(session_id):
    """删除会话"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    delete_messages = data.get('delete_messages', False)

    success = SessionService.delete_session(session_id, user_id, delete_messages)
    if not success:
        return jsonify({'error': '会话不存在或无权访问'}), 404

    return jsonify({'message': '会话删除成功'})


@jwt_required()
def get_session_messages(session_id):
    """获取会话消息历史"""
    user_id = int(get_jwt_identity())
    messages = SessionService.get_session_messages(session_id, user_id)
    return jsonify(messages)


@jwt_required()
def get_session_stats(session_id):
    """获取会话统计信息"""
    user_id = int(get_jwt_identity())
    stats = SessionService.get_session_stats(session_id, user_id)
    if not stats:
        return jsonify({'error': '会话不存在或无权访问'}), 404

    return jsonify(stats)
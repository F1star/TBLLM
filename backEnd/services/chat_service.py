from config.settings import db
from db_models.chat_history import ChatHistory


class ChatService:
    @staticmethod
    def add_chat(user_id, role, content, session_id=None):
        """添加聊天记录，支持关联到会话"""
        chat = ChatHistory(
            user_id=user_id,
            role=role,
            content=content,
            session_id=session_id
        )
        db.session.add(chat)
        db.session.commit()
        return chat

    @staticmethod
    def get_user_history(user_id, session_id=None):
        """获取用户历史记录，可按会话过滤"""
        query = ChatHistory.query.filter_by(user_id=user_id)
        if session_id is not None:
            query = query.filter_by(session_id=session_id)

        history = query.order_by(ChatHistory.timestamp).all()
        return [{
            'id': h.id,
            'role': h.role,
            'content': h.content,
            'timestamp': h.timestamp.isoformat(),
            'session_id': h.session_id
        } for h in history]

    @staticmethod
    def clear_user_history(user_id, session_id=None):
        """清空用户历史记录，可指定会话"""
        query = ChatHistory.query.filter_by(user_id=user_id)
        if session_id is not None:
            query = query.filter_by(session_id=session_id)
        query.delete()
        db.session.commit()

    @staticmethod
    def get_chat_by_id(chat_id, user_id):
        return ChatHistory.query.filter_by(id=chat_id, user_id=user_id).first()

    @staticmethod
    def get_recent_chats(user_id, limit=10, session_id=None):
        """获取最近聊天记录，可按会话过滤"""
        query = ChatHistory.query.filter_by(user_id=user_id)
        if session_id is not None:
            query = query.filter_by(session_id=session_id)
        return query.order_by(ChatHistory.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_unassigned_chats(user_id):
        """获取未关联到任何会话的聊天记录（旧历史）"""
        history = ChatHistory.query.filter_by(user_id=user_id, session_id=None).order_by(ChatHistory.timestamp).all()
        return [{
            'id': h.id,
            'role': h.role,
            'content': h.content,
            'timestamp': h.timestamp.isoformat()
        } for h in history]

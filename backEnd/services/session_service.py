from config.settings import db
from db_models.chat_session import ChatSession
from db_models.chat_history import ChatHistory


class SessionService:
    @staticmethod
    def create_session(user_id, name=None):
        """创建新会话"""
        if not name:
            name = "新会话"
        session = ChatSession(user_id=user_id, name=name)
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def get_user_sessions(user_id):
        """获取用户的所有会话，按更新时间倒序排列"""
        sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
        return [session.to_dict() for session in sessions]

    @staticmethod
    def get_session(session_id, user_id):
        """获取指定会话（验证用户权限）"""
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        return session

    @staticmethod
    def update_session(session_id, user_id, name):
        """更新会话名称"""
        session = SessionService.get_session(session_id, user_id)
        if not session:
            return None
        session.name = name
        db.session.commit()
        return session

    @staticmethod
    def delete_session(session_id, user_id, delete_messages=False):
        """删除会话"""
        session = SessionService.get_session(session_id, user_id)
        if not session:
            return False

        if delete_messages:
            # 级联删除消息（由于关系中的cascade='all, delete-orphan'，这会自动发生）
            pass

        db.session.delete(session)
        db.session.commit()
        return True

    @staticmethod
    def get_session_messages(session_id, user_id):
        """获取会话中的所有消息"""
        session = SessionService.get_session(session_id, user_id)
        if not session:
            return []

        messages = ChatHistory.query.filter_by(session_id=session_id, user_id=user_id).order_by(ChatHistory.timestamp).all()
        return [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'timestamp': (msg.timestamp.isoformat() + 'Z') if msg.timestamp else None
        } for msg in messages]

    @staticmethod
    def add_message_to_session(user_id, session_id, role, content):
        """向会话添加消息"""
        session = SessionService.get_session(session_id, user_id)
        if not session:
            return None

        message = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content
        )
        db.session.add(message)

        # 更新会话的更新时间
        db.session.commit()
        return message

    @staticmethod
    def get_session_stats(session_id, user_id):
        """获取会话统计信息"""
        session = SessionService.get_session(session_id, user_id)
        if not session:
            return None

        message_count = ChatHistory.query.filter_by(session_id=session_id).count()

        return {
            'id': session.id,
            'name': session.name,
            'message_count': message_count,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'updated_at': session.updated_at.isoformat() if session.updated_at else None
        }

    @staticmethod
    def generate_session_name(first_message):
        """根据第一条消息自动生成会话标题"""
        if not first_message:
            return "新会话"

        # 取前20个字符，如果超过则加省略号
        if len(first_message) > 20:
            return first_message[:20] + "..."
        return first_message
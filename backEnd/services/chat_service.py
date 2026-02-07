from config.settings import db
from db_models.chat_history import ChatHistory

class ChatService:
    @staticmethod
    def add_chat(user_id, role, content):
        chat = ChatHistory(user_id=user_id, role=role, content=content)
        db.session.add(chat)
        db.session.commit()
        return chat
    
    @staticmethod
    def get_user_history(user_id):
        history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp).all()
        return [{
            'id': h.id,
            'role': h.role,
            'content': h.content,
            'timestamp': h.timestamp.isoformat()
        } for h in history]
    
    @staticmethod
    def clear_user_history(user_id):
        ChatHistory.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    
    @staticmethod
    def get_chat_by_id(chat_id, user_id):
        return ChatHistory.query.filter_by(id=chat_id, user_id=user_id).first()
    
    @staticmethod
    def get_recent_chats(user_id, limit=10):
        return ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()

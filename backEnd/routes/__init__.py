from .auth_routes import register, login, change_password
from .chat_routes import chat, clear_chat, get_chat_history
from .evaluation_routes import evaluate_user_overall, get_latest_evaluation, get_evaluations
from .file_routes import upload_file, get_user_files, get_file_content, download_file, delete_file
from .session_routes import (get_sessions, create_session, update_session,
                           delete_session, get_session_messages, get_session_stats)

def register_routes(app):
    app.add_url_rule('/api/register', 'register', register, methods=['POST'])
    app.add_url_rule('/api/login', 'login', login, methods=['POST'])
    app.add_url_rule('/api/change-password', 'change_password', change_password, methods=['POST'])
    app.add_url_rule('/api/chat', 'chat', chat, methods=['POST'])
    app.add_url_rule('/api/chat/clear', 'clear_chat', clear_chat, methods=['POST'])
    app.add_url_rule('/api/chat/history', 'get_chat_history', get_chat_history, methods=['GET'])
    app.add_url_rule('/api/evaluate', 'evaluate_user_overall', evaluate_user_overall, methods=['POST'])
    app.add_url_rule('/api/evaluation/latest', 'get_latest_evaluation', get_latest_evaluation, methods=['GET'])
    app.add_url_rule('/api/evaluations', 'get_evaluations', get_evaluations, methods=['GET'])
    app.add_url_rule('/api/files/upload', 'upload_file', upload_file, methods=['POST'])
    app.add_url_rule('/api/files', 'get_user_files', get_user_files, methods=['GET'])
    app.add_url_rule('/api/files/<int:file_id>', 'get_file_content', get_file_content, methods=['GET'])
    app.add_url_rule('/api/files/<int:file_id>/download', 'download_file', download_file, methods=['GET'])
    app.add_url_rule('/api/files/<int:file_id>', 'delete_file', delete_file, methods=['DELETE'])

    # 会话管理API
    app.add_url_rule('/api/sessions', 'get_sessions', get_sessions, methods=['GET'])
    app.add_url_rule('/api/sessions', 'create_session', create_session, methods=['POST'])
    app.add_url_rule('/api/sessions/<int:session_id>', 'update_session', update_session, methods=['PUT'])
    app.add_url_rule('/api/sessions/<int:session_id>', 'delete_session', delete_session, methods=['DELETE'])
    app.add_url_rule('/api/sessions/<int:session_id>/messages', 'get_session_messages', get_session_messages, methods=['GET'])
    app.add_url_rule('/api/sessions/<int:session_id>/stats', 'get_session_stats', get_session_stats, methods=['GET'])

__all__ = ['register_routes']

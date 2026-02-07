from .auth_routes import register, login
from .chat_routes import chat, clear_chat, get_chat_history
from .evaluation_routes import evaluate_user_overall, get_latest_evaluation, get_evaluations

def register_routes(app):
    app.add_url_rule('/api/register', 'register', register, methods=['POST'])
    app.add_url_rule('/api/login', 'login', login, methods=['POST'])
    app.add_url_rule('/api/chat', 'chat', chat, methods=['POST'])
    app.add_url_rule('/api/chat/clear', 'clear_chat', clear_chat, methods=['POST'])
    app.add_url_rule('/api/chat/history', 'get_chat_history', get_chat_history, methods=['GET'])
    app.add_url_rule('/api/evaluate', 'evaluate_user_overall', evaluate_user_overall, methods=['POST'])
    app.add_url_rule('/api/evaluation/latest', 'get_latest_evaluation', get_latest_evaluation, methods=['GET'])
    app.add_url_rule('/api/evaluations', 'get_evaluations', get_evaluations, methods=['GET'])

__all__ = ['register_routes']

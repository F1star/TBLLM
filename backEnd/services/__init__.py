__all__ = ['ModelService', 'ChatService', 'EvaluationService', 'SessionService']


def __getattr__(name):
    if name == 'ModelService':
        from .model_service import ModelService
        return ModelService
    if name == 'ChatService':
        from .chat_service import ChatService
        return ChatService
    if name == 'EvaluationService':
        from .evaluation_service import EvaluationService
        return EvaluationService
    if name == 'SessionService':
        from .session_service import SessionService
        return SessionService
    raise AttributeError(f"module 'services' has no attribute {name!r}")

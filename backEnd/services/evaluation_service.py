from config.settings import db
from db_models.evaluation import Evaluation
from services.chat_service import ChatService
from services.file_service import FileService


class EvaluationService:
    @staticmethod
    def evaluate_user_overall(user_id, model_service, file_ids=None):
        user_chats = ChatService.get_user_history(user_id)

        try:
            chat_history_text = EvaluationService._build_chat_history_text(user_chats)
            file_context_text = EvaluationService._build_file_context_text(user_id, file_ids)

            if chat_history_text == "暂无历史对话。" and file_context_text == "暂无文件内容。":
                return None, "暂无可评估的历史对话或文件内容。"

            evaluation_data = model_service.generate_evaluation(
                chat_history_text=chat_history_text,
                file_context_text=file_context_text,
            )

            evaluation = Evaluation(
                user_id=user_id,
                chat_history_id=0,
                logic_score=evaluation_data.get("logic_score", 0),
                creativity_score=evaluation_data.get("creativity_score", 0),
                expression_score=evaluation_data.get("expression_score", 0),
                knowledge_score=evaluation_data.get("knowledge_score", 0),
                overall_score=evaluation_data.get("overall_score", 0),
                feedback=evaluation_data.get("feedback", ""),
            )
            db.session.add(evaluation)
            db.session.commit()
            return evaluation, None
        except Exception as e:
            import traceback

            traceback.print_exc()
            return None, f"评分失败: {str(e)}"

    @staticmethod
    def get_latest_evaluation(user_id):
        evaluation = Evaluation.query.filter_by(user_id=user_id).order_by(Evaluation.timestamp.desc()).first()
        if evaluation:
            return {
                "id": evaluation.id,
                "logic_score": evaluation.logic_score,
                "creativity_score": evaluation.creativity_score,
                "expression_score": evaluation.expression_score,
                "knowledge_score": evaluation.knowledge_score,
                "overall_score": evaluation.overall_score,
                "feedback": evaluation.feedback,
                "timestamp": evaluation.timestamp.isoformat(),
            }
        return None

    @staticmethod
    def get_user_evaluations(user_id):
        evaluations = Evaluation.query.filter_by(user_id=user_id).order_by(Evaluation.timestamp.desc()).all()
        return [
            {
                "id": e.id,
                "chat_history_id": e.chat_history_id,
                "logic_score": e.logic_score,
                "creativity_score": e.creativity_score,
                "expression_score": e.expression_score,
                "knowledge_score": e.knowledge_score,
                "overall_score": e.overall_score,
                "feedback": e.feedback,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in evaluations
        ]

    @staticmethod
    def _build_chat_history_text(user_chats):
        if not user_chats:
            return "暂无历史对话。"
        return "\n".join(
            f"{chat['role']}: {chat['content']}" for chat in user_chats[-20:]
        )

    @staticmethod
    def _build_file_context_text(user_id, file_ids=None):
        files = []
        if file_ids:
            for file_id in file_ids:
                file = FileService.get_file_by_id(int(file_id), user_id)
                if file:
                    files.append(file)
        else:
            files = FileService.get_user_files(user_id)

        if not files:
            return "暂无文件内容。"

        file_blocks = []
        for file in files:
            file_content = FileService.parse_file(file.filepath, user_id)
            file_blocks.append(f"文件: {file.filename}\n内容:\n{file_content[:1500]}")
        return "\n\n".join(file_blocks)

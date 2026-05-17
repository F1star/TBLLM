from config.settings import db
from datetime import datetime
from db_models.evaluation import Evaluation
from services.chat_service import ChatService
from services.file_service import FileService
from services.session_service import SessionService


class EvaluationService:
    @staticmethod
    def evaluate_user_overall(user_id, model_service, file_ids=None, session_id=None, deep_mode=False):
        """评估用户整体或特定会话
        Args:
            user_id: 用户ID
            model_service: 模型服务
            file_ids: 文件ID列表
            session_id: 可选，会话ID。如果为None，则评估未关联到会话的历史记录
            deep_mode: 是否启用深度思考（ReAct循环）
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 用户ID: {user_id}, 文件IDs: {file_ids}, 会话ID: {session_id}, 深度思考: {deep_mode}")
        if session_id:
            # 评估特定会话
            user_chats = ChatService.get_user_history(user_id, session_id=session_id)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 获取会话历史，记录数: {len(user_chats)}")
        else:
            # 评估未关联到会话的历史记录（旧历史）
            user_chats = ChatService.get_unassigned_chats(user_id)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 获取未关联历史，记录数: {len(user_chats)}")

        try:
            chat_history_text = EvaluationService._build_chat_history_text(user_chats)
            file_context_text = EvaluationService._build_file_context_text(user_id, file_ids)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 聊天历史长度: {len(chat_history_text)}, 文件上下文长度: {len(file_context_text)}")

            if chat_history_text == "暂无历史对话。" and file_context_text == "暂无文件内容。":
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 暂无可评估的历史对话或文件内容")
                return None, "暂无可评估的历史对话或文件内容。"

            evaluation_data = model_service.generate_evaluation(
                chat_history_text=chat_history_text,
                file_context_text=file_context_text,
                user_id=user_id,
                deep_mode=deep_mode,
            )
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 模型评估完成")

            evaluation = Evaluation(
                user_id=user_id,
                session_id=session_id,
                chat_history_id=None,  # 不再关联单条消息
                logic_score=evaluation_data.get("logic_score", 0),
                creativity_score=evaluation_data.get("creativity_score", 0),
                expression_score=evaluation_data.get("expression_score", 0),
                knowledge_score=evaluation_data.get("knowledge_score", 0),
                overall_score=evaluation_data.get("overall_score", 0),
                feedback=evaluation_data.get("feedback", ""),
            )
            db.session.add(evaluation)
            db.session.commit()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 评估记录已保存，ID: {evaluation.id}")
            return evaluation, None
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EvaluationService.evaluate_user_overall - 评分失败: {str(e)}")
            return None, f"评分失败: {str(e)}"

    @staticmethod
    def get_latest_evaluation(user_id, session_id=None):
        """获取最新评估记录，可指定会话（排除专业测评记录）"""
        query = Evaluation.query.filter_by(user_id=user_id).filter(
            Evaluation.assessment_session_id.is_(None)
        )
        if session_id is not None:
            query = query.filter_by(session_id=session_id)
        evaluation = query.order_by(Evaluation.timestamp.desc()).first()
        if evaluation:
            return {
                "id": evaluation.id,
                "session_id": evaluation.session_id,
                "chat_history_id": evaluation.chat_history_id,
                "logic_score": evaluation.logic_score,
                "creativity_score": evaluation.creativity_score,
                "expression_score": evaluation.expression_score,
                "knowledge_score": evaluation.knowledge_score,
                "overall_score": evaluation.overall_score,
                "feedback": evaluation.feedback,
                "timestamp": (evaluation.timestamp.isoformat() + 'Z') if evaluation.timestamp else None,
            }
        return None

    @staticmethod
    def get_user_evaluations(user_id, session_id=None):
        """获取用户评估记录，可指定会话（排除专业测评记录）"""
        query = Evaluation.query.filter_by(user_id=user_id).filter(
            Evaluation.assessment_session_id.is_(None)
        )
        if session_id is not None:
            query = query.filter_by(session_id=session_id)
        evaluations = query.order_by(Evaluation.timestamp.desc()).all()
        return [
            {
                "id": e.id,
                "session_id": e.session_id,
                "chat_history_id": e.chat_history_id,
                "logic_score": e.logic_score,
                "creativity_score": e.creativity_score,
                "expression_score": e.expression_score,
                "knowledge_score": e.knowledge_score,
                "overall_score": e.overall_score,
                "feedback": e.feedback,
                "timestamp": (e.timestamp.isoformat() + 'Z') if e.timestamp else None,
            }
            for e in evaluations
        ]

    @staticmethod
    def delete_evaluation(evaluation_id, user_id):
        """删除评估记录"""
        evaluation = Evaluation.query.filter_by(id=evaluation_id, user_id=user_id).first()
        if not evaluation:
            return False
        db.session.delete(evaluation)
        db.session.commit()
        return True

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

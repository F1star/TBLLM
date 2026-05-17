from config.settings import db
from datetime import datetime
import json
import random
from typing import List, Dict, Any, Optional, Tuple

from db_models import (
    QuestionnaireQuestion, ProfessionalAssessmentSession,
    ProfessionalAssessmentResponse, Evaluation, User
)


class ProfessionalAssessmentService:
    """专业测评服务"""

    @staticmethod
    def create_session(user_id: int, name: str = None, cohort: str = None,
                       question_count: int = 10) -> Tuple[Optional[ProfessionalAssessmentSession], Optional[str]]:
        """
        创建新的专业测评会话

        Args:
            user_id: 用户ID
            name: 会话名称，默认为"专业测评"
            cohort: 学生组别，'younger'（年轻组）或 'elderly'（年长组）
            question_count: 问题数量，默认为10

        Returns:
            (会话对象, 错误信息)
        """
        try:
            # 检查用户是否存在
            user = User.query.get(user_id)
            if not user:
                return None, "用户不存在"

            # 如果未指定cohort，随机选择一个
            if not cohort:
                cohort = random.choice(['younger', 'elderly'])

            # 获取问题列表
            questions = QuestionnaireQuestion.query.filter_by(cohort=cohort).all()
            if not questions:
                return None, f"找不到{cohort}组别的问题"

            # 如果请求的问题数量大于可用问题数量，调整
            if question_count > len(questions):
                question_count = len(questions)

            # 随机选择问题
            selected_questions = random.sample(questions, question_count)

            # 创建会话
            session_name = name or f"{cohort}组专业测评"
            session = ProfessionalAssessmentSession(
                user_id=user_id,
                name=session_name,
                cohort=cohort,
                question_count=question_count,
                answered_count=0,
                status='in_progress'
            )
            db.session.add(session)
            db.session.commit()

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.create_session - "
                  f"创建会话 {session.id}，用户 {user_id}，问题数量 {question_count}")

            return session, None

        except Exception as e:
            db.session.rollback()
            error_msg = f"创建会话失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.create_session - {error_msg}")
            return None, error_msg

    @staticmethod
    def get_session(session_id: int, user_id: int = None) -> Tuple[Optional[ProfessionalAssessmentSession], Optional[str]]:
        """
        获取专业测评会话

        Args:
            session_id: 会话ID
            user_id: 可选的用户ID，用于验证会话所有权

        Returns:
            (会话对象, 错误信息)
        """
        try:
            session = ProfessionalAssessmentSession.query.get(session_id)
            if not session:
                return None, "会话不存在"

            # 如果提供了user_id，验证会话所有权
            if user_id and session.user_id != user_id:
                return None, "无权访问此会话"

            return session, None

        except Exception as e:
            error_msg = f"获取会话失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_session - {error_msg}")
            return None, error_msg

    @staticmethod
    def get_user_sessions(user_id: int) -> Tuple[List[ProfessionalAssessmentSession], Optional[str]]:
        """
        获取用户的所有专业测评会话

        Args:
            user_id: 用户ID

        Returns:
            (会话列表, 错误信息)
        """
        try:
            sessions = ProfessionalAssessmentSession.query.filter_by(user_id=user_id)\
                .order_by(ProfessionalAssessmentSession.created_at.desc()).all()
            return sessions, None

        except Exception as e:
            error_msg = f"获取用户会话失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_user_sessions - {error_msg}")
            return [], error_msg

    @staticmethod
    def get_session_questions(session_id: int, user_id: int = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        获取会话的问题列表，包含问题详情和用户的回答（如果有）

        Args:
            session_id: 会话ID
            user_id: 可选的用户ID，用于验证会话所有权

        Returns:
            (问题列表, 错误信息)
        """
        try:
            # 获取会话
            session, error = ProfessionalAssessmentService.get_session(session_id, user_id)
            if error:
                return [], error

            # 获取该组别的问题
            questions = QuestionnaireQuestion.query.filter_by(cohort=session.cohort).all()

            # 获取用户的回答
            responses = {r.question_id: r for r in session.responses}

            # 构建问题列表
            result = []
            for question in questions:
                response = responses.get(question.question_id)
                question_dict = {
                    'question_id': question.question_id,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'cohort': question.cohort,
                    'options': json.loads(question.options_json) if question.options_json else {},
                    'metadata': json.loads(question.metadata_json) if question.metadata_json else {},
                    'has_response': response is not None,
                    'response': response.to_dict() if response else None
                }
                result.append(question_dict)

            return result, None

        except Exception as e:
            error_msg = f"获取会话问题失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_session_questions - {error_msg}")
            return [], error_msg

    @staticmethod
    def submit_response(session_id: int, question_id: str, answer_text: str,
                        raw_value: float = None) -> Tuple[Optional[ProfessionalAssessmentResponse], Optional[str]]:
        """
        提交回答

        Args:
            session_id: 会话ID
            question_id: 问题ID
            answer_text: 回答文本
            raw_value: 原始数值（可选）

        Returns:
            (回答对象, 错误信息)
        """
        try:
            # 获取会话
            session = ProfessionalAssessmentSession.query.get(session_id)
            if not session:
                return None, "会话不存在"

            if session.status != 'in_progress':
                return None, "会话已结束，无法提交回答"

            # 检查问题是否存在
            question = QuestionnaireQuestion.query.filter_by(question_id=question_id).first()
            if not question:
                return None, "问题不存在"

            # 检查是否已回答过
            existing_response = ProfessionalAssessmentResponse.query.filter_by(
                session_id=session_id, question_id=question_id).first()

            if existing_response:
                # 更新现有回答
                existing_response.answer_text = answer_text
                existing_response.raw_value = raw_value
                existing_response.response_timestamp = datetime.now()
                response = existing_response
            else:
                # 创建新回答
                response = ProfessionalAssessmentResponse(
                    session_id=session_id,
                    question_id=question_id,
                    answer_text=answer_text,
                    raw_value=raw_value,
                    response_timestamp=datetime.now()
                )
                db.session.add(response)

            db.session.commit()

            # 更新会话进度
            session.update_progress()

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.submit_response - "
                  f"会话 {session_id}，问题 {question_id}，已回答 {session.answered_count}/{session.question_count}")

            return response, None

        except Exception as e:
            db.session.rollback()
            error_msg = f"提交回答失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.submit_response - {error_msg}")
            return None, error_msg

    @staticmethod
    def evaluate_session(session_id: int, user_id: int, model_service) -> Tuple[Optional[Evaluation], Optional[str]]:
        """
        评估专业测评会话

        Args:
            session_id: 会话ID
            user_id: 用户ID
            model_service: 模型服务

        Returns:
            (评估对象, 错误信息)
        """
        try:
            # 获取会话
            session, error = ProfessionalAssessmentService.get_session(session_id, user_id)
            if error:
                return None, error

            if session.status == 'in_progress':
                return None, "会话尚未完成，无法评估"

            if session.status == 'evaluated' and session.evaluation_id:
                # 返回现有评估
                evaluation = Evaluation.query.get(session.evaluation_id)
                if evaluation:
                    return evaluation, None

            # 获取所有回答
            responses = session.responses.all()
            if not responses:
                return None, "没有回答可评估"

            # 获取问题详情
            question_ids = [r.question_id for r in responses]
            questions = QuestionnaireQuestion.query.filter(QuestionnaireQuestion.question_id.in_(question_ids)).all()
            question_map = {q.question_id: q for q in questions}

            # 构建评估文本
            assessment_text = ProfessionalAssessmentService._build_assessment_text(responses, question_map)

            # 调用模型进行评估
            evaluation_data = model_service.generate_professional_assessment(
                assessment_text=assessment_text,
                cohort=session.cohort
            )

            if not evaluation_data:
                return None, "模型评估失败"

            # 从评估结果中提取技能评分
            skill_scores = evaluation_data.get('skill_scores', {})
            overall_score = evaluation_data.get('overall_score', 0)
            feedback = evaluation_data.get('feedback', '')

            # 映射到Evaluation模型的字段
            # 从17项技能中选取最相关的映射到四个维度
            logic_score = skill_scores.get('逻辑思维', skill_scores.get('责任感', 0))
            creativity_score = skill_scores.get('创造力', 0)
            expression_score = skill_scores.get('表达能力', skill_scores.get('同理心', 0))
            knowledge_score = skill_scores.get('知识广度', skill_scores.get('好奇心', 0))

            # 如果没有这些技能名，尝试用前四个任意技能
            if not any([logic_score, creativity_score, expression_score, knowledge_score]):
                skill_values = list(skill_scores.values())
                logic_score = skill_values[0] if len(skill_values) > 0 else 0
                creativity_score = skill_values[1] if len(skill_values) > 1 else 0
                expression_score = skill_values[2] if len(skill_values) > 2 else 0
                knowledge_score = skill_values[3] if len(skill_values) > 3 else 0

            # 创建评估记录
            evaluation = Evaluation(
                user_id=user_id,
                assessment_session_id=session_id,
                logic_score=logic_score,
                creativity_score=creativity_score,
                expression_score=expression_score,
                knowledge_score=knowledge_score,
                overall_score=overall_score,
                skill_scores=skill_scores,
                feedback=feedback,
            )
            db.session.add(evaluation)
            db.session.commit()

            # 更新会话状态
            session.mark_as_evaluated(evaluation.id)

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.evaluate_session - "
                  f"会话 {session_id} 评估完成，评估ID: {evaluation.id}")

            return evaluation, None

        except Exception as e:
            db.session.rollback()
            error_msg = f"评估会话失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.evaluate_session - {error_msg}")
            import traceback
            traceback.print_exc()
            return None, error_msg

    @staticmethod
    def persist_evaluation_result(
        session_id: int,
        user_id: int,
        evaluation_data: Dict[str, Any]
    ) -> Tuple[Optional[Evaluation], Optional[str]]:
        """将专业测评模型结果持久化到 Evaluation 表，并更新会话状态。"""
        try:
            session, error = ProfessionalAssessmentService.get_session(session_id, user_id)
            if error:
                return None, error

            skill_scores = evaluation_data.get('skill_scores', {}) or {}
            overall_score = evaluation_data.get('overall_score', 0)
            feedback = evaluation_data.get('feedback', '')

            logic_score = skill_scores.get('逻辑思维', skill_scores.get('责任感', 0))
            creativity_score = skill_scores.get('创造力', 0)
            expression_score = skill_scores.get('表达能力', skill_scores.get('同理心', 0))
            knowledge_score = skill_scores.get('知识广度', skill_scores.get('好奇心', 0))

            if not any([logic_score, creativity_score, expression_score, knowledge_score]):
                skill_values = list(skill_scores.values())
                logic_score = skill_values[0] if len(skill_values) > 0 else 0
                creativity_score = skill_values[1] if len(skill_values) > 1 else 0
                expression_score = skill_values[2] if len(skill_values) > 2 else 0
                knowledge_score = skill_values[3] if len(skill_values) > 3 else 0

            evaluation = Evaluation.query.get(session.evaluation_id) if session.evaluation_id else None
            if evaluation is None:
                evaluation = Evaluation(
                    user_id=user_id,
                    assessment_session_id=session_id,
                )
                db.session.add(evaluation)

            evaluation.logic_score = logic_score
            evaluation.creativity_score = creativity_score
            evaluation.expression_score = expression_score
            evaluation.knowledge_score = knowledge_score
            evaluation.overall_score = overall_score
            evaluation.skill_scores = skill_scores
            evaluation.feedback = feedback
            db.session.commit()

            session.mark_as_evaluated(evaluation.id)
            return evaluation, None

        except Exception as e:
            db.session.rollback()
            error_msg = f"保存专业测评评估结果失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.persist_evaluation_result - {error_msg}")
            import traceback
            traceback.print_exc()
            return None, error_msg

    @staticmethod
    def _build_assessment_text(responses: List[ProfessionalAssessmentResponse],
                               question_map: Dict[str, QuestionnaireQuestion]) -> str:
        """构建评估文本"""
        lines = ["专业测评回答记录："]
        lines.append("=" * 50)

        for i, response in enumerate(responses, 1):
            question = question_map.get(response.question_id)
            question_text = question.question_text if question else response.question_id

            lines.append(f"问题 {i}: {question_text}")
            lines.append(f"回答: {response.answer_text}")

            # 如果是选择题，显示选项映射
            if question and question.options_json:
                try:
                    options = json.loads(question.options_json)
                    if response.raw_value is not None:
                        raw_val_str = str(int(response.raw_value)) if response.raw_value.is_integer() else str(response.raw_value)
                        option_text = options.get(raw_val_str, f"代码 {raw_val_str}")
                        lines.append(f"选项: {option_text}")
                except:
                    pass

            lines.append("-" * 30)

        lines.append("=" * 50)
        return "\n".join(lines)

    @staticmethod
    def get_available_cohorts() -> List[Dict[str, str]]:
        """获取可用的学生组别"""
        try:
            cohorts = db.session.query(QuestionnaireQuestion.cohort).distinct().all()
            cohort_list = [{'value': c[0], 'label': c[0]} for c in cohorts if c[0]]
            return cohort_list
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_available_cohorts - 错误: {str(e)}")
            return []

    @staticmethod
    def delete_session(session_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除专业测评会话

        Args:
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            (是否成功, 错误信息)
        """
        try:
            session, error = ProfessionalAssessmentService.get_session(session_id, user_id)
            if error:
                return False, error

            db.session.delete(session)
            db.session.commit()

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.delete_session - "
                  f"删除会话 {session_id}，用户 {user_id}")

            return True, None

        except Exception as e:
            db.session.rollback()
            error_msg = f"删除会话失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.delete_session - {error_msg}")
            return False, error_msg

    @staticmethod
    def get_remembered_answers(user_id: int, cohort: str) -> Tuple[dict, Optional[str]]:
        """
        获取用户指定组别的最新回答记录（记忆功能）

        查找用户最近一次该组别的测评会话，提取所有已提交的回答，
        用于在新测评中预填，避免用户重复回答。

        Args:
            user_id: 用户ID
            cohort: 学生组别

        Returns:
            (答案字典 {question_id: {answer_text, raw_value}}, 错误信息)
        """
        try:
            # 查找该用户该组别最近已完成或有回答记录的会话
            # 排除当前正在进行的 in_progress 会话
            latest_session = ProfessionalAssessmentSession.query.filter_by(
                user_id=user_id,
                cohort=cohort
            ).filter(
                ProfessionalAssessmentSession.status != 'in_progress'
            ).order_by(
                ProfessionalAssessmentSession.created_at.desc()
            ).first()

            if not latest_session or latest_session.responses.count() == 0:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_remembered_answers - "
                      f"用户 {user_id} 在组别 {cohort} 中没有历史记录")
                return {}, None

            # 获取所有回答
            responses = latest_session.responses.all()

            remembered = {}
            for resp in responses:
                remembered[resp.question_id] = {
                    'answer_text': resp.answer_text,
                    'raw_value': resp.raw_value
                }

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_remembered_answers - "
                  f"用户 {user_id} 组别 {cohort} 找到 {len(remembered)} 条记忆答案 "
                  f"(来源会话 {latest_session.id})")

            return remembered, None

        except Exception as e:
            error_msg = f"获取记忆答案失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_remembered_answers - {error_msg}")
            import traceback
            traceback.print_exc()
            return {}, error_msg

    @staticmethod
    def complete_session(session_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        将会话标记为已完成

        Args:
            session_id: 会话ID
            user_id: 用户ID（用于验证所有权）

        Returns:
            (是否成功, 错误信息)
        """
        try:
            session, error = ProfessionalAssessmentService.get_session(session_id, user_id)
            if error:
                return False, error

            if session.status == 'in_progress':
                session.status = 'completed'
                session.completed_at = datetime.now()
                db.session.commit()
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.complete_session - "
                      f"会话 {session_id} 已标记为完成")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.complete_session - "
                      f"会话 {session_id} 状态为 {session.status}，无需变更")

            return True, None

        except Exception as e:
            db.session.rollback()
            error_msg = f"完成会话失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.complete_session - {error_msg}")
            return False, error_msg

    @staticmethod
    def save_submission_answers(session_id: int, answers_by_question_id: Dict[str, str],
                                 matrix_answers: Dict[str, Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        """
        批量保存提交的答案到数据库（提交时使用，不检查会话状态以确保可用）

        Args:
            session_id: 会话ID
            answers_by_question_id: {question_id: answer_text} 格式的普通答案
            matrix_answers: {question_id: {rowIndex: optionKey}} 格式的矩阵答案

        Returns:
            (是否成功, 错误信息)
        """
        try:
            session = ProfessionalAssessmentSession.query.get(session_id)
            if not session:
                return False, "会话不存在"

            now = datetime.now()

            # 批量保存普通答案
            for question_id, answer_text in answers_by_question_id.items():
                existing = ProfessionalAssessmentResponse.query.filter_by(
                    session_id=session_id, question_id=question_id).first()
                if existing:
                    existing.answer_text = str(answer_text)
                    existing.response_timestamp = now
                else:
                    db.session.add(ProfessionalAssessmentResponse(
                        session_id=session_id,
                        question_id=question_id,
                        answer_text=str(answer_text),
                        response_timestamp=now
                    ))

            # 批量保存矩阵题答案
            for question_id, rows in matrix_answers.items():
                if not rows:
                    continue
                answer_text = json.dumps(rows)
                existing = ProfessionalAssessmentResponse.query.filter_by(
                    session_id=session_id, question_id=question_id).first()
                if existing:
                    existing.answer_text = answer_text
                    existing.response_timestamp = now
                else:
                    db.session.add(ProfessionalAssessmentResponse(
                        session_id=session_id,
                        question_id=question_id,
                        answer_text=answer_text,
                        response_timestamp=now
                    ))

            db.session.commit()

            # 重新统计已回答数量并更新进度
            total_answered = ProfessionalAssessmentResponse.query.filter_by(
                session_id=session_id).count()
            session.answered_count = total_answered
            if session.answered_count >= session.question_count and session.status == 'in_progress':
                session.status = 'completed'
                session.completed_at = now
            db.session.commit()

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.save_submission_answers - "
                  f"会话 {session_id} 已保存 {len(answers_by_question_id) + len(matrix_answers)} 个答案")

            return True, None

        except Exception as e:
            db.session.rollback()
            error_msg = f"批量保存答案失败: {str(e)}"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.save_submission_answers - {error_msg}")
            return False, error_msg

    @staticmethod
    def get_all_questions():
        """获取所有问卷问题"""
        try:
            questions = QuestionnaireQuestion.query.order_by(QuestionnaireQuestion.question_id).all()
            return questions
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ProfessionalAssessmentService.get_all_questions - 错误: {str(e)}")
            return []

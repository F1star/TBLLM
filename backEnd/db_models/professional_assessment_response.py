from config.settings import db
from datetime import datetime


class ProfessionalAssessmentResponse(db.Model):
    """
    专业测评回答表
    存储用户在专业测评会话中的回答
    """
    __tablename__ = 'professional_assessment_response'

    id = db.Column(db.Integer, primary_key=True)
    # 会话ID，外键关联到ProfessionalAssessmentSession
    session_id = db.Column(db.Integer, db.ForeignKey('professional_assessment_session.id'), nullable=False, index=True)
    # 问题ID，关联到QuestionnaireQuestion的question_id字段
    question_id = db.Column(db.String(100), nullable=False, index=True)
    # 原始数值回答（如果有）
    raw_value = db.Column(db.Float, nullable=True)
    # 文本回答
    answer_text = db.Column(db.Text, nullable=True)
    # 回答时间
    response_timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    # 回答顺序（可选，用于保持问题顺序）
    question_order = db.Column(db.Integer, nullable=True, default=0)

    # 索引：会话和问题的组合索引，确保每个问题在每个会话中只回答一次
    __table_args__ = (
        db.Index('idx_session_question', 'session_id', 'question_id', unique=True),
    )

    def __repr__(self):
        return f'<ProfessionalAssessmentResponse session:{self.session_id} question:{self.question_id}>'

    def to_dict(self):
        """转换为字典，用于JSON序列化"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'raw_value': self.raw_value,
            'answer_text': self.answer_text,
            'response_timestamp': self.response_timestamp.isoformat() if self.response_timestamp else None,
            'question_order': self.question_order
        }
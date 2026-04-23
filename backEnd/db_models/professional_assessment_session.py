from config.settings import db
from datetime import datetime


class ProfessionalAssessmentSession(db.Model):
    """
    专业测评会话表
    存储用户进行的专业测评会话
    """
    __tablename__ = 'professional_assessment_session'

    id = db.Column(db.Integer, primary_key=True)
    # 用户ID，外键关联到User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    # 会话名称
    name = db.Column(db.String(200), nullable=False, default='专业测评')
    # 状态：'in_progress'（进行中），'completed'（已完成），'evaluated'（已评估）
    status = db.Column(db.String(20), nullable=False, default='in_progress', index=True)
    # 创建时间
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # 完成时间
    completed_at = db.Column(db.DateTime, nullable=True)
    # 评估ID，外键关联到Evaluation
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=True)
    # 关联的学生组别：'younger'（年轻组）或 'elderly'（年长组）
    cohort = db.Column(db.String(20), nullable=True, index=True)
    # 问题数量
    question_count = db.Column(db.Integer, nullable=False, default=0)
    # 已回答数量
    answered_count = db.Column(db.Integer, nullable=False, default=0)

    # 与ProfessionalAssessmentResponse的关系
    responses = db.relationship('ProfessionalAssessmentResponse', backref='session', lazy='dynamic',
                                cascade='all, delete-orphan')
    # 与Evaluation的关系（通过evaluation_id连接）
    evaluation = db.relationship('Evaluation', foreign_keys=[evaluation_id], lazy='joined')
    # 与User的关系
    user = db.relationship('User', backref='assessment_sessions', lazy='joined')

    def __repr__(self):
        return f'<ProfessionalAssessmentSession {self.id}: {self.name} ({self.status})>'

    def to_dict(self):
        """转换为字典，用于JSON序列化"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'status': self.status,
            'cohort': self.cohort,
            'question_count': self.question_count,
            'answered_count': self.answered_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'evaluation_id': self.evaluation_id,
            'evaluation': self.evaluation.to_dict() if self.evaluation else None
        }

    def update_progress(self):
        """更新进度（已回答数量）"""
        self.answered_count = self.responses.count()
        if self.answered_count >= self.question_count and self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = datetime.now()
        db.session.commit()

    def mark_as_evaluated(self, evaluation_id):
        """标记为已评估"""
        self.status = 'evaluated'
        self.evaluation_id = evaluation_id
        db.session.commit()
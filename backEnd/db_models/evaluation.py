from config.settings import db

class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=True)
    chat_history_id = db.Column(db.Integer, db.ForeignKey('chat_history.id'), nullable=True)
    # 专业测评会话ID，外键关联到ProfessionalAssessmentSession
    assessment_session_id = db.Column(db.Integer, db.ForeignKey('professional_assessment_session.id'), nullable=True)
    logic_score = db.Column(db.Float, default=0.0)
    creativity_score = db.Column(db.Float, default=0.0)
    expression_score = db.Column(db.Float, default=0.0)
    knowledge_score = db.Column(db.Float, default=0.0)
    overall_score = db.Column(db.Float, default=0.0)
    skill_scores = db.Column(db.JSON, nullable=True)  # 存储完整的17项技能分数
    feedback = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # 与ProfessionalAssessmentSession的关系
    assessment_session = db.relationship('ProfessionalAssessmentSession', foreign_keys=[assessment_session_id], backref='evaluation_records', lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'chat_history_id': self.chat_history_id,
            'assessment_session_id': self.assessment_session_id,
            'logic_score': self.logic_score,
            'creativity_score': self.creativity_score,
            'expression_score': self.expression_score,
            'knowledge_score': self.knowledge_score,
            'overall_score': self.overall_score,
            'skill_scores': self.skill_scores,
            'feedback': self.feedback,
            'timestamp': (self.timestamp.isoformat() + 'Z') if self.timestamp else None,
        }

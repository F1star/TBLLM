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
    feedback = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # 与ProfessionalAssessmentSession的关系
    assessment_session = db.relationship('ProfessionalAssessmentSession', foreign_keys=[assessment_session_id], backref='evaluation_records', lazy='joined')

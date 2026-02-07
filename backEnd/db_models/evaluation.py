from config.settings import db

class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_history_id = db.Column(db.Integer, db.ForeignKey('chat_history.id'), nullable=False)
    logic_score = db.Column(db.Float, default=0.0)
    creativity_score = db.Column(db.Float, default=0.0)
    expression_score = db.Column(db.Float, default=0.0)
    knowledge_score = db.Column(db.Float, default=0.0)
    overall_score = db.Column(db.Float, default=0.0)
    feedback = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

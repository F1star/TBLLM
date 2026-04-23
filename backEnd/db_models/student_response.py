from config.settings import db

class StudentResponse(db.Model):
    """
    学生回答表
    存储每个学生对每个问题的回答
    """
    __tablename__ = 'student_response'

    id = db.Column(db.Integer, primary_key=True)
    # 虚拟学生ID，外键关联到VirtualStudent
    virtual_student_id = db.Column(db.Integer, db.ForeignKey('virtual_student.id'), nullable=False, index=True)
    # 问题ID，外键关联到QuestionnaireQuestion的question_id字段
    question_id = db.Column(db.String(100), nullable=False, index=True)
    # 原始数值回答（SPSS中的数值）
    raw_value = db.Column(db.Float, nullable=True)
    # 解码后的文本回答
    answer_text = db.Column(db.Text, nullable=True)
    # 数据收集时间（使用数据集中的时间或导入时间）
    response_timestamp = db.Column(db.DateTime, nullable=True)
    # 导入时间
    imported_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # 与QuestionnaireQuestion的关系（通过question_id关联，不是外键约束）
    # 注意：这里使用question_id作为关联字段，不是外键约束
    # 可以通过 backref='responses' 在QuestionnaireQuestion中访问

    # 索引
    # __table_args__ = (
    #     db.Index('idx_student_question', 'virtual_student_id', 'question_id'),
    # )

    def __repr__(self):
        return f'<StudentResponse student:{self.virtual_student_id} question:{self.question_id} answer:{self.answer_text[:50] if self.answer_text else self.raw_value}>'

    def to_dict(self):
        """转换为字典，用于JSON序列化"""
        return {
            'id': self.id,
            'virtual_student_id': self.virtual_student_id,
            'question_id': self.question_id,
            'raw_value': self.raw_value,
            'answer_text': self.answer_text,
            'response_timestamp': self.response_timestamp.isoformat() if self.response_timestamp else None,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None
        }
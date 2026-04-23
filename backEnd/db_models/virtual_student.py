from config.settings import db

class VirtualStudent(db.Model):
    """
    虚拟学生表
    代表数据集中的中国学生，用于关联他们的回答
    """
    __tablename__ = 'virtual_student'

    id = db.Column(db.Integer, primary_key=True)
    # 数据集中的原始学生ID (FullID)
    original_student_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    # 虚拟用户名，唯一
    username = db.Column(db.String(80), unique=True, nullable=False)
    # 虚拟邮箱，唯一
    email = db.Column(db.String(120), unique=True, nullable=False)
    # 哈希密码（统一密码）
    password = db.Column(db.String(120), nullable=False)
    # 地点代码 (SiteID)
    site_id = db.Column(db.String(20), nullable=False, index=True)
    # 问卷类型：'younger'（年轻组）或 'elderly'（年长组）
    cohort = db.Column(db.String(20), nullable=False, index=True)
    # 测试语言
    language = db.Column(db.String(10), nullable=False, default='zh')
    # 创建时间
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # 与StudentResponse的关系
    responses = db.relationship('StudentResponse', backref='student', lazy='dynamic')

    def __repr__(self):
        return f'<VirtualStudent {self.username} ({self.original_student_id})>'

    def to_dict(self):
        """转换为字典，用于JSON序列化"""
        return {
            'id': self.id,
            'original_student_id': self.original_student_id,
            'username': self.username,
            'email': self.email,
            'site_id': self.site_id,
            'cohort': self.cohort,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
from config.settings import db
import json

class QuestionnaireQuestion(db.Model):
    """
    问卷问题定义表
    存储问卷中的问题文本、选项和元数据
    """
    __tablename__ = 'questionnaire_question'

    id = db.Column(db.Integer, primary_key=True)
    # 问题ID，如 STQM00101, COGM00101
    question_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    # 问题完整文本
    question_text = db.Column(db.Text, nullable=False)
    # 问卷类型：'younger'（年轻组）或 'elderly'（年长组）
    cohort = db.Column(db.String(20), nullable=False, index=True)
    # 问题类型：'text'（填空题）, 'single_choice'（单选题）,
    # 'multiple_choice'（多选题）, 'matrix'（矩阵题）, 'table'（表格题）
    question_type = db.Column(db.String(30), nullable=False, default='single_choice')
    # 选项映射，JSON格式：{"1": "选项文本1", "2": "选项文本2", ...}
    # 对于填空题，可为空
    options_json = db.Column(db.Text, nullable=True)
    # 额外元数据，JSON格式：{"subquestion_text": "子问题文本", "matrix_index": "a", ...}
    metadata_json = db.Column(db.Text, nullable=True)
    # 创建时间
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # 注意：与StudentResponse的关联通过question_id字段，没有外键关系
    # 因此不定义ORM关系，通过查询手动关联

    def __repr__(self):
        return f'<QuestionnaireQuestion {self.question_id}: {self.question_text[:50]}...>'

    # @property
    # def options(self):
    #     """获取选项字典"""
    #     if self.options_json:
    #         try:
    #             return json.loads(self.options_json)
    #         except json.JSONDecodeError:
    #             return {}
    #     return {}
    #
    # @options.setter
    # def options(self, value):
    #     """设置选项字典"""
    #     self.options_json = json.dumps(value, ensure_ascii=False) if value else None
    #
    # @property
    # def metadata(self):
    #     """获取元数据字典"""
    #     if self.metadata_json:
    #         try:
    #             return json.loads(self.metadata_json)
    #         except json.JSONDecodeError:
    #             return {}
    #     return {}
    #
    # @metadata.setter
    # def metadata(self, value):
    #     """设置元数据字典"""
    #     self.metadata_json = json.dumps(value, ensure_ascii=False) if value else None
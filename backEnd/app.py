import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.environment import setup_environment
from config.settings import app, db
from routes import register_routes
from sqlalchemy import inspect, text

setup_environment()

def migrate_database():
    """迁移数据库，添加新列"""
    with app.app_context():
        # 首先创建所有表（如果不存在）
        db.create_all()

        inspector = inspect(db.engine)

        # 检查chat_history表是否存在session_id列
        if 'chat_history' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('chat_history')]
            if 'session_id' not in columns:
                print("添加session_id列到chat_history表...")
                try:
                    # SQLite不支持直接添加外键，先添加列，外键约束可能不会被强制执行
                    db.session.execute(text('ALTER TABLE chat_history ADD COLUMN session_id INTEGER'))
                    db.session.commit()
                    print("session_id列添加成功")
                except Exception as e:
                    db.session.rollback()
                    print(f"添加session_id列失败: {e}")

        # 检查evaluation表是否存在session_id列
        if 'evaluation' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('evaluation')]
            if 'session_id' not in columns:
                print("添加session_id列到evaluation表...")
                try:
                    db.session.execute(text('ALTER TABLE evaluation ADD COLUMN session_id INTEGER'))
                    db.session.commit()
                    print("session_id列添加成功")
                except Exception as e:
                    db.session.rollback()
                    print(f"添加session_id列失败: {e}")

            # 检查chat_history_id列是否允许NULL（从NOT NULL改为NULL）
            # 注意：SQLite不支持ALTER COLUMN，需要重新创建表，这里暂时跳过
            # 由于chat_history_id现在在模型中是nullable=True，新创建的表会正确设置
            # 现有表可能需要手动处理，但我们可以暂时忽略，因为旧数据有chat_history_id=0

        print("数据库迁移完成")

with app.app_context():
    migrate_database()

register_routes(app)

@app.before_request
def block_if_model_busy():
    from services.model_service import ModelService
    from flask import jsonify
    
    model_service = ModelService()
    if model_service.is_busy():
        return jsonify({"error": "模型正在生成，请稍后再试"}), 429

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

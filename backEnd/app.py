import sys
import os
from datetime import datetime

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
            # 注意：SQLite不支持ALTER COLUMN，需要重新创建表
            # 检查chat_history_id列是否定义为NOT NULL
            for col in inspector.get_columns('evaluation'):
                if col['name'] == 'chat_history_id' and not col.get('nullable', True):
                    print("修复evaluation表chat_history_id列的NULL约束...")
                    _fix_evaluation_table_constraint(inspector)
                    break

        print("数据库迁移完成")

def _fix_evaluation_table_constraint(inspector):
    """修复evaluation表中chat_history_id列的NOT NULL约束"""
    try:
        # 1. 创建新表evaluation_new，使用正确的约束（chat_history_id允许NULL）
        # 首先获取原始表的定义并修改
        db.session.execute(text('''
            CREATE TABLE evaluation_new (
                id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                chat_history_id INTEGER,
                logic_score FLOAT,
                creativity_score FLOAT,
                expression_score FLOAT,
                knowledge_score FLOAT,
                overall_score FLOAT,
                feedback TEXT,
                timestamp DATETIME,
                session_id INTEGER,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES user (id),
                FOREIGN KEY(chat_history_id) REFERENCES chat_history (id)
            )
        '''))

        # 2. 复制数据，将chat_history_id=0转换为NULL
        db.session.execute(text('''
            INSERT INTO evaluation_new
            SELECT
                id,
                user_id,
                CASE WHEN chat_history_id = 0 THEN NULL ELSE chat_history_id END,
                logic_score,
                creativity_score,
                expression_score,
                knowledge_score,
                overall_score,
                feedback,
                timestamp,
                session_id
            FROM evaluation
        '''))

        # 3. 删除旧表
        db.session.execute(text('DROP TABLE evaluation'))

        # 4. 重命名新表
        db.session.execute(text('ALTER TABLE evaluation_new RENAME TO evaluation'))

        db.session.commit()
        print("成功修复evaluation表的chat_history_id约束")

    except Exception as e:
        db.session.rollback()
        print(f"修复evaluation表约束失败: {e}")
        print("注意：评估功能可能无法正常工作，chat_history_id列需要允许NULL")

with app.app_context():
    migrate_database()

register_routes(app)

@app.before_request
def block_if_model_busy():
    from services.model_service import ModelService
    from flask import jsonify, request
    
    model_service = ModelService()
    if model_service.is_busy():
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型繁忙，请求被拒绝: {request.path}")
        return jsonify({"error": "模型正在生成，请稍后再试"}), 429

if __name__ == '__main__':
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动青少年综合能力评价系统后端服务")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 监听地址: http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)

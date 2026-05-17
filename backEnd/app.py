import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.environment import setup_environment
from config.settings import app, db
from routes import register_routes
from sqlalchemy import inspect, text
from config.constants import LOG_LEVEL, ENABLE_DETAILED_LOGGING

setup_environment()

# 配置详细日志
def setup_logging():
    """配置应用程序日志，启用详细日志输出"""
    # 解析日志级别
    log_level = getattr(logging, LOG_LEVEL.upper()) if hasattr(logging, LOG_LEVEL.upper()) else logging.DEBUG

    # 设置根日志级别
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 如果已有处理程序，移除它们（避免重复）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建控制台处理程序
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 添加处理程序
    root_logger.addHandler(console_handler)

    # 如果启用详细日志，特别为Agent和RAG模块设置DEBUG级别
    if ENABLE_DETAILED_LOGGING:
        logging.getLogger('services.advanced_agent').setLevel(logging.DEBUG)
        logging.getLogger('services.rag_service').setLevel(logging.DEBUG)
        logging.getLogger('services.vector_store').setLevel(logging.DEBUG)
        logging.getLogger('services.agent_tools_enhanced').setLevel(logging.DEBUG)

        # 降低transformers等库的日志级别，避免过多输出
        logging.getLogger('transformers').setLevel(logging.WARNING)
        logging.getLogger('langchain').setLevel(logging.WARNING)
        logging.getLogger('chromadb').setLevel(logging.WARNING)

        logging.info(f"详细日志已启用，级别：{LOG_LEVEL}（Agent和RAG模块：DEBUG）")
    else:
        logging.info(f"标准日志已启用，级别：{LOG_LEVEL}")

# 初始化日志
setup_logging()

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

            # 检查是否存在skill_scores列（JSON类型存储17项技能分数）
            if 'skill_scores' not in columns:
                print("添加skill_scores列到evaluation表...")
                try:
                    db.session.execute(text('ALTER TABLE evaluation ADD COLUMN skill_scores JSON'))
                    db.session.commit()
                    print("skill_scores列添加成功")
                except Exception as e:
                    db.session.rollback()
                    print(f"添加skill_scores列失败: {e}")

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
                assessment_session_id INTEGER,
                skill_scores JSON,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES user (id),
                FOREIGN KEY(chat_history_id) REFERENCES chat_history (id),
                FOREIGN KEY(assessment_session_id) REFERENCES professional_assessment_session (id)
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
                session_id,
                assessment_session_id,
                skill_scores
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
    host = os.environ.get("TBLLM_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("TBLLM_BACKEND_PORT", "5050"))
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动青少年综合能力评价系统后端服务")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 监听地址: http://{host}:{port}")
    app.run(host=host, port=port, debug=True, use_reloader=False)

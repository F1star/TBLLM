import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.environment import setup_environment
from config.settings import app, db
from routes import register_routes

setup_environment()

with app.app_context():
    db.create_all()

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

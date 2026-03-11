import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-this-in-production'
app.config['SECRET_KEY'] = 'file-encryption-secret-key-change-this-in-production'
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'json']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app,
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"])

jwt = JWTManager(app)
db = SQLAlchemy(app)

# 导出配置
SECRET_KEY = app.config['SECRET_KEY']

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    from flask import jsonify
    return jsonify({'message': 'Token 已过期'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    from flask import jsonify
    return jsonify({'message': 'Token 无效'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    from flask import jsonify
    return jsonify({'message': '缺少 Token'}), 401

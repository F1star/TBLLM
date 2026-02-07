from flask import request, jsonify
from flask_jwt_extended import create_access_token
from db_models.user import User
from config.settings import db

def register():
    data = request.get_json()
    if not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'message': '缺少字段'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '邮箱已存在'}), 400

    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '注册成功'}), 201

def login():
    data = request.get_json()
    print(f"登录请求: {data}")
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or user.password != data.get('password'):
        print("账号或密码错误")
        return jsonify({'message': '账号或密码错误'}), 401

    token = create_access_token(identity=str(user.id))
    print(f"创建的 token: {token[:50]}... 用户ID: {user.id}")
    return jsonify({'access_token': token, 'username': user.username})

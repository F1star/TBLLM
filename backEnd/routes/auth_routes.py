from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
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

@jwt_required()
def change_password():
    try:
        uid = get_jwt_identity()
        data = request.get_json()
        
        if not all(k in data for k in ('current_password', 'new_password')):
            return jsonify({'error': '缺少字段'}), 400
        
        user = User.query.get(int(uid))
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.password != data.get('current_password'):
            return jsonify({'error': '当前密码错误'}), 400
        
        user.password = data.get('new_password')
        db.session.commit()
        
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from services.model_service import ModelService
from services.evaluation_service import EvaluationService

model_service = ModelService()

@jwt_required()
def evaluate_user_overall():
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] evaluate_user_overall - 用户ID: {uid}")

    # 从请求中获取文件ID列表、会话ID和深度思考模式
    data = request.get_json() or {}
    file_ids = data.get('file_ids', None)
    session_id = data.get('session_id', None)
    deep_mode = data.get('deep_mode', False)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] evaluate_user_overall - 文件IDs: {file_ids}, 会话ID: {session_id}, 深度思考: {deep_mode}")

    evaluation, error = EvaluationService.evaluate_user_overall(int(uid), model_service, file_ids, session_id, deep_mode)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] evaluate_user_overall - 评估结果: {error if error else '成功'}")

    if error:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] evaluate_user_overall - 评分错误: {error}")
        return jsonify({'error': error}), 500

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] evaluate_user_overall - 评估完成，ID: {evaluation.id}, 逻辑: {evaluation.logic_score}, 创造力: {evaluation.creativity_score}, 表达: {evaluation.expression_score}, 知识: {evaluation.knowledge_score}")
    return jsonify({
        'evaluation_id': evaluation.id,
        'session_id': evaluation.session_id,
        'logic_score': evaluation.logic_score,
        'creativity_score': evaluation.creativity_score,
        'expression_score': evaluation.expression_score,
        'knowledge_score': evaluation.knowledge_score,
        'overall_score': evaluation.overall_score,
        'feedback': evaluation.feedback,
        'timestamp': (evaluation.timestamp.isoformat() + 'Z') if evaluation.timestamp else None,
    })

@jwt_required()
def get_latest_evaluation():
    uid = get_jwt_identity()
    session_id = request.args.get('session_id', type=int)  # 可选
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_latest_evaluation - 用户ID: {uid}, 会话ID: {session_id}")
    evaluation = EvaluationService.get_latest_evaluation(int(uid), session_id)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_latest_evaluation - 获取到评估: {'是' if evaluation else '否'}")
    return jsonify(evaluation)

@jwt_required()
def get_evaluations():
    uid = get_jwt_identity()
    session_id = request.args.get('session_id', type=int)  # 可选
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_evaluations - 用户ID: {uid}, 会话ID: {session_id}")
    evaluations = EvaluationService.get_user_evaluations(int(uid), session_id)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_evaluations - 获取到评估数量: {len(evaluations)}")
    return jsonify(evaluations)


@jwt_required()
def delete_evaluation(evaluation_id):
    uid = int(get_jwt_identity())
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] delete_evaluation - 用户ID: {uid}, 评估ID: {evaluation_id}")
    success = EvaluationService.delete_evaluation(evaluation_id, uid)
    if not success:
        return jsonify({'error': '评估记录不存在或无权访问'}), 404
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] delete_evaluation - 删除成功")
    return jsonify({'message': '删除成功'})

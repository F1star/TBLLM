from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.model_service import ModelService
from services.evaluation_service import EvaluationService

model_service = ModelService()

@jwt_required()
def evaluate_user_overall():
    uid = get_jwt_identity()

    # 从请求中获取文件ID列表和会话ID
    data = request.get_json() or {}
    file_ids = data.get('file_ids', None)
    session_id = data.get('session_id', None)

    evaluation, error = EvaluationService.evaluate_user_overall(int(uid), model_service, file_ids, session_id)

    if error:
        print(f"评分错误: {error}")
        return jsonify({'error': error}), 500

    return jsonify({
        'evaluation_id': evaluation.id,
        'session_id': evaluation.session_id,
        'logic_score': evaluation.logic_score,
        'creativity_score': evaluation.creativity_score,
        'expression_score': evaluation.expression_score,
        'knowledge_score': evaluation.knowledge_score,
        'overall_score': evaluation.overall_score,
        'feedback': evaluation.feedback
    })

@jwt_required()
def get_latest_evaluation():
    uid = get_jwt_identity()
    session_id = request.args.get('session_id', type=int)  # 可选
    evaluation = EvaluationService.get_latest_evaluation(int(uid), session_id)
    return jsonify(evaluation)

@jwt_required()
def get_evaluations():
    uid = get_jwt_identity()
    session_id = request.args.get('session_id', type=int)  # 可选
    evaluations = EvaluationService.get_user_evaluations(int(uid), session_id)
    return jsonify(evaluations)

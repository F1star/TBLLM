from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from services.professional_assessment_service import ProfessionalAssessmentService

# 尝试导入模型服务，如果失败则创建模拟服务
try:
    from services.model_service import ModelService
    model_service = ModelService()
    MODEL_SERVICE_AVAILABLE = True
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型服务加载成功")
except Exception as e:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 模型服务加载失败: {e}")
    # 创建模拟模型服务
    class MockModelService:
        def optimize_question_text(self, question_text):
            # 返回模拟优化文本
            return f"[模拟优化] {question_text} (此优化文本为模拟数据，实际使用时需要加载模型)"

        def generate_professional_assessment(self, assessment_text, cohort):
            # 返回模拟专业测评结果
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MockModelService.generate_professional_assessment - 模拟评估, 组别: {cohort}")
            # 模拟评估数据
            import random
            # 生成模拟技能评分（17项社会情感技能）
            mock_skill_scores = {
                '责任感': random.uniform(70, 99),
                '同理心': random.uniform(65, 95),
                '成就动机': random.uniform(60, 90),
                '乐观': random.uniform(55, 90),
                '社交能力': random.uniform(60, 90),
                '自我效能': random.uniform(55, 85),
                '坚持': random.uniform(60, 90),
                '信任': random.uniform(55, 85),
                '合作': random.uniform(60, 90),
                '好奇心': random.uniform(65, 95),
                '创造力': random.uniform(60, 90),
                '抗压能力': random.uniform(50, 85),
                '活力': random.uniform(55, 85),
                '自我控制': random.uniform(50, 85),
                '情绪控制': random.uniform(50, 85),
                '包容': random.uniform(55, 85),
                '自信/主张': random.uniform(40, 80),
            }
            mock_overall = round(sum(mock_skill_scores.values()) / len(mock_skill_scores), 1)
            return {
                'skill_scores': mock_skill_scores,
                'overall_score': mock_overall,
                'feedback': '这是模拟评估结果。在实际使用中，系统会基于您的回答进行深度分析。您的表现显示了良好的潜力，建议继续努力。'
            }


    model_service = MockModelService()
    MODEL_SERVICE_AVAILABLE = False


@jwt_required()
def get_available_cohorts():
    """获取可用的学生组别"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_available_cohorts - 用户ID: {uid}")

    cohorts = ProfessionalAssessmentService.get_available_cohorts()
    return jsonify({'cohorts': cohorts})


@jwt_required()
def create_session():
    """创建新的专业测评会话"""
    uid = get_jwt_identity()
    data = request.get_json() or {}
    name = data.get('name')
    cohort = data.get('cohort')
    question_count = data.get('question_count', 10)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] create_session - 用户ID: {uid}, 名称: {name}, 组别: {cohort}, 问题数量: {question_count}")

    session, error = ProfessionalAssessmentService.create_session(
        user_id=int(uid),
        name=name,
        cohort=cohort,
        question_count=question_count
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': '会话创建成功',
        'session': session.to_dict()
    }), 201


@jwt_required()
def get_user_sessions():
    """获取用户的所有专业测评会话"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_user_sessions - 用户ID: {uid}")

    sessions, error = ProfessionalAssessmentService.get_user_sessions(int(uid))

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'sessions': [session.to_dict() for session in sessions]
    })


@jwt_required()
def get_session(session_id):
    """获取专业测评会话详情"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_session - 用户ID: {uid}, 会话ID: {session_id}")

    session, error = ProfessionalAssessmentService.get_session(int(session_id), int(uid))

    if error:
        return jsonify({'error': error}), 404

    return jsonify({
        'session': session.to_dict()
    })


@jwt_required()
def get_session_questions(session_id):
    """获取会话的问题列表"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_session_questions - 用户ID: {uid}, 会话ID: {session_id}")

    questions, error = ProfessionalAssessmentService.get_session_questions(int(session_id), int(uid))

    if error:
        return jsonify({'error': error}), 404

    return jsonify({
        'questions': questions,
        'total': len(questions)
    })


@jwt_required()
def submit_response(session_id):
    """提交回答"""
    uid = get_jwt_identity()
    data = request.get_json() or {}
    question_id = data.get('question_id')
    answer_text = data.get('answer_text')
    raw_value = data.get('raw_value')

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_response - 用户ID: {uid}, 会话ID: {session_id}, 问题ID: {question_id}")

    if not question_id or not answer_text:
        return jsonify({'error': '缺少问题ID或回答文本'}), 400

    response, error = ProfessionalAssessmentService.submit_response(
        session_id=int(session_id),
        question_id=question_id,
        answer_text=answer_text,
        raw_value=raw_value
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': '回答提交成功',
        'response': response.to_dict()
    })


@jwt_required()
def evaluate_session(session_id):
    """评估专业测评会话"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] evaluate_session - 用户ID: {uid}, 会话ID: {session_id}")

    evaluation, error = ProfessionalAssessmentService.evaluate_session(
        session_id=int(session_id),
        user_id=int(uid),
        model_service=model_service
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': '评估完成',
        'evaluation': {
            'id': evaluation.id,
            'logic_score': evaluation.logic_score,
            'creativity_score': evaluation.creativity_score,
            'expression_score': evaluation.expression_score,
            'knowledge_score': evaluation.knowledge_score,
            'overall_score': evaluation.overall_score,
            'feedback': evaluation.feedback,
            'timestamp': (evaluation.timestamp.isoformat() + 'Z') if evaluation.timestamp else None
        }
    })


@jwt_required()
def delete_session(session_id):
    """删除专业测评会话"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] delete_session - 用户ID: {uid}, 会话ID: {session_id}")

    success, error = ProfessionalAssessmentService.delete_session(int(session_id), int(uid))

    if error:
        return jsonify({'error': error}), 404

    return jsonify({
        'message': '会话删除成功'
    })


@jwt_required()
def complete_session(session_id):
    """标记专业测评会话为已完成"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] complete_session - 用户ID: {uid}, 会话ID: {session_id}")

    success, error = ProfessionalAssessmentService.complete_session(int(session_id), int(uid))

    if error:
        return jsonify({'error': error}), 400

    return jsonify({'message': '会话已标记为完成'})


@jwt_required()
def get_remembered_answers(cohort):
    """获取用户指定组别的历史回答记录（记忆功能）"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_remembered_answers - 用户ID: {uid}, 组别: {cohort}")

    remembered, error = ProfessionalAssessmentService.get_remembered_answers(int(uid), cohort)

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'cohort': cohort,
        'remembered_answers': remembered,
        'count': len(remembered)
    })


@jwt_required()
def get_all_questions():
    """获取所有问卷问题"""
    uid = get_jwt_identity()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] get_all_questions - 用户ID: {uid}")

    questions = ProfessionalAssessmentService.get_all_questions()

    # 格式化问题数据
    formatted_questions = []
    for q in questions:
        question_dict = {
            'question_id': q.question_id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'cohort': q.cohort,
            'options': {},
            'metadata': {},
            'original_text': None,
            'optimized_text': None
        }

        # 解析选项
        if q.options_json:
            try:
                import json
                question_dict['options'] = json.loads(q.options_json)
            except:
                pass

        # 解析元数据
        if q.metadata_json:
            try:
                import json
                metadata = json.loads(q.metadata_json)
                question_dict['metadata'] = metadata
                # 从元数据中提取原始文本
                question_dict['original_text'] = metadata.get('original_text', '')
                question_dict['original_text_zh'] = metadata.get('original_text_zh', '')
            except:
                pass

        formatted_questions.append(question_dict)

    return jsonify(formatted_questions)


@jwt_required()
def optimize_question():
    """优化问题描述"""
    uid = get_jwt_identity()
    data = request.get_json() or {}
    question_id = data.get('question_id')
    question_text = data.get('question_text')

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] optimize_question - 用户ID: {uid}, 问题ID: {question_id}")

    if not question_id or not question_text:
        return jsonify({'error': '缺少问题ID或问题文本'}), 400

    try:
        # 调用模型服务优化问题
        optimized_text = model_service.optimize_question_text(question_text)

        return jsonify({
            'question_id': question_id,
            'original_text': question_text,
            'optimized_text': optimized_text,
            'message': '问题优化成功'
        })
    except Exception as e:
        print(f"优化问题时出错: {e}")
        # 如果模型服务失败，返回模拟优化文本用于测试
        # 在实际使用中，这应该被移除或记录为错误
        simulated_optimized = f"[模拟优化] {question_text} (优化版本)"
        return jsonify({
            'question_id': question_id,
            'original_text': question_text,
            'optimized_text': simulated_optimized,
            'message': '问题优化成功(模拟)',
            'warning': '模型服务不可用，返回模拟结果'
        })


@jwt_required()
def submit_assessment():
    """提交专业测评答案并进行LLM评估"""
    uid = get_jwt_identity()
    data = request.get_json() or {}
    cohort = data.get('cohort')
    answers = data.get('answers', {})
    matrix_answers = data.get('matrix_answers', {})
    dialogue_data = data.get('dialogue_data', [])
    assessment_type = data.get('assessment_type', 'professional_assessment')
    session_id = data.get('session_id')
    answers_by_question_id = data.get('answers_by_question_id', {})

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 用户ID: {uid}, 组别: {cohort}, 答案数量: {len(answers)}, 矩阵答案: {len(matrix_answers)}")

    if not cohort:
        return jsonify({'error': '缺少组别信息'}), 400

    try:
        # === 将答案直接保存到后端数据库 ===
        if session_id:
            save_ok, save_err = ProfessionalAssessmentService.save_submission_answers(
                session_id=int(session_id),
                answers_by_question_id=answers_by_question_id,
                matrix_answers=matrix_answers
            )
            if not save_ok:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 保存答案到数据库失败: {save_err}")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 答案已保存到数据库")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 未提供session_id，跳过数据库保存")

        # 如果没有对话数据，尝试从answers和matrix_answers构建评估文本
        if dialogue_data and len(dialogue_data) > 0:
            # 使用对话格式进行评估
            # 提取对话文本
            conversations = dialogue_data[0].get('conversations', [])
            if conversations and len(conversations) > 0:
                assessment_text = conversations[0].get('value', '')
            else:
                assessment_text = "无对话数据"
        else:
            # 构建简单的评估文本
            assessment_text = f"学生组别: {cohort}\n\n"
            assessment_text += "学生回答:\n"

            # 处理普通答案
            for idx, answer in answers.items():
                if answer:  # 跳过空答案
                    assessment_text += f"问题{idx}: {answer}\n"

            # 处理矩阵答案
            for question_id, row_answers in matrix_answers.items():
                if row_answers:
                    assessment_text += f"矩阵问题{question_id}: {row_answers}\n"

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 评估文本长度: {len(assessment_text)}")

        # 调用模型服务进行评估
        try:
            evaluation_data = model_service.generate_professional_assessment(
                assessment_text=assessment_text,
                cohort=cohort
            )

            # 使用模型返回的技能评分（直接从文本解析得到，包含17项社会情感技能）
            skill_scores = evaluation_data.get('skill_scores', {})
            overall_score = evaluation_data.get('overall_score', 0)
            feedback = evaluation_data.get('feedback', '')

            result = {
                'skill_scores': skill_scores,
                'overall_score': overall_score,
                'feedback': feedback,
                'raw_evaluation': evaluation_data  # 包含原始评估数据
            }

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 评估完成 - 技能数: {len(skill_scores)}, 综合分数: {overall_score}")

            return jsonify({
                'message': '测评提交成功',
                'cohort': cohort,
                'answered_count': len(answers) + sum(len(v) for v in matrix_answers.values()),
                'timestamp': datetime.now().isoformat(),
                'assessment_result': result
            })

        except Exception as model_error:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 模型评估失败: {model_error}")
            # 如果模型服务不可用，返回模拟结果
            if not MODEL_SERVICE_AVAILABLE:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 使用模拟评估结果")
                # 模拟评估结果
                skill_scores = {
                    '责任感': 85.2,
                    '同理心': 78.5,
                    '成就动机': 82.0,
                    '乐观': 75.0,
                    '社交能力': 80.0,
                    '自我效能': 72.0,
                    '坚持': 78.0,
                    '信任': 74.0,
                    '合作': 80.0,
                    '好奇心': 88.0,
                    '创造力': 82.0,
                    '抗压能力': 70.0,
                    '活力': 75.0,
                    '自我控制': 72.0,
                    '情绪控制': 70.0,
                    '包容': 68.0,
                    '自信/主张': 62.0,
                }
                overall_score = 76.5
                feedback = '您的综合能力表现优秀，特别是在创新能力和学习能力方面表现突出。建议进一步加强沟通能力和适应能力的培养。'

                result = {
                    'skill_scores': skill_scores,
                    'overall_score': overall_score,
                    'feedback': feedback,
                    'warning': '模型服务不可用，返回模拟结果'
                }

                return jsonify({
                    'message': '测评提交成功(模拟)',
                    'cohort': cohort,
                    'answered_count': len(answers) + sum(len(v) for v in matrix_answers.values()),
                    'timestamp': datetime.now().isoformat(),
                    'assessment_result': result
                })
            else:
                raise model_error

    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] submit_assessment - 提交测评时出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'提交测评时出错: {str(e)}'}), 500



import json
import re
import torch
from config.settings import db
from config.constants import EVALUATION_PROMPT_TEMPLATE
from db_models.evaluation import Evaluation
from db_models.chat_history import ChatHistory
from services.chat_service import ChatService

class EvaluationService:
    @staticmethod
    def evaluate_user_overall(user_id, model_service):
        user_chats = ChatService.get_user_history(user_id)
        if not user_chats:
            return None, "暂无对话记录"
        
        # 1. 准备对话内容
        chat_content = '\n'.join([f"{c['role']}: {c['content']}" for c in user_chats[-20:]])
        
        # 2. 构造符合 Chat 规范的 Messages 列表
        # 建议将 EVALUATION_PROMPT_TEMPLATE 作为 system 角色或 user 角色传入
        messages = [
            {"role": "system", "content": "你是一个专业的文本分析助手，请严格按照 JSON 格式输出评估结果。"},
            {"role": "user", "content": EVALUATION_PROMPT_TEMPLATE.format(chat_content=chat_content)}
        ]
        
        try:
            # 3. 使用 apply_chat_template 生成输入文本
            input_text = model_service.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            inputs = model_service.tokenizer(
                [input_text], 
                return_tensors="pt"
            ).to(model_service.model.device)
            
            # 4. 推理生成
            with torch.inference_mode():
                outputs = model_service.model.generate(
                    **inputs,
                    max_new_tokens=512, # 评估通常包含 feedback，建议稍微大一点
                    temperature=0.3,    # 降低随机性，保证 JSON 格式更稳定
                    top_p=0.9,
                    do_sample=True,
                    repetition_penalty=1.1,
                    pad_token_id=model_service.tokenizer.eos_token_id
                )
            
            # 5. 【核心修改】精准截断，只保留模型生成的部分
            input_length = inputs.input_ids.shape[1]
            response_ids = outputs[0][input_length:]
            response = model_service.tokenizer.decode(response_ids, skip_special_tokens=True).strip()
            
            print("=" * 50)
            print("大模型生成的内容:")
            print(response)
            print("=" * 50)
            
            # 定义内部解析函数
            def extract_all_jsons(text):
                # 预处理：去掉 Markdown 代码块标记
                text = re.sub(r'```json\s*|\s*```', '', text).strip()
                # 寻找 JSON 对象
                jsons = []
                brace_count = 0
                start = -1
                for i, char in enumerate(text):
                    if char == '{':
                        if brace_count == 0: start = i
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and start != -1:
                            jsons.append(text[start:i+1])
                return jsons

            def is_evaluation_json(json_str):
                # 简单校验字段
                required = ["logic_score", "overall_score"]
                return all(field in json_str for field in required)
            
            all_jsons = extract_all_jsons(response)
            
            json_str = next((j for j in all_jsons if is_evaluation_json(j)), None)
            
            if json_str:
                evaluation_data = json.loads(json_str)
                evaluation = Evaluation(
                    user_id=user_id,
                    chat_history_id=0,
                    logic_score=evaluation_data.get('logic_score', 0),
                    creativity_score=evaluation_data.get('creativity_score', 0),
                    expression_score=evaluation_data.get('expression_score', 0),
                    knowledge_score=evaluation_data.get('knowledge_score', 0),
                    overall_score=evaluation_data.get('overall_score', 0),
                    feedback=evaluation_data.get('feedback', '')
                )
                db.session.add(evaluation)
                db.session.commit()
                return evaluation, None
            else:
                return None, f"解析失败，模型输出内容为: {response[:100]}..."
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None, f"评分失败: {str(e)}"
    
    @staticmethod
    def get_latest_evaluation(user_id):
        evaluation = Evaluation.query.filter_by(user_id=user_id).order_by(Evaluation.timestamp.desc()).first()
        if evaluation:
            return {
                'id': evaluation.id,
                'logic_score': evaluation.logic_score,
                'creativity_score': evaluation.creativity_score,
                'expression_score': evaluation.expression_score,
                'knowledge_score': evaluation.knowledge_score,
                'overall_score': evaluation.overall_score,
                'feedback': evaluation.feedback,
                'timestamp': evaluation.timestamp.isoformat()
            }
        return None
    
    @staticmethod
    def get_user_evaluations(user_id):
        evaluations = Evaluation.query.filter_by(user_id=user_id).order_by(Evaluation.timestamp.desc()).all()
        return [{
            'id': e.id,
            'chat_history_id': e.chat_history_id,
            'logic_score': e.logic_score,
            'creativity_score': e.creativity_score,
            'expression_score': e.expression_score,
            'knowledge_score': e.knowledge_score,
            'overall_score': e.overall_score,
            'feedback': e.feedback,
            'timestamp': e.timestamp.isoformat()
        } for e in evaluations]

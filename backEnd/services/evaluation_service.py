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
        
        chat_content = '\n'.join([f"{c['role']}: {c['content']}" for c in user_chats[-20:]])
        
        prompt = EVALUATION_PROMPT_TEMPLATE.format(chat_content=chat_content)
        
        print("=" * 50)
        print("评估Prompt:")
        print(prompt)
        print("=" * 50)
        
        try:
            inputs = model_service.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512
            ).to(model_service.model.device)
            
            with torch.inference_mode():
                outputs = model_service.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=model_service.tokenizer.eos_token_id,
                    eos_token_id=model_service.tokenizer.eos_token_id
                )
            
            response = model_service.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print("=" * 50)
            print("大模型原始输出:")
            print(response)
            print("=" * 50)
            
            def extract_all_jsons(text):
                text = text.strip()
                
                if text.startswith('```json'):
                    text = text[7:]
                elif text.startswith('```'):
                    text = text[3:]
                
                if text.endswith('```'):
                    text = text[:-3]
                
                text = text.strip()
                
                jsons = []
                i = 0
                
                while i < len(text):
                    start = text.find('{', i)
                    if start == -1:
                        break
                    
                    brace_count = 0
                    in_string = False
                    escape = False
                    
                    for j in range(start, len(text)):
                        char = text[j]
                        
                        if escape:
                            escape = False
                            continue
                        
                        if char == '\\':
                            escape = True
                            continue
                        
                        if char == '"':
                            in_string = not in_string
                            continue
                        
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    jsons.append(text[start:j+1])
                                    i = j + 1
                                    break
                    
                    if brace_count != 0:
                        i = start + 1
                
                return jsons
            
            def is_evaluation_json(json_str):
                pattern = r'"(logic_score|creativity_score|expression_score|knowledge_score|overall_score)"\s*:\s*\d+'
                matches = re.findall(pattern, json_str)
                return len(matches) >= 3
            
            all_jsons = extract_all_jsons(response)
            
            print("=" * 50)
            print(f"找到 {len(all_jsons)} 个JSON对象")
            print("=" * 50)
            
            json_str = None
            for j in all_jsons:
                if is_evaluation_json(j):
                    json_str = j
                    break
            
            if json_str:
                print("=" * 50)
                print("提取的JSON:")
                print(json_str)
                print("=" * 50)
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
                return None, "无法解析评分结果"
                
        except Exception as e:
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

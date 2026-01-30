import os
os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import warnings
warnings.filterwarnings('ignore')

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)

from peft import PeftModel
import threading

# ================= Flask 基础配置 =================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)

# ================= 数据库模型 =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_time = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

# ================= 模型加载 =================

BASE_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'models', 'deepseek-ai', 'deepseek-llm-7b-chat'
)

LORA_ADAPTER_PATH = os.path.join(
    os.path.dirname(__file__),
    'lora_adapter'   # 你训练好的 adapter 目录
)

# 🚨 Flask + 大模型 必须加锁
generate_lock = threading.Lock()

print("🚀 加载 DeepSeek 7B（4bit + LoRA / QLoRA 推理模式）")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    # 核心：允许量化模型将部分层卸载到 CPU
    llm_int8_enable_fp32_cpu_offload=True 
)

tokenizer = None
model = None

try:
    print("📦 加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_PATH,
        trust_remote_code=True,
        use_fast=False
    )

    print("🧠 加载 4bit base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        # 极致压缩显存占用，给系统留出空间
        max_memory={0: "2.8GiB", "cpu": "20GiB"}, 
        offload_folder="offload" # 必须指定一个真实存在的文件夹名
    )

    print("🧩 加载 LoRA / QLoRA adapter...")
    model = PeftModel.from_pretrained(
        base_model,
        LORA_ADAPTER_PATH,
        device_map="auto"
    )

    model.eval()
    model.config.use_cache = True   # 推理必须开 cache

    print("✅ 模型加载完成")
    print(f"📍 模型设备: {next(model.parameters()).device}")
    print(f"💾 显存占用: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

except Exception as e:
    import traceback
    print("❌ 模型加载失败")
    traceback.print_exc()
    model = None
    tokenizer = None


# ================= 对话逻辑 =================
chat_history = {}

MAX_CONTEXT_CHARS = 800
MAX_NEW_TOKENS = 128

def generate_response(prompt, user_id):
    if model is None or tokenizer is None:
        return "模型未正确加载，请检查服务器日志。"

    # 🚨 同一时间只允许一个生成任务
    with generate_lock:
        try:
            history = chat_history.get(user_id, "")
            full_prompt = (history + prompt)[-MAX_CONTEXT_CHARS:]

            inputs = tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(model.device)

            with torch.inference_mode():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    temperature=0.6,
                    top_p=0.85,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id
                )

            decoded = tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )

            response = decoded[len(full_prompt):].strip()

            # 只保留少量上下文
            chat_history[user_id] = (
                full_prompt + response
            )[-MAX_CONTEXT_CHARS:]

            return response or "（模型未生成有效内容）"

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                torch.cuda.empty_cache()
                return "显存不足，请稍后重试或清空对话。"
            return f"推理错误: {str(e)}"

@app.before_request
def block_if_model_busy():
    if generate_lock.locked():
        return jsonify({"error": "模型正在生成，请稍后再试"}), 429

# ================= API =================
@app.route('/api/register', methods=['POST'])
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

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or user.password != data.get('password'):
        return jsonify({'message': '账号或密码错误'}), 401

    token = create_access_token(identity=user.id)
    return jsonify({'access_token': token, 'username': user.username})

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    data = request.get_json()
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'error': '消息不能为空'}), 400

    uid = get_jwt_identity()
    reply = generate_response(msg, uid)
    return jsonify({'response': reply})

@app.route('/api/chat/clear', methods=['POST'])
@jwt_required()
def clear_chat():
    chat_history.pop(get_jwt_identity(), None)
    return jsonify({'message': '对话已清空'})

# ================= 启动 =================
if __name__ == '__main__':
    app.run(debug=True)

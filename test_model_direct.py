import os
import sys
import torch

print("禁用transformers的torch版本检查...")
os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import transformers
print(f"Transformers版本: {transformers.__version__}")
print(f"PyTorch版本: {torch.__version__}")

from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_PATH = os.path.join('models', 'deepseek-ai', 'deepseek-llm-7b-chat')
print(f"模型路径: {MODEL_PATH}")

try:
    print("加载tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    print("Tokenizer加载成功！")
    
    print("加载模型到CPU...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float32,
        use_safetensors=False
    )
    
    print("模型加载成功！")
    print(f"模型设备: {next(model.parameters()).device}")
    print(f"模型参数数量: {sum(p.numel() for p in model.parameters()) / 1e9:.2f}B")
    
except Exception as e:
    import traceback
    print(f"模型加载失败: {e}")
    print("详细错误信息:")
    traceback.print_exc()

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    'models', 'Qwen1.5-1.8B-Chat'
)

MAX_CONTEXT_CHARS = 800
MAX_NEW_TOKENS = 128

EVALUATION_PROMPT_TEMPLATE = """
你是一位专业的教育评估专家，要对青少年的对话进行评估，请根据以下对话内容，从四个维度对用户（user）一方的对话进行评分（0-100分）：

对话内容：
{chat_content}

请从以下四个维度进行评分：
1. 逻辑思维（Logic）：评估回答的逻辑性、条理性和推理能力
2. 创造力（Creativity）：评估回答的创新性、独特性和想象力
3. 表达能力（Expression）：评估回答的清晰度、准确性和语言组织能力
4. 知识广度（Knowledge）：评估回答的知识深度、准确性和覆盖面

请以JSON格式返回评分结果，格式如下：
{{
    "logic_score": 分数,
    "creativity_score": 分数,
    "expression_score": 分数,
    "knowledge_score": 分数,
    "overall_score": 平均分,
    "feedback": "简要的反馈意见"
}}

注意：
- 所有分数必须是0-100之间的整数
- overall_score为四个维度的平均分
- feedback应该包含具体的改进建议
"""

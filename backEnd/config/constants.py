import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 原始模型路径
ORIGINAL_MODEL_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    'models', 'Qwen1.5-1.8B-Chat'
)

# 微调模型路径
FINETUNED_MODEL_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    'lora_weights'
)

MAX_CONTEXT_CHARS = 8000
MAX_NEW_TOKENS = 1280

# 普通聊天生成配置。评估类任务仍使用 MAX_NEW_TOKENS，避免影响长文本评估输出。
CHAT_MAX_NEW_TOKENS = 768
CHAT_TEMPERATURE = 0.2
CHAT_TOP_P = 0.8
CHAT_HISTORY_LIMIT = 6
CHAT_MESSAGE_CONTEXT_CHARS = 1200
CHAT_SYSTEM_PROMPT = """你是“智评小助手”，面向学生的友好 AI 对话助手。
请严格遵守以下规则：
1. 只回答用户当前明确提出的问题。
2. 不要脑补未说明的知识点、学科、作业内容或背景。
3. 如果用户说某个知识没听懂但没有说明具体知识点，先共情安慰，再询问具体是哪一个知识点或哪一部分，不要直接讲解某个学科内容。
4. 简单寒暄或情绪支持默认用 2-5 句话回答；当用户明确询问具体知识、步骤、原因或方案时，要完整回答，可以分段或列要点，不要中途停在半句话。
5. 如果引用历史对话，只使用与当前问题直接相关的内容。"""

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

# LangChain 框架配置
# =============================================================================

# AdvancedAgent 配置
USE_ADVANCED_AGENT = True  # 是否使用AdvancedAgent（True：使用，False：使用原版AgentService）

# 向量存储配置
VECTOR_STORE_PATH = os.path.join(BASE_DIR, "vector_store")
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_COLLECTION_NAME = "user_documents"

# RAG 配置
USE_VECTOR_RETRIEVAL = True  # 是否使用向量检索（True：使用，False：使用关键词检索）
RAG_TOP_K = 3  # 检索返回的文档数量
RAG_CHUNK_SIZE = 500  # 文本分块大小
RAG_CHUNK_OVERLAP = 50  # 文本分块重叠大小

# Agent 配置
AGENT_MAX_ITERATIONS = 5  # Agent最大迭代次数（工具调用次数）
AGENT_VERBOSE = True  # 是否输出详细日志

# 日志配置
ENABLE_DETAILED_LOGGING = True  # 是否启用详细日志（DEBUG级别）
LOG_LEVEL = "DEBUG" if ENABLE_DETAILED_LOGGING else "INFO"

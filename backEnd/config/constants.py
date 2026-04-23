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

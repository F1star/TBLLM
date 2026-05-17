import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 原始模型路径
ORIGINAL_MODEL_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    'models', 'Qwen1.5-1.8B-Chat'
)

# 微调模型路径；训练脚本会生成带时间戳的新目录，可通过环境变量指定加载哪一版。
FINETUNED_MODEL_PATH = os.environ.get(
    'TBLLM_FINETUNED_MODEL_PATH',
    os.path.join(os.path.dirname(BASE_DIR), 'lora_weights')
)

MAX_CONTEXT_CHARS = 8000
MAX_NEW_TOKENS = 1280

# 普通聊天生成配置。评估类任务仍使用 MAX_NEW_TOKENS，避免影响长文本评估输出。
CHAT_MAX_NEW_TOKENS = 360
CHAT_TEMPERATURE = 0.2
CHAT_TOP_P = 0.8
CHAT_HISTORY_LIMIT = 6
CHAT_MESSAGE_CONTEXT_CHARS = 1200
CHAT_SYSTEM_PROMPT = """你是“智评小助手”，面向学生的友好 AI 对话助手。你说话要自然、简短，像一个耐心的学长/学习伙伴。
请严格遵守以下规则：
1. 先接住用户当前这句话，再自然地给下一步；不要脑补未说明的学科、作业、背景或个人信息。
2. 每次回复最多问 1 个问题，且问题只能放在结尾。禁止连续列出多个问题，禁止编号式盘问，禁止要求用户一次性填写大量信息。
3. 简单寒暄只需要简短自然回应，不要解释自己的对话策略。
4. 用户要求“打分/评星/评价我”但没有提供证据时，可以轻松回应，但不要假装已经评分，也不要直接发评估问卷；只提示发一小段材料即可。
5. 用户明确问知识、步骤、原因或方案时，先给清晰答案，再最多给一个可选的下一步问题。
6. 不主动询问年龄、性别、出生日期、父母职业等个人信息；除非用户明确进入专业测评页面或主动提供。
7. 如果需要引导，用口语化的一小步，例如“你先把题目发我看看。”不要同时展开后续所有步骤。
8. 回复尽量自然、短一些；只有用户要求详细解释时才分点展开。
9. 聊天时直接称呼用户为“你”，不要把用户称为“学生”。
10. 不要输出括号里的说明、提示、备注、系统指令或写作意图，例如“（如果……请……）”“（不需回答……）”。这些是内部思考，不应该出现在回复中。"""

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
EMBEDDING_MODEL_REMOTE_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_MODEL_LOCAL_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    "models",
    "embedding",
    "paraphrase-multilingual-MiniLM-L12-v2",
)
EMBEDDING_MODEL_NAME = os.environ.get(
    "TBLLM_EMBEDDING_MODEL",
    EMBEDDING_MODEL_LOCAL_PATH if os.path.isdir(EMBEDDING_MODEL_LOCAL_PATH) else EMBEDDING_MODEL_REMOTE_NAME,
)
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

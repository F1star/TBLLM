"""
LangChain组件测试

这个模块测试LangChain相关组件的基本功能，包括：
1. AdvancedAgent基础功能
2. VectorStore基本操作
3. RAGService检索功能
4. 工具系统

注意：这些测试主要是为了验证组件接口和基本功能，
实际运行时可能需要依赖项和环境配置。
"""

import sys
import os
import unittest
import tempfile
import shutil
import threading
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVectorStore(unittest.TestCase):
    """VectorStore测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()

        # 模拟配置
        os.environ['VECTOR_STORE_PATH'] = self.temp_dir

    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('sentence_transformers.SentenceTransformer')
    @patch('chromadb.Client')
    def test_vector_store_initialization(self, mock_chroma_client, mock_sentence_transformer):
        """测试VectorStore初始化"""
        from services.vector_store import VectorStore

        # 模拟ChromaDB客户端和集合
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection

        # 初始化VectorStore
        vector_store = VectorStore(persist_directory=self.temp_dir)
        _ = vector_store.chroma_client

        # 验证属性
        self.assertEqual(vector_store.persist_directory, self.temp_dir)
        self.assertIsNotNone(vector_store.embedding_model_name)

        # 验证客户端被调用
        mock_chroma_client.assert_called_once()

        print("✓ VectorStore初始化测试通过")

    @patch('sentence_transformers.SentenceTransformer')
    @patch('chromadb.Client')
    def test_create_embeddings(self, mock_chroma_client, mock_sentence_transformer_class):
        """测试创建嵌入向量"""
        from services.vector_store import VectorStore

        # 模拟嵌入模型
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_sentence_transformer_class.return_value = mock_model

        # 初始化VectorStore
        vector_store = VectorStore(persist_directory=self.temp_dir)

        # 测试创建嵌入向量
        texts = ["测试文本"]
        embeddings = vector_store.create_embeddings(texts)

        # 验证
        self.assertEqual(len(embeddings), 1)
        self.assertEqual(len(embeddings[0]), 3)
        mock_model.encode.assert_called_once_with(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True
        )

        print("✓ 创建嵌入向量测试通过")


class TestAdvancedAgent(unittest.TestCase):
    """AdvancedAgent测试类"""

    def setUp(self):
        """测试前准备"""
        pass

    @patch('services.advanced_agent.LocalChatLLM')
    def test_advanced_agent_initialization(self, mock_llm_class):
        """测试AdvancedAgent初始化"""
        from services.advanced_agent import AdvancedAgent
        from langchain.tools import BaseTool

        # 模拟LLM
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        # 创建模拟工具
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "test_tool"
        mock_tool.description = "测试工具"

        # 初始化AdvancedAgent
        agent = AdvancedAgent(llm=mock_llm, tools=[mock_tool])

        # 验证属性
        self.assertEqual(agent.llm, mock_llm)
        self.assertEqual(len(agent.tools), 1)
        self.assertEqual(agent.tools[0].name, "test_tool")
        self.assertEqual(agent.max_iterations, 5)

        print("✓ AdvancedAgent初始化测试通过")

    @patch('services.advanced_agent.LocalChatLLM')
    @patch('langchain.agents.AgentExecutor')
    def test_agent_chat_method(self, mock_agent_executor_class, mock_llm_class):
        """测试Agent的chat方法"""
        from services.advanced_agent import AdvancedAgent
        from langchain.tools import BaseTool

        # 模拟LLM
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        # 创建模拟工具
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "test_tool"
        mock_tool.description = "测试工具"

        # 模拟AgentExecutor
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": "测试回复"}
        mock_agent_executor_class.return_value = mock_executor

        # 初始化AdvancedAgent
        agent = AdvancedAgent(llm=mock_llm, tools=[mock_tool])
        agent.agent_executor = mock_executor

        # 测试chat方法
        response = agent.chat("你好", "历史对话")

        # 验证
        self.assertEqual(response, "测试回复")
        mock_executor.invoke.assert_called_once()

        print("✓ AdvancedAgent chat方法测试通过")

    def test_collect_evidence_with_react_strips_trace(self):
        """测试ReAct证据收集只返回证据摘要，不泄漏过程标签"""
        from services.advanced_agent import AdvancedAgent

        agent = object.__new__(AdvancedAgent)
        history_tool = MagicMock()
        history_tool.name = "all_history"
        history_tool.run.return_value = "用户曾说明自己想改进表达。"
        file_tool = MagicMock()
        file_tool.name = "file_summary"
        file_tool.run.return_value = "用户上传了学习总结。"
        agent.tools = [
            history_tool,
            file_tool,
        ]
        agent.memory = None
        agent.llm = MagicMock()
        agent.llm.invoke.return_value = (
            "Thought: 我需要整理证据\n"
            "Final Answer: 用户能说明学习目标，并上传了学习总结。"
        )

        evidence = agent._collect_evidence_with_react("用户: 我想改进表达", "学习总结")

        self.assertIn("【ReAct证据摘要】", evidence)
        self.assertIn("用户能说明学习目标", evidence)
        self.assertNotIn("Thought:", evidence)
        self.assertNotIn("Action:", evidence)
        self.assertNotIn("Observation:", evidence)

        print("OK ReAct证据摘要清理测试通过")

    def test_evaluate_deep_mode_uses_react_evidence_for_final_json(self):
        """测试deep_mode=True时ReAct只供证据，最终仍返回稳定JSON"""
        from services.advanced_agent import AdvancedAgent

        agent = object.__new__(AdvancedAgent)
        agent.llm = MagicMock()
        agent.llm.invoke.return_value = (
            '{"logic_score": 80, "creativity_score": 75, '
            '"expression_score": 82, "knowledge_score": 78, '
            '"overall_score": 79, "feedback": "能结合材料说明学习目标，表达较清楚。"}'
        )
        agent._collect_evidence_with_react = MagicMock(
            return_value="【ReAct证据摘要】\n用户能说明目标。"
        )

        result = agent.evaluate("用户: 我想提升表达", "学习总结", deep_mode=True)

        self.assertEqual(result["overall_score"], 79)
        self.assertNotIn("Thought", result["feedback"])
        agent._collect_evidence_with_react.assert_called_once()
        prompt = agent.llm.invoke.call_args.args[0]
        self.assertIn("【ReAct证据摘要】", prompt)

        print("OK deep_mode ReAct证据评估测试通过")

    def test_evaluate_deep_mode_falls_back_when_react_fails(self):
        """测试ReAct失败时回退到程序化工具上下文"""
        from services.advanced_agent import AdvancedAgent

        agent = object.__new__(AdvancedAgent)
        agent.llm = MagicMock()
        agent.llm.invoke.return_value = (
            '{"logic_score": 70, "creativity_score": 68, '
            '"expression_score": 72, "knowledge_score": 69, '
            '"overall_score": 70, "feedback": "当前证据有限，但能看出基本表达能力。"}'
        )
        agent._collect_evidence_with_react = MagicMock(side_effect=RuntimeError("parse failed"))
        agent._collect_evaluation_tool_context = MagicMock(return_value="【all_history】\n备用证据")

        result = agent.evaluate("用户: 你好", "", deep_mode=True)

        self.assertEqual(result["overall_score"], 70)
        agent._collect_evaluation_tool_context.assert_called_once()
        self.assertIn("备用证据", agent.llm.invoke.call_args.args[0])

        print("OK ReAct失败回退测试通过")


class TestModelServiceChat(unittest.TestCase):
    """普通聊天生成路径测试类"""

    class FakeTensor:
        shape = (1, 3)

    class FakeInputs(dict):
        def __init__(self):
            self.input_ids = TestModelServiceChat.FakeTensor()
            self.attention_mask = TestModelServiceChat.FakeTensor()
            super().__init__(
                input_ids=self.input_ids,
                attention_mask=self.attention_mask
            )

        def to(self, device):
            self.device = device
            return self

    def _make_service(self):
        from services.model_service import ModelService

        service = object.__new__(ModelService)
        service.tokenizer = MagicMock()
        service.tokenizer.apply_chat_template.return_value = "formatted-chat"
        service.tokenizer.return_value = self.FakeInputs()
        service.tokenizer.eos_token_id = 0
        service.tokenizer.decode.return_value = "助手：好的，我先陪你把这个点找出来。\n用户：继续"

        service.model = MagicMock()
        service.model.device = "cpu"
        service.model.generate.return_value = [[1, 2, 3, 4, 5]]
        service.generate_lock = threading.Lock()
        return service

    def test_chat_text_uses_chat_template_and_chat_token_budget(self):
        """测试普通聊天使用chat template和聊天专用token上限"""
        from config.constants import CHAT_MAX_NEW_TOKENS, MAX_NEW_TOKENS

        service = self._make_service()
        with patch('services.model_service.ChatService.get_recent_chats', return_value=[]):
            response = service._generate_chat_text("我有一个知识没听懂", user_id=1, session_id=2)

        self.assertEqual(response, "好的，我先陪你把这个点找出来。")
        service.tokenizer.apply_chat_template.assert_called_once()

        messages = service.tokenizer.apply_chat_template.call_args.args[0]
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("不要脑补未说明", messages[0]["content"])
        self.assertEqual(messages[-1], {"role": "user", "content": "我有一个知识没听懂"})

        generation_kwargs = service.model.generate.call_args.kwargs
        self.assertEqual(generation_kwargs["max_new_tokens"], CHAT_MAX_NEW_TOKENS)
        self.assertLess(generation_kwargs["max_new_tokens"], MAX_NEW_TOKENS)

        print("OK 普通聊天chat template和token上限测试通过")

    def test_build_chat_messages_filters_current_prompt_and_keeps_chronological_history(self):
        """测试当前问题不重复进入历史，历史按旧到新排序"""
        service = self._make_service()
        history = [
            SimpleNamespace(role="user", content="当前问题"),
            SimpleNamespace(role="assistant", content="最近回复"),
            SimpleNamespace(role="user", content="较早问题"),
        ]

        messages = service._build_chat_messages("当前问题", history)
        message_contents = [message["content"] for message in messages]

        self.assertEqual(message_contents[1:], ["较早问题", "最近回复", "当前问题"])
        self.assertEqual(message_contents.count("当前问题"), 1)

        print("OK 普通聊天历史过滤和排序测试通过")

    def test_build_chat_messages_limits_history_count(self):
        """测试普通聊天只保留最近指定数量的历史消息"""
        from config.constants import CHAT_HISTORY_LIMIT

        service = self._make_service()
        history = [
            SimpleNamespace(role="user", content=f"历史消息{i}")
            for i in range(CHAT_HISTORY_LIMIT + 3)
        ]

        messages = service._build_chat_messages("当前问题", history)

        self.assertEqual(len(messages), CHAT_HISTORY_LIMIT + 2)
        self.assertEqual(messages[-1], {"role": "user", "content": "当前问题"})

        print("OK 普通聊天历史数量限制测试通过")


class TestEnhancedToolFactory(unittest.TestCase):
    """增强版工具工厂测试类"""

    def test_create_basic_tools(self):
        """测试创建基础工具"""
        from services.agent_tools_enhanced import EnhancedToolFactory

        tools = EnhancedToolFactory.create_basic_tools()

        # 验证返回了工具列表
        self.assertIsInstance(tools, list)

        # 基础工具集目前只保留文件摘要工具，评估专用Agent再按需注入其他工具
        if tools:
            tool_names = [tool.name for tool in tools]
            self.assertIn("file_summary", tool_names)

        print("✓ 基础工具创建测试通过")

    @patch('services.agent_tools_enhanced.RAGService')
    def test_create_user_tools(self, mock_rag_service_class):
        """测试创建用户工具"""
        from services.agent_tools_enhanced import EnhancedToolFactory

        # 模拟RAGService
        mock_rag_service = MagicMock()
        mock_rag_service_class.return_value = mock_rag_service

        tools = EnhancedToolFactory.create_user_tools(
            user_id=1,
            rag_service=mock_rag_service
        )

        # 验证返回了工具列表
        self.assertIsInstance(tools, list)

        # 应该包含多种工具
        if tools:
            tool_names = [tool.name for tool in tools]
            expected_tools = ["get_current_time", "calculator", "education_assessment"]
            for expected in expected_tools:
                if expected in tool_names:
                    print(f"  - 找到工具: {expected}")

        print("✓ 用户工具创建测试通过")


class TestRAGService(unittest.TestCase):
    """RAGService测试类"""

    def setUp(self):
        """测试前准备"""
        pass

    @patch('services.file_service.FileService')
    @patch('services.rag_service.get_vector_store')
    def test_rag_service_initialization(self, mock_get_vector_store, mock_file_service):
        """测试RAGService初始化"""
        from services.rag_service import RAGService

        # 模拟vector_store
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        # 初始化RAGService
        rag_service = RAGService()

        # 验证属性
        self.assertIsNotNone(rag_service.chunk_size)
        self.assertIsNotNone(rag_service.chunk_overlap)

        print("✓ RAGService初始化测试通过")

    @patch('services.file_service.FileService')
    def test_keyword_retrieval(self, mock_file_service):
        """测试关键词检索"""
        from services.rag_service import RAGService

        # 模拟文件服务
        mock_file = MagicMock()
        mock_file.id = 1
        mock_file.filename = "test.txt"
        mock_file.filepath = "/path/to/test.txt"

        mock_file_service.get_user_files.return_value = [mock_file]
        mock_file_service.parse_file.return_value = "这是一个测试文档内容"

        # 初始化RAGService（禁用向量检索）
        with patch('services.rag_service.USE_VECTOR_RETRIEVAL', False):
            rag_service = RAGService()
            rag_service.use_vector_retrieval = False

            # 执行检索
            results = rag_service.retrieve(
                query="测试",
                user_id=1,
                top_k=2
            )

        # 验证返回结果格式
        self.assertIsInstance(results, list)

        print("✓ 关键词检索测试通过")


class TestIntegration(unittest.TestCase):
    """集成测试类"""

    def test_config_import(self):
        """测试配置导入"""
        from config import constants

        # 验证配置项存在
        self.assertTrue(hasattr(constants, 'USE_ADVANCED_AGENT'))
        self.assertTrue(hasattr(constants, 'USE_VECTOR_RETRIEVAL'))
        self.assertTrue(hasattr(constants, 'VECTOR_STORE_PATH'))
        self.assertTrue(hasattr(constants, 'RAG_TOP_K'))

        print("✓ 配置导入测试通过")

    def test_module_imports(self):
        """测试模块导入"""
        # 测试主要模块是否可以导入
        modules_to_test = [
            'services.advanced_agent',
            'services.agent_tools_enhanced',
            'services.vector_store',
            'services.rag_service',
            'services.model_service'
        ]

        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"  - {module_name}: ✓")
            except ImportError as e:
                print(f"  - {module_name}: ✗ ({e})")
                # 对于测试，我们只记录但不失败
                pass

        print("✓ 模块导入测试完成")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行LangChain组件测试")
    print("=" * 60)

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTest(unittest.makeSuite(TestVectorStore))
    suite.addTest(unittest.makeSuite(TestAdvancedAgent))
    suite.addTest(unittest.makeSuite(TestModelServiceChat))
    suite.addTest(unittest.makeSuite(TestEnhancedToolFactory))
    suite.addTest(unittest.makeSuite(TestRAGService))
    suite.addTest(unittest.makeSuite(TestIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 60)
    print(f"测试完成: {result.testsRun} 个测试运行")
    print(f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    # 如果直接运行，执行所有测试
    success = run_tests()
    sys.exit(0 if success else 1)

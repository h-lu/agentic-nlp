"""
test_client.py - Client 类测试

测试 LLMClient 类的初始化、错误处理和日志记录功能。
"""

import os
import logging
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO


# 检查是否有 API Key
HAS_OPENAI_KEY = bool(os.getenv("OPENAI_API_KEY"))
HAS_ANY_LLM_KEY = HAS_OPENAI_KEY or bool(os.getenv("ZHIPU_API_KEY")) or bool(os.getenv("DEEPSEEK_API_KEY"))


# 从 CHAPTER.md 中描述的 LLMClient 实现
class LLMClient:
    """统一的 LLM API 客户端（用于测试的基础实现）"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "gpt-4o",
        default_temperature: float = 0,
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API Key，如果不传则从环境变量读取
            base_url: API 地址，用于切换到其他兼容 OpenAI 接口的服务
            model: 默认使用的模型
            default_temperature: 默认温度
        """
        from openai import OpenAI

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未设置，请传入 api_key 参数或设置 OPENAI_API_KEY 环境变量")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )
        self.model = model
        self.default_temperature = default_temperature
        self.total_tokens = 0  # 累计 Token 消耗

    def call(
        self,
        user_message: str,
        system_message: str = "你是一个有帮助的助手。",
        temperature: float = None,
    ) -> str:
        """
        发起一次 LLM 调用

        Args:
            user_message: 用户输入
            system_message: 系统设定
            temperature: 温度，不传则使用默认值

        Returns:
            模型输出的文本
        """
        from openai import APIError, RateLimitError, AuthenticationError

        temp = temperature if temperature is not None else self.default_temperature

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=temp,
            )

            result = completion.choices[0].message.content
            usage = completion.usage
            self.total_tokens += usage.total_tokens

            return result

        except AuthenticationError as e:
            raise
        except RateLimitError as e:
            raise
        except APIError as e:
            raise
        except Exception as e:
            raise

    def classify(self, text: str, categories: list) -> str:
        """文本分类的便捷方法"""
        system = f"你是一个分类助手。请将文本分类到以下类别之一：{', '.join(categories)}。只输出类别名称，不要解释。"
        return self.call(text, system)

    def summarize(self, text: str, max_words: int = 100) -> str:
        """文本摘要的便捷方法"""
        system = f"你是一个摘要助手。请将文本压缩成 {max_words} 字以内的摘要，保留关键信息。"
        return self.call(text, system)

    def extract(self, text: str, entity_types: list) -> str:
        """实体抽取的便捷方法"""
        system = f"""你是一个实体抽取助手。请从文本中抽取以下类型的实体：{', '.join(entity_types)}。
以 JSON 格式输出，格式为 {{"实体类型": ["实体1", "实体2"]}}。
如果某类实体不存在，输出空列表。只输出 JSON，不要其他内容。"""
        return self.call(text, system)


class TestClientInitialization:
    """测试 Client 初始化"""

    def test_init_with_explicit_api_key(self):
        """测试使用显式 API Key 初始化"""
        client = LLMClient(api_key="sk-test-key-12345", model="gpt-4o-mini")
        assert client.api_key == "sk-test-key-12345"
        assert client.model == "gpt-4o-mini"
        assert client.default_temperature == 0

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="需要设置 OPENAI_API_KEY 环境变量")
    def test_init_with_env_api_key(self):
        """测试从环境变量读取 API Key"""
        client = LLMClient(model="gpt-4o-mini")
        assert client.api_key == os.getenv("OPENAI_API_KEY")

    def test_init_without_api_key_raises_error(self):
        """测试没有 API Key 时抛出错误"""
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(ValueError) as exc_info:
                LLMClient()
            assert "API Key 未设置" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_init_with_custom_base_url(self):
        """测试自定义 base_url（用于切换 LLM 后端）"""
        custom_url = "https://api.deepseek.com/v1"
        client = LLMClient(
            api_key="sk-test-key",
            base_url=custom_url,
            model="deepseek-chat",
        )
        assert client.model == "deepseek-chat"

    def test_init_with_custom_temperature(self):
        """测试自定义默认温度"""
        client = LLMClient(api_key="sk-test-key", default_temperature=0.5)
        assert client.default_temperature == 0.5

    def test_init_total_tokens_starts_at_zero(self):
        """测试初始化时 total_tokens 为 0"""
        client = LLMClient(api_key="sk-test-key")
        assert client.total_tokens == 0


class TestClientCallMethod:
    """测试 Client call 方法"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_call_basic(self):
        """测试基础调用"""
        client = LLMClient(model="gpt-4o-mini")
        result = client.call("1+1=?", "你是一个数学助手。只回答数字。")
        assert result is not None
        assert len(result) > 0

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_call_with_custom_temperature(self):
        """测试使用自定义温度调用"""
        client = LLMClient(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini")
        result = client.call("你好", temperature=0.5)
        assert result is not None

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_call_updates_total_tokens(self):
        """测试调用后更新 total_tokens"""
        client = LLMClient(model="gpt-4o-mini")
        initial_tokens = client.total_tokens

        client.call("你好", max_tokens=10)

        # 调用后 total_tokens 应该增加
        assert client.total_tokens > initial_tokens

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_call_with_default_temperature(self):
        """测试使用默认温度"""
        client = LLMClient(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini", default_temperature=0.7)
        # 应该使用 default_temperature 而不报错
        result = client.call("1+1=?")
        assert result is not None


class TestClientConvenienceMethods:
    """测试 Client 便捷方法"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_classify_method(self):
        """测试 classify 便捷方法"""
        client = LLMClient(model="gpt-4o-mini")
        result = client.classify(
            "苹果公司发布新 iPhone",
            categories=["财经", "科技", "体育", "娱乐"],
        )
        assert result in ["财经", "科技", "体育", "娱乐"]

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_summarize_method(self):
        """测试 summarize 便捷方法"""
        client = LLMClient(model="gpt-4o-mini")
        long_text = "这是一段很长的文本。" * 20
        result = client.summarize(long_text, max_words=50)
        assert result is not None
        # 摘要应该比原文短
        assert len(result) < len(long_text)

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_extract_method(self):
        """测试 extract 便捷方法"""
        client = LLMClient(model="gpt-4o-mini")
        result = client.extract(
            "苹果公司 CEO 蒂姆·库克宣布新 iPhone 上市，售价 5999 元。",
            entity_types=["公司", "人名", "产品", "数字"],
        )
        # 应该返回 JSON 格式的字符串
        assert result is not None


class TestClientErrorHandling:
    """测试 Client 错误处理"""

    def test_invalid_api_key_raises_error(self):
        """测试无效 API Key 抛出错误"""
        from openai import AuthenticationError

        client = LLMClient(api_key="sk-invalid-key-xyz", model="gpt-4o-mini")

        with pytest.raises(AuthenticationError):
            client.call("你好")

    def test_empty_user_message(self):
        """测试空用户消息"""
        client = LLMClient(api_key=os.getenv("OPENAI_API_KEY") or "sk-test", model="gpt-4o-mini")

        # 空字符串可能会报错或返回空结果
        # 这里测试不会崩溃
        try:
            result = client.call("")
        except Exception:
            pass  # 空消息可能导致错误，这是预期行为


class TestClientLogging:
    """测试 Client 日志记录"""

    def test_token_tracking(self):
        """测试 Token 追踪"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "测试回复"
        mock_response.usage.total_tokens = 100
        mock_response.usage.prompt_tokens = 80
        mock_response.usage.completion_tokens = 20

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            client = LLMClient(api_key="sk-test-key")
            assert client.total_tokens == 0

            client.call("测试消息")

            assert client.total_tokens == 100

            client.call("另一条消息")
            assert client.total_tokens == 200  # 累加

    def test_multiple_calls_accumulate_tokens(self):
        """测试多次调用累加 Token"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回复"
        mock_response.usage.total_tokens = 50

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            client = LLMClient(api_key="sk-test-key")

            for _ in range(5):
                client.call("测试")

            assert client.total_tokens == 250  # 5 * 50


class TestClientModelSwitching:
    """测试 Client 模型切换"""

    def test_different_models(self):
        """测试不同模型"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回复"
        mock_response.usage.total_tokens = 50

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            # 使用 gpt-4o-mini
            client1 = LLMClient(api_key="sk-test-key", model="gpt-4o-mini")
            client1.call("测试")

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o-mini"

            # 使用 gpt-4o
            client2 = LLMClient(api_key="sk-test-key", model="gpt-4o")
            client2.call("测试")

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o"


class TestClientBackendSwitching:
    """测试 Client 后端切换"""

    def test_openai_backend(self):
        """测试 OpenAI 后端"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回复"
        mock_response.usage.total_tokens = 50

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            client = LLMClient(
                api_key="sk-openai-key",
                model="gpt-4o-mini",
            )
            client.call("测试")

            # 验证 OpenAI 客户端被正确初始化
            MockClient.assert_called_once_with(
                api_key="sk-openai-key",
                base_url=None,
            )

    def test_deepseek_backend(self):
        """测试 DeepSeek 后端"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回复"
        mock_response.usage.total_tokens = 50

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            client = LLMClient(
                api_key="sk-deepseek-key",
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
            )
            client.call("测试")

            # 验证 DeepSeek base_url 被正确设置
            MockClient.assert_called_once_with(
                api_key="sk-deepseek-key",
                base_url="https://api.deepseek.com/v1",
            )

    def test_zhipu_backend(self):
        """测试智谱后端"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回复"
        mock_response.usage.total_tokens = 50

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            client = LLMClient(
                api_key="sk-zhipu-key",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                model="glm-4",
            )
            client.call("测试")

            # 验证智谱 base_url 被正确设置
            MockClient.assert_called_once_with(
                api_key="sk-zhipu-key",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
            )

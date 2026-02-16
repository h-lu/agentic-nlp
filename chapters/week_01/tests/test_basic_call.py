"""
test_basic_call.py - 基础 API 调用测试

测试 LLM API 的基础连接和参数功能。
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock


# 检查是否有 API Key
HAS_OPENAI_KEY = bool(os.getenv("OPENAI_API_KEY"))
HAS_ZHIPU_KEY = bool(os.getenv("ZHIPU_API_KEY"))
HAS_DEEPSEEK_KEY = bool(os.getenv("DEEPSEEK_API_KEY"))
HAS_ANY_LLM_KEY = HAS_OPENAI_KEY or HAS_ZHIPU_KEY or HAS_DEEPSEEK_KEY


class TestBasicAPICall:
    """测试基础 API 调用功能"""

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="需要设置 OPENAI_API_KEY 环境变量")
    def test_openai_connection(self):
        """测试 OpenAI API 连接"""
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "说一个字：好"}],
            temperature=0,
            max_tokens=10,
        )

        assert completion is not None
        assert len(completion.choices) > 0
        assert completion.choices[0].message.content is not None

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="需要设置 OPENAI_API_KEY 环境变量")
    def test_openai_with_system_message(self):
        """测试带 system message 的调用"""
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个新闻分类助手。"},
                {"role": "user", "content": "今天沪指大涨 3%。这是什么类别？只输出类别。"},
            ],
            temperature=0,
            max_tokens=10,
        )

        result = completion.choices[0].message.content
        assert result is not None
        assert len(result) > 0


class TestMessagesParameter:
    """测试 messages 参数的各种情况"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_messages_with_user_only(self):
        """测试只有 user 消息的情况"""
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "1+1=?"}],
            temperature=0,
            max_tokens=10,
        )

        result = completion.choices[0].message.content
        assert result is not None

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_messages_with_system_and_user(self):
        """测试 system + user 消息组合"""
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你只回答'是'或'否'"},
                {"role": "user", "content": "1+1=2 吗？"},
            ],
            temperature=0,
            max_tokens=10,
        )

        result = completion.choices[0].message.content
        assert result is not None
        assert "是" in result or "否" in result or "Yes" in result.lower() or "No" in result.lower()

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_messages_with_conversation_history(self):
        """测试包含对话历史的 messages"""
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个数学助手。"},
                {"role": "user", "content": "1+1=?"},
                {"role": "assistant", "content": "1+1=2"},
                {"role": "user", "content": "那 2+2 呢？"},
            ],
            temperature=0,
            max_tokens=10,
        )

        result = completion.choices[0].message.content
        assert result is not None
        assert "4" in result


class TestTemperatureParameter:
    """测试 temperature 参数"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_temperature_zero_deterministic(self):
        """测试 temperature=0 时输出的确定性"""
        from openai import OpenAI

        client = OpenAI()

        # 多次调用应该得到非常相似的结果
        results = []
        for _ in range(3):
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "1+1=? 只回答数字"}],
                temperature=0,
                max_tokens=5,
            )
            results.append(completion.choices[0].message.content)

        # temperature=0 时，相同输入应该得到相同输出
        assert all(r == results[0] for r in results), f"temperature=0 应该产生相同输出，但得到：{results}"

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_temperature_higher_variance(self):
        """测试较高 temperature 时输出的多样性（仅验证不报错）"""
        from openai import OpenAI

        client = OpenAI()

        # 高 temperature 不报错即可，不验证随机性
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "说一个随机数字"}],
            temperature=1.5,
            max_tokens=10,
        )

        result = completion.choices[0].message.content
        assert result is not None

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_temperature_boundary_zero(self):
        """测试 temperature 边界值 0"""
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "你好"}],
            temperature=0,
            max_tokens=10,
        )
        assert completion.choices[0].message.content is not None

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_temperature_boundary_two(self):
        """测试 temperature 边界值 2"""
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "你好"}],
            temperature=2,
            max_tokens=10,
        )
        assert completion.choices[0].message.content is not None


class TestErrors:
    """测试错误处理"""

    def test_invalid_api_key(self):
        """测试无效 API Key 的错误处理"""
        from openai import OpenAI, AuthenticationError

        client = OpenAI(api_key="sk-invalid-key-12345")

        with pytest.raises(AuthenticationError):
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
            )

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="需要设置 OPENAI_API_KEY 环境变量")
    def test_empty_messages(self):
        """测试空 messages 的错误处理"""
        from openai import OpenAI

        client = OpenAI()

        with pytest.raises(Exception):  # 可能是 BadRequestError 或类似的错误
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[],
            )

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="需要设置 OPENAI_API_KEY 环境变量")
    def test_invalid_model(self):
        """测试无效模型的错误处理"""
        from openai import OpenAI

        client = OpenAI()

        with pytest.raises(Exception):  # 可能是 NotFound 或类似的错误
            client.chat.completions.create(
                model="non-existent-model-xyz",
                messages=[{"role": "user", "content": "test"}],
            )


class TestMockedCalls:
    """使用 Mock 测试（不需要真实 API Key）"""

    def test_mocked_basic_call(self):
        """Mock 测试基础调用"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "财经"
        mock_response.usage.total_tokens = 100
        mock_response.usage.prompt_tokens = 80
        mock_response.usage.completion_tokens = 20

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            # 模拟调用
            client = MockClient()
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}],
            )

            assert completion.choices[0].message.content == "财经"
            assert completion.usage.total_tokens == 100

    def test_mocked_temperature_passed_correctly(self):
        """Mock 测试 temperature 参数正确传递"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test"

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            client = MockClient()
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}],
                temperature=0.5,
            )

            # 验证调用参数
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.5

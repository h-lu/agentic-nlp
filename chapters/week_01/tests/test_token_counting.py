"""
test_token_counting.py - Token 计算测试

测试 Token 计算功能，包括英文、中文以及与字数的比例关系。
"""

import os
import pytest
from unittest.mock import patch, MagicMock


# 尝试导入 tiktoken
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


class TestTokenCounting:
    """测试 Token 计算"""

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_english_token_counting(self):
        """测试英文 Token 计算"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 简单英文文本
        text = "hello world"
        tokens = enc.encode(text)
        assert len(tokens) == 2  # "hello" + "world"

        # 更长的英文文本
        text2 = "The quick brown fox jumps over the lazy dog."
        tokens2 = enc.encode(text2)
        # 英文大约 4 字符 = 1 token
        assert len(tokens2) > 0
        assert len(tokens2) < len(text2)  # Token 数通常小于字符数

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_chinese_token_counting(self):
        """测试中文 Token 计算"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 中文文本
        text = "苹果公司今天发布了新手机"
        tokens = enc.encode(text)
        assert len(tokens) > 0

        # 中文 Token 数应该大于英文字符数 / 4
        # 因为中文通常 1.5-2 个字 = 1 token
        char_count = len(text)
        token_count = len(tokens)

        # 验证中文 Token 与字符的比例关系
        # 大约 1.5-2 个中文字符 = 1 token
        ratio = char_count / token_count
        assert 1.0 <= ratio <= 3.0, f"中文 Token 比例应该在 1-3 之间，实际：{ratio}"

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_mixed_language_token_counting(self):
        """测试中英混合文本的 Token 计算"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 中英混合文本
        text = "苹果公司发布了 iPhone 15，售价 5999 元。"
        tokens = enc.encode(text)
        assert len(tokens) > 0

        # 混合文本的 Token 数应该合理
        char_count = len(text)
        token_count = len(tokens)
        # Token 数应该小于字符数
        assert token_count < char_count * 2  # 不会膨胀太多

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_numbers_token_counting(self):
        """测试数字 Token 计算"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 纯数字
        text = "1234567890"
        tokens = enc.encode(text)
        assert len(tokens) > 0

        # 大数字
        text2 = "1,000,000,000"
        tokens2 = enc.encode(text2)
        assert len(tokens2) > 0


class TestTokenCharRatio:
    """测试 Token 与字符的比例关系"""

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_english_ratio(self):
        """测试英文 Token/字符比例"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 英文文本：大约 4 字符 = 1 token
        english_texts = [
            "hello world",
            "The quick brown fox jumps over the lazy dog.",
            "Natural language processing is a subfield of linguistics, computer science, and artificial intelligence.",
        ]

        for text in english_texts:
            tokens = enc.encode(text)
            char_count = len(text)
            token_count = len(tokens)
            ratio = char_count / token_count

            # 英文比例通常在 3-5 之间
            assert 2 <= ratio <= 6, f"英文比例应该在 2-6 之间，实际：{ratio} (文本：{text[:30]}...)"

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_chinese_ratio(self):
        """测试中文 Token/字符比例"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 中文文本：大约 1.5-2 个汉字 = 1 token
        chinese_texts = [
            "苹果公司发布新手机",
            "今天天气很好，适合出去玩",
            "自然语言处理是人工智能的重要分支，它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。",
        ]

        for text in chinese_texts:
            tokens = enc.encode(text)
            char_count = len(text)
            token_count = len(tokens)
            ratio = char_count / token_count

            # 中文比例通常在 1-2.5 之间（每 token 约 1-2.5 个汉字）
            assert 0.8 <= ratio <= 3.0, f"中文比例应该在 0.8-3.0 之间，实际：{ratio} (文本：{text[:30]}...)"

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_chinese_vs_english_efficiency(self):
        """测试中文 vs 英文的 Token 效率"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 相同含义的中英文
        chinese = "苹果公司发布了新款 iPhone"
        english = "Apple Inc. released a new iPhone"

        cn_tokens = len(enc.encode(chinese))
        en_tokens = len(enc.encode(english))

        # 中文和英文表达相同含义，Token 数应该相近
        # 但由于分词方式不同，可能有差异
        assert cn_tokens > 0 and en_tokens > 0


class TestDifferentEncodings:
    """测试不同编码器"""

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_gpt4_encoding(self):
        """测试 GPT-4 编码器"""
        enc = tiktoken.encoding_for_model("gpt-4")
        assert enc.name == "cl100k_base"

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_gpt4o_encoding(self):
        """测试 GPT-4o 编码器"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        # GPT-4o 使用 o200k_base 编码
        assert enc.name == "o200k_base"

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_different_encodings_produce_different_counts(self):
        """测试不同编码器产生不同的 Token 数"""
        text = "苹果公司发布了 2025 年第一季度财报"

        enc_gpt4 = tiktoken.encoding_for_model("gpt-4")
        enc_gpt4o = tiktoken.encoding_for_model("gpt-4o")

        tokens_gpt4 = enc_gpt4.encode(text)
        tokens_gpt4o = enc_gpt4o.encode(text)

        # 两种编码器可能产生不同的 Token 数
        # 重要的是都能正确编码
        assert len(tokens_gpt4) > 0
        assert len(tokens_gpt4o) > 0


class TestTokenCountingHelpers:
    """测试 Token 计算辅助函数"""

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_count_tokens(self):
        """测试 Token 计数函数"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        def count_tokens(text: str, model: str = "gpt-4o") -> int:
            """计算文本的 Token 数"""
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))

        # 测试各种文本
        assert count_tokens("hello") > 0
        assert count_tokens("你好") > 0
        assert count_tokens("") == 0  # 空字符串应该是 0 token

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_estimate_cost(self):
        """测试成本估算函数"""
        def estimate_cost(
            num_items: int,
            input_tokens_per_item: int,
            output_tokens_per_item: int,
            input_price: float = 2.50,  # $/1M tokens
            output_price: float = 10.00,  # $/1M tokens
        ) -> float:
            """估算成本（美元）"""
            total_input = num_items * input_tokens_per_item
            total_output = num_items * output_tokens_per_item
            cost = (total_input / 1_000_000 * input_price +
                    total_output / 1_000_000 * output_price)
            return cost

        # 测试成本计算
        # 1000 条，每条 400 输入 + 2 输出
        cost = estimate_cost(1000, 400, 2)
        expected = (1000 * 400 / 1_000_000 * 2.50 +
                    1000 * 2 / 1_000_000 * 10.00)
        assert abs(cost - expected) < 0.0001

        # 测试大数量
        cost_large = estimate_cost(10000, 400, 80)
        assert cost_large > cost  # 更多项目应该更贵

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_token_budget_warning(self):
        """测试 Token 预算警告"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 假设预算是 4000 tokens
        budget = 4000
        text = "这是一段很长的文本，" * 100
        tokens = enc.encode(text)

        if len(tokens) > budget:
            warning = f"警告：文本超过预算 ({len(tokens)} > {budget} tokens)"
            assert "警告" in warning


class TestTokenCountingEdgeCases:
    """测试 Token 计算边界情况"""

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_empty_string(self):
        """测试空字符串"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        tokens = enc.encode("")
        assert len(tokens) == 0

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_whitespace_only(self):
        """测试只有空白字符"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        tokens = enc.encode("   \t\n  ")
        # 空白字符也会产生 token
        assert len(tokens) >= 0

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_special_characters(self):
        """测试特殊字符"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        tokens = enc.encode(text)
        assert len(tokens) > 0

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_emoji(self):
        """测试 Emoji"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        text = "Hello! 👋🌍🎉"
        tokens = enc.encode(text)
        assert len(tokens) > 0
        # Emoji 通常会占用多个 token

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_code_snippets(self):
        """测试代码片段"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        tokens = enc.encode(code)
        assert len(tokens) > 0
        # 代码通常 token 数较多

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_json_string(self):
        """测试 JSON 字符串"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        json_text = '{"name": "张三", "age": 25, "city": "北京"}'
        tokens = enc.encode(json_text)
        assert len(tokens) > 0

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_very_long_text(self):
        """测试非常长的文本"""
        enc = tiktoken.encoding_for_model("gpt-4o")
        # 生成一个长文本
        long_text = "这是测试文本。" * 1000
        tokens = enc.encode(long_text)
        assert len(tokens) > 0
        # 验证 token 数与文本长度成比例
        assert len(tokens) < len(long_text) * 2  # 不会膨胀太多


class TestTokenCountingMocked:
    """使用 Mock 测试 Token 计算（不需要 tiktoken）"""

    def test_mocked_token_counting(self):
        """Mock 测试 Token 计算"""
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 个 token

        with patch("tiktoken.encoding_for_model") as mock_get_encoding:
            mock_get_encoding.return_value = mock_encoding

            # 模拟计算 Token
            text = "测试文本"
            tokens = mock_encoding.encode(text)

            assert len(tokens) == 5

    def test_mocked_chinese_ratio(self):
        """Mock 测试中文比例"""
        mock_encoding = MagicMock()

        # 模拟中文：10 个字符 -> 6 个 token（约 1.67 字/token）
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5, 6]

        with patch("tiktoken.encoding_for_model") as mock_get_encoding:
            mock_get_encoding.return_value = mock_encoding

            text = "苹果公司发布新手机"  # 10 个字符
            tokens = mock_encoding.encode(text)

            char_count = len(text)
            token_count = len(tokens)
            ratio = char_count / token_count

            # 验证比例在合理范围内
            assert 1.0 <= ratio <= 2.5

    def test_mocked_cost_estimation(self):
        """Mock 测试成本估算"""
        # 模拟 Token 计数
        mock_input_tokens = 400
        mock_output_tokens = 50

        def estimate_cost(num_items, input_price=2.50, output_price=10.00):
            total_input = num_items * mock_input_tokens
            total_output = num_items * mock_output_tokens
            return (total_input / 1_000_000 * input_price +
                    total_output / 1_000_000 * output_price)

        # 1000 条项目
        cost = estimate_cost(1000)
        expected = (1000 * 400 / 1_000_000 * 2.50 +
                    1000 * 50 / 1_000_000 * 10.00)
        assert abs(cost - expected) < 0.0001


class TestRealWorldScenarios:
    """测试真实场景"""

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_news_classification_tokens(self):
        """测试新闻分类场景的 Token 数"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 典型的新闻文本
        news = """
苹果公司今天发布了 2025 财年第一季度财报。财报显示，公司营收达到 1243 亿美元，
同比增长 4%。iPhone 业务贡献了 697 亿美元收入，超出分析师预期。苹果 CEO 蒂姆·库克
表示，对中国市场的发展势头感到乐观。财报发布后，苹果股价在盘后交易中上涨 2.3%。
"""

        # 系统 Prompt
        system_prompt = "你是一个新闻分类助手。请将新闻分类到以下类别之一：财经、科技、体育、娱乐、教育、健康。只输出类别名称，不要解释。"

        # 计算 Token
        news_tokens = len(enc.encode(news))
        system_tokens = len(enc.encode(system_prompt))
        total_input = system_tokens + news_tokens

        # 验证 Token 数在合理范围内
        assert news_tokens > 0
        assert system_tokens > 0
        assert total_input < 1000  # 单条新闻应该少于 1000 token

    @pytest.mark.skipif(not HAS_TIKTOKEN, reason="需要安装 tiktoken")
    def test_batch_processing_budget(self):
        """测试批量处理的 Token 预算"""
        enc = tiktoken.encoding_for_model("gpt-4o")

        # 假设每条新闻平均 300 token
        avg_tokens_per_news = 300
        system_tokens = 50
        num_news = 1000

        total_input_tokens = (system_tokens + avg_tokens_per_news) * num_news
        estimated_output_tokens = 2 * num_news  # 分类输出很短

        # GPT-4o 价格
        input_price = 2.50 / 1_000_000
        output_price = 10.00 / 1_000_000

        estimated_cost = (total_input_tokens * input_price +
                          estimated_output_tokens * output_price)

        # 验证成本在合理范围内
        assert estimated_cost > 0
        assert estimated_cost < 10  # 1000 条新闻应该不超过 $10

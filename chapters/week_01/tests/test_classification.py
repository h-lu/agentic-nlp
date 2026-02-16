"""
test_classification.py - 分类功能测试

测试新闻分类和其他文本分类任务。
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock


# 检查是否有 API Key
HAS_OPENAI_KEY = bool(os.getenv("OPENAI_API_KEY"))
HAS_ANY_LLM_KEY = HAS_OPENAI_KEY or bool(os.getenv("ZHIPU_API_KEY")) or bool(os.getenv("DEEPSEEK_API_KEY"))


# 测试数据
NEWS_SAMPLES = {
    "finance": {
        "text": "今天沪指大涨 3%，创下半年新高。银行板块领涨，招商银行涨幅超过 5%。",
        "expected_category": "财经",
    },
    "sports": {
        "text": "中国女排在世界锦标赛中 3-0 战胜巴西队，成功晋级决赛。队长朱婷贡献了 25 分。",
        "expected_category": "体育",
    },
    "tech": {
        "text": "苹果公司今天发布了新款 iPhone，搭载 A18 芯片，性能提升 30%，售价 5999 元起。",
        "expected_category": "科技",
    },
    "entertainment": {
        "text": "电影《流浪地球 3》今日上映，首日票房突破 5 亿元，打破国产电影首日票房纪录。",
        "expected_category": "娱乐",
    },
}

CATEGORIES = ["财经", "科技", "体育", "娱乐", "教育", "健康"]


class NewsClassifier:
    """新闻分类器（用于测试的基础实现）"""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def classify(self, text: str, categories: list = None) -> str:
        """对文本进行分类"""
        categories = categories or CATEGORIES
        system_message = (
            f"你是一个新闻分类助手。请将新闻分类到以下类别之一："
            f"{', '.join(categories)}。只输出类别名称，不要解释。"
        )

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=10,
        )

        return completion.choices[0].message.content.strip()


class TestNewsClassification:
    """测试新闻分类功能"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_classify_finance_news(self):
        """测试财经新闻分类"""
        classifier = NewsClassifier()
        result = classifier.classify(NEWS_SAMPLES["finance"]["text"], CATEGORIES)
        assert result in CATEGORIES
        # 财经新闻应该被分类为财经
        assert result == NEWS_SAMPLES["finance"]["expected_category"]

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_classify_sports_news(self):
        """测试体育新闻分类"""
        classifier = NewsClassifier()
        result = classifier.classify(NEWS_SAMPLES["sports"]["text"], CATEGORIES)
        assert result in CATEGORIES
        assert result == NEWS_SAMPLES["sports"]["expected_category"]

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_classify_tech_news(self):
        """测试科技新闻分类"""
        classifier = NewsClassifier()
        result = classifier.classify(NEWS_SAMPLES["tech"]["text"], CATEGORIES)
        assert result in CATEGORIES
        assert result == NEWS_SAMPLES["tech"]["expected_category"]

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_classify_entertainment_news(self):
        """测试娱乐新闻分类"""
        classifier = NewsClassifier()
        result = classifier.classify(NEWS_SAMPLES["entertainment"]["text"], CATEGORIES)
        assert result in CATEGORIES
        assert result == NEWS_SAMPLES["entertainment"]["expected_category"]


class TestClassificationOutputFormat:
    """测试分类输出格式"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_output_is_single_category(self):
        """测试输出是单个类别"""
        classifier = NewsClassifier()
        result = classifier.classify(NEWS_SAMPLES["finance"]["text"], CATEGORIES)

        # 输出应该是单个类别，不包含多余文本
        assert result in CATEGORIES, f"输出应该是一个有效类别，但得到：{result}"

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_output_no_explanation(self):
        """测试输出不包含解释"""
        classifier = NewsClassifier()
        result = classifier.classify(NEWS_SAMPLES["tech"]["text"], CATEGORIES)

        # 输出不应该是长文本
        assert len(result) <= 10, f"输出应该是简短的类别名，但得到：{result}"
        # 输出不应该包含常见的解释词
        explanation_words = ["因为", "所以", "属于", "这条", "新闻"]
        assert not any(word in result for word in explanation_words), f"输出不应该包含解释：{result}"

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_output_is_valid_category(self):
        """测试输出是有效类别之一"""
        classifier = NewsClassifier()
        result = classifier.classify("这是一个普通的技术产品发布新闻。", CATEGORIES)

        # 输出必须在预定义的类别列表中
        assert result in CATEGORIES, f"输出必须是预定义类别之一，但得到：{result}"


class TestClassificationConsistency:
    """测试分类一致性"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_same_input_same_output(self):
        """测试相同输入应该得到相同输出（temperature=0）"""
        classifier = NewsClassifier()
        text = NEWS_SAMPLES["finance"]["text"]

        results = [classifier.classify(text, CATEGORIES) for _ in range(3)]

        # temperature=0 时，相同输入应该得到相同输出
        assert all(r == results[0] for r in results), f"相同输入应该得到相同输出：{results}"


class TestClassificationEdgeCases:
    """测试分类边界情况"""

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_short_text(self):
        """测试短文本分类"""
        classifier = NewsClassifier()
        result = classifier.classify("股市大跌", CATEGORIES)
        assert result in CATEGORIES

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_long_text(self):
        """测试长文本分类"""
        classifier = NewsClassifier()
        long_text = "这是一条关于科技公司的新闻。" * 50
        result = classifier.classify(long_text, CATEGORIES)
        assert result in CATEGORIES

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_mixed_content(self):
        """测试混合内容分类（边界模糊的新闻）"""
        classifier = NewsClassifier()
        # 科技公司的财经新闻，可能被分类为财经或科技
        result = classifier.classify(
            "苹果公司今天公布了季度财报，营收超过 1000 亿美元，但 iPhone 销量有所下滑。",
            CATEGORIES,
        )
        # 应该被分类为财经或科技之一
        assert result in ["财经", "科技"], f"混合内容应被分类为财经或科技，但得到：{result}"

    @pytest.mark.skipif(not HAS_ANY_LLM_KEY, reason="需要设置至少一个 LLM API Key")
    def test_custom_categories(self):
        """测试自定义类别"""
        classifier = NewsClassifier()
        custom_categories = ["正面", "负面", "中性"]
        result = classifier.classify(
            "公司业绩大幅增长，股价飙升。",
            custom_categories,
        )
        assert result in custom_categories


class TestClassificationMocked:
    """使用 Mock 测试分类（不需要真实 API Key）"""

    def test_mocked_classify_returns_valid_category(self):
        """Mock 测试分类返回有效类别"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "财经"

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            classifier = NewsClassifier(api_key="mock-key")
            result = classifier.classify(NEWS_SAMPLES["finance"]["text"], CATEGORIES)

            assert result == "财经"
            assert result in CATEGORIES

    def test_mocked_classify_with_different_categories(self):
        """Mock 测试不同类别的分类"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "体育"

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            classifier = NewsClassifier(api_key="mock-key")
            result = classifier.classify(NEWS_SAMPLES["sports"]["text"], CATEGORIES)

            assert result == "体育"

    def test_mocked_system_message_contains_categories(self):
        """Mock 测试 system message 包含所有类别"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "科技"

        with patch("openai.OpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create.return_value = mock_response

            classifier = NewsClassifier(api_key="mock-key")
            classifier.classify(NEWS_SAMPLES["tech"]["text"], CATEGORIES)

            # 验证 system message 包含所有类别
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]
            system_message = messages[0]["content"]

            for category in CATEGORIES:
                assert category in system_message, f"System message 应包含类别：{category}"

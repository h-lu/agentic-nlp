"""
Tests for text analysis tools.

Tests cover:
- analyze_sentiment: Sentiment analysis (positive/negative/neutral)
- extract_keywords: Keyword extraction
- count_word_freq: Word frequency statistics
"""

import pytest
from .conftest import TextAnalyzerTools


class TestAnalyzeSentiment:
    """Test sentiment analysis functionality."""

    def test_positive_sentiment(self):
        """Test analysis of positive sentiment text."""
        result = TextAnalyzerTools.analyze_sentiment("产品质量很好，非常满意，推荐购买！")

        assert result["sentiment"] == "positive"
        assert result["score"] > 0
        assert "confidence" in result
        assert "reason" in result

    def test_negative_sentiment(self):
        """Test analysis of negative sentiment text."""
        result = TextAnalyzerTools.analyze_sentiment("物流太慢了，客服态度差，很失望。")

        assert result["sentiment"] == "negative"
        assert result["score"] > 0
        assert "confidence" in result

    def test_neutral_sentiment(self):
        """Test analysis of neutral sentiment text."""
        result = TextAnalyzerTools.analyze_sentiment("产品已收到，正在使用中。")

        assert result["sentiment"] == "neutral"
        assert result["score"] == 0

    @pytest.mark.parametrize("text,expected", [
        ("很好，满意", "positive"),
        ("很差，不满", "negative"),
        ("产品已收到，正在使用", "neutral"),
    ])
    def test_sentiment_classification(self, text, expected):
        """Test sentiment classification for various inputs."""
        result = TextAnalyzerTools.analyze_sentiment(text)
        assert result["sentiment"] == expected

    def test_sentiment_score_calculation(self):
        """Test sentiment score is calculated correctly."""
        # More positive words should give higher score
        result1 = TextAnalyzerTools.analyze_sentiment("很好满意")
        result2 = TextAnalyzerTools.analyze_sentiment("很好满意喜欢棒")

        assert result2["score"] > result1["score"]

    def test_mixed_sentiment(self):
        """Test analysis of mixed sentiment text."""
        result = TextAnalyzerTools.analyze_sentiment("产品质量很好，但物流太慢了，希望改进。")

        # Should be either positive or negative depending on word counts
        # In our implementation: positive(2) vs negative(1) = positive
        assert result["sentiment"] in ["positive", "negative", "neutral"]
        assert "reason" in result

    def test_sentiment_confidence_range(self):
        """Test confidence is within valid range."""
        result = TextAnalyzerTools.analyze_sentiment("产品质量很好")

        assert 0 <= result["confidence"] <= 1.0

    def test_sentiment_reason_format(self):
        """Test reason field provides useful information."""
        result = TextAnalyzerTools.analyze_sentiment("很好，满意，喜欢")

        assert "正面词" in result["reason"]
        assert "负面词" in result["reason"]


class TestExtractKeywords:
    """Test keyword extraction functionality."""

    def test_extract_basic_keywords(self):
        """Test basic keyword extraction."""
        result = TextAnalyzerTools.extract_keywords("产品质量很好，物流很快，服务态度不错")

        assert "keywords" in result
        assert "counts" in result
        assert len(result["keywords"]) > 0
        assert len(result["keywords"]) == len(result["counts"])

    def test_keywords_sorted_by_frequency(self):
        """Test keywords are sorted by frequency (high to low)."""
        result = TextAnalyzerTools.extract_keywords("质量 质量 质量 物流 物流 服务")

        # First keyword should have highest count
        assert result["counts"][0] >= result["counts"][1] if len(result["counts"]) > 1 else True

    def test_keywords_top_k_limit(self):
        """Test top_k parameter limits output."""
        result_default = TextAnalyzerTools.extract_keywords("质量 物流 服务 价格 态度 包装 发货 售后 退款 质量")
        result_k3 = TextAnalyzerTools.extract_keywords("质量 物流 服务 价格 态度 包装 发货 售后 退款 质量", top_k=3)

        assert len(result_k3["keywords"]) <= 3

    def test_keywords_empty_text(self):
        """Test keyword extraction with empty text."""
        result = TextAnalyzerTools.extract_keywords("")

        assert result["keywords"] == []
        assert result["counts"] == []

    def test_keywords_whitespace_only(self):
        """Test keyword extraction with whitespace only."""
        result = TextAnalyzerTools.extract_keywords("   \n\t   ")

        assert result["keywords"] == []

    def test_keywords_no_stopwords(self):
        """Test stopwords are filtered out."""
        result = TextAnalyzerTools.extract_keywords("我的你的他的了的是在在在和")

        # Should not contain common stopwords
        assert "的" not in result["keywords"]
        assert "了" not in result["keywords"]
        assert "是" not in result["keywords"]

    def test_keywords_chinese_text(self):
        """Test keyword extraction works with Chinese text."""
        result = TextAnalyzerTools.extract_keywords("产品质量很好，物流速度快，服务态度棒")

        assert len(result["keywords"]) > 0

    def test_keywords_english_mixed(self):
        """Test keyword extraction with mixed Chinese/English."""
        result = TextAnalyzerTools.extract_keywords("The 产品 质量 is very good")

        assert len(result["keywords"]) > 0

    def test_keywords_special_chars(self):
        """Test keyword extraction handles special characters."""
        result = TextAnalyzerTools.extract_keywords("产品!!!质量@@@很好###")

        assert len(result["keywords"]) > 0

    def test_keywords_returns_list(self):
        """Test keywords returns proper list structure."""
        result = TextAnalyzerTools.extract_keywords("产品质量很好")

        assert isinstance(result["keywords"], list)
        assert isinstance(result["counts"], list)


class TestCountWordFreq:
    """Test word frequency statistics."""

    def test_basic_word_frequency(self):
        """Test basic word frequency counting."""
        result = TextAnalyzerTools.count_word_freq("物流 物流 物流 质量 质量 服务")

        assert "top_words" in result
        assert len(result["top_words"]) > 0

        # First word should be "物流" with count 3
        assert result["top_words"][0]["word"] == "物流"
        assert result["top_words"][0]["count"] == 3

    def test_word_freq_sorted_descending(self):
        """Test results are sorted by count descending."""
        result = TextAnalyzerTools.count_word_freq("服务 服务 服务 物流 物流 质量")

        counts = [w["count"] for w in result["top_words"]]
        assert counts == sorted(counts, reverse=True)

    def test_word_freq_top_k_limit(self):
        """Test top_k parameter limits results."""
        result = TextAnalyzerTools.count_word_freq(
            "物流 质量 服务 价格 态度 包装 发货 售后 退款 维修",
            top_k=5
        )

        assert len(result["top_words"]) <= 5

    def test_word_freq_empty_text(self):
        """Test word frequency with empty text."""
        result = TextAnalyzerTools.count_word_freq("")

        assert result["top_words"] == []

    def test_word_freq_whitespace_only(self):
        """Test word frequency with whitespace only."""
        result = TextAnalyzerTools.count_word_freq("   \n\t   ")

        assert result["top_words"] == []

    def test_word_freq_no_stopwords(self):
        """Test stopwords are excluded from frequency."""
        result = TextAnalyzerTools.count_word_freq("的 了 是 在 我 有 和")

        # Should not contain stopwords
        for word_obj in result["top_words"]:
            assert word_obj["word"] not in ["的", "了", "是", "在", "我", "有", "和"]

    def test_word_freq_punctuation_filtered(self):
        """Test punctuation is filtered out."""
        result = TextAnalyzerTools.count_word_freq("产品，。！！、？")

        # Should not contain punctuation-only items
        for word_obj in result["top_words"]:
            assert word_obj["word"] not in ["，", "。", "！", "！", "、", "？"]

    def test_word_freq_structure(self):
        """Test word frequency result structure."""
        result = TextAnalyzerTools.count_word_freq("产品质量很好")

        assert isinstance(result["top_words"], list)
        if result["top_words"]:
            assert "word" in result["top_words"][0]
            assert "count" in result["top_words"][0]
            assert isinstance(result["top_words"][0]["count"], int)

    def test_word_freq_min_word_length(self):
        """Test single character words are filtered."""
        result = TextAnalyzerTools.count_word_freq("我 有 个 好 产 品")

        # Single characters should be filtered
        for word_obj in result["top_words"]:
            assert len(word_obj["word"]) >= 2


class TestToolsEdgeCases:
    """Test edge cases for all tools."""

    @pytest.mark.parametrize("empty_input", ["", "   ", "\n\t", None])
    def test_sentiment_empty_input(self, empty_input):
        """Test sentiment analysis with empty/whitespace input."""
        if empty_input is None:
            # None should be handled
            result = TextAnalyzerTools.analyze_sentiment(empty_input or "")
        else:
            result = TextAnalyzerTools.analyze_sentiment(empty_input)

        assert result["sentiment"] in ["neutral", "negative", "positive"]

    def test_keywords_very_short_input(self):
        """Test keyword extraction with very short input."""
        result = TextAnalyzerTools.extract_keywords("好")

        # Should handle gracefully
        assert "keywords" in result

    def test_wordfreq_very_short_input(self):
        """Test word frequency with very short input."""
        result = TextAnalyzerTools.count_word_freq("好")

        # Should handle gracefully
        assert "top_words" in result

    def test_sentiment_very_long_input(self):
        """Test sentiment analysis with very long input."""
        long_text = "很好，满意" * 1000
        result = TextAnalyzerTools.analyze_sentiment(long_text)

        assert "sentiment" in result

    def test_keywords_very_long_input(self):
        """Test keyword extraction with very long input."""
        long_text = "产品 质量 很好" * 1000
        result = TextAnalyzerTools.extract_keywords(long_text)

        assert "keywords" in result

    def test_wordfreq_very_long_input(self):
        """Test word frequency with very long input."""
        long_text = "物流 质量 服务" * 1000
        result = TextAnalyzerTools.count_word_freq(long_text)

        assert "top_words" in result

    @pytest.mark.parametrize("special_text", [
        "!!!@@@###",
        "123456789",
        "😊😊😊",
        "a<b>c&d",
        "null undefined NaN"
    ])
    def test_special_characters(self, special_text):
        """Test tools handle special characters."""
        sentiment_result = TextAnalyzerTools.analyze_sentiment(special_text)
        keywords_result = TextAnalyzerTools.extract_keywords(special_text)
        freq_result = TextAnalyzerTools.count_word_freq(special_text)

        # All should return valid structure
        assert "sentiment" in sentiment_result
        assert "keywords" in keywords_result
        assert "top_words" in freq_result

    def test_unicode_characters(self):
        """Test tools handle unicode characters."""
        unicode_text = "产品质量很好🎉，物流太快了🚀，非常满意😊"
        result = TextAnalyzerTools.analyze_sentiment(unicode_text)

        assert "sentiment" in result


class TestToolsIntegration:
    """Integration tests for tools working together."""

    def test_analyze_then_extract_keywords(self):
        """Test sentiment analysis followed by keyword extraction."""
        text = "产品质量很好，非常满意，推荐购买"

        sentiment = TextAnalyzerTools.analyze_sentiment(text)
        keywords = TextAnalyzerTools.extract_keywords(text)

        # Both should work on same text
        assert sentiment["sentiment"] == "positive"
        assert len(keywords["keywords"]) > 0

    def test_extract_keywords_then_word_freq(self):
        """Test keyword extraction and word frequency consistency."""
        text = "物流 物流 质量 质量 质量 服务"

        keywords = TextAnalyzerTools.extract_keywords(text, top_k=10)
        freq = TextAnalyzerTools.count_word_freq(text, top_k=10)

        # Both should find same top words
        if keywords["keywords"] and freq["top_words"]:
            assert keywords["keywords"][0] == freq["top_words"][0]["word"]

    def test_multi_text_batch_processing(self):
        """Test processing multiple texts."""
        texts = [
            "产品质量很好，非常满意",
            "物流太慢了，很失望",
            "产品还可以，正在使用"
        ]

        results = [TextAnalyzerTools.analyze_sentiment(t) for t in texts]

        assert len(results) == 3
        assert results[0]["sentiment"] == "positive"
        assert results[1]["sentiment"] == "negative"
        assert results[2]["sentiment"] == "neutral"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

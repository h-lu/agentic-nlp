"""
Tests for LLM Evaluator - Week 07

Tests the evaluation functionality including:
- Single test case evaluation
- Batch evaluation
- Faithfulness and relevancy metrics
- Edge cases (empty cases, malformed inputs)
"""

import pytest
import sys
import importlib.util

# Load local conftest using absolute path to avoid parent conftest conflict
spec = importlib.util.spec_from_file_location(
    'week07_conftest',
    '/home/ubuntu/agentic-nlp/chapters/week_07/tests/conftest.py'
)
week07_conftest = importlib.util.module_from_spec(spec)
sys.modules['week07_conftest'] = week07_conftest
spec.loader.exec_module(week07_conftest)

# Extract classes from local conftest
TestCase = week07_conftest.TestCase
MockLLMEvaluator = week07_conftest.MockLLMEvaluator
MockLLMClient = week07_conftest.MockLLMClient


class TestLLMEvaluatorBasics:
    """Test basic evaluator functionality."""

    def test_evaluator_initialization(self, mock_llm_evaluator):
        """Test that evaluator initializes correctly."""
        assert mock_llm_evaluator is not None
        assert mock_llm_evaluator.evaluation_history == []

    def test_evaluate_single_test_case(self, mock_llm_evaluator):
        """Test evaluating a single test case."""
        test_case = TestCase(
            query="产品质量怎么样？",
            expected="产品质量很好，客户满意度高",
            context="根据客户反馈分析，产品质量评分4.5/5"
        )

        result = mock_llm_evaluator.evaluate_single(test_case)

        assert result.query == test_case.query
        assert result.expected == test_case.expected
        assert 0 <= result.faithfulness <= 1
        assert 0 <= result.relevancy <= 1

    def test_evaluate_single_stores_history(self, mock_llm_evaluator):
        """Test that single evaluation is stored in history."""
        test_case = TestCase(
            query="测试问题",
            expected="测试答案",
            context="测试上下文"
        )

        mock_llm_evaluator.evaluate_single(test_case)

        assert len(mock_llm_evaluator.evaluation_history) == 1

    def test_evaluate_batch_multiple_cases(self, mock_llm_evaluator, sample_test_cases):
        """Test batch evaluation of multiple test cases."""
        # Filter out empty case for this test
        valid_cases = [c for c in sample_test_cases if c.query]

        result = mock_llm_evaluator.evaluate_batch(valid_cases)

        assert result["num_cases"] == len(valid_cases)
        assert 0 <= result["avg_faithfulness"] <= 1
        assert 0 <= result["avg_relevancy"] <= 1
        assert len(result["details"]) == len(valid_cases)

    def test_evaluate_batch_empty_list(self, mock_llm_evaluator):
        """Test batch evaluation with empty test case list."""
        result = mock_llm_evaluator.evaluate_batch([])

        assert result["num_cases"] == 0
        assert result["avg_faithfulness"] == 0
        assert result["avg_relevancy"] == 0
        assert result["details"] == []


class TestLLMEvaluatorMetrics:
    """Test evaluation metrics calculation."""

    def test_faithfulness_score_range(self, mock_llm_evaluator):
        """Test that faithfulness scores are within valid range."""
        test_cases = [
            TestCase(
                query=f"问题{i}",
                expected=f"答案{i}",
                context=f"答案{i}相关的上下文"
            )
            for i in range(10)
        ]

        result = mock_llm_evaluator.evaluate_batch(test_cases)

        for detail in result["details"]:
            assert 0 <= detail["faithfulness"] <= 1

    def test_relevancy_score_range(self, mock_llm_evaluator):
        """Test that relevancy scores are within valid range."""
        test_cases = [
            TestCase(
                query=f"关于{i}的问题",
                expected=f"关于{i}的回答"
            )
            for i in range(10)
        ]

        result = mock_llm_evaluator.evaluate_batch(test_cases)

        for detail in result["details"]:
            assert 0 <= detail["relevancy"] <= 1

    def test_average_metrics_calculation(self, mock_llm_evaluator):
        """Test that average metrics are calculated correctly."""
        test_cases = [
            TestCase(
                query=f"问题{i}",
                expected=f"答案{i}",
                context=f"答案{i}"  # Context contains expected answer
            )
            for i in range(5)
        ]

        result = mock_llm_evaluator.evaluate_batch(test_cases)

        # All cases should have same faithfulness (context contains answer)
        assert result["avg_faithfulness"] == 0.85

    def test_evaluation_details_completeness(self, mock_llm_evaluator):
        """Test that evaluation details contain all required fields."""
        test_case = TestCase(
            query="测试查询",
            expected="测试期望答案",
            context="测试上下文"
        )

        result = mock_llm_evaluator.evaluate_batch([test_case])

        detail = result["details"][0]
        required_fields = ["query", "expected", "actual", "faithfulness", "relevancy"]
        for field in required_fields:
            assert field in detail


class TestLLMEvaluatorEdgeCases:
    """Test edge cases for evaluator."""

    def test_empty_test_case(self, mock_llm_evaluator):
        """Test evaluating an empty test case."""
        empty_case = TestCase(
            query="",
            expected="",
            context=""
        )

        result = mock_llm_evaluator.evaluate_single(empty_case)

        # Should still return a result
        assert result is not None
        assert result.query == ""
        assert result.expected == ""

    def test_very_long_query(self, mock_llm_evaluator):
        """Test evaluating a very long query."""
        long_query = "这是一个非常长的查询" * 100

        test_case = TestCase(
            query=long_query,
            expected="这是一个回答",
            context="相关上下文"
        )

        result = mock_llm_evaluator.evaluate_single(test_case)

        assert result is not None
        assert len(result.query) == len(long_query)

    def test_special_characters_in_query(self, mock_llm_evaluator):
        """Test evaluating queries with special characters."""
        special_cases = [
            TestCase(query="测试???@@@###", expected="答案", context="上下文"),
            TestCase(query="Test\n\nNewlines", expected="Answer", context="Context"),
            TestCase(query="Test\t\tTabs", expected="Answer", context="Context"),
            TestCase(query='Test "quotes" and \'apostrophes\'', expected="Answer", context="Context"),
        ]

        for case in special_cases:
            result = mock_llm_evaluator.evaluate_single(case)
            assert result is not None

    def test_unicode_characters(self, mock_llm_evaluator):
        """Test evaluating with various unicode characters."""
        unicode_case = TestCase(
            query="测试中文emoji 🎉 😊 and العربية",
            expected="答案 🎉",
            context="上下文"
        )

        result = mock_llm_evaluator.evaluate_single(unicode_case)
        assert result is not None

    def test_mismatched_query_expected(self, mock_llm_evaluator):
        """Test when query and expected answer are unrelated."""
        unrelated_case = TestCase(
            query="关于物流速度的问题",
            expected="这是一个关于产品质量的答案",  # Unrelated
            context="产品上下文"
        )

        result = mock_llm_evaluator.evaluate_single(unrelated_case)

        # Relevancy should be lower since query and expected are unrelated
        assert result.relevancy < 0.8


class TestLLMEvaluatorBatchProcessing:
    """Test batch evaluation scenarios."""

    def test_batch_with_varied_quality(self, mock_llm_evaluator):
        """Test batch evaluation with varying quality."""
        test_cases = [
            # High quality
            TestCase(
                query="关于产品质量",
                expected="产品质量很好",
                context="产品质量很好，客户满意度高"
            ),
            # Medium quality
            TestCase(
                query="物流速度",
                expected="物流一般",
                context="物流需要3-5天"
            ),
            # Low quality (unrelated)
            TestCase(
                query="退货政策",
                expected="价格便宜",
                context="价格相关信息"
            ),
        ]

        result = mock_llm_evaluator.evaluate_batch(test_cases)

        # Should have a mix of scores
        scores = [r["faithfulness"] for r in result["details"]]
        assert len(set(scores)) > 1  # Not all the same

    def test_batch_preserves_case_order(self, mock_llm_evaluator):
        """Test that batch evaluation preserves input order."""
        test_cases = [
            TestCase(query=f"问题{i}", expected=f"答案{i}")
            for i in range(5)
        ]

        result = mock_llm_evaluator.evaluate_batch(test_cases)

        # Check order is preserved
        for i, detail in enumerate(result["details"]):
            assert f"问题{i}" in detail["query"]

    def test_large_batch_evaluation(self, mock_llm_evaluator):
        """Test evaluating a large batch of test cases."""
        large_batch = [
            TestCase(
                query=f"测试问题{i}",
                expected=f"测试答案{i}",
                context=f"测试上下文{i}"
            )
            for i in range(100)
        ]

        result = mock_llm_evaluator.evaluate_batch(large_batch)

        assert result["num_cases"] == 100
        assert len(result["details"]) == 100


class TestLLMEvaluatorValidation:
    """Test validation scenarios."""

    def test_missing_optional_fields(self, mock_llm_evaluator):
        """Test evaluation with optional context missing."""
        minimal_case = TestCase(
            query="简单问题",
            expected="简单答案"
            # context is optional
        )

        result = mock_llm_evaluator.evaluate_single(minimal_case)

        assert result is not None
        # Faithfulness should be lower without context
        assert result.faithfulness < 0.8

    def test_all_fields_present(self, mock_llm_evaluator):
        """Test evaluation with all fields present."""
        complete_case = TestCase(
            query="完整问题",
            expected="完整答案",
            context="完整上下文",
            metadata={"source": "test", "category": "evaluation"}
        )

        result = mock_llm_evaluator.evaluate_single(complete_case)

        assert result is not None
        assert result.metadata == complete_case.metadata


class TestLLMEvaluatorMetricsAggregation:
    """Test metrics aggregation across evaluations."""

    def test_average_faithfulness_calculation(self, mock_llm_evaluator):
        """Test that average faithfulness is calculated correctly."""
        # Create cases with known faithfulness values
        test_cases = [
            TestCase(query="q1", expected="a1", context="a1相关"),  # 0.85
            TestCase(query="q2", expected="a2", context="unrelated"),  # 0.65
            TestCase(query="q3", expected="a3", context="a3相关"),  # 0.85
        ]

        result = mock_llm_evaluator.evaluate_batch(test_cases)

        # Average should be (0.85 + 0.65 + 0.85) / 3 = 0.783...
        expected_avg = (0.85 + 0.65 + 0.85) / 3
        assert abs(result["avg_faithfulness"] - expected_avg) < 0.01

    def test_average_relevancy_calculation(self, mock_llm_evaluator):
        """Test that average relevancy is calculated correctly."""
        test_cases = [
            TestCase(query="关于产品", expected="关于产品的答案"),
            TestCase(query="关于物流", expected="关于其他事情"),  # Lower relevancy
            TestCase(query="关于价格", expected="关于价格的答案"),
        ]

        result = mock_llm_evaluator.evaluate_batch(test_cases)

        # Average should be between min and max
        individual_scores = [r["relevancy"] for r in result["details"]]
        assert min(individual_scores) <= result["avg_relevancy"] <= max(individual_scores)

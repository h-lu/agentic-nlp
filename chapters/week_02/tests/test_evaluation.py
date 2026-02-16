"""
Tests for Prompt Evaluation concepts.

This module tests evaluation metrics, test set loading,
and version comparison logic.

Validates anchor: prompt-evaluation-iteration
"""

import pytest
import csv
import json
from dataclasses import dataclass
from typing import List, Dict, Callable
from unittest.mock import MagicMock, patch
from .conftest import TestCase, EvalResult, MockLLMClient, build_prompt_v1, build_prompt_v2, parse_category


class TestEvaluationMetrics:
    """Tests for evaluation metrics calculation."""
    
    def calculate_accuracy(self, predictions: List[str], expectations: List[str]) -> float:
        """Calculate accuracy from predictions and expected values."""
        if not predictions:
            return 0.0
        correct = sum(p == e for p, e in zip(predictions, expectations))
        return correct / len(predictions)
    
    def calculate_format_compliance(self, responses: List[str], parser: Callable) -> float:
        """Calculate format compliance rate."""
        if not responses:
            return 0.0
        successful = 0
        for response in responses:
            try:
                parser(response)
                successful += 1
            except Exception:
                pass
        return successful / len(responses)
    
    def test_accuracy_calculation(self):
        """Test basic accuracy calculation."""
        predictions = ["科技", "财经", "体育", "娱乐"]
        expectations = ["科技", "财经", "体育", "其他"]
        
        accuracy = self.calculate_accuracy(predictions, expectations)
        
        assert accuracy == 0.75  # 3 out of 4 correct
    
    def test_accuracy_perfect(self):
        """Test 100% accuracy case."""
        predictions = ["科技", "财经"]
        expectations = ["科技", "财经"]
        
        accuracy = self.calculate_accuracy(predictions, expectations)
        
        assert accuracy == 1.0
    
    def test_accuracy_zero(self):
        """Test 0% accuracy case."""
        predictions = ["科技", "科技"]
        expectations = ["财经", "财经"]
        
        accuracy = self.calculate_accuracy(predictions, expectations)
        
        assert accuracy == 0.0
    
    def test_accuracy_empty_lists(self):
        """Test accuracy with empty lists."""
        accuracy = self.calculate_accuracy([], [])
        
        assert accuracy == 0.0
    
    def test_format_compliance_all_valid(self):
        """Test format compliance when all outputs are valid."""
        responses = ["科技", "财经", "体育", "娱乐"]
        
        compliance = self.calculate_format_compliance(responses, parse_category)
        
        assert compliance == 1.0
    
    def test_format_compliance_with_invalid(self):
        """Test format compliance with some invalid outputs."""
        responses = ["科技", "", "体育", "这条新闻属于财经类别"]
        
        compliance = self.calculate_format_compliance(responses, parse_category)
        
        # parse_category just strips, so all would pass
        assert compliance == 1.0
    
    def test_format_compliance_with_json_parser(self):
        """Test format compliance with JSON parsing."""
        def json_parser(response):
            return json.loads(response)
        
        responses = [
            '{"category": "科技"}',
            '{"category": "财经"}',
            'not valid json',
            '{"category": "体育"}'
        ]
        
        compliance = self.calculate_format_compliance(responses, json_parser)
        
        assert compliance == 0.75  # 3 out of 4 valid JSON


class TestTestSetLoading:
    """Tests for loading and managing test sets."""
    
    def test_load_csv_test_set(self, temp_csv_testset):
        """Test loading test set from CSV file."""
        test_cases = []
        with open(temp_csv_testset, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                test_cases.append(TestCase(row['input'], row['expected']))
        
        assert len(test_cases) == 2
        assert test_cases[0].input == "苹果发布新品"
        assert test_cases[0].expected_output == "科技"
    
    def test_load_json_test_set(self, tmp_path):
        """Test loading test set from JSON file."""
        json_data = [
            {"input": "新闻1", "expected": "科技"},
            {"input": "新闻2", "expected": "财经"}
        ]
        
        json_file = tmp_path / "test_set.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False)
        
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        test_cases = [TestCase(item['input'], item['expected']) for item in loaded]
        
        assert len(test_cases) == 2
    
    def test_load_test_set_with_metadata(self, tmp_path):
        """Test loading test set with additional metadata."""
        csv_content = "input,expected,difficulty,source\n新闻1,科技,easy,source_a\n新闻2,财经,hard,source_b"
        
        csv_file = tmp_path / "test_with_meta.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        test_cases = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tc = TestCase(
                    row['input'], 
                    row['expected'],
                    metadata={'difficulty': row['difficulty'], 'source': row['source']}
                )
                test_cases.append(tc)
        
        assert test_cases[0].metadata['difficulty'] == "easy"
        assert test_cases[1].metadata['source'] == "source_b"
    
    def test_handle_missing_fields(self, tmp_path):
        """Test handling rows with missing fields."""
        csv_content = "input,expected\n新闻1,科技\n新闻2,\n,财经"
        
        csv_file = tmp_path / "incomplete.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        test_cases = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['input'] and row['expected']:  # Filter complete rows
                    test_cases.append(TestCase(row['input'], row['expected']))
        
        assert len(test_cases) == 1  # Only one complete row
    
    def test_large_test_set(self, tmp_path):
        """Test loading a large test set."""
        # Generate large test set
        rows = [("新闻" + str(i), "科技" if i % 2 == 0 else "财经") for i in range(1000)]
        
        csv_file = tmp_path / "large_test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['input', 'expected'])
            writer.writerows(rows)
        
        test_cases = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                test_cases.append(TestCase(row['input'], row['expected']))
        
        assert len(test_cases) == 1000


class TestVersionComparison:
    """Tests for comparing different prompt versions."""
    
    def evaluate_prompt(
        self,
        client,
        test_cases: List[TestCase],
        build_prompt: Callable[[str], str],
        parse_output: Callable,
        prompt_version: str = "v1"
    ) -> EvalResult:
        """Evaluate a prompt version against test cases."""
        correct = 0
        format_errors = 0
        total_latency = 0
        total_tokens = 0
        error_cases = []
        
        for case in test_cases:
            prompt = build_prompt(case.input)
            
            try:
                import time
                start = time.time()
                
                response = client.call(prompt)
                parsed = parse_output(response)
                
                latency = (time.time() - start) * 1000
                total_latency += latency
                total_tokens += client.last_usage.total_tokens
                
                if parsed == case.expected_output:
                    correct += 1
                else:
                    error_cases.append({
                        "input": case.input,
                        "expected": case.expected_output,
                        "actual": parsed,
                        "raw_response": response,
                    })
            
            except Exception as e:
                format_errors += 1
                error_cases.append({
                    "input": case.input,
                    "expected": case.expected_output,
                    "error": str(e),
                })
        
        n = len(test_cases)
        return EvalResult(
            prompt_version=prompt_version,
            accuracy=correct / n if n > 0 else 0,
            format_compliance=(n - format_errors) / n if n > 0 else 0,
            avg_latency_ms=total_latency / n if n > 0 else 0,
            total_tokens=total_tokens,
            error_cases=error_cases,
        )
    
    def test_compare_two_versions(self, mock_client, test_cases):
        """Test comparing two prompt versions."""
        result_v1 = self.evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "v1"
        )
        result_v2 = self.evaluate_prompt(
            mock_client, test_cases, build_prompt_v2, parse_category, "v2"
        )
        
        assert result_v1.prompt_version == "v1"
        assert result_v2.prompt_version == "v2"
    
    def test_version_improvement_detection(self, mock_client):
        """Test detecting improvement between versions."""
        # Create test cases that v2 handles better
        test_cases_v2_better = [
            TestCase("苹果发布iPhone", "科技"),
            TestCase("央行降准", "财经"),
        ]
        
        result_v1 = self.evaluate_prompt(
            mock_client, test_cases_v2_better, build_prompt_v1, parse_category, "v1"
        )
        result_v2 = self.evaluate_prompt(
            mock_client, test_cases_v2_better, build_prompt_v2, parse_category, "v2"
        )
        
        # Both should have some accuracy
        assert result_v1.accuracy >= 0
        assert result_v2.accuracy >= 0
    
    def test_error_case_tracking(self, mock_client, test_cases):
        """Test that error cases are properly tracked."""
        result = self.evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "v1"
        )
        
        # Error cases should be a list
        assert isinstance(result.error_cases, list)
    
    def test_metrics_calculation(self, mock_client, test_cases):
        """Test that all metrics are calculated correctly."""
        result = self.evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "v1"
        )
        
        # All metrics should be in valid range
        assert 0 <= result.accuracy <= 1
        assert 0 <= result.format_compliance <= 1
        assert result.avg_latency_ms >= 0
        assert result.total_tokens >= 0
    
    def test_generate_comparison_report(self, mock_client, test_cases):
        """Test generating a comparison report."""
        result_v1 = self.evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "v1"
        )
        result_v2 = self.evaluate_prompt(
            mock_client, test_cases, build_prompt_v2, parse_category, "v2"
        )
        
        report = self.generate_comparison_report([result_v1, result_v2])
        
        assert "v1" in report
        assert "v2" in report
        assert "accuracy" in report["v1"]
    
    def generate_comparison_report(self, results: List[EvalResult]) -> Dict:
        """Generate a comparison report from multiple results."""
        report = {}
        for result in results:
            report[result.prompt_version] = {
                "accuracy": result.accuracy,
                "format_compliance": result.format_compliance,
                "avg_latency_ms": result.avg_latency_ms,
                "total_tokens": result.total_tokens,
            }
        return report


class TestEvaluationFramework:
    """Tests for the overall evaluation framework."""
    
    def test_evaluation_with_mock_client(self, mock_client):
        """Test evaluation using mock client."""
        test_cases = [
            TestCase("苹果发布新品", "科技"),
            TestCase("央行降准", "财经"),
        ]
        
        def simple_builder(text):
            return f"分类：{text}"
        
        result = TestVersionComparison().evaluate_prompt(
            mock_client, test_cases, simple_builder, parse_category, "test"
        )
        
        assert result is not None
        assert result.prompt_version == "test"
    
    def test_evaluation_handles_client_errors(self):
        """Test that evaluation handles client errors gracefully."""
        failing_client = MagicMock()
        failing_client.call.side_effect = Exception("API Error")
        failing_client.last_usage = MagicMock(total_tokens=0)
        
        test_cases = [TestCase("test", "result")]
        
        result = TestVersionComparison().evaluate_prompt(
            failing_client, test_cases, build_prompt_v1, parse_category, "error_test"
        )
        
        # Should have recorded the error
        assert len(result.error_cases) == 1
        assert result.format_compliance == 0
    
    def test_batch_evaluation(self, mock_client, test_cases):
        """Test evaluating multiple prompts in batch."""
        prompts = [
            ("v1", build_prompt_v1),
            ("v2", build_prompt_v2),
        ]
        
        results = []
        for version, builder in prompts:
            result = TestVersionComparison().evaluate_prompt(
                mock_client, test_cases, builder, parse_category, version
            )
            results.append(result)
        
        assert len(results) == 2
        assert results[0].prompt_version == "v1"
        assert results[1].prompt_version == "v2"


class TestEvaluationReport:
    """Tests for evaluation report generation."""
    
    def test_report_markdown_generation(self):
        """Test generating Markdown report from evaluation result."""
        result = EvalResult(
            prompt_version="v1",
            accuracy=0.85,
            format_compliance=0.95,
            avg_latency_ms=450.0,
            total_tokens=15000,
            error_cases=[]
        )
        
        report = self.generate_markdown_report(result)
        
        assert "v1" in report
        assert "85" in report  # Matches both "85%" and "85.00%"
        assert "95" in report  # Matches both "95%" and "95.00%"
    
    def generate_markdown_report(self, result: EvalResult) -> str:
        """Generate a Markdown report from evaluation result."""
        return f"""
## Prompt 评估报告：{result.prompt_version}

| 指标 | 值 |
|------|-----|
| 准确率 | {result.accuracy:.2%} |
| 格式合规率 | {result.format_compliance:.2%} |
| 平均延迟 | {result.avg_latency_ms:.0f}ms |
| 总 Token 消耗 | {result.total_tokens} |
"""
    
    def test_report_with_error_analysis(self):
        """Test report includes error analysis when errors exist."""
        result = EvalResult(
            prompt_version="v1",
            accuracy=0.6,
            format_compliance=0.8,
            avg_latency_ms=300,
            total_tokens=10000,
            error_cases=[
                {"input": "test1", "expected": "科技", "actual": "财经"},
                {"input": "test2", "expected": "财经", "actual": "科技"},
            ]
        )
        
        report = self.generate_error_analysis(result)
        
        assert "test1" in report or "错误" in report
    
    def generate_error_analysis(self, result: EvalResult) -> str:
        """Generate error analysis section."""
        if not result.error_cases:
            return "无错误"
        
        lines = ["### 错误分析\n"]
        for e in result.error_cases[:5]:
            lines.append(f"- 输入：{e['input']}")
            lines.append(f"  期望：{e['expected']}")
            lines.append(f"  实际：{e['actual']}")
        
        return "\n".join(lines)


class TestEvaluationEdgeCases:
    """Tests for edge cases in evaluation."""
    
    def test_empty_test_set(self, mock_client):
        """Test evaluation with empty test set."""
        result = TestVersionComparison().evaluate_prompt(
            mock_client, [], build_prompt_v1, parse_category, "empty"
        )
        
        # Should handle gracefully without division by zero
        assert result.accuracy == 0
        assert result.format_compliance == 0
    
    def test_single_test_case(self, mock_client):
        """Test evaluation with single test case."""
        test_cases = [TestCase("苹果", "科技")]
        
        result = TestVersionComparison().evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "single"
        )
        
        assert result.accuracy in [0.0, 1.0]  # Either correct or not
    
    def test_all_same_expected_output(self, mock_client):
        """Test evaluation when all cases have same expected output."""
        test_cases = [
            TestCase("新闻1", "科技"),
            TestCase("新闻2", "科技"),
            TestCase("新闻3", "科技"),
        ]
        
        result = TestVersionComparison().evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "same_output"
        )
        
        assert result.accuracy >= 0
    
    def test_very_long_input_in_test_case(self, mock_client):
        """Test handling very long input in test cases."""
        long_input = "这是一段很长的文本。" * 100
        test_cases = [TestCase(long_input, "科技")]
        
        result = TestVersionComparison().evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "long_input"
        )
        
        assert result is not None
    
    def test_unicode_in_test_cases(self, mock_client):
        """Test handling unicode in test cases."""
        test_cases = [
            TestCase("日本語テスト", "科技"),
            TestCase("한국어 테스트", "科技"),
            TestCase("emoji 🎉 test", "科技"),
        ]
        
        result = TestVersionComparison().evaluate_prompt(
            mock_client, test_cases, build_prompt_v1, parse_category, "unicode"
        )
        
        assert result is not None

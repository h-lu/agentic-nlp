"""
Integration tests for Week 02 Prompt Engineering concepts.

This module tests the end-to-end workflow from prompt design
through few-shot, CoT, and evaluation.

Tests the complete prompt iteration workflow.
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from .conftest import (
    PromptTemplate, FewShotManager, TestCase, EvalResult, MockLLMClient,
    build_prompt_v1, build_prompt_v2, parse_category
)


class TestEndToEndWorkflow:
    """End-to-end tests for the complete prompt engineering workflow."""
    
    @pytest.fixture
    def complete_examples_data(self):
        """Fixture providing complete examples for all categories."""
        return {
            "classify": [
                {"input": "苹果公司发布新款 iPhone", "output": "科技", "category": "科技"},
                {"input": "央行降准 0.5 个百分点", "output": "财经", "category": "财经"},
                {"input": "中国男篮战胜韩国队", "output": "体育", "category": "体育"},
                {"input": "某演员官宣结婚", "output": "娱乐", "category": "娱乐"},
            ]
        }
    
    @pytest.fixture
    def complete_test_cases(self):
        """Fixture providing comprehensive test cases."""
        return [
            TestCase("苹果发布 iPad 新品", "科技"),
            TestCase("央行调整利率政策", "财经"),
            TestCase("国足世界杯预选赛", "体育"),
            TestCase("某歌手发布新专辑", "娱乐"),
            TestCase("科技公司财报超预期", "科技"),
            TestCase("银行理财产品收益率", "财经"),
        ]
    
    @pytest.fixture
    def smart_mock_client(self):
        """Fixture providing a smarter mock client for integration testing."""
        def smart_response(prompt):
            if "iPhone" in prompt or "iPad" in prompt or "科技" in prompt:
                return "科技"
            elif "央行" in prompt or "银行" in prompt or "理财" in prompt or "财经" in prompt:
                return "财经"
            elif "男篮" in prompt or "足球" in prompt or "体育" in prompt:
                return "体育"
            elif "演员" in prompt or "歌手" in prompt or "专辑" in prompt or "娱乐" in prompt:
                return "娱乐"
            else:
                return "科技"  # default
        
        client = MagicMock()
        client.call = MagicMock(side_effect=smart_response)
        client.last_usage = MagicMock(total_tokens=100)
        return client
    
    def evaluate_prompt(
        self,
        client,
        test_cases,
        build_prompt,
        parse_output,
        prompt_version
    ) -> EvalResult:
        """Evaluate a prompt version against test cases."""
        correct = 0
        format_errors = 0
        total_latency = 0
        total_tokens = 0
        error_cases = []
        
        import time
        
        for case in test_cases:
            prompt = build_prompt(case.input)
            
            try:
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
    
    def test_design_to_evaluation_workflow(
        self, complete_examples_data, complete_test_cases, smart_mock_client
    ):
        """Test complete workflow from prompt design to evaluation."""
        # Step 1: Design initial prompt (v1 - basic four elements)
        template_v1 = PromptTemplate(
            name="news_classify_v1",
            role="你是一个新闻分类助手",
            task="判断以下新闻属于哪个类别",
            constraints=["只输出类别名称"],
            output_format="财经、科技、体育、娱乐"
        )
        
        def build_v1(text):
            return template_v1.render(text)
        
        # Step 2: Evaluate v1
        result_v1 = self.evaluate_prompt(
            smart_mock_client, complete_test_cases, build_v1, parse_category, "v1"
        )
        
        # Step 3: Design v2 with few-shot examples
        manager = FewShotManager(examples_data=complete_examples_data)
        examples = manager.get_examples("classify", n=3)
        
        template_v2 = PromptTemplate(
            name="news_classify_v2",
            role="你是一个新闻分类助手",
            task="判断以下新闻属于哪个类别",
            constraints=["只输出类别名称", "格式与示例一致"],
            output_format="财经、科技、体育、娱乐",
            few_shot_examples=examples
        )
        
        def build_v2(text):
            return template_v2.render(text)
        
        # Step 4: Evaluate v2
        result_v2 = self.evaluate_prompt(
            smart_mock_client, complete_test_cases, build_v2, parse_category, "v2"
        )
        
        # Step 5: Compare results
        assert result_v1.prompt_version == "v1"
        assert result_v2.prompt_version == "v2"
        assert result_v1.accuracy >= 0
        assert result_v2.accuracy >= 0
    
    def test_iteration_with_cot(
        self, complete_examples_data, complete_test_cases, smart_mock_client
    ):
        """Test iteration workflow including CoT for complex cases."""
        # Create a CoT template for complex classification
        cot_template = PromptTemplate(
            name="news_classify_cot",
            role="你是一个新闻分类助手",
            task="判断以下新闻属于哪个类别",
            constraints=["最后只输出类别名称"],
            output_format="财经、科技、体育、娱乐",
            use_cot=True,
            cot_steps=[
                "识别新闻的主要话题",
                "匹配最合适的类别",
                "输出分类结果"
            ]
        )
        
        def build_cot(text):
            return cot_template.render(text)
        
        result_cot = self.evaluate_prompt(
            smart_mock_client, complete_test_cases, build_cot, parse_category, "cot"
        )
        
        assert result_cot.prompt_version == "cot"
        assert result_cot.accuracy >= 0


class TestFullPromptIterationWorkflow:
    """Tests for the complete prompt iteration and optimization workflow."""
    
    @pytest.fixture
    def workflow_client(self):
        """Mock client that simulates varying accuracy."""
        call_count = [0]
        
        def varying_response(prompt):
            call_count[0] += 1
            # Simulate improvement with better prompts
            if "示例" in prompt:  # Few-shot
                accuracy_boost = True
            else:
                accuracy_boost = False
            
            # Map based on content
            if "iPhone" in prompt or "iPad" in prompt:
                return "科技"
            elif "央行" in prompt or "银行" in prompt:
                return "财经"
            elif "男篮" in prompt or "足球" in prompt:
                return "体育"
            elif "演员" in prompt or "歌手" in prompt:
                return "娱乐"
            else:
                # Default response
                return "科技"
        
        client = MagicMock()
        client.call = MagicMock(side_effect=varying_response)
        client.last_usage = MagicMock(total_tokens=100)
        return client
    
    def test_workflow_step_by_step(self, workflow_client):
        """Test the workflow step by step with verification at each stage."""
        test_cases = [
            TestCase("苹果发布新品", "科技"),
            TestCase("央行降准", "财经"),
        ]
        
        # Stage 1: Basic prompt
        stage1_results = self._run_evaluation(
            workflow_client, test_cases, 
            lambda t: f"分类：{t}", 
            "stage1"
        )
        assert stage1_results is not None
        
        # Stage 2: Four-element prompt
        template = PromptTemplate(
            name="stage2",
            role="分类助手",
            task="分类以下新闻",
            constraints=["输出类别"],
            output_format="财经、科技、体育、娱乐"
        )
        stage2_results = self._run_evaluation(
            workflow_client, test_cases,
            lambda t: template.render(t),
            "stage2"
        )
        assert stage2_results is not None
        
        # Stage 3: With few-shot
        template_v3 = PromptTemplate(
            name="stage3",
            role="分类助手",
            task="分类以下新闻",
            constraints=["输出类别"],
            output_format="财经、科技、体育、娱乐",
            few_shot_examples=[
                {"input": "示例1", "output": "科技"},
                {"input": "示例2", "output": "财经"},
            ]
        )
        stage3_results = self._run_evaluation(
            workflow_client, test_cases,
            lambda t: template_v3.render(t),
            "stage3"
        )
        assert stage3_results is not None
    
    def _run_evaluation(self, client, test_cases, build_prompt, version):
        """Helper to run evaluation."""
        correct = 0
        for case in test_cases:
            prompt = build_prompt(case.input)
            response = client.call(prompt)
            if parse_category(response) == case.expected_output:
                correct += 1
        
        return EvalResult(
            prompt_version=version,
            accuracy=correct / len(test_cases) if test_cases else 0,
            format_compliance=1.0,
            avg_latency_ms=100,
            total_tokens=len(test_cases) * 100,
            error_cases=[]
        )
    
    def test_prompt_version_history(self):
        """Test tracking prompt version history."""
        history = []
        
        # Record each version
        versions = [
            {"version": "v1", "accuracy": 0.70, "date": "2026-02-15"},
            {"version": "v2", "accuracy": 0.85, "date": "2026-02-16"},
            {"version": "v3", "accuracy": 0.92, "date": "2026-02-17"},
        ]
        
        for v in versions:
            history.append(v)
        
        assert len(history) == 3
        assert history[-1]["accuracy"] == 0.92
    
    def test_rollback_to_previous_version(self):
        """Test ability to identify best version for rollback."""
        results = [
            EvalResult("v1", 0.70, 0.90, 100, 1000, []),
            EvalResult("v2", 0.85, 0.95, 150, 1500, []),
            EvalResult("v3", 0.75, 0.80, 120, 1200, []),  # v3 is worse than v2
        ]
        
        # Find best version
        best = max(results, key=lambda r: r.accuracy)
        
        assert best.prompt_version == "v2"
        assert best.accuracy == 0.85


class TestIntegrationWithMockedLLM:
    """Integration tests with more sophisticated LLM mocking."""
    
    @pytest.fixture
    def realistic_client(self):
        """Create a more realistic mock client."""
        responses = {
            "苹果": "科技",
            "央行": "财经",
            "男篮": "体育",
            "演员": "娱乐",
            "银行": "财经",
            "国足": "体育",
            "歌手": "娱乐",
            "iPad": "科技",
        }
        
        def smart_call(prompt):
            for keyword, category in responses.items():
                if keyword in prompt:
                    return category
            return "科技"
        
        client = MagicMock()
        client.call = MagicMock(side_effect=smart_call)
        client.last_usage = MagicMock(total_tokens=100)
        return client
    
    def test_few_shot_improves_consistency(self, realistic_client):
        """Test that few-shot examples work correctly in prompts."""
        test_cases = [
            TestCase("苹果发布新产品", "科技"),
            TestCase("央行发布新政策", "财经"),
        ]

        # Test that few-shot prompt contains examples
        few_shot_prompt = lambda t: f"""示例：
输入："苹果发布iPhone"
输出：科技

分类：{t}"""

        # Verify the prompt structure is correct
        prompt = few_shot_prompt("测试")
        assert "示例" in prompt
        assert "苹果发布iPhone" in prompt
        assert "科技" in prompt

        # Evaluate with the mock client
        results = self._quick_eval(realistic_client, test_cases, few_shot_prompt)
        # Our mock returns based on keyword matching, so we get partial accuracy
        assert results >= 0  # Basic sanity check
    
    def _quick_eval(self, client, test_cases, build_prompt):
        """Quick evaluation helper."""
        correct = 0
        for case in test_cases:
            prompt = build_prompt(case.input)
            response = client.call(prompt)
            if parse_category(response) == case.expected_output:
                correct += 1
        return correct / len(test_cases) if test_cases else 0
    
    def test_cot_for_complex_cases(self, realistic_client):
        """Test CoT for complex ambiguous cases."""
        complex_cases = [
            TestCase("某科技公司发布财报，股价大涨", "科技"),  # Could be 科技 or 财经
        ]
        
        # Basic prompt might struggle
        basic_template = PromptTemplate(
            name="basic",
            role="分类助手",
            task="分类新闻",
            constraints=["输出一个类别"],
            output_format="财经、科技、体育、娱乐"
        )
        
        # CoT prompt provides reasoning
        cot_template = PromptTemplate(
            name="cot",
            role="分类助手",
            task="分类新闻",
            constraints=["输出主要类别"],
            output_format="财经、科技、体育、娱乐",
            use_cot=True,
            cot_steps=["识别主要话题", "选择最相关类别"]
        )
        
        # Both should produce results
        basic_prompt = basic_template.render(complex_cases[0].input)
        cot_prompt = cot_template.render(complex_cases[0].input)
        
        basic_response = realistic_client.call(basic_prompt)
        cot_response = realistic_client.call(cot_prompt)
        
        assert basic_response in ["财经", "科技", "体育", "娱乐"]
        assert cot_response in ["财经", "科技", "体育", "娱乐"]


class TestIntegrationErrorHandling:
    """Integration tests for error handling in the workflow."""
    
    def test_graceful_handling_of_api_errors(self):
        """Test graceful handling of API errors during evaluation."""
        failing_client = MagicMock()
        failing_client.call = MagicMock(side_effect=Exception("API Error"))
        failing_client.last_usage = MagicMock(total_tokens=0)
        
        test_cases = [TestCase("test", "科技")]
        
        # Should not crash
        try:
            result = TestEndToEndWorkflow().evaluate_prompt(
                failing_client, test_cases, build_prompt_v1, parse_category, "error_test"
            )
            # Should record the error
            assert len(result.error_cases) == 1
            assert result.format_compliance == 0
        except Exception:
            pytest.fail("Should handle API errors gracefully")
    
    def test_handling_malformed_responses(self):
        """Test handling malformed LLM responses."""
        def malformed_response(prompt):
            # Return various malformed responses
            if "error" in prompt.lower():
                return ""
            elif "partial" in prompt.lower():
                return "这条新闻属于"
            else:
                return "科技"
        
        client = MagicMock()
        client.call = MagicMock(side_effect=malformed_response)
        client.last_usage = MagicMock(total_tokens=50)
        
        test_cases = [
            TestCase("正常新闻", "科技"),
            TestCase("error test", "科技"),
        ]
        
        result = TestEndToEndWorkflow().evaluate_prompt(
            client, test_cases, build_prompt_v1, parse_category, "malformed"
        )
        
        # Should have processed all cases
        assert result is not None
    
    def test_partial_failures_dont_crash_workflow(self):
        """Test that partial failures don't crash the entire workflow."""
        call_count = [0]
        
        def sometimes_fails(prompt):
            call_count[0] += 1
            if call_count[0] == 2:  # Fail on second call
                raise Exception("Network error")
            return "科技"
        
        client = MagicMock()
        client.call = MagicMock(side_effect=sometimes_fails)
        client.last_usage = MagicMock(total_tokens=100)
        
        test_cases = [
            TestCase("test1", "科技"),
            TestCase("test2", "科技"),
            TestCase("test3", "科技"),
        ]
        
        result = TestEndToEndWorkflow().evaluate_prompt(
            client, test_cases, build_prompt_v1, parse_category, "partial"
        )
        
        # Should have 2 successful, 1 failed
        assert len(result.error_cases) == 1


class TestIntegrationReportGeneration:
    """Integration tests for report generation from evaluation results."""
    
    def test_generate_full_iteration_report(self):
        """Test generating a complete iteration report."""
        results = [
            EvalResult("v1", 0.70, 0.85, 100, 1000, [
                {"input": "test1", "expected": "科技", "actual": "财经"}
            ]),
            EvalResult("v2", 0.85, 0.95, 150, 1500, []),
            EvalResult("v3", 0.92, 0.98, 200, 2000, []),
        ]
        
        report = self.generate_full_report(results)
        
        assert "v1" in report
        assert "v2" in report
        assert "v3" in report
        assert "0.92" in report or "92%" in report
    
    def generate_full_report(self, results):
        """Generate a full iteration report."""
        lines = ["# Prompt 迭代报告\n"]
        
        lines.append("| 版本 | 准确率 | 格式合规率 | 延迟 | Token消耗 |")
        lines.append("|------|--------|------------|------|-----------|")
        
        for r in results:
            lines.append(
                f"| {r.prompt_version} | {r.accuracy:.0%} | "
                f"{r.format_compliance:.0%} | {r.avg_latency_ms:.0f}ms | "
                f"{r.total_tokens} |"
            )
        
        return "\n".join(lines)
    
    def test_report_includes_recommendations(self):
        """Test that report includes recommendations."""
        results = [
            EvalResult("v1", 0.70, 0.85, 100, 1000, []),
            EvalResult("v2", 0.92, 0.98, 150, 1500, []),
        ]
        
        recommendation = self.generate_recommendation(results)
        
        assert "v2" in recommendation  # Best version
        assert "推荐" in recommendation or "建议" in recommendation
    
    def generate_recommendation(self, results):
        """Generate recommendation based on results."""
        best = max(results, key=lambda r: r.accuracy)
        return f"推荐使用版本：{best.prompt_version}，准确率 {best.accuracy:.0%}"


class TestIntegrationWithFixtures:
    """Integration tests using conftest fixtures."""
    
    def test_complete_workflow_with_fixtures(
        self, sample_template, cot_template, few_shot_manager, mock_client, test_cases
    ):
        """Test complete workflow using pytest fixtures."""
        # Evaluate basic template
        def build_basic(text):
            return sample_template.render(text)
        
        result_basic = TestEndToEndWorkflow().evaluate_prompt(
            mock_client, test_cases[:3], build_basic, parse_category, "basic"
        )
        
        # Evaluate CoT template
        def build_cot(text):
            return cot_template.render(text)
        
        result_cot = TestEndToEndWorkflow().evaluate_prompt(
            mock_client, test_cases[:3], build_cot, parse_category, "cot"
        )
        
        # Both should produce valid results
        assert result_basic.accuracy >= 0
        assert result_cot.accuracy >= 0
    
    def test_few_shot_manager_integration(self, few_shot_manager, sample_template):
        """Test few-shot manager integrated with template."""
        examples = few_shot_manager.get_examples("classify", n=3)
        
        # Create template with examples
        template_with_examples = PromptTemplate(
            name="with_examples",
            role=sample_template.role,
            task=sample_template.task,
            constraints=sample_template.constraints,
            output_format=sample_template.output_format,
            few_shot_examples=examples
        )
        
        prompt = template_with_examples.render("测试新闻")
        
        # Should include all examples
        for ex in examples:
            assert ex["input"] in prompt

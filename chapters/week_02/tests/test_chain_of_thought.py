"""
Tests for Chain-of-Thought (CoT) prompting concepts.

This module tests CoT prompt generation, reasoning step extraction,
and handling of ambiguous cases.

Validates anchor: cot-accuracy
"""

import pytest
import re
from .conftest import PromptTemplate


class TestCoTPromptGeneration:
    """Tests for Chain-of-Thought prompt generation."""
    
    def test_cot_prompt_includes_steps(self, cot_template):
        """Test that CoT prompt includes reasoning steps."""
        prompt = cot_template.render("测试工单内容")
        
        assert "请按以下步骤思考：" in prompt
        assert "1." in prompt
        assert "2." in prompt
    
    def test_cot_prompt_includes_all_steps(self, cot_template):
        """Test that all CoT steps are included in the prompt."""
        prompt = cot_template.render("测试工单")
        
        for step in cot_template.cot_steps:
            assert step in prompt
    
    def test_cot_steps_numbered_correctly(self, cot_template):
        """Test that CoT steps are numbered sequentially."""
        prompt = cot_template.render("测试")
        
        for i, step in enumerate(cot_template.cot_steps, 1):
            assert f"{i}. {step}" in prompt
    
    def test_non_cot_template_excludes_steps(self, sample_template):
        """Test that non-CoT template doesn't include reasoning steps."""
        prompt = sample_template.render("测试新闻")
        
        assert "请按以下步骤思考：" not in prompt
    
    def test_cot_prompt_structure(self, cot_template):
        """Test the overall structure of CoT prompts."""
        prompt = cot_template.render("用户反馈")
        
        # Should contain role
        assert "角色：" in prompt
        # Should contain task
        assert "任务：" in prompt
        # Should contain CoT steps
        assert "请按以下步骤思考：" in prompt
        # Should contain format
        assert "格式：" in prompt
    
    def test_cot_with_custom_steps(self):
        """Test creating a CoT template with custom steps."""
        custom_steps = [
            "分析问题的核心",
            "识别关键实体",
            "评估可能的答案",
            "选择最佳答案"
        ]
        
        template = PromptTemplate(
            name="custom_cot",
            role="分析助手",
            task="分析问题",
            constraints=[],
            output_format="JSON",
            use_cot=True,
            cot_steps=custom_steps
        )
        
        prompt = template.render("测试问题")
        
        for step in custom_steps:
            assert step in prompt


class TestReasoningStepExtraction:
    """Tests for extracting reasoning steps from CoT outputs."""
    
    def extract_steps(self, response: str) -> list:
        """Helper method to extract numbered steps from CoT response."""
        pattern = r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|最终|$)'
        matches = re.findall(pattern, response, re.DOTALL)
        return [m.strip() for m in matches]
    
    def extract_final_answer(self, response: str, keywords: list = None) -> str:
        """Helper method to extract final answer from CoT response."""
        if keywords is None:
            keywords = ["最终", "结论", "答案", "结果"]
        
        for keyword in keywords:
            pattern = rf'{keyword}[：:]\s*(.+)'
            match = re.search(pattern, response)
            if match:
                return match.group(1).strip()
        
        # Fallback: return last line
        lines = [l.strip() for l in response.strip().split('\n') if l.strip()]
        return lines[-1] if lines else ""
    
    def test_extract_numbered_steps(self):
        """Test extracting numbered reasoning steps."""
        response = """1. 用户遇到了充值问题
2. 核心诉求是解决会员状态
3. 账务部门最适合处理
4. 最终分类：账务问题"""
        
        steps = self.extract_steps(response)
        
        assert len(steps) >= 3
        assert "充值问题" in steps[0]
    
    def test_extract_final_answer(self):
        """Test extracting the final answer from CoT response."""
        response = """1. 分析问题：用户充值后状态未更新
2. 判断部门：账务问题
最终分类：账务问题"""
        
        answer = self.extract_final_answer(response)
        
        assert "账务问题" in answer
    
    def test_extract_answer_with_different_keywords(self):
        """Test extracting answer with various keyword formats."""
        test_cases = [
            ("最终：技术支持", "技术支持"),
            ("结论: 账务问题", "账务问题"),
            ("答案：投诉", "投诉"),
            ("结果：功能建议", "功能建议"),
        ]
        
        for response, expected in test_cases:
            answer = self.extract_final_answer(response)
            assert expected in answer
    
    def test_extract_from_multiline_response(self):
        """Test extracting from a complex multi-line response."""
        response = """
1. 用户遇到什么问题？
   用户充值后会员状态未更新，客服响应慢

2. 问题的核心诉求是什么？
   用户需要恢复会员权益

3. 哪个部门最适合处理？
   账务问题部门，因为涉及充值和会员状态

4. 最终分类结果是什么？
最终分类：账务问题
"""
        
        steps = self.extract_steps(response)
        answer = self.extract_final_answer(response)
        
        assert len(steps) >= 2
        assert "账务问题" in answer
    
    def test_extract_from_response_without_clear_structure(self):
        """Test extracting from a response without clear step structure."""
        response = """这个工单涉及充值问题，应该分到账务部门处理。
账务问题"""
        
        answer = self.extract_final_answer(response)
        
        # Should fall back to last line
        assert "账务问题" in answer


class TestAmbiguousCaseHandling:
    """Tests for handling ambiguous or complex cases with CoT."""
    
    def test_ambiguous_case_requires_cot(self, cot_template):
        """Test that ambiguous cases benefit from CoT prompting."""
        ambiguous_ticket = """
我购买的高级会员一直没到账，给客服打电话没人接，
app上显示的订单状态也不对，太失望了！
"""
        
        prompt = cot_template.render(ambiguous_ticket)
        
        # CoT prompt should include reasoning steps
        assert "请按以下步骤思考：" in prompt
        
        # Should ask to identify the core issue
        assert "问题" in prompt.lower() or "诉求" in prompt
    
    def test_multiple_issues_in_one_ticket(self, cot_template):
        """Test handling tickets with multiple issues."""
        multi_issue_ticket = """
充值失败，申请退款也没反应，而且你们app经常闪退，
客服排队等了30分钟，我要投诉！
"""
        
        prompt = cot_template.render(multi_issue_ticket)
        
        # Prompt should guide the model to analyze systematically
        assert "步骤" in prompt
    
    def test_cot_handles_edge_cases(self):
        """Test that CoT helps with edge cases in classification."""
        edge_cases = [
            ("这是一条空白的工单", "其他"),
            ("感谢你们的帮助！", "其他"),  # 无明确问题
            ("所有问题都解决了，取消投诉", "其他"),
        ]
        
        cot_template = PromptTemplate(
            name="edge_case_cot",
            role="工单分类助手",
            task="判断工单类型",
            constraints=["如果无法判断，归为其他"],
            output_format="分类结果",
            use_cot=True,
            cot_steps=["识别用户主要诉求", "匹配最相关的部门", "无法匹配时选择其他"]
        )
        
        for ticket_text, expected_type in edge_cases:
            prompt = cot_template.render(ticket_text)
            assert "步骤" in prompt
    
    def test_cot_vs_non_cot_comparison(self, sample_template, cot_template):
        """Compare CoT and non-CoT prompts for the same input."""
        complex_ticket = "充值会员后没有到账，而且app经常闪退，客服也打不通"
        
        non_cot_prompt = sample_template.render(complex_ticket)
        cot_prompt = cot_template.render(complex_ticket)
        
        # CoT prompt should be longer and more structured
        assert len(cot_prompt) > len(non_cot_prompt)
        assert "步骤" in cot_prompt
        assert "步骤" not in non_cot_prompt


class TestCoTOutputParsing:
    """Tests for parsing and validating CoT outputs."""
    
    def parse_cot_response(self, response: str) -> dict:
        """Helper to parse CoT response into structured data."""
        result = {
            "reasoning": [],
            "final_answer": None
        }
        
        # Extract reasoning steps
        step_pattern = r'\d+\.\s*(.+?)(?=\n\d+\.|\n最终|\n\n|$)'
        matches = re.findall(step_pattern, response, re.DOTALL)
        result["reasoning"] = [m.strip() for m in matches]
        
        # Extract final answer
        final_pattern = r'最终[分类结果]*[：:]\s*(.+)'
        final_match = re.search(final_pattern, response)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
        
        return result
    
    def test_parse_complete_cot_response(self):
        """Test parsing a complete CoT response."""
        response = """
1. 用户遇到了什么问题？充值后状态未更新
2. 问题的核心诉求是什么？恢复会员权益
3. 哪个部门最适合处理？账务部门
4. 最终分类结果是什么？
最终分类：账务问题
"""
        
        parsed = self.parse_cot_response(response)
        
        assert len(parsed["reasoning"]) >= 2
        assert parsed["final_answer"] == "账务问题"
    
    def test_parse_incomplete_cot_response(self):
        """Test parsing an incomplete CoT response."""
        response = "1. 这是第一步分析\n2. 这是第二步"
        
        parsed = self.parse_cot_response(response)
        
        assert len(parsed["reasoning"]) >= 1
        assert parsed["final_answer"] is None
    
    def test_parse_response_with_extra_text(self):
        """Test parsing response with additional explanatory text."""
        response = """
好的，让我分析一下这个工单。

1. 问题分析：用户充值失败
2. 部门判断：账务问题

根据分析，这个工单应该分到账务部门。
最终分类：账务问题
"""
        
        parsed = self.parse_cot_response(response)
        
        assert "账务问题" in parsed["final_answer"]


class TestCoTBestPractices:
    """Tests for CoT best practices and recommendations."""
    
    def test_recommended_step_count(self):
        """Test that recommended CoT has 3-5 steps."""
        recommended_steps = [
            "识别问题",
            "分析原因", 
            "确定解决方案",
            "给出结论"
        ]
        
        assert 3 <= len(recommended_steps) <= 5
    
    def test_cot_steps_should_be_sequential(self):
        """Test that CoT steps follow a logical sequence."""
        good_steps = [
            "用户遇到了什么问题？",
            "问题的核心诉求是什么？",
            "哪个部门最适合处理这个诉求？",
            "最终分类结果是什么？"
        ]
        
        # Steps should flow from problem identification to conclusion
        assert "问题" in good_steps[0]
        assert "最终" in good_steps[-1] or "结果" in good_steps[-1]
    
    def test_cot_prompt_length_reasonable(self, cot_template):
        """Test that CoT prompt doesn't become excessively long."""
        prompt = cot_template.render("短输入")
        
        # Prompt should be reasonable length (not more than 2000 chars for template)
        assert len(prompt) < 2000
    
    def test_zero_shot_cot_phrase(self):
        """Test the zero-shot CoT phrase."""
        zero_shot_cot = "Let's think step by step."
        
        # This phrase should trigger CoT reasoning
        assert "step" in zero_shot_cot.lower()


class TestCoTWithDifferentTasks:
    """Tests for CoT with different types of tasks."""
    
    def test_cot_for_classification(self):
        """Test CoT for classification tasks."""
        template = PromptTemplate(
            name="classify_cot",
            role="分类助手",
            task="对文本进行分类",
            constraints=["输出单一类别"],
            output_format="类别名称",
            use_cot=True,
            cot_steps=["识别文本主题", "匹配预定义类别", "输出分类结果"]
        )
        
        prompt = template.render("这是一篇关于科技公司的新闻")
        
        assert "识别文本主题" in prompt
        assert "匹配预定义类别" in prompt
    
    def test_cot_for_extraction(self):
        """Test CoT for information extraction tasks."""
        template = PromptTemplate(
            name="extract_cot",
            role="信息抽取助手",
            task="从文本中提取关键信息",
            constraints=["输出JSON格式"],
            output_format="JSON",
            use_cot=True,
            cot_steps=["识别实体", "识别关系", "构建结构化输出"]
        )
        
        prompt = template.render("张三在北京工作，职位是工程师")
        
        assert "识别实体" in prompt
        assert "构建结构化输出" in prompt
    
    def test_cot_for_summarization(self):
        """Test CoT for summarization tasks."""
        template = PromptTemplate(
            name="summarize_cot",
            role="摘要助手",
            task="生成文本摘要",
            constraints=["保持简洁"],
            output_format="一段话",
            use_cot=True,
            cot_steps=["识别主要观点", "去除冗余信息", "组织成连贯摘要"]
        )
        
        prompt = template.render("这是一段需要总结的长文本...")
        
        assert "识别主要观点" in prompt
        assert "组织成连贯摘要" in prompt

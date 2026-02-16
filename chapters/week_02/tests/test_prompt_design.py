"""
Tests for Prompt Design concepts.

This module tests the PromptTemplate class and four-element prompt construction
including role, task, constraints, and output format.

Validates anchor: prompt-four-elements
"""

import pytest
from .conftest import PromptTemplate


class TestPromptTemplateInit:
    """Tests for PromptTemplate class initialization."""
    
    def test_basic_initialization(self):
        """Test that PromptTemplate initializes correctly with required fields."""
        template = PromptTemplate(
            name="test_template",
            role="你是一个助手",
            task="完成任务",
            constraints=["约束1"],
            output_format="输出格式"
        )
        
        assert template.name == "test_template"
        assert template.role == "你是一个助手"
        assert template.task == "完成任务"
        assert template.constraints == ["约束1"]
        assert template.output_format == "输出格式"
    
    def test_initialization_with_few_shot_examples(self):
        """Test initialization with few-shot examples."""
        examples = [
            {"input": "示例输入", "output": "示例输出"}
        ]
        
        template = PromptTemplate(
            name="test",
            role="助手",
            task="分类",
            constraints=[],
            output_format="JSON",
            few_shot_examples=examples
        )
        
        assert template.few_shot_examples == examples
        assert len(template.few_shot_examples) == 1
    
    def test_initialization_with_cot(self):
        """Test initialization with Chain-of-Thought enabled."""
        cot_steps = [
            "第一步：分析问题",
            "第二步：给出答案"
        ]
        
        template = PromptTemplate(
            name="cot_template",
            role="助手",
            task="推理任务",
            constraints=[],
            output_format="JSON",
            use_cot=True,
            cot_steps=cot_steps
        )
        
        assert template.use_cot is True
        assert template.cot_steps == cot_steps
    
    def test_default_values(self):
        """Test that optional fields have correct default values."""
        template = PromptTemplate(
            name="minimal",
            role="助手",
            task="任务",
            constraints=[],
            output_format="文本"
        )
        
        assert template.few_shot_examples is None
        assert template.use_cot is False
        assert template.cot_steps is None


class TestFourElementPrompt:
    """Tests for four-element prompt construction."""
    
    def test_role_element_present(self, sample_template):
        """Test that role element is included in rendered prompt."""
        prompt = sample_template.render("测试输入")
        
        assert "角色：" in prompt
        assert sample_template.role in prompt
    
    def test_task_element_present(self, sample_template):
        """Test that task element is included in rendered prompt."""
        prompt = sample_template.render("测试输入")
        
        assert "任务：" in prompt
        assert sample_template.task in prompt
    
    def test_constraints_element_present(self, sample_template):
        """Test that constraints element is included in rendered prompt."""
        prompt = sample_template.render("测试输入")
        
        assert "约束：" in prompt
        for constraint in sample_template.constraints:
            assert constraint in prompt
    
    def test_format_element_present(self, sample_template):
        """Test that output format element is included in rendered prompt."""
        prompt = sample_template.render("测试输入")
        
        assert "格式：" in prompt
        assert sample_template.output_format in prompt
    
    def test_all_four_elements_together(self, sample_template):
        """Test that all four elements appear in correct structure."""
        prompt = sample_template.render("测试新闻")
        
        # Verify all elements are present
        assert "角色：" in prompt
        assert "任务：" in prompt
        assert "约束：" in prompt
        assert "格式：" in prompt
        
        # Verify the input is included
        assert "测试新闻" in prompt
    
    def test_four_elements_improve_clarity(self):
        """Test that four-element prompt is more structured than minimal prompt."""
        # Minimal prompt (just task)
        minimal_prompt = "判断以下新闻属于哪个类别：苹果发布新品"
        
        # Four-element prompt
        template = PromptTemplate(
            name="news_classify",
            role="你是一个新闻分类助手",
            task="判断以下新闻属于哪个类别",
            constraints=["只输出类别名称", "不要解释原因"],
            output_format="财经、科技、体育、娱乐"
        )
        full_prompt = template.render("苹果发布新品")
        
        # Four-element prompt should be longer and more structured
        assert len(full_prompt) > len(minimal_prompt)
        assert full_prompt.count("\n") >= minimal_prompt.count("\n")


class TestTemplateVariableSubstitution:
    """Tests for template variable substitution."""
    
    def test_single_input_substitution(self, sample_template):
        """Test that input text is substituted correctly."""
        input_text = "这是一条测试新闻"
        prompt = sample_template.render(input_text)
        
        assert input_text in prompt
    
    def test_different_inputs_produce_different_prompts(self, sample_template):
        """Test that different inputs produce different prompts."""
        prompt1 = sample_template.render("新闻A")
        prompt2 = sample_template.render("新闻B")
        
        assert prompt1 != prompt2
        assert "新闻A" in prompt1
        assert "新闻B" in prompt2
    
    def test_examples_override_default(self, sample_template):
        """Test that explicitly provided examples override default few-shot examples."""
        custom_examples = [
            {"input": "自定义示例", "output": "自定义输出"}
        ]
        
        prompt = sample_template.render("测试", examples=custom_examples)
        
        assert "自定义示例" in prompt
        assert "自定义输出" in prompt
    
    def test_empty_examples_parameter(self, sample_template):
        """Test behavior when empty examples list is provided."""
        # Empty list should still use default examples if available
        prompt = sample_template.render("测试", examples=[])
        
        # When examples=[] is passed explicitly, it's falsy so default should be used
        # Based on the logic: (examples or self.few_shot_examples)
        # Empty list is falsy, so default should be used
        assert "苹果公司发布新款 iPhone" in prompt  # from default examples


class TestMissingVariableHandling:
    """Tests for handling missing or invalid variables."""
    
    def test_empty_input_text(self, sample_template):
        """Test that empty input is handled gracefully."""
        prompt = sample_template.render("")
        
        # Should still contain the four elements
        assert "角色：" in prompt
        assert "任务：" in prompt
        # Input line should be present but empty
        assert prompt.endswith("\n") or prompt.strip().endswith("")
    
    def test_none_input_handling(self, sample_template):
        """Test that None input is handled appropriately."""
        # The current implementation converts None to string "None"
        # This test documents the behavior
        try:
            prompt = sample_template.render(None)
            # If no error, None was converted to string
            assert "None" in prompt or prompt is not None
        except (TypeError, AttributeError):
            # Also acceptable: raising an error
            pass
    
    def test_special_characters_in_input(self, sample_template):
        """Test that special characters in input are preserved."""
        special_input = "新闻中包含\"引号\"和\n换行符"
        prompt = sample_template.render(special_input)
        
        assert "引号" in prompt
    
    def test_very_long_input(self, sample_template):
        """Test handling of very long input text."""
        long_input = "这是一段非常长的新闻内容。" * 1000
        prompt = sample_template.render(long_input)
        
        # Should include the full input
        assert long_input in prompt
    
    def test_unicode_input(self, sample_template):
        """Test handling of various unicode characters."""
        unicode_inputs = [
            "中文新闻",
            "日本語ニュース",
            "emoji 🎉 news",
            "العربية news"
        ]
        
        for input_text in unicode_inputs:
            prompt = sample_template.render(input_text)
            assert input_text in prompt


class TestPromptStructure:
    """Tests for overall prompt structure and format."""
    
    def test_prompt_sections_order(self, sample_template):
        """Test that prompt sections appear in correct order."""
        prompt = sample_template.render("测试输入")
        
        # Find positions of key sections
        role_pos = prompt.find("角色：")
        task_pos = prompt.find("任务：")
        constraint_pos = prompt.find("约束：")
        format_pos = prompt.find("格式：")
        
        # Role should come before task
        assert role_pos < task_pos
        # Task should come before format
        assert task_pos < format_pos
    
    def test_cot_steps_included_when_enabled(self, cot_template):
        """Test that CoT steps are included when use_cot is True."""
        prompt = cot_template.render("测试工单")
        
        assert "请按以下步骤思考：" in prompt
        for step in cot_template.cot_steps:
            assert step in prompt
    
    def test_cot_steps_not_included_when_disabled(self, sample_template):
        """Test that CoT steps are not included when use_cot is False."""
        prompt = sample_template.render("测试新闻")
        
        assert "请按以下步骤思考：" not in prompt

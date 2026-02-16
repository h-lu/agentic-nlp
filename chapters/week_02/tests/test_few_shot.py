"""
Tests for Few-shot Learning concepts.

This module tests the FewShotManager class including example loading,
dynamic selection, and example count management.

Validates anchor: few-shot-stability
"""

import pytest
import os
import yaml
from .conftest import FewShotManager


class TestFewShotManagerInit:
    """Tests for FewShotManager class initialization."""
    
    def test_initialization_with_data(self, sample_few_shot_examples):
        """Test initialization with direct examples data."""
        manager = FewShotManager(examples_data=sample_few_shot_examples)
        
        assert manager.examples == sample_few_shot_examples
        assert "classify" in manager.examples
    
    def test_initialization_with_file(self, temp_yaml_file):
        """Test initialization by loading from YAML file."""
        manager = FewShotManager(examples_file=temp_yaml_file)
        
        assert "classify" in manager.examples
        assert len(manager.examples["classify"]) == 2
    
    def test_initialization_empty(self):
        """Test initialization with no data."""
        manager = FewShotManager()
        
        assert manager.examples == {}
    
    def test_initialization_nonexistent_file(self):
        """Test initialization with non-existent file path."""
        manager = FewShotManager(examples_file="/nonexistent/path.yaml")
        
        assert manager.examples == {}


class TestExampleLoading:
    """Tests for loading examples from YAML files."""
    
    def test_load_valid_yaml(self, temp_yaml_file):
        """Test loading examples from a valid YAML file."""
        manager = FewShotManager(examples_file=temp_yaml_file)
        
        examples = manager.get_examples("classify")
        
        assert len(examples) == 2
        assert examples[0]["input"] == "苹果公司发布新款 iPhone"
    
    def test_load_with_unicode_content(self, tmp_path):
        """Test loading YAML file with Chinese characters."""
        yaml_content = {
            "classify": [
                {"input": "中文测试输入", "output": "中文输出"}
            ]
        }
        
        yaml_file = tmp_path / "unicode_examples.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, allow_unicode=True)
        
        manager = FewShotManager(examples_file=str(yaml_file))
        examples = manager.get_examples("classify")
        
        assert examples[0]["input"] == "中文测试输入"
    
    def test_load_multiple_tasks(self, tmp_path):
        """Test loading examples for multiple task types."""
        yaml_content = {
            "classify": [
                {"input": "分类输入", "output": "分类输出"}
            ],
            "summarize": [
                {"input": "摘要输入", "output": "摘要输出"}
            ],
            "extract": [
                {"input": "抽取输入", "output": "抽取输出"}
            ]
        }
        
        yaml_file = tmp_path / "multi_task.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, allow_unicode=True)
        
        manager = FewShotManager(examples_file=str(yaml_file))
        
        assert len(manager.get_examples("classify")) == 1
        assert len(manager.get_examples("summarize")) == 1
        assert len(manager.get_examples("extract")) == 1
    
    def test_load_empty_task(self, temp_yaml_file):
        """Test getting examples for a task with no examples."""
        manager = FewShotManager(examples_file=temp_yaml_file)
        
        examples = manager.get_examples("nonexistent_task")
        
        assert examples == []


class TestDynamicExampleSelection:
    """Tests for dynamic example selection based on criteria."""
    
    def test_select_by_category(self, few_shot_manager):
        """Test selecting examples filtered by category."""
        examples = few_shot_manager.get_examples("classify", category="科技")
        
        assert len(examples) == 1
        assert examples[0]["category"] == "科技"
    
    def test_select_all_categories(self, few_shot_manager):
        """Test selecting examples without category filter."""
        examples = few_shot_manager.get_examples("classify")
        
        # Should return examples from all categories
        categories = {e["category"] for e in examples}
        assert len(categories) > 1
    
    def test_select_nonexistent_category(self, few_shot_manager):
        """Test selecting examples for a category that doesn't exist."""
        examples = few_shot_manager.get_examples("classify", category="不存在的类别")
        
        assert examples == []
    
    def test_category_preserves_order(self, sample_few_shot_examples):
        """Test that examples are returned in their original order."""
        # Create manager with ordered examples
        ordered_examples = {
            "classify": [
                {"input": "第一", "output": "A", "category": "cat1"},
                {"input": "第二", "output": "B", "category": "cat1"},
                {"input": "第三", "output": "C", "category": "cat1"},
            ]
        }
        manager = FewShotManager(examples_data=ordered_examples)
        
        examples = manager.get_examples("classify", category="cat1", n=3)
        
        assert examples[0]["input"] == "第一"
        assert examples[1]["input"] == "第二"
        assert examples[2]["input"] == "第三"


class TestExampleCountLimits:
    """Tests for controlling the number of examples returned."""
    
    def test_default_count(self, few_shot_manager):
        """Test that default count is 3 examples."""
        examples = few_shot_manager.get_examples("classify")
        
        assert len(examples) <= 3
    
    def test_explicit_count_limit(self, few_shot_manager):
        """Test explicit count limit parameter."""
        examples = few_shot_manager.get_examples("classify", n=2)
        
        assert len(examples) == 2
    
    def test_count_exceeds_available(self, few_shot_manager):
        """Test when requested count exceeds available examples."""
        # Only 1 example with category "科技"
        examples = few_shot_manager.get_examples("classify", category="科技", n=5)
        
        assert len(examples) == 1  # Should return all available
    
    def test_count_zero(self, few_shot_manager):
        """Test requesting zero examples."""
        examples = few_shot_manager.get_examples("classify", n=0)
        
        assert len(examples) == 0
    
    def test_negative_count(self, few_shot_manager):
        """Test behavior with negative count (should return empty or handle gracefully)."""
        examples = few_shot_manager.get_examples("classify", n=-1)
        
        # Python slicing with negative indices has specific behavior
        # The implementation uses [:n] which with n=-1 returns all but last
        # This is an edge case to document
        assert isinstance(examples, list)


class TestExampleFormatting:
    """Tests for formatting examples as prompt sections."""
    
    def test_format_basic_examples(self, few_shot_manager):
        """Test basic example formatting."""
        examples = few_shot_manager.get_examples("classify", n=2)
        formatted = few_shot_manager.format_examples(examples)
        
        assert "示例：" in formatted
        assert "输入：" in formatted
        assert "输出：" in formatted
    
    def test_format_preserves_content(self, few_shot_manager):
        """Test that formatting preserves example content."""
        examples = few_shot_manager.get_examples("classify", n=1)
        formatted = few_shot_manager.format_examples(examples)
        
        assert examples[0]["input"] in formatted
        assert examples[0]["output"] in formatted
    
    def test_format_empty_list(self, few_shot_manager):
        """Test formatting an empty example list."""
        formatted = few_shot_manager.format_examples([])
        
        # Should still have the header
        assert "示例：" in formatted
    
    def test_format_multiple_examples(self, few_shot_manager):
        """Test formatting multiple examples."""
        examples = few_shot_manager.get_examples("classify", n=3)
        formatted = few_shot_manager.format_examples(examples)
        
        # Should have "输入：" for each example
        input_count = formatted.count("输入：")
        assert input_count == len(examples)


class TestFewShotEdgeCases:
    """Tests for edge cases in few-shot management."""
    
    def test_malformed_example_data(self):
        """Test handling of malformed example data."""
        malformed_data = {
            "classify": [
                {"input": "正常示例", "output": "正常输出"},
                {"input": "缺少输出"},  # Missing 'output' key
                {"output": "缺少输入"},  # Missing 'input' key
            ]
        }
        manager = FewShotManager(examples_data=malformed_data)
        
        examples = manager.get_examples("classify")
        
        # Should return all examples even if some are malformed
        assert len(examples) == 3
    
    def test_empty_example_values(self):
        """Test handling of examples with empty values."""
        data_with_empties = {
            "classify": [
                {"input": "", "output": "有输出"},
                {"input": "有输入", "output": ""},
            ]
        }
        manager = FewShotManager(examples_data=data_with_empties)
        
        examples = manager.get_examples("classify")
        
        assert len(examples) == 2
    
    def test_very_long_example_text(self):
        """Test handling of very long example text."""
        long_text = "这是一段很长的文本。" * 100
        data = {
            "classify": [
                {"input": long_text, "output": "类别"}
            ]
        }
        manager = FewShotManager(examples_data=data)
        
        examples = manager.get_examples("classify")
        formatted = manager.format_examples(examples)
        
        assert long_text in formatted
    
    def test_special_characters_in_examples(self):
        """Test handling of special characters in examples."""
        special_chars = ["\"", "'", "\n", "\t", "{}", "[]"]
        data = {
            "classify": [
                {"input": f"包含{char}的文本", "output": "类别"}
                for char in special_chars
            ]
        }
        manager = FewShotManager(examples_data=data)
        
        examples = manager.get_examples("classify", n=len(special_chars))
        
        assert len(examples) == len(special_chars)


class TestFewShotIntegration:
    """Integration tests for few-shot with prompt templates."""
    
    def test_few_shot_improves_format_consistency(self, sample_few_shot_examples):
        """Test that few-shot examples are properly formatted for prompt use."""
        from .conftest import PromptTemplate
        
        manager = FewShotManager(examples_data=sample_few_shot_examples)
        examples = manager.get_examples("classify", n=3)
        
        template = PromptTemplate(
            name="test",
            role="助手",
            task="分类",
            constraints=[],
            output_format="类别",
            few_shot_examples=examples
        )
        
        prompt = template.render("新输入")
        
        # Verify all examples are in the prompt
        for ex in examples:
            assert ex["input"] in prompt
            assert ex["output"] in prompt
    
    def test_different_example_counts_affect_prompt_length(self, few_shot_manager):
        """Test that more examples create longer prompts."""
        from .conftest import PromptTemplate
        
        examples_2 = few_shot_manager.get_examples("classify", n=2)
        examples_4 = few_shot_manager.get_examples("classify", n=4)
        
        template_2 = PromptTemplate(
            name="test",
            role="助手",
            task="分类",
            constraints=[],
            output_format="类别",
            few_shot_examples=examples_2
        )
        
        template_4 = PromptTemplate(
            name="test",
            role="助手",
            task="分类",
            constraints=[],
            output_format="类别",
            few_shot_examples=examples_4
        )
        
        prompt_2 = template_2.render("测试")
        prompt_4 = template_4.render("测试")
        
        # More examples should create longer prompt
        assert len(prompt_4) > len(prompt_2)

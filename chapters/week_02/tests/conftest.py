"""
Pytest configuration and fixtures for Week 02 tests.

This module provides common fixtures for testing Prompt Engineering concepts
including PromptTemplate, FewShotManager, CoT generation, and evaluation.
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Optional


# =============================================================================
# Mock Classes for Testing (simulating the actual implementations)
# =============================================================================

@dataclass
class PromptTemplate:
    """Mock PromptTemplate class for testing."""
    name: str
    role: str
    task: str
    constraints: List[str]
    output_format: str
    few_shot_examples: Optional[List[dict]] = None
    use_cot: bool = False
    cot_steps: Optional[List[str]] = None

    def render(self, input_text: str, examples: List[dict] = None) -> str:
        """Render the prompt with the given input."""
        parts = [f"角色：{self.role}"]

        # Add Few-shot examples
        if examples or self.few_shot_examples:
            parts.append("\n示例：")
            for ex in (examples or self.few_shot_examples):
                parts.append(f"输入：\"{ex['input']}\"")
                parts.append(f"输出：{ex['output']}")
            parts.append("")

        # Add task
        parts.append(f"任务：{self.task}")

        # Add constraints
        if self.constraints:
            parts.append("约束：")
            for c in self.constraints:
                parts.append(f"- {c}")

        # Add CoT steps
        if self.use_cot and self.cot_steps:
            parts.append("\n请按以下步骤思考：")
            for i, step in enumerate(self.cot_steps, 1):
                parts.append(f"{i}. {step}")

        # Add output format
        parts.append(f"\n格式：{self.output_format}")

        # Add input
        parts.append(f"\n{input_text}")

        return "\n".join(parts)


class FewShotManager:
    """Mock FewShotManager class for testing."""
    
    def __init__(self, examples_file: str = None, examples_data: dict = None):
        """Initialize with either a file path or direct data."""
        if examples_data:
            self.examples = examples_data
        elif examples_file and os.path.exists(examples_file):
            import yaml
            with open(examples_file, 'r', encoding='utf-8') as f:
                self.examples = yaml.safe_load(f)
        else:
            self.examples = {}
    
    def get_examples(self, task: str, category: str = None, n: int = 3) -> List[Dict]:
        """
        Get examples for a specific task.
        
        Args:
            task: Task type (classify/summarize/extract)
            category: Optional category filter
            n: Maximum number of examples to return
        """
        task_examples = self.examples.get(task, [])
        
        if category:
            task_examples = [e for e in task_examples if e.get('category') == category]
        
        return task_examples[:n]
    
    def format_examples(self, examples: List[Dict]) -> str:
        """Format examples as a prompt section."""
        lines = ["示例："]
        for ex in examples:
            lines.append(f"输入：\"{ex['input']}\"")
            lines.append(f"输出：{ex['output']}")
            lines.append("")
        return "\n".join(lines)


@dataclass
class TestCase:
    """Test case for evaluation."""
    input: str
    expected_output: str
    metadata: Dict = None


@dataclass
class EvalResult:
    """Evaluation result."""
    prompt_version: str
    accuracy: float
    format_compliance: float
    avg_latency_ms: float
    total_tokens: int
    error_cases: List[Dict]


class MockLLMClient:
    """Mock LLM client for testing without real API calls."""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.last_usage = MagicMock(total_tokens=100)
        self.call_count = 0
    
    def call(self, prompt: str) -> str:
        """Simulate an LLM API call."""
        self.call_count += 1
        
        # Try to find a matching response based on keywords
        for key, response in self.responses.items():
            if key in prompt:
                return response
        
        # Default response
        return "科技"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_template():
    """Fixture providing a basic PromptTemplate instance."""
    return PromptTemplate(
        name="news_classify",
        role="你是一个新闻分类助手",
        task="判断以下新闻属于哪个类别",
        constraints=["只输出类别名称", "不要解释原因"],
        output_format="从以下选项中选一个：财经、科技、体育、娱乐",
        few_shot_examples=[
            {"input": "苹果公司发布新款 iPhone", "output": "科技"},
            {"input": "央行降准 0.5 个百分点", "output": "财经"},
        ]
    )


@pytest.fixture
def cot_template():
    """Fixture providing a CoT-enabled PromptTemplate."""
    return PromptTemplate(
        name="ticket_classify_cot",
        role="你是一个客服工单分类助手",
        task="判断以下工单应该分到哪个部门",
        constraints=["最后只输出部门名称", "分析过程要简洁"],
        output_format="从以下选项中选一个：技术支持、账务问题、功能建议、投诉、其他",
        use_cot=True,
        cot_steps=[
            "用户遇到了什么问题？",
            "问题的核心诉求是什么？",
            "哪个部门最适合处理这个诉求？",
            "最终分类结果是什么？"
        ]
    )


@pytest.fixture
def sample_few_shot_examples():
    """Fixture providing sample few-shot examples data."""
    return {
        "classify": [
            {"input": "苹果公司发布新款 iPhone，搭载 A18 芯片", "output": "科技", "category": "科技"},
            {"input": "中国男篮在亚运会决赛中战胜韩国队", "output": "体育", "category": "体育"},
            {"input": "央行宣布下调存款准备金率 0.5 个百分点", "output": "财经", "category": "财经"},
            {"input": "某知名演员宣布结婚消息", "output": "娱乐", "category": "娱乐"},
        ]
    }


@pytest.fixture
def few_shot_manager(sample_few_shot_examples):
    """Fixture providing a FewShotManager instance with sample data."""
    return FewShotManager(examples_data=sample_few_shot_examples)


@pytest.fixture
def mock_client():
    """Fixture providing a mock LLM client."""
    return MockLLMClient(
        responses={
            "iPhone": "科技",
            "央行": "财经",
            "男篮": "体育",
            "演员": "娱乐",
        }
    )


@pytest.fixture
def test_cases():
    """Fixture providing a list of test cases for evaluation."""
    return [
        TestCase("苹果发布新款 iPhone", "科技"),
        TestCase("央行降准 0.5 个百分点", "财经"),
        TestCase("中国男篮战胜韩国队", "体育"),
        TestCase("某演员官宣结婚", "娱乐"),
        TestCase("某科技公司发布新产品", "科技"),
    ]


@pytest.fixture
def temp_yaml_file(tmp_path):
    """Fixture providing a temporary YAML file with examples."""
    import yaml
    
    yaml_content = {
        "classify": [
            {"input": "苹果公司发布新款 iPhone", "output": "科技", "category": "科技"},
            {"input": "央行降准 0.5 个百分点", "output": "财经", "category": "财经"},
        ]
    }
    
    yaml_file = tmp_path / "test_examples.yaml"
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    return str(yaml_file)


@pytest.fixture
def temp_csv_testset(tmp_path):
    """Fixture providing a temporary CSV test set file."""
    import csv
    
    csv_file = tmp_path / "test_set.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['input', 'expected'])
        writer.writeheader()
        writer.writerow({'input': '苹果发布新品', 'expected': '科技'})
        writer.writerow({'input': '央行降准', 'expected': '财经'})
    
    return str(csv_file)


# =============================================================================
# Helper Functions
# =============================================================================

def build_prompt_v1(input_text: str) -> str:
    """Build a basic prompt without few-shot examples."""
    return f"""角色：你是一个新闻分类助手。
任务：判断以下新闻属于哪个类别。
约束：只输出类别名称，不要解释。
格式：财经、科技、体育、娱乐。

新闻内容：{input_text}"""


def build_prompt_v2(input_text: str) -> str:
    """Build a prompt with few-shot examples."""
    return f"""角色：你是一个新闻分类助手。

示例：
输入："苹果公司发布新款 iPhone"
输出：科技

输入："央行降准 0.5 个百分点"
输出：财经

任务：判断以下新闻属于哪个类别。
约束：只输出类别名称，格式与示例一致。
格式：财经、科技、体育、娱乐。

新闻内容：{input_text}"""


def parse_category(response: str) -> str:
    """Parse classification result from response."""
    return response.strip()

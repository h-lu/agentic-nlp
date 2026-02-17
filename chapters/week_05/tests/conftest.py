"""
Pytest configuration and fixtures for Week 05 tests.

This module provides common fixtures for testing LLM Agent concepts including
text analysis tools, Function Calling, ReAct pattern, and task planning.
"""

import pytest
from unittest.mock import MagicMock, Mock
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from collections import Counter
import json


# =============================================================================
# Mock Classes for Testing (simulating actual Agent implementations)
# =============================================================================

@dataclass
class ToolCall:
    """Represents a single tool call."""
    name: str
    arguments: Dict
    id: str = "test_call_id"


@dataclass
class LLMResponse:
    """Mock LLM response."""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class TextAnalyzerTools:
    """Text analysis tools for testing."""

    POSITIVE_WORDS = ["好", "优秀", "满意", "喜欢", "棒", "推荐", "不错"]
    NEGATIVE_WORDS = ["差", "慢", "糟糕", "不满", "差劲", "坏", "问题"]

    @staticmethod
    def analyze_sentiment(text: str) -> Dict:
        """
        Analyze text sentiment (simplified implementation).

        Returns:
            Dict with sentiment (positive/negative/neutral) and score
        """
        if not text or not text.strip():
            return {"sentiment": "neutral", "score": 0, "reason": "空文本"}

        pos_count = sum(1 for word in TextAnalyzerTools.POSITIVE_WORDS if word in text)
        neg_count = sum(1 for word in TextAnalyzerTools.NEGATIVE_WORDS if word in text)

        if pos_count > neg_count:
            return {
                "sentiment": "positive",
                "score": pos_count - neg_count,
                "confidence": min(0.5 + (pos_count - neg_count) * 0.1, 1.0),
                "reason": f"正面词{pos_count}个，负面词{neg_count}个"
            }
        elif neg_count > pos_count:
            return {
                "sentiment": "negative",
                "score": neg_count - pos_count,
                "confidence": min(0.5 + (neg_count - pos_count) * 0.1, 1.0),
                "reason": f"正面词{pos_count}个，负面词{neg_count}个"
            }
        else:
            return {
                "sentiment": "neutral",
                "score": 0,
                "confidence": 0.5,
                "reason": "正负面词数量相当"
            }

    @staticmethod
    def extract_keywords(text: str, top_k: int = 5) -> Dict:
        """
        Extract keywords from text.

        Returns:
            Dict with keywords list and counts
        """
        if not text or not text.strip():
            return {"keywords": [], "counts": []}

        # Simple word extraction (in production, use jieba)
        import re
        words = re.findall(r'[\w]{2,}', text)

        # Filter stopwords
        stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "也", "都"}
        filtered = [w for w in words if w not in stopwords]

        if not filtered:
            return {"keywords": [], "counts": []}

        counter = Counter(filtered)
        top_words = counter.most_common(top_k)

        return {
            "keywords": [w for w, c in top_words],
            "counts": [c for w, c in top_words]
        }

    @staticmethod
    def count_word_freq(text: str, top_k: int = 10) -> Dict:
        """
        Count word frequency in text.

        Returns:
            Dict with top_words list
        """
        if not text or not text.strip():
            return {"top_words": []}

        import re
        # Extract Chinese characters and words
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)

        stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "也", "都", "，", "。", "！", "？"}
        filtered = [w for w in words if w not in stopwords]

        if not filtered:
            return {"top_words": []}

        counter = Counter(filtered)
        top_words = counter.most_common(top_k)

        return {
            "top_words": [
                {"word": w, "count": c}
                for w, c in top_words
            ]
        }

    @staticmethod
    def summarize_text(text: str, max_length: int = 100) -> Dict:
        """Summarize text (simplified: truncate)."""
        if not text or not text.strip():
            return {"summary": "", "original_length": 0}

        summary = text[:max_length] + "..." if len(text) > max_length else text
        return {"summary": summary, "original_length": len(text)}


class MockLLMClient:
    """Mock LLM client for testing Agent behavior."""

    def __init__(
        self,
        responses: Dict[str, Any] = None,
        tool_call_sequence: List[ToolCall] = None
    ):
        """
        Initialize mock client.

        Args:
            responses: Predefined responses for specific prompts
            tool_call_sequence: Sequence of tool calls to return
        """
        self.responses = responses or {}
        self.tool_call_sequence = tool_call_sequence or []
        self.call_count = 0
        self.message_history = []

    def chat(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> LLMResponse:
        """
        Simulate chat completion.

        Args:
            messages: Chat messages
            tools: Available tools for function calling
            **kwargs: Additional parameters

        Returns:
            LLMResponse with content or tool_calls
        """
        self.call_count += 1
        self.message_history.append(messages)

        # Check for predefined responses
        last_msg = messages[-1].get("content", "") if messages else ""
        for key, response in self.responses.items():
            if key in last_msg:
                if isinstance(response, str):
                    return LLMResponse(content=response)
                return response

        # Return tool calls if sequence defined
        if self.tool_call_sequence:
            idx = self.call_count - 1
            if idx < len(self.tool_call_sequence):
                return LLMResponse(
                    content="让我调用工具来处理这个请求。",
                    tool_calls=[self.tool_call_sequence[idx]]
                )

        # Default response
        return LLMResponse(content="这是一个测试回复。")

    def reset(self):
        """Reset call count and history."""
        self.call_count = 0
        self.message_history = []


class ReActAgent:
    """ReAct pattern Agent for testing."""

    def __init__(
        self,
        tools: Dict[str, Callable],
        llm_client: MockLLMClient = None,
        max_iterations: int = 10,
        verbose: bool = False
    ):
        """
        Initialize ReAct Agent.

        Args:
            tools: Dictionary of tool name to function mapping
            llm_client: Mock LLM client
            max_iterations: Maximum iterations before stopping
            verbose: Whether to print verbose output
        """
        self.tools = tools
        self.llm = llm_client or MockLLMClient()
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.tool_schemas = self._build_tool_schemas()

    def _build_tool_schemas(self) -> List[Dict]:
        """Build tool schemas for LLM."""
        schemas = []
        for name in self.tools.keys():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"Tool: {name}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Input text"}
                        },
                        "required": ["text"]
                    }
                }
            })
        return schemas

    def run(self, task: str) -> Dict:
        """
        Run ReAct loop.

        Args:
            task: Task description

        Returns:
            Dict with final_answer and history
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个智能助手，能够使用工具完成复杂任务。"
            },
            {"role": "user", "content": task}
        ]

        history = []

        for iteration in range(self.max_iterations):
            response = self.llm.chat(messages, tools=self.tool_schemas)

            # Record history
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    try:
                        tool_func = self.tools[tool_call.name]
                        result = tool_func(**tool_call.arguments)

                        history.append({
                            "iteration": iteration + 1,
                            "action": tool_call.name,
                            "input": tool_call.arguments,
                            "result": result
                        })

                        # Add result to messages
                        messages.append({
                            "role": "assistant",
                            "content": response.content or ""
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                    except Exception as e:
                        history.append({
                            "iteration": iteration + 1,
                            "action": tool_call.name,
                            "input": tool_call.arguments,
                            "error": str(e)
                        })
                        # Continue on error
            else:
                # No tool calls, return final answer
                return {
                    "final_answer": response.content,
                    "history": history,
                    "iterations": iteration + 1,
                    "status": "completed"
                }

        return {
            "final_answer": "达到最大迭代次数",
            "history": history,
            "iterations": self.max_iterations,
            "status": "max_iterations_reached"
        }


class PlanningAgent(ReActAgent):
    """Planning Agent that decomposes tasks before execution."""

    def __init__(self, *args, plan_first: bool = True, **kwargs):
        """
        Initialize Planning Agent.

        Args:
            *args: Args passed to ReActAgent
            plan_first: Whether to create plan before execution
            **kwargs: Kwargs passed to ReActAgent
        """
        super().__init__(*args, **kwargs)
        self.plan_first = plan_first
        self.last_plan = None

    def run(self, task: str) -> Dict:
        """
        Run planning + execution.

        Args:
            task: Task description

        Returns:
            Dict with final_answer, history, and plan
        """
        plan = None
        if self.plan_first:
            plan = self._create_plan(task)
            self.last_plan = plan

        result = super().run(task)
        result["plan"] = plan
        return result

    def _create_plan(self, task: str) -> str:
        """Create task plan."""
        tool_list = list(self.tools.keys())

        # Simple planning logic
        if "分析" in task and "情感" in task:
            steps = [
                "1. 加载文本",
                "2. 分析情感",
                "3. 汇总结果"
            ]
        elif "关键词" in task or "词频" in task:
            steps = [
                "1. 加载文本",
                "2. 提取关键词/统计词频",
                "3. 返回结果"
            ]
        else:
            steps = [
                f"1. 理解任务: {task[:20]}...",
                f"2. 执行分析 (使用 {', '.join(tool_list)})",
                "3. 生成答案"
            ]

        return "\n".join(steps)


@dataclass
class ToolDefinition:
    """Tool definition for Function Calling."""
    name: str
    description: str
    parameters: Dict
    function: Callable = None

    def to_schema(self) -> Dict:
        """Convert to OpenAI-style schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_texts():
    """Fixture providing sample texts for testing."""
    return {
        "positive": "产品质量很好，非常满意，推荐购买！",
        "negative": "物流太慢了，客服态度差，很失望。",
        "neutral": "产品已收到，正在使用中。",
        "mixed": "产品质量很好，但物流太慢了，希望改进。",
        "empty": "",
        "short": "好",
        "long": "这是一段较长的文本内容。" * 20,
        "special_chars": "产品???质量@@@很好###，但物流!!!太慢了...",
        "chinese_english": "The 产品质量 is very good, but 物流 is too slow.",
        "multiple_feedback": [
            "产品质量很好，但物流太慢了，希望改进。",
            "客服态度很差，问题一直没解决。",
            "价格合理，物流也快，推荐购买。",
            "用了两周就坏了，质量堪忧。"
        ]
    }


@pytest.fixture
def text_analyzer():
    """Fixture providing TextAnalyzerTools."""
    return TextAnalyzerTools()


@pytest.fixture
def mock_llm_client():
    """Fixture providing MockLLMClient."""
    return MockLLMClient()


@pytest.fixture
def tool_call_sentiment():
    """Fixture providing sentiment analysis tool call."""
    return ToolCall(
        name="analyze_sentiment",
        arguments={"text": "产品质量很好，非常满意"},
        id="call_sentiment_1"
    )


@pytest.fixture
def tool_call_keywords():
    """Fixture providing keyword extraction tool call."""
    return ToolCall(
        name="extract_keywords",
        arguments={"text": "物流太慢了，客服态度差", "top_k": 3},
        id="call_keywords_1"
    )


@pytest.fixture
def tool_call_wordfreq():
    """Fixture providing word frequency tool call."""
    return ToolCall(
        name="count_word_freq",
        arguments={"text": "产品质量很好，物流太慢", "top_k": 5},
        id="call_wordfreq_1"
    )


@pytest.fixture
def tool_definitions():
    """Fixture providing tool definitions."""
    return [
        ToolDefinition(
            name="analyze_sentiment",
            description="分析一段文本的情感倾向（正面/负面/中性）",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要分析的文本内容"
                    }
                },
                "required": ["text"]
            }
        ),
        ToolDefinition(
            name="extract_keywords",
            description="从文本中提取关键词",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要提取关键词的文本"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回前 K 个关键词",
                        "default": 5
                    }
                },
                "required": ["text"]
            }
        ),
        ToolDefinition(
            name="count_word_freq",
            description="统计文本中词频最高的前 K 个词",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要统计词频的文本"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回前 K 个高频词",
                        "default": 10
                    }
                },
                "required": ["text"]
            }
        )
    ]


@pytest.fixture
def tool_dict(text_analyzer):
    """Fixture providing tools as dictionary."""
    return {
        "analyze_sentiment": text_analyzer.analyze_sentiment,
        "extract_keywords": text_analyzer.extract_keywords,
        "count_word_freq": text_analyzer.count_word_freq,
    }


@pytest.fixture
def react_agent(tool_dict, mock_llm_client):
    """Fixture providing ReActAgent."""
    return ReActAgent(
        tools=tool_dict,
        llm_client=mock_llm_client,
        max_iterations=10,
        verbose=False
    )


@pytest.fixture
def planning_agent(tool_dict, mock_llm_client):
    """Fixture providing PlanningAgent."""
    return PlanningAgent(
        tools=tool_dict,
        llm_client=mock_llm_client,
        max_iterations=10,
        verbose=False,
        plan_first=True
    )


@pytest.fixture
def tool_call_sequence_analyze():
    """Fixture providing tool call sequence for analysis task."""
    return [
        ToolCall(
            name="analyze_sentiment",
            arguments={"text": "产品质量很好"},
            id="call_1"
        ),
        ToolCall(
            name="extract_keywords",
            arguments={"text": "产品质量很好", "top_k": 3},
            id="call_2"
        )
    ]


@pytest.fixture
def llm_client_with_sequence(tool_call_sequence_analyze):
    """Fixture providing LLM client with predefined tool call sequence."""
    return MockLLMClient(tool_call_sequence=tool_call_sequence_analyze)


@pytest.fixture
def agent_tasks():
    """Fixture providing sample Agent tasks."""
    return {
        "simple_analyze": "分析这段文本的情感：产品质量很好，非常满意。",
        "multi_tool": "分析客户反馈的情感并提取关键词：物流太慢了，客服态度差。",
        "empty_task": "",
        "complex_task": """分析以下客户反馈，并给出总结：
1. "产品质量很好，但物流太慢了，希望改进。"
2. "客服态度很差，问题一直没解决。"
3. "价格合理，物流也快，推荐购买。"
4. "用了两周就坏了，质量堪忧。"
"""
    }


@pytest.fixture
def agent_config():
    """Fixture providing Agent configuration."""
    return {
        "max_iterations": 10,
        "verbose": False,
        "temperature": 0.3,
        "timeout": 30
    }

"""
Pytest configuration and fixtures for Week 06 tests.

This module provides common fixtures for testing Multi-Agent Systems including:
- Planner-Executor pattern
- Agent communication
- Agentic RAG
- Human-in-the-Loop mechanisms
"""

import pytest
from unittest.mock import MagicMock, Mock
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from collections import Counter
import json
from enum import Enum


# =============================================================================
# Mock Classes for Testing Multi-Agent Systems
# =============================================================================

class AgentRole(Enum):
    """Agent roles in multi-agent system."""
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    RETRIEVER = "retriever"


class MessageStatus(Enum):
    """Message status in agent communication."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentMessage:
    """Message passed between agents."""
    sender: str
    receiver: str
    content: Dict
    message_id: str = "msg_1"
    status: MessageStatus = MessageStatus.PENDING
    timestamp: float = 0

    def __post_init__(self):
        if self.timestamp == 0:
            import time
            self.timestamp = time.time()


@dataclass
class SubTask:
    """A subtask in a plan."""
    step: int
    action: str
    tool: str
    params: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """A plan created by the Planner agent."""
    task_understanding: str
    subtasks: List[SubTask]
    expected_output: str
    plan_id: str = "plan_1"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "task_understanding": self.task_understanding,
            "subtasks": [
                {
                    "step": st.step,
                    "action": st.action,
                    "tool": st.tool,
                    "params": st.params,
                    "dependencies": st.dependencies
                }
                for st in self.subtasks
            ],
            "expected_output": self.expected_output,
            "plan_id": self.plan_id
        }


@dataclass
class ExecutionResult:
    """Result of executing a plan."""
    plan: ExecutionPlan
    results: List[Dict]
    status: str = "completed"
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "plan": self.plan.to_dict(),
            "results": self.results,
            "status": self.status,
            "errors": self.errors
        }


@dataclass
class ReviewReport:
    """Review report from the Reviewer agent."""
    status: str  # approved/needs_revision
    issues: List[str] = field(default_factory=list)
    final_answer: str = ""
    revision_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "issues": self.issues,
            "final_answer": self.final_answer,
            "revision_suggestions": self.revision_suggestions
        }


@dataclass
class RetrievalStrategy:
    """Retrieval strategy decision."""
    method: str  # vector/hybrid/multi_round
    top_k: int = 5
    reasoning: str = ""
    improved_query: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "method": self.method,
            "top_k": self.top_k,
            "reasoning": self.reasoning,
            "improved_query": self.improved_query
        }


@dataclass
class RetrievalResult:
    """Result from retrieval agent."""
    query: str
    results: List[Dict]
    strategy: RetrievalStrategy
    assessment: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": self.results,
            "strategy": self.strategy.to_dict(),
            "assessment": self.assessment
        }


class TextAnalyzerTools:
    """Text analysis tools for testing."""

    POSITIVE_WORDS = ["好", "优秀", "满意", "喜欢", "棒", "推荐", "不错"]
    NEGATIVE_WORDS = ["差", "慢", "糟糕", "不满", "差劲", "坏", "问题"]

    @staticmethod
    def analyze_sentiment(text: str) -> Dict:
        """Analyze text sentiment (simplified implementation)."""
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
        """Extract keywords from text."""
        if not text or not text.strip():
            return {"keywords": [], "counts": []}

        import re
        words = re.findall(r'[\w]{2,}', text)
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
        """Count word frequency in text."""
        if not text or not text.strip():
            return {"top_words": []}

        import re
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)
        stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "也", "都"}
        filtered = [w for w in words if w not in stopwords]

        if not filtered:
            return {"top_words": []}

        counter = Counter(filtered)
        top_words = counter.most_common(top_k)

        return {
            "top_words": [{"word": w, "count": c} for w, c in top_words]
        }


class MockVectorStore:
    """Mock vector store for testing."""

    def __init__(self):
        self.documents = [
            {"id": "doc1", "text": "产品质量很好，非常满意", "score": 0.95},
            {"id": "doc2", "text": "物流太慢了，客服态度差", "score": 0.88},
            {"id": "doc3", "text": "价格合理，物流也快", "score": 0.82},
            {"id": "doc4", "text": "用了两周就坏了，质量堪忧", "score": 0.79},
        ]

    def search(self, query: str, top_k: int = 5) -> Dict:
        """Mock search."""
        results = self.documents[:top_k]
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }


class MockKeywordIndex:
    """Mock keyword index for testing."""

    def __init__(self):
        self.index = {
            "质量": ["doc1", "doc4"],
            "物流": ["doc2", "doc3"],
            "客服": ["doc2"],
            "价格": ["doc3"]
        }

    def search(self, query: str, top_k: int = 5) -> Dict:
        """Mock keyword search."""
        results = []
        for term, docs in self.index.items():
            if term in query:
                for doc_id in docs:
                    results.append({"id": doc_id, "term": term})
        return {
            "query": query,
            "results": results[:top_k],
            "total": len(results)
        }


class MockLLMClient:
    """Mock LLM client for testing Agent behavior."""

    def __init__(
        self,
        responses: Dict[str, Any] = None,
        predefined_plans: List[Dict] = None
    ):
        """Initialize mock client."""
        self.responses = responses or {}
        self.predefined_plans = predefined_plans or []
        self.call_count = 0
        self.message_history = []
        self.plan_index = 0

    def chat(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> Dict:
        """Simulate chat completion."""
        self.call_count += 1
        self.message_history.append(messages)

        last_msg = messages[-1].get("content", "") if messages else ""

        # Check for predefined responses
        for key, response in self.responses.items():
            if key in last_msg:
                if isinstance(response, str):
                    return {"content": response, "tool_calls": None}
                return response

        # Check if this is a planning request
        if "计划" in last_msg or "plan" in last_msg.lower():
            if self.plan_index < len(self.predefined_plans):
                plan = self.predefined_plans[self.plan_index]
                self.plan_index += 1
                return {"content": json.dumps(plan, ensure_ascii=False), "tool_calls": None}

        # Default response
        return {"content": "这是一个测试回复。", "tool_calls": None}

    def reset(self):
        """Reset call count and history."""
        self.call_count = 0
        self.message_history = []
        self.plan_index = 0


class PlannerAgent:
    """Planner Agent for testing."""

    def __init__(self, llm_client: MockLLMClient = None):
        """Initialize Planner Agent."""
        self.llm = llm_client or MockLLMClient()
        self.role = AgentRole.PLANNER
        self.last_plan = None

    def create_plan(self, task: str, context: Dict = None) -> ExecutionPlan:
        """Create task plan."""
        # Simplified planning logic
        if "分析" in task and "情感" in task:
            subtasks = [
                SubTask(step=1, action="加载文本", tool="load_text", params={}),
                SubTask(step=2, action="分析情感", tool="analyze_sentiment", params={}),
                SubTask(step=3, action="汇总结果", tool="summarize", params={})
            ]
        elif "关键词" in task or "词频" in task:
            subtasks = [
                SubTask(step=1, action="加载文本", tool="load_text", params={}),
                SubTask(step=2, action="提取关键词", tool="extract_keywords", params={}),
                SubTask(step=3, action="返回结果", tool="output", params={})
            ]
        else:
            subtasks = [
                SubTask(step=1, action="理解任务", tool="analyze", params={"task": task[:20]}),
                SubTask(step=2, action="执行分析", tool="execute", params={}),
                SubTask(step=3, action="生成答案", tool="answer", params={})
            ]

        plan = ExecutionPlan(
            task_understanding=f"理解任务: {task[:30]}...",
            subtasks=subtasks,
            expected_output="分析结果"
        )
        self.last_plan = plan
        return plan

    def revise_plan(self, original_plan: ExecutionPlan, feedback: str) -> ExecutionPlan:
        """Revise plan based on feedback."""
        revised_subtasks = original_plan.subtasks.copy()
        # Add a revision step
        revised_subtasks.append(
            SubTask(
                step=len(revised_subtasks) + 1,
                action="修订计划",
                tool="revise",
                params={"feedback": feedback}
            )
        )

        return ExecutionPlan(
            task_understanding=f"{original_plan.task_understanding} (已修订)",
            subtasks=revised_subtasks,
            expected_output=original_plan.expected_output
        )


class ExecutorAgent:
    """Executor Agent for testing."""

    def __init__(self, tools: Dict[str, Callable] = None):
        """Initialize Executor Agent."""
        self.tools = tools or {}
        self.role = AgentRole.EXECUTOR
        self.execution_history = []

    def execute_plan(self, plan: ExecutionPlan, retriever=None) -> ExecutionResult:
        """Execute plan."""
        results = []
        errors = []

        for subtask in plan.subtasks:
            tool_name = subtask.tool
            params = subtask.params

            # Handle retrieval
            if tool_name == "retrieve_documents" and retriever:
                result = retriever.retrieve(params.get("query", ""))
            elif tool_name in self.tools:
                try:
                    result = self.tools[tool_name](**params)
                except Exception as e:
                    result = {"error": str(e)}
                    errors.append(f"Tool {tool_name} failed: {e}")
            else:
                # Mock unknown tools
                result = {"tool": tool_name, "params": params, "status": "mocked"}

            results.append({
                "step": subtask.step,
                "action": subtask.action,
                "tool": tool_name,
                "result": result
            })

            # Record history
            self.execution_history.append({
                "subtask": subtask,
                "result": result
            })

        status = "completed" if not errors else "completed_with_errors"

        return ExecutionResult(
            plan=plan,
            results=results,
            status=status,
            errors=errors
        )


class ReviewerAgent:
    """Reviewer Agent for testing."""

    def __init__(self, llm_client: MockLLMClient = None):
        """Initialize Reviewer Agent."""
        self.llm = llm_client or MockLLMClient()
        self.role = AgentRole.REVIEWER
        self.review_history = []

    def review_result(self, plan: ExecutionPlan, execution_result: ExecutionResult) -> ReviewReport:
        """Review execution result."""
        errors = execution_result.errors

        if errors:
            return ReviewReport(
                status="needs_revision",
                issues=errors,
                revision_suggestions=["修复工具执行错误"]
            )

        # Check if results are complete
        if not execution_result.results:
            return ReviewReport(
                status="needs_revision",
                issues=["执行结果为空"],
                revision_suggestions=["检查执行流程"]
            )

        # Approved
        self.review_history.append({
            "plan": plan,
            "result": execution_result,
            "status": "approved"
        })

        return ReviewReport(
            status="approved",
            issues=[],
            final_answer=f"任务完成，执行了{len(execution_result.results)}个步骤"
        )


class RetrieverAgent:
    """Retriever Agent for testing."""

    def __init__(
        self,
        llm_client: MockLLMClient = None,
        vector_store=None,
        keyword_index=None
    ):
        """Initialize Retriever Agent."""
        self.llm = llm_client or MockLLMClient()
        self.vector_store = vector_store or MockVectorStore()
        self.keyword_index = keyword_index or MockKeywordIndex()
        self.role = AgentRole.RETRIEVER
        self.retrieval_history = []

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Autonomous retrieval."""
        # Decide strategy with custom top_k
        strategy = self._decide_strategy(query, top_k)

        # Execute retrieval
        if strategy.method == "vector":
            results = self.vector_store.search(query, top_k=top_k)
        elif strategy.method == "hybrid":
            results = self._hybrid_search(query, top_k)
        else:
            results = self.vector_store.search(query, top_k=top_k)

        # Assess results
        assessment = self._assess_results(query, results)

        retrieval_result = RetrievalResult(
            query=query,
            results=results.get("results", []),
            strategy=strategy,
            assessment=assessment
        )

        self.retrieval_history.append(retrieval_result)
        return retrieval_result

    def _decide_strategy(self, query: str, top_k: int = 5) -> RetrievalStrategy:
        """Decide retrieval strategy."""
        # Simple logic: use hybrid for longer queries
        if len(query) > 10:
            return RetrievalStrategy(
                method="hybrid",
                top_k=top_k,
                reasoning="查询较长，使用混合检索"
            )
        return RetrievalStrategy(
            method="vector",
            top_k=top_k,
            reasoning="简单查询，使用向量检索"
        )

    def _hybrid_search(self, query: str, top_k: int) -> Dict:
        """Hybrid search."""
        vector_results = self.vector_store.search(query, top_k=top_k * 2)
        keyword_results = self.keyword_index.search(query, top_k=top_k * 2)
        # Simplified RRF fusion
        return {
            "query": query,
            "results": vector_results.get("results", [])[:top_k],
            "method": "hybrid"
        }

    def _assess_results(self, query: str, results: Dict) -> Dict:
        """Assess retrieval results."""
        if results is None:
            return {
                "sufficient": False,
                "confidence": 0.0,
                "result_count": 0
            }
        result_count = len(results.get("results", []))
        return {
            "sufficient": result_count > 0,
            "confidence": min(0.5 + result_count * 0.1, 1.0),
            "result_count": result_count
        }


class MessageBus:
    """Message bus for agent communication."""

    def __init__(self):
        """Initialize message bus."""
        self.messages = []
        self.message_queue = {}

    def send(self, message: AgentMessage) -> bool:
        """Send message."""
        message.status = MessageStatus.DELIVERED
        self.messages.append(message)
        return True

    def receive(self, receiver: str) -> List[AgentMessage]:
        """Receive messages for agent."""
        return [m for m in self.messages if m.receiver == receiver and m.status == MessageStatus.DELIVERED]

    def get_status(self, message_id: str) -> MessageStatus:
        """Get message status."""
        for msg in self.messages:
            if msg.message_id == message_id:
                return msg.status
        return MessageStatus.FAILED


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_tools():
    """Fixture providing sample tools."""
    return {
        "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
        "extract_keywords": TextAnalyzerTools.extract_keywords,
        "count_word_freq": TextAnalyzerTools.count_word_freq,
    }


@pytest.fixture
def mock_llm_client():
    """Fixture providing MockLLMClient."""
    return MockLLMClient()


@pytest.fixture
def planner_agent(mock_llm_client):
    """Fixture providing PlannerAgent."""
    return PlannerAgent(llm_client=mock_llm_client)


@pytest.fixture
def executor_agent(sample_tools):
    """Fixture providing ExecutorAgent."""
    return ExecutorAgent(tools=sample_tools)


@pytest.fixture
def reviewer_agent(mock_llm_client):
    """Fixture providing ReviewerAgent."""
    return ReviewerAgent(llm_client=mock_llm_client)


@pytest.fixture
def retriever_agent(mock_llm_client):
    """Fixture providing RetrieverAgent."""
    return RetrieverAgent(
        llm_client=mock_llm_client,
        vector_store=MockVectorStore(),
        keyword_index=MockKeywordIndex()
    )


@pytest.fixture
def message_bus():
    """Fixture providing MessageBus."""
    return MessageBus()


@pytest.fixture
def sample_tasks():
    """Fixture providing sample tasks."""
    return {
        "sentiment_analysis": "分析客户反馈的情感倾向",
        "keyword_extraction": "从文本中提取关键词",
        "complex_task": "分析反馈的情感、提取关键词、统计词频",
        "empty_task": "",
        "very_long_task": "分析" * 100 + "的情感",
    }


@pytest.fixture
def sample_queries():
    """Fixture providing sample queries for retrieval."""
    return {
        "simple": "产品质量",
        "complex": "产品质量和物流速度",
        "empty": "",
        "specific": "订单号12345的物流状态",
    }


@pytest.fixture
def sample_plans():
    """Fixture providing sample execution plans."""
    return {
        "simple_plan": ExecutionPlan(
            task_understanding="分析情感",
            subtasks=[
                SubTask(step=1, action="加载", tool="load", params={}),
                SubTask(step=2, action="分析", tool="analyze", params={})
            ],
            expected_output="情感分析结果"
        ),
        "empty_plan": ExecutionPlan(
            task_understanding="",
            subtasks=[],
            expected_output=""
        ),
        "complex_plan": ExecutionPlan(
            task_understanding="复杂任务分析",
            subtasks=[
                SubTask(step=i, action=f"步骤{i}", tool=f"tool_{i}", params={"idx": i})
                for i in range(1, 6)
            ],
            expected_output="完整分析结果"
        )
    }


@pytest.fixture
def agent_workflow(planner_agent, executor_agent, reviewer_agent, retriever_agent):
    """Fixture providing a complete multi-agent workflow."""
    return {
        "planner": planner_agent,
        "executor": executor_agent,
        "reviewer": reviewer_agent,
        "retriever": retriever_agent
    }


@pytest.fixture
def human_review_options():
    """Fixture providing human review options."""
    return {
        "approve": "y",
        "reject": "n",
        "feedback": "需要更详细的分析",
        "timeout": None,
    }

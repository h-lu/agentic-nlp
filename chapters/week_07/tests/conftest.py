"""
Pytest configuration and fixtures for Week 07 tests.

This module provides common fixtures for testing production-ready LLM applications including:
- Cost tracking and optimization
- LLM evaluation systems
- FastAPI deployment
- Observability (logging, metrics, tracing)
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
import json
import time
from enum import Enum
import sys
import os


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Ensure this conftest.py's classes are available during collection."""
    # Add this directory to sys.path if not already there
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)


# =============================================================================
# Data Classes for Production Testing
# =============================================================================

@dataclass
class LLMMetrics:
    """LLM call metrics for cost tracking."""
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    timestamp: datetime
    agent_name: Optional[str] = None


@dataclass
class TestCase:
    """Test case for evaluation."""
    query: str
    expected: str
    context: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class EvalResult:
    """Evaluation result."""
    query: str
    expected: str
    actual: str
    faithfulness: float
    relevancy: float
    metadata: Dict = field(default_factory=dict)


class ModelTier(str, Enum):
    """Model pricing tier."""
    PREMIUM = "gpt-4o"
    STANDARD = "gpt-4o-mini"
    BASIC = "gpt-3.5-turbo"


# =============================================================================
# Mock Implementations
# =============================================================================

class MockCostTracker:
    """Mock cost tracker for testing."""

    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self):
        self.calls: List[LLMMetrics] = []

    def record_call(self, metrics: LLMMetrics):
        """Record an LLM call."""
        self.calls.append(metrics)

    def calculate_cost(self, metrics: LLMMetrics) -> float:
        """Calculate cost for a single call."""
        pricing = self.PRICING.get(metrics.model, {})
        input_cost = metrics.input_tokens * pricing.get("input", 0) / 1_000_000
        output_cost = metrics.output_tokens * pricing.get("output", 0) / 1_000_000
        return input_cost + output_cost

    def get_summary(self) -> Dict:
        """Get cost summary."""
        if not self.calls:
            return {
                "total_calls": 0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "cost_by_agent": {},
                "avg_latency_ms": 0
            }

        total_cost = sum(self.calculate_cost(m) for m in self.calls)
        total_tokens = sum(m.input_tokens + m.output_tokens for m in self.calls)

        by_agent = {}
        for m in self.calls:
            agent = m.agent_name or "unknown"
            if agent not in by_agent:
                by_agent[agent] = {"calls": 0, "cost": 0}
            by_agent[agent]["calls"] += 1
            by_agent[agent]["cost"] += self.calculate_cost(m)

        return {
            "total_calls": len(self.calls),
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "cost_by_agent": by_agent,
            "avg_latency_ms": sum(m.latency_ms for m in self.calls) / len(self.calls)
        }

    def reset(self):
        """Reset tracking."""
        self.calls.clear()


class MockLLMEvaluator:
    """Mock LLM evaluator for testing."""

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.evaluation_history = []

    def evaluate_single(self, test_case: TestCase) -> EvalResult:
        """Evaluate a single test case."""
        # Mock evaluation logic
        faithfulness = 0.85 if "相关" in test_case.expected or test_case.expected in test_case.context else 0.65
        relevancy = 0.9 if test_case.query in test_case.expected else 0.7

        result = EvalResult(
            query=test_case.query,
            expected=test_case.expected,
            actual=test_case.expected,  # Mock: assume actual matches expected
            faithfulness=faithfulness,
            relevancy=relevancy,
            metadata=getattr(test_case, 'metadata', {})
        )
        self.evaluation_history.append(result)
        return result

    def evaluate_batch(self, test_cases: List[TestCase]) -> Dict:
        """Evaluate a batch of test cases."""
        results = []
        for case in test_cases:
            result = self.evaluate_single(case)
            results.append({
                "query": result.query,
                "expected": result.expected,
                "actual": result.actual,
                "faithfulness": result.faithfulness,
                "relevancy": result.relevancy
            })

        return {
            "num_cases": len(results),
            "avg_faithfulness": sum(r["faithfulness"] for r in results) / len(results) if results else 0,
            "avg_relevancy": sum(r["relevancy"] for r in results) / len(results) if results else 0,
            "details": results
        }


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.message_history = []

    def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """Simulate chat completion."""
        self.call_count += 1
        self.message_history.append(messages)

        last_msg = messages[-1].get("content", "") if messages else ""

        # Check for predefined responses
        for key, response in self.responses.items():
            if key in last_msg:
                if isinstance(response, str):
                    return {
                        "content": response,
                        "usage": {"prompt_tokens": 100, "completion_tokens": 50}
                    }
                return response

        # Default response
        return {
            "content": "这是一个测试回复。",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }

    def reset(self):
        """Reset call count and history."""
        self.call_count = 0
        self.message_history.clear()


class MockModelSelector:
    """Mock model selector for cost optimization."""

    AGENT_MODELS = {
        "planner": "gpt-4o",
        "executor": "gpt-4o-mini",
        "reviewer": "gpt-4o",
        "retriever": "gpt-4o-mini"
    }

    def get_model_for_agent(self, agent_name: str) -> str:
        """Get the optimal model for an agent."""
        return self.AGENT_MODELS.get(agent_name, "gpt-4o-mini")


class MockPromptOptimizer:
    """Mock prompt optimizer for testing."""

    CORE_PROMPTS = {
        "planner": "分析任务并制定执行计划。",
        "executor": "执行工具调用。",
        "reviewer": "审核执行结果。",
    }

    def get_prompt(self, agent: str, use_extensions: bool = False) -> str:
        """Get optimized prompt."""
        prompt = self.CORE_PROMPTS.get(agent, "执行任务。")
        if use_extensions:
            prompt += "\n\n注意：确保结果准确完整。"
        return prompt

    def estimate_token_savings(self, agent: str) -> int:
        """Estimate token savings from optimization."""
        return 50 if agent in self.CORE_PROMPTS else 0


class MockSemanticCache:
    """Mock semantic cache for testing."""

    def __init__(self, hit_rate: float = 0.3):
        self.cache: Dict[str, str] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.hit_rate = hit_rate

    def get(self, query: str) -> Optional[str]:
        """Get cached result."""
        if query in self.cache:
            self.hit_count += 1
            return self.cache[query]

        # Simulate hit rate for testing
        import random
        if random.random() < self.hit_rate:
            self.hit_count += 1
            return f"缓存结果: {query[:20]}..."

        self.miss_count += 1
        return None

    def set(self, query: str, response: str):
        """Store in cache."""
        self.cache[query] = response

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.hit_count + self.miss_count
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": self.hit_count / total if total > 0 else 0,
            "size": len(self.cache)
        }

    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0


class MockStructuredLogger:
    """Mock structured logger for testing."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logs: List[Dict] = []

    def log_llm_call(self, agent: str, model: str, prompt: str, response: str, tokens: Dict, cost: float):
        """Log LLM call."""
        self.logs.append({
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "event": "llm_call",
            "agent": agent,
            "model": model,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "input_tokens": tokens.get("input"),
            "output_tokens": tokens.get("output"),
            "cost_usd": cost
        })

    def log_agent_execution(self, agent: str, action: str, status: str, details: Dict):
        """Log agent execution."""
        self.logs.append({
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "event": "agent_execution",
            "agent": agent,
            "action": action,
            "status": status,
            "details": details
        })

    def get_logs(self, event_type: str = None) -> List[Dict]:
        """Get logs, optionally filtered by event type."""
        if event_type:
            return [log for log in self.logs if log.get("event") == event_type]
        return self.logs.copy()

    def clear(self):
        """Clear logs."""
        self.logs.clear()


class MockMetricsCollector:
    """Mock metrics collector for testing."""

    def __init__(self):
        self.counters: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.gauges: Dict[str, float] = {}

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict = None):
        """Increment a counter."""
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value

    def observe_histogram(self, name: str, value: float, labels: Dict = None):
        """Observe a histogram value."""
        key = self._make_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)

    def set_gauge(self, name: str, value: float, labels: Dict = None):
        """Set a gauge."""
        key = self._make_key(name, labels)
        self.gauges[key] = value

    def get_metrics(self) -> Dict:
        """Get all metrics."""
        return {
            "counters": self.counters.copy(),
            "histograms": self.histograms.copy(),
            "gauges": self.gauges.copy()
        }

    def _make_key(self, name: str, labels: Dict = None) -> str:
        """Make a metric key with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def reset(self):
        """Reset all metrics."""
        self.counters.clear()
        self.histograms.clear()
        self.gauges.clear()


class MockTraceContext:
    """Mock trace context for testing."""

    def __init__(self):
        import uuid
        self.trace_id = str(uuid.uuid4())
        self.spans: List[Dict] = []
        self._current_span = None

    def span(self, name: str, **metadata):
        """Create a span (context manager)."""
        return self._SpanContext(self, name, metadata)

    def add_span(self, span: Dict):
        """Add a completed span."""
        self.spans.append(span)

    def get_trace(self) -> Dict:
        """Get complete trace."""
        return {
            "trace_id": self.trace_id,
            "spans": self.spans,
            "total_duration_ms": sum(s.get("duration_ms", 0) for s in self.spans)
        }

    class _SpanContext:
        """Internal span context manager."""

        def __init__(self, trace_ctx, name: str, metadata: Dict):
            self.trace_ctx = trace_ctx
            self.name = name
            self.metadata = metadata
            self.start_time = None
            self.span_data = None

        def __enter__(self):
            import uuid
            self.start_time = time.time()
            self.span_data = {
                "span_id": str(uuid.uuid4()),
                "name": self.name,
                "start_time": self.start_time,
                "metadata": self.metadata
            }
            return self.span_data

        def __exit__(self, exc_type, exc_val, exc_tb):
            end_time = time.time()
            self.span_data["end_time"] = end_time
            self.span_data["duration_ms"] = int((end_time - self.start_time) * 1000)
            self.trace_ctx.add_span(self.span_data)
            return False


class MockAlertManager:
    """Mock alert manager for testing."""

    def __init__(self):
        self.rules: List[Dict] = []
        self.alerts: List[Dict] = []

    def add_rule(self, name: str, condition: Callable[[Dict], bool], message: str):
        """Add an alert rule."""
        self.rules.append({
            "name": name,
            "condition": condition,
            "message": message
        })

    def check(self, metrics: Dict) -> List[Dict]:
        """Check all rules against metrics."""
        triggered = []
        for rule in self.rules:
            try:
                if rule["condition"](metrics):
                    alert = {
                        "rule": rule["name"],
                        "message": rule["message"],
                        "metrics": metrics,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.alerts.append(alert)
                    triggered.append(alert)
            except Exception as e:
                # Rule evaluation failed
                pass
        return triggered

    def get_alerts(self, rule_name: str = None) -> List[Dict]:
        """Get alerts, optionally filtered by rule name."""
        if rule_name:
            return [a for a in self.alerts if a.get("rule") == rule_name]
        return self.alerts.copy()

    def clear_alerts(self):
        """Clear alert history."""
        self.alerts.clear()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_cost_tracker():
    """Fixture providing MockCostTracker."""
    return MockCostTracker()


@pytest.fixture
def mock_llm_evaluator():
    """Fixture providing MockLLMEvaluator."""
    return MockLLMEvaluator()


@pytest.fixture
def mock_llm_client():
    """Fixture providing MockLLMClient."""
    return MockLLMClient()


@pytest.fixture
def mock_model_selector():
    """Fixture providing MockModelSelector."""
    return MockModelSelector()


@pytest.fixture
def mock_prompt_optimizer():
    """Fixture providing MockPromptOptimizer."""
    return MockPromptOptimizer()


@pytest.fixture
def mock_semantic_cache():
    """Fixture providing MockSemanticCache."""
    return MockSemanticCache(hit_rate=0.3)


@pytest.fixture
def mock_structured_logger():
    """Fixture providing MockStructuredLogger."""
    return MockStructuredLogger("test_service")


@pytest.fixture
def mock_metrics_collector():
    """Fixture providing MockMetricsCollector."""
    return MockMetricsCollector()


@pytest.fixture
def mock_trace_context():
    """Fixture providing MockTraceContext."""
    return MockTraceContext()


@pytest.fixture
def mock_alert_manager():
    """Fixture providing MockAlertManager."""
    return MockAlertManager()


@pytest.fixture
def sample_llm_metrics():
    """Fixture providing sample LLM metrics."""
    return [
        LLMMetrics(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500,
            timestamp=datetime.now(),
            agent_name="planner"
        ),
        LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=500,
            output_tokens=300,
            latency_ms=800,
            timestamp=datetime.now(),
            agent_name="executor"
        ),
        LLMMetrics(
            model="gpt-4o",
            input_tokens=800,
            output_tokens=200,
            latency_ms=1200,
            timestamp=datetime.now(),
            agent_name="reviewer"
        ),
    ]


@pytest.fixture
def sample_test_cases():
    """Fixture providing sample test cases for evaluation."""
    return [
        TestCase(
            query="产品质量怎么样？",
            expected="产品质量很好，客户满意度高",
            context="根据客户反馈分析，产品质量评分4.5/5"
        ),
        TestCase(
            query="物流速度快吗？",
            expected="物流速度一般，有客户投诉配送慢",
            context="物流平均配送时间3-5天，部分区域需要更长时间"
        ),
        TestCase(
            query="",
            expected="",
            context=""
        ),
    ]


@pytest.fixture
def sample_api_requests():
    """Fixture providing sample API requests."""
    return {
        "valid_request": {
            "task": "分析客户反馈的情感倾向",
            "enable_review": True,
            "use_cache": True
        },
        "minimal_request": {
            "task": "简单分析"
        },
        "invalid_request": {
            "task": "",  # Empty task
            "enable_review": "invalid",  # Wrong type
        },
        "long_task_request": {
            "task": "这是一个非常长的任务描述" * 100,
            "enable_review": False
        }
    }


@pytest.fixture
def sample_pricing():
    """Fixture providing sample pricing data."""
    return {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }


@pytest.fixture
def sample_alert_rules():
    """Fixture providing sample alert rules."""
    return [
        {
            "name": "high_cost",
            "condition": lambda m: m.get("hourly_cost_usd", 0) > 10,
            "message": "每小时成本超过 $10"
        },
        {
            "name": "high_latency",
            "condition": lambda m: m.get("p95_latency_ms", 0) > 5000,
            "message": "P95 延迟超过 5 秒"
        },
        {
            "name": "high_error_rate",
            "condition": lambda m: m.get("error_rate", 0) > 0.05,
            "message": "错误率超过 5%"
        }
    ]


@pytest.fixture
def agent_config():
    """Fixture providing agent configuration."""
    return {
        "planner": {
            "model": "gpt-4o",
            "temperature": 0.3,
            "max_tokens": 1000
        },
        "executor": {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 500
        },
        "reviewer": {
            "model": "gpt-4o",
            "temperature": 0.2,
            "max_tokens": 800
        }
    }


@pytest.fixture
def production_metrics():
    """Fixture providing sample production metrics."""
    return {
        "hourly_cost_usd": 15.50,
        "p95_latency_ms": 6200,
        "error_rate": 0.03,
        "total_requests": 1000,
        "avg_tokens_per_request": 1500
    }


@pytest.fixture
def healthy_metrics():
    """Fixture providing healthy metrics (no alerts)."""
    return {
        "hourly_cost_usd": 5.00,
        "p95_latency_ms": 2000,
        "error_rate": 0.01,
        "total_requests": 500,
        "avg_tokens_per_request": 800
    }

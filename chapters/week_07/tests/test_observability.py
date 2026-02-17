"""
Tests for Observability - Week 07

Tests the observability functionality including:
- Structured logging
- Metrics collection
- Distributed tracing
- Alert management
- Edge cases
"""

import pytest
import time
from datetime import datetime
from decimal import Decimal
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
MockStructuredLogger = week07_conftest.MockStructuredLogger
MockMetricsCollector = week07_conftest.MockMetricsCollector
MockTraceContext = week07_conftest.MockTraceContext
MockAlertManager = week07_conftest.MockAlertManager


class TestStructuredLogging:
    """Test structured logging functionality."""

    def test_logger_initialization(self, mock_structured_logger):
        """Test that logger initializes correctly."""
        assert mock_structured_logger is not None
        assert mock_structured_logger.service_name == "test_service"
        assert mock_structured_logger.logs == []

    def test_log_llm_call(self, mock_structured_logger):
        """Test logging an LLM call."""
        mock_structured_logger.log_llm_call(
            agent="planner",
            model="gpt-4o",
            prompt="分析任务",
            response="计划已生成",
            tokens={"input": 1000, "output": 500},
            cost=0.0075
        )

        logs = mock_structured_logger.get_logs()
        assert len(logs) == 1
        assert logs[0]["event"] == "llm_call"
        assert logs[0]["agent"] == "planner"
        assert logs[0]["model"] == "gpt-4o"

    def test_log_agent_execution(self, mock_structured_logger):
        """Test logging agent execution."""
        mock_structured_logger.log_agent_execution(
            agent="executor",
            action="analyze_sentiment",
            status="success",
            details={"result": "positive"}
        )

        logs = mock_structured_logger.get_logs()
        assert len(logs) == 1
        assert logs[0]["event"] == "agent_execution"
        assert logs[0]["agent"] == "executor"
        assert logs[0]["status"] == "success"

    def test_multiple_logs(self, mock_structured_logger):
        """Test logging multiple events."""
        mock_structured_logger.log_llm_call(
            agent="planner",
            model="gpt-4o",
            prompt="任务",
            response="结果",
            tokens={"input": 100, "output": 50},
            cost=0.001
        )

        mock_structured_logger.log_agent_execution(
            agent="executor",
            action="execute",
            status="success",
            details={}
        )

        logs = mock_structured_logger.get_logs()
        assert len(logs) == 2

    def test_filter_logs_by_event_type(self, mock_structured_logger):
        """Test filtering logs by event type."""
        mock_structured_logger.log_llm_call(
            agent="planner",
            model="gpt-4o",
            prompt="任务",
            response="结果",
            tokens={"input": 100, "output": 50},
            cost=0.001
        )

        mock_structured_logger.log_agent_execution(
            agent="executor",
            action="execute",
            status="success",
            details={}
        )

        llm_logs = mock_structured_logger.get_logs("llm_call")
        execution_logs = mock_structured_logger.get_logs("agent_execution")

        assert len(llm_logs) == 1
        assert len(execution_logs) == 1

    def test_log_structure_completeness(self, mock_structured_logger):
        """Test that logs have complete structure."""
        mock_structured_logger.log_llm_call(
            agent="test",
            model="gpt-4o-mini",
            prompt="测试",
            response="响应",
            tokens={"input": 500, "output": 200},
            cost=0.0005
        )

        log = mock_structured_logger.get_logs()[0]

        required_fields = ["service", "timestamp", "event", "agent", "model",
                          "prompt_length", "response_length", "cost_usd"]
        for field in required_fields:
            assert field in log

    def test_clear_logs(self, mock_structured_logger):
        """Test clearing logs."""
        mock_structured_logger.log_llm_call(
            agent="test",
            model="gpt-4o",
            prompt="任务",
            response="结果",
            tokens={"input": 100, "output": 50},
            cost=0.001
        )

        assert len(mock_structured_logger.get_logs()) == 1

        mock_structured_logger.clear()

        assert len(mock_structured_logger.get_logs()) == 0


class TestMetricsCollection:
    """Test metrics collection functionality."""

    def test_metrics_collector_initialization(self, mock_metrics_collector):
        """Test that metrics collector initializes correctly."""
        assert mock_metrics_collector is not None
        assert mock_metrics_collector.counters == {}
        assert mock_metrics_collector.histograms == {}
        assert mock_metrics_collector.gauges == {}

    def test_increment_counter(self, mock_metrics_collector):
        """Test incrementing a counter."""
        mock_metrics_collector.increment_counter("requests_total", 1.0)

        metrics = mock_metrics_collector.get_metrics()
        assert metrics["counters"]["requests_total"] == 1.0

    def test_counter_with_labels(self, mock_metrics_collector):
        """Test counter with labels."""
        mock_metrics_collector.increment_counter(
            "requests_total",
            1.0,
            labels={"endpoint": "/analyze", "status": "success"}
        )

        metrics = mock_metrics_collector.get_metrics()
        # Key should include labels
        assert any("endpoint=/analyze" in k for k in metrics["counters"].keys())

    def test_counter_multiple_increments(self, mock_metrics_collector):
        """Test counter increments accumulate."""
        mock_metrics_collector.increment_counter("requests_total", 1.0)
        mock_metrics_collector.increment_counter("requests_total", 2.0)
        mock_metrics_collector.increment_counter("requests_total", 3.0)

        metrics = mock_metrics_collector.get_metrics()
        assert metrics["counters"]["requests_total"] == 6.0

    def test_observe_histogram(self, mock_metrics_collector):
        """Test observing histogram values."""
        mock_metrics_collector.observe_histogram("request_duration_ms", 100)
        mock_metrics_collector.observe_histogram("request_duration_ms", 200)
        mock_metrics_collector.observe_histogram("request_duration_ms", 150)

        metrics = mock_metrics_collector.get_metrics()
        assert "request_duration_ms" in metrics["histograms"]
        assert len(metrics["histograms"]["request_duration_ms"]) == 3
        assert 100 in metrics["histograms"]["request_duration_ms"]

    def test_set_gauge(self, mock_metrics_collector):
        """Test setting a gauge value."""
        mock_metrics_collector.set_gauge("active_requests", 5)

        metrics = mock_metrics_collector.get_metrics()
        assert metrics["gauges"]["active_requests"] == 5

    def test_gauge_overwrites_value(self, mock_metrics_collector):
        """Test that gauge overwrites previous value."""
        mock_metrics_collector.set_gauge("memory_usage_mb", 100)
        mock_metrics_collector.set_gauge("memory_usage_mb", 200)

        metrics = mock_metrics_collector.get_metrics()
        assert metrics["gauges"]["memory_usage_mb"] == 200

    def test_reset_metrics(self, mock_metrics_collector):
        """Test resetting all metrics."""
        mock_metrics_collector.increment_counter("test", 1)
        mock_metrics_collector.observe_histogram("test_hist", 100)
        mock_metrics_collector.set_gauge("test_gauge", 5)

        assert len(mock_metrics_collector.get_metrics()["counters"]) > 0

        mock_metrics_collector.reset()

        assert mock_metrics_collector.counters == {}
        assert mock_metrics_collector.histograms == {}
        assert mock_metrics_collector.gauges == {}

    def test_cost_metric_tracking(self, mock_metrics_collector):
        """Test tracking cost as a counter metric."""
        mock_metrics_collector.increment_counter(
            "llm_cost_usd_total",
            0.015,
            labels={"model": "gpt-4o", "agent": "planner"}
        )

        metrics = mock_metrics_collector.get_metrics()
        assert metrics["counters"]["llm_cost_usd_total{agent=planner,model=gpt-4o}"] == 0.015


class TestDistributedTracing:
    """Test distributed tracing functionality."""

    def test_trace_context_initialization(self, mock_trace_context):
        """Test that trace context initializes correctly."""
        assert mock_trace_context is not None
        assert mock_trace_context.trace_id is not None
        assert len(mock_trace_context.trace_id) > 0
        assert mock_trace_context.spans == []

    def test_create_span(self, mock_trace_context):
        """Test creating a span."""
        with mock_trace_context.span("test_operation", key="value") as span:
            assert span is not None
            assert span["name"] == "test_operation"
            assert span["metadata"]["key"] == "value"

    def test_span_recording(self, mock_trace_context):
        """Test that span is recorded after completion."""
        with mock_trace_context.span("operation"):
            pass  # Empty span

        trace = mock_trace_context.get_trace()
        assert len(trace["spans"]) == 1

    def test_span_duration_calculation(self, mock_trace_context):
        """Test that span duration is calculated correctly."""
        with mock_trace_context.span("operation"):
            time.sleep(0.01)  # 10ms

        trace = mock_trace_context.get_trace()
        span = trace["spans"][0]

        assert span["duration_ms"] >= 10  # At least 10ms
        assert "start_time" in span
        assert "end_time" in span

    def test_multiple_spans(self, mock_trace_context):
        """Test creating multiple spans in a trace."""
        with mock_trace_context.span("operation1"):
            pass

        with mock_trace_context.span("operation2"):
            pass

        with mock_trace_context.span("operation3"):
            pass

        trace = mock_trace_context.get_trace()
        assert len(trace["spans"]) == 3

    def test_nested_spans(self, mock_trace_context):
        """Test nested spans (simulated by sequential creation)."""
        with mock_trace_context.span("parent"):
            time.sleep(0.005)
        with mock_trace_context.span("child"):
            time.sleep(0.005)

        trace = mock_trace_context.get_trace()
        assert len(trace["spans"]) == 2

    def test_trace_total_duration(self, mock_trace_context):
        """Test that trace total duration is calculated correctly."""
        with mock_trace_context.span("op1"):
            time.sleep(0.01)
        with mock_trace_context.span("op2"):
            time.sleep(0.015)

        trace = mock_trace_context.get_trace()

        assert trace["total_duration_ms"] >= 25  # At least 25ms

    def test_span_metadata(self, mock_trace_context):
        """Test that span metadata is recorded."""
        with mock_trace_context.span(
            "llm_call",
            agent="planner",
            model="gpt-4o",
            tokens=1500
        ):
            pass

        trace = mock_trace_context.get_trace()
        span = trace["spans"][0]

        assert span["metadata"]["agent"] == "planner"
        assert span["metadata"]["model"] == "gpt-4o"
        assert span["metadata"]["tokens"] == 1500

    def test_trace_id_consistency(self, mock_trace_context):
        """Test that trace_id is consistent across the trace."""
        trace_id_1 = mock_trace_context.trace_id

        with mock_trace_context.span("operation"):
            pass

        trace = mock_trace_context.get_trace()

        assert trace["trace_id"] == trace_id_1
        assert trace["trace_id"] == mock_trace_context.trace_id


class TestAlertManagement:
    """Test alert management functionality."""

    def test_alert_manager_initialization(self, mock_alert_manager):
        """Test that alert manager initializes correctly."""
        assert mock_alert_manager is not None
        assert mock_alert_manager.rules == []
        assert mock_alert_manager.alerts == []

    def test_add_alert_rule(self, mock_alert_manager):
        """Test adding an alert rule."""
        mock_alert_manager.add_rule(
            name="test_rule",
            condition=lambda m: m.get("test_value", 0) > 10,
            message="Test value exceeded"
        )

        assert len(mock_alert_manager.rules) == 1
        assert mock_alert_manager.rules[0]["name"] == "test_rule"

    def test_alert_triggered(self, mock_alert_manager):
        """Test that alert is triggered when condition is met."""
        mock_alert_manager.add_rule(
            name="high_cost",
            condition=lambda m: m.get("cost", 0) > 10,
            message="Cost too high"
        )

        triggered = mock_alert_manager.check({"cost": 15})

        assert len(triggered) == 1
        assert triggered[0]["rule"] == "high_cost"

    def test_alert_not_triggered(self, mock_alert_manager):
        """Test that alert is not triggered when condition is not met."""
        mock_alert_manager.add_rule(
            name="high_cost",
            condition=lambda m: m.get("cost", 0) > 10,
            message="Cost too high"
        )

        triggered = mock_alert_manager.check({"cost": 5})

        assert len(triggered) == 0

    def test_multiple_rules(self, mock_alert_manager):
        """Test multiple alert rules."""
        mock_alert_manager.add_rule(
            name="rule1",
            condition=lambda m: m.get("value", 0) > 10,
            message="Rule 1 triggered"
        )
        mock_alert_manager.add_rule(
            name="rule2",
            condition=lambda m: m.get("value", 0) < 0,
            message="Rule 2 triggered"
        )

        # Only rule1 should trigger
        triggered = mock_alert_manager.check({"value": 15})

        assert len(triggered) == 1
        assert triggered[0]["rule"] == "rule1"

    def test_multiple_alerts_triggered(self, mock_alert_manager):
        """Test multiple alerts triggered simultaneously."""
        mock_alert_manager.add_rule(
            name="rule1",
            condition=lambda m: m.get("value", 0) > 10,
            message="Rule 1 triggered"
        )
        mock_alert_manager.add_rule(
            name="rule2",
            condition=lambda m: m.get("value", 0) > 5,
            message="Rule 2 triggered"
        )

        # Both should trigger
        triggered = mock_alert_manager.check({"value": 15})

        assert len(triggered) == 2

    def test_alert_history(self, mock_alert_manager):
        """Test that alerts are recorded in history."""
        mock_alert_manager.add_rule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            message="Test"
        )

        mock_alert_manager.check({"value": 15})
        mock_alert_manager.check({"value": 20})

        all_alerts = mock_alert_manager.get_alerts()
        assert len(all_alerts) == 2

    def test_filter_alerts_by_rule(self, mock_alert_manager):
        """Test filtering alerts by rule name."""
        mock_alert_manager.add_rule(
            name="rule1",
            condition=lambda m: m.get("value", 0) > 10,
            message="Rule 1"
        )
        mock_alert_manager.add_rule(
            name="rule2",
            condition=lambda m: m.get("value", 0) > 10,
            message="Rule 2"
        )

        mock_alert_manager.check({"value": 15})

        rule1_alerts = mock_alert_manager.get_alerts("rule1")
        rule2_alerts = mock_alert_manager.get_alerts("rule2")

        assert len(rule1_alerts) == 1
        assert len(rule2_alerts) == 1

    def test_clear_alerts(self, mock_alert_manager):
        """Test clearing alert history."""
        mock_alert_manager.add_rule(
            name="test",
            condition=lambda m: True,
            message="Test"
        )

        mock_alert_manager.check({})
        assert len(mock_alert_manager.get_alerts()) == 1

        mock_alert_manager.clear_alerts()
        assert len(mock_alert_manager.get_alerts()) == 0

    def test_alert_timestamp(self, mock_alert_manager):
        """Test that alerts include timestamp."""
        mock_alert_manager.add_rule(
            name="test",
            condition=lambda m: True,
            message="Test"
        )

        before = datetime.now()
        triggered = mock_alert_manager.check({})
        after = datetime.now()

        alert = triggered[0]
        alert_time = datetime.fromisoformat(alert["timestamp"])

        assert before <= alert_time <= after

    def test_alert_includes_metrics(self, mock_alert_manager):
        """Test that alerts include the metrics that triggered them."""
        mock_alert_manager.add_rule(
            name="test",
            condition=lambda m: m.get("value", 0) > 10,
            message="Test"
        )

        test_metrics = {"value": 15, "other": "data"}
        triggered = mock_alert_manager.check(test_metrics)

        assert triggered[0]["metrics"] == test_metrics


class TestObservabilityIntegration:
    """Test integration of observability components."""

    def test_end_to_end_observability_flow(self, mock_structured_logger,
                                           mock_metrics_collector,
                                           mock_trace_context):
        """Test complete observability flow."""
        # Start trace
        with mock_trace_context.span("workflow", task="test_task"):
            # Log event
            mock_structured_logger.log_agent_execution(
                agent="test_agent",
                action="process",
                status="running",
                details={"task": "test_task"}
            )

            # Record metric
            mock_metrics_collector.increment_counter(
                "tasks_started",
                1,
                labels={"agent": "test_agent"}
            )

        # Verify all components recorded data
        assert len(mock_trace_context.get_trace()["spans"]) == 1
        assert len(mock_structured_logger.get_logs()) == 1
        assert mock_metrics_collector.get_metrics()["counters"]["tasks_started{agent=test_agent}"] == 1

    def test_correlation_between_logs_and_traces(self, mock_structured_logger,
                                                  mock_trace_context):
        """Test correlating logs with traces."""
        trace_id = mock_trace_context.trace_id

        with mock_trace_context.span("operation", correlation_id="test123"):
            mock_structured_logger.log_agent_execution(
                agent="test",
                action="op",
                status="done",
                details={"trace_id": trace_id}
            )

        # Both should have trace information
        trace = mock_trace_context.get_trace()
        logs = mock_structured_logger.get_logs()

        assert trace["trace_id"] == trace_id
        assert logs[0]["details"]["trace_id"] == trace_id

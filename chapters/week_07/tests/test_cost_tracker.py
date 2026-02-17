"""
Tests for Cost Tracker - Week 07

Tests the cost tracking functionality including:
- Recording LLM calls
- Calculating costs per call and totals
- Grouping costs by agent
- Edge cases (empty, zero tokens, unknown models)
"""

import pytest
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
LLMMetrics = week07_conftest.LLMMetrics
MockCostTracker = week07_conftest.MockCostTracker


class TestCostTrackerBasics:
    """Test basic cost tracker functionality."""

    def test_cost_tracker_initialization(self, mock_cost_tracker):
        """Test that cost tracker initializes correctly."""
        assert mock_cost_tracker is not None
        assert mock_cost_tracker.calls == []
        assert len(mock_cost_tracker.PRICING) > 0

    def test_record_single_call(self, mock_cost_tracker):
        """Test recording a single LLM call."""
        metrics = LLMMetrics(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500,
            timestamp=datetime.now(),
            agent_name="planner"
        )

        mock_cost_tracker.record_call(metrics)

        assert len(mock_cost_tracker.calls) == 1
        assert mock_cost_tracker.calls[0] == metrics

    def test_record_multiple_calls(self, mock_cost_tracker):
        """Test recording multiple LLM calls."""
        calls = [
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
        ]

        for call in calls:
            mock_cost_tracker.record_call(call)

        assert len(mock_cost_tracker.calls) == 2

    def test_calculate_cost_single_call_gpt4o(self, mock_cost_tracker):
        """Test cost calculation for GPT-4o."""
        metrics = LLMMetrics(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500,
            timestamp=datetime.now(),
            agent_name="planner"
        )

        cost = mock_cost_tracker.calculate_cost(metrics)

        # GPT-4o: $2.50/M input, $10.00/M output
        # 1000 input * 2.50 / 1M = 0.0025
        # 500 output * 10.00 / 1M = 0.005
        # Total = 0.0075
        expected_cost = (1000 * 2.50 / 1_000_000) + (500 * 10.00 / 1_000_000)
        assert abs(cost - expected_cost) < 1e-6

    def test_calculate_cost_single_call_mini(self, mock_cost_tracker):
        """Test cost calculation for GPT-4o-mini."""
        metrics = LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=800,
            timestamp=datetime.now(),
            agent_name="executor"
        )

        cost = mock_cost_tracker.calculate_cost(metrics)

        # GPT-4o-mini: $0.15/M input, $0.60/M output
        expected_cost = (1000 * 0.15 / 1_000_000) + (500 * 0.60 / 1_000_000)
        assert abs(cost - expected_cost) < 1e-6

    def test_get_summary_empty_tracker(self, mock_cost_tracker):
        """Test getting summary when no calls recorded."""
        summary = mock_cost_tracker.get_summary()

        assert summary["total_calls"] == 0
        assert summary["total_cost_usd"] == 0
        assert summary["total_tokens"] == 0
        assert summary["cost_by_agent"] == {}
        assert summary["avg_latency_ms"] == 0

    def test_get_summary_with_calls(self, mock_cost_tracker, sample_llm_metrics):
        """Test getting summary with recorded calls."""
        for metrics in sample_llm_metrics:
            mock_cost_tracker.record_call(metrics)

        summary = mock_cost_tracker.get_summary()

        assert summary["total_calls"] == 3
        assert summary["total_cost_usd"] > 0
        assert summary["total_tokens"] > 0
        assert len(summary["cost_by_agent"]) > 0
        assert summary["avg_latency_ms"] > 0

    def test_cost_by_agent_grouping(self, mock_cost_tracker):
        """Test that costs are correctly grouped by agent."""
        calls = [
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
                agent_name="planner"
            ),
        ]

        for call in calls:
            mock_cost_tracker.record_call(call)

        summary = mock_cost_tracker.get_summary()

        assert "planner" in summary["cost_by_agent"]
        assert "executor" in summary["cost_by_agent"]
        assert summary["cost_by_agent"]["planner"]["calls"] == 2
        assert summary["cost_by_agent"]["executor"]["calls"] == 1


class TestCostTrackerEdgeCases:
    """Test edge cases for cost tracker."""

    def test_zero_tokens(self, mock_cost_tracker):
        """Test handling of zero token counts."""
        metrics = LLMMetrics(
            model="gpt-4o",
            input_tokens=0,
            output_tokens=0,
            latency_ms=100,
            timestamp=datetime.now(),
            agent_name="test"
        )

        cost = mock_cost_tracker.calculate_cost(metrics)
        assert cost == 0

    def test_unknown_model(self, mock_cost_tracker):
        """Test handling of unknown model names."""
        metrics = LLMMetrics(
            model="unknown-model",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1000,
            timestamp=datetime.now(),
            agent_name="test"
        )

        # Unknown model should have zero cost
        cost = mock_cost_tracker.calculate_cost(metrics)
        assert cost == 0

    def test_no_agent_name(self, mock_cost_tracker):
        """Test handling of calls without agent names."""
        metrics = LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=500,
            output_tokens=200,
            latency_ms=600,
            timestamp=datetime.now(),
            agent_name=None
        )

        mock_cost_tracker.record_call(metrics)
        summary = mock_cost_tracker.get_summary()

        # Should be grouped under "unknown"
        assert "unknown" in summary["cost_by_agent"]
        assert summary["cost_by_agent"]["unknown"]["calls"] == 1

    def test_very_large_token_counts(self, mock_cost_tracker):
        """Test handling of very large token counts (128K context)."""
        metrics = LLMMetrics(
            model="gpt-4o",
            input_tokens=128000,
            output_tokens=4000,
            latency_ms=15000,
            timestamp=datetime.now(),
            agent_name="test"
        )

        cost = mock_cost_tracker.calculate_cost(metrics)

        # Should calculate cost correctly for large inputs
        expected_cost = (128000 * 2.50 / 1_000_000) + (4000 * 10.00 / 1_000_000)
        assert abs(cost - expected_cost) < 1e-4

    def test_negative_latency(self, mock_cost_tracker):
        """Test handling of negative latency (shouldn't happen but test defensive)."""
        metrics = LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            latency_ms=-100,  # Invalid
            timestamp=datetime.now(),
            agent_name="test"
        )

        mock_cost_tracker.record_call(metrics)
        summary = mock_cost_tracker.get_summary()

        # Average latency should be negative (data validation is separate concern)
        assert summary["avg_latency_ms"] < 0

    def test_reset_tracker(self, mock_cost_tracker, sample_llm_metrics):
        """Test resetting the cost tracker."""
        for metrics in sample_llm_metrics:
            mock_cost_tracker.record_call(metrics)

        assert len(mock_cost_tracker.calls) == 3

        mock_cost_tracker.reset()

        assert len(mock_cost_tracker.calls) == 0


class TestCostTrackerCostComparison:
    """Test cost comparison between different models."""

    def test_mini_vs_full_cost_savings(self, mock_cost_tracker):
        """Test cost savings when using mini vs full model."""
        full_metrics = LLMMetrics(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500,
            timestamp=datetime.now(),
            agent_name="test"
        )

        mini_metrics = LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=800,
            timestamp=datetime.now(),
            agent_name="test"
        )

        full_cost = mock_cost_tracker.calculate_cost(full_metrics)
        mini_cost = mock_cost_tracker.calculate_cost(mini_metrics)

        # Mini should be significantly cheaper
        savings_ratio = (full_cost - mini_cost) / full_cost
        assert savings_ratio > 0.9  # More than 90% cheaper

    def test_agent_cost_distribution(self, mock_cost_tracker, sample_llm_metrics):
        """Test analyzing cost distribution across agents."""
        for metrics in sample_llm_metrics:
            mock_cost_tracker.record_call(metrics)

        summary = mock_cost_tracker.get_summary()

        # Get costs by agent
        planner_cost = summary["cost_by_agent"].get("planner", {}).get("cost", 0)
        executor_cost = summary["cost_by_agent"].get("executor", {}).get("cost", 0)
        reviewer_cost = summary["cost_by_agent"].get("reviewer", {}).get("cost", 0)

        # All should have non-zero costs
        assert planner_cost > 0
        assert executor_cost > 0
        assert reviewer_cost > 0

        # Total should match summary
        agent_total = planner_cost + executor_cost + reviewer_cost
        assert abs(agent_total - summary["total_cost_usd"]) < 1e-6


class TestCostTrackerLatencyMetrics:
    """Test latency tracking functionality."""

    def test_average_latency_calculation(self, mock_cost_tracker):
        """Test average latency is calculated correctly."""
        calls = [
            LLMMetrics(
                model="gpt-4o-mini",
                input_tokens=100,
                output_tokens=50,
                latency_ms=1000,
                timestamp=datetime.now(),
                agent_name="test"
            ),
            LLMMetrics(
                model="gpt-4o-mini",
                input_tokens=100,
                output_tokens=50,
                latency_ms=2000,
                timestamp=datetime.now(),
                agent_name="test"
            ),
            LLMMetrics(
                model="gpt-4o-mini",
                input_tokens=100,
                output_tokens=50,
                latency_ms=3000,
                timestamp=datetime.now(),
                agent_name="test"
            ),
        ]

        for call in calls:
            mock_cost_tracker.record_call(call)

        summary = mock_cost_tracker.get_summary()
        assert summary["avg_latency_ms"] == 2000

    def test_latency_by_agent_analysis(self, mock_cost_tracker):
        """Test analyzing latency patterns by agent."""
        # Planner usually slower (more thinking)
        planner_call = LLMMetrics(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=2500,
            timestamp=datetime.now(),
            agent_name="planner"
        )

        # Executor usually faster (tool calls)
        executor_call = LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=200,
            output_tokens=100,
            latency_ms=500,
            timestamp=datetime.now(),
            agent_name="executor"
        )

        mock_cost_tracker.record_call(planner_call)
        mock_cost_tracker.record_call(executor_call)

        summary = mock_cost_tracker.get_summary()
        # Average should be between the two
        assert 500 < summary["avg_latency_ms"] < 2500

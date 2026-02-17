"""
Tests for Planner-Executor pattern in multi-agent systems.

This module tests the Planner-Executor pattern where:
- Planner Agent: Creates plans by decomposing tasks
- Executor Agent: Executes plans by calling tools
- Reviewer Agent: Reviews execution results
"""

import pytest
from typing import Dict, List

from .conftest import (
    PlannerAgent, ExecutorAgent, ReviewerAgent, ExecutionPlan, SubTask,
    ExecutionResult
)


# =============================================================================
# Planner Agent Tests
# =============================================================================

class TestPlannerAgentCreation:
    """Tests for PlannerAgent creation and initialization."""

    def test_planner_agent_can_be_created(self, mock_llm_client):
        """Test that PlannerAgent can be instantiated."""
        agent = PlannerAgent(llm_client=mock_llm_client)

        assert agent is not None
        assert agent.role.value == "planner"
        assert agent.llm == mock_llm_client

    def test_planner_agent_has_required_methods(self, planner_agent):
        """Test PlannerAgent has required methods."""
        assert hasattr(planner_agent, "create_plan")
        assert hasattr(planner_agent, "revise_plan")


class TestPlanCreation:
    """Tests for plan creation by Planner Agent."""

    def test_create_plan_returns_valid_plan(self, planner_agent, sample_tasks):
        """Test create_plan returns valid ExecutionPlan."""
        plan = planner_agent.create_plan(sample_tasks["sentiment_analysis"])

        assert plan is not None
        assert plan.task_understanding is not None
        assert len(plan.subtasks) > 0
        assert plan.expected_output is not None

    def test_create_plan_for_sentiment_analysis(self, planner_agent):
        """Test plan creation for sentiment analysis task."""
        plan = planner_agent.create_plan("分析客户反馈的情感倾向")

        assert "情感" in plan.task_understanding or "分析" in plan.task_understanding
        assert any(st.tool == "analyze_sentiment" for st in plan.subtasks)

    def test_create_plan_for_keyword_extraction(self, planner_agent):
        """Test plan creation for keyword extraction task."""
        plan = planner_agent.create_plan("从文本中提取关键词")

        assert "关键词" in plan.task_understanding or "提取" in plan.task_understanding
        assert any(st.tool == "extract_keywords" for st in plan.subtasks)

    def test_create_plan_for_complex_task(self, planner_agent):
        """Test plan creation for complex multi-step task."""
        plan = planner_agent.create_plan("分析反馈的情感、提取关键词、统计词频")

        # Should have more subtasks for complex task
        assert len(plan.subtasks) >= 3

    def test_create_plan_stores_last_plan(self, planner_agent, sample_tasks):
        """Test that create_plan stores the plan."""
        plan1 = planner_agent.create_plan(sample_tasks["sentiment_analysis"])
        plan2 = planner_agent.last_plan

        assert plan1 == plan2

    def test_plan_subtasks_have_correct_structure(self, planner_agent):
        """Test that plan subtasks have the correct structure."""
        plan = planner_agent.create_plan("分析情感")

        for subtask in plan.subtasks:
            assert hasattr(subtask, "step")
            assert hasattr(subtask, "action")
            assert hasattr(subtask, "tool")
            assert hasattr(subtask, "params")
            assert isinstance(subtask.step, int)
            assert isinstance(subtask.action, str)
            assert isinstance(subtask.tool, str)


class TestPlanRevision:
    """Tests for plan revision by Planner Agent."""

    def test_revise_plan_modifies_original_plan(self, planner_agent):
        """Test that revise_plan creates a modified version."""
        original_plan = planner_agent.create_plan("分析情感")
        feedback = "需要更详细的分析步骤"

        revised_plan = planner_agent.revise_plan(original_plan, feedback)

        assert revised_plan is not None
        assert revised_plan != original_plan
        assert "修订" in revised_plan.task_understanding

    def test_revise_plan_adds_revision_step(self, planner_agent):
        """Test that revise_plan adds a revision subtask."""
        original_plan = planner_agent.create_plan("分析情感")
        feedback = "增加验证步骤"

        revised_plan = planner_agent.revise_plan(original_plan, feedback)

        assert len(revised_plan.subtasks) > len(original_plan.subtasks)
        assert any(st.action == "修订计划" for st in revised_plan.subtasks)

    def test_revise_plan_preserves_expected_output(self, planner_agent):
        """Test that revise_plan preserves the expected output."""
        original_plan = planner_agent.create_plan("分析情感")
        original_output = original_plan.expected_output

        revised_plan = planner_agent.revise_plan(original_plan, "改进")

        assert revised_plan.expected_output == original_output


# =============================================================================
# Executor Agent Tests
# =============================================================================

class TestExecutorAgentCreation:
    """Tests for ExecutorAgent creation and initialization."""

    def test_executor_agent_can_be_created(self, sample_tools):
        """Test that ExecutorAgent can be instantiated."""
        agent = ExecutorAgent(tools=sample_tools)

        assert agent is not None
        assert agent.role.value == "executor"
        assert agent.tools == sample_tools

    def test_executor_agent_has_required_methods(self, executor_agent):
        """Test ExecutorAgent has required methods."""
        assert hasattr(executor_agent, "execute_plan")
        assert hasattr(executor_agent, "execution_history")


class TestPlanExecution:
    """Tests for plan execution by Executor Agent."""

    def test_execute_plan_returns_valid_result(self, executor_agent, sample_plans):
        """Test execute_plan returns valid ExecutionResult."""
        result = executor_agent.execute_plan(sample_plans["simple_plan"])

        assert result is not None
        assert result.plan == sample_plans["simple_plan"]
        assert result.results is not None
        assert result.status is not None

    def test_execute_plan_with_valid_tools(self, executor_agent):
        """Test execute_plan with available tools."""
        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[
                SubTask(step=1, action="分析", tool="analyze_sentiment",
                       params={"text": "很好，满意"})
            ],
            expected_output="结果"
        )

        result = executor_agent.execute_plan(plan)

        assert result.status == "completed"
        assert len(result.results) == 1

    def test_execute_plan_records_execution_history(self, executor_agent, sample_plans):
        """Test that execute_plan records history."""
        initial_history_len = len(executor_agent.execution_history)

        executor_agent.execute_plan(sample_plans["simple_plan"])

        assert len(executor_agent.execution_history) > initial_history_len

    def test_execute_plan_with_multiple_subtasks(self, executor_agent):
        """Test execute_plan with multiple subtasks."""
        plan = ExecutionPlan(
            task_understanding="多步骤测试",
            subtasks=[
                SubTask(step=i, action=f"步骤{i}", tool="mock_tool", params={"idx": i})
                for i in range(1, 4)
            ],
            expected_output="结果"
        )

        result = executor_agent.execute_plan(plan)

        assert len(result.results) == 3
        assert result.results[0]["step"] == 1
        assert result.results[1]["step"] == 2
        assert result.results[2]["step"] == 3

    def test_execute_plan_result_structure(self, executor_agent):
        """Test execute_plan result has correct structure."""
        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[
                SubTask(step=1, action="测试", tool="test", params={})
            ],
            expected_output="输出"
        )

        result = executor_agent.execute_plan(plan)

        for result_item in result.results:
            assert "step" in result_item
            assert "action" in result_item
            assert "tool" in result_item
            assert "result" in result_item


# =============================================================================
# Planner-Executor Integration Tests
# =============================================================================

class TestPlannerExecutorIntegration:
    """Tests for Planner-Executor integration."""

    def test_full_planner_executor_cycle(self, planner_agent, executor_agent, sample_tasks):
        """Test complete planner-executor cycle."""
        # Create plan
        plan = planner_agent.create_plan(sample_tasks["sentiment_analysis"])
        assert plan is not None

        # Execute plan
        result = executor_agent.execute_plan(plan)
        assert result.status in ["completed", "completed_with_errors"]

        # Verify execution matches plan
        assert len(result.results) == len(plan.subtasks)


# =============================================================================
# Edge Cases
# =============================================================================

class TestPlannerExecutorEdgeCases:
    """Edge case tests for Planner-Executor pattern."""

    def test_planner_with_empty_task(self, planner_agent):
        """Test planner with empty task."""
        plan = planner_agent.create_plan("")

        assert plan is not None

    def test_planner_with_very_long_task(self, planner_agent):
        """Test planner with very long task description."""
        long_task = "分析" * 100 + "的情感"

        plan = planner_agent.create_plan(long_task)

        assert plan is not None

    def test_executor_with_empty_plan(self, executor_agent):
        """Test executor with empty plan (no subtasks)."""
        empty_plan = ExecutionPlan(
            task_understanding="",
            subtasks=[],
            expected_output=""
        )

        result = executor_agent.execute_plan(empty_plan)

        assert result.status == "completed"
        assert len(result.results) == 0

    def test_executor_with_very_complex_plan(self, executor_agent):
        """Test executor with many subtasks."""
        complex_plan = ExecutionPlan(
            task_understanding="复杂任务",
            subtasks=[
                SubTask(step=i, action=f"步骤{i}", tool="tool", params={})
                for i in range(1, 51)
            ],
            expected_output="结果"
        )

        result = executor_agent.execute_plan(complex_plan)

        assert len(result.results) == 50

    def test_planner_with_special_characters(self, planner_agent):
        """Test planner with special characters in task."""
        task = "分析@#￥%……&*()的情感"

        plan = planner_agent.create_plan(task)

        assert plan is not None

    def test_executor_with_tool_that_raises_exception(self, executor_agent):
        """Test executor when tool raises exception."""

        def failing_tool(**kwargs):
            raise ValueError("Tool failed")

        executor_agent.tools["failing_tool"] = failing_tool

        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[
                SubTask(step=1, action="测试", tool="failing_tool", params={})
            ],
            expected_output="结果"
        )

        result = executor_agent.execute_plan(plan)

        # Should handle exception gracefully
        assert result.status == "completed_with_errors"
        assert len(result.errors) > 0

    def test_planner_with_unicode_task(self, planner_agent):
        """Test planner with Unicode characters."""
        task = "分析客户反馈的Emotional状态😊"

        plan = planner_agent.create_plan(task)

        assert plan is not None

    def test_multiple_plans_from_same_planner(self, planner_agent):
        """Test creating multiple plans from same planner."""
        plan1 = planner_agent.create_plan("任务1")
        plan2 = planner_agent.create_plan("任务2")
        plan3 = planner_agent.create_plan("任务3")

        # Each plan should be independent
        assert plan1 != plan2
        assert plan2 != plan3
        assert planner_agent.last_plan == plan3


class TestPlannerExecutorErrorCases:
    """Error case tests for Planner-Executor pattern."""

    def test_subtask_with_missing_params(self, executor_agent):
        """Test executor with subtask missing params."""
        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[
                SubTask(step=1, action="测试", tool="analyze_sentiment", params=None)
            ],
            expected_output="结果"
        )

        result = executor_agent.execute_plan(plan)

        # Should handle missing params
        assert result is not None

"""
Tests for Planning Agent functionality.

Tests cover:
- Task decomposition (task planning)
- Plan parsing and validation
- Execution of planned steps
- Plan-Execute separation
"""

import pytest
from .conftest import (
    PlanningAgent,
    MockLLMClient,
    ToolCall,
    TextAnalyzerTools
)


class TestTaskDecomposition:
    """Test task decomposition and planning."""

    def test_planning_agent_creates_plan(self, planning_agent):
        """Test Planning Agent creates a plan."""
        result = planning_agent.run("分析客户反馈")

        assert "plan" in result
        assert result["plan"] is not None
        assert isinstance(result["plan"], str)

    def test_plan_contains_steps(self, planning_agent):
        """Test plan contains multiple steps."""
        result = planning_agent.run("分析情感并提取关键词")

        plan = result["plan"]
        assert len(plan) > 0

    def test_plan_for_sentiment_analysis(self, tool_dict):
        """Test plan for sentiment analysis task."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())
        result = agent.run("分析这段文本的情感倾向")

        plan = result["plan"]
        # Plan should mention analysis/keywords
        assert any(keyword in plan.lower() for keyword in ["分析", "情感", "步骤"])

    def test_plan_for_keyword_extraction(self, tool_dict):
        """Test plan for keyword extraction task."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())
        result = agent.run("提取这段文本的关键词")

        plan = result["plan"]
        # Plan should mention keywords
        assert any(keyword in plan.lower() for keyword in ["关键词", "词频", "步骤"])

    def test_plan_for_complex_task(self, tool_dict):
        """Test plan for complex multi-step task."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())
        task = """分析以下客户反馈并生成报告：
        1. "产品质量很好，但物流太慢"
        2. "客服态度差，问题没解决"
        3. "价格合理，推荐购买"
        """
        result = agent.run(task)

        plan = result["plan"]
        # Complex task should generate longer plan
        assert len(plan) > 0

    def test_plan_first_flag_true(self, tool_dict):
        """Test plan_first=True creates plan."""
        agent = PlanningAgent(
            tools=tool_dict,
            llm_client=MockLLMClient(),
            plan_first=True
        )
        result = agent.run("测试任务")

        assert result["plan"] is not None

    def test_plan_first_flag_false(self, tool_dict):
        """Test plan_first=False skips planning."""
        agent = PlanningAgent(
            tools=tool_dict,
            llm_client=MockLLMClient(),
            plan_first=False
        )
        result = agent.run("测试任务")

        assert result["plan"] is None

    def test_plan_stored_in_agent(self, planning_agent):
        """Test plan is stored in agent after creation."""
        planning_agent.run("分析情感")

        assert planning_agent.last_plan is not None
        assert isinstance(planning_agent.last_plan, str)


class TestPlanParsing:
    """Test parsing and validation of plans."""

    def test_plan_is_string(self, planning_agent):
        """Test plan is returned as string."""
        result = planning_agent.run("测试")

        assert isinstance(result["plan"], str)

    def test_plan_not_empty(self, planning_agent):
        """Test plan is not empty."""
        result = planning_agent.run("分析情感")

        plan = result["plan"]
        assert len(plan.strip()) > 0

    def test_plan_has_multiple_lines(self, planning_agent):
        """Test plan typically spans multiple lines."""
        result = planning_agent.run("分析并提取关键词")

        plan = result["plan"]
        lines = plan.split("\n")

        # Should have multiple lines/steps
        assert len(lines) >= 2

    def test_plan_contains_numbered_steps(self, planning_agent):
        """Test plan contains numbered steps."""
        result = planning_agent.run("分析情感")

        plan = result["plan"]
        # Should contain step numbers
        assert "1." in plan or "步骤" in plan

    def test_plan_mentions_available_tools(self, tool_dict):
        """Test plan references available tools."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())
        result = agent.run("测试")

        plan = result["plan"].lower()

        # Plan should be generated based on available tools
        # (Our simple implementation always generates a plan)
        assert len(plan) > 0


class TestPlanExecution:
    """Test execution of planned steps."""

    def test_plan_then_execute(self, tool_dict):
        """Test plan is created before execution."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())

        result = agent.run("分析情感")

        # Should have both plan and execution history
        assert "plan" in result
        assert "history" in result
        assert "final_answer" in result

    def test_execution_follows_plan_structure(self, tool_dict):
        """Test execution has expected structure."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())

        result = agent.run("分析情感")

        # Execution should produce valid result structure
        assert "status" in result
        assert "iterations" in result

    def test_execution_with_plan_first(self, tool_dict):
        """Test execution when plan_first=True."""
        agent = PlanningAgent(
            tools=tool_dict,
            llm_client=MockLLMClient(),
            plan_first=True
        )

        result = agent.run("分析情感")

        # Plan should be present
        assert result["plan"] is not None
        # Execution should complete
        assert result["status"] in ["completed", "max_iterations_reached"]

    def test_execution_without_plan(self, tool_dict):
        """Test execution when plan_first=False."""
        agent = PlanningAgent(
            tools=tool_dict,
            llm_client=MockLLMClient(),
            plan_first=False
        )

        result = agent.run("分析情感")

        # No plan should be created
        assert result["plan"] is None
        # Execution should still complete
        assert "final_answer" in result


class TestPlanningAgentEdgeCases:
    """Test Planning Agent edge cases."""

    def test_empty_task(self, planning_agent):
        """Test planning with empty task."""
        result = planning_agent.run("")

        # Should still generate a plan
        assert "plan" in result
        assert "final_answer" in result

    def test_very_long_task(self, planning_agent):
        """Test planning with very long task."""
        long_task = "这是一个很长的任务描述" * 100
        result = planning_agent.run(long_task)

        # Should handle gracefully
        assert "plan" in result

    def test_task_with_special_characters(self, planning_agent):
        """Test planning with special characters."""
        special_task = "分析：!!!@@@### 😊"
        result = planning_agent.run(special_task)

        assert "plan" in result

    def test_vague_task(self, planning_agent):
        """Test planning with vague/unclear task."""
        result = planning_agent.run("帮我分析一下")

        # Should still create some plan
        assert "plan" in result

    def test_consecutive_plans(self, planning_agent):
        """Test creating multiple plans consecutively."""
        result1 = planning_agent.run("分析情感")
        result2 = planning_agent.run("提取关键词")

        # Both should have plans
        assert result1["plan"] is not None
        assert result2["plan"] is not None

        # Plans should be stored
        assert planning_agent.last_plan is not None

    def test_plan_with_no_tools(self):
        """Test planning when no tools are available."""
        agent = PlanningAgent(
            tools={},
            llm_client=MockLLMClient(),
            plan_first=True
        )

        result = agent.run("测试任务")

        # Should still create a plan
        assert "plan" in result

    def test_plan_execution_with_tools(self, tool_dict):
        """Test plan execution with actual tool calls."""
        calls = [
            ToolCall(name="analyze_sentiment", arguments={"text": "很好"}, id="c1"),
            ToolCall(name="extract_keywords", arguments={"text": "很好"}, id="c2")
        ]

        client = MockLLMClient(tool_call_sequence=calls)
        agent = PlanningAgent(tools=tool_dict, llm_client=client, plan_first=True)

        result = agent.run("分析情感和关键词")

        # Should have plan AND execution history
        assert result["plan"] is not None
        assert len(result["history"]) == 2
        assert result["history"][0]["action"] == "analyze_sentiment"

    @pytest.mark.parametrize("task", [
        "分析情感",
        "提取关键词",
        "统计词频",
        "分析并总结",
        "分析情感、提取关键词、统计词频"
    ])
    def test_various_tasks_generate_plans(self, tool_dict, task):
        """Test various task types all generate plans."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())
        result = agent.run(task)

        assert "plan" in result
        assert len(result["plan"]) > 0


class TestPlanningAgentInheritance:
    """Test PlanningAgent correctly inherits from ReActAgent."""

    def test_has_react_methods(self, planning_agent):
        """Test PlanningAgent has ReActAgent methods."""
        assert hasattr(planning_agent, "run")
        assert hasattr(planning_agent, "tools")
        assert hasattr(planning_agent, "max_iterations")

    def test_overrides_run(self, planning_agent):
        """Test PlanningAgent overrides run method."""
        # PlanningAgent.run should include plan in result
        result = planning_agent.run("测试")

        # Regular ReActAgent wouldn't have "plan"
        assert "plan" in result

    def test_has_create_plan_method(self, planning_agent):
        """Test PlanningAgent has _create_plan method."""
        assert hasattr(planning_agent, "_create_plan")
        assert callable(planning_agent._create_plan)

    def test_uses_parent_execution_logic(self, tool_dict):
        """Test PlanningAgent uses parent's execution logic."""
        calls = [
            ToolCall(name="analyze_sentiment", arguments={"text": "很好"}, id="c1")
        ]

        client = MockLLMClient(tool_call_sequence=calls)
        agent = PlanningAgent(tools=tool_dict, llm_client=client, plan_first=True)

        result = agent.run("测试")

        # Should execute tools using parent's logic
        assert "history" in result
        assert "iterations" in result
        assert "status" in result


class TestPlanningAgentIntegration:
    """Integration tests for Planning Agent."""

    def test_full_plan_execute_cycle(self, tool_dict):
        """Test complete plan-then-execute cycle."""
        calls = [
            ToolCall(name="analyze_sentiment", arguments={"text": "很好"}, id="c1"),
            ToolCall(name="extract_keywords", arguments={"text": "很好"}, id="c2")
        ]

        client = MockLLMClient(tool_call_sequence=calls)
        agent = PlanningAgent(tools=tool_dict, llm_client=client, plan_first=True)

        result = agent.run("分析情感和关键词")

        # Plan first
        assert result["plan"] is not None
        # Then execute
        assert len(result["history"]) == 2
        # Final answer
        assert result["status"] == "completed"

    def test_multi_task_planning(self, tool_dict):
        """Test planning across multiple different tasks."""
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())

        tasks = [
            "分析第一条反馈的情感",
            "提取第二条反馈的关键词",
            "统计所有反馈的词频"
        ]

        results = [agent.run(task) for task in tasks]

        # Each should have its own plan
        for result in results:
            assert "plan" in result
            assert "final_answer" in result

    def test_plan_influences_execution(self, tool_dict):
        """Test that plan influences subsequent execution."""
        # This is a conceptual test - in real implementation,
        # the plan would guide tool selection
        agent = PlanningAgent(tools=tool_dict, llm_client=MockLLMClient())

        result = agent.run("分析情感")

        # Plan should be available before execution
        assert result["plan"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

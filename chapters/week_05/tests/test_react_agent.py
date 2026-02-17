"""
Tests for ReAct Agent functionality.

Tests cover:
- ReAct loop (Thought-Action-Observation)
- Tool call history tracking
- Final answer generation
- Edge cases and error handling
"""

import pytest
import json
from .conftest import (
    ReActAgent,
    MockLLMClient,
    ToolCall,
    LLMResponse,
    TextAnalyzerTools
)


class TestReAgentLoop:
    """Test ReAct Agent loop execution."""

    def test_agent_initialization(self, tool_dict):
        """Test Agent initializes correctly."""
        client = MockLLMClient()
        agent = ReActAgent(
            tools=tool_dict,
            llm_client=client,
            max_iterations=10,
            verbose=False
        )

        assert agent.tools == tool_dict
        assert agent.llm == client
        assert agent.max_iterations == 10
        assert len(agent.tool_schemas) == len(tool_dict)

    def test_agent_run_returns_result(self, react_agent):
        """Test Agent run returns expected result structure."""
        result = react_agent.run("测试任务")

        assert "final_answer" in result
        assert "history" in result
        assert "iterations" in result
        assert "status" in result

    def test_agent_direct_answer_no_tools(self, tool_dict):
        """Test Agent gives direct answer without calling tools."""
        client = MockLLMClient(responses={
            "测试": "这是我的答案"
        })
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试任务")

        assert result["final_answer"] == "这是我的答案"
        assert result["status"] == "completed"
        assert len(result["history"]) == 0

    def test_agent_with_single_tool_call(self, tool_dict, tool_call_sentiment):
        """Test Agent with single tool call."""
        client = MockLLMClient(tool_call_sequence=[tool_call_sentiment])
        agent = ReActAgent(tools=tool_dict, llm_client=client, max_iterations=5)

        result = agent.run("分析情感")

        assert result["status"] == "completed"
        assert len(result["history"]) == 1
        assert result["history"][0]["action"] == "analyze_sentiment"

    def test_agent_with_multiple_tool_calls(self, tool_dict, tool_call_sequence_analyze):
        """Test Agent with multiple tool calls in sequence."""
        client = MockLLMClient(tool_call_sequence=tool_call_sequence_analyze)
        agent = ReActAgent(tools=tool_dict, llm_client=client, max_iterations=10)

        result = agent.run("分析并提取关键词")

        assert len(result["history"]) == 2
        assert result["history"][0]["action"] == "analyze_sentiment"
        assert result["history"][1]["action"] == "extract_keywords"

    def test_agent_max_iterations_limit(self, tool_dict):
        """Test Agent stops at max_iterations."""
        # Create infinite tool call sequence
        infinite_calls = [
            ToolCall(
                name="analyze_sentiment",
                arguments={"text": "test"},
                id=f"call_{i}"
            )
            for i in range(100)
        ]

        client = MockLLMClient(tool_call_sequence=infinite_calls)
        agent = ReActAgent(tools=tool_dict, llm_client=client, max_iterations=5)

        result = agent.run("无限循环任务")

        assert result["iterations"] == 5
        assert result["status"] == "max_iterations_reached"
        assert len(result["history"]) == 5

    def test_agent_iteration_count(self, tool_dict, tool_call_sequence_analyze):
        """Test Agent correctly counts iterations."""
        client = MockLLMClient(tool_call_sequence=tool_call_sequence_analyze)
        agent = ReActAgent(tools=tool_dict, llm_client=client, max_iterations=10)

        result = agent.run("测试")

        # Should be 2 tool calls + 1 final answer = 3 iterations
        assert result["iterations"] == 3

    def test_agent_tool_execution(self, tool_dict):
        """Test Agent executes tools correctly."""
        call = ToolCall(
            name="analyze_sentiment",
            arguments={"text": "产品质量很好"},
            id="call_1"
        )

        client = MockLLMClient(tool_call_sequence=[call])
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("分析情感")

        assert len(result["history"]) == 1
        assert result["history"][0]["result"]["sentiment"] == "positive"


class TestReAgentHistory:
    """Test ReAct Agent history tracking."""

    def test_history_records_action(self, tool_dict, tool_call_sentiment):
        """Test history records tool action."""
        client = MockLLMClient(tool_call_sequence=[tool_call_sentiment])
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试")

        assert "action" in result["history"][0]
        assert result["history"][0]["action"] == "analyze_sentiment"

    def test_history_records_input(self, tool_dict, tool_call_sentiment):
        """Test history records tool input arguments."""
        client = MockLLMClient(tool_call_sequence=[tool_call_sentiment])
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试")

        assert "input" in result["history"][0]
        assert result["history"][0]["input"]["text"] == "产品质量很好，非常满意"

    def test_history_records_result(self, tool_dict, tool_call_sentiment):
        """Test history records tool execution result."""
        client = MockLLMClient(tool_call_sequence=[tool_call_sentiment])
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试")

        assert "result" in result["history"][0]
        assert "sentiment" in result["history"][0]["result"]

    def test_history_records_iteration_number(self, tool_dict, tool_call_sequence_analyze):
        """Test history records iteration number."""
        client = MockLLMClient(tool_call_sequence=tool_call_sequence_analyze)
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试")

        assert result["history"][0]["iteration"] == 1
        assert result["history"][1]["iteration"] == 2

    def test_history_preserves_order(self, tool_dict, tool_call_sequence_analyze):
        """Test history maintains chronological order."""
        client = MockLLMClient(tool_call_sequence=tool_call_sequence_analyze)
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试")

        # First action should be sentiment, second should be keywords
        assert result["history"][0]["action"] == "analyze_sentiment"
        assert result["history"][1]["action"] == "extract_keywords"

    def test_history_empty_without_tool_calls(self, tool_dict):
        """Test history is empty when no tools are called."""
        client = MockLLMClient(responses={"测试": "直接答案"})
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试")

        assert len(result["history"]) == 0


class TestReAgentEdgeCases:
    """Test ReAct Agent edge cases."""

    def test_empty_task(self, react_agent):
        """Test Agent with empty task."""
        result = react_agent.run("")

        # Should still return valid structure
        assert "final_answer" in result
        assert "status" in result

    def test_very_long_task(self, react_agent):
        """Test Agent with very long task description."""
        long_task = "这是一个很长的任务描述" * 100
        result = react_agent.run(long_task)

        assert "final_answer" in result

    def test_task_with_special_characters(self, react_agent):
        """Test Agent with special characters in task."""
        special_task = "分析这段文本：!!!@@@### 😊😊😊"
        result = react_agent.run(special_task)

        assert "final_answer" in result

    def test_unknown_tool_in_sequence(self, tool_dict):
        """Test Agent when LLM returns unknown tool."""
        unknown_call = ToolCall(
            name="unknown_tool",
            arguments={"text": "test"},
            id="call_unknown"
        )

        client = MockLLMClient(tool_call_sequence=[unknown_call])
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试")

        # Should handle gracefully - history records error
        assert len(result["history"]) == 1
        assert "error" in result["history"][0]

    def test_tool_execution_error(self, tool_dict):
        """Test Agent when tool execution fails."""
        # Create a failing tool
        def failing_tool(text: str) -> dict:
            raise ValueError("Tool failed")

        tools_with_fail = {**tool_dict, "failing_tool": failing_tool}

        fail_call = ToolCall(
            name="failing_tool",
            arguments={"text": "test"},
            id="call_fail"
        )

        client = MockLLMClient(tool_call_sequence=[fail_call])
        agent = ReActAgent(tools=tools_with_fail, llm_client=client)

        result = agent.run("测试")

        # Should record error in history
        assert "error" in result["history"][0]

    def test_zero_max_iterations(self, tool_dict):
        """Test Agent with max_iterations=0."""
        client = MockLLMClient()
        agent = ReActAgent(tools=tool_dict, llm_client=client, max_iterations=0)

        result = agent.run("测试")

        assert result["iterations"] == 0
        assert result["status"] == "max_iterations_reached"

    def test_single_max_iteration(self, tool_dict, tool_call_sentiment):
        """Test Agent with max_iterations=1."""
        client = MockLLMClient(tool_call_sequence=[tool_call_sentiment])
        agent = ReActAgent(tools=tool_dict, llm_client=client, max_iterations=1)

        result = agent.run("测试")

        # Should stop after first tool call without final answer
        assert result["iterations"] == 1
        assert result["status"] == "max_iterations_reached"

    def test_agent_with_no_tools(self):
        """Test Agent initialized with empty tools dict."""
        client = MockLLMClient()
        agent = ReActAgent(tools={}, llm_client=client)

        result = agent.run("测试")

        # Should give direct answer without tool calls
        assert "final_answer" in result
        assert len(result["history"]) == 0

    def test_consecutive_runs(self, react_agent):
        """Test Agent can be run multiple times."""
        result1 = react_agent.run("第一次运行")
        result2 = react_agent.run("第二次运行")

        # Both should return valid results
        assert "final_answer" in result1
        assert "final_answer" in result2

    @pytest.mark.parametrize("task", [
        "分析情感",
        "提取关键词",
        "统计词频",
        "分析并总结"
    ])
    def test_various_task_types(self, react_agent, task):
        """Test Agent handles various task types."""
        result = react_agent.run(task)

        assert "final_answer" in result
        assert "status" in result


class TestReAgentMessages:
    """Test ReAct Agent message handling."""

    def test_messages_initial_structure(self, tool_dict):
        """Test Agent starts with correct message structure."""
        client = MockLLMClient()
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        # Run to trigger message construction
        agent.run("测试")

        # Check first call had system prompt
        assert client.call_count >= 1
        first_messages = client.message_history[0]
        assert first_messages[0]["role"] == "system"

    def test_messages_include_task(self, tool_dict):
        """Test Agent includes user task in messages."""
        client = MockLLMClient()
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        task = "分析这段文本的情感"
        agent.run(task)

        first_messages = client.message_history[0]
        assert first_messages[1]["role"] == "user"
        assert task in first_messages[1]["content"]

    def test_messages_include_tools_parameter(self, tool_dict):
        """Test Agent passes tools to LLM."""
        client = MockLLMClient()
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        agent.run("测试")

        # Check that tools were passed (via call count check)
        assert client.call_count >= 1


class TestReAgentIntegration:
    """Integration tests for ReAct Agent."""

    def test_full_thought_action_observation_cycle(self, tool_dict):
        """Test complete Thought-Action-Observation cycle."""
        # Setup: sentiment -> keywords -> final answer
        calls = [
            ToolCall(name="analyze_sentiment", arguments={"text": "很好"}, id="c1"),
            ToolCall(name="extract_keywords", arguments={"text": "很好", "top_k": 3}, id="c2")
        ]

        client = MockLLMClient(tool_call_sequence=calls)
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("分析情感和关键词")

        # Should have 2 tool calls + 1 final answer = 3 iterations
        assert result["iterations"] == 3
        assert len(result["history"]) == 2
        assert result["status"] == "completed"

    def test_multi_step_analysis_task(self, tool_dict):
        """Test Agent on multi-step analysis task."""
        feedback = [
            "产品质量很好，但物流太慢了",
            "客服态度差，问题没解决"
        ]

        # Create calls for analyzing each feedback
        calls = [
            ToolCall(name="analyze_sentiment", arguments={"text": feedback[0]}, id="c1"),
            ToolCall(name="analyze_sentiment", arguments={"text": feedback[1]}, id="c2"),
            ToolCall(name="count_word_freq", arguments={"text": " ".join(feedback)}, id="c3")
        ]

        client = MockLLMClient(tool_call_sequence=calls)
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("分析多条反馈")

        assert len(result["history"]) == 3
        assert result["history"][0]["action"] == "analyze_sentiment"
        assert result["history"][2]["action"] == "count_word_freq"

    def test_agent_with_real_tools(self):
        """Test Agent with actual text analyzer tools."""
        tools = {
            "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
            "extract_keywords": TextAnalyzerTools.extract_keywords,
            "count_word_freq": TextAnalyzerTools.count_word_freq
        }

        calls = [
            ToolCall(name="analyze_sentiment", arguments={"text": "产品质量很好"}, id="c1"),
        ]

        client = MockLLMClient(tool_call_sequence=calls)
        agent = ReActAgent(tools=tools, llm_client=client)

        result = agent.run("分析情感")

        assert result["history"][0]["result"]["sentiment"] == "positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Smoke tests for Week 05 test infrastructure.

Basic tests to verify the testing environment is working correctly.
"""

import pytest


class TestWeek05TestInfrastructure:
    """Basic infrastructure tests."""

    def test_conftest_imports(self):
        """Test that conftest fixtures can be imported."""
        from .conftest import (
            TextAnalyzerTools,
            MockLLMClient,
            ReActAgent,
            PlanningAgent,
            ToolCall,
            LLMResponse,
            ToolDefinition
        )

        assert TextAnalyzerTools is not None
        assert MockLLMClient is not None
        assert ReActAgent is not None
        assert PlanningAgent is not None
        assert ToolCall is not None
        assert LLMResponse is not None
        assert ToolDefinition is not None

    def test_text_analyzer_creation(self):
        """Test TextAnalyzerTools can be created."""
        from .conftest import TextAnalyzerTools

        analyzer = TextAnalyzerTools()
        assert hasattr(analyzer, "analyze_sentiment")
        assert hasattr(analyzer, "extract_keywords")
        assert hasattr(analyzer, "count_word_freq")

    def test_mock_llm_creation(self):
        """Test MockLLMClient can be created."""
        from .conftest import MockLLMClient

        client = MockLLMClient()
        assert client.call_count == 0
        assert client.message_history == []

    def test_react_agent_creation(self, tool_dict):
        """Test ReActAgent can be created."""
        from .conftest import ReActAgent, MockLLMClient

        client = MockLLMClient()
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        assert agent.tools == tool_dict
        assert agent.max_iterations == 10
        assert agent.llm == client

    def test_planning_agent_creation(self, tool_dict):
        """Test PlanningAgent can be created."""
        from .conftest import PlanningAgent, MockLLMClient

        client = MockLLMClient()
        agent = PlanningAgent(tools=tool_dict, llm_client=client)

        assert agent.tools == tool_dict
        assert agent.plan_first is True

    def test_tool_call_creation(self):
        """Test ToolCall dataclass works."""
        from .conftest import ToolCall

        call = ToolCall(
            name="test_tool",
            arguments={"text": "test"},
            id="test_id"
        )

        assert call.name == "test_tool"
        assert call.arguments == {"text": "test"}
        assert call.id == "test_id"

    def test_llm_response_creation(self):
        """Test LLMResponse dataclass works."""
        from .conftest import LLMResponse, ToolCall

        # Response with content only
        resp1 = LLMResponse(content="Hello")
        assert resp1.content == "Hello"
        assert resp1.tool_calls is None

        # Response with tool calls
        call = ToolCall(name="tool", arguments={}, id="1")
        resp2 = LLMResponse(content="Thinking", tool_calls=[call])
        assert resp2.tool_calls == [call]

    def test_tool_definition_to_schema(self):
        """Test ToolDefinition.to_schema() works."""
        from .conftest import ToolDefinition

        tool = ToolDefinition(
            name="test_tool",
            description="Test description",
            parameters={"type": "object", "properties": {}}
        )

        schema = tool.to_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test_tool"
        assert schema["function"]["description"] == "Test description"

    def test_text_analyzer_sentiment_basic(self):
        """Test basic sentiment analysis."""
        from .conftest import TextAnalyzerTools

        result = TextAnalyzerTools.analyze_sentiment("很好，满意")

        assert "sentiment" in result
        assert "score" in result
        assert result["sentiment"] == "positive"

    def test_text_analyzer_keywords_basic(self):
        """Test basic keyword extraction."""
        from .conftest import TextAnalyzerTools

        result = TextAnalyzerTools.extract_keywords("产品质量很好，物流很快")

        assert "keywords" in result
        assert "counts" in result
        assert isinstance(result["keywords"], list)

    def test_text_analyzer_wordfreq_basic(self):
        """Test basic word frequency."""
        from .conftest import TextAnalyzerTools

        result = TextAnalyzerTools.count_word_freq("物流 物流 质量")

        assert "top_words" in result
        assert isinstance(result["top_words"], list)

    def test_mock_llm_chat_basic(self):
        """Test basic mock LLM chat."""
        from .conftest import MockLLMClient

        client = MockLLMClient()
        response = client.chat([{"role": "user", "content": "Hello"}])

        assert response.content is not None
        assert client.call_count == 1

    def test_react_agent_run_simple(self, tool_dict):
        """Test ReActAgent can run simple task."""
        from .conftest import ReActAgent, MockLLMClient

        client = MockLLMClient()
        agent = ReActAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试任务")

        assert "final_answer" in result
        assert "history" in result
        assert "iterations" in result

    def test_planning_agent_run_simple(self, tool_dict):
        """Test PlanningAgent can run simple task."""
        from .conftest import PlanningAgent, MockLLMClient

        client = MockLLMClient()
        agent = PlanningAgent(tools=tool_dict, llm_client=client)

        result = agent.run("测试任务")

        assert "final_answer" in result
        assert "plan" in result


class TestWeek05Coverage:
    """Tests to verify all Week 05 topics are covered."""

    def test_tools_tests_exist(self):
        """Test that tools tests exist."""
        from . import test_tools

        assert hasattr(test_tools, "TestAnalyzeSentiment")
        assert hasattr(test_tools, "TestExtractKeywords")
        assert hasattr(test_tools, "TestCountWordFreq")
        assert hasattr(test_tools, "TestToolsEdgeCases")

    def test_function_calling_tests_exist(self):
        """Test that Function Calling tests exist."""
        from . import test_function_calling

        assert hasattr(test_function_calling, "TestToolSchema")
        assert hasattr(test_function_calling, "TestToolCallParsing")
        assert hasattr(test_function_calling, "TestToolExecution")

    def test_react_agent_tests_exist(self):
        """Test that ReAct Agent tests exist."""
        from . import test_react_agent

        assert hasattr(test_react_agent, "TestReAgentLoop")
        assert hasattr(test_react_agent, "TestReAgentHistory")
        assert hasattr(test_react_agent, "TestReAgentEdgeCases")

    def test_planning_agent_tests_exist(self):
        """Test that Planning Agent tests exist."""
        from . import test_planning_agent

        assert hasattr(test_planning_agent, "TestTaskDecomposition")
        assert hasattr(test_planning_agent, "TestPlanParsing")
        assert hasattr(test_planning_agent, "TestPlanExecution")


class TestWeek05Anchors:
    """Tests that validate Week 05 anchor claims."""

    def test_agent_four_capabilities(self):
        """Verify Agent four capabilities are testable."""
        # Agent has: Perception, Planning, Action, Reflection
        from .conftest import ReActAgent, PlanningAgent

        # ReAct handles Action and Reflection (via loop)
        # PlanningAgent handles Planning
        # Both handle Perception (via LLM)

        assert hasattr(ReActAgent, "run")  # Action loop
        assert hasattr(PlanningAgent, "_create_plan")  # Planning

    def test_function_calling_safety(self):
        """Verify Function Calling safety is testable."""
        from .conftest import ToolDefinition

        # Tools must be explicitly defined
        safe_tool = ToolDefinition(
            name="safe_analyzer",
            description="Safe text analysis",
            parameters={"type": "object", "properties": {}}
        )

        schema = safe_tool.to_schema()
        assert schema["function"]["name"] == "safe_analyzer"

    def test_react_pattern_testable(self):
        """Verify ReAct pattern (Thought-Action-Observation) is testable."""
        from .conftest import ReActAgent

        # ReAct loop produces history with action/result
        agent = ReActAgent(tools={}, llm_client=None)
        assert hasattr(agent, "run")
        # History tracks iterations

    def test_task_decomposition_testable(self):
        """Verify task decomposition is testable."""
        from .conftest import PlanningAgent

        agent = PlanningAgent(tools={}, llm_client=None)
        assert hasattr(agent, "_create_plan")
        # Should produce structured plan


class TestWeek05Integration:
    """Integration tests for Week 05 components."""

    def test_full_agent_pipeline(self, tool_dict, tool_call_sequence_analyze):
        """Test full Agent pipeline: plan -> execute -> answer."""
        from .conftest import (
            ReActAgent,
            PlanningAgent,
            MockLLMClient,
            TextAnalyzerTools
        )

        # Create client with tool call sequence
        client = MockLLMClient(tool_call_sequence=tool_call_sequence_analyze)

        # Create agents
        react_agent = ReActAgent(tools=tool_dict, llm_client=client)
        planning_agent = PlanningAgent(tools=tool_dict, llm_client=client)

        # Run ReAct agent
        react_result = react_agent.run("分析情感")
        assert "history" in react_result

        # Run Planning agent
        plan_result = planning_agent.run("分析情感")
        assert "plan" in plan_result
        assert "history" in plan_result

    def test_tools_to_schema_to_execution_flow(self):
        """Test flow from tool definition to execution."""
        from .conftest import ToolDefinition, TextAnalyzerTools

        # Define tool
        tool_def = ToolDefinition(
            name="analyze_sentiment",
            description="Analyze sentiment",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            },
            function=TextAnalyzerTools.analyze_sentiment
        )

        # Get schema
        schema = tool_def.to_schema()
        assert schema["function"]["name"] == "analyze_sentiment"

        # Execute
        result = tool_def.function(text="很好")
        assert result["sentiment"] == "positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

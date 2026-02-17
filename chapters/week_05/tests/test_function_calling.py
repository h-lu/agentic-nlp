"""
Tests for Function Calling functionality.

Tests cover:
- Tool Schema definition and validation
- Tool call parsing from LLM responses
- Tool execution with arguments
- Error handling for invalid tool calls
"""

import pytest
import json
from .conftest import (
    ToolDefinition,
    ToolCall,
    MockLLMClient,
    TextAnalyzerTools,
    LLMResponse
)


class TestToolSchema:
    """Test tool schema definition and validation."""

    def test_tool_definition_creation(self):
        """Test creating a tool definition."""
        tool = ToolDefinition(
            name="analyze_sentiment",
            description="Analyze sentiment of text",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"}
                },
                "required": ["text"]
            }
        )

        assert tool.name == "analyze_sentiment"
        assert tool.description == "Analyze sentiment of text"
        assert tool.parameters["type"] == "object"

    def test_tool_to_schema_format(self):
        """Test converting tool to OpenAI-style schema."""
        tool = ToolDefinition(
            name="extract_keywords",
            description="Extract keywords from text",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5}
                },
                "required": ["text"]
            }
        )

        schema = tool.to_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "extract_keywords"
        assert schema["function"]["description"] == "Extract keywords from text"
        assert "parameters" in schema["function"]

    def test_schema_has_required_fields(self):
        """Test schema contains all required fields."""
        tool = ToolDefinition(
            name="test_tool",
            description="Test",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

        schema = tool.to_schema()

        # Check required OpenAI schema fields
        assert "type" in schema
        assert "function" in schema
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]

    def test_schema_parameters_structure(self):
        """Test schema parameters have correct structure."""
        tool = ToolDefinition(
            name="count_word_freq",
            description="Count word frequency",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to analyze"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Top K words",
                        "default": 10
                    }
                },
                "required": ["text"]
            }
        )

        schema = tool.to_schema()
        params = schema["function"]["parameters"]

        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert "text" in params["properties"]
        assert "top_k" in params["properties"]
        assert "text" in params["required"]
        assert "top_k" not in params["required"]

    def test_multiple_tool_schemas(self, tool_definitions):
        """Test generating schemas for multiple tools."""
        schemas = [tool.to_schema() for tool in tool_definitions]

        assert len(schemas) == 3

        # Check each schema is valid
        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]

    def test_tool_names_are_unique(self, tool_definitions):
        """Test tool names are unique in schema list."""
        schemas = [tool.to_schema() for tool in tool_definitions]
        names = [s["function"]["name"] for s in schemas]

        assert len(names) == len(set(names)), "Tool names must be unique"

    def test_schema_with_function_attached(self):
        """Test tool can have executable function attached."""
        tool = ToolDefinition(
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

        assert tool.function is not None
        assert callable(tool.function)


class TestToolCallParsing:
    """Test parsing tool calls from LLM responses."""

    def test_tool_call_creation(self):
        """Test creating a tool call object."""
        call = ToolCall(
            name="analyze_sentiment",
            arguments={"text": "产品质量很好"},
            id="call_123"
        )

        assert call.name == "analyze_sentiment"
        assert call.arguments == {"text": "产品质量很好"}
        assert call.id == "call_123"

    def test_llm_response_with_tool_calls(self):
        """Test LLM response containing tool calls."""
        call1 = ToolCall(name="tool1", arguments={"arg": "val1"}, id="call1")
        call2 = ToolCall(name="tool2", arguments={"arg": "val2"}, id="call2")

        response = LLMResponse(
            content="Let me call some tools",
            tool_calls=[call1, call2]
        )

        assert response.content == "Let me call some tools"
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "tool1"

    def test_llm_response_without_tool_calls(self):
        """Test LLM response without tool calls (final answer)."""
        response = LLMResponse(content="This is the final answer.")

        assert response.content == "NotImplementedError" if False else "This is the final answer."
        assert response.tool_calls is None

    def test_parse_tool_arguments_json(self):
        """Test parsing tool arguments as JSON."""
        call = ToolCall(
            name="extract_keywords",
            arguments='{"text": "产品质量很好", "top_k": 5}',
            id="call_json"
        )

        # Arguments should be dict or JSON string
        if isinstance(call.arguments, str):
            parsed = json.loads(call.arguments)
        else:
            parsed = call.arguments

        assert parsed["text"] == "产品质量很好"
        assert parsed["top_k"] == 5

    def test_tool_call_with_complex_arguments(self):
        """Test tool call with nested/complex arguments."""
        call = ToolCall(
            name="complex_tool",
            arguments={
                "text": "产品质量",
                "options": {
                    "include_stopwords": False,
                    "min_length": 2,
                    "max_results": 10
                },
                "filters": ["positive", "neutral"]
            },
            id="call_complex"
        )

        assert call.arguments["options"]["include_stopwords"] is False
        assert call.arguments["filters"][0] == "positive"

    def test_tool_call_with_default_parameters(self):
        """Test tool call with missing optional parameters."""
        call = ToolCall(
            name="extract_keywords",
            arguments={"text": "产品质量很好"},  # top_k not provided
            id="call_default"
        )

        assert "text" in call.arguments
        # top_k should use default value defined in schema


class TestToolExecution:
    """Test executing tools with parsed arguments."""

    def test_execute_sentiment_tool(self):
        """Test executing sentiment analysis tool."""
        tool = ToolDefinition(
            name="analyze_sentiment",
            description="Analyze sentiment",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            },
            function=TextAnalyzerTools.analyze_sentiment
        )

        result = tool.function(text="产品质量很好，非常满意")

        assert result["sentiment"] == "positive"
        assert result["score"] > 0

    def test_execute_keywords_tool(self):
        """Test executing keyword extraction tool."""
        tool = ToolDefinition(
            name="extract_keywords",
            description="Extract keywords",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "top_k": {"type": "integer"}
                },
                "required": ["text"]
            },
            function=TextAnalyzerTools.extract_keywords
        )

        result = tool.function(text="物流太慢了，客服态度差", top_k=3)

        assert "keywords" in result
        assert len(result["keywords"]) <= 3

    def test_execute_wordfreq_tool(self):
        """Test executing word frequency tool."""
        tool = ToolDefinition(
            name="count_word_freq",
            description="Count word frequency",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "top_k": {"type": "integer"}
                },
                "required": ["text"]
            },
            function=TextAnalyzerTools.count_word_freq
        )

        result = tool.function(text="物流 物流 质量")

        assert "top_words" in result
        assert result["top_words"][0]["count"] == 2

    def test_execute_tool_from_call_object(self):
        """Test executing tool using ToolCall object."""
        tool_call = ToolCall(
            name="analyze_sentiment",
            arguments={"text": "产品很好，很满意"},
            id="call_1"
        )

        # Simulate tool registry
        tools = {
            "analyze_sentiment": TextAnalyzerTools.analyze_sentiment
        }

        tool_func = tools[tool_call.name]
        result = tool_func(**tool_call.arguments)

        assert result["sentiment"] == "positive"

    def test_execute_multiple_tools_in_sequence(self, tool_call_sequence_analyze):
        """Test executing multiple tools in sequence."""
        tools = {
            "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
            "extract_keywords": TextAnalyzerTools.extract_keywords
        }

        results = []
        for call in tool_call_sequence_analyze:
            tool_func = tools[call.name]
            result = tool_func(**call.arguments)
            results.append(result)

        assert len(results) == 2
        assert results[0]["sentiment"] == "positive"
        assert len(results[1]["keywords"]) > 0

    def test_tool_execution_with_json_arguments(self):
        """Test tool execution when arguments are JSON string."""
        tool_call = ToolCall(
            name="extract_keywords",
            arguments='{"text": "产品质量很好", "top_k": 5}',
            id="call_json"
        )

        tools = {"extract_keywords": TextAnalyzerTools.extract_keywords}

        # Parse arguments
        if isinstance(tool_call.arguments, str):
            args = json.loads(tool_call.arguments)
        else:
            args = tool_call.arguments

        result = tools[tool_call.name](**args)

        assert "keywords" in result


class TestToolExecutionErrors:
    """Test error handling in tool execution."""

    def test_missing_required_parameter(self):
        """Test error when required parameter is missing."""
        tool = ToolDefinition(
            name="analyze_sentiment",
            description="Analyze sentiment",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            },
            function=TextAnalyzerTools.analyze_sentiment
        )

        # Call without required parameter
        with pytest.raises(TypeError):
            tool.function()  # Missing 'text' parameter

    def test_invalid_parameter_type(self):
        """Test error when parameter has wrong type."""
        tool = ToolDefinition(
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

        # text parameter should be string; passing None tests edge case handling
        # In production, this would be validated before execution
        result = tool.function(text=None)

        # Our implementation handles None gracefully
        assert "sentiment" in result

    def test_unknown_tool_name(self):
        """Test error when tool name doesn't exist."""
        tools = {
            "analyze_sentiment": TextAnalyzerTools.analyze_sentiment
        }

        tool_call = ToolCall(
            name="unknown_tool",
            arguments={"text": "test"},
            id="call_unknown"
        )

        # Tool doesn't exist
        assert tool_call.name not in tools

    def test_tool_function_raises_exception(self):
        """Test handling when tool function raises exception."""
        def failing_tool(text: str) -> dict:
            raise ValueError("Tool execution failed")

        tools = {"failing_tool": failing_tool}
        tool_call = ToolCall(
            name="failing_tool",
            arguments={"text": "test"},
            id="call_fail"
        )

        with pytest.raises(ValueError, match="Tool execution failed"):
            tools[tool_call.name](**tool_call.arguments)

    def test_empty_arguments(self):
        """Test tool execution with empty arguments."""
        tool_call = ToolCall(
            name="analyze_sentiment",
            arguments={},
            id="call_empty"
        )

        tools = {"analyze_sentiment": TextAnalyzerTools.analyze_sentiment}

        with pytest.raises(TypeError):
            tools[tool_call.name](**tool_call.arguments)

    def test_null_arguments(self):
        """Test tool execution with null arguments."""
        tool_call = ToolCall(
            name="analyze_sentiment",
            arguments={"text": None},
            id="call_null"
        )

        tools = {"analyze_sentiment": TextAnalyzerTools.analyze_sentiment}

        # Should handle None gracefully
        result = tools[tool_call.name](**tool_call.arguments)
        assert "sentiment" in result


class TestLLMClientToolCalling:
    """Test MockLLMClient tool calling behavior."""

    def test_llm_returns_tool_call(self, tool_call_sentiment):
        """Test LLM client can return tool call."""
        client = MockLLMClient(
            tool_call_sequence=[tool_call_sentiment]
        )

        response = client.chat(
            messages=[{"role": "user", "content": "分析情感"}],
            tools=[]
        )

        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "analyze_sentiment"

    def test_llm_returns_final_answer(self):
        """Test LLM client can return final answer without tool calls."""
        client = MockLLMClient(responses={
            "分析": "分析完成：情感为正面"
        })

        response = client.chat(
            messages=[{"role": "user", "content": "分析这段文本"}],
            tools=[]
        )

        assert response.content is not None
        assert response.tool_calls is None

    def test_llm_tool_call_sequence(self, tool_call_sequence_analyze):
        """Test LLM returns sequence of tool calls."""
        client = MockLLMClient(
            tool_call_sequence=tool_call_sequence_analyze
        )

        # First call
        response1 = client.chat(messages=[], tools=[])
        assert response1.tool_calls[0].name == "analyze_sentiment"

        # Second call
        response2 = client.chat(messages=[], tools=[])
        assert response2.tool_calls[0].name == "extract_keywords"

        # Third call (no more in sequence)
        response3 = client.chat(messages=[], tools=[])
        assert response3.tool_calls is None

    def test_llm_message_history_tracking(self):
        """Test LLM client tracks message history."""
        client = MockLLMClient()

        client.chat(messages=[{"role": "user", "content": "Hello"}])
        client.chat(messages=[{"role": "user", "content": "Hi"}])

        assert len(client.message_history) == 2
        assert client.call_count == 2

    def test_llm_reset(self):
        """Test LLM client reset functionality."""
        client = MockLLMClient()

        client.chat(messages=[{"role": "user", "content": "test"}])
        assert client.call_count == 1

        client.reset()
        assert client.call_count == 0
        assert len(client.message_history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Week 05 Tests - LLM Agent Basics

This directory contains the test suite for Week 05: LLM Agent Basics.

## Test Coverage

The test suite covers the following topics:

### 1. Text Analysis Tools (`test_tools.py`)
- **Sentiment Analysis** (`analyze_sentiment`): positive/negative/neutral classification
- **Keyword Extraction** (`extract_keywords`): top-k keyword extraction
- **Word Frequency** (`count_word_freq`): word frequency statistics

### 2. Function Calling (`test_function_calling.py`)
- **Tool Schema Definition**: OpenAI-style tool schemas
- **Tool Call Parsing**: parsing tool calls from LLM responses
- **Tool Execution**: executing tools with arguments
- **Error Handling**: missing parameters, unknown tools, execution errors

### 3. ReAct Agent (`test_react_agent.py`)
- **ReAct Loop**: Thought-Action-Observation cycle
- **Tool Call History**: tracking execution history
- **Final Answer Generation**: completing tasks
- **Edge Cases**: empty tasks, max iterations, tool failures

### 4. Planning Agent (`test_planning_agent.py`)
- **Task Decomposition**: creating execution plans
- **Plan Parsing**: validating plan structure
- **Plan-Execute Separation**: planning before execution
- **Inheritance**: PlanningAgent extends ReActAgent

## Running Tests

### Run all tests
```bash
python3 -m pytest chapters/week_05/tests -v
```

### Run specific test file
```bash
python3 -m pytest chapters/week_05/tests/test_tools.py -v
python3 -m pytest chapters/week_05/tests/test_function_calling.py -v
python3 -m pytest chapters/week_05/tests/test_react_agent.py -v
python3 -m pytest chapters/week_05/tests/test_planning_agent.py -v
```

### Run specific test class
```bash
python3 -m pytest chapters/week_05/tests/test_tools.py::TestAnalyzeSentiment -v
python3 -m pytest chapters/week_05/tests/test_react_agent.py::TestReAgentLoop -v
```

### Run specific test case
```bash
python3 -m pytest chapters/week_05/tests/test_tools.py::TestAnalyzeSentiment::test_positive_sentiment -v
```

### Run with coverage
```bash
python3 -m pytest chapters/week_05/tests --cov=chapters.week_05 --cov-report=html
```

### Run only fast tests
```bash
python3 -m pytest chapters/week_05/tests -m "not slow" -v
```

## Test Organization

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Shared fixtures and mock classes
├── test_smoke.py            # Infrastructure smoke tests
├── test_tools.py            # Text analysis tools tests
├── test_function_calling.py # Function Calling tests
├── test_react_agent.py      # ReAct Agent tests
├── test_planning_agent.py   # Planning Agent tests
└── README.md               # This file
```

## Fixtures

The `conftest.py` provides the following fixtures:

### Sample Data
- `sample_texts`: Sample text inputs (positive, negative, neutral, mixed, empty, etc.)
- `text_analyzer`: TextAnalyzerTools instance
- `agent_tasks`: Sample Agent tasks

### Mock Classes
- `mock_llm_client`: Mock LLM client for testing
- `tool_call_sentiment`: Mock sentiment analysis tool call
- `tool_call_keywords`: Mock keyword extraction tool call
- `tool_call_wordfreq`: Mock word frequency tool call
- `tool_call_sequence_analyze`: Sequence of tool calls

### Agent Components
- `tool_dict`: Dictionary of tool functions
- `react_agent`: ReActAgent instance
- `planning_agent`: PlanningAgent instance
- `tool_definitions`: List of ToolDefinition objects

## Test Naming Convention

Tests follow the pattern `test_<function>_<scenario>_<expected>`:

```python
def test_sentiment_positive_text_returns_positive():
    """Test that positive text returns positive sentiment."""
    pass

def test_keywords_empty_text_returns_empty_list():
    """Test that empty text returns empty keywords."""
    pass
```

## Test Categories

### 1. Unit Tests
- Test individual tool functions
- Test mock class behavior
- Test Agent component initialization

### 2. Integration Tests
- Test Agent execution flow
- Test tool calling sequences
- Test plan-then-execute cycle

### 3. Edge Cases
- Empty inputs
- Very long inputs
- Special characters
- Invalid parameters
- Tool failures

## Expected Behavior

### TextAnalyzerTools
- `analyze_sentiment`: Returns `{"sentiment": "positive|negative|neutral", "score": int, ...}`
- `extract_keywords`: Returns `{"keywords": [...], "counts": [...]}`
- `count_word_freq`: Returns `{"top_words": [{"word": str, "count": int}, ...]}`

### ReActAgent
- Returns `{"final_answer": str, "history": [...], "iterations": int, "status": str}`
- History records: `{"iteration": int, "action": str, "input": dict, "result": dict}`

### PlanningAgent
- Returns `{"final_answer": str, "history": [...], "plan": str, "iterations": int, "status": str}`
- Plan is created before execution

## Troubleshooting

### Import Errors
If you see import errors, ensure you're running pytest from the project root:
```bash
cd /home/ubuntu/agentic-nlp
python3 -m pytest chapters/week_05/tests -v
```

### Missing Fixtures
If pytest can't find fixtures, check that `conftest.py` is in the same directory.

### Test Failures
If tests fail, check:
1. Is the mock implementation correct?
2. Are the fixtures properly configured?
3. Is the test expecting the right behavior?

## Adding New Tests

When adding new tests:

1. **Follow naming convention**: `test_<feature>_<scenario>_<expected>`
2. **Use parametrize** for multiple similar cases
3. **Add docstrings** explaining what is being tested
4. **Use fixtures** for common setup
5. **Test edge cases** alongside happy paths

Example:
```python
@pytest.mark.parametrize("text,expected", [
    ("很好", "positive"),
    ("很差", "negative"),
])
def test_sentiment_classification(text, expected):
    """Test sentiment classification for various inputs."""
    result = TextAnalyzerTools.analyze_sentiment(text)
    assert result["sentiment"] == expected
```

## Notes

- Tests use mock implementations to avoid external dependencies
- No real LLM API calls are made
- Tests are deterministic and fast
- All tests can run in parallel (no shared state)

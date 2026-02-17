# Week 05 测试用例矩阵

本文档总结了 Week 05 (LLM Agent 基础) 的测试用例覆盖情况。

## 测试覆盖概览

| 测试文件 | 测试类 | 测试数量 | 覆盖功能 |
|---------|-------|---------|---------|
| `test_smoke.py` | 4 | 31 | 基础设施、覆盖验证、锚点验证、集成测试 |
| `test_tools.py` | 5 | 50 | 情感分析、关键词提取、词频统计、边界情况、集成测试 |
| `test_function_calling.py` | 5 | 33 | Schema 定义、调用解析、执行、错误处理、LLM 客户端 |
| `test_react_agent.py` | 5 | 32 | ReAct 循环、历史记录、边界情况、消息处理、集成测试 |
| `test_planning_agent.py` | 5 | 24 | 任务分解、计划解析、计划执行、边界情况、继承、集成测试 |
| **总计** | **24** | **170** | - |

## 测试用例详细分类

### 1. 文本分析工具 (`test_tools.py`)

#### 1.1 情感分析 (TestAnalyzeSentiment) - 10 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_positive_sentiment` | 正面文本 | 返回 positive |
| `test_negative_sentiment` | 负面文本 | 返回 negative |
| `test_neutral_sentiment` | 中性文本 | 返回 neutral |
| `test_sentiment_classification` | 多种分类 | 正确分类 |
| `test_sentiment_score_calculation` | 分数计算 | 更多正面词 = 更高分 |
| `test_mixed_sentiment` | 混合情感 | 返回有效分类 |
| `test_sentiment_confidence_range` | 置信度范围 | 0-1 之间 |
| `test_sentiment_reason_format` | 原因格式 | 包含有用信息 |

#### 1.2 关键词提取 (TestExtractKeywords) - 11 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_extract_basic_keywords` | 基本提取 | 返回关键词列表 |
| `test_keywords_sorted_by_frequency` | 排序 | 按频率降序 |
| `test_keywords_top_k_limit` | Top K 限制 | 返回数量 <= top_k |
| `test_keywords_empty_text` | 空文本 | 返回空列表 |
| `test_keywords_whitespace_only` | 仅空白 | 返回空列表 |
| `test_keywords_no_stopwords` | 停用词过滤 | 不包含停用词 |
| `test_keywords_chinese_text` | 中文文本 | 正常工作 |
| `test_keywords_english_mixed` | 中英混合 | 正常工作 |
| `test_keywords_special_chars` | 特殊字符 | 正常工作 |

#### 1.3 词频统计 (TestCountWordFreq) - 10 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_basic_word_frequency` | 基本统计 | 正确计数 |
| `test_word_freq_sorted_descending` | 排序 | 降序排列 |
| `test_word_freq_top_k_limit` | Top K 限制 | 返回数量 <= top_k |
| `test_word_freq_empty_text` | 空文本 | 返回空列表 |
| `test_word_freq_no_stopwords` | 停用词过滤 | 不包含停用词 |
| `test_word_freq_punctuation_filtered` | 标点过滤 | 不包含标点 |
| `test_word_freq_structure` | 结果结构 | 正确的结构 |

#### 1.4 边界情况 (TestToolsEdgeCases) - 14 个测试

- 空输入、空白输入
- 极短/极长输入
- 特殊字符、Unicode
- 多文本批处理

### 2. Function Calling (`test_function_calling.py`)

#### 2.1 工具 Schema (TestToolSchema) - 7 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_tool_definition_creation` | 创建工具定义 | 正确初始化 |
| `test_tool_to_schema_format` | Schema 格式 | OpenAI 风格 |
| `test_schema_has_required_fields` | 必需字段 | 包含所有字段 |
| `test_schema_parameters_structure` | 参数结构 | 正确的参数定义 |
| `test_multiple_tool_schemas` | 多个工具 | 生成多个 Schema |
| `test_tool_names_are_unique` | 唯一名称 | 名称不重复 |

#### 2.2 工具调用解析 (TestToolCallParsing) - 6 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_tool_call_creation` | 创建调用对象 | 正确初始化 |
| `test_llm_response_with_tool_calls` | 包含工具调用 | 返回调用列表 |
| `test_llm_response_without_tool_calls` | 无工具调用 | 返回直接答案 |
| `test_parse_tool_arguments_json` | JSON 参数 | 正确解析 |
| `test_tool_call_with_complex_arguments` | 复杂参数 | 处理嵌套结构 |
| `test_tool_call_with_default_parameters` | 默认参数 | 使用默认值 |

#### 2.3 工具执行 (TestToolExecution) - 6 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_execute_sentiment_tool` | 执行情感分析 | 返回情感结果 |
| `test_execute_keywords_tool` | 执行关键词提取 | 返回关键词 |
| `test_execute_wordfreq_tool` | 执行词频统计 | 返回词频 |
| `test_execute_tool_from_call_object` | 从调用对象执行 | 正确执行 |
| `test_execute_multiple_tools_in_sequence` | 序列执行 | 按顺序执行 |
| `test_execute_tool_with_json_arguments` | JSON 参数执行 | 正确执行 |

#### 2.4 错误处理 (TestToolExecutionErrors) - 6 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_missing_required_parameter` | 缺少必需参数 | 抛出 TypeError |
| `test_invalid_parameter_type` | 无效参数类型 | 处理 gracefully |
| `test_unknown_tool_name` | 未知工具 | 工具不存在 |
| `test_tool_function_raises_exception` | 工具异常 | 抛出异常 |
| `test_empty_arguments` | 空参数 | 抛出 TypeError |
| `test_null_arguments` | Null 参数 | 处理 gracefully |

#### 2.5 LLM 客户端 (TestLLMClientToolCalling) - 5 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_llm_returns_tool_call` | 返回工具调用 | 包含 tool_calls |
| `test_llm_returns_final_answer` | 返回最终答案 | 无 tool_calls |
| `test_llm_tool_call_sequence` | 工具调用序列 | 按顺序返回 |
| `test_llm_message_history_tracking` | 历史记录 | 记录所有消息 |
| `test_llm_reset` | 重置 | 清空历史 |

### 3. ReAct Agent (`test_react_agent.py`)

#### 3.1 ReAct 循环 (TestReAgentLoop) - 7 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_agent_initialization` | Agent 初始化 | 正确配置 |
| `test_agent_run_returns_result` | 运行返回结果 | 包含所有字段 |
| `test_agent_direct_answer_no_tools` | 直接答案 | 无工具调用 |
| `test_agent_with_single_tool_call` | 单个工具调用 | 执行一次 |
| `test_agent_with_multiple_tool_calls` | 多个工具调用 | 执行多次 |
| `test_agent_max_iterations_limit` | 最大迭代限制 | 停止在限制 |
| `test_agent_iteration_count` | 迭代计数 | 正确计数 |
| `test_agent_tool_execution` | 工具执行 | 返回结果 |

#### 3.2 历史记录 (TestReAgentHistory) - 5 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_history_records_action` | 记录动作 | 包含 action |
| `test_history_records_input` | 记录输入 | 包含 input |
| `test_history_records_result` | 记录结果 | 包含 result |
| `test_history_records_iteration_number` | 记录迭代号 | 包含 iteration |
| `test_history_preserves_order` | 保留顺序 | 按时间顺序 |
| `test_history_empty_without_tool_calls` | 空历史 | 无工具调用时为空 |

#### 3.3 边界情况 (TestReAgentEdgeCases) - 11 个测试

- 空任务、极长任务
- 特殊字符
- 未知工具、工具执行错误
- 零/单次最大迭代
- 无工具、连续运行

#### 3.4 集成测试 (TestReAgentIntegration) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_full_thought_action_observation_cycle` | 完整循环 | 完成 ReAct 循环 |
| `test_multi_step_analysis_task` | 多步骤任务 | 执行所有步骤 |
| `test_agent_with_real_tools` | 真实工具 | 使用实际工具 |

### 4. Planning Agent (`test_planning_agent.py`)

#### 4.1 任务分解 (TestTaskDecomposition) - 7 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_planning_agent_creates_plan` | 创建计划 | 生成计划 |
| `test_plan_contains_steps` | 包含步骤 | 多个步骤 |
| `test_plan_for_sentiment_analysis` | 情感分析计划 | 相关计划 |
| `test_plan_for_keyword_extraction` | 关键词计划 | 相关计划 |
| `test_plan_for_complex_task` | 复杂任务计划 | 更长计划 |
| `test_plan_first_flag_true` | plan_first=True | 创建计划 |
| `test_plan_first_flag_false` | plan_first=False | 跳过计划 |

#### 4.2 计划解析 (TestPlanParsing) - 5 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_plan_is_string` | 计划类型 | 字符串 |
| `test_plan_not_empty` | 非空 | 有内容 |
| `test_plan_has_multiple_lines` | 多行 | 至少 2 行 |
| `test_plan_contains_numbered_steps` | 编号步骤 | 包含编号 |

#### 4.3 计划执行 (TestPlanExecution) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_plan_then_execute` | 先计划后执行 | 两者都有 |
| `test_execution_follows_plan_structure` | 执行结构 | 有效结构 |
| `test_execution_with_plan_first` | 带计划执行 | 有计划 |
| `test_execution_without_plan` | 无计划执行 | 无计划 |

#### 4.4 边界情况 (TestPlanningAgentEdgeCases) - 8 个测试

- 空任务、极长任务
- 特殊字符、模糊任务
- 连续计划、无工具
- 各种任务类型

#### 4.5 继承 (TestPlanningAgentInheritance) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_has_react_methods` | 继承方法 | 有 ReAct 方法 |
| `test_overrides_run` | 覆盖 run | 包含 plan |
| `test_has_create_plan_method` | _create_plan | 可调用 |
| `test_uses_parent_execution_logic` | 父类逻辑 | 使用父类执行 |

#### 4.6 集成测试 (TestPlanningAgentIntegration) - 3 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_full_plan_execute_cycle` | 完整循环 | 计划+执行 |
| `test_multi_task_planning` | 多任务 | 每个有计划 |
| `test_plan_influences_execution` | 计划影响执行 | 计划存在 |

## 测试覆盖总结

### 正例 (Happy Path) - ~70%
- 工具正常执行
- Agent 正常运行
- 计划正常创建和执行

### 边界情况 - ~20%
- 空输入、极短/极长输入
- 特殊字符、Unicode
- 最大迭代限制
- 默认参数

### 反例 (Error Cases) - ~10%
- 缺少必需参数
- 未知工具
- 工具执行失败
- 无效参数类型

## 测试命名规范

所有测试遵循 `test_<功能>_<场景>_<预期>` 格式：

```python
# 正例
def test_sentiment_positive_text_returns_positive()

# 边界
def test_keywords_empty_text_returns_empty_list()

# 反例
def test_missing_required_parameter_raises_error()
```

## 运行命令

```bash
# 全部测试
python3 -m pytest chapters/week_05/tests -v

# 特定文件
python3 -m pytest chapters/week_05/tests/test_tools.py -v

# 特定测试类
python3 -m pytest chapters/week_05/tests/test_tools.py::TestAnalyzeSentiment -v

# 特定测试用例
python3 -m pytest chapters/week_05/tests/test_tools.py::TestAnalyzeSentiment::test_positive_sentiment -v
```

# Week 07 测试矩阵

## 概述

Week 07 测试覆盖生产级 LLM 应用的四个核心领域：
1. **成本追踪** (Cost Tracker)
2. **评估系统** (LLM Evaluator)
3. **API 部署** (FastAPI Service)
4. **可观测性** (Observability)

---

## 测试文件结构

```
tests/
├── __init__.py              # 包初始化
├── conftest.py              # Pytest 配置和共享 fixtures
├── test_smoke.py            # 基础烟雾测试
├── test_cost_tracker.py     # 成本追踪测试
├── test_evaluator.py        # 评估器测试
├── test_api.py              # API 服务测试
└── test_observability.py    # 可观测性测试
```

---

## 测试覆盖矩阵

### 1. 成本追踪 (test_cost_tracker.py)

| 测试类别 | 测试名称 | 测试场景 | 预期结果 |
|---------|---------|---------|---------|
| **基础功能** | `test_cost_tracker_initialization` | 初始化成本追踪器 | 成功创建，调用列表为空 |
| **基础功能** | `test_record_single_call` | 记录单次 LLM 调用 | 调用被正确记录 |
| **基础功能** | `test_record_multiple_calls` | 记录多次 LLM 调用 | 所有调用都被记录 |
| **成本计算** | `test_calculate_cost_single_call_gpt4o` | 计算 GPT-4o 成本 | 正确计算 $2.50/M input + $10/M output |
| **成本计算** | `test_calculate_cost_single_call_mini` | 计算 GPT-4o-mini 成本 | 正确计算 $0.15/M input + $0.60/M output |
| **成本汇总** | `test_get_summary_empty_tracker` | 空追踪器获取汇总 | 返回零值汇总 |
| **成本汇总** | `test_get_summary_with_calls` | 有记录时获取汇总 | 返回正确统计 |
| **分组统计** | `test_cost_by_agent_grouping` | 按 Agent 分组统计 | 正确按 agent_name 分组 |
| **边界情况** | `test_zero_tokens` | 零 Token 处理 | 成本为 0 |
| **边界情况** | `test_unknown_model` | 未知模型处理 | 成本为 0 |
| **边界情况** | `test_no_agent_name` | 无 Agent 名称处理 | 分组到 "unknown" |
| **边界情况** | `test_very_large_token_counts` | 大 Token 数 (128K) | 正确计算 |
| **边界情况** | `test_negative_latency` | 负延迟处理 | 记录但标记为异常 |
| **边界情况** | `test_reset_tracker` | 重置追踪器 | 所有数据被清除 |
| **成本对比** | `test_mini_vs_full_cost_savings` | Mini vs Full 成本对比 | Mini 节省 90%+ |
| **成本对比** | `test_agent_cost_distribution` | Agent 成本分布分析 | 正确汇总各 Agent 成本 |
| **延迟指标** | `test_average_latency_calculation` | 平均延迟计算 | 正确计算平均值 |
| **延迟指标** | `test_latency_by_agent_analysis` | 按 Agent 分析延迟 | 正确汇总各 Agent 延迟 |

### 2. 评估系统 (test_evaluator.py)

| 测试类别 | 测试名称 | 测试场景 | 预期结果 |
|---------|---------|---------|---------|
| **基础功能** | `test_evaluator_initialization` | 初始化评估器 | 成功创建 |
| **基础功能** | `test_evaluate_single_test_case` | 评估单个测试用例 | 返回评估结果 |
| **历史记录** | `test_evaluate_single_stores_history` | 单次评估存储历史 | 历史被记录 |
| **批量评估** | `test_evaluate_batch_multiple_cases` | 批量评估多个用例 | 返回批量结果 |
| **批量评估** | `test_evaluate_batch_empty_list` | 空列表批量评估 | 返回零值结果 |
| **指标范围** | `test_faithfulness_score_range` | 忠实度分数范围 | 0-1 之间 |
| **指标范围** | `test_relevancy_score_range` | 相关性分数范围 | 0-1 之间 |
| **指标计算** | `test_average_metrics_calculation` | 平均指标计算 | 正确计算平均值 |
| **完整性** | `test_evaluation_details_completeness` | 评估详情完整性 | 包含所有必需字段 |
| **边界情况** | `test_empty_test_case` | 空测试用例 | 仍返回结果 |
| **边界情况** | `test_very_long_query` | 超长查询 | 正确处理 |
| **边界情况** | `test_special_characters_in_query` | 特殊字符 | 正确处理 |
| **边界情况** | `test_unicode_characters` | Unicode 字符 | 正确处理 |
| **边界情况** | `test_mismatched_query_expected` | 查询与期望不匹配 | 相关性分数降低 |
| **批量处理** | `test_batch_with_varied_quality` | 不同质量的批量 | 返回混合分数 |
| **批量处理** | `test_batch_preserves_case_order` | 保持用例顺序 | 顺序不被改变 |
| **批量处理** | `test_large_batch_evaluation` | 大批量评估 (100) | 正确处理 |
| **验证** | `test_missing_optional_fields` | 缺少可选字段 | 仍可评估 |
| **验证** | `test_all_fields_present` | 所有字段存在 | 元数据被保留 |
| **聚合** | `test_average_faithfulness_calculation` | 平均忠实度计算 | 数学正确 |
| **聚合** | `test_average_relevancy_calculation` | 平均相关性计算 | 数学正确 |

### 3. API 服务 (test_api.py)

| 测试类别 | 测试名称 | 测试场景 | 预期结果 |
|---------|---------|---------|---------|
| **基础端点** | `test_health_endpoint` | /health 健康检查 | 返回 healthy 状态 |
| **基础端点** | `test_analyze_endpoint_with_valid_request` | 有效请求 /analyze | 返回分析结果 |
| **基础端点** | `test_analyze_endpoint_with_minimal_request` | 最小请求 | 使用默认值 |
| **基础端点** | `test_metrics_endpoint` | /metrics 指标端点 | 返回指标数据 |
| **请求验证** | `test_empty_task_rejected` | 空任务被拒绝 | 返回 422 错误 |
| **请求验证** | `test_missing_task_rejected` | 缺少任务字段 | 返回 422 错误 |
| **请求验证** | `test_invalid_enable_review_type` | 无效 enable_review 类型 | 返回 422 错误 |
| **请求验证** | `test_extra_fields_ignored` | 额外字段被忽略 | 请求成功 |
| **错误处理** | `test_service_unavailable_when_not_initialized` | 服务未初始化 | 返回 503 错误 |
| **错误处理** | `test_internal_error_handling` | 内部错误处理 | 返回 500 错误 |
| **边界情况** | `test_very_long_task` | 超长任务描述 | 正确处理 |
| **边界情况** | `test_special_characters_in_task` | 特殊字符 | 正确处理 |
| **边界情况** | `test_unicode_characters` | Unicode 字符 | 正确处理 |
| **边界情况** | `test_concurrent_requests` | 并发请求 (10) | 全部成功 |
| **响应格式** | `test_response_contains_all_fields` | 包含所有必需字段 | 字段完整 |
| **响应格式** | `test_review_field_optional` | review 字段可选 | 正确处理 None |
| **响应格式** | `test_cost_usd_is_numeric` | cost_usd 是数值 | 数值类型且 >= 0 |
| **响应格式** | `test_latency_ms_is_integer` | latency_ms 是整数 | 整数类型且 >= 0 |
| **内容类型** | `test_json_content_type` | JSON 内容类型 | 接受 |
| **内容类型** | `test_form_data_rejected` | 表单数据被拒绝 | 返回 422 |
| **内容类型** | `test_missing_content_type` | 缺少内容类型 | 默认为 JSON |

### 4. 可观测性 (test_observability.py)

| 测试类别 | 测试名称 | 测试场景 | 预期结果 |
|---------|---------|---------|---------|
| **结构化日志** | `test_logger_initialization` | 初始化日志记录器 | 成功创建 |
| **结构化日志** | `test_log_llm_call` | 记录 LLM 调用 | 日志被记录 |
| **结构化日志** | `test_log_agent_execution` | 记录 Agent 执行 | 日志被记录 |
| **结构化日志** | `test_multiple_logs` | 记录多个日志 | 所有日志被记录 |
| **结构化日志** | `test_filter_logs_by_event_type` | 按事件类型过滤 | 正确过滤 |
| **结构化日志** | `test_log_structure_completeness` | 日志结构完整 | 包含所有必需字段 |
| **结构化日志** | `test_clear_logs` | 清除日志 | 日志被清除 |
| **指标收集** | `test_metrics_collector_initialization` | 初始化指标收集器 | 成功创建 |
| **指标收集** | `test_increment_counter` | 增加计数器 | 计数器增加 |
| **指标收集** | `test_counter_with_labels` | 带标签的计数器 | 标签被包含在键中 |
| **指标收集** | `test_counter_multiple_increments` | 多次增加计数器 | 值累加 |
| **指标收集** | `test_observe_histogram` | 观察直方图值 | 值被记录 |
| **指标收集** | `test_set_gauge` | 设置仪表值 | 值被设置 |
| **指标收集** | `test_gauge_overwrites_value` | 仪表值覆盖 | 新值覆盖旧值 |
| **指标收集** | `test_reset_metrics` | 重置指标 | 所有指标被清除 |
| **指标收集** | `test_cost_metric_tracking` | 成本指标追踪 | 成本被记录 |
| **分布式追踪** | `test_trace_context_initialization` | 初始化追踪上下文 | 成功创建，有 trace_id |
| **分布式追踪** | `test_create_span` | 创建 Span | Span 被创建 |
| **分布式追踪** | `test_span_recording` | Span 记录 | 完成后 Span 被记录 |
| **分布式追踪** | `test_span_duration_calculation` | Span 持续时间计算 | 正确计算毫秒数 |
| **分布式追踪** | `test_multiple_spans` | 多个 Span | 所有 Span 被记录 |
| **分布式追踪** | `test_nested_spans` | 嵌套 Span | 顺序记录 |
| **分布式追踪** | `test_trace_total_duration` | Trace 总持续时间 | 正确汇总 |
| **分布式追踪** | `test_span_metadata` | Span 元数据 | 元数据被记录 |
| **分布式追踪** | `test_trace_id_consistency` | Trace ID 一致性 | Trace ID 保持不变 |
| **告警管理** | `test_alert_manager_initialization` | 初始化告警管理器 | 成功创建 |
| **告警管理** | `test_add_alert_rule` | 添加告警规则 | 规则被添加 |
| **告警管理** | `test_alert_triggered` | 告警被触发 | 条件满足时触发 |
| **告警管理** | `test_alert_not_triggered` | 告警不被触发 | 条件不满足时不触发 |
| **告警管理** | `test_multiple_rules` | 多个告警规则 | 正确评估 |
| **告警管理** | `test_multiple_alerts_triggered` | 多个告警同时触发 | 全部触发 |
| **告警管理** | `test_alert_history` | 告警历史 | 历史被记录 |
| **告警管理** | `test_filter_alerts_by_rule` | 按规则过滤告警 | 正确过滤 |
| **告警管理** | `test_clear_alerts` | 清除告警 | 历史被清除 |
| **告警管理** | `test_alert_timestamp` | 告警时间戳 | 包含正确时间 |
| **告警管理** | `test_alert_includes_metrics` | 告警包含指标 | 触发指标被记录 |
| **集成** | `test_end_to_end_observability_flow` | 端到端可观测性流程 | 所有组件协同工作 |
| **集成** | `test_correlation_between_logs_and_traces` | 日志与追踪关联 | 通过 trace_id 关联 |

### 5. 烟雾测试 (test_smoke.py)

| 测试名称 | 测试场景 | 预期结果 |
|---------|---------|---------|
| `test_cost_tracker_exists` | 成本追踪器可用 | 可导入和使用 |
| `test_evaluator_exists` | 评估器可用 | 可导入和使用 |
| `test_logger_exists` | 日志记录器可用 | 可导入和使用 |
| `test_metrics_collector_exists` | 指标收集器可用 | 可导入和使用 |
| `test_trace_context_exists` | 追踪上下文可用 | 可导入和使用 |
| `test_alert_manager_exists` | 告警管理器可用 | 可导入和使用 |
| `test_cache_exists` | 缓存可用 | 可导入和使用 |
| `test_model_selector_exists` | 模型选择器可用 | 可导入和使用 |
| `test_prompt_optimizer_exists` | Prompt 优化器可用 | 可导入和使用 |
| `test_integration_basic_flow` | 基本集成流程 | 所有组件协同工作 |
| `test_pricing_data_available` | 定价数据可用 | 价格数据完整 |
| `test_cost_calculation_accuracy` | 成本计算准确性 | 数学正确 |
| `test_all_fixtures_work` | 所有 fixtures 可用 | Pytest 注入成功 |

---

## 运行测试

### 运行所有测试
```bash
python3 -m pytest chapters/week_07/tests -q
```

### 运行特定测试文件
```bash
python3 -m pytest chapters/week_07/tests/test_cost_tracker.py -q
python3 -m pytest chapters/week_07/tests/test_evaluator.py -q
python3 -m pytest chapters/week_07/tests/test_api.py -q
python3 -m pytest chapters/week_07/tests/test_observability.py -q
```

### 运行烟雾测试
```bash
python3 -m pytest chapters/week_07/tests/test_smoke.py -q
```

### 运行特定测试类
```bash
python3 -m pytest chapters/week_07/tests/test_cost_tracker.py::TestCostTrackerBasics -q
```

### 运行特定测试用例
```bash
python3 -m pytest chapters/week_07/tests/test_cost_tracker.py::TestCostTrackerBasics::test_cost_tracker_initialization -q
```

### 带详细输出
```bash
python3 -m pytest chapters/week_07/tests -v
```

### 带覆盖率报告
```bash
python3 -m pytest chapters/week_07/tests --cov=chapters/week_07 --cov-report=html
```

---

## Fixtures 列表

### 从 `conftest.py` 导入的 Fixtures

| Fixture 名称 | 类型 | 描述 |
|-------------|------|------|
| `mock_cost_tracker` | MockCostTracker | 模拟成本追踪器 |
| `mock_llm_evaluator` | MockLLMEvaluator | 模拟 LLM 评估器 |
| `mock_llm_client` | MockLLMClient | 模拟 LLM 客户端 |
| `mock_model_selector` | MockModelSelector | 模拟模型选择器 |
| `mock_prompt_optimizer` | MockPromptOptimizer | 模拟 Prompt 优化器 |
| `mock_semantic_cache` | MockSemanticCache | 模拟语义缓存 |
| `mock_structured_logger` | MockStructuredLogger | 模拟结构化日志记录器 |
| `mock_metrics_collector` | MockMetricsCollector | 模拟指标收集器 |
| `mock_trace_context` | MockTraceContext | 模拟追踪上下文 |
| `mock_alert_manager` | MockAlertManager | 模拟告警管理器 |
| `sample_llm_metrics` | List[LLMMetrics] | 示例 LLM 指标列表 |
| `sample_test_cases` | List[TestCase] | 示例测试用例列表 |
| `sample_api_requests` | Dict | 示例 API 请求 |
| `sample_pricing` | Dict | 示例定价数据 |
| `sample_alert_rules` | List[Dict] | 示例告警规则 |
| `agent_config` | Dict | Agent 配置 |
| `production_metrics` | Dict | 生产环境指标 |
| `healthy_metrics` | Dict | 健康指标 |

---

## 测试统计

| 测试文件 | 测试类数 | 测试用例数 |
|---------|---------|-----------|
| `test_cost_tracker.py` | 4 | 18 |
| `test_evaluator.py` | 6 | 22 |
| `test_api.py` | 6 | 27 |
| `test_observability.py` | 5 | 48 |
| `test_smoke.py` | 1 | 13 |
| **总计** | **22** | **128** |

---

## 反例场景说明

Week 07 的测试主要针对"可验证"的正例和边界场景。以下是不适用反例的场景说明：

1. **成本追踪**: 所有输入都被记录，"错误输入"通常只是数据质量问题，不影响记录功能
2. **评估器**: 即使空输入也会返回结果（低分），不会拒绝评估
3. **API 服务**: FastAPI 的 Pydantic 模型会自动验证并返回 422 错误，这是框架行为而非业务逻辑
4. **可观测性**: 日志/指标/追踪是"尽力而为"系统，通常会记录所有输入而不拒绝

因此，本测试套件的反例主要集中在 API 的输入验证（由 Pydantic 处理）。

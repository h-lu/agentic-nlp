# Week 06 测试用例矩阵

本文档总结了 Week 06 (多智能体系统与 Agentic RAG) 的测试用例覆盖情况。

## 测试覆盖概览

| 测试文件 | 测试类 | 测试数量 | 覆盖功能 |
|---------|-------|---------|---------|
| `test_smoke.py` | 4 | 39 | 基础设施、覆盖验证、锚点验证、集成测试 |
| `test_planner_executor.py` | 7 | 36 | 规划者-执行者模式、计划创建、计划执行、集成测试 |
| `test_agent_communication.py` | 6 | 26 | Agent 通信、消息总线、状态跟踪、边界情况 |
| `test_agentic_rag.py` | 6 | 30 | Agentic RAG、检索策略、结果评估、集成测试 |
| `test_human_in_loop.py` | 6 | 22 | Human-in-the-Loop、审批流程、反馈处理、边界情况 |
| **总计** | **29** | **153** | - |

## 测试用例详细分类

### 1. 规划者-执行者模式 (`test_planner_executor.py`)

#### 1.1 规划者 Agent 创建 (TestPlannerAgentCreation) - 2 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_planner_agent_can_be_created` | 创建规划者 | 正确初始化 |
| `test_planner_agent_has_required_methods` | 检查方法 | 有 create_plan, revise_plan |

#### 1.2 计划创建 (TestPlanCreation) - 6 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_create_plan_returns_valid_plan` | 创建计划 | 返回有效 ExecutionPlan |
| `test_create_plan_for_sentiment_analysis` | 情感分析任务 | 相关计划 |
| `test_create_plan_for_keyword_extraction` | 关键词提取任务 | 相关计划 |
| `test_create_plan_for_complex_task` | 复杂任务 | 更多子任务 |
| `test_create_plan_stores_last_plan` | 存储最后计划 | 记录已创建 |
| `test_plan_subtasks_have_correct_structure` | 子任务结构 | 正确的结构 |

#### 1.3 计划修订 (TestPlanRevision) - 3 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_revise_plan_modifies_original_plan` | 修订计划 | 创建修改版本 |
| `test_revise_plan_adds_revision_step` | 添加修订步骤 | 增加子任务 |
| `test_revise_plan_preserves_expected_output` | 保留期望输出 | 输出不变 |

#### 1.4 执行者 Agent 创建 (TestExecutorAgentCreation) - 2 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_executor_agent_can_be_created` | 创建执行者 | 正确初始化 |
| `test_executor_agent_has_required_methods` | 检查方法 | 有 execute_plan |

#### 1.5 计划执行 (TestPlanExecution) - 5 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_execute_plan_returns_valid_result` | 执行计划 | 返回有效结果 |
| `test_execute_plan_with_valid_tools` | 使用有效工具 | 工具正确执行 |
| `test_execute_plan_records_execution_history` | 记录历史 | 历史被记录 |
| `test_execute_plan_with_multiple_subtasks` | 多子任务 | 按顺序执行 |
| `test_execute_plan_result_structure` | 结果结构 | 正确的结构 |

#### 1.6 集成测试 (TestPlannerExecutorIntegration) - 1 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_full_planner_executor_cycle` | 完整循环 | 计划→执行 |

#### 1.7 边界情况 (TestPlannerExecutorEdgeCases) - 8 个测试

- 空任务、极长任务
- 空计划、复杂计划
- 特殊字符
- 工具异常处理
- Unicode 支持

#### 1.8 错误情况 (TestPlannerExecutorErrorCases) - 1 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_subtask_with_missing_params` | 缺少参数 | 正确处理 |

### 2. Agent 通信 (`test_agent_communication.py`)

#### 2.1 消息创建 (TestMessageCreation) - 6 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_agent_message_can_be_created` | 创建消息 | 正确初始化 |
| `test_agent_message_default_status` | 默认状态 | PENDING |
| `test_agent_message_timestamp_auto_generated` | 时间戳自动生成 | 时间递增 |
| `test_agent_message_with_custom_timestamp` | 自定义时间戳 | 使用自定义值 |
| `test_agent_message_content_types` | 不同内容类型 | 支持多种类型 |
| `test_agent_message_with_plan_content` | 计划作为内容 | 正确序列化 |

#### 2.2 消息总线 (TestMessageBus) - 7 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_message_bus_can_be_created` | 创建总线 | 正确初始化 |
| `test_message_bus_send_returns_true` | 发送消息 | 返回成功 |
| `test_message_bus_send_updates_message_status` | 更新状态 | DELIVERED |
| `test_message_bus_stores_sent_messages` | 存储消息 | 消息被存储 |
| `test_message_bus_receive_by_receiver` | 按接收者接收 | 返回相关消息 |
| `test_message_bus_receive_empty_for_unknown_receiver` | 未知接收者 | 返回空列表 |
| `test_message_bus_get_status_by_message_id` | 获取状态 | 返回正确状态 |

#### 2.3 Agent 消息传递 (TestAgentMessaging) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_executor_receives_plan_from_planner` | 规划者→执行者 | 消息传递 |
| `test_executor_sends_result_to_reviewer` | 执行者→审核者 | 消息传递 |
| `test_reviewer_sends_feedback_to_planner` | 审核者→规划者 | 消息传递 |
| `test_multi_agent_communication_chain` | 完整通信链 | 按顺序传递 |

#### 2.4 边界情况 (TestCommunicationEdgeCases) - 8 个测试

- 空消息、超大消息
- 特殊字符、Unicode
- 多消息、广播
- 消息顺序、并发

#### 2.5 状态跟踪 (TestMessageStatusTracking) - 3 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_message_status_transitions` | 状态转换 | PENDING→DELIVERED |
| `test_get_status_for_all_sent_messages` | 所有消息状态 | 全部可查询 |
| `test_message_status_after_failed_delivery` | 失败状态 | FAILED |

### 3. Agentic RAG (`test_agentic_rag.py`)

#### 3.1 检索 Agent 创建 (TestRetrieverAgentCreation) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_retriever_agent_can_be_created` | 创建 Agent | 正确初始化 |
| `test_retriever_agent_with_vector_store` | 自定义向量存储 | 使用自定义存储 |
| `test_retriever_agent_with_keyword_index` | 自定义关键词索引 | 使用自定义索引 |
| `test_retriever_agent_has_required_methods` | 检查方法 | 有必需方法 |

#### 3.2 检索策略 (TestRetrievalStrategy) - 6 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_strategy_for_simple_query` | 简单查询 | vector 策略 |
| `test_strategy_for_complex_query` | 复杂查询 | hybrid 策略 |
| `test_strategy_for_empty_query` | 空查询 | 正确处理 |
| `test_strategy_includes_reasoning` | 包含推理 | 有 reasoning |
| `test_strategy_to_dict` | 序列化 | 正确转换 |
| `test_different_strategies_for_different_queries` | 不同查询 | 不同策略 |

#### 3.3 检索执行 (TestRetrievalExecution) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_retrieve_returns_valid_result` | 检索 | 返回有效结果 |
| `test_retrieve_with_custom_top_k` | 自定义 top_k | 使用自定义值 |
| `test_retrieve_records_history` | 记录历史 | 历史被记录 |
| `test_retrieve_result_structure` | 结果结构 | 正确的结构 |

#### 3.4 结果评估 (TestResultAssessment) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_assess_results_with_valid_results` | 有效结果 | sufficient=True |
| `test_assess_results_with_empty_results` | 空结果 | sufficient=False |
| `test_assess_confidence_range` | 置信度范围 | 0-1 之间 |
| `test_assess_includes_result_count` | 结果计数 | 包含计数 |

#### 3.5 集成测试 (TestAgenticRAGIntegration) - 2 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_retriever_in_workflow` | 工作流中 | 检索工作 |
| `test_agentic_rag_decision_flow` | 完整流程 | 策略→检索→评估 |

#### 3.6 边界情况 (TestAgenticRAGEdgeCases) - 8 个测试

- 空查询、极长查询
- 特殊字符、Unicode
- top_k=0、负数、极大值
- None 结果、格式错误

#### 3.7 错误情况 (TestAgenticRAGErrorCases) - 1 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_concurrent_retrievals` | 并发检索 | 全部完成 |

### 4. Human-in-the-Loop (`test_human_in_loop.py`)

#### 4.1 人工审核创建 (TestHumanReviewCreation) - 4 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_review_report_can_be_created` | 创建报告 | 正确初始化 |
| `test_review_report_with_rejection` | 拒绝状态 | needs_revision |
| `test_review_report_to_dict` | 序列化 | 正确转换 |
| `test_review_report_statuses` | 不同状态 | approved/needs_revision |

#### 4.2 审批流程 (TestApprovalFlow) - 2 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_approve_at_plan_stage` | 计划阶段审批 | 继续执行 |
| `test_approve_at_execution_stage` | 执行阶段审批 | 确认完成 |

#### 4.3 拒绝流程 (TestRejectionFlow) - 2 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_reject_at_plan_stage` | 计划阶段拒绝 | 修订计划 |
| `test_rejection_with_revision_cycle` | 修订循环 | 循环到批准 |

#### 4.4 反馈处理 (TestFeedbackHandling) - 5 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_feedback_with_revisions` | 多次修订 | 累积修订 |
| `test_feedback_with_empty_string` | 空反馈 | 正确处理 |
| `test_feedback_with_special_characters` | 特殊字符 | 正确处理 |
| `test_feedback_with_multiple_suggestions` | 多条建议 | 正确处理 |
| `test_feedback_preserves_plan_structure` | 保留结构 | 核心结构不变 |

#### 4.5 边界情况 (TestHumanInLoopEdgeCases) - 6 个测试

- 超时处理
- 无响应
- 无效输入
- 多轮审核
- 并发审核
- Unicode 反馈

#### 4.6 错误情况 (TestHumanInLoopErrorCases) - 3 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_review_with_none_feedback` | None 反馈 | 正确处理 |
| `test_review_with_malformed_feedback` | 格式错误反馈 | 正确处理 |
| `test_approval_after_max_revisions` | 超过最大修订 | 仍可工作 |

#### 4.7 集成测试 (TestHumanInLoopIntegration) - 3 个测试

| 测试用例 | 场景 | 预期结果 |
|---------|------|---------|
| `test_full_workflow_with_human_intervention` | 完整工作流 | 各阶段审核 |
| `test_human_decision_affects_workflow` | 决策影响 | 影响后续流程 |
| `test_human_feedback_accumulation` | 反馈累积 | 记录所有反馈 |

## 测试覆盖总结

### 正例 (Happy Path) - ~65%
- 正常的 Agent 创建和初始化
- 正常的计划创建和执行
- 正常的消息传递
- 正常的检索和评估
- 正常的审批流程

### 边界情况 - ~25%
- 空输入、极短/极长输入
- 特殊字符、Unicode
- 并发操作
- 超时处理

### 反例 (Error Cases) - ~10%
- None 输入处理
- 格式错误处理
- 工具异常处理
- 缺少参数

## 测试命名规范

所有测试遵循 `test_<功能>_<场景>_<预期>` 格式：

```python
# 正例
def test_planner_creates_plan_for_sentiment_analysis()

# 边界
def test_executor_handles_empty_plan()

# 反例
def test_retriever_handles_none_results_gracefully()
```

## 运行命令

```bash
# 全部测试
python3 -m pytest chapters/week_06/tests -v

# 特定文件
python3 -m pytest chapters/week_06/tests/test_planner_executor.py -v

# 特定测试类
python3 -m pytest chapters/week_06/tests/test_planner_executor.py::TestPlanCreation -v

# 特定测试用例
python3 -m pytest chapters/week_06/tests/test_planner_executor.py::TestPlanCreation::test_create_plan_returns_valid_plan -v
```

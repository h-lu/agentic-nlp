# Week 06 Tests

Tests for Week 06 (Multi-Agent Systems and Agentic RAG).

## 测试文件

| 文件 | 描述 | 测试数 |
|------|------|-------|
| `test_smoke.py` | 基础设施和覆盖验证 | 39 |
| `test_planner_executor.py` | 规划者-执行者模式测试 | 36 |
| `test_agent_communication.py` | Agent 通信测试 | 26 |
| `test_agentic_rag.py` | Agentic RAG 测试 | 30 |
| `test_human_in_loop.py` | Human-in-the-Loop 测试 | 22 |

## 快速开始

```bash
# 运行所有测试
python3 -m pytest chapters/week_06/tests -v

# 运行特定文件
python3 -m pytest chapters/week_06/tests/test_planner_executor.py -v

# 查看测试覆盖率
python3 -m pytest chapters/week_06/tests --cov=chapters.week_06.tests.conftest
```

## 测试类别

### 1. 规划者-执行者模式
测试多智能体系统中规划者 Agent 和执行者 Agent 的协作：
- 计划创建和修订
- 计划执行
- 工具调用
- 历史记录

### 2. Agent 通信
测试 Agent 之间的消息传递机制：
- 消息创建和验证
- 消息总线
- 状态跟踪
- 并发处理

### 3. Agentic RAG
测试 Agent 自主控制的检索系统：
- 检索策略选择
- 结果评估
- 重试机制
- 工作流集成

### 4. Human-in-the-Loop
测试人工审核和反馈机制：
- 审批流程
- 拒绝和修订
- 反馈处理
- 超时处理

## Fixtures

主要 fixtures 在 `conftest.py` 中定义：

- `sample_tools`: 示例工具字典
- `mock_llm_client`: Mock LLM 客户端
- `planner_agent`: 规划者 Agent
- `executor_agent`: 执行者 Agent
- `reviewer_agent`: 审核者 Agent
- `retriever_agent`: 检索 Agent
- `message_bus`: 消息总线
- `sample_tasks`: 示例任务
- `sample_queries`: 示例查询
- `sample_plans`: 示例计划
- `agent_workflow`: 完整 Agent 工作流

## 贡献

添加新测试时请遵循：
1. 使用清晰的测试命名：`test_<功能>_<场景>_<预期>`
2. 包含正例、边界和反例
3. 使用 mock 隔离外部依赖
4. 添加适当的文档字符串

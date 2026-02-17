"""
测试端到端系统架构

测试模块：
- WorkflowOrchestrator
- TaskContext
- Agent 和 Capability 的实现
"""

import pytest
from typing import Dict, Any

from architecture import (
    TaskContext,
    WorkflowOrchestrator,
    MockAgent,
    MockPlannerAgent,
    MockExecutorAgent,
    MockRetrieverAgent,
    MockReviewerAgent,
    MockCapability,
    create_mock_orchestrator
)


class TestTaskContext:
    """测试 TaskContext"""

    def test_task_context_creation(self):
        """测试创建 TaskContext"""
        context = TaskContext(
            task_id="test-123",
            user_input="测试输入",
            metadata={"key": "value"},
            state={"initial": True}
        )

        assert context.task_id == "test-123"
        assert context.user_input == "测试输入"
        assert context.metadata == {"key": "value"}
        assert context.state == {"initial": True}

    def test_task_context_with_defaults(self):
        """测试使用默认值创建 TaskContext"""
        context = TaskContext(
            task_id="test-456",
            user_input="测试"
        )

        assert context.metadata == {}
        assert context.state == {}

    def test_task_context_state_mutation(self):
        """测试 TaskContext 状态可以修改"""
        context = TaskContext(
            task_id="test-789",
            user_input="测试"
        )

        context.state["plan"] = {"steps": ["analyze"]}
        context.state["result"] = {"output": "done"}

        assert "plan" in context.state
        assert "result" in context.state


class TestWorkflowOrchestrator:
    """测试 WorkflowOrchestrator"""

    @pytest.fixture
    def orchestrator(self):
        """创建测试用的 Orchestrator"""
        return create_mock_orchestrator()

    def test_orchestrator_initialization(self, orchestrator):
        """测试 Orchestrator 初始化"""
        assert orchestrator.agents is not None
        assert orchestrator.capabilities is not None
        assert "planner" in orchestrator.agents
        assert "executor" in orchestrator.agents
        assert "retriever" in orchestrator.agents
        assert "reviewer" in orchestrator.agents

    def test_orchestrator_run_basic(self, orchestrator):
        """测试基本运行流程"""
        result = orchestrator.run("分析这份数据")

        assert "task_id" in result
        assert "result" in result
        assert "review" in result
        assert "cost_usd" in result
        assert "latency_ms" in result
        assert result["task_id"] is not None
        assert result["cost_usd"] >= 0

    def test_orchestrator_task_id_unique(self, orchestrator):
        """测试每次运行生成不同的任务 ID"""
        result1 = orchestrator.run("测试1")
        result2 = orchestrator.run("测试2")

        assert result1["task_id"] != result2["task_id"]

    def test_orchestrator_with_retrieval(self, orchestrator):
        """测试需要检索的流程"""
        result = orchestrator.run("检索相关文档")

        assert "result" in result
        # 检索流程应该包含 retrieval 状态

    def test_orchestrator_with_review(self, orchestrator):
        """测试需要审核的流程"""
        result = orchestrator.run("审核这个结果")

        assert "review" in result
        assert result["review"] is not None

    def test_orchestrator_empty_input(self, orchestrator):
        """测试空输入"""
        result = orchestrator.run("")

        assert "task_id" in result
        assert "result" in result

    def test_orchestrator_with_special_characters(self, orchestrator):
        """测试包含特殊字符的输入"""
        special_inputs = [
            "测试\n换行",
            "测试\t制表符",
            "测试\"引号\"",
            "测试'单引号'",
            "测试\\反斜杠",
            "测试中文和English混合",
            "测试emoji 🎉"
        ]

        for input_text in special_inputs:
            result = orchestrator.run(input_text)
            assert "task_id" in result
            assert "result" in result


class TestMockAgent:
    """测试 Mock Agent 实现"""

    def test_planner_agent_plan(self):
        """测试规划 Agent 的 plan 方法"""
        agent = MockPlannerAgent()
        context = TaskContext(
            task_id="test",
            user_input="分析数据"
        )

        plan = agent.plan(context)

        assert "need_retrieval" in plan
        assert "enable_review" in plan
        assert "steps" in plan

    def test_planner_agent_detects_retrieval_need(self):
        """测试规划 Agent 能检测到需要检索"""
        agent = MockPlannerAgent()

        context_with_retrieval = TaskContext(
            task_id="test",
            user_input="检索相关文档"
        )
        plan = agent.plan(context_with_retrieval)
        assert plan["need_retrieval"] is True

        context_without_retrieval = TaskContext(
            task_id="test",
            user_input="简单分析"
        )
        plan = agent.plan(context_without_retrieval)
        assert plan["need_retrieval"] is False

    def test_executor_agent_execute(self):
        """测试执行 Agent 的 execute 方法"""
        agent = MockExecutorAgent()
        context = TaskContext(
            task_id="test",
            user_input="执行任务"
        )
        plan = {"steps": ["execute"]}

        result = agent.execute(context, plan)

        assert "status" in result
        assert "output" in result
        assert result["status"] == "completed"

    def test_executor_adds_metrics(self):
        """测试执行 Agent 添加成本和延迟指标"""
        agent = MockExecutorAgent()
        context = TaskContext(
            task_id="test",
            user_input="执行"
        )
        plan = {}

        agent.execute(context, plan)

        assert "cost_usd" in context.state
        assert "latency_ms" in context.state

    def test_retriever_agent_retrieve(self):
        """测试检索 Agent 的 retrieve 方法"""
        agent = MockRetrieverAgent()
        context = TaskContext(
            task_id="test",
            user_input="检索"
        )

        result = agent.retrieve(context)

        assert "status" in result
        assert "documents" in result

    def test_reviewer_agent_review(self):
        """测试审核 Agent 的 review 方法"""
        agent = MockReviewerAgent()
        context = TaskContext(
            task_id="test",
            user_input="审核"
        )
        execution_result = {"output": "done"}

        result = agent.review(context, execution_result)

        assert "status" in result
        assert "confidence" in result


class TestCapability:
    """测试 Capability 接口"""

    def test_mock_capability_execute(self):
        """测试 Mock Capability 的 execute 方法"""
        capability = MockCapability()
        context = TaskContext(
            task_id="test",
            user_input="测试"
        )

        result = capability.execute(context)

        assert "status" in result
        assert "data" in result
        assert result["status"] == "success"


class TestOrchestratorIntegration:
    """集成测试"""

    @pytest.fixture
    def custom_orchestrator(self):
        """创建自定义配置的 Orchestrator"""
        agents = {
            "planner": MockPlannerAgent(),
            "executor": MockExecutorAgent(),
            "retriever": MockRetrieverAgent(),
            "reviewer": MockReviewerAgent()
        }

        capabilities = {
            "custom_capability": MockCapability()
        }

        return WorkflowOrchestrator(agents, capabilities)

    def test_full_workflow_without_review(self, custom_orchestrator):
        """测试不带审核的完整工作流"""
        result = custom_orchestrator.run("简单任务")

        assert result["task_id"] is not None
        assert result["result"]["status"] == "completed"
        assert result["review"] is None  # 没有启用审核

    def test_full_workflow_with_review(self, custom_orchestrator):
        """测试带审核的完整工作流"""
        result = custom_orchestrator.run("审核这个任务")

        assert result["task_id"] is not None
        assert result["result"]["status"] == "completed"
        assert result["review"] is not None  # 有审核结果
        assert result["review"]["status"] == "approved"

    def test_cost_tracking(self, custom_orchestrator):
        """测试成本追踪"""
        result = custom_orchestrator.run("任何任务")

        assert result["cost_usd"] >= 0

    def test_latency_tracking(self, custom_orchestrator):
        """测试延迟追踪"""
        result = custom_orchestrator.run("任何任务")

        assert result["latency_ms"] >= 0


@pytest.mark.parametrize("user_input,expected_need_retrieval,expected_enable_review", [
    ("简单任务", False, False),
    ("检索文档", True, False),
    ("审核结果", False, True),
    ("检索并审核", True, True),
    ("search documents", True, False),
    ("review this", False, True),
])
def test_planner_intent_detection(user_input, expected_need_retrieval, expected_enable_review):
    """参数化测试：规划 Agent 的意图检测"""
    agent = MockPlannerAgent()
    context = TaskContext(
        task_id="test",
        user_input=user_input
    )

    plan = agent.plan(context)

    assert plan["need_retrieval"] == expected_need_retrieval
    assert plan["enable_review"] == expected_enable_review

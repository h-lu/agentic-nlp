"""
Smoke tests for Week 06 test infrastructure.

Basic tests to verify the testing environment is working correctly.
"""

import pytest


class TestWeek06TestInfrastructure:
    """Basic infrastructure tests."""

    def test_conftest_imports(self):
        """Test that conftest fixtures can be imported."""
        from .conftest import (
            AgentRole,
            MessageStatus,
            AgentMessage,
            SubTask,
            ExecutionPlan,
            ExecutionResult,
            ReviewReport,
            RetrievalStrategy,
            RetrievalResult,
            TextAnalyzerTools,
            MockVectorStore,
            MockKeywordIndex,
            MockLLMClient,
            PlannerAgent,
            ExecutorAgent,
            ReviewerAgent,
            RetrieverAgent,
            MessageBus,
        )

        assert AgentRole is not None
        assert MessageStatus is not None
        assert AgentMessage is not None
        assert SubTask is not None
        assert ExecutionPlan is not None
        assert ExecutionResult is not None
        assert ReviewReport is not None
        assert RetrievalStrategy is not None
        assert RetrievalResult is not None
        assert TextAnalyzerTools is not None
        assert MockVectorStore is not None
        assert MockKeywordIndex is not None
        assert MockLLMClient is not None
        assert PlannerAgent is not None
        assert ExecutorAgent is not None
        assert ReviewerAgent is not None
        assert RetrieverAgent is not None
        assert MessageBus is not None

    def test_agent_role_enum(self):
        """Test AgentRole enum works."""
        from .conftest import AgentRole

        assert AgentRole.PLANNER.value == "planner"
        assert AgentRole.EXECUTOR.value == "executor"
        assert AgentRole.REVIEWER.value == "reviewer"
        assert AgentRole.RETRIEVER.value == "retriever"

    def test_message_status_enum(self):
        """Test MessageStatus enum works."""
        from .conftest import MessageStatus

        assert MessageStatus.PENDING.value == "pending"
        assert MessageStatus.DELIVERED.value == "delivered"
        assert MessageStatus.FAILED.value == "failed"
        assert MessageStatus.TIMEOUT.value == "timeout"

    def test_agent_message_creation(self):
        """Test AgentMessage can be created."""
        from .conftest import AgentMessage

        msg = AgentMessage(
            sender="planner",
            receiver="executor",
            content={"task": "test"},
            message_id="msg_1"
        )

        assert msg.sender == "planner"
        assert msg.receiver == "executor"
        assert msg.content == {"task": "test"}
        assert msg.message_id == "msg_1"

    def test_subtask_creation(self):
        """Test SubTask can be created."""
        from .conftest import SubTask

        subtask = SubTask(
            step=1,
            action="分析",
            tool="analyze_sentiment",
            params={"text": "test"}
        )

        assert subtask.step == 1
        assert subtask.action == "分析"
        assert subtask.tool == "analyze_sentiment"
        assert subtask.params == {"text": "test"}

    def test_execution_plan_creation(self):
        """Test ExecutionPlan can be created."""
        from .conftest import ExecutionPlan, SubTask

        plan = ExecutionPlan(
            task_understanding="分析任务",
            subtasks=[
                SubTask(step=1, action="加载", tool="load", params={})
            ],
            expected_output="结果"
        )

        assert plan.task_understanding == "分析任务"
        assert len(plan.subtasks) == 1
        assert plan.expected_output == "结果"

    def test_execution_plan_to_dict(self):
        """Test ExecutionPlan.to_dict() works."""
        from .conftest import ExecutionPlan, SubTask

        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[SubTask(step=1, action="测试", tool="test", params={})],
            expected_output="输出"
        )

        plan_dict = plan.to_dict()
        assert "task_understanding" in plan_dict
        assert "subtasks" in plan_dict
        assert "expected_output" in plan_dict

    def test_execution_result_creation(self):
        """Test ExecutionResult can be created."""
        from .conftest import ExecutionResult, ExecutionPlan, SubTask

        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[],
            expected_output="输出"
        )

        result = ExecutionResult(
            plan=plan,
            results=[],
            status="completed"
        )

        assert result.plan == plan
        assert result.results == []
        assert result.status == "completed"

    def test_review_report_creation(self):
        """Test ReviewReport can be created."""
        from .conftest import ReviewReport

        report = ReviewReport(
            status="approved",
            issues=[],
            final_answer="任务完成"
        )

        assert report.status == "approved"
        assert report.issues == []
        assert report.final_answer == "任务完成"

    def test_retrieval_strategy_creation(self):
        """Test RetrievalStrategy can be created."""
        from .conftest import RetrievalStrategy

        strategy = RetrievalStrategy(
            method="vector",
            top_k=5,
            reasoning="简单查询"
        )

        assert strategy.method == "vector"
        assert strategy.top_k == 5
        assert strategy.reasoning == "简单查询"

    def test_retrieval_result_creation(self):
        """Test RetrievalResult can be created."""
        from .conftest import RetrievalResult, RetrievalStrategy

        strategy = RetrievalStrategy(method="vector", top_k=5)
        result = RetrievalResult(
            query="测试查询",
            results=[],
            strategy=strategy,
            assessment={"sufficient": True}
        )

        assert result.query == "测试查询"
        assert result.strategy == strategy

    def test_text_analyzer_tools_sentiment(self):
        """Test TextAnalyzerTools.analyze_sentiment works."""
        from .conftest import TextAnalyzerTools

        result = TextAnalyzerTools.analyze_sentiment("很好，满意")

        assert "sentiment" in result
        assert "score" in result
        assert result["sentiment"] == "positive"

    def test_text_analyzer_tools_keywords(self):
        """Test TextAnalyzerTools.extract_keywords works."""
        from .conftest import TextAnalyzerTools

        result = TextAnalyzerTools.extract_keywords("产品质量很好")

        assert "keywords" in result
        assert "counts" in result

    def test_text_analyzer_tools_wordfreq(self):
        """Test TextAnalyzerTools.count_word_freq works."""
        from .conftest import TextAnalyzerTools

        result = TextAnalyzerTools.count_word_freq("物流 物流 质量")

        assert "top_words" in result

    def test_mock_vector_store_creation(self):
        """Test MockVectorStore can be created."""
        from .conftest import MockVectorStore

        store = MockVectorStore()
        assert hasattr(store, "documents")
        assert hasattr(store, "search")

    def test_mock_vector_store_search(self):
        """Test MockVectorStore.search works."""
        from .conftest import MockVectorStore

        store = MockVectorStore()
        result = store.search("产品质量", top_k=3)

        assert "query" in result
        assert "results" in result
        assert "total" in result

    def test_mock_keyword_index_creation(self):
        """Test MockKeywordIndex can be created."""
        from .conftest import MockKeywordIndex

        index = MockKeywordIndex()
        assert hasattr(index, "index")
        assert hasattr(index, "search")

    def test_mock_llm_client_creation(self):
        """Test MockLLMClient can be created."""
        from .conftest import MockLLMClient

        client = MockLLMClient()
        assert client.call_count == 0
        assert client.message_history == []

    def test_mock_llm_client_chat(self):
        """Test MockLLMClient.chat works."""
        from .conftest import MockLLMClient

        client = MockLLMClient()
        response = client.chat([{"role": "user", "content": "测试"}])

        assert "content" in response
        assert client.call_count == 1

    def test_planner_agent_creation(self):
        """Test PlannerAgent can be created."""
        from .conftest import PlannerAgent

        agent = PlannerAgent()
        assert agent.role.value == "planner"
        assert hasattr(agent, "create_plan")

    def test_planner_agent_create_plan(self):
        """Test PlannerAgent.create_plan works."""
        from .conftest import PlannerAgent

        agent = PlannerAgent()
        plan = agent.create_plan("分析情感")

        assert plan.task_understanding is not None
        assert len(plan.subtasks) > 0

    def test_executor_agent_creation(self):
        """Test ExecutorAgent can be created."""
        from .conftest import ExecutorAgent

        agent = ExecutorAgent(tools={})
        assert agent.role.value == "executor"
        assert hasattr(agent, "execute_plan")

    def test_executor_agent_execute_plan(self):
        """Test ExecutorAgent.execute_plan works."""
        from .conftest import ExecutorAgent, ExecutionPlan, SubTask

        agent = ExecutorAgent(tools={})
        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[SubTask(step=1, action="测试", tool="test", params={})],
            expected_output="输出"
        )

        result = agent.execute_plan(plan)
        assert result.status == "completed"
        assert len(result.results) == 1

    def test_reviewer_agent_creation(self):
        """Test ReviewerAgent can be created."""
        from .conftest import ReviewerAgent

        agent = ReviewerAgent()
        assert agent.role.value == "reviewer"
        assert hasattr(agent, "review_result")

    def test_reviewer_agent_review_result(self):
        """Test ReviewerAgent.review_result works."""
        from .conftest import ReviewerAgent, ExecutionPlan, ExecutionResult, SubTask

        agent = ReviewerAgent()
        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[SubTask(step=1, action="测试", tool="test", params={})],
            expected_output="输出"
        )
        result = ExecutionResult(plan=plan, results=[], status="completed")

        review = agent.review_result(plan, result)
        assert review.status in ["approved", "needs_revision"]

    def test_retriever_agent_creation(self):
        """Test RetrieverAgent can be created."""
        from .conftest import RetrieverAgent

        agent = RetrieverAgent()
        assert agent.role.value == "retriever"
        assert hasattr(agent, "retrieve")

    def test_retriever_agent_retrieve(self):
        """Test RetrieverAgent.retrieve works."""
        from .conftest import RetrieverAgent

        agent = RetrieverAgent()
        result = agent.retrieve("产品质量")

        assert result.query == "产品质量"
        assert "results" in result.to_dict()
        assert "strategy" in result.to_dict()

    def test_message_bus_creation(self):
        """Test MessageBus can be created."""
        from .conftest import MessageBus

        bus = MessageBus()
        assert hasattr(bus, "send")
        assert hasattr(bus, "receive")

    def test_message_bus_send_receive(self):
        """Test MessageBus send and receive works."""
        from .conftest import MessageBus, AgentMessage

        bus = MessageBus()
        msg = AgentMessage(
            sender="planner",
            receiver="executor",
            content={"task": "test"}
        )

        success = bus.send(msg)
        assert success is True

        received = bus.receive("executor")
        assert len(received) == 1
        assert received[0].sender == "planner"


class TestWeek06Coverage:
    """Tests to verify all Week 06 topics are covered."""

    def test_planner_executor_tests_exist(self):
        """Test that planner-executor tests exist."""
        from . import test_planner_executor

        assert hasattr(test_planner_executor, "TestPlannerAgentCreation")
        assert hasattr(test_planner_executor, "TestPlanCreation")
        assert hasattr(test_planner_executor, "TestExecutorAgentCreation")
        assert hasattr(test_planner_executor, "TestPlanExecution")
        assert hasattr(test_planner_executor, "TestPlannerExecutorIntegration")

    def test_agent_communication_tests_exist(self):
        """Test that agent communication tests exist."""
        from . import test_agent_communication

        assert hasattr(test_agent_communication, "TestMessageCreation")
        assert hasattr(test_agent_communication, "TestMessageBus")
        assert hasattr(test_agent_communication, "TestAgentMessaging")
        assert hasattr(test_agent_communication, "TestCommunicationEdgeCases")

    def test_agentic_rag_tests_exist(self):
        """Test that agentic RAG tests exist."""
        from . import test_agentic_rag

        assert hasattr(test_agentic_rag, "TestRetrieverAgentCreation")
        assert hasattr(test_agentic_rag, "TestRetrievalStrategy")
        assert hasattr(test_agentic_rag, "TestRetrievalExecution")
        assert hasattr(test_agentic_rag, "TestResultAssessment")
        assert hasattr(test_agentic_rag, "TestAgenticRAGIntegration")

    def test_human_in_loop_tests_exist(self):
        """Test that human-in-the-loop tests exist."""
        from . import test_human_in_loop

        assert hasattr(test_human_in_loop, "TestHumanReviewCreation")
        assert hasattr(test_human_in_loop, "TestApprovalFlow")
        assert hasattr(test_human_in_loop, "TestRejectionFlow")
        assert hasattr(test_human_in_loop, "TestFeedbackHandling")
        assert hasattr(test_human_in_loop, "TestHumanInLoopEdgeCases")


class TestWeek06Anchors:
    """Tests that validate Week 06 anchor claims."""

    def test_multi_agent_architecture(self):
        """Verify multi-agent architecture is testable."""
        from .conftest import PlannerAgent, ExecutorAgent, ReviewerAgent

        # Should have separate agents for planning, executing, reviewing
        planner = PlannerAgent()
        executor = ExecutorAgent(tools={})
        reviewer = ReviewerAgent()

        assert planner.role.value == "planner"
        assert executor.role.value == "executor"
        assert reviewer.role.value == "reviewer"

    def test_agent_communication(self):
        """Verify agent communication is testable."""
        from .conftest import AgentMessage, MessageBus

        # Agents should be able to send messages
        bus = MessageBus()
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={"data": "test"}
        )

        success = bus.send(msg)
        assert success is True

    def test_agentic_rag_autonomous_retrieval(self):
        """Verify autonomous retrieval is testable."""
        from .conftest import RetrieverAgent

        # Agent should decide retrieval strategy
        agent = RetrieverAgent()
        result = agent.retrieve("test query")

        assert result.strategy is not None
        assert result.assessment is not None

    def test_human_in_the_loop(self):
        """Verify human-in-the-loop is testable."""
        from .conftest import ReviewReport

        # Should be able to represent approval/rejection
        approved_report = ReviewReport(status="approved")
        rejected_report = ReviewReport(status="needs_revision")

        assert approved_report.status == "approved"
        assert rejected_report.status == "needs_revision"


class TestWeek06Integration:
    """Integration tests for Week 06 components."""

    def test_full_planner_executor_reviewer_cycle(self, sample_tasks, sample_tools):
        """Test full planner-executor-reviewer cycle."""
        from .conftest import PlannerAgent, ExecutorAgent, ReviewerAgent

        planner = PlannerAgent()
        executor = ExecutorAgent(tools=sample_tools)
        reviewer = ReviewerAgent()

        # Plan
        plan = planner.create_plan(sample_tasks["sentiment_analysis"])
        assert plan is not None

        # Execute
        result = executor.execute_plan(plan)
        assert result.status in ["completed", "completed_with_errors"]

        # Review
        review = reviewer.review_result(plan, result)
        assert review.status in ["approved", "needs_revision"]

    def test_retrieval_in_workflow(self, sample_queries):
        """Test retrieval agent in workflow."""
        from .conftest import RetrieverAgent, ExecutionPlan, SubTask, ExecutorAgent

        retriever = RetrieverAgent()
        executor = ExecutorAgent(tools={"retrieve_documents": None})

        # Create plan with retrieval
        plan = ExecutionPlan(
            task_understanding="检索并分析",
            subtasks=[
                SubTask(step=1, action="检索", tool="retrieve_documents", params={"query": "产品质量"})
            ],
            expected_output="检索结果"
        )

        # Execute with retriever
        result = executor.execute_plan(plan, retriever=retriever)
        assert len(result.results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

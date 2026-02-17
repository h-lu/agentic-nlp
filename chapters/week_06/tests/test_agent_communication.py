"""
Tests for Agent communication in multi-agent systems.

This module tests communication mechanisms including:
- Message creation and validation
- Message bus for inter-agent communication
- Message delivery and status tracking
- Edge cases like timeouts and failures
"""

import pytest
import time
from typing import Dict, List

from .conftest import (
    AgentMessage, MessageStatus, ExecutionPlan, SubTask, ExecutionResult,
    ReviewReport, PlannerAgent, ExecutorAgent, ReviewerAgent, MessageBus
)


# =============================================================================
# Message Creation Tests
# =============================================================================

class TestMessageCreation:
    """Tests for message creation and structure."""

    def test_agent_message_can_be_created(self):
        """Test AgentMessage can be created."""
        msg = AgentMessage(
            sender="planner",
            receiver="executor",
            content={"task": "分析情感"},
            message_id="msg_1"
        )

        assert msg.sender == "planner"
        assert msg.receiver == "executor"
        assert msg.content == {"task": "分析情感"}
        assert msg.message_id == "msg_1"

    def test_agent_message_default_status(self):
        """Test AgentMessage has default PENDING status."""
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={}
        )

        assert msg.status == MessageStatus.PENDING

    def test_agent_message_timestamp_auto_generated(self):
        """Test AgentMessage generates timestamp automatically."""
        msg1 = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={}
        )

        time.sleep(0.01)

        msg2 = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={}
        )

        assert msg2.timestamp > msg1.timestamp

    def test_agent_message_with_custom_timestamp(self):
        """Test AgentMessage with custom timestamp."""
        custom_time = 1234567890.0
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={},
            timestamp=custom_time
        )

        assert msg.timestamp == custom_time

    def test_agent_message_content_types(self):
        """Test AgentMessage with different content types."""
        # Dict content
        msg1 = AgentMessage(
            sender="a", receiver="b", content={"key": "value"}
        )

        # List content
        msg2 = AgentMessage(
            sender="a", receiver="b", content=["item1", "item2"]
        )

        # String content
        msg3 = AgentMessage(
            sender="a", receiver="b", content="simple message"
        )

        assert msg1.content == {"key": "value"}
        assert msg2.content == ["item1", "item2"]
        assert msg3.content == "simple message"

    def test_agent_message_with_plan_content(self, sample_plans):
        """Test AgentMessage with ExecutionPlan as content."""
        msg = AgentMessage(
            sender="planner",
            receiver="executor",
            content={"plan": sample_plans["simple_plan"].to_dict()}
        )

        assert "plan" in msg.content
        assert "task_understanding" in msg.content["plan"]


# =============================================================================
# Message Bus Tests
# =============================================================================

class TestMessageBus:
    """Tests for MessageBus functionality."""

    def test_message_bus_can_be_created(self, message_bus):
        """Test MessageBus can be instantiated."""
        assert message_bus is not None
        assert hasattr(message_bus, "send")
        assert hasattr(message_bus, "receive")
        assert hasattr(message_bus, "get_status")

    def test_message_bus_send_returns_true(self, message_bus):
        """Test MessageBus.send returns success."""
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={"test": "data"}
        )

        result = message_bus.send(msg)

        assert result is True

    def test_message_bus_send_updates_message_status(self, message_bus):
        """Test MessageBus.send updates message status to DELIVERED."""
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={}
        )

        message_bus.send(msg)

        assert msg.status == MessageStatus.DELIVERED

    def test_message_bus_stores_sent_messages(self, message_bus):
        """Test MessageBus stores sent messages."""
        initial_count = len(message_bus.messages)

        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={}
        )

        message_bus.send(msg)

        assert len(message_bus.messages) == initial_count + 1

    def test_message_bus_receive_by_receiver(self, message_bus):
        """Test MessageBus.receive returns messages for specific receiver."""
        msg1 = AgentMessage(
            sender="agent1",
            receiver="executor",
            content={"task": "1"}
        )

        msg2 = AgentMessage(
            sender="agent2",
            receiver="reviewer",
            content={"task": "2"}
        )

        message_bus.send(msg1)
        message_bus.send(msg2)

        executor_messages = message_bus.receive("executor")
        reviewer_messages = message_bus.receive("reviewer")

        assert len(executor_messages) == 1
        assert len(reviewer_messages) == 1
        assert executor_messages[0].content["task"] == "1"
        assert reviewer_messages[0].content["task"] == "2"

    def test_message_bus_receive_empty_for_unknown_receiver(self, message_bus):
        """Test MessageBus.receive returns empty list for unknown receiver."""
        messages = message_bus.receive("unknown_agent")

        assert messages == []

    def test_message_bus_get_status_by_message_id(self, message_bus):
        """Test MessageBus.get_status returns correct status."""
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={},
            message_id="test_msg_123"
        )

        message_bus.send(msg)

        status = message_bus.get_status("test_msg_123")

        assert status == MessageStatus.DELIVERED

    def test_message_bus_get_status_for_unknown_message(self, message_bus):
        """Test MessageBus.get_status for unknown message."""
        status = message_bus.get_status("unknown_msg_id")

        assert status == MessageStatus.FAILED


# =============================================================================
# Agent Messaging Tests
# =============================================================================

class TestAgentMessaging:
    """Tests for agent-to-agent messaging."""

    def test_executor_receives_plan_from_planner(self, message_bus, sample_plans):
        """Test executor receives plan from planner."""
        msg = AgentMessage(
            sender="planner",
            receiver="executor",
            content={"plan": sample_plans["simple_plan"].to_dict()}
        )

        message_bus.send(msg)
        received = message_bus.receive("executor")

        assert len(received) == 1
        assert received[0].content.get("plan") is not None

    def test_executor_sends_result_to_reviewer(self, message_bus):
        """Test executor sends result to reviewer."""
        plan = ExecutionPlan(
            task_understanding="测试",
            subtasks=[SubTask(step=1, action="测试", tool="test", params={})],
            expected_output="结果"
        )
        result = ExecutionResult(plan=plan, results=[], status="completed")

        msg = AgentMessage(
            sender="executor",
            receiver="reviewer",
            content={"result": result.to_dict()}
        )

        message_bus.send(msg)
        received = message_bus.receive("reviewer")

        assert len(received) == 1
        assert received[0].content.get("result") is not None

    def test_reviewer_sends_feedback_to_planner(self, message_bus):
        """Test reviewer sends feedback to planner."""
        report = ReviewReport(
            status="needs_revision",
            issues=["结果不完整"],
            revision_suggestions=["增加更多分析"]
        )

        msg = AgentMessage(
            sender="reviewer",
            receiver="planner",
            content={"review": report.to_dict()}
        )

        message_bus.send(msg)
        received = message_bus.receive("planner")

        assert len(received) == 1
        assert received[0].content.get("review") is not None

    def test_multi_agent_communication_chain(self, message_bus, sample_plans):
        """Test full communication chain: planner -> executor -> reviewer."""
        # Planner sends plan to executor
        plan_msg = AgentMessage(
            sender="planner",
            receiver="executor",
            content={"plan": sample_plans["simple_plan"].to_dict()}
        )
        message_bus.send(plan_msg)

        # Executor sends result to reviewer
        result_msg = AgentMessage(
            sender="executor",
            receiver="reviewer",
            content={"result": {"status": "completed"}}
        )
        message_bus.send(result_msg)

        # Reviewer sends final report
        report_msg = AgentMessage(
            sender="reviewer",
            receiver="planner",
            content={"final_report": {"status": "approved"}}
        )
        message_bus.send(report_msg)

        # Verify all messages delivered
        executor_msgs = message_bus.receive("executor")
        reviewer_msgs = message_bus.receive("reviewer")
        planner_msgs = message_bus.receive("planner")

        assert len(executor_msgs) == 1
        assert len(reviewer_msgs) == 1
        assert len(planner_msgs) == 1


# =============================================================================
# Communication Edge Cases
# =============================================================================

class TestCommunicationEdgeCases:
    """Edge case tests for agent communication."""

    def test_empty_message_content(self, message_bus):
        """Test message with empty content."""
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={}
        )

        result = message_bus.send(msg)

        assert result is True

    def test_very_large_message_content(self, message_bus):
        """Test message with very large content."""
        large_content = {"data": "x" * 100000}

        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content=large_content
        )

        result = message_bus.send(msg)

        assert result is True

    def test_special_characters_in_content(self, message_bus):
        """Test message with special characters."""
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={"text": "测试@#￥%……&*()😊"}
        )

        result = message_bus.send(msg)

        assert result is True

    def test_unicode_in_message_fields(self, message_bus):
        """Test message with Unicode in sender/receiver."""
        msg = AgentMessage(
            sender="规划者",
            receiver="执行者",
            content={"task": "测试"}
        )

        result = message_bus.send(msg)

        assert result is True

    def test_multiple_messages_same_receiver(self, message_bus):
        """Test multiple messages to same receiver."""
        for i in range(5):
            msg = AgentMessage(
                sender=f"sender_{i}",
                receiver="executor",
                content={"idx": i}
            )
            message_bus.send(msg)

        received = message_bus.receive("executor")

        assert len(received) == 5

    def test_broadcast_message(self, message_bus):
        """Test broadcasting message to all agents."""
        agents = ["planner", "executor", "reviewer"]

        for agent in agents:
            msg = AgentMessage(
                sender="system",
                receiver=agent,
                content={"broadcast": "所有Agent请注意"}
            )
            message_bus.send(msg)

        for agent in agents:
            received = message_bus.receive(agent)
            assert len(received) == 1
            assert received[0].content.get("broadcast") == "所有Agent请注意"

    def test_message_order_preserved(self, message_bus):
        """Test that message order is preserved."""
        for i in range(10):
            msg = AgentMessage(
                sender="sender",
                receiver="receiver",
                content={"seq": i}
            )
            message_bus.send(msg)

        received = message_bus.receive("receiver")

        assert len(received) == 10
        for i, msg in enumerate(received):
            assert msg.content["seq"] == i

    def test_concurrent_send_receive(self, message_bus):
        """Test concurrent send and receive operations."""
        import threading

        def send_messages():
            for i in range(10):
                msg = AgentMessage(
                    sender=f"sender_{i}",
                    receiver="receiver",
                    content={"idx": i}
                )
                message_bus.send(msg)

        thread = threading.Thread(target=send_messages)
        thread.start()
        thread.join()

        received = message_bus.receive("receiver")
        assert len(received) == 10


class TestCommunicationErrorCases:
    """Error case tests for agent communication."""

    def test_duplicate_message_ids(self, message_bus):
        """Test messages with duplicate IDs."""
        msg1 = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={"seq": 1},
            message_id="duplicate_id"
        )

        msg2 = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={"seq": 2},
            message_id="duplicate_id"
        )

        message_bus.send(msg1)
        message_bus.send(msg2)

        # Both should be stored
        assert len(message_bus.messages) == 2

    def test_message_with_empty_sender_and_receiver(self, message_bus):
        """Test message with empty strings for sender/receiver."""
        msg = AgentMessage(
            sender="",
            receiver="",
            content={}
        )

        result = message_bus.send(msg)

        # Should handle gracefully
        assert result is not None


# =============================================================================
# Message Status Tracking Tests
# =============================================================================

class TestMessageStatusTracking:
    """Tests for message status tracking."""

    def test_message_status_transitions(self, message_bus):
        """Test message status transitions from PENDING to DELIVERED."""
        msg = AgentMessage(
            sender="agent1",
            receiver="agent2",
            content={}
        )

        assert msg.status == MessageStatus.PENDING

        message_bus.send(msg)

        assert msg.status == MessageStatus.DELIVERED

    def test_get_status_for_all_sent_messages(self, message_bus):
        """Test getting status for all sent messages."""
        message_ids = []
        for i in range(5):
            msg = AgentMessage(
                sender="agent1",
                receiver="agent2",
                content={"idx": i},
                message_id=f"msg_{i}"
            )
            message_bus.send(msg)
            message_ids.append(f"msg_{i}")

        for msg_id in message_ids:
            status = message_bus.get_status(msg_id)
            assert status == MessageStatus.DELIVERED

    def test_message_status_after_failed_delivery(self, message_bus):
        """Test message status when delivery fails."""
        # For non-existent message, status should be FAILED
        status = message_bus.get_status("non_existent_msg")

        assert status == MessageStatus.FAILED

"""
Tests for Agentic RAG (Retrieval-Augmented Generation with Agent control).

This module tests:
- Retriever Agent that autonomously decides retrieval strategies
- Strategy selection (vector, hybrid, multi-round)
- Result assessment and re-retrieval
- Integration with multi-agent workflow
"""

import pytest
from typing import Dict, List

from .conftest import (
    RetrieverAgent, RetrievalStrategy, RetrievalResult, MockVectorStore,
    MockKeywordIndex, ExecutionPlan, SubTask
)


# =============================================================================
# Retriever Agent Creation Tests
# =============================================================================

class TestRetrieverAgentCreation:
    """Tests for RetrieverAgent creation and initialization."""

    def test_retriever_agent_can_be_created(self, mock_llm_client):
        """Test RetrieverAgent can be instantiated."""
        agent = RetrieverAgent(llm_client=mock_llm_client)

        assert agent is not None
        assert agent.role.value == "retriever"
        assert agent.llm == mock_llm_client

    def test_retriever_agent_with_vector_store(self, mock_llm_client):
        """Test RetrieverAgent with custom vector store."""
        store = MockVectorStore()
        agent = RetrieverAgent(llm_client=mock_llm_client, vector_store=store)

        assert agent.vector_store == store

    def test_retriever_agent_with_keyword_index(self, mock_llm_client):
        """Test RetrieverAgent with keyword index."""
        index = MockKeywordIndex()
        agent = RetrieverAgent(llm_client=mock_llm_client, keyword_index=index)

        assert agent.keyword_index == index

    def test_retriever_agent_has_required_methods(self, retriever_agent):
        """Test RetrieverAgent has required methods."""
        assert hasattr(retriever_agent, "retrieve")
        assert hasattr(retriever_agent, "_decide_strategy")
        assert hasattr(retriever_agent, "_assess_results")


# =============================================================================
# Retrieval Strategy Tests
# =============================================================================

class TestRetrievalStrategy:
    """Tests for retrieval strategy selection."""

    def test_strategy_for_simple_query(self, retriever_agent, sample_queries):
        """Test strategy selection for simple query."""
        strategy = retriever_agent._decide_strategy(sample_queries["simple"])

        assert strategy is not None
        assert strategy.method in ["vector", "hybrid", "multi_round"]
        assert strategy.top_k > 0

    def test_strategy_for_complex_query(self, retriever_agent, sample_queries):
        """Test strategy selection for complex query."""
        strategy = retriever_agent._decide_strategy(sample_queries["complex"])

        assert strategy is not None
        # Complex queries might prefer hybrid
        assert strategy.method in ["vector", "hybrid", "multi_round"]

    def test_strategy_for_empty_query(self, retriever_agent):
        """Test strategy selection for empty query."""
        strategy = retriever_agent._decide_strategy("")

        assert strategy is not None
        # Should handle gracefully

    def test_strategy_includes_reasoning(self, retriever_agent, sample_queries):
        """Test strategy includes reasoning."""
        strategy = retriever_agent._decide_strategy(sample_queries["simple"])

        assert strategy.reasoning is not None
        assert len(strategy.reasoning) > 0

    def test_strategy_to_dict(self):
        """Test RetrievalStrategy.to_dict() works."""
        strategy = RetrievalStrategy(
            method="hybrid",
            top_k=10,
            reasoning="Complex query",
            improved_query="improved query"
        )

        strategy_dict = strategy.to_dict()

        assert strategy_dict["method"] == "hybrid"
        assert strategy_dict["top_k"] == 10
        assert strategy_dict["reasoning"] == "Complex query"
        assert strategy_dict["improved_query"] == "improved query"

    def test_different_strategies_for_different_queries(self, retriever_agent):
        """Test that different queries may get different strategies."""
        strategy1 = retriever_agent._decide_strategy("短查询")
        strategy2 = retriever_agent._decide_strategy("这是一个很长的查询包含更多细节和信息")

        # Strategies may differ based on query complexity
        assert strategy1 is not None
        assert strategy2 is not None


# =============================================================================
# Retrieval Execution Tests
# =============================================================================

class TestRetrievalExecution:
    """Tests for retrieval execution."""

    def test_retrieve_returns_valid_result(self, retriever_agent, sample_queries):
        """Test retrieve returns valid RetrievalResult."""
        result = retriever_agent.retrieve(sample_queries["simple"])

        assert result is not None
        assert result.query == sample_queries["simple"]
        assert result.results is not None
        assert result.strategy is not None
        assert result.assessment is not None

    def test_retrieve_with_custom_top_k(self, retriever_agent):
        """Test retrieve with custom top_k parameter."""
        result = retriever_agent.retrieve("测试查询", top_k=10)

        assert result.strategy.top_k == 10

    def test_retrieve_records_history(self, retriever_agent):
        """Test that retrieve records history."""
        initial_history_len = len(retriever_agent.retrieval_history)

        retriever_agent.retrieve("测试查询")

        assert len(retriever_agent.retrieval_history) > initial_history_len

    def test_retrieve_result_structure(self, retriever_agent, sample_queries):
        """Test retrieve result has correct structure."""
        result = retriever_agent.retrieve(sample_queries["simple"])

        # Check result structure
        assert hasattr(result, "query")
        assert hasattr(result, "results")
        assert hasattr(result, "strategy")
        assert hasattr(result, "assessment")

        # Check to_dict() works
        result_dict = result.to_dict()
        assert "query" in result_dict
        assert "results" in result_dict
        assert "strategy" in result_dict
        assert "assessment" in result_dict


# =============================================================================
# Result Assessment Tests
# =============================================================================

class TestResultAssessment:
    """Tests for retrieval result assessment."""

    def test_assess_results_with_valid_results(self, retriever_agent):
        """Test assessment with valid retrieval results."""
        results = {
            "results": [
                {"id": "doc1", "text": "测试文档1", "score": 0.9},
                {"id": "doc2", "text": "测试文档2", "score": 0.8}
            ],
            "total": 2
        }

        assessment = retriever_agent._assess_results("测试查询", results)

        assert assessment is not None
        assert "sufficient" in assessment
        assert "confidence" in assessment
        assert assessment["sufficient"] is True

    def test_assess_results_with_empty_results(self, retriever_agent):
        """Test assessment with empty results."""
        results = {"results": [], "total": 0}

        assessment = retriever_agent._assess_results("测试查询", results)

        assert assessment is not None
        assert assessment["sufficient"] is False

    def test_assess_confidence_range(self, retriever_agent):
        """Test that assessment confidence is in valid range."""
        results = {
            "results": [{"id": "doc1", "text": "测试"}],
            "total": 1
        }

        assessment = retriever_agent._assess_results("测试", results)

        assert 0 <= assessment["confidence"] <= 1

    def test_assess_includes_result_count(self, retriever_agent):
        """Test that assessment includes result count."""
        results = {
            "results": [
                {"id": f"doc{i}", "text": f"文档{i}"}
                for i in range(5)
            ],
            "total": 5
        }

        assessment = retriever_agent._assess_results("测试", results)

        assert "result_count" in assessment
        assert assessment["result_count"] == 5


# =============================================================================
# Agentic RAG Integration Tests
# =============================================================================

class TestAgenticRAGIntegration:
    """Tests for Agentic RAG integration with multi-agent workflow."""

    def test_retriever_in_workflow(self, agent_workflow, sample_queries):
        """Test retriever agent in multi-agent workflow."""
        retriever = agent_workflow["retriever"]

        result = retriever.retrieve(sample_queries["simple"])

        assert result is not None
        assert result.strategy is not None

    def test_agentic_rag_decision_flow(self, agent_workflow, sample_queries):
        """Test complete Agentic RAG decision flow."""
        retriever = agent_workflow["retriever"]

        # 1. Agent decides strategy
        strategy = retriever._decide_strategy(sample_queries["complex"])
        assert strategy is not None

        # 2. Agent executes retrieval
        result = retriever.retrieve(sample_queries["complex"])
        assert result is not None

        # 3. Agent assesses results
        assessment = retriever._assess_results(sample_queries["complex"],
                                                {"results": result.results, "total": len(result.results)})
        assert assessment is not None


# =============================================================================
# Edge Cases
# =============================================================================

class TestAgenticRAGEdgeCases:
    """Edge case tests for Agentic RAG."""

    def test_retrieve_with_empty_query(self, retriever_agent):
        """Test retrieve with empty query."""
        result = retriever_agent.retrieve("")

        assert result is not None
        # Should handle gracefully

    def test_retrieve_with_very_long_query(self, retriever_agent):
        """Test retrieve with very long query."""
        long_query = "测试查询" * 100

        result = retriever_agent.retrieve(long_query)

        assert result is not None

    def test_retrieve_with_special_characters(self, retriever_agent):
        """Test retrieve with special characters."""
        query = "测试@#￥%……&*()查询😊"

        result = retriever_agent.retrieve(query)

        assert result is not None

    def test_retrieve_with_unicode_query(self, retriever_agent):
        """Test retrieve with Unicode characters."""
        query = "测试Emotional状态😊客户反馈"

        result = retriever_agent.retrieve(query)

        assert result is not None

    def test_retrieve_with_zero_top_k(self, retriever_agent):
        """Test retrieve with top_k=0."""
        result = retriever_agent.retrieve("测试", top_k=0)

        assert result is not None

    def test_retrieve_with_negative_top_k(self, retriever_agent):
        """Test retrieve with negative top_k."""
        result = retriever_agent.retrieve("测试", top_k=-1)

        assert result is not None
        # Should handle gracefully

    def test_retrieve_with_very_large_top_k(self, retriever_agent):
        """Test retrieve with very large top_k."""
        result = retriever_agent.retrieve("测试", top_k=1000000)

        assert result is not None

    def test_assess_with_none_results(self, retriever_agent):
        """Test assessment with None results."""
        assessment = retriever_agent._assess_results("测试", None)

        assert assessment is not None

    def test_assess_with_malformed_results(self, retriever_agent):
        """Test assessment with malformed results dict."""
        assessment = retriever_agent._assess_results("测试", {"invalid": "data"})

        assert assessment is not None


# =============================================================================
# Error Cases
# =============================================================================

class TestAgenticRAGErrorCases:
    """Error case tests for Agentic RAG."""

    def test_concurrent_retrievals(self, retriever_agent):
        """Test concurrent retrieval operations."""
        import threading

        results = []

        def retrieve_task(query):
            result = retriever_agent.retrieve(query)
            results.append(result)

        threads = [
            threading.Thread(target=retrieve_task, args=(f"查询{i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5

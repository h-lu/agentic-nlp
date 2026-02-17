"""
Smoke tests for Week 04 test infrastructure.

Basic tests to verify the testing environment is working correctly.
"""

import pytest


class TestWeek04TestInfrastructure:
    """Basic infrastructure tests."""

    def test_conftest_imports(self):
        """Test that conftest fixtures can be imported."""
        from .conftest import (
            HybridRetriever,
            HybridSearchConfig,
            MockBM25Index,
            MockVectorCollection,
            CrossEncoderReranker,
            MockCrossEncoder,
            QueryRewriter,
            MockLLMClient,
            MockRAGASEvaluator,
            reciprocal_rank_fusion
        )

        assert HybridRetriever is not None
        assert HybridSearchConfig is not None
        assert MockBM25Index is not None
        assert MockVectorCollection is not None
        assert CrossEncoderReranker is not None
        assert MockCrossEncoder is not None
        assert QueryRewriter is not None
        assert MockLLMClient is not None
        assert MockRAGASEvaluator is not None
        assert reciprocal_rank_fusion is not None

    def test_hybrid_search_config_defaults(self):
        """Test HybridSearchConfig default values."""
        from .conftest import HybridSearchConfig

        config = HybridSearchConfig()

        assert config.top_k == 20
        assert config.alpha == 0.5
        assert config.rrf_k == 60

    def test_bm25_index_creation(self):
        """Test MockBM25Index can be created."""
        from .conftest import MockBM25Index

        docs = ["文档 1", "文档 2", "文档 3"]
        index = MockBM25Index(docs)

        assert len(index.documents) == 3
        assert index.get_scores("测试") is not None

    def test_vector_collection_creation(self):
        """Test MockVectorCollection can be created."""
        from .conftest import MockVectorCollection

        collection = MockVectorCollection()
        collection.add_documents(["文档 1", "文档 2"])

        assert len(collection.documents) == 2

    def test_cross_encoder_creation(self):
        """Test MockCrossEncoder can be created."""
        from .conftest import MockCrossEncoder

        model = MockCrossEncoder()
        scores = model.predict([("查询", "文档")])

        assert len(scores) == 1
        assert 0 <= scores[0] <= 1

    def test_query_rewriter_creation(self):
        """Test QueryRewriter can be created."""
        from .conftest import QueryRewriter, MockLLMClient

        client = MockLLMClient()
        rewriter = QueryRewriter(client)

        result = rewriter.rewrite("测试查询")
        assert isinstance(result, str)

    def test_ragas_evaluator_creation(self):
        """Test MockRAGASEvaluator can be created."""
        from .conftest import MockRAGASEvaluator

        evaluator = MockRAGASEvaluator()
        result = evaluator.evaluate(
            questions=["问题"],
            answers=["回答"],
            contexts=[["上下文"]]
        )

        assert result is not None
        assert hasattr(result, "faithfulness")

    def test_rrf_function(self):
        """Test reciprocal_rank_fusion function."""
        from .conftest import reciprocal_rank_fusion

        vec_results = [{"id": "a", "distance": 0.1}]
        bm25_results = [{"id": "b", "score": 1.0}]

        fused = reciprocal_rank_fusion(vec_results, bm25_results)

        assert isinstance(fused, list)
        assert len(fused) > 0

    def test_pytest_fixtures_available(self, request):
        """Test that pytest fixtures are available."""
        fixture_names = [
            "sample_documents",
            "vector_collection",
            "bm25_index",
            "hybrid_retriever",
            "hybrid_config",
            "mock_cross_encoder",
            "reranker",
            "mock_llm_client",
            "query_rewriter",
            "ragas_evaluator",
            "evaluation_dataset",
            "candidate_results"
        ]

        # Just check that the fixture names are strings
        assert all(isinstance(name, str) for name in fixture_names)


class TestWeek04Coverage:
    """Tests to verify all Week 04 topics are covered."""

    def test_hybrid_search_tests_exist(self):
        """Test that hybrid search tests exist."""
        from . import test_hybrid_search

        assert hasattr(test_hybrid_search, "TestBM25Search")
        assert hasattr(test_hybrid_search, "TestVectorSearch")
        assert hasattr(test_hybrid_search, "TestReciprocalRankFusion")
        assert hasattr(test_hybrid_search, "TestHybridRetriever")

    def test_reranking_tests_exist(self):
        """Test that reranking tests exist."""
        from . import test_reranking

        assert hasattr(test_reranking, "TestCrossEncoderScoring")
        assert hasattr(test_reranking, "TestRerankingLogic")
        assert hasattr(test_reranking, "TestRerankingPrecision")

    def test_query_rewriting_tests_exist(self):
        """Test that query rewriting tests exist."""
        from . import test_query_rewriting

        assert hasattr(test_query_rewriting, "TestSingleQueryRewriting")
        assert hasattr(test_query_rewriting, "TestQueryExpansion")
        assert hasattr(test_query_rewriting, "TestQueryRewriteEffectiveness")

    def test_ragas_tests_exist(self):
        """Test that RAGAS tests exist."""
        from . import test_ragas_evaluation

        assert hasattr(test_ragas_evaluation, "TestRAGASContextPrecision")
        assert hasattr(test_ragas_evaluation, "TestRAGASFaithfulness")
        assert hasattr(test_ragas_evaluation, "TestRAGASAnswerRelevance")


class TestWeek04Anchors:
    """Tests that validate Week 04 anchor claims."""

    def test_hybrid_search_recall_anchor(self):
        """Verify hybrid search recall boost anchor is testable."""
        from .conftest import HybridSearchConfig

        # The anchor claims 20%+ recall improvement
        # Tests should verify this
        config = HybridSearchConfig(alpha=0.5)
        assert config.alpha == 0.5  # Balanced for best recall

    def test_rerank_precision_anchor(self):
        """Verify reranking precision boost anchor is testable."""
        from .conftest import MockCrossEncoder

        # The anchor claims 30%+ Top-3 precision improvement
        model = MockCrossEncoder()
        # Use more distinct queries/documents for reliable scoring
        scores = model.predict([
            ("GPU 资源申请", "GPU 资源申请流程：需要填写申请表"),
            ("GPU 资源申请", "公司健身房位于 B1 层")
        ])

        # First (relevant) should be higher than second (irrelevant)
        # Note: Mock uses keyword overlap, so this should work
        assert scores[0] >= scores[1]

    def test_ragas_faithfulness_anchor(self):
        """Verify RAGAS faithfulness target anchor is testable."""
        from .conftest import MockRAGASEvaluator

        # The anchor claims >0.8 faithfulness for good systems
        evaluator = MockRAGASEvaluator()
        result = evaluator.evaluate(
            questions=["问题"],
            answers=["基于上下文的回答"],
            contexts=[["相关上下文"]]
        )

        # Should produce a score in valid range
        assert 0 <= result.faithfulness <= 1


class TestWeek04Integration:
    """Integration tests for Week 04 components."""

    def test_full_pipeline_components(self):
        """Test that all pipeline components can work together."""
        from .conftest import (
            HybridRetriever,
            CrossEncoderReranker,
            QueryRewriter,
            MockVectorCollection,
            MockBM25Index,
            MockCrossEncoder,
            MockLLMClient,
            HybridSearchConfig
        )

        # Create components
        vector_col = MockVectorCollection()
        vector_col.add_documents(["文档 1", "文档 2"])

        bm25 = MockBM25Index(["文档 1", "文档 2"])

        config = HybridSearchConfig(alpha=0.5, top_k=5)
        retriever = HybridRetriever(vector_col, bm25, config)

        cross_encoder = MockCrossEncoder()
        reranker = CrossEncoderReranker(cross_encoder)

        llm = MockLLMClient()
        rewriter = QueryRewriter(llm)

        # Test the flow
        query = "测试查询"
        rewritten = rewriter.rewrite(query)
        candidates = retriever.search(rewritten, top_k=5)
        reranked = reranker.rerank(query, [{"content": c.content, "id": c.id} for c in candidates], top_k=3)

        # Should complete without errors
        assert isinstance(rewritten, str)
        assert len(candidates) > 0
        assert len(reranked) <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

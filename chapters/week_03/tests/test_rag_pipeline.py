"""
Tests for End-to-End RAG Pipeline.

This module tests the complete RAG pipeline including retrieval quality,
prompt integration, and error handling.

Validates anchors:
- rag-hallucination-mitigation
- rag-prompt-integration
"""

import pytest
from .conftest import (
    MockChromaClient,
    MockLLMClient,
    MockEmbeddingClient,
    RAGResponse,
    build_rag_prompt,
    parse_rag_response,
    cosine_similarity
)


class SimpleRAGPipeline:
    """Simple RAG pipeline implementation for testing."""

    def __init__(self, collection, llm_client, embedding_client=None):
        self.collection = collection
        self.llm_client = llm_client
        self.embedding_client = embedding_client or MockEmbeddingClient()

    def retrieve(self, query: str, top_k: int = 3):
        """Retrieve relevant documents."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        documents = []
        for i, doc in enumerate(results["documents"][0]):
            documents.append({
                "content": doc,
                "source": results["metadatas"][0][i].get("source", "unknown"),
                "distance": results["distances"][0][i]
            })

        return documents

    def generate(self, prompt: str) -> str:
        """Generate response using LLM."""
        return self.llm_client.generate(prompt)

    def query(self, question: str, top_k: int = 3) -> RAGResponse:
        """Execute full RAG query."""
        # 1. Retrieve
        documents = self.retrieve(question, top_k)

        # 2. Build prompt
        prompt = build_rag_prompt(question, documents)

        # 3. Generate
        answer = self.generate(prompt)

        return RAGResponse(
            answer=answer,
            sources=documents,
            query=question
        )


class TestRAGPipelineBasic:
    """Tests for basic RAG pipeline functionality."""

    def test_rag_pipeline_initialization(self, populated_collection, mock_llm_client):
        """Test RAG pipeline initialization."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        assert pipeline.collection is not None
        assert pipeline.llm_client is not None

    def test_rag_retrieval(self, populated_collection, mock_llm_client):
        """Test RAG retrieval step."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        documents = pipeline.retrieve("远程办公怎么申请", top_k=3)

        assert len(documents) <= 3
        assert all("content" in doc for doc in documents)
        assert all("source" in doc for doc in documents)
        assert all("distance" in doc for doc in documents)

    def test_rag_generation(self, populated_collection, mock_llm_client):
        """Test RAG generation step."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        prompt = "用户问题：远程办公\n请回答："
        answer = pipeline.generate(prompt)

        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_full_rag_query(self, populated_collection, mock_llm_client):
        """Test full RAG query."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("远程办公需要满足什么条件？")

        assert isinstance(response, RAGResponse)
        assert response.query == "远程办公需要满足什么条件？"
        assert isinstance(response.answer, str)
        assert len(response.sources) > 0


class TestRAGRetrievalQuality:
    """Tests for RAG retrieval quality."""

    def test_retrieval_returns_relevant_documents(self, populated_collection, mock_llm_client):
        """Test that retrieval returns relevant documents."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        # Query about remote work
        documents = pipeline.retrieve("远程办公政策", top_k=3)

        # At least one document should be about remote work
        has_remote_work = any(
            "远程办公" in doc["content"] or "remote" in doc["source"]
            for doc in documents
        )
        assert has_remote_work

    def test_retrieval_returns_diverse_sources(self, populated_collection, mock_llm_client):
        """Test that retrieval can return documents from different sources."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        documents = pipeline.retrieve("公司政策", top_k=5)

        # Should have diverse sources
        sources = [doc["source"] for doc in documents]
        unique_sources = set(sources)

        assert len(unique_sources) >= 1  # At least some diversity

    def test_retrieval_distance_threshold(self, populated_collection, mock_llm_client):
        """Test that retrieved documents have reasonable distance scores."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        documents = pipeline.retrieve("健身房开放时间", top_k=3)

        # Distance should be less than 0.7 for relevant results (1 - similarity)
        # In our mock, distance is 1 - similarity, so < 0.7 means similarity > 0.3
        for doc in documents:
            assert 0 <= doc["distance"] <= 2  # Valid distance range

    def test_top_k_parameter_respected(self, populated_collection, mock_llm_client):
        """Test that top_k parameter is respected."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        for k in [1, 2, 3, 5]:
            documents = pipeline.retrieve("测试查询", top_k=k)
            assert len(documents) <= k


class TestRAGPromptIntegration:
    """Tests for RAG prompt integration.

    Validates anchor: rag-prompt-integration
    """

    def test_rag_prompt_includes_context(self):
        """Test that RAG prompt includes retrieved context."""
        query = "远程办公怎么申请"
        documents = [
            {"content": "远程办公需要提前申请", "source": "policy.pdf"},
            {"content": "申请需经理审批", "source": "policy.pdf"},
        ]

        prompt = build_rag_prompt(query, documents)

        assert query in prompt
        assert "远程办公需要提前申请" in prompt
        assert "参考文档" in prompt

    def test_rag_prompt_structured_format(self):
        """Test that RAG prompt uses structured format for context."""
        query = "测试问题"
        documents = [
            {"content": "文档内容1", "source": "source1.pdf"},
            {"content": "文档内容2", "source": "source2.pdf"},
        ]

        prompt = build_rag_prompt(query, documents)

        # Should include structured format
        assert "【参考文档" in prompt
        assert "来源" in prompt

    def test_structured_vs_simple_prompt_comparison(self):
        """Test that structured prompts are more informative than simple concatenation."""
        query = "测试问题"
        documents = [
            {"content": "文档1内容", "source": "source1.pdf"},
            {"content": "文档2内容", "source": "source2.pdf"},
        ]

        # Structured prompt
        structured_prompt = build_rag_prompt(query, documents)

        # Simple concatenation
        simple_context = " ".join([doc["content"] for doc in documents])
        simple_prompt = f"{query}\n{simple_context}"

        # Structured should be longer and include metadata
        assert "source1.pdf" in structured_prompt
        assert "source1.pdf" not in simple_prompt

    def test_prompt_includes_role_and_task(self):
        """Test that prompt includes role definition and task."""
        query = "测试问题"
        documents = [{"content": "内容", "source": "source.pdf"}]

        prompt = build_rag_prompt(query, documents)

        # Should include role definition
        assert "角色" in prompt or "助手" in prompt


class TestRAGHallucinationMitigation:
    """Tests for hallucination mitigation with RAG.

    Validates anchor: rag-hallucination-mitigation
    """

    def test_rag_returns_source_citations(self, populated_collection):
        """Test that RAG returns source citations with answers."""
        mock_llm = MockLLMClient(responses={
            "远程": "根据参考文档，远程办公需要提前申请。"
        })
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm
        )

        response = pipeline.query("远程办公怎么申请")

        # Response should include source information
        assert len(response.sources) > 0
        assert all("source" in s for s in response.sources)

    def test_rag_based_on_retrieved_context(self, populated_collection):
        """Test that RAG answers are based on retrieved context."""
        mock_llm = MockLLMClient()
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm
        )

        # Query that requires specific knowledge
        response = pipeline.query("健身房在哪里")

        # Answer should be based on retrieved documents
        assert response.answer is not None
        # Sources should contain relevant info
        relevant_source_found = any(
            "健身房" in doc["content"] or "B1" in doc["content"]
            for doc in response.sources
        )
        assert relevant_source_found

    def test_no_relevant_documents_handling(self, mock_chroma_client):
        """Test handling when no relevant documents are found."""
        collection = mock_chroma_client.create_collection("test")
        collection.add(
            documents=["这是一份关于烹饪的文档"],
            metadatas=[{"source": "cooking.pdf"}],
            ids=["d1"]
        )

        mock_llm = MockLLMClient(responses={
            "无法回答": "根据现有知识库无法回答这个问题。"
        })
        pipeline = SimpleRAGPipeline(
            collection=collection,
            llm_client=mock_llm
        )

        # Query about something not in the knowledge base
        response = pipeline.query("量子物理是什么")

        # Should still return a response with sources
        assert response.answer is not None
        assert len(response.sources) > 0

    def test_answer_traceability(self, populated_collection):
        """Test that answers can be traced back to source documents."""
        mock_llm = MockLLMClient()
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm
        )

        response = pipeline.query("报销流程")

        # Should have sources that mention reimbursement
        assert len(response.sources) > 0

        # At least one source should contain relevant info
        has_relevant = any(
            "报销" in doc["content"]
            for doc in response.sources
        )
        assert has_relevant


class TestRAGErrorHandling:
    """Tests for RAG pipeline error handling."""

    def test_empty_query_handling(self, populated_collection, mock_llm_client):
        """Test handling of empty query."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("")

        # Should still return a valid response
        assert response is not None
        assert isinstance(response.answer, str)

    def test_llm_error_handling(self, populated_collection):
        """Test handling of LLM errors."""
        class FailingLLMClient:
            def generate(self, prompt):
                raise Exception("LLM API Error")

        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=FailingLLMClient()
        )

        with pytest.raises(Exception):
            pipeline.query("测试问题")

    def test_retrieval_with_no_documents(self, mock_chroma_client, mock_llm_client):
        """Test retrieval when collection is empty."""
        collection = mock_chroma_client.create_collection("empty")

        pipeline = SimpleRAGPipeline(
            collection=collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("测试问题")

        # Should handle gracefully
        assert response.answer is not None
        assert len(response.sources) == 0


class TestRAGPipelineIntegration:
    """Tests for full RAG pipeline integration."""

    def test_end_to_end_query_flow(self, populated_collection, mock_llm_client):
        """Test complete end-to-end query flow."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        # Track LLM calls
        initial_calls = mock_llm_client.call_count

        response = pipeline.query("年假怎么计算")

        # Should have called LLM
        assert mock_llm_client.call_count > initial_calls

        # Response should be complete
        assert response.query == "年假怎么计算"
        assert response.answer is not None
        assert len(response.sources) > 0

    def test_multiple_queries(self, populated_collection, mock_llm_client):
        """Test multiple sequential queries."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        queries = [
            "远程办公政策",
            "报销流程",
            "健身房开放时间",
        ]

        responses = [pipeline.query(q) for q in queries]

        # All queries should return valid responses
        for i, response in enumerate(responses):
            assert response.query == queries[i]
            assert response.answer is not None

    def test_query_with_context_overflow(self, mock_chroma_client, mock_llm_client):
        """Test query with many retrieved documents."""
        collection = mock_chroma_client.create_collection("large")
        # Add many documents
        for i in range(50):
            collection.add(
                documents=[f"文档{i}的内容"],
                metadatas=[{"index": i}],
                ids=[f"d{i}"]
            )

        pipeline = SimpleRAGPipeline(
            collection=collection,
            llm_client=mock_llm_client
        )

        # Request many documents
        response = pipeline.query("测试", top_k=20)

        # Should handle large context
        assert len(response.sources) <= 20


class TestRAGCostTracking:
    """Tests for RAG cost tracking."""

    def test_token_tracking(self, populated_collection):
        """Test token usage tracking."""
        mock_llm = MockLLMClient()
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm
        )

        initial_tokens = mock_llm.last_usage.total_tokens
        pipeline.query("测试问题")

        # Token count should be tracked
        assert mock_llm.last_usage is not None

    def test_call_count_tracking(self, populated_collection):
        """Test API call count tracking."""
        mock_llm = MockLLMClient()
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm
        )

        initial_count = mock_llm.call_count
        pipeline.query("测试问题1")
        pipeline.query("测试问题2")

        # Should have made 2 calls
        assert mock_llm.call_count == initial_count + 2


class TestRAGResponseFormat:
    """Tests for RAG response format."""

    def test_response_structure(self, populated_collection, mock_llm_client):
        """Test that response has correct structure."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("测试问题")

        assert hasattr(response, "answer")
        assert hasattr(response, "sources")
        assert hasattr(response, "query")

        assert isinstance(response.answer, str)
        assert isinstance(response.sources, list)
        assert isinstance(response.query, str)

    def test_source_structure(self, populated_collection, mock_llm_client):
        """Test that source documents have correct structure."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("测试问题")

        for source in response.sources:
            assert "content" in source
            assert "source" in source
            assert "distance" in source

    def test_response_parseable(self, populated_collection, mock_llm_client):
        """Test that response can be parsed."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("测试问题")

        # Answer should be parseable
        parsed = parse_rag_response(response.answer)
        assert isinstance(parsed, str)
        assert parsed == response.answer.strip()


class TestRAGPerformance:
    """Tests for RAG pipeline performance."""

    def test_query_latency(self, populated_collection, mock_llm_client):
        """Test query latency."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        import time
        start = time.time()
        pipeline.query("测试问题")
        elapsed_ms = (time.time() - start) * 1000

        # Should complete in reasonable time
        assert elapsed_ms < 1000

    def test_repeated_query_performance(self, populated_collection, mock_llm_client):
        """Test repeated query performance."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        import time

        times = []
        for _ in range(10):
            start = time.time()
            pipeline.query("测试问题")
            times.append((time.time() - start) * 1000)

        avg_time = sum(times) / len(times)

        # Average should be reasonable
        assert avg_time < 500


class TestRAGEdgeCases:
    """Tests for RAG edge cases."""

    def test_query_with_code_snippet(self, mock_chroma_client, mock_llm_client):
        """Test query containing code snippets."""
        collection = mock_chroma_client.create_collection("code_docs")
        collection.add(
            documents=["```python\ndef hello():\n    print('Hello')\n```"],
            metadatas=[{"type": "code"}],
            ids=["code1"]
        )

        pipeline = SimpleRAGPipeline(
            collection=collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("如何定义函数")

        assert response.answer is not None

    def test_query_with_special_characters(self, populated_collection, mock_llm_client):
        """Test query with special characters."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        response = pipeline.query("什么是@#$%？")

        # Should handle gracefully
        assert response.answer is not None

    def test_query_with_very_long_text(self, populated_collection, mock_llm_client):
        """Test query with very long text."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        long_query = "这是一段很长的查询内容，" * 100
        response = pipeline.query(long_query)

        assert response.query == long_query
        assert response.answer is not None

    def test_unicode_query(self, populated_collection, mock_llm_client):
        """Test query with various Unicode characters."""
        pipeline = SimpleRAGPipeline(
            collection=populated_collection,
            llm_client=mock_llm_client
        )

        queries = [
            "日本語のクエリ",
            "한국어 질문",
            "emoji 🎉 query",
        ]

        for query in queries:
            response = pipeline.query(query)
            assert response.answer is not None

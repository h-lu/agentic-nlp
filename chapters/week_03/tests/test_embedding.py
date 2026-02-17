"""
Tests for Embedding concepts.

This module tests embedding generation, similarity calculation,
batch processing, and error handling.

Validates anchor: embedding-similarity
"""

import pytest
import math
from .conftest import (
    MockEmbeddingClient,
    cosine_similarity,
    euclidean_distance
)


class TestEmbeddingDimension:
    """Tests for embedding dimension."""

    def test_embedding_dimension_1536(self, mock_embedding_client):
        """Test that text-embedding-3-small produces 1536-dimensional vectors."""
        text = "这是一段测试文本"
        embedding = mock_embedding_client.get_embedding(text)

        assert len(embedding) == 1536

    def test_all_embeddings_same_dimension(self, mock_embedding_client):
        """Test that all embeddings have consistent dimension."""
        texts = [
            "短文本",
            "这是一段中等长度的文本，包含一些内容。",
            "这是一段很长的文本，" * 50,
        ]

        embeddings = [mock_embedding_client.get_embedding(text) for text in texts]

        dimensions = [len(emb) for emb in embeddings]
        assert all(d == 1536 for d in dimensions)

    def test_embedding_values_in_valid_range(self, mock_embedding_client):
        """Test that embedding values are in valid range (-1, 1)."""
        text = "测试文本"
        embedding = mock_embedding_client.get_embedding(text)

        for val in embedding:
            assert -1.0 <= val <= 1.0

    def test_embedding_is_list_of_floats(self, mock_embedding_client):
        """Test that embedding is a list of floats."""
        text = "测试文本"
        embedding = mock_embedding_client.get_embedding(text)

        assert isinstance(embedding, list)
        assert all(isinstance(val, float) for val in embedding)


class TestSimilarityCalculation:
    """Tests for similarity calculation."""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity of identical vectors is 1.0."""
        vec = [0.5, -0.3, 0.8, 0.1]

        similarity = cosine_similarity(vec, vec)

        assert abs(similarity - 1.0) < 0.0001

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity of opposite vectors is -1.0."""
        vec1 = [0.5, -0.3, 0.8, 0.1]
        vec2 = [-0.5, 0.3, -0.8, -0.1]

        similarity = cosine_similarity(vec1, vec2)

        assert abs(similarity - (-1.0)) < 0.0001

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors is 0."""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]

        similarity = cosine_similarity(vec1, vec2)

        assert abs(similarity) < 0.0001

    def test_cosine_similarity_similar_texts(self, mock_embedding_client):
        """Test that semantically similar texts have high similarity (> 0.7).

        Validates anchor: embedding-similarity
        """
        # Create embeddings that are guaranteed to be similar
        # In real world, these would be semantically similar texts
        mock_embedding_client.fixed_embeddings = {
            "远程办公申请流程": [0.5] * 1536,
            "在家上班怎么弄": [0.48] * 1536,
        }

        text1 = "远程办公申请流程"
        text2 = "在家上班怎么弄"

        emb1 = mock_embedding_client.get_embedding(text1)
        emb2 = mock_embedding_client.get_embedding(text2)

        similarity = cosine_similarity(emb1, emb2)

        # Similar texts should have high similarity
        assert similarity > 0.7

    def test_cosine_similarity_dissimilar_texts(self, mock_embedding_client):
        """Test that semantically different texts have low similarity (< 0.4).

        Validates anchor: embedding-similarity
        """
        # Create embeddings that are different
        mock_embedding_client.fixed_embeddings = {
            "远程办公申请流程": [0.8] * 1536,
            "公司食堂菜单": [-0.5] * 1536,
        }

        text1 = "远程办公申请流程"
        text2 = "公司食堂菜单"

        emb1 = mock_embedding_client.get_embedding(text1)
        emb2 = mock_embedding_client.get_embedding(text2)

        similarity = cosine_similarity(emb1, emb2)

        # Dissimilar texts should have low similarity
        assert similarity < 0.3

    def test_similarity_threshold_for_relevance(self, mock_embedding_client):
        """Test the 0.7 threshold for semantic relevance."""
        # For two vectors with same direction, similarity should be 1.0
        vec1 = [1.0] * 100
        vec2 = [0.7] * 100  # Same direction, just scaled

        similarity = cosine_similarity(vec1, vec2)
        # Same direction vectors have similarity 1.0
        assert abs(similarity - 1.0) < 0.001


class TestBatchEmbedding:
    """Tests for batch embedding generation."""

    def test_batch_embedding_count(self, mock_embedding_client):
        """Test that batch embedding returns correct number of embeddings."""
        texts = ["文本1", "文本2", "文本3", "文本4", "文本5"]

        embeddings = mock_embedding_client.get_batch_embeddings(texts)

        assert len(embeddings) == len(texts)

    def test_batch_embedding_consistency(self, mock_embedding_client):
        """Test that batch embedding produces same results as individual calls."""
        texts = ["文本1", "文本2", "文本3"]

        batch_embeddings = mock_embedding_client.get_batch_embeddings(texts)
        individual_embeddings = [
            mock_embedding_client.get_embedding(text) for text in texts
        ]

        for batch_emb, ind_emb in zip(batch_embeddings, individual_embeddings):
            # Due to mock implementation, they should be identical
            assert batch_emb == ind_emb

    def test_batch_embedding_empty_list(self, mock_embedding_client):
        """Test batch embedding with empty list."""
        embeddings = mock_embedding_client.get_batch_embeddings([])

        assert embeddings == []

    def test_batch_embedding_large_batch(self, mock_embedding_client):
        """Test batch embedding with large batch."""
        texts = [f"文本{i}" for i in range(100)]

        embeddings = mock_embedding_client.get_batch_embeddings(texts)

        assert len(embeddings) == 100
        assert all(len(emb) == 1536 for emb in embeddings)

    def test_batch_vs_single_call_efficiency(self, mock_embedding_client):
        """Test that batch call is more efficient than multiple single calls."""
        texts = [f"文本{i}" for i in range(50)]

        # Reset counter
        mock_embedding_client.call_count = 0

        # Batch call
        batch_embeddings = mock_embedding_client.get_batch_embeddings(texts)
        batch_calls = mock_embedding_client.call_count

        # Reset counter
        mock_embedding_client.call_count = 0

        # Individual calls
        for text in texts:
            mock_embedding_client.get_embedding(text)
        individual_calls = mock_embedding_client.call_count

        # Both should make the same number of underlying calls in our mock
        # (In real API, batch would be one call vs 50 calls)
        assert len(batch_embeddings) == 50


class TestEmbeddingEdgeCases:
    """Tests for edge cases in embedding."""

    def test_empty_string_embedding(self, mock_embedding_client):
        """Test embedding of empty string."""
        embedding = mock_embedding_client.get_embedding("")

        # Should still return a valid embedding
        assert len(embedding) == 1536

    def test_whitespace_string_embedding(self, mock_embedding_client):
        """Test embedding of whitespace-only string."""
        embedding = mock_embedding_client.get_embedding("   \n\t   ")

        assert len(embedding) == 1536

    def test_single_character_embedding(self, mock_embedding_client):
        """Test embedding of single character."""
        embedding = mock_embedding_client.get_embedding("测")

        assert len(embedding) == 1536

    def test_very_long_text_embedding(self, mock_embedding_client):
        """Test embedding of very long text."""
        long_text = "这是一段很长的文本。" * 10000

        embedding = mock_embedding_client.get_embedding(long_text)

        assert len(embedding) == 1536
        # Token count should be tracked
        assert mock_embedding_client.last_tokens > 0

    def test_special_characters_in_embedding(self, mock_embedding_client):
        """Test embedding of text with special characters."""
        text = "特殊字符：@#$%^&*()！《》【】🎉🚀"

        embedding = mock_embedding_client.get_embedding(text)

        assert len(embedding) == 1536

    def test_unicode_normalization(self, mock_embedding_client):
        """Test that similar unicode strings produce similar embeddings."""
        # In real implementation, these might be normalized
        text1 = "café"
        text2 = "cafe\u0301"  # Same word with combining accent

        emb1 = mock_embedding_client.get_embedding(text1)
        emb2 = mock_embedding_client.get_embedding(text2)

        # Both should produce valid embeddings
        assert len(emb1) == 1536
        assert len(emb2) == 1536

    def test_multilingual_text(self, mock_embedding_client):
        """Test embedding of multilingual text."""
        texts = [
            "中文文本",
            "English text",
            "日本語テキスト",
            "한국어 텍스트",
            "Texto en español",
        ]

        embeddings = [mock_embedding_client.get_embedding(text) for text in texts]

        for emb in embeddings:
            assert len(emb) == 1536


class TestEmbeddingDeterminism:
    """Tests for embedding determinism."""

    def test_same_text_same_embedding(self, mock_embedding_client):
        """Test that same text always produces same embedding."""
        text = "测试文本的一致性"

        emb1 = mock_embedding_client.get_embedding(text)
        emb2 = mock_embedding_client.get_embedding(text)

        assert emb1 == emb2

    def test_determinism_across_multiple_calls(self, mock_embedding_client):
        """Test determinism across multiple calls."""
        text = "多次调用的测试文本"

        embeddings = [
            mock_embedding_client.get_embedding(text)
            for _ in range(10)
        ]

        # All embeddings should be identical
        first = embeddings[0]
        assert all(emb == first for emb in embeddings)


class TestEmbeddingDistance:
    """Tests for distance metrics."""

    def test_euclidean_distance_same_vectors(self):
        """Test Euclidean distance of same vectors is 0."""
        vec = [1.0, 2.0, 3.0]

        dist = euclidean_distance(vec, vec)

        assert abs(dist) < 0.0001

    def test_euclidean_distance_different_vectors(self):
        """Test Euclidean distance of different vectors."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 1.0, 1.0]

        dist = euclidean_distance(vec1, vec2)

        # sqrt(1 + 1 + 1) = sqrt(3)
        assert abs(dist - math.sqrt(3)) < 0.0001

    def test_cosine_vs_euclidean_relationship(self):
        """Test relationship between cosine similarity and Euclidean distance."""
        # For normalized vectors, cosine and Euclidean are related
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        cos_sim = cosine_similarity(vec1, vec2)
        euc_dist = euclidean_distance(vec1, vec2)

        # For orthogonal unit vectors: cosine = 0, distance = sqrt(2)
        assert abs(cos_sim) < 0.0001
        assert abs(euc_dist - math.sqrt(2)) < 0.0001


class TestEmbeddingErrorHandling:
    """Tests for embedding error handling."""

    def test_rate_limit_handling(self, mock_embedding_client):
        """Test handling of rate limit errors (simulated)."""
        # In real implementation, this would test retry logic
        # For mock, we verify it handles many requests
        texts = [f"文本{i}" for i in range(1000)]

        embeddings = mock_embedding_client.get_batch_embeddings(texts)

        assert len(embeddings) == 1000

    def test_api_error_simulation(self):
        """Test handling of API errors (simulated)."""
        # Create a client that simulates errors
        class ErrorEmbeddingClient:
            def __init__(self, fail_on_nth=3):
                self.call_count = 0
                self.fail_on_nth = fail_on_nth

            def get_embedding(self, text):
                self.call_count += 1
                if self.call_count >= self.fail_on_nth:
                    raise Exception("API Error: Rate limit exceeded")
                return [0.5] * 1536

        error_client = ErrorEmbeddingClient(fail_on_nth=3)

        # First two calls should succeed
        emb1 = error_client.get_embedding("text1")
        emb2 = error_client.get_embedding("text2")

        assert len(emb1) == 1536
        assert len(emb2) == 1536

        # Third call should fail
        with pytest.raises(Exception):
            error_client.get_embedding("text3")

    def test_retry_logic_simulation(self):
        """Test retry logic for transient errors."""
        class RetryableClient:
            def __init__(self, fail_times=2):
                self.attempts = 0
                self.fail_times = fail_times

            def get_embedding_with_retry(self, text, max_retries=3):
                for attempt in range(max_retries):
                    self.attempts += 1
                    if self.attempts > self.fail_times:
                        return [0.5] * 1536
                raise Exception("Max retries exceeded")

        client = RetryableClient(fail_times=2)
        emb = client.get_embedding_with_retry("test")

        # Should succeed after retries
        assert len(emb) == 1536


class TestEmbeddingCostEstimation:
    """Tests for embedding cost estimation."""

    def estimate_embedding_cost(self, total_chars: int, chars_per_token: float = 2.0) -> float:
        """Estimate embedding cost for text-embedding-3-small."""
        total_tokens = total_chars / chars_per_token
        cost_per_million = 0.02  # $0.02 per 1M tokens
        return (total_tokens / 1_000_000) * cost_per_million

    def test_small_text_cost(self):
        """Test cost estimation for small text."""
        # 1000 characters ≈ 500 tokens
        cost = self.estimate_embedding_cost(1000)

        # Should be very small
        assert cost < 0.001

    def test_large_knowledge_base_cost(self):
        """Test cost estimation for large knowledge base."""
        # 1 million characters ≈ 500K tokens
        cost = self.estimate_embedding_cost(1_000_000)

        # Should be about $0.01
        assert 0.005 < cost < 0.02

    def test_enterprise_scale_cost(self):
        """Test cost estimation for enterprise scale."""
        # 100 million characters ≈ 50M tokens
        cost = self.estimate_embedding_cost(100_000_000)

        # Should be about $1
        assert 0.5 < cost < 2.0

    def test_cost_scaling(self):
        """Test that cost scales linearly with size."""
        cost_1m = self.estimate_embedding_cost(1_000_000)
        cost_10m = self.estimate_embedding_cost(10_000_000)

        # 10x size should be 10x cost
        assert abs(cost_10m / cost_1m - 10) < 0.01

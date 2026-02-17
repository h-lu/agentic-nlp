"""
Pytest configuration and fixtures for Week 04 tests.

This module provides common fixtures for testing Advanced RAG concepts including
hybrid search, re-ranking, query rewriting, and RAGAS evaluation.
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import hashlib


# =============================================================================
# Mock Classes for Testing (simulating the actual implementations)
# =============================================================================

@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search."""
    top_k: int = 20
    alpha: float = 0.5  # Weight for vector search (0-1), BM25 weight is 1-alpha
    rrf_k: int = 60  # RRF constant


@dataclass
class SearchResult:
    """Single search result."""
    content: str
    id: str
    score: float = 0.0
    distance: float = 0.0
    metadata: Dict = field(default_factory=dict)


class MockBM25Index:
    """Mock BM25 index for testing."""

    def __init__(self, documents: List[str] = None):
        """
        Initialize BM25 index.

        Args:
            documents: List of documents to index
        """
        self.documents = documents or []
        self.tokenized_docs = [doc.split() for doc in self.documents]

    def get_scores(self, query: str) -> List[float]:
        """
        Get BM25 scores for a query.

        Simplified BM25: count query term occurrences in each document.
        """
        query_tokens = set(query.split())
        scores = []

        for doc_tokens in self.tokenized_docs:
            score = 0.0
            for token in query_tokens:
                # Count occurrences
                score += doc_tokens.count(token) * 1.0
            scores.append(score)

        return scores

    def get_top_n(self, query: str, n: int = 10) -> List[tuple[int, float]]:
        """Get top N documents by score."""
        scores = self.get_scores(query)
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed[:n]


class MockVectorCollection:
    """Mock vector collection (like ChromaDB)."""

    def __init__(self, documents: List[str] = None):
        """Initialize with documents."""
        self.documents = documents or []
        self.embeddings: List[List[float]] = []

    def add_documents(self, documents: List[str]):
        """Add documents to collection."""
        self.documents.extend(documents)
        # Generate mock embeddings
        for doc in documents:
            self.embeddings.append(self._mock_embedding(doc))

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate deterministic mock embedding."""
        hash_bytes = hashlib.md5(text.encode()).digest()
        embedding = []
        for i in range(1536):
            byte_val = hash_bytes[i % len(hash_bytes)]
            val = (byte_val / 128.0) - 1.0
            embedding.append(round(val, 6))
        return embedding

    def query(self, query_text: str, n_results: int = 10) -> List[Dict]:
        """
        Query the collection.

        Returns results with distance (lower = more similar).
        """
        query_emb = self._mock_embedding(query_text)

        # Calculate distances (1 - cosine similarity)
        results = []
        for i, doc_emb in enumerate(self.embeddings):
            distance = 1 - self._cosine_similarity(query_emb, doc_emb)
            results.append({
                "content": self.documents[i],
                "id": f"vec_{i}",
                "distance": distance
            })

        # Sort by distance and return top n
        results.sort(key=lambda x: x["distance"])
        return results[:n_results]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


class HybridRetriever:
    """
    Mock hybrid retriever combining vector and BM25 search.

    Uses Reciprocal Rank Fusion (RRF) to merge results.
    """

    def __init__(
        self,
        vector_collection: MockVectorCollection = None,
        bm25_index: MockBM25Index = None,
        config: HybridSearchConfig = None
    ):
        """Initialize hybrid retriever."""
        self.vector_col = vector_collection or MockVectorCollection()
        self.bm25 = bm25_index or MockBM25Index()
        self.config = config or HybridSearchConfig()

    def search(self, query: str, top_k: int = None) -> List[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of fused and ranked results
        """
        top_k = top_k or self.config.top_k

        # Get vector results
        vec_results = self.vector_col.query(query, n_results=top_k)

        # Get BM25 results
        bm25_results_raw = self.bm25.get_top_n(query, n=top_k)
        bm25_results = [
            {
                "content": self.bm25.documents[idx],
                "id": f"bm25_{idx}",
                "score": score
            }
            for idx, score in bm25_results_raw
        ]

        # RRF fusion
        fused = self._reciprocal_rank_fusion(
            vec_results,
            bm25_results,
            k=self.config.rrf_k,
            alpha=self.config.alpha
        )

        return fused[:top_k]

    def _reciprocal_rank_fusion(
        self,
        vec_results: List[Dict],
        bm25_results: List[Dict],
        k: int = 60,
        alpha: float = 0.5
    ) -> List[SearchResult]:
        """Perform RRF fusion."""
        scores = {}

        # Vector search scores
        for rank, doc in enumerate(vec_results):
            doc_id = doc["id"]
            vec_score = 1 / (k + rank + 1)
            scores[doc_id] = {
                "score": alpha * vec_score,
                "content": doc["content"],
                "id": doc_id
            }

        # BM25 scores
        for rank, doc in enumerate(bm25_results):
            doc_id = doc["id"]
            bm25_score = 1 / (k + rank + 1)
            if doc_id in scores:
                scores[doc_id]["score"] += (1 - alpha) * bm25_score
            else:
                scores[doc_id] = {
                    "score": (1 - alpha) * bm25_score,
                    "content": doc["content"],
                    "id": doc_id
                }

        # Sort by score
        sorted_items = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

        return [
            SearchResult(
                content=item["content"],
                id=item["id"],
                score=item["score"]
            )
            for doc_id, item in sorted_items
        ]


class MockCrossEncoder:
    """Mock Cross-Encoder for re-ranking."""

    def __init__(self, model_name: str = "mock-reranker"):
        """Initialize mock model."""
        self.model_name = model_name
        self.call_count = 0

    def predict(self, pairs: List[tuple[str, str]]) -> List[float]:
        """
        Predict relevance scores for query-document pairs.

        Returns scores in [0, 1] range.
        """
        self.call_count += 1
        scores = []

        for query, doc in pairs:
            # Simulated scoring based on keyword overlap
            query_words = set(query.lower().split())
            doc_words = set(doc.lower().split())

            overlap = len(query_words & doc_words)
            total = len(query_words)

            if total == 0:
                score = 0.0
            else:
                # Base score from overlap
                score = overlap / total

                # Add some randomness for realism
                import random
                random.seed(hash(query + doc) % 1000)
                score += random.uniform(-0.1, 0.1)
                score = max(0.0, min(1.0, score))

            scores.append(score)

        return scores


class CrossEncoderReranker:
    """Mock Cross-Encoder re-ranker."""

    def __init__(self, model: MockCrossEncoder = None):
        """Initialize re-ranker."""
        self.model = model or MockCrossEncoder()

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 3
    ) -> List[SearchResult]:
        """
        Re-rank documents using Cross-Encoder.

        Args:
            query: Search query
            documents: List of documents with 'content' field
            top_k: Number of top results to return

        Returns:
            Re-ranked results
        """
        if not documents:
            return []

        # Build pairs
        pairs = [[query, doc.get("content", "")] for doc in documents]

        # Get scores
        scores = self.model.predict(pairs)

        # Combine and sort
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        return [
            SearchResult(
                content=doc.get("content", ""),
                id=doc.get("id", f"rerank_{i}"),
                score=float(score),
                metadata=doc.get("metadata", {})
            )
            for i, (doc, score) in enumerate(scored_docs[:top_k])
        ]


class MockLLMClient:
    """Mock LLM client for query rewriting."""

    def __init__(self, responses: Dict[str, str] = None):
        """Initialize with predefined responses."""
        self.responses = responses or {}
        self.call_count = 0

    def rewrite(self, query: str) -> str:
        """Simulate query rewriting."""
        self.call_count += 1

        # Check predefined responses
        for key, response in self.responses.items():
            if key in query.lower():
                return response

        # Default behavior: expand query
        expansions = {
            "报销": "费用报销申请流程和所需材料",
            "请假": "员工年假申请流程和审批要求",
            "gpu": "GPU 计算资源申请流程",
            "远程": "员工远程办公申请流程",
        }

        query_lower = query.lower()
        for key, expansion in expansions.items():
            if key in query_lower:
                return expansion

        # Return original if no expansion
        return query

    def expand(self, query: str, num_variants: int = 3) -> List[str]:
        """Generate query variants."""
        base = self.rewrite(query)
        variants = [base]

        # Add some variations
        if "远程" in query or "办公" in query:
            variants.extend([
                "在家办公申请条件和流程",
                "WFH 工作方式申请要求"
            ])
        elif "报销" in query:
            variants.extend([
                "费用报销需要什么材料",
                "如何申请费用报销"
            ])
        elif "gpu" in query.lower():
            variants.extend([
                "GPU 资源配额申请",
                "计算资源申请流程"
            ])

        return variants[:num_variants]


class QueryRewriter:
    """Query rewriter using LLM."""

    def __init__(self, llm_client: MockLLMClient = None):
        """Initialize query rewriter."""
        self.llm = llm_client or MockLLMClient()

    def rewrite(self, query: str) -> str:
        """Rewrite a single query."""
        return self.llm.rewrite(query)

    def rewrite_with_expansion(self, query: str, num_variants: int = 3) -> List[str]:
        """Generate multiple query variants."""
        return self.llm.expand(query, num_variants)


@dataclass
class RAGASEvaluationResult:
    """Result from RAGAS evaluation."""
    context_precision: float
    faithfulness: float
    answer_relevancy: float
    context_recall: float


class MockRAGASEvaluator:
    """Mock RAGAS evaluator."""

    def __init__(self):
        """Initialize evaluator."""
        self.evaluation_count = 0

    def evaluate(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str] = None
    ) -> RAGASEvaluationResult:
        """
        Evaluate RAG outputs.

        Returns mock scores in [0, 1] range.
        """
        self.evaluation_count += 1

        # Generate realistic-looking scores
        import random
        random.seed(self.evaluation_count)

        return RAGASEvaluationResult(
            context_precision=random.uniform(0.6, 0.95),
            faithfulness=random.uniform(0.65, 0.95),
            answer_relevancy=random.uniform(0.7, 0.95),
            context_recall=random.uniform(0.55, 0.90)
        )


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for testing."""
    return [
        "2024 年报假政策：员工每年可享受 5 天年假，需提前 7 天申请。",
        "2023 年报假政策：员工每年可享受 5 天年假，需提前 3 天申请。",
        "GPU 资源申请流程：需要填写资源申请表，经部门经理审批。",
        "TB 级别存储申请：单个项目最多申请 10TB 存储空间。",
        "公司远程办公政策：员工每周可远程办公最多 2 天，需提前 3 天申请。",
        "费用报销规定：费用发生后 30 天内提交报销申请，超期不予报销。",
        "员工健身房福利：公司健身房位于 B1 层，开放时间为早 6 点至晚 10 点。",
        "2024 年度绩效考核：绩效评级分为 A、B、C、D 四个等级。",
    ]


@pytest.fixture
def vector_collection(sample_documents):
    """Fixture providing a mock vector collection with documents."""
    collection = MockVectorCollection()
    collection.add_documents(sample_documents)
    return collection


@pytest.fixture
def bm25_index(sample_documents):
    """Fixture providing a mock BM25 index with documents."""
    return MockBM25Index(sample_documents)


@pytest.fixture
def hybrid_retriever(vector_collection, bm25_index):
    """Fixture providing a hybrid retriever."""
    return HybridRetriever(
        vector_collection=vector_collection,
        bm25_index=bm25_index,
        config=HybridSearchConfig(alpha=0.5, top_k=20)
    )


@pytest.fixture
def hybrid_config():
    """Fixture providing hybrid search configuration."""
    return HybridSearchConfig(alpha=0.5, top_k=20, rrf_k=60)


@pytest.fixture
def mock_cross_encoder():
    """Fixture providing a mock Cross-Encoder model."""
    return MockCrossEncoder()


@pytest.fixture
def reranker(mock_cross_encoder):
    """Fixture providing a re-ranker."""
    return CrossEncoderReranker(model=mock_cross_encoder)


@pytest.fixture
def mock_llm_client():
    """Fixture providing a mock LLM client."""
    return MockLLMClient(
        responses={
            "报销": "费用报销申请流程和所需材料",
            "请假": "员工年假申请流程和审批要求",
            "gpu": "GPU 计算资源申请流程",
        }
    )


@pytest.fixture
def query_rewriter(mock_llm_client):
    """Fixture providing a query rewriter."""
    return QueryRewriter(llm_client=mock_llm_client)


@pytest.fixture
def ragas_evaluator():
    """Fixture providing a mock RAGAS evaluator."""
    return MockRAGASEvaluator()


@pytest.fixture
def evaluation_dataset():
    """Fixture providing sample evaluation dataset."""
    return {
        "questions": [
            "2024 年报假政策是什么？",
            "GPU 资源怎么申请？",
            "TB 级别存储怎么申请？"
        ],
        "answers": [
            "根据 2024 年报假政策，员工每年可享受 5 天年假，需提前 7 天申请。",
            "GPU 资源需要填写资源申请表，经部门经理审批后分配。",
            "单个项目最多申请 10TB 存储空间，需提交存储资源申请表。"
        ],
        "contexts": [
            ["2024 年报假政策：员工每年可享受 5 天年假，需提前 7 天申请。"],
            ["GPU 资源申请流程：需要填写资源申请表，经部门经理审批。"],
            ["TB 级别存储申请：单个项目最多申请 10TB 存储空间。"]
        ],
        "ground_truths": [
            "5 天年假，提前 7 天申请",
            "填写申请表，部门经理审批",
            "最多 10TB"
        ]
    }


@pytest.fixture
def candidate_results(sample_documents):
    """Fixture providing candidate search results for re-ranking."""
    return [
        {"content": doc, "id": f"doc_{i}"}
        for i, doc in enumerate(sample_documents[:5])
    ]


# =============================================================================
# Helper Functions
# =============================================================================

def reciprocal_rank_fusion(
    vec_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60,
    alpha: float = 0.5
) -> List[Dict]:
    """
    RRF fusion algorithm for testing.

    Args:
        vec_results: Vector search results
        bm25_results: BM25 search results
        k: RRF constant
        alpha: Vector search weight

    Returns:
        Fused and ranked results
    """
    scores = {}

    for rank, doc in enumerate(vec_results):
        doc_id = doc.get("id", doc.get("content", ""))
        vec_score = 1 / (k + rank + 1)
        scores[doc_id] = {"score": alpha * vec_score, "doc": doc}

    for rank, doc in enumerate(bm25_results):
        doc_id = doc.get("id", doc.get("content", ""))
        bm25_score = 1 / (k + rank + 1)
        if doc_id in scores:
            scores[doc_id]["score"] += (1 - alpha) * bm25_score
        else:
            scores[doc_id] = {"score": (1 - alpha) * bm25_score, "doc": doc}

    sorted_items = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    return [{"id": doc_id, **item["doc"], "rrf_score": item["score"]} for doc_id, item in sorted_items]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity."""
    import math
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

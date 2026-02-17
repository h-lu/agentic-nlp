"""
Pytest configuration and fixtures for Week 03 tests.

This module provides common fixtures for testing RAG concepts including
text chunking, embedding, ChromaDB operations, and the full RAG pipeline.
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# =============================================================================
# Mock Classes for Testing (simulating the actual implementations)
# =============================================================================

@dataclass
class ChunkConfig:
    """Configuration for text chunking."""
    chunk_size: int = 500
    chunk_overlap: int = 50
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", "。", "！", "？", "；", " ", ""])


@dataclass
class TextChunk:
    """Represents a single text chunk."""
    content: str
    index: int
    metadata: Dict = field(default_factory=dict)


class TextChunker:
    """Mock text chunker for testing without LangChain dependency."""

    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()

    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Split text into chunks.

        Args:
            text: Input text to chunk

        Returns:
            List of TextChunk objects
        """
        if not text:
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.config.chunk_size
            chunk_content = text[start:end]
            chunks.append(TextChunk(
                content=chunk_content,
                index=chunk_index,
                metadata={"char_start": start, "char_end": min(end, len(text))}
            ))
            chunk_index += 1
            start = end - self.config.chunk_overlap

            # Avoid infinite loop when overlap >= chunk_size
            if self.config.chunk_overlap >= self.config.chunk_size:
                start = end

        return chunks

    def chunk_by_separator(self, text: str) -> List[TextChunk]:
        """
        Split text by separators (simplified recursive splitting simulation).

        Args:
            text: Input text to chunk

        Returns:
            List of TextChunk objects
        """
        if not text:
            return []

        # Try splitting by separators in order
        for separator in self.config.separators:
            if separator and separator in text:
                parts = text.split(separator)
                chunks = []
                current_chunk = ""
                chunk_index = 0

                for part in parts:
                    if len(current_chunk) + len(part) + len(separator) <= self.config.chunk_size:
                        current_chunk += (separator if current_chunk else "") + part
                    else:
                        if current_chunk:
                            chunks.append(TextChunk(
                                content=current_chunk.strip(),
                                index=chunk_index,
                                metadata={}
                            ))
                            chunk_index += 1
                        current_chunk = part

                if current_chunk:
                    chunks.append(TextChunk(
                        content=current_chunk.strip(),
                        index=chunk_index,
                        metadata={}
                    ))

                return chunks

        # No separator found, fall back to fixed size
        return self.chunk_text(text)


class MockEmbeddingClient:
    """Mock embedding client for testing without real API calls."""

    # Simulated embedding dimension for text-embedding-3-small
    EMBEDDING_DIM = 1536

    def __init__(self, fixed_embeddings: Dict[str, List[float]] = None):
        """
        Initialize mock client.

        Args:
            fixed_embeddings: Pre-defined embeddings for specific texts
        """
        self.fixed_embeddings = fixed_embeddings or {}
        self.call_count = 0
        self.last_tokens = 0

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.

        Args:
            text: Input text

        Returns:
            1536-dimensional embedding vector
        """
        self.call_count += 1
        self.last_tokens = len(text) // 2  # Rough token estimate

        # Return fixed embedding if available
        if text in self.fixed_embeddings:
            return self.fixed_embeddings[text]

        # Generate deterministic pseudo-embedding based on text hash
        import hashlib
        hash_bytes = hashlib.md5(text.encode()).digest()
        # Create a pseudo-random but deterministic embedding
        embedding = []
        for i in range(self.EMBEDDING_DIM):
            # Use hash bytes cyclically to generate values
            byte_val = hash_bytes[i % len(hash_bytes)]
            # Normalize to [-1, 1] range
            val = (byte_val / 128.0) - 1.0
            embedding.append(round(val, 6))

        return embedding

    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        return [self.get_embedding(text) for text in texts]


class MockChromaCollection:
    """Mock ChromaDB collection for testing."""

    def __init__(self, name: str = "test_collection"):
        self.name = name
        self.documents: List[str] = []
        self.metadatas: List[Dict] = []
        self.ids: List[str] = []
        self.embeddings: List[List[float]] = []
        self._embedding_client = MockEmbeddingClient()

    def add(
        self,
        documents: List[str],
        metadatas: List[Dict] = None,
        ids: List[str] = None,
        embeddings: List[List[float]] = None
    ):
        """Add documents to the collection."""
        if ids is None:
            ids = [f"doc_{len(self.ids) + i}" for i in range(len(documents))]

        if metadatas is None:
            metadatas = [{} for _ in documents]

        if embeddings is None:
            embeddings = [self._embedding_client.get_embedding(doc) for doc in documents]

        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)
        self.embeddings.extend(embeddings)

    def query(
        self,
        query_texts: List[str] = None,
        query_embeddings: List[List[float]] = None,
        n_results: int = 10,
        where: Dict = None
    ) -> Dict:
        """
        Query the collection.

        Args:
            query_texts: Query text (will be embedded)
            query_embeddings: Pre-computed query embeddings
            n_results: Number of results to return
            where: Metadata filter (simplified)

        Returns:
            Query results with ids, documents, metadatas, distances
        """
        if query_embeddings is None and query_texts:
            query_embeddings = [
                self._embedding_client.get_embedding(qt) for qt in query_texts
            ]

        if not self.documents or not query_embeddings:
            return {
                "ids": [[] for _ in query_texts] if query_texts else [],
                "documents": [[] for _ in query_texts] if query_texts else [],
                "metadatas": [[] for _ in query_texts] if query_texts else [],
                "distances": [[] for _ in query_texts] if query_texts else [],
            }

        results = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        for query_emb in query_embeddings:
            # Calculate distances (1 - cosine similarity)
            distances = []
            for doc_emb in self.embeddings:
                similarity = self._cosine_similarity(query_emb, doc_emb)
                distance = 1 - similarity
                distances.append(distance)

            # Get top-k indices
            sorted_indices = sorted(range(len(distances)), key=lambda i: distances[i])
            top_indices = sorted_indices[:n_results]

            # Apply metadata filter if provided
            if where:
                filtered_indices = []
                for idx in top_indices:
                    match = True
                    for key, value in where.items():
                        if self.metadatas[idx].get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_indices.append(idx)
                top_indices = filtered_indices

            results["ids"].append([self.ids[i] for i in top_indices])
            results["documents"].append([self.documents[i] for i in top_indices])
            results["metadatas"].append([self.metadatas[i] for i in top_indices])
            results["distances"].append([distances[i] for i in top_indices])

        return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def count(self) -> int:
        """Return number of documents in collection."""
        return len(self.documents)

    def delete(self, ids: List[str] = None, where: Dict = None):
        """Delete documents from collection."""
        if ids:
            indices_to_remove = [self.ids.index(id_) for id_ in ids if id_ in self.ids]
            for idx in sorted(indices_to_remove, reverse=True):
                self.ids.pop(idx)
                self.documents.pop(idx)
                self.metadatas.pop(idx)
                self.embeddings.pop(idx)


class MockChromaClient:
    """Mock ChromaDB client for testing."""

    def __init__(self):
        self.collections: Dict[str, MockChromaCollection] = {}

    def create_collection(
        self,
        name: str,
        metadata: Dict = None
    ) -> MockChromaCollection:
        """Create a new collection."""
        if name in self.collections:
            raise ValueError(f"Collection {name} already exists")
        collection = MockChromaCollection(name=name)
        self.collections[name] = collection
        return collection

    def get_collection(self, name: str) -> MockChromaCollection:
        """Get an existing collection."""
        if name not in self.collections:
            raise ValueError(f"Collection {name} does not exist")
        return self.collections[name]

    def get_or_create_collection(
        self,
        name: str,
        metadata: Dict = None
    ) -> MockChromaCollection:
        """Get or create a collection."""
        if name not in self.collections:
            return self.create_collection(name, metadata)
        return self.collections[name]

    def delete_collection(self, name: str):
        """Delete a collection."""
        if name in self.collections:
            del self.collections[name]

    def list_collections(self) -> List[str]:
        """List all collection names."""
        return list(self.collections.keys())


class MockLLMClient:
    """Mock LLM client for RAG pipeline testing."""

    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_usage = MagicMock(total_tokens=100)

    def generate(self, prompt: str) -> str:
        """Generate response for prompt."""
        self.call_count += 1

        # Try to find a matching response based on keywords
        for key, response in self.responses.items():
            if key in prompt:
                return response

        # Default response for RAG-style prompts
        if "参考文档" in prompt or "参考" in prompt:
            return "根据参考文档，相关信息如下：[基于提供的文档内容回答]"

        return "我无法回答这个问题，因为参考文档中没有相关信息。"


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    answer: str
    sources: List[Dict]
    query: str


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for testing."""
    return [
        "远程办公需要提前在 OA 系统申请，经直属经理审批后方可生效。每周远程办公天数不超过2天。",
        "员工报销需要在费用发生后的 30 天内提交，超期不予报销。报销金额超过5000元需要总监审批。",
        "公司健身房位于 B1 层，开放时间为早 6 点至晚 10 点。员工凭工牌进入。",
        "年假天数根据工龄确定：入职满1年5天，满3年10天，满5年15天。",
        "公司提供午餐补贴，每人每天50元，按实际出勤天数计算。",
    ]


@pytest.fixture
def long_document():
    """Fixture providing a long document for chunking tests."""
    return """
    公司员工手册

    第一章 总则

    本手册旨在规范公司员工的行为准则，明确各项管理制度，促进企业文化建设。
    公司坚持"以人为本"的管理理念，尊重每一位员工的价值和贡献。

    第二章 工作时间与考勤

    标准工作时间为周一至周五，每天8小时。上午9:00-12:00，下午13:30-18:30。
    员工应按时上下班，不得迟到早退。每月迟到超过3次将扣除当月全勤奖。

    迟到10分钟以内，每次扣除50元；迟到10-30分钟，每次扣除100元；
    迟到超过30分钟，按旷工半天处理。旷工半天扣除当日工资的50%。

    请假需提前在OA系统提交申请，经直属经理审批后方可生效。
    病假需提供医院证明，事假需提前3天申请。

    第三章 薪酬福利

    薪酬由基本工资、绩效奖金、年终奖金三部分组成。
    基本工资根据岗位级别确定，每年进行一次调薪评估。

    绩效奖金与个人绩效评级挂钩：A级120%，B级100%，C级80%，D级无奖金。
    年终奖金根据公司年度业绩和个人贡献确定，一般为1-3个月工资。

    公司为员工缴纳五险一金，包括养老保险、医疗保险、失业保险、
    工伤保险、生育保险和住房公积金。

    第四章 培训发展

    公司为员工提供多样化的培训机会，包括入职培训、岗位培训、
    管理培训和专业技能培训。

    员工可根据个人发展需求申请外部培训，公司承担培训费用，
    但需签订培训协议，承诺服务期限。
    """


@pytest.fixture
def chinese_text():
    """Fixture providing Chinese text for separator testing."""
    return "这是第一句话。这是第二句话！这是第三句话？还有分号；最后是结尾。"


@pytest.fixture
def chunk_config():
    """Fixture providing default chunk configuration."""
    return ChunkConfig(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def text_chunker(chunk_config):
    """Fixture providing a TextChunker instance."""
    return TextChunker(config=chunk_config)


@pytest.fixture
def mock_embedding_client():
    """Fixture providing a mock embedding client."""
    return MockEmbeddingClient()


@pytest.fixture
def mock_chroma_client():
    """Fixture providing a mock ChromaDB client."""
    return MockChromaClient()


@pytest.fixture
def mock_llm_client():
    """Fixture providing a mock LLM client."""
    return MockLLMClient(
        responses={
            "远程办公": "根据公司政策，远程办公需要提前申请并获得批准。",
            "报销": "报销需要在30天内提交申请。",
            "健身房": "公司健身房位于B1层，开放时间为早6点至晚10点。",
        }
    )


@pytest.fixture
def populated_collection(mock_chroma_client, sample_documents):
    """Fixture providing a ChromaDB collection with sample documents."""
    collection = mock_chroma_client.create_collection("test_docs")
    collection.add(
        documents=sample_documents,
        metadatas=[
            {"source": "remote_work_policy.pdf", "page": 1},
            {"source": "reimbursement_policy.docx", "page": 2},
            {"source": "employee_benefits.pdf", "page": 5},
            {"source": "leave_policy.pdf", "page": 1},
            {"source": "employee_benefits.pdf", "page": 8},
        ],
        ids=["doc_001", "doc_002", "doc_003", "doc_004", "doc_005"]
    )
    return collection


@pytest.fixture
def temp_chroma_dir(tmp_path):
    """Fixture providing a temporary directory for ChromaDB persistence."""
    chroma_dir = tmp_path / "chromadb"
    chroma_dir.mkdir()
    return str(chroma_dir)


@pytest.fixture
def temp_knowledge_base(tmp_path, sample_documents):
    """Fixture providing a temporary knowledge base directory with files."""
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()

    # Create sample document files
    for i, doc in enumerate(sample_documents):
        doc_file = kb_dir / f"doc_{i+1}.md"
        doc_file.write_text(doc, encoding="utf-8")

    return str(kb_dir)


# =============================================================================
# Helper Functions
# =============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Euclidean distance between two vectors."""
    import math
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def build_rag_prompt(query: str, documents: List[Dict]) -> str:
    """Build a RAG-style prompt with context."""
    context = "\n\n".join([
        f"【参考文档 {i+1}】\n来源：{doc.get('source', 'unknown')}\n内容：{doc.get('content', '')}"
        for i, doc in enumerate(documents)
    ])

    return f"""角色：你是公司的内部问答助手。

参考文档：
{context}

用户问题：{query}

请根据参考文档回答问题。"""


def parse_rag_response(response: str) -> str:
    """Parse and clean RAG response."""
    return response.strip()

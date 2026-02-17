"""
混合检索器（Hybrid Retriever）

结合向量检索和 BM25 关键词检索，使用 RRF 算法融合结果。

核心思想：
- 向量检索：擅长语义理解，但搞不定期确匹配
- BM25：擅长精确匹配，但理解不了同义词
- RRF 融合：两者结合，两全其美
"""

from typing import List, Dict, Optional

try:
    from rank_bm25 import BM25Okapi
    import jieba
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False


def reciprocal_rank_fusion(
    vec_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60,
    alpha: float = 0.5
) -> List[Dict]:
    """
    RRF（Reciprocal Rank Fusion）融合算法

    核心思想：不要关心绝对分数，只关心排名位置。
    公式：score = alpha/(k+rank_vec) + (1-alpha)/(k+rank_bm25)

    Args:
        vec_results: 向量检索结果，按相似度排序
        bm25_results: BM25 检索结果，按分数排序
        k: RRF 常数，通常取 60
        alpha: 向量检索权重（0-1），BM25 权重为 1-alpha

    Returns:
        融合后的结果列表
    """
    # 构建文档 ID 到排名的映射
    vec_ranks = {}
    for rank, doc in enumerate(vec_results):
        doc_id = doc.get("id", doc.get("content", ""))
        vec_ranks[doc_id] = rank

    bm25_ranks = {}
    for rank, doc in enumerate(bm25_results):
        doc_id = doc.get("id", doc.get("content", ""))
        bm25_ranks[doc_id] = rank

    # 计算融合分数
    scores = {}

    # 向量检索分数
    for doc_id, rank in vec_ranks.items():
        vec_score = 1 / (k + rank + 1)
        scores[doc_id] = alpha * vec_score

    # BM25 分数
    for doc_id, rank in bm25_ranks.items():
        bm25_score = 1 / (k + rank + 1)
        if doc_id in scores:
            scores[doc_id] += (1 - alpha) * bm25_score
        else:
            scores[doc_id] = (1 - alpha) * bm25_score

    # 按分数排序
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [{"id": doc_id, "fusion_score": score} for doc_id, score in sorted_docs]


class HybridRetriever:
    """混合检索：向量 + BM25"""

    def __init__(
        self,
        chroma_collection,
        top_k: int = 20,
        alpha: float = 0.5
    ):
        """
        Args:
            chroma_collection: ChromaDB Collection
            top_k: 返回的文档数量
            alpha: 向量检索权重（0-1），BM25 权重为 1-alpha
        """
        self.collection = chroma_collection
        self.top_k = top_k
        self.alpha = alpha
        self.bm25_index: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []

    def build_bm25_index(self, documents: List[str], doc_ids: Optional[List[str]] = None):
        """
        构建 BM25 索引

        Args:
            documents: 文档列表
            doc_ids: 文档 ID 列表（可选）
        """
        if not BM25_AVAILABLE:
            raise ImportError(
                "rank_bm25 或 jieba 未安装。"
                "请运行：pip install rank-bm25 jieba"
            )

        # 使用 jieba 分词
        tokenized_docs = [list(jieba.cut(doc)) for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        self.documents = documents
        if doc_ids:
            self.doc_ids = doc_ids
        else:
            self.doc_ids = [f"doc_{i}" for i in range(len(documents))]

    def search(self, query: str) -> List[Dict]:
        """
        混合检索

        步骤：
        1. 向量检索
        2. BM25 检索
        3. RRF 融合
        """
        # 1. 向量检索
        vec_results = self._vector_search(query, self.top_k)

        # 2. BM25 检索
        bm25_results = self._bm25_search(query, self.top_k)

        # 3. RRF 融合
        fused = reciprocal_rank_fusion(
            vec_results,
            bm25_results,
            k=60,
            alpha=self.alpha
        )

        # 补充文档内容
        for result in fused:
            doc_id = result["id"]
            # 从原始结果中找到文档内容
            for vec_res in vec_results:
                if vec_res["id"] == doc_id:
                    result["content"] = vec_res["content"]
                    result["vec_distance"] = vec_res.get("distance")
                    break
            for bm25_res in bm25_results:
                if bm25_res["id"] == doc_id:
                    if "content" not in result:
                        result["content"] = bm25_res["content"]
                    result["bm25_score"] = bm25_res.get("score")
                    break

        return fused[:self.top_k]

    def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """向量检索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        return [
            {
                "content": doc,
                "id": meta.get("doc_id", f"vec_{i}"),
                "distance": dist,
                "metadata": meta
            }
            for i, (doc, dist, meta) in enumerate(zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            ))
        ]

    def _bm25_search(self, query: str, top_k: int) -> List[Dict]:
        """BM25 检索"""
        if self.bm25_index is None:
            return []

        # 使用 jieba 分词
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25_index.get_scores(tokenized_query)

        # 获取 Top-K
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        return [
            {
                "content": self.documents[i],
                "id": self.doc_ids[i],
                "score": float(scores[i])
            }
            for i in top_indices
            if scores[i] > 0  # 只返回有分数的
        ]

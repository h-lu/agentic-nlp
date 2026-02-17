#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 04 作业参考实现

本文件是 Week 04 作业的参考实现，提供基础功能的完整代码。
当学生在作业中遇到困难时，可以查看此文件作为参考。

作业要求：
1. 实现混合检索（向量 + BM25）
2. 实现查询重写功能
3. 实现 RRF 融合算法
4. 对系统进行简单评估

注意：这是参考实现，学生应该先自己尝试，遇到困难时再查看。
"""

from __future__ import annotations

import os
from typing import List, Dict, Optional
from dataclasses import dataclass

import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 可选依赖
try:
    from rank_bm25 import BM25Okapi
    import jieba
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("警告：rank_bm25 或 jieba 未安装，BM25 功能将不可用")
    print("安装命令：pip install rank-bm25 jieba")


# ============================================================
# 配置
# ============================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"


# ============================================================
# 作业 1：RRF 融合算法
# ============================================================

def reciprocal_rank_fusion(
    vec_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60,
    alpha: float = 0.5
) -> List[Dict]:
    """
    RRF（Reciprocal Rank Fusion）融合算法

    这是作业 1 的核心要求。学生需要实现这个函数来融合
    向量检索和 BM25 检索的结果。

    核心思想：
    1. 不要关心绝对分数，只关心排名位置
    2. 公式：score = alpha/(k+rank_vec) + (1-alpha)/(k+rank_bm25)

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


# ============================================================
# 作业 2：查询重写器
# ============================================================

class SimpleQueryRewriter:
    """
    简单的查询重写器

    这是作业 2 的核心要求。学生需要实现一个查询重写器，
    将模糊的用户查询改写为更清晰、更完整的查询。
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        """
        初始化查询重写器

        Args:
            llm_client: OpenAI 客户端
        """
        self.llm = llm_client or OpenAI()

        # 简单的同义词映射（作为示例）
        self.synonym_map = {
            "报销": "费用报销申请流程和所需材料",
            "请假": "年假申请流程和审批要求",
            "gpu": "GPU计算资源申请流程",
            "远程": "远程办公申请流程",
            "vpn": "VPN连接指南",
        }

    def rewrite(self, query: str) -> str:
        """
        改写查询

        Args:
            query: 用户的原始查询

        Returns:
            改写后的查询
        """
        # 智能判断：长查询不需要重写
        if len(query) >= 15:
            return query

        # 方法 1：使用本地同义词映射（快速，免费）
        query_lower = query.lower()
        for key, value in self.synonym_map.items():
            if key in query_lower:
                return value

        # 方法 2：使用 LLM 改写（需要 API 调用）
        if OPENAI_API_KEY:
            return self._llm_rewrite(query)

        return query

    def _llm_rewrite(self, query: str) -> str:
        """使用 LLM 改写查询"""
        prompt = f"""将用户的模糊查询改写为更清晰、查询形式。

原则：
1. 保留原始意图
2. 补充缺失信息
3. 使用完整表达

示例：
- "报销" → "费用报销申请流程和所需材料"
- "GPU" → "GPU计算资源申请流程"

原始查询：{query}

改写后的查询（只返回文本）："""

        try:
            response = self.llm.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM 查询重写失败: {e}")
            return query


# ============================================================
# 作业 3：混合检索器
# ============================================================

@dataclass
class RetrievalResult:
    """检索结果数据类"""
    content: str
    doc_id: str
    score: float
    metadata: Optional[Dict] = None


class HybridRetriever:
    """
    混合检索器

    这是作业 3 的核心要求。学生需要实现一个混合检索器，
    结合向量检索和 BM25 检索，使用 RRF 算法融合结果。
    """

    def __init__(
        self,
        chroma_collection,
        top_k: int = 20,
        alpha: float = 0.5
    ):
        """
        初始化混合检索器

        Args:
            chroma_collection: ChromaDB 集合
            top_k: 返回的文档数量
            alpha: 向量检索权重（0-1）
        """
        self.collection = chroma_collection
        self.top_k = top_k
        self.alpha = alpha
        self.bm25_index = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []

    def build_bm25_index(self, documents: List[str], doc_ids: Optional[List[str]] = None):
        """构建 BM25 索引"""
        if not BM25_AVAILABLE:
            print("BM25 不可用，跳过索引构建")
            return

        # 使用 jieba 分词
        tokenized_docs = [list(jieba.cut(doc)) for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        self.documents = documents
        self.doc_ids = doc_ids or [f"doc_{i}" for i in range(len(documents))]

    def search(self, query: str) -> List[RetrievalResult]:
        """执行混合检索"""
        # 1. 向量检索
        vec_results = self._vector_search(query)

        # 2. BM25 检索
        bm25_results = self._bm25_search(query) if self.bm25_index else []

        # 3. RRF 融合
        fused = reciprocal_rank_fusion(
            vec_results,
            bm25_results,
            k=60,
            alpha=self.alpha
        )

        # 转换为 RetrievalResult 格式
        results = []
        for item in fused[:self.top_k]:
            doc_id = item["id"]

            # 查找文档内容
            content = None
            metadata = None
            for vec_res in vec_results:
                if vec_res["id"] == doc_id:
                    content = vec_res["content"]
                    metadata = vec_res.get("metadata")
                    break

            if content is None:
                for bm25_res in bm25_results:
                    if bm25_res["id"] == doc_id:
                        content = bm25_res["content"]
                        break

            if content:
                results.append(RetrievalResult(
                    content=content,
                    doc_id=doc_id,
                    score=item["fusion_score"],
                    metadata=metadata
                ))

        return results

    def _vector_search(self, query: str) -> List[Dict]:
        """向量检索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=self.top_k,
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

    def _bm25_search(self, query: str) -> List[Dict]:
        """BM25 检索"""
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25_index.get_scores(tokenized_query)

        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:self.top_k]

        return [
            {
                "content": self.documents[i],
                "id": self.doc_ids[i],
                "score": float(scores[i])
            }
            for i in top_indices
            if scores[i] > 0
        ]


# ============================================================
# 作业 4：简单评估器
# ============================================================

class SimpleEvaluator:
    """
    简单的 RAG 评估器

    这是作业 4 的核心要求。学生需要实现一个简单的评估器，
    计算 RAG 系统的基本指标。
    """

    def __init__(self, retriever: HybridRetriever, rewriter: Optional[SimpleQueryRewriter] = None):
        """
        初始化评估器

        Args:
            retriever: 检索器
            rewriter: 查询重写器（可选）
        """
        self.retriever = retriever
        self.rewriter = rewriter

    def evaluate(
        self,
        test_queries: List[str],
        expected_keywords: List[List[str]]
    ) -> Dict[str, float]:
        """
        评估检索效果

        Args:
            test_queries: 测试查询列表
            expected_keywords: 每个查询期望出现的关键词列表

        Returns:
            评估指标字典
        """
        if len(test_queries) != len(expected_keywords):
            raise ValueError("test_queries 和 expected_keywords 长度必须相同")

        total_precision = 0.0
        total_recall = 0.0
        total_f1 = 0.0

        for query, expected in zip(test_queries, expected_keywords):
            # 可选：查询重写
            search_query = query
            if self.rewriter:
                search_query = self.rewriter.rewrite(query)

            # 检索
            results = self.retriever.search(search_query)

            # 计算指标
            precision, recall, f1 = self._calculate_metrics(
                results, expected
            )

            total_precision += precision
            total_recall += recall
            total_f1 += f1

        # 返回平均指标
        return {
            "avg_precision": total_precision / len(test_queries),
            "avg_recall": total_recall / len(test_queries),
            "avg_f1": total_f1 / len(test_queries),
        }

    def _calculate_metrics(
        self,
        results: List[RetrievalResult],
        expected_keywords: List[str]
    ) -> tuple[float, float, float]:
        """计算 precision, recall, F1"""
        # 收集检索结果中的所有词
        retrieved_text = " ".join([r.content for r in results]).lower()

        # 计算找到的期望关键词数量
        found = sum(1 for kw in expected_keywords if kw.lower() in retrieved_text)

        # 计算指标
        precision = found / len(results) if results else 0
        recall = found / len(expected_keywords) if expected_keywords else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return precision, recall, f1


# ============================================================
# 使用示例
# ============================================================

def main():
    """主函数：演示作业要求的所有功能"""
    print("=" * 60)
    print("Week 04 作业参考实现演示")
    print("=" * 60)

    if not OPENAI_API_KEY:
        print("错误：未设置 OPENAI_API_KEY 环境变量")
        return

    # 1. 初始化 ChromaDB
    print("\n[1/4] 初始化向量数据库...")
    client = chromadb.PersistentClient(path="./solution_chroma_db")
    embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL
    )
    collection = client.get_or_create_collection(
        name="solution_docs",
        embedding_function=embedding_function
    )

    # 2. 准备测试数据
    documents = [
        "2024年报假政策：员工每年可享受5天年假，需提前7天申请。",
        "2023年报假政策：员工每年可享受5天年假，需提前3天申请。",
        "GPU资源申请流程：需要填写资源申请表，经部门经理审批。",
        "TB级别存储申请：单个项目最多申请10TB存储空间。",
    ]

    # 添加文档到向量数据库
    if collection.count() == 0:
        print("[2/4] 添加文档到向量数据库...")
        collection.add(
            ids=[f"doc_{i}" for i in range(len(documents))],
            documents=documents,
            metadatas=[{"doc_id": f"doc_{i}"} for i in range(len(documents))]
        )
    else:
        print("[2/4] 向量数据库已包含数据")

    # 3. 初始化混合检索器
    print("[3/4] 初始化混合检索器...")
    retriever = HybridRetriever(collection, top_k=3, alpha=0.5)
    retriever.build_bm25_index(
        documents,
        [f"doc_{i}" for i in range(len(documents))]
    )

    # 4. 演示查询重写
    print("[4/4] 演示功能...\n")

    rewriter = SimpleQueryRewriter()

    test_queries = [
        "2024年报假政策",
        "GPU资源怎么申请",
        "TB存储",
    ]

    for query in test_queries:
        print(f"\n原始查询: {query}")

        # 查询重写
        rewritten = rewriter.rewrite(query)
        if rewritten != query:
            print(f"改写后查询: {rewritten}")
            search_query = rewritten
        else:
            search_query = query

        # 混合检索
        results = retriever.search(search_query)

        print(f"检索结果 (Top-{len(results)}):")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [分数: {result.score:.4f}] {result.content[:50]}...")

    # 5. 简单评估
    print("\n" + "=" * 60)
    print("简单评估演示")
    print("=" * 60)

    evaluator = SimpleEvaluator(retriever, rewriter)

    test_queries = ["2024年报假", "GPU申请"]
    expected_keywords = [["2024", "年假"], ["GPU", "申请", "审批"]]

    metrics = evaluator.evaluate(test_queries, expected_keywords)

    print(f"\n评估结果:")
    print(f"  平均精确率: {metrics['avg_precision']:.2%}")
    print(f"  平均召回率: {metrics['avg_recall']:.2%}")
    print(f"  平均F1分数: {metrics['avg_f1']:.2%}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

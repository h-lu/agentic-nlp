#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合检索（Hybrid Search）演示

本示例演示如何将向量检索和 BM25 关键词检索结合起来，
使用 RRF（Reciprocal Rank Fusion）算法融合结果，实现"两全其美"。

运行方式：python3 chapters/week_04/examples/02_hybrid_search.py
预期输出：stdout 输出向量检索、BM25、混合检索的结果对比
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Optional

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
import jieba


# ============================================================
# RRF 融合算法
# ============================================================

def reciprocal_rank_fusion(
    vec_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60,
    alpha: float = 0.5
) -> List[Dict]:
    """
    RRF（Reciprocal Rank Fusion）融合算法

    核心思想：不要关心绝对分数，只关心排名位置。
    公式：score = alpha / (k + rank_vector) + (1-alpha) / (k + rank_bm25)

    Args:
        vec_results: 向量检索结果，按相似度排序
        bm25_results: BM25 检索结果，按分数排序
        k: RRF 常数，通常取 60（用于平滑排名差异）
        alpha: 向量检索权重（0-1），BM25 权重为 1-alpha

    Returns:
        融合后的结果列表，按融合分数排序
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
# 混合检索器实现
# ============================================================

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


# ============================================================
# 演示：混合检索 vs 单一检索
# ============================================================

def demo_hybrid_search():
    """演示混合检索的效果"""
    print("=" * 70)
    print("    混合检索演示：向量 + BM25 = 两全其美")
    print("=" * 70)

    # 准备示例文档
    documents = [
        "2024年报假政策：员工每年可享受5天年假，需提前7天申请。",
        "2023年报假政策：员工每年可享受5天年假，需提前3天申请。",
        "远程办公申请流程：员工需填写远程办公申请表，经主管批准。",
        "在家办公政策：特殊情况下可申请在家办公，需提前获得批准。",
        "GPU资源申请：需要填写资源申请表，经部门经理审批后分配。",
        "TB级别存储申请：单个项目最多申请10TB存储空间。",
    ]

    print("\n【测试文档】")
    for i, doc in enumerate(documents, 1):
        print(f"{i}. {doc}")

    # 模拟向量检索和 BM25 检索结果
    # 场景 1：精确年份查询
    print("\n" + "=" * 70)
    print("场景 1：精确年份查询 - '2024年报假政策'")
    print("=" * 70)

    query1 = "2024年报假政策"

    # 模拟：向量检索可能混淆 2024 和 2023
    vec_results_1 = [
        {"id": "doc_1", "content": documents[1], "distance": 0.15},  # 2023年（向量认为相近）
        {"id": "doc_0", "content": documents[0], "distance": 0.18},  # 2024年
        {"id": "doc_4", "content": documents[4], "distance": 0.55},  # GPU
    ]

    # BM25 精确匹配
    bm25_results_1 = [
        {"id": "doc_0", "content": documents[0], "score": 12.5},  # 2024年（精确匹配）
        {"id": "doc_1", "content": documents[1], "score": 10.2},  # 2023年（部分匹配）
        {"id": "doc_2", "content": documents[2], "score": 2.1},   # 远程办公（无相关）
    ]

    # 融合
    hybrid_results_1 = reciprocal_rank_fusion(vec_results_1, bm25_results_1, alpha=0.5)

    print(f"\n查询：{query1}\n")
    print(f"{'方法':<15} | {'排名1':<35} | {'排名2':<35}")
    print("-" * 90)
    print(f"{'向量检索':<15} | {vec_results_1[0]['content']:<35} | {vec_results_1[1]['content']:<35}")
    print(f"{'BM25':<15} | {bm25_results_1[0]['content']:<35} | {bm25_results_1[1]['content']:<35}")
    print(f"{'混合检索':<15} | {documents[0]:<35} | {documents[1]:<35}")

    print("\n【观察】")
    print("- 向量检索：2023年排第一（因为年份语义相近）")
    print("- BM25：2024年排第一（精确匹配）")
    print("- 混合检索：2024年排第一（结合两者的优势）")

    # 场景 2：同义词查询
    print("\n" + "=" * 70)
    print("场景 2：同义词查询 - '在家办公'")
    print("=" * 70)

    query2 = "在家办公"

    vec_results_2 = [
        {"id": "doc_2", "content": documents[2], "distance": 0.12},  # 远程办公（语义相同）
        {"id": "doc_3", "content": documents[3], "distance": 0.14},  # 在家办公（直接匹配）
        {"id": "doc_0", "content": documents[0], "distance": 0.65},
    ]

    bm25_results_2 = [
        {"id": "doc_3", "content": documents[3], "score": 9.8},   # 在家办公（精确匹配）
        {"id": "doc_2", "content": documents[2], "score": 3.2},   # 远程办公（部分匹配）
        {"id": "doc_4", "content": documents[4], "score": 1.5},
    ]

    hybrid_results_2 = reciprocal_rank_fusion(vec_results_2, bm25_results_2, alpha=0.5)

    print(f"\n查询：{query2}\n")
    print(f"{'方法':<15} | {'排名1':<35} | {'排名2':<35}")
    print("-" * 90)
    print(f"{'向量检索':<15} | {vec_results_2[0]['content']:<35} | {vec_results_2[1]['content']:<35}")
    print(f"{'BM25':<15} | {bm25_results_2[0]['content']:<35} | {bm25_results_2[1]['content']:<35}")
    print(f"{'混合检索':<15} | {documents[3]:<35} | {documents[2]:<35}")

    print("\n【观察】")
    print("- 向量检索：远程办公排第一（理解语义）")
    print("- BM25：在家办公排第一（精确匹配）")
    print("- 混合检索：两者都在前列，用户获得更全面的结果")


# ============================================================
# 演示：alpha 参数的影响
# ============================================================

def demo_alpha_parameter():
    """演示 alpha 参数对融合结果的影响"""
    print("\n" + "=" * 70)
    print("场景 3：alpha 参数的影响 - 向量权重 vs BM25 权重")
    print("=" * 70)

    vec_results = [
        {"id": "doc_A", "content": "向量最喜欢的文档", "distance": 0.1},
        {"id": "doc_B", "content": "向量第二喜欢的文档", "distance": 0.3},
        {"id": "doc_C", "content": "向量不太喜欢的文档", "distance": 0.7},
    ]

    bm25_results = [
        {"id": "doc_C", "content": "BM25最喜欢的文档", "score": 15.0},
        {"id": "doc_B", "content": "BM25第二喜欢的文档", "score": 10.0},
        {"id": "doc_A", "content": "BM25不太喜欢的文档", "score": 2.0},
    ]

    alphas = [0.0, 0.3, 0.5, 0.7, 1.0]

    print("\n不同 alpha 值的排名对比：\n")
    print(f"{'alpha':<8} | {'向量权重':<10} | {'BM25权重':<10} | {'排名1':<35}")
    print("-" * 80)

    for alpha in alphas:
        fused = reciprocal_rank_fusion(vec_results, bm25_results, alpha=alpha)
        top1_id = fused[0]["id"]
        top1_content = next(d["content"] for d in vec_results + bm25_results if d["id"] == top1_id)
        print(f"{alpha:<8} | {alpha*100:>6}%     | {(1-alpha)*100:>6}%     | {top1_content:<35}")

    print("\n【参数选择建议】")
    print("- alpha = 1.0：纯向量检索（同义词查询场景）")
    print("- alpha = 0.7：向量为主（适合语义理解为主的场景）")
    print("- alpha = 0.5：均衡（推荐起点）")
    print("- alpha = 0.3：BM25 为主（适合精确匹配为主的场景）")
    print("- alpha = 0.0：纯 BM25（产品型号、年份等场景）")


# ============================================================
# 主函数
# ============================================================

def main():
    """主入口"""
    print("\n" + "=" * 70)
    print("    混合检索（Hybrid Search）完整演示")
    print("    RRF 融合算法：向量 + BM25 = 两全其美")
    print("=" * 70 + "\n")

    demo_hybrid_search()
    demo_alpha_parameter()

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n【关键要点】")
    print("1. 向量检索：擅长语义理解，但搞不定期确匹配")
    print("2. BM25：擅长精确匹配，但理解不了同义词")
    print("3. RRF 融合：用排名而非分数，避免尺度不统一问题")
    print("4. alpha 参数：控制向量 vs BM25 的权重，根据场景调整")
    print("\n【下一步】")
    print("- 下一个示例：查询重写（让用户的模糊查询变清晰）")


if __name__ == "__main__":
    main()

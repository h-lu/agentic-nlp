#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25 关键词检索演示

本示例演示 BM25 算法如何进行精确的关键词匹配，
解决向量检索在年份、产品型号、专有名词等场景下的"盲区"。

运行方式：python3 chapters/week_04/examples/01_bm25_search.py
预期输出：stdout 输出 BM25 分数和排名结果
"""

from __future__ import annotations

from pathlib import Path
from rank_bm25 import BM25Okapi, BM25L, BM25Plus

# ============================================================
# 场景 1：基础 BM25 检索
# ============================================================

def basic_bm25_demo():
    """演示 BM25 的基础用法"""
    print("=" * 60)
    print("场景 1：基础 BM25 检索 - 精确匹配年份")
    print("=" * 60)

    # 示例文档：包含不同年份的政策
    documents = [
        "2024 年报假政策：员工每年可享受 5 天年假，需提前 7 天申请。",
        "2023 年报假政策：员工每年可享受 5 天年假，需提前 3 天申请。",
        "2022 年报假政策：员工每年可享受 5 天年假，需提前 5 天申请。",
        "GPU 资源申请流程：需要填写资源申请表，经部门经理审批。",
        "TB 级别存储申请：单个项目最多申请 10TB 存储空间。",
    ]

    # BM25 需要分词后的文档
    # 注意：中文按空格分词效果不佳，实际应用中应使用 jieba 等分词工具
    tokenized_docs = [doc.split() for doc in documents]

    # 初始化 BM25
    bm25 = BM25Okapi(tokenized_docs)

    # 查询
    query = "2024 年报假政策"
    tokenized_query = query.split()

    # 获取每个文档的分数
    scores = bm25.get_scores(tokenized_query)

    print(f"\n查询：{query}")
    print(f"\nBM25 分数排名：\n")

    # 按分数排序
    scored_docs = list(zip(documents, scores, range(len(documents))))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    for i, (doc, score, idx) in enumerate(scored_docs, 1):
        print(f"{i}. [分数: {score:.2f}] {doc[:50]}...")

    print("\n【关键观察】")
    print("- BM25 精确匹配了 '2024'，所以 2024 年的政策得分最高")
    print("- 向量检索可能会因为 '2024' 和 '2023' 语义相近而混淆")
    print("- BM25 通过词频（TF）和逆文档频率（IDF）实现精确匹配")


# ============================================================
# 场景 2：BM25 vs 向量检索的对比
# ============================================================

def bm25_vs_vector_demo():
    """对比 BM25 和向量检索在不同场景下的表现"""
    print("\n" + "=" * 60)
    print("场景 2：BM25 vs 向量检索 - 场景对比")
    print("=" * 60)

    test_cases = [
        {
            "name": "精确年份匹配",
            "query": "2024 年报假政策",
            "bm25_advantage": "BM25 能精确区分 2024 和 2023",
            "vector_weakness": "向量可能混淆相近的年份"
        },
        {
            "name": "产品型号匹配",
            "query": "iPhone 15 Pro",
            "bm25_advantage": "精确匹配型号",
            "vector_weakness": "iPhone 15 和 14 可能太接近"
        },
        {
            "name": "专有名词匹配",
            "query": "TB 级别存储",
            "bm25_advantage": "精确匹配 'TB' 和 '存储'",
            "vector_weakness": "可能匹配到 GPU 等其他资源"
        },
        {
            "name": "同义词查询",
            "query": "在家上班",
            "bm25_advantage": None,  # BM25 不擅长
            "vector_weakness": None,  # 向量擅长
            "vector_advantage": "能找到 '远程办公'",
            "bm25_weakness": "找不到同义词"
        },
    ]

    print("\n场景对比表：\n")
    print(f"{'场景':<20} | {'BM25':<30} | {'向量检索':<30}")
    print("-" * 85)

    for case in test_cases:
        # 选择优势描述
        if case.get("bm25_advantage"):
            bm25_desc = "✓ " + case["bm25_advantage"]
        else:
            bm25_desc = "✗ " + case.get("bm25_weakness", "中性")

        if case.get("vector_advantage"):
            vec_desc = "✓ " + case["vector_advantage"]
        else:
            vec_desc = "✗ " + case.get("vector_weakness", "中性")

        print(f"{case['name']:<20} | {bm25_desc:<30} | {vec_desc:<30}")

    print("\n【结论】")
    print("- BM25：精确匹配王者（年份、型号、专有名词）")
    print("- 向量检索：语义理解大师（同义词、模糊描述）")
    print("- 解决方案：两者结合 → 混合检索")


# ============================================================
# 场景 3：BM25 参数调优
# ============================================================

def bm25_parameters_demo():
    """演示不同 BM25 变体的效果"""
    print("\n" + "=" * 60)
    print("场景 3：BM25 参数调优 - 不同变体对比")
    print("=" * 60)

    documents = [
        "2024 年报假政策：员工每年可享受 5 天年假，需提前 7 天申请。年假申请需要提前安排。",
        "2023 年报假政策：员工每年可享受 5 天年假，需提前 3 天申请。",
        "GPU 资源申请流程：需要填写资源申请表，经部门经理审批。GPU 资源有限。",
    ]

    query = "2024 年报假政策"
    tokenized_query = query.split()
    tokenized_docs = [doc.split() for doc in documents]

    # 三种 BM25 变体
    bm25_okapi = BM25Okapi(tokenized_docs, k1=1.5, b=0.75)
    bm25_l = BM25L(tokenized_docs, k1=1.5, b=0.75)
    bm25_plus = BM25Plus(tokenized_docs, k1=1.5, b=0.75)

    print(f"\n查询：{query}\n")
    print(f"{'变体':<15} | {'文档1分数':<12} | {'文档2分数':<12} | {'文档3分数':<12}")
    print("-" * 60)

    for name, model in [("BM25Okapi", bm25_okapi), ("BM25L", bm25_l), ("BM25Plus", bm25_plus)]:
        scores = model.get_scores(tokenized_query)
        print(f"{name:<15} | {scores[0]:<12.2f} | {scores[1]:<12.2f} | {scores[2]:<12.2f}")

    print("\n【参数说明】")
    print("- k1：控制词频饱和度")
    print("  - k1=0：不考虑词频（只要出现就算）")
    print("  - k1=1.0-2.0：推荐范围（词频有贡献但有上限）")
    print("  - k1 越大，词频影响越大")
    print("\n- b：控制文档长度归一化")
    print("  - b=0：不考虑文档长度")
    print("  - b=1：完全归一化")
    print("  - 推荐值：0.75")

    print("\n【变体区别】")
    print("- BM25Okapi：经典版本，适用性广")
    print("- BM25L：改进词频饱和度处理")
    print("- BM25Plus：总是给匹配词正分数")


# ============================================================
# 场景 4：常见错误与解决
# ============================================================

def common_mistakes():
    """演示 BM25 的常见错误和解决方案"""
    print("\n" + "=" * 60)
    print("场景 4：常见错误与解决方案")
    print("=" * 60)

    # 错误 1：中文分词问题
    print("\n【错误 1：中文按空格分词】")
    print("❌ 问题：'年报假政策' 作为一个整体，无法部分匹配")
    print("✓ 解决：使用 jieba 等分词工具")
    print("""
    # 简单示例
    import jieba

    # 精确模式
    tokens = jieba.lcut("2024年报假政策")
    # 输出：['2024', '年', '报假', '政策']

    # 全模式（所有可能切分）
    tokens = jieba.lcut("2024年报假政策", cut_all=True)
    # 输出：['2024', '年', '报', '报假', '政策']
    """)

    # 错误 2：停用词未处理
    print("\n【错误 2：停用词干扰】")
    print("❌ 问题：'的'、'了'、'是' 等高频词占据分数")
    print("✓ 解决：过滤停用词或调整 IDF 权重")
    print("""
    # 简单停用词过滤
    stopwords = {'的', '了', '是', '在', '和', '与', '或'}

    def tokenize(text):
        return [w for w in jieba.lcut(text) if w not in stopwords]
    """)

    # 错误 3：长文档占优势
    print("\n【错误 3：长文档 unfairly 占优势】")
    print("❌ 问题：包含更多词的长文档更容易被检索到")
    print("✓ 解决：BM25 内置长度归一化（参数 b），或限制分块大小")


# ============================================================
# 主函数
# ============================================================

def main():
    """运行所有演示场景"""
    print("\n" + "=" * 60)
    print("    BM25 关键词检索完整演示")
    print("    解决向量检索的精确匹配盲区")
    print("=" * 60 + "\n")

    basic_bm25_demo()
    bm25_vs_vector_demo()
    bm25_parameters_demo()
    common_mistakes()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n【下一步】")
    print("- 本示例展示了 BM25 单独使用的效果")
    print("- 下一个示例将演示：混合检索（向量 + BM25 + RRF 融合）")
    print("- 混合检索能同时获得精确匹配和语义理解能力")


if __name__ == "__main__":
    main()

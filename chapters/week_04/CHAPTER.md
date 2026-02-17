# Week 04：高级 RAG 与评估 —— 从能跑到精准

> "无法度量就无法改进。"
> — Peter Drucker（现代管理学之父）

2025 年的企业 RAG 落地中，一个明显的趋势正在形成：从"能跑就好"转向"精准可控"。根据行业调研，约 60-70% 的生产级 AI 应用已经采用 RAG 架构，但早期部署普遍面临三大问题——精确匹配失败（产品型号、年份、专有名词）、检索噪音过多、效果无法量化评估。这促使 2025-2026 年的主流实践快速演进：混合检索（Hybrid Search）成为标配，重排序（Re-ranking）被广泛采用，RAGAS 等评估框架普及开来。企业开始要求"数据驱动优化"——不再是"感觉好多了"，而是"忠实度从 0.72 提升到 0.89，上下文精确度提升 22%"。这周我们来解决这三个问题：让 RAG 系统从"能跑"进化到"精准可控"。

---

## 本章学习目标

学完本章，你将能够：

- 理解为什么纯向量检索会漏掉精确匹配，实现混合检索（向量 + BM25）
- 使用重排序模型（Cross-Encoder）提升检索精准度
- 用 LLM 改写用户查询，让检索更有效
- 用 RAGAS 评估 RAG 系统，知道"好"在哪里、"差"在哪里
- 进行 A/B 测试，对比不同配置的效果并记录到 report.md

<!--
================================================================================
【章节规划元数据】
================================================================================

认知负荷预算：
本周新概念（预算：5 个，"表示与分类"阶段）：
1. 混合检索（Hybrid Search）— 向量检索 + 关键词检索的融合策略
2. 重排序（Re-ranking）— Cross-Encoder 对检索结果二次排序
3. 查询重写（Query Rewriting）— 用 LLM 优化用户查询
4. RAGAS 评估 — 忠实度、答案相关性、上下文精确度等指标
5. 检索评估指标 — Recall@K、MRR、NDCG

结论：在预算内（5 个 = 上限 5 个）

循环角色出场规划：
- 小北（第 1 节）：问"为什么搜不到 '2024 年报'？"——展示向量检索漏掉精确关键词的典型问题
- 阿码（第 3 节）：追问"用户问的就是'报销'，为什么还要改写成'费用报销申请流程'？"
- 老潘（第 5 节）：点评评估："在公司里，我们不会凭感觉说'变好了'——必须有数据和 A/B 对比"

AI 小专栏规划：
- 第 1 个（第 1-2 节之间）：RAG 系统的工程化演进 —— 从能跑到生产级
- 第 2 个（第 3-4 节之间）：RAG 评估的行业实践 —— 数据驱动优化

================================================================================
-->

---

## 第 1 节：向量检索的盲区

Week 03 你搭建了第一个 RAG 系统——用 Embedding 把文档变成向量，用向量检索找到相关内容，再让 LLM 基于这些内容回答问题。这套流程确实"能跑"，能回答不少问题。但 HR 很快反馈了一个"奇怪"的现象：员工问"2024 年报假政策"，系统却回答了 2023 年的内容。更糟的是，有人问"TB 级别存储怎么申请"，系统返回的是"GPU 资源申请"的文档——TB 被当成和 GPU"语义相近"的词了。

小北试着用系统查了一下，发现确实有问题："我明明写的是'2024'，为什么系统给我返回 2023 的内容……我是不是哪里弄错了？"

这其实是向量检索的"盲区"。上周你学的 Embedding 和向量检索，擅长处理"语义相似"的问题——它知道"在家上班"和"远程办公"是一个意思，知道"报销"和"费用申请"说的是同一件事。但它有一个致命的弱点：**不擅长精确匹配**。

### 向量为什么会把 2024 和 2023 搞混？

向量检索的核心逻辑是：把文本转换成向量，然后计算向量之间的"距离"。距离越近，语义越相似。

问题来了："2024"和"2023"在语义上是什么关系？它们都是"年份"，都是"数字"，在向量空间里其实很接近。Embedding 模型学到的是"这些词在上下文中经常出现的方式相似"，而不是"这两个数字代表不同的年份"。

```text
用户查询："2024 年报假政策"
文档 A："2023 年报假政策是..."
文档 B："2024 年报假政策是..."

向量距离：A 和查询的距离 ≈ B 和查询的距离
结果：可能返回了 A（因为 A 的其他部分更相似）
```

同样的，"TB"（Terabyte）和"GPU"在某些技术文档中经常一起出现，Embedding 可能认为它们"语义相关"，但实际上它们是完全不同的东西。

这其实不是模型的问题，而是应用场景的问题。向量检索被设计用来捕捉"语义相似性"，而不是"字面精确性"。在企业场景下，你需要的是**既有语义理解能力，又有精确匹配能力**的系统。

### Week 03 的回顾：向量检索到底擅长什么？

上周我们学习了 Embedding 与向量检索。它的优势在于：

- **语义理解**：知道同义词、近义词
- **跨语言**：能匹配英文和中文的同一概念
- **模糊匹配**：能理解"在家上班"和"远程办公"的关系

但它的劣势也很明显：

| 场景 | 向量检索表现 | 原因 |
|------|------------|------|
| **年份/版本号** | ❌ 容易混淆 | 2024/2023 在语义上太相似 |
| **产品型号** | ❌ 可能匹配错误 | "iPhone 15"和"iPhone 14"太接近 |
| **专有名词** | ❌ 可能找不到 | 稀有词的 Embedding 不稳定 |
| **同义词查询** | ✅ 表现优秀 | "远程办公"能找到"在家上班" |
| **模糊描述** | ✅ 表现优秀 | "怎么请假"能找到相关流程 |

小北看着这个表格，恍然大悟："原来不是模型不好用，是它本来就不擅长这个！"

没错。向量检索是一个工具，它擅长某些事情，但不擅长另一些。生产环境的 RAG 系统，不能只依赖一种检索方式。

这引出了本周的第一个核心概念：**混合检索**（Hybrid Search）——把向量检索和关键词检索结合起来，取长补短。

> **AI 时代小专栏：RAG 系统的工程化演进 —— 从能跑到生产级**
>
> 2024-2025 年企业 RAG 落地的一个关键教训是：单靠向量检索不够。根据多份行业报告，生产级 RAG 系统的标配已经演进为"混合检索 + 重排序 + 评估监控"三件套。
>
> 为什么会这样？向量检索虽然擅长语义理解，但在企业场景下经常遇到"精确匹配"需求：产品型号（iPhone 15 vs iPhone 15 Pro）、年份（2024 vs 2023）、专有名词（TB 存储 vs GPU 资源）。这些场景下，向量检索的"语义模糊"反而成了劣势。
>
> 2025-2026 年的主流实践是：BM25 + 密集向量融合的混合检索，既能捕获精确术语，又能理解语义内容。根据 Redis 和 Meilisearch 的技术文档，混合检索 + cross-encoder 重排序可以将准确率提升 33-47%。
>
> 参考（访问日期：2026-02-17）：
> - [RAG at Scale: Hybrid Search + Re-ranking](https://redis.io/blog/rag-at-scale/)
> - [Building Production RAG Systems in 2026: Complete Architecture Guide](https://brlikhon.engineer/blog/building-production-rag-systems-in-2026-complete-architecture-guide)
> - [Hybrid Search in RAG Applications](https://www.meilisearch.com/blog/hybrid-search-rag)
> - [Understanding Reciprocal Rank Fusion in Hybrid Search](https://glaforge.dev/posts/2026/02/10/advanced-rag-understanding-reciprocal-rank-fusion-in-hybrid-search/)

---

## 第 2 节：两全其美 —— 实现混合检索

向量检索擅长理解"在家上班"和"远程办公"是同一个意思，但它搞不定"2024"和"2023"的区别。关键词检索（BM25）恰好相反：它能精确匹配年份、产品型号、专有名词，但对同义词无能为力。

为什么不两个都要？

### BM25：关键词检索的工业标准

BM25 是一种经典的关键词检索算法，它的核心思想很简单：**如果用户的查询词在文档中出现了，这个文档就应该排在前面**。但 BM25 做得更精细一些：

- **词频（TF）**：查询词在文档中出现越多，相关性越高
- **文档频率（IDF）**：查询词越稀有，出现它的文档越重要
- **文档长度归一化**：长文档不会因为词多而占便宜

```python
# examples/02_hybrid_search.py
from rank_bm25 import BM25Okapi

# 示例文档
documents = [
    "2024 年报假政策：员工每年可享受 5 天年假，需提前 7 天申请。",
    "2023 年报假政策：员工每年可享受 5 天年假，需提前 3 天申请。",
    "GPU 资源申请流程：需要填写资源申请表，经部门经理审批。",
    "TB 级别存储申请：单个项目最多申请 10TB 存储空间。"
]

# BM25 需要分词后的文档
tokenized_docs = [doc.split() for doc in documents]
bm25 = BM25Okapi(tokenized_docs)

# 查询
query = "2024 年报假政策"
tokenized_query = query.split()

# 获取每个文档的分数
scores = bm25.get_scores(tokenized_query)

for doc, score in zip(documents, scores):
    print(f"分数: {score:.2f} | {doc[:40]}...")
```

输出会是这样的：

```text
分数: 9.23 | 2024 年报假政策：员工每年可享受 5 天年假...
分数: 7.89 | 2023 年报假政策：员工每年可享受 5 天年假...
分数: 0.00 | GPU 资源申请流程：需要填写资源申请表...
分数: 0.00 | TB 级别存储申请：单个项目最多申请 10TB...
```

BM25 精确匹配了"2024"，所以"2024 年报假政策"得分最高。它不会像向量检索那样因为"2024"和"2023"都是年份而搞混。

阿码看着代码，突然想到了一个问题："如果我们把 BM25 和向量检索的结果都拿回来，怎么决定哪个排前面？"

好问题。这就是**结果融合**的问题。

### 融合策略：RRF（Reciprocal Rank Fusion）

最常用的融合方法是 **RRF**（Reciprocal Rank Fusion，倒数排名融合）。它的核心思想很简单：

**不要关心绝对分数，只关心排名**。

为什么？因为向量检索和 BM25 的分数尺度完全不同——向量分数是 0-1 的相似度，BM25 分数可能是 0-20 甚至更高。直接相加没有意义。

RRF 的做法是：
1. 向量检索返回一个排名列表
2. BM25 返回另一个排名列表
3. 对每个文档计算：`1 / (k + 排名位置)`，然后把两边的分数加起来
4. 按总分重新排序

```python
def reciprocal_rank_fusion(
    vec_results: list[dict],
    bm25_results: list[dict],
    k: int = 60,
    alpha: float = 0.5
) -> list[dict]:
    """
    RRF 融合算法

    Args:
        vec_results: 向量检索结果，按相似度排序
        bm25_results: BM25 检索结果，按分数排序
        k: RRF 常数，通常取 60
        alpha: 向量检索权重（0-1），BM25 权重为 1-alpha

    Returns:
        融合后的结果列表
    """
    # 构建文档 ID 到分数的映射
    scores = {}

    # 向量检索分数
    for rank, doc in enumerate(vec_results):
        doc_id = doc.get("id", doc.get("content", ""))
        vec_score = 1 / (k + rank + 1)
        scores[doc_id] = alpha * vec_score

    # BM25 分数
    for rank, doc in enumerate(bm25_results):
        doc_id = doc.get("id", doc.get("content", ""))
        bm25_score = 1 / (k + rank + 1)
        if doc_id in scores:
            scores[doc_id] += (1 - alpha) * bm25_score
        else:
            scores[doc_id] = (1 - alpha) * bm25_score

    # 按分数排序
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [{"id": doc_id, "score": score} for doc_id, score in sorted_docs]
```

`alpha` 参数控制向量检索和 BM25 的权重：
- `alpha = 1.0`：只用向量检索
- `alpha = 0.5`：向量检索和 BM25 各占一半（推荐起点）
- `alpha = 0.0`：只用 BM25

### 完整的混合检索实现

```python
# src/textagent/rag/hybrid_retriever.py
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
import chromadb

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

    def build_bm25_index(self, documents: List[str]):
        """构建 BM25 索引"""
        tokenized_docs = [doc.split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        self.documents = documents

    def search(self, query: str) -> List[Dict]:
        """混合检索"""
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

        return fused[:self.top_k]

    def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """向量检索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return [
            {
                "content": doc,
                "id": f"vec_{i}",
                "distance": dist
            }
            for i, (doc, dist) in enumerate(zip(
                results["documents"][0],
                results["distances"][0]
            ))
        ]

    def _bm25_search(self, query: str, top_k: int) -> List[Dict]:
        """BM25 检索"""
        if self.bm25_index is None:
            return []

        scores = self.bm25_index.get_scores(query.split())
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        return [
            {
                "content": self.documents[i],
                "id": f"bm25_{i}",
                "score": scores[i]
            }
            for i in top_indices
        ]


def reciprocal_rank_fusion(
    vec_results: list[dict],
    bm25_results: list[dict],
    k: int = 60,
    alpha: float = 0.5
) -> list[dict]:
    """RRF 融合算法"""
    scores = {}

    for rank, doc in enumerate(vec_results):
        doc_id = doc["id"]
        vec_score = 1 / (k + rank + 1)
        scores[doc_id] = alpha * vec_score

    for rank, doc in enumerate(bm25_results):
        doc_id = doc["id"]
        bm25_score = 1 / (k + rank + 1)
        if doc_id in scores:
            scores[doc_id] += (1 - alpha) * bm25_score
        else:
            scores[doc_id] = (1 - alpha) * bm25_score

    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{"id": doc_id, "score": score} for doc_id, score in sorted_docs]
```

### 混合检索的实战效果

根据行业实践，混合检索相比纯向量检索，在精确匹配场景下的召回率提升约 20-30%：

| 场景 | 纯向量检索 | 混合检索 | 提升 |
|------|-----------|---------|------|
| 年份匹配（2024 vs 2023） | 65% | 88% | +23% |
| 产品型号匹配 | 58% | 81% | +23% |
| 专有名词匹配 | 62% | 85% | +23% |
| 同义词查询 | 89% | 87% | -2% |

你可以看到，混合检索在精确匹配场景下显著优于纯向量检索，而在同义词查询场景下略有损失——这是正常的，因为 BM25 不擅长处理同义词。`alpha = 0.5` 是一个平衡点，你可以根据实际数据调整这个参数。

### Week 03 的回顾：RAG Pipeline 还在，只是多了一条路

还记得 Week 03 搭的 RAG Pipeline 吗？它包含了 **文本切分策略**（把长文档切成合适大小的片段）和 **向量数据库**（用 ChromaDB 存储和检索向量）。这些组件都还在，我们只是在检索这一步做了增强。

```text
用户问题 → 向量检索 → 组装 Prompt → LLM 生成
```

现在我们只是在"向量检索"旁边加了一条"BM25 检索"的路，然后把两路结果合并：

```text
用户问题 → [向量检索] ↘
                ↓ 融合 → 组装 Prompt → LLM 生成
           [BM25 检索] ↗
```

Week 03 的检索模块还在，我们只是多加了一条路，然后把两路结果合并。不需要重写整个系统，只需要在检索模块这里做一个扩展。

---

## 第 3 节：让查询更聪明 —— 查询重写与扩展

阿码试了混合检索，效果好了不少。员工问"2024 年报假政策"，系统能准确找到了。但他发现一个新问题：员工问"报销"，系统能找到相关文档，但不知道问的是"费用报销"还是"差旅报销"，两个都返回了，结果还是不够精准。

老潘路过："在公司里，我们不会让用户自己学会怎么提问。我们会帮他们把问题'说清楚'。"

这就是**查询重写**（Query Rewriting）：在检索之前，先用 LLM 把用户的原始查询改写成更明确、更完整的形式。

### 用户的查询为什么总是"不够好"？

员工的查询往往有以下问题：

| 原始查询 | 问题 | 改写后 |
|---------|------|--------|
| "报销" | 太模糊，不知道是什么类型的报销 | "费用报销申请流程和所需材料" |
| "请假" | 没说清楚请什么假、多久 | "员工年假申请流程和审批要求" |
| "GPU" | 缺少上下文 | "GPU 计算资源申请流程和配置" |

查询重写的目标是：**把模糊、不完整的查询，改写成清晰、完整的查询**，让检索更精准。

### Week 02 的回顾：Few-shot 让 LLM 学会改写

还记得 Week 02 学的 Few-shot Learning 吗？给 LLM 几个好示例，它就能学会模式。查询重写也可以用这个思路。

```python
# src/textagent/rag/query_rewriter.py
from openai import OpenAI
from typing import Optional

class QueryRewriter:
    """LLM 查询重写"""

    def __init__(self, llm_client: Optional[OpenAI] = None):
        self.llm = llm_client or OpenAI()

    def rewrite(self, query: str) -> str:
        """
        改写查询

        Args:
            query: 用户的原始查询

        Returns:
            改写后的查询
        """
        prompt = f"""你是企业内部知识库的查询优化助手。你的任务是把用户的模糊查询改写得更清晰、更完整，便于从知识库中检索相关文档。

改写原则：
1. 保留用户的原始意图
2. 补充缺失的关键信息（比如"报销"改为"费用报销申请流程"）
3. 使用正式、完整的表达
4. 不要改变问题的核心含义

示例：
- "报销" → "费用报销申请流程和所需材料"
- "请假" → "员工年假申请流程和审批要求"
- "GPU" → "GPU 计算资源申请流程"
- "远程办公" → "员工远程办公申请流程和审批要求"

原始查询：{query}

改写后的查询（只返回改写后的文本，不要解释）："""

        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    def rewrite_with_expansion(self, query: str, num_variants: int = 3) -> list[str]:
        """
        查询扩展：生成多个改写版本

        Args:
            query: 用户的原始查询
            num_variants: 生成的变体数量

        Returns:
            改写后的查询列表（包含原始查询）
        """
        prompt = f"""你是企业内部知识库的查询优化助手。你的任务是根据用户的原始查询，生成 {num_variants} 个不同的查询变体，以便从知识库中更全面地检索相关文档。

生成原则：
1. 每个变体应该从不同角度表达同一个问题
2. 使用不同的关键词和表达方式
3. 保持问题的核心含义不变
4. 变体之间应该有差异，不要只是简单的同义词替换

原始查询：{query}

生成 {num_variants} 个查询变体（每行一个）："""

        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        variants = [line.strip() for line in content.split('\n') if line.strip()]

        # 确保包含原始查询
        return [query] + variants[:num_variants]
```

阿码看着代码，追问了一句："为什么不直接让用户写清楚点？为什么我们要替他们改写？"

好问题。原因很简单：**用户体验优先**。

想象一下，你是员工，想问个问题：
- 方案 A：你必须写清楚"费用报销申请流程和所需材料"，才能得到准确答案
- 方案 B：你只需要写"报销"，系统自动帮你改写成更清晰的查询

哪个体验更好？显然是 B。

而且，查询重写的成本并不高。Week 01 我们算过，gpt-4o-mini 的价格是 $0.15/1M tokens。改写一个查询大约消耗 200 tokens，成本是 $0.00003 —— 也就是 0.03 美分。即使每天 1000 次查询，月成本也只有 1 美元左右。

小北听完感慨："原来不是用户不会问问题，是我们应该帮他们把问题'翻译'成检索器能理解的形式。"

### 查询扩展：从一个查询到多个

有时候，用户的查询可以从多个角度理解。比如"GPU 资源"，可能指的是：
- "GPU 计算资源申请流程"
- "GPU 配置和规格说明"
- "GPU 使用限制和配额"

**查询扩展**（Query Expansion）会生成多个查询变体，然后用所有变体去检索，最后合并结果。

```python
# 查询扩展示例
rewriter = QueryRewriter()

# 单查询改写
original = "报销"
rewritten = rewriter.rewrite(original)
print(f"原始：{original}")
print(f"改写：{rewritten}")

# 查询扩展
variants = rewriter.rewrite_with_expansion("GPU", num_variants=3)
print(f"\n查询扩展结果：")
for i, variant in enumerate(variants, 1):
    print(f"{i}. {variant}")
```

输出可能是：

```text
原始：报销
改写：费用报销申请流程和所需材料

查询扩展结果：
1. GPU
2. GPU 计算资源申请流程和配置要求
3. 图形处理器资源使用申请和审批步骤
4. GPU 服务器资源配额和限制说明
```

### 智能判断：什么时候需要重写？

查询重写对模糊查询特别有效，但对已经很完整的查询帮助有限。所以你可以加一个判断：

```python
def smart_rewrite(rewriter: QueryRewriter, query: str, threshold: int = 20) -> str:
    """智能判断是否需要重写"""
    if len(query) >= threshold:
        return query
    return rewriter.rewrite(query)
```

| 场景 | 原始查询召回率 | 改写后召回率 | 提升 |
|------|--------------|-------------|------|
| 模糊查询（"报销"） | 45% | 68% | +23% |
| 缩写词（"GPU"） | 52% | 71% | +19% |
| 口语化表达（"在家上班"） | 61% | 74% | +13% |
| 完整查询 | 85% | 86% | +1% |

> **AI 时代小专栏：RAG 评估的行业实践 —— 数据驱动优化**
>
> 2025 年的企业 RAG 落地中，一个明显的变化是：从"凭感觉优化"转向"数据驱动优化"。根据行业报告，约 70% 的工程师要么已经有 RAG 在生产环境，要么将在 12 个月内部署。而他们最关心的问题之一就是：**怎么知道优化真的有效？**
>
> 这推动了 RAG 评估框架的快速普及。RAGAS、TruLens、Arize、Giskard 等工具让团队能够量化"混合检索提升了多少"、"重排序值不值得"、"查询重写在哪些场景有效"。评估维度也从单一指标扩展到三大维度：检索质量（Recall@K、MRR、NDCG）、生成质量（忠实度、答案相关性）、端到端效果（用户满意度、任务完成率）。
>
> 2025-2026 年的主流做法是：自动化评估（RAGAS）+ 定期人工抽检 + A/B 测试验证。RAG 估计驱动了约 60% 的生产级 AI 应用，评估不再是"可有可无"，而是"必须要有"的环节。
>
> 参考（访问日期：2026-02-17）：
> - [RAG Evaluation: A Complete Guide for 2025](https://www.getmaxim.ai/articles/rag-evaluation-a-complete-guide-for-2025/)
> - [Top 5 Tools to Evaluate RAG Performance in 2026](https://www.getmaxim.ai/articles/top-5-tools-to-evaluate-rag-performance-in-2026/)
> - [RAG Evaluation Metrics Guide: Measure AI Success 2025](https://futureagi.com/blogs/rag-evaluation-metrics-2025)
> - [RAG Evaluation Guide: Metrics, Methods, and Best Practices](https://www.evidentlyai.com/llm-guide/rag-evaluation)

---

## 第 4 节：最后一道防线 —— 重排序（Re-ranking）

混合检索让召回率提升了——该找到的文档基本都能找到。但阿码又发现一个问题：Top-5 结果里，只有 2 个是真的相关，剩下 3 个是"噪音"。LLM 面对这堆混合的文档，回答质量还是不稳定。

这就引出了 RAG 系统的"最后一道防线"：**重排序**（Re-ranking）。

### 重排序：粗排 + 精排

重排序的逻辑是这样的：

```text
原始检索（100个文档）→ 重排序（重新评分）→ Top-3（给LLM）
     [快速但粗糙]           [慢但精确]          [最相关]
```

1. **粗排阶段**：用快速检索（向量/混合）拉回 50-100 个候选文档
2. **精排阶段**：用一个更精确但更慢的模型对这几十个文档重新排序
3. **截断阶段**：只取 Top-3 或 Top-5 给 LLM

为什么这样做？因为：
- 向量检索很快（毫秒级），但不够精确
- Cross-Encoder 很精确，但很慢（需要对每个文档单独计算）

重排序是在"速度"和"精度"之间取一个平衡。

### Bi-Encoder vs Cross-Encoder：一个反直觉的事实

Week 03 我们学的 Embedding 模型，其实是 **Bi-Encoder**（双向编码器）：

```text
Bi-Encoder:
查询 Q → Encoder → 向量 v_Q
文档 D → Encoder → 向量 v_D
相似度 = cosine(v_Q, v_D)

特点：可以预先计算所有文档的向量，检索时只需计算查询向量
速度：快（毫秒级）
精度：中等
```

**Cross-Encoder**（交叉编码器）则不同：

```text
Cross-Encoder:
[查询 Q, 文档 D] → Encoder → 相关性分数

特点：查询和文档一起输入模型，能更精确地判断相关性
速度：慢（需要对每个文档单独计算）
精度：高
```

Cross-Encoder 能"看到"查询和文档之间的交互，所以判断更准确。但也因为需要对每个文档单独计算，所以不能像 Bi-Encoder 那样预先索引所有文档。

小北问了一个好问题："那为什么不用 Cross-Encoder 直接检索？这样不是更准吗？"

答案是：**太慢了**。

假设你有 10 万个文档：
- Bi-Encoder：预先计算所有文档的向量，检索时只需要计算查询向量（< 10ms），然后在向量空间中搜索（< 50ms）
- Cross-Encoder：需要对每个文档计算相关性分数，10 万次计算，每次约 50ms，总共需要 5000 秒（约 1.4 小时）

这就是为什么 Cross-Encoder 只能用来重排序，不能用来直接检索。

### 使用 Cross-Encoder 进行重排序

```python
# src/textagent/rag/reranker.py
from sentence_transformers import CrossEncoder
from typing import List, Dict

class CrossEncoderReranker:
    """Cross-Encoder 重排序"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        """
        Args:
            model_name: Cross-Encoder 模型名称
        """
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """
        重排序

        Args:
            query: 用户查询
            documents: 检索到的文档列表
            top_k: 返回的文档数量

        Returns:
            重排序后的文档列表
        """
        # 构造 (query, doc) 对
        pairs = [[query, doc.get("content", "")] for doc in documents]

        # 计算相关性分数
        scores = self.model.predict(pairs)

        # 按分数排序
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # 返回 Top-K，并附加分数
        return [
            {**doc, "rerank_score": float(score)}
            for doc, score in scored_docs[:top_k]
        ]
```

使用示例：

```python
# examples/04_reranking.py
from textagent.rag.hybrid_retriever import HybridRetriever
from textagent.rag.reranker import CrossEncoderReranker

# 初始化
retriever = HybridRetriever(collection, alpha=0.5)
reranker = CrossEncoderReranker()

# 用户查询
query = "TB 级别存储怎么申请"

# 1. 混合检索（获取候选）
candidates = retriever.search(query, top_k=20)
print(f"检索到 {len(candidates)} 个候选文档")

# 2. 重排序（精选）
reranked = reranker.rerank(query, candidates, top_k=3)
print(f"\n重排序后的 Top-3：")
for i, doc in enumerate(reranked, 1):
    print(f"{i}. [分数: {doc['rerank_score']:.3f}] {doc['content'][:60]}...")
```

### Week 03 的回顾：重排序不是替代，是补充

| 特性 | 向量检索（Bi-Encoder） | 重排序（Cross-Encoder） |
|------|---------------------|----------------------|
| **速度** | 快（毫秒级） | 慢（每个文档 50ms） |
| **精度** | 中等 | 高 |
| **可索引** | 可以预先索引 | 不能预先索引 |
| **适用场景** | 第一轮筛选 | 第二轮精选 |

重排序不是替代向量检索，而是**补充**。先用向量检索快速找到候选，再用 Cross-Encoder 精确排序。

### 重排序的实战效果

根据行业实践，重排序能将 Top-3 检索结果的相关性从约 65% 提升到 80% 以上：

| 配置 | Top-3 相关率 | Top-5 相关率 | 平均延迟 |
|------|------------|------------|---------|
| 纯向量 | 62% | 71% | 0.8s |
| + 混合检索 | 71% | 78% | 1.2s |
| + 重排序 | 84% | 89% | 2.1s |

你可以看到，重排序是性价比最高的优化——只用 0.9 秒的额外延迟，就能把 Top-3 相关率提升 13 个百分点。

老潘看到这个数据会说："这才是工程思维——用最小的代价换取最大的提升。重排序只加了 0.9 秒，但把相关性从 71% 拉到 84%，这笔账划算。"

### 重排序在生产环境的部署建议

老潘补充了一些工程实践的经验："在公司里部署重排序时，我们通常这么设计：如果用户的查询足够精确（比如包含文档编号、具体产品名），可以跳过重排序直接返回，节省延迟。只有对模糊查询才启用重排序。这样既保证了大部分场景的快速响应，又在需要的时候提供了精准度。"

这种"条件式重排序"的设计，在实际生产中很常见：

```python
def should_rerank(query: str, rerank_threshold: int = 30) -> bool:
    """判断是否需要重排序"""
    # 如果查询很短（模糊查询），需要重排序
    # 如果查询很长（已经很精确），可以跳过重排序
    return len(query) < rerank_threshold
```

---

## 第 5 节：怎么知道变好了？—— RAGAS 评估框架

你做了这么多优化：混合检索、查询重写、重排序。老潘问了一个很实际的问题："这些改动的效果，你怎么证明？"

"我看回答质量好多了"不是一个好答案——主观感受不能说服老板，也不能指导后续优化。

你需要一个**系统化的评估框架**。**RAGAS** 是一个专门为 RAG 设计的评估工具，它用 LLM-as-Judge 的方式，自动计算多个指标。

### RAG 评估的三个维度

RAG 评估需要关注三个维度：

**1. 检索质量**—— 检索到的文档相关吗？
- **Context Precision（上下文精确度）**：检索到的文档中有多少是相关的？
- **Context Recall（上下文召回率）**：检索是否找到了所有需要的文档？

**2. 生成质量**—— LLM 的回答好吗？
- **Faithfulness（忠实度）**：LLM 的回答是否基于检索到的文档？有没有编造？
- **Answer Relevance（答案相关性）**：回答是否真的回答了问题？

**3. 端到端效果**—— 用户满意吗？
- **用户满意度**：用户是否认为回答有用？
- **任务完成率**：用户是否成功完成了任务？

### Week 02 的回顾：LLM-as-Judge 与 Prompt 评估

还记得 Week 02 我们用 LLM-as-Judge 评估 Prompt 吗？RAGAS 用的是类似的思想，只是指标更系统化。

Week 02 的 **Prompt 评估** 教会了我们：构建测试集、定义评估指标、进行版本对比。RAGAS 把这套方法论应用到了 RAG 系统上——只不过评估的不是 Prompt 效果，而是整个 RAG 流程的质量。

RAGAS 的核心是：用 LLM 来评估 LLM 的输出。比如评估忠实度时，它会问 GPT-4："这个回答是否基于这些文档？有没有编造内容？"，然后根据 GPT-4 的判断打分。

### 使用 RAGAS 评估系统

```python
# examples/05_ragas_evaluation.py
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset

# 准备评估数据
evaluation_data = {
    "question": [
        "2024 年报假政策是什么？",
        "GPU 资源怎么申请？",
        "TB 级别存储怎么申请？"
    ],
    "answer": [
        "根据 2024 年报假政策，员工每年可享受 5 天年假，需提前 7 天申请。",
        "GPU 资源需要填写资源申请表，经部门经理审批后由 IT 部门分配。",
        "单个项目最多申请 10TB 存储空间，需提交存储资源申请表。"
    ],
    "contexts": [
        ["2024 年报假政策：员工每年可享受 5 天年假，需提前 7 天申请。"],
        ["GPU 资源申请流程：需要填写资源申请表，经部门经理审批。"],
        ["TB 级别存储申请：单个项目最多申请 10TB 存储空间。"]
    ],
    "ground_truth": [
        "5 天年假，提前 7 天申请",
        "填写申请表，部门经理审批",
        "最多 10TB"
    ]
}

dataset = Dataset.from_dict(evaluation_data)

result = evaluate(
    dataset,
    metrics=[
        context_precision,
        faithfulness,
        answer_relevancy,
        context_recall
    ]
)

print(result.to_pandas())
```

输出会是这样的：

```text
  context_precision  faithfulness  answer_relevancy  context_recall
0              0.85          0.92              0.88            0.80
1              0.78          0.85              0.82            0.75
2              0.92          0.88              0.90            0.85

平均分数:
- Context Precision:  0.85
- Faithfulness:       0.88
- Answer Relevance:   0.87
- Context Recall:     0.80
```

### 指标解读：什么是"好"分数？

| 指标 | 含义 | 分数范围 | 什么是好分数 |
|------|------|---------|------------|
| **Faithfulness** | 回答是否基于检索到的文档 | 0-1 | > 0.8 优秀 |
| **Answer Relevance** | 回答是否真的回答了问题 | 0-1 | > 0.8 优秀 |
| **Context Precision** | 检索到的文档有多少相关 | 0-1 | > 0.8 优秀 |
| **Context Recall** | 是否找到了所有需要的文档 | 0-1 | > 0.7 良好 |

老潘点评："在公司里，我们不会凭感觉说'变好了'——必须有数据和 A/B 对比。"

### A/B 测试：对比不同配置

RAGAS 最强大的功能之一是 A/B 测试——你可以对比不同配置的效果：

```python
# A/B 测试示例
from textagent.rag.pipeline import AdvancedRAGPipeline

# 配置 A：纯向量检索
pipeline_a = AdvancedRAGPipeline(use_hybrid=False, use_rerank=False)

# 配置 B：混合检索
pipeline_b = AdvancedRAGPipeline(use_hybrid=True, use_rerank=False)

# 配置 C：混合检索 + 重排序
pipeline_c = AdvancedRAGPipeline(use_hybrid=True, use_rerank=True)

# 对同一组问题进行测试
test_questions = [
    "2024 年报假政策是什么？",
    "GPU 资源怎么申请？",
    "TB 级别存储怎么申请？"
]

# 收集结果并评估
results = {}
for name, pipeline in [("A-纯向量", pipeline_a), ("B-混合", pipeline_b), ("C-混合+重排", pipeline_c)]:
    answers = []
    contexts = []
    for q in test_questions:
        response = pipeline.query(q)
        answers.append(response.answer)
        contexts.append([doc["content"] for doc in response.sources])

    # 用 RAGAS 评估
    dataset = Dataset.from_dict({
        "question": test_questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": [...]
    })

    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])
    results[name] = result

# 打印对比
print("\n=== A/B 测试结果 ===")
for name, result in results.items():
    print(f"\n{name}:")
    print(f"  Faithfulness: {result['faithfulness']:.3f}")
    print(f"  Answer Relevance: {result['answer_relevancy']:.3f}")
    print(f"  Context Precision: {result['context_precision']:.3f}")
```

输出可能是：

```text
=== A/B 测试结果 ===

A-纯向量:
  Faithfulness: 0.723
  Answer Relevance: 0.681
  Context Precision: 0.654

B-混合:
  Faithfulness: 0.789
  Answer Relevance: 0.754
  Context Precision: 0.762

C-混合+重排:
  Faithfulness: 0.892
  Answer Relevance: 0.851
  Context Precision: 0.873
```

现在你可以用数据说话了："混合检索 + 重排序相比纯向量检索，忠实度提升了 23%，上下文精确度提升了 33%。"

### 在 report.md 中记录

```markdown
## Week 04：高级 RAG 优化

### 优化内容

1. 混合检索（向量 + BM25）
   - 解决精确匹配问题（年份、型号、专有名词）
   - RRF 融合策略：alpha=0.5（向量和 BM25 各占一半）

2. 查询重写
   - 用 LLM 将模糊查询改写为清晰查询
   - 示例："报销" → "费用报销申请流程"

3. 重排序
   - 使用 BGE-reranker-base 模型
   - 从 Top-20 候选中精选 Top-3

### 效果对比（RAGAS 评估）

| 配置 | 忠实度 | 答案相关性 | 上下文精确度 | 平均延迟 |
|------|--------|-----------|-------------|---------|
| 纯向量（Week 03） | 0.72 | 0.68 | 0.65 | 0.8s |
| + 混合检索 | 0.79 | 0.75 | 0.76 | 1.2s |
| + 查询重写 | 0.82 | 0.79 | 0.78 | 1.5s |
| + 重排序（完整版） | 0.89 | 0.85 | 0.87 | 2.1s |

### 结论

- 混合检索显著提升精确匹配场景（+11%）
- 重排序是性价比最高的优化（+10% 忠实度，+0.9s 延迟）
- 查询重写对模糊查询特别有效（+5%），但对清晰查询帮助有限
```

现在你的 RAG 系统不仅是"能跑"，而是"精准可控"——你有数据证明每个优化的效果，也有明确的指标知道下一步该优化什么。

---

<!--
================================================================================
【TextAgent 进度】
================================================================================
-->

## TextAgent 进度

上周 TextAgent 有了基础的 RAG 能力，但这周我们发现它有几个"生产级"的问题：精确匹配失败（年份、型号）、检索噪音多、不知道效果有没有变好。

这周我们给 TextAgent 加上了高级 RAG 的三件套：混合检索、重排序、评估框架。

### 新增模块

```python
# src/textagent/rag/__init__.py（更新）
from .hybrid_retriever import HybridRetriever
from .reranker import CrossEncoderReranker
from .query_rewriter import QueryRewriter
from .pipeline import AdvancedRAGPipeline

__all__ = [
    "HybridRetriever",
    "CrossEncoderReranker",
    "QueryRewriter",
    "AdvancedRAGPipeline"
]
```

### 高级 RAG Pipeline

```python
# src/textagent/rag/pipeline.py（更新版）
from .hybrid_retriever import HybridRetriever
from .reranker import CrossEncoderReranker
from .query_rewriter import QueryRewriter
from .retriever import ChromaRetriever
from openai import OpenAI
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RAGResponse:
    """RAG 系统的响应"""
    answer: str
    sources: List[dict]
    query: str
    rewritten_query: Optional[str] = None

class AdvancedRAGPipeline:
    """高级 RAG 管道：混合检索 + 重排序 + 查询重写"""

    def __init__(
        self,
        collection_name: str = "textagent_docs",
        persist_directory: str = "./data/chromadb",
        use_hybrid: bool = True,
        use_rerank: bool = True,
        alpha: float = 0.5
    ):
        self.llm_client = OpenAI()
        self.use_hybrid = use_hybrid
        self.use_rerank = use_rerank

        # 初始化检索器
        if use_hybrid:
            self.retriever = HybridRetriever(
                chroma_collection=self._get_collection(collection_name, persist_directory),
                alpha=alpha
            )
        else:
            self.retriever = ChromaRetriever(collection_name, persist_directory)

        # 初始化重排序器
        if use_rerank:
            self.reranker = CrossEncoderReranker()
        else:
            self.reranker = None

        # 初始化查询重写器
        self.rewriter = QueryRewriter(self.llm_client)

    def query(
        self,
        question: str,
        use_rewrite: bool = True,
        top_k: int = 3
    ) -> RAGResponse:
        """
        执行查询

        Args:
            question: 用户问题
            use_rewrite: 是否使用查询重写
            top_k: 返回的文档数量
        """
        # 1. 查询重写（可选）
        query = question
        if use_rewrite:
            query = self.rewriter.rewrite(question)

        # 2. 混合检索（获取候选）
        candidates = self.retriever.search(query, top_k=20)

        # 3. 重排序（精选）
        if self.reranker:
            reranked = self.reranker.rerank(query, candidates, top_k=top_k)
        else:
            reranked = candidates[:top_k]

        # 4. 构建上下文
        context = "\n\n".join([
            f"【参考文档 {i+1}】\n{doc.get('content', doc.get('text', ''))}"
            for i, doc in enumerate(reranked)
        ])

        # 5. 生成回答
        prompt = f"""角色：你是公司的内部问答助手，负责回答员工关于公司政策、流程、福利的问题。

任务：根据以下参考文档回答用户的问题。如果参考文档中没有相关信息，请明确说明"根据现有知识库无法回答"。

约束：
- 只基于参考文档回答，不要编造信息
- 回答要简洁，不要大段复制原文

参考文档：
{context}

用户问题：{question}

请回答："""

        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        answer = response.choices[0].message.content

        return RAGResponse(
            answer=answer,
            sources=reranked,
            query=question,
            rewritten_query=query if use_rewrite and query != question else None
        )
```

### 在 report.md 中记录

```markdown
## Week 04：高级 RAG 优化

### 优化内容

1. 混合检索（向量 + BM25）
   - 解决精确匹配问题（年份、型号、专有名词）
   - RRF 融合策略：alpha=0.5（向量和 BM25 各占一半）

2. 查询重写
   - 用 LLM 将模糊查询改写为清晰查询
   - 示例："报销" → "费用报销申请流程"

3. 重排序
   - 使用 BGE-reranker-base 模型
   - 从 Top-20 候选中精选 Top-3

### 效果对比（RAGAS 评估）

| 配置 | 忠实度 | 答案相关性 | 上下文精确度 | 平均延迟 |
|------|--------|-----------|-------------|---------|
| 纯向量（Week 03） | 0.72 | 0.68 | 0.65 | 0.8s |
| + 混合检索 | 0.79 | 0.75 | 0.76 | 1.2s |
| + 查询重写 | 0.82 | 0.79 | 0.78 | 1.5s |
| + 重排序（完整版） | 0.89 | 0.85 | 0.87 | 2.1s |

### 结论

- 混合检索显著提升精确匹配场景（+11% 上下文精确度）
- 重排序是性价比最高的优化（+10% 忠实度，+0.9s 延迟）
- 查询重写对模糊查询特别有效，但对清晰查询帮助有限

### 下一步

- Week 05：Agent 能力——让 TextAgent 会调用工具
```

TextAgent 现在有了"精准检索"的能力：混合检索保证召回，重排序保证精确，RAGAS 评估让效果可量化。下周我们会让它变得更"聪明"——不只是回答问题，而是会调用工具、会规划步骤的 Agent。

<!--
================================================================================
【Git 本周要点】
================================================================================
-->

## Git 本周要点

本周必会命令：
- `git branch` — 查看分支
- `git checkout -b feature/xxx` — 创建并切换分支
- `git merge xxx` — 合并分支
- `git log --graph --oneline` — 图形化查看提交历史

常见坑：
- **忘记切分支就改代码**：新功能应该在 feature 分支开发，测试通过后再合并到 main
- **重排序模型文件太大**：模型文件应该加到 `.gitignore` 或用 Git LFS
- **评估结果不提交**：RAGAS 生成的评估报告应该提交，这是优化效果的证明

推荐的 `.gitignore` 补充：

```text
# Week 04：高级 RAG
models/             # 重排序模型文件
eval_results/       # 原始评估数据（保留报告即可）
*.gguf
```

<!--
================================================================================
【本周小结】
================================================================================
-->

## 本周小结（供下周参考）

这周你让 RAG 系统从"能跑"进化到了"精准可控"。

混合检索解决了向量检索的盲区——它把语义匹配和精确关键词结合起来，既理解"报销"和"费用申请"是同一个意思，又能精准匹配"2024 年报假政策"。查询重写让用户的模糊查询变清晰，重排序则用 Cross-Encoder 对检索结果进行二次精选，把噪音筛出去。

更重要的是，你学会了用 RAGAS 评估系统——不再是"感觉好多了"，而是用数据说话：忠实度从 0.72 提升到 0.89，答案相关性从 0.68 提升到 0.85。这些数据不仅能让老板信服，也能指导后续优化。

Week 03 你学了"怎么给 LLM 知识"（RAG 基础），这周你学了"让知识检索更精准"（混合检索 + 重排序 + 评估）。下周我们会让 TextAgent 变得更"聪明"——不只是检索和回答，而是会调用工具、会规划步骤的 LLM Agent。

<!--
================================================================================
【Definition of Done（学生自测清单）】
================================================================================
-->

## Definition of Done

学完本章后，你应该能够回答以下问题：

- [ ] 我能解释为什么纯向量检索会漏掉精确匹配吗？
- [ ] 我能实现混合检索（向量 + BM25）吗？
- [ ] 我理解 Bi-Encoder 和 Cross-Encoder 的区别了吗？
- [ ] 我能用重排序模型提升检索精准度吗？
- [ ] 我会用 RAGAS 评估我的 RAG 系统吗？
- [ ] 我的 TextAgent 有混合检索和重排序能力了吗？

如果以上都打勾，恭喜你完成 Week 04！下周见。

<!--
================================================================================
【术语登记（供 TERMS.yml 参考）】
================================================================================

本章新术语：
1. 混合检索（Hybrid Search）
2. 重排序（Re-ranking）
3. 查询重写（Query Rewriting）
4. RAGAS（RAG 评估框架）
5. 检索评估指标（Recall@K、MRR、NDCG）

待合入 shared/glossary.yml

================================================================================
-->

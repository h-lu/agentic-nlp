# Week 04 作业：高级 RAG 与评估

上周你搭建了基础的 RAG 系统，但这周你发现了它的局限性：精确匹配失败（年份、产品型号）、检索噪音过多、效果无法量化评估。

这周你要让 RAG 系统从"能跑"进化到"精准可控"——混合检索保证召回，重排序保证精确，RAGAS 评估让效果可量化。

---

## 作业背景

你所在公司的 RAG 系统上线后，收到了一些负面反馈：

- 员工问"2024 年报假政策"，系统却回答了 2023 年的内容
- 员工问"TB 级别存储怎么申请"，系统返回的是"GPU 资源申请"的文档
- Top-5 结果里，只有 2 个真的相关，剩下 3 个是噪音
- 老板问："这些优化效果，你怎么证明？"

这周你要用混合检索、重排序、查询重写和 RAGAS 评估来解决这些问题。

---

## 核心任务（必做，60 分）

### Part 1：实现混合检索（20 分）

纯向量检索擅长语义理解，但不擅长精确匹配。混合检索结合了向量检索和 BM25 关键词检索的优势。

#### 要求

**1.1 实现 BM25 检索器（8 分）**

```python
# rag/bm25_retriever.py
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
import jieba

class BM25Retriever:
    """BM25 关键词检索器"""

    def __init__(self):
        self.bm25_index: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        self.tokenized_docs: List[List[str]] = []

    def build_index(self, documents: List[str]):
        """
        构建 BM25 索引

        Args:
            documents: 文档列表
        """
        # TODO: 实现
        # 1. 使用 jieba 分词（中文友好）
        # 2. 构建 BM25Okapi 索引
        # 3. 保存原始文档
        pass

    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回的文档数量

        Returns:
            [{"content": "...", "score": 0.85, "rank": 0}, ...]
        """
        # TODO: 实现
        # 1. 对查询进行分词
        # 2. 调用 BM25 计算分数
        # 3. 返回 Top-K 结果
        pass
```

**1.2 实现混合检索（8 分）**

```python
# rag/hybrid_retriever.py
from typing import List, Dict
from .bm25_retriever import BM25Retriever

def reciprocal_rank_fusion(
    vec_results: List[Dict],
    bm25_results: List[Dict],
    k: int = 60,
    alpha: float = 0.5
) -> List[Dict]:
    """
    RRF 融合算法

    Args:
        vec_results: 向量检索结果（已排序）
        bm25_results: BM25 检索结果（已排序）
        k: RRF 常数
        alpha: 向量检索权重（0-1），BM25 权重为 1-alpha

    Returns:
        融合后的结果列表
    """
    # TODO: 实现 RRF 算法
    # 1. 构建文档 ID 到分数的映射
    # 2. 向量检索分数 = alpha * (1 / (k + rank + 1))
    # 3. BM25 分数 = (1-alpha) * (1 / (k + rank + 1))
    # 4. 合并分数并排序
    pass

class HybridRetriever:
    """混合检索：向量 + BM25"""

    def __init__(self, chroma_collection, alpha: float = 0.5):
        """
        Args:
            chroma_collection: ChromaDB Collection
            alpha: 向量检索权重
        """
        self.collection = chroma_collection
        self.alpha = alpha
        self.bm25 = BM25Retriever()

    def build_index(self, documents: List[str]):
        """构建 BM25 索引"""
        # TODO: 调用 BM25Retriever.build_index
        pass

    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回的文档数量

        Returns:
            融合后的结果列表
        """
        # TODO: 实现
        # 1. 向量检索
        # 2. BM25 检索
        # 3. RRF 融合
        # 4. 返回 Top-K
        pass
```

**1.3 对比实验（4 分）**

对比纯向量检索和混合检索的效果：

| 查询 | 期望文档 | 纯向量 Top-1 | 混合检索 Top-1 | 是否改善 |
|------|---------|-------------|---------------|---------|
| 2024 年报假政策 | remote_work_2024.md | ? | ? | ? |
| TB 级别存储怎么申请 | storage_policy.md | ? | ? | ? |
| GPU 资源申请 | gpu_resource.md | ? | ? | ? |

**输出分析**：
```markdown
### 混合检索效果分析

| 查询类型 | 纯向量准确率 | 混合检索准确率 | 提升 |
|---------|------------|---------------|------|
| 精确匹配（年份/型号） | ? | ? | ? |
| 专有名词 | ? | ? | ? |
| 同义词查询 | ? | ? | ? |

**结论**：
- 混合检索在哪些场景下有显著提升？
- 是否有场景下效果反而下降？
```

**提交内容**：
- `rag/bm25_retriever.py`：BM25 检索器
- `rag/hybrid_retriever.py`：混合检索器
- `experiments/hybrid_test.py`：对比实验代码
- `report.md`：包含效果分析表

---

### Part 2：重排序实现（20 分）

混合检索提升了召回率，但 Top-5 结果里还是有噪音。重排序能帮你精选最相关的文档。

#### 要求

**2.1 实现 Cross-Encoder 重排序（10 分）**

```python
# rag/reranker.py
from typing import List, Dict
from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    """Cross-Encoder 重排序器"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        """
        Args:
            model_name: 重排序模型名称
        """
        # TODO: 初始化 CrossEncoder 模型
        pass

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
            重排序后的文档列表，附加 rerank_score
        """
        # TODO: 实现
        # 1. 构造 (query, doc) 对
        # 2. 调用 model.predict 计算分数
        # 3. 按分数排序，返回 Top-K
        pass
```

**2.2 对比重排序前后的效果（6 分）**

```python
# experiments/rerank_test.py

# 测试查询
test_queries = [
    "TB 级别存储怎么申请",
    "2024 年报假政策",
    "费用报销需要什么材料"
]

for query in test_queries:
    # 1. 混合检索获取 Top-10
    candidates = retriever.search(query, top_k=10)

    # 2. 重排序取 Top-3
    reranked = reranker.rerank(query, candidates, top_k=3)

    # 3. 人工判断相关性
    print(f"查询: {query}")
    print("重排序前 Top-3 相关性: ? / 3")
    print("重排序后 Top-3 相关性: ? / 3")
```

**输出表格**：

| 查询 | 重排序前 Top-3 相关 | 重排序后 Top-3 相关 | 提升 |
|------|------------------|------------------|------|
| TB 级别存储怎么申请 | ?/? | ?/? | ? |
| 2024 年报假政策 | ?/? | ?/? | ? |
| 费用报销需要什么材料 | ?/? | ?/? | ? |

**2.3 延迟分析（4 分）**

测量重排序的延迟开销：

```python
import time

def measure_latency(pipeline, queries):
    """测量延迟"""
    # TODO: 实现延迟测量
    # 1. 测量纯混合检索的延迟
    # 2. 测量混合检索 + 重排序的延迟
    # 3. 计算平均延迟
    pass
```

**输出**：
```markdown
### 延迟分析

| 配置 | 平均延迟 | P50 | P95 |
|------|---------|-----|-----|
| 纯混合检索 | ? | ? | ? |
| + 重排序 | ? | ? | ? |
| 额外开销 | ? | ? | ? |

**结论**：
重排序的延迟开销是 ?ms，换取的相关性提升是 ?%，是否值得？
```

**提交内容**：
- `rag/reranker.py`：重排序器实现
- `experiments/rerank_test.py`：效果对比实验
- `report.md`：包含效果和延迟分析

---

### Part 3：RAGAS 评估（20 分）

你做了很多优化，但怎么证明效果真的变好了？RAGAS 能帮你量化评估。

#### 要求

**3.1 准备评估数据集（6 分）**

设计至少 10 个测试问题，每个问题包含：
- question：用户问题
- contexts：检索到的文档
- answer：RAG 系统的回答
- ground_truth：标准答案

> **提示**：`answer` 字段需要通过运行你的 RAG 系统生成。推荐流程：
> 1. 先完成 Part 1 和 Part 2 的混合检索 + 重排序实现
> 2. 运行 RAG 系统，对每个 `question` 生成回答
> 3. 将生成的回答填入 `answer` 列表，然后进行 RAGAS 评估

```python
# experiments/eval_dataset.py

EVALUATION_DATA = {
    "question": [
        "2024 年报假政策是什么？",
        # TODO: 再添加 9 个问题
    ],
    "contexts": [
        ["2024 年报假政策：员工每年可享受 5 天年假，需提前 7 天申请。"],
        # TODO: 对应的检索上下文
    ],
    "answer": [
        "根据 2024 年报假政策，员工每年可享受 5 天年假，需提前 7 天申请。",
        # TODO: RAG 系统的实际回答
    ],
    "ground_truth": [
        "5 天年假，提前 7 天申请",
        # TODO: 标准答案（用于评估）
    ]
}
```

**问题类型分布**：
- 至少 3 个精确匹配问题（年份、型号）
- 至少 3 个同义词问题
- 至少 2 个模糊查询问题
- 至少 2 个复杂推理问题

**3.2 使用 RAGAS 评估（8 分）**

```python
# experiments/ragas_eval.py
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset

def evaluate_rag_system(pipeline, test_data):
    """
    评估 RAG 系统

    Args:
        pipeline: RAG Pipeline
        test_data: 测试数据

    Returns:
        评估结果
    """
    # TODO: 实现
    # 1. 创建 Dataset
    # 2. 调用 evaluate
    # 3. 返回结果
    pass

# 对比不同配置
configs = {
    "纯向量": {"use_hybrid": False, "use_rerank": False},
    "混合检索": {"use_hybrid": True, "use_rerank": False},
    "混合+重排": {"use_hybrid": True, "use_rerank": True}
}

results = {}
for name, config in configs.items():
    pipeline = AdvancedRAGPipeline(**config)
    result = evaluate_rag_system(pipeline, EVALUATION_DATA)
    results[name] = result
```

**3.3 A/B 测试报告（6 分）**

生成 A/B 测试对比报告：

```markdown
### RAGAS A/B 测试结果

| 配置 | Faithfulness | Answer Relevance | Context Precision | Context Recall |
|------|-------------|-----------------|------------------|---------------|
| 纯向量 | ? | ? | ? | ? |
| 混合检索 | ? | ? | ? | ? |
| 混合+重排 | ? | ? | ? | ? |

**指标解读**：
- **Faithfulness（忠实度）**：回答是否基于检索到的文档（> 0.8 优秀）
- **Answer Relevance（答案相关性）**：回答是否真的回答了问题（> 0.8 优秀）
- **Context Precision（上下文精确度）**：检索到的文档有多少相关（> 0.8 优秀）
- **Context Recall（上下文召回率）**：是否找到了所有需要的文档（> 0.7 良好）

**结论**：
- 哪个配置效果最好？
- 每个优化带来的提升是多少？
- 是否有某个指标反而下降？
```

**提交内容**：
- `experiments/eval_dataset.py`：评估数据集
- `experiments/ragas_eval.py`：RAGAS 评估代码
- `report.md`：包含完整的 A/B 测试报告

---

## 进阶任务（选做，25 分）

### 任务 4：查询重写（15 分）

模糊查询是 RAG 系统的常见问题。查询重写能在检索前把用户问题改写得更清晰。

#### 要求

**4.1 实现查询重写（8 分）**

```python
# rag/query_rewriter.py
from openai import OpenAI
from typing import List

class QueryRewriter:
    """LLM 查询重写器"""

    def __init__(self, llm_client: OpenAI = None):
        # TODO: 初始化
        pass

    def rewrite(self, query: str) -> str:
        """
        改写查询

        Args:
            query: 用户的原始查询

        Returns:
            改写后的查询
        """
        # TODO: 实现
        # 使用 Few-shot 让 LLM 学会改写
        pass

    def rewrite_with_expansion(self, query: str, num_variants: int = 3) -> List[str]:
        """
        查询扩展：生成多个改写版本

        Args:
            query: 用户的原始查询
            num_variants: 生成的变体数量

        Returns:
            改写后的查询列表
        """
        # TODO: 实现
        pass
```

**4.2 测试查询重写效果（4 分）**

```python
# experiments/query_rewrite_test.py

TEST_QUERIES = [
    ("报销", "费用报销申请流程和所需材料"),
    ("请假", "员工年假申请流程和审批要求"),
    ("GPU", "GPU 计算资源申请流程"),
    # TODO: 再添加 3 个测试用例
]

for original, expected in TEST_QUERIES:
    rewritten = rewriter.rewrite(original)
    print(f"原始：{original}")
    print(f"改写：{rewritten}")
    print(f"期望：{expected}")
    print(f"匹配度：{self._similarity(rewritten, expected)}")
```

**4.3 端到端效果测试（3 分）**

对比查询重写前后的召回率：

```markdown
### 查询重写效果

| 查询类型 | 重写前召回率 | 重写后召回率 | 提升 |
|---------|------------|-------------|------|
| 极短查询（<5字） | ? | ? | ? |
| 模糊查询 | ? | ? | ? |
| 缩写词 | ? | ? | ? |
| 完整查询 | ? | ? | ? |

**结论**：
查询重写在哪些场景下最有效？
```

**提交内容**：
- `rag/query_rewriter.py`：查询重写器
- `experiments/query_rewrite_test.py`：效果测试
- `report.md`：包含效果分析

---

### 任务 5：高级重排序对比（10 分）

不同的重排序模型效果不同。对比至少 2 个重排序模型。

#### 要求

**5.1 实现多模型支持（5 分）**

```python
# experiments/reranker_comparison.py

RERANKER_MODELS = [
    "BAAI/bge-reranker-base",
    # TODO: 再添加至少 1 个重排序模型
    # 提示：可以试试 bge-reranker-large 或其他模型
]

def compare_rerankers(query: str, candidates: List[Dict]):
    """对比不同重排序模型"""
    # TODO: 实现
    # 1. 加载不同模型
    # 2. 对同一批候选文档重排序
    # 3. 对比 Top-3 结果
    pass
```

**5.2 效果与延迟对比（5 分）**

```markdown
### 重排序模型对比

| 模型 | Top-3 准确率 | 平均延迟 | 模型大小 |
|------|------------|---------|---------|
| bge-reranker-base | ? | ? | ? |
| ? | ? | ? | ? |

**结论**：
- 哪个模型效果最好？
- 哪个性价比最高？
- 生产环境应该选哪个？
```

**提交内容**：
- `experiments/reranker_comparison.py`：模型对比代码
- `report.md`：包含对比结果

---

## 挑战任务（加分，15 分）

### 任务 6：参数优化实验（8 分）

混合检索、重排序都有超参数（alpha、top_k、chunk_size 等）。设计系统化的实验找到最优配置。

#### 要求

**6.1 Alpha 参数网格搜索（4 分）**

```python
# experiments/alpha_tuning.py

ALPHA_VALUES = [0.0, 0.25, 0.5, 0.75, 1.0]

def grid_search_alpha(test_queries, alpha_values):
    """网格搜索最优 alpha"""
    # TODO: 实现
    # 1. 对每个 alpha 值测试
    # 2. 记录召回率和精确率
    # 3. 绘制曲线
    pass
```

**6.2 Top-K 参数实验（4 分）**

```python
# experiments/topk_tuning.py

TOP_K_VALUES = [3, 5, 10, 20, 50]

def analyze_top_k_impact(test_queries, top_k_values):
    """分析 top_k 对效果的影响"""
    # TODO: 实现
    pass
```

**输出**：
```markdown
### 参数优化结果

**Alpha 参数影响**：
| Alpha | Context Precision | Context Recall | F1 |
|-------|-----------------|---------------|-----|
| 0.0 | ? | ? | ? |
| 0.5 | ? | ? | ? |
| 1.0 | ? | ? | ? |

最优 Alpha：?

**Top-K 参数影响**：
| Top-K | 召回率 | 精确率 | 延迟 |
|-------|-------|-------|------|
| 3 | ? | ? | ? |
| 10 | ? | ? | ? |
| 20 | ? | ? | ? |

最优配置：alpha=?, top_k=?
```

---

### 任务 7：成本分析（7 分）

高级 RAG 不是免费的——重排序增加延迟，查询重写增加 LLM 调用成本。分析成本并给出优化建议。

#### 要求

**7.1 成本计算（4 分）**

```python
# experiments/cost_analysis.py

def estimate_rag_cost(
    queries_per_day: int,
    avg_query_tokens: int,
    use_rerank: bool,
    use_rewrite: bool
) -> dict:
    """
    估算高级 RAG 成本

    Returns:
        {
            "embedding_cost": Embedding 成本,
            "llm_cost": LLM 生成成本,
            "rewrite_cost": 查询重写成本,
            "total_daily": 每日总成本,
            "total_monthly": 每月总成本
        }
    """
    # TODO: 实现
    # 价格参考（2025-2026 年）
    # - GPT-4o-mini: $0.15/1M tokens (input), $0.60/1M (output)
    # - Embedding: $0.02/1M tokens
    pass
```

**7.2 成本优化建议（3 分）**

```markdown
### 成本分析与优化

**当前配置成本**：
- 每日查询：?
- 每月成本：?

**优化建议**：
1. **缓存查询重写结果**：相同查询不需要重复改写，预计节省 ?% 成本
2. **智能判断是否需要重排序**：如果 Top-3 分数都很高，可以跳过重排序
3. **选择更小的重排序模型**：从 large 改为 base，延迟降低 ?%，精度只降低 ?%

**优化后成本**：每月 ?（节省 ?%）
```

---

## AI 协作练习（可选）

Week 04 处于"识别期"，你需要学会审查 AI 生成的 RAG 代码。下面这段代码是某个 AI 工具生成的，请审查它：

### 待审查代码

```python
# AI 生成的混合检索代码（故意包含问题）
from openai import OpenAI
import chromadb

def create_hybrid_rag():
    """创建混合检索 RAG 系统"""
    client = chromadb.Client()
    collection = client.create_collection("docs")

    def search(query):
        # 向量检索
        vec_results = collection.query(
            query_texts=[query],
            n_results=10
        )

        # BM25 检索
        bm25_results = []  # TODO: 实现 BM25

        # 简单合并：取前 5 个向量结果 + 前 5 个 BM25 结果
        final_results = vec_results["documents"][0][:5] + bm25_results[:5]

        return final_results

    def answer(question):
        docs = search(question)
        context = "\n".join(docs)

        response = OpenAI().chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"回答：{context}\n\n问题：{question}"}]
        )
        return response.choices[0].message.content

    return answer
```

### 审查清单

请对照以下清单审查代码：

```markdown
## RAG 代码审查报告

### 1. 混合检索策略
- [ ] BM25 检索是空的（TODO 未实现），会导致什么问题？
- [ ] "简单合并"向量和 BM25 结果有什么问题？
- [ ] 没有使用 RRF 融合，会带来什么后果？

你的分析：
...

### 2. 重排序
- [ ] 有没有重排序？没有的话会有什么问题？
- [ ] 10 个候选文档直接合并，会不会引入太多噪音？

你的分析：
...

### 3. Prompt 设计
- [ ] Prompt 有没有角色定义？
- [ ] 有没有约束"只基于参考文档回答"？
- [ ] 直接拼接 10 个文档会有什么问题？

你的分析：
...

### 4. 模型选择
- [ ] 使用 GPT-4 是否有必要？
- [ ] 有没有考虑成本和延迟？

你的分析：
...

### 5. 错误处理
- [ ] 如果检索不到结果会怎样？
- [ ] 有没有处理空结果的情况？

你的分析：
...
```

### 你的修订版

基于审查，写出你的修订版本（只需修改关键部分）：

```python
# 我的修订版
def create_hybrid_rag_fixed():
    """修复后的混合检索 RAG 系统"""

    # 1. 修复 BM25 检索
    def bm25_search_fixed(query):
        # TODO: 你的实现
        pass

    # 2. 修复结果融合
    def merge_results_fixed(vec_results, bm25_results):
        # TODO: 你的实现（使用 RRF）
        pass

    # 3. 修复 Prompt
    def build_prompt_fixed(question, docs):
        # TODO: 你的实现
        pass

    # 4. 修复模型选择
    def answer_fixed(question):
        # TODO: 你的实现
        pass

    return answer_fixed
```

### 修订说明

解释你做的主要修改：

1. **BM25 检索修复**：...
2. **结果融合修复**：...
3. **Prompt 修复**：...
4. **模型选择修复**：...

**重要**：AI 协作练习不影响基础任务的评分，但需要展示你的审查过程和改进思路。

---

## 提交清单

在提交作业前，请确认以下内容：

### 文件结构

```
week04_作业_你的姓名/
├── rag/
│   ├── bm25_retriever.py      # BM25 检索器
│   ├── hybrid_retriever.py    # 混合检索器
│   ├── reranker.py            # 重排序器
│   ├── query_rewriter.py      # 查询重写器（进阶）
│   └── pipeline.py            # 完整 Pipeline（可选）
├── experiments/
│   ├── hybrid_test.py         # 混合检索测试
│   ├── rerank_test.py         # 重排序测试
│   ├── ragas_eval.py          # RAGAS 评估
│   ├── eval_dataset.py        # 评估数据集
│   ├── query_rewrite_test.py  # 查询重写测试（进阶）
│   └── reranker_comparison.py # 重排序模型对比（进阶）
├── data/
│   └── sample_docs/           # 示例文档
├── report.md                  # 完整实验报告
└── README.md                  # 简要说明
```

### 质量检查

- [ ] 所有代码都能独立运行
- [ ] API Key 没有硬编码
- [ ] 混合检索有对比实验数据
- [ ] 重排序有前后对比和延迟分析
- [ ] RAGAS 评估有至少 10 个测试问题
- [ ] A/B 测试有完整的对比表格
- [ ] report.md 包含所有实验结果
- [ ] 有运行输出或截图证明代码能工作

---

## 常见问题

**Q：我没有 GPU，能运行重排序模型吗？**

A：可以。BGE-reranker-base 是一个相对较小的模型（约 400MB），在 CPU 上运行速度也能接受（每个文档约 50ms）。如果你只有 20 个候选文档，重排序大约需要 1 秒。

**Q：jieba 分词需要额外安装吗？**

A：是的。`pip install jieba`。jieba 是一个纯 Python 实现的中文分词库，不需要额外依赖。

**Q：RAGAS 评估需要 GPT-4 吗？**

A：RAGAS 默认使用 GPT-3.5-turbo 作为 Judge，成本相对较低。你也可以配置使用其他模型（如智谱、通义千问）。

**Q：混合检索的 alpha 参数怎么选？**

A：没有标准答案，取决于你的数据特点。一般建议：
- 如果精确匹配很重要（年份、型号），alpha 设低一点（0.3-0.5）
- 如果语义理解更重要（同义词、模糊描述），alpha 设高一点（0.5-0.7）
- 最好通过网格搜索找到最优值

**Q：重排序和查询重写都需要，还是选一个？**

A：看你的场景。重排序是"通用优化"，对所有查询都有帮助。查询重写主要对模糊查询有效（如"报销"、"请假"）。建议先做重排序，如果发现模糊查询问题严重，再加查询重写。

---

## 评分重点

本次作业的评分重点：

1. **理解原理**：不只是调 API，而是理解为什么需要混合检索、重排序能解决什么问题
2. **实验驱动**：用数据说话，不是"感觉好多了"
3. **评估思维**：学会用 RAGAS 量化效果，知道"好"在哪里、"差"在哪里
4. **工程化**：代码结构清晰，可复用，有错误处理

记住老潘说的："在公司里，我们不会凭感觉说'变好了'——必须有数据和 A/B 对比。"

---

## 提示

如果你遇到困难，可以参考 `starter_code/solution.py`。但记住：
1. 不要直接复制粘贴
2. 理解每一行代码的作用
3. 自己动手修改和调试

真正的学习发生在你调试代码、理解错误、解决问题的过程中。

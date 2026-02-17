# Week 03 作业：搭建 RAG 知识库问答系统

本周你学会了让 LLM "查资料再回答"——从文本切分到向量检索，从 Embedding 到组装 Prompt。现在是时候把这些技能整合起来，搭建一个完整的 RAG 系统了。

**重要提示**：本作业不要求使用任何 AI 工具。你需要亲手实现每一个组件，调试每一次切分和检索——这是建立 RAG 直觉的必经之路。

---

## 作业背景

你所在的公司有一个内部知识库，包含产品手册、技术文档、FAQ、政策规定等几十份文档。老板希望能做一个智能问答系统，员工用自然语言提问，系统自动从知识库里找到答案。

上周你已经用 Prompt Engineering 做了一个初步版本，但它有个致命问题：LLM 只能"凭记忆"回答——它不知道公司最新的政策，也可能会编造不存在的流程。这周你要用 RAG 让它"先查资料再回答"。

---

## 核心任务（必做，75 分）

### Part 1：文本切分实验（25 分）

给定一份示例文档，实现文本切分并比较不同参数的效果。

#### 要求

**1.1 实现切分函数（10 分）**

使用 LangChain 的 `RecursiveCharacterTextSplitter` 实现切分：

```python
# rag/chunker.py
from dataclasses import dataclass
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

@dataclass
class ChunkResult:
    """切分结果"""
    chunks: List[str]
    chunk_count: int
    avg_chunk_size: float
    total_chars: int

def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: List[str] = None
) -> ChunkResult:
    """
    切分文本

    Args:
        text: 原始文本
        chunk_size: 每个片段的目标大小（字符数）
        chunk_overlap: 相邻片段的重叠字符数
        separators: 分隔符列表（按优先级排序）

    Returns:
        切分结果
    """
    if separators is None:
        # 中文友好的分隔符
        separators = ["\n\n", "\n", "。", "！", "？", "；", " ", ""]

    # TODO: 实现 RecursiveCharacterTextSplitter 切分
    # 1. 创建 splitter 实例
    # 2. 执行切分
    # 3. 计算统计信息
    # 4. 返回 ChunkResult
    pass


def analyze_chunks(chunks: List[str]) -> dict:
    """
    分析切分结果

    Returns:
        {
            "chunk_count": 片段数量,
            "avg_size": 平均大小,
            "min_size": 最小片段,
            "max_size": 最大片段,
            "size_distribution": {大小区间: 数量}
        }
    """
    # TODO: 实现分析逻辑
    pass
```

**1.2 参数对比实验（10 分）**

使用提供的示例文档（`data/sample_docs/company_faq.md`），对比以下配置的切分效果：

| 配置 | chunk_size | chunk_overlap | 预期片段数 |
|------|-----------|---------------|-----------|
| A（大片段） | 1000 | 100 | ? |
| B（推荐） | 500 | 50 | ? |
| C（小片段） | 200 | 20 | ? |

**输出表格**：

```markdown
| 配置 | 实际片段数 | 平均大小 | 最小 | 最大 | 问题分析 |
|------|-----------|---------|------|------|---------|
| A | ? | ? | ? | ? | ? |
| B | ? | ? | ? | ? | ? |
| C | ? | ? | ? | ? | ? |
```

**分析要点**：
- 哪种配置可能导致"关键信息被切断"？
- 哪种配置可能导致"噪音过多"？
- 你会选择哪种配置？为什么？

**1.3 边界案例分析（5 分）**

找出一个被"切断"的例子，展示原文和切分后的问题：

```markdown
### 切断案例

**原文片段**：
...员工可以申请远程办公，但需要满足以下条件：
1. 入职满 6 个月
2. 绩效评级为 B 及以上
3. 没有正在进行的绩效改进计划...

**切分后**：
- 片段 47：...员工可以申请远程办公，但需要满足以下条件：
- 片段 48：1. 入职满 6 个月 2. 绩效评级为 B 及以上...

**问题分析**：
用户问"远程办公需要什么条件"，如果检索到片段 47，会丢失关键信息。

**解决方案**：
- 调整 chunk_overlap 为 ?
- 或者使用按段落切分
```

**提交内容**：
- `rag/chunker.py`：切分函数实现
- `experiments/chunk_comparison.py`：对比实验代码
- `report.md`：包含分析表格和边界案例

---

### Part 2：Embedding 与相似度计算（25 分）

理解语义相似度，实现基于 Embedding 的文本比较。

#### 要求

**2.1 实现 Embedding 封装（10 分）**

```python
# rag/embedder.py
from openai import OpenAI
import numpy as np
from typing import List, Union
import hashlib
import json
from pathlib import Path

class Embedder:
    """Embedding 生成器"""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        cache_dir: str = "./data/embeddings"
    ):
        self.client = OpenAI()
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{self.model}:{text}".encode()).hexdigest()

    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        获取文本的 Embedding

        Args:
            text: 输入文本
            use_cache: 是否使用缓存

        Returns:
            Embedding 向量
        """
        # TODO: 实现带缓存的 Embedding 获取
        # 1. 检查缓存
        # 2. 如果缓存不存在，调用 API
        # 3. 保存到缓存
        # 4. 返回向量
        pass

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取 Embedding"""
        # TODO: 实现批量获取（可以并行）
        pass


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算余弦相似度

    Args:
        vec1: 向量 1
        vec2: 向量 2

    Returns:
        相似度 (0-1)
    """
    # TODO: 实现余弦相似度计算
    pass


def find_most_similar(
    query: str,
    candidates: List[str],
    embedder: Embedder,
    top_k: int = 3
) -> List[dict]:
    """
    找出与查询最相似的候选文本

    Returns:
        [{"text": "...", "similarity": 0.85}, ...]
    """
    # TODO: 实现
    pass
```

**2.2 相似度对比实验（10 分）**

计算以下文本对的相似度，并解释结果：

```python
# experiments/similarity_test.py

TEST_PAIRS = [
    # 同义词
    ("远程办公申请流程", "在家上班怎么弄"),
    ("报销费用需要什么材料", "费用报销要哪些单据"),

    # 语义相关但不同
    ("公司的远程办公政策", "公司的健身房开放时间"),
    ("如何申请年假", "年假有多少天"),

    # 完全不相关
    ("产品技术文档", "食堂今日菜单"),
    ("API 接口说明", "员工生日福利"),
]

# 输出格式：
# | 文本 1 | 文本 2 | 相似度 | 解释 |
# |--------|--------|--------|------|
# | 远程办公申请流程 | 在家上班怎么弄 | 0.85 | 同义词，语义高度相似 |
```

**2.3 阈值分析（5 分）**

基于实验结果，确定一个合理的相似度阈值：

```markdown
### 相似度阈值分析

基于以上实验：

- 相似度 > 0.7：语义非常相似，可以认为是同一主题
- 相似度 0.4-0.7：有一定相关性，可能需要进一步判断
- 相似度 < 0.4：基本不相关，不应作为检索结果

**我的选择**：将检索阈值设为 ?，原因是...
```

**提交内容**：
- `rag/embedder.py`：Embedding 类实现
- `experiments/similarity_test.py`：相似度测试代码
- `report.md`：包含相似度对比表和阈值分析

---

### Part 3：ChromaDB 知识库实践（25 分）

使用 ChromaDB 搭建一个可检索的知识库。

#### 要求

**3.1 实现 ChromaDB 封装（15 分）**

```python
# rag/retriever.py
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Document:
    """文档结构"""
    content: str
    source: str
    metadata: dict

@dataclass
class SearchResult:
    """检索结果"""
    content: str
    source: str
    distance: float
    metadata: dict

class ChromaRetriever:
    """ChromaDB 检索器"""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_directory: str = "./data/chromadb"
    ):
        """
        初始化 ChromaDB

        Args:
            collection_name: Collection 名称
            persist_directory: 持久化目录
        """
        # TODO: 初始化 ChromaDB 客户端
        # 提示：使用 PersistentClient
        pass

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> int:
        """
        添加文档到知识库

        Args:
            documents: 文档列表
            ids: 文档 ID（可选，自动生成）

        Returns:
            添加的文档数量
        """
        # TODO: 实现
        pass

    def search(
        self,
        query: str,
        top_k: int = 3,
        where: Optional[dict] = None
    ) -> List[SearchResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回的文档数量
            where: 元数据过滤条件

        Returns:
            检索结果列表
        """
        # TODO: 实现
        pass

    def delete_collection(self):
        """删除 Collection（用于重置）"""
        # TODO: 实现
        pass

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        # TODO: 返回文档数量等信息
        pass
```

**3.2 知识库构建（5 分）**

使用提供的示例文档构建知识库：

```python
# scripts/build_knowledge_base.py

from rag.chunker import chunk_text
from rag.retriever import ChromaRetriever, Document
from pathlib import Path

def build_knowledge_base(
    docs_dir: str = "./data/sample_docs",
    collection_name: str = "company_faq"
) -> ChromaRetriever:
    """
    构建知识库

    Args:
        docs_dir: 文档目录
        collection_name: Collection 名称

    Returns:
        检索器实例
    """
    retriever = ChromaRetriever(collection_name)

    # 清空现有数据
    retriever.delete_collection()
    retriever = ChromaRetriever(collection_name)

    # TODO: 遍历文档目录，切分并添加到知识库
    # 1. 读取所有 .md 文件
    # 2. 切分文本
    # 3. 添加到 ChromaDB

    return retriever

if __name__ == "__main__":
    retriever = build_knowledge_base()
    print(f"知识库统计: {retriever.get_stats()}")
```

**3.3 检索效果测试（5 分）**

设计 5 个测试查询，评估检索效果：

```python
# experiments/retrieval_test.py

TEST_QUERIES = [
    {
        "query": "远程办公怎么申请",
        "expected_source": "remote_work_policy.md",
        "expected_keywords": ["申请", "远程", "审批"]
    },
    {
        "query": "报销流程是什么",
        "expected_source": "reimbursement.md",
        "expected_keywords": ["报销", "流程", "发票"]
    },
    # TODO: 再添加 3 个测试查询
]

def test_retrieval(retriever: ChromaRetriever):
    """测试检索效果"""
    for test in TEST_QUERIES:
        results = retriever.search(test["query"], top_k=3)

        print(f"查询: {test['query']}")
        print(f"期望来源: {test['expected_source']}")
        print(f"实际结果:")

        for i, result in enumerate(results):
            print(f"  {i+1}. {result.source} (距离: {result.distance:.3f})")
            print(f"     内容: {result.content[:100]}...")

        # 检查是否命中
        hit = any(r.source == test["expected_source"] for r in results)
        print(f"命中: {'✓' if hit else '✗'}")
        print()
```

**输出示例**：

```markdown
### 检索效果测试

| 查询 | 期望来源 | 实际来源（Top 1） | 距离 | 是否命中 |
|------|---------|-----------------|------|---------|
| 远程办公怎么申请 | remote_work_policy.md | remote_work_policy.md | 0.25 | ✓ |
| ... | ... | ... | ... | ... |

准确率：?/5 = ?%
```

**提交内容**：
- `rag/retriever.py`：ChromaDB 封装实现
- `scripts/build_knowledge_base.py`：知识库构建脚本
- `experiments/retrieval_test.py`：检索测试代码
- `report.md`：包含检索效果测试结果

---

## 进阶任务（选做，20 分）

### 任务 4：端到端 RAG 管道（15 分）

组装完整的 RAG 流程，处理真实问答任务。

#### 要求

**4.1 实现 RAG Pipeline（10 分）**

```python
# rag/pipeline.py
from dataclasses import dataclass
from typing import List, Optional
from openai import OpenAI
from .retriever import ChromaRetriever

@dataclass
class RAGResponse:
    """RAG 响应"""
    answer: str
    sources: List[dict]
    query: str
    retrieval_time_ms: float
    generation_time_ms: float

class RAGPipeline:
    """RAG 管道"""

    def __init__(
        self,
        collection_name: str = "company_faq",
        persist_directory: str = "./data/chromadb"
    ):
        self.llm_client = OpenAI()
        self.retriever = ChromaRetriever(collection_name, persist_directory)

    def retrieve(self, query: str, top_k: int = 3) -> List[dict]:
        """检索相关文档"""
        # TODO: 调用 retriever.search
        pass

    def build_prompt(self, query: str, documents: List[dict]) -> str:
        """
        构建 RAG Prompt

        提示：使用 Week 02 学的四要素原则
        - 角色：定义 AI 的身份
        - 任务：明确要做什么
        - 约束：只基于参考文档回答
        - 格式：结构化输出
        """
        # TODO: 实现
        pass

    def generate(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """调用 LLM 生成回答"""
        # TODO: 实现
        pass

    def query(self, question: str, top_k: int = 3) -> RAGResponse:
        """
        执行 RAG 查询

        Args:
            question: 用户问题
            top_k: 检索的文档数量

        Returns:
            RAG 响应
        """
        # TODO: 实现完整流程
        # 1. 检索
        # 2. 构建 Prompt
        # 3. 生成
        # 4. 返回结果
        pass
```

**4.2 问答测试（5 分）**

设计 5 个真实问题，测试 RAG 系统的问答效果：

```markdown
### RAG 问答测试

| 问题 | RAG 回答 | 是否基于文档 | 评价 |
|------|---------|------------|------|
| 公司的远程办公政策是什么？ | ... | ✓/✗ | ... |
| ... | ... | ... | ... |

**评价维度**：
1. 是否基于检索到的文档回答（没有编造）
2. 回答是否完整
3. 是否引用了来源
```

---

### 任务 5：成本分析（5 分）

分析 RAG 系统的成本构成。

#### 要求

**5.1 成本计算（3 分）**

```python
# experiments/cost_analysis.py

def estimate_rag_cost(
    doc_count: int,
    avg_doc_chars: int,
    queries_per_day: int,
    avg_query_tokens: int
) -> dict:
    """
    估算 RAG 系统成本

    Returns:
        {
            "one_time_embedding_cost": 一次性 Embedding 成本,
            "daily_query_cost": 每日查询成本,
            "monthly_cost": 月度总成本
        }
    """
    # 价格参考（2025 年）
    EMBEDDING_PRICE = 0.02 / 1_000_000  # $/token
    GPT4O_MINI_PRICE = 0.15 / 1_000_000  # $/token（输入）

    # TODO: 实现成本计算
    pass

# 示例：100 份文档，每份 5000 字，每天 100 次查询
cost = estimate_rag_cost(
    doc_count=100,
    avg_doc_chars=5000,
    queries_per_day=100,
    avg_query_tokens=1500
)
print(cost)
```

**5.2 成本优化建议（2 分）**

```markdown
### 成本优化建议

基于成本分析，提出至少 3 条优化建议：

1. **Embedding 缓存**：...
2. **选择更便宜的模型**：...
3. **减少 top_k**：...
```

---

## AI 协作练习（可选）

Week 03 处于"识别期"，你需要学会审查 AI 生成的 RAG 代码。下面这段代码是某个 AI 工具生成的，请审查它：

### 待审查代码

```python
# AI 生成的 RAG 代码（故意包含问题）
from openai import OpenAI
import chromadb

def create_rag_system():
    """创建 RAG 系统"""
    # 创建 ChromaDB
    client = chromadb.Client()
    collection = client.create_collection("docs")

    # 切分文档
    def split_text(text):
        return [text[i:i+10000] for i in range(0, len(text), 10000)]

    # 添加文档
    def add_doc(text, doc_id):
        chunks = split_text(text)
        collection.add(
            documents=chunks,
            ids=[f"{doc_id}_{i}" for i in range(len(chunks))]
        )

    # 检索
    def search(query):
        results = collection.query(
            query_texts=[query],
            n_results=20  # 多返回一些，更全面
        )
        return results["documents"][0]

    # 生成回答
    def answer(question):
        docs = search(question)
        context = " ".join(docs)  # 把所有文档拼起来

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",  # 用最好的模型
            messages=[{
                "role": "user",
                "content": f"根据以下内容回答：{context}\n\n问题：{question}"
            }]
        )
        return response.choices[0].message.content

    return {"add_doc": add_doc, "answer": answer}
```

### 审查清单

请对照以下清单审查代码：

```markdown
## RAG 代码审查报告

### 1. 切分策略
- [ ] chunk_size 设置是否合理？当前设置为 10000，你觉得合适吗？
- [ ] 有没有设置 overlap？没有的话会有什么问题？
- [ ] 切分是否考虑了语义边界（段落、句子）？

你的分析：...

### 2. Embedding 与检索
- [ ] 检索数量（n_results=20）是否合适？
- [ ] 有没有对检索结果设置相似度阈值？
- [ ] 有没有处理"检索不到结果"的情况？

你的分析：...

### 3. Prompt 设计
- [ ] Prompt 是否包含角色定义？
- [ ] 有没有约束"只基于参考文档回答"？
- [ ] 把 20 个文档全部拼起来会有什么问题？

你的分析：...

### 4. 模型选择
- [ ] 使用 GPT-4 是否有必要？成本如何？
- [ ] 有没有考虑更经济的替代方案？

你的分析：...

### 5. 其他问题
- [ ] 是否有错误处理？
- [ ] 是否有成本控制？
- [ ] 是否有缓存机制？

你的分析：...
```

### 你的修订版

基于审查，写出你的修订版本（只需修改关键部分）：

```python
# 我的修订版
def create_rag_system_fixed():
    """修复后的 RAG 系统"""

    # 1. 改进切分策略
    def split_text_fixed(text):
        # TODO: 你的实现
        pass

    # 2. 改进检索
    def search_fixed(query):
        # TODO: 你的实现
        pass

    # 3. 改进 Prompt
    def build_prompt_fixed(question, docs):
        # TODO: 你的实现
        pass

    # 4. 改进生成
    def answer_fixed(question):
        # TODO: 你的实现
        pass

    return {"add_doc": add_doc_fixed, "answer": answer_fixed}
```

### 修订说明

解释你做的主要修改：

1. **切分策略修改**：原因...
2. **检索数量修改**：原因...
3. **Prompt 修改**：原因...
4. **模型选择修改**：原因...

**重要**：AI 协作练习不影响基础任务的评分，但需要展示你的审查过程和改进思路。

---

## 提交清单

在提交作业前，请确认以下内容：

### 文件结构

```
week03_作业_你的姓名/
├── rag/
│   ├── __init__.py
│   ├── chunker.py         # 文本切分
│   ├── embedder.py        # Embedding 封装
│   ├── retriever.py       # ChromaDB 封装
│   └── pipeline.py        # RAG Pipeline（进阶）
├── experiments/
│   ├── chunk_comparison.py    # 切分对比实验
│   ├── similarity_test.py     # 相似度测试
│   ├── retrieval_test.py      # 检索测试
│   └── cost_analysis.py       # 成本分析（进阶）
├── scripts/
│   └── build_knowledge_base.py  # 知识库构建
├── data/
│   └── sample_docs/       # 示例文档（使用提供的）
├── report.md              # 实验报告
└── README.md              # 简要说明
```

### 质量检查

- [ ] 所有代码都能独立运行
- [ ] API Key 没有硬编码
- [ ] 切分函数有三种参数对比
- [ ] 相似度测试有 6 对文本
- [ ] 检索测试有 5 个查询
- [ ] report.md 包含所有实验结果
- [ ] 有运行输出或截图证明代码能工作

---

## 常见问题

**Q：我没有 OpenAI API Key 怎么办？**

A：可以使用国产 LLM（智谱、通义千问、DeepSeek 等），它们大多也提供 Embedding API。或者使用 ChromaDB 内置的 Embedding 功能（不需要额外调用 API）。

**Q：ChromaDB 数据存在哪里？**

A：默认存在 `./data/chromadb` 目录。记得在 `.gitignore` 中排除这个目录，不要提交到 Git。

**Q：chunk_size 到底选多少合适？**

A：没有标准答案，取决于你的文档类型和查询需求。一般建议 200-500 tokens（约 300-800 中文字符），在这个作业中我们用 500 字符。

**Q：检索准确率多少算"好"？**

A：对于企业 FAQ 类文档，Top-3 召回率 80% 以上是比较合理的预期。如果低于 60%，需要检查切分策略或 Embedding 质量。

**Q：为什么要把 20 个文档都拼起来给 LLM？这有什么问题？**

A：首先，20 个文档可能超出 context window。其次，即使塞得进去，噪音太多也会干扰 LLM——它会"注意力分散"，抓不住重点。一般 3-5 个高质量文档效果更好。

---

## 评分重点

本次作业的评分重点：

1. **理解原理**：不只是"调 API"，而是理解为什么 chunk_size 要这样设置、相似度阈值怎么选
2. **实验驱动**：用数据说话，不是"感觉效果好"
3. **工程化**：代码结构清晰，可复用，有缓存
4. **完整性**：切分、Embedding、检索三个组件都要实现

记住老潘说的："在公司里，我们不会每次都调用 GPT-4，简单任务用 3.5 就够了，成本差十倍。RAG 的成本主要在 LLM 调用，Embedding 是一次性的。"

# Week 03 Starter Code - RAG: 让 LLM "查资料再回答"

本目录包含 Week 03 RAG 章节的参考解决方案代码。

## 文件说明

```
starter_code/
├── solution.py    # 完整的 RAG 系统实现
└── README.md      # 本文件
```

## 环境准备

### 1. 安装依赖

```bash
pip install openai chromadb langchain-text-splitters numpy
```

或使用 requirements.txt（如果项目根目录有）：

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

设置 OpenAI API Key 环境变量：

```bash
# macOS / Linux
export OPENAI_API_KEY="your-api-key-here"

# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Windows CMD
set OPENAI_API_KEY=your-api-key-here
```

或者在代码中直接设置（不推荐在生产环境中使用）：

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

## 代码结构

### solution.py 包含以下模块：

| 模块 | 类/函数 | 功能 |
|------|---------|------|
| 文本切分 | `ChunkConfig`, `chunk_text()`, `chunk_documents()` | 使用 RecursiveCharacterTextSplitter 切分文本 |
| Embedding | `Embedder`, `cosine_similarity()`, `estimate_embedding_cost()` | 生成向量并计算相似度 |
| 向量数据库 | `ChromaRetriever` | ChromaDB 存储和检索 |
| RAG Pipeline | `RAGPipeline`, `RAGResponse` | 端到端 RAG 系统 |

## 运行示例

### 完整演示

```bash
python solution.py
```

预期输出：
```
============================================================
Week 03 RAG 实战 - 参考解决方案
============================================================

【1】文本切分演示
原文长度: 432 字符
切分为 3 个片段
第一个片段: 远程办公政策（2025年修订版）...

【2】Embedding 和相似度演示
'远程办公申请流程' vs '在家上班怎么弄' 相似度: 0.85+
'远程办公申请流程' vs '公司食堂菜单' 相似度: 0.20-

【3】Embedding 成本估算
100 万字知识库的 Embedding 成本: $0.01

【4】ChromaDB 检索演示
已索引 8 个文档片段
查询: '远程办公需要什么条件'
检索到 2 个相关文档...

【5】完整 RAG Pipeline 演示
问题: 每周可以远程办公几天？需要什么条件？
回答: 根据远程办公政策...
```

### 分步运行

#### 1. 文本切分

```python
from solution import chunk_text, ChunkConfig

text = "你的长文档内容..."
config = ChunkConfig(chunk_size=500, chunk_overlap=50)
chunks = chunk_text(text, config)

print(f"切分为 {len(chunks)} 个片段")
for chunk in chunks:
    print(f"片段 {chunk['index']}: {chunk['content'][:50]}...")
```

#### 2. Embedding 和相似度

```python
from solution import Embedder, cosine_similarity

embedder = Embedder()

# 生成 Embedding
vector = embedder.embed("远程办公申请流程")
print(f"向量维度: {len(vector)}")  # 1536

# 计算相似度
vec1 = embedder.embed("远程办公")
vec2 = embedder.embed("在家上班")
similarity = cosine_similarity(vec1, vec2)
print(f"相似度: {similarity:.3f}")  # 应该 > 0.7
```

#### 3. 向量数据库

```python
from solution import ChromaRetriever, ChunkConfig, chunk_documents

# 初始化
retriever = ChromaRetriever(
    collection_name="my_kb",
    persist_directory="./data/chromadb"
)

# 索引文档
docs = [
    {"content": "文档内容...", "source": "doc1.txt"},
    {"content": "文档内容...", "source": "doc2.txt"},
]
chunks = chunk_documents(docs, ChunkConfig(chunk_size=300))
retriever.add_documents(chunks)

# 检索
results = retriever.search("远程办公怎么申请", top_k=3)
for r in results:
    print(f"来源: {r['source']}, 距离: {r['distance']:.3f}")
```

#### 4. 完整 RAG Pipeline

```python
from solution import RAGPipeline

# 初始化
pipeline = RAGPipeline(
    collection_name="company_docs",
    persist_directory="./data/chromadb"
)

# 索引知识库
docs = [
    {"content": "政策文档内容...", "source": "policy.pdf"},
    {"content": "流程文档内容...", "source": "process.docx"},
]
pipeline.index_documents(docs)

# 查询
response = pipeline.query("远程办公需要什么条件？")
print(f"回答: {response.answer}")
print(f"来源: {[s['source'] for s in response.sources]}")
```

## 数据持久化

ChromaDB 数据默认存储在 `./data/chromadb/` 目录：

```
data/
└── chromadb/
    └── chroma.sqlite3    # SQLite 数据库
```

建议在 `.gitignore` 中添加：

```gitignore
# RAG 相关
data/chromadb/
data/embeddings/
*.parquet
```

## 常见问题

### Q: 为什么检索不到相关文档？

可能原因：
1. **Chunk size 太小**：关键信息被切断了。尝试增大 `chunk_size`
2. **知识库内容不够**：检查文档是否包含相关信息
3. **查询方式不对**：尝试换一种问法

```python
# 尝试不同的 chunk size
config = ChunkConfig(chunk_size=500, chunk_overlap=100)  # 增大 overlap
```

### Q: ChromaDB 报错 "Collection already exists"

这是因为之前运行过程序。解决方法：

```python
# 方法 1: 清空 Collection
retriever.clear()

# 方法 2: 使用不同的 collection 名称
retriever = ChromaRetriever(collection_name="new_name")
```

### Q: OpenAI API 调用失败

检查：
1. `OPENAI_API_KEY` 是否正确设置
2. API Key 是否有效（未过期、有余额）
3. 网络是否能访问 OpenAI API

```python
import os
print(f"API Key 设置: {'已设置' if os.getenv('OPENAI_API_KEY') else '未设置'}")
```

### Q: 中文切分效果不好？

默认的 `ChunkConfig` 已经针对中文优化。如果效果仍不理想：

```python
# 自定义分隔符
config = ChunkConfig(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
)
```

## 参数调优建议

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `chunk_size` | 300-800 | 中文字符数，太小丢失上下文，太大噪音多 |
| `chunk_overlap` | chunk_size 的 10-20% | 保证边界信息不丢失 |
| `top_k` | 3-5 | 检索返回的文档数量 |
| `temperature` | 0.3 | RAG 场景建议用较低温度，提高一致性 |

## 成本估算

使用 OpenAI API 的成本（截至 2026 年）：

| 模型 | 用途 | 价格 |
|------|------|------|
| text-embedding-3-small | Embedding | $0.02 / 1M tokens |
| gpt-4o-mini | 生成回答 | $0.15 / 1M input tokens |

**估算**：
- 100 万字知识库的 Embedding 成本：约 $0.01（一次性）
- 每次查询（问题 + 上下文 + 回答约 1000 tokens）：约 $0.0002

## 下一步

学完本章后，建议：
1. 用自己的知识库数据测试 RAG 系统
2. 调整 `chunk_size` 和 `top_k` 参数，观察效果变化
3. 尝试不同的 Prompt 模板

Week 04 将学习：
- 混合检索（向量 + 关键词）
- 重排序（Reranking）
- RAG 评估指标

## 参考资源

- [LangChain Text Splitters 文档](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)

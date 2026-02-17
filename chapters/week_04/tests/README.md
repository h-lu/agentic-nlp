# Week 04 测试套件

本目录包含 Week 04（高级 RAG 与评估）的完整 pytest 测试套件。

## 测试文件概述

| 文件 | 测试内容 | 测试数量 |
|------|---------|---------|
| `conftest.py` | 共享 fixtures 和 mock 类 | - |
| `test_smoke.py` | 测试基础设施验证 | 17 |
| `test_hybrid_search.py` | 混合检索（向量 + BM25） | 40 |
| `test_reranking.py` | 重排序（Cross-Encoder） | 44 |
| `test_query_rewriting.py` | 查询重写 | 32 |
| `test_ragas_evaluation.py` | RAGAS 评估框架 | 37 |
| `test_examples.py` | 示例代码测试 | 14 |

**总计**：161 个测试，7 个跳过（需要 chromadb）

## 测试覆盖的锚点声明

| 锚点 | 说明 | 验证方式 |
|------|------|---------|
| `hybrid-search-recall-boost` | 混合检索比纯向量检索召回率提升 20%+ | `TestHybridSearchRecallBoost` |
| `rerank-precision-boost` | 重排序后 Top-3 精确度提升 30%+ | `TestRerankingPrecision` |
| `ragas-faithfulness-target` | RAGAS 忠实度 > 0.8 | `TestRAGASFaithfulness` |

## 运行测试

```bash
# 运行所有测试
python3 -m pytest chapters/week_04/tests/ -v

# 运行特定测试文件
python3 -m pytest chapters/week_04/tests/test_hybrid_search.py -v

# 运行特定测试类
python3 -m pytest chapters/week_04/tests/test_hybrid_search.py::TestBM25Search -v

# 运行特定测试
python3 -m pytest chapters/week_04/tests/test_hybrid_search.py::TestBM25Search::test_bm25_exact_match -v

# 查看测试覆盖率
python3 -m pytest chapters/week_04/tests/ --cov=chapters/week_04 --cov-report=html
```

## 测试分类

### 1. 混合检索测试 (`test_hybrid_search.py`)

- **BM25 检索**：关键词精确匹配能力
- **向量检索**：语义相似度匹配
- **RRF 融合**：倒数排名融合算法
- **混合检索**：结合两者的优势
- **召回率提升**：验证锚点声明

### 2. 重排序测试 (`test_reranking.py`)

- **Cross-Encoder 评分**：精确相关性计算
- **重排序逻辑**：结果重新排序
- **Top-K 选择**：返回前 K 个结果
- **精确度提升**：验证锚点声明
- **两阶段架构**：Bi-Encoder 召回 + Cross-Encoder 精排

### 3. 查询重写测试 (`test_query_rewriting.py`)

- **单查询改写**：将模糊查询改为清晰查询
- **查询扩展**：生成多个查询变体
- **智能阈值**：判断是否需要改写
- **召回率提升**：验证锚点声明

### 4. RAGAS 评估测试 (`test_ragas_evaluation.py`)

- **Context Precision**：上下文精确度
- **Faithfulness**：忠实度（无幻觉）
- **Answer Relevance**：答案相关性
- **Context Recall**：上下文召回率
- **A/B 测试**：对比不同配置

### 5. 烟雾测试 (`test_smoke.py`)

- **基础设施验证**：确保测试环境正常
- **组件导入**：验证所有类可导入
- **锚点可测性**：验证锚点声明可测试
- **集成测试**：端到端流程测试

## Mock 类说明

由于 Week 04 涉及外部 API（OpenAI、Embedding 服务）和大型模型（Cross-Encoder），测试使用 mock 类：

| Mock 类 | 用途 | 说明 |
|---------|------|------|
| `MockBM25Index` | BM25 检索 | 简化的关键词匹配 |
| `MockVectorCollection` | 向量检索 | 基于 MD5 哈希的伪 embedding |
| `MockCrossEncoder` | Cross-Encoder | 基于关键词重叠的评分 |
| `MockLLMClient` | LLM 调用 | 预定义响应的模拟 |
| `MockRAGASEvaluator` | RAGAS 评估 | 随机生成的评分 |

## Fixtures

主要 fixtures：

- `sample_documents`：示例文档集合
- `vector_collection`：向量数据库集合
- `bm25_index`：BM25 索引
- `hybrid_retriever`：混合检索器
- `reranker`：重排序器
- `query_rewriter`：查询重写器
- `ragas_evaluator`：RAGAS 评估器
- `evaluation_dataset`：评估数据集

## 测试矩阵

### 正例（Happy Path）

- 正常查询检索
- 正常重排序
- 正常查询改写
- 正常 RAGAS 评估

### 边界情况

- 空查询
- 单字符查询
- 超长查询
- 特殊字符
- Unicode 字符
- 空/无结果

### 反例（错误处理）

- 查询无匹配
- LLM 错误处理
- 评分异常

## 注意事项

1. **Mock 限制**：由于使用 mock，某些测试的断言更宽容（例如 mock 的 embedding 不擅长语义相似度）

2. **chromadb 跳过**：部分测试需要 chromadb，未安装时会跳过

3. **随机性**：RAGAS 评估的 mock 使用随机数种子，但可能仍有微小差异

4. **测试独立性**：每个测试独立运行，不依赖其他测试的状态

## 扩展测试

如需添加新测试：

1. 在相应的测试文件中添加测试方法
2. 使用现有的 fixtures 和 mock 类
3. 遵循命名约定：`test_<功能>_<场景>_<预期结果>`
4. 添加适当的文档字符串

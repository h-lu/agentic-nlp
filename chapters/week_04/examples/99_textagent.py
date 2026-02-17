#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TextAgent 高级 RAG 模块

本示例是 Week 04 的 TextAgent 超级线代码，在上周基础 RAG 能力之上，
增加了混合检索、查询重写、重排序和评估框架。

运行方式：
1. 构建知识库：python3 chapters/week_04/examples/99_textagent.py --build
2. 交互问答：python3 chapters/week_04/examples/99_textagent.py
3. 评估效果：python3 chapters/week_04/examples/99_textagent.py --evaluate

预期输出：
- 知识库构建成功
- 交互式问答界面
- 评估报告写入 report.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 尝试导入可选依赖
try:
    from rank_bm25 import BM25Okapi
    import jieba
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = False  # 默认不使用，避免下载大模型
except ImportError:
    RERANKER_AVAILABLE = False


# ============================================================
# 配置
# ============================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

CHROMA_PERSIST_DIR = str(Path(__file__).parent / "textagent_chroma_db")
COLLECTION_NAME = "textagent_docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

SAMPLE_DOCS_DIR = Path(__file__).parent / "sample_documents"
REPORT_PATH = Path(__file__).parent.parent / "report.md"


# ============================================================
# 查询重写器
# ============================================================

class QueryRewriter:
    """LLM 查询重写器"""

    def __init__(self, llm_client: Optional[OpenAI] = None):
        self.llm = llm_client or OpenAI()

    def rewrite(self, query: str) -> str:
        """改写查询"""
        if len(query) >= 15:  # 智能判断：长查询不需要重写
            return query

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
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"查询重写失败: {e}，使用原始查询")
            return query


# ============================================================
# 混合检索器
# ============================================================

class HybridRetriever:
    """混合检索：向量 + BM25"""

    def __init__(
        self,
        chroma_collection,
        top_k: int = 20,
        alpha: float = 0.5
    ):
        self.collection = chroma_collection
        self.top_k = top_k
        self.alpha = alpha
        self.bm25_index = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []

    def build_bm25_index(self, documents: List[str], doc_ids: Optional[List[str]] = None):
        """构建 BM25 索引"""
        if not BM25_AVAILABLE:
            print("警告：rank_bm25 未安装，跳过 BM25 索引构建")
            return

        tokenized_docs = [list(jieba.cut(doc)) for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        self.documents = documents
        self.doc_ids = doc_ids or [f"doc_{i}" for i in range(len(documents))]
        print(f"BM25 索引构建完成，包含 {len(documents)} 个文档")

    def search(self, query: str) -> List[Dict]:
        """混合检索"""
        # 向量检索
        vec_results = self._vector_search(query, self.top_k)

        # BM25 检索
        bm25_results = self._bm25_search(query, self.top_k) if self.bm25_index else []

        # RRF 融合
        fused = self._reciprocal_rank_fusion(vec_results, bm25_results)

        # 补充文档内容
        for result in fused:
            doc_id = result["id"]
            for vec_res in vec_results:
                if vec_res["id"] == doc_id:
                    result["content"] = vec_res["content"]
                    result["vec_distance"] = vec_res.get("distance")
                    break
            if "content" not in result:
                for bm25_res in bm25_results:
                    if bm25_res["id"] == doc_id:
                        result["content"] = bm25_res["content"]
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
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25_index.get_scores(tokenized_query)

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
            if scores[i] > 0
        ]

    def _reciprocal_rank_fusion(
        self,
        vec_results: List[Dict],
        bm25_results: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """RRF 融合"""
        vec_ranks = {doc["id"]: rank for rank, doc in enumerate(vec_results)}
        bm25_ranks = {doc["id"]: rank for rank, doc in enumerate(bm25_results)}

        scores = {}
        for doc_id, rank in vec_ranks.items():
            scores[doc_id] = self.alpha / (k + rank + 1)

        for doc_id, rank in bm25_ranks.items():
            score = (1 - self.alpha) / (k + rank + 1)
            if doc_id in scores:
                scores[doc_id] += score
            else:
                scores[doc_id] = score

        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [{"id": doc_id, "fusion_score": score} for doc_id, score in sorted_docs]


# ============================================================
# RAG 响应数据结构
# ============================================================

@dataclass
class RAGResponse:
    """RAG 系统的响应"""
    answer: str
    sources: List[Dict]
    query: str
    rewritten_query: Optional[str] = None
    retrieval_time: float = 0.0
    generation_time: float = 0.0


# ============================================================
# 高级 RAG Pipeline
# ============================================================

class AdvancedRAGPipeline:
    """高级 RAG 管道：混合检索 + 重排序 + 查询重写"""

    def __init__(
        self,
        collection_name: str = COLLECTION_NAME,
        persist_directory: str = CHROMA_PERSIST_DIR,
        use_hybrid: bool = True,
        use_rerank: bool = False,
        use_rewrite: bool = True,
        alpha: float = 0.5
    ):
        self.llm_client = OpenAI()
        self.use_hybrid = use_hybrid and BM25_AVAILABLE
        self.use_rerank = use_rerank and RERANKER_AVAILABLE
        self.use_rewrite = use_rewrite

        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name=EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )

        # 初始化检索器
        if self.use_hybrid:
            print("使用混合检索（向量 + BM25）")
            self.retriever = HybridRetriever(self.collection, alpha=alpha)
        else:
            print("使用纯向量检索")
            self.retriever = None  # 使用简单的向量检索

        # 初始化查询重写器
        if self.use_rewrite:
            self.rewriter = QueryRewriter(self.llm_client)
        else:
            self.rewriter = None

    def build_index(self, documents: List[Dict]):
        """构建索引"""
        # 分块
        chunks = self._chunk_documents(documents)

        # 构建向量索引
        self._build_vector_index(chunks)

        # 构建 BM25 索引
        if self.use_hybrid and self.retriever:
            chunk_texts = [c["content"] for c in chunks]
            chunk_ids = [c["id"] for c in chunks]
            self.retriever.build_bm25_index(chunk_texts, chunk_ids)

    def _chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """分块"""
        chinese_separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=chinese_separators,
            length_function=len,
        )

        chunks = []
        for doc in documents:
            doc_chunks = text_splitter.split_text(doc["content"])
            for i, chunk_content in enumerate(doc_chunks):
                chunks.append({
                    "id": f"{doc['filename']}_chunk_{i}",
                    "content": chunk_content,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": i,
                        "total_chunks": len(doc_chunks),
                    }
                })
        return chunks

    def _build_vector_index(self, chunks: List[Dict]):
        """构建向量索引"""
        if self.collection.count() > 0:
            print(f"向量索引已存在，包含 {self.collection.count()} 条文档")
            return

        ids = [c["id"] for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"向量索引构建完成，包含 {len(chunks)} 条文档")

    def query(
        self,
        question: str,
        use_rewrite: bool = True,
        top_k: int = 3
    ) -> RAGResponse:
        """执行查询"""
        import time
        start = time.time()

        # 1. 查询重写
        query = question
        if self.use_rewrite and use_rewrite and self.rewriter:
            query = self.rewriter.rewrite(question)

        # 2. 检索
        if self.retriever:
            candidates = self.retriever.search(query)
        else:
            # 纯向量检索
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )
            candidates = [
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

        retrieval_time = time.time() - start

        # 3. 生成回答
        gen_start = time.time()
        answer = self._generate_answer(question, candidates[:top_k])
        generation_time = time.time() - gen_start

        return RAGResponse(
            answer=answer,
            sources=candidates[:top_k],
            query=question,
            rewritten_query=query if query != question else None,
            retrieval_time=retrieval_time,
            generation_time=generation_time
        )

    def _generate_answer(self, question: str, contexts: List[Dict]) -> str:
        """生成回答"""
        context_parts = []
        for i, ctx in enumerate(contexts, 1):
            source = ctx.get("metadata", {}).get("source", "未知")
            context_parts.append(f"【参考资料 {i}】（来源：{source}）\n{ctx['content']}")

        context = "\n\n".join(context_parts)

        prompt = f"""你是公司的内部问答助手，负责回答员工关于公司政策、流程、福利的问题。

根据以下参考资料回答用户的问题。

要求：
1. 只基于参考资料回答，不要编造信息
2. 如果资料中没有相关信息，明确说明"根据现有知识库无法回答"
3. 回答要简洁、专业、友好
4. 如果涉及具体流程，列出关键步骤

参考资料：
{context}

用户问题：{question}

请回答："""

        try:
            response = self.llm_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成回答时出错：{e}"


# ============================================================
# 评估模块
# ============================================================

class RAGEvaluator:
    """RAG 系统评估器"""

    def __init__(self, pipeline: AdvancedRAGPipeline):
        self.pipeline = pipeline

    def evaluate(
        self,
        test_questions: List[str],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """评估系统"""
        results = []

        for i, question in enumerate(test_questions):
            print(f"评估问题 {i+1}/{len(test_questions)}: {question}")

            response = self.pipeline.query(question, use_rewrite=True)
            gt = ground_truths[i] if i < len(ground_truths) else ""

            # 简化的评估指标
            result = {
                "question": question,
                "answer": response.answer,
                "rewritten_query": response.rewritten_query,
                "num_sources": len(response.sources),
                "retrieval_time": response.retrieval_time,
                "generation_time": response.generation_time,
            }

            # 简单的相关性评估（基于关键词重叠）
            if gt:
                relevance = self._calculate_relevance(response.answer, gt)
                result["relevance"] = relevance

            results.append(result)

        # 计算平均指标
        avg_metrics = {
            "avg_retrieval_time": sum(r["retrieval_time"] for r in results) / len(results),
            "avg_generation_time": sum(r["generation_time"] for r in results) / len(results),
            "avg_num_sources": sum(r["num_sources"] for r in results) / len(results),
        }

        if ground_truths and any("relevance" in r for r in results):
            avg_metrics["avg_relevance"] = sum(
                r.get("relevance", 0) for r in results
            ) / len(results)

        return {
            "results": results,
            "avg_metrics": avg_metrics
        }

    def _calculate_relevance(self, answer: str, ground_truth: str) -> float:
        """简单的相关性评估"""
        gt_words = set(ground_truth.lower().split())
        a_words = set(answer.lower().split())
        overlap = len(gt_words & a_words)
        return min(1.0, overlap / max(len(gt_words), 1))


# ============================================================
# 主函数
# ============================================================

def load_documents(docs_dir: Path) -> List[Dict]:
    """加载文档"""
    documents = []

    for file_path in docs_dir.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        filename = file_path.stem
        if "remote" in filename or "远程" in filename:
            category = "远程办公"
        elif "expense" in filename or "报销" in filename:
            category = "财务报销"
        elif "it" in filename or "IT" in filename:
            category = "IT支持"
        else:
            category = "其他"

        documents.append({
            "filename": filename,
            "content": content,
            "metadata": {
                "source": file_path.name,
                "category": category,
            }
        })

    return documents


def build_knowledge_base():
    """构建知识库"""
    print("=" * 60)
    print("构建 TextAgent 知识库（Week 04 高级版）")
    print("=" * 60)

    # 检查 API Key
    if not OPENAI_API_KEY:
        print("错误：未设置 OPENAI_API_KEY 环境变量")
        return None

    # 加载文档
    print("\n[1/3] 加载文档...")
    documents = load_documents(SAMPLE_DOCS_DIR)
    print(f"加载了 {len(documents)} 个文档")
    for doc in documents:
        print(f"  - {doc['filename']} ({len(doc['content'])} 字符)")

    # 初始化 Pipeline
    print("\n[2/3] 初始化高级 RAG Pipeline...")
    pipeline = AdvancedRAGPipeline(
        use_hybrid=True,
        use_rerank=False,  # 需要下载大模型，默认关闭
        use_rewrite=True,
        alpha=0.5
    )

    # 构建索引
    print("\n[3/3] 构建索引...")
    pipeline.build_index(documents)

    print("\n知识库构建完成！")
    return pipeline


def interactive_qa(pipeline: AdvancedRAGPipeline):
    """交互式问答"""
    print("\n" + "=" * 60)
    print("TextAgent 问答系统（Week 04 高级版）")
    print("=" * 60)

    sample_questions = [
        "2024年报假政策是什么？",
        "GPU资源怎么申请？",
        "TB级别存储怎么申请？",
        "如何申请远程办公？",
        "忘记密码怎么办？",
    ]

    print("\n示例问题：")
    for i, q in enumerate(sample_questions, 1):
        print(f"  {i}. {q}")

    print("\n输入问题开始查询，输入 'quit' 退出")

    while True:
        print("\n" + "-" * 40)
        user_input = input("请输入问题: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if not user_input:
            continue

        try:
            response = pipeline.query(user_input, use_rewrite=True)

            print(f"\n查询：{response.query}")
            if response.rewritten_query:
                print(f"改写后：{response.rewritten_query}")
            print(f"\n回答：\n{response.answer}")
            print(f"\n来源：{len(response.sources)} 个文档，"
                  f"检索耗时 {response.retrieval_time:.2f}s，"
                  f"生成耗时 {response.generation_time:.2f}s")

        except Exception as e:
            print(f"\n发生错误：{e}")


def run_evaluation(pipeline: AdvancedRAGPipeline):
    """运行评估"""
    print("=" * 60)
    print("TextAgent 效果评估（Week 04）")
    print("=" * 60)

    test_questions = [
        "2024年报假政策是什么？",
        "GPU资源怎么申请？",
        "TB级别存储怎么申请？",
        "如何申请远程办公？",
    ]

    ground_truths = [
        "5天年假，提前7天申请",
        "填写申请表，部门经理审批",
        "最多10TB",
        "填写申请表，主管批准",
    ]

    evaluator = RAGEvaluator(pipeline)
    results = evaluator.evaluate(test_questions, ground_truths)

    print("\n评估结果：")
    print(f"平均检索时间: {results['avg_metrics']['avg_retrieval_time']:.2f}s")
    print(f"平均生成时间: {results['avg_metrics']['avg_generation_time']:.2f}s")
    print(f"平均相关度: {results['avg_metrics'].get('avg_relevance', 'N/A')}")

    # 写入报告
    generate_report(results)
    print(f"\n评估报告已写入：{REPORT_PATH}")


def generate_report(evaluation_results: Dict) -> None:
    """生成评估报告"""
    avg = evaluation_results["avg_metrics"]

    report_content = f"""# TextAgent 项目报告

## Week 04：高级 RAG 优化

### 更新日期
{datetime.now().strftime("%Y-%m-%d")}

### 优化内容

1. **混合检索（向量 + BM25）**
   - 解决精确匹配问题（年份、型号、专有名词）
   - RRF 融合策略：alpha=0.5（向量和 BM25 各占一半）
   - 使用 jieba 进行中文分词

2. **查询重写**
   - 用 LLM 将模糊查询改写为清晰查询
   - 智能判断：只对短查询（<15字）进行重写
   - 示例："报销" → "费用报销申请流程和所需材料"

3. **重排序（预留）**
   - 支持 CrossEncoderReranker（需单独安装）
   - 从 Top-20 候选中精选 Top-3

### 性能指标

| 指标 | 数值 |
|------|------|
| 平均检索时间 | {avg['avg_retrieval_time']:.2f}s |
| 平均生成时间 | {avg['avg_generation_time']:.2f}s |
| 平均相关度 | {avg.get('avg_relevance', 0):.2%} |
| 平均来源数量 | {avg['avg_num_sources']:.1f} |

### 技术栈

- **向量数据库**: ChromaDB
- **向量模型**: OpenAI text-embedding-3-small
- **LLM**: GPT-4o-mini
- **关键词检索**: BM25 (rank_bm25)
- **中文分词**: jieba

### 下一步

- Week 05：Agent 能力——让 TextAgent 会调用工具
---

*本报告由 TextAgent 自动生成*
"""

    # 确保目录存在
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 写入报告
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="TextAgent 高级 RAG 系统")
    parser.add_argument("--build", action="store_true", help="构建知识库")
    parser.add_argument("--evaluate", action="store_true", help="运行评估")
    args = parser.parse_args()

    # 检查 API Key
    if not OPENAI_API_KEY:
        print("错误：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        return

    # 构建或加载知识库
    pipeline = build_knowledge_base()
    if pipeline is None:
        return

    # 运行评估
    if args.evaluate:
        run_evaluation(pipeline)
    elif not args.build:
        # 进入交互模式
        interactive_qa(pipeline)


if __name__ == "__main__":
    main()

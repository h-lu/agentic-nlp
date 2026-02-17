#!/usr/bin/env python3
"""
Week 03 Assignment Solution - RAG: 让 LLM "查资料再回答"

这是作业的参考解决方案，包含：
1. 文本切分（Chunking）- 使用 RecursiveCharacterTextSplitter
2. Embedding 生成 - 使用 OpenAI text-embedding-3-small
3. 向量数据库 - 使用 ChromaDB 存储和检索
4. 完整的 RAG Pipeline - 端到端问答系统

学生应参考此解决方案的结构，但不应直接复制。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import json
import os

import chromadb
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI


# ============================================================================
# Part 1: 文本切分（Chunking）
# ============================================================================

@dataclass
class ChunkConfig:
    """
    切分配置

    参数说明：
    - chunk_size: 每个片段的最大字符数（推荐 200-500 tokens，约 300-800 中文字符）
    - chunk_overlap: 相邻片段的重叠字符数（推荐 chunk_size 的 10-20%）
    - separators: 分隔符列表，按优先级排序
    """
    chunk_size: int = 500
    chunk_overlap: int = 50
    # 针对中文优化的分隔符列表
    separators: list[str] = field(default_factory=lambda: [
        "\n\n",    # 段落分隔（最高优先级）
        "\n",      # 行分隔
        "。",      # 中文句号
        "！",      # 中文感叹号
        "？",      # 中文问号
        "；",      # 中文分号
        "\u3002",  # Ideographic full stop (中文句号 Unicode)
        "\uff0e",  # Fullwidth full stop (全角句号)
        "\uff0c",  # Fullwidth comma (全角逗号)
        "\u3001",  # Ideographic comma (中文顿号)
        " ",      # 空格
        "",       # 字符级别（最后手段）
    ])


def chunk_text(text: str, config: Optional[ChunkConfig] = None) -> list[dict[str, Any]]:
    """
    使用 RecursiveCharacterTextSplitter 切分文本

    Args:
        text: 原始文本
        config: 切分配置，如果为 None 则使用默认配置

    Returns:
        切分后的片段列表，每个片段包含 content 和 index

    示例:
        >>> chunks = chunk_text("长文档内容...", ChunkConfig(chunk_size=500))
        >>> print(f"共切分为 {len(chunks)} 个片段")
    """
    if config is None:
        config = ChunkConfig()

    # 创建切分器
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=config.separators,
        length_function=len,
        is_separator_regex=False,
    )

    # 执行切分
    raw_chunks = splitter.split_text(text)

    # 包装为结构化结果
    return [
        {"content": chunk, "index": i}
        for i, chunk in enumerate(raw_chunks)
    ]


def chunk_documents(docs: list[dict[str, str]], config: Optional[ChunkConfig] = None) -> list[dict[str, Any]]:
    """
    批量切分多个文档

    Args:
        docs: 文档列表，每个文档包含 'content' 和 'source' 字段
        config: 切分配置

    Returns:
        所有文档的切分结果列表，包含 source 元数据
    """
    if config is None:
        config = ChunkConfig()

    all_chunks = []

    for doc in docs:
        chunks = chunk_text(doc["content"], config)
        for chunk in chunks:
            chunk["source"] = doc.get("source", "unknown")
            chunk["doc_id"] = f"{doc.get('source', 'doc')}_{chunk['index']}"
        all_chunks.extend(chunks)

    return all_chunks


# ============================================================================
# Part 2: Embedding 生成
# ============================================================================

class Embedder:
    """
    Embedding 生成器

    使用 OpenAI text-embedding-3-small 模型将文本转换为向量。

    注意：
    - API 调用按 Token 计费：$0.02 / 1M tokens
    - 输出向量维度：1536
    - 建议对 Embedding 结果进行缓存，避免重复调用
    """

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        初始化 Embedder

        Args:
            model: Embedding 模型名称，默认使用 text-embedding-3-small
        """
        self.client = OpenAI()
        self.model = model

    def embed(self, text: str) -> list[float]:
        """
        生成单个文本的 Embedding

        Args:
            text: 输入文本

        Returns:
            1536 维向量

        示例:
            >>> embedder = Embedder()
            >>> vector = embedder.embed("远程办公申请流程")
            >>> print(f"向量维度: {len(vector)}")
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """
        批量生成 Embedding

        Args:
            texts: 文本列表
            batch_size: 每批处理的文本数量（OpenAI API 限制）

        Returns:
            向量列表
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的余弦相似度

    Args:
        vec1: 向量1
        vec2: 向量2

    Returns:
        相似度值（-1 到 1），值越大表示越相似

    经验值：
    - > 0.7: 语义非常相似
    - 0.4 - 0.7: 有一定相关性
    - < 0.4: 基本不相关
    """
    vec1_arr = np.array(vec1)
    vec2_arr = np.array(vec2)

    dot_product = np.dot(vec1_arr, vec2_arr)
    norm1 = np.linalg.norm(vec1_arr)
    norm2 = np.linalg.norm(vec2_arr)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def estimate_embedding_cost(total_chars: int, chars_per_token: float = 2.0) -> float:
    """
    估算 Embedding 成本

    Args:
        total_chars: 总字符数
        chars_per_token: 每个 Token 约等于多少字符（中文约 2，英文约 4）

    Returns:
        预估成本（美元）

    示例:
        >>> cost = estimate_embedding_cost(1_000_000)  # 100 万字
        >>> print(f"预估成本: ${cost:.2f}")
    """
    total_tokens = total_chars / chars_per_token
    cost_per_million = 0.02  # text-embedding-3-small 的价格
    return (total_tokens / 1_000_000) * cost_per_million


# ============================================================================
# Part 3: 向量数据库（ChromaDB）
# ============================================================================

class ChromaRetriever:
    """
    ChromaDB 向量检索器

    功能：
    - 创建和管理 Collection
    - 添加文档和 Embedding
    - 基于语义相似度检索

    优势：
    - 轻量级：无需部署独立服务
    - 自动 Embedding：默认使用 Sentence Transformers
    - 持久化存储：数据保存在本地
    """

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_directory: str = "./data/chromadb",
    ):
        """
        初始化检索器

        Args:
            collection_name: Collection 名称
            persist_directory: 数据持久化目录
        """
        # 确保目录存在
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # 创建持久化客户端
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 创建或获取 Collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )

        self.collection_name = collection_name

    def add_documents(
        self,
        chunks: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """
        添加文档片段到向量数据库

        Args:
            chunks: 文档片段列表，每个片段需包含 'content' 和 'id' 字段
            batch_size: 批量添加的大小

        Returns:
            添加的文档数量
        """
        if not chunks:
            return 0

        # 准备数据
        documents = [c["content"] for c in chunks]
        ids = [c.get("id", f"chunk_{i}") for i, c in enumerate(chunks)]
        metadatas = [
            {
                "source": c.get("source", "unknown"),
                "index": c.get("index", i),
            }
            for i, c in enumerate(chunks)
        ]

        # 批量添加（ChromaDB 会自动生成 Embedding）
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]

            self.collection.add(
                documents=batch_docs,
                ids=batch_ids,
                metadatas=batch_metas,
            )

        return len(documents)

    def search(
        self,
        query: str,
        top_k: int = 3,
        where_filter: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回的文档数量
            where_filter: 元数据过滤条件（可选）

        Returns:
            检索结果列表，每个结果包含 content、source、distance 字段

        示例:
            >>> retriever = ChromaRetriever()
            >>> results = retriever.search("远程办公怎么申请", top_k=3)
            >>> for r in results:
            ...     print(f"来源: {r['source']}, 相似度: {1 - r['distance']:.3f}")
        """
        query_params = {
            "query_texts": [query],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }

        if where_filter:
            query_params["where"] = where_filter

        results = self.collection.query(**query_params)

        # 格式化结果
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    "content": doc,
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "distance": results["distances"][0][i],
                })

        return formatted_results

    def count(self) -> int:
        """返回 Collection 中的文档数量"""
        return self.collection.count()

    def clear(self) -> None:
        """清空 Collection（删除并重建）"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )


# ============================================================================
# Part 4: RAG Pipeline
# ============================================================================

@dataclass
class RAGResponse:
    """RAG 系统的响应"""
    answer: str                    # LLM 生成的答案
    sources: list[dict[str, Any]]  # 来源文档列表
    query: str                     # 原始问题


class RAGPipeline:
    """
    完整的 RAG 管道

    流程：
    1. 用户提问
    2. 问题转 Embedding
    3. 向量检索获取相关文档
    4. 组装 Prompt（问题 + 检索结果）
    5. LLM 生成回答
    6. 返回答案和来源

    使用示例：
        >>> pipeline = RAGPipeline()
        >>> response = pipeline.query("远程办公需要什么条件？")
        >>> print(response.answer)
    """

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_directory: str = "./data/chromadb",
        llm_model: str = "gpt-4o-mini",
    ):
        """
        初始化 RAG 管道

        Args:
            collection_name: ChromaDB Collection 名称
            persist_directory: ChromaDB 持久化目录
            llm_model: LLM 模型名称
        """
        self.llm_client = OpenAI()
        self.llm_model = llm_model

        self.retriever = ChromaRetriever(
            collection_name=collection_name,
            persist_directory=persist_directory,
        )

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """
        检索相关文档

        Args:
            query: 用户问题
            top_k: 返回的文档数量

        Returns:
            检索到的文档列表
        """
        return self.retriever.search(query, top_k=top_k)

    def build_rag_prompt(self, query: str, documents: list[dict[str, Any]]) -> str:
        """
        构建 RAG Prompt

        使用 Week 02 的 Prompt 设计原则：
        - 角色：定义 AI 的身份
        - 任务：明确要做什么
        - 约束：限制回答范围
        - 格式：结构化输出

        Args:
            query: 用户问题
            documents: 检索到的文档列表

        Returns:
            完整的 Prompt 字符串
        """
        # 组装上下文
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"【参考文档 {i}】\n"
                f"来源：{doc['source']}\n"
                f"内容：{doc['content']}"
            )
        context = "\n\n".join(context_parts)

        prompt = f"""角色：你是公司的内部问答助手，负责回答员工关于公司政策、流程、福利的问题。

任务：根据以下参考文档回答用户的问题。如果参考文档中没有相关信息，请明确说明"根据现有知识库无法回答"。

约束：
- 只基于参考文档回答，不要编造信息
- 如果参考文档之间有矛盾，指出并说明
- 回答要简洁，不要大段复制原文
- 如果问题涉及具体数值（如天数、金额），请准确引用

参考文档：
{context}

用户问题：{query}

请回答："""

        return prompt

    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        """
        调用 LLM 生成回答

        Args:
            prompt: 完整的 Prompt
            temperature: 生成温度（越低越确定）

        Returns:
            LLM 生成的回答
        """
        response = self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def query(
        self,
        question: str,
        top_k: int = 3,
        temperature: float = 0.3,
    ) -> RAGResponse:
        """
        执行 RAG 查询

        Args:
            question: 用户问题
            top_k: 检索的文档数量
            temperature: LLM 生成温度

        Returns:
            RAG 响应（答案 + 来源）
        """
        # 1. 检索相关文档
        documents = self.retrieve(question, top_k)

        # 2. 构建 Prompt
        prompt = self.build_rag_prompt(question, documents)

        # 3. 生成回答
        answer = self.generate(prompt, temperature)

        return RAGResponse(
            answer=answer,
            sources=documents,
            query=question,
        )

    def index_documents(self, docs: list[dict[str, str]], config: Optional[ChunkConfig] = None) -> int:
        """
        索引文档到向量数据库

        Args:
            docs: 文档列表，每个文档包含 'content' 和 'source' 字段
            config: 切分配置

        Returns:
            索引的文档片段数量
        """
        # 切分文档
        chunks = chunk_documents(docs, config)

        # 添加到向量数据库
        return self.retriever.add_documents(chunks)


# ============================================================================
# Part 5: 示例知识库数据
# ============================================================================

SAMPLE_KNOWLEDGE_BASE = [
    {
        "source": "远程办公政策_v2.0.pdf",
        "content": """远程办公政策（2025年修订版）

一、申请条件
员工申请远程办公需满足以下条件：
1. 入职满 6 个月
2. 近一年绩效评级为 B 及以上
3. 所在岗位支持远程办公（需部门主管确认）

二、申请流程
1. 在 OA 系统提交远程办公申请
2. 直属经理审批（3 个工作日内）
3. VP 级别终审（重要岗位需此步骤）
4. HR 备案

三、审批标准
- 每周最多远程办公 1 天
- 需提前 3 个工作日申请
- 连续远程办公不超过 2 周
""",
    },
    {
        "source": "报销流程.docx",
        "content": """费用报销管理办法

一、报销时限
费用发生后 30 天内提交报销申请，超期不予报销。

二、报销类别
1. 差旅费：交通、住宿、餐饮
2. 办公用品：单笔 500 元以下
3. 培训费：需提前审批

三、审批流程
- 500 元以下：直属经理审批
- 500-5000 元：部门总监审批
- 5000 元以上：VP 审批

四、发票要求
- 必须是增值税发票
- 抬头：XX科技有限公司
- 税号：91110000XXXXXXXXXX
""",
    },
    {
        "source": "员工福利手册.pdf",
        "content": """员工福利手册

一、健康福利
1. 年度体检：每年 4 月安排
2. 补充医疗保险：公司全额缴纳
3. 心理咨询：EAP 服务，24 小时热线

二、休假福利
1. 年假：入职满 1 年 5 天，满 3 年 10 天
2. 病假：带薪病假 12 天/年
3. 婚假：3 天（晚婚 10 天）

三、其他福利
1. 生日福利：500 元购物卡
2. 节日福利：春节、中秋各 1000 元
3. 团建：每季度 500 元/人
""",
    },
]


# ============================================================================
# Main: 演示用法
# ============================================================================

def main():
    """演示 RAG 系统用法"""
    print("=" * 60)
    print("Week 03 RAG 实战 - 参考解决方案")
    print("=" * 60)

    # 1. 文本切分演示
    print("\n【1】文本切分演示")
    sample_text = SAMPLE_KNOWLEDGE_BASE[0]["content"]
    config = ChunkConfig(chunk_size=200, chunk_overlap=30)
    chunks = chunk_text(sample_text, config)
    print(f"原文长度: {len(sample_text)} 字符")
    print(f"切分为 {len(chunks)} 个片段")
    print(f"第一个片段: {chunks[0]['content'][:80]}...")

    # 2. Embedding 和相似度演示
    print("\n【2】Embedding 和相似度演示")
    try:
        embedder = Embedder()
        text1 = "远程办公申请流程"
        text2 = "在家上班怎么弄"
        text3 = "公司食堂菜单"

        # 注意：这里需要 OpenAI API Key
        emb1 = embedder.embed(text1)
        emb2 = embedder.embed(text2)
        emb3 = embedder.embed(text3)

        print(f"'{text1}' vs '{text2}' 相似度: {cosine_similarity(emb1, emb2):.3f}")
        print(f"'{text1}' vs '{text3}' 相似度: {cosine_similarity(emb1, emb3):.3f}")
    except Exception as e:
        print(f"Embedding 演示跳过（需要有效的 OpenAI API Key）: {e}")

    # 3. 成本估算
    print("\n【3】Embedding 成本估算")
    cost = estimate_embedding_cost(1_000_000)  # 100 万字
    print(f"100 万字知识库的 Embedding 成本: ${cost:.2f}")

    # 4. ChromaDB 演示
    print("\n【4】ChromaDB 检索演示")
    retriever = ChromaRetriever(
        collection_name="demo_kb",
        persist_directory="./data/chromadb_demo",
    )

    # 清空旧数据
    retriever.clear()

    # 准备文档片段
    all_chunks = chunk_documents(SAMPLE_KNOWLEDGE_BASE, ChunkConfig(chunk_size=300))

    # 添加到向量数据库
    count = retriever.add_documents(all_chunks)
    print(f"已索引 {count} 个文档片段")

    # 检索测试
    query = "远程办公需要什么条件"
    results = retriever.search(query, top_k=2)
    print(f"\n查询: '{query}'")
    print(f"检索到 {len(results)} 个相关文档:")
    for i, r in enumerate(results, 1):
        print(f"\n  结果 {i}:")
        print(f"    来源: {r['source']}")
        print(f"    距离: {r['distance']:.3f}")
        print(f"    内容: {r['content'][:80]}...")

    # 5. 完整 RAG Pipeline 演示
    print("\n【5】完整 RAG Pipeline 演示")
    try:
        pipeline = RAGPipeline(
            collection_name="demo_rag",
            persist_directory="./data/chromadb_demo",
        )

        # 清空并重新索引
        pipeline.retriever.clear()
        pipeline.index_documents(SAMPLE_KNOWLEDGE_BASE, ChunkConfig(chunk_size=300))

        # 执行查询
        question = "每周可以远程办公几天？需要什么条件？"
        print(f"问题: {question}")

        response = pipeline.query(question, top_k=3)
        print(f"\n回答:\n{response.answer}")

        print(f"\n来源文档:")
        for src in response.sources:
            print(f"  - {src['source']} (距离: {src['distance']:.3f})")

    except Exception as e:
        print(f"RAG Pipeline 演示跳过（需要有效的 OpenAI API Key）: {e}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

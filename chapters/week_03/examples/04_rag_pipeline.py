#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整 RAG 管道演示

本示例演示一个端到端的 RAG（检索增强生成）系统：
文档加载 → 文本分块 → 向量嵌入 → 存储 → 检索 → 生成回答

运行案例：企业内部 FAQ 知识库问答系统
"""

import os
from pathlib import Path
from typing import Optional

from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# 配置
# ============================================================

# OpenAI 配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# ChromaDB 配置
CHROMA_PERSIST_DIR = "./faq_chroma_db"
COLLECTION_NAME = "company_faq"

# 分块配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# 示例文档路径
SAMPLE_DOCS_DIR = Path(__file__).parent / "sample_documents"

# 初始化客户端
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# 嵌入函数
embedding_function = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name=EMBEDDING_MODEL
)


# ============================================================
# 第一步：文档加载
# ============================================================

def load_documents(docs_dir: Path) -> list[dict]:
    """
    从目录加载所有文本文档。

    返回：
        [{"filename": ..., "content": ..., "metadata": ...}, ...]
    """
    documents = []

    for file_path in docs_dir.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 根据文件名推断文档类型
        filename = file_path.stem
        if "remote" in filename or "远程" in filename:
            category = "远程办公"
        elif "expense" in filename or "报销" in filename:
            category = "财务报销"
        elif "it" in filename or "IT" in filename:
            category = "IT 支持"
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


# ============================================================
# 第二步：文本分块
# ============================================================

def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    将文档分块，保留元数据。

    使用中文优化的分隔符，确保语义完整性。
    """
    # 中文优化的分隔符
    chinese_separators = [
        "\n\n",  # 段落
        "\n",    # 行
        "。",    # 句号
        "！",   # 感叹号
        "？",   # 问号
        "；",   # 分号
        "，",   # 逗号
        " ",
        "",
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=chinese_separators,
        length_function=len,
    )

    chunks = []

    for doc in documents:
        # 分块
        doc_chunks = text_splitter.split_text(doc["content"])

        for i, chunk_content in enumerate(doc_chunks):
            # 创建分块对象，继承文档元数据
            chunk = {
                "content": chunk_content,
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": i,
                    "total_chunks": len(doc_chunks),
                }
            }
            chunks.append(chunk)

    return chunks


# ============================================================
# 第三步：向量嵌入与存储
# ============================================================

def create_vector_store(chunks: list[dict]) -> chromadb.Collection:
    """
    创建向量数据库并存储文档块。

    如果集合已存在，则复用。
    """
    # 创建持久化客户端
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # 获取或创建集合
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )

    # 如果集合已有数据，直接返回
    if collection.count() > 0:
        print(f"集合已存在，包含 {collection.count()} 条文档块")
        return collection

    # 准备数据
    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(f"chunk_{i}")
        documents.append(chunk["content"])
        metadatas.append(chunk["metadata"])

    # 批量添加
    print(f"正在添加 {len(chunks)} 个文档块到向量数据库...")
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"成功添加 {collection.count()} 个文档块")

    return collection


# ============================================================
# 第四步：检索相关文档
# ============================================================

def retrieve_relevant_chunks(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 5,
    filter_metadata: Optional[dict] = None
) -> list[dict]:
    """
    检索与查询最相关的文档块。

    参数：
        collection: ChromaDB 集合
        query: 用户查询
        n_results: 返回结果数量
        filter_metadata: 元数据过滤条件

    返回：
        [{"content": ..., "metadata": ..., "distance": ...}, ...]
    """
    query_params = {
        "query_texts": [query],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"]
    }

    if filter_metadata:
        query_params["where"] = filter_metadata

    results = collection.query(**query_params)

    # 整理结果
    retrieved = []
    for content, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "content": content,
            "metadata": metadata,
            "distance": distance,
        })

    return retrieved


# ============================================================
# 第五步：生成回答
# ============================================================

def generate_answer(query: str, retrieved_chunks: list[dict]) -> str:
    """
    使用检索到的上下文生成回答。
    """
    # 构建上下文字符串
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        source = chunk["metadata"].get("source", "未知来源")
        context_parts.append(f"【参考资料 {i}】（来源：{source}）\n{chunk['content']}")

    context = "\n\n".join(context_parts)

    # 构建 Prompt
    system_prompt = """你是一个专业的企业内部问答助手。你的任务是根据提供的参考资料回答员工的问题。

要求：
1. 只基于参考资料回答，不要编造信息
2. 如果资料中没有相关信息，明确告知用户
3. 回答要简洁、专业、友好
4. 如果涉及具体流程，列出关键步骤
5. 引用来源（如"根据《远程办公政策》..."）
"""

    user_prompt = f"""参考资料：
{context}

---
员工问题：{query}

请根据参考资料回答员工的问题："""

    # 调用 OpenAI Chat API
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,  # 较低的温度，确保回答稳定
        max_tokens=1000,
    )

    return response.choices[0].message.content


# ============================================================
# 完整 RAG 管道
# ============================================================

def rag_query(
    query: str,
    collection: chromadb.Collection,
    n_results: int = 5,
    show_context: bool = False
) -> str:
    """
    执行完整的 RAG 查询流程。

    步骤：
    1. 检索相关文档
    2. 构建上下文
    3. 生成回答
    """
    print(f"\n{'='*60}")
    print(f"查询：{query}")
    print("=" * 60)

    # 检索
    print("\n[1/2] 正在检索相关文档...")
    retrieved = retrieve_relevant_chunks(collection, query, n_results)

    print(f"检索到 {len(retrieved)} 个相关文档块：")
    for i, chunk in enumerate(retrieved, 1):
        distance = chunk["distance"]
        source = chunk["metadata"].get("source", "未知")
        print(f"  {i}. 距离={distance:.4f} | 来源={source}")

    if show_context:
        print("\n检索到的上下文：")
        for i, chunk in enumerate(retrieved, 1):
            print(f"\n--- 文档块 {i} ---")
            print(chunk["content"][:200] + "...")

    # 生成
    print("\n[2/2] 正在生成回答...")
    answer = generate_answer(query, retrieved)

    return answer


# ============================================================
# 交互式问答
# ============================================================

def interactive_qa(collection: chromadb.Collection):
    """交互式问答界面"""
    print("\n" + "=" * 60)
    print("    企业 FAQ 知识库问答系统")
    print("    输入问题开始查询，输入 'quit' 退出")
    print("=" * 60)

    # 预设问题
    sample_questions = [
        "如何申请远程办公？",
        "出差报销的标准是什么？",
        "忘记密码怎么办？",
        "VPN 连接不上怎么处理？",
        "新员工入职流程是什么？",
    ]

    print("\n示例问题：")
    for i, q in enumerate(sample_questions, 1):
        print(f"  {i}. {q}")

    while True:
        print("\n" + "-" * 40)
        user_input = input("请输入问题（或输入 quit 退出）: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if not user_input:
            continue

        # 检查是否是数字（选择示例问题）
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(sample_questions):
                user_input = sample_questions[idx]
                print(f"已选择：{user_input}")
            else:
                print("无效的选择，请重新输入")
                continue

        try:
            answer = rag_query(user_input, collection, n_results=3)
            print(f"\n回答：\n{answer}")
        except Exception as e:
            print(f"\n发生错误：{e}")


# ============================================================
# 主函数：构建与运行
# ============================================================

def build_knowledge_base():
    """构建知识库（完整管道）"""
    print("=" * 60)
    print("    构建 RAG 知识库")
    print("=" * 60)

    # Step 1: 加载文档
    print("\n[Step 1/4] 加载文档...")
    documents = load_documents(SAMPLE_DOCS_DIR)
    print(f"加载了 {len(documents)} 个文档")
    for doc in documents:
        print(f"  - {doc['filename']} ({len(doc['content'])} 字符)")

    # Step 2: 分块
    print("\n[Step 2/4] 文档分块...")
    chunks = chunk_documents(documents)
    print(f"生成 {len(chunks)} 个文档块")
    print(f"平均块长度：{sum(len(c['content']) for c in chunks) / len(chunks):.1f} 字符")

    # Step 3: 创建向量存储
    print("\n[Step 3/4] 创建向量存储...")
    collection = create_vector_store(chunks)

    # Step 4: 验证
    print("\n[Step 4/4] 验证...")
    test_query = "如何申请远程办公"
    results = retrieve_relevant_chunks(collection, test_query, n_results=2)
    print(f"测试查询 '{test_query}' 检索到 {len(results)} 个结果")

    return collection


def demo_queries(collection: chromadb.Collection):
    """演示几个典型查询"""
    print("\n" + "=" * 60)
    print("    演示查询")
    print("=" * 60)

    demo_questions = [
        ("如何申请远程办公？需要满足什么条件？", None),
        ("出差住宿报销标准是多少？", {"category": "财务报销"}),  # 带过滤
        ("VPN 连接失败怎么办？", None),
    ]

    for query, metadata_filter in demo_questions:
        print(f"\n查询：{query}")
        if metadata_filter:
            print(f"过滤条件：{metadata_filter}")

        retrieved = retrieve_relevant_chunks(
            collection,
            query,
            n_results=3,
            filter_metadata=metadata_filter
        )

        print(f"\n检索到 {len(retrieved)} 个相关文档：")
        for i, chunk in enumerate(retrieved, 1):
            print(f"\n  【{i}】距离={chunk['distance']:.4f}")
            print(f"      来源：{chunk['metadata'].get('source')}")
            print(f"      内容：{chunk['content'][:100]}...")

        answer = generate_answer(query, retrieved)
        print(f"\n回答：{answer}")
        print("-" * 60)


def main():
    """主入口"""
    print("\n" + "=" * 60)
    print("    完整 RAG 管道演示")
    print("    企业内部 FAQ 知识库问答系统")
    print("=" * 60)

    # 检查环境
    if not OPENAI_API_KEY:
        print("错误：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        return

    # 构建知识库
    collection = build_knowledge_base()

    # 运行演示查询
    demo_queries(collection)

    # 进入交互模式
    print("\n" + "=" * 60)
    interactive = input("是否进入交互问答模式？(y/n): ").strip().lower()
    if interactive == "y":
        interactive_qa(collection)

    print("\n演示完成！")
    print(f"向量数据库保存在：{CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    main()

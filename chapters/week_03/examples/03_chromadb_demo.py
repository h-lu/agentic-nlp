#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 向量数据库演示

本示例演示如何使用 ChromaDB 存储和检索向量嵌入，
构建一个简单的文档检索系统。

核心概念：
- Collection：文档集合，类似数据库的表
- Document：存储的文本内容
- Embedding：文档的向量表示
- Metadata：文档的元信息（可用于过滤）
- Distance：相似度度量方式（L2/余弦/内积）
"""

import os
import chromadb
from chromadb.utils import embedding_functions

# 数据持久化路径
CHROMA_PERSIST_DIR = "./chroma_db"

# 初始化 OpenAI 嵌入函数
# 注意：需要设置 OPENAI_API_KEY 环境变量
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)


# ============================================================
# 场景 1：ChromaDB 基础操作
# ============================================================

def basic_chromadb_demo():
    """演示 ChromaDB 的基础 CRUD 操作"""
    print("=" * 60)
    print("场景 1：ChromaDB 基础操作")
    print("=" * 60)

    # 创建内存客户端（数据不持久化）
    client = chromadb.Client()

    # 创建集合（类似数据库表）
    print("\n创建集合 'company_docs'...")
    collection = client.create_collection(
        name="company_docs",
        embedding_function=openai_ef,  # 使用 OpenAI 嵌入
        metadata={"hnsw:space": "cosine"}  # 使用余弦距离
    )

    # 添加文档
    print("添加文档...")
    collection.add(
        ids=["doc1", "doc2", "doc3"],
        documents=[
            "公司实行弹性工作制，核心工作时间为 10:00-16:00。",
            "年假天数根据工龄计算：1-5 年 5 天，5-10 年 10 天，10 年以上 15 天。",
            "加班需要提前申请，加班费按 1.5 倍工资计算。",
        ],
        metadatas=[
            {"category": "考勤制度", "department": "HR"},
            {"category": "假期制度", "department": "HR"},
            {"category": "薪酬制度", "department": "财务"},
        ]
    )

    print(f"集合中的文档数量：{collection.count()}")

    # 查询文档
    print("\n查询：'工作时间和假期'...")
    results = collection.query(
        query_texts=["工作时间和假期"],
        n_results=2
    )

    print("\n查询结果：")
    for i, (doc, metadata, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ), 1):
        print(f"\n结果 {i}（距离：{distance:.4f}）：")
        print(f"  内容：{doc}")
        print(f"  元数据：{metadata}")

    # 获取单个文档
    print("\n获取单个文档（id='doc1'）...")
    doc = collection.get(ids=["doc1"])
    print(f"  内容：{doc['documents'][0]}")
    print(f"  元数据：{doc['metadatas'][0]}")

    # 更新文档
    print("\n更新文档...")
    collection.update(
        ids=["doc1"],
        documents=["公司实行弹性工作制，核心工作时间为 10:00-16:00。员工可以自由安排上下班时间。"],
        metadatas=[{"category": "考勤制度", "department": "HR", "updated": "true"}]
    )

    # 删除文档
    print("删除文档（id='doc3'）...")
    collection.delete(ids=["doc3"])
    print(f"删除后文档数量：{collection.count()}")

    # 清理
    client.delete_collection("company_docs")
    print("\n集合已删除。")

    print("""
【ChromaDB 基础操作总结】

1. Client：数据库客户端
   - Client()：内存模式，数据不持久化
   - PersistentClient(path=...)：持久化模式

2. Collection：文档集合
   - create_collection()：创建新集合
   - get_collection()：获取已有集合
   - delete_collection()：删除集合

3. CRUD 操作：
   - add()：添加文档
   - get()：获取文档
   - update()：更新文档
   - delete()：删除文档
   - query()：相似度查询
""")


# ============================================================
# 场景 2：数据持久化
# ============================================================

def persistence_demo():
    """演示 ChromaDB 的数据持久化"""
    print("=" * 60)
    print("场景 2：数据持久化")
    print("=" * 60)

    # 持久化路径
    persist_dir = os.path.join(os.path.dirname(__file__), "chroma_storage")

    # 创建持久化客户端
    print(f"\n创建持久化客户端，存储路径：{persist_dir}")
    client = chromadb.PersistentClient(path=persist_dir)

    # 创建或获取集合
    collection = client.get_or_create_collection(
        name="persisted_docs",
        embedding_function=openai_ef,
    )

    # 检查是否是新集合
    if collection.count() == 0:
        print("新集合，添加文档...")
        collection.add(
            ids=["p1", "p2"],
            documents=[
                "这是一条会被持久化存储的文档。",
                "重启程序后，这些数据依然存在。",
            ],
            metadatas=[
                {"source": "demo", "batch": 1},
                {"source": "demo", "batch": 1},
            ]
        )
        print(f"已添加 {collection.count()} 条文档")
    else:
        print(f"集合已存在，包含 {collection.count()} 条文档")
        print("文档内容：")
        for doc in collection.get()["documents"]:
            print(f"  - {doc}")

    print("""
【持久化要点】

1. PersistentClient vs Client：
   - Client()：数据只在内存中，程序结束后丢失
   - PersistentClient()：数据保存到磁盘，永久保留

2. 存储位置：
   - 由 path 参数指定
   - 建议使用相对路径或项目内的目录
   - 注意 .gitignore 排除存储目录

3. get_or_create_collection：
   - 存在则获取，不存在则创建
   - 避免重复创建导致的错误

4. 生产环境建议：
   - 使用绝对路径，避免路径问题
   - 定期备份数据目录
   - 考虑使用 Chroma Cloud 或自托管服务器
""")

    # 清理（可选）
    print("\n是否清理测试数据？(y/n): ", end="")
    # 如果要清理，取消下面的注释
    # client.delete_collection("persisted_docs")
    # print("已清理。")


# ============================================================
# 场景 3：元数据过滤
# ============================================================

def metadata_filtering_demo():
    """演示使用元数据进行过滤查询"""
    print("=" * 60)
    print("场景 3：元数据过滤")
    print("=" * 60)

    client = chromadb.Client()
    collection = client.create_collection(
        name="filtered_docs",
        embedding_function=openai_ef,
    )

    # 添加带丰富元数据的文档
    documents = [
        "远程办公需要提前一天申请，并经过主管批准。",
        "出差报销需要在返回后 7 天内提交。",
        "新员工入职第一周需要完成安全培训。",
        "合同续签需要提前 30 天提交申请。",
        "远程办公期间需要保持在线，响应时间不超过 2 小时。",
    ]

    metadatas = [
        {"category": "远程办公", "department": "HR", "priority": "high"},
        {"category": "报销", "department": "财务", "priority": "medium"},
        {"category": "入职", "department": "HR", "priority": "high"},
        {"category": "合同", "department": "HR", "priority": "medium"},
        {"category": "远程办公", "department": "HR", "priority": "medium"},
    ]

    collection.add(
        ids=[f"doc{i}" for i in range(len(documents))],
        documents=documents,
        metadatas=metadatas,
    )

    print(f"已添加 {collection.count()} 条文档\n")

    # 过滤查询 1：按 category 过滤
    print("【查询 1：只查远程办公相关】")
    results = collection.query(
        query_texts="办公规定",
        n_results=5,
        where={"category": "远程办公"}  # 元数据过滤
    )

    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  - [{meta['category']}] {doc[:40]}...")

    # 过滤查询 2：使用比较运算符
    print("\n【查询 2：高优先级文档】")
    results = collection.query(
        query_texts="HR 政策",
        n_results=5,
        where={"priority": "high"}
    )

    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  - [{meta['category']}] {doc[:40]}...")

    # 过滤查询 3：组合条件
    print("\n【查询 3：HR 部门的高优先级文档】")
    results = collection.query(
        query_texts="公司政策",
        n_results=5,
        where={
            "$and": [
                {"department": "HR"},
                {"priority": "high"}
            ]
        }
    )

    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  - [{meta['category']}] {doc[:40]}...")

    # 过滤查询 4：使用 $contains 过滤文档内容
    print('\n【查询 4：文档内容包含"天"】')
    results = collection.query(
        query_texts="时间规定",
        n_results=5,
        where_document={"$contains": "天"}
    )

    for doc in results["documents"][0]:
        print(f"  - {doc[:50]}...")

    print("""
【元数据过滤语法】

1. 简单匹配：
   where={"category": "远程办公"}

2. 比较运算符：
   where={"price": {"$gt": 100}}   # 大于
   where={"price": {"$gte": 100}}  # 大于等于
   where={"price": {"$lt": 100}}   # 小于
   where={"price": {"$lte": 100}}  # 小于等于
   where={"price": {"$ne": 100}}   # 不等于

3. 逻辑运算符：
   where={"$and": [条件1, 条件2]}
   where={"$or": [条件1, 条件2]}

4. 文档内容过滤：
   where_document={"$contains": "关键词"}
   where_document={"$not_contains": "关键词"}

【应用场景】
- 按部门过滤文档
- 按时间范围查询
- 按文档类型筛选
- 多条件组合过滤
""")

    client.delete_collection("filtered_docs")


# ============================================================
# 场景 4：距离度量方式
# ============================================================

def distance_metrics_demo():
    """演示不同的距离度量方式"""
    print("=" * 60)
    print("场景 4：距离度量方式对比")
    print("=" * 60)

    # 准备测试文档
    documents = [
        "Python 是一种流行的编程语言。",
        "Python 广泛应用于数据科学和机器学习。",
        "Java 是另一种流行的编程语言。",
        "今天天气真好，适合出去散步。",
    ]

    # 测试三种距离度量
    metrics = ["cosine", "l2", "ip"]  # 余弦、L2、内积
    query = "编程语言"

    print(f"查询：'{query}'\n")

    for metric in metrics:
        client = chromadb.Client()
        collection = client.create_collection(
            name=f"metric_{metric}",
            embedding_function=openai_ef,
            metadata={"hnsw:space": metric}
        )

        collection.add(
            ids=[f"d{i}" for i in range(len(documents))],
            documents=documents,
        )

        results = collection.query(
            query_texts=[query],
            n_results=4,
        )

        print(f"【{metric.upper()} 距离】")
        for doc, dist in zip(results["documents"][0], results["distances"][0]):
            # 不同度量的分数含义不同
            if metric == "cosine":
                # 余弦：越小越相似（Chroma 返回的是 1 - cosine_similarity）
                print(f"  {dist:.4f} - {doc[:35]}...")
            elif metric == "l2":
                # L2：越小越相似
                print(f"  {dist:.4f} - {doc[:35]}...")
            else:  # ip
                # 内积：越大越相似（Chroma 返回负值，所以越小越好）
                print(f"  {dist:.4f} - {doc[:35]}...")

        client.delete_collection(f"metric_{metric}")
        print()

    print("""
【距离度量方式】

1. cosine（余弦距离）—— 推荐
   - 范围：[0, 2]，0 表示完全相同
   - 只考虑方向，不考虑长度
   - 对文本长度不敏感
   - 最常用的选择

2. l2（欧几里得距离）
   - 范围：[0, +∞]，0 表示完全相同
   - 考虑向量的大小和方向
   - 对文本长度敏感
   - 适合需要考虑长度差异的场景

3. ip（内积）
   - 范围：(-∞, +∞)，越大越相似
   - 同时考虑方向和长度
   - 适合归一化后的向量

【推荐选择】
对于文本相似度，推荐使用余弦距离（cosine）
因为它对文本长度不敏感，更适合语义匹配。
""")


# ============================================================
# 场景 5：批量操作与性能
# ============================================================

def batch_operations_demo():
    """演示批量操作和性能优化"""
    print("=" * 60)
    print("场景 5：批量操作与性能")
    print("=" * 60)

    client = chromadb.Client()
    collection = client.create_collection(
        name="batch_demo",
        embedding_function=openai_ef,
    )

    # 生成测试数据
    def generate_documents(n: int) -> tuple[list[str], list[str], list[dict]]:
        """生成测试文档"""
        templates = [
            "这是第 {} 条测试文档，内容关于{}。",
            "文档 {} 讨论了{}相关的内容。",
            "第 {} 条记录包含{}的信息。",
        ]
        topics = ["技术", "商业", "科学", "艺术", "体育"]

        docs = []
        ids = []
        metas = []

        for i in range(n):
            import random
            template = templates[i % len(templates)]
            topic = topics[i % len(topics)]
            docs.append(template.format(i, topic))
            ids.append(f"doc_{i}")
            metas.append({"batch": i // 100, "topic": topic})

        return docs, ids, metas

    # 批量添加
    print("\n【批量添加文档】")
    docs, ids, metas = generate_documents(100)

    import time
    start = time.time()
    collection.add(
        documents=docs,
        ids=ids,
        metadatas=metas,
    )
    elapsed = time.time() - start

    print(f"添加 {len(docs)} 条文档，耗时 {elapsed:.2f} 秒")
    print(f"平均速度：{len(docs) / elapsed:.1f} 条/秒")

    # 批量查询
    print("\n【批量查询】")
    queries = ["技术文档", "商业信息", "科学研究"]

    start = time.time()
    results = collection.query(
        query_texts=queries,
        n_results=3,
    )
    elapsed = time.time() - start

    print(f"执行 {len(queries)} 个查询，耗时 {elapsed:.2f} 秒")

    for query, docs in zip(queries, results["documents"]):
        print(f"\n查询 '{query}' 的前 3 个结果：")
        for doc in docs:
            print(f"  - {doc[:40]}...")

    # 增量添加
    print("\n【增量添加】")
    new_docs, new_ids, new_metas = generate_documents(50)
    # 修改 ID 避免冲突
    new_ids = [f"doc_new_{i}" for i in range(len(new_ids))]

    start = time.time()
    collection.add(
        documents=new_docs,
        ids=new_ids,
        metadatas=new_metas,
    )
    elapsed = time.time() - start

    print(f"增量添加 {len(new_docs)} 条文档，耗时 {elapsed:.2f} 秒")
    print(f"集合总文档数：{collection.count()}")

    # 使用 upsert（更新或插入）
    print("\n【Upsert 操作】")
    # 如果 ID 存在则更新，不存在则插入
    collection.upsert(
        ids=["doc_0", "new_doc_1"],
        documents=[
            "这是更新后的第一条文档。",
            "这是新插入的文档。",
        ],
        metadatas=[
            {"batch": 0, "topic": "更新", "updated": True},
            {"batch": "new", "topic": "新增"},
        ]
    )
    print("Upsert 完成")

    print("""
【批量操作建议】

1. 批量大小：
   - 添加文档：建议每批 100-1000 条
   - 查询：建议每批 10-50 个查询
   - 根据网络状况和文档大小调整

2. 性能优化：
   - 使用 PersistentClient 避免重复初始化
   - 批量操作代替单条操作
   - 合理设置索引参数

3. 内存管理：
   - 大规模数据分批处理
   - 及时释放不需要的集合
   - 避免同时持有太多查询结果

4. 错误处理：
   - 实现 ID 去重或使用 upsert
   - 网络异常时重试
   - 记录失败的项目
""")

    client.delete_collection("batch_demo")


# ============================================================
# 主函数
# ============================================================

def main():
    """运行所有演示场景"""
    print("\n" + "=" * 60)
    print("    ChromaDB 向量数据库完整演示")
    print("    RAG 系统的存储层：把向量存起来")
    print("=" * 60 + "\n")

    # 检查 API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("警告：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        print("\n以下演示将无法正常运行，请配置 API Key 后重试。")
        return

    try:
        # 运行各个场景
        basic_chromadb_demo()
        persistence_demo()
        metadata_filtering_demo()
        distance_metrics_demo()
        batch_operations_demo()

    except Exception as e:
        print(f"\n发生错误：{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本分块（Chunking）演示

本示例演示如何使用 LangChain 的 RecursiveCharacterTextSplitter
将长文档切分成适合 RAG 系统处理的小块。

核心概念：
- chunk_size: 每个文本块的最大字符数
- chunk_overlap: 相邻块之间的重叠字符数
- separators: 分隔符优先级列表
"""

import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# 场景 1：基础分块演示
# ============================================================

def basic_chunking_demo():
    """演示最基础的文本分块功能"""
    print("=" * 60)
    print("场景 1：基础文本分块")
    print("=" * 60)

    # 一段示例文本（来自公司的远程办公政策）
    sample_text = """
    远程办公是一种 privilege（特权），而非权利，需要员工和公司双方的同意。

    申请流程：
    1. 员工需填写《远程办公申请表》，提交给直接主管
    2. 主管在收到申请后 5 个工作日内给出书面答复
    3. 批准后，员工需签署《远程办公协议》
    4. 试用期员工需通过试用期后方可申请远程办公

    远程办公类型：
    1. 常规远程办公：每周固定 1-3 天远程
    2. 临时远程办公：因特殊情况临时申请，单次不超过 2 周
    3. 完全远程办公：特殊岗位经 HR 特别批准
    """

    # 创建分块器
    # chunk_size=100 表示每块最多 100 个字符
    # chunk_overlap=20 表示相邻块之间有 20 个字符的重叠
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
        length_function=len,  # 使用 len() 计算长度（中文字符也算 1）
        is_separator_regex=False,
    )

    # 执行分块
    chunks = text_splitter.split_text(sample_text)

    print(f"\n原文长度：{len(sample_text)} 字符")
    print(f"分块后得到：{len(chunks)} 个块\n")

    # 打印每个块
    for i, chunk in enumerate(chunks, 1):
        print(f"--- 块 {i}（{len(chunk)} 字符）---")
        print(chunk)
        print()


# ============================================================
# 场景 2：不同 chunk_size 的对比
# ============================================================

def compare_chunk_sizes():
    """演示不同 chunk_size 对分块结果的影响"""
    print("=" * 60)
    print("场景 2：不同 chunk_size 对比")
    print("=" * 60)

    # 读取示例文档
    doc_path = os.path.join(
        os.path.dirname(__file__),
        "sample_documents",
        "remote_work_policy.txt"
    )

    with open(doc_path, "r", encoding="utf-8") as f:
        document = f.read()

    print(f"\n文档总长度：{len(document)} 字符\n")

    # 测试三种不同的 chunk_size
    chunk_sizes = [200, 500, 1000]

    results = []

    for size in chunk_sizes:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=size // 10,  # overlap 设为 chunk_size 的 10%
            length_function=len,
        )

        chunks = splitter.split_text(document)

        # 统计信息
        avg_length = sum(len(c) for c in chunks) / len(chunks) if chunks else 0

        results.append({
            "chunk_size": size,
            "num_chunks": len(chunks),
            "avg_length": avg_length,
        })

        print(f"chunk_size={size}:")
        print(f"  - 生成块数：{len(chunks)}")
        print(f"  - 平均块长：{avg_length:.1f} 字符")
        print(f"  - 第一块预览：{chunks[0][:80]}...")
        print()

    # 打印对比表格
    print("\n对比总结：")
    print("-" * 50)
    print(f"{'chunk_size':>12} | {'块数':>8} | {'平均长度':>10}")
    print("-" * 50)
    for r in results:
        print(f"{r['chunk_size']:>12} | {r['num_chunks']:>8} | {r['avg_length']:>10.1f}")
    print("-" * 50)

    print("""
【选择 chunk_size 的建议】
- 太小（<200）：上下文不完整，语义被切断
- 太大（>1500）：检索精度下降，可能包含无关内容
- 推荐范围：500-1000 字符，根据文档类型调整

对于中文文档，建议 chunk_size 设为 500-800，因为：
1. 中文信息密度高，短文本也能包含完整语义
2. 避免 LLM 上下文窗口浪费
3. 提高检索的精准度
""")


# ============================================================
# 场景 3：中文优化的分隔符设置
# ============================================================

def chinese_text_chunking():
    """演示针对中文的优化分隔符设置"""
    print("=" * 60)
    print("场景 3：中文优化分隔符")
    print("=" * 60)

    # 中文示例文本
    chinese_text = """
    第一章 什么是 RAG

    RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合了信息检索和文本生成的技术。

    它的工作原理是：首先从知识库中检索相关文档，然后将这些文档作为上下文提供给大语言模型，让模型基于这些上下文生成回答。

    第二章 为什么需要 RAG

    大语言模型有两个主要限制：一是知识截止日期，模型无法知道训练之后发生的事情；二是容易产生"幻觉"，即编造看似合理但实际错误的信息。

    RAG 通过检索外部知识库来缓解这些问题，让模型能够基于真实、最新的信息生成回答。
    """

    # 默认分隔符（对中文效果可能不佳）
    default_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    # 中文优化的分隔符
    # 注意：\n\n 优先（段落），然后是 \n（行），再是中文标点
    chinese_separators = [
        "\n\n",  # 段落分隔（最优先）
        "\n",    # 换行
        "。",    # 中文句号
        "！",   # 中文感叹号
        "？",   # 中文问号
        "；",   # 中文分号
        "，",   # 中文逗号
        " ",    # 空格
        "",     # 最后兜底：按字符切分
    ]

    chinese_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
        separators=chinese_separators,
    )

    # 对比两种分块效果
    default_chunks = default_splitter.split_text(chinese_text)
    chinese_chunks = chinese_splitter.split_text(chinese_text)

    print("\n【默认分隔符分块结果】")
    for i, chunk in enumerate(default_chunks[:3], 1):  # 只显示前 3 个
        print(f"块 {i}: {repr(chunk[:50])}...")

    print("\n【中文优化分隔符分块结果】")
    for i, chunk in enumerate(chinese_chunks[:3], 1):
        print(f"块 {i}: {repr(chunk[:50])}...")

    print("""
【中文分隔符设置要点】

1. 优先级顺序很重要：
   - 先尝试段落分隔（\n\n）
   - 再尝试句子分隔（句号、问号、感叹号）
   - 最后尝试词语分隔（逗号、空格）

2. Unicode 中文标点：
   - 中文句号：\u3002 或直接写 "。"
   - 中文逗号：\uff0c 或 "，"
   - 中文问号：\uff1f 或 "？"
   - 顿号：\u3001 或 "、"

3. 实际使用中，建议直接使用中文字符而非 Unicode 编码，可读性更好
""")


# ============================================================
# 场景 4：处理文档对象（带元数据）
# ============================================================

def document_with_metadata_demo():
    """演示如何分块 Document 对象并保留元数据"""
    print("=" * 60)
    print("场景 4：处理 Document 对象（保留元数据）")
    print("=" * 60)

    from langchain_core.documents import Document

    # 创建带元数据的 Document 对象
    documents = [
        Document(
            page_content="""
            报销范围：
            1. 差旅费用：交通费、住宿费、餐饮费
            2. 业务招待费：客户招待、团队活动
            3. 办公用品：经批准的个人办公用品采购
            4. 培训费用：外部培训课程、考试费用

            不可报销费用：
            - 个人消费
            - 超出标准的消费
            - 无正规发票的费用
            """,
            metadata={
                "source": "expense_reimbursement.txt",
                "category": "财务制度",
                "department": "财务部",
            }
        ),
        Document(
            page_content="""
            差旅费用标准：

            【交通费】
            - 火车：高铁二等座、动车二等座、普通列车硬卧
            - 飞机：经济舱（飞行时间 4 小时以上可申请商务舱）
            - 市内交通：实报实销，单日上限 100 元

            【住宿费】
            - 一线城市：500 元/晚以下
            - 二线城市：350 元/晚以下
            - 其他城市：200 元/晚以下
            """,
            metadata={
                "source": "expense_reimbursement.txt",
                "category": "财务制度",
                "department": "财务部",
            }
        )
    ]

    # 创建分块器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    # 使用 split_documents 方法（会自动继承元数据）
    chunks = text_splitter.split_documents(documents)

    print(f"\n原始文档数：{len(documents)}")
    print(f"分块后文档数：{len(chunks)}\n")

    # 展示分块结果
    for i, chunk in enumerate(chunks[:4], 1):  # 只显示前 4 个
        print(f"--- 块 {i} ---")
        print(f"内容：{chunk.page_content[:60]}...")
        print(f"元数据：{chunk.metadata}")
        print()

    print("""
【关键点】

1. split_documents() 会自动继承原始文档的元数据
2. 每个分块都有相同的 metadata 字典
3. 可以在 metadata 中存储来源、分类、权限等信息
4. RAG 检索时可以根据 metadata 进行过滤
""")


# ============================================================
# 场景 5：常见错误与解决方案
# ============================================================

def common_mistakes():
    """演示常见的分块错误和解决方案"""
    print("=" * 60)
    print("场景 5：常见错误与解决方案")
    print("=" * 60)

    sample = "这是一个测试句子。这是另一个测试句子。"

    # 错误 1：chunk_overlap 大于 chunk_size
    print("\n【错误 1：chunk_overlap > chunk_size】")
    try:
        bad_splitter = RecursiveCharacterTextSplitter(
            chunk_size=50,
            chunk_overlap=100,  # 错误！
        )
        print("  创建成功，但分块时可能出问题...")
        chunks = bad_splitter.split_text(sample)
        print(f"  结果：{chunks}")
    except Exception as e:
        print(f"  报错：{e}")

    # 错误 2：忘记设置 overlap
    print("\n【错误 2：chunk_overlap=0（可能导致语义断裂）】")
    no_overlap_splitter = RecursiveCharacterTextSplitter(
        chunk_size=20,
        chunk_overlap=0,
    )
    chunks = no_overlap_splitter.split_text("这是一段很长的文本用于测试没有重叠时的效果。")
    for i, chunk in enumerate(chunks, 1):
        print(f"  块 {i}: {repr(chunk)}")

    print("\n  问题：信息可能在边界处丢失")
    print("  解决：设置合理的 overlap（推荐 chunk_size 的 10-20%）")

    # 错误 3：使用错误的 length_function
    print("\n【错误 3：使用错误的长度计算方式】")

    # 对于需要按 token 计数的场景
    def token_length(text: str) -> int:
        """简单的 token 计数（按空格和字符估算）"""
        # 这是一个简化版本，实际应使用 tiktoken
        return len(text.split()) + len(text) // 2

    token_splitter = RecursiveCharacterTextSplitter(
        chunk_size=50,  # 这里表示 50 个 token
        chunk_overlap=10,
        length_function=token_length,
    )

    print("  使用自定义 length_function 计算 token 数量")
    print("  注意：对于精确控制，应使用 tiktoken 库")

    # 最佳实践总结
    print("""
【最佳实践总结】

1. chunk_size 选择：
   - 中文文档：500-800 字符
   - 英文文档：800-1200 字符
   - 代码文件：1000-1500 字符

2. chunk_overlap 选择：
   - 一般情况：chunk_size 的 10-20%
   - 重要文档：可以更大（20-30%）
   - 避免超过 chunk_size 的 50%

3. 分隔符设置：
   - 中文：优先使用中文标点
   - 代码：使用类/函数定义作为分隔
   - Markdown：使用标题作为分隔

4. 测试验证：
   - 分块后检查边界处是否有语义断裂
   - 确保重要信息不会被切断
   - 抽样检查分块质量
""")


# ============================================================
# 主函数
# ============================================================

def main():
    """运行所有演示场景"""
    print("\n" + "=" * 60)
    print("    文本分块（Chunking）完整演示")
    print("    RAG 系统的第一步：把长文档变成小块")
    print("=" * 60 + "\n")

    # 运行各个场景
    basic_chunking_demo()
    compare_chunk_sizes()
    chinese_text_chunking()
    document_with_metadata_demo()
    common_mistakes()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量嵌入（Embedding）演示

本示例演示如何使用 OpenAI 的 Embedding API 将文本转换为向量，
以及如何计算向量之间的相似度。

核心概念：
- Embedding：将文本转换为高维向量表示
- Cosine Similarity：余弦相似度，衡量两个向量的相似程度
- text-embedding-3-small：OpenAI 的高效嵌入模型
"""

import os
import numpy as np
from openai import OpenAI

# 初始化 OpenAI 客户端
# 确保环境变量 OPENAI_API_KEY 已设置
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 使用的嵌入模型
EMBEDDING_MODEL = "text-embedding-3-small"


# ============================================================
# 工具函数：计算余弦相似度
# ============================================================

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的余弦相似度。

    余弦相似度的值范围是 [-1, 1]：
    - 1 表示方向完全相同（最相似）
    - 0 表示正交（无相关性）
    - -1 表示方向完全相反（最不相似）

    在文本嵌入中，相似度通常在 [0, 1] 范围内。
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    # 计算点积
    dot_product = np.dot(vec1, vec2)

    # 计算向量的模（长度）
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    # 避免除以零
    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    """
    获取文本的嵌入向量。

    参数：
        text: 要嵌入的文本
        model: 嵌入模型名称

    返回：
        嵌入向量（1536 维的浮点数列表）
    """
    # 替换换行符（OpenAI 建议这样做）
    text = text.replace("\n", " ")

    response = client.embeddings.create(
        input=[text],
        model=model,
    )

    return response.data[0].embedding


def get_embeddings_batch(texts: list[str], model: str = EMBEDDING_MODEL) -> list[list[float]]:
    """
    批量获取多个文本的嵌入向量。

    批量调用比逐个调用更高效，因为：
    1. 减少网络请求次数
    2. 更好地利用 GPU 批处理
    """
    # 清理文本
    texts = [text.replace("\n", " ") for text in texts]

    response = client.embeddings.create(
        input=texts,
        model=model,
    )

    # 按 index 顺序返回
    return [data.embedding for data in sorted(response.data, key=lambda x: x.index)]


# ============================================================
# 场景 1：基础嵌入演示
# ============================================================

def basic_embedding_demo():
    """演示最基础的文本嵌入功能"""
    print("=" * 60)
    print("场景 1：基础文本嵌入")
    print("=" * 60)

    text = "RAG 是一种结合检索和生成的技术"

    print(f"\n原始文本：{text}")
    print("\n正在调用 OpenAI Embedding API...")

    embedding = get_embedding(text)

    print(f"\n嵌入向量维度：{len(embedding)}")
    print(f"向量类型：{type(embedding)}")
    print(f"前 10 个维度值：{embedding[:10]}")
    print(f"向量范数：{np.linalg.norm(embedding):.4f}")

    print("""
【关于 text-embedding-3-small 模型】

1. 向量维度：1536
2. 最大输入：8191 tokens
3. 性能：速度和质量的平衡选择
4. 成本：$0.02 / 1M tokens（2024 年价格）

5. 与 text-embedding-3-large 的对比：
   - large 维度：3072
   - large 质量更高，但成本也更高（$0.13 / 1M tokens）
   - 对于大多数 RAG 应用，small 已经足够
""")


# ============================================================
# 场景 2：语义相似度对比
# ============================================================

def semantic_similarity_demo():
    """演示语义相似度的计算"""
    print("=" * 60)
    print("场景 2：语义相似度对比")
    print("=" * 60)

    # 准备测试文本
    texts = {
        "query": "如何申请远程办公？",
        "similar_1": "远程办公的申请流程是什么？",  # 语义相似
        "similar_2": "怎样办理居家办公手续？",    # 语义相似（同义词）
        "different_1": "公司的午餐时间是几点？",  # 完全不同
        "different_2": "报销流程需要多长时间？",  # 完全不同
        "related": "远程办公期间的工作时间要求",  # 相关但不是同一个问题
    }

    print("\n获取所有文本的嵌入向量...")
    embeddings = {}
    for name, text in texts.items():
        embeddings[name] = get_embedding(text)
        print(f"  已获取：{name}")

    # 计算查询文本与其他文本的相似度
    query_embedding = embeddings["query"]

    print("\n相似度分析：")
    print("-" * 50)

    similarities = []
    for name, embedding in embeddings.items():
        if name != "query":
            sim = cosine_similarity(query_embedding, embedding)
            similarities.append((name, sim, texts[name]))
            print(f"\n与 '{name}' 的相似度：{sim:.4f}")
            print(f"  文本：{texts[name]}")

    # 排序展示
    print("\n" + "=" * 50)
    print("按相似度排序：")
    print("=" * 50)
    similarities.sort(key=lambda x: x[1], reverse=True)
    for name, sim, text in similarities:
        bar = "█" * int(sim * 40)  # 可视化
        print(f"{sim:.4f} {bar} {name}")

    print("""
【观察结论】

1. 语义相似的文本，即使用词不同，相似度也较高
2. 同义词替换（"申请" → "办理"）对相似度影响较小
3. 完全不相关的主题，相似度明显较低
4. 这就是 RAG 能够"理解"用户问题的原因

【相似度阈值参考】
- > 0.8：高度相关，可能是同一主题
- 0.6-0.8：相关，可以作为检索结果
- 0.4-0.6：弱相关，需要进一步判断
- < 0.4：基本不相关
""")


# ============================================================
# 场景 3：跨语言相似度
# ============================================================

def cross_language_similarity():
    """演示中英文之间的语义相似度"""
    print("=" * 60)
    print("场景 3：跨语言语义相似度")
    print("=" * 60)

    # 同一个概念的中英文表达
    texts = {
        "中文": "机器学习是人工智能的一个分支",
        "英文": "Machine learning is a branch of artificial intelligence",
        "中文变体": "机器学习属于人工智能领域",
        "无关中文": "今天天气真不错",
    }

    print("\n获取嵌入向量...")
    embeddings = {name: get_embedding(text) for name, text in texts.items()}

    # 计算中文与英文的相似度
    sim_cn_en = cosine_similarity(embeddings["中文"], embeddings["英文"])
    sim_cn_variant = cosine_similarity(embeddings["中文"], embeddings["中文变体"])
    sim_cn_random = cosine_similarity(embeddings["中文"], embeddings["无关中文"])

    print(f"\n【相似度对比】")
    print(f"中文 vs 英文：{sim_cn_en:.4f}")
    print(f"中文 vs 中文变体：{sim_cn_variant:.4f}")
    print(f"中文 vs 无关中文：{sim_cn_random:.4f}")

    print("""
【观察结论】

1. 中英文翻译的相似度较高（>0.9），说明模型理解了语义
2. 这意味着 RAG 系统可以用中文查询，检索英文文档
3. 或者用英文查询，检索中文文档
4. 这对多语言知识库非常有用

【注意事项】
- 跨语言检索的效果取决于嵌入模型的训练数据
- text-embedding-3 系列对多语言支持良好
- 对于专业术语，同语言检索效果更好
""")


# ============================================================
# 场景 4：批量嵌入与成本估算
# ============================================================

def batch_embedding_and_cost():
    """演示批量嵌入和成本估算"""
    print("=" * 60)
    print("场景 4：批量嵌入与成本估算")
    print("=" * 60)

    # 准备一批文档
    documents = [
        "公司的远程办公政策允许员工每周在家工作最多 3 天。",
        "报销流程需要提供正规发票，并在费用发生后 30 天内提交。",
        "IT 部门的工作时间是周一至周五 8:30-18:30。",
        "新员工入职当天需要到 IT 服务台领取笔记本电脑。",
        "VPN 连接失败时，请先检查账号密码是否正确。",
    ]

    print(f"\n文档数量：{len(documents)}")
    print("文档内容：")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. {doc[:40]}...")

    # 方法 1：逐个调用（不推荐）
    print("\n【方法 1：逐个调用】")
    print("正在逐个获取嵌入向量...")

    import time
    start_time = time.time()
    embeddings_sequential = []
    for doc in documents:
        emb = get_embedding(doc)
        embeddings_sequential.append(emb)
    sequential_time = time.time() - start_time

    print(f"完成！耗时：{sequential_time:.2f} 秒")

    # 方法 2：批量调用（推荐）
    print("\n【方法 2：批量调用】")
    print("正在批量获取嵌入向量...")

    start_time = time.time()
    embeddings_batch = get_embeddings_batch(documents)
    batch_time = time.time() - start_time

    print(f"完成！耗时：{batch_time:.2f} 秒")
    print(f"速度提升：{sequential_time / batch_time:.1f}x")

    # 成本估算
    print("\n【成本估算】")

    # 估算 token 数（简化：中文字符约等于 token）
    total_chars = sum(len(doc) for doc in documents)
    estimated_tokens = total_chars  # 粗略估计

    # text-embedding-3-small 定价：$0.02 / 1M tokens
    cost_per_1m = 0.02
    estimated_cost = (estimated_tokens / 1_000_000) * cost_per_1m

    print(f"总字符数：{total_chars}")
    print(f"预估 token 数：{estimated_tokens}")
    print(f"预估成本：${estimated_cost:.6f}")

    # 扩展到大规模场景
    print("\n【大规模场景成本估算】")
    scenarios = [
        ("小型知识库", 1_000, 500),
        ("中型知识库", 10_000, 500),
        ("大型知识库", 100_000, 500),
        ("企业级知识库", 1_000_000, 500),
    ]

    print(f"{'场景':<15} | {'文档数':>10} | {'平均长度':>8} | {'预估成本':>12}")
    print("-" * 55)
    for name, num_docs, avg_length in scenarios:
        total_tokens = num_docs * avg_length
        cost = (total_tokens / 1_000_000) * cost_per_1m
        print(f"{name:<15} | {num_docs:>10,} | {avg_length:>8} | ${cost:>10.2f}")

    print("""
【成本优化建议】

1. 批量调用：
   - 减少网络请求次数
   - 更好地利用 API 速率限制
   - 建议每批最多 2048 个文本

2. 缓存策略：
   - 嵌入向量不变，可以缓存
   - 只在文档更新时重新计算
   - 使用本地向量数据库存储

3. 模型选择：
   - 小规模/高质量需求：text-embedding-3-large
   - 大规模/成本敏感：text-embedding-3-small
   - 开源替代：bge-large-zh, m3e-base 等
""")


# ============================================================
# 场景 5：错误处理与最佳实践
# ============================================================

def error_handling_demo():
    """演示嵌入 API 的错误处理"""
    print("=" * 60)
    print("场景 5：错误处理与最佳实践")
    print("=" * 60)

    # 错误 1：空文本
    print("\n【错误 1：空文本】")
    try:
        get_embedding("")
    except Exception as e:
        print(f"  报错：{type(e).__name__}: {e}")
        print("  解决：在调用前检查文本是否为空")

    # 错误 2：文本过长
    print("\n【错误 2：文本过长】")
    long_text = "测试内容 " * 10000  # 非常长的文本
    try:
        get_embedding(long_text)
    except Exception as e:
        print(f"  报错：{type(e).__name__}")
        print("  解决：在嵌入前对长文本进行分块")

    # 错误 3：API Key 未设置
    print("\n【错误 3：API Key 未设置】")
    print("  如果未设置 OPENAI_API_KEY 环境变量，会报错：")
    print("  openai.AuthenticationError: Incorrect API key provided")
    print("  解决：export OPENAI_API_KEY='your-api-key'")

    # 最佳实践代码
    print("\n【最佳实践：安全的嵌入函数】")

    safe_embedding_code = '''
def safe_get_embedding(text: str) -> list[float] | None:
    """安全的嵌入获取函数"""
    # 1. 检查空文本
    if not text or not text.strip():
        print("警告：文本为空，跳过嵌入")
        return None

    # 2. 检查文本长度
    max_tokens = 8000  # 留一些余量
    if len(text) > max_tokens:
        print(f"警告：文本过长（{len(text)} 字符），截断处理")
        text = text[:max_tokens]

    # 3. 调用 API（带重试）
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return get_embedding(text)
        except openai.RateLimitError:
            wait_time = (attempt + 1) * 2
            print(f"速率限制，等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
        except openai.APIError as e:
            print(f"API 错误：{e}")
            if attempt == max_retries - 1:
                raise

    return None
'''
    print(safe_embedding_code)

    print("""
【嵌入前预处理建议】

1. 清理文本：
   - 移除多余的空白字符
   - 统一换行符
   - 移除不可见字符

2. 文本长度控制：
   - 超长文本应先分块
   - 保留语义完整性
   - 避免在句子中间截断

3. 批量处理：
   - 使用批量 API 提高效率
   - 注意 API 速率限制
   - 实现指数退避重试
""")


# ============================================================
# 主函数
# ============================================================

def main():
    """运行所有演示场景"""
    print("\n" + "=" * 60)
    print("    向量嵌入（Embedding）完整演示")
    print("    RAG 系统的核心：把文本变成向量")
    print("=" * 60 + "\n")

    # 检查 API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("警告：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        print("\n以下演示将无法正常运行，请配置 API Key 后重试。")
        return

    try:
        # 运行各个场景
        basic_embedding_demo()
        semantic_similarity_demo()
        cross_language_similarity()
        batch_embedding_and_cost()
        error_handling_demo()

    except Exception as e:
        print(f"\n发生错误：{type(e).__name__}: {e}")
        print("请检查网络连接和 API Key 是否正确。")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

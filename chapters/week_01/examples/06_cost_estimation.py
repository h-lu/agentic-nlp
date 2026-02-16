#!/usr/bin/env python3
"""
06_cost_estimation.py - Token 计算和成本估算

本示例展示如何计算 Token 数和估算 API 调用成本：
- 使用 tiktoken 库计算 Token 数
- 展示中英文 Token 差异
- 成本估算函数

运行前安装依赖：
    pip install tiktoken

本示例不需要 API Key，所有操作都在本地进行。
"""

import tiktoken
from typing import Literal


# 当前主流模型的定价（美元/百万 Token）
# 数据来源：各模型官方定价页面，2025 年 2 月
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "glm-4": {"input": 0.10, "output": 0.10},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
}


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    计算文本的 Token 数量。

    Args:
        text: 需要计算 Token 的文本
        model: 模型名称，用于选择正确的编码器

    Returns:
        Token 数量

    Example:
        >>> count_tokens("Hello, world!")
        4
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        # 未知模型，使用 cl100k_base（GPT-4/3.5 的编码）
        enc = tiktoken.get_encoding("cl100k_base")

    return len(enc.encode(text))


def count_tokens_for_messages(
    messages: list[dict],
    model: str = "gpt-4o"
) -> int:
    """
    计算 Chat API 消息列表的 Token 数量。

    注意：这是近似计算，实际 Token 数可能略有差异。
    OpenAI 官方的计算方法更复杂，包含额外的格式化 Token。

    Args:
        messages: Chat API 的消息列表
        model: 模型名称

    Returns:
        Token 数量
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    # 每条消息的固定开销（tokens per message）
    # GPT-4/3.5 使用 cl100k_base 编码时为 3-4 tokens
    tokens_per_message = 4
    tokens_per_name = 1

    num_tokens = 0

    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(enc.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 2  # 每个回复的开头需要 assistant primer

    return num_tokens


def estimate_cost(
    num_items: int,
    input_tokens_per_item: int,
    output_tokens_per_item: int,
    model: str = "gpt-4o",
) -> float:
    """
    估算 API 调用成本。

    Args:
        num_items: 调用次数（处理的项目数量）
        input_tokens_per_item: 每次调用的输入 Token 数
        output_tokens_per_item: 每次调用的输出 Token 数
        model: 模型名称

    Returns:
        预估成本（美元）

    Example:
        >>> # 处理 1000 条新闻，每条约 400 输入 + 50 输出
        >>> estimate_cost(1000, 400, 50, "gpt-4o")
        1.5
    """
    if model not in MODEL_PRICING:
        raise ValueError(f"未知模型：{model}。支持的模型：{list(MODEL_PRICING.keys())}")

    pricing = MODEL_PRICING[model]

    total_input_tokens = num_items * input_tokens_per_item
    total_output_tokens = num_items * output_tokens_per_item

    input_cost = (total_input_tokens / 1_000_000) * pricing["input"]
    output_cost = (total_output_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost


def compare_models(
    num_items: int,
    input_tokens_per_item: int,
    output_tokens_per_item: int,
    models: list[str] | None = None,
) -> dict[str, float]:
    """
    比较不同模型的成本。

    Args:
        num_items: 调用次数
        input_tokens_per_item: 每次调用的输入 Token 数
        output_tokens_per_item: 每次调用的输出 Token 数
        models: 要比较的模型列表，默认比较所有支持的模型

    Returns:
        字典，键为模型名称，值为预估成本
    """
    if models is None:
        models = list(MODEL_PRICING.keys())

    costs = {}
    for model in models:
        if model in MODEL_PRICING:
            costs[model] = estimate_cost(
                num_items, input_tokens_per_item, output_tokens_per_item, model
            )

    return costs


def analyze_text_tokenization(text: str, model: str = "gpt-4o") -> dict:
    """
    分析文本的 Token 化情况。

    Args:
        text: 要分析的文本
        model: 模型名称

    Returns:
        包含字符数、Token 数、Token/字符比等信息
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    tokens = enc.encode(text)

    return {
        "text": text,
        "char_count": len(text),
        "token_count": len(tokens),
        "tokens": tokens[:20],  # 只显示前 20 个 Token
        "token_example": [enc.decode([t]) for t in tokens[:10]],  # 前 10 个 Token 的解码
        "ratio": len(tokens) / len(text) if text else 0,
    }


# 示例文本
SAMPLE_TEXTS = {
    "english_short": "Hello, world!",
    "english_long": """
    The quick brown fox jumps over the lazy dog. This is a sample English text
    used to demonstrate token counting. The text contains multiple sentences
    and various punctuation marks to show how different elements are tokenized.
    """,
    "chinese_short": "你好，世界！",
    "chinese_long": """
    苹果公司今天发布了 2025 财年第一季度财报。财报显示，公司营收达到 1243 亿美元，
    同比增长 4%。iPhone 业务贡献了 697 亿美元收入，超出分析师预期。苹果 CEO 蒂姆·库克
    表示，对中国市场的发展势头感到乐观。
    """,
    "mixed": """
    OpenAI announced GPT-4o today. 这款新模型支持多模态输入，
    including text, images, and audio. 价格为 $5/1M input tokens。
    """,
    "code": """
def hello_world():
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    hello_world()
    """,
}


def main() -> None:
    """主函数：演示 Token 计算和成本估算"""
    print("=" * 60)
    print("Token 计算和成本估算演示")
    print("=" * 60)

    # 1. 中英文 Token 对比
    print("\n1. 中英文 Token 对比：")
    print("-" * 40)

    for name, text in SAMPLE_TEXTS.items():
        if name in ["english_short", "chinese_short", "mixed"]:
            analysis = analyze_text_tokenization(text.strip())
            print(f"\n【{name}】")
            print(f"  文本：{text.strip()[:30]}...")
            print(f"  字符数：{analysis['char_count']}")
            print(f"  Token 数：{analysis['token_count']}")
            print(f"  Token/字符比：{analysis['ratio']:.2f}")
            print(f"  Token 示例：{analysis['token_example']}")

    # 2. 不同文本类型的 Token 分析
    print("\n" + "=" * 60)
    print("2. 不同文本类型的 Token 分析：")
    print("-" * 40)

    for name, text in SAMPLE_TEXTS.items():
        analysis = analyze_text_tokenization(text.strip())
        print(f"\n【{name}】")
        print(f"  字符数：{analysis['char_count']:4d} | Token 数：{analysis['token_count']:4d} | 比率：{analysis['ratio']:.2f}")

    # 3. Chat API 消息的 Token 计算
    print("\n" + "=" * 60)
    print("3. Chat API 消息的 Token 计算：")
    print("-" * 40)

    messages = [
        {"role": "system", "content": "你是一个新闻分类助手。请判断新闻属于哪个类别。"},
        {"role": "user", "content": "苹果公司发布新款 iPhone，搭载 A18 芯片。"},
    ]

    token_count = count_tokens_for_messages(messages)
    print(f"消息列表 Token 数：{token_count}")
    print(f"消息内容：")
    for msg in messages:
        print(f"  [{msg['role']}]: {msg['content'][:50]}...")

    # 4. 成本估算
    print("\n" + "=" * 60)
    print("4. 成本估算示例：")
    print("-" * 40)

    # 假设处理 1000 条新闻
    num_news = 1000

    # 每条新闻的 Token 估算
    news_text = SAMPLE_TEXTS["chinese_long"]
    news_tokens = count_tokens(news_text)

    # 分类任务：约 100 Token Prompt + 新闻 Token，输出约 2 Token
    classify_input = 100 + news_tokens
    classify_output = 2

    # 摘要任务：约 100 Token Prompt + 新闻 Token，输出约 80 Token
    summarize_input = 100 + news_tokens
    summarize_output = 80

    # 实体抽取：约 150 Token Prompt + 新闻 Token，输出约 50 Token
    extract_input = 150 + news_tokens
    extract_output = 50

    print(f"\n假设处理 {num_news} 条新闻，每条约 {news_tokens} Token")
    print(f"\n各任务成本（使用 gpt-4o）：")

    for task, input_t, output_t in [
        ("分类", classify_input, classify_output),
        ("摘要", summarize_input, summarize_output),
        ("实体抽取", extract_input, extract_output),
    ]:
        cost = estimate_cost(num_news, input_t, output_t, "gpt-4o")
        print(f"  {task}：输入 {input_t:3d} + 输出 {output_t:3d} = ${cost:.4f}")

    total_cost = estimate_cost(num_news, classify_input, classify_output, "gpt-4o")
    total_cost += estimate_cost(num_news, summarize_input, summarize_output, "gpt-4o")
    total_cost += estimate_cost(num_news, extract_input, extract_output, "gpt-4o")
    print(f"\n  总计：${total_cost:.4f}")

    # 5. 模型成本对比
    print("\n" + "=" * 60)
    print("5. 不同模型的成本对比：")
    print("-" * 40)

    # 使用分类任务的 Token 数进行对比
    costs = compare_models(
        num_news,
        classify_input,
        classify_output,
        models=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "deepseek-chat", "glm-4"]
    )

    print(f"\n处理 {num_news} 条新闻（分类任务）的成本对比：")
    for model, cost in sorted(costs.items(), key=lambda x: x[1]):
        print(f"  {model:20s}: ${cost:.4f}")

    # 6. 大规模处理成本估算
    print("\n" + "=" * 60)
    print("6. 大规模处理成本估算：")
    print("-" * 40)

    scales = [1000, 10000, 100000, 1000000]

    print(f"\n使用 gpt-4o-mini 处理不同规模文本的成本：")
    for scale in scales:
        cost = estimate_cost(scale, classify_input, classify_output, "gpt-4o-mini")
        print(f"  {scale:10,d} 条：${cost:10.2f}")

    # 7. 获取编码器信息
    print("\n" + "=" * 60)
    print("7. 编码器信息：")
    print("-" * 40)

    encodings = tiktoken.list_encoding_names()
    print(f"\n可用的编码器：{encodings}")

    for model in ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]:
        enc_name = tiktoken.encoding_name_for_model(model)
        enc = tiktoken.get_encoding(enc_name)
        print(f"\n{model}：")
        print(f"  编码器：{enc_name}")
        print(f"  词汇表大小：{enc.n_vocab}")


if __name__ == "__main__":
    main()

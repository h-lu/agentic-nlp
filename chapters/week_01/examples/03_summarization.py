#!/usr/bin/env python3
"""
03_summarization.py - 文本摘要示例

本示例展示如何使用 LLM 进行文本摘要：
- 新闻摘要生成
- 指定摘要长度限制
- 多种摘要风格

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

from typing import Literal
from openai import OpenAI


# 摘要风格类型
SummaryStyle = Literal["简洁", "详细", "要点"]


def summarize_text(
    text: str,
    max_words: int = 100,
    style: SummaryStyle = "简洁"
) -> str:
    """
    使用 LLM 生成文本摘要。

    Args:
        text: 需要摘要的文本
        max_words: 摘要的最大字数限制
        style: 摘要风格，可选 "简洁"/"详细"/"要点"

    Returns:
        生成的摘要文本

    Example:
        >>> news = "苹果公司发布财报，营收 1243 亿美元..."
        >>> summarize_text(news, max_words=50)
        '苹果Q1营收1243亿美元增4%，iPhone贡献697亿超预期。'
    """
    client = OpenAI()

    # 根据风格构建不同的 system prompt
    style_prompts = {
        "简洁": f"""你是一个新闻摘要助手。请将文本压缩成 {max_words} 字以内的简洁摘要。
要求：
1. 保留关键信息：谁、什么事、多少、变化趋势
2. 使用简洁的语言，去除冗余
3. 不要添加原文没有的信息""",

        "详细": f"""你是一个新闻摘要助手。请生成一份 {max_words} 字以内的详细摘要。
要求：
1. 包含主要事实和关键细节
2. 保留重要数据和引述
3. 结构清晰，可以分段""",

        "要点": f"""你是一个新闻摘要助手。请提取文本的 {max_words} 字以内的关键要点。
要求：
1. 用条目形式列出 3-5 个要点
2. 每个要点一行，以 "- " 开头
3. 突出最重要的信息"""
    }

    system_prompt = style_prompts.get(style, style_prompts["简洁"])

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0,
    )

    return completion.choices[0].message.content or ""


def summarize_with_structure(text: str) -> dict[str, str]:
    """
    生成结构化的新闻摘要，包含标题、一句话摘要和详细摘要。

    Args:
        text: 新闻文本

    Returns:
        包含 title、one_liner、detail 三个键的字典
    """
    client = OpenAI()

    system_prompt = """你是一个新闻摘要助手。请对给定的新闻生成结构化摘要：
1. title: 一个 10-15 字的标题
2. one_liner: 一句话摘要（20-30 字）
3. detail: 详细摘要（50-100 字）

请严格按照以下 JSON 格式输出：
{
    "title": "...",
    "one_liner": "...",
    "detail": "..."
}

只输出 JSON，不要其他内容。"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0,
    )

    # 解析 JSON 响应
    import json
    result = completion.choices[0].message.content or "{}"

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # 如果 JSON 解析失败，返回默认结构
        return {
            "title": "解析失败",
            "one_liner": result[:50],
            "detail": result
        }


# 示例新闻（较长，适合做摘要练习）
LONG_NEWS = """
北京时间 2 月 15 日凌晨，苹果公司发布了 2025 财年第一季度财报。财报显示，
公司当季营收达到 1243 亿美元，同比增长 4%，超过市场预期的 1210 亿美元。
这是苹果公司历史上最高的季度营收记录。

分业务来看，iPhone 业务依然是营收的主力军，贡献了 697 亿美元收入，
同比增长 3%，超出分析师预期的 670 亿美元。Mac 业务营收为 89 亿美元，
同比增长 6%；iPad 业务营收 72 亿美元，同比下降 2%。服务业务表现亮眼，
营收达到 235 亿美元，同比增长 14%，创下历史新高。

苹果 CEO 蒂姆·库克在财报电话会议上表示，公司对中国市场的发展势头感到乐观。
他说："我们在中国看到了强劲的需求，尤其是 iPhone 16 系列的销售表现超出了
我们的预期。"库克还透露，苹果正在积极布局人工智能领域，预计将在今年晚些
时候推出更多 AI 相关功能。

财报发布后，苹果股价在盘后交易中上涨 2.3%，报收于 195.42 美元。分析师普遍
认为，这份财报表明苹果在全球经济不确定性增加的背景下，依然保持着强劲的
盈利能力。多家投行上调了苹果的目标股价，摩根士丹利将目标价从 200 美元
上调至 220 美元，维持"增持"评级。
"""


def main() -> None:
    """主函数：演示文本摘要功能"""
    print("=" * 60)
    print("示例：使用 LLM 进行文本摘要")
    print("=" * 60)

    # 展示原文
    print("\n原始新闻（约 400 字）：")
    print("-" * 40)
    print(LONG_NEWS[:200] + "...")

    # 不同风格的摘要
    print("\n" + "=" * 60)
    print("1. 不同风格的摘要：")
    print("-" * 40)

    for style in ["简洁", "详细", "要点"]:
        summary = summarize_text(LONG_NEWS, max_words=80, style=style)
        print(f"\n【{style}风格摘要】（80字以内）")
        print(f"  {summary}")

    # 不同长度限制
    print("\n" + "=" * 60)
    print("2. 不同长度限制的摘要：")
    print("-" * 40)

    for max_len in [30, 50, 100]:
        summary = summarize_text(LONG_NEWS, max_words=max_len, style="简洁")
        print(f"\n【{max_len}字以内】")
        print(f"  {summary}")
        print(f"  实际字数：{len(summary)}")

    # 结构化摘要
    print("\n" + "=" * 60)
    print("3. 结构化摘要（标题 + 一句话 + 详细）：")
    print("-" * 40)

    structured = summarize_with_structure(LONG_NEWS)
    print(f"  标题：{structured['title']}")
    print(f"  一句话：{structured['one_liner']}")
    print(f"  详细：{structured['detail']}")


if __name__ == "__main__":
    main()

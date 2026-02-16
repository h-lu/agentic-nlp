#!/usr/bin/env python3
"""
02_classification.py - 文本分类示例

本示例展示如何使用 LLM 进行文本分类：
- 新闻分类（体育/财经/科技/娱乐）
- 使用贯穿案例中的新闻文本
- 可复用的分类函数

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

from typing import Literal
from openai import OpenAI


# 定义新闻类别（使用 Literal 类型进行类型约束）
NewsCategory = Literal["财经", "体育", "科技", "娱乐", "教育", "健康"]


def classify_news(text: str, categories: list[NewsCategory] | None = None) -> str:
    """
    使用 LLM 对新闻进行分类。

    Args:
        text: 新闻文本内容
        categories: 可选的分类类别列表，默认为财经/体育/科技/娱乐/教育/健康

    Returns:
        分类结果（类别名称）

    Example:
        >>> news = "苹果公司发布新款 iPhone，搭载 A18 芯片"
        >>> classify_news(news)
        '科技'
    """
    if categories is None:
        categories = ["财经", "体育", "科技", "娱乐", "教育", "健康"]

    client = OpenAI()

    # 构建 system message，明确分类任务和可选类别
    system_prompt = f"""你是一个新闻分类助手。请将新闻分类到以下类别之一：
{', '.join(categories)}

要求：
1. 只输出类别名称，不要解释
2. 如果不确定，选择最接近的类别
3. 不要输出任何其他内容"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0,  # 分类任务使用 temperature=0 确保结果稳定
    )

    return completion.choices[0].message.content or ""


def classify_batch(
    texts: list[str],
    categories: list[NewsCategory] | None = None
) -> list[str]:
    """
    批量分类新闻文本。

    Args:
        texts: 新闻文本列表
        categories: 可选的分类类别列表

    Returns:
        分类结果列表（与输入列表一一对应）
    """
    results = []
    for text in texts:
        category = classify_news(text, categories)
        results.append(category)
    return results


# 示例新闻数据（贯穿案例中使用）
SAMPLE_NEWS = {
    "finance": """
    苹果公司今天发布了 2025 财年第一季度财报。财报显示，公司营收达到 1243 亿美元，
    同比增长 4%。iPhone 业务贡献了 697 亿美元收入，超出分析师预期。苹果 CEO 蒂姆·库克
    表示，对中国市场的发展势头感到乐观。财报发布后，苹果股价在盘后交易中上涨 2.3%。
    """,

    "sports": """
    中国女排在今晚的世界女排联赛中以 3:1 战胜巴西队，取得三连胜。朱婷砍下全场最高的
    26 分，李盈莹贡献 18 分。主教练蔡斌赛后表示，球队在关键分的把握上做得很好。
    下一场比赛将对阵意大利队。
    """,

    "tech": """
    华为今日正式发布鸿蒙 HarmonyOS 5.0 系统。新系统在性能、安全性和跨设备协同方面
    都有显著提升。据华为消费者业务 CEO 余承东介绍，新系统的启动速度提升了 20%，
    续航时间延长了 15%。目前已有超过 5000 款应用适配鸿蒙生态。
    """,

    "entertainment": """
    电影《流浪地球 3》今日官宣定档 2026 年春节档。导演郭帆透露，第三部将延续前作的
    世界观，但会有全新的故事线和角色。刘德华、吴京确认回归主演。首支预告片预计
    今年年底发布。
    """,

    "education": """
    教育部今日发布通知，2025 年全国硕士研究生招生考试报名人数达到 438 万人，
    同比增长 3.2%。其中，报考人工智能、大数据等新兴专业的考生比例显著上升。
    专家建议考生理性选择报考院校和专业。
    """,

    "health": """
    国家卫健委今日通报，我国自主研发的新型 mRNA 疫苗已完成三期临床试验，
    有效率达到 92%。该疫苗对变异株也显示出良好的保护效果。预计将在下月获批
    上市，届时将优先为老年人和基础疾病患者接种。
    """,
}


def main() -> None:
    """主函数：演示新闻分类功能"""
    print("=" * 60)
    print("示例：使用 LLM 进行新闻分类")
    print("=" * 60)

    # 单条新闻分类
    print("\n1. 单条新闻分类：")
    print("-" * 40)

    for category_name, news in SAMPLE_NEWS.items():
        print(f"\n原文（{category_name}类）：")
        print(f"  {news.strip()[:50]}...")

        result = classify_news(news)
        print(f"  -> 分类结果：{result}")

    # 批量分类
    print("\n" + "=" * 60)
    print("2. 批量分类：")
    print("-" * 40)

    news_list = list(SAMPLE_NEWS.values())
    expected_categories = list(SAMPLE_NEWS.keys())

    results = classify_batch(news_list)

    for expected, result in zip(expected_categories, results):
        match = "ok" if expected.lower() in result.lower() else "mismatch"
        print(f"  期望：{expected:12} -> 结果：{result:8} [{match}]")

    # 自定义分类类别
    print("\n" + "=" * 60)
    print("3. 自定义分类类别：")
    print("-" * 40)

    custom_news = "特斯拉宣布全系车型降价 2 万元，Model 3 起售价降至 22.99 万元"
    custom_categories = ["汽车", "房产", "金融", "其他"]

    result = classify_news(custom_news, custom_categories)  # type: ignore
    print(f"新闻：{custom_news}")
    print(f"自定义类别：{custom_categories}")
    print(f"分类结果：{result}")


if __name__ == "__main__":
    main()

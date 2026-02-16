#!/usr/bin/env python3
"""
04_extraction.py - 实体抽取示例

本示例展示如何使用 LLM 进行实体抽取：
- 抽取人名、地名、机构名等实体
- 使用 JSON 输出格式
- 结构化的实体抽取结果

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

import json
from typing import Any
from openai import OpenAI


def extract_entities(text: str, entity_types: list[str] | None = None) -> dict[str, list[str]]:
    """
    从文本中抽取指定类型的实体。

    Args:
        text: 需要抽取实体的文本
        entity_types: 需要抽取的实体类型列表
                     默认为 ["公司", "人名", "产品", "地点", "数字指标"]

    Returns:
        字典，键为实体类型，值为该类型的实体列表

    Example:
        >>> text = "苹果公司 CEO 蒂姆·库克宣布 iPhone 15 销量突破 2 亿台"
        >>> extract_entities(text)
        {'公司': ['苹果公司'], '人名': ['蒂姆·库克'], '产品': ['iPhone 15'], ...}
    """
    if entity_types is None:
        entity_types = ["公司", "人名", "产品", "地点", "数字指标"]

    client = OpenAI()

    # 构建 JSON Schema 格式的 system prompt
    system_prompt = f"""你是一个实体抽取助手。请从文本中抽取以下类型的实体：
{', '.join(entity_types)}

请严格按照以下 JSON 格式输出：
{{
    "公司": ["公司名称1", "公司名称2"],
    "人名": ["人名1", "人名2"],
    "产品": ["产品名1"],
    "地点": ["地点1", "地点2"],
    "数字指标": ["数字和指标1", "数字和指标2"]
}}

要求：
1. 如果某类实体不存在，输出空列表 []
2. 只输出 JSON，不要有任何其他内容
3. 不要添加解释或注释
4. 数字指标应包含具体数值和单位（如"1243亿美元"、"同比增长4%"）"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0,
    )

    # 解析 JSON 响应
    result_text = completion.choices[0].message.content or "{}"

    try:
        return json.loads(result_text)
    except json.JSONDecodeError as e:
        print(f"[警告] JSON 解析失败：{e}")
        print(f"原始响应：{result_text}")
        return {entity_type: [] for entity_type in entity_types}


def extract_with_confidence(text: str, entity_types: list[str]) -> dict[str, list[dict[str, Any]]]:
    """
    抽取实体并附带置信度信息。

    Args:
        text: 需要抽取实体的文本
        entity_types: 需要抽取的实体类型列表

    Returns:
        字典，键为实体类型，值为包含实体和置信度的字典列表
    """
    client = OpenAI()

    system_prompt = f"""你是一个实体抽取助手。请从文本中抽取以下类型的实体：
{', '.join(entity_types)}

请严格按照以下 JSON 格式输出：
{{
    "实体类型": [
        {{"entity": "实体名称", "confidence": 0.95, "context": "原文中出现该实体的上下文"}}
    ]
}}

要求：
1. confidence 表示对抽取结果的置信度，范围 0-1
2. context 是实体在原文中的上下文片段
3. 只输出 JSON"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0,
    )

    result_text = completion.choices[0].message.content or "{}"

    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {entity_type: [] for entity_type in entity_types}


def extract_relations(text: str) -> list[dict[str, str]]:
    """
    抽取实体之间的关系。

    Args:
        text: 需要抽取关系的文本

    Returns:
        关系列表，每个关系包含 subject（主体）、predicate（谓语）、object（客体）
    """
    client = OpenAI()

    system_prompt = """你是一个关系抽取助手。请从文本中抽取实体之间的关系。

请严格按照以下 JSON 格式输出：
{
    "relations": [
        {"subject": "主体", "predicate": "关系", "object": "客体"}
    ]
}

例如：
- "苹果公司 CEO 蒂姆·库克" -> {"subject": "蒂姆·库克", "predicate": "是...的CEO", "object": "苹果公司"}
- "iPhone 15 售价 5999 元" -> {"subject": "iPhone 15", "predicate": "售价", "object": "5999元"}

只输出 JSON，不要其他内容。"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0,
    )

    result_text = completion.choices[0].message.content or '{"relations": []}'

    try:
        data = json.loads(result_text)
        return data.get("relations", [])
    except json.JSONDecodeError:
        return []


# 示例新闻
SAMPLE_TEXTS = {
    "apple_report": """
    苹果公司今天发布了 2025 财年第一季度财报。财报显示，公司营收达到 1243 亿美元，
    同比增长 4%。iPhone 业务贡献了 697 亿美元收入，超出分析师预期。苹果 CEO 蒂姆·库克
    表示，对中国市场的发展势头感到乐观。财报发布后，苹果股价在盘后交易中上涨 2.3%。
    """,

    "tech_launch": """
    特斯拉 CEO 埃隆·马斯克在今日的发布会上宣布，Model 3 全系降价 2 万元，起售价
    调整为 22.99 万元。同时，特斯拉上海超级工厂的年产能已提升至 100 万辆。
    摩根士丹利分析师亚当·乔纳斯表示，这次降价将进一步巩固特斯拉在中国市场的地位。
    """,

    "sports_news": """
    中国女排在今晚的世界女排联赛中以 3:1 战胜巴西队，取得三连胜。朱婷砍下全场最高的
    26 分，李盈莹贡献 18 分。主教练蔡斌赛后表示，球队在关键分的把握上做得很好。
    比赛在澳门银河综艺馆举行，现场观众超过 1 万人。
    """,
}


def main() -> None:
    """主函数：演示实体抽取功能"""
    print("=" * 60)
    print("示例：使用 LLM 进行实体抽取")
    print("=" * 60)

    # 基础实体抽取
    print("\n1. 基础实体抽取：")
    print("-" * 40)

    for name, text in SAMPLE_TEXTS.items():
        print(f"\n【{name}】")
        print(f"原文：{text.strip()[:60]}...")

        entities = extract_entities(text)

        for entity_type, entity_list in entities.items():
            if entity_list:
                print(f"  {entity_type}：{entity_list}")

    # 带置信度的实体抽取
    print("\n" + "=" * 60)
    print("2. 带置信度的实体抽取：")
    print("-" * 40)

    text = SAMPLE_TEXTS["apple_report"]
    result = extract_with_confidence(
        text,
        ["公司", "人名", "产品", "地点"]
    )

    for entity_type, entities in result.items():
        if entities:
            print(f"\n{entity_type}：")
            for item in entities:
                print(f"  - {item.get('entity', 'N/A')} (置信度: {item.get('confidence', 'N/A')})")

    # 关系抽取
    print("\n" + "=" * 60)
    print("3. 实体关系抽取：")
    print("-" * 40)

    for name, text in SAMPLE_TEXTS.items():
        print(f"\n【{name}】")
        relations = extract_relations(text)

        for rel in relations:
            print(f"  {rel.get('subject', '?')} -> {rel.get('predicate', '?')} -> {rel.get('object', '?')}")

    # 自定义实体类型
    print("\n" + "=" * 60)
    print("4. 自定义实体类型抽取：")
    print("-" * 40)

    custom_types = ["时间", "金额", "百分比", "产品型号"]
    text = SAMPLE_TEXTS["apple_report"]

    print(f"自定义类型：{custom_types}")
    print(f"原文：{text.strip()[:60]}...")

    entities = extract_entities(text, entity_types=custom_types)

    for entity_type, entity_list in entities.items():
        print(f"  {entity_type}：{entity_list}")


if __name__ == "__main__":
    main()

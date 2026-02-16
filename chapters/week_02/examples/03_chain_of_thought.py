#!/usr/bin/env python3
"""
03_chain_of_thought.py - Chain-of-Thought 思维链推理

本示例展示 Chain-of-Thought (CoT) 的核心概念和实现：
- Zero-shot vs CoT 的效果对比
- 显式步骤提示 vs 零样本 CoT
- 处理模糊/边界情况
- CoT 的适用场景和成本权衡

CoT 的核心思想：
让 LLM 把推理过程写出来，而不是直接跳到结论。
这就像让人"写出草稿"而不是"口算答案"——减少出错。

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# Part 1: CoT 配置和数据结构
# ============================================================================

class CoTStyle(str, Enum):
    """CoT 风格"""
    ZERO_SHOT = "zero_shot"  # 不使用 CoT
    EXPLICIT = "explicit"  # 显式步骤提示
    MAGIC = "magic"  # 魔法咒语 "Let's think step by step"


@dataclass
class CoTConfig:
    """CoT 配置"""
    style: CoTStyle = CoTStyle.ZERO_SHOT
    steps: list[str] = field(default_factory=list)  # 显式步骤
    show_reasoning: bool = True  # 是否在输出中显示推理过程


# 预设的 CoT 步骤模板
COT_STEP_TEMPLATES = {
    "ticket_classification": [
        "用户遇到了什么问题？",
        "问题的核心诉求是什么？",
        "用户的情绪状态如何？",
        "哪个部门最适合处理这个诉求？",
        "最终分类结果是什么？",
    ],
    "ambiguous_classification": [
        "文本中提到了哪些关键信息？",
        "这些信息分别指向哪些可能的类别？",
        "哪个类别的证据更强？",
        "最终分类结果是什么？",
    ],
    "sentiment_analysis": [
        "文本中的情感词汇有哪些？",
        "正面和负面词汇的比例如何？",
        "整体情感倾向是什么？",
        "最终情感分类结果是什么？",
    ],
    "math_reasoning": [
        "问题问的是什么？",
        "已知条件有哪些？",
        "需要计算什么？",
        "计算过程是什么？",
        "最终答案是什么？",
    ],
}


# ============================================================================
# Part 2: CoT Prompt 构建器
# ============================================================================

class CoTPromptBuilder:
    """
    Chain-of-Thought Prompt 构建器。

    支持三种 CoT 风格：
    1. ZERO_SHOT: 不使用 CoT，直接要求答案
    2. EXPLICIT: 显式列出思考步骤
    3. MAGIC: 使用 "Let's think step by step" 魔法咒语
    """

    MAGIC_PHRASES = [
        "Let's think step by step.",
        "让我们一步一步思考。",
        "请一步步分析这个问题。",
    ]

    def __init__(
        self,
        role: str,
        task: str,
        categories: list[str],
        cot_style: CoTStyle = CoTStyle.ZERO_SHOT,
        cot_steps: Optional[list[str]] = None,
    ):
        self.role = role
        self.task = task
        self.categories = categories
        self.cot_style = cot_style
        self.cot_steps = cot_steps or COT_STEP_TEMPLATES.get("ambiguous_classification", [])

    def build(self, input_text: str) -> str:
        """构建完整的 CoT Prompt"""
        parts = [f"角色：你是一个{self.role}。"]

        # 根据 CoT 风格添加不同的提示
        if self.cot_style == CoTStyle.EXPLICIT:
            parts.append(f"\n任务：{self.task}")
            parts.append("\n请按以下步骤思考：")
            for i, step in enumerate(self.cot_steps, 1):
                parts.append(f"{i}. {step}")
            parts.append("\n最后输出最终结果。")

        elif self.cot_style == CoTStyle.MAGIC:
            parts.append(f"\n任务：{self.task}")
            parts.append(f"\n{self.MAGIC_PHRASES[1]}")  # 中文版本

        else:  # ZERO_SHOT
            parts.append(f"\n任务：{self.task}")
            parts.append("\n直接输出结果，不需要解释。")

        # 添加格式约束
        parts.append(f"\n格式：从以下选项中选一个：{', '.join(self.categories)}")

        # 添加输入
        parts.append(f"\n输入：{input_text}")

        return "\n".join(parts)

    def build_with_few_shot(
        self,
        input_text: str,
        examples: list[dict],
        show_reasoning: bool = True
    ) -> str:
        """
        构建 Few-shot + CoT 的 Prompt。

        Args:
            input_text: 输入文本
            examples: Few-shot 示例，每个示例包含 input, reasoning, output
            show_reasoning: 是否在示例中显示推理过程
        """
        parts = [f"角色：你是一个{self.role}。"]

        # 添加 Few-shot 示例
        if examples:
            parts.append("\n示例：")
            for ex in examples:
                parts.append(f"\n输入：\"{ex['input']}\"")
                if show_reasoning and 'reasoning' in ex:
                    parts.append(f"\n分析：\n{ex['reasoning']}")
                parts.append(f"\n输出：{ex['output']}")
            parts.append("")

        # 添加任务
        parts.append(f"任务：{self.task}")

        # 添加 CoT 提示
        if self.cot_style == CoTStyle.EXPLICIT:
            parts.append("\n请按以下步骤思考：")
            for i, step in enumerate(self.cot_steps, 1):
                parts.append(f"{i}. {step}")

        # 添加格式
        parts.append(f"\n格式：从以下选项中选一个：{', '.join(self.categories)}")

        # 添加输入
        parts.append(f"\n输入：{input_text}")

        return "\n".join(parts)


# ============================================================================
# Part 3: 模糊分类示例（展示 CoT 的价值）
# ============================================================================

# 模糊的客服工单示例（需要推理才能正确分类）
AMBIGUOUS_TICKETS = [
    {
        "id": 1,
        "text": "我用你们 App 充值了会员，但是显示还是普通用户，而且客服一直没人接，我已经等了 20 分钟了，再不解决我就要投诉了！",
        "correct_category": "账务问题",  # 核心问题是充值，不是投诉
        "reasoning": """
1. 用户遇到的问题：充值后会员状态未更新，客服响应慢
2. 核心诉求：会员权益问题需要解决
3. 用户情绪：焦虑、不满，但仍在寻求解决方案
4. 最适合的部门：账务问题（核心是充值和会员状态）
5. 最终分类：账务问题（建议标记为高优先级处理）""",
    },
    {
        "id": 2,
        "text": "你们这个新版本太难用了，登录按钮我都找不到，而且还经常闪退，能不能改回去？",
        "correct_category": "功能建议",  # 包含投诉但核心是产品反馈
        "reasoning": """
1. 用户遇到的问题：新版 UI 难用，登录按钮难找，有闪退问题
2. 核心诉求：希望改进产品体验
3. 用户情绪：抱怨，但表达了具体改进意见
4. 最适合的部门：功能建议（用户在反馈产品问题）
5. 最终分类：功能建议（闪退问题可转技术支持）""",
    },
    {
        "id": 3,
        "text": "我上周反馈的 Bug 还没修复，今天又遇到一样的问题，严重影响我工作，你们到底什么时候能修好？",
        "correct_category": "技术支持",  # 核心是 Bug 未修复
        "reasoning": """
1. 用户遇到的问题：之前反馈的 Bug 未修复，再次遇到
2. 核心诉求：技术问题需要解决
3. 用户情绪：不满、急躁
4. 最适合的部门：技术支持（这是技术 Bug 问题）
5. 最终分类：技术支持（建议优先处理）""",
    },
]


# ============================================================================
# Part 4: CoT 输出解析
# ============================================================================

class CoTOutput(BaseModel):
    """CoT 输出的结构化模型"""
    reasoning: str = Field(description="推理过程")
    conclusion: str = Field(description="最终结论")


def parse_cot_output(raw_output: str) -> CoTOutput:
    """
    解析 CoT 输出。

    尝试从输出中分离推理过程和最终结论。
    """
    lines = raw_output.strip().split('\n')

    # 尝试找到"最终"或"结论"相关的行
    conclusion_markers = ["最终", "结论", "结果", "答案", "输出"]
    conclusion_idx = -1

    for i, line in enumerate(lines):
        if any(marker in line for marker in conclusion_markers):
            conclusion_idx = i
            break

    if conclusion_idx >= 0:
        reasoning = '\n'.join(lines[:conclusion_idx])
        conclusion = lines[conclusion_idx]
        # 清理结论行
        for marker in conclusion_markers:
            conclusion = conclusion.replace(marker, "").replace("：", "").replace(":", "")
        conclusion = conclusion.strip()
    else:
        # 如果找不到标记，假设最后一行是结论
        reasoning = '\n'.join(lines[:-1])
        conclusion = lines[-1].strip()

    return CoTOutput(reasoning=reasoning, conclusion=conclusion)


def extract_final_category(output: str, categories: list[str]) -> str:
    """
    从 CoT 输出中提取最终分类结果。

    Args:
        output: LLM 的原始输出
        categories: 可能的类别列表

    Returns:
        提取的类别（如果找不到则返回原始输出的最后一行）
    """
    # 尝试在输出中找到类别
    for category in categories:
        if category in output:
            # 找到最后一次出现的位置（通常在结论部分）
            lines = output.split('\n')
            for line in reversed(lines):
                if category in line:
                    return category

    # 如果找不到，返回最后一行
    return output.strip().split('\n')[-1].strip()


# ============================================================================
# Part 5: CoT vs Non-CoT 对比
# ============================================================================

def build_non_cot_prompt(input_text: str, categories: list[str]) -> str:
    """构建不使用 CoT 的 Prompt"""
    return f"""角色：你是一个客服工单分类助手。

任务：判断以下工单应该分到哪个部门。

约束：
- 只输出部门名称
- 不要解释原因

格式：从以下选项中选一个：{', '.join(categories)}

工单内容：{input_text}"""


def build_cot_prompt(input_text: str, categories: list[str]) -> str:
    """构建使用 CoT 的 Prompt"""
    return f"""角色：你是一个客服工单分类助手。

任务：判断以下工单应该分到哪个部门。

请按以下步骤思考：
1. 用户遇到了什么问题？
2. 问题的核心诉求是什么？
3. 用户的情绪状态如何？
4. 哪个部门最适合处理这个诉求？
5. 最终分类结果是什么？

格式：从以下选项中选一个：{', '.join(categories)}

工单内容：{input_text}

请分析后输出最终分类结果。"""


def build_few_shot_cot_prompt(
    input_text: str,
    categories: list[str],
    examples: list[dict]
) -> str:
    """构建 Few-shot + CoT 的 Prompt"""
    examples_text = ""
    for ex in examples:
        examples_text += f"""
输入："{ex['input']}"
分析：
{ex['reasoning']}
输出：{ex['output']}

"""

    return f"""角色：你是一个客服工单分类助手。

示例：
{examples_text}
任务：判断以下工单应该分到哪个部门。

请按以下步骤思考：
1. 用户遇到了什么问题？
2. 问题的核心诉求是什么？
3. 哪个部门最适合处理这个诉求？
4. 最终分类结果是什么？

格式：从以下选项中选一个：{', '.join(categories)}

工单内容：{input_text}

请分析后输出最终分类结果。"""


# ============================================================================
# Part 6: 演示函数
# ============================================================================

def demo_cot_styles() -> None:
    """演示不同的 CoT 风格"""
    print("=" * 60)
    print("CoT 风格对比")
    print("=" * 60)

    input_text = "特斯拉发布新款电动车，续航里程突破 1000 公里"
    categories = ["财经", "科技", "体育", "娱乐"]

    # 1. Zero-shot（不使用 CoT）
    print("\n【1. Zero-shot（无 CoT）】")
    print("-" * 40)
    builder = CoTPromptBuilder(
        role="新闻分类助手",
        task="判断以下新闻属于哪个类别",
        categories=categories,
        cot_style=CoTStyle.ZERO_SHOT
    )
    print(builder.build(input_text))

    # 2. 显式步骤 CoT
    print("\n【2. 显式步骤 CoT】")
    print("-" * 40)
    builder = CoTPromptBuilder(
        role="新闻分类助手",
        task="判断以下新闻属于哪个类别",
        categories=categories,
        cot_style=CoTStyle.EXPLICIT,
        cot_steps=COT_STEP_TEMPLATES["ambiguous_classification"]
    )
    print(builder.build(input_text))

    # 3. 魔法咒语 CoT
    print("\n【3. 魔法咒语 CoT】")
    print("-" * 40)
    builder = CoTPromptBuilder(
        role="新闻分类助手",
        task="判断以下新闻属于哪个类别",
        categories=categories,
        cot_style=CoTStyle.MAGIC
    )
    print(builder.build(input_text))


def demo_ambiguous_classification() -> None:
    """演示模糊分类（展示 CoT 的价值）"""
    print("\n" + "=" * 60)
    print("模糊分类：为什么需要 CoT？")
    print("=" * 60)

    categories = ["技术支持", "账务问题", "功能建议", "投诉", "其他"]

    for ticket in AMBIGUOUS_TICKETS:
        print(f"\n【工单 {ticket['id']}】")
        print(f"内容：{ticket['text'][:50]}...")
        print(f"正确分类：{ticket['correct_category']}")
        print(f"\n推理过程：{ticket['reasoning'][:200]}...")


def demo_cot_parsing() -> None:
    """演示 CoT 输出解析"""
    print("\n" + "=" * 60)
    print("CoT 输出解析")
    print("=" * 60)

    # 模拟 LLM 输出
    mock_outputs = [
        """1. 用户遇到的问题：充值后会员状态未更新，客服响应慢
2. 核心诉求：会员权益问题需要解决
3. 最适合的部门：账务问题（核心是充值和会员状态）
4. 最终分类：账务问题""",
        """让我一步步分析：
- 文本提到"充值"和"会员"，这是账务相关
- 虽然用户说"要投诉"，但核心诉求是解决充值问题
- 结论：账务问题""",
    ]

    categories = ["技术支持", "账务问题", "功能建议", "投诉", "其他"]

    for i, output in enumerate(mock_outputs, 1):
        print(f"\n【模拟输出 {i}】")
        print("-" * 40)
        print(output)

        parsed = parse_cot_output(output)
        print(f"\n解析结果：")
        print(f"  推理过程: {parsed.reasoning[:50]}...")
        print(f"  结论: {parsed.conclusion}")

        extracted = extract_final_category(output, categories)
        print(f"  提取类别: {extracted}")


def demo_cot_applicability() -> None:
    """演示 CoT 的适用场景"""
    print("\n" + "=" * 60)
    print("CoT 适用场景")
    print("=" * 60)

    suitable = [
        ("多步推理任务", "数学问题、逻辑推理、复杂分类"),
        ("边界模糊的输入", "可能有多种解释的情况"),
        ("需要可解释性", "你要知道'为什么是这个答案'"),
        ("高风险决策", "医疗、金融等需要解释的场景"),
    ]

    not_suitable = [
        ("简单明确的任务", "直接分类就够了，CoT 反而增加延迟"),
        ("对延迟敏感", "生成推理过程需要更多时间"),
        ("不需要解释", "只要答案，不需要过程"),
        ("成本敏感", "CoT 会显著增加 Token 消耗"),
    ]

    print("\n【适合使用 CoT】")
    for title, desc in suitable:
        print(f"  ✓ {title}：{desc}")

    print("\n【不适合使用 CoT】")
    for title, desc in not_suitable:
        print(f"  ✗ {title}：{desc}")


def demo_cot_cost_analysis() -> None:
    """演示 CoT 的成本分析"""
    print("\n" + "=" * 60)
    print("CoT 成本分析")
    print("=" * 60)

    # 假设的 Token 数量
    scenarios = [
        ("简单分类（无 CoT）", 150, 2),
        ("简单分类 + CoT", 150, 50),
        ("复杂工单（无 CoT）", 300, 2),
        ("复杂工单 + CoT", 300, 150),
    ]

    # gpt-4o-mini 定价（美元/百万 Token）
    input_price = 0.15
    output_price = 0.60

    print("\n【单次调用成本对比（gpt-4o-mini）】")
    print(f"{'场景':<25} {'输入':>10} {'输出':>10} {'成本':>12}")
    print("-" * 60)

    for scenario, input_tokens, output_tokens in scenarios:
        cost = (input_tokens / 1_000_000 * input_price +
                output_tokens / 1_000_000 * output_price) * 100  # 转换为 cents
        print(f"{scenario:<25} {input_tokens:>10} {output_tokens:>10} ${cost:>10.4f}")

    # 大规模处理
    print("\n【大规模处理成本（10000 次调用）】")
    print(f"{'方法':<20} {'成本':>15}")
    print("-" * 40)

    # 无 CoT
    cost_no_cot = 10000 * (300 / 1_000_000 * input_price + 2 / 1_000_000 * output_price)
    print(f"{'无 CoT':<20} ${cost_no_cot:>14.2f}")

    # 有 CoT
    cost_with_cot = 10000 * (300 / 1_000_000 * input_price + 150 / 1_000_000 * output_price)
    print(f"{'有 CoT':<20} ${cost_with_cot:>14.2f}")

    print(f"\n成本差异：${cost_with_cot - cost_no_cot:.2f}（{(cost_with_cot / cost_no_cot - 1) * 100:.0f}% 增加）")

    # 建议
    print("\n【老潘的建议】")
    print("  '在公司里，我们会对高价值工单用 CoT——比如 VIP 用户、")
    print("  涉及金额大的投诉。简单明确的工单用快速分类，不需要想太多。")
    print("  不是一刀切，而是分级处理。'")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("Chain-of-Thought 思维链演示")
    print("=" * 60)

    # 1. CoT 风格对比
    demo_cot_styles()

    # 2. 模糊分类
    demo_ambiguous_classification()

    # 3. 输出解析
    demo_cot_parsing()

    # 4. 适用场景
    demo_cot_applicability()

    # 5. 成本分析
    demo_cot_cost_analysis()


if __name__ == "__main__":
    main()

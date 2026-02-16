#!/usr/bin/env python3
"""
02_few_shot.py - Few-shot Learning 示例

本示例展示 Few-shot Learning 的核心概念和实现：
- 通过示例引导 LLM 输出格式
- 动态示例选择策略
- YAML 配置文件管理示例
- Few-shot 与 Zero-shot 的效果对比

Few-shot 的核心思想：
与其用文字描述"你要怎么做"，不如直接给它看几个"输入-输出"的例子。
LLM 有很强的模式匹配能力，看到几个例子后就能"猜"出你想要的格式。

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

import os
import yaml
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from pathlib import Path
from pydantic import BaseModel, Field


# ============================================================================
# Part 1: Few-shot 示例数据结构
# ============================================================================

@dataclass
class FewShotExample:
    """单个 Few-shot 示例"""
    input: str
    output: str
    category: Optional[str] = None  # 用于分类任务
    metadata: dict = field(default_factory=dict)  # 额外元数据

    def to_prompt_format(self, input_label: str = "输入", output_label: str = "输出") -> str:
        """转换为 Prompt 中的格式"""
        return f'{input_label}："{self.input}"\n{output_label}：{self.output}'


class FewShotExampleCollection(BaseModel):
    """Few-shot 示例集合（支持 Pydantic 验证）"""
    task_type: str = Field(description="任务类型：classify, summarize, extract 等")
    examples: list[FewShotExample] = Field(default_factory=list, description="示例列表")
    version: str = Field(default="1.0", description="版本号")

    def get_examples_by_category(self, category: str) -> list[FewShotExample]:
        """按类别筛选示例"""
        return [ex for ex in self.examples if ex.category == category]

    def get_random_examples(self, n: int = 3, seed: int = 42) -> list[FewShotExample]:
        """随机选择 n 个示例"""
        import random
        random.seed(seed)
        return random.sample(self.examples, min(n, len(self.examples)))

    def format_for_prompt(self, examples: Optional[list[FewShotExample]] = None) -> str:
        """格式化为 Prompt 片段"""
        examples = examples or self.examples
        lines = ["示例："]
        for ex in examples:
            lines.append(f"输入：\"{ex.input}\"")
            lines.append(f"输出：{ex.output}")
            lines.append("")  # 空行分隔
        return "\n".join(lines)


# ============================================================================
# Part 2: YAML 配置文件管理
# ============================================================================

# 默认示例配置（实际项目中会放在单独的 YAML 文件中）
DEFAULT_CLASSIFY_EXAMPLES = """
task_type: classify
version: "1.0"
examples:
  - input: "苹果公司发布新款 iPhone，搭载 A18 芯片"
    output: "科技"
    category: "科技"
  - input: "中国男篮在亚运会决赛中战胜韩国队"
    output: "体育"
    category: "体育"
  - input: "央行宣布下调存款准备金率 0.5 个百分点"
    output: "财经"
    category: "财经"
  - input: "某知名演员宣布结婚消息"
    output: "娱乐"
    category: "娱乐"
  - input: "特斯拉股价单日大涨 8%，创历史新高"
    output: "财经"
    category: "财经"
  - input: "世界杯预选赛中国队战平日本队"
    output: "体育"
    category: "体育"
  - input: "OpenAI 发布 GPT-5 模型"
    output: "科技"
    category: "科技"
  - input: "某歌手新专辑销量破百万"
    output: "娱乐"
    category: "娱乐"
"""

DEFAULT_EXTRACT_EXAMPLES = """
task_type: extract
version: "1.0"
examples:
  - input: "苹果公司 CEO 蒂姆·库克今天在北京发布了新款 iPhone"
    output: '{"companies": ["苹果公司"], "people": ["蒂姆·库克"], "locations": ["北京"], "products": ["iPhone"]}'
    category: "entity_extraction"
  - input: "马斯克宣布特斯拉将在上海建设新工厂"
    output: '{"companies": ["特斯拉"], "people": ["马斯克"], "locations": ["上海"], "products": []}'
    category: "entity_extraction"
"""


class FewShotManager:
    """
    Few-shot 示例管理器。

    功能：
    - 从 YAML 文件加载示例
    - 动态选择示例（按类别、随机、相似度）
    - 格式化示例为 Prompt 片段

    Example:
        >>> manager = FewShotManager.from_yaml("examples.yaml")
        >>> examples = manager.get_examples(n=3)
        >>> prompt = manager.format_examples(examples)
    """

    def __init__(self, collection: FewShotExampleCollection):
        self.collection = collection

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "FewShotManager":
        """从 YAML 文件加载示例"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 转换为 Pydantic 模型
        examples = [
            FewShotExample(**ex) if isinstance(ex, dict) else ex
            for ex in data.get('examples', [])
        ]
        collection = FewShotExampleCollection(
            task_type=data.get('task_type', 'unknown'),
            examples=examples,
            version=data.get('version', '1.0')
        )
        return cls(collection)

    @classmethod
    def from_yaml_string(cls, yaml_string: str) -> "FewShotManager":
        """从 YAML 字符串加载示例"""
        data = yaml.safe_load(yaml_string)
        examples = [
            FewShotExample(**ex) if isinstance(ex, dict) else ex
            for ex in data.get('examples', [])
        ]
        collection = FewShotExampleCollection(
            task_type=data.get('task_type', 'unknown'),
            examples=examples,
            version=data.get('version', '1.0')
        )
        return cls(collection)

    def get_examples(
        self,
        n: int = 3,
        strategy: Literal["random", "balanced", "similar"] = "balanced",
        category: Optional[str] = None,
        seed: int = 42
    ) -> list[FewShotExample]:
        """
        获取示例。

        Args:
            n: 返回的示例数量
            strategy: 选择策略
                - random: 随机选择
                - balanced: 平衡各类别（优先选择）
                - similar: 相似度选择（需要实现）
            category: 限定类别（可选）
            seed: 随机种子

        Returns:
            选中的示例列表
        """
        import random
        random.seed(seed)

        # 按类别筛选
        candidates = self.collection.examples
        if category:
            candidates = [ex for ex in candidates if ex.category == category]

        if strategy == "random":
            return random.sample(candidates, min(n, len(candidates)))

        elif strategy == "balanced":
            # 平衡各类别：每个类别选一个，然后随机填充
            categories = {}
            for ex in candidates:
                cat = ex.category or "default"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(ex)

            result = []
            # 先从每个类别选一个
            for cat, examples in categories.items():
                if examples and len(result) < n:
                    result.append(random.choice(examples))

            # 如果还不够，随机填充
            remaining = n - len(result)
            if remaining > 0:
                available = [ex for ex in candidates if ex not in result]
                result.extend(random.sample(available, min(remaining, len(available))))

            return result[:n]

        else:  # similar
            # 简化版：实际应用中可以用 embedding 相似度
            return random.sample(candidates, min(n, len(candidates)))

    def format_examples(self, examples: list[FewShotExample]) -> str:
        """将示例格式化为 Prompt 片段"""
        return self.collection.format_for_prompt(examples)

    def inject_into_prompt(
        self,
        base_prompt: str,
        examples: list[FewShotExample],
        position: Literal["before_task", "after_task"] = "before_task"
    ) -> str:
        """
        将示例注入到 Prompt 中。

        Args:
            base_prompt: 基础 Prompt 模板
            examples: 要注入的示例
            position: 注入位置

        Returns:
            包含示例的完整 Prompt
        """
        examples_text = self.format_examples(examples)

        if position == "before_task":
            return f"{examples_text}\n{base_prompt}"
        else:
            # 在任务描述后、输入前插入
            lines = base_prompt.split('\n')
            # 找到"任务："行的位置
            task_idx = next(
                (i for i, line in enumerate(lines) if line.startswith("任务：")),
                len(lines)
            )
            lines.insert(task_idx + 1, f"\n{examples_text}")
            return '\n'.join(lines)


# ============================================================================
# Part 3: Zero-shot vs Few-shot 对比
# ============================================================================

def build_zero_shot_prompt(input_text: str, categories: list[str]) -> str:
    """构建 Zero-shot Prompt（无示例）"""
    return f"""角色：你是一个新闻分类助手。

任务：判断以下新闻属于哪个类别。

约束：
- 只输出类别名称
- 不要解释原因

格式：从以下选项中选一个：{', '.join(categories)}

新闻内容：{input_text}"""


def build_few_shot_prompt(
    input_text: str,
    categories: list[str],
    examples: list[FewShotExample]
) -> str:
    """构建 Few-shot Prompt（包含示例）"""
    # 格式化示例
    examples_text = "\n".join([
        f"输入：\"{ex.input}\"\n输出：{ex.output}\n"
        for ex in examples
    ])

    return f"""角色：你是一个新闻分类助手。

示例：
{examples_text}
任务：判断以下新闻属于哪个类别。

约束：
- 只输出类别名称
- 格式与示例一致

格式：从以下选项中选一个：{', '.join(categories)}

新闻内容：{input_text}"""


# ============================================================================
# Part 4: 动态示例选择
# ============================================================================

class DynamicExampleSelector:
    """
    动态示例选择器。

    根据输入文本动态选择最相关的示例。
    简化版：使用关键词匹配；完整版可以用 embedding 相似度。
    """

    def __init__(self, manager: FewShotManager):
        self.manager = manager

    def select_by_keywords(
        self,
        input_text: str,
        n: int = 3
    ) -> list[FewShotExample]:
        """
        根据关键词匹配选择示例。

        Args:
            input_text: 输入文本
            n: 返回的示例数量

        Returns:
            匹配度最高的示例
        """
        # 定义类别关键词
        category_keywords = {
            "科技": ["手机", "芯片", "AI", "互联网", "软件", "科技", "发布"],
            "财经": ["股价", "财报", "央行", "利率", "银行", "投资", "市场"],
            "体育": ["比赛", "球队", "运动员", "世界杯", "NBA", "冠军"],
            "娱乐": ["演员", "歌手", "电影", "专辑", "明星", "娱乐"],
        }

        # 检测输入文本可能的类别
        detected_category = None
        max_matches = 0

        for category, keywords in category_keywords.items():
            matches = sum(1 for kw in keywords if kw in input_text)
            if matches > max_matches:
                max_matches = matches
                detected_category = category

        # 优先选择匹配类别的示例
        if detected_category:
            same_category = self.manager.get_examples(
                n=n // 2,
                category=detected_category
            )
            other_categories = self.manager.get_examples(
                n=n - len(same_category),
                strategy="random"
            )
            # 过滤掉重复的
            other_categories = [
                ex for ex in other_categories
                if ex not in same_category
            ]
            return same_category + other_categories

        return self.manager.get_examples(n=n, strategy="random")


# ============================================================================
# Part 5: 演示函数
# ============================================================================

def demo_few_shot_basics() -> None:
    """演示 Few-shot 基础概念"""
    print("=" * 60)
    print("Few-shot Learning 基础")
    print("=" * 60)

    # 从 YAML 字符串加载
    manager = FewShotManager.from_yaml_string(DEFAULT_CLASSIFY_EXAMPLES)

    print(f"\n加载了 {len(manager.collection.examples)} 个示例")
    print(f"任务类型: {manager.collection.task_type}")
    print(f"版本: {manager.collection.version}")

    # 获取示例
    print("\n【随机选择 3 个示例】")
    examples = manager.get_examples(n=3, strategy="random")
    for i, ex in enumerate(examples, 1):
        print(f"{i}. [{ex.category}] {ex.input[:30]}... -> {ex.output}")

    print("\n【平衡选择 3 个示例（覆盖不同类别）】")
    examples = manager.get_examples(n=3, strategy="balanced")
    for i, ex in enumerate(examples, 1):
        print(f"{i}. [{ex.category}] {ex.input[:30]}... -> {ex.output}")


def demo_format_examples() -> None:
    """演示示例格式化"""
    print("\n" + "=" * 60)
    print("示例格式化为 Prompt 片段")
    print("=" * 60)

    manager = FewShotManager.from_yaml_string(DEFAULT_CLASSIFY_EXAMPLES)
    examples = manager.get_examples(n=3, strategy="balanced")

    formatted = manager.format_examples(examples)
    print(formatted)


def demo_zero_vs_few_shot() -> None:
    """演示 Zero-shot vs Few-shot"""
    print("\n" + "=" * 60)
    print("Zero-shot vs Few-shot Prompt 对比")
    print("=" * 60)

    test_input = "华为发布新款折叠屏手机，售价 2 万元"
    categories = ["财经", "科技", "体育", "娱乐"]

    # Zero-shot
    zero_shot = build_zero_shot_prompt(test_input, categories)

    # Few-shot
    manager = FewShotManager.from_yaml_string(DEFAULT_CLASSIFY_EXAMPLES)
    examples = manager.get_examples(n=3, strategy="balanced")
    few_shot = build_few_shot_prompt(test_input, categories, examples)

    print("\n【Zero-shot Prompt】")
    print("-" * 40)
    print(zero_shot)

    print("\n【Few-shot Prompt】")
    print("-" * 40)
    print(few_shot)


def demo_dynamic_selection() -> None:
    """演示动态示例选择"""
    print("\n" + "=" * 60)
    print("动态示例选择")
    print("=" * 60)

    manager = FewShotManager.from_yaml_string(DEFAULT_CLASSIFY_EXAMPLES)
    selector = DynamicExampleSelector(manager)

    test_inputs = [
        "特斯拉发布新款电动车，续航里程突破 1000 公里",
        "央行宣布降息，A股市场大涨",
        "某知名歌手宣布全球巡演计划",
    ]

    for input_text in test_inputs:
        print(f"\n【输入】{input_text}")
        examples = selector.select_by_keywords(input_text, n=3)
        print("【选择的示例】")
        for ex in examples:
            print(f"  - [{ex.category}] {ex.input[:25]}...")


def demo_yaml_config() -> None:
    """演示 YAML 配置文件的使用"""
    print("\n" + "=" * 60)
    print("YAML 配置文件管理")
    print("=" * 60)

    # 创建示例配置
    config = {
        "task_type": "extract",
        "version": "1.0",
        "examples": [
            {
                "input": "北京今天气温 25 度，明天将下降到 20 度",
                "output": '{"locations": ["北京"], "temperatures": ["25度", "20度"]}',
                "category": "weather"
            },
            {
                "input": "上海和深圳的 GDP 增长率分别为 5.2% 和 6.1%",
                "output": '{"locations": ["上海", "深圳"], "percentages": ["5.2%", "6.1%"]}',
                "category": "economics"
            }
        ]
    }

    # 保存到临时文件
    temp_path = "/tmp/few_shot_examples.yaml"
    with open(temp_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    print(f"\n配置已保存到: {temp_path}")

    # 从文件加载
    manager = FewShotManager.from_yaml(temp_path)
    print(f"加载了 {len(manager.collection.examples)} 个示例")

    # 打印配置内容
    print("\n【YAML 配置内容】")
    print(yaml.dump(config, allow_unicode=True, default_flow_style=False))


def demo_few_shot_best_practices() -> None:
    """演示 Few-shot 最佳实践"""
    print("\n" + "=" * 60)
    print("Few-shot 最佳实践")
    print("=" * 60)

    practices = [
        ("覆盖主要类别", "如果分类任务有四个类别，示例最好能覆盖全部四个"),
        ("格式严格一致", "所有示例的输入输出格式必须完全一样"),
        ("难度适中", "70% 标准案例 + 30% 边界案例"),
        ("避免偏见", "示例不能暗示某种'偏好'"),
        ("数量适度", "3-5 个示例通常就够了，太多会增加 Token 消耗"),
    ]

    print("\n【Few-shot 示例选择原则】")
    for i, (title, desc) in enumerate(practices, 1):
        print(f"{i}. {title}")
        print(f"   {desc}")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("Few-shot Learning 演示")
    print("=" * 60)

    # 1. 基础概念
    demo_few_shot_basics()

    # 2. 格式化
    demo_format_examples()

    # 3. Zero-shot vs Few-shot
    demo_zero_vs_few_shot()

    # 4. 动态选择
    demo_dynamic_selection()

    # 5. YAML 配置
    demo_yaml_config()

    # 6. 最佳实践
    demo_few_shot_best_practices()


if __name__ == "__main__":
    main()

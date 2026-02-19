#!/usr/bin/env python3
"""
01_prompt_design.py - Prompt 四要素设计

本示例展示 Prompt 设计的四个核心要素：
- Role（角色）：告诉 LLM "你是谁"
- Task（任务）：告诉 LLM "做什么"
- Constraint（约束）：告诉 LLM "不能做什么"
- Format（格式）：告诉 LLM "输出长什么样"

通过 bad prompt vs good prompt 的对比，
展示四要素对输出质量的显著影响。

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."

本示例需要真实的 API 调用。
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel, Field

# 从 week_01 导入 LLM Client
import sys
# 注意：sys.path 操作仅用于开发环境，正式安装包后应使用正常的 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'week_01', 'examples'))

try:
    # 尝试从 week_01 导入
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# ============================================================================
# Part 1: Prompt 四要素数据结构
# ============================================================================

@dataclass
class PromptElements:
    """
    Prompt 四要素的数据结构。

    一个完整的 Prompt 应该包含：
    - role: 角色设定（system message 的核心）
    - task: 具体任务描述
    - constraints: 约束条件列表
    - output_format: 输出格式要求
    """
    role: str
    task: str
    constraints: list[str] = field(default_factory=list)
    output_format: str = ""

    def build_system_message(self) -> str:
        """构建 system message"""
        return f"你是一个{self.role}。"

    def build_user_message(self, input_text: str) -> str:
        """
        构建 user message（包含任务、约束、格式、输入）。

        使用 f-string 进行模板构建，确保可读性和可维护性。
        """
        parts = [f"任务：{self.task}"]

        # 添加约束条件
        if self.constraints:
            parts.append("\n约束：")
            for c in self.constraints:
                parts.append(f"- {c}")

        # 添加输出格式要求
        if self.output_format:
            parts.append(f"\n格式：{self.output_format}")

        # 添加输入文本
        parts.append(f"\n{input_text}")

        return "\n".join(parts)

    def render(self, input_text: str) -> tuple[str, str]:
        """
        渲染完整的 Prompt（system + user）。

        Returns:
            (system_message, user_message) 元组
        """
        return self.build_system_message(), self.build_user_message(input_text)


# ============================================================================
# Part 2: Bad Prompt vs Good Prompt 对比
# ============================================================================

# Bad Prompt 示例：只有任务，缺少其他要素
BAD_PROMPT_TEMPLATE = """请帮我分类以下新闻：

{input_text}"""

# Good Prompt 示例：包含完整的四要素
GOOD_PROMPT_TEMPLATE = """角色：你是一个新闻分类助手。

任务：判断以下新闻属于哪个类别。

约束：
- 只输出类别名称，不要解释原因
- 如果不确定，选择最接近的类别
- 不要输出多余的文字

格式：从以下选项中选一个：财经、科技、体育、娱乐

新闻内容：{input_text}"""


def compare_prompts(input_text: str, client=None) -> dict:
    """
    对比 bad prompt 和 good prompt 的输出差异。

    Args:
        input_text: 输入的新闻文本
        client: LLM 客户端（可选，如果为 None 则返回 Prompt 本身）

    Returns:
        包含两个 Prompt 和（可选）输出的字典
    """
    bad_prompt = BAD_PROMPT_TEMPLATE.format(input_text=input_text)
    good_prompt = GOOD_PROMPT_TEMPLATE.format(input_text=input_text)

    result = {
        "input": input_text,
        "bad_prompt": bad_prompt,
        "good_prompt": good_prompt,
    }

    if client and HAS_OPENAI:
        # 检查 client 是否有 call 方法
        if not hasattr(client, 'call'):
            result["bad_output"] = "[错误：client 对象缺少 call 方法]"
            result["good_output"] = "[错误：client 对象缺少 call 方法]"
        else:
            # 使用 bad prompt
            try:
                result["bad_output"] = client.call(bad_prompt, "你是一个有帮助的助手。")
            except Exception as e:
                result["bad_output"] = f"[调用失败: {e}]"

            # 使用 good prompt
            try:
                system, user = PromptElements(
                    role="新闻分类助手",
                    task="判断以下新闻属于哪个类别",
                    constraints=[
                        "只输出类别名称，不要解释原因",
                        "如果不确定，选择最接近的类别",
                    ],
                    output_format="从以下选项中选一个：财经、科技、体育、娱乐"
                ).render(input_text)
                result["good_output"] = client.call(user, system)
            except Exception as e:
                result["good_output"] = f"[调用失败: {e}]"

    return result


# ============================================================================
# Part 3: 使用 Pydantic 进行结构化输出验证
# ============================================================================

class NewsClassification(BaseModel):
    """新闻分类结果的结构化模型"""
    category: str = Field(
        description="新闻类别",
        examples=["财经", "科技", "体育", "娱乐"]
    )
    confidence: float = Field(
        description="分类置信度，0-1 之间",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="简短的分类理由",
        max_length=50
    )


class TicketClassification(BaseModel):
    """客服工单分类结果的结构化模型"""
    department: str = Field(
        description="工单应该分配到的部门"
    )
    priority: str = Field(
        description="优先级：高、中、低"
    )
    key_entities: list[str] = Field(
        description="工单中的关键实体（如产品名、用户ID等）",
        default_factory=list
    )


# ============================================================================
# Part 4: Prompt 模板构建器
# ============================================================================

class PromptBuilder:
    """
    Prompt 构建器：使用 f-string 构建结构化的 Prompt。

    核心方法：
    - with_role(): 设置角色
    - with_task(): 设置任务
    - with_constraints(): 设置约束
    - with_format(): 设置输出格式
    - build(): 生成最终 Prompt
    """

    def __init__(self):
        self._role: Optional[str] = None
        self._task: Optional[str] = None
        self._constraints: list[str] = []
        self._output_format: Optional[str] = None
        self._few_shot_examples: list[dict] = []

    def with_role(self, role: str) -> "PromptBuilder":
        """设置角色"""
        self._role = role
        return self

    def with_task(self, task: str) -> "PromptBuilder":
        """设置任务"""
        self._task = task
        return self

    def with_constraints(self, *constraints: str) -> "PromptBuilder":
        """添加约束条件"""
        self._constraints.extend(constraints)
        return self

    def with_format(self, format_spec: str) -> "PromptBuilder":
        """设置输出格式"""
        self._output_format = format_spec
        return self

    def with_examples(self, *examples: dict) -> "PromptBuilder":
        """添加 Few-shot 示例"""
        self._few_shot_examples.extend(examples)
        return self

    def build(self, input_text: str = "") -> str:
        """
        构建完整的 Prompt。

        使用链式调用风格：
        >>> prompt = (PromptBuilder()
        ...     .with_role("新闻分类助手")
        ...     .with_task("判断新闻类别")
        ...     .with_constraints("只输出类别名")
        ...     .build("苹果发布新iPhone"))
        """
        parts = []

        # 角色
        if self._role:
            parts.append(f"角色：你是{self._role}。")

        # Few-shot 示例
        if self._few_shot_examples:
            parts.append("\n示例：")
            for ex in self._few_shot_examples:
                parts.append(f"输入：\"{ex.get('input', '')}\"")
                parts.append(f"输出：{ex.get('output', '')}")
            parts.append("")

        # 任务
        if self._task:
            parts.append(f"任务：{self._task}")

        # 约束
        if self._constraints:
            parts.append("\n约束：")
            for c in self._constraints:
                parts.append(f"- {c}")

        # 格式
        if self._output_format:
            parts.append(f"\n格式：{self._output_format}")

        # 输入
        if input_text:
            parts.append(f"\n{input_text}")

        return "\n".join(parts)

    def build_messages(self, input_text: str = "") -> tuple[str, str]:
        """
        构建 system 和 user 两条消息。

        Returns:
            (system_message, user_message)
        """
        system = f"你是{self._role}。" if self._role else "你是一个有帮助的助手。"

        # 构建不包含角色的 user message
        parts = []

        if self._few_shot_examples:
            parts.append("示例：")
            for ex in self._few_shot_examples:
                parts.append(f"输入：\"{ex.get('input', '')}\"")
                parts.append(f"输出：{ex.get('output', '')}")
            parts.append("")

        if self._task:
            parts.append(f"任务：{self._task}")

        if self._constraints:
            parts.append("\n约束：")
            for c in self._constraints:
                parts.append(f"- {c}")

        if self._output_format:
            parts.append(f"\n格式：{self._output_format}")

        if input_text:
            parts.append(f"\n{input_text}")

        return system, "\n".join(parts)


# ============================================================================
# Part 5: 演示函数
# ============================================================================

def demo_bad_vs_good_prompt() -> None:
    """演示 bad prompt 和 good prompt 的差异"""
    print("=" * 60)
    print("Bad Prompt vs Good Prompt 对比")
    print("=" * 60)

    test_news = "苹果公司发布新款 iPhone，搭载 A18 芯片，性能提升 30%"

    # 构建 bad prompt
    bad_prompt = BAD_PROMPT_TEMPLATE.format(input_text=test_news)

    # 使用 PromptElements 构建 good prompt
    elements = PromptElements(
        role="新闻分类助手",
        task="判断以下新闻属于哪个类别",
        constraints=[
            "只输出类别名称，不要解释原因",
            "不要输出多余的标点或换行",
        ],
        output_format="从以下选项中选一个：财经、科技、体育、娱乐"
    )
    system, user = elements.render(test_news)

    print("\n【输入】")
    print(f"  {test_news}")

    print("\n【Bad Prompt】")
    print("-" * 40)
    print(bad_prompt)

    print("\n【Good Prompt（四要素完整）】")
    print("-" * 40)
    print(f"[System]\n{system}")
    print(f"\n[User]\n{user}")


def demo_prompt_builder() -> None:
    """演示 PromptBuilder 的链式调用"""
    print("\n" + "=" * 60)
    print("PromptBuilder 链式调用演示")
    print("=" * 60)

    # 使用链式调用构建 Prompt
    prompt = (
        PromptBuilder()
        .with_role("客服工单分类助手")
        .with_task("判断以下工单应该分到哪个部门")
        .with_constraints(
            "只输出部门名称",
            "不要解释原因",
            "如果不确定，选择'其他'"
        )
        .with_format("从以下选项中选一个：技术支持、账务问题、功能建议、投诉、其他")
        .with_examples(
            {"input": "App 无法登录，一直提示密码错误", "output": "技术支持"},
            {"input": "申请退款，订单号 12345", "output": "账务问题"},
        )
        .build("充值了会员但显示还是普通用户，已经等了20分钟没人处理")
    )

    print("\n【构建的 Prompt】")
    print("-" * 40)
    print(prompt)


def demo_pydantic_validation() -> None:
    """演示 Pydantic 结构化输出验证"""
    print("\n" + "=" * 60)
    print("Pydantic 结构化输出验证")
    print("=" * 60)

    # 模拟 LLM 输出（实际应用中从 API 获取）
    mock_outputs = [
        '{"category": "科技", "confidence": 0.95, "reasoning": "提到 iPhone 和芯片"}',
        '{"category": "财经", "confidence": 0.8, "reasoning": "涉及股价和财报"}',
        '{"category": "体育", "confidence": 0.9, "reasoning": "篮球比赛新闻"}',
    ]

    print("\n【解析模拟的 LLM 输出】")

    for i, output in enumerate(mock_outputs, 1):
        try:
            import json
            data = json.loads(output)
            classification = NewsClassification(**data)
            print(f"\n输出 {i}:")
            print(f"  类别: {classification.category}")
            print(f"  置信度: {classification.confidence:.0%}")
            print(f"  理由: {classification.reasoning}")
        except Exception as e:
            print(f"\n输出 {i}: 解析失败 - {e}")


def demo_common_mistakes() -> None:
    """演示常见的 Prompt 设计错误"""
    print("\n" + "=" * 60)
    print("常见 Prompt 设计错误")
    print("=" * 60)

    mistakes = [
        {
            "name": "动词不够具体",
            "bad": "分析这条新闻",
            "good": "判断这条新闻属于哪个类别：财经、科技、体育、娱乐",
            "problem": "'分析'太宽泛，LLM 可能做情感分析、主题分析等任何分析",
        },
        {
            "name": "缺少边界约束",
            "bad": "提取新闻中的公司名",
            "good": "提取新闻中的公司名。如果没有提到公司，输出'无'",
            "problem": "不告诉 LLM '没有怎么办'，它可能会编造或输出无法处理的文字",
        },
        {
            "name": "格式不明确",
            "bad": "用 JSON 格式输出",
            "good": "用 JSON 格式输出：{\"companies\": [\"公司名1\", \"公司名2\"]}",
            "problem": "'JSON 格式'还是太宽，LLM 可能用你不期望的字段名",
        },
    ]

    for i, m in enumerate(mistakes, 1):
        print(f"\n【错误 {i}】{m['name']}")
        print(f"  Bad:  {m['bad']}")
        print(f"  Good: {m['good']}")
        print(f"  问题: {m['problem']}")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("Prompt 四要素设计演示")
    print("=" * 60)

    # 1. Bad vs Good Prompt 对比
    demo_bad_vs_good_prompt()

    # 2. PromptBuilder 链式调用
    demo_prompt_builder()

    # 3. Pydantic 结构化验证
    demo_pydantic_validation()

    # 4. 常见错误
    demo_common_mistakes()

    # 5. 如果有 API Key，可以实际调用
    if os.getenv("OPENAI_API_KEY") and HAS_OPENAI:
        print("\n" + "=" * 60)
        print("实际 API 调用（需要 OPENAI_API_KEY）")
        print("=" * 60)

        from openai import OpenAI

        client = OpenAI()
        test_news = "苹果公司发布新款 iPhone，搭载 A18 芯片"

        # 测试 good prompt
        elements = PromptElements(
            role="新闻分类助手",
            task="判断以下新闻属于哪个类别",
            constraints=["只输出类别名称"],
            output_format="财经、科技、体育、娱乐"
        )
        system, user = elements.render(test_news)

        print(f"\n输入: {test_news}")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0
        )
        print(f"输出: {response.choices[0].message.content}")
    else:
        print("\n[提示] 设置 OPENAI_API_KEY 环境变量可以进行实际 API 调用测试")


if __name__ == "__main__":
    main()

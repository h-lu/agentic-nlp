#!/usr/bin/env python3
"""
05_template_library.py - PromptTemplate 类

本示例展示如何构建一个工程化的 Prompt 模板库：
- PromptTemplate 类：支持变量替换和模板渲染
- Few-shot 示例注入
- CoT 步骤集成
- YAML 配置文件管理

模板库的设计目标：
- 复用性：同一个模板可以用于不同输入
- 可维护性：修改模板不影响业务代码
- 版本管理：追踪模板变更历史

基于 Week 01 的 LLM Client 构建。

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

import os
import yaml
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Callable, Union
from pathlib import Path
from string import Template
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


# ============================================================================
# Part 1: Prompt 模板数据结构
# ============================================================================

class PromptStyle(str, Enum):
    """Prompt 风格"""
    STANDARD = "standard"  # 标准格式（角色-任务-约束-格式）
    CONVERSATIONAL = "conversational"  # 对话式
    STRUCTURED = "structured"  # 结构化（JSON 输出）


@dataclass
class FewShotExample:
    """Few-shot 示例"""
    input: str
    output: str
    reasoning: Optional[str] = None  # CoT 推理过程（可选）

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FewShotExample":
        return cls(
            input=data["input"],
            output=data["output"],
            reasoning=data.get("reasoning")
        )


class PromptTemplateConfig(BaseModel):
    """Prompt 模板配置（Pydantic 模型，用于验证）"""
    name: str = Field(description="模板名称")
    version: str = Field(default="1.0", description="版本号")
    description: str = Field(default="", description="模板描述")

    # 四要素
    role: str = Field(description="角色设定")
    task: str = Field(description="任务描述")
    constraints: List[str] = Field(default_factory=list, description="约束条件")
    output_format: str = Field(default="", description="输出格式")

    # 可选组件
    few_shot_examples: List[dict] = Field(default_factory=list, description="Few-shot 示例")
    use_cot: bool = Field(default=False, description="是否使用 CoT")
    cot_steps: List[str] = Field(default_factory=list, description="CoT 步骤")

    # 元数据
    style: PromptStyle = Field(default=PromptStyle.STANDARD, description="Prompt 风格")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Part 2: PromptTemplate 类
# ============================================================================

class PromptTemplate:
    """
    Prompt 模板类。

    支持功能：
    - 四要素模板构建
    - Few-shot 示例注入
    - CoT 步骤集成
    - 变量替换

    Example:
        >>> template = PromptTemplate(
        ...     role="新闻分类助手",
        ...     task="判断新闻类别",
        ...     constraints=["只输出类别名"],
        ...     output_format="财经、科技、体育、娱乐"
        ... )
        >>> prompt = template.render("苹果发布新 iPhone")
    """

    def __init__(
        self,
        role: str,
        task: str,
        constraints: Optional[List[str]] = None,
        output_format: str = "",
        few_shot_examples: Optional[List[FewShotExample]] = None,
        use_cot: bool = False,
        cot_steps: Optional[List[str]] = None,
        name: str = "unnamed",
        version: str = "1.0",
    ):
        self.role = role
        self.task = task
        self.constraints = constraints or []
        self.output_format = output_format
        self.few_shot_examples = few_shot_examples or []
        self.use_cot = use_cot
        self.cot_steps = cot_steps or []
        self.name = name
        self.version = version

    @classmethod
    def from_config(cls, config: PromptTemplateConfig) -> "PromptTemplate":
        """从配置对象创建模板"""
        examples = [FewShotExample.from_dict(e) for e in config.few_shot_examples]
        return cls(
            role=config.role,
            task=config.task,
            constraints=config.constraints,
            output_format=config.output_format,
            few_shot_examples=examples,
            use_cot=config.use_cot,
            cot_steps=config.cot_steps,
            name=config.name,
            version=config.version,
        )

    @classmethod
    def from_yaml(cls, yaml_path: str, template_name: Optional[str] = None) -> "PromptTemplate":
        """从 YAML 文件加载模板"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 支持单模板和多模板文件
        if 'templates' in data:
            templates = data['templates']
            if template_name:
                t = next((t for t in templates if t['name'] == template_name), None)
                if not t:
                    raise ValueError(f"模板 '{template_name}' 不存在")
            else:
                t = templates[0]  # 默认取第一个
        else:
            t = data

        config = PromptTemplateConfig(**t)
        return cls.from_config(config)

    def render(
        self,
        input_text: str,
        examples: Optional[List[FewShotExample]] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        渲染 Prompt。

        Args:
            input_text: 输入文本
            examples: 额外的 Few-shot 示例（会与模板中的示例合并）
            variables: 额外的变量替换

        Returns:
            渲染后的完整 Prompt
        """
        parts = []

        # 1. 角色设定
        parts.append(f"角色：你是{self.role}。")

        # 2. Few-shot 示例
        all_examples = self.few_shot_examples + (examples or [])
        if all_examples:
            parts.append("\n示例：")
            for ex in all_examples:
                parts.append(f"输入：\"{ex.input}\"")
                if self.use_cot and ex.reasoning:
                    parts.append(f"分析：{ex.reasoning}")
                parts.append(f"输出：{ex.output}")
            parts.append("")

        # 3. 任务描述
        parts.append(f"任务：{self.task}")

        # 4. 约束条件
        if self.constraints:
            parts.append("\n约束：")
            for c in self.constraints:
                parts.append(f"- {c}")

        # 5. CoT 步骤
        if self.use_cot and self.cot_steps:
            parts.append("\n请按以下步骤思考：")
            for i, step in enumerate(self.cot_steps, 1):
                parts.append(f"{i}. {step}")

        # 6. 输出格式
        if self.output_format:
            parts.append(f"\n格式：{self.output_format}")

        # 7. 输入
        parts.append(f"\n{input_text}")

        prompt = "\n".join(parts)

        # 8. 变量替换
        if variables:
            for key, value in variables.items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        return prompt

    def render_messages(
        self,
        input_text: str,
        examples: Optional[List[FewShotExample]] = None,
    ) -> List[Dict[str, str]]:
        """
        渲染为 Chat API 消息格式。

        Returns:
            [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
        """
        system = f"你是{self.role}。"

        # 构建 user message（不包含角色）
        parts = []

        all_examples = self.few_shot_examples + (examples or [])
        if all_examples:
            parts.append("示例：")
            for ex in all_examples:
                parts.append(f"输入：\"{ex.input}\"")
                if self.use_cot and ex.reasoning:
                    parts.append(f"分析：{ex.reasoning}")
                parts.append(f"输出：{ex.output}")
            parts.append("")

        parts.append(f"任务：{self.task}")

        if self.constraints:
            parts.append("\n约束：")
            for c in self.constraints:
                parts.append(f"- {c}")

        if self.use_cot and self.cot_steps:
            parts.append("\n请按以下步骤思考：")
            for i, step in enumerate(self.cot_steps, 1):
                parts.append(f"{i}. {step}")

        if self.output_format:
            parts.append(f"\n格式：{self.output_format}")

        parts.append(f"\n{input_text}")

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n".join(parts)}
        ]

    def to_config(self) -> PromptTemplateConfig:
        """转换为配置对象"""
        return PromptTemplateConfig(
            name=self.name,
            version=self.version,
            role=self.role,
            task=self.task,
            constraints=self.constraints,
            output_format=self.output_format,
            few_shot_examples=[e.to_dict() for e in self.few_shot_examples],
            use_cot=self.use_cot,
            cot_steps=self.cot_steps,
        )

    def save_to_yaml(self, path: str) -> None:
        """保存到 YAML 文件"""
        config = self.to_config()
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(
                {'templates': [config.model_dump(mode='json')]},
                f,
                allow_unicode=True,
                default_flow_style=False
            )


# ============================================================================
# Part 3: Prompt 模板库
# ============================================================================

class PromptLibrary:
    """
    Prompt 模板库。

    功能：
    - 管理多个 Prompt 模板
    - 从配置文件批量加载
    - 支持模板版本管理

    Example:
        >>> library = PromptLibrary.from_yaml("templates/prompts.yaml")
        >>> template = library.get("news_classify")
        >>> prompt = template.render("苹果发布新 iPhone")
    """

    def __init__(self, templates: Optional[Dict[str, PromptTemplate]] = None):
        self.templates = templates or {}
        self._metadata = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "PromptLibrary":
        """从 YAML 文件加载模板库"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        templates = {}
        for t in data.get('templates', []):
            config = PromptTemplateConfig(**t)
            template = PromptTemplate.from_config(config)
            templates[template.name] = template

        library = cls(templates)
        library._metadata = {
            "created_at": data.get('created_at', datetime.now().isoformat()),
            "version": data.get('version', '1.0')
        }
        return library

    def get(self, name: str) -> Optional[PromptTemplate]:
        """获取指定模板"""
        return self.templates.get(name)

    def get_required(self, name: str) -> PromptTemplate:
        """获取指定模板（不存在则报错）"""
        template = self.templates.get(name)
        if not template:
            raise KeyError(f"模板 '{name}' 不存在")
        return template

    def list_templates(self) -> List[str]:
        """列出所有模板名称"""
        return list(self.templates.keys())

    def add_template(self, template: PromptTemplate) -> None:
        """添加模板"""
        self.templates[template.name] = template

    def remove_template(self, name: str) -> bool:
        """移除模板"""
        if name in self.templates:
            del self.templates[name]
            return True
        return False

    def save_to_yaml(self, path: str) -> None:
        """保存到 YAML 文件"""
        data = {
            'version': self._metadata['version'],
            'created_at': self._metadata['created_at'],
            'templates': [t.to_config().model_dump(mode='json') for t in self.templates.values()]
        }
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


# ============================================================================
# Part 4: 默认模板配置
# ============================================================================

# 默认模板 YAML 配置（实际项目中会放在单独的文件中）
DEFAULT_TEMPLATES_YAML = """
version: "1.0"
created_at: "2026-02-16"

templates:
  - name: news_classify
    version: "1.0"
    description: "新闻分类模板"
    role: "新闻分类助手"
    task: "判断以下新闻属于哪个类别"
    constraints:
      - "只输出类别名称"
      - "不要解释原因"
    output_format: "从以下选项中选一个：财经、科技、体育、娱乐"
    few_shot_examples:
      - input: "苹果公司发布新款 iPhone"
        output: "科技"
      - input: "央行宣布下调存款准备金率"
        output: "财经"
      - input: "中国男篮战胜韩国队"
        output: "体育"
    tags:
      - classification
      - news

  - name: ticket_classify_cot
    version: "1.0"
    description: "客服工单分类（带 CoT）"
    role: "客服工单分类助手"
    task: "判断以下工单应该分到哪个部门"
    constraints:
      - "最后只输出部门名称"
      - "分析过程要简洁"
    output_format: "从以下选项中选一个：技术支持、账务问题、功能建议、投诉、其他"
    use_cot: true
    cot_steps:
      - "用户遇到了什么问题？"
      - "问题的核心诉求是什么？"
      - "哪个部门最适合处理这个诉求？"
      - "最终分类结果是什么？"
    tags:
      - classification
      - customer-service
      - cot

  - name: entity_extract
    version: "1.0"
    description: "实体抽取模板"
    role: "实体抽取助手"
    task: "从文本中抽取指定的实体"
    constraints:
      - "以 JSON 格式输出"
      - "如果某类实体不存在，输出空列表"
    output_format: '{"companies": [], "people": [], "locations": [], "dates": []}'
    tags:
      - extraction
      - ner
"""


# ============================================================================
# Part 5: 模板构建器（Builder 模式）
# ============================================================================

class PromptTemplateBuilder:
    """
    Prompt 模板构建器（Builder 模式）。

    提供链式调用的方式构建模板。

    Example:
        >>> template = (PromptTemplateBuilder()
        ...     .with_name("my_template")
        ...     .with_role("分类助手")
        ...     .with_task("分类文本")
        ...     .with_constraints("只输出类别")
        ...     .build())
    """

    def __init__(self):
        self._name = "unnamed"
        self._version = "1.0"
        self._role = ""
        self._task = ""
        self._constraints: List[str] = []
        self._output_format = ""
        self._few_shot_examples: List[FewShotExample] = []
        self._use_cot = False
        self._cot_steps: List[str] = []

    def with_name(self, name: str) -> "PromptTemplateBuilder":
        self._name = name
        return self

    def with_version(self, version: str) -> "PromptTemplateBuilder":
        self._version = version
        return self

    def with_role(self, role: str) -> "PromptTemplateBuilder":
        self._role = role
        return self

    def with_task(self, task: str) -> "PromptTemplateBuilder":
        self._task = task
        return self

    def with_constraints(self, *constraints: str) -> "PromptTemplateBuilder":
        self._constraints.extend(constraints)
        return self

    def with_output_format(self, format_spec: str) -> "PromptTemplateBuilder":
        self._output_format = format_spec
        return self

    def with_example(self, input_text: str, output: str, reasoning: str = None) -> "PromptTemplateBuilder":
        self._few_shot_examples.append(FewShotExample(input=input_text, output=output, reasoning=reasoning))
        return self

    def with_cot(self, *steps: str) -> "PromptTemplateBuilder":
        self._use_cot = True
        self._cot_steps.extend(steps)
        return self

    def build(self) -> PromptTemplate:
        """构建模板"""
        if not self._role:
            raise ValueError("必须设置角色 (role)")
        if not self._task:
            raise ValueError("必须设置任务 (task)")

        return PromptTemplate(
            name=self._name,
            version=self._version,
            role=self._role,
            task=self._task,
            constraints=self._constraints,
            output_format=self._output_format,
            few_shot_examples=self._few_shot_examples,
            use_cot=self._use_cot,
            cot_steps=self._cot_steps,
        )


# ============================================================================
# Part 6: 演示函数
# ============================================================================

def demo_basic_template() -> None:
    """演示基础模板创建和渲染"""
    print("=" * 60)
    print("基础模板创建和渲染")
    print("=" * 60)

    # 创建模板
    template = PromptTemplate(
        name="news_classify",
        role="新闻分类助手",
        task="判断以下新闻属于哪个类别",
        constraints=[
            "只输出类别名称",
            "不要解释原因",
        ],
        output_format="从以下选项中选一个：财经、科技、体育、娱乐",
        few_shot_examples=[
            FewShotExample(input="苹果发布新 iPhone", output="科技"),
            FewShotExample(input="央行宣布降息", output="财经"),
        ]
    )

    # 渲染 Prompt
    input_text = "特斯拉发布新款电动车，续航里程突破 1000 公里"
    prompt = template.render(input_text)

    print(f"\n【模板信息】")
    print(f"  名称: {template.name}")
    print(f"  角色: {template.role}")

    print(f"\n【渲染结果】")
    print("-" * 40)
    print(prompt)


def demo_cot_template() -> None:
    """演示 CoT 模板"""
    print("\n" + "=" * 60)
    print("CoT 模板演示")
    print("=" * 60)

    template = PromptTemplate(
        name="ticket_classify_cot",
        role="客服工单分类助手",
        task="判断以下工单应该分到哪个部门",
        constraints=[
            "最后只输出部门名称",
        ],
        output_format="从以下选项中选一个：技术支持、账务问题、功能建议、投诉、其他",
        use_cot=True,
        cot_steps=[
            "用户遇到了什么问题？",
            "问题的核心诉求是什么？",
            "哪个部门最适合处理这个诉求？",
            "最终分类结果是什么？",
        ]
    )

    input_text = "我用你们 App 充值了会员，但是显示还是普通用户"
    prompt = template.render(input_text)

    print(f"\n【CoT 模板渲染结果】")
    print("-" * 40)
    print(prompt)


def demo_builder_pattern() -> None:
    """演示 Builder 模式构建模板"""
    print("\n" + "=" * 60)
    print("Builder 模式构建模板")
    print("=" * 60)

    template = (
        PromptTemplateBuilder()
        .with_name("sentiment_analysis")
        .with_role("情感分析助手")
        .with_task("判断以下文本的情感倾向")
        .with_constraints(
            "只输出情感类别：正面、负面、中性",
            "不要解释原因",
        )
        .with_output_format("正面/负面/中性")
        .with_example("这个产品太棒了！", "正面")
        .with_example("服务太差了，再也不来了", "负面")
        .with_example("今天天气不错", "中性")
        .build()
    )

    print(f"\n【通过 Builder 创建的模板】")
    print(f"  名称: {template.name}")
    print(f"  角色: {template.role}")
    print(f"  示例数量: {len(template.few_shot_examples)}")

    prompt = template.render("这个 App 好用是好用，就是太贵了")
    print(f"\n【渲染结果】")
    print("-" * 40)
    print(prompt)


def demo_yaml_config() -> None:
    """演示 YAML 配置文件"""
    print("\n" + "=" * 60)
    print("YAML 配置文件管理")
    print("=" * 60)

    # 从 YAML 字符串加载
    import tempfile

    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(DEFAULT_TEMPLATES_YAML)
        temp_path = f.name

    # 加载模板库
    library = PromptLibrary.from_yaml(temp_path)

    print(f"\n加载了 {len(library.list_templates())} 个模板")
    print(f"模板列表: {library.list_templates()}")

    # 获取并渲染模板
    template = library.get("news_classify")
    if template:
        print(f"\n【news_classify 模板】")
        prompt = template.render("OpenAI 发布 GPT-5 模型")
        print(prompt)

    # 清理
    os.unlink(temp_path)


def demo_messages_format() -> None:
    """演示 Chat API 消息格式"""
    print("\n" + "=" * 60)
    print("Chat API 消息格式")
    print("=" * 60)

    template = PromptTemplate(
        name="test",
        role="分类助手",
        task="分类文本",
        constraints=["只输出类别"],
        few_shot_examples=[
            FewShotExample(input="苹果", output="水果"),
        ]
    )

    messages = template.render_messages("香蕉")

    print(f"\n【Chat API 消息格式】")
    for msg in messages:
        print(f"\n[{msg['role'].upper()}]")
        print(msg['content'])


def demo_template_persistence() -> None:
    """演示模板持久化"""
    print("\n" + "=" * 60)
    print("模板持久化")
    print("=" * 60)

    # 创建模板
    template = PromptTemplate(
        name="my_template",
        version="1.0",
        role="测试助手",
        task="测试任务",
        constraints=["约束1", "约束2"],
    )

    # 保存到临时文件
    temp_path = "/tmp/my_template.yaml"
    template.save_to_yaml(temp_path)
    print(f"\n模板已保存到: {temp_path}")

    # 从文件加载
    loaded = PromptTemplate.from_yaml(temp_path)
    print(f"加载的模板名称: {loaded.name}")
    print(f"加载的模板角色: {loaded.role}")

    # 显示文件内容
    print(f"\n【YAML 文件内容】")
    with open(temp_path, 'r', encoding='utf-8') as f:
        print(f.read())


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("PromptTemplate 类演示")
    print("=" * 60)

    # 1. 基础模板
    demo_basic_template()

    # 2. CoT 模板
    demo_cot_template()

    # 3. Builder 模式
    demo_builder_pattern()

    # 4. YAML 配置
    demo_yaml_config()

    # 5. Chat API 格式
    demo_messages_format()

    # 6. 持久化
    demo_template_persistence()


if __name__ == "__main__":
    main()

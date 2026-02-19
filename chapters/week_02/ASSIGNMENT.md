# Week 02 作业：Prompt Engineering 实战演练

本周你学会了设计清晰的 Prompt、用 Few-shot 稳定输出格式、用 CoT 处理复杂推理。现在是时候把这些技能整合起来，搭建一个完整的 Prompt 工程化系统了。

**重要提示**：本作业不要求使用任何 AI 工具。你需要亲手设计每一个 Prompt，调试每一次迭代——这是建立 Prompt Engineering 直觉的必经之路。

---

## 作业背景

你所在的公司有一个客服工单系统，每天接收数百条用户反馈。上周你已经用 LLM 做了一个分类原型，但效果不稳定：
- 有时候输出格式不规范，导致解析代码崩溃
- 分类准确率忽高忽低，不知道是 Prompt 问题还是模型问题
- 边界模糊的工单经常分类错误

这周你的任务是搭建一个工程化的 Prompt 库和评估系统，让整个流程可复现、可评估、可迭代。

---

## 核心任务（必做，75 分）

### Part 1：设计 Prompt 模板库（30 分）

为客服工单系统设计三个 Prompt 模板，分别用于分类、摘要和实体抽取。

#### 要求

**1.1 四要素完整性（12 分）**

每个 Prompt 必须包含：
- **角色（Role）**：告诉 LLM "你是谁"
- **任务（Task）**：明确要做什么
- **约束（Constraint）**：不能做什么，边界条件
- **格式（Format）**：输出长什么样

**1.2 Pydantic 输出格式定义（10 分）**

> 💡 **提示**：我们使用 Pydantic 来定义输出格式，这是第 4 节中介绍的用法。如果你还不熟悉 Pydantic，请先阅读第 4 节的"用 Pydantic 定义数据结构"小节。简单来说，Pydantic 和 `dataclasses` 很像，但多了运行时验证——能自动把字符串 "0.95" 转成浮点数 0.95，还能在数据不符合约束时报错。

使用 Pydantic 定义三个任务的输出格式：

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class TicketCategory(str, Enum):
    """工单类别"""
    TECH_SUPPORT = "技术支持"
    BILLING = "账务问题"
    FEATURE_REQUEST = "功能建议"
    COMPLAINT = "投诉"
    OTHER = "其他"

class Urgency(str, Enum):
    """紧急程度"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

class ClassificationResult(BaseModel):
    """分类结果"""
    category: TicketCategory = Field(description="工单类别")
    urgency: Urgency = Field(description="紧急程度")
    confidence: float = Field(description="置信度 (0-1)")

class SummaryResult(BaseModel):
    """摘要结果"""
    main_issue: str = Field(description="主要问题描述")
    affected_product: Optional[str] = Field(default=None, description="涉及的产品")
    user_intent: str = Field(description="用户意图")

class ExtractionResult(BaseModel):
    """实体抽取结果"""
    user_id: Optional[str] = Field(default=None, description="用户ID")
    order_id: Optional[str] = Field(default=None, description="订单号")
    product_names: List[str] = Field(default_factory=list, description="提到的产品")
    mentioned_features: List[str] = Field(default_factory=list, description="提到的功能")
```

**1.3 模板可渲染（8 分）**

实现一个 `PromptTemplate` 类，支持：
- 从 YAML 配置文件加载模板
- 动态填充输入内容
- 输出完整的 Prompt 字符串

> **注意**：本节的代码骨架使用 `dataclass` 简化实现。如果你已经熟悉 Pydantic，也可以用 Pydantic 重写（参考 1.2 节的示例）。

**代码骨架**：

```python
# prompts/templates.py
from dataclasses import dataclass
from typing import List, Optional
import yaml

@dataclass
class PromptTemplate:
    """Prompt 模板"""
    name: str
    role: str
    task: str
    constraints: List[str]
    output_format: str
    few_shot_examples: Optional[List[dict]] = None

    def render(self, input_text: str) -> str:
        """渲染 Prompt"""
        # TODO: 实现渲染逻辑
        # 1. 添加角色
        # 2. 添加 Few-shot 示例（如果有）
        # 3. 添加任务描述
        # 4. 添加约束条件
        # 5. 添加输出格式
        # 6. 添加输入内容
        pass

class PromptLibrary:
    """Prompt 模板库"""

    def __init__(self, config_path: str):
        # TODO: 从 YAML 文件加载配置
        pass

    def get(self, name: str) -> PromptTemplate:
        """获取指定模板"""
        pass

    def list_templates(self) -> List[str]:
        """列出所有模板名称"""
        pass
```

**对应的 YAML 配置文件**：

```yaml
# templates/prompts.yaml
templates:
  - name: ticket_classify
    role: "你是一个客服工单分类助手"
    task: "判断以下工单应该分到哪个部门"
    constraints:
      - "只输出 JSON 格式的分类结果"
      - "如果不确定，选择 OTHER"
      - "confidence 必须在 0-1 之间"
    output_format: |
      {"category": "技术支持|账务问题|功能建议|投诉|其他",
       "urgency": "高|中|低",
       "confidence": 0.0-1.0}

  - name: ticket_summarize
    role: "你是一个工单摘要助手"
    task: "提取工单的核心信息"
    constraints:
      - "main_issue 不超过 50 字"
      - "只提取明确提到的信息，不要猜测"
    output_format: |
      {"main_issue": "问题描述",
       "affected_product": "产品名或 null",
       "user_intent": "用户想要什么"}

  - name: ticket_extract
    role: "你是一个信息抽取助手"
    task: "从工单中提取关键实体"
    constraints:
      - "只提取明确出现在文本中的信息"
      - "如果某类实体不存在，返回空列表"
    output_format: |
      {"user_id": "用户ID或 null",
       "order_id": "订单号或 null",
       "product_names": ["产品1", "产品2"],
       "mentioned_features": ["功能1", "功能2"]}
```

**提交内容**：
- `prompts/templates.py`：模板类实现
- `prompts/__init__.py`：模块初始化
- `templates/prompts.yaml`：模板配置文件
- 运行示例：展示三个模板的渲染结果

---

### Part 2：实现 Few-shot 示例管理（25 分）

为分类任务准备 Few-shot 示例，并实现动态示例选择。

#### 要求

**2.1 示例准备（10 分）**

为工单分类任务准备 5-10 个高质量示例，要求：
- 覆盖所有 5 个类别
- 包含至少 2 个边界模糊的案例
- 输出格式严格一致

**示例格式**：

```yaml
# examples/classify_examples.yaml
examples:
  - input: "我的 App 一直闪退，根本用不了，订单号是 ORD-12345"
    output: '{"category": "技术支持", "urgency": "高", "confidence": 0.9}'
    category: "技术支持"
    is_boundary: false

  - input: "充值了会员但显示还是普通用户，而且找不到客服"
    output: '{"category": "账务问题", "urgency": "中", "confidence": 0.85}'
    category: "账务问题"
    is_boundary: true  # 边界案例：涉及技术问题但核心是账务
    note: "用户提到了客服响应问题，但核心诉求是会员权益"

  # TODO: 继续添加更多示例
```

**2.2 Few-shot 管理器实现（10 分）**

```python
# prompts/examples.py
from typing import List, Dict, Optional
import yaml

class FewShotManager:
    """Few-shot 示例管理器"""

    def __init__(self, examples_file: str):
        """加载示例配置"""
        # TODO: 实现
        pass

    def get_examples(
        self,
        task: str,
        category: Optional[str] = None,
        include_boundary: bool = True,
        n: int = 5
    ) -> List[Dict]:
        """
        获取示例

        Args:
            task: 任务类型
            category: 优先选择指定类别的示例
            include_boundary: 是否包含边界案例
            n: 返回的示例数量
        """
        # TODO: 实现
        pass

    def format_examples(self, examples: List[Dict]) -> str:
        """将示例格式化为 Prompt 片段"""
        # TODO: 实现
        # 输出格式：
        # 示例：
        # 输入："..."
        # 输出：...
        pass
```

**2.3 效果对比实验（5 分）**

在至少 10 条测试样本上对比：
- 无 Few-shot 的准确率
- 有 3 个 Few-shot 示例的准确率
- 有 5 个 Few-shot 示例的准确率

**记录表格**：

```markdown
| 配置 | 准确率 | 格式合规率 | 平均 Token 消耗 |
|------|--------|-----------|----------------|
| 无 Few-shot | ? | ? | ? |
| 3-shot | ? | ? | ? |
| 5-shot | ? | ? | ? |
```

**提交内容**：
- `examples/classify_examples.yaml`：示例配置文件
- `prompts/examples.py`：Few-shot 管理器实现
- 对比实验代码和结果

---

### Part 3：搭建评估流程（20 分）

建立 Prompt 的评估体系，让迭代有据可依。

#### 要求

**3.1 测试集构建（8 分）**

构建至少 20 条标注好的测试样本：

```python
# evaluation/test_cases.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class TestCase:
    """测试用例"""
    input_text: str
    expected_category: str
    expected_urgency: str
    difficulty: str  # "easy", "medium", "hard"
    notes: str = ""

# TODO: 添加至少 20 条测试用例
TEST_CASES = [
    TestCase(
        input_text="App 打不开了，一直显示加载中",
        expected_category="技术支持",
        expected_urgency="高",
        difficulty="easy",
        notes="典型技术问题"
    ),
    # ... 更多用例
]
```

测试集要求：
- 覆盖所有 5 个类别
- 包含 easy/medium/hard 三种难度
- 至少 5 个边界模糊的案例

**3.2 评估指标实现（8 分）**

```python
# evaluation/metrics.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class EvalResult:
    """评估结果"""
    prompt_version: str
    test_set_size: int
    accuracy: float  # 分类准确率
    urgency_accuracy: float  # 紧急程度准确率
    format_compliance: float  # 格式合规率
    avg_latency_ms: float
    total_tokens: int
    error_cases: List[Dict]

def evaluate_prompt(
    client,
    test_cases: List[TestCase],
    template: PromptTemplate,
    parse_output: callable,
    prompt_version: str
) -> EvalResult:
    """
    评估一个 Prompt 版本

    Args:
        client: LLM Client
        test_cases: 测试用例列表
        template: Prompt 模板
        parse_output: 输出解析函数
        prompt_version: Prompt 版本号
    """
    # TODO: 实现评估逻辑
    # 1. 遍历测试用例
    # 2. 渲染 Prompt
    # 3. 调用 LLM
    # 4. 解析输出
    # 5. 计算指标
    # 6. 记录错误案例
    pass

def format_comparison(results: List[EvalResult]) -> str:
    """格式化对比结果为 Markdown 表格"""
    # TODO: 实现
    pass
```

**3.3 Prompt 迭代记录（4 分）**

在 `report.md` 中记录至少 3 轮 Prompt 迭代：

```markdown
## Prompt 迭代历史

| 版本 | 修改内容 | 准确率 | 格式合规率 | 迭代日期 |
|------|---------|--------|-----------|---------|
| v1 | 基础四要素 Prompt | ? | ? | ? |
| v2 | 添加 3 个 Few-shot 示例 | ? | ? | ? |
| v3 | 优化约束条件，增加边界示例 | ? | ? | ? |

### v1 -> v2 变化分析
- 修改原因：...
- 效果变化：...
- 新问题：...

### v2 -> v3 变化分析
- ...
```

**提交内容**：
- `evaluation/test_cases.py`：测试集定义
- `evaluation/metrics.py`：评估指标实现
- `evaluation/evaluate.py`：评估主程序
- `report.md`：包含迭代记录的评估报告

---

## 进阶任务（选做，20 分）

### 任务 4：动态示例选择（10 分）

实现基于输入相似度的动态示例选择。

**要求**：
1. 实现简单的文本相似度计算（如关键词匹配、词频向量）
2. 根据输入文本选择最相似的 3-5 个示例
3. 对比动态选择 vs 随机选择的效果差异

**代码骨架**：

```python
# prompts/similarity.py
from typing import List, Dict
import re
from collections import Counter

def extract_keywords(text: str) -> List[str]:
    """提取关键词（简单实现）"""
    # TODO: 分词、去停用词、提取关键词
    pass

def calculate_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度"""
    # TODO: 实现简单的相似度计算
    # 可以用 Jaccard 相似度、词频向量余弦相似度等
    pass

def select_similar_examples(
    input_text: str,
    all_examples: List[Dict],
    n: int = 5
) -> List[Dict]:
    """选择与输入最相似的示例"""
    # TODO: 实现
    pass
```

**对比实验**：

```markdown
| 选择策略 | 准确率 | 说明 |
|---------|--------|------|
| 固定示例 | ? | 使用固定的 5 个示例 |
| 随机选择 | ? | 每次随机选 5 个 |
| 相似度选择 | ? | 选择最相似的 5 个 |
```

---

### 任务 5：CoT 处理边界案例（10 分）

对边界模糊的复杂工单，使用 Chain-of-Thought 提升准确率。

**要求**：
1. 从测试集中挑选 5-8 个边界模糊的案例
2. 设计 CoT Prompt（显式步骤）
3. 对比使用 CoT 前后的效果

**CoT Prompt 设计**：

```yaml
# templates/prompts_cot.yaml
templates:
  - name: ticket_classify_cot
    role: "你是一个客服工单分类助手"
    task: "判断以下工单应该分到哪个部门"
    constraints:
      - "按照步骤逐步分析"
      - "最后只输出 JSON 结果"
    output_format: |
      分析过程：
      1. 用户遇到的问题：...
      2. 核心诉求：...
      3. 最适合的部门：...
      4. 紧急程度判断：...

      最终结果：
      {"category": "...", "urgency": "...", "confidence": ...}
    cot_steps:
      - "用户遇到了什么问题？"
      - "问题的核心诉求是什么？"
      - "哪个部门最适合处理这个诉求？"
      - "紧急程度如何判断？"
```

**对比表格**：

```markdown
| 工单内容 | 无 CoT 结果 | CoT 结果 | 正确答案 |
|---------|-----------|---------|---------|
| ... | ? | ? | ? |
```

---

## AI 协作练习（可选）

Week 02 处于"观察期"，AI 只能提供候选代码，不替学生下结论。

如果你使用 AI 工具辅助完成作业，需要额外提交：

### AI 审查报告

**1. 记录 AI 建议**

记录 AI 给出的 Prompt 设计建议或代码实现：

```markdown
## AI 建议记录

### 场景 1：Prompt 设计
- AI 建议："使用更具体的角色定义，比如'你是一个有 5 年经验的客服分类专家'"
- 我的判断：采纳/部分采纳/拒绝
- 原因：...

### 场景 2：Few-shot 示例选择
- AI 建议：...
- 我的判断：...
- 原因：...
```

**2. 审查清单**

对 AI 生成的 Prompt 进行人工审查：

```markdown
## Prompt 审查清单

### Prompt：ticket_classify_v2

- [ ] 四要素完整？
  - 角色：有/无
  - 任务：有/无
  - 约束：有/无，是否足够具体
  - 格式：有/无，是否可解析

- [ ] 约束条件是否覆盖边界情况？
  - 不确定时的处理：有/无
  - 多类别情况：有/无
  - 输出格式异常：有/无

- [ ] Few-shot 示例是否合理？
  - 覆盖所有类别：是/否
  - 格式一致：是/否
  - 无明显偏见：是/否

- [ ] 实际测试效果？
  - 准确率：?
  - 格式合规率：?
  - 发现的问题：...

### 我的修订
基于审查，我对 AI 生成的 Prompt 做了以下修改：
1. ...
2. ...
```

**重要**：AI 协作部分不影响基础任务的评分，但需要展示你的人工审查过程。

---

## 提交清单

在提交作业前，请确认以下内容：

### 文件结构
```
week02_作业_你的姓名/
├── prompts/
│   ├── __init__.py
│   ├── templates.py      # Prompt 模板类
│   └── examples.py       # Few-shot 管理器
├── templates/
│   └── prompts.yaml      # 模板配置
├── examples/
│   └── classify_examples.yaml  # Few-shot 示例
├── evaluation/
│   ├── test_cases.py     # 测试集
│   ├── metrics.py        # 评估指标
│   └── evaluate.py       # 评估主程序
├── report.md             # 评估报告（含迭代记录）
└── README.md             # 简要说明
```

### 质量检查
- [ ] 所有代码都能独立运行
- [ ] API Key 没有硬编码
- [ ] 三个 Prompt 模板都包含四要素
- [ ] Few-shot 示例至少 5 个，覆盖所有类别
- [ ] 测试集至少 20 条
- [ ] report.md 包含至少 3 轮迭代记录
- [ ] 有运行输出或截图证明代码能工作

---

## 常见问题

**Q：测试集的标注从哪里来？**

A：自己标注即可。用你作为人类的判断来标注"正确答案"——这也是建立 LLM 评估直觉的过程。

**Q：准确率多少算"好"？**

A：没有统一标准。对于 5 分类任务，随机猜测是 20%，简单规则可能 50-60%，好的 Prompt 通常能达到 70-85%。关键是看迭代是否有效——每次修改是否真的变好了。

**Q：Few-shot 示例越多越好吗？**

A：不一定。示例太多会增加 Token 消耗，而且边际收益递减。通常 3-5 个高质量示例比 10 个低质量示例效果好。

**Q：我没有 LLM API Key 怎么办？**

A：可以使用国产 LLM（智谱、通义千问、DeepSeek 等），接口大多兼容 OpenAI 格式。也可以在作业中用模拟输出来演示流程。

**Q：CoT 什么时候该用，什么时候不该用？**

A：简单明确的任务不需要 CoT——会增加延迟和成本。只有当任务需要多步推理、边界模糊、或者你需要可解释性时才用。

---

## 评分重点

本次作业的评分重点：

1. **工程化思维**：不是"写几个 Prompt"，而是"搭建一个可管理的 Prompt 系统"
2. **评估驱动**：每一次迭代都有数据支撑，不是"感觉变好了"
3. **完整性**：四要素、Few-shot、评估流程缺一不可
4. **可复现性**：别人拿到你的代码能跑起来

记住老潘说的："在公司里，我们不会只靠'感觉'判断 Prompt 好不好，要有测试集和量化指标。"

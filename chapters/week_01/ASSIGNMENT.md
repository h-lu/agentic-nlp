# Week 01 作业：LLM API 实战

**环境要求**：Python 3.9+（代码使用了 `list[str]` 等现代类型注解语法）

本周你学会了用 LLM API 完成文本处理任务。现在是时候把这些知识变成你能独立完成的技能了。

**重要提示**：本作业不要求使用任何 AI 工具。你需要亲手敲每一行代码，调试每一个错误——这是建立 LLM 调用直觉的必经之路。

---

## 基础任务（必做）

### 任务 1：第一次 API 调用（20 分）

完成你的第一次 LLM API 调用。

**要求**：
1. 安装 `openai` 库
2. 正确设置 API Key（使用环境变量，不要写在代码里）
3. 调用 GPT-4o 或其他可用模型，发送一条简单消息
4. 打印模型返回的内容

**代码骨架**（补全并运行）：

```python
from openai import OpenAI

# TODO: 初始化客户端（API Key 应该从哪里来？）
client = ...

# TODO: 发起一次对话
completion = client.chat.completions.create(
    model="gpt-4o",  # 或其他可用模型
    messages=[
        # TODO: 填写 system 和 user 消息
    ],
    temperature=0,
)

# TODO: 打印结果
```

**提交内容**：
- 完整的 Python 代码（`.py` 文件）
- 运行截图或终端输出（证明代码能跑通）

**常见错误自查**：
- `AuthenticationError`：检查 API Key 是否正确设置
- `RateLimitError`：等待几秒后重试
- `APIError`：检查模型名称是否正确

---

### 任务 2：文本分类（20 分）

用 LLM 完成一次文本分类任务。

**场景**：你有一批用户评论，需要判断情感倾向（正面/负面/中性）。

**要求**：
1. 编写一个 `classify_sentiment(text)` 函数
2. 使用合适的 system message 引导模型输出
3. 处理至少 5 条测试评论
4. 统计并打印各类别的数量

**测试数据**：

```python
reviews = [
    "这个产品真的太棒了，强烈推荐！",
    "质量一般，凑合用吧。",
    "太差了，完全是浪费钱，千万别买！",
    "物流很快，包装也很好，五星好评。",
    "和描述不符，有点失望。",
    "性价比很高，下次还会回购。",
    "不知道怎么说，还行吧。",
    "客服态度很差，不会再来了。",
]
```

**预期输出示例**：

```
评论 1：这个产品真的太棒了... -> 正面
评论 2：质量一般，凑合用吧。 -> 中性
...
统计：正面 3，中性 2，负面 3
```

**提交内容**：
- 完整的 Python 代码
- 运行输出（分类结果和统计）

---

### 任务 3：成本估算（20 分）

在运行大规模任务前，先算一笔账。

**场景**：你要处理 5000 条新闻，每条平均 400 字。任务包括：
- 分类：Prompt 约 80 Token，输出约 3 Token
- 摘要：Prompt 约 80 Token，输出约 60 Token

**要求**：
1. 编写一个成本估算函数 `estimate_cost(...)`
2. 分别计算两个任务的成本
3. 使用 GPT-4o 和 GPT-4o-mini 两种模型的价格对比
4. 输出详细估算结果

**价格参考（2026 年 2 月）**：

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| GPT-4o | $2.50 / 1M tokens | $10.00 / 1M tokens |
| GPT-4o-mini | $0.15 / 1M tokens | $0.60 / 1M tokens |

**代码骨架**：

```python
def estimate_cost(
    num_items: int,
    input_tokens_per_item: int,
    output_tokens_per_item: int,
    input_price: float,  # $/1M tokens
    output_price: float,  # $/1M tokens
) -> float:
    """估算成本（美元）"""
    # TODO: 实现估算逻辑
    pass

# 中文 Token 估算：约 1.5-2 个中文字符 = 1 Token（即 Token 数 ≈ 字数 ÷ 1.75）
AVG_CHARS_PER_TOKEN = 1.75

# TODO: 计算并打印结果
```

**提交内容**：
- 完整的 Python 代码
- 估算结果（包含两种模型的对比）

---

## 进阶任务（选做）

### 任务 4：封装 LLM Client 类（15 分）

把重复的代码封装起来，提高复用性。

**要求**：
1. 创建一个 `LLMClient` 类
2. 实现以下方法：
   - `__init__(api_key, model, temperature)`：初始化
   - `call(user_message, system_message)`：通用调用方法
   - `classify(text, categories)`：分类便捷方法
   - `summarize(text, max_words)`：摘要便捷方法
3. 包含基本的错误处理（try-except）
4. 支持通过 `base_url` 参数切换到其他兼容 OpenAI 的 LLM

**代码骨架**：

```python
import os
from openai import OpenAI, APIError, RateLimitError

class LLMClient:
    """统一的 LLM API 客户端"""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "gpt-4o",
        temperature: float = 0,
    ):
        # TODO: 初始化客户端
        pass
    
    def call(self, user_message: str, system_message: str = "你是一个有帮助的助手。") -> str:
        """发起一次 LLM 调用"""
        # TODO: 实现
        pass
    
    def classify(self, text: str, categories: list[str]) -> str:
        """文本分类"""
        # TODO: 使用 self.call 实现
        pass
    
    def summarize(self, text: str, max_words: int = 100) -> str:
        """文本摘要"""
        # TODO: 使用 self.call 实现
        pass
```

**提交内容**：
- 完整的类代码
- 使用示例（展示如何调用各方法）
- 运行输出

---

### 任务 5：实体抽取与 JSON 解析（15 分）

让 LLM 输出结构化数据，并解析它。

**要求**：
1. 编写 `extract_entities(text)` 函数，让 LLM 输出 JSON 格式的实体
2. 使用 `json.loads()` 解析 LLM 返回的 JSON
3. 处理解析失败的情况（try-except）
4. 从一段新闻中抽取：公司、人名、地点、数字

**测试数据**：

```python
news = """
特斯拉 CEO 埃隆·马斯克今天宣布，公司将在上海建设第二座超级工厂，
预计投资 50 亿美元，年产能达到 100 万辆电动汽车。
这一消息公布后，特斯拉股价在纳斯达克上涨 4.2%。
"""
```

**预期输出**：

```python
{
    "companies": ["特斯拉"],
    "people": ["埃隆·马斯克"],
    "locations": ["上海", "纳斯达克"],
    "numbers": ["50 亿美元", "100 万辆", "4.2%"]
}
```

**提交内容**：
- 完整的 Python 代码
- 运行输出（JSON 解析结果）
- 错误处理代码（处理 JSON 解析失败的情况）

---

## 挑战任务（加分）

### 任务 6：多模型对比实验（10 分）

同一个任务，用不同模型跑一遍，对比效果和成本。

**要求**：
1. 选择 5 条有代表性的评论（包含正面、负面、中性）
2. 分别用 GPT-4o 和 GPT-4o-mini（或其他小模型）进行分类
3. 记录每次调用的 Token 消耗
4. 对比：准确率、成本、响应时间

**提交内容**：
- 实验代码
- 对比表格（Markdown 格式）
- 简短分析：两个模型在你的测试集上表现如何？成本差距多大？

---

### 任务 7：Token 计数验证（5 分）

用 `tiktoken` 验证我们对 Token 数的估算是否准确。

**要求**：
1. 安装 `tiktoken` 库
2. 选取 10 段不同长度的中文文本
3. 用 tiktoken 计算 Token 数，与"字数 / 1.75"估算值对比
4. 计算平均误差率

**代码骨架**：

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")

texts = [
    "这是一段测试文本。",
    # ... 添加更多测试文本
]

for text in texts:
    actual_tokens = len(enc.encode(text))
    estimated_tokens = len(text) / 1.75
    error_rate = abs(actual_tokens - estimated_tokens) / actual_tokens
    print(f"文本：{text[:20]}... | 实际：{actual_tokens} | 估算：{estimated_tokens:.1f} | 误差：{error_rate:.1%}")
```

**提交内容**：
- 完整代码
- 10 段文本的对比结果
- 平均误差率

---

## AI 协作练习（可选）

[Week 01 属于观察期，不设置 AI 协作练习]

---

## 提交清单

在提交作业前，请确认以下内容：

- [ ] 所有代码都能独立运行（不依赖未说明的文件或配置）
- [ ] API Key 没有硬编码在任何文件中
- [ ] 每个任务都有运行输出/截图
- [ ] 代码有基本的注释说明逻辑
- [ ] 文件命名清晰（如 `task1_basic_call.py`、`task4_client.py`）

**提交方式**：将所有文件打包为 `week01_作业_你的姓名.zip` 提交。

---

## 常见问题

**Q：我没有 OpenAI API Key 怎么办？**

A：可以使用国产 LLM 的 API（智谱、通义千问、DeepSeek 等），它们的接口大多兼容 OpenAI 格式。只需要修改 `base_url` 和 `api_key` 即可。

**Q：API 调用报错怎么办？**

A：按以下顺序排查：
1. 检查 API Key 是否正确
2. 检查模型名称是否正确
3. 检查网络连接
4. 查看错误信息，搜索解决方案

**Q：成本估算的 Token 数怎么确定？**

A：使用 `tiktoken` 库可以精确计算。如果没有安装，可以用"字数 / 1.75"粗略估算中文文本的 Token 数。

**Q：代码运行很慢怎么办？**

A：LLM API 调用本身有网络延迟，这是正常的。如果特别慢，检查网络状况或尝试换一个 API 端点。

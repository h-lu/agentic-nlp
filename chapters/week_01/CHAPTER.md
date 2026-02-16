# Week 01：从文本处理到 LLM 时代 —— 范式转变与 API 实践

> "The best way to predict the future is to invent it."
> — Alan Kay

2024 到 2025 年间，一个曾经被反复讨论的问题终于有了明确答案：LLM 是昙花一现的玩具，还是能真正进入生产力的工具？数据给出了结论。OpenAI 的企业版用户从 2024 年初的 15 万增长到年底的 60 万，ChatGPT 周活跃用户突破 8 亿。与此同时，国产大模型在 API 价格战中把调用成本压到几乎"不要钱"的程度——智谱 GLM 的 API 价格在 2024 年下降了 80%，1 块钱能写上万条小红书内容。更戏剧性的是 2025 年 1 月，DeepSeek-R1 以开源姿态登场，在推理能力上对标 OpenAI o1，成本却只有对方的 5% 到 10%。这些变化的共同指向是：调用 LLM API 不再是技术 demo，而是日常开发的常规操作。

但范式转变不只是换工具。三年前你做文本分类，需要收集数据、分词、训练模型、评估、部署；现在你只需要写一个 Prompt，调用一次 API。门槛降低了，但对"怎么用好这个工具"的要求反而更高了——因为模型不会读心，它只会理解你写的 Prompt。这周我们从最基础的问题开始：LLM 时代的文本处理，和以前有什么不同？你需要先建立一个新心智模型，再动手写第一行代码。

<!--
================================================================================
【章节规划元数据】
================================================================================

## 本章学习目标

读者学完本章后能够：
1. 理解从"训练模型"到"调用 API"的范式转变及其背后的原因
2. 使用 OpenAI 或国产 LLM API 完成基础文本处理任务
3. 封装一个统一、可复用的 LLM Client 类
4. 用 LLM 完成三种文本任务：分类、摘要、实体抽取
5. 建立 Token 计费意识，理解成本优化的基本原则

## 认知负荷预算

本周新概念（预算：4 个）：
1. 范式转变（Paradigm Shift）— 从训练到调用
2. Token（词元）— LLM 计费和上下文的基本单位
3. API 封装（API Wrapper）— 统一接口设计模式
4. 结构化输出（Structured Output）— JSON Mode / Function Calling

结论：✅ 在预算内（4 个 = 上限 4 个）

Week 01 豁免回顾桥要求。

================================================================================
-->

---

## 本章学习目标

学完本章，你将能够：

- 说清楚为什么 LLM 时代做文本分析，和三年前完全不是一个思路
- 用 OpenAI 或国产 LLM 的 API 完成文本分类、摘要、实体抽取
- 封装一个统一的 LLM Client，不用每次都重复写错误处理
- 知道每次调用花了多少钱，以及怎么省

---

<!--
================================================================================
【章节结构骨架】
================================================================================

本章共 5 个主要小节 + 1 个 TextAgent 进度 + 固定结尾板块

## 第 1 节：为什么现在做 NLP 的方式变了？
- 学习目标：理解范式转变的背景和原因
- Bloom 层次：理解
- 叙事入口：从"想做一个情感分类器"的真实场景出发，对比两种方法的体验

## 第 2 节：用 LLM 写第一行代码
- 学习目标：成功调用 LLM API 并理解基本参数
- Bloom 层次：应用
- 叙事入口：亲手敲出第一个能跑的 LLM 调用

## 第 3 节：不只是聊天 —— LLM 的三种文本处理能力
- 学习目标：用 LLM 完成分类、摘要、实体抽取
- Bloom 层次：应用
- 叙事入口：展示 LLM 不只是"对话"，而是文本处理的通用引擎

## 第 4 节：封装你的 LLM Client
- 学习目标：设计一个统一的 API 封装类
- Bloom 层次：应用 + 分析
- 叙事入口：从"每次都复制粘贴 try-except"的痛点出发

## 第 5 节：知道你花了多少钱
- 学习目标：理解 Token 计费和基础成本优化
- Bloom 层次：理解 + 应用
- 叙事入口：收到第一笔 API 账单时的"惊喜"

## AI 时代小专栏 1（第 1-2 节之间）
- 主题：LLM API 的成本之战 —— 2024-2025 的价格革命
- 与相邻章节关联：呼应第 1 节的范式转变，为第 2 节的 API 调用提供现实背景

## AI 时代小专栏 2（第 3-4 节之间）
- 主题：当 LLM 遇到结构化数据 —— 从"差不多就行"到"必须准确"
- 与相邻章节关联：呼应第 3 节的文本处理，为第 4 节的封装和结构化输出铺垫

## TextAgent 进度
- 本周目标：搭建项目框架和 LLM 调用层
- 占正文 20-30%

## 结尾板块
- Git 本周要点
- 本周小结

================================================================================
-->

<!--
================================================================================
【循环角色出场规划】
================================================================================

出场次数：3 次（要求：每章至少 2 次）✅

| 角色 | 出场位置 | 场景设计 | 推动叙事的作用 |
|------|---------|---------|---------------|
| 小北 | 第 2 节 | 第一次调用 API 时忘记设置 API Key，报错后慌张 | 让读者看到"新手常见错误"，降低试错心理负担 |
| 阿码 | 第 3 节 | 追问"为什么 LLM 输出有时候是 JSON 有时候是自然语言？边界在哪？" | 引出结构化输出的需求，为第 4 节铺垫 |
| 老潘 | 第 5 节 | 点评成本优化："在公司里，我们不会每次都调 GPT-4，简单任务用小模型就够了，成本差十倍" | 带入工程视角，强调成本意识 |

角色性格一致性检查：
- 小北：犯新手错误 + 需要鼓励 ✅
- 阿码：追问边界问题 + 举一反三 ✅
- 老潘：务实 + 工程经验 + "在公司里"口头禅 ✅

================================================================================
-->

<!--
================================================================================
【AI 小专栏规划】
================================================================================

### AI 时代小专栏 1：LLM API 的成本之战 —— 2024-2025 的价格革命

位置：第 1-2 节之间（章节前段）

与相邻章节关联：
- 呼应第 1 节的范式转变："为什么现在人人都能用 LLM？不只是技术进步，还有成本骤降"
- 为第 2 节的 API 调用提供现实背景："你现在能用得起这个，是因为过去一年发生了什么"

核心内容方向：
- 2024-2025 年间 LLM API 价格的变化（需搜索具体数据）
- OpenAI vs 国产 LLM 的价格竞争
- DeepSeek 等开源模型的成本革命
- "API 调用"从奢侈品变成日常工具的历史意义

建议搜索词（含当前年份）：
- "LLM API price drop 2024 2025"
- "GPT-4 pricing history 2024"
- "DeepSeek R1 cost comparison 2025"
- "中国大模型 API 价格战 2024 2025"
- "智谱 GLM-4 API 定价"

参考链接要求：必须来自 WebSearch 搜索结果，禁止编造

---

### AI 时代小专栏 2：当 LLM 遇到结构化数据 —— 从"差不多就行"到"必须准确"

位置：第 3-4 节之间（章节中段）

与相邻章节关联：
- 呼应第 3 节的文本处理："LLM 生成自然语言很厉害，但如果你需要的是结构化数据呢？"
- 为第 4 节的封装和结构化输出铺垫："所以我们需要 JSON Mode 和 Function Calling"

核心内容方向：
- JSON Mode 的出现解决了什么问题
- Function Calling / Tool Use 的原理和价值
- Pydantic 等数据验证框架与 LLM 的结合
- 企业应用中对"准确输出"的需求（示例：合同信息抽取、报表生成）

建议搜索词（含当前年份）：
- "OpenAI JSON mode structured output 2024 2025"
- "LLM function calling best practices 2025"
- "Pydantic LLM validation 2025"
- "LLM structured output enterprise applications 2024"

参考链接要求：必须来自 WebSearch 搜索结果，禁止编造

================================================================================
-->

<!--
================================================================================
【贯穿案例设计】
================================================================================

本章贯穿案例：新闻文本处理 Pipeline

案例场景：
你刚加入一家做舆情监控的初创公司，老板让你"先做一个能跑的原型"：把每天抓取的新闻文本做分类、摘要、实体抽取，然后存进数据库。

案例演进路线：
- 第 1 节：讨论"为什么不用传统的 BERT 微调"——因为数据不够、迭代太慢、部署复杂
- 第 2 节：用 LLM API 测试单条新闻的分类
- 第 3 节：扩展到三种任务（分类、摘要、抽取），用一个新闻样本演示
- 第 4 节：把三种任务的调用封装成统一的 Client 类
- 第 5 节：计算处理 1000 条新闻的成本，讨论优化策略

每节结束时的"可交付物"：
- 第 1 节：技术选型的决策理由（写在代码注释里）
- 第 2 节：一个能跑的单次 LLM 调用
- 第 3 节：三个任务的 Prompt 和调用代码
- 第 4 节：一个完整的 LLM Client 类
- 第 5 节：一份成本估算报告

================================================================================
-->

<!--
================================================================================
【TextAgent 超级线规划】
================================================================================

本周 TextAgent 进度：项目初始化 + LLM 调用层

具体任务：
1. 搭建项目结构
   - src/textagent/
     - __init__.py
     - client.py (LLM Client 类)
     - tasks.py (分类、摘要、抽取任务)
   - tests/
     - test_client.py
   - docs/
     - README.md

2. 封装统一的 LLM Client 类
   - 支持多 LLM 后端（OpenAI、智谱）
   - 统一的错误处理（重试、超时、限流）
   - 日志记录（请求、响应、Token 消耗）

3. 实现基础文本分析功能
   - classify_text(text, categories) -> str
   - summarize_text(text, max_length) -> str
   - extract_entities(text, entity_types) -> list[dict]

4. 生成最小可用 report.md
   - 项目概述
   - 技术选型理由
   - 初步测试结果（准确率/成本/延迟）

与本周知识点的关联：
- 第 2 节的 API 调用代码 → client.py 的核心逻辑
- 第 3 节的三种任务 → tasks.py 的三个函数
- 第 4 节的封装思路 → Client 类的设计
- 第 5 节的成本意识 → report.md 中的成本分析

================================================================================
-->

<!--
================================================================================
【锚点规划（供 ANCHORS.yml 参考）】
================================================================================

本章需要验证的核心结论（锚点）：

1. 【anchor:llm-vs-traditional】
   claim: 对于小样本（<100 条）文本分类任务，LLM API 调用的开发周期比传统 BERT 微调短 10 倍以上
   evidence: 对比两种方法的代码量和步骤
   verification: 在 tests/ 中提供计时对比脚本

2. 【anchor:api-call-basic】
   claim: 成功调用 OpenAI Chat Completions API 需要三个必要参数：model、messages、api_key
   evidence: 最小可运行代码示例
   verification: tests/test_client.py 中的 test_basic_call

3. 【anchor:token-counting】
   claim: 中文文本的 Token 数约为字数的 1.5-2 倍（取决于模型和切词方式）
   evidence: 用 tiktoken 库计算多个中文样本的 Token 数
   verification: tests/test_token_counting.py

4. 【anchor:structured-output】
   claim: 使用 JSON Mode 可以让 LLM 输出稳定可解析的 JSON 格式，准确率 >95%
   evidence: 10 个样本的结构化输出测试
   verification: tests/test_structured_output.py

================================================================================
-->

<!--
================================================================================
【每节详细规划】
================================================================================
-->

## 第 1 节：100 条新闻，两种选择 —— 为什么现在做 NLP 的方式变了？

假设你刚加入那家做舆情监控的初创公司。老板丢给你一份 Excel：100 条新闻，每条已经标好了类别（财经、体育、科技、娱乐）。你的任务是：做一个分类器，以后每天抓到的新闻能自动归到这四个类。

三年前，你会怎么做？

大概是这么一个流程：先把文本分词，用 TF-IDF 或者训练一个 Word2Vec 把词变成向量，然后搭一个分类模型——逻辑回归、SVM、或者时髦一点的 BERT 微调。接着划分训练集验证集，调参，看准确率到 85% 还是 90%。最后把模型打包，找一台有 GPU 的服务器部署上去。整个过程，顺利的话两周，遇到坑的话一个月。

这方法没错。但问题来了：你只有 100 条标注数据。这点数据训练 BERT，大概率过拟合；用传统方法，又需要大量特征工程。更要命的是，两周后老板说："我们加两个新类别：教育和健康，顺便把分类标准改一下。"你得重新收集数据、重新训练、重新部署。

现在换一种思路。

你打开 LLM 的 API 文档，写一段 Prompt：

```text
你是一个新闻分类助手。请判断以下新闻属于哪个类别：
- 财经
- 体育
- 科技
- 娱乐

新闻内容：{新闻文本}

只输出类别名称，不要解释。
```

然后调用 API，把新闻文本填进去，拿到结果。整个过程，10 分钟就能跑通第一个版本。老板要改分类标准？改 Prompt 就行，5 分钟。要加新类别？在列表里加两个字。

这就是**范式转变**（Paradigm Shift）：从"训练模型"到"设计系统"。你不再需要花大量时间在模型训练上，而是把精力放在：怎么写好 Prompt、怎么设计调用流程、怎么处理返回结果。

两种方法的对比，可以这么看：

| 维度 | 传统方法 | LLM 方法 |
|------|---------|----------|
| 数据需求 | 需要大量标注数据（通常 1000+ 条） | 少量示例即可（Few-shot，甚至 Zero-shot） |
| 开发周期 | 以周计 | 以小时计 |
| 部署复杂度 | 需要 GPU 服务器 | 只需要 HTTP 请求 |
| 迭代速度 | 改数据、重训练、重部署 | 改 Prompt，立刻生效 |
| 可解释性 | 有特征权重，能看"为什么" | 黑盒，但可以用 Prompt 引导解释 |
| 成本结构 | 前期投入大（服务器、标注），边际成本低 | 前期投入小，按调用付费 |

但别误会——不是说传统方法没用了。如果你有几万条标注数据、对准确率要求极高、而且分类标准长期不变，传统方法仍然是更经济的选择。LLM 方法的优势在于：快速验证、灵活迭代、低门槛启动。

理解了"为什么变"，下一步是"怎么变"——我们来写第一行 LLM 调用代码。

> **AI 时代小专栏：LLM API 的成本之战 —— 2024-2025 的价格革命**
>
> 你刚才看到的"10 分钟跑通一个分类器"，在两年前是要花真金白银的。2023 年初，调用 GPT-4 处理 100 万 Token 输出要花 60 美元；如果你每天处理 1 万条新闻，一个月下来光 API 费用就得几千美元。那时候，LLM 确实像是"奢侈品"。
>
> 然后价格战开始了。2024 年 8 月，GPT-4 的输出价格已经从 60 美元降到 10 美元，降幅 83%。更戏剧性的是 2025 年 1 月，DeepSeek-R1 以开源姿态登场，推理能力对标 OpenAI o1，成本却只有对方的 2% 到 5%——同样 100 万 Token 输出，DeepSeek-R1 收 2.19 美元，o1 收 60 美元，差距 25 倍以上。
>
> 这意味着什么？意味着"调用 LLM API"从"需要审批的预算项"变成了"像调用数据库一样日常"。你现在能用 1 美元处理上千条文本，这在两年前是不可想象的。范式转变的背后，不只是技术进步，还有成本的断崖式下跌。
>
> 参考（访问日期：2026-02-16）：
> - https://cloudatler.com/blog/deepseek-r1-vs-openai-o1-cost-comparison
> - https://www.datacamp.com/blog/deepseek-r1
> - https://epoch.ai/data-insights/llm-inference-price-trends

## 第 2 节：让 LLM 开口说话 —— 你的第一次 API 调用

概念说得再多，不如亲手敲一次代码。我们直接用 OpenAI 的 API 来做一次调用。如果你用的是国产 LLM（智谱、通义千问、DeepSeek），代码结构几乎一样，后面会讲怎么切换。

首先安装依赖：

```bash
pip install openai
```

然后是第一行能跑的代码：

```python
from openai import OpenAI

# 初始化客户端 —— 它会自动从环境变量 OPENAI_API_KEY 读取
client = OpenAI()

# 发起一次调用
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个新闻分类助手。"},
        {"role": "user", "content": "今天沪指大涨 3%，创下半年新高。这条新闻属于什么类别？只输出类别名称。"},
    ],
    temperature=0,
)

print(completion.choices[0].message.content)
# 输出：财经
```

运行这段代码，你应该看到"财经"两个字。

如果你看到的是 `AuthenticationError`，别慌——小北第一次跑也遇到了。问题大概率出在 API Key 没设置好。

```text
小北：等等，这报错是什么意思？我是不是哪里打错了……

你：检查一下环境变量。API Key 需要设置到 OPENAI_API_KEY 里。
```

**设置 API Key 的正确姿势**：永远不要把它写在代码里。你可以在终端里设置环境变量：

```bash
# macOS / Linux
export OPENAI_API_KEY="sk-..."

# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."
```

或者更推荐的做法是用 `.env` 文件 + `python-dotenv`：

```bash
# .env 文件（记得加到 .gitignore！）
OPENAI_API_KEY=sk-...
```

```python
# 代码里加载
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件
```

### messages 参数详解

`messages` 是一个列表，每条消息有三个关键字段：

- **role**：角色，可以是 `system`（系统设定）、`user`（用户输入）、`assistant`（模型历史回复）
- **content**：具体内容

`system` 消息用来设定 LLM 的"角色"和"行为边界"。你可以把它理解成给演员的剧本大纲。`user` 消息是具体的任务输入。

为什么要把 system 和 user 分开？因为这样可以复用 system 设定，只改 user 内容。比如处理 100 条新闻时，system 只发一次，user 每条新闻换一个。

### temperature 参数

`temperature` 控制输出的随机性，范围 0-2，默认 1：

- **temperature=0**：几乎确定性输出。同样的输入，每次调用结果基本一致。适合分类、抽取等"有标准答案"的任务。
- **temperature=0.7-1**：有一定随机性，但还比较连贯。适合日常对话。
- **temperature>1.5**：更随机，可能产生意想不到的创意，但也更容易跑题。

对于新闻分类这种任务，用 `temperature=0` 是合理的选择。

### 错误处理

网络请求总会出问题。API 调用可能遇到：认证失败、请求超时、服务器限流、网络断开。你需要把这些异常兜住：

```python
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

client = OpenAI()

try:
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "你好"}
        ]
    )
    print(completion.choices[0].message.content)

except AuthenticationError as e:
    print(f"认证失败，请检查 API Key：{e}")
except RateLimitError as e:
    print(f"请求太快被限流了，等几秒再试：{e}")
except APIError as e:
    print(f"服务器出问题了：{e.status_code} - {e.message}")
except Exception as e:
    print(f"未知错误：{e}")
```

现在你能让 LLM 说话了。但除了"聊天"，它还能帮你做什么？下一节我们看三种具体的文本处理任务。

## 第 3 节：不只是聊天 —— 让 LLM 做分类、摘要和抽取

很多人以为 LLM 就是聊天机器人。其实它更像一个"文本处理器"——给它文本，告诉它你想要什么格式的输出，它就能按你的要求加工。

在舆情监控的场景里，你需要三种核心能力：分类、摘要、实体抽取。我们用同一条新闻来演示。

先准备一条示例新闻：

```python
news_text = """
苹果公司今天发布了 2025 财年第一季度财报。财报显示，公司营收达到 1243 亿美元，
同比增长 4%。iPhone 业务贡献了 697 亿美元收入，超出分析师预期。苹果 CEO 蒂姆·库克
表示，对中国市场的发展势头感到乐观。财报发布后，苹果股价在盘后交易中上涨 2.3%。
"""
```

### 任务一：文本分类

```python
from openai import OpenAI

client = OpenAI()

def classify_news(text: str) -> str:
    """对新闻进行分类"""
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "你是一个新闻分类助手。请将新闻分类到以下类别之一：财经、科技、体育、娱乐、教育、健康。只输出类别名称，不要解释。"
            },
            {"role": "user", "content": text}
        ],
        temperature=0,
    )
    return completion.choices[0].message.content

category = classify_news(news_text)
print(f"分类结果：{category}")
# 输出：分类结果：财经（或者"科技"，取决于模型判断，都有道理）
```

### 任务二：文本摘要

```python
def summarize_news(text: str, max_words: int = 50) -> str:
    """生成新闻摘要"""
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"你是一个新闻摘要助手。请将新闻压缩成 {max_words} 字以内的摘要，保留关键信息：谁、什么事、多少、变化趋势。"
            },
            {"role": "user", "content": text}
        ],
        temperature=0,
    )
    return completion.choices[0].message.content

summary = summarize_news(news_text)
print(f"摘要：{summary}")
# 输出示例：苹果发布 2025Q1 财报，营收 1243 亿美元同比增长 4%，
#          iPhone 收入 697 亿美元超预期。CEO 库克看好中国市场，股价盘后涨 2.3%。
```

### 任务三：实体抽取

```python
def extract_entities(text: str) -> str:
    """从新闻中抽取关键实体"""
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """你是一个实体抽取助手。请从新闻中抽取以下类型的实体，以 JSON 格式输出：
{
    "companies": ["公司名称"],
    "people": ["人名"],
    "products": ["产品名"],
    "locations": ["地名"],
    "metrics": ["关键数字和指标"]
}
如果某类实体不存在，输出空列表。只输出 JSON，不要其他内容。"""
            },
            {"role": "user", "content": text}
        ],
        temperature=0,
    )
    return completion.choices[0].message.content

entities_json = extract_entities(news_text)
print(entities_json)
# 输出：
# {
#     "companies": ["苹果公司"],
#     "people": ["蒂姆·库克"],
#     "products": ["iPhone"],
#     "locations": ["中国"],
#     "metrics": ["1243亿美元", "4%", "697亿美元", "2.3%"]
# }
```

三个任务的代码结构几乎一样：只有 system message 不同。这就是 LLM 的魅力——同一个模型，不同的 Prompt，就能完成不同的任务。

```text
阿码追问：我发现有时候输出是 JSON，有时候是自然语言，怎么控制？边界在哪？

好问题。输出格式主要靠 system message 约束。如果你明确说"只输出 JSON"，大概率能得到 JSON；
但如果你说"请分析一下"，它可能给你一段话。边界在于：你的指令越具体，输出越稳定。
下一节我们会讲更"硬"的控制方式——JSON Mode 和 Pydantic 验证。
```

你现在能做三种任务了，但每次都要写一大段 Prompt 和 try-except，太累了。下一节我们来封装一个统一的 Client 类。

> **AI 时代小专栏：当 LLM 遇到结构化数据 —— 从"差不多就行"到"必须准确"**
>
> 你刚才让 LLM 输出 JSON，它确实输出了——但你能保证每次都格式正确吗？早期用 LLM 做数据抽取的人都有过这种经历：明明 Prompt 里写了"输出 JSON"，模型有时候会多加一句"以下是结果"，有时候会把字段名写错，有时候还会加注释。你的解析代码一跑就崩溃。
>
> 2024 年 8 月，OpenAI 发布了 Structured Outputs 功能，解决了这个痛点。它和之前的 JSON Mode 不一样：JSON Mode 只保证输出"是合法 JSON"，但不保证遵循你的 Schema；Structured Outputs 则强制模型严格按照你提供的 JSON Schema 输出，字段名、类型、嵌套结构都不能错。配合 Function Calling，你可以让 LLM 的输出直接对接你的代码和数据库。
>
> 这看似是个小功能，但对企业应用意义重大。合同信息抽取、报表生成、API 集成——这些场景不需要"有创意"的回答，需要的是"可解析、可验证、可追溯"的数据。从"差不多就行"到"必须准确"，LLM 终于能进入生产环境了。
>
> 参考（访问日期：2026-02-16）：
> - https://openai.com/index/introducing-structured-outputs-in-the-api/
> - https://platform.openai.com/docs/guides/structured-outputs
> - https://vellum.ai/blog/structured-outputs-vs-function-calling-vs-json-mode

## 第 4 节：别再复制粘贴了 —— 封装一个 LLM Client

你已经写了三遍 try-except，复制粘贴了三次 API 调用代码。这时候你应该想到：该封装了。

封装的目的不只是"少写代码"。更重要的是：统一错误处理、统一日志记录、方便切换 LLM 后端。如果你今天用 OpenAI，明天想换成智谱，只需要改一个地方。

### Client 类设计

```python
import os
import logging
from typing import Optional
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """统一的 LLM API 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        default_temperature: float = 0,
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API Key，如果不传则从环境变量读取
            base_url: API 地址，用于切换到其他兼容 OpenAI 接口的服务
            model: 默认使用的模型
            default_temperature: 默认温度
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未设置，请传入 api_key 参数或设置 OPENAI_API_KEY 环境变量")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,  # None 时使用 OpenAI 默认地址
        )
        self.model = model
        self.default_temperature = default_temperature

    def call(
        self,
        user_message: str,
        system_message: str = "你是一个有帮助的助手。",
        temperature: Optional[float] = None,
    ) -> str:
        """
        发起一次 LLM 调用

        Args:
            user_message: 用户输入
            system_message: 系统设定
            temperature: 温度，不传则使用默认值

        Returns:
            模型输出的文本
        """
        temp = temperature if temperature is not None else self.default_temperature

        try:
            logger.info(f"调用 LLM: model={self.model}, temperature={temp}")
            logger.debug(f"System: {system_message[:50]}...")
            logger.debug(f"User: {user_message[:50]}...")

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=temp,
            )

            result = completion.choices[0].message.content
            usage = completion.usage

            logger.info(f"调用成功: 输入 {usage.prompt_tokens} tokens, 输出 {usage.completion_tokens} tokens")
            return result

        except AuthenticationError as e:
            logger.error(f"认证失败: {e}")
            raise
        except RateLimitError as e:
            logger.error(f"请求被限流: {e}")
            raise
        except APIError as e:
            logger.error(f"API 错误: {e.status_code} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise

    def classify(self, text: str, categories: list[str]) -> str:
        """文本分类的便捷方法"""
        system = f"你是一个分类助手。请将文本分类到以下类别之一：{', '.join(categories)}。只输出类别名称，不要解释。"
        return self.call(text, system)

    def summarize(self, text: str, max_words: int = 100) -> str:
        """文本摘要的便捷方法"""
        system = f"你是一个摘要助手。请将文本压缩成 {max_words} 字以内的摘要，保留关键信息。"
        return self.call(text, system)

    def extract(self, text: str, entity_types: list[str]) -> str:
        """实体抽取的便捷方法"""
        system = f"""你是一个实体抽取助手。请从文本中抽取以下类型的实体：{', '.join(entity_types)}。
以 JSON 格式输出，格式为 {{"实体类型": ["实体1", "实体2"]}}。
如果某类实体不存在，输出空列表。只输出 JSON，不要其他内容。"""
        return self.call(text, system)
```

### 使用示例

```python
# 初始化
client = LLMClient(model="gpt-4o", default_temperature=0)

# 分类
category = client.classify(
    "苹果公司发布新款 iPhone，搭载 A18 芯片，性能提升 30%。",
    categories=["财经", "科技", "体育", "娱乐"]
)
print(f"分类：{category}")

# 摘要
summary = client.summarize(news_text, max_words=50)
print(f"摘要：{summary}")

# 实体抽取
entities = client.extract(news_text, entity_types=["公司", "人名", "产品", "地点", "数字"])
print(f"实体：{entities}")
```

### 支持多后端

如果你想切换到智谱 GLM，只需要改 `base_url` 和 `api_key`：

```python
# 智谱 GLM
zhipu_client = LLMClient(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    model="glm-4",
)

# DeepSeek
deepseek_client = LLMClient(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
    model="deepseek-chat",
)
```

这些国产 LLM 的 API 接口大多兼容 OpenAI 格式，所以你的 Client 类几乎不用改。

你的 Client 已经能稳定运行了。但在跑大规模任务之前，有一个问题需要先想清楚：这要花多少钱？

## 第 5 节：收到账单别慌 —— Token 计费与成本优化

假设老板让你处理 10000 条新闻，每条平均 500 字。在按下"运行"之前，你最好先算一下账。

### Token 是什么

LLM 的计费单位不是"字"，而是 **Token**（词元）。Token 可以理解为一个"片段"——可能是一个词、一个子词、或者一个标点符号。

对于英文，大约 4 个字符 = 1 个 Token。比如 "hello world" 是 2 个 Token。

对于中文，情况更复杂。大约 1.5-2 个汉字 = 1 个 Token（取决于模型和分词器）。比如"苹果公司发布新手机"可能是 6-8 个 Token。

### 用 tiktoken 计算 Token 数

```python
import tiktoken

# 获取编码器（不同模型用不同的编码器）
enc = tiktoken.encoding_for_model("gpt-4o")  # o200k_base 编码
enc_gpt4 = tiktoken.encoding_for_model("gpt-4")  # cl100k_base 编码

# 计算一段文本的 Token 数
text = "苹果公司今天发布了 2025 财年第一季度财报。"
tokens = enc.encode(text)
print(f"文本：{text}")
print(f"字符数：{len(text)}")
print(f"Token 数：{len(tokens)}")
# 输出示例：字符数：20，Token 数：约 15

# 英文对比
english_text = "Apple Inc. released its Q1 2025 financial report today."
print(f"英文 Token 数：{len(enc.encode(english_text))}")
```

### 计费方式

LLM 的费用分两部分：**输入 Token**（你的 Prompt）和 **输出 Token**（模型的回复）。两者价格不同，通常输出比输入贵。

以 GPT-4o 为例（2025 年价格，可能有变动）：

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| GPT-4o | $2.50 / 1M tokens | $10.00 / 1M tokens |
| GPT-4o-mini | $0.15 / 1M tokens | $0.60 / 1M tokens |
| DeepSeek-V3 | $0.14 / 1M tokens | $0.28 / 1M tokens |

### 成本估算实例

假设你要处理 1000 条新闻，每条 500 字，任务分别是：

1. **分类**：Prompt 约 100 Token + 新闻约 300 Token = 400 输入，输出约 2 Token
2. **摘要**：Prompt 约 100 Token + 新闻约 300 Token = 400 输入，输出约 80 Token
3. **实体抽取**：Prompt 约 150 Token + 新闻约 300 Token = 450 输入，输出约 50 Token

用 GPT-4o 的价格计算：

```python
# 成本估算函数
def estimate_cost(
    num_items: int,
    input_tokens_per_item: int,
    output_tokens_per_item: int,
    input_price: float = 2.50,  # $/1M tokens
    output_price: float = 10.00,  # $/1M tokens
) -> float:
    """估算成本（美元）"""
    total_input = num_items * input_tokens_per_item
    total_output = num_items * output_tokens_per_item
    cost = (total_input / 1_000_000 * input_price +
            total_output / 1_000_000 * output_price)
    return cost

# 分类任务
classify_cost = estimate_cost(1000, 400, 2)
print(f"分类 1000 条：${classify_cost:.4f}")  # 约 $1.00

# 摘要任务
summarize_cost = estimate_cost(1000, 400, 80)
print(f"摘要 1000 条：${summarize_cost:.4f}")  # 约 $1.20

# 实体抽取
extract_cost = estimate_cost(1000, 450, 50)
print(f"抽取 1000 条：${extract_cost:.4f}")  # 约 $1.60

print(f"总计：${classify_cost + summarize_cost + extract_cost:.4f}")  # 约 $3.80
```

1000 条新闻处理三遍，成本大约 4 美元。听起来不多，但如果每天都要处理呢？一个月就是 120 美元。

```text
老潘说：在公司里，我们不会每次都调 GPT-4。简单任务用小模型就够了，
成本差十倍。分类这种任务，GPT-4o-mini 甚至 DeepSeek 都能做，
为什么要用 GPT-4？

还有一个坑：很多人不知道 Prompt 本身也在烧钱。如果你写了 500 字的 system message，
每次调用都要付这 500 字的钱。把 Prompt 精简一下，能省不少。
```

### 成本优化策略

1. **模型选择**：分类、简单抽取用小模型（GPT-4o-mini、DeepSeek），复杂推理才用大模型
2. **Prompt 精简**：删掉不必要的描述，每省 100 Token 都是在省钱
3. **批量处理**：有些 API 支持批量调用，延迟高但价格低
4. **缓存复用**：如果 system message 很长且不变，部分 API 支持缓存计费更低
5. **监控成本**：设置预算上限，别等月底账单吓一跳

现在你已经掌握了 LLM API 的基本用法和成本意识。接下来，我们把这些知识应用到 TextAgent 项目中。

<!--
================================================================================
【TextAgent 进度】
================================================================================
-->

## TextAgent 进度

你现在掌握了调用 LLM API 的基本技能。是时候把这些技能整合到一个真正的项目中——TextAgent，一个会在接下来 8 周持续演进的文本分析系统。

### 项目结构

```
textagent/
├── src/
│   └── textagent/
│       ├── __init__.py
│       ├── client.py      # LLM Client 类
│       └── tasks.py       # 分类、摘要、抽取任务
├── tests/
│   └── test_client.py     # 单元测试
├── docs/
│   └── README.md          # 项目文档
├── .env.example           # 环境变量示例
├── pyproject.toml         # 依赖配置
└── report.md              # 分析报告
```

### Client 类实现

`client.py` 的核心就是我们第 4 节写的 `LLMClient` 类。这里增加一些项目特定的功能：

```python
# src/textagent/client.py
import os
import logging
from typing import Optional
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

logger = logging.getLogger(__name__)


class LLMClient:
    """TextAgent 的 LLM 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        default_temperature: float = 0,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未设置")

        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.model = model
        self.default_temperature = default_temperature
        self.total_tokens = 0  # 累计 Token 消耗

    def call(
        self,
        user_message: str,
        system_message: str = "你是一个有帮助的助手。",
        temperature: Optional[float] = None,
    ) -> str:
        temp = temperature if temperature is not None else self.default_temperature

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=temp,
            )

            result = completion.choices[0].message.content
            usage = completion.usage
            self.total_tokens += usage.total_tokens

            logger.info(f"Token 消耗: {usage.total_tokens} (累计: {self.total_tokens})")
            return result

        except (AuthenticationError, RateLimitError, APIError) as e:
            logger.error(f"API 错误: {e}")
            raise
```

### 任务方法

`tasks.py` 封装三种文本处理任务：

```python
# src/textagent/tasks.py
from .client import LLMClient


class TextTasks:
    """文本处理任务集合"""

    def __init__(self, client: LLMClient):
        self.client = client

    def classify(self, text: str, categories: list[str]) -> str:
        """分类任务"""
        system = f"你是分类助手。分类到：{', '.join(categories)}。只输出类别名。"
        return self.client.call(text, system)

    def summarize(self, text: str, max_words: int = 100) -> str:
        """摘要任务"""
        system = f"你是摘要助手。压缩到 {max_words} 字内，保留关键信息。"
        return self.client.call(text, system)

    def extract_entities(self, text: str, entity_types: list[str]) -> str:
        """实体抽取任务"""
        system = f"""抽取实体类型：{', '.join(entity_types)}。
输出 JSON：{{"类型": ["实体"]}}。只输出 JSON。"""
        return self.client.call(text, system)
```

### 使用示例

```python
from textagent import LLMClient, TextTasks

# 初始化
client = LLMClient(model="gpt-4o")
tasks = TextTasks(client)

# 处理新闻
news = "苹果公司发布 2025Q1 财报，营收 1243 亿美元..."

print(f"分类: {tasks.classify(news, ['财经', '科技', '体育'])}")
print(f"摘要: {tasks.summarize(news, 50)}")
print(f"实体: {tasks.extract_entities(news, ['公司', '人名', '数字'])}")

print(f"总 Token 消耗: {client.total_tokens}")
```

TextAgent 现在有了骨架和肌肉。下周我们会给它"大脑"——一套精心设计的 Prompt 模板库，让 LLM 更准确地理解你的需求。

<!--
================================================================================
【Git 本周要点】
================================================================================
-->

## Git 本周要点

本周必会命令：
- `git init` — 初始化仓库
- `git status` — 查看工作区状态
- `git add <file>` — 暂存文件
- `git commit -m "message"` — 提交
- `git log --oneline -n 10` — 查看提交历史

常见坑：
- **API Key 提交到 Git**：这是最危险的新手错误。使用 `.gitignore` 排除 `.env` 文件，或使用环境变量管理敏感信息。
- **只改文件不提交**：下周找不到"当时怎么改的"。至少做 draft + verify 两次提交。
- **commit message 写得太模糊**：一个月后看不懂自己改了什么。建议格式：`<type>: <description>`，如 `feat: add LLM client class`。

Pull Request (PR)：
- Gitea 上也叫 Pull Request，流程等价 GitHub：push 分支 → 开 PR → review → merge。

<!--
================================================================================
【本周小结】
================================================================================
-->

## 本周小结

这一周你做的不是"学会调用 API"，而是建立了一个新的心智模型：在 LLM 时代，文本分析从"训练模型"变成了"设计系统"。你学会了用 API 完成分类、摘要、抽取，封装了统一的 Client 类，也知道了每次调用都在烧钱——以及怎么少烧一点。

这些技能看起来简单，但它们是你接下来 7 周所有工作的基础。RAG 系统需要调用 LLM，Agent 需要调用 LLM，企业应用更是天天和 API 打交道。把这一周的基础打牢，后面才不会在"调不通 API"这种低级问题上浪费精力。

下周，我们会深入 Prompt 的设计——让 LLM 更准确地理解你的需求。你会发现，同样的 LLM，不同的 Prompt，效果可能天差地别。

<!--
================================================================================
【Definition of Done（学生自测清单）】
================================================================================
-->

## Definition of Done

学完本章后，你应该能够回答以下问题：

- [ ] 我能用一句话说清楚"LLM 时代的 NLP"和"传统 NLP"的核心差异吗？
- [ ] 我能独立完成一次 LLM API 调用（不复制代码）吗？
- [ ] 我能解释 Token 是什么，以及为什么它和"字数"不一样吗？
- [ ] 我知道怎么估算处理 1000 条文本的成本吗？
- [ ] 我的 TextAgent 项目能跑起来，并且有基本的错误处理吗？

如果以上都打勾，恭喜你完成 Week 01！下周见。

<!--
================================================================================
【术语登记（供 TERMS.yml 参考）】
================================================================================

本章新术语：
1. 范式转变（Paradigm Shift）
2. Token（词元）
3. API 封装（API Wrapper）
4. 结构化输出（Structured Output）

待合入 shared/glossary.yml

================================================================================
-->

<!--
================================================================================
【Context7 技术查证清单】
================================================================================

本章涉及的核心技术点（chapter-writer 动笔前必须查证）：

1. OpenAI Python SDK
   - 查询：openai chat completions api python 2025
   - 重点：最新的 API 接口、异步调用、流式输出

2. 智谱 AI SDK
   - 查询：zhipuai GLM-4 api python 2025
   - 重点：与 OpenAI 的兼容性、国产 LLM 特有参数

3. tiktoken
   - 查询：tiktoken token counting python 2025
   - 重点：支持哪些模型、中文 Token 计算

4. Pydantic
   - 查询：pydantic data validation python 2025
   - 重点：与 LLM 输出结合的最佳实践

================================================================================
-->

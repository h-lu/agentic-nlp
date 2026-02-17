# Week 05：让 LLM 不只是回答问题 —— 从 RAG 到 Agent

> "工欲善其事，必先利其器。"
> — 孔子

2024 年的一个午后，一位开发者演示了他刚写的"客服机器人"。演示很顺利——能回答常见问题，能查订单状态，甚至能"智能"推荐产品。但在 Q&A 环节，有人问："它能帮我退款吗？"

开发者愣了一下："这个……目前还需要人工操作。"

全场都笑了，但这种笑带着尴尬——因为所有人都意识到：我们已经让 LLM 变成了"超级搜索引擎"，但它还是不会"做事"。

2024-2025 年，情况开始改变。OpenAI、Anthropic、Google 都密集推出了 Function Calling 和 Agent 能力，让 LLM 不再只是"聊天"，而是能调用工具、规划任务、迭代反思。根据 McKinsey 2025 年的报告，约 23% 的组织已经开始扩展 agentic AI 系统，78% 的组织已在至少一个业务职能中使用 AI。这周我们来学这波浪潮的核心：让 LLM 从"回答问题"进化为"解决问题"。

---

## 前情提要

Week 04 你让 TextAgent 有了"精准检索"的能力：混合检索保证召回，重排序保证精确，RAGAS 评估让效果可量化。TextAgent 现在能从知识库中找到相关信息，并基于这些信息回答问题。但它仍然是一个"被动"的系统——你问，它答；你不问，它什么也不会做。

这周我们要让它变得更"主动"——不只是回答问题，而是会调用工具、会规划步骤、能完成多步骤任务的 LLM Agent。

---

## 本章学习目标

学完本章，你将能够：

- 理解 Agent 与 Chatbot 的本质区别，以及 Agent 的核心能力（感知、规划、执行、反思）
- 使用 Function Calling API 让 LLM 调用外部工具
- 实现 ReAct 模式的 Agent，让 LLM 交替进行推理和行动
- 设计任务分解策略，让 Agent 能完成复杂的多步骤任务
- 为 TextAgent 添加工具调用和 Agent 能力

<!--
================================================================================
【章节规划元数据】
================================================================================

贯穿案例：智能分析助手

- 第 1 节（Agent 架构）：案例从"单个 RAG 问答"变成"能调用工具的助手框架"
- 第 2 节（Function Calling）：添加文本分析工具（词频统计、情感分析、关键词提取）
- 第 3 节（ReAct 模式）：实现推理-行动循环，让助手能自主决定调用哪个工具
- 第 4 节（规划与任务分解）：让助手能拆解复杂任务（"分析这份文档"→ 切分→ 分析→ 汇总）

最终成果：一个能自主调用工具、规划步骤的智能文本分析助手

认知负荷预算：
本周新概念（预算：5 个，"抽取与发现"阶段）：
1. Agent 架构（Agent Architecture）— 感知、规划、执行、反思
2. Function Calling（函数调用）— LLM 调用外部工具的能力
3. ReAct 模式（Reasoning + Acting）— 推理与行动交替的循环
4. 任务分解（Task Decomposition）— 将复杂任务拆解为可执行步骤
5. 工具定义（Tool Definition）— 用 Schema 描述工具的能力

结论：在预算内（5 个 = 上限 5 个）

循环角色出场规划：
- 小北（第 1 节）：问"为什么不能直接让 LLM 写代码然后执行？"——引出安全性和可控性问题
- 阿码（第 2 节）：追问"工具描述怎么写？写太简单 LLM 会乱调用吗？"
- 老潘（第 3 节）：点评"生产环境中，每个工具调用都要有日志和审计"
- 小北（第 4 节）：发现任务分解后步骤顺序错了，引出规划的重要性

回顾桥设计（至少 2 个，来自前几周）：
- [Prompt 设计原则]（来自 week_02）：在第 2 节，通过工具描述的 Prompt 展示清晰性的重要性
- [Chain-of-Thought]（来自 week_02）：在第 3 节，ReAct 模式本质上是 CoT + 工具调用
- [RAG 架构]（来自 week_03）：在第 1 节，对比 RAG 和 Agent 的区别
- [结构化输出]（来自 week_01）：在第 2 节，Function Calling 返回的是结构化的工具调用

AI 小专栏规划：
- 第 1 个（第 1-2 节之间）：Function Calling 的演进与行业应用
- 第 2 个（第 3-4 节之间）：Agent 框架竞争战 — LangChain vs LlamaIndex vs 原生实现

TextAgent 本周推进：
- 上周状态：TextAgent 是一个 RAG 系统，能检索和回答
- 本周改进：
  1. 封装文本分析工具（词频统计、情感分析等）
  2. 实现 Function Calling 接口
  3. 实现 ReAct 模式的 Agent 循环
  4. 添加任务分解能力
- 涉及的本周概念：Function Calling、ReAct 模式、任务分解
- 建议示例文件：examples/05_textagent_agent.py

================================================================================
-->

---

## 第 1 节：从回答问题到解决问题

小北上周刚完成 Week 04 的作业，对 TextAgent 的检索能力很满意。于是当他老板让他"分析这 100 份客户反馈，告诉我主要问题是什么"时，他毫不犹豫地打开 TextAgent，输入："这些反馈的主要问题是什么？"

TextAgent 很快给出了回答："客户关注物流、质量、服务等多个方面。建议关注物流速度和产品质量。"

小北觉得挺有道理，就把这段话复制到周报里，发给老板。

第二天老板在周会上拿起他的报告，念了一句："客户关注物流、质量、服务等多个方面。"

然后抬起头看着小北："这说了等于没说啊。我问的是'主要问题'——具体是哪个问题占多少比例？哪个渠道的反馈最集中？有没有什么明显的趋势？"

会议室里安静了几秒。

小北的脸有点烫——他突然意识到：TextAgent 给他的，是一个"看起来专业"的空壳。它检索到了一些相关内容，然后用 LLM 的"话术"包装了一下，但没有真正"分析"任何东西。

"我再试试。"小北回到座位，这次他换了个问法："统计这些反馈中的高频词。"

TextAgent 回答："请提供具体文本……"

"我刚才不是给你了吗？"小北有点抓狂。

老潘走过来看了一眼，说："你给它的是'任务'，但它只会'回答问题'。"

这就是 Week 01-04 你一直在做的事情：让 LLM 回答问题。Week 01-02 是设计 Prompt，让 LLM 准确理解需求；Week 03-04 是加上 RAG，让 LLM 能访问外部知识。但无论怎么优化，TextAgent 始终是一个"问答系统"——你问，它答；你不问，它什么也不会做。

### Chatbot vs Agent：本质区别在哪里？

| 维度 | Chatbot | Agent |
|------|---------|-------|
| **核心能力** | 回答问题 | 解决问题 |
| **交互模式** | 一问一答 | 多轮对话 + 工具调用 |
| **能力边界** | 只能用 Prompt 中表达的能力 | 可以调用外部工具/API |
| **任务类型** | 单轮问答 | 多步骤任务 |
| **自主性** | 被动响应 | 主动规划 |

Chatbot 是"被动的"：你问它，它答；你不问，它就等着。Agent 是"主动的"：给它一个目标，它会自己规划步骤、调用工具、迭代反思，直到完成目标。

### Week 03 的回顾：RAG 给了 Agent "记忆"

还记得 Week 03 我们学的 RAG 吗？它让 LLM 能访问外部知识库——相当于给 LLM 装上了"长期记忆"。

```text
RAG: 用户问题 → 检索知识库 → 基于知识回答
```

但 RAG 只是让 LLM "知道"更多信息，它仍然是"回答问题"的模式。Agent 则更进一步——它不仅能"知道"，还能"做事"。

```text
Agent: 目标 → 规划步骤 → 调用工具 → 观察 → 调整 → 继续执行
```

### Agent 的四大核心能力

一个完整的 Agent 需要四种能力：

1. **感知（Perception）**：理解用户的目标和当前状态
2. **规划（Planning）**：把大目标拆解成小步骤
3. **执行（Action）**：调用工具、执行代码、发送请求
4. **反思（Reflection）**：根据执行结果调整策略

小北看着这个四能力模型，突然明白了："我之前让 TextAgent 总结客户反馈，它直接给了个泛泛的回答——是因为它没有真正'分析'，只是检索和总结。如果它是一个 Agent，它应该先规划：1) 加载所有反馈 2) 统计高频词 3) 分析情感倾向 4) 汇总发现，然后一步步执行。"

没错。小北的问题在于：他让 TextAgent "总结反馈"，但 TextAgent 没有真正"分析"——它只是检索了一些相关片段，然后用 LLM 总结了一遍。如果它是一个 Agent，它应该先规划：1) 加载所有反馈 2) 统计高频词 3) 分析情感倾向 4) 汇总发现，然后一步步执行。

这周我们要做的：给 TextAgent 装上"规划"和"执行"的能力，让它从"问答系统"进化为"Agent"。

> **AI 时代小专栏：Function Calling 的演进与行业应用**
>
> 2023 年 8 月，OpenAI 推出 Function Calling API，标志着 LLM 从"聊天"走向"行动"的关键转折。2024-2025 年，所有主流 LLM 都跟进了这一能力：Anthropic Claude 的 Tool Use、Google Gemini 的 Function Calling、国产大模型的工具调用接口。
>
> Function Calling 的核心思想很简单：让 LLM 不是返回"自然语言答案"，而是返回"结构化的工具调用指令"——比如 `{"name": "search_database", "arguments": {"query": "..."}}`，然后由系统执行这个调用，再把结果反馈给 LLM。
>
> 这个看似简单的变化，引发了 2025 年企业级应用的爆发式增长。根据行业报告，约 60% 的生产级 AI 应用在 2025 年已经集成了工具调用能力——从"聊天客服"到"能查订单、能退款、能调库存的智能客服"；从"数据分析助手"到"能写 SQL、能执行查询、能生成图表的自动分析系统"。
>
> 参考（访问日期：2026-02-17）：
> - [OpenAI - The State of Enterprise AI 2025 Report](https://cdn.openai.com/pdf/7ef17d82-96bf-4dd1-9df2-228f7f377a29/the-state-of-enterprise-ai_2025-report.pdf)
> - [McKinsey - The State of AI in 2025](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai)
> - [Menlo Ventures - 2025 State of Generative AI in the Enterprise](https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/)
> - [Wharton - 2025 AI Adoption Report](https://knowledge.wharton.upenn.edu/special-report/2025-ai-adoption-report/)

---

## 第 2 节：给 LLM 装上"手"—— Function Calling 实战

小北问了一个很实际的问题："为什么不能直接让 LLM 写 Python 代码，然后用 `exec()` 执行？这样不就能做任何事情了吗？"

阿码听完笑了，说："我之前试过。结果有一次它写了 `os.system('rm -rf /')` ——幸好我在 Docker 容器里跑的。"

小北脸都白了。"还能这样？"

"还有更离谱的，"阿码继续说，"有一次它写了个死循环，把我的 CPU 跑到 100%，风扇像直升机一样响。从那以后我再也不敢随便 `exec()` 了。"

这就是问题所在：让 LLM 随意执行代码，就像给一把万能钥匙——能开任何门，但也可能打开你不想开的门。Function Calling 则是另一套思路：LLM 不直接"做事"，它只"决定做什么"，然后由系统执行预先定义好的、安全的工具。

### Function Calling 是怎么工作的？

让我们用一个具体场景来理解：用户问"查一下 2024 年 Q1 的销售额"。

```text
用户："查一下 2024 年 Q1 的销售额"

LLM 的内部推理（你看不到）：
用户想要查询销售额 → 我有一个 search_sales 工具 → 需要参数：quarter="Q1", year=2024

LLM 返回（不是自然语言，而是结构化指令）：
{
  "tool": "search_sales",
  "arguments": {"quarter": "Q1", "year": 2024}
}

系统执行（安全可控）：
调用 search_sales(quarter="Q1", year=2024) → 得到结果：$1.2M

系统把结果反馈给 LLM：
"search_sales 返回了 1.2M"

LLM 生成最终答案：
"2024 年 Q1 的销售额是 120 万美元。"
```

整个流程的核心是：**LLM 决策，系统执行**。你定义了哪些工具，LLM 就只能调这些工具；它想干别的，没门。

### Week 01 的回顾：结构化输出

还记得 Week 01 我们学的**结构化输出**（Structured Output）吗？当时我们用 JSON Mode 让 LLM 返回符合格式的数据。

Function Calling 本质上是结构化输出的一种——只不过输出的不是普通的 JSON 数据，而是"工具调用指令"。Week 01 我们让 LLM 返回 `{"name": "...", "value": "..."}`，现在我们让它返回 `{"tool": "search_sales", "arguments": {...}}`。

原理相同，只是用途不同。

### 定义工具：Schema 是关键

LLM 怎么知道有哪些工具可用？你得在 API 调用时告诉它——用一种叫"Schema"的格式描述每个工具的能力。

让我们来定义三个文本分析工具：情感分析、关键词提取、词频统计。

```python
# examples/02_function_calling.py
from openai import OpenAI
import json

client = OpenAI()

# 先定义工具函数（这些是实际执行的函数）
def analyze_sentiment(text: str) -> dict:
    """分析文本情感（简化实现）"""
    positive_words = ["好", "优秀", "满意", "喜欢", "棒"]
    negative_words = ["差", "慢", "糟糕", "不满", "差劲"]

    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)

    if pos_count > neg_count:
        return {"sentiment": "positive", "score": pos_count - neg_count}
    elif neg_count > pos_count:
        return {"sentiment": "negative", "score": neg_count - pos_count}
    else:
        return {"sentiment": "neutral", "score": 0}
```

注意：上面这些函数（`analyze_sentiment` 等）是**实际执行的函数**，它们定义了 Agent "能做什么"。简化起见，这里用词匹配方法；生产环境你可以替换成真实的模型调用。

接下来定义工具的 Schema——这是给 LLM 看的"工具说明书"：

```python
# 定义工具列表（告诉 LLM 有哪些工具可用）
tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_sentiment",
            "description": "分析一段文本的情感倾向（正面/负面/中性）",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要分析的文本内容"
                    }
                },
                "required": ["text"]
            }
        }
    },
    # ... extract_keywords 和 count_word_freq 的 Schema 定义类似
]

# 用户问题
user_message = "帮我分析一下这段客户反馈的情感，并提取关键词：产品质量很好，但物流太慢了，希望改进。"

# 调用 LLM
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": user_message}],
    tools=tools,
    tool_choice="auto"  # 让 LLM 自动决定是否调用工具
)
```

阿码看着代码，追问："工具描述要写多详细？写太简单会不会让 LLM 乱调用？"

好问题。工具描述是 LLM 决策的唯一依据，写得不清楚会让 LLM 要么不用工具、要么用错工具。

让我们看一个真实的对比：

| 坏的描述 | 好的描述 | 为什么？ |
|---------|---------|---------|
| "分析情感" | "分析一段文本的情感倾向（正面/负面/中性），返回情感类型和置信度" | 明确输入和输出，说清返回什么 |
| "提取关键词" | "从文本中提取关键词，返回最多 top_k 个（默认 5 个）" | 说明有参数、有默认值 |
| "统计词频" | "统计文本中词频最高的前 K 个词（默认 10 个），需要先分词" | 预告依赖（需要分词） |
| "分析" | "分析客户反馈中的问题类别，返回前 3 个最常见的问题" | 限定使用场景和输出数量 |
| "查询数据" | "根据订单 ID 查询订单状态（shipped/delivered/cancelled）" | 限定返回值的枚举范围 |

看出区别了吗？坏的描述像是一个"函数名"——LLM 猜不到它具体做什么、返回什么。好的描述像是一个"使用说明书"——LLM 看完就知道该不该用这个工具、该怎么用。

### 工具描述的 Prompt 设计原则

还记得 Week 02 的**Prompt 设计原则**吗？工具描述本质上也是一种 Prompt，同样需要：清晰性、一致性、鲁棒性。

| 原则 | 好的描述 | 坏的描述 |
|------|---------|---------|
| **清晰性** | "分析一段文本的情感倾向（正面/负面/中性）" | "分析情感" |
| **边界明确** | "从文本中提取关键词，返回最多 top_k 个" | "提取关键词" |
| **示例说明** | "输入：'产品质量很好' → 输出：'正面'" | 无 |

老潘补充："在生产环境中，我们还会在描述里写清楚'什么时候不该用这个工具'——比如情感分析工具不适合分析纯数值数据。这能减少误调用。"

### 实现 Function Calling 循环

Function Calling 不是一次调用就完事，而是一个循环：LLM 决定调用工具 → 系统执行 → 把结果反馈给 LLM → LLM 可能继续调用其他工具或生成最终答案。

```python
def run_function_calling_loop(user_message: str, max_iterations: int = 5):
    """Function Calling 循环"""
    messages = [{"role": "user", "content": user_message}]

    for iteration in range(max_iterations):
        # 调用 LLM
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # 检查是否有工具调用
        if not assistant_message.tool_calls:
            # 没有，说明 LLM 已经给出最终答案
            break

        # 执行工具调用
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # 执行工具
            if function_name == "analyze_sentiment":
                result = analyze_sentiment(function_args["text"])
            elif function_name == "extract_keywords":
                result = extract_keywords(function_args["text"], function_args.get("top_k", 5))
            elif function_name == "count_word_freq":
                result = count_word_freq(function_args["text"], function_args.get("top_k", 10))
            else:
                result = f"Unknown tool: {function_name}"

            # 把工具结果反馈给 LLM
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": json.dumps(result)
            })

    # 返回最终答案
    return messages[-1]["content"]
```

阿码突然想起了什么："等等，我之前试过让 LLM 直接写 Python 代码然后用 `exec()` 执行，结果有一次它写了 `os.system('rm -rf /')` ——幸好我在 Docker 容器里跑的。"

小北听完脸都白了："还能这样？"

这就是 Function Calling 的核心价值：**安全可控**。你定义了哪些工具，LLM 就只能调这些工具；它想干别的，没门。

但这里有一个反直觉的事实：**限制工具数量反而能让 Agent 更聪明**。

阿码一开始觉得"工具越多越好"，于是给 Agent 定义了 20 个工具——结果 Agent 开始"乱点菜"：分析一个简单的情感，它先调了词频统计、再调关键词提取、又调摘要生成，最后才想起来要做情感分析。

"它像是个拿到新玩具的孩子，每个都想试一遍，"阿码无奈地说。

老潘听了点点头："在公司里，我们有个经验法则：**只给 Agent 当前任务需要的工具**。如果任务是'分析情感'，只给它 `analyze_sentiment`，不要给它其他工具。这样它就不会'分心'。"

小北听完恍然大悟："哦！所以工具少一点，Agent 反而更专注？"

---

## 第 3 节：推理与行动的舞蹈 —— ReAct 模式

Function Calling 让 LLM 能调用工具，但还有一个问题：LLM 怎么知道"先调用哪个工具、再调用哪个工具"？

想象一下，老板让你"分析这 100 份反馈并生成报告"。你怎么做？你会先规划一下：
1. 先加载所有反馈
2. 统计高频词
3. 分析情感分布
4. 提取关键主题
5. 生成报告

但如果你不规划，可能会一边做一边想："先调用情感分析？哦等等，我还没加载数据……" 这样效率很低。

LLM 也一样。如果你只是给它一堆工具，它可能会"走弯路"。**ReAct 模式**（Reasoning + Acting）就是解决这个问题：让 LLM 在每一步都先"思考"（Thought），再"行动"（Action），然后"观察"（Observation），如此循环。

### 先看一个最小示例

在写完整代码之前，让我们先用手动方式"扮演"一次 ReAct 流程。这样你能直观理解它在做什么。

假设用户问："分析这段客户反馈：产品质量很好，但物流太慢了。"

```text
=== 第 1 轮 ===

LLM 的思考（你看不到，但它在内部推理）：
用户想让我分析反馈。我需要先了解它的情感倾向，再提取关键词。

LLM 返回：
Action: analyze_sentiment
Action Input: {"text": "产品质量很好，但物流太慢了"}

系统执行工具：
→ analyze_sentiment("产品质量很好，但物流太慢了")
→ 返回：{"sentiment": "mixed", "positive_score": 0.5, "negative_score": 0.4}

系统把结果反馈给 LLM：
Observation: 情感分析结果是混合（mixed），正面分 0.5，负面分 0.4

=== 第 2 轮 ===

LLM 的思考：
用户还想知道关键问题是什么。我需要提取关键词。

LLM 返回：
Action: extract_keywords
Action Input: {"text": "产品质量很好，但物流太慢了", "top_k": 3}

系统执行工具：
→ extract_keywords(...)
→ 返回：{"keywords": ["产品质量", "物流", "慢"]}

系统把结果反馈给 LLM：
Observation: 提取到关键词：产品质量、物流、慢

=== 第 3 轮 ===

LLM 的思考：
我已经收集了足够信息，可以给出最终答案了。

LLM 返回：
Final Answer: 这条反馈的情感是混合的。正面方面是产品质量好，负面方面是物流太慢。主要关注点是物流速度。
```

看明白了吗？**ReAct 的核心就是"多轮对话"**：
1. LLM 不需要一次性给出答案
2. 每轮它都可以调用一个工具
3. 工具的结果会被"喂回"给 LLM，帮助它做下一步决策

### Week 02 的回顾：Chain-of-Thought

还记得 Week 02 的**Chain-of-Thought**（CoT）吗？CoT 让 LLM 展示推理过程："让我一步步思考"。ReAct 本质上是 CoT + 工具调用——不仅让 LLM "思考"，还让它"行动"。

| 模式 | 核心思想 | 输出 |
|------|---------|------|
| **CoT** | 让 LLM 展示推理过程 | 自然语言的思考步骤 |
| **ReAct** | 让 LLM 交替进行推理和行动 | Thought + Action + Observation |

### 实现最小 ReAct Agent

现在让我们把上面的流程写成代码。先从一个最小版本开始——只做 3 轮循环，让你看清每个步骤。

```python
# examples/03_react_minimal.py
from openai import OpenAI
import json

client = OpenAI()

def run_minimal_react_loop(task: str, max_rounds: int = 3):
    """最小版本的 ReAct 循环——清晰展示每一步在做什么"""

    # 第一步：构造初始消息
    messages = [
        {
            "role": "system",
            "content": "你是一个文本分析助手。使用工具分析用户的问题。"
        },
        {"role": "user", "content": task}
    ]

    # 定义工具（简化版：只一个工具）
    tools = [{
        "type": "function",
        "function": {
            "name": "analyze_text",
            "description": "分析文本的情感和关键词",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要分析的文本"}
                },
                "required": ["text"]
            }
        }
    }]

    # 第二步：循环调用
    for round_num in range(1, max_rounds + 1):
        print(f"\n{'='*40}")
        print(f"第 {round_num} 轮")
        print(f"{'='*40}")

        # 调用 LLM
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        # 检查是否有工具调用
        if msg.tool_calls:
            # 有工具调用：执行并反馈
            tool_call = msg.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"Action: {tool_name}")
            print(f"Input: {json.dumps(tool_args, ensure_ascii=False)}")

            # 执行工具（这里简化为直接返回）
            if tool_name == "analyze_text":
                result = {
                    "sentiment": "mixed",
                    "keywords": ["物流", "质量"]
                }
                print(f"Result: {json.dumps(result, ensure_ascii=False)}")
            else:
                result = {"error": "Unknown tool"}

            # 把结果反馈给 LLM（重要！）
            messages.append(msg)  # LLM 的回复（包含工具调用请求）
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
        else:
            # 没有工具调用：给出最终答案
            print(f"Final Answer: {msg.content}")
            return msg.content

    return "达到最大轮数"

# 测试
result = run_minimal_react_loop("分析：产品质量好，物流慢")
```

小北看完这段代码，说："哦！我明白了——`messages` 列表在不断增长，每轮对话都会把之前的工具调用结果加进去。这样 LLM 就能'记住'之前做了什么。"

没错！这就是 ReAct 的核心：**对话历史**。每次工具调用的结果都会被记录下来，LLM 可以基于这些历史信息做下一步决策。

但这里有个反直觉的事实：**Agent 经常会"固执"地反复调用同一个工具**。

阿码最近就遇到了这个问题：他让 Agent "分析这份文档的情感倾向"，结果 Agent 连续调用了 5 次 `analyze_sentiment`，每次都是同一个参数——它似乎"忘记"了自己已经分析过了。

"这不是很蠢吗？"阿码不解地问，"它不应该看看历史记录，发现已经做过这个分析了吗？"

你说得对——人类会这样做，但 LLM 不会自动"回头看"。它只看 `messages` 列表，但如果你不在 System Prompt 里强调"不要重复调用同一工具"，它真的会一遍又一遍地做同样的事。

这就是为什么 `max_iterations` 参数很重要：它不是"正常情况下的执行步数"，而是**防止 Agent 陷入死循环的安全阀**。你可能会想："10 轮够吗？"——正常任务 3-5 轮就完成了，设置 10 是为了在 Agent "犯傻"时强行终止。

### 完整版 ReAct Agent

现在让我们把最小版本扩展成一个更完整的 Agent。主要增加：
1. 支持多个工具
2. 更好的历史记录
3. 错误处理

```python
# examples/03_react_agent.py
from typing import List, Dict, Optional
import json
from openai import OpenAI

class ReActAgent:
    """ReAct 模式的 Agent"""

    def __init__(self, tools: List[Dict], llm_client: Optional[OpenAI] = None):
        self.tools = {tool["function"]["name"]: tool for tool in tools}
        self.llm = llm_client or OpenAI()
        self.max_iterations = 10
```

关键在于 `run` 方法——它实现了 Thought-Action-Observation 循环：

```python
    def run(self, task: str) -> Dict:
        """运行 ReAct 循环"""
        messages = [
            {
                "role": "system",
                "content": """你是一个智能助手，能够使用工具完成复杂任务。

请按以下格式思考和行动：

Thought: [你的思考过程]
Action: [工具名称]
Action Input: [工具参数（JSON 格式）]

你会收到工具的执行结果，然后继续思考下一步行动。

当你完成所有步骤后，用以下格式给出最终答案：

Final Answer: [最终答案]

重要约束：
1. 每次只能调用一个工具
2. Thought 必须清晰说明你为什么要采取这个行动
3. Action Input 必须是有效的 JSON 格式
4. 如果工具调用失败，在 Thought 中分析原因并尝试替代方案"""
            },
            {"role": "user", "content": task}
        ]

        history = []

        for iteration in range(self.max_iterations):
            response = self.llm.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=[self.tools[name] for name in self.tools]
            )

            response_msg = response.choices[0].message

            # 检查是否有工具调用
            if response_msg.tool_calls:
                # 有工具调用：执行并反馈
                tool_call = response_msg.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                try:
                    result = self._execute_tool(tool_name, tool_args)
                    observation = json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    observation = json.dumps({"error": str(e)})

                # 记录历史（重要！）
                history.append({
                    "iteration": iteration + 1,
                    "action": tool_name,
                    "input": tool_args,
                    "result": result if 'result' in locals() else str(e)
                })

                # 把结果反馈给 LLM
                messages.append({"role": "assistant", "content": response_msg.content or ""})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": observation
                })
            else:
                # 没有工具调用，说明已经给出最终答案
                return {
                    "final_answer": response_msg.content,
                    "history": history,
                    "iterations": iteration + 1
                }

        return {
            "final_answer": "达到最大迭代次数",
            "history": history,
            "iterations": self.max_iterations
        }

    def _execute_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """执行工具（需要实现具体的工具逻辑）"""
        # 这里需要实现具体的工具函数
        if tool_name == "analyze_sentiment":
            return {"sentiment": "positive", "confidence": 0.85}
        elif tool_name == "extract_keywords":
            return {"keywords": ["物流", "质量", "服务"]}
        # ... 其他工具
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
```

**这段代码做了什么？** 让我们拆解关键步骤：

1. **`messages` 列表**：它是"记忆"，记录了整个对话历史。每次工具调用的结果都会被加进去。
2. **循环**：最多执行 `max_iterations` 轮，每轮都调用 LLM → 检查是否有工具调用 → 执行工具 → 反馈结果。
3. **终止条件**：当 LLM 不再调用工具时，说明它认为任务完成了，会给出 Final Answer。
4. **历史记录**：每步操作都被记录在 `history` 中，方便后续审计和调试。

老潘看到这个实现会点评："ReAct 的关键是'可追踪性'——每一步的 Thought、Action、Observation 都要记录下来。生产环境中，这些日志是审计和调试的关键。"

### ReAct 的常见陷阱

小北在实现 ReAct 时遇到了几个问题：

| 问题 | 表现 | 解决方案 |
|------|------|---------|
| **死循环** | Agent 反复调用同一个工具，不会停止 | 设置 max_iterations，在 Thought 中强调"完成即停止" |
| **工具参数错误** | LLM 传了错误的参数类型或缺失必需参数 | 在 Schema 中明确参数类型和默认值，添加参数验证 |
| **过早停止** | Agent 没有完成任务就给出 Final Answer | 在 System Prompt 中强调"必须确保任务完全完成" |

阿码追问："如果 Agent 调用工具失败了怎么办？它会自己重试吗？"

好问题。默认情况下，Agent 会把错误信息当作 Observation，然后在下一次 Thought 中决定是否重试或尝试替代方案。你也可以在工具执行层面添加自动重试机制。

### 喘口气：理解 ReAct 的本质

在进入下一节之前，让我们确认你理解了 ReAct 的本质。

**ReAct 不是魔法，它就是"多轮对话 + 工具调用"**：
- LLM 不需要一次性给出答案
- 每轮它可以调用一个工具，然后根据结果决定下一步
- 最终它会给出 Final Answer

老潘看到这里会补一句："所以 ReAct 的关键是**可追踪性**——每一步的 Thought、Action、Observation 都要记录下来。生产环境中，这些日志是审计和调试的关键。如果 Agent 给出了错误的答案，你得能回溯是哪一步出了问题。"

小北试了之后又发现一个新问题："我让它'分析反馈并给出建议'，结果它先给了建议，然后才说'现在让我分析一下'——完全反过来了。"

这确实是个问题。ReAct 模式下，LLM 是"边想边做"，有时会走弯路——它可能会"跳到结论"再回头分析。下一节我们来解决这个问题：**规划与任务分解**。

---

## 第 4 节：把大任务拆开 —— 规划与任务分解

小北最近遇到的"反向操作"问题（先给建议再分析），本质上是 **规划缺失**。

ReAct 模式下，LLM 是"边想边做"，有时会走弯路——比如先调用情感分析，再决定加载反馈，导致效率低下。这就需要 **规划**（Planning）：在执行之前，先把大任务拆解成小步骤，然后按顺序执行。

### 任务分解：为什么需要？

想象一下，老板让你"分析这 100 份反馈并生成报告"。有两种做法：

**做法 A（无规划）**：Agent 一边做一边想
1. 先调用情感分析？哦等等，我还没加载数据
2. 先加载数据
3. 现在做情感分析
4. 等等，我还应该先统计高频词
5. ... 反复调整

小北上周就遇到了这种情况：他让 Agent "分析反馈并总结"，结果 Agent 先给出了一段总结，然后才说"现在让我分析一下情感"——完全反过来了。他盯着屏幕，不知道该笑还是该哭。

**做法 B（有规划）**：Agent 先规划，再执行
1. **规划阶段**：任务分解为 4 步：加载 → 统计词频 → 情感分析 → 生成报告
2. **执行阶段**：按顺序执行，不回头

这就像做菜：有规划的人会先准备好所有食材（切好、洗净），然后按顺序下锅；没规划的人会一边炒菜一边发现"哎呀没买葱"，然后手忙脚乱地去买——最后菜可能糊了。

### 先看一个最简示例

让我们从最简单的任务分解开始：给 LLM 一个"规划 Prompt"，让它先写出步骤列表。

```python
# examples/04_planning_simple.py
from openai import OpenAI

client = OpenAI()

def create_simple_plan(task: str) -> str:
    """让 LLM 制定一个简单的任务计划"""

    prompt = f"""你是一个任务规划专家。请把以下任务分解成清晰的步骤。

任务：{task}

请按以下格式输出计划：

步骤 1: [做什么]
步骤 2: [做什么]
步骤 3: [做什么]
...

示例：

任务：分析客户反馈

计划：
步骤 1: 加载所有反馈数据
步骤 2: 统计高频词，了解主要关注点
步骤 3: 分析情感分布，了解满意度
步骤 4: 汇总发现，给出建议

现在请为任务"{task}"制定计划："""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content

# 测试
plan = create_simple_plan("分析 100 份客户反馈并生成报告")
print(plan)
```

运行这个函数，你会得到类似这样的输出：

```text
计划：
步骤 1: 加载所有反馈数据
步骤 2: 统计高频词，了解主要关注点
步骤 3: 分析每条反馈的情感倾向
步骤 4: 汇总统计结果
步骤 5: 生成分析报告
```

阿码看完说："这看起来像是一个'清单'（checklist）。Agent 真的会按这个清单执行吗？"

好问题。目前我们只是让 LLM "写了个清单"，但我们还没有让 Agent 真的按这个清单执行。这就像是：你有菜谱，但你还是得自己一步步做菜。

### 让 Agent 真的按计划执行

现在让我们把"规划"和"执行"真正结合起来。思路是：
1. **规划阶段**：让 LLM 写一个计划
2. **执行阶段**：把计划"喂回"给 LLM，让它按步骤执行

```python
# examples/04_planning_agent.py
class PlanningAgent(ReActAgent):
    """带规划能力的 Agent —— 先规划，再执行"""

    def run(self, task: str) -> Dict:
        # 第一步：让 LLM 制定计划
        plan = self._create_plan(task)
        print(f"\n{'='*40}")
        print(f"【计划】")
        print(f"{'='*40}")
        print(plan)
        print(f"{'='*40}\n")

        # 第二步：把计划加入到 System Prompt，让 Agent 按计划执行
        return super().run(f"任务：{task}\n\n计划：\n{plan}")

    def _create_plan(self, task: str) -> str:
        """创建任务计划"""
        plan_prompt = f"""请为以下任务制定执行计划。

任务：{task}

请输出清晰的步骤列表：

步骤 1: [做什么]
步骤 2: [做什么]
...

计划："""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": plan_prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content
```

小北试了之后发现："有了计划，Agent 确实更有序了！它不再乱调用工具，而是按步骤来。"

但老潘提醒了一个问题："如果计划本身错了怎么办？比如 LLM 把'生成报告'放在'统计分析'之前。"

### 任务分解的常见错误

让我们列一下任务分解可能出错的地方：

| 错误类型 | 表现 | 后果 |
|---------|------|------|
| **顺序错误** | 步骤 3 依赖步骤 1，但步骤 3 排在步骤 1 前面 | Agent 会失败或得到错误结果 |
| **遗漏依赖** | 没有加载数据就直接分析 | Agent 会报错或得到空结果 |
| **步骤太粗** | 一步做完所有事情 | Agent 可能直接放弃，不知道怎么开始 |
| **步骤太细** | 把"打开文件"和"读取第一行"分成两步 | 浪费 token，效率低下 |

小北遇到的就是第一种错误：顺序错误。"LLM 给我的计划是：先生成报告，再分析数据。这完全反过来了。"

阿码也遇到了类似的问题："我让它'分析反馈并给出建议'，结果它先给了建议，然后才说'现在让我分析一下'——完全反过来了。"

两人对视一眼，然后转向老潘："这怎么办？"

### 人工审核 + 迭代修正

老潘笑了笑："规划不是一次性的。你可以让 LLM 先规划，然后你检查一下；如果不合理，让它重新规划。生产环境里，我们甚至会让人工审核关键任务的计划。"

这就叫 **human-in-the-loop**（人在回路）：AI 做初步规划，人来审核和修正。

```python
# 带人工审核的规划
def create_plan_with_review(task: str, max_retries: int = 3) -> str:
    """创建计划，允许人工审核和修正"""

    for retry in range(max_retries):
        plan = create_simple_plan(task)

        print(f"\n{'='*40}")
        print(f"计划（第 {retry + 1} 版）")
        print(f"{'='*40}")
        print(plan)
        print(f"{'='*40}")

        # 人工审核
        user_input = input("\n是否接受这个计划？(y/n/修改): ")

        if user_input.lower() == 'y':
            return plan
        elif user_input.lower() == '修改':
            # 让用户输入修改意见
            feedback = input("请输入修改意见：")
            task = f"{task}\n\n之前的计划有误，请根据以下反馈修改：{feedback}"
        # else: 重新生成

    return create_simple_plan(task)  # 最后一次尝试
```

小北试了这个方法，说："好的，我可以先让 LLM 给个计划，然后我自己检查一遍。如果顺序错了，我就告诉它'步骤 2 应该在步骤 1 之后'，它就会重新规划。"

### Week 02 的回顾：Few-shot 让规划更可靠

还记得 Week 02 的 **Few-shot Learning** 吗？给 LLM 几个正确的示例，它就能学会模式。

任务分解也一样。如果你发现 LLM 总是把顺序搞错，可以在 Prompt 里加几个正确的示例：

```python
def create_plan_with_fewshot(task: str) -> str:
    """用 Few-shot 示例让 LLM 学会正确的规划"""

    prompt = f"""你是一个任务规划专家。请把任务分解成清晰的步骤。

示例 1：

任务：分析客户反馈并生成报告

计划：
步骤 1: 加载所有反馈数据
步骤 2: 统计高频词，了解主要关注点
步骤 3: 分析情感分布
步骤 4: 生成分析报告

示例 2：

任务：查询销售数据并制作图表

计划：
步骤 1: 连接数据库
步骤 2: 查询销售数据
步骤 3: 处理数据（聚合、排序）
步骤 4: 生成图表

现在请为以下任务制定计划：

任务：{task}

计划："""

    # ... 调用 LLM
```

注意示例中的关键点：
1. **依赖关系清晰**：加载数据总是在分析之前
2. **逻辑顺序**：先做统计，再汇总
3. **每步只有一个目标**：不要在一个步骤里做太多事

老潘看到这个方法会点评："示例是最好的老师。如果你想让它怎么工作，就给它看正确的例子。"

---

### 小结：ReAct 与规划的协同

这节我们学了任务分解，它解决了 ReAct 模式的一个问题："边想边做"可能走弯路。

**ReAct（第 3 节）** 给了 Agent "思考和行动"的能力，但它是"在线规划"——一边做一边想下一步。

**任务分解（第 4 节）** 则是"离线规划"——先想好整个计划，再按计划执行。

两者结合，Agent 就能：
1. 先制定一个计划（离线）
2. 然后按计划执行，每步都用 ReAct 的方式思考-行动-观察（在线）
3. 如果遇到意外情况，可以调整计划

这就像你去旅行：先查攻略做好行程单（规划），然后到了目的地按行程单游玩（ReAct），但遇到下雨或景点关闭可以临时调整。

---

> **AI 时代小专栏：Agent 框架竞争战 —— LangChain vs LlamaIndex vs 原生实现**
>
> 2024-2025 年，Agent 开发框架经历了激烈的竞争和快速演进。LangChain 早期凭借"链式调用"成为标准，但随着 Agent 复杂度提升，其局限性也逐渐暴露：过度抽象、调试困难、性能开销。2024 年底，LlamaIndex 凭借"图结构工作流"（后来独立为 LangGraph）和更强的 RAG 集成迅速崛起。同时，OpenAI、Anthropic 等厂商推出了更轻量的"Assistant API"，让开发者可以用原生接口实现 Agent，无需框架。
>
> 2025-2026 年的主流实践是：**从简单开始，按需升级**。简单 Agent 用原生 Function Calling 即可；复杂多智能体系统才考虑 LangGraph/AutoGen/CrewAI 等框架。根据行业调研，约 55% 的开发者倾向于先用原生实现，确认需求后再引入框架。
>
> 参考（访问日期：2026-02-17）：
> - [LlamaIndex vs LangChain: A 2025 Comparison](https://www.latent.space/llama-vs-langchain)
> - [LangGraph - Building Stateful Agents with LangChain](https://langchain-ai.github.io/langgraph/)
> - [LlamaIndex Workflows - Agent Orchestration](https://docs.llamaindex.ai/en/stable/module_guides/workflows/)
> - [Building Agents Without Frameworks: Native Function Calling Guide](https://community.openai.com/t/function-calling-best-practices/727885)

---

<!--
================================================================================
【TextAgent 进度】
================================================================================
-->

## TextAgent 进度

Week 04 结束时，TextAgent 是一个"精准问答系统"：混合检索保证召回，重排序保证精确，RAGAS 评估让效果可量化。但它仍然是"被动"的——你问，它答；你不问，它什么也不会做。

这周我们让 TextAgent 变成了一个"主动的" Agent：它能调用工具、能规划步骤、能完成复杂任务。

### 本周改进

```python
# src/textagent/agent/__init__.py（新增）
from .tools import TextAnalyzerTools
from .react_agent import ReActAgent
from .planning_agent import PlanningAgent

__all__ = ["TextAnalyzerTools", "ReActAgent", "PlanningAgent"]
```

### 1. 封装文本分析工具

```python
# src/textagent/agent/tools.py
from typing import List, Dict
import jieba
from collections import Counter
import re

class TextAnalyzerTools:
    """文本分析工具集"""

    @staticmethod
    def analyze_sentiment(text: str) -> Dict:
        """分析情感（简化版，生产环境应用真实模型）"""
        # 这里可以用真实的情感分析模型
        positive_words = ["好", "优秀", "满意", "喜欢"]
        negative_words = ["差", "慢", "糟糕", "不满"]

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            return {"sentiment": "positive", "confidence": 0.7, "reason": f"正面词{pos_count}个，负面词{neg_count}个"}
        elif neg_count > pos_count:
            return {"sentiment": "negative", "confidence": 0.7, "reason": f"正面词{pos_count}个，负面词{neg_count}个"}
        else:
            return {"sentiment": "neutral", "confidence": 0.5, "reason": "正负面词数量相当"}

    @staticmethod
    def extract_keywords(text: str, top_k: int = 5) -> Dict:
        """提取关键词"""
        words = jieba.cut(text)
        # 过滤停用词
        stopwords = {"的", "了", "是", "在", "我", "有", "和"}
        filtered = [w for w in words if len(w) > 1 and w not in stopwords]

        counter = Counter(filtered)
        top_words = counter.most_common(top_k)

        return {"keywords": [w for w, c in top_words], "counts": [c for w, c in top_words]}

    @staticmethod
    def count_word_freq(text: str, top_k: int = 10) -> Dict:
        """统计词频"""
        words = jieba.cut(text)
        stopwords = {"的", "了", "是", "在", "我", "有", "和", "，", "。", "！"}
        filtered = [w for w in words if len(w) > 1 and w not in stopwords]

        counter = Counter(filtered)
        top_words = counter.most_common(top_k)

        return {"top_words": [{"word": w, "count": c} for w, c in top_words]}

    @staticmethod
    def summarize_text(text: str, max_length: int = 100) -> Dict:
        """摘要文本（简化版：取前 N 个字符）"""
        summary = text[:max_length] + "..." if len(text) > max_length else text
        return {"summary": summary, "original_length": len(text)}

    @staticmethod
    def get_tool_schemas() -> List[Dict]:
        """获取工具的 Function Calling Schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_sentiment",
                    "description": "分析一段文本的情感倾向（正面/负面/中性）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "要分析的文本内容"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_keywords",
                    "description": "从文本中提取关键词",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "要提取关键词的文本"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "返回前 K 个关键词，默认 5",
                                "default": 5
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "count_word_freq",
                    "description": "统计文本中词频最高的前 K 个词",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "要统计词频的文本"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "返回前 K 个高频词，默认 10",
                                "default": 10
                            }
                        },
                        "required": ["text"]
                    }
                }
            }
        ]
```

### 2. 实现 ReAct Agent

```python
# src/textagent/agent/react_agent.py
from typing import List, Dict, Optional
from openai import OpenAI
import json

class ReActAgent:
    """ReAct 模式的文本分析 Agent"""

    def __init__(
        self,
        tools: Dict,
        llm_client: Optional[OpenAI] = None,
        verbose: bool = True
    ):
        self.tools = tools
        self.llm = llm_client or OpenAI()
        self.verbose = verbose
        self.max_iterations = 10

    def run(self, task: str) -> Dict:
        """运行 ReAct 循环"""
        messages = [
            {
                "role": "system",
                "content": """你是一个智能文本分析助手，能够使用工具完成分析任务。

请按以下格式思考和行动：

Thought: [你的思考过程]
Action: [工具名称]
Action Input: [工具参数（JSON 格式）]

你会收到工具的执行结果，然后继续思考下一步行动。

当你完成所有步骤后，用以下格式给出最终答案：

Final Answer: [最终答案]

约束：
1. 每次只能调用一个工具
2. Action Input 必须是有效的 JSON 格式
3. 确保任务完全完成后再给出 Final Answer"""
            },
            {"role": "user", "content": task}
        ]

        history = []

        for iteration in range(self.max_iterations):
            response = self.llm.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=[self.tools[name] for name in self.tools]
            )

            response_msg = response.choices[0].message

            # 检查是否有工具调用
            if response_msg.tool_calls:
                tool_call = response_msg.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                if self.verbose:
                    print(f"\n[Iteration {iteration + 1}]")
                    print(f"Action: {tool_name}")
                    print(f"Input: {json.dumps(tool_args, ensure_ascii=False)}")

                # 执行工具
                try:
                    result = self.tools[tool_name](**tool_args)
                    observation = json.dumps(result, ensure_ascii=False)

                    if self.verbose:
                        print(f"Result: {observation[:200]}...")
                except Exception as e:
                    observation = json.dumps({"error": str(e)})
                    if self.verbose:
                        print(f"Error: {e}")

                # 记录历史
                history.append({
                    "iteration": iteration + 1,
                    "action": tool_name,
                    "input": tool_args,
                    "result": result if 'result' in locals() else str(e)
                })

                # 把结果反馈给 LLM
                messages.append({"role": "assistant", "content": response_msg.content or ""})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": observation
                })
            else:
                # 没有工具调用，给出最终答案
                if self.verbose:
                    print(f"\n[Final Answer]")
                    print(response_msg.content)

                return {
                    "final_answer": response_msg.content,
                    "history": history,
                    "iterations": iteration + 1
                }

        return {
            "final_answer": "达到最大迭代次数",
            "history": history,
            "iterations": self.max_iterations
        }
```

### 3. 使用示例

```python
# examples/05_textagent_agent.py
from textagent.agent.tools import TextAnalyzerTools
from textagent.agent.react_agent import ReActAgent

# 初始化工具
tools = {
    "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
    "extract_keywords": TextAnalyzerTools.extract_keywords,
    "count_word_freq": TextAnalyzerTools.count_word_freq,
}

# 创建 Agent
agent = ReActAgent(tools, verbose=True)

# 任务
task = """
分析以下客户反馈，并给出总结：
1. "产品质量很好，但物流太慢了，希望改进。"
2. "客服态度很差，问题一直没解决。"
3. "价格合理，物流也快，推荐购买。"
4. "用了两周就坏了，质量堪忧。"
"""

# 运行
result = agent.run(task)
print(f"\n最终答案：{result['final_answer']}")
```

### 在 report.md 中记录

```markdown
## Week 05：Agent 能力

### 新增功能

1. 文本分析工具集
   - 情感分析（analyze_sentiment）
   - 关键词提取（extract_keywords）
   - 词频统计（count_word_freq）

2. ReAct Agent
   - 实现 Thought-Action-Observation 循环
   - 支持工具调用和结果反馈
   - 可追踪的执行历史

### 示例任务

任务："分析 4 条客户反馈并总结"

执行步骤：
1. analyze_sentiment → 逐条分析情感
2. count_word_freq → 统计高频词
3. 最终答案：汇总发现

### 下一步

- Week 06：多智能体协作
```

TextAgent 现在不再只是"回答问题"，而是能"主动调用工具、规划步骤、完成任务"的 Agent。下周我们会让它变得更"聪明"——多个 Agent 协作，一个负责规划，一个负责执行，一个负责审核。

<!--
================================================================================
【Git 本周要点】
================================================================================
-->

## Git 本周要点

本周必会命令：
- `git log --oneline --graph` — 图形化查看提交历史
- `git diff HEAD~1` — 查看与上一个提交的差异
- `git stash` — 临时保存修改
- `git stash pop` — 恢复保存的修改

常见坑：
- **工具调用结果不提交**：Agent 的执行历史应该提交到 report.md，这是调试和审计的依据
- **API Key 泄露**：测试代码中的 API Key 不要提交，用环境变量
- **日志文件污染仓库**：Agent 的详细日志应该加到 `.gitignore`

推荐的 `.gitignore` 补充：

```text
# Week 05：Agent
agent_logs/        # Agent 执行日志
*.agent_trace      # 执行追踪文件
```

<!--
================================================================================
【本周小结】
================================================================================
-->

## 本周小结（供下周参考）

这周你让 TextAgent 从"被动回答"进化为"主动执行"。

你先理解了 Agent 和 Chatbot 的本质区别：一个是"回答问题"，一个是"解决问题"。Agent 有四大核心能力——感知、规划、执行、反思。

然后你学了 Function Calling：LLM 不直接"做事"，而是决定"做什么"，由系统执行预先定义的工具。这就像给 LLM 装上了"手"，但它只能用你给它的那些"安全工具"。

接下来是 ReAct 模式：让 LLM 交替进行推理和行动。核心就是一个循环——调用 LLM → 它决定调用哪个工具 → 系统执行 → 把结果反馈给 LLM → 继续。关键点是 `messages` 列表不断增长，记录了整个对话历史。

最后是任务分解：让 Agent 在执行之前先制定计划。你学会了用 Few-shot 示例让 LLM 学会正确的规划顺序，也知道了可以人工审核计划（human-in-the-loop）。

小北发现："有了计划，Agent 不再乱调用工具了。"老潘则提醒："生产环境中，每一步都要有日志——出了问题能追溯。"

Week 03-04 你学了"怎么给 LLM 知识"（RAG），这周你学了"怎么让 LLM 做事"（Agent）。但单个 Agent 能力有限，复杂任务需要多个 Agent 协作——一个负责规划，一个负责执行，一个负责审核。下周我们会学习多智能体系统。

<!--
================================================================================
【Definition of Done（学生自测清单）】
================================================================================
-->

## Definition of Done

学完本章后，你应该能够回答以下问题：

- [ ] 我能解释 Agent 和 Chatbot 的本质区别了吗？（Hint：一个是"回答问题"，一个是"解决问题"）
- [ ] 我能用 Function Calling API 让 LLM 调用工具吗？（Hint：LLM 决策，系统执行）
- [ ] 我理解 ReAct 模式的 Thought-Action-Observation 循环了吗？（Hint：推理与行动交替进行）
- [ ] 我能实现一个简单的 ReAct Agent 吗？（Hint：一个循环 + 工具定义）
- [ ] 我知道如何让 Agent 进行任务规划吗？（Hint：Few-shot 示例 + 人工审核）
- [ ] 我的 TextAgent 有工具调用和 Agent 能力了吗？（Hint：试试让它分析客户反馈）

如果以上都打勾，恭喜你完成 Week 05！你现在已经掌握让 LLM 从"聊天"走向"行动"的核心技术。下周我们会学习如何让多个 Agent 协作——一个负责规划，一个负责执行，一个负责审核。这就像给 LLM 组了一个"团队"。

<!--
================================================================================
【术语登记（供 TERMS.yml 参考】
================================================================================

本章新术语：
1. Agent 架构（Agent Architecture）
2. Function Calling（函数调用）
3. ReAct 模式（ReAct Pattern）
4. 任务分解（Task Decomposition）
5. 工具定义（Tool Definition）

待合入 shared/glossary.yml

================================================================================
-->

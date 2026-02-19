# Week 02：Prompt Engineering 实战 —— 让 LLM 听懂你的需求

> "语言是人类最伟大的发明——它让我们能把思想装进别人的脑子里。"
> — Stephen Pinker（认知心理学家，《语言本能》作者）

上周你学会了让 LLM "开口说话"——一个能跑的 API 调用，几句 Prompt，模型就能帮你分类新闻、生成摘要、抽取实体。但你也可能发现了一个问题：同样的任务，换个写法，结果可能天差地别。你写"请分类"，它可能给你一段解释而不是类别名；你写"输出 JSON"，它可能加一句"好的，以下是结果"然后你的解析代码就崩了。这不是模型的问题，是你和它之间的"沟通协议"没对齐。2024 年到 2025 年间，Prompt Engineering 从"玄学"变成了一门有方法论的实践：OpenAI 发布了官方 Prompt Engineering 指南，DeepSeek 在技术报告中专门分析 CoT 对推理任务的提升，各类框架和最佳实践层出不穷。更关键的是，随着 LLM 进入企业生产环境，"Prompt 写得好不好"直接影响业务——一个歧义的指令可能导致客服机器人给出错误报价，一个遗漏的约束可能让文档摘要泄露敏感信息。这周我们不谈"魔法咒语"，而是建立一个工程化的 Prompt 设计思维：先想清楚你要什么，再用 LLM 能理解的方式说出来。

<!--
================================================================================
【章节规划元数据】
================================================================================

## 本章学习目标

读者学完本章后能够：
1. 掌握 Prompt 设计的核心原则（角色、任务、约束、格式）
2. 使用 Few-shot 示例提升输出稳定性
3. 应用 Chain-of-Thought 思维链处理复杂推理任务
4. 建立 Prompt 评估的迭代思维，能判断"好 Prompt"和"坏 Prompt"
5. 在 TextAgent 项目中实现 Prompt 模板库和基础评估流程

## 认知负荷预算

本周新概念（预算：4 个）：
1. Prompt 设计原则（Prompt Design Principles）— 角色/任务/约束/格式四要素
2. Few-shot Learning（少样本学习）— 用示例引导输出
3. Chain-of-Thought（思维链）— 分步推理提升复杂任务准确率
4. Prompt 评估（Prompt Evaluation）— 迭代优化的方法论

结论：✅ 在预算内（4 个 = 上限 4 个）

## 回顾桥规划

Week 02 必须回顾 Week 01 的至少 2 个概念：

| 回顾概念 | 计划位置 | 回顾方式 |
|---------|---------|---------|
| Token 与成本 | 第 1 节 | 在讨论 Prompt 长度时自然引入："还记得上周说的 Token 吗？Prompt 越长，输入成本越高" |
| 结构化输出 | 第 2 节 | 在讨论输出格式约束时回顾："上周我们用 JSON Mode 保证输出格式，这周我们看 Prompt 层面怎么约束" |
| LLM API 调用 | 第 4 节 | 在 Prompt 评估部分回顾："上周封装的 Client 类，这周要加入 Prompt 版本管理" |

================================================================================
-->

---

## 本章学习目标

学完本章，你将能够：

- 写出让 LLM "一听就懂"的 Prompt——不是靠运气，而是有方法
- 用 Few-shot 示例稳定输出格式，不再担心解析报错
- 用 Chain-of-Thought 处理"需要想一下"的复杂任务
- 建立 Prompt 的迭代评估思维——知道怎么判断"变好了还是变差了"

<!--
================================================================================
【章节结构骨架】
================================================================================

本章共 5 个主要小节 + 1 个 TextAgent 进度 + 固定结尾板块

## 第 1 节：为什么你的 Prompt 总是被误解？
- 学习目标：理解 Prompt 设计的常见问题，掌握角色-任务-约束-格式四要素
- Bloom 层次：理解 + 应用
- 叙事入口：展示一个"写得不好"的 Prompt，让读者感受被误解的痛苦

## 第 2 节：给 LLM 看 "参考答案" —— Few-shot Learning
- 学习目标：使用 Few-shot 示例稳定输出格式和风格
- Bloom 层次：应用
- 叙事入口：从"输出格式不稳定"的痛点出发，引出示例的价值

## 第 3 节：让 LLM "想清楚再说" —— Chain-of-Thought
- 学习目标：使用思维链处理复杂推理任务
- Bloom 层次：应用 + 分析
- 叙事入口：展示一个 LLM 算错的例子，引出"分步思考"的重要性

## 第 4 节：怎么知道 Prompt "好不好"？—— Prompt 评估
- 学习目标：建立 Prompt 评估的方法论和迭代思维
- Bloom 层次：评估
- 叙事入口：从"改了 Prompt 但不知道变好还是变差"的困境出发

## 第 5 节：Prompt Engineering 的边界 —— 什么能做，什么不能做
- 学习目标：理解 Prompt 的能力边界，知道什么时候该用其他方法
- Bloom 层次：分析 + 评估
- 叙事入口：从"过度神话 Prompt"的现象出发，建立理性认知

## AI 时代小专栏 1（第 1-2 节之间）
- 主题：Prompt Engineering 从"玄学"到"工程"—— 2024-2025 的方法论演进
- 与相邻章节关联：呼应第 1 节的设计原则，为第 2 节的 Few-shot 提供背景

## AI 时代小专栏 2（第 3-4 节之间）
- 主题：当 LLM 学会"慢思考"—— 推理模型的崛起与 CoT 的价值
- 与相邻章节关联：呼应第 3 节的 CoT，为第 4 节的评估方法铺垫

## TextAgent 进度
- 本周目标：Prompt 模板库 + 基础评估框架
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
| 小北 | 第 1 节 | 写了一个模糊的 Prompt，LLM 输出一大段无关内容，困惑"为什么它不懂我" | 展示新手常见错误，引出 Prompt 设计四要素 |
| 阿码 | 第 3 节 | 追问"CoT 会不会让 Token 消耗翻倍？成本怎么办？" | 引出成本与效果的权衡讨论，带入工程视角 |
| 老潘 | 第 4 节 | 点评评估方法："在公司里，我们不会只靠'感觉'判断 Prompt 好不好，要有测试集和量化指标" | 强调工程化的评估思维，为 Week 07 的系统评估铺垫 |

角色性格一致性检查：
- 小北：困惑 + 需要引导 + "为什么" ✅
- 阿码：追问边界 + 举一反三 + 成本意识 ✅
- 老潘：务实 + 工程经验 + 量化思维 ✅

================================================================================
-->

<!--
================================================================================
【AI 小专栏规划】
================================================================================

### AI 时代小专栏 1：Prompt Engineering 从"玄学"到"工程"—— 2024-2025 的方法论演进

位置：第 1-2 节之间（章节前段）

与相邻章节关联：
- 呼应第 1 节的设计原则："为什么现在有了'官方指南'而不是靠网上零散的'咒语'？"
- 为第 2 节的 Few-shot 提供背景："Few-shot 不是新概念，但 2024 年的研究让它更有据可循"

核心内容方向：
- 2024-2025 年 Prompt Engineering 方法论的标准化（OpenAI 官方指南、学术论文）
- 从"提示词工程"到"提示词工程学"的转变
- 企业实践中 Prompt 管理的工具化（版本控制、A/B 测试、监控）
- Prompt 模板库和框架的兴起

建议搜索词（含当前年份）：
- "OpenAI prompt engineering guide 2025"
- "prompt engineering best practices 2024 2025"
- "LLM prompt management tools enterprise 2025"
- "prompt engineering research papers 2024"

参考链接要求：必须来自 WebSearch 搜索结果，禁止编造

---

### AI 时代小专栏 2：当 LLM 学会"慢思考"—— 推理模型的崛起与 CoT 的价值

位置：第 3-4 节之间（章节中段）

与相邻章节关联：
- 呼应第 3 节的 CoT："Chain-of-Thought 不只是技巧，2025 年的推理模型把它变成了'出厂设置'"
- 为第 4 节的评估铺垫："推理模型的评估方法和普通模型不一样，需要看推理过程而不仅仅是结果"

核心内容方向：
- 2025 年推理模型的兴起（OpenAI o1、DeepSeek-R1 等）
- CoT 从"手动触发"到"内置能力"的演变
- 推理模型的成本与效果权衡
- "快思考"vs"慢思考"在 LLM 应用中的选择

建议搜索词（含当前年份）：
- "OpenAI o1 chain of thought reasoning 2025"
- "DeepSeek R1 reasoning model 2025"
- "LLM reasoning models comparison 2025"
- "chain of thought prompting research 2024 2025"

参考链接要求：必须来自 WebSearch 搜索结果，禁止编造

================================================================================
-->

<!--
================================================================================
【贯穿案例设计】
================================================================================

本章贯穿案例：客服工单自动分类系统

案例场景：
你所在的公司有一个客服工单系统，每天接收数百条用户反馈。老板希望你能做一个自动分类器，把工单分到正确的部门（技术支持、账务问题、功能建议、投诉、其他），并提取关键信息（产品、 urgency、用户 ID）。上周你已经用 LLM 做了一个原型，但准确率不稳定——有时候分类正确，有时候会漏掉关键信息，还有时候输出格式不规范导致后续处理失败。

案例演进路线：
- 第 1 节：分析现有 Prompt 的问题，用四要素重写
- 第 2 节：加入 Few-shot 示例，稳定输出格式
- 第 3 节：用 CoT 处理"边界模糊"的复杂工单
- 第 4 节：建立评估流程，测试不同 Prompt 版本的效果
- 第 5 节：讨论什么情况下应该用其他方法（规则引擎、传统分类模型）

每节结束时的"可交付物"：
- 第 1 节：一个符合四要素的 Prompt 初版
- 第 2 节：带有 Few-shot 示例的 Prompt v2
- 第 3 节：支持 CoT 的复杂工单处理 Prompt
- 第 4 节：一个包含测试集和评估指标的 Prompt 评估脚本
- 第 5 节：技术选型的决策文档

================================================================================
-->

<!--
================================================================================
【TextAgent 超级线规划】
================================================================================

本周 TextAgent 进度：Prompt 模板库 + 基础评估框架

具体任务：
1. 设计 Prompt 模板库
   - src/textagent/
     - prompts/
       - __init__.py
       - templates.py (Prompt 模板类)
       - examples.py (Few-shot 示例管理)
     - templates/
       - classify.yaml (分类任务模板)
       - summarize.yaml (摘要任务模板)
       - extract.yaml (实体抽取模板)

2. 实现 Few-shot 示例管理
   - 示例的存储和加载
   - 示例的动态选择（根据输入相似度）
   - 示例数量控制（平衡效果和成本）

3. 搭建简单的效果评估流程
   - 定义评估指标（准确率、格式合规率）
   - 构建小规模测试集（20-50 条）
   - 实现 Prompt 版本对比脚本

4. 记录 Prompt 迭代历史
   - report.md 中添加 Prompt 迭代表格
   - 记录每次修改的原因和效果变化

与本周知识点的关联：
- 第 1 节的四要素 → templates.py 的设计原则
- 第 2 节的 Few-shot → examples.py 的实现
- 第 4 节的评估 → 评估脚本的实现
- 第 5 节的边界讨论 → report.md 中的技术选型分析

================================================================================
-->

<!--
================================================================================
【锚点规划（供 ANCHORS.yml 参考）】
================================================================================

本章需要验证的核心结论（锚点）：

1. 【anchor:prompt-four-elements】
   claim: 包含角色、任务、约束、格式四要素的 Prompt，相比只有任务的 Prompt，输出符合预期的比例提升 30% 以上
   evidence: 在 50 条测试样本上的对比实验
   verification: tests/test_prompt_design.py

2. 【anchor:few-shot-stability】
   claim: 使用 3-5 个 Few-shot 示例可以将 JSON 输出的格式合规率从约 80% 提升到 95% 以上
   evidence: 对比有无 Few-shot 的输出格式合规率
   verification: tests/test_few_shot.py

3. 【anchor:cot-accuracy】
   claim: 对于需要多步推理的分类任务，使用 CoT 可以将准确率提升 10-20 个百分点
   evidence: 在边界模糊样本上的对比实验
   verification: tests/test_cot.py

4. 【anchor:prompt-evaluation-iteration】
   claim: Prompt 评估需要测试集和量化指标，"感觉变好了"不可靠
   evidence: 展示一个"感觉变好但实际变差"的案例
   verification: tests/test_evaluation.py

================================================================================
-->

<!--
================================================================================
【每节详细规划】
================================================================================
-->

## 第 1 节："帮我分类这条新闻"—— 为什么你的 Prompt 总是被误解？

你花了两分钟写了个 Prompt："请帮我分类以下新闻"。然后满怀期待地把那条关于苹果财报的新闻丢进去。结果 LLM 给你输出了三段话：第一段解释什么是新闻分类，第二段分析这条新闻涉及的公司和财务数据，第三段才说"我认为应该分到财经类"。

你盯着屏幕，心想：我只是要一个类别名啊。

小北把这输出复制给老潘看，老潘只回了一句："你让它分类，没说你要什么格式的分类。"

```text
小北（有点委屈）：但它不是挺聪明的吗？怎么连这个都猜不到？

老潘：LLM 不是读心术。你给的信息越少，它猜的空间越大。
```

问题出在哪？你只给了**任务**（"分类"），但没给**约束**（"只要类别名"）和**格式**（"不要解释"）。LLM 是一个"过度热情"的助手——它会尽力帮你，但如果你的指令不够具体，它就会"猜测"你的意图，然后可能猜错。

### Prompt 四要素：角色、任务、约束、格式

一个清晰的 Prompt 至少要包含四个要素。这不是什么神秘公式，而是沟通的基本礼貌：告诉对方"你是谁"、"做什么"、"不能做什么"、"结果长什么样"。

| 要素 | 是什么 | 为什么重要 |
|------|-------|-----------|
| **角色**（Role） | 告诉 LLM "你是谁" | 设定行为边界和专业程度 |
| **任务**（Task） | 告诉 LLM "做什么" | 明确目标 |
| **约束**（Constraint） | 告诉 LLM "不能做什么" | 防止过度输出或跑题 |
| **格式**（Format） | 告诉 LLM "输出长什么样" | 确保可解析、可对接 |

还记得上周我们讨论 Token 的时候说过吗？Prompt 越长，输入成本越高。所以这四个要素不是"写得越多越好"，而是"写得越精准越好"——用最少的 Token 把意图说清楚。这就好比写代码：注释要写，但废话不要写。

让我们用四要素重写刚才的 Prompt：

```text
角色：你是一个新闻分类助手。
任务：判断以下新闻属于哪个类别。
约束：只输出类别名称，不要解释原因。
格式：从以下选项中选一个：财经、科技、体育、娱乐。

新闻内容：{新闻文本}
```

同样的任务，这个 Prompt 更可能给你一个干净的"财经"两个字。

### 小北的"踩坑日记"：三个模糊 Prompt 的翻车现场

四要素框架听起来简单，但小北在实践里连踩了三个坑。

**第一个坑：动词不够具体**

小北接到任务，要分析一批新闻。他写了个 Prompt："分析这条新闻"。结果 LLM 给他输出了一段情感分析 + 一段主题提取 + 一段关键词总结——整整三段话，而小北只想要一个类别名。

"它怎么给我这么多？"小北把输出给老潘看。

"你让它'分析'，它就分析给你看。"老潘笑了，"'分析'太宽泛了，LLM 可能做情感分析、主题分析、语法分析，甚至帮你数形容词。你得说清楚：'判断这条新闻属于哪个类别：财经、科技、体育、娱乐'。"

**第二个坑：缺少边界约束**

小北吸取教训，把 Prompt 改成："提取新闻中的公司名"。这次输出确实简洁多了——直到他遇到一条新闻里根本没有公司名。LLM 输出："我在文本中没有找到公司名称，但根据上下文推测可能涉及科技行业……"

小北的解析代码直接崩了——它只期待一个公司名列表，不是一段解释。

阿码刚好路过，看了一眼："这是边界条件。写代码的时候你要测 null、测空字符串，写 Prompt 的时候也要想——如果没找到怎么办？"

"那我应该怎么写？"

"加一句：'如果没有提到公司，输出"无"'。告诉 LLM 边界在哪。"

**第三个坑：格式不明确**

小北又改了一版："用 JSON 格式输出公司名"。这次 LLM 倒是输出 JSON 了——但它加了注释、换了行、字段名还是 `company_names` 而不是 `companies`。

```json
// 提取的公司列表
{
  "company_names": ["苹果公司"],  // 可能还有更多
  "note": "文本中只提到了一家公司"
}
```

小北的 JSON 解析器又崩了。

"JSON 格式"还是太宽——LLM 可能加注释、换行、用你不期望的字段名。老潘拍拍他的肩膀："给它一个具体的 Schema：`{"companies": ["公司名1", "公司名2"]}`。精确到字段名，它才能精准命中。"

上周我们用 JSON Mode 保证输出是合法的 JSON，这周我们从 Prompt 层面进一步约束——告诉 LLM 具体的字段名、类型、嵌套结构。两者配合使用效果最好：JSON Mode 确保"语法正确"，Prompt 约束确保"内容正确"。

现在你有了四要素框架。这一节你做的不是"背诵四要素"，而是学会了**把模糊意图翻译成 LLM 能听懂的指令**：角色设定行为边界，任务明确目标，约束防止过度输出，格式确保可解析。小北的三个踩坑现场——动词太宽泛、缺边界约束、格式不明确——你以后大概率能避开。

但还有一个问题：即使 Prompt 写得很清楚，LLM 的输出有时候还是会"飘"——这次给你"财经"，下次给你"财经新闻"，再下次给你"这篇文章属于财经类"。下一节我们来看怎么用 Few-shot 示例稳定输出。

> **AI 时代小专栏：Prompt Engineering 从"玄学"到"工程"—— 2024-2025 的方法论演进**
>
> 2023 年的时候，Prompt Engineering 还像是一门"玄学"：网上流传着各种"魔法咒语"，什么"请作为一个专家"、"深呼吸，仔细思考"——有效吗？有时候有，但没人说得清为什么。
>
> 2024 年到 2025 年，情况开始变化。OpenAI 发布了官方的 Prompt Engineering 指南，不再是什么"祖传秘方"，而是有结构、有方法、可复现的实践。学术论文也开始系统性地研究 Few-shot、CoT、Self-consistency 等技术的效果边界——不是"越多越好"，而是"在什么条件下有效"。2025 年，企业级的 Prompt 管理工具开始涌现：PromptLayer 提供 Git-like 版本控制，Langfuse 整合了可观测性，LangSmith 支持 CI/CD 集成——Prompt 终于被当成"代码"来管理了。
>
> 这意味着什么？意味着你正在学的不是"技巧"，而是一套正在工程化的方法论。它在变成熟，也在变标准。
>
> 参考（访问日期：2026-02-19）：
> - OpenAI Prompt Engineering 官方指南: https://platform.openai.com/docs/guides/prompt-engineering
> - Microsoft Azure OpenAI 官方文档（2025年12月更新）: https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/prompt-engineering
> - 企业级 Prompt 管理工具对比（Arize AI, 2025年11月）: https://arize.com/blog/top-5-ai-prompt-management-tools-of-2025/
> - Prompting Guide 社区资源: https://www.promptingguide.ai/

## 第 2 节：给 LLM 看 "参考答案" —— Few-shot Learning

你按四要素重写了 Prompt，分类准确率确实上去了。但还有个恼人的问题：输出格式不稳定。

```
第 1 次调用：财经
第 2 次调用：财经类
第 3 次调用：这条新闻属于财经类别
```

你的解析代码要疯了。你写了个 `if result == "财经"`，结果第二次调用就漏掉了。改成正则匹配？那"财经类"和"财经类别"又不一样。干脆把所有可能的变体都列出来？那"财经方向"、"财经领域"怎么办？

"能不能让它每次都输出一样的格式？"你开始怀念传统软件的确定性了。

答案其实很简单：给它看几个"参考答案"。

### Few-shot 的原理：从示例中学习

**Few-shot Learning**（少样本学习）的核心思想很简单：与其用文字描述"你要怎么做"，不如直接给它看几个"输入-输出"的例子。LLM 有很强的模式匹配能力，看到几个例子后，它就能"猜"出你想要的格式和风格。

```text
角色：你是一个新闻分类助手。

示例：
输入："苹果公司发布新款 iPhone，搭载 A18 芯片"
输出：科技

输入："中国男篮在亚运会决赛中战胜韩国队"
输出：体育

输入："央行宣布下调存款准备金率 0.5 个百分点"
输出：财经

任务：判断以下新闻属于哪个类别。
约束：只输出类别名称，格式与示例一致。
格式：从以下选项中选一个：财经、科技、体育、娱乐。

新闻内容：{新闻文本}
```

有了这三个示例，LLM 输出"财经类"或"这条新闻属于财经类别"的概率会大大降低——因为它"看到"了你要的是单个类别名。

### Few-shot 示例的选择原则

不是随便抓几个示例就能用的。阿码曾经试过把最近 20 条分类记录全塞进 Prompt，结果 Token 消耗翻了三倍，准确率反而下降了——因为有些示例本身就标错了。

好的 Few-shot 示例应该满足几个条件：

**覆盖主要类别**：如果分类任务有四个类别，示例最好能覆盖全部四个。否则 LLM 可能"忘记"你没展示的那个类别。

**格式严格一致**：所有示例的输入输出格式必须完全一样。如果第一个示例输出"科技"，第二个输出"类别：科技"，模型就会困惑。

**难度适中**：全是简单示例，模型学不到边界情况；全是复杂示例，可能"带偏"模型对常规情况的处理。一个实用的做法是：70% 标准案例 + 30% 边界案例。

**避免偏见**：示例不能暗示某种"偏好"。比如科技类的示例全是正面新闻，模型可能误以为"科技类 = 好消息"。

```text
阿码追问：示例给多少个合适？越多越好吗？

好问题。研究表明，3-5 个示例通常就够了。太少（1 个）模型学不到模式；
太多（10+）会增加 Token 消耗，而且边际收益递减——第七个示例的效果远不如第三个。
更关键的是示例的质量，而不是数量。一个清晰展示边界的示例，比五个雷同的示例都有用。
```

### Few-shot 在 TextAgent 中的实现

让我们把 Few-shot 示例管理起来，而不是每次都写在 Prompt 里：

```python
# src/textagent/prompts/examples.py
from typing import List, Dict
import yaml

class FewShotManager:
    """管理 Few-shot 示例"""

    def __init__(self, examples_file: str):
        with open(examples_file, 'r', encoding='utf-8') as f:
            self.examples = yaml.safe_load(f)

    def get_examples(self, task: str, category: str = None, n: int = 3) -> List[Dict]:
        """
        获取指定任务的示例

        Args:
            task: 任务类型（classify/summarize/extract）
            category: 类别（可选，用于分类任务）
            n: 返回的示例数量
        """
        task_examples = self.examples.get(task, [])

        if category:
            # 优先选择目标类别的示例
            task_examples = [e for e in task_examples if e.get('category') == category]

        return task_examples[:n]

    def format_examples(self, examples: List[Dict]) -> str:
        """将示例格式化为 Prompt 片段"""
        lines = ["示例："]
        for ex in examples:
            lines.append(f"输入：\"{ex['input']}\"")
            lines.append(f"输出：{ex['output']}")
            lines.append("")
        return "\n".join(lines)
```

对应的 YAML 配置文件（节选）：

```yaml
# templates/classify_examples.yaml
classify:
  - input: "苹果公司发布新款 iPhone，搭载 A18 芯片"
    output: "科技"
    category: "科技"
  - input: "央行宣布下调存款准备金率 0.5 个百分点"
    output: "财经"
    category: "财经"
  # ... 更多示例见完整配置
```

完整的 YAML 文件包含所有四个类别的示例，并支持按 `category` 字段筛选。实际项目中，你可能有 20-50 个示例，覆盖各种边界情况。

现在你有了稳定的输出格式。但有些任务不只是"分类"这么简单——它们需要"想一想"。下一节我们来聊聊 Chain-of-Thought。

## 第 3 节：让 LLM "想清楚再说" —— Chain-of-Thought

你收到一条模棱两可的工单：

```text
"我用你们 App 充值了会员，但是显示还是普通用户，而且客服一直没人接，
 我已经等了 20 分钟了，再不解决我就要投诉了！"
```

这条工单应该分到哪个部门？

- 技术支持？—— 因为有"显示还是普通用户"的技术问题
- 账务问题？—— 因为涉及"充值"
- 投诉？—— 因为用户说了"我要投诉"

你把它丢给 LLM，第一次调用返回"投诉"，第二次返回"账务问题"，第三次返回"技术支持"。小北在旁边看得目瞪口呆："这模型是掷骰子吗？"

问题不是模型不稳定，而是这个任务本身就需要**推理**：先理解用户的核心诉求是什么（会员权益），再判断哪个部门能解决这个问题（账务），同时注意到用户的情绪需要安抚（可能需要升级处理）。

直接让 LLM 给答案，就像让一个人不写草稿直接做数学题——容易出错。但如果让它把思考过程写出来呢？

### CoT：分步思考，减少错误

**Chain-of-Thought**（思维链）的核心思想是：让 LLM 把推理过程写出来，而不是直接跳到结论。

```text
角色：你是一个客服工单分类助手。

任务：判断以下工单应该分到哪个部门。

请按以下步骤思考：
1. 用户遇到了什么问题？
2. 问题的核心诉求是什么？
3. 哪个部门最适合处理这个诉求？
4. 最终分类结果是什么？

工单内容：{工单文本}

请按上述步骤分析，最后输出部门名称。
```

LLM 可能会输出：

```text
1. 用户遇到的问题：充值后会员状态未更新，且客服响应慢
2. 核心诉求：会员权益问题需要解决
3. 最适合的部门：账务问题（核心是充值和会员状态），
   但投诉情绪强烈，可能需要升级处理
4. 最终分类：账务问题（建议标记为高优先级）
```

有了推理过程，你不仅能看到结论，还能理解"为什么"。更重要的是，分步思考本身就能减少错误——因为 LLM 被迫"慢下来"，而不是凭直觉快速给出答案。

```text
阿码追问：CoT 会不会让 Token 消耗翻倍？成本怎么办？

确实会。CoT 的输出比直接分类长 5-10 倍。如果你要处理 10000 条工单，
用 CoT 可能比不用多花几十美元。

但你要权衡：是省这点 API 费用，还是提高准确率？
如果分类错误导致工单被转来转去，用户等了三天还没人处理，
客服成本和用户满意度损失可能远超那几十美元。

老潘会说：在公司里，我们会对"高价值"工单用 CoT——比如 VIP 用户、
涉及金额大的投诉。简单明确的工单用快速分类，不需要想太多。
不是一刀切，而是分级处理。
```

### CoT 的适用场景

CoT 不是万能药。它适合：

- **需要多步推理的任务**：数学问题、逻辑推理、复杂分类
- **边界模糊的输入**：可能有多种解释的情况
- **需要可解释性的场景**：你要知道"为什么是这个答案"

它不适合：

- **简单明确的任务**：直接分类就够了，CoT 反而增加延迟和成本
- **对延迟敏感的场景**：生成推理过程需要更多时间
- **不需要解释的场景**：只要答案，不需要过程

### CoT 的两种写法

**写法 1：显式步骤提示**（推荐初学者）

```text
请按以下步骤思考：
1. ...
2. ...
3. ...
```

**写法 2：零样本 CoT**

```text
Let's think step by step.
```

这句"魔法咒语"在 2022 年被发现有奇效——即使不给具体步骤，只是让 LLM "一步一步想"，也能显著提升推理任务的准确率。但它不如显式步骤稳定，适合快速实验。

现在你有了 CoT 这个"武器"。但怎么知道你的 Prompt 是变好了还是变差了？靠"感觉"是不行的——你需要评估。下一节我们来建立 Prompt 的评估框架。

> **AI 时代小专栏：当 LLM 学会"慢思考"—— 推理模型的崛起与 CoT 的价值**
>
> 2024 年底到 2025 年初，一类新的 LLM 开始出现：**推理模型**（Reasoning Models）。OpenAI 的 o1、DeepSeek 的 R1，它们和普通 LLM 的最大区别是——会"慢思考"。
>
> 普通的 LLM 是"快思考"：看到问题，立刻生成答案。这就像人类的直觉反应，快但容易出错。推理模型则会在内部生成 CoT（你可以理解为"草稿纸"），反复验证、修正，最后才给出答案。2025 年 1 月，DeepSeek 发布了 R1 模型，在 AIME 数学竞赛基准测试中得分 83%，接近 OpenAI o1 的水平——但 API 调用成本只有对方的 5% 左右。更关键的是，研究发现推理能力可以通过纯强化学习激发，无需人类标注的推理数据。
>
> 这意味着什么？意味着 CoT 从"你需要手动触发"变成了"模型内置能力"。当你使用推理模型时，不需要特意写"Let's think step by step"——它自己会想。但普通模型仍然需要你显式地引导。所以你刚学的 CoT 技巧，在 AI 时代不但没过时，反而更重要了——它帮你理解"模型是怎么想的"。
>
> 参考（访问日期：2026-02-19）：
> - OpenAI o1 官方介绍: https://openai.com/index/learning-to-reason-with-llms/
> - DeepSeek-R1 GitHub 仓库: https://github.com/deepseek-ai/DeepSeek-R1
> - DeepSeek-R1 论文 "Incentivizing Reasoning Capability in LLMs": https://arxiv.org/pdf/2501.12948
> - Nature 论文（2025年9月）关于推理能力的强化学习: https://www.nature.com/articles/s41586-025-09422-z

## 第 4 节：怎么知道 Prompt "好不好"？—— Prompt 评估

你改了 Prompt，加了一些 Few-shot 示例，又尝试了 CoT。跑了十几条测试，感觉比之前好了。于是你准备提交代码，上线部署。

### 用 Pydantic 定义数据结构

在开始评估之前，我们需要一个可靠的方式来定义测试用例和评估结果。

小北最近刚踩过一个坑。他用 `dataclasses` 定义了一个评估结果类：

```python
from dataclasses import dataclass

@dataclass
class EvalResult:
    accuracy: float
    format_compliance: float
```

跑完评估后，他兴冲冲地去看结果——结果程序在计算平均值的时候崩溃了。原来 LLM 输出的准确率是字符串 `"88%"` 而不是浮点数 `0.88`，`dataclasses` 默认不做运行时类型检查，默默接受了这个字符串，直到后续代码尝试计算时才爆炸。

"为什么 Python 不帮我拦住这个问题？"小北一脸委屈。

老潘看了一眼代码："Python 的哲学是'显式优于隐式'，但在处理 LLM 这种'不可靠输入'时，你需要更严格的数据验证。试试 Pydantic。"

**Pydantic** 的核心价值就在这里：它**不只是类型提示，而是真正的运行时验证**。当 LLM 输出"0.95"（字符串）时，Pydantic 会自动把它转成 `0.95`（浮点数）；当 LLM 输出 `1.5`（超出范围）时，Pydantic 会直接报错——问题在入口就被拦住了，而不是等到某个奇怪的地方崩溃。

```python
from dataclasses import dataclass
from pydantic import BaseModel, Field

# dataclasses：类型只是"提示"，运行时不检查
@dataclass
class ResultDC:
    accuracy: float  # 传入 "0.95"（字符串）不会报错，但后续计算时报 TypeError

# Pydantic：运行时会验证和转换
class ResultPD(BaseModel):
    accuracy: float = Field(ge=0, le=1)  # 传入 "0.95" 会自动转成 0.95
                                         # 传入 1.5 会直接报错
```

Pydantic 还有两个在 LLM 应用中特别有用的能力：
- **自动生成 JSON Schema**：可以传给 LLM 作为"格式说明书"
- **与 OpenAI 等框架无缝集成**：OpenAI 的 structured outputs 直接支持 Pydantic 模型

如果你之前没用过 Pydantic，不用担心——它的写法和 `dataclasses` 几乎一样，只是多了运行时验证。

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class TestCase(BaseModel):
    """测试用例"""
    input: str
    expected_output: str
    metadata: Optional[dict] = None  # 可选的额外信息

class EvalResult(BaseModel):
    """评估结果"""
    prompt_version: str
    accuracy: float = Field(ge=0, le=1)  # 限制在 0-1 范围
    format_compliance: float = Field(ge=0, le=1)
```

`Field(ge=0, le=1)` 的意思是：这个字段的值必须 `>= 0` 且 `<= 1`。如果你不小心传了 `1.5`，Pydantic 会直接报错——这比在生产环境里发现数据异常要安全得多。

老潘拦住了你："你怎么知道变好了？"

"感觉啊，之前经常输出乱七八糟的，现在都很整齐。"

老潘摇摇头："感觉是不可靠的。你刚改完 Prompt，心理上会倾向于'它应该变好了'，然后就会无意识地挑那些变好的案例来看。这在工程上叫确认偏误。"

"那怎么办？"

"要有测试集，有量化指标，有版本对比。Prompt 也是代码，需要测试。"

上周我们封装了一个 LLM Client 类，统一了错误处理和日志记录。这周我们要在这个基础上加入 Prompt 版本管理——每次评估都记录使用的是哪个 Prompt 版本，这样下周你还能复现"当时 88% 准确率是怎么跑出来的"。

### 建立 Prompt 评估流程

一个基础的 Prompt 评估流程其实不复杂，就四步：

**准备测试集**：20-50 条有标注的样本。太少（比如 5 条）偶然性太大；太多（比如 500 条）人工标注成本高。20 条起步，逐步扩充。

**定义指标**：准确率是最直观的，但不是唯一的。格式合规率（输出能不能被程序解析）、延迟（用户等多久）、Token 消耗（花多少钱）——这些都要看。

**批量测试**：用同一个测试集测试不同版本的 Prompt，而不是每次改完手动跑几条。

**记录结果**：用表格或图表展示对比。下次老板问"为什么用这个 Prompt"，你能拿出数据说话。

#### 简化版：30 行代码跑起来

别被"评估框架"吓到，核心逻辑其实就是个循环加计数：

```python
# 最简版本：30 行代码就能跑
test_cases = [
    {"input": "苹果发布新 iPhone", "expected": "科技"},
    {"input": "央行降准 0.5 个百分点", "expected": "财经"},
    # ... 更多测试用例
]

def evaluate_simple(client, test_cases, build_prompt):
    """最简评估：只算准确率"""
    correct = 0
    for case in test_cases:
        prompt = build_prompt(case["input"])
        response = client.call(prompt)
        if response.strip() == case["expected"]:
            correct += 1
    return correct / len(test_cases)

# 调用
acc = evaluate_simple(client, test_cases, build_prompt_v1)
print(f"准确率: {acc:.1%}")
```

这 30 行代码已经能帮你回答"改了 Prompt 效果有没有变好"这个问题。先跑起来，再逐步完善。

#### 完整版：加上更多指标

> 💡 **阅读提示**：下面的完整版代码较长，涉及 Pydantic 数据结构、多指标计算、错误处理等多个概念。如果你是第一次接触，建议先关注：
> 1. `TestCase` 和 `EvalResult` 这两个数据结构"长什么样"
> 2. `evaluate_prompt` 函数的输入输出是什么
> 3. 最后的对比表格是怎么生成的
>
> 具体实现细节可以等实际使用时再细读。

当你需要更细的指标（格式合规率、延迟、Token 消耗）时，可以升级到完整版：

```python
# src/textagent/evaluation/prompt_eval.py
from typing import List, Dict, Callable, Optional
from pydantic import BaseModel, Field
import json

class TestCase(BaseModel):
    """测试用例（使用 Pydantic 进行数据验证）"""
    input: str
    expected_output: str
    metadata: Optional[Dict] = None  # 可选的额外信息

class EvalResult(BaseModel):
    """评估结果"""
    prompt_version: str
    accuracy: float = Field(ge=0, le=1)  # 限制在 0-1 范围
    format_compliance: float = Field(ge=0, le=1)
    avg_latency_ms: float
    total_tokens: int
    error_cases: List[Dict] = Field(default_factory=list)

def evaluate_prompt(
    client,
    test_cases: List[TestCase],
    build_prompt: Callable[[str], str],
    parse_output: Callable,
    prompt_version: str = "v1",
) -> EvalResult:
    """
    评估一个 Prompt 版本

    Args:
        client: LLM Client
        test_cases: 测试用例列表
        build_prompt: 构建 Prompt 的函数，接受输入文本，返回完整 Prompt
        parse_output: 输出解析函数
        prompt_version: Prompt 版本号
    """
    correct = 0
    format_errors = 0
    total_latency = 0
    total_tokens = 0
    error_cases = []

    for case in test_cases:
        prompt = build_prompt(case.input)

        try:
            # 记录开始时间
            import time
            start = time.time()

            response = client.call(prompt)
            parsed = parse_output(response)

            # 记录结束时间
            latency = (time.time() - start) * 1000  # ms
            total_latency += latency
            # 注意：这里假设 client 有 last_usage 属性
            # 实际实现中，你可能需要从 client.response.usage 获取
            # 或者在调用时让 client 返回 usage 信息
            if hasattr(client, 'last_usage') and client.last_usage:
                total_tokens += client.last_usage.total_tokens

            # 检查正确性
            if parsed == case.expected_output:
                correct += 1
            else:
                error_cases.append({
                    "input": case.input,
                    "expected": case.expected_output,
                    "actual": parsed,
                    "raw_response": response,
                })

        except Exception as e:
            format_errors += 1
            error_cases.append({
                "input": case.input,
                "expected": case.expected_output,
                "error": str(e),
            })

    n = len(test_cases)
    return EvalResult(
        prompt_version=prompt_version,
        accuracy=correct / n,
        format_compliance=(n - format_errors) / n,
        avg_latency_ms=total_latency / n,
        total_tokens=total_tokens,
        error_cases=error_cases,
    )
```

### 对比不同 Prompt 版本

```python
# 准备测试集
test_cases = [
    TestCase("苹果发布新款 iPhone", "科技"),
    TestCase("央行降准 0.5 个百分点", "财经"),
    TestCase("某演员官宣结婚", "娱乐"),
    # ... 更多测试用例
]

# 定义 Prompt 构建函数（使用 f-strings）
SYSTEM_PROMPT_V1 = "你是一个新闻分类助手。"

def build_prompt_v1(input_text: str) -> str:
    """构建 Prompt v1（无 Few-shot）"""
    return f"""角色：{SYSTEM_PROMPT_V1}
任务：判断以下新闻属于哪个类别。
约束：只输出类别名称，不要解释。
格式：财经、科技、体育、娱乐。

新闻内容：{input_text}"""

def build_prompt_v2(input_text: str) -> str:
    """构建 Prompt v2（有 Few-shot）"""
    return f"""角色：{SYSTEM_PROMPT_V1}

示例：
输入："苹果公司发布新款 iPhone"
输出：科技

输入："央行降准 0.5 个百分点"
输出：财经

任务：判断以下新闻属于哪个类别。
约束：只输出类别名称，格式与示例一致。
格式：财经、科技、体育、娱乐。

新闻内容：{input_text}"""

def parse_category(response: str) -> str:
    """解析分类结果"""
    return response.strip()

# 测试 Prompt v1（无 Few-shot）
result_v1 = evaluate_prompt(client, test_cases, build_prompt_v1, parse_category, "v1")

# 测试 Prompt v2（有 Few-shot）
result_v2 = evaluate_prompt(client, test_cases, build_prompt_v2, parse_category, "v2")

# 对比结果
print(f"{'指标':<20} {'v1':>10} {'v2':>10} {'变化':>10}")
print("-" * 52)
print(f"{'准确率':<20} {result_v1.accuracy:>10.2%} {result_v2.accuracy:>10.2%} {result_v2.accuracy - result_v1.accuracy:>+10.2%}")
print(f"{'格式合规率':<20} {result_v1.format_compliance:>10.2%} {result_v2.format_compliance:>10.2%} {result_v2.format_compliance - result_v1.format_compliance:>+10.2%}")
print(f"{'平均延迟(ms)':<20} {result_v1.avg_latency_ms:>10.0f} {result_v2.avg_latency_ms:>10.0f} {result_v2.avg_latency_ms - result_v1.avg_latency_ms:>+10.0f}")
print(f"{'总 Token 消耗':<20} {result_v1.total_tokens:>10} {result_v2.total_tokens:>10} {result_v2.total_tokens - result_v1.total_tokens:>+10}")
```

输出示例：

```text
指标                      v1         v2       变化
----------------------------------------------------
准确率                 75.00%     88.00%    +13.00%
格式合规率             82.00%     96.00%    +14.00%
平均延迟(ms)              450        520      +70
总 Token 消耗           15000      22000    +7000
```

现在你有了数据支撑：v2 的准确率提升了 13%，格式合规率提升了 14%，但 Token 消耗也增加了 47%。这个 trade-off 值不值？取决于你的业务场景。

### 避免"过拟合"测试集

一个常见的坑是：你不断调整 Prompt，让它在测试集上表现越来越好——90%、92%、95%——然后信心满满地上线。结果实际效果一塌糊涂。

为什么？因为你可能"过拟合"了测试集。Prompt 不是在学通用的分类规则，而是在"记住"测试集的特殊模式。比如你的测试集里所有财经新闻都提到"股价"，于是 Prompt 学到"看到股价就是财经"——但实际数据里可能有很多提到"股价"的科技新闻。

阿码会问："这和机器学习里的过拟合不是一回事吗？"

确实是同一个问题。避免方法也类似：

**测试集要多样化**：覆盖不同长度、不同风格、不同来源的输入。不能全是正规媒体的新闻，也得有社交媒体的帖子。

**保留验证集**：测试集用来调参，验证集用来最终评估。验证集的数据不要在调优过程中看，只在"上线前最后检查"时用一次。

**定期更新测试集**：每周加入几条新的真实案例，防止 Prompt "老化"。

老潘补充："在公司里，我们还会做 A/B 测试——让新旧 Prompt 同时处理线上流量，看真实业务指标的变化。这比离线测试集更可靠，但成本也更高。"

### 常见评估误区

除了过拟合，还有几个评估时的常见坑：

**误区一：只看准确率，不看错误分布**

准确率 85% 听起来不错。但如果 15% 的错误全都集中在"投诉"这一类——可能占了投诉类工单的 50%——那问题就严重了。投诉处理不当会直接导致用户流失。

```python
# 错误分析：不只是数错了多少，还要看错在哪
def analyze_errors(eval_result: EvalResult) -> dict:
    """按类别统计错误分布"""
    from collections import defaultdict
    errors_by_category = defaultdict(lambda: {"wrong": 0})

    # 第一步：遍历所有错误案例，按类别统计
    for case in eval_result.error_cases:
        expected = case.get("expected", "")
        if isinstance(expected, str):
            # 假设 expected 就是分类名称（如"技术支持"、"账务问题"）
            category = expected
            errors_by_category[category]["wrong"] += 1

    # 第二步：计算每个类别的错误占比
    total_errors = len(eval_result.error_cases)
    return {
        cat: data["wrong"] / total_errors if total_errors > 0 else 0
        for cat, data in errors_by_category.items()
    }
```

**误区二：测试集太小，结论不可靠**

只有 10 条测试用例，准确率从 70% 涨到 90%——这可能是随机波动。统计学上，10 条样本的置信区间很宽，这个"提升"可能只是运气。

经验法则：
- **20-50 条**：初步判断，能看到明显问题
- **100-200 条**：比较可靠的对比
- **500+ 条**：可以做精细分析

**误区三：忽视基线对比**

你的 Prompt 准确率 85%，是好是坏？没有基线就没法判断。

常见的基线：
- **随机基线**：瞎猜的准确率（比如 4 分类任务是 25%）
- **规则基线**：简单的 if-else 规则能到多少
- **旧版基线**：之前的 Prompt 版本

小北恍然大悟："所以 85% 相比随机基线的 25% 是巨大提升，但如果规则基线已经 80% 了，那就是'费大力气提升 5 个点'？"

"对。"老潘点头，"这就是为什么我们说'没有基线的评估是耍流氓'。"

## 第 5 节：Prompt Engineering 的边界 —— 什么能做，什么不能做

学了这么多 Prompt 技巧，你可能开始觉得：只要 Prompt 写得好，LLM 什么都能做。

慢着。这是过度神话。老潘见过太多项目"把一切丢给 LLM"，最后以失败告终。

### Prompt 能做的

**快速原型验证**：产品经理说"能不能做个自动分类"，你 10 分钟就能搭个原型跑起来。传统机器学习方法？光是标注数据就得一周。

**小规模生产应用**：每天几百次调用，成本几美元，效果稳定。对于很多内部工具、低频场景，完全够用。

**复杂推理任务**：配合 CoT，能处理那些"需要想一想"的问题。有些逻辑判断用规则写不出来，但 LLM 能"理解"。

**格式转换和抽取**：从杂乱的文本里提取结构化信息——"把这段会议记录转成 JSON"、"从这个 PDF 里提取所有日期和人名"。以前要写正则的活，现在一句话就能搞定。

### Prompt 不擅长（或不如其他方法）的

但 Prompt Engineering 不是万能钥匙。有些场景，其他方法更合适。

**超大规模应用**：每天百万次调用，每次 0.01 美元，一个月就是 30 万美元。传统分类模型可能只要十分之一的成本。

**对准确率要求极高的场景**：医疗诊断、金融风控，99% 都不够——那 1% 的错误可能意味着生命或巨额损失。LLM 会"幻觉"、会"猜"，不适合这种场景。

**需要实时响应的场景**：LLM 的延迟在几百毫秒到几秒，不适合高频交易、实时推荐这种毫秒级响应的场景。

**需要完全可解释的场景**：即使有 CoT，LLM 的推理过程仍然是黑盒。"为什么判定这个用户是欺诈？"LLM 给出的理由可能是"感觉不对"——这在监管审查时是通不过的。

### 知道什么时候换方法

假设你的客服工单分类系统上线了，每天处理 5000 条工单，准确率 85%。老板问能不能再提高。

你拿着这个问题去找老潘。

"有三种路子，"老潘掰着手指，"看你愿意投什么。"

"第一条，继续优化 Prompt。花几天时间调，几十美元跑测试集，能再提个 2 到 5 个点。但有个坑——你调着调着，Prompt 可能就变成'背测试集答案'了，上线反而更差。"

"第二条，上传统机器学习。先收集 5000 条标注数据——对，得人标——然后训练、部署、监控。开发周期一个月起步，后续还得管'数据漂移'、'模型监控'、'定期重训'这些事。能提 5 到 10 个点，但你要问问自己值不值。"

"第三条，走混合路线。简单明确的用规则——标题含'退款'直接分账务。边界模糊的才走 LLM。复杂度会上升，但成本可控，整体能提 3 到 8 个点。"

小北听完有点懵："那……选哪个？"

"没有标准答案。"老潘笑了，"看你的资源、时间、和对准确率的要求。但关键是——你得知道每个选项的成本和收益，不能无脑'All in LLM'。"

Prompt Engineering 是一个工具，不是万能药。知道工具的边界，比掌握工具的技巧更重要。

### 下周预告：当 Prompt 遇到知识库

小北问了一个老潘没法用 Prompt 解决的问题："老板让我做一个'智能客服'，要能回答产品规格、保修政策、退换货流程——这些信息都在公司内部文档里，几百页呢。我怎么把它们塞进 Prompt？"

老潘摇摇头："塞不进去的。Prompt 有长度限制，而且这些文档天天变，你不可能每次都改 Prompt。"

"那怎么办？"

"下周我们学 RAG——检索增强生成。"老潘说，"简单说，就是把文档切成小块存起来，用户提问时先搜出相关的内容，再把这些内容喂给 LLM。这样 LLM 就能'看见'你的知识库了。"

"这和直接把文档贴给 LLM 有什么区别？"

"区别大了。"老潘掰着手指数，"第一，文档太长 LLM 会'忘'前面的内容；第二，每次都传完整文档 Token 成本爆炸；第三，文档更新了你得改 Prompt——RAG 这些问题都能解决。"

阿码插嘴："所以 RAG 是 Prompt Engineering 的升级版？"

"不是升级，是组合。"老潘纠正，"RAG 里仍然要用 Prompt——告诉 LLM'这是检索到的内容，请基于这些内容回答'。你现在学的 Prompt 技巧，下周全用得上。"

<!--
================================================================================
【TextAgent 进度】
================================================================================
-->

## TextAgent 进度

上周 TextAgent 有了"骨架"——LLM Client 和三种基础任务（分类、摘要、抽取）。但这骨架有个问题：每次调用都要手写 Prompt，而且写完就忘了，下周想复现都不知道"当时怎么写的"。

这周我们给它加一个"大脑"：Prompt 模板库和评估框架。模板库把 Prompt 变成可复用的"配方"，评估框架让你能判断"配方改得好不好"。

### Prompt 模板库

```python
# src/textagent/prompts/templates.py
from pydantic import BaseModel, Field
from typing import List, Optional
import yaml

class PromptTemplate(BaseModel):
    """Prompt 模板（使用 Pydantic 进行配置验证）"""
    name: str
    role: str
    task: str
    constraints: List[str] = Field(default_factory=list)
    output_format: str = ""
    few_shot_examples: Optional[List[dict]] = None
    use_cot: bool = False
    cot_steps: Optional[List[str]] = None

    def render(self, input_text: str, examples: List[dict] = None) -> str:
        """渲染 Prompt"""
        parts = [f"角色：{self.role}"]

        # 添加 Few-shot 示例（合并传入的 examples 和模板中的 few_shot_examples）
        merged_examples = (self.few_shot_examples or []) + (examples or [])
        if merged_examples:
            parts.append("\n示例：")
            for ex in merged_examples:
                parts.append(f"输入：\"{ex['input']}\"")
                parts.append(f"输出：{ex['output']}")
            parts.append("")

        # 添加任务
        parts.append(f"任务：{self.task}")

        # 添加约束
        if self.constraints:
            parts.append("约束：")
            for c in self.constraints:
                parts.append(f"- {c}")

        # 添加 CoT 步骤
        if self.use_cot and self.cot_steps:
            parts.append("\n请按以下步骤思考：")
            for i, step in enumerate(self.cot_steps, 1):
                parts.append(f"{i}. {step}")

        # 添加输出格式
        parts.append(f"\n格式：{self.output_format}")

        # 添加输入
        parts.append(f"\n{input_text}")

        return "\n".join(parts)


class PromptLibrary:
    """Prompt 模板库"""

    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.templates = {t['name']: PromptTemplate(**t) for t in self.config['templates']}

    def get(self, name: str) -> PromptTemplate:
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        return list(self.templates.keys())
```

模板配置文件：

```yaml
# templates/prompts.yaml
templates:
  - name: news_classify
    role: "你是一个新闻分类助手"
    task: "判断以下新闻属于哪个类别"
    constraints:
      - "只输出类别名称"
      - "不要解释原因"
    output_format: "从以下选项中选一个：财经、科技、体育、娱乐"
    few_shot_examples:
      - input: "苹果公司发布新款 iPhone"
        output: "科技"
      - input: "央行降准 0.5 个百分点"
        output: "财经"

  - name: ticket_classify_cot
    role: "你是一个客服工单分类助手"
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
```

### 评估框架

```python
# src/textagent/evaluation/evaluator.py
from pydantic import BaseModel, Field
from typing import List, Dict
import json
import csv

class EvalReport(BaseModel):
    """评估报告（使用 Pydantic 确保数据结构一致性）"""
    prompt_version: str
    test_set_size: int
    accuracy: float = Field(ge=0, le=1)
    format_compliance: float = Field(ge=0, le=1)
    avg_latency_ms: float
    total_cost_usd: float
    error_analysis: List[Dict] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """生成 Markdown 报告"""
        return f"""
## Prompt 评估报告：{self.prompt_version}

| 指标 | 值 |
|------|-----|
| 测试集大小 | {self.test_set_size} |
| 准确率 | {self.accuracy:.2%} |
| 格式合规率 | {self.format_compliance:.2%} |
| 平均延迟 | {self.avg_latency_ms:.0f}ms |
| 总成本 | ${self.total_cost_usd:.4f} |

### 错误分析

{self._format_errors()}
"""

    def _format_errors(self) -> str:
        if not self.error_analysis:
            return "无错误"
        lines = []
        for e in self.error_analysis[:5]:  # 只显示前 5 个
            lines.append(f"- 输入：{e['input'][:50]}...")
            lines.append(f"  期望：{e['expected']}")
            lines.append(f"  实际：{e['actual']}")
        return "\n".join(lines)


class PromptEvaluator:
    """Prompt 评估器"""

    def __init__(self, client, test_set_path: str):
        self.client = client
        self.test_cases = self._load_test_set(test_set_path)

    def _load_test_set(self, path: str) -> List[Dict]:
        with open(path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def evaluate(self, template: PromptTemplate, version: str) -> EvalReport:
        """运行评估"""
        from .prompt_eval import evaluate_prompt, TestCase, EvalResult

        test_cases = [
            TestCase(tc['input'], tc['expected'])
            for tc in self.test_cases
        ]

        def parse_output(response: str) -> str:
            return response.strip()

        def build_prompt(input_text: str) -> str:
            return template.render(input_text)

        result = evaluate_prompt(
            self.client,
            test_cases,
            build_prompt,
            parse_output,
            version,
        )

        return EvalReport(
            prompt_version=version,
            test_set_size=len(test_cases),
            accuracy=result.accuracy,
            format_compliance=result.format_compliance,
            avg_latency_ms=result.avg_latency_ms,
            total_cost_usd=result.total_tokens * 0.00001,  # 假设 $10/1M tokens
            error_analysis=result.error_cases,
        )
```

### 在 report.md 中记录

```markdown
## Week 02：Prompt Engineering 进展

### Prompt 版本历史

| 版本 | 修改内容 | 准确率 | 格式合规率 | 日期 |
|------|---------|--------|-----------|------|
| v1 | 基础 Prompt，无 Few-shot | 75% | 82% | 2026-02-17 |
| v2 | 添加 3 个 Few-shot 示例 | 88% | 96% | 2026-02-17 |
| v3 | 对复杂工单启用 CoT | 92% | 95% | 2026-02-17 |

### 技术选型

- 分类任务：使用 v2 Prompt（平衡准确率和成本）
- 复杂工单：使用 v3 Prompt（CoT，准确率优先）
- 简单抽取：使用规则引擎 + LLM 验证

### 下一步

- Week 03：引入 RAG，让 TextAgent 能检索知识库
```

TextAgent 现在有了"大脑"——知道怎么说话（Prompt 模板），也知道怎么自检（评估框架）。下周我们会给它"记忆"——一个能检索的知识库。

<!--
================================================================================
【Git 本周要点】
================================================================================
-->

## Git 本周要点

本周必会命令：
- `git diff` — 查看未暂存的更改
- `git log --oneline --graph` — 图形化查看分支历史
- `git branch <name>` — 创建分支
- `git checkout <branch>` — 切换分支
- `git merge <branch>` — 合并分支

常见坑：
- **在 main 分支上直接改**：一旦出错很难回退。应该开一个 feature 分支，改完测试后再合并。
- **Prompt 变更不记录版本**：下周不知道"当时怎么写的"。每个 Prompt 版本都应该有对应的 commit。
- **测试集忘记提交**：评估无法复现。测试集是项目的一部分，应该进入版本控制。

分支命名建议：
- `feature/prompt-v2` — 新 Prompt 版本
- `feature/few-shot-examples` — Few-shot 示例
- `fix/classify-accuracy` — 修复准确率问题

<!--
================================================================================
【本周小结】
================================================================================
-->

## 本周小结（供下周参考）

这周你学的不是"怎么写 Prompt"，而是"怎么设计 Prompt"。

角色、任务、约束、格式四要素帮你把模糊的意图变成清晰的指令——不再出现"我让它分类，它给我写论文"的尴尬。Few-shot 示例让输出格式稳定下来——你的解析代码终于不用处理"财经类"和"这条新闻属于财经类别"了。Chain-of-Thought 让 LLM "慢下来"处理复杂推理——那些模棱两可的工单，现在能看到模型"是怎么想的"。评估框架让你能判断"变好还是变差"——不再靠"感觉"，而是有数据支撑。

这些技能构成了 Prompt Engineering 的核心。但更重要的是，你开始建立一种工程化思维：Prompt 不是"咒语"，是代码，需要设计、测试、迭代、版本管理。

下周，我们会进入 RAG 的世界——让 LLM 不只是"凭记忆回答"，而是能"查资料再回答"。你会发现，RAG 的很多设计决策（怎么检索、怎么排序、怎么组合检索结果和用户问题），都和你这周学的 Prompt 技巧紧密相关。

<!--
================================================================================
【Definition of Done（学生自测清单）】
================================================================================
-->

## Definition of Done

学完本章后，你应该能够回答以下问题：

- [ ] 我能用四要素框架分析一个 Prompt 的问题吗？
- [ ] 我能解释 Few-shot 为什么能稳定输出格式吗？
- [ ] 我知道什么时候该用 CoT，什么时候不该用吗？
- [ ] 我能搭建一个基础的 Prompt 评估流程吗？
- [ ] 我的 TextAgent 有 Prompt 模板库和评估框架了吗？

如果以上都打勾，恭喜你完成 Week 02！下周见。

<!--
================================================================================
【术语登记（供 TERMS.yml 参考）】
================================================================================

本章新术语：
1. Prompt 设计原则（Prompt Design Principles）
2. Few-shot Learning（少样本学习）
3. Chain-of-Thought（思维链）
4. Prompt 评估（Prompt Evaluation）

待合入 shared/glossary.yml

================================================================================
-->

<!--
================================================================================
【Context7 技术查证清单】
================================================================================

本章涉及的核心技术点（chapter-writer 动笔前必须查证）：

1. OpenAI Prompt Engineering Guide
   - 查询：OpenAI prompt engineering best practices 2025
   - 重点：官方推荐的四要素、Few-shot、CoT 写法

2. PyYAML 配置管理
   - 查询：python yaml configuration management best practices 2025
   - 重点：模板配置文件的加载和验证

3. Python dataclasses
   - 查询：python dataclasses best practices 2025
   - 重点：PromptTemplate 和 EvalResult 的设计

4. 测试框架
   - 查询：pytest parameterized tests best practices 2025
   - 重点：Prompt 评估的参数化测试

================================================================================
-->

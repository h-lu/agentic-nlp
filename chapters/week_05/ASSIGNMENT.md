# Week 05 作业：让 LLM 不只是回答问题 —— 从 RAG 到 Agent

上周你搭建了 RAG 系统，让 TextAgent 有了"长期记忆"。但你很快发现了一个问题：老板说"分析这 100 份客户反馈并给我报告"，TextAgent 只会泛泛而谈，不会真正"做事"。

这周你要让 TextAgent 从"被动回答"进化为"主动执行"——它能调用工具、能规划步骤、能完成复杂的多步骤任务。

---

## 作业背景

你所在公司的客服团队收到了大量客户反馈，老板要求：

1. **自动分析反馈**：统计高频问题、分析情感分布、提取关键主题
2. **生成分析报告**：不是泛泛而谈，而是基于真实数据的洞察
3. **可追溯**：每个结论都要能追溯到具体的反馈原文
4. **可扩展**：未来能轻松添加新的分析能力

你用 Week 03-04 的 RAG 系统试了试，发现它只能"回答问题"，不会"执行任务"。这周你要用 Agent 技术来解决这个问题。

---

## 核心任务（必做，60 分）

### Part 1：Function Calling 基础（20 分）

在实现 Agent 之前，先掌握 Function Calling 的基础——让 LLM 能调用外部工具。

#### 要求

**1.1 定义文本分析工具（8 分）**

```python
# agent/tools.py
from typing import Dict, List
import jieba
from collections import Counter

class TextAnalyzerTools:
    """文本分析工具集"""

    @staticmethod
    def analyze_sentiment(text: str) -> Dict:
        """
        分析文本的情感倾向

        Args:
            text: 要分析的文本

        Returns:
            {"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0}
        """
        # TODO: 实现情感分析
        # 提示：可以用简单的词匹配方法，或者调用真实模型
        pass

    @staticmethod
    def extract_keywords(text: str, top_k: int = 5) -> Dict:
        """
        提取文本中的关键词

        Args:
            text: 要提取关键词的文本
            top_k: 返回前 K 个关键词

        Returns:
            {"keywords": ["词1", "词2", ...], "counts": [count1, count2, ...]}
        """
        # TODO: 实现关键词提取
        # 提示：用 jieba 分词 + 词频统计
        pass

    @staticmethod
    def count_word_freq(text: str, top_k: int = 10) -> Dict:
        """
        统计文本中的高频词

        Args:
            text: 要统计的文本
            top_k: 返回前 K 个高频词

        Returns:
            {"top_words": [{"word": "词", "count": 次数}, ...]}
        """
        # TODO: 实现词频统计
        pass
```

**1.2 定义工具 Schema（8 分）**

```python
# agent/tools.py (续)

    @staticmethod
    def get_tool_schemas() -> List[Dict]:
        """
        获取工具的 Function Calling Schema

        Returns:
            工具 Schema 列表，符合 OpenAI Function Calling 格式
        """
        # TODO: 返回工具的 Schema 定义
        # 每个工具需要包含：
        # - name: 工具名称
        # - description: 工具描述（重要！LLM 根据描述决定何时调用）
        # - parameters: 参数定义（类型、描述、是否必需）
        pass
```

**工具描述要求**：
- `analyze_sentiment`：描述应说明"分析一段文本的情感倾向（正面/负面/中性）"
- `extract_keywords`：描述应说明"从文本中提取关键词，返回前 K 个"
- `count_word_freq`：描述应说明"统计文本中词频最高的前 K 个词"

**1.3 测试工具调用（4 分）**

```python
# experiments/test_tools.py

def test_tool_calling():
    """测试 Function Calling"""
    from openai import OpenAI
    import json

    client = OpenAI()

    # TODO: 完成工具调用循环
    # 1. 定义工具列表（调用 get_tool_schemas）
    # 2. 用户问题："帮我分析这段反馈的情感并提取关键词：产品质量很好，但物流太慢了。"
    # 3. 调用 LLM，让它决定是否调用工具
    # 4. 如果有工具调用，执行工具并返回结果
    # 5. 将结果反馈给 LLM，生成最终答案
    pass
```

**预期输出示例**：

```text
用户问题：帮我分析这段反馈的情感并提取关键词：产品质量很好，但物流太慢了。

LLM 决定调用工具：
- analyze_sentiment(text="产品质量很好，但物流太慢了。")
- extract_keywords(text="产品质量很好，但物流太慢了。", top_k=5)

工具返回：
- analyze_sentiment: {"sentiment": "neutral", "confidence": 0.6}
- extract_keywords: {"keywords": ["产品", "质量", "物流", "慢"], "counts": [2, 1, 1, 1]}

最终答案：这段反馈情感倾向为中性，包含正面评价（产品质量）和负面评价（物流慢）。关键词包括产品、质量、物流、慢等。
```

**提交内容**：
- `agent/tools.py`：工具实现
- `experiments/test_tools.py`：测试代码
- `report.md`：包含测试输出和分析

---

### Part 2：实现 ReAct Agent（20 分）

有了工具调用能力，现在来实现 ReAct 模式的 Agent——让它能够自主决定调用哪个工具、何时停止。

#### 要求

**2.1 实现 ReAct 循环（12 分）**

```python
# agent/react_agent.py
from typing import Dict, List, Optional
from openai import OpenAI
import json

class ReActAgent:
    """ReAct 模式的 Agent"""

    def __init__(
        self,
        tools: Dict,
        llm_client: Optional[OpenAI] = None,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Args:
            tools: 工具字典，格式为 {"tool_name": tool_function}
            llm_client: LLM 客户端
            max_iterations: 最大迭代次数
            verbose: 是否打印详细日志
        """
        # TODO: 初始化
        pass

    def run(self, task: str) -> Dict:
        """
        运行 ReAct 循环

        Args:
            task: 用户任务

        Returns:
            {
                "final_answer": "最终答案",
                "history": [执行历史],
                "iterations": 迭代次数
            }
        """
        # TODO: 实现 ReAct 循环
        # 1. 构造 System Prompt（强调 Thought-Action-Observation 格式）
        # 2. 循环调用 LLM
        # 3. 解析工具调用，执行工具
        # 4. 将结果反馈给 LLM
        # 5. 直到 LLM 给出 Final Answer 或达到最大迭代次数
        # 6. 记录每一步的执行历史
        pass
```

**System Prompt 要求**：

```text
你是一个智能文本分析助手，能够使用工具完成分析任务。

请按以下格式思考和行动：

Thought: [你的思考过程，解释为什么采取这个行动]
Action: [工具名称]
Action Input: [工具参数，JSON 格式]

你会收到工具的执行结果（Observation），然后继续思考下一步行动。

当你完成所有步骤后，用以下格式给出最终答案：

Final Answer: [最终答案]

约束：
1. 每次只能调用一个工具
2. Action Input 必须是有效的 JSON 格式
3. Thought 必须清晰说明你为什么要采取这个行动
4. 确保任务完全完成后再给出 Final Answer
```

**2.2 测试 ReAct Agent（8 分）**

```python
# experiments/test_react_agent.py

def test_react_agent():
    """测试 ReAct Agent"""
    from agent.tools import TextAnalyzerTools
    from agent.react_agent import ReActAgent

    # 初始化工具
    tools = {
        "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
        "extract_keywords": TextAnalyzerTools.extract_keywords,
        "count_word_freq": TextAnalyzerTools.count_word_freq,
    }

    # 创建 Agent
    agent = ReActAgent(tools, verbose=True)

    # 测试任务
    task = """
    分析以下客户反馈并给出总结：
    1. "产品质量很好，但物流太慢了，希望改进。"
    2. "客服态度很差，问题一直没解决。"
    3. "价格合理，物流也快，推荐购买。"
    4. "用了两周就坏了，质量堪忧。"
    """

    result = agent.run(task)
    print(f"最终答案：{result['final_answer']}")
    print(f"迭代次数：{result['iterations']}")
    print(f"执行历史：{result['history']}")
```

**预期输出示例**：

```text
[Iteration 1]
Thought: 用户要求分析 4 条客户反馈并给出总结。首先我需要逐条分析每条反馈的情感倾向。
Action: analyze_sentiment
Action Input: {"text": "产品质量很好，但物流太慢了，希望改进。"}
Result: {"sentiment": "neutral", "confidence": 0.6}

[Iteration 2]
Thought: 继续分析第二条反馈的情感。
Action: analyze_sentiment
...

[Iteration 7]
Thought: 我已经分析了所有反馈的情感，现在需要统计高频词来了解主要关注点。
Action: count_word_freq
...

[Final Answer]
最终答案：分析完成。4 条反馈中，正面 2 条、负面 2 条。主要关注点为：质量（3 次）、物流（3 次）、客服（1 次）。建议重点改进物流速度和质量稳定性。
```

**提交内容**：
- `agent/react_agent.py`：ReAct Agent 实现
- `experiments/test_react_agent.py`：测试代码
- `report.md`：包含完整的执行历史和分析

---

### Part 3：任务分解与规划（20 分）

ReAct 模式让 Agent 能"边想边做"，但有时会走弯路（比如先做情感分析，再决定加载反馈）。任务分解让 Agent 先规划、再执行。

#### 要求

**3.1 实现任务规划器（10 分）**

```python
# agent/planning_agent.py
from .react_agent import ReActAgent

class PlanningAgent(ReActAgent):
    """带规划能力的 Agent"""

    def run(self, task: str, show_plan: bool = True) -> Dict:
        """
        运行带规划的 Agent

        Args:
            task: 用户任务
            show_plan: 是否显示计划

        Returns:
            执行结果
        """
        # TODO: 实现
        # 1. 先调用 LLM 生成执行计划
        # 2. 如果 show_plan=True，打印计划
        # 3. 然后调用父类的 run 方法执行
        pass

    def _create_plan(self, task: str) -> str:
        """
        创建任务计划

        Args:
            task: 用户任务

        Returns:
            计划文本
        """
        # TODO: 实现
        # 使用 Few-shot 让 LLM 学会规划
        #
        # 示例格式：
        # 任务："分析客户反馈并生成报告"
        #
        # Plan:
        # 1. 加载反馈数据
        #    - 工具: load_feedbacks
        #    - 依赖: 无
        #
        # 2. 统计高频词
        #    - 工具: count_word_freq
        #    - 依赖: 步骤 1
        #
        # 3. 分析情感分布
        #    - 工具: analyze_sentiment_batch
        #    - 依赖: 步骤 1
        #
        # 4. 生成报告
        #    - 工具: generate_report
        #    - 依赖: 步骤 2, 3
        pass
```

**3.2 对比有规划和无规划的效果（10 分）**

```python
# experiments/test_planning.py

def compare_planning():
    """对比有规划和无规划的 Agent"""
    from agent.tools import TextAnalyzerTools
    from agent.react_agent import ReActAgent
    from agent.planning_agent import PlanningAgent

    tools = {
        "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
        "extract_keywords": TextAnalyzerTools.extract_keywords,
        "count_word_freq": TextAnalyzerTools.count_word_freq,
    }

    # 复杂任务
    complex_task = """
    分析以下 5 条客户反馈：
    1. "产品质量很好，但物流太慢了。"
    2. "客服态度很差，问题一直没解决。"
    3. "价格合理，物流也快，推荐购买。"
    4. "用了两周就坏了，质量堪忧。"
    5. "包装破损，但产品本身没问题。"

    请：
    1. 统计所有反馈的高频词（Top 5）
    2. 分析每条反馈的情感
    3. 总结主要问题和优点
    4. 给出改进建议
    """

    # 测试无规划 Agent
    react_agent = ReActAgent(tools, verbose=False)
    react_result = react_agent.run(complex_task)

    # 测试有规划 Agent
    planning_agent = PlanningAgent(tools, verbose=False)
    planning_result = planning_agent.run(complex_task, show_plan=True)

    # 对比
    print("=== 无规划 Agent ===")
    print(f"迭代次数：{react_result['iterations']}")
    print(f"最终答案：{react_result['final_answer']}")

    print("\n=== 有规划 Agent ===")
    print(f"迭代次数：{planning_result['iterations']}")
    print(f"最终答案：{planning_result['final_answer']}")
```

**输出分析表格**：

```markdown
### 规划效果对比

| 维度 | 无规划 Agent | 有规划 Agent | 差异 |
|------|------------|------------|------|
| 迭代次数 | ? | ? | ? |
| 执行时间（秒） | ? | ? | ? |
| 工具调用顺序 | ? | ? | ? |
| 是否有重复调用 | ? | ? | ? |
| 最终答案质量 | ? | ? | ? |

**分析**：
- 有规划 Agent 是否减少了迭代次数？
- 有规划 Agent 是否避免了无效的工具调用？
- 哪种方式的最终答案更好？
```

**提交内容**：
- `agent/planning_agent.py`：规划 Agent 实现
- `experiments/test_planning.py`：对比测试
- `report.md`：包含对比表格和分析

---

## 进阶任务（选做，25 分）

### 任务 4：添加更多分析工具（15 分）

基础的三个工具不够用。添加更多实用的文本分析工具。

#### 要求

**4.1 实现新工具（10 分）**

从以下工具中选择至少 2 个实现：

```python
# agent/advanced_tools.py

class AdvancedTextTools:
    """高级文本分析工具"""

    @staticmethod
    def extract_entities(text: str) -> Dict:
        """
        提取文本中的实体（人名、地名、机构名）

        Returns:
            {"persons": [...], "locations": [...], "organizations": [...]}
        """
        # TODO: 实现实体抽取
        # 提示：可以用简单的规则，或者调用 NLP 库
        pass

    @staticmethod
    def classify_text(text: str, categories: List[str]) -> Dict:
        """
        将文本分类到给定类别

        Args:
            text: 要分类的文本
            categories: 候选类别列表

        Returns:
            {"category": "最可能的类别", "confidence": 置信度}
        """
        # TODO: 实现文本分类
        pass

    @staticmethod
    def detect_duplicates(texts: List[str], threshold: float = 0.8) -> Dict:
        """
        检测重复或高度相似的文本

        Args:
            texts: 文本列表
            threshold: 相似度阈值

        Returns:
            {"duplicates": [(i, j, similarity), ...]}
        """
        # TODO: 实现重复检测
        # 提示：可以用编辑距离或余弦相似度
        pass

    @staticmethod
    def summarize_long_text(text: str, max_length: int = 200) -> Dict:
        """
        摘要长文本

        Args:
            text: 长文本
            max_length: 摘要最大长度

        Returns:
            {"summary": "摘要内容"}
        """
        # TODO: 实现文本摘要
        pass
```

**4.2 更新工具 Schema（5 分）**

```python
# agent/advanced_tools.py (续)

    @staticmethod
    def get_tool_schemas() -> List[Dict]:
        """获取新工具的 Schema"""
        # TODO: 返回新工具的 Schema
        pass
```

**测试新工具**：

```python
# experiments/test_advanced_tools.py

def test_advanced_tools():
    """测试高级工具"""
    # TODO: 测试你实现的新工具
    # 展示它们在分析客户反馈时的价值
    pass
```

**提交内容**：
- `agent/advanced_tools.py`：新工具实现
- `experiments/test_advanced_tools.py`：测试代码
- `report.md`：包含使用示例和效果分析

---

### 任务 5：工具调用结果缓存（10 分）

Agent 可能会重复调用相同工具（如多次分析同一条反馈）。添加缓存机制避免重复计算。

#### 要求

**5.1 实现 LRU 缓存（6 分）**

```python
# agent/cached_agent.py
from functools import lru_cache
from .react_agent import ReActAgent
import hashlib
import json

class CachedReActAgent(ReActAgent):
    """带缓存的 ReAct Agent"""

    def __init__(self, *args, cache_size: int = 128, **kwargs):
        """
        Args:
            cache_size: 缓存大小
        """
        # TODO: 初始化
        # 使用 lru_cache 装饰器或手动实现
        pass

    def _execute_tool_cached(self, tool_name: str, tool_args: Dict) -> Dict:
        """
        带缓存的工具执行

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具执行结果
        """
        # TODO: 实现
        # 1. 生成缓存键（tool_name + tool_args 的 hash）
        # 2. 检查缓存
        # 3. 如果命中，直接返回
        # 4. 如果未命中，执行工具并缓存结果
        pass
```

**5.2 对比缓存效果（4 分）**

```python
# experiments/test_cache.py

def compare_cache_effectiveness():
    """对比缓存的效果"""
    # TODO: 设计测试用例
    # 1. 构造一个会触发重复调用的任务
    # 2. 对比有无缓存的性能
    # 3. 输出命中率统计
    pass
```

**输出表格**：

```markdown
### 缓存效果对比

| 指标 | 无缓存 | 有缓存 | 提升 |
|------|-------|-------|------|
| 工具调用次数 | ? | ? | ? |
| 执行时间（秒） | ? | ? | ? |
| 缓存命中率 | N/A | ? | N/A |

**结论**：
- 缓存在什么场景下最有效？
- 缓存大小设置为多少合适？
```

**提交内容**：
- `agent/cached_agent.py`：缓存 Agent 实现
- `experiments/test_cache.py`：对比测试
- `report.md`：包含效果分析

---

## 挑战任务（加分，15 分）

### 任务 6：生产级 Agent 系统（15 分）

挑战任务要求你设计一个接近生产级的 Agent 系统，包含日志、监控、异常处理等工程实践。

#### 要求

**6.1 完整的日志系统（5 分）**

```python
# agent/production_agent.py
import logging
from datetime import datetime
from typing import Dict, Any
import json

class ProductionAgent(ReActAgent):
    """生产级 Agent"""

    def __init__(self, *args, log_file: str = "agent_trace.log", **kwargs):
        """
        Args:
            log_file: 日志文件路径
        """
        # TODO: 初始化日志系统
        pass

    def _log_step(self, step_type: str, data: Dict[str, Any]):
        """
        记录执行步骤

        Args:
            step_type: 步骤类型（thought/action/observation/final_answer）
            data: 步骤数据
        """
        # TODO: 实现日志记录
        # 格式：timestamp | step_type | data
        pass

    def get_trace_summary(self) -> Dict:
        """
        获取执行追踪摘要

        Returns:
            {
                "total_steps": 总步骤数,
                "tool_calls": 工具调用次数,
                "errors": 错误次数,
                "duration": 执行时长
            }
        """
        # TODO: 实现
        pass
```

**6.2 异常处理和重试（5 分）**

```python
# agent/production_agent.py (续)

    def _execute_tool_with_retry(
        self,
        tool_name: str,
        tool_args: Dict,
        max_retries: int = 3
    ) -> Dict:
        """
        带重试的工具执行

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            max_retries: 最大重试次数

        Returns:
            工具执行结果

        Raises:
            Exception: 重试失败后抛出异常
        """
        # TODO: 实现重试逻辑
        # 1. 尝试执行工具
        # 2. 如果失败，记录错误并重试
        # 3. 重试失败后抛出异常
        pass

    def run_with_fallback(self, task: str) -> Dict:
        """
        带降级策略的运行

        如果某个工具持续失败，Agent 应该能继续完成任务
        """
        # TODO: 实现降级策略
        pass
```

**6.3 成本和性能监控（5 分）**

```python
# agent/production_agent.py (续)

class AgentMetrics:
    """Agent 性能指标"""

    def __init__(self):
        # TODO: 初始化指标
        pass

    def record_tool_call(self, tool_name: str, duration: float, success: bool):
        """记录工具调用"""
        pass

    def record_llm_call(self, model: str, tokens: int, cost: float):
        """记录 LLM 调用"""
        pass

    def get_summary(self) -> Dict:
        """获取指标摘要"""
        # 返回：
        # - 总成本
        # - 平均延迟
        # - 工具调用成功率
        # - LLM 调用次数
        pass
```

**测试生产级 Agent**：

```python
# experiments/test_production_agent.py

def test_production_agent():
    """测试生产级 Agent"""
    # TODO: 测试各种异常场景
    # 1. 工具调用失败
    # 2. LLM 超时
    # 3. 无效参数
    # 4. 验证日志、重试、降级是否正常工作
    pass
```

**输出示例**：

```markdown
### 生产级 Agent 测试报告

**日志追踪示例**：
```
2026-02-17 10:23:15 | THOUGHT | 用户要求分析反馈，首先统计高频词
2026-02-17 10:23:16 | ACTION | count_word_freq({"text": "...", "top_k": 10})
2026-02-17 10:23:16 | OBSERVATION | {"top_words": [...]}
2026-02-17 10:23:17 | ACTION | analyze_sentiment({"text": "..."})
2026-02-17 10:23:18 | ERROR | analyze_sentiment failed: Connection timeout
2026-02-17 10:23:19 | RETRY | analyze_sentiment (attempt 2/3)
...
```

**性能指标**：
| 指标 | 值 |
|------|---|
| 总步骤数 | 12 |
| 工具调用次数 | 8 |
| 错误次数 | 1 |
| 重试次数 | 1 |
| 执行时长 | 5.2 秒 |
| LLM 调用成本 | $0.002 |

**异常处理验证**：
- [ ] 工具调用失败后自动重试
- [ ] 重试失败后记录日志并继续
- [ ] 所有步骤都有日志追踪
- [ ] 成本正确计算
```

**提交内容**：
- `agent/production_agent.py`：生产级 Agent 实现
- `experiments/test_production_agent.py`：测试代码
- `report.md`：包含完整的测试报告和日志示例

---

## AI 协作练习（可选）

Week 05 处于"协作期"，你可以用 AI 辅助 Agent 开发。下面这段 AI 生成的代码有几个问题，请审查并修复。

### 待审查代码

```python
# AI 生成的 ReAct Agent 实现（故意包含问题）
from openai import OpenAI
import json

class SimpleAgent:
    def __init__(self, tools):
        self.tools = tools

    def run(self, task):
        messages = [{"role": "user", "content": task}]

        while True:
            response = OpenAI().chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                for call in msg.tool_calls:
                    result = self.tools[call.function.name](**call.function.arguments)
                    # 结果反馈给 LLM
                    messages.append({"role": "assistant", "content": msg.content})
                    messages.append({"role": "tool", "content": str(result)})
            else:
                return msg.content
```

### 审查清单

请对照以下清单审查代码：

```markdown
## Agent 代码审查报告

### 1. 无限循环风险
- [ ] while True 没有退出条件，会发生什么？
- [ ] LLM 持续调用工具不停止怎么办？

你的分析和修复方案：
...

### 2. 错误处理
- [ ] 工具调用失败会怎样？
- [ ] 没有 try-except，会导致什么问题？

你的分析和修复方案：
...

### 3. 日志和追踪
- [ ] 有没有记录执行历史？
- [ ] 调试时如何知道 Agent 做了什么？

你的分析和修复方案：
...

### 4. System Prompt
- [ ] 有没有 System Prompt？
- [ ] LLM 知道要用 Thought-Action-Observation 格式吗？

你的分析和修复方案：
...

### 5. 工具参数验证
- [ ] LLM 传的参数一定正确吗？
- [ ] 工具函数需要参数验证吗？

你的分析和修复方案：
...

### 6. 成本和性能
- [ ] 每次循环都创建新的 OpenAI() 客户端，有什么问题？
- [ ] 没有记录 LLM 调用次数和成本

你的分析和修复方案：
...
```

### 你的修订版

基于审查，写出你的修订版本（只需修改关键部分）：

```python
# 我的修订版
class FixedSimpleAgent:
    """修复后的 Agent"""

    def __init__(self, tools, llm_client=None, max_iterations=10):
        # TODO: 你的初始化
        pass

    def run(self, task):
        # TODO: 你的实现
        # 1. 添加 System Prompt
        # 2. 添加退出条件
        # 3. 添加错误处理
        # 4. 添加日志记录
        # 5. 复用 LLM 客户端
        pass
```

### 审查总结

```markdown
## 审查总结

发现的问题：
1. ...
2. ...
3. ...

修复后的改进：
1. ...
2. ...
3. ...

从这次审查中学到的：
- Agent 开发中最重要的工程实践是什么？
- 哪些问题容易被忽略但很关键？
```

**重要**：AI 协作练习不影响基础任务的评分，但需要展示你的审查过程和工程思维。

---

## 提交清单

在提交作业前，请确认以下内容：

### 文件结构

```
week05_作业_你的姓名/
├── agent/
│   ├── tools.py                # 基础工具（Part 1）
│   ├── react_agent.py          # ReAct Agent（Part 2）
│   ├── planning_agent.py       # 规划 Agent（Part 3）
│   ├── advanced_tools.py       # 高级工具（任务 4）
│   ├── cached_agent.py         # 缓存 Agent（任务 5）
│   └── production_agent.py     # 生产级 Agent（任务 6）
├── experiments/
│   ├── test_tools.py           # 工具测试
│   ├── test_react_agent.py     # ReAct 测试
│   ├── test_planning.py        # 规划测试
│   ├── test_advanced_tools.py  # 高级工具测试
│   ├── test_cache.py           # 缓存测试
│   └── test_production_agent.py # 生产级测试
├── data/
│   └── sample_feedback.txt     # 示例反馈数据
├── report.md                   # 完整实验报告
└── README.md                   # 简要说明
```

### 质量检查

- [ ] 所有代码都能独立运行
- [ ] API Key 没有硬编码（使用环境变量）
- [ ] Function Calling 有完整的测试输出
- [ ] ReAct Agent 有详细的执行历史
- [ ] 规划对比有实验数据支撑
- [ ] report.md 包含所有实验结果
- [ ] 有运行输出或截图证明代码能工作
- [ ] （可选）AI 协作练习包含审查报告

---

## 常见问题

**Q：工具描述要写多详细？**

A：工具描述是 LLM 决策的唯一依据，建议：
- 明确工具的功能（"做什么"）
- 说明适用场景（"什么时候用"）
- 给出示例（"输入输出是什么"）
- 说明约束（"不能做什么"）

**Q：ReAct 循环最多迭代多少次合适？**

A：没有标准答案，取决于任务复杂度：
- 简单任务：3-5 次
- 中等任务：5-10 次
- 复杂任务：10-20 次
- 超过 20 次可能需要优化规划

**Q：如何避免 Agent 死循环？**

A：几种策略：
1. 设置 `max_iterations` 上限
2. 在 System Prompt 中强调"完成即停止"
3. 检测重复的工具调用并中断
4. 添加"进展检测"，如果 N 步没有新进展则停止

**Q：规划 Agent 一定能减少迭代次数吗？**

A：不一定。规划 Agent 的优势是：
- 避免无效的工具调用
- 让执行路径更清晰
- 便于人类理解和调试

但如果任务很简单，规划反而会增加额外开销。建议对复杂任务使用规划。

**Q：缓存什么情况下有效？**

A：缓存在以下场景最有效：
- 相同文本被多次分析（如批量情感分析）
- Agent 会重复调用相同工具
- 工具执行成本高（如调用外部 API）

**Q：生产级 Agent 最重要的是什么？**

A：根据老潘的经验：
1. **可观测性**：每一步都能追踪，出问题能定位
2. **容错性**：工具失败不崩溃，有降级方案
3. **成本可控**：知道每次调用花多少钱，有预算限制
4. **安全性**：工具调用有权限控制，不能随便执行

---

## 评分重点

本次作业的评分重点：

1. **理解 Agent 原理**：不只是调 API，而是理解 ReAct 模式的思想
2. **工具定义能力**：能设计清晰、有效的工具 Schema
3. **工程化思维**：日志、缓存、异常处理，这些在生产环境必不可少
4. **实验驱动**：用数据对比有规划和无规划的效果

记住老潘的话："在公司里，Agent 的每一步都必须可追踪——日志、审计、异常处理，一个都不能少。"

---

## 提示

如果你遇到困难，可以参考 `starter_code/solution.py`。但记住：
1. 不要直接复制粘贴
2. 理解每一行代码的作用
3. 自己动手修改和调试

真正的学习发生在你调试代码、理解错误、解决问题的过程中。

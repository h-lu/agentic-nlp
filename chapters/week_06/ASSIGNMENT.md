# Week 06 作业：让智能体团队协作 —— 多智能体系统与 Agentic RAG

Week 05 你让 TextAgent 从"被动回答"进化为"主动执行"——它能调用工具、能规划步骤。但上周小北发现了一个问题：当任务复杂时，单个 Agent 会"超载"，它会走回头路、会坚持错误决策、会因为认知负荷过高而做出奇怪的事情。

这周你要让 TextAgent 从"单兵作战"进化为"团队协作"——多个 Agent 各司其职，一个负责规划，一个负责执行，一个负责审核。

---

## 作业背景

你所在公司的智能客服系统上线后，老板提出了新要求：

1. **可解释性**：每个结论都要能追溯到"谁决策的、为什么决策"
2. **专业化分工**：不同任务由不同的专业 Agent 处理
3. **动态检索策略**：根据查询类型自动选择最佳检索方式
4. **人工审核**：高风险决策需要人工确认

你用 Week 05 的单 Agent 系统试了试，发现它既做规划又做执行，既做分析又做审核，最后日志混乱、决策难以追溯。这周你要用多智能体系统来解决这些问题。

---

## 核心任务（必做，60 分）

### Part 1：实现规划者-执行者-审核者架构（25 分）

多智能体系统的核心是角色分工。首先实现最经典的三角色架构。

#### 要求

**1.1 实现规划者 Agent（8 分）**

```python
# multiagent/planner.py
from typing import Dict
from openai import OpenAI
import json

class PlannerAgent:
    """规划者 Agent：理解任务，制定计划"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def create_plan(self, task: str, context: Dict = None) -> Dict:
        """
        创建任务计划

        Args:
            task: 用户任务描述
            context: 上下文信息（可选）

        Returns:
            计划字典，包含：
            {
                "task_understanding": "对任务的理解",
                "subtasks": [
                    {"step": 1, "action": "做什么", "tool": "工具名", "params": {...}},
                    ...
                ],
                "expected_output": "期望的最终输出"
            }
        """
        # TODO: 实现
        # 提示：使用 Few-shot 让 LLM 学会制定计划
        pass

    def revise_plan(self, original_plan: Dict, feedback: str) -> Dict:
        """
        根据反馈修订计划

        Args:
            original_plan: 原始计划
            feedback: 反馈意见

        Returns:
            修订后的计划，应包含：
            - 保留原计划的 "task_understanding" 和 "subtasks" 结构
            - 添加 "revision_note" 字段，记录修订原因和内容
            - 可以调整 subtasks 的顺序、添加/删除步骤、修改工具或参数

        示例修订后的计划：
        {
            "task_understanding": "...",
            "subtasks": [...],  # 修改后的步骤
            "revision_note": "根据反馈增加了情感分析步骤"
        }
        """
        # TODO: 实现
        pass
```

**规划格式示例**：

```json
{
  "task_understanding": "用户要求分析客户反馈并总结主要问题",
  "subtasks": [
    {
      "step": 1,
      "action": "加载反馈数据",
      "tool": "load_feedbacks",
      "params": {"source": "database"}
    },
    {
      "step": 2,
      "action": "统计高频词",
      "tool": "count_word_freq",
      "params": {"text": "${feedbacks}", "top_k": 10}
    },
    {
      "step": 3,
      "action": "分析情感分布",
      "tool": "analyze_sentiment_batch",
      "params": {"texts": "${feedbacks}"}
    },
    {
      "step": 4,
      "action": "生成总结报告",
      "tool": "generate_report",
      "params": {"word_freq": "${step2}", "sentiments": "${step3}"}
    }
  ],
  "expected_output": "包含高频问题统计和情感分布的分析报告"
}
```

**1.2 实现执行者 Agent（8 分）**

```python
# multiagent/executor.py
from typing import Dict, Callable

class ExecutorAgent:
    """执行者 Agent：按计划执行工具调用"""

    def __init__(self, tools: Dict[str, Callable]):
        """
        Args:
            tools: 工具字典，格式为 {"tool_name": tool_function}
        """
        # TODO: 初始化
        pass

    def execute_plan(self, plan: Dict) -> Dict:
        """
        执行计划

        Args:
            plan: 规划者生成的计划

        Returns:
            {
                "plan": plan,
                "results": [
                    {"step": 1, "action": "...", "result": {...}},
                    ...
                ],
                "status": "completed/failed",
                "errors": [...]
            }
        """
        # TODO: 实现
        # 1. 按顺序执行子任务
        # 2. 处理变量引用（如 "${feedbacks}"）
        # 3. 记录每步的执行结果
        # 4. 处理工具调用失败的情况
        pass

    def _resolve_params(self, params: Dict, context: Dict) -> Dict:
        """
        解析参数中的变量引用

        例如：{"text": "${feedbacks}"} 中的 "${feedbacks}" 需要替换为实际数据
        """
        # TODO: 实现（可选）
        pass
```

**1.3 实现审核者 Agent（9 分）**

```python
# multiagent/reviewer.py
from typing import Dict
from openai import OpenAI
import json

class ReviewerAgent:
    """审核者 Agent：检查执行结果"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def review_result(self, plan: Dict, execution_result: Dict) -> Dict:
        """
        审核执行结果

        Args:
            plan: 原始计划
            execution_result: 执行者返回的结果

        Returns:
            {
                "status": "approved/needs_revision",
                "issues": ["问题1", "问题2"],
                "final_answer": "最终答案（如果 approved）",
                "revision_suggestions": ["修改建议1", "修改建议2"]
            }
        """
        # TODO: 实现
        # 审核点：
        # 1. 所有步骤是否完成
        # 2. 结果是否完整
        # 3. 逻辑是否一致
        # 4. 是否有明显的错误
        pass
```

**测试三 Agent 协作**：

```python
# experiments/test_three_agents.py

def test_planner_executor_reviewer():
    """测试三 Agent 协作"""
    from multiagent.planner import PlannerAgent
    from multiagent.executor import ExecutorAgent
    from multiagent.reviewer import ReviewerAgent
    from agent.tools import TextAnalyzerTools  # Week 05 的工具

    # 初始化
    llm = OpenAI()
    planner = PlannerAgent(llm)
    executor = ExecutorAgent({
        "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
        "extract_keywords": TextAnalyzerTools.extract_keywords,
        "count_word_freq": TextAnalyzerTools.count_word_freq,
    })
    reviewer = ReviewerAgent(llm)

    # 任务
    task = """
    分析以下客户反馈并给出总结：
    1. "产品质量很好，但物流太慢了。"
    2. "客服态度很差，问题一直没解决。"
    3. "价格合理，物流也快，推荐购买。"
    """

    # 执行
    print("=== 规划阶段 ===")
    plan = planner.create_plan(task)
    print(f"计划：{json.dumps(plan, ensure_ascii=False, indent=2)}")

    print("\n=== 执行阶段 ===")
    execution_result = executor.execute_plan(plan)
    print(f"结果：{json.dumps(execution_result, ensure_ascii=False, indent=2)}")

    print("\n=== 审核阶段 ===")
    review = reviewer.review_result(plan, execution_result)
    print(f"审核：{json.dumps(review, ensure_ascii=False, indent=2)}")

    # 如果需要修订
    if review["status"] == "needs_revision":
        print("\n=== 修订阶段 ===")
        revised_plan = planner.revise_plan(plan, review["revision_suggestions"])
        execution_result = executor.execute_plan(revised_plan)
        review = reviewer.review_result(revised_plan, execution_result)

    print(f"\n最终答案：{review.get('final_answer', '任务完成')}")
```

**预期输出示例**：

```text
=== 规划阶段 ===
计划：{
  "task_understanding": "分析3条客户反馈，找出主要问题和优点",
  "subtasks": [
    {"step": 1, "action": "分析每条反馈的情感", "tool": "analyze_sentiment", ...},
    {"step": 2, "action": "统计高频词", "tool": "count_word_freq", ...},
    {"step": 3, "action": "生成总结", "tool": "generate_summary", ...}
  ],
  ...
}

=== 执行阶段 ===
结果：{
  "results": [
    {"step": 1, "result": {"sentiment": "neutral", ...}},
    {"step": 2, "result": {"top_words": [{"word": "物流", "count": 2}, ...]}},
    ...
  ],
  "status": "completed"
}

=== 审核阶段 ===
审核：{
  "status": "approved",
  "final_answer": "分析完成。3条反馈中，正面评价2条（质量、价格），负面评价2条（物流、客服）。主要问题为物流速度和客服态度。"
}
```

**提交内容**：
- `multiagent/planner.py`：规划者实现
- `multiagent/executor.py`：执行者实现
- `multiagent/reviewer.py`：审核者实现
- `experiments/test_three_agents.py`：测试代码
- `report.md`：包含测试输出和分析

---

### Part 2：实现检索 Agent（Agentic RAG）（20 分）

传统 RAG 是"被动检索"——用户问问题就检索一次。Agentic RAG 是"主动检索"——Agent 自主决定检索策略。

#### 要求

**2.1 实现检索 Agent（12 分）**

```python
# multiagent/retriever.py
from typing import Dict, Optional
from openai import OpenAI
import json

class RetrieverAgent:
    """检索 Agent：自主决定检索策略"""

    def __init__(self, llm_client: OpenAI, vector_store, keyword_store=None):
        """
        Args:
            llm_client: LLM 客户端
            vector_store: 向量存储（Week 03）
            keyword_store: 关键词索引（Week 04，可选）
        """
        # TODO: 初始化
        pass

    def retrieve(self, query: str, top_k: int = 5) -> Dict:
        """
        自主检索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            {
                "query": query,
                "results": [...],
                "strategy": {
                    "method": "vector/hybrid/multi_round",
                    "reasoning": "选择该策略的原因",
                    "top_k": top_k
                },
                "assessment": {
                    "sufficient": True/False,
                    "confidence": 0.8
                }
            }
        """
        # TODO: 实现
        # 1. 让 Agent 决定检索策略
        # 2. 按策略执行检索
        # 3. 评估检索结果
        # 4. 如果结果不够好，重新检索
        pass

    def _decide_strategy(self, query: str) -> Dict:
        """
        决定检索策略

        Returns:
            {
                "method": "vector/hybrid/multi_round",
                "reasoning": "选择该策略的原因",
                "top_k": 5,
                "improved_query": "改进后的查询（可选）"
            }

        说明：
        - method: 检索方法（vector=向量检索, hybrid=混合检索, multi_round=多轮检索）
        - reasoning: 为什么选择这个策略（帮助解释决策过程）
        - top_k: 返回多少个结果
        - improved_query: 当原始查询太短或太模糊时，可以返回一个改进版本
          例如：查询"政策" → improved_query="政策 规定 制度 办法"
          这个字段会在第一次检索结果不足时用于重新检索
        """
        # TODO: 实现
        # 提示：考虑查询的特征
        # - 精确匹配（如订单号）-> 关键词检索
        # - 语义相似（如"类似产品"）-> 向量检索
        # - 复杂查询 -> 混合检索
        pass

    def _assess_results(self, query: str, results: Dict) -> Dict:
        """
        评估检索结果是否足够

        Returns:
            {"sufficient": True/False, "confidence": 0.8, "missing_aspects": [...]}
        """
        # TODO: 实现
        # 提示：让 LLM 评估结果是否覆盖了查询的需求
        pass
```

**2.2 集成检索 Agent 到多 Agent 系统（8 分）**

```python
# multiagent/workflow.py
from .planner import PlannerAgent
from .executor import ExecutorAgent
from .reviewer import ReviewerAgent
from .retriever import RetrieverAgent

class MultiAgentWorkflow:
    """集成了检索的多 Agent 工作流"""

    def __init__(
        self,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        reviewer: ReviewerAgent,
        retriever: RetrieverAgent
    ):
        # TODO: 初始化
        pass

    def run(self, task: str, context: Dict = None) -> Dict:
        """
        运行完整工作流

        流程：
        1. Planner 制定计划
        2. Executor 执行计划（遇到检索任务时调用 Retriever）
        3. Reviewer 审核结果
        """
        # TODO: 实现
        pass
```

**测试 Agentic RAG**：

```python
# experiments/test_agentic_rag.py

def test_agentic_rag():
    """测试 Agentic RAG"""
    from multiagent.workflow import MultiAgentWorkflow
    from textagent.rag.vector_store import VectorStore  # Week 03

    # 初始化
    vector_store = VectorStore()
    # ... 初始化其他组件

    workflow = MultiAgentWorkflow(planner, executor, reviewer, retriever)

    # 测试不同类型的查询
    queries = [
        "订单 #12345 的状态是什么？",  # 精确匹配
        "类似产品的推荐",  # 语义相似
        "产品质量问题和物流投诉的统计"  # 复杂查询
    ]

    for query in queries:
        print(f"\n查询：{query}")
        result = workflow.run(query)

        # 输出检索策略
        if "retrieval" in result:
            strategy = result["retrieval"]["strategy"]
            print(f"检索策略：{strategy['method']}")
            print(f"选择原因：{strategy['reasoning']}")
            print(f"结果评估：{result['retrieval']['assessment']}")
```

**预期输出示例**：

```text
查询：订单 #12345 的状态是什么？
检索策略：keyword
选择原因：查询包含精确的订单号，使用关键词检索更准确
结果评估：{"sufficient": true, "confidence": 0.95}

查询：类似产品的推荐
检索策略：vector
选择原因：查询是语义相似性搜索，向量检索能找到语义相近的产品
结果评估：{"sufficient": true, "confidence": 0.85}

查询：产品质量问题和物流投诉的统计
检索策略：hybrid
选择原因：查询需要综合多个维度的信息，混合检索能确保覆盖面
结果评估：{"sufficient": true, "confidence": 0.8}
```

**提交内容**：
- `multiagent/retriever.py`：检索 Agent 实现
- `multiagent/workflow.py`：工作流实现
- `experiments/test_agentic_rag.py`：测试代码
- `report.md`：包含不同查询类型的策略选择分析

---

### Part 3：Human-in-the-Loop 机制（15 分）

小北上周发现，规划者有时会制定明显错误的计划，但执行者还是照做了，最后浪费很多时间。这需要在关键决策点引入人工审核。

#### 要求

**3.1 实现人工审核机制（10 分）**

```python
# multiagent/human_in_loop.py
from typing import Dict, List, Callable

class HumanInTheLoopWorkflow:
    """带人工审核的多 Agent 工作流"""

    def __init__(
        self,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        reviewer: ReviewerAgent,
        retriever: RetrieverAgent = None
    ):
        # TODO: 初始化
        pass

    def run(
        self,
        task: str,
        review_points: List[str] = None
    ) -> Dict:
        """
        运行带人工审核的工作流

        Args:
            task: 用户任务
            review_points: 审核点列表，可选：
                - "plan_review": 审核计划
                - "execution_monitor": 监控执行异常
                - "result_review": 审核最终结果

        Returns:
            执行结果
        """
        # TODO: 实现
        # 在每个审核点暂停，等待人工确认
        pass

    def _request_human_approval(self, stage: str, data: Dict) -> tuple:
        """
        请求人工批准

        Returns:
            tuple[bool, str|None]: (approved, feedback)
            - approved: True 表示批准，False 表示拒绝
            - feedback: 拒绝时的反馈意见
        """
        # TODO: 实现
        # 在实际应用中，这里可能是 Web 界面或消息通知
        # 作业中可以用 input() 简化实现
        print(f"\n{'='*40}")
        print(f"【人工审核 - {stage}】")
        print(f"{'='*40}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"{'='*40}")

        user_input = input("\n是否批准？(y/n/修改建议): ")

        if user_input.lower() == 'y':
            return True, None
        elif user_input.lower() == 'n':
            return False, "人工拒绝"
        else:
            return False, user_input  # 用户输入了修改建议
```

**3.2 测试人工审核（5 分）**

```python
# experiments/test_human_in_loop.py

def test_human_review():
    """测试人工审核"""
    from multiagent.human_in_loop import HumanInTheLoopWorkflow

    workflow = HumanInTheLoopWorkflow(planner, executor, reviewer, retriever)

    # 测试任务
    task = "分析客户反馈并生成报告"

    # 运行，启用所有审核点
    result = workflow.run(
        task,
        review_points=["plan_review", "execution_monitor", "result_review"]
    )

    print(f"\n最终结果：{result}")
```

**测试场景**：

1. **计划审核**：规划者制定计划后，人工检查是否合理
   - 如果合理，输入 `y` 继续
   - 如果不合理，输入修改建议（如"增加情感分析步骤"）

2. **执行监控**：如果执行中出现工具调用失败，人工决定是否中止

3. **结果审核**：审核者给出最终答案后，人工确认是否可接受

**提交内容**：
- `multiagent/human_in_loop.py`：人工审核实现
- `experiments/test_human_in_loop.py`：测试代码
- `report.md`：包含审核流程截图或日志

---

## 进阶任务（选做，25 分）

### 任务 4：并行执行与竞争共识（15 分）

三角色架构是顺序协作，但有些任务可以并行执行。添加并行执行能力。

#### 要求

**4.1 实现并行执行者（8 分）**

```python
# multiagent/parallel_executor.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

class ParallelExecutorAgent(ExecutorAgent):
    """支持并行执行的执行者"""

    def execute_plan_parallel(self, plan: Dict, max_workers: int = 3) -> Dict:
        """
        并行执行计划

        规则：
        1. 没有依赖关系的步骤可以并行
        2. 有依赖关系的步骤必须串行
        3. 依赖关系由 plan 中的 "depends_on" 字段指定

        示例计划：
        {
            "subtasks": [
                {"step": 1, "action": "加载文档A", "tool": "load", "depends_on": []},
                {"step": 2, "action": "加载文档B", "tool": "load", "depends_on": []},
                {"step": 3, "action": "合并分析", "tool": "analyze", "depends_on": [1, 2]}
            ]
        }

        步骤 1 和 2 可以并行，步骤 3 必须等待 1 和 2 完成
        """
        # TODO: 实现
        # 1. 分析依赖关系
        # 2. 找出可以并行的步骤
        # 3. 用线程池并行执行
        # 4. 等待所有步骤完成
        # 5. 处理依赖关系
        pass
```

**4.2 对比串行和并行性能（7 分）**

```python
# experiments/test_parallel.py

def compare_serial_vs_parallel():
    """对比串行和并行执行"""
    # 构造一个可以部分并行的任务
    task = """
    分析以下文档并生成综合报告：
    1. 加载文档 A（产品说明书）
    2. 加载文档 B（用户手册）
    3. 加载文档 C（FAQ）
    4. 合并三份文档的关键信息
    5. 生成综合报告
    """

    # 步骤 1-3 可以并行，步骤 4-5 必须串行

    # 测试串行执行
    serial_result = executor.execute_plan(plan)
    serial_time = serial_result["duration"]

    # 测试并行执行
    parallel_result = parallel_executor.execute_plan_parallel(plan)
    parallel_time = parallel_result["duration"]

    # 对比
    print(f"串行执行时间：{serial_time:.2f} 秒")
    print(f"并行执行时间：{parallel_time:.2f} 秒")
    print(f"加速比：{serial_time / parallel_time:.2f}x")
```

**输出表格**：

```markdown
### 串行 vs 并行性能对比

| 场景 | 串行时间 | 并行时间 | 加速比 |
|------|---------|---------|--------|
| 3 文档分析 | ? | ? | ? |
| 5 文档分析 | ? | ? | ? |
| 10 文档分析 | ? | ? | ? |

**结论**：
- 并行在什么场景下最有效？
- 加速比是否接近理论值（N/可并行步骤数）？
```

**提交内容**：
- `multiagent/parallel_executor.py`：并行执行者实现
- `experiments/test_parallel.py`：对比测试
- `report.md`：包含性能分析

---

### 任务 5：Agent 决策冲突与仲裁（10 分）

阿码问："如果规划者和执行者的决策冲突怎么办？" 添加仲裁机制。

#### 要求

**5.1 实现仲裁者 Agent（6 分）**

```python
# multiagent/arbitrator.py
from typing import Dict
from openai import OpenAI

class ArbitratorAgent:
    """仲裁者 Agent：解决 Agent 之间的决策冲突"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def arbitrate(
        self,
        agent_a_name: str,
        agent_a_decision: Dict,
        agent_b_name: str,
        agent_b_decision: Dict,
        context: Dict
    ) -> Dict:
        """
        仲裁两个 Agent 的决策冲突

        Args:
            agent_a_name: Agent A 的名称（如 "Planner"）
            agent_a_decision: Agent A 的决策
            agent_b_name: Agent B 的名称
            agent_b_decision: Agent B 的决策
            context: 冲突的上下文

        Returns:
            {
                "decision": "a/b/compromise",
                "reasoning": "选择该决策的原因",
                "modified_decision": {...}  # 如果是 compromise
            }
        """
        # TODO: 实现
        # 让 LLM 分析两个决策的优缺点，选择最合理的
        pass
```

**5.2 测试仲裁场景（4 分）**

```python
# experiments/test_arbitrator.py

def test_arbitrator():
    """测试仲裁者"""
    # 场景：规划者想先检索，执行者想先分析
    planner_decision = {
        "action": "retrieve_documents",
        "reasoning": "需要先获取背景信息才能准确分析"
    }

    executor_decision = {
        "action": "analyze_directly",
        "reasoning": "当前信息已经足够，可以先快速分析"
    }

    arbitrator = ArbitratorAgent(llm)

    decision = arbitrator.arbitrate(
        "Planner", planner_decision,
        "Executor", executor_decision,
        {"task": "分析客户反馈"}
    )

    print(f"仲裁结果：{decision['decision']}")
    print(f"理由：{decision['reasoning']}")
```

**提交内容**：
- `multiagent/arbitrator.py`：仲裁者实现
- `experiments/test_arbitrator.py`：测试代码
- `report.md`：包含仲裁场景分析

---

## 挑战任务（加分，15 分）

### 任务 6：自适应检索策略优化（15 分）

当前的检索 Agent 根据查询特征选择策略。挑战任务：让它能根据检索结果质量**自适应调整策略**。

#### 要求

**6.1 实现自适应检索（8 分）**

```python
# multiagent/adaptive_retriever.py
from .retriever import RetrieverAgent

class AdaptiveRetrieverAgent(RetrieverAgent):
    """自适应检索 Agent"""

    def retrieve_adaptive(
        self,
        query: str,
        top_k: int = 5,
        max_iterations: int = 3
    ) -> Dict:
        """
        自适应检索：根据结果质量动态调整策略

        流程：
        1. 初始策略决策
        2. 执行检索
        3. 评估结果质量
        4. 如果质量不够好：
           - 分析问题（召回不足？精度不足？）
           - 调整策略（换检索方式？增加 top_k？重写查询？）
           - 重新检索
        5. 重复直到质量满意或达到最大迭代次数

        Returns:
            {
                "query": query,
                "final_results": [...],
                "iterations": [
                    {"strategy": {...}, "results": [...], "assessment": {...}},
                    ...
                ],
                "total_iterations": 2
            }
        """
        # TODO: 实现
        pass

    def _analyze_retrieval_problem(
        self,
        query: str,
        results: Dict,
        assessment: Dict
    ) -> Dict:
        """
        分析检索问题

        Returns:
            {
                "problem_type": "recall/precision/query_ambiguity",
                "suggested_adjustment": {...}
            }
        """
        # TODO: 实现
        # 让 LLM 分析为什么检索结果不够好
        # 可能的问题：
        # - recall不足：需要增加 top_k 或重写查询
        # - precision不足：需要重排序或换检索方式
        # - query_ambiguity：需要查询扩展或分解
        pass
```

**6.2 对比自适应与单次检索（7 分）**

```python
# experiments/test_adaptive_retrieval.py

def compare_adaptive_retrieval():
    """对比自适应检索和单次检索"""
    # 测试查询
    test_queries = [
        "如何退货和换货？",  # 简单查询，单次检索应该足够
        "产品质量问题和物流投诉的处理流程",  # 复杂查询，可能需要多次调整
        "类似但是更便宜的产品推荐",  # 需要调整检索策略
    ]

    for query in test_queries:
        print(f"\n查询：{query}")

        # 单次检索
        single_result = retriever.retrieve(query)
        print(f"单次检索策略：{single_result['strategy']['method']}")
        print(f"单次检索质量：{single_result['assessment']['confidence']}")

        # 自适应检索
        adaptive_result = adaptive_retriever.retrieve_adaptive(query)
        print(f"自适应检索迭代：{adaptive_result['total_iterations']} 次")
        print(f"最终检索质量：{adaptive_result['final_assessment']['confidence']}")

        # 对比
        improvement = (
            adaptive_result['final_assessment']['confidence'] -
            single_result['assessment']['confidence']
        )
        print(f"质量提升：{improvement:.2f}")
```

**输出表格**：

```markdown
### 自适应检索效果对比

| 查询类型 | 单次检索质量 | 自适应检索质量 | 迭代次数 | 提升 |
|---------|------------|--------------|---------|------|
| 简单查询 | ? | ? | ? | ? |
| 复杂查询 | ? | ? | ? | ? |
| 模糊查询 | ? | ? | ? | ? |

**分析**：
- 自适应检索在什么场景下最有价值？
- 迭代次数和性能提升的权衡是什么？
```

**提交内容**：
- `multiagent/adaptive_retriever.py`：自适应检索实现
- `experiments/test_adaptive_retrieval.py`：对比测试
- `report.md`：包含完整的自适应策略分析

---

## AI 协作练习（可选）

Week 06 处于"协作期"，你可以用 AI 辅助调试多 Agent 通信问题。下面这段 AI 生成的代码有几个问题，请审查并修复。

### 待审查代码

```python
# AI 生成的多 Agent 系统实现（故意包含问题）
from openai import OpenAI
import json

class MultiAgentSystem:
    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reviewer = ReviewerAgent()

    def run(self, task):
        # 规划
        plan = self.planner.create_plan(task)

        # 执行
        for subtask in plan["subtasks"]:
            tool = subtask["tool"]
            params = subtask["params"]
            result = self.executor.tools[tool](**params)
            subtask["result"] = result  # 直接修改原始 plan

        # 审核
        review = self.reviewer.review(plan)
        return review
```

### 审查清单

请对照以下清单审查代码：

```markdown
## 多 Agent 代码审查报告

### 1. Agent 通信
- [ ] Agent 之间传递什么数据？（plan、result、review）
- [ ] 数据格式是否一致？（JSON、Dict、自定义对象）
- [ ] 直接修改原始 plan 会有什么问题？

你的分析和修复方案：
...

### 2. 错误处理
- [ ] 如果工具调用失败会怎样？
- [ ] 如果某个 Agent 返回格式错误会怎样？
- [ ] 有没有异常捕获和降级？

你的分析和修复方案：
...

### 3. 状态管理
- [ ] 执行结果存在哪里？
- [ ] 如果需要修订计划，原始 plan 是否保留？
- [ ] 如何追踪 Agent 之间的依赖关系？

你的分析和修复方案：
...

### 4. LLM 客户端复用
- [ ] 每个 Agent 都创建独立的 OpenAI() 客户端吗？
- [ ] 这会造成什么问题（成本、连接数）？

你的分析和修复方案：
...

### 5. 并发安全
- [ ] 如果多个 Agent 并行执行，会不会有竞态条件？
- [ ] 共享状态如何同步？

你的分析和修复方案：
...
```

### 你的修订版

基于审查，写出你的修订版本（只需修改关键部分）：

```python
# 我的修订版
class FixedMultiAgentSystem:
    """修复后的多 Agent 系统"""

    def __init__(self, llm_client):
        # TODO: 你的初始化
        pass

    def run(self, task, enable_parallel=False):
        # TODO: 你的实现
        # 1. 正确的 Agent 通信
        # 2. 完整的错误处理
        # 3. 清晰的状态管理
        # 4. LLM 客户端复用
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
- 多 Agent 系统最难的地方是什么？
- 如何设计清晰的 Agent 通信协议？
```

**重要**：AI 协作练习不影响基础任务的评分，但需要展示你的审查过程和系统思维。

---

## TextAgent 项目任务

本周将多智能体能力整合到 TextAgent 系统中。

### 要求

**更新 TextAgent 架构**：

```python
# src/textagent/__init__.py

# 新增多智能体模块
from .multiagent import (
    PlannerAgent,
    ExecutorAgent,
    ReviewerAgent,
    RetrieverAgent,
    MultiAgentWorkflow
)

# TextAgent 现在有两种模式：
# 1. 单 Agent 模式（Week 05）
# 2. 多 Agent 模式（Week 06）

class TextAgent:
    def __init__(self, mode="multiagent", **kwargs):
        if mode == "multiagent":
            self.workflow = MultiAgentWorkflow(...)
        else:
            self.agent = ReActAgent(...)

    def analyze(self, task):
        if hasattr(self, 'workflow'):
            return self.workflow.run(task)
        else:
            return self.agent.run(task)
```

**在 report.md 中记录**：

```markdown
## Week 06：多智能体协作

### 架构变更

1. 新增多智能体模块
   - PlannerAgent：任务规划
   - ExecutorAgent：工具执行
   - ReviewerAgent：结果审核
   - RetrieverAgent：智能检索

2. Human-in-the-Loop 机制
   - 计划审核点
   - 执行监控点
   - 结果审核点

3. Agentic RAG
   - Agent 自主决定检索策略
   - 自适应检索优化

### 示例任务

任务："分析产品反馈并生成报告"

执行流程：
1. Planner 制定 4 步计划
2. Executor 并行执行步骤 1-3
3. Retriever 使用混合检索
4. Reviewer 审核并通过

### 性能对比

| 指标 | Week 05（单 Agent） | Week 06（多 Agent） | 改进 |
|------|-------------------|-------------------|------|
| 平均迭代次数 | ? | ? | ? |
| 执行时间 | ? | ? | ? |
| 可追溯性 | 低 | 高 | ✅ |
| 错误率 | ? | ? | ? |

### 下一步

- Week 07：评估与优化
```

---

## 提交清单

在提交作业前，请确认以下内容：

### 文件结构

```
week06_作业_你的姓名/
├── multiagent/
│   ├── planner.py              # 规划者（Part 1.1）
│   ├── executor.py             # 执行者（Part 1.2）
│   ├── reviewer.py             # 审核者（Part 1.3）
│   ├── retriever.py            # 检索 Agent（Part 2.1）
│   ├── workflow.py             # 工作流（Part 2.2）
│   ├── human_in_loop.py        # 人工审核（Part 3.1）
│   ├── parallel_executor.py    # 并行执行（任务 4）
│   ├── arbitrator.py           # 仲裁者（任务 5）
│   └── adaptive_retriever.py   # 自适应检索（任务 6）
├── experiments/
│   ├── test_three_agents.py    # 三 Agent 测试
│   ├── test_agentic_rag.py     # Agentic RAG 测试
│   ├── test_human_in_loop.py   # 人工审核测试
│   ├── test_parallel.py        # 并行测试
│   ├── test_arbitrator.py      # 仲裁测试
│   └── test_adaptive_retrieval.py  # 自适应检索测试
├── src/textagent/
│   └── __init__.py             # TextAgent 更新
├── report.md                   # 完整实验报告
└── README.md                   # 简要说明
```

### 质量检查

- [ ] 所有代码都能独立运行
- [ ] 三 Agent 协作有完整的测试输出
- [ ] Agentic RAG 展示了不同查询的策略选择
- [ ] 人工审核有日志或截图
- [ ] report.md 包含所有实验结果
- [ ] TextAgent 整合了多 Agent 模式
- [ ] （可选）AI 协作练习包含审查报告

---

## 常见问题

**Q：多 Agent 系统一定比单 Agent 好吗？**

A：不一定。多 Agent 的优势是：
- 责任分离，每个 Agent 专注自己的领域
- 决策可追溯，知道"谁做了什么决定"
- 容错性更好，单个 Agent 错误不会导致全盘失败

但代价是：
- 成本更高（多个 LLM 调用）
- 延迟更大（Agent 之间通信）
- 调试更难（问题可能出在多个地方）

建议：简单任务用单 Agent，复杂任务用多 Agent。

**Q：规划者和执行者的决策冲突怎么办？**

A：几种策略：
1. **层级制**：规划者决策，执行者服从（本周默认）
2. **民主制**：Agent 协商，投票决定
3. **仲裁制**：第三方 Agent 裁决（见任务 5）

**注意**：如 CHAPTER.md 第 2 节"阿码的问题：决策冲突怎么办？"中所述（第 354-370 行），民主制在多 Agent 系统中往往是最差的选择。因为 LLM 没有"真正的信念"，两个 Agent 协商可能被对方说服，达成"平庸的共识"而非"最优决策"。这就像"两个都没去过目的地的人争论走哪条路，最后可能选了一条最远的路"。因此本周推荐使用层级制——明确责任边界，规划者负责决策，执行者负责执行。

**Q：检索 Agent 如何知道哪种策略更好？**

A：靠训练和经验：
- 用 Few-shot 示例教 LLM 什么查询用什么策略
- 让 LLM 分析查询特征（精确匹配 vs 语义相似）
- 用评估结果反馈，强化正确的策略选择

**Q：Human-in-the-Loop 会不会很慢？**

A：是的，人工审核会增加延迟。但在以下场景值得：
- 高风险决策（退款、删除数据）
- 容易出错的场景（新任务、边缘案例）
- 需要学习的阶段（收集反馈改进系统）

随着系统成熟，可以逐步减少审核点（渐进式自动化）。

**Q：并行执行一定更快吗？**

A：不一定。并行的收益来自：
- 可以真正并行的步骤（I/O 密集型任务最有效）
- 步骤之间的依赖关系少

如果步骤之间有强依赖，并行反而会增加复杂度。而且 LLM 调用通常受 API 限流，真正的并行有限。

---

## 评分重点

本次作业的评分重点：

1. **理解多智能体架构**：不只是"多个 Agent"，而是责任分离和协作模式
2. **Agent 通信设计**：清晰的消息格式、状态管理
3. **检索策略决策**：让 Agent 自主决定，而不是硬编码规则
4. **人工审核设计**：在关键点引入人工，而不是全盘自动化

记住老潘的话："多 Agent 系统的关键是**可追溯性**——每个 Agent 的决策都要有日志，出了问题能找到责任方。"

---

## 提示

如果你遇到困难，可以参考 `starter_code/solution.py`。但记住：
1. 不要直接复制粘贴
2. 理解每一行代码的作用
3. 自己动手修改和调试

真正的学习发生在你调试 Agent 通信、解决决策冲突、设计审核点的过程中。

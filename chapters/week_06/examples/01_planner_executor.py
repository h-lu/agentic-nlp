#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：规划者-执行者模式（Planner-Executor Pattern）

本例演示多智能体系统的最简单形式：规划者 Agent 负责制定计划，
执行者 Agent 负责按计划执行工具调用。

核心思想：
- 规划者（Planner）：理解任务，分解为子任务，生成执行计划
- 执行者（Executor）：按计划调用工具，收集结果
- 责任分离：规划者不执行，执行者不规划

运行方式：python3 chapters/week_06/examples/01_planner_executor.py
预期输出：展示规划者如何分解任务，执行者如何按计划执行

依赖：
- pip install openai
- export OPENAI_API_KEY="your-api-key"
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from openai import OpenAI


# ============================================================
# 数据结构
# ============================================================

@dataclass
class SubTask:
    """子任务定义"""
    step: int
    action: str
    tool: str
    params: Dict[str, Any]
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Any = None


@dataclass
class ExecutionPlan:
    """执行计划"""
    task_understanding: str
    subtasks: List[SubTask]
    expected_output: str


@dataclass
class ExecutionResult:
    """执行结果"""
    plan: ExecutionPlan
    results: List[Dict[str, Any]]
    status: str


# ============================================================
# 规划者 Agent
# ============================================================

class PlannerAgent:
    """
    规划者 Agent：专注于任务分解和计划制定

    职责：
    - 理解用户任务的意图
    - 将复杂任务分解为可执行的子任务
    - 确定子任务的执行顺序和依赖关系

    不负责：
    - 不直接调用工具
    - 不执行具体的操作
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        if llm_client is None and os.environ.get("OPENAI_API_KEY"):
            self.llm = OpenAI()
        else:
            self.llm = llm_client  # 可能是 None，表示模拟模式

    def create_plan(self, task: str, available_tools: List[str]) -> ExecutionPlan:
        """创建任务计划"""

        if self.llm is None:
            # 模拟模式：返回基于规则的计划
            return self._mock_plan(task, available_tools)

        tools_desc = "\n".join([f"- {tool}" for tool in available_tools])

        prompt = f"""你是一个任务规划专家。请分析以下任务，制定执行计划。

任务：{task}

可用工具：
{tools_desc}

请按以下 JSON 格式输出计划：

{{
  "task_understanding": "对任务的理解",
  "subtasks": [
    {{"step": 1, "action": "做什么", "tool": "工具名称", "params": {{"参数": "值"}}}},
    ...
  ],
  "expected_output": "期望的最终输出"
}}

要求：
1. 每个子任务应该有明确的目的
2. 子任务之间应该有逻辑顺序
3. 只使用可用工具列表中的工具
4. params 应该是具体的参数值，不要用占位符

计划（JSON格式）："""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            plan_text = response.choices[0].message.content
            plan_data = json.loads(plan_text)

            # 构建 SubTask 对象
            subtasks = []
            for st in plan_data.get("subtasks", []):
                subtasks.append(SubTask(
                    step=st["step"],
                    action=st["action"],
                    tool=st["tool"],
                    params=st.get("params", {}),
                ))

            return ExecutionPlan(
                task_understanding=plan_data["task_understanding"],
                subtasks=subtasks,
                expected_output=plan_data["expected_output"]
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"解析计划失败: {e}")
            return self._mock_plan(task, available_tools)

    def revise_plan(self, original_plan: ExecutionPlan, feedback: str) -> ExecutionPlan:
        """根据反馈修订计划"""
        if self.llm is None:
            # 模拟模式：简单返回原计划
            print(f"[模拟模式] 收到反馈: {feedback}")
            return original_plan

        plan_summary = {
            "task_understanding": original_plan.task_understanding,
            "subtasks": [
                {
                    "step": st.step,
                    "action": st.action,
                    "tool": st.tool,
                    "params": st.params
                }
                for st in original_plan.subtasks
            ],
            "expected_output": original_plan.expected_output
        }

        prompt = f"""原计划：

{json.dumps(plan_summary, ensure_ascii=False, indent=2)}

反馈：
{feedback}

请根据反馈修订计划，输出新的 JSON 格式计划。"""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            plan_text = response.choices[0].message.content
            plan_data = json.loads(plan_text)

            subtasks = []
            for st in plan_data.get("subtasks", []):
                subtasks.append(SubTask(
                    step=st["step"],
                    action=st["action"],
                    tool=st["tool"],
                    params=st.get("params", {}),
                ))

            return ExecutionPlan(
                task_understanding=plan_data["task_understanding"],
                subtasks=subtasks,
                expected_output=plan_data["expected_output"]
            )
        except Exception as e:
            print(f"修订计划失败: {e}")
            return original_plan

    def _mock_plan(self, task: str, available_tools: List[str]) -> ExecutionPlan:
        """模拟模式：生成预设的计划"""
        if "分析" in task and "情感" in task:
            return ExecutionPlan(
                task_understanding="用户需要分析文本的情感倾向",
                subtasks=[
                    SubTask(step=1, action="分析情感", tool="analyze_sentiment",
                           params={"text": "这是待分析的文本"}),
                ],
                expected_output="情感分析结果（正面/负面/中性）"
            )
        elif "检索" in task or "搜索" in task:
            return ExecutionPlan(
                task_understanding="用户需要检索相关文档",
                subtasks=[
                    SubTask(step=1, action="检索文档", tool="search_documents",
                           params={"query": "搜索关键词", "top_k": 5}),
                ],
                expected_output="相关文档列表"
            )
        else:
            # 默认计划
            return ExecutionPlan(
                task_understanding=f"处理任务: {task}",
                subtasks=[
                    SubTask(step=1, action="直接响应", tool="direct_answer",
                           params={"message": task}),
                ],
                expected_output="响应结果"
            )


# ============================================================
# 执行者 Agent
# ============================================================

class ExecutorAgent:
    """
    执行者 Agent：专注于按计划执行工具调用

    职责：
    - 按照计划逐步执行子任务
    - 调用相应的工具
    - 收集执行结果

    不负责：
    - 不质疑或修改计划
    - 不做高层决策
    """

    def __init__(self, tools: Dict[str, Callable]):
        self.tools = tools

    def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """执行计划"""

        results = []

        for subtask in plan.subtasks:
            subtask.status = "in_progress"

            print(f"\n  [步骤 {subtask.step}] {subtask.action}")
            print(f"    工具: {subtask.tool}")

            tool_name = subtask.tool
            params = subtask.params

            # 执行工具
            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](**params)
                    subtask.result = result
                    subtask.status = "completed"
                    results.append({
                        "step": subtask.step,
                        "action": subtask.action,
                        "result": result
                    })
                    print(f"    结果: {result}")
                except Exception as e:
                    subtask.result = str(e)
                    subtask.status = "failed"
                    results.append({
                        "step": subtask.step,
                        "action": subtask.action,
                        "error": str(e)
                    })
                    print(f"    错误: {e}")
            else:
                error_msg = f"未知工具: {tool_name}"
                subtask.result = error_msg
                subtask.status = "failed"
                results.append({
                    "step": subtask.step,
                    "action": subtask.action,
                    "error": error_msg
                })
                print(f"    {error_msg}")

        return ExecutionResult(
            plan=plan,
            results=results,
            status="completed"
        )


# ============================================================
# 工具定义
# ============================================================

def search_documents(query: str, top_k: int = 5) -> Dict:
    """搜索文档（模拟）"""
    return {
        "query": query,
        "documents": [f"文档{i+1}: {query}相关内容" for i in range(min(top_k, 5))],
        "count": min(top_k, 5)
    }


def analyze_sentiment(text: str) -> Dict:
    """分析情感（模拟）"""
    positive_words = ["满意", "好", "棒", "优秀", "喜欢"]
    negative_words = ["不满意", "差", "糟糕", "讨厌"]

    score = 0
    for word in positive_words:
        if word in text:
            score += 1
    for word in negative_words:
        if word in text:
            score -= 1

    if score > 0:
        return {"sentiment": "positive", "confidence": 0.8, "text": text}
    elif score < 0:
        return {"sentiment": "negative", "confidence": 0.8, "text": text}
    else:
        return {"sentiment": "neutral", "confidence": 0.5, "text": text}


def extract_keywords(text: str, top_k: int = 5) -> Dict:
    """提取关键词（模拟）"""
    words = ["产品", "质量", "服务", "物流", "价格", "体验"]
    return {"keywords": words[:top_k], "text": text}


def direct_answer(message: str) -> str:
    """直接回答（模拟）"""
    return f"收到您的消息：{message}"


# ============================================================
# 反例：没有分工的糟糕实现
# ============================================================

def bad_implementation_example():
    """
    反例：单个 Agent 既规划又执行

    常见错误：
    1. 规划和执行混在一起，难以调试
    2. 无法单独优化规划或执行逻辑
    3. 职责不清晰，容易出现认知超载
    """

    class MonolithicAgent:
        """❌ 单体 Agent（不推荐）"""

        def __init__(self, tools, llm):
            self.tools = tools
            self.llm = llm

        def run(self, task):
            # 问题1: 规划和执行混在一起
            # 问题2: 代码难以测试和维护
            # 问题3: 无法单独复用规划或执行逻辑
            plan = self._create_plan(task)
            results = self._execute_plan(plan)
            return self._format_results(results)

    print("❌ 错误做法示例：")
    print("MonolithicAgent 把规划和执行混在一起")
    print("✅ 正确做法：使用 PlannerAgent 和 ExecutorAgent 分离职责")


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    print("=" * 70)
    print("规划者-执行者模式演示")
    print("=" * 70)

    # 检查 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n警告：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        print("\n将使用模拟模式演示...")
        demo_mode = True
    else:
        demo_mode = False

    # 工具定义
    tools = {
        "search_documents": search_documents,
        "analyze_sentiment": analyze_sentiment,
        "extract_keywords": extract_keywords,
        "direct_answer": direct_answer,
    }

    # 创建 Agent
    planner = PlannerAgent()
    executor = ExecutorAgent(tools)

    # 测试任务
    test_tasks = [
        "分析客户反馈的情感倾向",
        "检索关于远程办公政策的文档",
    ]

    for task in test_tasks:
        print(f"\n{'='*70}")
        print(f"用户任务: {task}")
        print('='*70)

        # 1. 规划阶段
        print("\n[规划阶段] Planner Agent 工作中...")
        plan = planner.create_plan(task, list(tools.keys()))

        print(f"\n任务理解: {plan.task_understanding}")
        print(f"\n执行计划:")
        for st in plan.subtasks:
            print(f"  步骤 {st.step}: {st.action}")
            print(f"    工具: {st.tool}")
            print(f"    参数: {json.dumps(st.params, ensure_ascii=False)}")
        print(f"\n期望输出: {plan.expected_output}")

        # 2. 执行阶段
        print(f"\n{'='*70}")
        print("[执行阶段] Executor Agent 工作中...")
        print('='*70)

        result = executor.execute_plan(plan)

        # 3. 结果汇总
        print(f"\n{'='*70}")
        print("执行结果:")
        print('='*70)
        print(f"状态: {result.status}")
        print(f"完成的步骤: {len([r for r in result.results if 'error' not in r])}/{len(plan.subtasks)}")

    # 对比说明
    print("\n" + "=" * 70)
    print("规划者-执行者模式的价值")
    print("=" * 70)
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 单 Agent                          │  规划者-执行者模式             │
├─────────────────────────────────────────────────────────────────┤
│ 规划和执行混在一起                   │  规划和执行分离                │
│ 认知负荷高（同时思考两件事）           │  每个 Agent 专注一件事         │
│ 难以调试（不知道是规划错还是执行错）     │  职责清晰，问题易定位           │
│ 无法单独优化规划或执行               │  可独立改进每个 Agent          │
└─────────────────────────────────────────────────────────────────┘

规划者-执行者的关键价值：
1. 责任分离：规划者不执行，执行者不规划
2. 专业化：每个 Agent 专注自己的领域
3. 可扩展性：可以添加审核者（Reviewer）等新角色
4. 可测试性：可以单独测试规划者和执行者

老潘的点评：
"在公司里，我们从来不让一个人同时做架构设计和写代码。
规划是架构师的事，执行是工程师的事。多 Agent 系统也是一样。"

适用场景：
✅ 复杂的多步骤任务
✅ 需要可解释性的场景（可以查看计划）
✅ 需要人工审核的场景（可以先审核计划）

❌ 简单的单步任务（直接 Function Calling 更高效）
    """)

    # 展示反例
    print("\n" + "=" * 70)
    print("反例：没有分工的糟糕实现")
    print("=" * 70)
    bad_implementation_example()


if __name__ == "__main__":
    main()

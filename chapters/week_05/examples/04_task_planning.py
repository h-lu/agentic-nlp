#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：任务规划（Task Planning）

本例演示 Agent 如何将复杂任务分解为可执行的子任务：
1. 规划阶段：分析任务，生成执行计划
2. 执行阶段：按计划调用工具
3. 反思阶段：检查结果，决定是否需要调整

运行方式：python3 chapters/week_05/examples/04_task_planning.py
预期输出：展示 Agent 如何分解复杂任务并逐步执行

依赖：
- pip install openai
- export OPENAI_API_KEY="your-api-key"
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from openai import OpenAI


# ============================================================
# 数据结构
# ============================================================

@dataclass
class SubTask:
    """子任务定义"""
    id: str
    description: str
    tool: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Any = None
    depends_on: Optional[List[str]] = None  # 依赖的其他子任务


@dataclass
class ExecutionPlan:
    """执行计划"""
    goal: str
    subtasks: List[SubTask]
    status: str = "planning"  # planning, executing, completed, failed


# ============================================================
# 规划模板（Few-shot 示例）
# ============================================================

PLANNING_EXAMPLES = """
## 示例1：天气比较任务

用户请求：北京和上海哪个城市今天更热？

规划：
- subtask_1: 查询北京的天气
  tool: get_weather
  params: {"city": "北京"}

- subtask_2: 查询上海的天气
  tool: get_weather
  params: {"city": "上海"}

- subtask_3: 比较两个城市的温度
  tool: compare_temperatures
  params: {"temp1": "${subtask_1.result.temp}", "temp2": "${subtask_2.result.temp}"}


## 示例2：信息汇总任务

用户请求：帮我总结一下公司关于远程办公和报销的政策

规划：
- subtask_1: 搜索远程办公相关政策
  tool: search_policy
  params: {"keyword": "远程办公"}

- subtask_2: 搜索报销相关政策
  tool: search_policy
  params: {"keyword": "报销"}

- subtask_3: 汇总两项政策信息
  tool: summarize
  params: {"inputs": ["${subtask_1.result}", "${subtask_2.result}"]}
"""


# ============================================================
# 工具定义
# ============================================================

def get_weather(city: str) -> Dict[str, Any]:
    """获取城市天气（模拟）"""
    weather_data = {
        "北京": {"temp": 22, "condition": "晴"},
        "上海": {"temp": 26, "condition": "多云"},
        "深圳": {"temp": 30, "condition": "阵雨"},
    }
    return {
        "city": city,
        **weather_data.get(city, {"temp": 25, "condition": "未知"})
    }


def search_policy(keyword: str) -> str:
    """搜索公司政策（模拟）"""
    policies = {
        "远程办公": "远程办公需提前3天申请，每周最多2天，需主管审批。",
        "报销": "费用报销需在发生后30天内提交，发票需为公司抬头的正式发票。",
        "年假": "年假需提前7天申请，5天以下需主管审批。",
    }
    return policies.get(keyword, f"未找到关于'{keyword}'的政策信息。")


def compare_temperatures(temp1: float, temp2: float, city1: str, city2: str) -> str:
    """比较温度"""
    if temp1 > temp2:
        return f"{city1}（{temp1}°C）比{city2}（{temp2}°C）更热"
    elif temp1 < temp2:
        return f"{city2}（{temp2}°C）比{city1}（{temp1}°C）更热"
    else:
        return f"{city1}和{city2}温度相同，都是{temp1}°C"


def summarize_policies(policies: list[str]) -> str:
    """汇总政策信息"""
    return "\n\n".join([f"- {p}" for p in policies])


# ============================================================
# 规划 Agent
# ============================================================

class PlanningAgent:
    """
    规划 Agent：负责将复杂任务分解为子任务

    核心能力：
    - 理解用户意图
    - 识别需要的步骤
    - 生成可执行计划
    """

    def __init__(self, llm: Optional[OpenAI] = None):
        if llm is None and os.environ.get("OPENAI_API_KEY"):
            self.llm = OpenAI()
        else:
            self.llm = llm  # 可能是 None，表示模拟模式
        self.available_tools = {
            "get_weather": get_weather,
            "search_policy": search_policy,
            "compare_temperatures": compare_temperatures,
            "summarize_policies": summarize_policies,
        }

    def plan(self, task: str) -> ExecutionPlan:
        """
        为任务生成执行计划

        Returns:
            ExecutionPlan 包含目标和一个或多个子任务
        """
        tools_desc = self._describe_tools()

        prompt = f"""你是一个任务规划专家。你的职责是将用户请求分解为清晰的子任务。

可用工具：
{tools_desc}

{PLANNING_EXAMPLES}

现在请为以下用户请求生成执行计划。

用户请求：{task}

请以JSON格式输出计划，格式如下：
{{
    "goal": "对用户目标的简短描述",
    "subtasks": [
        {{
            "id": "subtask_1",
            "description": "这个子任务做什么",
            "tool": "工具名称",
            "parameters": {{"参数": "值"}}
        }}
    ]
}}

注意：
1. 每个子任务应该有明确的目的
2. 子任务之间可能存在依赖关系（后续任务引用前序任务的结果）
3. 只使用可用工具列表中的工具
4. parameters 中的值如果是引用前序任务结果，使用格式 "${{subtask_X.result.key}}"

计划（JSON格式）："""

        if self.llm is None:
            # 模拟模式：返回基于规则的计划
            return self._mock_plan(task)

        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        try:
            plan_data = json.loads(response.choices[0].message.content)

            # 构建 SubTask 对象
            subtasks = []
            for st in plan_data.get("subtasks", []):
                subtasks.append(SubTask(
                    id=st["id"],
                    description=st["description"],
                    tool=st.get("tool"),
                    parameters=st.get("parameters"),
                ))

            return ExecutionPlan(
                goal=plan_data["goal"],
                subtasks=subtasks,
                status="planning"
            )
        except (json.JSONDecodeError, KeyError) as e:
            # 如果解析失败，返回一个简单的默认计划
            return ExecutionPlan(
                goal=task,
                subtasks=[
                    SubTask(
                        id="subtask_1",
                        description="直接响应用户",
                        tool=None,
                        parameters=None,
                    )
                ]
            )

    def execute_plan(self, plan: ExecutionPlan) -> str:
        """
        执行计划

        按顺序执行子任务，处理依赖关系，收集结果
        """
        plan.status = "executing"
        results = {}

        for subtask in plan.subtasks:
            subtask.status = "in_progress"

            print(f"\n  执行: {subtask.description}")

            if subtask.tool and subtask.tool in self.available_tools:
                # 解析参数（可能包含对前序任务结果的引用）
                params = self._resolve_parameters(subtask.parameters, results)

                try:
                    tool_result = self.available_tools[subtask.tool](**params)
                    subtask.result = tool_result
                    subtask.status = "completed"
                    results[subtask.id] = tool_result
                    print(f"    结果: {tool_result}")
                except Exception as e:
                    subtask.result = str(e)
                    subtask.status = "failed"
                    print(f"    失败: {e}")
            else:
                # 没有 tool 的子任务，跳过或直接完成
                subtask.status = "completed"

        plan.status = "completed"

        # 生成最终回复
        return self._generate_final_response(plan)

    def _describe_tools(self) -> str:
        """描述可用工具"""
        descriptions = []
        for name, func in self.available_tools.items():
            desc = f"- {name}: {func.__doc__}"
            descriptions.append(desc)
        return "\n".join(descriptions)

    def _mock_plan(self, task: str) -> ExecutionPlan:
        """模拟模式：生成预设的计划"""
        if "天气" in task and "比较" in task:
            return ExecutionPlan(
                goal="比较北京和上海的天气温度",
                subtasks=[
                    SubTask(
                        id="subtask_1",
                        description="查询北京的天气",
                        tool="get_weather",
                        parameters={"city": "北京"},
                    ),
                    SubTask(
                        id="subtask_2",
                        description="查询上海的天气",
                        tool="get_weather",
                        parameters={"city": "上海"},
                    ),
                    SubTask(
                        id="subtask_3",
                        description="比较两城市温度",
                        tool="compare_temperatures",
                        parameters={
                            "temp1": "${subtask_1.result.temp}",
                            "temp2": "${subtask_2.result.temp}",
                            "city1": "北京",
                            "city2": "上海"
                        },
                    ),
                ]
            )
        elif "政策" in task or "报销" in task or "远程" in task:
            return ExecutionPlan(
                goal="汇总相关政策信息",
                subtasks=[
                    SubTask(
                        id="subtask_1",
                        description="搜索远程办公政策",
                        tool="search_policy",
                        parameters={"keyword": "远程办公"},
                    ),
                    SubTask(
                        id="subtask_2",
                        description="搜索报销政策",
                        tool="search_policy",
                        parameters={"keyword": "报销"},
                    ),
                    SubTask(
                        id="subtask_3",
                        description="汇总政策信息",
                        tool="summarize_policies",
                        parameters={
                            "policies": [
                                "${subtask_1.result}",
                                "${subtask_2.result}"
                            ]
                        },
                    ),
                ]
            )
        else:
            # 默认计划
            return ExecutionPlan(
                goal=task,
                subtasks=[
                    SubTask(
                        id="subtask_1",
                        description="直接响应用户",
                    )
                ]
            )

    def _resolve_parameters(
        self,
        parameters: Optional[Dict[str, Any]],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析参数，替换对前序任务结果的引用"""
        if not parameters:
            return {}

        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 引用前序任务结果: ${subtask_1.result.temp}
                ref = value[2:-1]  # 去掉 ${ 和 }
                parts = ref.split(".")
                if parts[0] in results:
                    if len(parts) == 2:
                        resolved[key] = results[parts[0]].get(parts[1])
                    else:
                        resolved[key] = results[parts[0]]
                else:
                    resolved[key] = value
            else:
                resolved[key] = value

        return resolved

    def _generate_final_response(self, plan: ExecutionPlan) -> str:
        """基于执行结果生成最终回复"""
        # 收集所有子任务的结果
        completed_results = [
            f"{st.description}: {st.result}"
            for st in plan.subtasks
            if st.status == "completed"
        ]

        if not completed_results:
            return "抱歉，未能完成您的请求。"

        return "\n\n".join(completed_results)


# ============================================================
# 反例：没有规划的糟糕实现
# ============================================================

def bad_planning_example():
    """
    反例：没有规划，直接执行

    常见错误：
    1. 遇到复杂任务时无法拆解
    2. 没有明确的执行顺序
    3. 难以处理任务间的依赖关系
    """

    print("""
❌ 错误做法：没有规划的 Agent

class ImpulsiveAgent:
    def run(self, task):
        # 问题1：直接执行，没有规划
        if "天气" in task and "比较" in task:
            # 问题2：硬编码逻辑，无法扩展
            return self._handle_weather_compare(task)
        elif "政策" in task:
            return self._handle_policy_query(task)
        # ...

问题：
1. 每种任务类型都需要硬编码
2. 无法处理新的任务组合
3. 难以处理多步骤复杂任务

✅ 正确做法：使用 Planning Agent

- 先规划：将任务分解为子任务
- 再执行：按计划逐步执行
- 可扩展：新工具只需要注册即可
    """)


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    print("=" * 70)
    print("任务规划（Task Planning）演示")
    print("=" * 70)

    # 检查 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n错误：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        print("\n将使用模拟模式演示...")
        demo_mode = True
    else:
        demo_mode = False

    # 创建 Agent
    agent = PlanningAgent()

    # 测试任务
    test_tasks = [
        "北京和上海哪个城市今天更热？",
        "帮我总结一下公司关于远程办公和报销的政策",
    ]

    for task in test_tasks:
        print(f"\n{'='*70}")
        print(f"用户任务: {task}")
        print('='*70)

        if demo_mode:
            # 模拟模式：展示规划结果
            if "天气" in task and "比较" in task:
                plan = ExecutionPlan(
                    goal="比较北京和上海的天气温度",
                    subtasks=[
                        SubTask(
                            id="subtask_1",
                            description="查询北京的天气",
                            tool="get_weather",
                            parameters={"city": "北京"},
                        ),
                        SubTask(
                            id="subtask_2",
                            description="查询上海的天气",
                            tool="get_weather",
                            parameters={"city": "上海"},
                        ),
                        SubTask(
                            id="subtask_3",
                            description="比较两城市温度",
                            tool="compare_temperatures",
                            parameters={
                                "temp1": "${subtask_1.result.temp}",
                                "temp2": "${subtask_2.result.temp}",
                                "city1": "北京",
                                "city2": "上海"
                            },
                        ),
                    ]
                )
            else:
                plan = ExecutionPlan(
                    goal="汇总远程办公和报销政策",
                    subtasks=[
                        SubTask(
                            id="subtask_1",
                            description="搜索远程办公政策",
                            tool="search_policy",
                            parameters={"keyword": "远程办公"},
                        ),
                        SubTask(
                            id="subtask_2",
                            description="搜索报销政策",
                            tool="search_policy",
                            parameters={"keyword": "报销"},
                        ),
                        SubTask(
                            id="subtask_3",
                            description="汇总政策信息",
                            tool="summarize_policies",
                            parameters={
                                "policies": [
                                    "${subtask_1.result}",
                                    "${subtask_2.result}"
                                ]
                            },
                        ),
                    ]
                )
        else:
            # 真实模式：让 LLM 生成计划
            try:
                plan = agent.plan(task)
            except Exception as e:
                print(f"\n规划失败: {e}")
                continue

        # 展示计划
        print(f"\n目标: {plan.goal}")
        print(f"\n子任务计划:")
        for i, st in enumerate(plan.subtasks, 1):
            deps = f" (依赖: {st.depends_on})" if st.depends_on else ""
            print(f"  {i}. {st.description}")
            if st.tool:
                print(f"     工具: {st.tool}")
                if st.parameters:
                    print(f"     参数: {json.dumps(st.parameters, ensure_ascii=False)}")
            print(f"     状态: {st.status}{deps}")

        # 执行计划
        print(f"\n{'='*70}")
        print("执行计划:")
        print('='*70)

        result = agent.execute_plan(plan)

        print(f"\n{'='*70}")
        print("最终结果:")
        print('='*70)
        print(result)

    # 总结
    print(f"\n{'='*70}")
    print("任务规划的核心价值")
    print('='*70)
    print("""
1. 分而治之：复杂任务 → 简单子任务
2. 依赖管理：确保子任务按正确顺序执行
3. 可解释性：用户可以看到完整执行计划
4. 可扩展性：新工具只需要注册即可使用

规划 vs 不规划：

不规划：
  用户: "北京和上海哪个更热？"
  Agent: [随机调用一个工具] → 可能返回错误答案

有规划：
  用户: "北京和上海哪个更热？"
  Agent: [生成计划]
    1. 查询北京天气
    2. 查询上海天气
    3. 比较温度
  Agent: [按计划执行] → 返回正确答案

最佳实践：
✅ 对于复杂任务（需要多步骤、有依赖），使用规划
✅ 对于简单任务（单次工具调用），直接 Function Calling 即可
    """)


if __name__ == "__main__":
    main()

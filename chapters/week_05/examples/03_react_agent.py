#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：ReAct Agent — Reasoning + Acting 循环

本例演示 ReAct（Reasoning + Acting）模式的核心思想：
1. Thought：思考当前状态和下一步行动
2. Action：执行具体工具调用
3. Observation：观察工具返回的结果
4. 重复直到完成任务

运行方式：python3 chapters/week_05/examples/03_react_agent.py
预期输出：展示 Agent 如何通过多轮 Thought-Action-Observation 循环解决复杂问题

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
class Step:
    """单步执行记录"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    step_number: int = 0


@dataclass
class ReActResult:
    """ReAct 执行结果"""
    answer: str
    steps: List[Step] = field(default_factory=list)
    total_tokens_used: int = 0


# ============================================================
# 工具定义
# ============================================================

def search_knowledge_base(query: str) -> str:
    """搜索知识库（模拟）"""
    knowledge = {
        "GPU": "GPU计算资源需要通过内部工单系统申请，需填写使用时长、用途、所需型号等信息。",
        "远程办公": "远程办公需提前3天申请，每周最多2天，需主管审批。",
        "报销": "费用报销需在发生后30天内提交，发票需为公司抬头的正式发票。",
        "年假": "年假需提前7天申请，5天以下需主管审批，5天以上需部门经理审批。",
    }

    for key, value in knowledge.items():
        if key in query:
            return value
    return "未找到相关信息"


def lookup_policy(keyword: str) -> str:
    """查询具体政策（模拟）"""
    policies = {
        "GPU申请流程": "1.登录工单系统 2.选择GPU资源申请 3.填写使用计划 4.等待审批",
        "远程办公审批": "需要直属主管审批，系统会自动发邮件给主管",
        "报销时限": "费用发生后30天内，超过时限不予报销",
    }
    return policies.get(keyword, "该政策暂时未收录")


def ask_human(question: str) -> str:
    """询问人类（模拟）"""
    return f"人工回复：关于'{question}'的问题，建议联系HR部门获取最新信息。"


# ============================================================
# ReAct Agent 实现
# ============================================================

class ReActAgent:
    """
    ReAct Agent：通过 Thought-Action-Observation 循环解决问题

    核心思想：
    - Agent 不只是一次性调用工具，而是持续思考和行动
    - 每一步都有明确的 Thought（为什么这么做）
    - 可以根据 Observation 调整策略
    """

    def __init__(self, tools: dict[str, Callable], llm: OpenAI | None = None):
        self.tools = tools
        self.llm = llm or OpenAI()
        self.max_steps = 10  # 防止无限循环

    def run(self, task: str, verbose: bool = True) -> ReActResult:
        """
        执行 ReAct 循环

        Args:
            task: 用户任务描述
            verbose: 是否打印详细过程

        Returns:
            ReActResult 包含最终答案和完整执行轨迹
        """
        steps: List[Step] = []
        history: List[Dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": task},
        ]

        for step_num in range(1, self.max_steps + 1):
            if verbose:
                print(f"\n{'='*60}")
                print(f"步骤 {step_num}")
                print('='*60)

            # 1. Thought + Action 决策
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=history,
                temperature=0,
            )

            response_text = response.choices[0].message.content
            thought, action, action_input = self._parse_response(response_text)

            current_step = Step(
                thought=thought,
                action=action,
                action_input=action_input,
                step_number=step_num
            )

            if verbose:
                print(f"Thought: {thought}")
                if action:
                    print(f"Action: {action}")
                    if action_input:
                        print(f"Input: {json.dumps(action_input, ensure_ascii=False)}")

            # 2. 检查是否完成
            if action == "FINISH":
                current_step.observation = action_input.get("answer", "")
                steps.append(current_step)
                if verbose:
                    print(f"\n✅ 任务完成！")
                    print(f"最终答案: {current_step.observation}")
                return ReActResult(answer=current_step.observation, steps=steps)

            # 3. 执行 Action
            if action and action in self.tools:
                try:
                    observation = self.tools[action](**action_input)
                except Exception as e:
                    observation = f"执行错误: {e}"
            else:
                observation = f"未知操作: {action}"

            current_step.observation = observation
            steps.append(current_step)

            if verbose:
                print(f"Observation: {observation}")

            # 4. 将结果加入历史
            history.append({
                "role": "assistant",
                "content": f"Thought: {thought}\nAction: {action}\nAction Input: {json.dumps(action_input, ensure_ascii=False)}",
            })
            history.append({
                "role": "user",
                "content": f"Observation: {observation}",
            })

        # 超过最大步数
        return ReActResult(
            answer="执行超时，未能完成目标任务",
            steps=steps
        )

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_desc = "\n".join([
            f"- {name}: {func.__doc__ or 'No description'}"
            for name, func in self.tools.items()
        ])

        return f"""你是一个智能助手，通过思考和行动来解决用户的问题。

可用工具：
{tools_desc}

响应格式（必须严格遵守）：
Thought: [你的思考过程，分析当前状态和下一步计划]
Action: [工具名称，可选值：{', '.join(self.tools.keys())}, 或 FINISH]
Action Input: [工具参数，JSON 格式]

示例：
Thought: 用户问GPU申请流程，我需要先搜索知识库
Action: search_knowledge_base
Action Input: {{"query": "GPU申请"}}

Thought: 知识库返回了概要信息，但用户可能需要详细流程，我应该继续查询具体政策
Action: lookup_policy
Action Input: {{"keyword": "GPU申请流程"}}

Thought: 我已经收集到足够信息，可以给出完整答案
Action: FINISH
Action Input: {{"answer": "根据知识库，GPU申请需要..."}}

注意事项：
1. 每次只执行一个操作
2. Thought 要清晰说明为什么选择这个操作
3. 如果信息不足，继续搜索；如果已足够，使用 FINISH
4. Action Input 必须是合法的 JSON 格式
"""

    def _parse_response(self, response: str) -> tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        解析 LLM 响应

        返回: (thought, action, action_input)
        """
        lines = response.strip().split('\n')
        thought = ""
        action = None
        action_input = None

        for line in lines:
            if line.startswith("Thought:"):
                thought = line[8:].strip()
            elif line.startswith("Action:"):
                action = line[7:].strip()
            elif line.startswith("Action Input:"):
                try:
                    action_input = json.loads(line[13:].strip())
                except json.JSONDecodeError:
                    action_input = {"raw": line[13:].strip()}

        return thought, action, action_input


# ============================================================
# 反例：非 ReAct 的糟糕实现
# ============================================================

def bad_implementation_example():
    """
    反例：没有 Thought 的盲目执行

    常见错误：
    1. Agent 没有思考过程，直接执行
    2. 无法根据观察结果调整策略
    3. 容易陷入死循环
    """

    class BlindAgent:
        """❌ 盲目执行的 Agent（不推荐）"""

        def __init__(self, tools: dict[str, Callable]):
            self.tools = tools

        def run(self, task: str) -> str:
            # 问题1: 没有思考，直接按固定顺序执行
            for tool_name in self.tools:
                result = self.tools[tool_name](task)
                # 问题2: 无法判断是否已经找到答案
                # 问题3: 可能执行不必要的工具调用
            return "执行完成"

    print("❌ 错误做法示例：")
    print("BlindAgent 会按固定顺序执行所有工具，无法根据结果调整策略")


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    print("=" * 70)
    print("ReAct Agent 演示")
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

    # 定义工具
    tools = {
        "search_knowledge_base": search_knowledge_base,
        "lookup_policy": lookup_policy,
        "ask_human": ask_human,
    }

    if demo_mode:
        # 模拟模式：展示 ReAct 的执行流程
        print("\n【模拟演示】ReAct 执行流程")
        print("-" * 70)

        task = "我想申请GPU资源用于深度学习训练，请问具体流程是什么？"
        print(f"\n用户任务: {task}")

        simulated_steps = [
            Step(
                thought="用户询问GPU申请流程，我需要先搜索知识库获取概要信息",
                action="search_knowledge_base",
                action_input={"query": "GPU"},
                observation="GPU计算资源需要通过内部工单系统申请，需填写使用时长、用途、所需型号等信息。",
                step_number=1
            ),
            Step(
                thought="知识库返回了概要，但用户需要具体流程，我应该查询详细政策",
                action="lookup_policy",
                action_input={"keyword": "GPU申请流程"},
                observation="1.登录工单系统 2.选择GPU资源申请 3.填写使用计划 4.等待审批",
                step_number=2
            ),
            Step(
                thought="我已经收集到完整信息，可以给用户提供详细的申请流程",
                action="FINISH",
                action_input={"answer": "GPU资源申请流程如下：\n1. 登录内部工单系统\n2. 选择'GPU资源申请'类型\n3. 填写使用计划（使用时长、用途、所需型号）\n4. 提交后等待审批\n\n注意事项：请提前规划好使用时间，避免资源浪费。"},
                step_number=3
            ),
        ]

        for step in simulated_steps:
            print(f"\n[步骤 {step.step_number}]")
            print(f"  Thought: {step.thought}")
            if step.action:
                print(f"  Action: {step.action}")
            if step.action_input:
                print(f"  Input: {json.dumps(step.action_input, ensure_ascii=False)}")
            if step.observation:
                print(f"  Observation: {step.observation}")

    else:
        # 真实模式：调用 OpenAI API
        agent = ReActAgent(tools)

        test_tasks = [
            "我想申请GPU资源用于深度学习训练，请问具体流程是什么？",
            "我想明天远程办公，需要怎么申请？",
        ]

        for task in test_tasks:
            print(f"\n{'='*70}")
            print(f"任务: {task}")
            print('='*70)

            try:
                result = agent.run(task, verbose=True)
                print(f"\n{'='*70}")
                print("执行摘要")
                print('='*70)
                print(f"总步数: {len(result.steps)}")
                print(f"最终答案: {result.answer}")
            except Exception as e:
                print(f"\n错误: {e}")

    # 对比说明
    print("\n" + "=" * 70)
    print("ReAct 模式的优势")
    print("=" * 70)
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 传统 Function Calling          │  ReAct 模式                    │
├─────────────────────────────────────────────────────────────────┤
│ 一次性决策                       │  多轮迭代思考                   │
│ 无法根据结果调整                 │  可基于观察调整策略              │
│ 只能解决简单任务                 │  可处理复杂多步骤任务            │
│ "输入→输出"                     │  "思考→行动→观察→思考..."        │
└─────────────────────────────────────────────────────────────────┘

ReAct 的关键价值：
1. 可解释性：每一步都有清晰的 Thought
2. 灵活性：可根据 Observation 调整策略
3. 鲁棒性：工具调用失败可以尝试其他方案
4. 适应性：可以处理未见过的复杂任务

适用场景：
✅ 需要多轮推理的任务（如数学证明、代码调试）
✅ 信息不确定需要逐步验证的任务
✅ 需要尝试多种方案的探索性任务

❌ 简单的问答任务（直接 Function Calling 更高效）
    """)


if __name__ == "__main__":
    main()

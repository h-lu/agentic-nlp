#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 05 作业参考实现

本文件是 Week 05 作业的参考解决方案。
当你在作业中遇到困难时，可以参考此实现，
但建议自己先尝试完成作业。

作业要求：
1. 实现一个简单的 Agent，能够调用工具完成任务
2. 实现 Function Calling 的基础流程
3. 实现 ReAct 循环（至少2轮）

参考实现包含：
- 基础 Agent 类
- 工具定义和注册机制
- Function Calling 流程
- 简单的 ReAct 循环
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from openai import OpenAI


# ============================================================
# 工具定义
# ============================================================

def get_weather(city: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    获取天气信息（模拟）

    Args:
        city: 城市名称
        unit: 温度单位 (celsius/fahrenheit)

    Returns:
        天气信息字典
    """
    mock_data = {
        "北京": {"temp": 22, "condition": "晴"},
        "上海": {"temp": 26, "condition": "多云"},
        "深圳": {"temp": 30, "condition": "阵雨"},
    }

    data = mock_data.get(city, {"temp": 20, "condition": "未知"})

    if unit == "fahrenheit":
        data["temp"] = data["temp"] * 9/5 + 32

    return {
        "city": city,
        "temperature": data["temp"],
        "unit": unit,
        "condition": data["condition"],
    }


def calculate(expression: str) -> Dict[str, Any]:
    """
    计算数学表达式（简化版，仅用于演示）

    注意：生产环境应使用更安全的计算方式
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


def search_database(query: str) -> str:
    """
    搜索数据库（模拟）

    Args:
        query: 搜索关键词

    Returns:
        搜索结果
    """
    mock_db = {
        "GPU": "GPU资源需要通过工单系统申请",
        "远程": "远程办公需提前3天申请",
        "报销": "报销需在30天内提交发票",
    }

    for key, value in mock_db.items():
        if key in query:
            return value

    return "未找到相关信息"


# ============================================================
# 工具 Schema 定义
# ============================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位",
                    },
                },
                "required": ["city"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如'2+2'",
                    },
                },
                "required": ["expression"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "搜索数据库获取信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                },
                "required": ["query"],
            },
        }
    },
]

# 工具名称到函数的映射
AVAILABLE_FUNCTIONS: Dict[str, Callable] = {
    "get_weather": get_weather,
    "calculate": calculate,
    "search_database": search_database,
}


# ============================================================
# 简单 Agent 实现（作业要求1）
# ============================================================

class SimpleAgent:
    """
    简单的 Agent 实现

    功能：
    1. 注册工具
    2. 处理用户消息
    3. 根据意图调用工具
    4. 返回结果
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Agent

        Args:
            api_key: OpenAI API Key，如果不提供则从环境变量读取
        """
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.tools: Dict[str, Callable] = {}
        self.tool_history: List[Dict[str, Any]] = []

        # 注册默认工具
        for name, func in AVAILABLE_FUNCTIONS.items():
            self.register_tool(name, func)

    def register_tool(self, name: str, func: Callable) -> None:
        """
        注册新工具

        Args:
            name: 工具名称
            func: 工具函数
        """
        self.tools[name] = func

    def run(self, user_message: str, model: str = "gpt-4o-mini") -> str:
        """
        运行 Agent

        Args:
            user_message: 用户消息
            model: 使用的 LLM 模型

        Returns:
            Agent 的回复
        """
        messages = [{"role": "user", "content": user_message}]

        # 构建工具 Schema
        tools_schema = self._build_tools_schema()

        # 调用 LLM
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools_schema,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # 如果没有工具调用，直接返回
        if not tool_calls:
            return response_message.content or "抱歉，我没有理解您的问题。"

        # 执行工具调用
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # 执行函数
            if function_name in self.tools:
                result = self.tools[function_name](**function_args)

                # 记录历史
                self.tool_history.append({
                    "tool": function_name,
                    "args": function_args,
                    "result": result,
                })

                # 添加工具结果到消息
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        # 生成最终回复
        final_response = self.client.chat.completions.create(
            model=model,
            messages=messages,
        )

        return final_response.choices[0].message.content

    def _build_tools_schema(self) -> List[Dict]:
        """构建工具 Schema"""
        return TOOLS_SCHEMA

    def get_history(self) -> List[Dict[str, Any]]:
        """获取工具调用历史"""
        return self.tool_history


# ============================================================
# ReAct Agent 实现（作业要求2和3）
# ============================================================

@dataclass
class ReActStep:
    """ReAct 执行步骤"""
    step: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[Any] = None


class ReActAgent:
    """
    ReAct Agent 实现

    实现 Thought-Action-Observation 循环
    """

    def __init__(
        self,
        tools: Dict[str, Callable],
        max_steps: int = 5
    ):
        """
        初始化 ReAct Agent

        Args:
            tools: 可用工具字典
            max_steps: 最大执行步数
        """
        self.tools = tools
        self.max_steps = max_steps
        self.client = OpenAI()
        self.steps: List[ReActStep] = []

    def run(self, task: str, verbose: bool = True) -> str:
        """
        执行 ReAct 循环

        Args:
            task: 用户任务
            verbose: 是否打印详细过程

        Returns:
            最终答案
        """
        self.steps = []

        # 构建系统提示
        system_prompt = self._build_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]

        for step_num in range(1, self.max_steps + 1):
            if verbose:
                print(f"\n[步骤 {step_num}]")

            # 调用 LLM 获取 Thought 和 Action
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0,
            )

            response_text = response.choices[0].message.content

            # 解析响应
            thought, action, action_input = self._parse_response(response_text)

            current_step = ReActStep(
                step=step_num,
                thought=thought,
                action=action,
                action_input=action_input,
            )

            if verbose:
                print(f"Thought: {thought}")
                if action:
                    print(f"Action: {action}")
                    if action_input:
                        print(f"Input: {json.dumps(action_input, ensure_ascii=False)}")

            # 检查是否完成
            if action == "FINISH":
                current_step.observation = action_input.get("answer", "") if action_input else ""
                self.steps.append(current_step)
                if verbose:
                    print(f"\n完成: {current_step.observation}")
                return current_step.observation or "任务完成"

            # 执行 Action
            if action and action in self.tools:
                try:
                    observation = self.tools[action](**action_input)
                except Exception as e:
                    observation = f"执行错误: {e}"
            else:
                observation = f"未知操作: {action}"

            current_step.observation = observation
            self.steps.append(current_step)

            if verbose:
                print(f"Observation: {observation}")

            # 添加到消息历史
            messages.append({
                "role": "assistant",
                "content": f"Thought: {thought}\nAction: {action}\nAction Input: {json.dumps(action_input, ensure_ascii=False) if action_input else ''}",
            })
            messages.append({
                "role": "user",
                "content": f"Observation: {observation}",
            })

        return "执行超时，未能完成任务"

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        tools_list = ", ".join(self.tools.keys())

        return f"""你是一个智能助手，通过思考和行动来解决问题。

可用工具: {tools_list}

响应格式：
Thought: [你的思考]
Action: [工具名称或FINISH]
Action Input: [JSON格式的参数]

示例：
Thought: 用户问天气，我需要查询
Action: get_weather
Action Input: {{"city": "北京"}}

Thought: 我已经获取到足够信息
Action: FINISH
Action Input: {{"answer": "北京今天晴天，22度"}}

注意：
1. Thought 要清晰说明你的思考过程
2. 只使用可用工具列表中的工具
3. 完成后使用 FINISH
"""

    def _parse_response(self, response: str) -> tuple[str, Optional[str], Optional[Dict]]:
        """
        解析 LLM 响应

        Returns:
            (thought, action, action_input)
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
# 主函数
# ============================================================

def main():
    """演示 Agent 的使用"""
    print("=" * 60)
    print("Week 05 作业参考实现演示")
    print("=" * 60)

    # 检查 API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n错误：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        return

    # 创建 Simple Agent
    print("\n[演示1] SimpleAgent - Function Calling")
    print("-" * 60)

    agent = SimpleAgent()

    test_queries = [
        "北京今天天气怎么样？",
        "帮我算一下 15 乘以 7 等于多少？",
        "怎么申请GPU资源？",
    ]

    for query in test_queries:
        print(f"\n用户: {query}")
        try:
            response = agent.run(query)
            print(f"Agent: {response}")
        except Exception as e:
            print(f"错误: {e}")

    # 创建 ReAct Agent
    print("\n" + "=" * 60)
    print("[演示2] ReActAgent - 多步推理")
    print("-" * 60)

    react_agent = ReActAgent(AVAILABLE_FUNCTIONS)

    # 复杂任务示例
    complex_task = "我想知道北京的天气，然后根据温度决定是否需要带伞"

    print(f"\n用户: {complex_task}")
    try:
        result = react_agent.run(complex_task, verbose=True)
        print(f"\n最终答案: {result}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

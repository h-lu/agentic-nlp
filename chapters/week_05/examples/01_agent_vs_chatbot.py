#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：Chatbot vs Agent — 展示两者的根本区别

本例演示 Chatbot 和 Agent 的核心差异：
- Chatbot：只能对话回答问题，被动响应用户输入
- Agent：能主动调用工具，执行多步骤任务完成目标

运行方式：python3 chapters/week_05/examples/01_agent_vs_chatbot.py
预期输出：
- Chatbot 场景：给出天气查询的建议，但无法真正查询
- Agent 场景：调用工具获取真实天气数据
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Callable
from dataclasses import dataclass


# 模拟的天气工具（不需要真实 API）
def get_weather(city: str) -> Dict[str, Any]:
    """模拟获取天气信息"""
    mock_data = {
        "北京": {"temp": 5, "condition": "晴", "humidity": 30},
        "上海": {"temp": 12, "condition": "多云", "humidity": 65},
        "深圳": {"temp": 22, "condition": "阴", "humidity": 80},
    }
    return mock_data.get(city, {"temp": 15, "condition": "未知", "humidity": 50})


# ============================================================
# ❌ Chatbot：只能对话，无法执行
# ============================================================

class SimpleChatbot:
    """简单的聊天机器人：只能生成文本回复"""

    def __init__(self, name: str = "小助手"):
        self.name = name

    def chat(self, user_message: str) -> str:
        """
        Chatbot 只能返回文本，无法真正执行操作

        常见错误：把 Chatbot 当成万能工具
        - 它不能联网查询
        - 它不能调用函数
        - 它甚至不知道"现在"是几点
        """
        if "天气" in user_message and "北京" in user_message:
            # Chatbot 只能给出"建议"，不能真正查询
            return f"我是{self.name}，我无法查询实时天气。建议您查看天气APP或网站。"
        return f"我是{self.name}，请问有什么可以帮助您？"


# ============================================================
# ✅ Agent：能调用工具，执行任务
# ============================================================

@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any


class SimpleAgent:
    """简单的 Agent：能分析意图并调用工具"""

    def __init__(self, name: str = "智能助手"):
        self.name = name
        self.tools: Dict[str, Callable] = {
            "get_weather": get_weather,
        }
        self.tool_calls: List[ToolCall] = []

    def run(self, user_message: str) -> str:
        """
        Agent 执行流程：
        1. 理解用户意图
        2. 决定是否需要调用工具
        3. 执行工具获取结果
        4. 基于结果生成回复
        """
        # 步骤1: 意图识别（简化版，实际会用 LLM）
        intent = self._parse_intent(user_message)

        # 步骤2: 决定是否调用工具
        if intent["action"] == "get_weather":
            city = intent.get("city", "北京")
            # 步骤3: 执行工具
            result = self._execute_tool("get_weather", {"city": city})
            # 步骤4: 生成回复
            return self._format_weather_response(city, result)
        else:
            return f"我是{self.name}，请问有什么可以帮助您？"

    def _parse_intent(self, message: str) -> Dict[str, Any]:
        """解析用户意图（简化版）"""
        if "天气" in message:
            for city in ["北京", "上海", "深圳"]:
                if city in message:
                    return {"action": "get_weather", "city": city}
            return {"action": "get_weather", "city": "北京"}
        return {"action": "unknown"}

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """执行工具调用"""
        if tool_name not in self.tools:
            raise ValueError(f"未知工具: {tool_name}")

        tool_func = self.tools[tool_name]
        result = tool_func(**args)

        # 记录调用日志
        self.tool_calls.append(ToolCall(
            tool_name=tool_name,
            arguments=args,
            result=result
        ))

        return result

    def _format_weather_response(self, city: str, weather: Dict) -> str:
        """格式化天气回复"""
        return (
            f"{city}当前天气：{weather['condition']}，"
            f"温度 {weather['temp']}°C，湿度 {weather['humidity']}%"
        )

    def get_tool_history(self) -> List[ToolCall]:
        """获取工具调用历史"""
        return self.tool_calls


# ============================================================
# 对比演示
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Chatbot vs Agent 对比演示")
    print("=" * 60)

    user_query = "北京今天天气怎么样？"

    # 场景1: Chatbot 回应
    print("\n【场景1】Chatbot 的回应")
    print("-" * 40)
    chatbot = SimpleChatbot("小北")
    response = chatbot.chat(user_query)
    print(f"用户: {user_query}")
    print(f"Chatbot: {response}")
    print("\n问题：Chatbot 只能'说'，不能'做'")

    # 场景2: Agent 执行
    print("\n【场景2】Agent 的执行")
    print("-" * 40)
    agent = SimpleAgent("阿码")
    response = agent.run(user_query)
    print(f"用户: {user_query}")
    print(f"Agent: {response}")
    print(f"\n工具调用历史：")
    for call in agent.get_tool_history():
        print(f"  - 调用 {call.tool_name}({call.arguments})")
        print(f"    结果: {call.result}")

    # 核心差异总结
    print("\n" + "=" * 60)
    print("核心差异总结")
    print("=" * 60)
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ Chatbot                      │  Agent                           │
├─────────────────────────────────────────────────────────────────┤
│ 被动响应                       │  主动执行                         │
│ 只生成文本                     │  调用工具                         │
│ 无法访问外部世界               │  可以获取实时数据                  │
│ 对话结束即停止                 │  会持续执行直到完成任务             │
│ "我会帮你"                     │  "我来做"                         │
└─────────────────────────────────────────────────────────────────┘
    """)

    # 反例说明
    print("\n常见错误示例")
    print("-" * 40)
    print("""
❌ 错误：期待 Chatbot 执行实际操作
   chatbot.chat("帮我发邮件给老板")  # Chatbot 只能说"建议您..."

✅ 正确：使用 Agent 执行实际操作
   agent.run("帮我发邮件给老板")  # Agent 会调用邮件工具发送
    """)


# ============================================================
# 反例：错误的 Agent 实现
# ============================================================

def bad_agent_example():
    """
    反例：没有工具调用的"假 Agent"

    常见错误：
    1. 用 if-else 硬编码所有逻辑
    2. 无法扩展新工具
    3. 不是真正的"智能体"，只是规则引擎
    """
    class BadAgent:
        """❌ 硬编码的 Agent（不推荐）"""

        def run(self, message: str) -> str:
            # 硬编码所有逻辑，无法扩展
            if "天气" in message and "北京" in message:
                return "北京今天晴天，5°C"
            elif "天气" in message and "上海" in message:
                return "上海今天多云，12°C"
            # ... 需要穷举所有情况
            return "我不明白"

    # 正确做法：使用工具注册机制
    class GoodAgent:
        """✅ 可扩展的 Agent（推荐）"""

        def __init__(self):
            self.tools = {}

        def register_tool(self, name: str, func: callable):
            """注册新工具"""
            self.tools[name] = func

        def run(self, message: str) -> str:
            # 根据意图动态调用工具
            # 可以轻松添加新工具
            pass


if __name__ == "__main__":
    main()

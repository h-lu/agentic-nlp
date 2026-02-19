#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：Function Calling（函数调用）基础

本例演示如何使用 OpenAI 的 Function Calling 功能：
1. 定义工具 Schema（JSON Schema）
2. 让 LLM 决定是否调用工具
3. 执行工具并反馈结果
4. 将工具结果返回给 LLM 生成最终回复

运行方式：python3 chapters/week_05/examples/02_function_calling.py
预期输出：展示 Function Calling 的完整流程，包括工具定义、LLM 决策、执行和回复生成

依赖：
- pip install openai
- export OPENAI_API_KEY="your-api-key"
"""

from __future__ import annotations

import os
import json
from typing import Any
from openai import OpenAI


# ============================================================
# 工具定义
# ============================================================

def get_current_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    获取指定位置的天气信息（模拟）

    Args:
        location: 城市名称，如 "北京" 或 "San Francisco, CA"
        unit: 温度单位，"celsius" 或 "fahrenheit"

    Returns:
        包含天气信息的字典
    """
    # 模拟天气数据
    weather_data = {
        "北京": {"temp": 22, "condition": "晴", "humidity": 45},
        "上海": {"temp": 25, "condition": "多云", "humidity": 70},
        "深圳": {"temp": 28, "condition": "阵雨", "humidity": 85},
        "San Francisco, CA": {"temp": 18, "condition": "Foggy", "humidity": 80},
        "New York, NY": {"temp": 15, "condition": "Sunny", "humidity": 55},
    }

    data = weather_data.get(location, {"temp": 20, "condition": "未知", "humidity": 50})

    # 温度单位转换
    if unit == "fahrenheit":
        data["temp"] = data["temp"] * 9/5 + 32

    return {
        "location": location,
        "temperature": data["temp"],
        "unit": unit,
        "condition": data["condition"],
        "humidity": data["humidity"],
    }


def calculate(expression: str) -> Dict[str, Any]:
    """
    安全计算数学表达式（仅演示）

    Args:
        expression: 数学表达式，如 "2 + 2" 或 "10 * 5"

    Returns:
        计算结果

    安全警告:
        eval() 即使限制 __builtins__ 仍有安全风险，不建议在生产环境使用。
        生产环境替代方案：
        1. numexpr 库 — 专门用于数学表达式计算
        2. simpleeval 库 — 安全的表达式求值器
        3. ast.literal_eval — 只支持字面量，不支持运算
        4. 自定义解析器 — 完全控制允许的操作
    """
    try:
        # ⚠️ 警告：此实现仅供教学演示，生产环境请使用上述替代方案
        result = eval(expression, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


# ============================================================
# 工具 Schema 定义（JSON Schema 格式）
# ============================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "获取指定位置的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如 '北京' 或 'San Francisco, CA'",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位",
                    },
                },
                "required": ["location"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式的值",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，如 '2 + 2' 或 '10 * 5'",
                    },
                },
                "required": ["expression"],
            },
        }
    }
]

# 工具名称到函数的映射
AVAILABLE_FUNCTIONS = {
    "get_current_weather": get_current_weather,
    "calculate": calculate,
}


# ============================================================
# Function Calling 核心流程
# ============================================================

class FunctionCallingAgent:
    """使用 Function Calling 的 Agent"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.tools = TOOLS_SCHEMA

    def run(self, user_message: str, model: str = "gpt-4o-mini") -> str:
        """
        执行 Function Calling 流程

        流程：
        1. 发送消息和工具 Schema 给 LLM
        2. LLM 决定是否调用工具
        3. 如果需要，执行工具并返回结果
        4. 将工具结果发回 LLM 生成最终回复
        """
        messages = [{"role": "user", "content": user_message}]

        # 步骤1: 第一次调用 LLM，看是否需要工具
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=self.tools,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # 步骤2: 如果没有工具调用，直接返回
        if not tool_calls:
            return response_message.content or "抱歉，我没有理解您的问题。"

        # 步骤3: 执行工具调用
        print(f"\n[Agent] 检测到 {len(tool_calls)} 个工具调用请求")

        messages.append(response_message)  # 添加助手的回复（包含 tool_calls）

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"  - 调用 {function_name}({function_args})")

            # 执行函数
            function_response = AVAILABLE_FUNCTIONS[function_name](**function_args)

            print(f"    结果: {function_response}")

            # 添加工具结果到消息历史
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_response, ensure_ascii=False),
            })

        # 步骤4: 让 LLM 基于工具结果生成最终回复
        print("\n[Agent] 基于工具结果生成回复...")

        final_response = self.client.chat.completions.create(
            model=model,
            messages=messages,
        )

        return final_response.choices[0].message.content


# ============================================================
# 反例：错误的做法
# ============================================================

def bad_practice_example():
    """
    反例：不使用 Function Calling 的错误做法

    常见错误：
    1. 让 LLM 直接输出 Python 代码然后执行（安全风险）
    2. 用正则表达式从文本中解析参数（不可靠）
    3. 手动实现意图分类（无法处理复杂表达）
    """

    import re

    def bad_weather_agent(user_message: str) -> str:
        """❌ 用正则表达式解析的脆弱实现"""

        # 问题1: 硬编码模式，无法应对各种表达方式
        if "天气" not in user_message:
            return "我只能回答天气问题"

        # 问题2: 正则匹配很脆弱
        city_match = re.search(r"(北京|上海|深圳)", user_message)
        if not city_match:
            return "请告诉我你想查询哪个城市的天气"

        city = city_match.group(1)
        weather = get_current_weather(city)

        # 问题3: 无法处理复杂请求（如比较、计算等）
        return f"{city}的天气是{weather['condition']}，温度{weather['temperature']}度"

    # 正确做法：使用 Function Calling
    print("❌ 错误做法示例：")
    print(bad_weather_agent("北京今天天气怎么样"))
    print(bad_weather_agent("Beijing weather"))  # 无法识别
    print(bad_weather_agent("北京冷还是上海冷"))  # 无法处理比较


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    print("=" * 70)
    print("Function Calling 完整流程演示")
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

    if demo_mode:
        # 模拟模式：展示 Function Calling 的流程
        print("\n【模拟演示】Function Calling 流程步骤")
        print("-" * 70)

        print("\n步骤1: 用户发送消息")
        user_message = "北京今天天气怎么样？"
        print(f"  用户: {user_message}")

        print("\n步骤2: LLM 分析并决定调用工具")
        print("  LLM: 我需要调用 get_current_weather 工具")
        print("  参数: {'location': '北京', 'unit': 'celsius'}")

        print("\n步骤3: Agent 执行工具")
        result = get_current_weather("北京", "celsius")
        print(f"  工具返回: {result}")

        print("\n步骤4: LLM 基于工具结果生成回复")
        print("  Agent: 北京今天天气晴朗，温度 22°C，湿度 45%")

        print("\n" + "=" * 70)
        print("关键要点：")
        print("1. LLM 不执行代码，只输出'调用哪个工具'的指令")
        print("2. Agent 执行工具，保证安全性和可控性")
        print("3. 工具结果返回给 LLM，生成自然语言回复")

    else:
        # 真实模式：调用 OpenAI API
        agent = FunctionCallingAgent()

        test_queries = [
            "北京今天天气怎么样？",
            "帮我算一下 25 乘以 4 等于多少？",
            "上海比北京热吗？",  # 需要两次工具调用
        ]

        for query in test_queries:
            print("\n" + "=" * 70)
            print(f"用户: {query}")
            print("-" * 70)

            try:
                response = agent.run(query)
                print(f"\nAgent: {response}")
            except Exception as e:
                print(f"\n错误: {e}")

    # 反例说明
    print("\n" + "=" * 70)
    print("常见错误与最佳实践")
    print("=" * 70)
    print("""
❌ 错误做法：
1. 让 LLM 直接输出可执行代码然后用 eval() 执行（安全风险）
2. 用正则表达式从 LLM 输出中解析参数（脆弱且不可靠）
3. 手动实现意图分类器（无法处理复杂表达）

✅ 正确做法：
1. 使用 Function Calling API（安全、可靠、标准）
2. 用 JSON Schema 清晰定义工具接口
3. 让 LLM 决定何时调用哪个工具
4. Agent 执行工具后，将结果返回给 LLM 生成回复

工具设计原则：
- 每个工具只做一件事（单一职责）
- 参数名和描述要清晰（LLM 会据此决定是否调用）
- 提供 description 而不是依赖参数名自解释
    """)


if __name__ == "__main__":
    main()

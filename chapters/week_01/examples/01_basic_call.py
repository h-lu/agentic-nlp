#!/usr/bin/env python3
"""
01_basic_call.py - 最小可运行的 LLM API 调用示例

本示例展示如何使用 OpenAI SDK 进行最基本的 LLM API 调用：
- 初始化 OpenAI 客户端
- 使用 messages 参数（system, user）
- 基本的错误处理

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."

或使用 .env 文件配合 python-dotenv：
    OPENAI_API_KEY=sk-...
"""

import os
import sys
from openai import OpenAI, APIError, RateLimitError, AuthenticationError


def basic_call() -> str:
    """
    执行一次最基本的 LLM API 调用。

    Returns:
        模型生成的文本回复

    Raises:
        ValueError: API Key 未设置
        AuthenticationError: 认证失败
        RateLimitError: 请求被限流
        APIError: 其他 API 错误
    """
    # 初始化客户端
    # OpenAI() 会自动从环境变量 OPENAI_API_KEY 读取 API Key
    # 也可以显式传入：OpenAI(api_key="sk-...")
    client = OpenAI()

    # 发起一次 Chat Completions API 调用
    completion = client.chat.completions.create(
        model="gpt-4o",  # 使用 gpt-4o 模型
        messages=[
            # system 消息：设定 LLM 的角色和行为边界
            {
                "role": "system",
                "content": "你是一个新闻分类助手。请判断新闻属于哪个类别。"
            },
            # user 消息：具体的任务输入
            {
                "role": "user",
                "content": "今天沪指大涨 3%，创下半年新高。这条新闻属于什么类别？只输出类别名称。"
            },
        ],
        temperature=0,  # temperature=0 使输出几乎确定，适合分类任务
    )

    # 从响应中提取生成的文本
    # completion.choices 是一个列表，通常只有一个元素
    # .message.content 是模型生成的文本
    return completion.choices[0].message.content


def call_with_error_handling() -> str | None:
    """
    带完整错误处理的 LLM API 调用示例。

    API 调用可能遇到多种错误，需要进行适当的处理：
    - AuthenticationError: API Key 无效或未设置
    - RateLimitError: 请求频率超过限制
    - APIError: 服务器端错误

    Returns:
        模型生成的文本，失败时返回 None
    """
    client = OpenAI()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "你好，请简单介绍一下你自己。"}
            ]
        )
        return completion.choices[0].message.content

    except AuthenticationError as e:
        # 认证失败：检查 API Key 是否正确设置
        print(f"[错误] 认证失败，请检查 API Key：{e}")
        return None

    except RateLimitError as e:
        # 限流：请求太快，需要等待后重试
        print(f"[错误] 请求被限流，请稍后重试：{e}")
        return None

    except APIError as e:
        # API 服务器错误：查看状态码和错误信息
        print(f"[错误] API 服务器错误：{e.status_code} - {e.message}")
        return None

    except Exception as e:
        # 其他未知错误
        print(f"[错误] 未知错误：{e}")
        return None


def check_api_key() -> bool:
    """
    检查 API Key 是否已正确设置。

    Returns:
        True 如果 API Key 已设置，False 否则
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[提示] API Key 未设置。请使用以下方式之一设置：")
        print("  1. 环境变量：export OPENAI_API_KEY='sk-...'")
        print("  2. .env 文件：创建 .env 文件并添加 OPENAI_API_KEY=sk-...")
        return False

    # 检查 API Key 格式（以 sk- 开头）
    if not api_key.startswith("sk-"):
        print("[警告] API Key 格式可能不正确，通常以 'sk-' 开头")
        return False

    return True


def main() -> None:
    """主函数：演示基本的 LLM API 调用"""
    print("=" * 60)
    print("示例 1：最基本的 LLM API 调用")
    print("=" * 60)

    # 检查 API Key
    if not check_api_key():
        sys.exit(1)

    print("\n正在调用 LLM API...")

    try:
        result = basic_call()
        print(f"\n[模型回复] {result}")

        # 展示响应的元信息
        print("\n" + "-" * 40)
        print("响应详情：")

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": "1+1=?"}
            ],
            temperature=0,
        )

        print(f"  - 模型：{completion.model}")
        print(f"  - 输入 Token 数：{completion.usage.prompt_tokens}")
        print(f"  - 输出 Token 数：{completion.usage.completion_tokens}")
        print(f"  - 总 Token 数：{completion.usage.total_tokens}")

    except Exception as e:
        print(f"\n[错误] 调用失败：{e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("示例 2：带错误处理的调用")
    print("=" * 60)

    result = call_with_error_handling()
    if result:
        print(f"\n[模型回复] {result}")


if __name__ == "__main__":
    main()

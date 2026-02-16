#!/usr/bin/env python3
"""
05_client_class.py - LLM Client 类封装

本示例展示如何封装一个统一的 LLM Client 类：
- 支持多后端（OpenAI、智谱、DeepSeek 等）
- 统一错误处理
- 日志记录
- Token 消耗统计

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
    # 可选：其他 LLM 服务的 API Key
    export ZHIPU_API_KEY="..."
    export DEEPSEEK_API_KEY="..."
"""

import os
import logging
from typing import Optional
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMClient:
    """
    统一的 LLM API 客户端封装。

    支持多后端切换、统一错误处理、日志记录和 Token 消耗统计。

    Example:
        >>> client = LLMClient(model="gpt-4o")
        >>> response = client.call("你好，请介绍一下你自己")
        >>> print(response)
    """

    # 预设的 LLM 后端配置
    BACKEND_CONFIGS = {
        "openai": {
            "base_url": None,  # 使用 OpenAI 默认地址
            "default_model": "gpt-4o",
        },
        "zhipu": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4/",
            "default_model": "glm-4",
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat",
        },
        "moonshot": {
            "base_url": "https://api.moonshot.cn/v1",
            "default_model": "moonshot-v1-8k",
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        default_temperature: float = 0,
        backend: Optional[str] = None,
    ):
        """
        初始化 LLM 客户端。

        Args:
            api_key: API Key，如果不传则从环境变量读取
            base_url: API 地址，用于切换到其他兼容 OpenAI 接口的服务
            model: 默认使用的模型
            default_temperature: 默认温度
            backend: 预设后端名称（"openai"/"zhipu"/"deepseek"/"moonshot"）
                    如果指定，会使用预设的 base_url 和 default_model

        Raises:
            ValueError: API Key 未设置
        """
        # 处理预设后端
        if backend and backend in self.BACKEND_CONFIGS:
            config = self.BACKEND_CONFIGS[backend]
            base_url = base_url or config["base_url"]
            model = model if model != "gpt-4o" else config["default_model"]
            # 根据后端选择对应的环境变量
            env_key_map = {
                "openai": "OPENAI_API_KEY",
                "zhipu": "ZHIPU_API_KEY",
                "deepseek": "DEEPSEEK_API_KEY",
                "moonshot": "MOONSHOT_API_KEY",
            }
            api_key = api_key or os.getenv(env_key_map.get(backend, "OPENAI_API_KEY"))

        # 获取 API Key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key 未设置，请通过以下方式之一提供：\n"
                "1. 传入 api_key 参数\n"
                "2. 设置 OPENAI_API_KEY 环境变量"
            )

        # 初始化 OpenAI 客户端（兼容 OpenAI 接口的服务）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

        # 保存配置
        self.model = model
        self.default_temperature = default_temperature
        self.base_url = base_url

        # 统计信息
        self.total_tokens = 0
        self.total_calls = 0
        self.total_errors = 0

        logger.info(f"LLM Client 初始化完成：model={model}, base_url={base_url or 'default'}")

    def call(
        self,
        user_message: str,
        system_message: str = "你是一个有帮助的助手。",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        发起一次 LLM 调用。

        Args:
            user_message: 用户输入
            system_message: 系统设定
            temperature: 温度，不传则使用默认值
            max_tokens: 最大输出 Token 数

        Returns:
            模型输出的文本

        Raises:
            AuthenticationError: 认证失败
            RateLimitError: 请求被限流
            APIError: 其他 API 错误
        """
        temp = temperature if temperature is not None else self.default_temperature
        self.total_calls += 1

        try:
            logger.debug(f"调用 LLM: model={self.model}, temperature={temp}")
            logger.debug(f"System: {system_message[:50]}...")
            logger.debug(f"User: {user_message[:50]}...")

            # 构建请求参数
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                "temperature": temp,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            # 发起调用
            completion = self.client.chat.completions.create(**params)

            # 提取结果
            result = completion.choices[0].message.content or ""
            usage = completion.usage

            # 更新统计
            if usage:
                self.total_tokens += usage.total_tokens

            logger.info(
                f"调用成功: 输入 {usage.prompt_tokens if usage else '?'} tokens, "
                f"输出 {usage.completion_tokens if usage else '?'} tokens"
            )

            return result

        except AuthenticationError as e:
            self.total_errors += 1
            logger.error(f"认证失败: {e}")
            raise

        except RateLimitError as e:
            self.total_errors += 1
            logger.error(f"请求被限流: {e}")
            raise

        except APIError as e:
            self.total_errors += 1
            logger.error(f"API 错误: {e.status_code} - {e.message}")
            raise

        except Exception as e:
            self.total_errors += 1
            logger.error(f"未知错误: {e}")
            raise

    def classify(self, text: str, categories: list[str]) -> str:
        """
        文本分类的便捷方法。

        Args:
            text: 需要分类的文本
            categories: 分类类别列表

        Returns:
            分类结果
        """
        system = (
            f"你是一个分类助手。请将文本分类到以下类别之一：{', '.join(categories)}。"
            f"只输出类别名称，不要解释。"
        )
        return self.call(text, system)

    def summarize(self, text: str, max_words: int = 100) -> str:
        """
        文本摘要的便捷方法。

        Args:
            text: 需要摘要的文本
            max_words: 摘要的最大字数

        Returns:
            摘要文本
        """
        system = (
            f"你是一个摘要助手。请将文本压缩成 {max_words} 字以内的摘要，"
            f"保留关键信息：谁、什么事、多少、变化趋势。"
        )
        return self.call(text, system)

    def extract(self, text: str, entity_types: list[str]) -> str:
        """
        实体抽取的便捷方法。

        Args:
            text: 需要抽取实体的文本
            entity_types: 实体类型列表

        Returns:
            JSON 格式的实体抽取结果
        """
        system = f"""你是一个实体抽取助手。请从文本中抽取以下类型的实体：{', '.join(entity_types)}。
以 JSON 格式输出，格式为 {{"实体类型": ["实体1", "实体2"]}}。
如果某类实体不存在，输出空列表。只输出 JSON，不要其他内容。"""
        return self.call(text, system)

    def get_stats(self) -> dict:
        """
        获取调用统计信息。

        Returns:
            包含 total_calls、total_tokens、total_errors 的字典
        """
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
        }

    def reset_stats(self) -> None:
        """重置统计信息。"""
        self.total_calls = 0
        self.total_tokens = 0
        self.total_errors = 0
        logger.info("统计信息已重置")


def demo_openai_client() -> None:
    """演示 OpenAI 客户端的使用"""
    print("=" * 60)
    print("示例 1：OpenAI 客户端")
    print("=" * 60)

    client = LLMClient(model="gpt-4o", default_temperature=0)

    # 分类任务
    news = "苹果公司发布新款 iPhone，搭载 A18 芯片，性能提升 30%"
    category = client.classify(news, ["财经", "科技", "体育", "娱乐"])
    print(f"\n分类结果：{category}")

    # 摘要任务
    long_text = """
    北京时间 2 月 15 日凌晨，苹果公司发布了 2025 财年第一季度财报。
    财报显示，公司当季营收达到 1243 亿美元，同比增长 4%。
    iPhone 业务贡献了 697 亿美元收入，超出分析师预期。
    """
    summary = client.summarize(long_text, max_words=50)
    print(f"摘要：{summary}")

    # 统计信息
    stats = client.get_stats()
    print(f"\n调用统计：{stats}")


def demo_multi_backend() -> None:
    """演示多后端切换"""
    print("\n" + "=" * 60)
    print("示例 2：多后端切换")
    print("=" * 60)

    # 使用预设后端配置
    backends = ["openai"]  # 可以添加 "zhipu", "deepseek" 等

    for backend in backends:
        api_key = os.getenv(f"{backend.upper()}_API_KEY") or os.getenv("OPENAI_API_KEY")

        if not api_key:
            print(f"\n跳过 {backend}：未设置 API Key")
            continue

        try:
            client = LLMClient(backend=backend, api_key=api_key)
            response = client.call("1+1=?")
            print(f"\n{backend} 响应：{response}")
        except Exception as e:
            print(f"\n{backend} 调用失败：{e}")


def demo_error_handling() -> None:
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("示例 3：错误处理")
    print("=" * 60)

    # 使用错误的 API Key 演示认证错误
    try:
        client = LLMClient(api_key="invalid-key")
        client.call("Hello")
    except AuthenticationError as e:
        print(f"\n捕获到认证错误（预期行为）：{type(e).__name__}")

    # 正常客户端的错误处理
    client = LLMClient()

    try:
        # 调用可能触发限流的请求（演示用）
        for i in range(3):
            client.call(f"测试请求 {i + 1}")
    except RateLimitError as e:
        print(f"\n捕获到限流错误：{type(e).__name__}")
    except Exception as e:
        print(f"\n其他错误：{type(e).__name__}: {e}")

    print(f"\n错误统计：{client.get_stats()}")


def main() -> None:
    """主函数：演示 LLM Client 类的各种功能"""
    print("=" * 60)
    print("LLM Client 类演示")
    print("=" * 60)

    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[错误] 请先设置 OPENAI_API_KEY 环境变量")
        print("示例：export OPENAI_API_KEY='sk-...'")
        return

    # OpenAI 客户端演示
    demo_openai_client()

    # 多后端演示
    demo_multi_backend()

    # 错误处理演示（注释掉以避免不必要的 API 调用）
    # demo_error_handling()


if __name__ == "__main__":
    main()

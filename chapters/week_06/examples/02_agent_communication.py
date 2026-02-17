#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：Agent 间通信（Agent Communication）

本例演示多个 Agent 之间如何传递消息和共享状态。

核心概念：
- 消息传递（Message Passing）：Agent 之间通过结构化消息通信
- 共享状态（Shared State）：Agent 可以访问和修改共享的状态
- 消息队列（Message Queue）：用于存储和传递消息

运行方式：python3 chapters/week_06/examples/02_agent_communication.py
预期输出：展示 Agent 之间如何协作完成复杂任务

依赖：
- pip install openai
- export OPENAI_API_KEY="your-api-key"
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from openai import OpenAI


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Message:
    """Agent 之间的消息"""
    sender: str  # 发送者 Agent 名称
    receiver: str  # 接收者 Agent 名称（或 "broadcast"）
    content: Dict[str, Any]  # 消息内容
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    msg_id: str = field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")


@dataclass
class SharedState:
    """Agent 之间的共享状态"""
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# 消息总线
# ============================================================

class MessageBus:
    """
    消息总线：负责 Agent 之间的消息传递

    职责：
    - 存储和传递消息
    - 路由消息到正确的接收者
    - 维护消息历史
    """

    def __init__(self):
        self.messages: deque[Message] = deque()
        self.subscribers: Dict[str, List[str]] = {}  # agent -> list of topics

    def send(self, message: Message) -> None:
        """发送消息"""
        self.messages.append(message)
        print(f"[消息总线] {message.sender} -> {message.receiver}: {message.content.get('type', 'unknown')}")

    def receive(self, receiver: str) -> List[Message]:
        """接收发给该 Agent 的所有消息"""
        received = []
        remaining = deque()

        for msg in self.messages:
            if msg.receiver == receiver or msg.receiver == "broadcast":
                received.append(msg)
            else:
                remaining.append(msg)

        self.messages = remaining
        return received

    def broadcast(self, sender: str, content: Dict[str, Any]) -> None:
        """广播消息给所有 Agent"""
        msg = Message(sender=sender, receiver="broadcast", content=content)
        self.send(msg)

    def get_history(self, agent: Optional[str] = None) -> List[Message]:
        """获取消息历史"""
        if agent is None:
            return list(self.messages)
        return [msg for msg in self.messages if msg.sender == agent or msg.receiver == agent]


# ============================================================
# 基础 Agent 类
# ============================================================

class BaseAgent:
    """
    基础 Agent 类：所有 Agent 的基类

    提供：
    - 消息发送和接收能力
    - 共享状态访问
    - 基础的生命周期方法
    """

    def __init__(
        self,
        name: str,
        message_bus: MessageBus,
        shared_state: SharedState,
        llm_client: Optional[OpenAI] = None
    ):
        self.name = name
        self.message_bus = message_bus
        self.shared_state = shared_state
        self.llm = llm_client

    def send_message(self, receiver: str, content: Dict[str, Any]) -> None:
        """发送消息给其他 Agent"""
        msg = Message(sender=self.name, receiver=receiver, content=content)
        self.message_bus.send(msg)

    def broadcast_message(self, content: Dict[str, Any]) -> None:
        """广播消息"""
        self.message_bus.broadcast(self.name, content)

    def receive_messages(self) -> List[Message]:
        """接收发给自己的消息"""
        return self.message_bus.receive(self.name)

    def update_state(self, key: str, value: Any) -> None:
        """更新共享状态"""
        self.shared_state.context[key] = value
        print(f"[{self.name}] 更新状态: {key} = {value}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """获取共享状态"""
        return self.shared_state.context.get(key, default)

    def run(self) -> None:
        """运行 Agent（子类实现）"""
        raise NotImplementedError


# ============================================================
# 具体 Agent 实现
# ============================================================

class CoordinatorAgent(BaseAgent):
    """
    协调者 Agent：负责任务分配和结果汇总

    职责：
    - 接收用户任务
    - 将任务分配给合适的 Agent
    - 收集所有 Agent 的结果
    - 生成最终报告
    """

    def __init__(self, *args, available_agents: List[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_agents = available_agents or []
        self.pending_results = set()

    def run(self, task: str) -> None:
        """运行协调流程"""
        print(f"\n[{self.name}] 开始协调任务: {task}")

        # 更新任务到共享状态
        self.update_state("current_task", task)
        self.update_state("task_status", "coordinating")

        # 分析任务，决定分配给哪些 Agent
        agents_to_dispatch = self._analyze_task(task)

        # 分发任务
        for agent_name in agents_to_dispatch:
            self.pending_results.add(agent_name)
            self.send_message(agent_name, {
                "type": "task_assignment",
                "task": task,
                "context": self.shared_state.context.copy()
            })

        print(f"[{self.name}] 任务已分配给: {', '.join(agents_to_dispatch)}")

    def collect_results(self) -> Dict[str, Any]:
        """收集所有 Agent 的结果"""
        print(f"\n[{self.name}] 收集执行结果...")

        # 从共享状态获取结果
        results = self.shared_state.results.copy()
        errors = self.shared_state.errors.copy()

        summary = {
            "task": self.shared_state.task,
            "results": results,
            "errors": errors,
            "status": "completed" if not errors else "completed_with_errors"
        }

        return summary

    def _analyze_task(self, task: str) -> List[str]:
        """分析任务，决定分配给哪些 Agent"""
        # 简化实现：基于关键词判断
        if "情感" in task or "态度" in task:
            return ["SentimentAgent"]
        elif "检索" in task or "搜索" in task:
            return ["RetrieverAgent"]
        elif "关键词" in task or "摘要" in task:
            return ["AnalyzerAgent"]
        else:
            # 复杂任务需要多个 Agent
            return ["RetrieverAgent", "AnalyzerAgent"]


class RetrieverAgent(BaseAgent):
    """
    检索 Agent：负责文档检索

    职责：
    - 接收检索任务
    - 执行检索操作
    - 报告检索结果
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self) -> None:
        """运行检索流程"""
        messages = self.receive_messages()

        for msg in messages:
            if msg.content.get("type") == "task_assignment":
                task = msg.content.get("task", "")
                print(f"\n[{self.name}] 执行检索任务: {task}")

                # 模拟检索
                results = self._perform_retrieval(task)

                # 更新共享状态
                self.shared_state.results["retrieval"] = results
                self.update_state("retrieval_completed", True)

                # 报告完成
                self.send_message("CoordinatorAgent", {
                    "type": "task_completion",
                    "agent": self.name,
                    "result": results
                })

    def _perform_retrieval(self, query: str) -> Dict[str, Any]:
        """执行检索（模拟）"""
        # 模拟检索结果
        return {
            "query": query,
            "documents": [
                {"id": 1, "content": f"关于{query}的文档1"},
                {"id": 2, "content": f"关于{query}的文档2"},
                {"id": 3, "content": f"关于{query}的文档3"},
            ],
            "count": 3
        }


class AnalyzerAgent(BaseAgent):
    """
    分析 Agent：负责文本分析

    职责：
    - 接收分析任务
    - 执行文本分析（关键词、摘要等）
    - 报告分析结果
    """

    def run(self) -> None:
        """运行分析流程"""
        messages = self.receive_messages()

        for msg in messages:
            if msg.content.get("type") == "task_assignment":
                task = msg.content.get("task", "")
                print(f"\n[{self.name}] 执行分析任务: {task}")

                # 检查是否有检索结果
                retrieval_results = self.shared_state.results.get("retrieval")

                if retrieval_results:
                    # 基于检索结果进行分析
                    text_to_analyze = " ".join([d["content"] for d in retrieval_results["documents"]])
                else:
                    text_to_analyze = task

                # 执行分析
                results = self._perform_analysis(text_to_analyze)

                # 更新共享状态
                self.shared_state.results["analysis"] = results
                self.update_state("analysis_completed", True)

                # 报告完成
                self.send_message("CoordinatorAgent", {
                    "type": "task_completion",
                    "agent": self.name,
                    "result": results
                })

    def _perform_analysis(self, text: str) -> Dict[str, Any]:
        """执行文本分析（模拟）"""
        # 简化实现
        words = ["产品", "质量", "服务", "客户", "满意度"]
        return {
            "keywords": words[:3],
            "summary": f"分析摘要：{text[:50]}...",
            "sentiment": "positive"
        }


class SentimentAgent(BaseAgent):
    """
    情感分析 Agent：专门负责情感分析

    职责：
    - 接收情感分析任务
    - 执行情感分析
    - 报告情感分析结果
    """

    def run(self) -> None:
        """运行情感分析流程"""
        messages = self.receive_messages()

        for msg in messages:
            if msg.content.get("type") == "task_assignment":
                task = msg.content.get("task", "")
                print(f"\n[{self.name}] 执行情感分析任务: {task}")

                # 执行情感分析
                results = self._perform_sentiment_analysis(task)

                # 更新共享状态
                self.shared_state.results["sentiment"] = results
                self.update_state("sentiment_completed", True)

                # 报告完成
                self.send_message("CoordinatorAgent", {
                    "type": "task_completion",
                    "agent": self.name,
                    "result": results
                })

    def _perform_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """执行情感分析（模拟）"""
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
            sentiment = "positive"
        elif score < 0:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "confidence": 0.8,
            "score": score
        }


# ============================================================
# 反例：糟糕的通信实现
# ============================================================

def bad_communication_example():
    """
    反例：没有统一通信机制的糟糕实现

    常见错误：
    1. Agent 之间直接调用，耦合度高
    2. 没有消息历史，难以调试
    3. 状态分散，难以追踪
    """

    class BadAgent1:
        """❌ 直接调用的 Agent（不推荐）"""
        def __init__(self):
            self.agent2 = None  # 直接引用其他 Agent

        def set_agent2(self, agent2):
            self.agent2 = agent2  # 问题1: 直接依赖

        def run(self, task):
            # 问题2: 直接调用其他 Agent
            result = self.agent2.do_something(task)
            return result

    print("❌ 错误做法示例：")
    print("BadAgent1 直接引用和调用 BadAgent2")
    print("问题：")
    print("  1. Agent 之间耦合度高")
    print("  2. 难以添加新的 Agent")
    print("  3. 没有通信记录，难以调试")
    print("\n✅ 正确做法：使用 MessageBus 和 SharedState")
    print("  Agent 通过消息总线通信，通过共享状态交换数据")


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    print("=" * 70)
    print("Agent 间通信演示")
    print("=" * 70)

    # 初始化消息总线和共享状态
    message_bus = MessageBus()
    shared_state = SharedState(task="初始化")

    # 创建 Agent
    coordinator = CoordinatorAgent(
        name="CoordinatorAgent",
        message_bus=message_bus,
        shared_state=shared_state,
        available_agents=["RetrieverAgent", "AnalyzerAgent", "SentimentAgent"]
    )

    retriever = RetrieverAgent(
        name="RetrieverAgent",
        message_bus=message_bus,
        shared_state=shared_state
    )

    analyzer = AnalyzerAgent(
        name="AnalyzerAgent",
        message_bus=message_bus,
        shared_state=shared_state
    )

    sentiment = SentimentAgent(
        name="SentimentAgent",
        message_bus=message_bus,
        shared_state=shared_state
    )

    # 测试任务
    test_tasks = [
        "检索关于远程办公政策的文档",
        "分析客户反馈的情感倾向：我对公司的服务很满意",
        "分析并检索：产品反馈中提到了质量和物流问题",
    ]

    for task in test_tasks:
        print(f"\n{'='*70}")
        print(f"用户任务: {task}")
        print('='*70)

        # 重置状态
        shared_state.task = task
        shared_state.context = {}
        shared_state.results = {}
        shared_state.errors = []
        message_bus.messages = deque()

        # 1. 协调者分配任务
        coordinator.run(task)

        # 2. 其他 Agent 执行任务
        retriever.run()
        analyzer.run()
        sentiment.run()

        # 3. 协调者收集结果
        summary = coordinator.collect_results()

        print(f"\n{'='*70}")
        print("最终结果:")
        print('='*70)
        print(json.dumps(summary, ensure_ascii=False, indent=2))

        # 4. 显示消息历史
        print(f"\n{'='*70}")
        print("消息历史:")
        print('='*70)
        history = message_bus.get_history()
        for msg in history:
            print(f"  {msg.sender} -> {msg.receiver}: {msg.content.get('type', 'unknown')}")

    # 对比说明
    print("\n" + "=" * 70)
    print("Agent 间通信的关键设计")
    print("=" * 70)
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 设计模式           │  优点                          │  缺点        │
├─────────────────────────────────────────────────────────────────┤
│ 直接调用            │  简单、直接                      │  耦合度高    │
│                    │                                │  难以扩展    │
├─────────────────────────────────────────────────────────────────┤
│ 消息传递            │  解耦、灵活                      │  复杂度较高  │
│ （MessageBus）      │  可追溯、可扩展                  │  需要管理消息 │
├─────────────────────────────────────────────────────────────────┤
│ 共享状态            │  简单的数据共享                  │  需要同步    │
│ （SharedState）     │  状态一致                      │  可能冲突    │
└─────────────────────────────────────────────────────────────────┘

阿码的问题：如果两个 Agent 同时修改共享状态怎么办？

答案：有两种方案
1. 锁机制（Lock）：同一时间只有一个 Agent 能修改状态
2. 消息队列：Agent 通过消息请求修改，由协调者统一处理

老潘的点评：
"在生产环境里，我们会用消息队列（如 RabbitMQ、Kafka）来做 Agent 通信。
这样即使某个 Agent 挂了，消息也不会丢失，而且可以支持分布式部署。"

最佳实践：
✅ 使用消息总线进行通信（解耦）
✅ 使用共享状态存储结果（方便访问）
✅ 记录所有消息历史（可追溯）
✅ 每个消息有明确的类型和格式
    """)

    # 展示反例
    print("\n" + "=" * 70)
    print("反例：没有统一通信机制的糟糕实现")
    print("=" * 70)
    bad_communication_example()


if __name__ == "__main__":
    main()

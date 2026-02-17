#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：TextAgent 的 Agent 能力集成

本例是 Week 05 的 TextAgent 超级线代码，在 Week 04 高级 RAG 基础之上，
增加了 Agent 能力：工具调用、任务规划、ReAct 循环。

运行方式：
1. 构建知识库：python3 chapters/week_05/examples/05_textagent_agent.py --build
2. 交互问答：python3 chapters/week_05/examples/05_textagent_agent.py
3. 评估效果：python3 chapters/week_05/examples/05_textagent_agent.py --evaluate

预期输出：
- 知识库构建成功
- 交互式问答界面（支持复杂多步骤任务）
- 评估报告写入 report.md

主要更新（Week 05）：
1. 文本分析工具集（情感分析、摘要、关键词提取）
2. ReAct Agent 实现（Thought-Action-Observation 循环）
3. 任务规划能力（自动分解复杂任务）
4. 工具调用日志（用于可追溯性）
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai import OpenAI

# 导入 Week 04 的 RAG 模块
try:
    from textagent.rag.advanced_pipeline import AdvancedRAGPipeline, RAGResponse
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("警告：无法导入 RAG 模块，将使用简化版本")


# ============================================================
# 配置
# ============================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHAT_MODEL = "gpt-4o-mini"

SAMPLE_DOCS_DIR = Path(__file__).parent / "sample_documents"
REPORT_PATH = Path(__file__).parent.parent / "report.md"

# 复用 Week 04 的配置
CHROMA_PERSIST_DIR = str(Path(__file__).parent / "textagent_chroma_db")
COLLECTION_NAME = "textagent_docs"


# ============================================================
# 文本分析工具集
# ============================================================

@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class TextAnalysisToolkit:
    """
    文本分析工具包

    Week 05 新增：提供一系列文本分析工具，
    供 Agent 根据任务需求调用。
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        if llm_client is None and os.environ.get("OPENAI_API_KEY"):
            self.llm = OpenAI()
        else:
            self.llm = llm_client  # 可能是 None
        self.tools: Dict[str, Callable] = {
            "sentiment_analysis": self.sentiment_analysis,
            "summarize": self.summarize,
            "extract_keywords": self.extract_keywords,
            "classify_topic": self.classify_topic,
            "detect_language": self.detect_language,
        }

    def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        情感分析：判断文本的情感倾向

        Returns:
            包含 sentiment（positive/negative/neutral）和 confidence 的字典
        """
        if self.llm is None:
            # 模拟模式：基于简单规则
            positive_words = ["满意", "好", "棒", "优秀", "喜欢", "开心"]
            negative_words = ["不满意", "差", "糟糕", "讨厌", "难过"]

            score = 0
            for word in positive_words:
                if word in text:
                    score += 1
            for word in negative_words:
                if word in text:
                    score -= 1

            if score > 0:
                return {"sentiment": "positive", "confidence": 0.7}
            elif score < 0:
                return {"sentiment": "negative", "confidence": 0.7}
            else:
                return {"sentiment": "neutral", "confidence": 0.5}

        prompt = f"""分析以下文本的情感倾向（正面/负面/中性），并给出置信度（0-1）。

文本：{text}

请以JSON格式返回：
{{"sentiment": "positive/negative/neutral", "confidence": 0.95, "reasoning": "简要说明"}}"""

        try:
            response = self.llm.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {"sentiment": "neutral", "confidence": 0.0, "error": str(e)}

    def summarize(self, text: str, max_length: int = 100) -> str:
        """文本摘要"""
        if self.llm is None:
            # 模拟模式：截断文本
            if len(text) <= max_length:
                return text
            return text[:max_length] + "..."

        prompt = f"""将以下文本总结为不超过{max_length}字的摘要。

文本：{text}

摘要："""

        try:
            response = self.llm.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"摘要生成失败: {e}"

    def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """关键词提取"""
        if self.llm is None:
            # 模拟模式：提取常见的名词性词语
            # 简化实现
            words = ["GPU", "远程办公", "报销", "政策", "流程"]
            return words[:top_k]

        prompt = f"""从以下文本中提取 {top_k} 个最重要的关键词。

文本：{text}

关键词（以逗号分隔）："""

        try:
            response = self.llm.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            keywords_text = response.choices[0].message.content.strip()
            return [k.strip() for k in keywords_text.split(",")]
        except Exception as e:
            return []

    def classify_topic(self, text: str) -> Dict[str, Any]:
        """主题分类"""
        topics = ["人力资源", "财务报销", "IT支持", "远程办公", "其他"]

        if self.llm is None:
            # 模拟模式：基于关键词匹配
            if "GPU" in text or "IT" in text:
                return {"topic": "IT支持", "confidence": 0.7}
            elif "报销" in text or "费用" in text:
                return {"topic": "财务报销", "confidence": 0.7}
            elif "远程" in text:
                return {"topic": "远程办公", "confidence": 0.7}
            else:
                return {"topic": "其他", "confidence": 0.5}

        prompt = f"""将以下文本归类到以下主题之一：{', '.join(topics[:-1])}

文本：{text}

请只返回主题名称。"""

        try:
            response = self.llm.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            topic = response.choices[0].message.content.strip()
            return {"topic": topic, "confidence": 0.8}
        except Exception as e:
            return {"topic": "其他", "error": str(e)}

    def detect_language(self, text: str) -> str:
        """语言检测"""
        # 简化实现：检测是否包含中文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > len(text) * 0.3:
            return "zh"
        return "en"

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """执行指定工具"""
        import time

        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"未知工具: {tool_name}"
            )

        start = time.time()
        try:
            result = self.tools[tool_name](**kwargs)
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=time.time() - start
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time=time.time() - start
            )

    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有可用工具"""
        return [
            {
                "name": name,
                "description": func.__doc__ or "No description",
            }
            for name, func in self.tools.items()
        ]


# ============================================================
# ReAct Agent 实现
# ============================================================

@dataclass
class AgentStep:
    """Agent 执行步骤"""
    step_number: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Any = None
    tool_result: Optional[ToolResult] = None


@dataclass
class AgentResponse:
    """Agent 响应"""
    answer: str
    steps: List[AgentStep] = field(default_factory=list)
    tool_calls: List[ToolResult] = field(default_factory=list)
    rag_used: bool = False
    total_time: float = 0.0


class TextAgentAgent:
    """
    TextAgent 的 Agent 核心实现

    整合了：
    1. RAG 能力（从 Week 04 继承）
    2. 文本分析工具（Week 05 新增）
    3. ReAct 推理循环（Week 05 新增）
    """

    def __init__(
        self,
        use_rag: bool = True,
        openai_api_key: Optional[str] = None
    ):
        api_key = openai_api_key or OPENAI_API_KEY
        if api_key:
            self.llm = OpenAI(api_key=api_key)
        else:
            self.llm = None

        self.use_rag = use_rag and RAG_AVAILABLE and api_key is not None

        # 初始化工具包
        self.toolkit = TextAnalysisToolkit(self.llm)

        # 初始化 RAG Pipeline
        self.rag_pipeline: Optional[AdvancedRAGPipeline] = None
        if self.use_rag and api_key:
            try:
                self.rag_pipeline = AdvancedRAGPipeline(
                    collection_name=COLLECTION_NAME,
                    persist_directory=CHROMA_PERSIST_DIR,
                    openai_api_key=api_key,
                )
                print("RAG 模块已加载")
            except Exception as e:
                print(f"RAG 模块加载失败: {e}")
                self.use_rag = False
                self.use_rag = False

    def query(self, user_message: str, verbose: bool = True) -> AgentResponse:
        """
        处理用户查询

        流程：
        1. 分析用户意图（RAG vs 工具调用 vs 直接回答）
        2. 如果需要 RAG，先检索相关文档
        3. 根据意图决定使用哪些工具
        4. 执行工具并收集结果
        5. 生成最终回复
        """
        import time
        start = time.time()

        steps: List[AgentStep] = []
        tool_results: List[ToolResult] = []

        if verbose:
            print(f"\n用户: {user_message}")

        # 步骤1: 意图识别
        intent = self._classify_intent(user_message)

        step1 = AgentStep(
            step_number=1,
            thought=f"用户意图: {intent['category']}。{intent['reasoning']}"
        )
        steps.append(step1)

        if verbose:
            print(f"\n[步骤1] 意图分析")
            print(f"  类别: {intent['category']}")
            print(f"  思考: {intent['reasoning']}")

        # 步骤2: 根据意图执行
        answer = ""

        if intent["category"] == "rag_query":
            # 使用 RAG
            if self.rag_pipeline:
                rag_response = self.rag_pipeline.query(user_message)
                answer = rag_response.answer
                step2 = AgentStep(
                    step_number=2,
                    thought="使用 RAG 检索相关文档并生成回答",
                    action="rag_query",
                    observation=f"检索到 {len(rag_response.sources)} 个相关文档"
                )
                steps.append(step2)

        elif intent["category"] == "text_analysis":
            # 执行文本分析
            tool_name = intent.get("tool", "sentiment_analysis")
            text_to_analyze = intent.get("text", user_message)

            step2 = AgentStep(
                step_number=2,
                thought=f"使用 {tool_name} 工具分析文本",
                action=tool_name,
                action_input={"text": text_to_analyze}
            )

            result = self.toolkit.execute_tool(tool_name, text=text_to_analyze)
            tool_results.append(result)
            step2.tool_result = result
            step2.observation = result.result if result.success else result.error

            steps.append(step2)

            if result.success:
                answer = self._format_analysis_result(tool_name, result.result)
            else:
                answer = f"分析失败: {result.error}"

        elif intent["category"] == "complex_task":
            # 复杂任务：需要多步骤
            answer = self._handle_complex_task(user_message, steps, tool_results, verbose)

        else:
            # 直接回答
            step2 = AgentStep(
                step_number=2,
                thought="这是一个简单问题，直接回答即可",
                action="direct_answer"
            )
            steps.append(step2)

            answer = self._direct_answer(user_message)

        total_time = time.time() - start

        return AgentResponse(
            answer=answer,
            steps=steps,
            tool_calls=tool_results,
            rag_used=intent["category"] == "rag_query",
            total_time=total_time
        )

    def _classify_intent(self, message: str) -> Dict[str, Any]:
        """分类用户意图"""
        # 简化的意图分类逻辑
        keywords_rag = ["政策", "流程", "怎么", "如何", "什么", "申请"]
        keywords_sentiment = ["情感", "态度", "看法", "评价"]
        keywords_summary = ["摘要", "总结", "概括"]
        keywords_keywords = ["关键词", "主题"]
        keywords_topic = ["分类", "归类"]

        if any(kw in message for kw in keywords_rag):
            return {
                "category": "rag_query",
                "reasoning": "用户询问公司政策或流程，需要检索知识库"
            }
        elif any(kw in message for kw in keywords_sentiment):
            return {
                "category": "text_analysis",
                "tool": "sentiment_analysis",
                "reasoning": "用户要求分析文本情感"
            }
        elif any(kw in message for kw in keywords_summary):
            return {
                "category": "text_analysis",
                "tool": "summarize",
                "reasoning": "用户要求文本摘要"
            }
        elif any(kw in message for kw in keywords_keywords):
            return {
                "category": "text_analysis",
                "tool": "extract_keywords",
                "reasoning": "用户要求提取关键词"
            }
        elif any(kw in message for kw in keywords_topic):
            return {
                "category": "text_analysis",
                "tool": "classify_topic",
                "reasoning": "用户要求主题分类"
            }
        else:
            return {
                "category": "direct_answer",
                "reasoning": "可以直接回答，无需特殊处理"
            }

    def _handle_complex_task(
        self,
        message: str,
        steps: List[AgentStep],
        tool_results: List[ToolResult],
        verbose: bool
    ) -> str:
        """处理复杂多步骤任务"""
        # 简化实现：假设复杂任务需要多个工具
        step_num = len(steps) + 1

        # 示例：同时进行情感分析和关键词提取
        step = AgentStep(
            step_number=step_num,
            thought="复杂任务，执行多个文本分析工具",
            action="multi_tool_analysis"
        )
        steps.append(step)

        results = []
        for tool_name in ["sentiment_analysis", "extract_keywords"]:
            result = self.toolkit.execute_tool(tool_name, text=message)
            tool_results.append(result)
            if result.success:
                results.append(f"{tool_name}: {result.result}")

        return "\n".join(results)

    def _format_analysis_result(self, tool_name: str, result: Any) -> str:
        """格式化分析结果"""
        if tool_name == "sentiment_analysis":
            sentiment = result.get("sentiment", "unknown")
            confidence = result.get("confidence", 0)
            sentiment_map = {"positive": "正面", "negative": "负面", "neutral": "中性"}
            return f"情感倾向: {sentiment_map.get(sentiment, sentiment)} (置信度: {confidence:.2%})"
        elif tool_name == "summarize":
            return f"摘要: {result}"
        elif tool_name == "extract_keywords":
            return f"关键词: {', '.join(result)}"
        elif tool_name == "classify_topic":
            return f"主题: {result.get('topic', '未知')}"
        return str(result)

    def _direct_answer(self, message: str) -> str:
        """直接回答（不使用工具）"""
        return f"收到您的问题：{message}。这是一个简单问题，我可以直接回答。"


# ============================================================
# 主函数
# ============================================================

def load_documents(docs_dir: Path) -> List[Dict]:
    """加载文档（复用 Week 04 的逻辑）"""
    documents = []

    for file_path in docs_dir.glob("*.txt"):
        if not file_path.exists():
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        filename = file_path.stem

        if "remote" in filename or "远程" in filename:
            category = "远程办公"
        elif "expense" in filename or "报销" in filename:
            category = "财务报销"
        elif "it" in filename or "IT" in filename:
            category = "IT支持"
        else:
            category = "其他"

        documents.append({
            "filename": filename,
            "content": content,
            "metadata": {
                "source": file_path.name,
                "category": category,
            }
        })

    return documents


def build_knowledge_base():
    """构建知识库"""
    print("=" * 60)
    print("构建 TextAgent 知识库（Week 05 Agent 版）")
    print("=" * 60)

    if not OPENAI_API_KEY:
        print("错误：未设置 OPENAI_API_KEY 环境变量")
        return None

    # 加载文档
    print("\n[1/2] 加载文档...")
    SAMPLE_DOCS_DIR.mkdir(exist_ok=True)

    # 如果目录为空，创建示例文档
    if not list(SAMPLE_DOCS_DIR.glob("*.txt")):
        print("创建示例文档...")
        create_sample_documents()

    documents = load_documents(SAMPLE_DOCS_DIR)
    print(f"加载了 {len(documents)} 个文档")

    # 初始化 Agent
    print("\n[2/2] 初始化 TextAgent Agent...")
    agent = TextAgentAgent(use_rag=True)

    # 构建 RAG 索引
    if agent.rag_pipeline:
        agent.rag_pipeline.build_index(documents)

    print("\n知识库构建完成！")
    return agent


def create_sample_documents():
    """创建示例文档（如果不存在）"""
    docs = {
        "remote_work.txt": """远程办公政策

1. 申请流程
   - 员工需提前3个工作日提交远程办公申请
   - 每周远程办公不超过2天
   - 需直属主管审批

2. 工作要求
   - 保持工作时间内在线响应
   - 定期向主管汇报工作进展
   - 参加必要线上会议

3. 设备支持
   - 公司可提供必要的办公设备
   - 需提前申请并登记""",
        "expense_policy.txt": """费用报销政策

1. 报销时限
   - 费用发生后30天内提交
   - 超过时限不予报销

2. 发票要求
   - 必须为公司抬头的正式发票
   - 发票内容与实际费用一致
   - 需附费用说明

3. 审批流程
   - 500元以下：主管审批
   - 500-2000元：部门经理审批
   - 2000元以上：需财务总监审批""",
        "it_support.txt": """IT支持服务

1. 常见问题
   - 密码重置：联系IT热线
   - 软件安装：使用自助服务门户
   - 硬件故障：提交工单

2. GPU资源申请
   - 需说明使用时长和用途
   - 每次申请最长7天
   - 需技术主管审批

3. 存储资源
   - 个人配额：100GB
   - 项目存储：需申请，最多10TB""",
    }

    for filename, content in docs.items():
        with open(SAMPLE_DOCS_DIR / filename, "w", encoding="utf-8") as f:
            f.write(content)


def interactive_qa(agent: TextAgentAgent):
    """交互式问答"""
    print("\n" + "=" * 60)
    print("TextAgent 问答系统（Week 05 Agent 版）")
    print("=" * 60)

    # 展示可用工具
    print("\n可用工具:")
    for tool in agent.toolkit.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")

    sample_questions = [
        "远程办公政策是什么？",  # RAG
        "分析这句话的情感：我很满意公司的福利待遇",  # 情感分析
        "总结一下：GPU资源需要申请，每次最长7天",  # 摘要
        "提取关键词：IT支持包括密码重置、软件安装和硬件故障",  # 关键词
    ]

    print("\n示例问题:")
    for i, q in enumerate(sample_questions, 1):
        print(f"  {i}. {q}")

    print("\n输入问题开始查询，输入 'quit' 退出")

    while True:
        print("\n" + "-" * 40)
        user_input = input("请输入问题: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if not user_input:
            continue

        try:
            response = agent.query(user_input, verbose=True)

            print(f"\n回答:\n{response.answer}")
            print(f"\n执行信息: {len(response.steps)} 步, "
                  f"{len(response.tool_calls)} 次工具调用, "
                  f"耗时 {response.total_time:.2f}s")

        except Exception as e:
            print(f"\n发生错误: {e}")


def run_evaluation(agent: TextAgentAgent):
    """运行评估"""
    print("=" * 60)
    print("TextAgent 效果评估（Week 05 Agent）")
    print("=" * 60)

    test_queries = [
        ("远程办公政策是什么？", "rag_query"),
        ("分析情感：我很满意公司的福利待遇", "sentiment_analysis"),
        ("总结：GPU资源需要申请，每次最长7天", "summarize"),
        ("提取关键词：IT支持包括密码重置和软件安装", "extract_keywords"),
    ]

    results = []

    for query, expected_type in test_queries:
        print(f"\n评估: {query}")
        try:
            response = agent.query(query, verbose=False)

            result = {
                "query": query,
                "expected_type": expected_type,
                "answer": response.answer,
                "steps": len(response.steps),
                "tools_used": len(response.tool_calls),
                "time": response.total_time,
            }
            results.append(result)

        except Exception as e:
            print(f"  错误: {e}")
            results.append({"query": query, "error": str(e)})

    # 写入报告
    generate_report(results)
    print(f"\n评估报告已写入：{REPORT_PATH}")


def generate_report(results: List[Dict]) -> None:
    """生成评估报告"""
    report_content = f"""# TextAgent 项目报告

## Week 05：Agent 能力

### 更新日期
{datetime.now().strftime("%Y-%m-%d")}

### 新增功能

1. **文本分析工具集**
   - 情感分析（sentiment_analysis）
   - 文本摘要（summarize）
   - 关键词提取（extract_keywords）
   - 主题分类（classify_topic）
   - 语言检测（detect_language）

2. **ReAct Agent 实现**
   - Thought-Action-Observation 循环
   - 意图识别与路由
   - 工具调用与结果聚合

3. **RAG + Agent 整合**
   - 自动判断何时使用 RAG
   - 自动判断何时调用工具
   - 统一的响应格式

### 架构演进

```
Week 04: 用户 → RAG → 检索 → LLM → 回答
Week 05: 用户 → Agent → [RAG | 工具 | 直接回答] → 回答
```

### 评估结果

| 查询 | 类型 | 步骤数 | 工具调用 | 耗时 |
|------|------|--------|----------|------|
"""

    for r in results:
        if "error" not in r:
            report_content += f"| {r['query'][:20]}... | {r['expected_type']} | {r['steps']} | {r['tools_used']} | {r['time']:.2f}s |\n"

    report_content += f"""
### 技术栈

- **LLM**: GPT-4o-mini
- **RAG**: ChromaDB + OpenAI Embeddings（Week 04）
- **Agent**: 自研 ReAct 实现（Week 05）
- **工具**: LLM 驱动的文本分析

### 下一步

- Week 06：多智能体协作（Multi-Agent）
- 规划者-执行者-审核者架构
- Human-in-the-Loop 机制

---

*本报告由 TextAgent 自动生成*
"""

    # 确保目录存在
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 写入报告
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="TextAgent Agent 系统")
    parser.add_argument("--build", action="store_true", help="构建知识库")
    parser.add_argument("--evaluate", action="store_true", help="运行评估")
    args = parser.parse_args()

    # 检查 API Key
    if not OPENAI_API_KEY:
        print("错误：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        return

    # 构建或加载知识库
    agent = build_knowledge_base()
    if agent is None:
        return

    # 运行评估
    if args.evaluate:
        run_evaluation(agent)
    elif not args.build:
        # 进入交互模式
        interactive_qa(agent)


if __name__ == "__main__":
    main()

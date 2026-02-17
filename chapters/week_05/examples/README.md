# Week 05 示例代码说明

本目录包含 Week 05（LLM Agent 基础）的所有示例代码。

## 示例列表

### 01_agent_vs_chatbot.py
展示 Chatbot 和 Agent 的根本区别。

**运行方式**：
```bash
python3 chapters/week_05/examples/01_agent_vs_chatbot.py
```

**核心要点**：
- Chatbot 只能对话回答问题，被动响应用户输入
- Agent 能主动调用工具，执行多步骤任务完成目标

### 02_function_calling.py
演示 Function Calling 的基础流程。

**运行方式**：
```bash
# 不设置 API Key 时使用模拟模式
python3 chapters/week_05/examples/02_function_calling.py

# 使用真实 API
export OPENAI_API_KEY="your-api-key"
python3 chapters/week_05/examples/02_function_calling.py
```

**核心要点**：
1. 定义工具 Schema（JSON Schema 格式）
2. 让 LLM 决定是否调用工具
3. 执行工具并反馈结果
4. 将工具结果返回给 LLM 生成最终回复

### 03_react_agent.py
演示 ReAct（Reasoning + Acting）模式的实现。

**运行方式**：
```bash
# 不设置 API Key 时使用模拟模式
python3 chapters/week_05/examples/03_react_agent.py

# 使用真实 API
export OPENAI_API_KEY="your-api-key"
python3 chapters/week_05/examples/03_react_agent.py
```

**核心要点**：
- Thought：思考当前状态和下一步行动
- Action：执行具体工具调用
- Observation：观察工具返回的结果
- 循环执行直到完成任务

### 04_task_planning.py
演示任务规划（Task Planning）能力。

**运行方式**：
```bash
# 不设置 API Key 时使用模拟模式
python3 chapters/week_05/examples/04_task_planning.py

# 使用真实 API
export OPENAI_API_KEY="your-api-key"
python3 chapters/week_05/examples/04_task_planning.py
```

**核心要点**：
1. 规划阶段：分析任务，生成执行计划
2. 执行阶段：按计划调用工具
3. 处理任务间的依赖关系

### 05_textagent_agent.py
TextAgent 的 Agent 能力集成（Week 05 超级线代码）。

**运行方式**：
```bash
# 构建知识库
export OPENAI_API_KEY="your-api-key"
python3 chapters/week_05/examples/05_textagent_agent.py --build

# 交互式问答
python3 chapters/week_05/examples/05_textagent_agent.py

# 运行评估
python3 chapters/week_05/examples/05_textagent_agent.py --evaluate
```

**核心要点**：
- 整合 RAG 能力（从 Week 04 继承）
- 文本分析工具集（情感分析、摘要、关键词提取等）
- ReAct 推理循环
- 自动意图识别与路由

## 依赖安装

```bash
pip install openai
```

## 环境变量设置

```bash
export OPENAI_API_KEY="your-api-key"
```

## 注意事项

1. 所有示例都支持模拟模式（不需要 API Key），但功能有限
2. 使用真实 API 时需要设置 `OPENAI_API_KEY` 环境变量
3. 示例代码包含详细的注释和反例说明
4. 建议按顺序运行示例，从简单到复杂

## 测试

运行测试：
```bash
python3 -m pytest chapters/week_05/tests/ -v
```

运行 smoke 测试：
```bash
python3 -m pytest chapters/week_05/tests/test_smoke.py -v
```

---
name: new-week
description: 初始化一个 week_XX 章包目录与模板，并更新 TOC/current_week。
argument-hint: "<week_number> <title>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
disable-model-invocation: true
---

# /new-week

## 用法

```
/new-week 01 从数据到问题：你的第一份数据卡
```

## 步骤

1. 运行脚本生成周目录与模板：
   ```bash
   python3 scripts/new_week.py --week 01 --title "从数据到问题：你的第一份数据卡"
   ```
2. 打开并快速检查生成的文件（至少确认标题与 week 号正确）：
   - `chapters/week_XX/CHAPTER.md`
   - `chapters/week_XX/ASSIGNMENT.md`
   - `chapters/week_XX/RUBRIC.md`
   - `chapters/week_XX/tests/test_smoke.py`
3. 建议输出并复制下面的 team 任务约定到 lead 会话：
   - 所有 task subject 必须以 `[week_XX]` 开头（hooks 依赖它定位 week）。
   - 也可以直接运行：`/team-week week_XX`（生成一段 kickoff 提示词，用于 agent team 一次产出整周内容）。

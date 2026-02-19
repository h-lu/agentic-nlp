---
name: qa-week
description: 完整 QA 审读：一致性 + 技术正确性 + 学生视角四维评分；输出并收敛 QA_REPORT。
argument-hint: "<week_id e.g. week_01>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task
---

# /qa-week

## 用法

```
/qa-week week_XX
```

## 目标

执行完整的三维度 QA 审读，收敛到 QA_REPORT.md，并通过 release 校验：

```bash
python3 scripts/validate_week.py --week week_XX --mode release
```

## QA 流程

### Stage 1: 并行审读（一致性 + 技术正确性）

同时启动以下两个 agent（可并行）：

1. **`consistency-editor`**：
   - 修复格式/术语/角色一致性
   - 同步 `TERMS.yml` -> `shared/glossary.yml`
   - 检查循环角色使用（对照 `shared/characters.yml`）
   - 修复 `ANCHORS.yml` 问题（依赖 `validate_week.py` 报错定位）
   - **可直接修改文件**

2. **`technical-reviewer`**：
   - 审读概念/公式/代码/答案正确性
   - 检查教学法对齐（目标/递进/示例-练习）
   - 检查练习题质量（可评分/难度梯度）
   - **只读，输出问题清单（含 Severity 分级）**

### Stage 2: 收集结果

- 等待 Stage 1 的两个 agent 完成
- 收集 `technical-reviewer` 的问题清单
- 确认 `consistency-editor` 的修改已生效

### Stage 3: 学生视角审读

调用 **`student-qa`**：

- **传入 technical-reviewer 发现的 S1/S2 问题摘要**
- 基于修复后的文件进行审读
- 输出四维评分（叙事流畅度/趣味性/知识覆盖/认知负荷）
- 如有 S1 错误，在"知识覆盖"维度标注扣分原因
- **只读，通过 tool result 返回评分和清单**

### Stage 4: Lead 收敛

由 Lead agent（你）执行：

1. **汇总问题清单**：
   - consistency-editor 已修复的问题（无需列出）
   - technical-reviewer 发现的问题（按 S1→S2→S3→S4 排序）
   - student-qa 发现的问题（阻塞项 + 建议项）

2. **写入 QA_REPORT.md**：

```markdown
# QA Report: week_XX

## 四维评分

| 维度 | 分数 | 说明 |
|------|------|------|
| 叙事流畅度 | X/5 | ... |
| 趣味性 | X/5 | ... |
| 知识覆盖 | X/5 | ... |
| 认知负荷 | X/5 | ... |
| **总分** | **XX/20** | |

## 技术审读问题

### S1 致命（必须修复）
- [ ] {问题描述} — `CHAPTER.md#xxx`

### S2 重要（强烈建议修复）
- [ ] {问题描述} — `CHAPTER.md#xxx`

## 阻塞项

- [ ] {问题描述} — {位置}

## 建议项

- [ ] {问题描述} — {位置}

## 教学法建议
{technical-reviewer 的教学法建议}

## 审读记录
- consistency-editor: 已修复 X 处一致性问题
- technical-reviewer: 发现 X 个问题（S1: X, S2: X, S3: X, S4: X）
- student-qa: 四维评分 XX/20
```

3. **如有 S1/S2 问题**：
   - 标注需回传 `chapter-writer` 或 `prose-polisher` 修复
   - 等待修复后重新运行 `/qa-week`

4. **最终 release 校验**：

```bash
python3 scripts/validate_week.py --week week_XX --mode release
```

## 通过标准

- QA_REPORT 的"阻塞项"必须清零（不允许 `- [ ]`）
- S1 问题必须清零
- 四维评分总分 >= 18/20

## 错误处理

如果 release 校验失败：
1. 调用 `error-fixer` 逐条修复
2. 重新运行校验
3. 更新 QA_REPORT.md

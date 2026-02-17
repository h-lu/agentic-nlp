---
name: make-assignment
description: 生成作业 + rubric + tests 草案，并产出最小示例与反例。
argument-hint: "<week_id e.g. week_01>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
disable-model-invocation: true
---

# /make-assignment

## 用法

```
/make-assignment week_XX
```

## 步骤

1. 调用 `exercise-factory`：
   - 生成基础/进阶/挑战三层作业到 `ASSIGNMENT.md`
   - 同步更新 `RUBRIC.md`
2. 调用 `example-engineer`：
   - 产出最小可运行示例与反例到 `examples/`
   - 在 `CHAPTER.md` 插入引用（短讲解即可）
3. 调用 `test-designer`：
   - 生成 pytest 用例到 `tests/`
4. 本地验证（必须）：
   ```bash
   python3 -m pytest chapters/week_XX/tests -q
   ```

---
name: qa-book
description: 需要确保 14 周内容在术语、目录、标题与校验标准上保持一致时，运行全书级校验（跨周一致性）。
argument-hint: "[--mode fast|release] [--strict]"
allowed-tools: Bash, Read, Grep, Glob
disable-model-invocation: true
---

# /qa-book

## 用法

```bash
/qa-book
/qa-book --mode fast
/qa-book --mode release
/qa-book --mode fast --strict
```

## 说明

- `fast`：快速一致性检查（并对已存在的 week 运行 `validate_week --mode idle`，不跑 pytest）。
- `release`：更严格（对已存在的 week 运行 `validate_week --mode release`，会跑 pytest）。
- `--strict`：把 warnings 当成 errors（用于收敛阶段）。

## 执行

```bash
python3 scripts/validate_book.py --mode fast
```

根据需要替换参数。


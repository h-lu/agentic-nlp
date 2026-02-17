---
name: scaffold-book
description: 当需要一次性生成 week_01..week_08 的章包目录与模板（不写正文内容）时，批量调用 new_week 脚手架。
argument-hint: "[--start 1] [--end 8] [--force]"
allowed-tools: Bash, Read, Grep, Glob
disable-model-invocation: true
---

# /scaffold-book

## 用法

```bash
/scaffold-book
/scaffold-book --start 2 --end 8
/scaffold-book --force
```

## 说明

- 标题来源：`chapters/TOC.md`（作为全书标题的单一事实源）。
- 默认不覆盖已存在的 week 文件（安全）。`--force` 才会覆盖（谨慎使用）。

## 执行

```bash
python3 scripts/scaffold_book.py --start 1 --end 8
```

---
name: release-week
description: 收敛与发布：生成 RELEASE.md，更新 TOC/Glossary，并跑 release 校验。
argument-hint: "<week_id e.g. week_01>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
disable-model-invocation: true
---

# /release-week

## 用法

```
/release-week week_XX
```

## 步骤

1. 执行发布脚本（会更新 TOC/Glossary，并生成 RELEASE.md）：
   ```bash
   python3 scripts/release_week.py --week week_XX
   ```
   说明：发布脚本会额外执行跨周一致性硬门禁（`validate_book.py --mode fast --strict`）。
2. 发布前自检（提示性质，不作为 hooks 硬闸门）：
   ```bash
   git status --porcelain
   git log -n 5 --oneline
   ```
3. 最终确认：
   - `chapters/week_XX/RELEASE.md` 存在且可读
   - `python3 -m pytest chapters/week_XX/tests -q` 通过

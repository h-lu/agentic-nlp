# Gitea 协作流程速查（等价 GitHub）

本书使用自建 Gitea 做远端协作。核心流程与 GitHub 等价：

`local commits -> push -> Pull Request (PR) -> review -> merge`

> 约定：默认主分支名为 `main`。如果你的仓库是 `master`，把文中的 `main` 替换成 `master` 即可。

## 1) SSH vs HTTPS（推荐 SSH）

- HTTPS：每次 push 可能需要输入账号/Token（或配置 credential helper）。
- SSH（推荐）：配置一次 SSH key，后续 push/pull 更稳定。

Gitea（UI 操作）：
- 进入 “Settings / SSH Keys” 添加你的公钥（`~/.ssh/id_ed25519.pub`）。

## 2) 初始化与第一次推送（first push）

在本地项目目录：

```bash
git init
git add .
git commit -m "init: scaffold textbook factory"
```

添加远端（用你自己的 Gitea 地址替换）：

```bash
git remote add origin git@your-gitea-host:OWNER/agentic-nlp.git
git branch -M main
git push -u origin main
```

## 3) 每周作业/章包的标准分支命名

建议分支名：

- `week_06/input-validation`
- `week_08/pytest-basics`

创建分支并切换：

```bash
git switch -c week_06/input-validation
```

或：

```bash
git checkout -b week_06/input-validation
```

## 4) 提交（commit）最小规范

- 一周至少 2 次提交（draft + verify），便于复盘与回滚
- 提交信息格式（最小版）：`<动词>: <做了什么>`
  - `draft: add week_06 outline`
  - `test: add week_06 edge cases`
  - `fix: handle empty input`

常用命令：

```bash
git status
git diff
git add -A
git commit -m "draft: ..."
git log --oneline -n 10
```

## 5) 推送到 Gitea

```bash
git push -u origin week_06/input-validation
```

## 6) 开 Pull Request (PR)

Gitea（UI 操作）：
1. 进入仓库的 “Pull Requests”
2. New Pull Request
3. base: `main`  compare: `week_06/input-validation`
4. 填写标题与描述（见下方 PR 模板）
5. Create Pull Request

### PR 描述建议模板（与 agentic/DoD 对齐）

```text
Week: week_XX

DoD:
- [x] files complete (CHAPTER/ASSIGNMENT/RUBRIC/tests/QA/anchors/terms)
- [x] pytest pass: python3 -m pytest chapters/week_XX/tests -q

Verification:
- python3 scripts/validate_week.py --week week_XX --mode release

Notes:
- what changed / why
```

## 7) Review 与修改

Gitea（UI 操作）：
- reviewer 留 comment 后，本地修改并继续 commit
- push 同一分支，PR 自动更新

```bash
# 修改后
git add -A
git commit -m "fix: address review comments"
git push
```

## 8) 合并（merge）到 main

Gitea（UI 操作）：
- 确认 checks（pytest/validate）都通过
- 选择 merge（普通 merge 即可；本书不要求 rebase）

合并后同步本地：

```bash
git switch main
git pull
```

## 9) 撤销与修复（只讲安全场景）

撤销工作区改动（未 add）：

```bash
git restore path/to/file
```

撤销暂存（已 add，但不想丢工作区内容）：

```bash
git restore --staged path/to/file
```

把最近一次 commit “拆回暂存区”（保留文件内容，安全场景）：

```bash
git reset --soft HEAD~1
```

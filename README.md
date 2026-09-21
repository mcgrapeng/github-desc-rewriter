# github-desc-rewriter

> 把 GitHub 用户名下所有仓库的 description 按统一中文格式批量重写。

## 格式

```
类型 · 是什么 / 能干什么 / 解决什么问题 — 用户痛点
```

实际存储（GitHub API 限制）单行 `/` 分隔，≤ 350 字符。

## 安装

```bash
~/.config/opencode/skills/github-desc-rewriter/install.sh
```

会自动 symlink 到：
- `~/.claude/skills/github-desc-rewriter/` (Claude Code)
- `~/.codex/skills/github-desc-rewriter/` (Codex CLI)
- `~/.config/opencode/skills/github-desc-rewriter/` (OpenCode)
- `~/.easycode/skills/github-desc-rewriter/` (EasyCode)

并把 `command/ghd.md` 复制到 `~/.config/opencode/command/ghd.md` 让 OpenCode 注册 `/ghd` 斜杠命令。

## 触发

- `Claude Code / OpenCode / EasyCode` → `/ghd [owner]`
- `Codex CLI` → `$ghd [owner]`
- 自然语言（任意 host）：
  - 「批量改 GitHub 介绍」
  - 「按 * / * / 解决：* 格式重写所有仓库」
  - 「统一 mcgrapeng 仓库描述格式」
  - 「format my GitHub repos」

`owner` 缺省 `mcgrapeng`。

## 工作流程

```
list_repos.py → /tmp/<owner>_repos.json
                ↓
        宿主 LLM 生成新描述（按 templates/format.md）
                ↓
        /tmp/<owner>_new_descs.json
                ↓
apply_descs.py --dry-run → 宿主 LLM 自检前 10 条
                ↓
apply_descs.py → 批量 PATCH（≤350 字符、429/5xx 重试、单批 sleep）
                ↓
              报告
```

## 手动使用

```bash
# 1. 拉数据
python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/list_repos.py \
  --owner mcgrapeng --out /tmp/mcgrapeng_repos.json

# 2. LLM 生成新描述到 /tmp/mcgrapeng_new_descs.json

# 3. dry-run
python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/apply_descs.py \
  --repos /tmp/mcgrapeng_repos.json \
  --new-descs /tmp/mcgrapeng_new_descs.json \
  --owner mcgrapeng --dry-run

# 4. 真正执行
python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/apply_descs.py \
  --repos /tmp/mcgrapeng_repos.json \
  --new-descs /tmp/mcgrapeng_new_descs.json \
  --owner mcgrapeng
```

## 关键设计

**为什么不让脚本生成描述**：326 个仓库的描述质量必须有 LLM 介入。脚本只做"无脑 IO"，描述生成由宿主 LLM 负责。这样换描述格式（如 `* | * | *`）只需要改 SKILL.md + templates/format.md。

**为什么不读 README**：326 个 README 全读会爆 context。只用仓库名 + 当前 description + language + topics 推断。同类仓库复用同一模板。

## 限制

- GitHub API 限流 5000/小时 → 326 个 PATCH 约 1-2 分钟，安全
- description 硬限制 350 字符；脚本自动截断
- 不允许换行符；脚本自动替换
- 单用户仓库；不跨用户

## 卸载

```bash
~/.config/opencode/skills/github-desc-rewriter/uninstall.sh
```

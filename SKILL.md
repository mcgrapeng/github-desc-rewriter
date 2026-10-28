---
name: github-desc-rewriter
description: 批量按指定格式重写 GitHub 用户所有仓库的 description。流程：API 拉全部仓库 + 当前 description → 宿主 LLM 按统一中文格式生成新描述（是什么: / 能干什么: / 解决: / 何时选: 四段标签式，单行 ≤150 字符）→ 脚本批量 PATCH → 验证。当用户说「把我的 GitHub 仓 description 全部改成中文」「按 是什么/能干什么/解决/何时选 格式重写所有仓库」「批量改 GitHub 介绍」「把我的项目统一格式」时触发。触发短语：「批量改 GitHub 介绍」「统一仓库描述格式」「重写所有仓库 description」「批量改 GitHub description」「format my GitHub repos」。
allowed-tools: Bash, Read, Write, Edit, WebFetch
---

# github-desc-rewriter

> 把 GitHub 用户名下所有仓库的 description（项目简介）按统一中文格式批量重写。
> 格式：**`是什么: X | 能干什么: Y | 解决: Z | 何时选: W`**（单行，标签 + ` | ` 分隔；GitHub API 拒绝换行符；**不带语言前缀**；**总长 ≤ 150 字符**）

**跨平台**：Claude Code (`~/.claude/skills/`) · Codex CLI (`~/.codex/skills/`) · OpenCode (`~/.config/opencode/skills/`) · EasyCode (`~/.easycode/skills/`)。一次 `install.sh` 同时注册四端。

## 何时使用本 skill

- 用户说"把我 GitHub 上所有仓库的 description 都按 是什么: / 能干什么: / 解决: / 何时选: 格式重写一遍"
- 用户给出 GitHub username（缺省 = 当前认证账号），要求批量改简介
- 用户说"统一我所有 GitHub 项目的介绍风格"
- 用户说"按什么什么结构批量改 GitHub repo 描述"
- 用户提供了新的描述模板，要应用到所有仓库

## 触发命令

- **Claude Code / OpenCode / EasyCode**：`/gdr [owner]`（缺省 owner = 当前 GitHub 认证账号：`$GITHUB_USER`，否则 `gh api user`）
- **Codex CLI**：`$gdr [owner]`
- **自然语言**：「批量改 GitHub 介绍」「统一仓库描述」「重写所有仓库 description」

## 宿主 LLM 的执行流程（**宿主 LLM 必须按顺序执行**）

> **前置**: 宿主 LLM 须确认 `GITHUB_TOKEN` 已设置。来源优先级: shell `export` > 工程根目录 `.env` 文件 > 报错。脚本对无 token 情况会 `RuntimeError` 退出。`.env` 在 `.gitignore`，**永不可提交**；可参考 `.env.example`。

### 阶段 1 — 拉数据（脚本完成）

```bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || dirname "$(which gdr 2>/dev/null)")"
# 兜底用绝对路径
SKILL_DIR="${SKILL_DIR:-~/.config/opencode/skills/github-desc-rewriter}"
python3 "$SKILL_DIR/scripts/list_repos.py" --owner <owner> --out /tmp/<owner>_repos.json
```

`list_repos.py` 输出 JSON：
```json
[
  {"name": "awesome-llm", "description": "...", "language": "Python", "topics": [...], "stars": 0, "updated_at": "..."},
  ...
]
```

### 阶段 2 — 生成新描述（**宿主 LLM 介入**，核心环节）

宿主 LLM 读取 `/tmp/<owner>_repos.json`，对**每个仓库**生成一条新 description，**严格遵循**以下格式（单行，四段标签，≤ 150 字符）：

```
是什么: 一句话说明项目本体 | 能干什么: 具体能力 | 解决: 用户痛点 | 何时选: 决策建议
```

示例（实测可用）：
- `是什么: 聚合 GitHub/HuggingFace/arXiv 的 AI 项目雷达 | 能干什么: 抓趋势榜并按 20 个用途分类 | 解决: 找 AI 工具要在多平台来回跳 | 何时选: 想一站式找最新 AI 项目时`
- `是什么: 自托管 PaaS,开源替代 Vercel/Heroku | 能干什么: 一条命令部署应用与数据库,自动 TLS | 解决: 被商业 PaaS 锁定,升级降价受制于人 | 何时选: 想自己掌控数据与部署链路时`

**生成规则**（宿主 LLM 必须遵守）：
1. **不读 README** — 只看仓库名 + 当前 description + topics + language，**绝不读 README**，避免几百个仓库的 context 爆炸
2. **不知道就说不知道** — 信息不足时基于现有 description 推断，宁可写"X 资源合集"也不要编造细节
3. **单行** — 严禁 `\n`（API 返回 422）、emoji 装饰
4. **四段标签齐全** — `是什么:` `能干什么:` `解决:` `何时选:` 一个都不能少，段间用 ` | `（空格 + 半角竖线 + 空格）分隔
5. **总长 ≤ 150 字符** — 每段 20-35 字，精炼具体；硬上限 350（GitHub API 限制,超出脚本会截断）
6. **统一使用半角符号** — `: `、`,`，不用全角
7. **分组复用模板** — 同类仓库用同一模板（如 awesome-* 都用 "X 精选列表 / 分类浏览与检索 / X 资源分散 / 找 X 资源时"）
8. **不加语言前缀** — 描述以「是什么」开头，不用 `Python · `、`TS · ` 等语言/类型前缀

输出：构造一个 Python dict，写入 `/tmp/<owner>_new_descs.json`：
```json
{"awesome-llm": "...", "my-cli-tool": "...", ...}
```

### 阶段 3 — 应用（脚本完成，带 dry-run 守卫）

```bash
python3 "$SKILL_DIR/scripts/apply_descs.py" \
  --repos /tmp/<owner>_repos.json \
  --new-descs /tmp/<owner>_new_descs.json \
  --owner <owner> \
  --dry-run    # 先 dry-run 一次,宿主 LLM 检查 5-10 条描述是否合格
# 宿主 LLM 检查后再去掉 --dry-run 真正执行
python3 "$SKILL_DIR/scripts/apply_descs.py" \
  --repos /tmp/<owner>_repos.json \
  --new-descs /tmp/<owner>_new_descs.json \
  --owner <owner>
```

### 阶段 4 — 报告

`apply_descs.py` 输出：
- 成功 N / 失败 M / 跳过 K（unchanged）
- 失败列表（如有）

宿主 LLM 把结果用一段中文报告给用户。

## 关键设计：为什么不一次性脚本生成

- 上百个仓库的描述生成**必须有 LLM 介入**，否则只能用通用模板糊弄
- 脚本只做"无脑 IO"（拉数据 + PATCH），描述质量靠宿主 LLM
- 这样做的好处：换个描述格式只需要改 SKILL.md 阶段 2，脚本不动

## 限制

- GitHub API 限流：5000 次/小时（认证用户）。几百个 PATCH 约 1-2 分钟，**安全**
- GitHub description 硬限制 350 字符；目标 ≤150，脚本会校验，超出则截断并 warn
- **不允许换行符**（API 422 `description control characters are not allowed`）；只能靠 ` | ` 和标签制造层次
- 单 GitHub 用户的仓库；不跨用户

## 输入文件

无（用户只需说"批量改我 GitHub 介绍"）。

## 输出

直接修改远端 GitHub 仓库 description。脚本会先把旧描述备份到 `/tmp/github-desc/backup_<owner>_<时间戳>.json`，可回滚；dry-run 阶段仍必须让用户确认。

## 触发短语（自然语言）

- 「批量改 GitHub 介绍」
- 「按 是什么/能干什么/解决/何时选 格式重写所有仓库」
- 「统一仓库描述格式」
- 「重写所有仓库 description」
- 「format my GitHub repos」
- 「按这个格式批量改」

## 安装

```bash
~/.config/opencode/skills/github-desc-rewriter/install.sh
~/.config/opencode/skills/github-desc-rewriter/uninstall.sh
```

## 手动调用

凭据用 `.env` 管（`cp .env.example .env` 后填入），也支持 shell `export` 覆盖。
owner 省略时自动取当前认证账号（`$GITHUB_USER` → `gh api user`）：

```bash
# 1. 拉仓库
python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/list_repos.py \
  --out /tmp/<owner>_repos.json

# 2. 让 LLM 生成新描述 → /tmp/<owner>_new_descs.json

# 3. dry-run
python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/apply_descs.py \
  --repos /tmp/<owner>_repos.json \
  --new-descs /tmp/<owner>_new_descs.json \
  --dry-run

# 4. 真正执行
python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/apply_descs.py \
  --repos /tmp/<owner>_repos.json \
  --new-descs /tmp/<owner>_new_descs.json
```

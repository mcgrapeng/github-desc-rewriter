<p align="center">
  <img src="assets/logo-lockup.svg" alt="github-desc-rewriter" width="320">
</p>

<p align="center">
  <strong>把 GitHub 用户名下所有仓库的 description 按统一中文格式批量重写。</strong><br>
  <em>Batch-rewrite every GitHub repo description under one owner into a single, structured Chinese format.</em>
</p>

<p align="center">
  <a href="https://github.com/mcgrapeng/github-desc-rewriter"><img alt="Repo" src="https://img.shields.io/badge/repo-github--desc--rewriter-0f172a?style=flat-square&logo=github"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.8%2B-3776ab?style=flat-square&logo=python&logoColor=white">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-✓-d97757?style=flat-square">
  <img alt="Codex CLI" src="https://img.shields.io/badge/Codex%20CLI-✓-000?style=flat-square">
  <img alt="OpenCode" src="https://img.shields.io/badge/OpenCode-✓-7c3aed?style=flat-square">
  <img alt="EasyCode" src="https://img.shields.io/badge/EasyCode-✓-2563eb?style=flat-square">
  <img alt="API" src="https://img.shields.io/badge/GitHub%20API-v3-181717?style=flat-square&logo=github">
</p>

<p align="center">
  <a href="#-中文">中文</a> · <a href="#-english">English</a> · <a href="#安装--installation">安装</a> · <a href="#格式规范--format-spec">格式规范</a>
</p>

---

## 📝 中文

### 它是什么

`github-desc-rewriter`（命令别名 `/gdr`）是一个跨 agent 平台的 **GitHub 仓库 description 批量重写器**。它一次脚本调用，从 GitHub API 拉出指定用户名下的所有仓库，让宿主 LLM 按结构化模板逐条生成新 description，再用脚本批量 PATCH 回去。

**目标格式**（单行、`/` 分隔，≤ 350 字符）：

```
类型 · 是什么 / 能干什么 / 解决什么问题 — 用户痛点
```

### 解决什么问题

- **风格零散**：几十上百个仓库的 description 风格不一，新访客一眼看不出项目是干什么的
- **不会写简介**：写仓库时只写 "init commit" 或抄模板，没体现"做什么 / 解决什么"
- **格式不可执行**：手动改 326 个仓库枯燥易错，需要工具但不想造轮子
- **中文上下文**：海外仓库多是英文描述，但国内/中文用户浏览 GitHub 同样需要一个中文入口

### 核心特性

- **跨 4 家 agent 平台** —— 一次 `install.sh` 同时注册到 Claude Code / Codex CLI / OpenCode / EasyCode
- **LLM 在格式是核心** —— 脚本只做"无脑 IO"（拉数据 + PATCH），质量由宿主 LLM 兜底；换描述格式只需改 `templates/format.md`
- **不读 README** —— 326 个 README 全读会爆 context，只用仓库名 + 原 description + language + topics 推断
- **安全守卫** —— `--dry-run` 先打 10 条让宿主 LLM 自检；350 字符硬截断；`\n` 自动替换为 `/`；429/5xx 自动退避重试
- **零依赖** —— Python 3.8+ 标准库 `urllib` + `json`，无 pip install

### 工作流

```
┌──────────────────────────────────────────────────────────────┐
│ scripts/list_repos.py --owner <owner>                        │
│   └─→ /tmp/<owner>_repos.json   (name, desc, lang, topics…)   │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 宿主 LLM (Claude / Codex / OpenCode / EasyCode)              │
│   └─ 读 JSON → 按 templates/format.md 生成新 description     │
│   └─→ /tmp/<owner>_new_descs.json   {name: new_desc}         │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ scripts/apply_descs.py --dry-run    ← 宿主 LLM 自检前 10 条   │
│ scripts/apply_descs.py              ← 真执行批量 PATCH        │
│   · 跳过 unchanged · 350 字符截断 · \n → / · 429/5xx 退避     │
│   · 25 个/批 sleep 0.3s · 报告 成功 N / 失败 M / 跳过 K      │
└──────────────────────────────────────────────────────────────┘
```

### 安装

```bash
# 前置：clone 仓库到本地任意目录，复制 .env.example 为 .env 并填入 GITHUB_TOKEN
git clone https://github.com/mcgrapeng/github-desc-rewriter.git
cd github-desc-rewriter
cp .env.example .env
# 编辑 .env：GITHUB_TOKEN=ghp_xxx  (classic PAT, scope: repo 读写)

# 一键安装（symlink 到 4 家 agent 的 skills 目录 + 注册 /gdr 命令）
./install.sh

# 卸载
./uninstall.sh
```

**手动指定 GitHub 用户**（缺省 `mcgrapeng`）：

```bash
GITHUB_USER=yourname ./install.sh   # 仅首次安装提示
```

### 使用

四种 agent 任一即可触发，自然语言也认：

| Agent | 命令 |
|---|---|
| Claude Code | `/gdr [owner]` |
| Codex CLI | `$gdr [owner]` |
| OpenCode | `/gdr [owner]` |
| EasyCode | `/gdr [owner]` |

触发后，宿主 LLM 会自动按 `SKILL.md` 的 4 阶段执行（`list → generate → apply`）。

**自然语言触发**（四家都支持）：

- 「批量改 GitHub 介绍」
- 「按 `* / * / 解决：*` 格式重写所有仓库」
- 「统一仓库描述格式」
- 「format my GitHub repos」

### 手动调用

凭据读取优先级：**shell `export` > 工程根目录 `.env`（gitignored）**。

```bash
export GITHUB_TOKEN=ghp_xxx   # classic PAT, scope: repo (read+write)

# 1. 拉仓库
python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/list_repos.py \
  --owner mcgrapeng --out /tmp/mcgrapeng_repos.json

# 2. 让 LLM 生成新描述到 /tmp/mcgrapeng_new_descs.json

# 3. dry-run（必跑）
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

### 文件结构

```
github-desc-rewriter/
├── SKILL.md               ← agent 读取的指令（核心）
├── README.md              ← 你正在看这个
├── install.sh             ← 一键安装（symlink 4 家）
├── uninstall.sh           ← 一键卸载
├── .env.example           ← 凭据模板（gitignored .env）
├── command/
│   └── gdr.md             ← OpenCode /gdr 斜杠命令源
├── scripts/
│   ├── list_repos.py      ← 拉全部仓库 + 元数据到 JSON
│   └── apply_descs.py     ← 批量 PATCH（dry-run / sanitize / 重试）
├── templates/
│   └── format.md          ← 描述格式模板（描述生成器读这个）
└── assets/
    ├── logo.svg           ← 图标
    └── logo-lockup.svg    ← README 横幅（含 wordmark）
```

### 关键设计

> **为什么不让脚本生成 description？** 326 个仓库的描述质量**必须**有 LLM 介入，否则只能用通用模板糊弄。脚本只做"无脑 IO"，描述生成由宿主 LLM 负责。换描述格式（如 `* | * | *`）只需改 `templates/format.md`，脚本不动。

> **为什么不读 README？** 326 个 README 全读会爆 context。只用仓库名 + 当前 description + language + topics 推断。同类仓库复用同一模板（如 awesome-* 列表统一一个句式）。

### 限制

| 项 | 说明 |
|---|---|
| GitHub API 限流 | 5000 次/小时（认证用户），326 个 PATCH ≈ 1-2 分钟，安全 |
| description 长度 | 硬限制 350 字符；脚本在语义边界（空格/标点）截断，超过会 warn |
| 换行符 | GitHub API 拒绝（422）；脚本自动替换 `\n` → `/` |
| 范围 | 单 GitHub 用户；不跨组织、不跨用户 |
| 不可逆 | 直接修改远端 description，dry-run 阶段必须确认 |

### 故障排查

| 现象 | 原因 / 修法 |
|---|---|
| `RuntimeError: GITHUB_TOKEN env var is required` | 没设 token：要么 `export GITHUB_TOKEN=ghp_xxx`，要么 `.env` 里填 |
| 大量 `429` | 触发了 API 限流；脚本已自动退避重试 3 次；如继续失败，等一晚再跑 |
| `422 ...` | description 含 GitHub 不接受的内容（极少）；检查 `apply_descs.py` sanitize 输出 |
| `/gdr` 没识别 | `install.sh` 没跑，或 4 家平台对 agent 不覆盖；自然语言 ↔ keyword 仍可触发 |
| owner 想换人 | `/gdr yourname`，或编辑 `command/gdr.md` 里的默认 |

---

## 🌐 English

<details>
<summary><strong>Click to expand the English version</strong></summary>

### What it is

`github-desc-rewriter` (slash command `/gdr`) is a **cross-agent GitHub repo-description batch rewriter**. In one run, it pulls every repo under a GitHub owner via the REST API, asks the host LLM to mint a new structured description per repo, and PATCHes them all back.

**Target format** (single line, `/` separated, ≤ 350 chars):

```
<type> · what-it-is / what-it-does / problem-it-solves — user pain point
```

### Why it exists

- **Inconsistent style** — dozens or hundreds of repos, each with a different description; visitors can't tell what a project does at a glance
- **Description paralysis** — devs leave `init commit` or copy a template; "what / why" never gets written
- **Manual bulk-edit error-prone** — re-writing 326 repos by hand is tedious; needs tooling but not a new framework
- **Bilingual audience** — Chinese-speaking devs browsing English repos need a Chinese entry point

### Key features

- **Cross-platform** — one `install.sh` symlinks into Claude Code / Codex CLI / OpenCode / EasyCode
- **LLM-in-the-loop for quality** — scripts only do dumb IO (GET + PATCH); description quality is the host LLM's job; swap formats by editing `templates/format.md` only
- **No README reads** — reading 326 READMEs would blow the context budget; inference uses `name + old description + language + topics` only
- **Safety nets** — `--dry-run` previews the first 10; 350-char hard truncation; `\n` → `/` rewrite; 429/5xx exponential backoff
- **Zero deps** — Python 3.8+ stdlib only (`urllib`, `json`); no `pip install`

### Workflow

```
┌──────────────────────────────────────────────────────────────┐
│ scripts/list_repos.py --owner <owner>                        │
│   └─→ /tmp/<owner>_repos.json   (name, desc, lang, topics…)   │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Host LLM (Claude / Codex / OpenCode / EasyCode)              │
│   └─ reads JSON → generates per templates/format.md           │
│   └─→ /tmp/<owner>_new_descs.json   {name: new_desc}         │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ scripts/apply_descs.py --dry-run    ← host LLM reviews 10     │
│ scripts/apply_descs.py              ← batch PATCH             │
│   · skip unchanged · 350-char truncate · \n → / · 429 retry   │
│   · sleep 0.3s / 25 items · report N ok / M fail / K skip     │
└──────────────────────────────────────────────────────────────┘
```

### Install

```bash
git clone https://github.com/mcgrapeng/github-desc-rewriter.git
cd github-desc-rewriter
cp .env.example .env
# edit .env: GITHUB_TOKEN=ghp_xxx  (classic PAT, scope: repo read+write)

./install.sh

# uninstall
./uninstall.sh
```

### Usage

Pick any of the four agents and trigger by command or natural language.

| Agent | Slash | Token |
|---|---|---|
| Claude Code | `/gdr [owner]` | — |
| Codex CLI | `$gdr [owner]` | `$ARGUMENTS` |
| OpenCode | `/gdr [owner]` | — |
| EasyCode | `/gdr [owner]` | — |

The host LLM then executes the 4 phases in `SKILL.md` (`list → generate → apply`).

**Natural-language triggers** (any host):

- "batch rewrite GitHub descriptions"
- "rewrite all my repos in * / * / solves: * format"
- "unify repo description style"
- "format my GitHub repos"

### Manual run

Token precedence: **shell `export` > repo `.env`** (gitignored).

```bash
export GITHUB_TOKEN=ghp_xxx

python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/list_repos.py \
  --owner mcgrapeng --out /tmp/mcgrapeng_repos.json

# Ask the LLM to write /tmp/mcgrapeng_new_descs.json

python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/apply_descs.py \
  --repos /tmp/mcgrapeng_repos.json \
  --new-descs /tmp/mcgrapeng_new_descs.json \
  --owner mcgrapeng --dry-run

python3 ~/.config/opencode/skills/github-desc-rewriter/scripts/apply_descs.py \
  --repos /tmp/mcgrapeng_repos.json \
  --new-descs /tmp/mcgrapeng_new_descs.json \
  --owner mcgrapeng
```

### Layout

```
github-desc-rewriter/
├── SKILL.md               ← agent instructions (core)
├── README.md              ← you are here
├── install.sh / uninstall.sh
├── .env.example           ← token template (gitignored .env)
├── command/gdr.md         ← OpenCode /gdr slash source
├── scripts/
│   ├── list_repos.py      ← GET repos + metadata → JSON
│   └── apply_descs.py     ← batch PATCH (dry-run / sanitize / retry)
├── templates/format.md    ← description format template
└── assets/
    ├── logo.svg           ← mark
    └── logo-lockup.svg    ← README banner (with wordmark)
```

### Design notes

> **Why no in-script description generation?** 326 repos need an LLM in the loop; a templated script would produce garbage. Scripts do dumb IO; the host LLM owns quality. To switch formats (`* | * | *`), edit `templates/format.md` only.

> **Why no README reads?** Reading 326 READMEs would blow context. Inference uses `name + current description + language + topics`. Same-template repos (e.g. all `awesome-*`) reuse one sentence.

### Limits

| Item | Detail |
|---|---|
| GitHub API rate limit | 5000/hr authenticated; 326 PATCHes ≈ 1–2 min, safe |
| Description length | 350-char hard cap; script truncates at semantic boundary (space/punct) and warns |
| Newlines | GitHub rejects (422); script replaces `\n` → `/` |
| Scope | single GitHub user; not cross-org or cross-user |
| Reversibility | directly mutates remote; dry-run is mandatory before the real run |

### Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `RuntimeError: GITHUB_TOKEN env var is required` | token missing: `export GITHUB_TOKEN=ghp_xxx` or fill `.env` |
| Many `429` | hit rate limit; script already retries 3×; if it persists try next day |
| `422 ...` | description contains content GitHub rejects (rare); inspect `apply_descs.py` sanitize output |
| `/gdr` not recognized | `install.sh` not run, or host not in the four; natural-language keywords still work |
| Switch default owner | `/gdr yourname`, or edit `command/gdr.md` default |

</details>

---

## 格式规范 / Format Spec

> 详细规则见 [`templates/format.md`](templates/format.md)。下面是精简版。

### 模板

```
<类型> · 一句话是什么 / 能干什么：做了什么 / 解决什么问题 — 用户痛点：具体痛点
```

### 硬约束

| 约束 | 值 | 来源 |
|---|---|---|
| 总长 | ≤ 350 字符 | GitHub API 硬约束 |
| 换行 | 不允许（用 `/` 分隔） | API 422 |
| 符号 | 半角 `:` `,` `/` `—` | 风格统一 |
| emoji | 不用 | 不必要 |

### 类型前缀

`Python · ` · `TS · ` · `Rust · ` · `Go · ` · `Java · ` · `HTML · ` · `CC0 · ` · `Other · `

### 同类复用模板

| 类型 | 模板 |
|---|---|
| awesome-* 列表 | `CC0 · X 精选 / 浏览与发现 / 解决:X 资源分散` |
| skill 集合 | `X · Skill 集合 / 提供 X 工作流 / 解决:X 重复搭建` |
| RAG 框架 | `Python · RAG 框架 / 提供 X 检索 / 解决:文档/检索需从零搭` |
| Agent 框架 | `X · Agent 框架 / 提供 X 编排 / 解决:多 Agent 协作难统一` |
| 编码 Agent | `X · 编码 Agent / 提供 X 编程入口 / 解决:AI 编码工具商业版受限` |
| CLI 工具 | `X · 终端工具 / 提供 X / 解决:命令行操作靠记忆` |
| TUI | `X · 终端 UI / 提供 X 交互 / 解决:网页/CLI 反复切` |
| 中文教程 | `Python · 中文教程 / 提供 X 学习路径 / 解决:中文资料零散` |
| MCP server | `X · MCP Server / 提供 X 能力给 Agent / 解决:Agent 缺 X 工具` |
| Java 源码仓 | `Java · X 源码阅读 / 提供 X 内部机制 / 解决:只会用不会排查` |
| Fork 镜像 | 原始仓按实际功能写；fork 镜像保留上游定位 + 加一句"镜像" |

### 示例（实测可用）

```
Python · 实时聚合 GitHub/HF/MCP/arXiv 的 AI 项目情报多源雷达 / 抓趋势榜+20 用途分类+生成中文仪表盘 / 解决:多平台来回跳找 AI 工具、缺统一筛选入口
```

```
TS · 自托管 PaaS 平台, Vercel/Netlify/Heroku 开源替代 / 部署应用、数据库、容器 / 解决:用商业 PaaS 被锁定 + 贵
```

```
Rust · 命令行模糊查找器(文件/命令/历史/列表) / 交互式模糊匹配快速定位 / 解决:终端中候选项多精确输入效率低
```

### 反例（不要这样写）

```
❌ 多行 — GitHub 拒绝
❌ 超长（> 350 字符）— 应拆短
❌ 🚀 emoji: 装饰 📊 — 风格不一致
```

---

## 相关链接 / Links

- 仓库: <https://github.com/mcgrapeng/github-desc-rewriter>
- Skill 定义: [`SKILL.md`](SKILL.md)
- 描述模板: [`templates/format.md`](templates/format.md)
- 安装: [`install.sh`](install.sh)
- 卸载: [`uninstall.sh`](uninstall.sh)

---

<p align="center">
  <sub>Built for <a href="https://docs.anthropic.com/en/docs/claude-code">Claude Code</a> · <a href="https://github.com/openai/codex">Codex CLI</a> · <a href="https://opencode.ai">OpenCode</a> · <a href="https://easycode.market">EasyCode</a></sub>
</p>
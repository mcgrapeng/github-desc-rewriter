#!/usr/bin/env bash
# install.sh — install github-desc-rewriter skill for
# Claude Code / Codex CLI / OpenCode / EasyCode.
#
# Strategy: symlink (single source of truth, no duplication).
# OpenCode also gets command/gdr.md copied to ~/.config/opencode/command/.

set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="github-desc-rewriter"
CMD="gdr"

CLAUDE_DIR="${HOME}/.claude/skills"
CODEX_DIR="${HOME}/.codex/skills"
OPENCODE_SKILLS_DIR="${HOME}/.config/opencode/skills"
OPENCODE_COMMAND_DIR="${HOME}/.config/opencode/command"
EASYCODE_DIR="${HOME}/.easycode/skills"

ok()   { printf "  \033[32m✓\033[0m %s\n" "$*"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$*"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$*"; exit 1; }

echo ""
echo "⚡ github-desc-rewriter · /gdr skill (Claude Code + Codex + OpenCode + EasyCode)"
echo "   源目录: $HERE"
echo ""

[ -f "$HERE/SKILL.md" ] || fail "SKILL.md not found in $HERE"
[ -x "$HERE/scripts/list_repos.py" ] || chmod +x "$HERE/scripts/list_repos.py"
[ -x "$HERE/scripts/apply_descs.py" ] || chmod +x "$HERE/scripts/apply_descs.py"

link_one() {
    local label="$1"; local dir="$2"
    echo ""
    echo "📦 $label ($dir/$NAME)"
    mkdir -p "$dir" 2>/dev/null || true
    [ -d "$dir" ] || { warn "目录不存在,跳过 ($dir)"; return 0; }
    if [ -L "$dir/$NAME" ]; then
        warn "已存在 symlink → $(readlink "$dir/$NAME")，重新指向"
        rm "$dir/$NAME"
    elif [ -e "$dir/$NAME" ]; then
        warn "已存在实体目录,备份为 ${NAME}.bak"
        mv "$dir/$NAME" "${dir}/${NAME}.bak.$(date +%s)"
    fi
    ln -s "$HERE" "$dir/$NAME"
    ok "symlinked"
}

install_opencode_commands() {
    local cmd_dir="$1"
    echo ""
    echo "📦 OpenCode slash commands ($cmd_dir)"
    mkdir -p "$cmd_dir" 2>/dev/null || true
    [ -d "$cmd_dir" ] || { warn "目录不存在,跳过 ($cmd_dir)"; return 0; }
    local src="$HERE/command/$CMD.md"
    local dst="$cmd_dir/$CMD.md"
    [ -f "$src" ] || { warn "工程里缺 $src,跳过"; return 0; }
    if [ -e "$dst" ]; then
        if cmp -s "$src" "$dst"; then
            ok "$CMD.md 已就位且一致"
        else
            warn "$dst 已存在且内容不同,备份为 ${dst}.bak.$(date +%s)"
            mv "$dst" "${dst}.bak.$(date +%s)"
            cp "$src" "$dst"
            ok "$CMD.md 已更新"
        fi
    else
        cp "$src" "$dst"
        ok "$CMD.md 已建好"
    fi
}

link_one "Claude Code" "$CLAUDE_DIR"
link_one "Codex CLI"   "$CODEX_DIR"
link_one "OpenCode"    "$OPENCODE_SKILLS_DIR"
link_one "EasyCode"    "$EASYCODE_DIR"
install_opencode_commands "$OPENCODE_COMMAND_DIR"

echo ""
echo "🎉 安装完成!"
echo ""
echo "触发方式:"
echo "  Claude Code → /gdr [owner]   (owner 缺省 mcgrapeng)"
echo "  Codex CLI   → \$gdr [owner]"
echo "  OpenCode    → /gdr [owner]"
echo "  EasyCode    → /gdr [owner]"
echo ""
echo "自然语言触发(四家都支持):"
echo "  「批量改 GitHub 介绍」「按 * / * / 解决：* 重写所有仓库 description」"
echo "  「统一仓库描述格式」"
echo ""
echo "前置条件:"
echo "  • cp .env.example .env   然后编辑填入真实 GITHUB_TOKEN (scope: repo 读写)"
echo "  • .env 已 gitignore, 不会被提交"
echo ""
echo "卸载:"
echo "  $HERE/uninstall.sh"
echo ""

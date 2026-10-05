#!/usr/bin/env bash
# uninstall.sh — remove github-desc-rewriter symlinks + OpenCode command wrapper

set -e
NAME="github-desc-rewriter"
CMD="gdr"

remove_symlink() {
    local target="$1"
    if [ -L "$target" ]; then
        rm "$target"
        echo "  ✓ removed $target"
    elif [ -e "$target" ]; then
        echo "  ! $target exists but is not a symlink (skipping)"
    else
        echo "  · $target not installed"
    fi
}

remove_file() {
    local target="$1"
    if [ -e "$target" ]; then
        rm "$target"
        echo "  ✓ removed $target"
    else
        echo "  · $target not installed"
    fi
}

echo "🧹 Removing github-desc-rewriter skill..."
for D in \
    "${HOME}/.claude/skills" \
    "${HOME}/.codex/skills" \
    "${HOME}/.config/opencode/skills" \
    "${HOME}/.easycode/skills"; do
    echo ""
    echo "📦 $D"
    remove_symlink "$D/$NAME"
done

echo ""
echo "📦 ${HOME}/.config/opencode/command  (OpenCode slash-command wrapper)"
remove_file "${HOME}/.config/opencode/command/${CMD}.md"

echo ""
echo "🎉 卸载完成。"

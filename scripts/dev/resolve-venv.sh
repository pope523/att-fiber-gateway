#!/usr/bin/env bash
# Shared venv resolution for all dev scripts and pre-commit hooks.
#
# Resolves the project's .venv directory, even from a git worktree
# where .venv doesn't exist locally. Git worktrees share the main
# repo's venv via `git rev-parse --git-common-dir`.
#
# Usage (source this, don't execute):
#   source "$(dirname "${BASH_SOURCE[0]}")/resolve-venv.sh"
#   # Now $VENV_ROOT is set to the absolute path of .venv
#   # $VENV_ROOT/bin/python, $VENV_ROOT/bin/pytest, etc.
#
# Priority:
#   1. Local .venv (normal clone or dev container)
#   2. Main worktree's .venv (git worktree)
#
# If neither exists, VENV_ROOT is empty and VENV_PYTHON falls back
# to pyenv or system python.

# Resolve the main git worktree root. In a normal repo this returns
# the repo root; in a worktree it returns the original clone's root.
_resolve_main_root() {
    local git_common_dir
    git_common_dir="$(git rev-parse --git-common-dir 2>/dev/null)" || return 1
    dirname "$git_common_dir"
}

# Find .venv: local first, then main worktree.
# In a worktree, creates a .venv symlink so that all tools (pyright,
# Pylance, VS Code tasks, hardcoded paths) work without configuration.
# The symlink is gitignored.
_resolve_venv_root() {
    if [[ -d ".venv" ]]; then
        echo "$(pwd)/.venv"
        return
    fi

    local main_root
    main_root="$(_resolve_main_root)"
    if [[ -n "$main_root" && -d "$main_root/.venv" ]]; then
        # Create symlink so pyrightconfig.json, VS Code, and all
        # hardcoded .venv paths work transparently in the worktree
        if [[ ! -e ".venv" ]]; then
            ln -s "$main_root/.venv" ".venv" 2>/dev/null || true
        fi
        echo "$main_root/.venv"
        return
    fi
}

# Find the best available Python interpreter
_resolve_python() {
    if [[ -n "$VENV_ROOT" && -x "$VENV_ROOT/bin/python" ]]; then
        echo "$VENV_ROOT/bin/python"
        return
    fi

    # Pyenv fallbacks
    if [[ -x "$HOME/.pyenv/versions/3.12.12/bin/python" ]]; then
        echo "$HOME/.pyenv/versions/3.12.12/bin/python"
        return
    fi
    if command -v python3 &>/dev/null; then
        echo "python3"
        return
    fi
    if command -v python &>/dev/null; then
        echo "python"
        return
    fi

    echo "ERROR: No Python interpreter found" >&2
    return 1
}

# Export resolved paths
VENV_ROOT="$(_resolve_venv_root)"
VENV_PYTHON="$(_resolve_python)"

export VENV_ROOT VENV_PYTHON

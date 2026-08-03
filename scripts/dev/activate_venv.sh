#!/bin/bash
# VS Code terminal auto-activation script for Bash/Zsh
# This runs automatically when you open a terminal in VS Code.
# Worktree-aware: resolves .venv from the main repo if needed.

source "$(dirname "${BASH_SOURCE[0]}")/resolve-venv.sh"

if [[ -n "$VENV_ROOT" && -f "$VENV_ROOT/bin/activate" ]]; then
    source "$VENV_ROOT/bin/activate"
    clear
    echo ""
    cat "${BASH_SOURCE%/*}/next_steps.txt"
    echo ""
else
    cat "${BASH_SOURCE%/*}/welcome_message.txt"
    echo ""
fi

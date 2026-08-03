#!/usr/bin/env bash
# Worktree-aware Python runner for pre-commit hooks and scripts.
# Delegates venv resolution to resolve-venv.sh.
set -e

source "$(dirname "${BASH_SOURCE[0]}")/resolve-venv.sh"

$VENV_PYTHON "$@"

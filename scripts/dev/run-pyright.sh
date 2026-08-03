#!/usr/bin/env bash
# Worktree-aware pyright runner for pre-commit hooks.
# Delegates venv resolution to resolve-venv.sh.
set -e

source "$(dirname "${BASH_SOURCE[0]}")/resolve-venv.sh"

if [[ -n "$VENV_ROOT" && -x "$VENV_ROOT/bin/pyright" ]]; then
    exec "$VENV_ROOT/bin/pyright" "$@"
fi

echo "ERROR: pyright not found in .venv or main worktree" >&2
exit 1

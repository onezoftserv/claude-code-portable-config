#!/usr/bin/env bash
# Install or upgrade: this script clones on first run, `git pull`s on every
# run after that. Re-running it later IS the upgrade command — there's no
# separate one.
#
#   curl -fsSL https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.sh | bash
set -euo pipefail

REPO_URL="https://github.com/onezoftserv/claude-code-portable-config.git"
DEST="${CLAUDE_PORTABLE_CONFIG_DIR:-$HOME/.claude-portable-config}"

if [ -d "$DEST/.git" ]; then
  echo "Updating existing clone at $DEST"
  git -C "$DEST" pull --ff-only
else
  echo "Cloning into $DEST"
  git clone --depth 1 "$REPO_URL" "$DEST"
fi

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "python3 (or python) not found on PATH — install Python first." >&2
  exit 1
fi

echo "Running installer with $PYTHON_BIN"
exec "$PYTHON_BIN" "$DEST/scripts/install.py" "$@"

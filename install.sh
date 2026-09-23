#!/usr/bin/env bash
# Install or upgrade: this script sets up on first run, re-fetches on every
# run after that. Re-running it later IS the upgrade command — there's no
# separate one.
#
#   curl -fsSL https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.sh | bash
#
# Pin to a branch, tag, or FULL (not abbreviated) commit SHA instead of
# main. The env var must be a prefix on `bash`, the right side of the
# pipe — putting it before `curl` scopes it to curl instead and silently
# installs main:
#   curl -fsSL .../install.sh | CLAUDE_PORTABLE_CONFIG_REF=v1.0.0 bash
set -euo pipefail

REPO_URL="https://github.com/onezoftserv/claude-code-portable-config.git"
DEST="${CLAUDE_PORTABLE_CONFIG_DIR:-$HOME/.claude-portable-config}"
REF="${CLAUDE_PORTABLE_CONFIG_REF:-main}"

if [ ! -d "$DEST/.git" ]; then
  echo "Setting up $DEST"
  git init -q "$DEST"
  git -C "$DEST" remote add origin "$REPO_URL"
fi

echo "Fetching $REF into $DEST"
git -C "$DEST" fetch --depth 1 origin "$REF"
git -C "$DEST" checkout --quiet --detach FETCH_HEAD

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "python3 (or python) not found on PATH — install Python first." >&2
  exit 1
fi

echo "Running installer with $PYTHON_BIN"
exec "$PYTHON_BIN" "$DEST/scripts/install.py" "$@"

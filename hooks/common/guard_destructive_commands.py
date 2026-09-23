#!/usr/bin/env python3
"""PreToolUse hook for Bash and PowerShell.

Asks for confirmation before genuinely destructive commands, even if a
permission rule would otherwise auto-allow them. Pure Python, no LLM call,
so it costs zero tokens to run. Both tools pass the shell command as
tool_input.command, so one script covers both.

This is a backstop heuristic, not a shell parser: it strips quoted spans
(so a match inside a commit message or a grep pattern doesn't fire) and
then looks for flag combinations, not full argument parsing. Scoped to
git and filesystem deletion — not a general infra-destruction guard
(terraform/kubectl and friends are out of scope on purpose).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import read_hook_input, write_hook_output

_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")

# git push --force (but not the safe --force-with-lease), git reset --hard,
# git clean -f, git checkout/restore that discards uncommitted changes,
# git branch -D, DROP TABLE.
LINE_PATTERNS = [
    re.compile(r"\bgit\s+push\b(?!.*--force-with-lease)(?:.*\s(?:--force|-f)\b)", re.IGNORECASE),
    re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
    re.compile(r"\bgit\s+clean\b.*(?:--force|-[a-z]*f[a-z]*)\b", re.IGNORECASE),
    re.compile(r"\bgit\s+(?:checkout|restore)\s+(?:--\s+)?\.", re.IGNORECASE),
    re.compile(r"\bgit\s+branch\s+-[a-z]*D\b"),
    re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
]

# rm/del/rmdir/Remove-Item with both a recursive flag and a force flag,
# in any order, short or long form (covers `rm -rf`, `rm -fr`, `rm -r -f`,
# `Remove-Item -Recurse -Force`, `Remove-Item -r -fo`, `rd /s /q`, ...).
DELETE_COMMANDS = re.compile(r"\b(rm|del|rd|rmdir|remove-item|ri)\b", re.IGNORECASE)
RECURSIVE_FLAG = re.compile(r"(--recursive\b|-[a-z]*r[a-z]*\b|/s\b)", re.IGNORECASE)
FORCE_FLAG = re.compile(r"(--force\b|-[a-z]*f[a-z]*\b|/q\b)", re.IGNORECASE)


def is_dangerous(command: str) -> str:
    """Return a human-readable reason if command looks dangerous, else ""."""
    stripped = _QUOTED.sub(" ", command)
    for pattern in LINE_PATTERNS:
        if pattern.search(stripped):
            return f"matched pattern: {pattern.pattern}"
    if DELETE_COMMANDS.search(stripped) and RECURSIVE_FLAG.search(stripped) and FORCE_FLAG.search(stripped):
        return "recursive + forced delete"
    return ""


def main() -> None:
    data = read_hook_input()
    command = (data.get("tool_input") or {}).get("command") or ""
    reason = is_dangerous(command)
    if not reason:
        return
    write_hook_output({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"Destructive-command guard: {reason}",
        }
    })


if __name__ == "__main__":
    main()

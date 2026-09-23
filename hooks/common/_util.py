"""Shared helpers for Claude Code hook scripts.

Hooks receive JSON on stdin and (optionally) write JSON to stdout. Windows
Python defaults stdin/stdout to the system codepage (often cp1252), which
breaks on file paths or command text containing non-ASCII characters. These
helpers force UTF-8 on both ends so a hook behaves the same on every OS.
"""
import json
import sys


def read_hook_input() -> dict:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    return json.loads(raw) if raw.strip() else {}


def write_hook_output(data: dict) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(data))

#!/usr/bin/env python3
"""Install this portable Claude Code config into ~/.claude (or $CLAUDE_CONFIG_DIR).

Run this with whichever Python you use day to day on this machine — the
interpreter running this script (sys.executable) is the one baked into the
hook and statusLine commands in settings.json. The PreToolUse hook uses
exec-form args (no shell); statusLine has no exec-form in the schema, so
its command is a quoted string, which is why it's built to be a no-op
difference between bash, PowerShell and cmd.exe.

Usage:
    python scripts/install.py [--target DIR] [--dry-run] [--force]

--target DIR   Install into DIR instead of ~/.claude / $CLAUDE_CONFIG_DIR.
               Use this to test against a scratch directory first.
--dry-run      Print what would change; write nothing.
--force        Overwrite CLAUDE.md / commands / agents even if the target
               copy differs from this repo (existing copies are backed up
               to *.bak either way when they're about to be overwritten).
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT_NAME = "guard_destructive_commands.py"
HOOK_MATCHER = "Bash|PowerShell"
STATUSLINE_SCRIPT_NAME = "status_line.py"


def resolve_target(cli_target: Optional[str]) -> Path:
    if cli_target:
        return Path(cli_target).expanduser().resolve()
    env_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return Path.home() / ".claude"


def load_json_or_die(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON ({e}). Fix it by hand before re-running.", file=sys.stderr)
        sys.exit(1)


def copy_with_backup(src: Path, dst: Path, force: bool, dry_run: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    new_content = src.read_text(encoding="utf-8")
    if dst.exists():
        old_content = dst.read_text(encoding="utf-8")
        if old_content == new_content:
            print(f"  unchanged  {dst}")
            return
        if not force:
            print(f"  SKIPPED    {dst} (differs from repo copy; rerun with --force to overwrite)")
            return
        if dry_run:
            print(f"  would back up {dst} -> {dst}.bak, then overwrite")
        else:
            shutil.copy2(dst, dst.with_suffix(dst.suffix + ".bak"))
    if dry_run:
        print(f"  would write {dst}")
        return
    dst.write_text(new_content, encoding="utf-8")
    print(f"  wrote      {dst}")


def build_guard_hook(hooks_dir: Path) -> dict:
    return {
        "type": "command",
        "command": sys.executable,
        "args": [str(hooks_dir / HOOK_SCRIPT_NAME)],
        "statusMessage": "Checking command safety...",
    }


def merge_hooks(settings: dict, hooks_dir: Path) -> None:
    """Find any PreToolUse block already running our script (by any matcher,
    so a rename or matcher change still updates in place) and bring it up to
    date; otherwise add a fresh block."""
    hook_entry = build_guard_hook(hooks_dir)
    hooks = settings.setdefault("hooks", {})
    pretooluse = hooks.setdefault("PreToolUse", [])

    owning_block = None
    for block in pretooluse:
        for h in block.get("hooks", []):
            if str(h.get("args", [""])[-1]).endswith(HOOK_SCRIPT_NAME):
                owning_block = block
                break
        if owning_block:
            break

    if owning_block is None:
        pretooluse.append({"matcher": HOOK_MATCHER, "hooks": [hook_entry]})
        return

    owning_block["matcher"] = HOOK_MATCHER
    block_hooks = owning_block.setdefault("hooks", [])
    existing = next(
        (h for h in block_hooks if str(h.get("args", [""])[-1]).endswith(HOOK_SCRIPT_NAME)),
        None,
    )
    if existing is None:
        block_hooks.append(hook_entry)
    else:
        existing.update(hook_entry)


def build_statusline_command(hooks_dir: Path) -> str:
    script = hooks_dir / STATUSLINE_SCRIPT_NAME
    return f'"{sys.executable}" "{script}"'


def merge_statusline(settings: dict, hooks_dir: Path) -> None:
    existing = settings.get("statusLine")
    if existing is not None and STATUSLINE_SCRIPT_NAME not in existing.get("command", ""):
        print(f"  keeping existing statusLine (not ours): {existing.get('command')!r}")
        return
    settings["statusLine"] = {
        "type": "command",
        "command": build_statusline_command(hooks_dir),
    }


def merge_settings(base: dict, existing: dict, hooks_dir: Path) -> dict:
    merged = dict(existing)
    for key, value in base.items():
        if key not in merged:
            merged[key] = value
        elif merged[key] != value:
            print(f"  keeping existing settings.json value for {key!r} ({merged[key]!r}); repo default is {value!r}")
    merge_hooks(merged, hooks_dir)
    merge_statusline(merged, hooks_dir)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", help="Install into this directory instead of ~/.claude")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    target = resolve_target(args.target)
    print(f"Target config directory: {target}")
    print(f"Python interpreter to bake into hooks: {sys.executable}")

    existing_settings_path = target / "settings.json"
    existing_settings = {}
    if existing_settings_path.exists():
        existing_settings = load_json_or_die(existing_settings_path)

    print("\nCLAUDE.md:")
    copy_with_backup(REPO_ROOT / "CLAUDE.md", target / "CLAUDE.md", args.force, args.dry_run)

    print("\nCommands:")
    for src in sorted((REPO_ROOT / "commands").glob("*.md")):
        copy_with_backup(src, target / "commands" / src.name, args.force, args.dry_run)

    print("\nAgents:")
    for src in sorted((REPO_ROOT / "agents").glob("*.md")):
        copy_with_backup(src, target / "agents" / src.name, args.force, args.dry_run)

    print("\nHooks (always synced from repo):")
    hooks_target_dir = target / "hooks"
    for src in sorted((REPO_ROOT / "hooks" / "common").glob("*.py")):
        dst = hooks_target_dir / src.name
        if args.dry_run:
            print(f"  would write {dst}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  wrote      {dst}")

    print("\nsettings.json:")
    base_settings = load_json_or_die(REPO_ROOT / "settings.base.json")
    merged = merge_settings(base_settings, existing_settings, hooks_target_dir)

    if args.dry_run:
        print("  would write (dry run, showing result):")
        print(json.dumps(merged, indent=2))
    else:
        text = json.dumps(merged, indent=2) + "\n"
        json.loads(text)  # re-parse before touching disk
        existing_settings_path.parent.mkdir(parents=True, exist_ok=True)
        existing_settings_path.write_text(text, encoding="utf-8")
        print(f"  wrote      {existing_settings_path}")

    print(
        "\nDone. If Claude Code was already running against this config dir, "
        "open /hooks once (or restart) so it picks up the new hook."
    )


if __name__ == "__main__":
    main()

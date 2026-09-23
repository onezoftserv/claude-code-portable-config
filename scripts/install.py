#!/usr/bin/env python3
"""Install this portable Claude Code config into ~/.claude (or $CLAUDE_CONFIG_DIR).

Run this with whichever Python you use day to day on this machine — the
interpreter running this script (sys.executable) is the one baked into the
hook and statusLine commands in settings.json. sys.executable resolves to
the real interpreter binary (not a Windows Store alias stub), which is
exactly why this script uses it instead of `shutil.which("python")`.

The PreToolUse hook uses exec-form args (no shell involved at all).
statusLine has no exec-form in the schema, so its command is a shell
string; this script checks whether `bash` is resolvable on this machine
(true on Mac/Linux always, true on Windows only with Git Bash installed —
matching Claude Code's own documented hook-shell default) and builds the
statusLine command to match whichever shell will actually run it.

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
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT_NAME = "guard_destructive_commands.py"
HOOK_MATCHER = "Bash|PowerShell"
STATUSLINE_SCRIPT_NAME = "status_line.py"
PERMISSION_LIST_KEYS = ("allow", "ask", "deny")


def resolve_target(cli_target: Optional[str]) -> Path:
    if cli_target:
        return Path(cli_target).expanduser().resolve()
    env_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return Path.home() / ".claude"


def load_json_or_die(path: Path) -> dict:
    try:
        # utf-8-sig transparently strips a BOM if present (common when a
        # settings.json was last saved by Notepad or PowerShell 5) and
        # behaves like plain utf-8 otherwise.
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON ({e}). Fix it by hand before re-running.", file=sys.stderr)
        sys.exit(1)


def copy_with_backup(src: Path, dst: Path, force: bool, dry_run: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    new_content = src.read_text(encoding="utf-8")
    if dst.exists():
        old_content = dst.read_text(encoding="utf-8-sig")
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


def last_arg(hook: dict) -> str:
    args = hook.get("args") or [""]
    return str(args[-1])


def build_guard_hook(hooks_dir: Path) -> dict:
    return {
        "type": "command",
        "command": sys.executable,
        "args": [str(hooks_dir / HOOK_SCRIPT_NAME)],
        "statusMessage": "Checking command safety...",
    }


def merge_hooks(settings: dict, hooks_dir: Path) -> dict:
    """Find any PreToolUse block already running our script (by any matcher,
    so a rename or matcher change still updates in place) and bring it up to
    date; otherwise add a fresh block. Returns the hook entry that ends up
    installed, so the caller can verify it actually fires."""
    hook_entry = build_guard_hook(hooks_dir)
    hooks = settings.setdefault("hooks", {})
    pretooluse = hooks.setdefault("PreToolUse", [])

    owning_block = None
    for block in pretooluse:
        for h in block.get("hooks", []):
            if last_arg(h).endswith(HOOK_SCRIPT_NAME):
                owning_block = block
                break
        if owning_block:
            break

    if owning_block is None:
        pretooluse.append({"matcher": HOOK_MATCHER, "hooks": [hook_entry]})
        return hook_entry

    owning_block["matcher"] = HOOK_MATCHER
    block_hooks = owning_block.setdefault("hooks", [])
    existing = next((h for h in block_hooks if last_arg(h).endswith(HOOK_SCRIPT_NAME)), None)
    if existing is None:
        block_hooks.append(hook_entry)
    else:
        existing.update(hook_entry)
    return hook_entry


def build_statusline_command(hooks_dir: Path) -> str:
    script = hooks_dir / STATUSLINE_SCRIPT_NAME
    quoted = f'"{sys.executable}" "{script}"'
    # A bare `"exe" "arg"` line is valid in bash but a parse error in
    # PowerShell, which needs the call operator. Claude Code runs hooks
    # (and, as far as we can tell, statusLine) through bash when it's
    # resolvable, else PowerShell on Windows — so match that here.
    if shutil.which("bash") is None:
        return f"& {quoted}"
    return quoted


def merge_statusline(settings: dict, hooks_dir: Path) -> None:
    existing = settings.get("statusLine")
    if existing is not None and STATUSLINE_SCRIPT_NAME not in existing.get("command", ""):
        print(f"  keeping existing statusLine (not ours): {existing.get('command')!r}")
        return
    settings["statusLine"] = {
        "type": "command",
        "command": build_statusline_command(hooks_dir),
    }


def merge_permission_lists(merged: dict, base: dict) -> None:
    base_perms = base.get("permissions")
    if not base_perms:
        return
    merged_perms = merged.setdefault("permissions", {})
    for key in PERMISSION_LIST_KEYS:
        base_list = base_perms.get(key)
        if not base_list:
            continue
        existing_list = merged_perms.setdefault(key, [])
        for rule in base_list:
            if rule not in existing_list:
                existing_list.append(rule)


def merge_settings(base: dict, existing: dict, hooks_dir: Path) -> dict:
    merged = dict(existing)
    for key, value in base.items():
        if key == "permissions":
            continue  # handled by merge_permission_lists below
        if key not in merged:
            merged[key] = value
        elif merged[key] != value:
            print(f"  keeping existing settings.json value for {key!r} ({merged[key]!r}); repo default is {value!r}")
    merge_permission_lists(merged, base)
    hook_entry = merge_hooks(merged, hooks_dir)
    merge_statusline(merged, hooks_dir)
    return merged, hook_entry


def verify_guard_hook(hook_entry: dict) -> None:
    """Actually run the baked hook command against a known-dangerous
    payload. If this doesn't print an "ask" decision, the guard is
    silently doing nothing (wrong interpreter path, args form not
    supported, etc.) and we want that loud, not discovered later."""
    command = [hook_entry["command"], *hook_entry.get("args", [])]
    payload = b'{"tool_input":{"command":"rm -rf /"}}'
    try:
        result = subprocess.run(command, input=payload, capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"  VERIFY FAILED: could not run the baked hook command ({e})")
        return
    if b'"permissionDecision": "ask"' in result.stdout or b'"permissionDecision":"ask"' in result.stdout:
        print("  verify OK: guard hook correctly flags `rm -rf /`")
    else:
        print(
            "  VERIFY FAILED: guard hook did not flag `rm -rf /` — it will fail open. "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", help="Install into this directory instead of ~/.claude")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    target = resolve_target(args.target)
    print(f"Target config directory: {target}")
    print(f"Python interpreter to bake into hooks: {sys.executable}")
    if any(marker in sys.executable.lower() for marker in ("venv", "virtualenvs")):
        print("  NOTE: this looks like a virtualenv interpreter — if you delete this venv later, the hook breaks silently until you rerun this installer.")

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

    print("\nScripts (always synced from repo):")
    scripts_target_dir = target / "scripts"
    for src in [REPO_ROOT / "scripts" / "pr_watch.py"]:
        dst = scripts_target_dir / src.name
        if args.dry_run:
            print(f"  would write {dst}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  wrote      {dst}")

    print("\nsettings.json:")
    base_settings = load_json_or_die(REPO_ROOT / "settings.base.json")
    merged, hook_entry = merge_settings(base_settings, existing_settings, hooks_target_dir)

    if args.dry_run:
        print("  would write (dry run, showing result):")
        print(json.dumps(merged, indent=2))
        print("\nDone (dry run, nothing written).")
        return

    text = json.dumps(merged, indent=2) + "\n"
    json.loads(text)  # re-parse before touching disk
    existing_settings_path.parent.mkdir(parents=True, exist_ok=True)
    if existing_settings_path.exists():
        shutil.copy2(existing_settings_path, existing_settings_path.with_suffix(".json.bak"))
    existing_settings_path.write_text(text, encoding="utf-8")
    print(f"  wrote      {existing_settings_path}")

    print("\nVerifying the guard hook actually fires:")
    verify_guard_hook(hook_entry)

    print(
        "\nDone. If Claude Code was already running against this config dir, "
        "open /hooks once (or restart) so it picks up the new hook."
    )


if __name__ == "__main__":
    main()

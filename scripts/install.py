#!/usr/bin/env python3
"""Install/upgrade this portable Claude Code config into ~/.claude (or $CLAUDE_CONFIG_DIR).

Run this with whichever Python you use day to day on this machine — the
interpreter running this script (sys.executable) is the one baked into the
hook and statusLine commands in settings.json. sys.executable resolves to
the real interpreter binary (not a Windows Store alias stub), which is
exactly why this script uses it instead of `shutil.which("python")`.

Upgrades are tracked with a manifest (.portable-config-manifest.json in the
target dir): it records the hash of each prose file (CLAUDE.md, commands,
agents) this installer wrote, and which permission rules it added. A file
still matching its recorded hash hasn't been touched locally, so a new run
safely updates it to the new repo version; one that no longer matches was
edited by hand and is left alone. Without this, "rerun to upgrade" silently
does nothing for anything you (or a previous run) already wrote.

settings.json's managed scalar keys (every top-level key settings.base.json
sets, other than "permissions") work differently: this installer fully
owns them and always overwrites them to match settings.base.json (merged
with settings.local.json, if you have one at the repo root — gitignored,
not the same file as Claude Code's own per-project .claude/settings.local.json).
Any of those keys can be overridden per machine in settings.local.json --
the allowed set is derived from settings.base.json's own keys, not a fixed
list. To pin a different value on one machine, put it in settings.local.json,
not by hand-editing the installed settings.json — a hand-edit there will be
overwritten on the next run. Permission list rules still use the manifest's
add/retract tracking, since those need to merge with rules you or Claude
Code added directly.

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
               copy was hand-edited since the last install (still backed
               up first, with a timestamp so repeated --force runs don't
               destroy each other's backups).
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT_NAME = "guard_destructive_commands.py"
HOOK_MATCHER = "Bash|PowerShell"
STATUSLINE_SCRIPT_NAME = "status_line.py"
PERMISSION_LIST_KEYS = ("allow", "ask", "deny")
MANIFEST_NAME = ".portable-config-manifest.json"
LOCAL_SETTINGS_NAME = "settings.local.json"


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


def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(target: Path) -> dict:
    path = target / MANIFEST_NAME
    if not path.exists():
        return {"files": {}, "permission_rules": {}}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        print(f"  WARNING: {path} is corrupt — treating as a fresh install for upgrade-tracking purposes.")
        manifest = {}
    manifest.setdefault("files", {})
    manifest.setdefault("permission_rules", {})
    manifest.pop("settings_keys", None)  # obsolete; scalar keys are now fully owned, not tracked
    return manifest


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def validate_local_overrides(allowed: dict, base: dict, path: Path) -> None:
    """Fail loudly and BEFORE anything is written, rather than crash
    mid-install (leaving CLAUDE.md/commands/agents/hooks written but
    settings.json/manifest not) or silently corrupt settings.json with the
    wrong shape (a string iterated as one rule per character, etc.)."""
    for key, value in allowed.items():
        if key == "permissions":
            continue
        if key in base and type(value) is not type(base[key]):
            die(
                f"{path}: {key!r} must be the same type as settings.base.json's value "
                f"({type(base[key]).__name__}), got {type(value).__name__} ({value!r})"
            )

    perms = allowed.get("permissions")
    if perms is None:
        return
    if not isinstance(perms, dict):
        die(f"{path}: 'permissions' must be an object, got {type(perms).__name__}")
    for key in PERMISSION_LIST_KEYS:
        if key in perms and not isinstance(perms[key], list):
            die(f"{path}: 'permissions.{key}' must be an array of rule strings, got {type(perms[key]).__name__}")
    remove = perms.get("remove")
    if remove is not None:
        if not isinstance(remove, dict):
            die(f"{path}: 'permissions.remove' must be an object keyed by allow/ask/deny, got {type(remove).__name__} -- did you mean {{\"ask\": {remove!r}}}?")
        for key in PERMISSION_LIST_KEYS:
            if key in remove and not isinstance(remove[key], list):
                die(f"{path}: 'permissions.remove.{key}' must be an array of rule strings, got {type(remove[key]).__name__}")


def load_local_overrides(base: dict) -> dict:
    """settings.local.json at the repo root -- gitignored, per-machine
    overrides. NOT Claude Code's own .claude/settings.local.json (that one
    is project-scoped only); this one is read by this script alone.

    The allowed scalar keys are derived from settings.base.json's own keys
    (whatever it manages, minus "permissions"), not a hardcoded list --
    otherwise a new key added to base can't be overridden per machine
    until this script is also updated by hand."""
    path = REPO_ROOT / LOCAL_SETTINGS_NAME
    if not path.exists():
        return {}
    raw = load_json_or_die(path)
    managed_scalar_keys = set(base) - {"permissions"}
    allowed = {k: v for k, v in raw.items() if k in managed_scalar_keys or k == "permissions"}
    ignored = sorted(set(raw) - set(allowed))
    if ignored:
        print(f"  ignoring unrecognized {LOCAL_SETTINGS_NAME} key(s): {ignored}")
    validate_local_overrides(allowed, base, path)
    return allowed


def save_manifest(target: Path, manifest: dict, dry_run: bool) -> None:
    if dry_run:
        return
    (target / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def timestamped_backup(dst: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return dst.with_name(f"{dst.name}.{ts}.bak")


def remove_renamed_file(target: Path, rel_key: str, manifest: dict, dry_run: bool) -> None:
    """A file this installer previously shipped was renamed or dropped (e.g.
    commands/resume.md -> pickup.md, since "resume" shadowed Claude Code's
    own built-in command). Remove the old one, but only if it still matches
    what we wrote -- if it was hand-edited, leave it, same as sync_managed_file."""
    dst = target / rel_key
    recorded_hash = manifest["files"].get(rel_key)
    if recorded_hash is None or not dst.exists():
        return
    if file_hash(dst.read_text(encoding="utf-8-sig")) != recorded_hash:
        print(f"  keeping    {dst} (hand-edited; would otherwise remove it, it's been renamed/dropped upstream)")
        return
    if dry_run:
        print(f"  would remove {dst} (renamed/dropped upstream)")
        return
    dst.unlink()
    manifest["files"].pop(rel_key, None)
    print(f"  removed    {dst} (renamed/dropped upstream)")


def sync_managed_file(src: Path, dst: Path, rel_key: str, manifest: dict, force: bool, dry_run: bool) -> None:
    """Copy src -> dst, but only overwrite an existing dst if it still
    matches what THIS installer last wrote there (per the manifest) — i.e.
    it hasn't been hand-edited since. That makes a plain rerun a real
    upgrade for files that haven't been touched, while still protecting
    local edits without needing --force."""
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
    new_content = src.read_text(encoding="utf-8")
    new_hash = file_hash(new_content)
    recorded_hash = manifest["files"].get(rel_key)

    if dst.exists():
        old_content = dst.read_text(encoding="utf-8-sig")
        old_hash = file_hash(old_content)
        if old_hash == new_hash:
            print(f"  unchanged  {dst}")
            manifest["files"][rel_key] = new_hash
            return
        hand_edited = recorded_hash is None or old_hash != recorded_hash
        if hand_edited and not force:
            reason = "hand-edited since last install" if recorded_hash else "already exists, not one this installer wrote before"
            print(f"  SKIPPED    {dst} ({reason}; rerun with --force to overwrite)")
            return
        if dry_run:
            print(f"  would back up {dst} -> {timestamped_backup(dst).name}, then upgrade")
        else:
            shutil.copy2(dst, timestamped_backup(dst))
    if dry_run:
        print(f"  would write {dst}")
        return
    dst.write_text(new_content, encoding="utf-8")
    manifest["files"][rel_key] = new_hash
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


def merge_permission_lists(merged: dict, base: dict, local: dict, manifest: dict) -> None:
    """Union in base's + settings.local.json's rules, minus anything
    settings.local.json explicitly retracts (permissions.remove), and also
    retract a rule this installer itself added in a previous run if it's
    no longer wanted. A rule the user (or Claude Code) added by hand,
    never recorded in our manifest, is left alone unless local.json's
    `remove` explicitly names it."""
    base_perms = base.get("permissions") or {}
    local_perms = local.get("permissions") or {}
    to_remove = local_perms.get("remove") or {}
    merged_perms = merged.setdefault("permissions", {})
    installer_added = manifest.setdefault("permission_rules", {})

    for key in PERMISSION_LIST_KEYS:
        wanted = list(base_perms.get(key, []))
        for rule in local_perms.get(key, []):
            if rule not in wanted:
                wanted.append(rule)
        removed_here = set(to_remove.get(key, []))
        wanted = [r for r in wanted if r not in removed_here]

        existing_list = merged_perms.get(key, [])
        previously_added = set(installer_added.get(key, []))
        kept = [r for r in existing_list if not (r in previously_added and r not in wanted)]
        kept = [r for r in kept if r not in removed_here]
        for rule in wanted:
            if rule not in kept:
                kept.append(rule)

        if kept:
            merged_perms[key] = kept
        elif key in merged_perms:
            del merged_perms[key]
        installer_added[key] = wanted

    if not merged_perms:
        merged.pop("permissions", None)


def merge_settings(base: dict, existing: dict, manifest: dict, hooks_dir: Path, local: dict) -> tuple:
    """settings.json's managed scalar keys are fully owned by this
    installer: they always end up matching base (overridden by
    settings.local.json if set), full stop -- no hand-edit detection, no
    manifest tracking, no ambiguity about "did the user change this since
    we set it". Want a different value on this machine? Put it in
    settings.local.json and rerun; don't hand-edit the installed file."""
    merged = dict(existing)

    for key in {*base, *local} - {"permissions"}:
        value = local[key] if key in local else base[key]
        source = LOCAL_SETTINGS_NAME if key in local else "settings.base.json"
        if merged.get(key) != value:
            print(f"  settings.json {key!r} = {value!r} (from {source})")
        merged[key] = value

    merge_permission_lists(merged, base, local, manifest)
    hook_entry = merge_hooks(merged, hooks_dir)
    merge_statusline(merged, hooks_dir)
    return merged, hook_entry


def verify_guard_hook(hook_entry: dict) -> bool:
    """Actually run the baked hook command against a known-dangerous
    payload. If this doesn't print an "ask" decision, the guard is
    silently doing nothing (wrong interpreter path, args form not
    supported, etc.) and we want that loud -- including a nonzero exit
    code, so CI (or a script) actually catches it instead of it being
    a print statement nobody reads."""
    command = [hook_entry["command"], *hook_entry.get("args", [])]
    payload = b'{"tool_input":{"command":"rm -rf /"}}'
    try:
        result = subprocess.run(command, input=payload, capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"  VERIFY FAILED: could not run the baked hook command ({e})")
        return False
    if b'"permissionDecision": "ask"' in result.stdout or b'"permissionDecision":"ask"' in result.stdout:
        print("  verify OK: guard hook correctly flags `rm -rf /`")
        return True
    print(
        "  VERIFY FAILED: guard hook did not flag `rm -rf /` — it will fail open. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return False


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

    manifest = load_manifest(target)
    base_settings = load_json_or_die(REPO_ROOT / "settings.base.json")
    local_overrides = load_local_overrides(base_settings)
    print(f"Local overrides: {LOCAL_SETTINGS_NAME} " + ("found, applying" if local_overrides else f"none (create {LOCAL_SETTINGS_NAME} at the repo root to override per-machine)"))

    existing_settings_path = target / "settings.json"
    existing_settings = {}
    if existing_settings_path.exists():
        existing_settings = load_json_or_die(existing_settings_path)

    print("\nCLAUDE.md:")
    sync_managed_file(REPO_ROOT / "CLAUDE.md", target / "CLAUDE.md", "CLAUDE.md", manifest, args.force, args.dry_run)

    print("\nCommands:")
    remove_renamed_file(target, "commands/resume.md", manifest, args.dry_run)  # -> pickup.md; "resume" shadowed the built-in
    for src in sorted((REPO_ROOT / "commands").glob("*.md")):
        rel_key = f"commands/{src.name}"
        sync_managed_file(src, target / "commands" / src.name, rel_key, manifest, args.force, args.dry_run)

    print("\nAgents:")
    for src in sorted((REPO_ROOT / "agents").glob("*.md")):
        rel_key = f"agents/{src.name}"
        sync_managed_file(src, target / "agents" / src.name, rel_key, manifest, args.force, args.dry_run)

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
    merged, hook_entry = merge_settings(base_settings, existing_settings, manifest, hooks_target_dir, local_overrides)

    if args.dry_run:
        print("  would write (dry run, showing result):")
        print(json.dumps(merged, indent=2))
        print("\nDone (dry run, nothing written).")
        return

    text = json.dumps(merged, indent=2) + "\n"
    json.loads(text)  # re-parse before touching disk
    if existing_settings_path.exists() and existing_settings_path.read_text(encoding="utf-8-sig") == text:
        print(f"  unchanged  {existing_settings_path}")
    else:
        existing_settings_path.parent.mkdir(parents=True, exist_ok=True)
        if existing_settings_path.exists():
            shutil.copy2(existing_settings_path, timestamped_backup(existing_settings_path))
        existing_settings_path.write_text(text, encoding="utf-8")
        print(f"  wrote      {existing_settings_path}")

    save_manifest(target, manifest, args.dry_run)

    print("\nVerifying the guard hook actually fires:")
    if not verify_guard_hook(hook_entry):
        print("\nInstall completed, but the guard hook does not work -- treat this as failed.", file=sys.stderr)
        sys.exit(1)

    print(
        "\nDone. If Claude Code was already running against this config dir, "
        "open /hooks once (or restart) so it picks up the new hook."
    )


if __name__ == "__main__":
    main()

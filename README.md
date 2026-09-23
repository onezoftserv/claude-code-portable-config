# Portable Claude Code config

Personal config, meant to travel to Mac, Linux containers, and a Windows work laptop. This folder is the source of truth — edit files here, then run the installer on each machine. Nothing here is meant to be edited in place inside `~/.claude`.

## Layout

- `CLAUDE.md` — working rules: model routing, token efficiency, the dev workflow, PR/comment style.
- `settings.base.json` — model (`opusplan`), fallback model, and a starter permissions allowlist/asklist. The installer merges this into the machine's real `settings.json` — it unions permission lists and keeps any existing keys it doesn't recognize.
- `hooks/common/` — the actual hook + statusLine scripts (Python, mostly OS-agnostic logic).
- `hooks/windows/`, `hooks/mac/`, `hooks/linux/` — notes on OS quirks, and the place to add a hook that genuinely needs OS-specific behavior.
- `commands/ship.md` — `/ship`: pushes, opens the PR, and watches it live for CodeRabbit/reviewer comments via `scripts/pr_watch.py`.
- `agents/adversarial-reviewer.md` — the subagent used for plan/code adversarial review, defaulting to Sonnet; pass `model: "opus"` on the `Agent` call for complex/high-stakes work.
- `scripts/install.py` — installs all of the above into `~/.claude` (or `$CLAUDE_CONFIG_DIR`), verifies the guard hook actually fires, and backs up whatever it overwrites.
- `scripts/pr_watch.py` — polls a PR for new/updated reviewer comments; `/ship` runs this in the background.

## Install on a new machine

```
python scripts/install.py --dry-run   # see what would change first
python scripts/install.py
```

The installer bakes the exact Python interpreter it's run with (`sys.executable`) into the hooks config as an absolute path, using exec-form `args` — no shell involved. That's what makes the guard hook work on Windows, macOS and Linux without branching: there's no `python` vs `python3` vs `py` guessing, no shell-quoting differences. `statusLine` has no exec-form in its schema, so that one command is a shell string; the installer checks whether `bash` is resolvable on this machine and adjusts the syntax so it matches whichever shell will actually run it (PowerShell needs the `&` call operator, bash doesn't).

It never overwrites `CLAUDE.md`/`commands/`/`agents/` files that differ from the repo copy unless you pass `--force` (and even then, it backs the old copy up to `*.bak` first). `hooks/` and `scripts/pr_watch.py` are always synced — they're managed code, not something to hand-edit on a target machine. `settings.json` is merged: permission lists are unioned, other keys are kept if already set, and the old file is backed up to `settings.json.bak` before it's overwritten.

After every install it actually pipes a synthetic `rm -rf /` through the freshly baked hook command and prints whether the guard fired — a silent no-op hook (wrong interpreter path, unsupported `args` form, etc.) shows up immediately instead of being discovered later.

After installing, open `/hooks` once in Claude Code (or restart it) so it picks up the new hook — the settings watcher only reloads on that trigger.

## Why this shape

- **Portability**: the repo has no machine-specific paths in it. Only the installed, per-machine `settings.json` does, and that file isn't checked in.
- **Token efficiency**: `CLAUDE.md` stays short and stable (it's replayed every turn — verbosity and churn both cost tokens). `"model": "opusplan"` gets Opus during planning for free, at the harness level, instead of relying on Claude to remember to switch models mid-task (it can't). Haiku is reserved for genuinely mechanical work.
- **Safety**: the guard hook (`guard_destructive_commands.py`) is a pure-Python, zero-token backstop that asks before force-pushes, `git reset --hard`, recursive+forced deletes, and similar — on both Bash and PowerShell — even if a permission rule would otherwise auto-allow the command. It's a heuristic backstop, not a shell parser: quoted spans (commit messages, grep patterns) are stripped before matching, to cut false positives.

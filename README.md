# Portable Claude Code config

Personal config, meant to travel to Mac, Linux containers, and a Windows work laptop. This folder is the source of truth — edit files here, then run the installer on each machine. Nothing here is meant to be edited in place inside `~/.claude`.

## Layout

- `CLAUDE.md` — working rules: model routing, token efficiency, the dev workflow, PR/comment style.
- `settings.base.json` — the settings this config wants (currently just the default model). The installer merges this into the machine's real `settings.json` without clobbering anything already set there.
- `hooks/common/` — the actual hook scripts (Python, OS-agnostic logic).
- `hooks/windows/`, `hooks/mac/`, `hooks/linux/` — notes on OS quirks, and the place to add a hook that genuinely needs OS-specific behavior.
- `commands/ship.md` — `/ship`: opens the PR and watches it for CodeRabbit/reviewer comments for a few minutes.
- `agents/adversarial-reviewer.md` — the subagent used for plan/code adversarial review, defaulting to Sonnet (never silently drops to Haiku).
- `scripts/install.py` — installs all of the above into `~/.claude` (or `$CLAUDE_CONFIG_DIR`).

## Install on a new machine

```
python scripts/install.py --dry-run   # see what would change first
python scripts/install.py
```

The installer bakes the exact Python interpreter it's run with (`sys.executable`) into the hooks config as an absolute path, using exec-form `args` — no shell involved. That's the trick that makes the same hook config work on Windows, macOS and Linux without branching: there's no `python` vs `python3` vs `py` guessing, no shell-quoting differences, no `$VAR` vs `%VAR%` vs `$env:VAR` mismatch.

It never overwrites something that differs from the repo copy unless you pass `--force` (and even then, it backs the old copy up to `*.bak` first). `settings.json` is merged, not replaced — existing keys and hook entries are kept.

After installing, open `/hooks` once in Claude Code (or restart it) so it picks up the new hook — the settings watcher only reloads on that trigger.

## Why this shape

- **Portability**: the repo has no machine-specific paths in it. Only the installed, per-machine `settings.json` does, and that file isn't checked in.
- **Token efficiency**: `CLAUDE.md` stays short and stable (it's replayed every turn — verbosity and churn both cost tokens). Model routing keeps Haiku for genuinely mechanical work only, and pushes Opus/Fable to just the two steps that most need the extra reasoning: planning and the final review, and only when the task actually classifies as complex.
- **Safety**: the one included hook (`guard_destructive_bash.py`) is a pure-Python, zero-token backstop that asks before `rm -rf /`, `git push --force`, `git reset --hard`, and similar, even if a permission rule would otherwise auto-allow the command.

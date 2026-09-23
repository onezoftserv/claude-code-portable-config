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

## Install (and upgrade) on a new machine

One-liner, per OS — sets up on first run, re-fetches on every run after. **Re-running this same command is the upgrade command**, there's no separate one, and `scripts/install.py`'s own manifest tracking means base-repo changes actually reach the machine (see below):

macOS / Linux / containers:
```
curl -fsSL https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.sh | bash
```

Windows (PowerShell):
```
irm https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.ps1 | iex
```

Either script sets up (or re-fetches into) `~/.claude-portable-config` (override with `$CLAUDE_PORTABLE_CONFIG_DIR`), then runs `scripts/install.py`. To pass it extra args (e.g. `--dry-run` to preview first) when piping: `curl -fsSL ... | bash -s -- --dry-run` (bash) or `... | iex` won't take args — download and run `install.ps1 -args` locally instead for that case.

To pin to a specific version instead of tracking `main` (e.g. before an upgrade you're unsure about, or to roll back one), set `CLAUDE_PORTABLE_CONFIG_REF` to a branch, tag, or **full** commit SHA — this is the only rollback lever if a `git pull`-equivalent ever brings in something broken, since hooks/scripts always sync on every run.

```
curl -fsSL .../install.sh | CLAUDE_PORTABLE_CONFIG_REF=v1.0.0 bash    # put it on bash, not curl — a prefix before curl only scopes to curl
$env:CLAUDE_PORTABLE_CONFIG_REF = "v1.0.0"; irm .../install.ps1 | iex
```

The `~/.claude-portable-config` checkout these scripts manage is disposable — they always `checkout --detach`, so don't edit files there. To change the config, edit (and push) this repo directly.

Already have it cloned and just want to work on it directly?

```
python scripts/install.py --dry-run   # see what would change first
python scripts/install.py
```

The installer bakes the exact Python interpreter it's run with (`sys.executable`) into the hooks config as an absolute path, using exec-form `args` — no shell involved. That's what makes the guard hook work on Windows, macOS and Linux without branching: there's no `python` vs `python3` vs `py` guessing, no shell-quoting differences. `statusLine` has no exec-form in its schema, so that one command is a shell string; the installer checks whether `bash` is resolvable on this machine and adjusts the syntax so it matches whichever shell will actually run it (PowerShell needs the `&` call operator, bash doesn't).

It tracks what it last installed in `.portable-config-manifest.json` (in the target dir): a `CLAUDE.md`/command/agent file that still matches what the installer wrote last time gets upgraded automatically; one that's been hand-edited since is left alone (rerun with `--force` to overwrite it anyway — always backed up first, with a timestamp, so repeated `--force` runs don't destroy each other's backups). `hooks/` and `scripts/pr_watch.py` are always synced — they're managed code, not something to hand-edit on a target machine. `settings.json` is merged the same way: a key/permission rule the installer set before and that's unchanged locally gets upgraded to the new repo value; one you've since changed by hand is kept. The old `settings.json` is always backed up (timestamped) before being overwritten.

After every install it actually pipes a synthetic `rm -rf /` through the freshly baked hook command and prints whether the guard fired — a silent no-op hook (wrong interpreter path, unsupported `args` form, etc.) shows up immediately instead of being discovered later.

After installing, open `/hooks` once in Claude Code (or restart it) so it picks up the new hook — the settings watcher only reloads on that trigger.

## Why this shape

- **Portability**: the repo has no machine-specific paths in it. Only the installed, per-machine `settings.json` does, and that file isn't checked in.
- **Token efficiency**: `CLAUDE.md` stays short and stable (it's replayed every turn — verbosity and churn both cost tokens). `"model": "opusplan"` gets Opus during planning for free, at the harness level, instead of relying on Claude to remember to switch models mid-task (it can't). Haiku is reserved for genuinely mechanical work.
- **Safety**: the guard hook (`guard_destructive_commands.py`) is a pure-Python, zero-token backstop that asks before force-pushes, `git reset --hard`, recursive+forced deletes, and similar — on both Bash and PowerShell — even if a permission rule would otherwise auto-allow the command. It's a heuristic backstop, not a shell parser: quoted spans (commit messages, grep patterns) are stripped before matching, to cut false positives.

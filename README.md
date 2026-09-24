# Claude Code portable config

[![test](https://github.com/onezoftserv/claude-code-portable-config/actions/workflows/test.yml/badge.svg)](https://github.com/onezoftserv/claude-code-portable-config/actions/workflows/test.yml)
[![codeql](https://github.com/onezoftserv/claude-code-portable-config/actions/workflows/codeql.yml/badge.svg)](https://github.com/onezoftserv/claude-code-portable-config/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/onezoftserv/claude-code-portable-config/graph/badge.svg)](https://codecov.io/gh/onezoftserv/claude-code-portable-config)
[![release](https://img.shields.io/github/v/release/onezoftserv/claude-code-portable-config)](https://github.com/onezoftserv/claude-code-portable-config/releases)
[![license](https://img.shields.io/github/license/onezoftserv/claude-code-portable-config)](LICENSE)

> Personal Claude Code setup — CLAUDE.md, settings, hooks, and commands — that travels to Mac, Linux containers, and Windows with one command.

This repo is the source of truth for how Claude Code behaves for me: what model runs when, what it asks before doing, and the review workflow it follows. Install it on a new machine, or rerun the same command later to upgrade.

## Get started

Pick your OS. Both commands set up on first run and upgrade on every run after — there's no separate upgrade step.

**macOS, Linux, containers:**
```bash
curl -fsSL https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/onezoftserv/claude-code-portable-config/main/install.ps1 | iex
```

Either script sets up (or re-fetches) `~/.claude-portable-config` (override with `$CLAUDE_PORTABLE_CONFIG_DIR`), then runs `scripts/install.py` there. Preview first with `curl -fsSL ... | bash -s -- --dry-run`.

After installing, open `/hooks` once in Claude Code (or restart it) so it picks up the new hook.

Already have it cloned?

```bash
python scripts/install.py --dry-run   # preview
python scripts/install.py
```

## What's in it

**Model routing.** `settings.base.json` sets `"model": "opusplan"` — Opus while planning, Sonnet otherwise, enforced by the harness rather than left as a prose reminder. `CLAUDE.md` reserves Haiku for genuinely mechanical work and tiers `adversarial-reviewer` explicitly: Sonnet default, `model: "opus"` for complex/high-stakes, `model: "fable"` for the really-complex tier on top of that.

**A review workflow for complex work.** `CLAUDE.md` lays out an 8-step process for anything with an unclear root cause or that crosses module boundaries: understand → plan → adversarial plan review → implement → tests → adversarial code review → optional CodeRabbit pass → `/ship`. Small, well-understood changes skip the ceremony on purpose.

**A destructive-command guard.** `hooks/common/guard_destructive_commands.py` is a zero-token, pure-Python `PreToolUse` hook (Bash + PowerShell) that asks before force-pushes, branch deletes, `git reset --hard`, and recursive+forced deletes — even if a permission rule would otherwise auto-allow the command. It's a heuristic backstop, not a shell parser: quoted spans (commit messages, grep patterns) are stripped before matching, and it's backed by 24+ test cases in `tests/`.

```bash
git push origin main --force          # asks
git push --force-with-lease origin main   # doesn't -- the safe variant
```

**`/ship`.** Pushes, opens the PR non-interactively, then watches it live in the background via `scripts/pr_watch.py` for new or edited reviewer comments (CodeRabbit and friends), instead of a one-shot summary at the end. Checks the project's own instructions first and stops if they forbid auto-pushing.

**`/check-repo-config`.** A read-only audit for when you start work in a different project: checks that repo's own `CLAUDE.md`/settings against a fixed checklist of this config's behaviors, and tells you which are a genuine contradiction versus a legitimate project-level override.

**Per-machine overrides.** `settings.local.json` (gitignored — copy `settings.local.example.json` to start one) merges on top of `settings.base.json` before either gets installed. Not the same file as Claude Code's own project-scoped `.claude/settings.local.json` — this one lives at the repo root and only `scripts/install.py` reads it. Hand-editing the installed `settings.json` directly doesn't stick, by design; the installer fully owns its managed keys so a plain rerun is a real upgrade, not a silent no-op.

**Version pinning.** `CLAUDE_PORTABLE_CONFIG_REF` pins install/upgrade to a branch, tag, or full commit SHA instead of `main` — the rollback lever if an upgrade ever brings in something broken, since hooks and scripts always sync on every run.

```bash
curl -fsSL .../install.sh | CLAUDE_PORTABLE_CONFIG_REF=v1.0.0 bash
```

## Where things live

| What I want to do | Where |
|---|---|
| Change a rule Claude follows every session | `CLAUDE.md` |
| Change the default model or permission rules | `settings.base.json` |
| Override a setting on just this machine | `settings.local.json` (see `settings.local.example.json`) |
| Add or tune a safety hook | `hooks/common/`, wired into `scripts/install.py` |
| Change what `/ship` does | `commands/ship.md`, `scripts/pr_watch.py` |
| Audit a different repo's config against this one | `/check-repo-config` |
| Pin to or roll back to a specific version | `CLAUDE_PORTABLE_CONFIG_REF` |
| See what changed between versions | `CHANGELOG.md` |
| Add a hook, run the tests, understand the release process | `CONTRIBUTING.md` |

## Why this shape

- **Portability**: no machine-specific paths in the repo. Only the installed, per-machine `settings.json` has them, and it isn't checked in. The guard hook bakes `sys.executable` as an absolute path using exec-form `args` (no shell), which is what makes it work on Windows, macOS and Linux without branching.
- **Token efficiency**: `CLAUDE.md` stays short and stable — it's replayed every turn, and both verbosity and churn cost tokens. `opusplan` gets Opus during planning for free, at the harness level, instead of relying on Claude to remember to switch models mid-task (it can't).
- **Upgrades that actually upgrade**: `scripts/install.py` tracks a manifest of what it last wrote. A prose file (`CLAUDE.md`, commands, agents) still matching that gets upgraded automatically on rerun; one you've hand-edited since is left alone. `settings.json`'s managed keys (`model`, `fallbackModel`) work differently — the installer fully owns them and always overwrites them (use `settings.local.json` for a per-machine value instead of hand-editing the installed file). It also self-verifies the guard hook actually fires after every install and fails the run if it doesn't, so a silent no-op (wrong interpreter path, unsupported `args` form) shows up immediately instead of being discovered later.

## Next steps

- [CHANGELOG.md](CHANGELOG.md) — release history, and the design decisions made on purpose (no symlinks, no eval harness — see 1.0.0)
- [CONTRIBUTING.md](CONTRIBUTING.md) — adding a hook, running the tests, commit/release conventions
- [LICENSE](LICENSE) — MIT
- [Releases](https://github.com/onezoftserv/claude-code-portable-config/releases) — tagged versions, for `CLAUDE_PORTABLE_CONFIG_REF`

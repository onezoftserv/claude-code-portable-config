# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions are tags in this repo; `install.sh`/`install.ps1` can pin to any of them via `CLAUDE_PORTABLE_CONFIG_REF`.

## [Unreleased]

### Changed
- `adversarial-reviewer`'s default model raised from Sonnet to Opus — it's a second opinion, so it shouldn't run on a weaker model than the main thread. `model: "fable"` is now the escalation for the really-complex tier, not just "opus vs. default."
- Pinned `pytest-cov`/`coverage` versions in CI: an unpinned `coverage` install let a since-changed subprocess-measurement behavior silently shift the reported number (52% was always correct; a locally-cached older `coverage` version was over-crediting e2e subprocess tests).

## [1.0.0] - 2026-09-23

First tagged release. Everything below shipped on `main` before this repo had version tags, folded into one entry.

### Added
- `CLAUDE.md`: model routing (`opusplan` for planning, Sonnet default, Haiku for mechanical work only), token-efficiency rules, an 8-step workflow for complex tasks, PR/comment style rules.
- `settings.base.json`: model, fallback model, starter Bash/PowerShell permission allow/ask lists.
- `settings.local.json` support (gitignored, repo root) for per-machine overrides — see `settings.local.example.json`. Can also explicitly retract a base permission rule via `permissions.remove`, since Claude Code's `deny > ask > allow` precedence means adding a rule to a higher-precedence list doesn't override a lower one.
- `hooks/common/guard_destructive_commands.py`: a zero-token Python PreToolUse hook (Bash + PowerShell) that asks before force-pushes/branch-deletes, `git reset --hard`, recursive+forced deletes, `DROP TABLE`. Backstop heuristic, not a shell parser — strips quoted spans before matching.
- `hooks/common/status_line.py`: model/cost/directory status line.
- `commands/ship.md` (`/ship`): pushes, opens the PR non-interactively, then watches it live via `scripts/pr_watch.py` for new/updated reviewer comments. Checks the project's own instructions first and stops if they forbid auto-pushing.
- `commands/check-repo-config.md` (`/check-repo-config`): read-only audit of a project's own Claude Code config against this one, against a fixed checklist, distinguishing real contradictions from legitimate project-level overrides.
- `agents/adversarial-reviewer.md`: the subagent used for plan/code adversarial review.
- `scripts/install.py`: installs everything into `~/.claude` (or `$CLAUDE_CONFIG_DIR`). Tracks a manifest so reruns are real upgrades for unedited files, not silent no-ops; backs up anything it overwrites (timestamped); self-verifies the guard hook actually fires after install.
- `install.sh` / `install.ps1`: one-line install *and* upgrade (same command; `git init`+fetch+`checkout --detach`, not clone/pull, so `CLAUDE_PORTABLE_CONFIG_REF` can pin to a branch, tag, or full commit SHA for rollback).
- `tests/`: guard-hook cases, merge/upgrade logic, install.py end-to-end, schema validation against a vendored copy of the official settings schema. `.github/workflows/test.yml` runs all of it on ubuntu/macos/windows × Python 3.10/3.12, plus a job that exercises `install.sh`/`install.ps1` themselves.
- `LICENSE` (MIT), `.gitattributes` (forces LF on `.sh`/`.ps1`/`.py` — CRLF breaks `set -euo pipefail` under Git Bash).

### Design decisions (not built, on purpose)
- **Symlinking installed files back into the repo clone**: skipped. The upgrade manifest gets most of the same benefit without Windows Developer-Mode/admin friction or a second code path to test on three OSes.
- **A 4-arm eval comparing this config against plain model usage**: not built. Properly isolating model choice from config effects needs enough repeated runs that the eval would cost more than the config saves; revisit only if a specific rule is suspected of hurting rather than helping.

[1.0.0]: https://github.com/onezoftserv/claude-code-portable-config/releases/tag/v1.0.0

---
description: Audit this project's own Claude Code config against the global portable config for real contradictions vs. legitimate overrides. Read-only except for one optional, separately-gated .gitignore fix.
allowed-tools: Read, Grep, Glob, Bash(git check-ignore*), Bash(git ls-files*)
---

Run manually when starting work in a new project, not automatically. Never edit this project's own config — only read it and report.

1. Read this project's own instructions: `./CLAUDE.md`, `./CLAUDE.local.md`, `./.claude/CLAUDE.md`, any `./.claude/rules/**/*.md`, and any `CLAUDE.md` in parent directories up to the repo root. Also read `./.claude/settings.json` and `./.claude/settings.local.json` if present.
2. Read the installed global config — `${CLAUDE_CONFIG_DIR:-~/.claude}/CLAUDE.md` and `.../settings.json` — the actually-installed files, not this repo's source copies.
3. Check this project against this fixed checklist of global behaviors (don't go looking for open-ended "conflicts" — check exactly these):
   - `/ship` pushes and opens a PR the moment it's run, no separate confirmation.
   - PR/comment style: plain wording, as little text as possible, bullets over prose.
   - Model routing: `opusplan` (Opus while planning), Sonnet by default, Haiku only for mechanical work.
   - The guard hook *asks* (doesn't block) before force-push/branch-delete, `git reset --hard`, recursive+forced deletes.
   - `/code-review` (raised effort for complex/high-stakes work) plus an `adversarial-reviewer` pass (Opus by default, `model: fable` for the really-complex tier) before calling something done.
   For each item, classify it as one of:
   - **Contradiction** — the project's own `CLAUDE.md`/`CLAUDE.local.md`/rules say something that directly conflicts. CLAUDE.md files have no precedence (they all concatenate into context), so this is genuinely ambiguous and worth flagging loudly.
   - **Override** — the project's `settings.json`/`settings.local.json` sets something that legitimately wins (project settings outrank user settings). Not a conflict — just report which value applies here.
   - **Compatible** — no conflict.
4. Separately, check for name collisions: does this project have its own `.claude/commands/ship.md`, `.claude/agents/adversarial-reviewer.md`, `.claude/commands/check-repo-config.md`, or similarly-named commands/agents/skills? Project-level ones silently shadow the global ones — flag any match by name.
5. Report as a short table: behavior — project says (file:line) — verdict. Skip rows with nothing to say.
6. Only if the user asks, as a separate step: check whether `.claude/settings.local.json` is covered by `git check-ignore -q .claude/settings.local.json` (this respects global excludes and nested `.gitignore`s — don't just grep `.gitignore` text). If it isn't covered, offer to add one line to this project's `.gitignore` (or create one). This is git hygiene, unrelated to the audit above, and only happens if asked.

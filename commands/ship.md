---
description: Push, open a PR, and watch it live for reviewer comments (CodeRabbit, etc.) for a bounded window.
---

Last step of the CLAUDE.md workflow — only run after the local adversarial code review passed. Running `/ship` at all is the go-ahead to push and open the PR; don't ask again about that.

0. Check this project's own instructions first — root `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, any `.claude/rules/`. If any of them say not to push, not to open PRs automatically, or route PRs through some other process, stop and tell the user instead of continuing. This check runs every time, not just when someone remembers to audit first.
1. `git push -u origin HEAD` (non-interactive; fails loudly if there's nothing to push).
2. Write the PR title and body per CLAUDE.md's PR style — plain wording, as little text as possible, bullets over prose, no restating the diff, keep the attribution line. If this project keeps a `CHANGELOG.md`, add an entry under `Unreleased` now, before pushing — this is the step that's easy to forget after the fact.
3. `gh pr create --title "<title>" --body "<body>"` — always pass both flags explicitly. Without them `gh` opens `$EDITOR` or prompts interactively, which hangs.
4. Run `python "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/scripts/pr_watch.py" <pr-number>` (adjust the path/shell syntax for whichever shell you're actually in) as a background process, then use `Monitor` to watch it — it prints each new/updated comment as a single line the moment it finds one, so you get live updates, not just a summary at the end. Default window is ~8 minutes; pass `--minutes`/`--interval` to change it.
5. When `pr_watch.py` reports something, relay it to the user in plain language, don't just paste its output. If the window ends with nothing new, say so briefly.
6. Report the PR URL either way.

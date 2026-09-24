---
description: Push, open a PR, and watch it live for reviewer comments (CodeRabbit, etc.) for a bounded window.
---

Last step of the CLAUDE.md workflow — only run after the local adversarial code review passed. Running `/ship` at all is the go-ahead to push and open the PR; don't ask again about that.

0. Check this project's own instructions first — root `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, any `.claude/rules/`. If any of them say not to push, not to open PRs automatically, or route PRs through some other process, stop and tell the user instead of continuing. This check runs every time, not just when someone remembers to audit first.
1. Check the current branch (`git branch --show-current`) against the repo's default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, falling back to `main`/`master` if that fails). If they match, stop — opening a PR needs a branch to open it *from*; create one first.
2. If the working tree has uncommitted changes, that means the adversarial review ran against something that isn't what's about to ship — stop and say so rather than pushing it anyway.
3. If this project keeps a `CHANGELOG.md`, add an entry under `Unreleased` now and commit it (amend the last commit or add a new one, whichever fits) — before the push in the next step, not after. This is the step that's easy to forget once the push already happened.
4. `git push -u origin HEAD` (non-interactive; fails loudly if there's nothing to push).
5. Write the PR title and body per CLAUDE.md's PR style — plain wording, as little text as possible, bullets over prose, no restating the diff, keep the attribution line.
6. `gh pr create --title "<title>" --body "<body>"` — always pass both flags explicitly. Without them `gh` opens `$EDITOR` or prompts interactively, which hangs.
7. Run `pr_watch.py` (from `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/scripts/pr_watch.py`) with `python3` — plain `python` doesn't exist on stock macOS — as a background process, then use `Monitor` to watch it. It prints each new/updated comment as a single line the moment it finds one, so you get live updates, not just a summary at the end. Default window is ~8 minutes; pass `--minutes`/`--interval` to change it.
8. When `pr_watch.py` reports something, relay it to the user in plain language, don't just paste its output. If the window ends with nothing new, say so briefly.
9. Report the PR URL either way.

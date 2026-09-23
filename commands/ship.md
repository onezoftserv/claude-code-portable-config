---
description: Open a PR for the current branch and watch it for automated review comments (CodeRabbit, etc.) for a few minutes.
---

Push the current branch and open a pull request, then monitor it briefly. This is the last step of the workflow in CLAUDE.md — only run it after the local adversarial code review has passed.

1. Confirm the branch is ready: local adversarial code review done, tests passing. If not, stop and say so.
2. Confirm with the user before pushing/opening the PR — this is a visible, hard-to-reverse action.
3. Write the PR title and description per CLAUDE.md's PR style: plain wording, as little text as possible, bullets over prose, no restating the diff. Keep the attribution line.
4. Create the PR with `gh pr create`.
5. Start a bounded background poll (`run_in_background`, ~5-10 minutes total, checking every 30-60s) against all three comment surfaces:
   - `gh api repos/{owner}/{repo}/pulls/{number}/comments` (inline review comments)
   - `gh api repos/{owner}/{repo}/pulls/{number}/reviews` (review summaries, e.g. CodeRabbit's walkthrough)
   - `gh api repos/{owner}/{repo}/issues/{number}/comments` (issue-style comments)
   Track which comment/review IDs have already been seen so only new ones get reported.
6. When new comments appear, summarize them in plain language — don't dump raw JSON. If nothing new shows up in the window, say so briefly and stop polling.
7. Report the PR URL.

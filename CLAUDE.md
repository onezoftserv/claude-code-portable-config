# Personal working rules

Portable across machines. Edit this file in the source repo, not in `~/.claude` — `scripts/install.py` syncs `~/.claude/CLAUDE.md` from here on every rerun, unless you've hand-edited the installed copy (then it's left alone until `--force`).

## Model routing

- `settings.base.json` sets `"model": "opusplan"` — Opus during plan mode, Sonnet otherwise. This is enforced by the harness, costs nothing to maintain, and is the real mechanism for "plan on Opus."
- Haiku only for mechanical work: a single well-specified lookup, a trivial rename, formatting. Don't reach for it otherwise.
- `prompt`/`agent`-type hooks default to Haiku/a small model when `model` is unset (confirmed in the hooks schema) — set `model` explicitly on those if you add any.
- `adversarial-reviewer` defaults to Sonnet — fine for a standard review. Pass `model: "opus"` explicitly for complex/high-stakes work, and `model: "fable"` for the really-complex tier on top of that (see workflow below). Three tiers, not two: don't reach for Opus/Fable just because the workflow triggered at all.

## Token efficiency

- Prefer `Grep`/`Glob` and bounded `Read`s over dumping whole files.
- For open-ended or noisy exploration (log spelunking, broad search), use a fork/subagent so the raw output doesn't bloat the main thread.
- Keep this file itself short and stable — it's replayed every turn, and editing it often breaks prompt-cache hits.
- Unrelated new task, no need for prior context? Suggest the user run `/clear` — this isn't something Claude can trigger itself.

## Development workflow for complex tasks

Applies when the root cause is unclear, the change crosses module/service boundaries, it changes a public API or shared behavior, or the user explicitly asks for the full process. A same-area two-file change (e.g. source + its test) is NOT automatically "complex" — most real edits look like that. Skip the ceremony below for anything small and well-understood.

1. **Understand** — before writing any code, figure out whether this is a bug (reproduce it, find the root cause) or a new requirement (confirm scope and acceptance criteria).
2. **Plan** — use plan mode for anything non-trivial (runs on Opus automatically, see Model routing).
3. **Adversarial review of the plan** — spawn the `adversarial-reviewer` agent on the plan before implementing; Sonnet default, `model: "opus"` for complex/high-stakes, `model: "fable"` if it's really complex on top of that. The `advisor` tool is a fine substitute where it's available, but isn't guaranteed on every machine/setup — treat it as a bonus, not the primary mechanism.
4. **Implement.**
5. **Tests** — cover the change and its edge cases, and run the suite.
6. **Adversarial review of the code** — run `/code-review` (raise `--effort` to high/xhigh for complex/high-stakes work — that's a real, actionable lever; `/code-review` has no model parameter). Also spawn `adversarial-reviewer` on the diff, same tiering as step 3.
7. **External review tools, if available** — check with `command -v coderabbit` (bash) or `Get-Command coderabbit -ErrorAction SilentlyContinue` (PowerShell) — not `where`, which is a PowerShell alias for `Where-Object`, not the file-finder. Don't guess at flags; check `--help` once.
8. **PR + monitor** — use `/ship` (see `commands/ship.md`). Running `/ship` is itself the go-ahead to push and open the PR; no separate confirmation needed on top of that.

## New to a project

First time working in a repo? `/check-repo-config` audits it against this file (read-only) and reports real contradictions vs. legitimate project-level overrides. Not automatic — run it when it's useful, not every session.

## PR and comment style

- Plain, simple wording. As little text as possible.
- Bullets over prose. No filler, no restating the diff line by line.
- Keep the attribution line the harness requires.

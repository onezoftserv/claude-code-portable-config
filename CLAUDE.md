# Personal working rules

Portable across machines. Edit this file in the source repo, not in `~/.claude` — `scripts/install.py` syncs `~/.claude/CLAUDE.md` from here (skips if your copy differs, unless you pass `--force`).

## Model routing

- `settings.base.json` sets `"model": "opusplan"` — Opus during plan mode, Sonnet otherwise. This is enforced by the harness, costs nothing to maintain, and is the real mechanism for "plan on Opus."
- Haiku only for mechanical work: a single well-specified lookup, a trivial rename, formatting. Don't reach for it otherwise.
- `prompt`/`agent`-type hooks default to Haiku/a small model when `model` is unset (confirmed in the hooks schema) — set `model` explicitly on those if you add any.
- When spawning the `adversarial-reviewer` agent (or any subagent) for a genuinely complex/high-stakes review, pass `model: "opus"` (or `"fable"`) explicitly on the `Agent` call — that parameter is real and you control it directly. For everything else, let it use its default (Sonnet).

## Token efficiency

- Prefer `Grep`/`Glob` and bounded `Read`s over dumping whole files.
- For open-ended or noisy exploration (log spelunking, broad search), use a fork/subagent so the raw output doesn't bloat the main thread.
- Keep this file itself short and stable — it's replayed every turn, and editing it often breaks prompt-cache hits.
- Unrelated new task, no need for prior context? Suggest the user run `/clear` — this isn't something Claude can trigger itself.

## Development workflow for complex tasks

Applies when the root cause is unclear, the change crosses module/service boundaries, it changes a public API or shared behavior, or the user explicitly asks for the full process. A same-area two-file change (e.g. source + its test) is NOT automatically "complex" — most real edits look like that. Skip the ceremony below for anything small and well-understood.

1. **Understand** — before writing any code, figure out whether this is a bug (reproduce it, find the root cause) or a new requirement (confirm scope and acceptance criteria).
2. **Plan** — use plan mode for anything non-trivial (runs on Opus automatically, see Model routing).
3. **Adversarial review of the plan** — spawn the `adversarial-reviewer` agent on the plan before implementing (pass `model: "opus"` for complex/high-stakes work). The `advisor` tool is a fine substitute where it's available, but isn't guaranteed on every machine/setup — treat it as a bonus, not the primary mechanism.
4. **Implement.**
5. **Tests** — cover the change and its edge cases, and run the suite.
6. **Adversarial review of the code** — run `/code-review` (raise `--effort` to high/xhigh for complex/high-stakes work — that's a real, actionable lever; `/code-review` has no model parameter). For genuinely high-stakes work, also spawn `adversarial-reviewer` with `model: "opus"` on the diff.
7. **External review tools, if available** — check with `command -v coderabbit` (bash) or `Get-Command coderabbit -ErrorAction SilentlyContinue` (PowerShell) — not `where`, which is a PowerShell alias for `Where-Object`, not the file-finder. Don't guess at flags; check `--help` once.
8. **PR + monitor** — use `/ship` (see `commands/ship.md`). Running `/ship` is itself the go-ahead to push and open the PR; no separate confirmation needed on top of that.

## PR and comment style

- Plain, simple wording. As little text as possible.
- Bullets over prose. No filler, no restating the diff line by line.
- Keep the attribution line the harness requires.

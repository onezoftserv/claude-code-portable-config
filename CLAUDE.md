# Personal working rules

Portable across machines. Edit this file in the source repo, not in `~/.claude` — `scripts/install.py` overwrites `~/.claude/CLAUDE.md` (with a backup) from here.

## Model routing

- Classify the task before picking a model:
  - **Mechanical** — a single well-specified lookup, a trivial rename, formatting, or similarly rote work with no judgment involved. Haiku is fine here, and only here.
  - **Standard** — typical implementation, debugging, review work. Sonnet (the default).
  - **Complex / high-stakes** — ambiguous bugs, architecture decisions, or anything where getting it wrong is expensive. Use Opus or Fable.
- Apply this explicitly at the **Plan** step and the **final adversarial review** (the code review right before PR) in the workflow below: if the task classifies as complex/high-stakes, run those two steps on Opus or Fable, not Sonnet. Standard-complexity work stays on Sonnet for every step.
- When spawning a subagent (`Agent` tool) or a `prompt`/`agent`-type hook, pass an explicit `model` matching the classification above. Several of these default silently to a small/fast model when `model` is omitted — don't rely on the default.

## Token efficiency

- Prefer `Grep`/`Glob` and bounded `Read`s over dumping whole files.
- For open-ended or noisy exploration (log spelunking, broad search), use a fork/subagent so the raw output doesn't bloat the main thread.
- Keep this file itself short and stable — it's replayed every turn, and editing it often breaks prompt-cache hits.
- Use `/clear` between unrelated tasks instead of carrying dead context forward.

## Development workflow for complex tasks

Applies when a task touches more than one file/module, the root cause is unclear, it changes behavior or an API, or the user explicitly asks for the full process. For a small, well-understood, single-file change, skip the ceremony and just make the change.

1. **Understand** — before writing any code, figure out whether this is a bug (reproduce it, find the root cause) or a new requirement (confirm scope and acceptance criteria).
2. **Plan** — use plan mode for anything non-trivial. Complex/high-stakes tasks (see Model routing above): plan on Opus or Fable.
3. **Adversarial review of the plan** — before implementing, have the plan critiqued for missed edge cases, hidden assumptions, and simpler alternatives (the `adversarial-reviewer` agent or the `advisor` tool). Don't skip this step just because the plan feels obviously right.
4. **Implement.**
5. **Tests** — cover the change and its edge cases, and run the suite.
6. **Adversarial review of the code** — run `/code-review` (or `/simplify` then `/code-review`) before calling it done. This is the final review: for a complex/high-stakes task, run it on Opus or Fable.
7. **External review tools, if available** — check for a CLI reviewer (e.g. `command -v coderabbit` / `where coderabbit`) and run it as an extra pass if present. Don't guess at its flags; check `--help` once.
8. **PR + monitor** — use `/ship` (see `commands/ship.md`). Opening a PR is a visible, hard-to-reverse action — confirm with the user first, same as any other risky action.

## PR and comment style

- Plain, simple wording. As little text as possible.
- Bullets over prose. No filler, no restating the diff line by line.
- Keep the attribution line the harness requires.

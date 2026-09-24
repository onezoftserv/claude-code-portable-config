---
description: Write a handoff doc summarizing in-progress work, for picking up on another machine. Complements auto-memory, which explicitly excludes in-progress task state.
---

Write (or update) `.claude/handoff.md` in the current project root with:

- **What's in progress** — the task, in one or two sentences.
- **Decisions made and why** — especially ones that weren't obvious from the code, so they don't need re-litigating.
- **Current state** — what's done, what's half-done, what's untouched.
- **Next steps** — concrete, in order.
- **Open questions / blockers** — anything unresolved that the next session needs to pick up.

Keep it short — this is a memory aid, not documentation. Overwrite the previous handoff rather than appending to it; it describes the *current* state, not a log.

This file isn't tracked by anything automatically — if you want it to travel to another machine, commit it. Tell the user it's written and mention whether it's worth committing now or later.

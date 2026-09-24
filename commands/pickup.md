---
description: Read .claude/handoff.md (if present) and pick up where a previous session on another machine left off.
---

Read `.claude/handoff.md` in the current project root.

- If it doesn't exist, say so and stop — nothing to resume.
- If it exists, summarize it back to the user in a few lines (what was in progress, what's next) rather than dumping the whole file, then ask how they want to proceed or just continue with the first next step if it's unambiguous.
- Don't delete or edit the handoff file yourself — `/handoff` owns writing it, this command only reads.

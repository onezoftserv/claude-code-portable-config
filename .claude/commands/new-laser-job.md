---
description: Create a cut / score / print job for the xTool M2
argument-hint: <what to make, and on what material>
---

Create an xTool M2 job: $ARGUMENTS

1. Identify the material and thickness. If it is on the banned list in `laser/materials.md`, or the user cannot say what it is, stop and say why.
2. Read `laser/NOTES.md`. If it is still unfilled, say once that the import test in `laser/_import-test` has not been done and behaviour in xTool Studio is assumed.
3. Copy `laser/_template` to `laser/<kebab-name>/` and write `job.py` with `scripts/svgjob.py`: red = cut, blue = score, filled = print or engrave. Millimetres, final coordinates, no transforms, no `<text>`.
4. For icons or artwork, look in `libs/` and `docs/libraries.md`; copy path data and scale it in the script. Record anything taken in `laser/<kebab-name>/SOURCES.md`.
5. Run `python laser/<kebab-name>/job.py` then `python scripts/check_svg.py laser/<kebab-name>/build/job.svg`. Fix and rerun until it prints `OK`.
6. Settings: quote power/speed/passes only from a `confirmed` row in `laser/materials.md` for this material, thickness and module. Otherwise write "UNTESTED, run a scrap test first".
7. Save the version: `python scripts/snapshot.py laser/<kebab-name> -m "<what this version is>"`. It commits and pushes.
8. Report: the version path (`versions/vNNN/job.svg`), overall size, what each colour layer is for, the order to run them (print, score, cut), and whether the print area fits the inkjet module. Point to "First cut of a new job" in `docs/checklists.md`.

Do not send anything to the machine.

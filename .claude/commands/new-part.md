---
description: Design a new 3D-printed part for the Bambu Lab X2D
argument-hint: <what to make>
---

Design a part for the X2D: $ARGUMENTS

1. If size, mating parts, load direction or material are unclear, ask once, briefly. Otherwise state your assumptions and go.
2. Check `docs/libraries.md` and `libs/` for something that already does the job (BOSL2 threads/screws, Gridfinity, hardware dimensions) before modelling from scratch.
3. Copy `printer/_template` to `printer/<kebab-name>/` and write `part.scad`: parameters first, millimetres, sitting on z=0 in print orientation, designed to print without supports where practical.
4. Run `python scripts/build_part.py printer/<kebab-name>` (add `--dual` for a two-material part). Fix and rerun until it prints `OK`.
5. Read `build/preview.png` and confirm the shape is what was asked for.
6. If anything was downloaded or copied, record it in `printer/<kebab-name>/SOURCES.md` (URL, author, licence).
7. Save the version: `python scripts/snapshot.py printer/<kebab-name> -m "<what this version is>"` with the same build options. It commits and pushes.
8. Report: the version path (`versions/vNNN/part.3mf`), overall size, the parameters worth tuning, suggested orientation and material, and anything to assign by hand in Bambu Studio (filament per body, supports). Point to "First print of a new part" in `docs/checklists.md`.

Do not slice, upload or start a print.

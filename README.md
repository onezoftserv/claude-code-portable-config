# Workshop

Parts for a Bambu Lab X2D (AMS 2 Pro) and laser/print jobs for an xTool M2, written as code so Claude Code can generate and check them.

This branch is self-contained and shares no history with `main`; it can be moved to its own repository unchanged.

## Setup (Windows)

```powershell
.\setup.ps1              # tools, Python packages, default libraries, self-test
.\setup.ps1 -AllLibs     # also fetch the optional libraries
.\setup.ps1 -SkipInstall # no winget installs, just the Python side
```

It installs Git, Python, OpenSCAD and Inkscape with winget (Bambu Studio with `-WithBambuStudio`), creates `.venv`, fetches the libraries in `libs.json` and runs the tests. xTool Studio is a manual download.

On macOS/Linux: install OpenSCAD and Python, then `pip install -r requirements.txt && python scripts/fetch_libs.py`.

## Use

| Task | Command |
|---|---|
| New 3D part | `/new-part` in Claude Code, or copy `printer/_template` |
| Build + check a part | `python scripts/build_part.py printer/cable-clip` |
| New laser job | `/new-laser-job`, or copy `laser/_template` |
| Build + check a job | `python laser/name-tag/job.py && python scripts/check_svg.py laser/name-tag/build/job.svg` |
| Save a version (build, check, commit, push) | `python scripts/snapshot.py printer/cable-clip -m "what changed"` |
| Tests | `python -m unittest discover tests` |

## Before the first laser job

Import `laser/_import-test/test.svg` into xTool Studio and fill in `laser/NOTES.md`. The colour convention and validator assume behaviour that has not been confirmed on your machine yet.

## Layout

- `CLAUDE.md`: rules Claude follows here, including the safety rules.
- `machines.json`: bed sizes and colour convention used by every script.
- `printer/`, `laser/`: one folder per project. Working files at the top, frozen numbered copies with their outputs in `versions/v001`, `v002`, ...
- `laser/materials.md`: confirmed laser settings and banned materials.
- `docs/libraries.md`: free part, model and SVG libraries.
- `docs/checklists.md`: first print and first cut.
- `scripts/`: build and check tools.

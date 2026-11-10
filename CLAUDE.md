# Workshop

Design files for two machines. Limits live in `machines.json`; read them from there, don't restate numbers from memory.

- **Bambu Lab X2D** + AMS 2 Pro: dual nozzle (direct-drive main, Bowden auxiliary). Dual-nozzle jobs have a narrower bed.
- **xTool M2 Color Craft**: diode laser, optional IR module, CMYK inkjet module with a smaller print area. Software: xTool Studio.

## Safety rules (not negotiable)

- A human starts every print and every laser job. Never send, start or schedule a job on a machine.
- Laser settings (power, speed, passes) come only from a `confirmed` row in `laser/materials.md`. No matching row: say "UNTESTED, run a scrap test first" and suggest nothing stronger than the nearest confirmed row.
- Refuse materials on the banned list in `laser/materials.md` (PVC/vinyl, unknown plastics, etc.), and anything the user cannot identify.
- Never put printer access codes, serial numbers, IPs or Wi-Fi details in this repo.
- No printer-control MCP servers. Tools that bundle the extracted Bambu Connect certificate are ruled out.

## 3D parts (`printer/<name>/part.scad`)

- OpenSCAD, parameters at the top, millimetres, part sitting on z=0 in its print orientation.
- Build and check with `python scripts/build_part.py printer/<name>` (`--dual` for two-material parts). Do not call a part done until it prints `OK`.
- Look at `build/preview.png` before reporting.
- The exported 3MF is geometry only. Filament, colour and AMS slots are assigned by hand in Bambu Studio; supports are a slicer setting, not modelled.
- Libraries are in `libs/` (see `docs/libraries.md`); run `python scripts/fetch_libs.py` if it is empty.

## Laser / print jobs (`laser/<name>/job.py`)

- A Python script using `scripts/svgjob.py` writes `build/job.svg`. 1 unit = 1 mm, no transforms, no `<text>` (outline it first).
- Colours: red `#ff0000` = cut, blue `#0000ff` = score, anything filled = print or engrave. This only sorts objects into layers; the user sets each layer's processing type in xTool Studio.
- Validate with `python scripts/check_svg.py laser/<name>/build/job.svg`. Do not call a job done until it prints `OK`.
- Check `laser/NOTES.md` for how xTool Studio actually imported earlier files before assuming behaviour.

## Third-party models and artwork

- Record every downloaded or copied file in the project's `SOURCES.md` (URL, author, licence). No licence found: reference only, do not copy.

## Repo habits

- `build/` and `libs/` are generated; never commit them.
- Slicing and anything touching the machines happens on the user's computer, not in a cloud session.

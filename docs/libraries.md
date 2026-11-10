# Free libraries

Licences in the first table were read from each repository's licence file at the commits pinned in `libs.lock.json`. Everything else on this page (generators, sites, artwork sources) is as recalled and was not checked: read the licence on the item itself before using it, especially for anything you sell.

## Fetched into `libs/` (usable directly by Claude)

Listed in `libs.json`, fetched by `python scripts/fetch_libs.py [--all | name ...]`. `build_part.py` puts `libs/` on OpenSCAD's library path.

| Library | For | Licence | Default |
|---|---|---|---|
| [BOSL2](https://github.com/BelfrySCAD/BOSL2) | Rounding, threads, screws, gears, hinges, attachments | BSD-2 | yes |
| [gridfinity-rebuilt-openscad](https://github.com/kennetek/gridfinity-rebuilt-openscad) | Gridfinity bins and baseplates | MIT | yes |
| [Round-Anything](https://github.com/Irev-Dev/Round-Anything) | Rounded polygons and extrusions | MIT | no |
| [NopSCADlib](https://github.com/nophead/NopSCADlib) | Models of real hardware (screws, bearings, fans, PCBs) for fit checks | GPL-3 | no |
| [MCAD](https://github.com/openscad/MCAD) | Older mechanical library | LGPL-2.1 | no |
| [Lucide](https://github.com/lucide-icons/lucide) | Stroke-only icons, good for scoring | ISC | yes |
| [Tabler Icons](https://github.com/tabler/tabler-icons) | Outline and filled icons | MIT | no |
| [Bootstrap Icons](https://github.com/twbs/icons) | Filled icons, good for engraving | MIT | no |

Using an icon in a job: icons come in their own small viewBox (24x24 or 16x16) and often use `stroke="currentColor"`. Copy the path data into `job.py`, scale the coordinates to millimetres there, and set the colour explicitly. Do not paste the `<svg>` wrapper or a `transform`; the validator rejects both.

GPL note: a design that includes NopSCADlib code is a derived work. Use it to check fit, or accept GPL for that part.

## Generators (run, don't copy)

| Tool | For | Licence |
|---|---|---|
| [boxes.py](https://github.com/florianfesti/boxes) | Finger-jointed boxes, drawers, trays and many more laser-cut designs as SVG, with kerf compensation | GPL-3 (the tool; its output is yours) |
| [MakerCase](https://www.makercase.com) | Simple box generator in the browser | free web tool |
| Inkscape Hershey Text extension | Single-line fonts for scoring text instead of engraving it | bundled with Inkscape |
| [Google Fonts](https://fonts.google.com) | Fonts to outline into paths | mostly OFL |

boxes.py output uses its own colours and units; run its SVG through `check_svg.py` and recolour to the convention here before use.

## Model sites (reference or per-model download)

No bulk download, and every model has its own licence. Record what you take in the project's `SOURCES.md`.

| Site | Notes |
|---|---|
| [MakerWorld](https://makerworld.com) | Bambu's own; many models ship with X-series print profiles |
| [Printables](https://www.printables.com) | Clear licence shown per model |
| [Thingiverse](https://www.thingiverse.com) | Large, older catalogue |
| [Thangs](https://thangs.com) | Search across several sites |
| [NIH 3D](https://3d.nih.gov) | Scientific and medical models |
| [Smithsonian 3D](https://3d.si.edu) | Museum scans; open-access items are CC0 |
| [NASA 3D Resources](https://nasa3d.arc.nasa.gov) | Spacecraft and terrain models |

Common licence traps: "non-commercial" (no selling prints), "no derivatives" (no remixing), and "share-alike" (your remix carries the same licence).

## Real-part CAD (dimensions and fit checks)

| Source | Notes |
|---|---|
| [McMaster-Carr](https://www.mcmaster.com) | CAD for most catalogue hardware; for your own design use, not redistribution |
| [GrabCAD Library](https://grabcad.com/library) | User-uploaded CAD, account needed, licence varies |
| [FreeCAD-library](https://github.com/FreeCAD/FreeCAD-library) | Community parts library |
| [KiCad 3D models](https://gitlab.com/kicad/libraries/kicad-packages3D) | Electronic components as STEP |

## Artwork (SVG)

| Source | Licence | Notes |
|---|---|---|
| [Openclipart](https://openclipart.org) | CC0 | Safe default for clip art |
| [SVG Repo](https://www.svgrepo.com) | per item | Filter by licence |
| [Wikimedia Commons](https://commons.wikimedia.org) | per item | Often needs attribution |
| [Public Domain Vectors](https://publicdomainvectors.org) | CC0 | |
| [Atomm](https://www.atomm.com) | per project | xTool's community: finished laser projects and material settings |

Imported artwork usually needs cleaning before it passes the validator: text outlined, transforms applied, units set to millimetres. Inkscape does all three (Path > Object to Path, then save as Plain SVG with the document in mm).

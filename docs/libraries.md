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

## Where to search for free projects

Claude cannot browse or download from these: most need a browser or a login. Find the project yourself, download it into the project folder, and record it in `SOURCES.md`. Every item has its own licence, and "free" very often means personal use only.

### 3D printing

| Site | Best for |
|---|---|
| [MakerWorld](https://makerworld.com) | Bambu's own; many models ship with ready print profiles and multi-colour setups |
| [Printables](https://www.printables.com) | General-purpose, well curated, licence shown clearly per model |
| [Thingiverse](https://www.thingiverse.com) | Largest and oldest catalogue; quality varies |
| [Thangs](https://thangs.com) | Search engine across many sites, including search by shape |
| [Yeggi](https://www.yeggi.com) | Meta-search across model sites |
| [Cults3D](https://cults3d.com) | Mix of free and paid; strong on decorative models |
| [MyMiniFactory](https://www.myminifactory.com) | Miniatures and figures; free section |
| [NIH 3D](https://3d.nih.gov) | Scientific and medical models |
| [Smithsonian 3D](https://3d.si.edu) | Museum scans; open-access items are CC0 |
| [NASA 3D Resources](https://nasa3d.arc.nasa.gov) | Spacecraft and terrain models |

### Laser cutting, engraving and print-then-cut

| Site | Best for |
|---|---|
| [Atomm](https://www.atomm.com) | xTool's community: finished projects that open in xTool Studio, with material settings |
| [3axis.co](https://3axis.co) | Thousands of free laser files, decorative and craft; many are CDR or DXF, not SVG |
| [Instructables](https://www.instructables.com) | Step-by-step builds with files attached |
| [Printables](https://www.printables.com) and [Thingiverse](https://www.thingiverse.com) | Both carry laser-cut designs alongside 3D models |
| [DXFforCNC](https://www.dxfforcnc.com) | Free DXF files without signup |
| [Creative Fabrica](https://www.creativefabrica.com) and [Design Bundles](https://designbundles.net) | Craft SVGs; a free section inside mostly paid catalogues |
| [SVG Repo](https://www.svgrepo.com) and [FreeSVG](https://freesvg.org) | Free vector artwork, much of it usable commercially |

Files made for other machines carry settings that do not apply to the M2. Take the geometry, not the power and speed.

Common licence traps: "non-commercial" (no selling what you make), "no derivatives" (no remixing), and "share-alike" (your remix carries the same licence).

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

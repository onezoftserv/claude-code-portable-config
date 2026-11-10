# How xTool Studio imports our SVGs

Fill this in once, by importing `laser/_import-test/test.svg` into xTool Studio with the M2 selected. Until it is filled in, the colour convention in `CLAUDE.md` is an assumption.

Studio version: ____   Date: ____

| # | What to look at | Expected | Observed |
|---|---|---|---|
| 1 | Outer rectangle size | 100.0 x 60.0 mm | |
| 2 | Red rectangle and red circle | One layer, hairline outlines, no fill | |
| 3 | Blue line and blue path | One separate layer | |
| 4 | Processing type of the red and blue layers after import | Not set automatically; you choose | |
| 5 | Black filled square | Own layer, importable as engrave | |
| 6 | Green filled circle | Own layer; "Convert to Print then Cut" available | |
| 7 | Orange rectangle with both fill and stroke | One object or split in two? | |
| 8 | Shape inside a `transform` (purple) | Lands at x=70..90, y=40..50? | |
| 9 | `<text>` element | Imported, dropped, or font substituted? | |
| 10 | Two overlapping identical red lines at the bottom | Kept as two (would cut twice)? | |

Rows 8 to 10 are things our own jobs never contain; they show what happens with artwork from elsewhere.

## Decisions taken from the results

- _e.g. "save a layer template named M2-default with red=cut, blue=score"_

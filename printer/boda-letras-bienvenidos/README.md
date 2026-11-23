# Welcome sign letters, batch 1

BIENVENIDOS, A LA BODA DE and the "&" for the Janny & Alex sign: 21 letters, 3 mm tall,
hanging from carrier rails by thin tabs so each line goes onto the board in one piece.

- Font EB Garamond Bold, 14 mm capitals (17 mm for the "&"), outlines thickened 0.15 mm per side.
- Thinnest stroke about 1.1 mm: 0.4 mm nozzle, 0.2 mm layers or finer, slow outer walls.
- Prints mirrored, readable face on the plate (`face_down = true` in `part.scad`). No supports:
  the tabs are short bridges at the back of the letters.
- Two assemblies: one frame with both text lines, one short rail with the "&".

| Assembly | Width | Top edge of the rail from top of board | Left edge from left of board |
|---|---|---|---|
| BIENVENIDOS / A LA BODA DE | 200.9 mm | 181.5 mm | 204.3 mm |
| & | 40.2 mm | 464.2 mm | 284.7 mm |

How to place:

1. Prime and paint the whole assembly on its carrier. Keep paint off the backs of the letters.
2. Mark the board's vertical centre line (304.8 mm from either side) in pencil.
3. Glue on the backs of the letters only, never on the rails or tabs.
4. Turn it over, put the V notches on the centre line and the top edge of the rail at the distance above. Press down.
5. Let the glue cure (24 h for a contact adhesive), then cut each tab at the letter with flush cutters or a sharp blade and lift the carrier away.
6. Touch up the small cut marks with a fine brush.

The "&" goes on after the metallic names; it sits between them.

Sizes and positions come from `printer/boda-janny-alex/design/make_layout.py`; regenerate `shapes.scad`
with `python printer/boda-janny-alex/design/make_print.py` after changing them.

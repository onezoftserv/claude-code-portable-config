# Welcome sign letters, batch 1

BIENVENIDOS, A LA BODA DE and the "&" for the Janny & Alex sign: 21 letters, 3 mm tall,
held in carrier frames by thin tabs so each block goes onto the board in one piece.

- Font EB Garamond Bold, 14 mm capitals (17 mm for the "&"), outlines thickened 0.15 mm per side.
- Thinnest stroke about 1.1 mm: 0.4 mm nozzle, 0.2 mm layers or finer, slow outer walls.
- Prints mirrored, readable face on the plate (`face_down = true` in `part.scad`). No supports:
  the tabs are bridges of up to 7 mm at mid-height.
- In the text frame every letter hangs between a rail above (one or two tabs) and a rail below (one tab).
- The "&" hangs from a single rail above it by two tabs, with nothing below.
- Tabs are 0.6 mm thick and sit halfway up the side walls: they touch neither the front nor the back of a letter.
- The frame is 0.6 mm lower than the letters, so it never touches the board or the glue.
- Rails are 2 mm wide and side posts 1.2 mm: handle the frames gently.

| Carrier | Size | Top edge from top of board | Left edge from left of board |
|---|---|---|---|
| BIENVENIDOS / A LA BODA DE | 200.9 x 54.9 mm | 184.5 mm | 204.3 mm |
| & (rail only) | 40.2 mm wide | 467.2 mm | 284.7 mm |

How to place:

1. Prime and paint the whole frame with its letters. Keep paint off the backs of the letters.
2. Mark the board's vertical centre line (304.8 mm from either side) in pencil.
3. Put glue on the backs of the letters.
4. Turn the frame over, put the V notches on the centre line and its top edge at the distance above. Press the letters down.
5. Let the glue cure (24 h for a contact adhesive), then cut each tab at the letter with flush cutters or a sharp blade and lift the frame away.
6. Touch up the cut marks on the letters' sides with a fine brush.

The "&" goes on after the metallic names; it sits between them.

Sizes and positions come from `printer/boda-janny-alex/design/make_layout.py`; regenerate `shapes.scad`
with `python printer/boda-janny-alex/design/make_print.py` after changing them.

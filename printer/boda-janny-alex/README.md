# Welcome sign: Janny & Alex

2 x 4 ft board (609.6 x 1219.2 mm), portrait.

- **Names** (JANNY, ALEX): made by an outside supplier in a metallic finish. Send `design/nombres-metalico.svg`.
- **Everything else**: 3D printed, 3 mm raised, primed and airbrushed black. Outlines in `design/letras-negras.svg`.
- Sizes and positions: `design/medidas.md` and `design/medidas.svg`.

Regenerate after changing anything in `design/make_layout.py`:

    pip install fonttools uharfbuzz shapely cairosvg
    python printer/boda-janny-alex/design/make_layout.py

Status: design proposal. The printable letters and the placement template are not built yet.

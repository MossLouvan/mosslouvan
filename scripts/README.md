# ascii-portrait generator

Regenerate `ascii-portrait-{dark,light}.svg` from a new photo:

```bash
# 1. cut the subject out of the background (macOS Vision framework)
swift subject_mask.swift photo.jpg masked.png

# 2. render both animated SVGs (needs Pillow)
python3 svg_gen.py
```

`ascii_gen.py` maps luminance to glyph density + per-character opacity;
`svg_gen.py` renders the grid as 4 SMIL-flickered frames — every glyph
re-rolls to a same-density sibling each frame, so the characters churn
while the portrait holds. If `masked.png` is missing, the grid is
recovered from the previous SVG via `grid_from_svg.py`.

Animation is SMIL-only (no CSS animations) and the base state is the
complete portrait: browsers that freeze image animations still show a
perfect static render instead of a blank.

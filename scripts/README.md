# ascii-portrait generator

Regenerate `ascii-portrait-{dark,light}.svg` from a new photo:

```bash
# 1. cut the subject out of the background (macOS Vision framework)
swift subject_mask.swift photo.jpg masked.png

# 2. render both animated SVGs (needs Pillow)
python3 svg_gen.py
```

`ascii_gen.py` maps luminance to glyph density + per-character opacity;
`svg_gen.py` wraps the grid in the animated terminal-window SVG.

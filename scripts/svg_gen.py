"""Render ASCII rows as an animated SVG portrait (no chrome, transparent bg).

The portrait's brightness lives in per-char fill-opacity, so the glyphs are
free to churn: we emit FRAMES copies of the grid, each with every glyph
re-rolled to a same-density sibling, and hard-cut between them so the
characters visibly change while the picture holds steady.
"""
from ascii_gen import to_grid, LEVELS

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
FS = 12          # font size
CW = FS * 0.6    # monospace char width
LH = 12          # line height
PAD = 14
FRAMES = 4       # churn frames
FRAME_DUR = 0.5  # seconds each frame is visible

# same-density siblings per glyph — swapping within a set keeps the
# perceived brightness (opacity does the heavy lifting anyway)
ALTS = {
    ".": ".,'`",
    ",": ",.'`",
    ":": ":;!i",
    "-": "-~!i",
    "~": "~-i!",
    "=": "=~<>",
    "+": "+=<>x",
    "*": "*+xn",
    "#": "#%X&",
    "%": "%#X&",
    "@": "@&#W",
}

THEMES = {
    "dark": dict(
        colors_top=["#67e8f9", "#7dd3fc", "#a5b4fc", "#67e8f9"],
        colors_mid=["#60a5fa", "#818cf8", "#38bdf8", "#60a5fa"],
        colors_bot=["#a78bfa", "#c084fc", "#818cf8", "#a78bfa"],
        glow="rgba(96,165,250,0.35)",
    ),
    "light": dict(
        colors_top=["#0e7490", "#0369a1", "#4338ca", "#0e7490"],
        colors_mid=["#4338ca", "#6d28d9", "#0e7490", "#4338ca"],
        colors_bot=["#7e22ce", "#4338ca", "#a21caf", "#7e22ce"],
        glow="rgba(67,56,202,0.18)",
    ),
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _hash(x: int, y: int, f: int) -> float:
    return ((x * 73856093) ^ (y * 19349663) ^ (f * 83492791)) % 1000 / 1000.0


def _reroll(grid, frame: int):
    """Frame 0 is the original art; later frames swap each glyph within
    its density class, deterministically, so output is reproducible."""
    if frame == 0:
        return grid
    out = []
    for y, row in enumerate(grid):
        new_row = []
        for x, (glyph, level) in enumerate(row):
            alts = ALTS.get(glyph)
            if level and alts:
                glyph = alts[int(_hash(x, y, frame) * len(alts))]
            new_row.append((glyph, level))
        out.append(new_row)
    return out


def _frame_texts(lines, art_top: int) -> str:
    """Static rows — visibility is gated per-frame by the SMIL flicker.
    Deliberately no opacity-0 reveal cascade: browsers that freeze image
    animations (reduced motion, animation policy, some embeds) render the
    base state, which must be the complete portrait, never a blank."""
    texts = []
    for i, row in enumerate(lines):
        end = len(row)
        while end and row[end - 1][1] == 0:
            end -= 1
        if not end:
            continue
        spans, run, lvl = [], [], row[0][1]
        for glyph, level in row[:end]:
            if level in (lvl, 0):  # spaces are invisible; merge into current run
                run.append(glyph)
            else:
                spans.append((lvl, "".join(run)))
                run, lvl = [glyph], level
        spans.append((lvl, "".join(run)))
        body = "".join(
            f'<tspan fill-opacity="{l / LEVELS:.1f}">{esc(s)}</tspan>'
            for l, s in spans
        )
        y = art_top + i * LH
        texts.append(f'<text class="r" x="{PAD}" y="{y}">{body}</text>')
    return "".join(texts)


def _stop(offset, colors):
    values = ";".join(colors)
    return (f'<stop offset="{offset}" stop-color="{colors[0]}">'
            f'<animate attributeName="stop-color" values="{values}" '
            f'dur="9s" repeatCount="indefinite"/></stop>')


def build(lines, theme_name, out_path):
    t = THEMES[theme_name]
    rows = len(lines)
    width = round(len(lines[0]) * CW + PAD * 2)
    art_top = PAD + FS
    height = round(art_top + (rows - 1) * LH + PAD)
    cycle = FRAMES * FRAME_DUR

    # each frame owns 1/FRAMES of the cycle; discrete SMIL keyTimes give a
    # hard cut (no cross-fade), so density never doubles at the seams
    frames = "".join(
        f'<g opacity="{1 if f == 0 else 0}">'
        f'<animate attributeName="opacity" values="1;0" keyTimes="0;{1 / FRAMES:.4g}" '
        f'calcMode="discrete" dur="{cycle:.2f}s" begin="{f * FRAME_DUR:.2f}s" '
        f'repeatCount="indefinite"/>'
        f'{_frame_texts(_reroll(lines, f), art_top)}</g>'
        for f in range(FRAMES)
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}" xml:space="preserve" role="img"
     aria-label="Animated ASCII art portrait of Moss">
  <style>
    .r {{
      font: {FS}px {FONT};
      fill: url(#ink);
      white-space: pre;
    }}
    .art {{ filter: drop-shadow(0 0 10px {t["glow"]}); }}
  </style>
  <defs>
    <linearGradient id="ink" x1="0" y1="{art_top}" x2="0" y2="{height - PAD}"
        gradientUnits="userSpaceOnUse">
      {_stop("0", t["colors_top"])}
      {_stop(".55", t["colors_mid"])}
      {_stop("1", t["colors_bot"])}
    </linearGradient>
  </defs>
  <g class="art">{frames}</g>
</svg>'''
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"{out_path}: {width}x{height}, {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    import os
    if os.path.exists("masked.png"):
        lines = to_grid("masked.png", cols=108)
    else:  # no photo on disk: recover the grid from the last render
        from grid_from_svg import from_svg
        lines = from_svg("../ascii-portrait-dark.svg")
    build(lines, "dark", "../ascii-portrait-dark.svg")
    build(lines, "light", "../ascii-portrait-light.svg")

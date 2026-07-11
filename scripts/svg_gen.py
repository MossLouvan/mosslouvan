"""Render ASCII rows as an animated SVG portrait (no chrome, transparent bg)."""
from ascii_gen import to_grid, LEVELS

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
FS = 12          # font size
CW = FS * 0.6    # monospace char width
LH = 12          # line height
PAD = 14

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


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
        texts.append(
            f'<text class="r" x="{PAD}" y="{y}" '
            f'style="animation-delay:{i * 0.045:.3f}s">{body}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}" xml:space="preserve" role="img"
     aria-label="Animated ASCII art portrait of Moss">
  <style>
    .r {{
      font: {FS}px {FONT};
      fill: url(#ink);
      white-space: pre;
      opacity: 0;
      animation: reveal .45s cubic-bezier(.2,.7,.3,1) both;
    }}
    @keyframes reveal {{
      from {{ opacity: 0; transform: translateY(7px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
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
  <g class="art">{"".join(texts)}</g>
</svg>'''
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"{out_path}: {width}x{height}, {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    lines = to_grid("masked.png", cols=108)
    build(lines, "dark", "ascii-portrait-dark.svg")
    build(lines, "light", "ascii-portrait-light.svg")

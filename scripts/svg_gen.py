"""Render ASCII rows as an animated terminal-window SVG for a GitHub README."""
from ascii_gen import to_grid, LEVELS

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
FS = 12          # font size
CW = FS * 0.6    # monospace char width
LH = 12          # line height
PAD_X = 28
HEADER_H = 64
PAD_BOTTOM = 34

THEMES = {
    "dark": dict(
        bg="#0b0f17", border="#1e293b", header="#111827",
        grad_top="#67e8f9", grad_mid="#60a5fa", grad_bot="#a78bfa",
        prompt="#34d399", cmd="#e5e7eb", title="#6b7280",
        shimmer="255,255,255", shimmer_op="0.10",
        glow="rgba(96,165,250,0.35)", footer="#4b5563",
    ),
    "light": dict(
        bg="#ffffff", border="#d0d7de", header="#f6f8fa",
        grad_top="#0e7490", grad_mid="#4338ca", grad_bot="#7e22ce",
        prompt="#059669", cmd="#1f2328", title="#8b949e",
        shimmer="67,56,202", shimmer_op="0.06",
        glow="rgba(67,56,202,0.18)", footer="#8b949e",
    ),
}

CMD_TEXT = "moss@github:~$ ./render --self photo.jpg"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(lines, theme_name, out_path):
    t = THEMES[theme_name]
    cols = len(lines[0])
    rows = len(lines)
    art_w = cols * CW
    width = round(art_w + PAD_X * 2)
    art_top = HEADER_H + 26
    height = round(art_top + rows * LH + PAD_BOTTOM)
    reveal_total = rows * 0.045 + 0.45  # last row done
    shimmer_delay = reveal_total + 0.4

    texts = []
    for i, row in enumerate(lines):
        # drop trailing blanks
        end = len(row)
        while end and row[end - 1][1] == 0:
            end -= 1
        if not end:
            continue
        # group consecutive cells into runs of equal opacity level
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
            f'<text class="r" x="{PAD_X}" y="{y}" '
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
    .cmd {{
      font: 12px {FONT};
      fill: {t["cmd"]};
    }}
    .prompt {{ fill: {t["prompt"]}; }}
    .title {{ font: 11px {FONT}; fill: {t["title"]}; }}
    .footer {{
      font: 11px {FONT}; fill: {t["footer"]};
      opacity: 0;
      animation: reveal .6s ease-out {reveal_total + 0.2:.2f}s both;
    }}
    .typer {{
      animation: type 1.6s steps(28, end) .2s both;
    }}
    @keyframes type {{
      from {{ transform: translateX(-{len(CMD_TEXT) * 7.2:.0f}px); }}
      to   {{ transform: translateX(0); }}
    }}
    .cursor {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .sweep {{
      animation: sweep 5.5s ease-in-out {shimmer_delay:.2f}s infinite;
    }}
    @keyframes sweep {{
      0%   {{ transform: translateY(-160px); opacity: 0; }}
      12%  {{ opacity: 1; }}
      55%  {{ transform: translateY({height}px); opacity: 1; }}
      56%  {{ opacity: 0; }}
      100% {{ transform: translateY({height}px); opacity: 0; }}
    }}
  </style>
  <defs>
    <linearGradient id="ink" x1="0" y1="{art_top}" x2="0" y2="{height - PAD_BOTTOM}"
        gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{t["grad_top"]}"/>
      <stop offset=".55" stop-color="{t["grad_mid"]}"/>
      <stop offset="1" stop-color="{t["grad_bot"]}"/>
    </linearGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="rgb({t["shimmer"]})" stop-opacity="0"/>
      <stop offset=".5" stop-color="rgb({t["shimmer"]})" stop-opacity="{t["shimmer_op"]}"/>
      <stop offset="1" stop-color="rgb({t["shimmer"]})" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="card"><rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14"/></clipPath>
    <clipPath id="cmdclip"><rect x="{PAD_X - 2}" y="{HEADER_H - 26}" width="{len(CMD_TEXT) * 7.4 + 14:.0f}" height="22"/></clipPath>
  </defs>

  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14"
        fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>
  <g clip-path="url(#card)">
    <rect x="1" y="1" width="{width - 2}" height="34" fill="{t["header"]}"/>
    <circle cx="24" cy="18" r="5.5" fill="#ff5f57"/>
    <circle cx="44" cy="18" r="5.5" fill="#febc2e"/>
    <circle cx="64" cy="18" r="5.5" fill="#28c840"/>
    <text class="title" x="{width / 2:.0f}" y="22" text-anchor="middle">moss — ascii-portrait — {cols}×{rows}</text>

    <g clip-path="url(#cmdclip)">
      <text class="cmd typer" x="{PAD_X}" y="{HEADER_H - 10}"><tspan class="prompt">moss@github</tspan>:~$ ./render --self photo.jpg</text>
    </g>
    <rect class="cursor" x="{PAD_X + len(CMD_TEXT) * 7.2 + 6:.0f}" y="{HEADER_H - 21}" width="8" height="14" fill="{t["prompt"]}"/>

    <g class="art">{"".join(texts)}</g>

    <text class="footer" x="{PAD_X}" y="{height - 14}">// 100% ascii · rendered from one photo · no pixels were harmed</text>

    <rect class="sweep" x="1" y="0" width="{width - 2}" height="160" fill="url(#beam)"/>
  </g>
</svg>'''
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"{out_path}: {width}x{height}, {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    lines = to_grid("masked.png", cols=108)
    build(lines, "dark", "ascii-portrait-dark.svg")
    build(lines, "light", "ascii-portrait-light.svg")

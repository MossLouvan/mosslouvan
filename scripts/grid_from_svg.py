"""Recover the (glyph, level) grid from a previously generated portrait SVG.

Lets us re-render new animation styles without the original photo:
the SVG's tspans already encode glyph + quantized opacity per char.
"""
import re

LEVELS = 10
PAD = 14
LH = 12
ART_TOP = PAD + 12  # PAD + FS


def from_svg(path: str) -> list[list[tuple[str, int]]]:
    src = open(path).read()
    rows: dict[int, list[tuple[str, int]]] = {}
    for m in re.finditer(r'<text class="r" x="\d+" y="(\d+)"[^>]*>(.*?)</text>', src):
        i = (int(m.group(1)) - ART_TOP) // LH
        row: list[tuple[str, int]] = []
        for op, body in re.findall(r'<tspan fill-opacity="([\d.]+)">(.*?)</tspan>', m.group(2)):
            level = round(float(op) * LEVELS)
            body = body.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            row.extend((g, 0) if g == " " else (g, level) for g in body)
        rows[i] = row
    n = max(rows) + 1
    cols = max(len(r) for r in rows.values())
    grid = [rows.get(i, []) for i in range(n)]
    return [r + [(" ", 0)] * (cols - len(r)) for r in grid]

"""Convert a background-removed RGBA portrait into an ASCII grid.

Returns per-cell (glyph, brightness-level) so the renderer can vary
character opacity with the photo's luminance — bright pixels get dense,
bright glyphs; dark pixels get sparse, dim ones.
"""
from PIL import Image, ImageFilter

RAMP = " .,:-~=+*#%@"  # sparse/dim -> dense/bright
LEVELS = 10            # quantized opacity levels (0 = invisible)


def _hash(x, y):
    return ((x * 73856093) ^ (y * 19349663)) % 1000 / 1000.0


def to_grid(path, cols=100, char_aspect=0.6, gamma=0.9, contrast=1.6,
            alpha_cut=110, keep_top=0.62, fade_start=0.80, floor=0.22):
    img = Image.open(path).convert("RGBA")
    bbox = img.getchannel("A").point(lambda a: 255 if a > alpha_cut else 0).getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    img = img.crop((0, 0, w, int(h * keep_top)))  # head and shoulders only
    w, h = img.size
    rows = max(1, round(h / w * cols * char_aspect))
    # sharpen at 4x target res so facial features survive the downsample
    img = img.resize((cols * 4, rows * 4), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=6, percent=160, threshold=2))
    img = img.resize((cols, rows), Image.LANCZOS)
    px = img.load()
    n = len(RAMP)
    grid = []
    for y in range(rows):
        row = []
        fade = 0.0
        if y / rows > fade_start:  # dissolve the bottom edge into dust
            fade = (y / rows - fade_start) / (1 - fade_start)
        for x in range(cols):
            r, g, b, a = px[x, y]
            if a < alpha_cut or _hash(x, y) < fade * 1.25:
                row.append((" ", 0))
                continue
            v = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            v = min(1.0, max(0.0, (v - 0.5) * contrast + 0.5)) ** gamma
            v *= (1.0 - fade * 0.7)
            if v < 0.32:
                # shadows: dense glyph at low opacity -> solid dim mass,
                # the way dark hair/suit actually reads in a photo
                glyph = "@%#"[min(2, int(v / 0.32 * 3))]
                level = 3
            else:
                t = (v - 0.32) / 0.68
                glyph = RAMP[min(n - 1, max(3, int(3 + t * (n - 3))))]
                level = max(4, round((0.4 + 0.6 * t) * LEVELS))
            row.append((glyph, level))
        grid.append(row)
    return grid

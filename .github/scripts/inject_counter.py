#!/usr/bin/env python3
"""Inject a contribution counter into a Platane/snk snake SVG so it shares the
snake's master animation clock and ticks up exactly as cells are eaten."""
import re, sys

def parse(svg):
    # master duration, e.g. "animation:none 22700ms linear infinite"
    dur = re.search(r'(\d+)ms linear infinite', svg).group(1)
    # each filled cell: @keyframes cN{P%{fill:var(--cLEVEL)} ...}
    events = []
    for m in re.finditer(r'@keyframes (c[0-9a-zA-Z]+)\{([0-9.]+)%\{fill:var\(--c([0-4])\)\}', svg):
        pct = float(m.group(2)); level = int(m.group(3))
        if level >= 1:
            events.append((pct, level))
    events.sort()
    return dur, events

def main():
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    inp = sys.argv[2]; color = sys.argv[3] if len(sys.argv) > 3 else "#ffffff"
    svg = open(inp).read()
    dur, events = parse(svg)
    n = len(events)
    if n == 0:
        print(f"  no filled cells in {inp}; skipping"); return
    weight_sum = sum(l for _, l in events)
    scale = (total / weight_sum) if (total and weight_sum) else 1.0
    # cumulative displayed value at each eat event
    cum = 0; pts = []
    for pct, level in events:
        cum += level
        pts.append((pct, round(cum * scale)))
    pts[-1] = (pts[-1][0], total if total else pts[-1][1])

    # build frames: one per distinct displayed value, capped at K to limit size
    K = 80
    step = max(1, n // K)
    frames = [(0.0, 0)]  # start showing 0 before the first cell is eaten
    last_val = 0
    for i in range(0, n, step):
        pct, val = pts[i]
        if val != last_val:
            frames.append((pct, val)); last_val = val
    # ensure final value present at its real time
    if frames[-1][1] != total and total:
        frames.append((pts[-1][0], total))

    # geometry: grow a dedicated header band on top so the counter never
    # collides with the snake/grid, then anchor it top-right in that band.
    HEADER = 42
    vb = re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"', svg)
    vx, vy, vw, vh = map(float, vb.groups())
    nvy = vy - HEADER; nvh = vh + HEADER
    svg = svg.replace(vb.group(0), 'viewBox="%g %g %g %g"' % (vx, nvy, vw, nvh), 1)
    # bump the outer <svg> height attribute to keep cells the same size
    hm = re.search(r'(<svg[^>]*?height=")([\d.]+)(")', svg)
    if hm:
        new_h = float(hm.group(2)) * nvh / vh
        svg = svg.replace(hm.group(0), hm.group(1) + ("%g" % round(new_h)) + hm.group(3), 1)
    cx = vx + vw - 4           # right edge, anchored end
    cap_y = nvy + 14
    num_y = nvy + 38

    css = [".cnt{opacity:0;animation:none %sms linear infinite;"
           "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}" % dur]
    texts = []
    for j, (start, val) in enumerate(frames):
        end = frames[j+1][0] if j+1 < len(frames) else 100.0
        name = "k%d" % j
        a = round(start, 4); b = round(end, 4)
        eps = 0.001
        if j == len(frames) - 1:
            kf = "@keyframes %s{0%%,%s%%{opacity:0}%s%%,100%%{opacity:1}}" % (name, a, round(a+eps,4))
        elif a <= 0:
            kf = "@keyframes %s{0%%{opacity:1}%s%%{opacity:1}%s%%,100%%{opacity:0}}" % (name, b, round(b+eps,4))
        else:
            kf = ("@keyframes %s{0%%,%s%%{opacity:0}%s%%,%s%%{opacity:1}%s%%,100%%{opacity:0}}"
                  % (name, a, round(a+eps,4), b, round(b+eps,4)))
        css.append(kf)
        texts.append(
            '<text x="%g" y="%g" text-anchor="end" class="cnt" style="animation-name:%s" '
            'fill="%s" font-size="26" font-weight="700" letter-spacing="0.5">%s</text>'
            % (cx, num_y, name, color, f"{val:,}"))
    # static caption (always visible)
    cap = ('<text x="%g" y="%g" text-anchor="end" '
           'font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif" '
           'fill="%s" font-size="9" font-weight="600" letter-spacing="2" opacity="0.85">'
           'CONTRIBUTIONS EATEN</text>' % (cx, cap_y, color))

    inject_style = "<style>" + "".join(css) + "</style>"
    inject_nodes = inject_style + "".join(texts) + cap
    out = svg.replace("</svg>", inject_nodes + "</svg>")
    open(inp, "w").write(out)
    print(f"  {inp}: {n} cells, {len(frames)} frames, total={total}, dur={dur}ms")

if __name__ == "__main__":
    main()

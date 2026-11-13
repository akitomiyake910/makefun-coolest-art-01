"""make.fun coolest-art-01 entry v2: "The Moon Is a Kite".

A small child on a dark hill flies the full moon as a kite. Pure
standard-library Python: the picture is drawn pixel by pixel into an
RGB buffer and written out as a PNG (own minimal encoder).

Deterministic: fixed seed, no clock, no network. Running the program
twice writes byte-identical output.
"""

import math
import os
import random
import struct
import zlib

W = H = 1024

# ---------------------------------------------------------------- canvas

img = [bytearray(3 * W) for _ in range(H)]


def _bytes(rgb, n):
    return bytes(rgb) * n


def span(y, x0, x1, rgb):
    """Fill row y, columns [x0, x1), with one colour."""
    if y < 0 or y >= H:
        return
    x0 = max(0, int(x0))
    x1 = min(W, int(x1))
    if x1 <= x0:
        return
    img[y][x0 * 3:x1 * 3] = _bytes(rgb, x1 - x0)


def span_blend(y, x0, x1, rgb, alpha, base):
    """Fill row y with rgb blended over a uniform base colour."""
    if y < 0 or y >= H or alpha <= 0.0:
        return
    x0 = max(0, int(x0))
    x1 = min(W, int(x1))
    if x1 <= x0:
        return
    if alpha >= 1.0:
        span(y, x0, x1, rgb)
        return
    mixed = tuple(int(rgb[i] * alpha + base[i] * (1.0 - alpha)) for i in range(3))
    img[y][x0 * 3:x1 * 3] = _bytes(mixed, x1 - x0)


def disc(cx, cy, r, rgb, alpha=1.0, base=None):
    """Filled circle, optionally blended over a uniform base colour."""
    r = int(r)
    for dy in range(-r, r + 1):
        yy = cy + dy
        if yy < 0 or yy >= H:
            continue
        half = int(math.sqrt(max(0, r * r - dy * dy)))
        if alpha >= 1.0 or base is None:
            span(yy, cx - half, cx + half + 1, rgb)
        else:
            span_blend(yy, cx - half, cx + half + 1, rgb, alpha, base)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- sky

SKY_STOPS = [
    (0, (7, 11, 38)),
    (320, (14, 22, 60)),
    (620, (24, 33, 80)),
    (820, (44, 50, 96)),
    (1024, (20, 22, 48)),
]


def sky_row(y):
    for i in range(len(SKY_STOPS) - 1):
        y0, c0 = SKY_STOPS[i]
        y1, c1 = SKY_STOPS[i + 1]
        if y <= y1:
            t = (y - y0) / max(1, y1 - y0)
            return lerp(c0, c1, t)
    return SKY_STOPS[-1][1]


for _y in range(H):
    _c = sky_row(_y)
    img[_y][:] = _bytes(_c, W)

# ---------------------------------------------------------------- stars

rng = random.Random(2026)
for _ in range(260):
    sx = rng.randrange(0, W)
    sy = rng.randrange(0, 800)
    b = rng.randrange(120, 256)
    s = 1 if rng.random() < 0.8 else 2
    col = (b, b, min(255, b + 18))
    if s == 1:
        span(sy, sx, sx + 1, col)
    else:
        span(sy, sx, sx + 2, col)
        span(sy + 1, sx, sx + 2, col)
# gold stars, brighter, clustered near the moon
for _ in range(26):
    sx = rng.randrange(60, 760)
    sy = rng.randrange(40, 620)
    span(sy, sx, sx + 2, (240, 200, 110))
    span(sy + 1, sx, sx + 2, (240, 200, 110))
# a few sparkle stars
for _ in range(10):
    sx = rng.randrange(50, W - 50)
    sy = rng.randrange(40, 500)
    span(sy, sx - 3, sx + 4, (255, 255, 255))
    span(sy - 3, sx, sx + 1, (255, 255, 255))
    span(sy + 1, sx, sx + 1, (255, 255, 255))
    span(sy + 2, sx, sx + 1, (255, 255, 255))
    span(sy + 3, sx, sx + 1, (255, 255, 255))

# ---------------------------------------------------------------- the moon

MCX, MCY, MR = 340, 310, 235

# moon body
for _dy in range(-MR, MR + 1):
    _yy = MCY + _dy
    if _yy < 0 or _yy >= H:
        continue
    _half = int(math.sqrt(max(0, MR * MR - _dy * _dy)))
    if _half <= 0:
        continue
    # gentle shading: brighter top-left, dimmer bottom-right
    _t = ((_yy - (MCY - MR)) / (2.0 * MR))
    _base = lerp((252, 240, 212), (238, 220, 180), _t)
    span(_yy, MCX - _half, MCX + _half + 1, _base)

# craters (fixed, deterministic)
CRATERS = [
    (272, 232, 26, (224, 208, 168)),
    (398, 268, 18, (224, 208, 168)),
    (318, 372, 30, (222, 206, 166)),
    (382, 392, 14, (226, 210, 170)),
    (248, 332, 16, (224, 208, 168)),
    (428, 214, 12, (228, 212, 172)),
    (300, 296, 10, (230, 214, 174)),
    (356, 250, 8, (228, 212, 172)),
    (440, 330, 10, (224, 208, 168)),
    (276, 420, 12, (226, 210, 170)),
]
for _cx, _cy, _cr, _cc in CRATERS:
    disc(_cx, _cy, _cr, _cc)
    disc(_cx - _cr // 3, _cy - _cr // 3, _cr // 2, (246, 234, 204))

# ---------------------------------------------------------------- kite string

def bez(p0, p1, p2, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
    return x, y


HAND = (726, 748)
ANCHOR = (491, 490)  # where the string meets the moon
CTRL = (650, 600)
STRING = (238, 192, 96)
for _i in range(150):
    _t = _i / 149.0
    _x, _y = bez(HAND, CTRL, ANCHOR, _t)
    disc(int(_x), int(_y), 2, STRING)

# ---------------------------------------------------------------- hills


def ridge_top(x, base, comps):
    y = float(base)
    for amp, freq, ph in comps:
        y += amp * math.sin(x * freq + ph)
    return y


def paint_ridge(base, comps, rgb):
    col = bytes(rgb)
    for x in range(W):
        top = int(ridge_top(x, base, comps))
        top = max(0, min(H - 1, top))
        for y in range(top, H):
            img[y][x * 3:x * 3 + 3] = col


HILL1 = [(30, 0.007, 2.1), (14, 0.018, 5.0), (7, 0.040, 8.0)]
paint_ridge(860, HILL1, (13, 17, 44))
HILL2 = [(36, 0.006, 4.4), (18, 0.015, 1.2), (9, 0.037, 6.6)]
paint_ridge(928, HILL2, (7, 9, 26))

# ---------------------------------------------------------------- the child

FEET = int(ridge_top(700, 860, HILL1))
FIG = (245, 238, 222)   # pale coat
DARK = (34, 36, 62)
RED = (214, 69, 65)     # red scarf, the one warm accent
SKIN = (244, 214, 180)
HAIR = (58, 40, 28)
# legs (pale coat colour so they read against the night sky)
span(FEET - 32, 690, 700, FIG)
span(FEET - 32, 702, 712, FIG)
# coat body
for _y in range(FEET - 84, FEET - 30):
    span(_y, 686, 716, FIG)
# head: skin face with hair cap on top so the face still shows
disc(700, FEET - 96, 14, SKIN)
disc(700, FEET - 102, 12, HAIR)
# raised arm, drawn after the head so it stays visible: diagonal up-right
for _i in range(40):
    _t = _i / 39.0
    _x = int(710 + _t * 16)
    _y = int(FEET - 76 - _t * 28)
    span(_y, _x - 4, _x + 5, FIG)
# hand gripping the string
disc(726, 748, 5, FIG)
# red scarf: band at the neck + fluttering tail to the left
for _y in range(FEET - 84, FEET - 74):
    span(_y, 684, 718, RED)
for _i in range(30):
    _sx = 684 - _i
    _sy = FEET - 79 + int(_i * 0.35) + int(3 * math.sin(_i * 0.5))
    span(_sy, _sx - 3, _sx + 3, RED)
    span(_sy + 1, _sx - 3, _sx + 3, RED)

# ---------------------------------------------------------------- fireflies

for _fx, _fy in [(180, 900), (260, 940), (880, 900), (940, 950),
                 (120, 960), (820, 970), (520, 990), (620, 920)]:
    disc(_fx, _fy, 3, (250, 220, 120))
    disc(_fx, _fy, 6, (250, 220, 120), 0.25, (7, 9, 26))

# ---------------------------------------------------------------- PNG encode


def png_chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    raw = b"".join(b"\x00" + row for row in img)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) +
           png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b""))
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()

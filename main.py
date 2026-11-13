"""make.fun coolest-art-01 entry: "The Last Flag on Kepler Ridge".

A lone astronaut plants a flag on an alien ridge under a giant ringed
planet. Pure standard-library Python: the picture is drawn pixel by pixel
into an RGB buffer and written out as a PNG (own minimal encoder).

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
    (0, (7, 9, 34)),
    (240, (20, 20, 66)),
    (430, (52, 32, 92)),
    (560, (108, 48, 100)),
    (640, (176, 72, 92)),
    (700, (255, 138, 54)),
]


def sky_row(y):
    for i in range(len(SKY_STOPS) - 1):
        y0, c0 = SKY_STOPS[i]
        y1, c1 = SKY_STOPS[i + 1]
        if y <= y1:
            t = (y - y0) / max(1, y1 - y0)
            return lerp(c0, c1, t)
    return SKY_STOPS[-1][1]


for _y in range(700):
    _c = sky_row(_y)
    img[_y][:] = _bytes(_c, W)

# ground base below the horizon (ridges paint over it)
for _y in range(700, H):
    img[_y][:] = _bytes((18, 12, 30), W)

# ---------------------------------------------------------------- stars

rng = random.Random(1234)
for _ in range(380):
    sx = rng.randrange(0, W)
    sy = rng.randrange(0, 660)
    b = rng.randrange(130, 256)
    s = 1 if rng.random() < 0.75 else 2
    col = (b, b, min(255, b + 20))
    if s == 1:
        span(sy, sx, sx + 1, col)
    else:
        span(sy, sx, sx + 2, col)
        span(sy + 1, sx, sx + 2, col)
# a few bright sparkle stars
for _ in range(12):
    sx = rng.randrange(40, W - 40)
    sy = rng.randrange(30, 480)
    b = 255
    span(sy, sx - 3, sx + 4, (b, b, b))
    span(sy - 3, sx, sx + 1, (b, b, b))
    span(sy + 1, sx, sx + 1, (b, b, b))
    span(sy + 2, sx, sx + 1, (b, b, b))
    span(sy + 3, sx, sx + 1, (b, b, b))

# ---------------------------------------------------------------- small moon

MOON = (182, 148)
disc(MOON[0], MOON[1], 52, (255, 176, 96), 0.10, sky_row(MOON[1]))
disc(MOON[0], MOON[1], 40, (255, 176, 96), 0.14, sky_row(MOON[1]))
disc(MOON[0], MOON[1], 30, (242, 236, 214))
disc(MOON[0] - 9, MOON[1] - 7, 5, (214, 206, 184))
disc(MOON[0] + 8, MOON[1] + 9, 4, (214, 206, 184))
disc(MOON[0] + 11, MOON[1] - 11, 3, (222, 214, 192))

# ---------------------------------------------------------------- shooting star

for _i in range(46):
    _t = _i / 45.0
    _x = int(856 - _t * 118)
    _y = int(96 + _t * 84)
    _b = int(255 * (1.0 - _t))
    span(_y, _x, _x + 2, (_b, _b, min(255, _b + 30)))

PCX, PCY, PR = 648, 296, 238

# smooth radial glow: alpha falls off with true distance from the centre
for _yy in range(max(0, PCY - PR - 200), min(700, PCY + PR + 201)):
    _dy = _yy - PCY
    _half = int(math.sqrt(max(0, (PR + 200) ** 2 - _dy * _dy)))
    if _half <= 0:
        continue
    _n = 40
    for _s in range(_n):
        _sx0 = PCX - _half + (2 * _half) * _s / _n
        _sx1 = PCX - _half + (2 * _half) * (_s + 1) / _n
        _cx = (_sx0 + _sx1) / 2.0
        _d = math.sqrt(max(0, (_cx - PCX) ** 2 + _dy * _dy))
        if _d <= PR:
            continue
        _al = 0.20 * max(0.0, 1.0 - (_d - PR) / 200.0) ** 1.5
        span_blend(_yy, int(_sx0), int(_sx1) + 1, (255, 168, 92), _al,
                   sky_row(_yy))

# ---------------------------------------------------------------- ring, back half

def ring_point(t, rr):
    ct, st = math.cos(t), math.sin(t)
    tilt = math.radians(-16)
    x = PCX + rr * ct * math.cos(tilt) - 92 * st * math.sin(tilt)
    y = PCY + rr * ct * math.sin(tilt) + 92 * st * math.cos(tilt)
    return x, y


RING_COL = (236, 206, 150)
for _rr in range(330, 432, 9):
    _t = 0.0
    while _t < 2 * math.pi:
        _x, _y = ring_point(_t, _rr)
        if _y < PCY - 6:
            disc(int(_x), int(_y), 4, RING_COL, 0.9, sky_row(max(0, min(699, int(_y)))))
        _t += 0.016

# ---------------------------------------------------------------- planet

BANDS = [
    (0.00, (240, 216, 172)),
    (0.12, (228, 188, 140)),
    (0.26, (207, 150, 98)),
    (0.40, (184, 118, 72)),
    (0.55, (162, 94, 64)),
    (0.70, (198, 142, 94)),
    (0.84, (228, 188, 140)),
    (1.01, (240, 216, 172)),
]


def band_col(v, y):
    for i in range(len(BANDS) - 1):
        if v < BANDS[i + 1][0]:
            return BANDS[i][1]
    return BANDS[-1][1]


for _dy in range(-PR, PR + 1):
    _yy = PCY + _dy
    if _yy < 0 or _yy >= H:
        continue
    _half = int(math.sqrt(max(0, PR * PR - _dy * _dy)))
    if _half <= 0:
        continue
    _v = (_yy - (PCY - PR)) / (2.0 * PR)
    _base = band_col(_v, _yy)
    _wob = 0.96 + 0.04 * math.sin(_yy * 0.31)
    _base = tuple(min(255, int(c * _wob)) for c in _base)
    # terminator: light from the right, 64 thin vertical slices
    _x0 = PCX - _half
    _x1 = PCX + _half
    _n = 64
    for _s in range(_n):
        _sx0 = _x0 + (_x1 - _x0) * _s / _n
        _sx1 = _x0 + (_x1 - _x0) * (_s + 1) / _n
        _sc = (_sx0 + _sx1) / 2.0
        _sn = (_sc - _x0) / max(1, _x1 - _x0)
        _shade = 0.42 + 0.58 * (0.5 + 0.5 * math.sin((_sn - 0.12) * math.pi))
        _shade = max(0.42, min(1.0, _shade))
        _col = tuple(int(c * _shade) for c in _base)
        # bright limb on the far right edge
        if _sn > 0.94:
            _col = lerp(_col, (255, 224, 176), 0.55)
        span(_yy, int(_sx0), int(_sx1) + 1, _col)

# ---------------------------------------------------------------- ring, front half

for _rr in range(330, 432, 9):
    _t = 0.0
    while _t < 2 * math.pi:
        _x, _y = ring_point(_t, _rr)
        if _y >= PCY - 6:
            disc(int(_x), int(_y), 4, RING_COL)
        _t += 0.016

# ---------------------------------------------------------------- ridges


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


paint_ridge(706, [(26, 0.011, 1.7), (14, 0.023, 4.2), (7, 0.051, 9.1)],
            (52, 34, 74))
paint_ridge(748, [(34, 0.008, 3.9), (18, 0.019, 0.6), (9, 0.043, 5.5)],
            (30, 19, 48))

# warm sheen on the ground beneath the planet
for _dy in range(0, 130):
    _yy = 760 + _dy
    if _yy >= H:
        break
    _al = 0.10 * (1.0 - _dy / 130.0)
    _half = int(150 * (1.0 - _dy / 260.0)) + 40
    span_blend(_yy, PCX - _half, PCX + _half, (255, 150, 70), _al, (30, 19, 48))

paint_ridge(812, [(44, 0.006, 2.3), (22, 0.015, 5.0), (11, 0.037, 8.8)],
            (15, 10, 28))

# ---------------------------------------------------------------- astronaut

AX = 400
feet = int(ridge_top(AX, 812, [(44, 0.006, 2.3), (22, 0.015, 5.0),
                                (11, 0.037, 8.8)]))
FIG = (8, 7, 16)
# long shadow to the right
for _i in range(170):
    _sx = AX + 12 + _i
    _sy = feet + 1 + int(_i * 0.10)
    if _sx < W and _sy < H:
        span(_sy, _sx, _sx + 3, (6, 5, 12))
        span(_sy + 1, _sx, _sx + 3, (6, 5, 12))
# legs
span(feet - 24, AX - 10, AX - 2, FIG)
span(feet - 24, AX + 2, AX + 10, FIG)
# torso
for _y in range(feet - 64, feet - 22):
    span(_y, AX - 14, AX + 16, FIG)
# backpack
for _y in range(feet - 60, feet - 28):
    span(_y, AX + 16, AX + 26, FIG)
# raised arm
for _i in range(24):
    span(feet - 60 + _i, AX + 16 + _i, AX + 22 + _i, FIG)
# helmet
disc(AX, feet - 76, 18, FIG)
# glowing cyan visor
disc(AX + 4, feet - 78, 6, (110, 240, 255))

# flag pole and flag
for _y in range(feet - 112, feet):
    span(_y, AX + 58, AX + 62, (200, 200, 205))
for _y in range(feet - 112, feet - 84):
    _w = 40 - (_y - (feet - 112))
    span(_y, AX + 62, AX + 62 + max(12, _w), (255, 122, 40))
disc(AX + 60, feet - 114, 4, (255, 190, 90))

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

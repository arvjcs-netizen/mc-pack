"""Animated textures: water, lava, fire, portal, ore twinkle. All loops are seamless in time and space."""
import math
import random

from lib import new, save, save_anim, vnoise_xy

TWO_PI = 2 * math.pi


def waves(x, y, t, size, terms):
    """Sum of sines with whole-number frequencies, so it tiles every `size` px and loops at t=1."""
    v = 0.0
    for fx, fy, ft, amp, ph in terms:
        v += amp * math.sin(TWO_PI * (fx * x / size + fy * y / size + ft * t) + ph)
    return v


def banded(v, cuts, pal, alpha=255):
    i = sum(v > c for c in cuts)
    c = pal[i]
    return (*c[:3], c[3] if len(c) > 3 else alpha)


WATER = [(26, 66, 164, 190), (36, 94, 204, 180), (62, 132, 232, 175), (132, 192, 250, 190)]
WATER_TERMS = [(1, 0, 1, 1.0, 0.0), (0, 1, -1, 0.9, 1.3), (1, 1, 2, 0.6, 2.1), (2, -1, -1, 0.45, 0.4)]

LAVA = [(140, 28, 10), (204, 66, 12), (244, 128, 22), (255, 204, 80)]
LAVA_TERMS = [(1, 0, 1, 1.0, 0.0), (0, 1, 1, 0.9, 2.0), (1, -1, -1, 0.7, 1.0), (2, 1, 0, 0.35, 0.5)]


def still(size, frames, terms, pal, cuts):
    out = []
    for f in range(frames):
        t = f / frames
        img = new(size, size)
        px = img.load()
        for y in range(size):
            for x in range(size):
                px[x, y] = banded(waves(x, y, t, size, terms), cuts, pal)
        out.append(img)
    return out


def flow(size, frames, terms, pal, cuts):
    """Same pattern, scrolling downward one full tile per loop."""
    out = []
    for f in range(frames):
        t = f / frames
        img = new(size, size)
        px = img.load()
        for y in range(size):
            for x in range(size):
                yy = y - t * size
                px[x, y] = banded(waves(x, yy, t * 0, size, terms) + 0.3 * math.sin(TWO_PI * (x / size * 2 + t)),
                                  cuts, pal)
        out.append(img)
    return out


def fire(seed, frames=32):
    """Flames rising: a noise field scrolls up through a bottom-heavy heat gradient."""
    n = vnoise_xy(16, 16, 4, 4, seed)
    n2 = vnoise_xy(16, 16, 2, 2, seed + 7)
    pal = [(170, 34, 16), (232, 92, 20), (250, 160, 40), (255, 228, 140)]
    out = []
    for f in range(frames):
        t = f / frames
        img = new()
        px = img.load()
        shift = t * 16
        ph = seed * 0.37
        for x in range(16):
            # each column is a flame tongue whose height wobbles; whole-number frequencies = seamless
            hgt = (9.5 + 3.0 * math.sin(TWO_PI * (2 * x / 16 + t) + ph)
                   + 2.2 * math.sin(TWO_PI * (3 * x / 16 - 2 * t) + 1 + ph)
                   + 1.3 * math.sin(TWO_PI * (5 * x / 16 + 3 * t) + 2 + ph))
            top = 16 - hgt
            for y in range(16):
                if y < top:
                    continue
                depth = (y - top) / max(1.0, hgt)          # 0 at the tip, 1 at the base
                flick = n[int(y + shift) % 16][x] * 0.25 + n2[int(y + shift * 2) % 16][x] * 0.15
                k = depth + flick - 0.2
                if depth < 0.12 and flick > 0.3:
                    continue                                 # ragged tips
                c = pal[3] if k > 0.72 else pal[2] if k > 0.42 else pal[1] if k > 0.16 else pal[0]
                px[x, y] = (*c, 255)
        out.append(img)
    return out


def portal(frames=32):
    pal = [(70, 16, 120, 190), (110, 36, 180, 190), (150, 70, 220, 200), (210, 150, 255, 210)]
    terms = [(1, 1, 1, 1.0, 0.0), (1, -1, -1, 1.0, 1.0), (2, 0, 1, 0.5, 2.0), (0, 2, -1, 0.5, 0.5)]
    out = []
    for f in range(frames):
        t = f / frames
        img = new()
        px = img.load()
        for y in range(16):
            for x in range(16):
                v = abs(waves(x, y, t, 16, terms))
                px[x, y] = banded(v, [0.6, 1.2, 1.9], pal)
        out.append(img)
    return out


def twinkle(base, spots, frames=16):
    """Static ore texture with a small 4-point glint that travels between gems."""
    out = []
    for f in range(frames):
        img = base.copy()
        px = img.load()
        k = f % 8
        if k < 3:
            x, y = spots[(f // 8) % len(spots)]
            bright = (255, 255, 255, 255) if k == 1 else (210, 250, 255, 255)
            px[x, y] = bright
            if k == 1:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 16 and 0 <= yy < 16 and px[xx, yy][3]:
                        px[xx, yy] = (*[min(255, c + 70) for c in px[xx, yy][:3]], 255)
        out.append(img)
    return out


def generate():
    save_anim(still(16, 32, WATER_TERMS, WATER, [-1.2, 0.2, 1.4]), "blocks/water_still.png", frametime=2)
    save_anim(flow(32, 32, WATER_TERMS, WATER, [-1.2, 0.2, 1.4]), "blocks/water_flow.png", frametime=1)
    save_anim(still(16, 40, LAVA_TERMS, LAVA, [-0.9, 0.5, 1.6]), "blocks/lava_still.png", frametime=3)
    save_anim(flow(32, 32, LAVA_TERMS, LAVA, [-0.9, 0.5, 1.6]), "blocks/lava_flow.png", frametime=3)
    save_anim(fire(3), "blocks/fire_layer_0.png", frametime=1)
    save_anim(fire(17), "blocks/fire_layer_1.png", frametime=1)
    save_anim(portal(), "blocks/portal.png", frametime=2)

    from PIL import Image
    from lib import TEX
    for ore, spots in (("diamond", [(3, 2), (13, 4), (7, 8), (14, 12)]), ("emerald", [(13, 12), (3, 2), (8, 8)])):
        base = Image.open(TEX / f"blocks/{ore}_ore.png").convert("RGBA")
        save_anim(twinkle(base, spots), f"blocks/{ore}_ore.png", frametime=3)

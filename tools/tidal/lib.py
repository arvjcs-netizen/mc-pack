"""Shared helpers for the Tidal pack generator: color ramps, noise, sprites, saving."""
import colorsys
import json
import math
import random
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "packs" / "tidal"
TEX = PACK / "assets" / "minecraft" / "textures"

CLEAR = (0, 0, 0, 0)


# ---------------------------------------------------------------- color
def hsv(c):
    return colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)


def rgb(h, s, v):
    s, v = min(max(s, 0), 1), min(max(v, 0), 1)
    return tuple(round(x * 255) for x in colorsys.hsv_to_rgb(h % 1, s, v))


def _toward(h, target, amt):
    d = ((target - h + 0.5) % 1) - 0.5
    return (h + d * amt) % 1


def shade(base, t):
    """t in [-1, 1]. Shadows shift cool (toward blue), highlights shift warm and desaturate."""
    h, s, v = hsv(base)
    gray = s < 0.06
    if gray:
        h = 0.6
    if t < 0:
        k = -t
        s2 = s + 0.05 * k if gray else s + (1 - s) * 0.15 * k
        return rgb(_toward(h, 0.68, 0.10 * k), s2, v * (1 - 0.55 * k))
    k = t
    h2 = h if gray else _toward(h, 0.15, 0.07 * k)
    return rgb(h2, s * (1 - 0.35 * k), v + (1 - v) * 0.6 * k)


def ramp(base, ts=(-0.7, -0.3, 0.0, 0.3, 0.65)):
    """A list of shades of `base`, darkest first."""
    return [shade(base, t) for t in ts]


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def mul(c, k):
    return tuple(min(255, max(0, round(x * k))) for x in c[:3])


# ---------------------------------------------------------------- noise
def vnoise(w, h, cell, seed):
    """Tileable value noise in 0..1 (w and h must be multiples of cell)."""
    rng = random.Random(seed)
    gw, gh = max(1, w // cell), max(1, h // cell)
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]

    def sm(t):
        return t * t * (3 - 2 * t)

    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            gx, gy = x / cell, y / cell
            x0, y0 = int(gx), int(gy)
            fx, fy = sm(gx - x0), sm(gy - y0)
            a = g[y0 % gh][x0 % gw]
            b = g[y0 % gh][(x0 + 1) % gw]
            c = g[(y0 + 1) % gh][x0 % gw]
            d = g[(y0 + 1) % gh][(x0 + 1) % gw]
            out[y][x] = a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy
    return out


def fbm(w, h, seed, cells=(8, 4, 2), weights=(0.55, 0.3, 0.15), sx=1, sy=1):
    """Layered noise, normalized to 0..1. sx/sy stretch it (e.g. sx=4 for wood grain)."""
    acc = [[0.0] * w for _ in range(h)]
    for i, (c, wt) in enumerate(zip(cells, weights)):
        cw, ch = max(1, min(w, c * sx)), max(1, min(h, c * sy))
        n = vnoise_xy(w, h, cw, ch, seed * 31 + i)
        for y in range(h):
            for x in range(w):
                acc[y][x] += n[y][x] * wt
    return normalize(acc)


def vnoise_xy(w, h, cw, ch, seed):
    rng = random.Random(seed)
    gw, gh = max(1, w // cw), max(1, h // ch)
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]

    def sm(t):
        return t * t * (3 - 2 * t)

    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            gx, gy = x / cw, y / ch
            x0, y0 = int(gx), int(gy)
            fx, fy = sm(gx - x0), sm(gy - y0)
            a = g[y0 % gh][x0 % gw]
            b = g[y0 % gh][(x0 + 1) % gw]
            c = g[(y0 + 1) % gh][x0 % gw]
            d = g[(y0 + 1) % gh][(x0 + 1) % gw]
            out[y][x] = a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy
    return out


def normalize(f):
    lo = min(min(r) for r in f)
    hi = max(max(r) for r in f)
    return [[(v - lo) / (hi - lo or 1) for v in r] for r in f]


def quantize(field, fractions, base=0):
    """Rank-based: the lowest fractions[0] of pixels get `base`, the next fractions[1] get base+1, ..."""
    h, w = len(field), len(field[0])
    vals = sorted(v for r in field for v in r)
    cuts, acc = [], 0.0
    for f in fractions[:-1]:
        acc += f
        cuts.append(vals[min(len(vals) - 1, int(acc * len(vals)))])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            v = field[y][x]
            out[y][x] = base + sum(v >= c for c in cuts)
    return out


# ---------------------------------------------------------------- images
def new(w=16, h=16):
    return Image.new("RGBA", (w, h), CLEAR)


def paint(idx, pal, alpha=255):
    """idx: 2D list of palette indices (None/-1 = transparent). pal: list of RGB(A)."""
    h, w = len(idx), len(idx[0])
    img = new(w, h)
    px = img.load()
    for y in range(h):
        for x in range(w):
            i = idx[y][x]
            if i is None or i < 0:
                continue
            c = pal[max(0, min(len(pal) - 1, i))]
            px[x, y] = (*c[:3], c[3] if len(c) > 3 else alpha)
    return img


def sprite(rows, colors):
    """Draw from a list of strings; each char maps to a color in `colors` ('.' = clear)."""
    img = new(len(rows[0]), len(rows))
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colors and colors[ch] is not None:
                c = colors[ch]
                px[x, y] = (*c[:3], c[3] if len(c) > 3 else 255)
    return img


def outline(img, color, diagonal=False, outside_only=False):
    """Add a 1px outline around opaque pixels (optionally only on the outside of hollow shapes)."""
    out = img.copy()
    src, dst = img.load(), out.load()
    w, h = img.size
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        nb += [(1, 1), (-1, -1), (1, -1), (-1, 1)]
    outside = None
    if outside_only:
        outside, stack = set(), [(0, 0)]
        while stack:
            x, y = stack.pop()
            if (x, y) in outside or not (0 <= x < w and 0 <= y < h) or src[x, y][3] > 0:
                continue
            outside.add((x, y))
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for y in range(h):
        for x in range(w):
            if outside is not None and (x, y) not in outside:
                continue
            if src[x, y][3] == 0 and any(
                0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3] > 0 for dx, dy in nb
            ):
                dst[x, y] = (*color[:3], 255)
    return out


def grid(w=16, h=16, fill=0):
    return [[fill] * w for _ in range(h)]


# ---------------------------------------------------------------- saving
WRITTEN = []


def save(img, rel):
    p = TEX / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p)
    WRITTEN.append(rel)


def save_anim(frames, rel, frametime=2, interpolate=False, order=None):
    w, h = frames[0].size
    strip = Image.new("RGBA", (w, h * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, i * h))
    save(strip, rel)
    anim = {"frametime": frametime}
    if interpolate:
        anim["interpolate"] = True
    if order:
        anim["frames"] = order
    (TEX / f"{rel}.mcmeta").write_text(json.dumps({"animation": anim}, indent=2) + "\n")


def tau():
    return 2 * math.pi


def save_meta(rel, meta):
    """Write <rel>.mcmeta (e.g. {"texture": {"blur": True}})."""
    (TEX / f"{rel}.mcmeta").write_text(json.dumps(meta, indent=2) + "\n")


# ---------------------------------------------------------------- layout reference
# The vanilla jar is used ONLY for geometry: which pixels of a texture the game samples (its UV layout),
# never for colors or art. Everything drawn is generated here.
_JAR = None


def layout_mask(rel):
    """2D list of booleans: True where the vanilla texture at `rel` is non-transparent (UV occupancy)."""
    global _JAR
    import io
    import os
    import zipfile
    if _JAR is None:
        _JAR = zipfile.ZipFile(Path(os.environ["APPDATA"]) / ".minecraft" / "versions" / "1.8.9" / "1.8.9.jar")
    im = Image.open(io.BytesIO(_JAR.read(f"assets/minecraft/textures/{rel}"))).convert("RGBA")
    w, h = im.size
    a = im.getchannel("A").load()
    return [[a[x, y] > 0 for x in range(w)] for y in range(h)]


def layout_gray(rel):
    """Grayscale-only view of a vanilla GUI texture, used to find slot rectangles (geometry only)."""
    global _JAR
    import io
    import os
    import zipfile
    if _JAR is None:
        _JAR = zipfile.ZipFile(Path(os.environ["APPDATA"]) / ".minecraft" / "versions" / "1.8.9" / "1.8.9.jar")
    return Image.open(io.BytesIO(_JAR.read(f"assets/minecraft/textures/{rel}"))).convert("RGBA")


def line(px, p0, p1, color, w=None, h=None):
    (x0, y0), (x1, y1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
        if (w is None or 0 <= x < w) and (h is None or 0 <= y < h):
            px[x, y] = (*color[:3], color[3] if len(color) > 3 else 255)


def rect(px, x0, y0, w, h, color):
    c = (*color[:3], color[3] if len(color) > 3 else 255)
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            px[x, y] = c

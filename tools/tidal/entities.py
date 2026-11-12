"""Entity textures (mobs, chests, signs, banners, effects). A small box painter knows each model's UV boxes
and shades every face the same way (lit top, darker sides and bottom), then details are drawn on the faces.
Models whose boxes aren't listed here are painted from the vanilla UV *occupancy* (which pixels are used)
with Tidal materials. No vanilla colors or art are used."""
import math
import random

from PIL import Image

from blocks import DYES, WOODS
from lib import fbm, layout_mask, mix, new, ramp, rect, save, save_anim, shade

TIDAL_BLUE = (44, 120, 214)
INK = (22, 20, 28)


# ---------------------------------------------------------------- box painter
def faces(u, v, w, h, d):
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h),
            "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}


LIGHT = {"top": 0.22, "bottom": -0.42, "front": 0.0, "right": -0.12, "left": -0.12, "back": -0.18}
_NOISE = {}


def noise(seed, w=128, h=128):
    if seed not in _NOISE:
        _NOISE[seed] = fbm(w, h, seed, cells=(8, 4, 2), weights=(0.5, 0.35, 0.15))
    return _NOISE[seed]


def mat_px(base, x, y, t, seed=1, grain=0.16):
    n = noise(seed)[y % 128][x % 128]
    k = -1 if n < 0.3 else 1 if n > 0.72 else 0
    return shade(base, max(-1, min(1, t + k * grain)))


def paint_box(img, box, base, seed=1, grain=0.16, faces_only=None, alpha=255):
    """Fill every face of a box with shaded material."""
    p = img.load()
    W, H = img.size
    for name, (x0, y0, w, h) in faces(*box).items():
        if faces_only and name not in faces_only:
            continue
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                t = LIGHT[name]
                if name not in ("top", "bottom"):
                    t -= 0.18 * (y - y0) / max(1, h - 1)           # soft vertical falloff
                    if y == y0 + h - 1 and h > 2:
                        t -= 0.12
                c = mat_px(base, x, y, t, seed, grain)
                p[x, y] = (*c, alpha)
    return img


def face(box, name="front"):
    return faces(*box)[name]


def put(img, x, y, c, a=255):
    p = img.load()
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        p[x, y] = (*c[:3], a)


def fill_rect(img, x, y, w, h, c, a=255):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            put(img, xx, yy, c, a)


def band(img, box, rows, color, seed=3, faces_only=("front", "back", "left", "right")):
    """Paint horizontal rows (relative to the side faces' top) in another material, e.g. a belt or collar."""
    p = img.load()
    for name, (x0, y0, w, h) in faces(*box).items():
        if name not in faces_only:
            continue
        for r in rows:
            if 0 <= r < h:
                for x in range(x0, x0 + w):
                    p[x, y0 + r] = (*mat_px(color, x, y0 + r, LIGHT[name] - (0.1 if r == rows[-1] else 0), seed, 0.08), 255)


def from_mask(rel, base, seed=1, grain=0.16, alpha=255, edge=True, skip=None):
    """Paint every pixel the vanilla model samples with Tidal material (for models without listed boxes).
    skip: (x0, y0, x1, y1) area to leave empty (e.g. a signature that isn't part of the UV layout)."""
    m = layout_mask(rel)
    if skip:
        for y in range(skip[1], skip[3]):
            for x in range(skip[0], skip[2]):
                m[y][x] = False
    h, w = len(m), len(m[0])
    img = new(w, h)
    p = img.load()
    for y in range(h):
        for x in range(w):
            if m[y][x]:
                t = 0.0
                if edge and (y == 0 or not m[y - 1][x]):
                    t += 0.18
                if edge and (y == h - 1 or not m[y + 1][x]):
                    t -= 0.3
                p[x, y] = (*mat_px(base, x, y, t, seed, grain), alpha)
    return img


# ---------------------------------------------------------------- faces / features
def eyes(img, fx, fy, row, pairs, color, pupil=None, white=None):
    for (ex, w) in pairs:
        for dx in range(w):
            put(img, fx + ex + dx, fy + row, white or color)
        if pupil:
            put(img, fx + ex + (w - 1 if ex < 4 else 0), fy + row, pupil)


def simple_face(img, box, eye=(20, 20, 28), white=(236, 240, 246), mouth=None, row=None, width=None):
    fx, fy, fw, fh = face(box)
    r = row if row is not None else fh // 2 - 1 + (fh % 2)
    ew = width or (2 if fw >= 8 else 1)
    left, right = 1 if fw >= 8 else 0, fw - 1 - ew - (1 if fw >= 8 else 0) + 1
    for ex in (left, right):
        for dx in range(ew):
            put(img, fx + ex + dx, fy + r, white if (dx == 0 and ex == left) or (dx == ew - 1 and ex == right) else eye)
        put(img, fx + ex + (ew - 1 if ex == left else 0), fy + r, eye)
    if mouth:
        for dx in range(fw // 2 - 1, fw // 2 + 1):
            put(img, fx + dx, fy + r + 3, mouth)


# ---------------------------------------------------------------- biped mobs
BIPED = {"head": (0, 0, 8, 8, 8), "body": (16, 16, 8, 12, 4), "arm": (40, 16, 4, 12, 4), "leg": (0, 16, 4, 12, 4)}


def biped(size, skin, shirt, pants, shoe=None, arm=None, thin=False, head=None, extra64=False):
    img = new(*size)
    hb = head or BIPED["head"]
    paint_box(img, hb, skin, 11)
    paint_box(img, BIPED["body"], shirt, 12)
    armb = (40, 16, 2, 12, 2) if thin else BIPED["arm"]
    legb = (0, 16, 2, 12, 2) if thin else BIPED["leg"]
    paint_box(img, armb, arm or shirt, 13)
    band(img, armb, range(4 if not thin else 0, 12), skin) if not thin and arm is None else None
    paint_box(img, legb, pants, 14)
    if shoe:
        band(img, legb, (10, 11), shoe)
        paint_box(img, legb, shoe, 15, faces_only=("bottom",))
    if extra64:
        paint_box(img, (32, 48, 4, 12, 4), arm or shirt, 13)
        band(img, (32, 48, 4, 12, 4), range(4, 12), skin) if arm is None else None
        paint_box(img, (16, 48, 4, 12, 4), pants, 14)
        if shoe:
            band(img, (16, 48, 4, 12, 4), (10, 11), shoe)
    return img


def human_face(img, hb, skin, hair, eye=(40, 90, 200)):
    fx, fy, fw, fh = face(hb)
    for name in ("top", "back", "left", "right"):
        x0, y0, w, h = face(hb, name)
        for y in range(y0, y0 + (h if name == "top" else 3 if name != "back" else h)):
            for x in range(x0, x0 + w):
                put(img, x, y, mat_px(hair, x, y, LIGHT[name], 21, 0.12))
    fill_rect(img, fx, fy, fw, 2, shade(hair, 0.1))
    put(img, fx, fy + 2, hair)
    put(img, fx + fw - 1, fy + 2, hair)
    for ex in (1, 5):
        put(img, fx + ex, fy + 4, (240, 244, 250))
        put(img, fx + ex + 1, fy + 4, eye)
    put(img, fx + 2, fy + 4, eye)
    put(img, fx + 5, fy + 4, eye)
    put(img, fx + 1, fy + 4, (240, 244, 250))
    put(img, fx + 6, fy + 4, (240, 244, 250))
    put(img, fx + 3, fy + 6, shade(skin, -0.35))
    put(img, fx + 4, fy + 6, shade(skin, -0.35))


def player(alex=False):
    skin = (226, 176, 140)
    img = biped((64, 64), skin, TIDAL_BLUE, (40, 46, 66), shoe=(30, 30, 36), extra64=True,
                arm=None)
    if alex:
        # slim arms: repaint the arm boxes 3px wide
        for b in ((40, 16, 4, 12, 4), (32, 48, 4, 12, 4)):
            x0, y0 = b[0], b[1]
            fill_rect(img, x0, y0, 16, 16, (0, 0, 0), 0)
        for b in ((40, 16, 3, 12, 4), (32, 48, 3, 12, 4)):
            paint_box(img, b, TIDAL_BLUE, 13)
            band(img, b, range(5, 12), skin)
    human_face(img, BIPED["head"], skin, (70, 46, 30) if not alex else (196, 110, 50))
    # hoodie strings and a white wave on the chest
    fx, fy, fw, fh = face(BIPED["body"])
    for y in range(fy, fy + 4):
        put(img, fx + 3, y, (236, 240, 246))
        put(img, fx + 4, y, (236, 240, 246)) if y == fy else None
    for i, (dx, dy) in enumerate(((1, 7), (2, 6), (3, 7), (4, 7), (5, 6), (6, 7))):
        put(img, fx + dx, fy + dy, (190, 226, 250))
    return img


def zombie():
    skin = (100, 150, 96)
    img = biped((64, 64), skin, (40, 130, 150), (60, 56, 120), shoe=(50, 50, 56))
    fx, fy, fw, fh = face(BIPED["head"])
    hair = (60, 80, 52)
    for name in ("top",):
        x0, y0, w, h = face(BIPED["head"], name)
        fill_rect(img, x0, y0, w, h, hair)
    for ex in (1, 5):
        fill_rect(img, fx + ex, fy + 4, 2, 1, (24, 30, 26))
    fill_rect(img, fx + 3, fy + 4, 2, 1, shade(skin, -0.25))
    fill_rect(img, fx + 2, fy + 6, 4, 1, shade(skin, -0.45))
    return img


def zombie_villager():
    skin = (100, 150, 96)
    img = new(64, 64)
    head = (0, 32, 8, 10, 8)
    paint_box(img, head, skin, 11)
    paint_box(img, (24, 32, 2, 4, 2), shade(skin, -0.05), 12)
    paint_box(img, BIPED["body"], (110, 86, 60), 12)
    paint_box(img, BIPED["arm"], (110, 86, 60), 13)
    band(img, BIPED["arm"], range(6, 12), skin)
    paint_box(img, BIPED["leg"], (80, 64, 50), 14)
    fx, fy, fw, fh = face(head)
    for ex in (1, 5):
        fill_rect(img, fx + ex, fy + 4, 2, 1, (24, 30, 26))
    fill_rect(img, fx + 1, fy, 6, 2, shade(skin, -0.3))
    return img


def pigman():
    skin = (236, 156, 150)
    img = biped((64, 64), skin, (190, 150, 60), (120, 90, 50), shoe=(60, 50, 40))
    fx, fy, fw, fh = face(BIPED["head"])
    # half the face shows bone: the gaze and a tusk
    for y in range(fy, fy + 8):
        for x in range(fx + 4, fx + 8):
            if (x + y) % 3 != 0:
                put(img, x, y, mat_px((230, 226, 210), x, y, 0.0, 9, 0.1))
    for ex in (1, 5):
        fill_rect(img, fx + ex, fy + 3, 2, 1, (30, 20, 20))
    fill_rect(img, fx + 2, fy + 5, 4, 2, shade(skin, -0.1))
    put(img, fx + 3, fy + 6, shade(skin, -0.5))
    put(img, fx + 4, fy + 6, shade(skin, -0.5))
    return img


def skeleton(wither=False):
    bone = (60, 62, 68) if wither else (216, 214, 206)
    img = new(64, 32)
    paint_box(img, BIPED["head"], bone, 11, 0.1)
    paint_box(img, BIPED["body"], bone, 12, 0.1)
    paint_box(img, (40, 16, 2, 12, 2), bone, 13, 0.1)
    paint_box(img, (0, 16, 2, 12, 2), bone, 14, 0.1)
    fx, fy, fw, fh = face(BIPED["head"])
    hole = (16, 16, 20) if not wither else (8, 8, 10)
    for ex in (1, 5):
        fill_rect(img, fx + ex, fy + 3, 2, 2, hole)
    put(img, fx + 3, fy + 5, hole)
    put(img, fx + 4, fy + 5, hole)
    for x in range(fx + 1, fx + 7):
        put(img, x, fy + 6, shade(bone, -0.5) if x % 2 else shade(bone, 0.1))
    # ribs on the body
    bx, by, bw, bh = face(BIPED["body"])
    for y in range(by, by + bh):
        for x in range(bx, bx + bw):
            if (y - by) % 2 == 1 and (y - by) < 8 and x not in (bx + 3, bx + 4):
                put(img, x, y, shade(bone, -0.4))
            elif (y - by) >= 8 and x not in (bx + 3, bx + 4):
                put(img, x, y, (0, 0, 0), 0)
    return img


def creeper():
    green = (88, 176, 70)
    img = new(64, 32)
    for b, s in (((0, 0, 8, 8, 8), 11), ((16, 16, 8, 12, 4), 12), ((0, 16, 4, 6, 4), 13)):
        paint_box(img, b, green, s, 0.24)
    fx, fy, fw, fh = face((0, 0, 8, 8, 8))
    face_rows = ["........", "........", ".##..##.", ".##..##.", "...##...", "..####..", "..####..", "..#..#.."]
    for y, row in enumerate(face_rows):
        for x, ch in enumerate(row):
            if ch == "#":
                put(img, fx + x, fy + y, (18, 24, 18))
    return img


def creeper_armor():
    """Additive glow texture (black = invisible): Tidal-blue electric streaks."""
    img = new(64, 32)
    p = img.load()
    for y in range(32):
        for x in range(64):
            v = 0.5 + 0.5 * math.sin(2 * math.pi * (x / 16 + y / 32)) * math.sin(2 * math.pi * (x / 32 - y / 16))
            v = max(0.0, v - 0.55) / 0.45
            p[x, y] = (round(30 * v), round(130 * v), round(255 * v), 255)
    return img


def spider(cave=False):
    body = (60, 50, 50) if not cave else (30, 70, 80)
    img = new(64, 32)
    paint_box(img, (32, 4, 8, 8, 8), body, 11)
    paint_box(img, (0, 0, 6, 6, 6), shade(body, -0.1), 12)
    paint_box(img, (0, 12, 10, 8, 12), body, 13)
    paint_box(img, (18, 0, 16, 2, 2), shade(body, -0.2), 14)
    # fuzzy back stripe
    x0, y0, w, h = face((0, 12, 10, 8, 12), "top")
    for y in range(y0, y0 + h):
        for x in range(x0 + 3, x0 + 7):
            put(img, x, y, shade(body, 0.25 if (x + y) % 3 else -0.2))
    fx, fy, fw, fh = face((32, 4, 8, 8, 8))
    for (x, y) in ((1, 2), (6, 2), (2, 3), (5, 3), (3, 3), (4, 3)):
        put(img, fx + x, fy + y, (60, 14, 14))
    for x in range(fx + 2, fx + 6):
        put(img, x, fy + 6, (200, 196, 180) if x in (fx + 2, fx + 5) else shade(body, -0.5))
    return img


def spider_eyes():
    img = new(64, 32)
    fx, fy, fw, fh = face((32, 4, 8, 8, 8))
    for (x, y), c in (((1, 2), (255, 60, 60)), ((6, 2), (255, 60, 60)), ((2, 3), (255, 120, 120)),
                      ((5, 3), (255, 120, 120)), ((3, 3), (230, 40, 40)), ((4, 3), (230, 40, 40))):
        put(img, fx + x, fy + y, c)
    return img


def enderman():
    body = (26, 22, 34)
    img = new(64, 32)
    paint_box(img, (0, 0, 8, 8, 8), body, 11, 0.12)
    paint_box(img, (32, 16, 8, 12, 4), body, 12, 0.12)
    paint_box(img, (56, 0, 2, 30, 2), body, 13, 0.12)
    # the jaw layer (0,16) stays transparent except a thin lower jaw so the head reads as two parts
    jaw = (0, 16, 8, 8, 8)
    for name in ("front", "left", "right", "back"):
        x0, y0, w, h = face(jaw, name)
        for x in range(x0, x0 + w):
            put(img, x, y0 + h - 1, shade(body, -0.1))
    fx, fy, fw, fh = face((0, 0, 8, 8, 8))
    for ex in (0, 5):
        fill_rect(img, fx + ex, fy + 4, 3, 1, (200, 120, 240))
        put(img, fx + ex + (1 if ex == 0 else 1), fy + 4, (240, 200, 255))
    return img


def enderman_eyes():
    img = new(64, 32)
    fx, fy, fw, fh = face((0, 0, 8, 8, 8))
    for ex in (0, 5):
        fill_rect(img, fx + ex, fy + 4, 3, 1, (220, 140, 255))
        put(img, fx + ex + 1, fy + 4, (255, 230, 255))
    return img


def villager(robe, apron=None, trim=None):
    skin = (196, 140, 108)
    img = new(64, 64)
    head = (0, 0, 8, 10, 8)
    paint_box(img, head, skin, 11)
    paint_box(img, (24, 0, 2, 4, 2), shade(skin, -0.05), 12)
    paint_box(img, (16, 20, 8, 12, 6), robe, 13)
    paint_box(img, (0, 38, 8, 18, 6), robe, 14)
    paint_box(img, (44, 22, 4, 8, 4), robe, 15)
    paint_box(img, (40, 38, 8, 4, 4), robe, 16)
    band(img, (44, 22, 4, 8, 4), (6, 7), skin)
    paint_box(img, (0, 22, 4, 12, 4), shade(robe, -0.35), 17)
    if apron:
        for b in ((16, 20, 8, 12, 6), (0, 38, 8, 18, 6)):
            x0, y0, w, h = face(b)
            for y in range(y0 + (2 if b[1] == 20 else 0), y0 + h):
                for x in range(x0 + 1, x0 + w - 1):
                    put(img, x, y, mat_px(apron, x, y, 0.0, 19, 0.08))
    if trim:
        band(img, (0, 38, 8, 18, 6), (16, 17), trim)
        band(img, (16, 20, 8, 12, 6), (0,), trim)
    fx, fy, fw, fh = face(head)
    fill_rect(img, fx, fy, fw, 3, shade(skin, -0.12))
    fill_rect(img, fx + 1, fy + 3, 6, 1, (60, 44, 34))              # unibrow
    for ex in (1, 5):
        put(img, fx + ex, fy + 4, (240, 244, 250))
        put(img, fx + ex + 1, fy + 4, (60, 150, 80))
    fill_rect(img, fx + 2, fy + 8, 4, 1, shade(skin, -0.35))
    return img


def witch():
    img = villager((70, 40, 100), trim=(60, 160, 80))
    img = img.crop((0, 0, 64, 64))
    out = new(64, 128)
    out.alpha_composite(img)
    hat = (40, 30, 56)
    for b in ((0, 64, 10, 2, 10), (0, 76, 7, 4, 7), (0, 87, 4, 4, 4), (0, 95, 1, 2, 1)):
        paint_box(out, b, hat, 31, 0.1)
    band(out, (0, 76, 7, 4, 7), (3,), (80, 170, 90))
    paint_box(out, (0, 0, 1, 1, 1), (90, 140, 60), 32)
    return out


def iron_golem():
    iron = (200, 196, 188)
    img = new(128, 128)
    for b, s in (((0, 0, 8, 10, 8), 11), ((24, 0, 2, 4, 2), 12), ((0, 40, 18, 12, 11), 13), ((0, 70, 9, 5, 6), 14),
                 ((60, 21, 4, 30, 6), 15), ((37, 0, 6, 16, 5), 16), ((60, 0, 6, 16, 5), 17)):
        paint_box(img, b, iron, s, 0.2)
    rng = random.Random(5)
    vine_c = [(70, 140, 50), (90, 170, 60)]
    for b in ((0, 40, 18, 12, 11), (60, 21, 4, 30, 6), (37, 0, 6, 16, 5)):
        x0, y0, w, h = face(b)
        for _ in range(max(4, w * h // 18)):
            x, y = x0 + rng.randrange(w), y0 + rng.randrange(h)
            for k in range(rng.randint(2, 5)):
                put(img, x, y + k, vine_c[k % 2])
    fx, fy, fw, fh = face((0, 0, 8, 10, 8))
    fill_rect(img, fx, fy + 3, 8, 1, shade(iron, -0.35))
    for ex in (1, 5):
        fill_rect(img, fx + ex, fy + 4, 2, 1, (180, 40, 40))
    return img


def snowman():
    snow = (240, 244, 250)
    img = new(64, 64)
    paint_box(img, (0, 16, 10, 10, 10), snow, 11, 0.08)
    paint_box(img, (0, 36, 12, 12, 12), snow, 12, 0.08)
    paint_box(img, (32, 0, 12, 2, 2), (110, 80, 50), 13)
    pumpkin = (222, 126, 30)
    paint_box(img, (0, 0, 8, 8, 8), pumpkin, 14, 0.2)
    fx, fy, fw, fh = face((0, 0, 8, 8, 8))
    for (x, y) in ((1, 2), (2, 2), (5, 2), (6, 2), (1, 5), (2, 6), (3, 6), (4, 6), (5, 6), (6, 5)):
        put(img, fx + x, fy + y, (250, 210, 80))
    return img


def pig():
    pink = (236, 156, 160)
    img = new(64, 32)
    for b, s in (((0, 0, 8, 8, 8), 11), ((28, 8, 10, 16, 8), 12), ((0, 16, 4, 6, 4), 13)):
        paint_box(img, b, pink, s, 0.12)
    paint_box(img, (16, 16, 4, 3, 1), shade(pink, 0.15), 14)
    sx, sy, sw, sh = face((16, 16, 4, 3, 1))
    put(img, sx, sy + 1, (150, 80, 90))
    put(img, sx + 3, sy + 1, (150, 80, 90))
    fx, fy, fw, fh = face((0, 0, 8, 8, 8))
    for ex in (0, 6):
        put(img, fx + ex, fy + 3, (240, 244, 250))
        put(img, fx + ex + 1, fy + 3, (24, 24, 30))
    band(img, (0, 16, 4, 6, 4), (5,), (120, 80, 80))
    return img


def pig_saddle():
    img = new(64, 32)
    leather = (120, 76, 44)
    for name in ("front", "back", "left", "right", "top"):
        x0, y0, w, h = face((28, 8, 10, 16, 8), name)
        if name == "top":
            continue
        for y in range(y0 + 4, y0 + 11):
            for x in range(x0, x0 + w):
                c = mat_px(leather, x, y, LIGHT[name], 21, 0.1)
                if y in (y0 + 4, y0 + 10):
                    c = shade(leather, -0.4)
                put(img, x, y, c)
    return img


def cow(red=False):
    base = (240, 236, 230)
    spot = (60, 46, 40) if not red else (190, 40, 40)
    if red:
        base, spot = (196, 40, 40), (236, 230, 226)
    img = new(64, 32)
    for b, s in (((0, 0, 8, 8, 6), 11), ((18, 4, 12, 18, 10), 12), ((0, 16, 4, 12, 4), 13)):
        paint_box(img, b, base, s, 0.1)
    paint_box(img, (22, 0, 1, 3, 1), (220, 214, 196), 14)
    paint_box(img, (52, 0, 4, 6, 1), (236, 160, 170), 15)
    rng = random.Random(3)
    sp = fbm(64, 32, 41, cells=(8, 4), weights=(0.7, 0.3))
    p = img.load()
    for y in range(32):
        for x in range(64):
            if p[x, y][3] and sp[y][x] > 0.62 and not (52 <= x < 62 and y < 8) and not (22 <= x < 26 and y < 4):
                p[x, y] = (*mat_px(spot, x, y, 0.0, 7, 0.08), 255)
    band(img, (0, 16, 4, 12, 4), (10, 11), (60, 50, 44))
    fx, fy, fw, fh = face((0, 0, 8, 8, 6))
    for ex in (0, 6):
        fill_rect(img, fx + ex, fy + 3, 2, 1, (24, 24, 30))
        put(img, fx + (ex if ex == 0 else 7), fy + 3, (240, 244, 250))
    fill_rect(img, fx + 2, fy + 5, 4, 3, (236, 180, 170) if not red else (236, 190, 186))
    put(img, fx + 2, fy + 6, (120, 70, 70))
    put(img, fx + 5, fy + 6, (120, 70, 70))
    if red:   # mushrooms on the back
        x0, y0, w, h = face((18, 4, 12, 18, 10), "top")
        for (x, y) in ((3, 4), (8, 12), (5, 15)):
            fill_rect(img, x0 + x, y0 + y, 2, 2, (206, 40, 40))
            put(img, x0 + x, y0 + y, (240, 236, 230))
    return img


def sheep():
    img = new(64, 32)
    paint_box(img, (0, 0, 6, 6, 8), (226, 196, 176), 11, 0.1)
    paint_box(img, (28, 8, 8, 16, 6), (226, 196, 176), 12, 0.1)
    paint_box(img, (0, 16, 4, 12, 4), (226, 196, 176), 13, 0.1)
    fx, fy, fw, fh = face((0, 0, 6, 6, 8))
    put(img, fx, fy + 2, (24, 24, 30))
    put(img, fx + 5, fy + 2, (24, 24, 30))
    fill_rect(img, fx + 2, fy + 4, 2, 1, (180, 120, 120))
    return img


def sheep_fur():
    wool = (232, 232, 232)
    img = new(64, 32)
    for b, s in (((0, 0, 6, 6, 6), 11), ((28, 8, 8, 16, 6), 12), ((0, 16, 4, 6, 4), 13)):
        paint_box(img, b, wool, s, 0.1)
    p = img.load()
    for y in range(32):
        for x in range(64):
            if p[x, y][3] and (x + 2 * y) % 6 == 0:
                p[x, y] = (*shade(p[x, y][:3], -0.15), 255)
    return img


def chicken():
    white = (240, 240, 236)
    img = new(64, 32)
    for b, s in (((0, 0, 4, 6, 3), 11), ((0, 9, 6, 8, 6), 12), ((24, 13, 1, 4, 6), 13)):
        paint_box(img, b, white, s, 0.08)
    paint_box(img, (14, 0, 4, 2, 2), (240, 170, 40), 14)
    paint_box(img, (14, 4, 2, 2, 2), (214, 40, 40), 15)
    paint_box(img, (26, 0, 3, 5, 3), (240, 170, 40), 16)
    fx, fy, fw, fh = face((0, 0, 4, 6, 3))
    put(img, fx, fy + 2, (24, 24, 30))
    put(img, fx + 3, fy + 2, (24, 24, 30))
    return img


def wolf(kind="wild"):
    fur = {"wild": (206, 200, 194), "tame": (226, 222, 216), "angry": (186, 176, 170)}[kind]
    img = new(64, 32)
    for b, s in (((0, 0, 6, 6, 4), 11), ((18, 14, 6, 9, 6), 12), ((21, 0, 8, 6, 7), 13), ((0, 18, 2, 8, 2), 14),
                 ((9, 18, 2, 8, 2), 15), ((16, 14, 2, 2, 1), 16), ((0, 10, 3, 3, 4), 17)):
        paint_box(img, b, fur, s, 0.12)
    # darker saddle along the back, tail tip
    x0, y0, w, h = face((18, 14, 6, 9, 6), "front")
    fill_rect(img, x0 + 1, y0, w - 2, 4, shade(fur, -0.3))
    nx, ny, nw, nh = face((0, 10, 3, 3, 4))
    fill_rect(img, nx + 1, ny, 1, 1, (24, 24, 30))
    fx, fy, fw, fh = face((0, 0, 6, 6, 4))
    eye = (24, 24, 30)
    if kind == "angry":
        eye = (200, 40, 40)
        for x in range(fx, fx + fw):
            put(img, x, fy + 1, shade(fur, -0.4))
    put(img, fx + 1, fy + 2, eye)
    put(img, fx + 4, fy + 2, eye)
    return img


def wolf_collar():
    img = new(64, 32)
    for name in ("front", "back", "left", "right"):
        x0, y0, w, h = face((21, 0, 8, 6, 7), name)
        for x in range(x0, x0 + w):
            for y in (y0 + h - 2, y0 + h - 1):
                put(img, x, y, (226, 226, 226) if y == y0 + h - 2 else (196, 196, 196))
    return img


def cat(fur, stripes=None, eye=(80, 200, 120)):
    img = new(64, 32)
    for b, s in (((0, 0, 5, 4, 5), 11), ((20, 0, 4, 16, 6), 12), ((0, 15, 1, 8, 1), 13), ((4, 15, 1, 8, 1), 14),
                 ((8, 13, 2, 6, 2), 15), ((40, 0, 2, 10, 2), 16), ((0, 10, 1, 1, 2), 17), ((6, 10, 1, 1, 2), 18)):
        paint_box(img, b, fur, s, 0.12)
    paint_box(img, (0, 24, 3, 2, 2), shade(fur, 0.15), 19)
    if stripes:
        p = img.load()
        for y in range(32):
            for x in range(64):
                if p[x, y][3] and (x + y // 2) % 4 == 0:
                    p[x, y] = (*stripes, 255)
    fx, fy, fw, fh = face((0, 0, 5, 4, 5))
    put(img, fx, fy + 2, eye)
    put(img, fx + 4, fy + 2, eye)
    return img


def slime(magma=False):
    img = new(64, 32)
    if magma:
        return from_mask("entity/slime/magmacube.png", (190, 70, 30), 31, 0.28)
    paint_box(img, (0, 0, 8, 8, 8), (110, 200, 90), 11, 0.1, alpha=150)
    paint_box(img, (0, 16, 6, 6, 6), (90, 180, 76), 12, 0.1)
    paint_box(img, (32, 0, 2, 2, 2), (24, 50, 24), 13, 0.0)
    paint_box(img, (32, 4, 2, 2, 2), (24, 50, 24), 13, 0.0)
    paint_box(img, (32, 8, 1, 1, 1), (24, 50, 24), 13, 0.0)
    return img


def blaze():
    img = new(64, 32)
    paint_box(img, (0, 0, 8, 8, 8), (240, 190, 60), 11, 0.24)
    paint_box(img, (0, 16, 2, 8, 2), (250, 160, 40), 12, 0.2)
    fx, fy, fw, fh = face((0, 0, 8, 8, 8))
    for ex in (1, 5):
        fill_rect(img, fx + ex, fy + 3, 2, 1, (60, 30, 10))
    fill_rect(img, fx + 2, fy + 6, 4, 1, (120, 60, 20))
    return img


def ghast(shooting=False):
    img = new(64, 32)
    paint_box(img, (0, 0, 16, 16, 16), (236, 236, 240), 11, 0.08)
    fx, fy, fw, fh = face((0, 0, 16, 16, 16))
    eye = (40, 40, 48) if not shooting else (200, 40, 40)
    for ex in (3, 10):
        if shooting:
            fill_rect(img, fx + ex, fy + 4, 3, 3, (40, 40, 48))
            put(img, fx + ex + 1, fy + 5, eye)
        else:
            fill_rect(img, fx + ex, fy + 6, 3, 1, (60, 60, 70))
    if shooting:
        fill_rect(img, fx + 5, fy + 10, 6, 4, (40, 30, 36))
    else:
        fill_rect(img, fx + 6, fy + 11, 4, 1, (90, 90, 100))
    return img


def squid():
    img = new(64, 32)
    paint_box(img, (0, 0, 12, 16, 12), (40, 70, 110), 11, 0.14)
    paint_box(img, (48, 0, 2, 18, 2), (50, 84, 130), 12, 0.14)
    fx, fy, fw, fh = face((0, 0, 12, 16, 12))
    for ex in (2, 8):
        fill_rect(img, fx + ex, fy + 10, 2, 2, (230, 236, 246))
        put(img, fx + ex + 1, fy + 11, (24, 24, 30))
    return img


def silverfish(mite=False):
    img = new(64, 32)
    col = (140, 146, 156) if not mite else (60, 30, 80)
    if mite:
        sizes, uvs = [[4, 3, 2], [6, 4, 5], [3, 3, 1], [1, 2, 1]], [[0, 0], [0, 5], [0, 14], [0, 18]]
    else:
        sizes = [[3, 2, 2], [4, 3, 2], [6, 4, 3], [3, 3, 3], [2, 2, 3], [2, 1, 2], [1, 1, 2]]
        uvs = [[0, 0], [0, 4], [0, 9], [0, 16], [0, 22], [11, 0], [13, 4]]
    for (w, h, d), (u, v) in zip(sizes, uvs):
        paint_box(img, (u, v, w, h, d), col, 11 + u + v, 0.18)
    if not mite:
        for b in ((20, 0, 10, 8, 3), (20, 11, 6, 4, 3), (20, 18, 6, 5, 2)):
            paint_box(img, b, shade(col, -0.2), 21, 0.2)
    return img


def chest(kind, double=False):
    """Lid / base / latch. normal & trapped share the wood; trapped gets red bands; ender is obsidian + teal."""
    w = 30 if double else 14
    size = (128, 64) if double else (64, 64)
    wood = {"normal": (166, 110, 56), "trapped": (166, 110, 56), "christmas": (196, 50, 50), "ender": (34, 30, 50)}[kind]
    trim = {"normal": (90, 64, 40), "trapped": (200, 50, 40), "christmas": (60, 150, 70), "ender": (40, 150, 140)}[kind]
    img = new(*size)
    lid, base = (0, 0, w, 5, 14), (0, 19, w, 10, 14)
    paint_box(img, lid, wood, 11, 0.12)
    paint_box(img, base, wood, 12, 0.12)
    # planks: horizontal lines on the sides, a rim at the lid's bottom and base's top
    for b in (lid, base):
        for name in ("front", "back", "left", "right"):
            x0, y0, fw, fh = face(b, name)
            for x in range(x0, x0 + fw):
                put(img, x, y0, shade(trim, 0.0))
                put(img, x, y0 + fh - 1, shade(trim, -0.2))
                if b is base:
                    put(img, x, y0 + 4, shade(wood, -0.3))
            for y in range(y0, y0 + fh):
                put(img, x0, y, shade(trim, -0.1))
                put(img, x0 + fw - 1, y, shade(trim, -0.3))
        x0, y0, fw, fh = face(b, "top" if b is lid else "bottom")
        for x in range(x0, x0 + fw):
            put(img, x, y0, trim)
            put(img, x, y0 + fh - 1, trim)
        for y in range(y0, y0 + fh):
            put(img, x0, y, trim)
            put(img, x0 + fw - 1, y, trim)
    latch = (230, 210, 120) if kind != "ender" else (120, 230, 220)
    paint_box(img, (0, 0, 2, 4, 1), latch, 13, 0.1)
    return img


def sign():
    img = new(64, 32)
    paint_box(img, (0, 0, 24, 12, 2), WOODS["oak"][0], 11, 0.12)
    paint_box(img, (0, 14, 2, 14, 2), WOODS["oak"][1], 12, 0.12)
    fx, fy, fw, fh = face((0, 0, 24, 12, 2))
    for b in ((0, 0, 24, 12, 2),):
        for name in ("front", "back"):
            x0, y0, w, h = face(b, name)
            for x in range(x0, x0 + w):
                put(img, x, y0, shade(WOODS["oak"][0], -0.4))
                put(img, x, y0 + h - 1, shade(WOODS["oak"][0], -0.4))
            for y in range(y0, y0 + h):
                put(img, x0, y, shade(WOODS["oak"][0], -0.4))
                put(img, x0 + w - 1, y, shade(WOODS["oak"][0], -0.4))
    return img


def arrow_entity():
    img = new(32, 32)
    shaft = ramp((112, 76, 44), (-0.3, 0.0, 0.3))
    tip = ramp((150, 154, 164), (-0.4, 0.0, 0.4))
    for base in (0, 10):
        for x in range(16):
            put(img, x, base + 2, shaft[1])
        for (x, y) in ((0, 2), (1, 1), (1, 3), (2, 0), (2, 4), (1, 2), (2, 2), (3, 2)):
            put(img, x, base + y, tip[2] if y <= 2 else tip[0])
        for x in range(12, 16):
            for y in (1, 3):
                put(img, x, base + y, (236, 240, 246) if x % 2 else (200, 206, 216))
    for i in range(5):
        put(img, i, 7, (236, 240, 246))
        put(img, 2, 5 + i, (236, 240, 246))
    return img


def xp_orbs():
    img = new(64, 64)
    for i in range(11):
        cx, cy = (i % 4) * 16 + 8, (i // 4) * 16 + 8
        r = 2.2 + i * 0.42
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - 8, y + 0.5 - 8
                d = math.hypot(dx, dy)
                if d <= r:
                    t = math.hypot(dx + r * 0.35, dy + r * 0.35) / (r * 1.3)
                    v = 255 if t < 0.25 else 220 if t < 0.55 else 176 if d < r - 0.8 else 120
                    put(img, cx - 8 + x, cy - 8 + y, (v, v, v))
    return img


def explosion():
    frames = new(128, 128)
    for f in range(16):
        ox, oy = (f % 4) * 32, (f // 4) * 32
        t = f / 15
        rng = random.Random(f)
        for k in range(10):
            ang = k / 10 * 2 * math.pi + rng.uniform(-0.2, 0.2)
            dist = 4 + t * 9
            cx, cy = 16 + math.cos(ang) * dist * rng.uniform(0.5, 1), 16 + math.sin(ang) * dist * rng.uniform(0.5, 1)
            r = (5 - t * 3) * rng.uniform(0.8, 1.2)
            for y in range(32):
                for x in range(32):
                    d = math.hypot(x - cx, y - cy)
                    if d < r:
                        heat = 1 - t
                        c = mix((90, 90, 96), (255, 220, 120), heat * (1 - d / r))
                        put(frames, ox + x, oy + y, c)
    return frames


def end_portal():
    img = Image.new("RGBA", (256, 256), (6, 10, 18, 255))
    rng = random.Random(77)
    p = img.load()
    for _ in range(900):
        x, y = rng.randrange(256), rng.randrange(256)
        c = rng.choice([(60, 180, 200), (90, 120, 230), (140, 230, 220), (40, 100, 160)])
        p[x, y] = (*c, 255)
    return img


def beam(color, w=16, h=16, alpha=True):
    img = new(w, h)
    for y in range(h):
        for x in range(w):
            t = abs(x + 0.5 - w / 2) / (w / 2)
            c = mix((255, 255, 255), color, t)
            put(img, x, y, c, round(255 * (1 - t * 0.6)) if alpha else 255)
    return img


def book_model():
    img = new(64, 32)
    p = img.load()
    cover = (110, 70, 140)
    for y in range(32):
        for x in range(64):
            if y < 10:
                p[x, y] = (*mat_px(cover, x, y, 0.0, 41, 0.12), 255)
            elif y < 20:
                p[x, y] = (*((236, 230, 214) if (y % 2 or x % 5) else (200, 196, 186)), 255)
    return img


def endercrystal():
    img = new(128, 64)
    for b in ((0, 0, 8, 8, 8),):
        paint_box(img, b, (190, 120, 230), 11, 0.1, alpha=170)
    paint_box(img, (32, 0, 8, 8, 8), (240, 120, 240), 12, 0.2)
    paint_box(img, (0, 16, 12, 4, 12), (40, 30, 56), 13, 0.12)
    return img


# ---------------------------------------------------------------- banners
def banner_model():
    img = new(64, 64)
    paint_box(img, (0, 0, 20, 40, 1), (230, 230, 230), 11, 0.06)
    paint_box(img, (44, 0, 2, 42, 2), WOODS["oak"][0], 12, 0.12)
    paint_box(img, (0, 42, 20, 2, 2), WOODS["oak"][0], 13, 0.12)
    return img


def banner_patterns():
    """Masks drawn on the flag (front face at (1,1), back at (22,1), both 20x40). White = pattern."""
    W, H = 20, 40

    def shapes(name, x, y):
        cx, cy = x - 9.5, y - 19.5
        return {
            "base": True,
            "border": x < 2 or x > 17 or y < 2 or y > 37,
            "curly_border": (x < 2 or x > 17 or y < 2 or y > 37) or ((x < 4 or x > 15 or y < 4 or y > 35) and (x + y) % 4 == 0),
            "bricks": (y % 6 == 5) or ((x + (6 if (y // 6) % 2 else 0)) % 12 == 11),
            "circle": math.hypot(cx, cy * 1.0) < 5.5,
            "creeper": _emblem("creeper", x, y),
            "cross": abs(x - y * 0.5) < 1.6 or abs((19 - x) - y * 0.5) < 1.6,
            "straight_cross": abs(cx) < 2.5 or abs(cy) < 2.5,
            "diagonal_left": x + y * 0.5 < 20,
            "diagonal_right": (19 - x) + y * 0.5 < 20,
            "diagonal_up_left": x + y * 0.5 >= 20,
            "diagonal_up_right": (19 - x) + y * 0.5 >= 20,
            "flower": _emblem("flower", x, y),
            "gradient": True,
            "gradient_up": True,
            "half_horizontal": y < 20,
            "half_horizontal_bottom": y >= 20,
            "half_vertical": x < 10,
            "half_vertical_right": x >= 10,
            "mojang": _emblem("wave", x, y),
            "rhombus": abs(cx) / 7 + abs(cy) / 14 < 1,
            "skull": _emblem("skull", x, y),
            "small_stripes": x % 4 in (1, 2) and y < 36,
            "square_bottom_left": x < 7 and y > 25,
            "square_bottom_right": x > 12 and y > 25,
            "square_top_left": x < 7 and y < 14,
            "square_top_right": x > 12 and y < 14,
            "stripe_bottom": y > 27,
            "stripe_center": abs(cx) < 3,
            "stripe_downleft": abs((19 - x) - y * 0.5) < 2.5,
            "stripe_downright": abs(x - y * 0.5) < 2.5,
            "stripe_left": x < 6,
            "stripe_middle": abs(cy) < 3,
            "stripe_right": x > 13,
            "stripe_top": y < 12,
            "triangles_bottom": y > 34 - (abs((x % 5) - 2)),
            "triangles_top": y < 5 + abs((x % 5) - 2) - 2,
            "triangle_bottom": y > 39 - (10 - abs(cx)),
            "triangle_top": y < (10 - abs(cx)),
        }[name]

    names = ["base", "border", "bricks", "circle", "creeper", "cross", "curly_border", "diagonal_left",
             "diagonal_right", "diagonal_up_left", "diagonal_up_right", "flower", "gradient", "gradient_up",
             "half_horizontal", "half_horizontal_bottom", "half_vertical", "half_vertical_right", "mojang", "rhombus",
             "skull", "small_stripes", "square_bottom_left", "square_bottom_right", "square_top_left",
             "square_top_right", "straight_cross", "stripe_bottom", "stripe_center", "stripe_downleft",
             "stripe_downright", "stripe_left", "stripe_middle", "stripe_right", "stripe_top", "triangles_bottom",
             "triangles_top", "triangle_bottom", "triangle_top"]
    out = {}
    for name in names:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 255))
        p = img.load()
        for y in range(H):
            for x in range(W):
                on = shapes(name, x, y)
                if name == "gradient":
                    v = round(255 * (1 - y / 39))
                elif name == "gradient_up":
                    v = round(255 * (y / 39))
                elif name == "base":
                    v = 200 + (12 if (x + y) % 7 == 0 else 0)
                else:
                    v = 255 if on else 0
                p[1 + x, 1 + y] = (v, v, v, 255)
                p[22 + (19 - x), 1 + y] = (v, v, v, 255)
        if name == "base":
            # the rest of the flag box (edges/top) keeps the base shading too
            for y in range(0, 41):
                for x in range(0, 42):
                    if p[x, y][:3] == (0, 0, 0):
                        p[x, y] = (190, 190, 190, 255)
        out[name] = img
    return out


EMBLEMS = {
    "creeper": ["..........", "..##..##..", "..##..##..", "....##....", "...####...", "...#..#..."],
    "skull": ["...####...", "..######..", "..#.##.#..", "..######..", "...#..#...", "..#....#..", ".#......#."],
    "flower": ["....##....", "..#.##.#..", "...####...", ".########.", "...####...", "..#.##.#..", "....##...."],
    "wave": ["..........", "...###....", "..#...#...", ".#.....#.#", ".......##.", "..........",
             "...###....", "..#...#...", ".#.....#.#", ".......##."],
}


def _emblem(kind, x, y):
    rows = EMBLEMS[kind]
    oy = 20 - len(rows)          # 2x scale, centered on the flag
    ey = (y - oy) // 2
    if 0 <= ey < len(rows) and 0 <= x // 2 < 10:
        return rows[ey][x // 2] == "#"
    return False


# ---------------------------------------------------------------- mask-painted models
HORSES = {"horse_white": (236, 232, 226), "horse_creamy": (220, 190, 140), "horse_chestnut": (170, 100, 56),
          "horse_brown": (120, 80, 50), "horse_black": (40, 36, 40), "horse_gray": (130, 130, 136),
          "horse_darkbrown": (80, 54, 36), "donkey": (130, 116, 100), "mule": (100, 70, 50),
          "horse_skeleton": (216, 214, 206), "horse_zombie": (100, 150, 96)}


def generate():
    save(player(), "entity/steve.png")
    save(player(alex=True), "entity/alex.png")
    save(zombie(), "entity/zombie/zombie.png")
    save(zombie_villager(), "entity/zombie/zombie_villager.png")
    save(pigman(), "entity/zombie_pigman.png")
    save(skeleton(), "entity/skeleton/skeleton.png")
    save(skeleton(wither=True), "entity/skeleton/wither_skeleton.png")
    save(creeper(), "entity/creeper/creeper.png")
    save(creeper_armor(), "entity/creeper/creeper_armor.png")
    save(spider(), "entity/spider/spider.png")
    save(spider(cave=True), "entity/spider/cave_spider.png")
    save(spider_eyes(), "entity/spider_eyes.png")
    save(enderman(), "entity/enderman/enderman.png")
    save(enderman_eyes(), "entity/enderman/enderman_eyes.png")
    save(villager((120, 84, 52)), "entity/villager/villager.png")
    save(villager((120, 84, 52), apron=None, trim=(214, 178, 74)), "entity/villager/farmer.png")
    save(villager((230, 226, 214), trim=(150, 60, 40)), "entity/villager/librarian.png")
    save(villager((120, 60, 150), trim=(230, 200, 80)), "entity/villager/priest.png")
    save(villager((60, 60, 66), apron=(30, 30, 34)), "entity/villager/smith.png")
    save(villager((120, 84, 52), apron=(236, 232, 226)), "entity/villager/butcher.png")
    save(witch(), "entity/witch.png")
    save(iron_golem(), "entity/iron_golem.png")
    save(snowman(), "entity/snowman.png")
    save(pig(), "entity/pig/pig.png")
    save(pig_saddle(), "entity/pig/pig_saddle.png")
    save(cow(), "entity/cow/cow.png")
    save(cow(red=True), "entity/cow/mooshroom.png")
    save(sheep(), "entity/sheep/sheep.png")
    save(sheep_fur(), "entity/sheep/sheep_fur.png")
    save(chicken(), "entity/chicken.png")
    save(wolf(), "entity/wolf/wolf.png")
    save(wolf("tame"), "entity/wolf/wolf_tame.png")
    save(wolf("angry"), "entity/wolf/wolf_angry.png")
    save(wolf_collar(), "entity/wolf/wolf_collar.png")
    save(cat((230, 190, 90), stripes=(200, 150, 60), eye=(90, 200, 90)), "entity/cat/ocelot.png")
    save(cat((40, 40, 46), eye=(230, 200, 60)), "entity/cat/black.png")
    save(cat((226, 140, 60), stripes=(200, 110, 40), eye=(230, 200, 60)), "entity/cat/red.png")
    save(cat((236, 226, 206), stripes=None, eye=(60, 140, 230)), "entity/cat/siamese.png")
    save(slime(), "entity/slime/slime.png")
    save(slime(magma=True), "entity/slime/magmacube.png")
    save(blaze(), "entity/blaze.png")
    save(ghast(), "entity/ghast/ghast.png")
    save(ghast(True), "entity/ghast/ghast_shooting.png")
    save(squid(), "entity/squid.png")
    save(silverfish(), "entity/silverfish.png")
    save(silverfish(mite=True), "entity/endermite.png")
    for kind in ("normal", "trapped", "christmas"):
        save(chest(kind), f"entity/chest/{kind}.png")
        save(chest(kind, double=True), f"entity/chest/{kind}_double.png")
    save(chest("ender"), "entity/chest/ender.png")
    save(sign(), "entity/sign.png")
    save(arrow_entity(), "entity/arrow.png")
    save(xp_orbs(), "entity/experience_orb.png")
    save(explosion(), "entity/explosion.png")
    save(end_portal(), "entity/end_portal.png")
    save(beam((120, 220, 255)), "entity/beacon_beam.png")
    save(beam((120, 230, 220), 32, 32), "entity/guardian_beam.png")
    save(beam((220, 120, 255), 16, 256), "entity/endercrystal/endercrystal_beam.png")
    save(book_model(), "entity/enchanting_table_book.png")
    save(endercrystal(), "entity/endercrystal/endercrystal.png")
    save(banner_model(), "entity/banner_base.png")
    for name, img in banner_patterns().items():
        save(img, f"entity/banner/{name}.png")

    # models painted from UV occupancy
    for name, c in HORSES.items():
        save(from_mask(f"entity/horse/{name}.png", c, 51, 0.12), f"entity/horse/{name}.png")
    for name, c in (("blackdots", (30, 30, 34)), ("white", (240, 240, 240)), ("whitedots", (240, 240, 240)),
                    ("whitefield", (240, 240, 240))):
        save(from_mask(f"entity/horse/horse_markings_{name}.png", c, 53, 0.06), f"entity/horse/horse_markings_{name}.png")
    for mat, c in (("iron", (214, 218, 228)), ("gold", (250, 204, 54)), ("diamond", (76, 226, 216))):
        save(from_mask(f"entity/horse/armor/horse_armor_{mat}.png", c, 55, 0.14), f"entity/horse/armor/horse_armor_{mat}.png")
    save(from_mask("entity/enderdragon/dragon.png", (34, 26, 44), 57, 0.2), "entity/enderdragon/dragon.png")
    save(from_mask("entity/enderdragon/dragon_eyes.png", (220, 140, 255), 58, 0.0, edge=False), "entity/enderdragon/dragon_eyes.png")
    save(from_mask("entity/enderdragon/dragon_exploding.png", (40, 30, 50), 59, 0.1), "entity/enderdragon/dragon_exploding.png")
    save(from_mask("entity/wither/wither.png", (40, 42, 48), 61, 0.16), "entity/wither/wither.png")
    save(creeper_armor().resize((64, 64), Image.NEAREST), "entity/wither/wither_armor.png")
    save(from_mask("entity/wither/wither_invulnerable.png", (90, 110, 170), 62, 0.16), "entity/wither/wither_invulnerable.png")
    save(from_mask("entity/guardian.png", (90, 168, 150), 63, 0.18, skip=(42, 54, 64, 64)), "entity/guardian.png")
    save(from_mask("entity/guardian_elder.png", (200, 196, 180), 64, 0.18, skip=(42, 54, 64, 64)), "entity/guardian_elder.png")
    save(from_mask("entity/bat.png", (70, 56, 50), 65, 0.14), "entity/bat.png")
    for name, c in (("black", (40, 36, 40)), ("brown", (140, 100, 70)), ("caerbannog", (240, 240, 240)),
                    ("gold", (230, 190, 100)), ("salt", (200, 180, 160)), ("toast", (60, 50, 50)),
                    ("white", (240, 240, 240)), ("white_splotched", (230, 228, 224))):
        save(from_mask(f"entity/rabbit/{name}.png", c, 66, 0.14), f"entity/rabbit/{name}.png")
    save(from_mask("entity/boat.png", WOODS["oak"][0], 67, 0.16), "entity/boat.png")
    save(from_mask("entity/minecart.png", (130, 134, 146), 68, 0.16), "entity/minecart.png")
    save(from_mask("entity/lead_knot.png", (190, 160, 110), 69, 0.14), "entity/lead_knot.png")
    save(from_mask("entity/armorstand/wood.png", WOODS["oak"][0], 70, 0.12), "entity/armorstand/wood.png")

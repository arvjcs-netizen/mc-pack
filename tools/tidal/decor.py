"""Every block texture blocks.py doesn't cover: plants, crops, redstone, rails, doors, utility blocks, stone
variants, nether/end/ocean blocks. Same rules as blocks.py: families share one shape and only change palette."""
import math
import random

from blocks import (DYES, STONE, WOODS, bevel, brick_pattern, cobble_pattern, dirt_tex, grass_fringe, plank_pattern,
                    soft_noise, stone_tex)
from lib import (fbm, grid, layout_mask, line, mix, mul, new, outline, paint, quantize, ramp, rect, save, save_anim,
                 shade, sprite)

IRON_DARK = (74, 76, 86)
IRON = (196, 200, 212)
GOLD = (250, 204, 54)
REDSTONE = (226, 30, 30)
SAND = (214, 198, 140)
RED_SAND = (196, 104, 48)
LEAF = {  # sapling / plant leaf colors per wood type (saplings are not biome-tinted)
    "oak": (82, 150, 50), "spruce": (50, 96, 62), "birch": (120, 168, 70),
    "jungle": (60, 150, 40), "acacia": (130, 150, 50), "roofed_oak": (54, 110, 36),
}
SAPLING_BARK = {"oak": "oak", "spruce": "spruce", "birch": "birch", "jungle": "jungle", "acacia": "acacia",
                "roofed_oak": "big_oak"}


def px_of(img):
    return img.load()


def clip(img, mask):
    """Clear every pixel the game never samples (mask from the vanilla UV layout)."""
    p = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                p[x, y] = (0, 0, 0, 0)
    return img


def planks(wood):
    return paint(plank_pattern(), ramp(WOODS[wood][0], (-0.55, -0.22, 0.0, 0.2, 0.42)))


def smooth_stone(base=STONE, seed=5):
    return paint(bevel(soft_noise(seed, (0.3, 0.4, 0.3), base=1), 4, 0), ramp(base, (-0.45, -0.12, 0.0, 0.12, 0.3)))


def framed(img, color, inner=None):
    p = img.load()
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)):
            p[x, y] = (*color, 255)
        if inner:
            for (x, y) in ((i, 1), (1, i)):
                if 0 < i < 15:
                    p[x, y] = (*inner, 255)
    return img


# ---------------------------------------------------------------- plants
def blades(seed, n, hmin, hmax, pal, spread=(2, 14), lean=0.35, img=None):
    """Grass-like blades from the bottom edge. pal: dark..light."""
    rng = random.Random(seed)
    img = img or new()
    p = img.load()
    for i in range(n):
        x0 = spread[0] + (spread[1] - spread[0]) * (i + rng.random() * 0.6) / n
        hgt = rng.uniform(hmin, hmax)
        bend = rng.uniform(-lean, lean)
        for k in range(int(hgt)):
            t = k / max(1, hgt - 1)
            x = round(x0 + bend * k * t * 2.2)
            y = 15 - k
            if 0 <= x < 16 and 0 <= y < 16:
                c = pal[min(len(pal) - 1, int(t * len(pal) * 0.999))] if k > 0 else pal[0]
                p[x, y] = (*c, 255)
    return img


GRAY_PLANT = [(70, 70, 70), (104, 104, 104), (140, 140, 140), (176, 176, 176)]


def fern(seed=4, tall=False, top=False):
    img = new()
    p = img.load()
    rng = random.Random(seed)
    fronds = [(4, -0.55), (8, 0.05), (12, 0.5)] if not tall else [(5, -0.35), (10, 0.3)]
    for fx, lean in fronds:
        hgt = (13 if not tall else 16) - abs(lean) * 4
        for k in range(int(hgt)):
            y = 15 - k
            x = round(fx + lean * k)
            if not (0 <= x < 16 and 0 <= y < 16):
                continue
            c = GRAY_PLANT[1 + min(2, k // 5)]
            p[x, y] = (*c, 255)
            if k > 2 and k % 2 == 0:            # leaflets
                for s in (-1, 1):
                    for j in (1, 2) if k < hgt - 3 else (1,):
                        xx = x + s * j
                        if 0 <= xx < 16:
                            p[xx, y - (j - 1)] = (*GRAY_PLANT[2 if s < 0 else 1], 255)
    if top:
        img = img.transpose(0)  # mirror so the two halves of a double fern differ
    return img


def deadbush():
    img = new()
    p = img.load()
    c = ramp((150, 104, 52), (-0.4, 0.0, 0.3))
    branches = [((8, 15), (8, 9)), ((8, 11), (4, 6)), ((8, 10), (12, 5)), ((4, 6), (2, 3)), ((4, 6), (5, 2)),
                ((12, 5), (14, 2)), ((12, 5), (10, 2)), ((8, 9), (8, 4)), ((6, 13), (3, 11)), ((10, 13), (13, 11))]
    for a, b in branches:
        line(p, a, b, c[1], 16, 16)
    for (x, y) in [(2, 3), (5, 2), (14, 2), (10, 2), (8, 4), (3, 11), (13, 11)]:
        p[x, y] = (*c[2], 255)
    return img


def stem_and_leaves(img, top, leaf=(70, 140, 50), x=7, leaves=((10, -1), (12, 1))):
    p = img.load()
    g = ramp(leaf, (-0.4, 0.0, 0.3))
    for y in range(top, 16):
        p[x, y] = (*g[1], 255)
    for (y, s) in leaves:
        for j in (1, 2):
            p[x + s * j, y - (j - 1)] = (*g[2 if s < 0 else 0], 255)
        p[x + s * 3, y - 2] = (*g[1], 255)
    return img


BLOSSOMS = {
    "rose": ["..aa...", ".abba..", "abbcba.", "abcdcba", ".abbba.", "..aaa.."],
    "tulip": [".a.a.a.", ".ababa.", ".abcba.", ".abcba.", "..aba.."],
    "daisy": ["...b...", ".b.b.b.", "..bcb..", "bbcdcbb", "..bcb..", ".b.b.b.", "...b..."],
    "puff": [".aba.", "abcba", "bcdcb", "abcba", ".aba."],
    "orchid": ["a...a", ".bcb.", ".cdc.", ".bcb.", "a...a"],
    "ball": [".bcb.", "bcccb", "bcdcb", "abcba", ".aba."],
}


def blossom(kind, color, center=None):
    r = ramp(color, (-0.45, -0.1, 0.25, 0.0))
    cols = {"a": r[0], "b": r[1], "c": r[2], "d": center or shade(color, -0.6)}
    return sprite(BLOSSOMS[kind], cols)


def flower(kind, color, center=None, height=6, leaf=(70, 140, 50)):
    img = stem_and_leaves(new(), height, leaf)
    b = blossom(kind, color, center)
    bw, bh = b.size
    img.alpha_composite(b, (7 - bw // 2, max(0, height - bh + 1)))
    return img


def houstonia():
    img = new()
    p = img.load()
    g = ramp((80, 150, 60), (-0.4, 0.0))
    for (x, top) in ((4, 8), (8, 5), (11, 9)):
        for y in range(top, 16):
            p[x, y] = (*g[1], 255)
        for dx, dy, c in ((0, -1, (236, 240, 250)), (-1, 0, (210, 220, 240)), (1, 0, (210, 220, 240)),
                          (0, 0, (240, 214, 70)), (0, 1, (190, 200, 230))):
            p[x + dx, top + dy] = (*c, 255)
    return img


def sapling(kind):
    img = new()
    p = img.load()
    bark = ramp(WOODS[SAPLING_BARK[kind]][1], (-0.3, 0.0, 0.3))
    for y in range(9, 16):
        p[7, y] = (*bark[1], 255)
        p[8, y] = (*bark[0], 255)
    p[6, 12] = (*bark[1], 255)
    p[9, 11] = (*bark[0], 255)
    crown = [
        ".....aaaa.....",
        "...aabbbbaa...",
        "..abbbccbbba..",
        ".abbccddccbba.",
        ".abccddddccba.",
        "abbccddccbbbba",
        ".abbbccbbbbba.",
        "..aabbbbbbaa..",
        "....aaaaaa....",
    ]
    if kind == "spruce":
        crown = ["......aa......", ".....abba.....", "....abccba....", "...abbccbba...", "....abccba....",
                 "..abbccccbba..", ".abbccddccbba.", "..aabbbbbbaa..", "....aaaaaa...."]
    l = ramp(LEAF[kind], (-0.45, -0.15, 0.1, 0.35))
    img.alpha_composite(sprite(crown, {"a": l[0], "b": l[1], "c": l[2], "d": l[3]}), (1, 1))
    return img


def mushroom(cap, spots=False):
    c = ramp(cap, (-0.45, -0.1, 0.2, 0.45))
    stem = ramp((226, 214, 196), (-0.3, 0.0, 0.2))
    img = sprite([
        "................",
        "................",
        "................",
        "................",
        "................",
        "......cccc......",
        "....cbbddbbc....",
        "...cbbbbbbbbc...",
        "...abbbbbbbba...",
        "....aaaaaaaa....",
        "......sSSs......",
        "......sSSs......",
        "......sSSs......",
        "......sSSs......",
        "................",
        "................",
    ], {"a": c[0], "b": c[1], "c": c[2], "d": c[3], "s": stem[0], "S": stem[1]})
    if spots:
        p = img.load()
        for (x, y) in [(5, 7), (9, 6), (10, 8), (7, 8)]:
            p[x, y] = (240, 236, 230, 255)
    return img


def reeds():
    img = new()
    p = img.load()
    for x0 in (3, 8, 12):
        for y in range(16):
            v = 2 if (y + x0) % 6 else 0
            p[x0, y] = (*GRAY_PLANT[v + 1 if v < 3 else 3], 255)
            p[x0 + 1, y] = (*GRAY_PLANT[v], 255)
        lx = x0 - 1 if x0 > 4 else x0 + 2
        for y in ((x0 * 3) % 7 + 3, (x0 * 5) % 7 + 9):
            p[lx, y] = (*GRAY_PLANT[2], 255)
            p[lx + (1 if lx > x0 else -1), y - 1] = (*GRAY_PLANT[3], 255)
    return img


def vine():
    img = new()
    p = img.load()
    rng = random.Random(12)
    for x0 in (2, 7, 12):
        x = x0
        for y in range(16):
            x = max(0, min(15, x + rng.choice((-1, 0, 0, 1))))
            p[x, y] = (*GRAY_PLANT[0], 255)
            if y % 3 == 0:
                for dx, dy, v in ((1, 0, 2), (2, 0, 3), (1, 1, 1), (-1, 0, 2), (-2, 1, 1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 16 and 0 <= yy < 16:
                        p[xx, yy] = (*GRAY_PLANT[v], 255)
    return img


def waterlily():
    img = new()
    p = img.load()
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            if r < 7.2 and not (-0.35 < ang < 0.35 and r > 1.5):
                v = 1 if r > 6.2 else 3 if (abs(dx) < 0.6 or abs(dy) < 0.6 or abs(abs(dx) - abs(dy)) < 0.6) and r > 2 else 2
                p[x, y] = (*GRAY_PLANT[v], 255)
    return img


def web():
    img = new()
    p = img.load()
    w = (230, 232, 238, 230)
    for k in range(16):
        p[k, k] = w
        p[15 - k, k] = w
        p[7, k] = w if k % 2 == 0 else p[7, k]
        p[k, 8] = w if k % 2 == 1 else p[k, 8]
    for r in (3, 6):
        for a in range(48):
            t = a / 48 * 2 * math.pi
            x, y = round(7.5 + r * math.cos(t) * 1.05), round(7.5 + r * math.sin(t))
            p[x, y] = w
    return img


def crop_wheat(stage):
    ripe = stage / 7
    base = mix((74, 160, 52), (214, 178, 74), ripe ** 1.6)
    pal = ramp(base, (-0.45, -0.15, 0.1, 0.3))
    img = blades(40 + stage, 7, 2 + stage * 1.6, 3 + stage * 1.8, pal, spread=(1, 15), lean=0.12)
    if stage >= 5:
        p = img.load()
        g = ramp(mix((196, 170, 70), (226, 186, 80), ripe), (-0.4, 0.0, 0.35))
        for x in range(16):
            col = [y for y in range(16) if p[x, y][3]]
            if col and len(col) > 6:
                y = col[0]
                for k in range(3 if stage == 7 else 2):
                    if y + k < 16:
                        p[x, y + k] = (*g[(k + x) % 3], 255)
    return img


def crop_tuber(stage, top):
    """Carrots / potatoes: leafy tufts that grow; the last stage shows the crop at the soil line."""
    leaf = (70, 150, 52) if top != (226, 120, 30) else (86, 160, 50)
    img = blades(60 + stage, 6, 2 + stage * 2.2, 3 + stage * 2.6, ramp(leaf, (-0.45, -0.15, 0.1, 0.3)),
                 spread=(2, 14), lean=0.4)
    if stage == 3:
        p = img.load()
        t = ramp(top, (-0.35, 0.0, 0.3))
        for x0 in (3, 8, 12):
            for dx in (0, 1):
                p[x0 + dx, 14] = (*t[1 + dx], 255)
                p[x0 + dx, 15] = (*t[0], 255)
    return img


def nether_wart(stage):
    img = new()
    p = img.load()
    c = ramp((160, 36, 44), (-0.45, -0.1, 0.25))
    hgt = [5, 8, 12][stage]
    for x0 in (3, 7, 11):
        for k in range(hgt - (x0 % 3)):
            p[x0, 15 - k] = (*c[1], 255)
            if k == hgt - (x0 % 3) - 1:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (1, -1)):
                    p[x0 + dx, 15 - k + dy] = (*c[2 if dy else 0], 255)
                if stage == 2:
                    p[x0 + 1, 15 - k + 1] = (*c[2], 255)
    return img


def stem(connected=False):
    img = new()
    p = img.load()
    if not connected:
        for y in range(4, 16):
            p[7, y] = (*GRAY_PLANT[2 if y % 3 else 3], 255)
            p[8, y] = (*GRAY_PLANT[1], 255)
        for (x, y) in [(5, 9), (6, 9), (9, 6), (10, 6), (5, 13), (10, 12)]:
            p[x, y] = (*GRAY_PLANT[2], 255)
        return img
    for y in range(9, 16):
        p[7, y] = (*GRAY_PLANT[2], 255)
        p[8, y] = (*GRAY_PLANT[1], 255)
    line(p, (7, 9), (0, 6), GRAY_PLANT[2], 16, 16)
    line(p, (8, 9), (1, 7), GRAY_PLANT[1], 16, 16)
    for (x, y) in [(4, 8), (3, 9), (6, 11)]:
        p[x, y] = (*GRAY_PLANT[3], 255)
    return img


def cocoa(stage):
    mask = layout_mask(f"blocks/cocoa_stage_{stage}.png")
    pod = mix((110, 150, 40), (150, 80, 40), stage / 2)
    img = paint(soft_noise(70 + stage, (0.3, 0.4, 0.3)), ramp(pod, (-0.3, 0.0, 0.25)))
    p = img.load()
    for y in range(16):
        for x in range(16):
            if (x + y * 2) % 4 == 0:
                p[x, y] = (*shade(pod, -0.35), 255)
    for y in range(0, 4):           # stem in the top-right corner
        for x in range(12, 16):
            p[x, y] = (*ramp((100, 130, 40), (-0.2, 0.2))[(x + y) % 2], 255)
    return clip(img, mask)


# ---------------------------------------------------------------- double plants
def double_bottom(leaf=(70, 140, 50), gray=False):
    pal = GRAY_PLANT if gray else ramp(leaf, (-0.45, -0.15, 0.1, 0.3))
    img = blades(91, 9, 12, 16, pal, spread=(1, 15), lean=0.25)
    return img


def double_top(kind):
    if kind == "grass":
        return blades(93, 8, 6, 12, GRAY_PLANT, spread=(2, 14), lean=0.35)
    if kind == "fern":
        return fern(9, tall=True, top=True)
    img = new()
    if kind == "sunflower":
        return stem_and_leaves(new(), 0, leaves=((7, 1),))
    stems = blades(95, 5, 4, 9, ramp((70, 140, 50), (-0.4, -0.1, 0.2)), spread=(3, 13), lean=0.3)
    img.alpha_composite(stems)
    spec = {"rose": ("rose", (206, 36, 40)), "syringa": ("ball", (180, 120, 210)), "paeonia": ("ball", (232, 150, 190))}
    k, col = spec[kind]
    for (x, y) in ((1, 4), (8, 2), (5, 8)) if kind != "rose" else ((0, 5), (8, 3)):
        img.alpha_composite(blossom(k, col), (x, y))
    return img


def sunflower_face(back=False):
    img = new()
    p = img.load()
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5)
            if back:
                if r < 4.6:
                    p[x, y] = (*ramp((80, 150, 50), (-0.3, 0.0, 0.2))[int(r) % 3], 255)
            elif r < 2.4:
                p[x, y] = (96, 56, 28, 255) if (x + y) % 2 else (122, 74, 36, 255)
            elif r < 4.6:
                ang = math.atan2(y - 7.5, x - 7.5)
                p[x, y] = (*((250, 214, 50) if math.sin(ang * 8) > -0.3 else (230, 170, 30)), 255)
    return img


# ---------------------------------------------------------------- doors / trapdoors
def door(wood=None, upper=False):
    """One shape for all 7 doors: frame + two panels; the upper half has a 2-pane window."""
    if wood is None:
        r = ramp(IRON, (-0.55, -0.25, 0.0, 0.25, 0.5))
    else:
        r = ramp(WOODS[wood][0], (-0.6, -0.25, 0.0, 0.2, 0.42))
    idx = grid(fill=2)
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or (y == 0 and upper) or (y == 15 and not upper):
                idx[y][x] = 0
            elif x in (1, 14):
                idx[y][x] = 1 if x == 14 else 3
            elif (y in (2, 13)) and 3 <= x <= 12:
                idx[y][x] = 3 if y == 2 else 1
            elif x in (3, 12) and 2 <= y <= 13:
                idx[y][x] = 3 if x == 3 else 1
            elif (x - (y // 3) * 3) % 5 == 0 and wood is not None:
                idx[y][x] = 1          # faint grain lines in the panel
            if wood is None and (x + y * 3) % 7 == 0 and 4 <= x <= 11:
                idx[y][x] = 3
    img = paint(idx, r)
    p = img.load()
    if upper:
        glass = [(140, 190, 230, 255), (190, 222, 246, 255)]
        for y in range(4, 11):
            for x in range(4, 12):
                if x in (7, 8) or y == 7:
                    p[x, y] = (*r[1], 255)
                else:
                    p[x, y] = glass[1] if x + y in (9, 10, 17) else glass[0]
    else:
        for (x, y), c in (((12, 1), r[4]), ((12, 0), r[1])) if False else ():
            p[x, y] = (*c, 255)
        handle = (60, 60, 66) if wood else (40, 40, 48)
        for y in (6, 7):
            p[12, y] = (*handle, 255)
            p[13, y] = (*handle, 255)
    return img


def trapdoor(iron=False):
    r = ramp(IRON if iron else WOODS["oak"][0], (-0.6, -0.25, 0.0, 0.2, 0.42))
    img = paint(bevel(grid(fill=2), 3, 0), r)
    p = img.load()
    holes = [(3, 3), (9, 3), (3, 9), (9, 9)]
    for hx, hy in holes:
        for y in range(hy, hy + 4):
            for x in range(hx, hx + 4):
                if x in (hx, hx + 3) or y in (hy, hy + 3):
                    p[x, y] = (*r[1], 255)
                else:
                    p[x, y] = (0, 0, 0, 0)
    if not iron:
        for y in range(16):
            for x in (1, 14):
                p[x, y] = (*r[1 if x == 14 else 3], 255)
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        p[x, y] = (*mix(r[0], (40, 40, 48), 0.5), 255)
    return img


# ---------------------------------------------------------------- rails / redstone
def rail(kind="normal", powered=False, turned=False):
    rail_c = {"normal": IRON, "golden": GOLD, "detector": IRON, "activator": IRON}[kind]
    r = ramp(rail_c, (-0.55, -0.2, 0.1, 0.4))
    tie = ramp(WOODS["spruce"][0], (-0.4, -0.1, 0.15))
    img = new()
    p = img.load()
    if turned:
        cx, cy = 16.5, 16.5
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                ang = math.atan2(cy - y - 0.5, cx - x - 0.5)
                if any(abs(d - rr) < 0.8 for rr in (3.6, 8.8, 14)) and False:
                    pass
                # ties: radial planks
                if 1.5 < d < 15.5 and (abs(math.sin(ang * 6)) < 0.32):
                    p[x, y] = (*tie[1 if (x + y) % 2 else 2], 255)
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if 3.2 <= d < 4.6 or 12.2 <= d < 13.6:
                    p[x, y] = (*r[2 if d < 4 or d < 13 else 1], 255)
        return img
    for y in range(16):
        if y % 4 in (1, 2):
            for x in range(1, 15):
                p[x, y] = (*tie[2 if y % 4 == 1 else 1], 255)
        for x in (2, 3, 12, 13):
            p[x, y] = (*r[2 if x in (2, 12) else 1], 255)
    if kind != "normal":
        mid = {"golden": REDSTONE if powered else (100, 30, 30), "detector": (150, 154, 160),
               "activator": REDSTONE if powered else (100, 30, 30)}[kind]
        for y in range(16):
            for x in (7, 8):
                if kind == "detector":
                    if 5 <= y <= 10:
                        p[x - 2 if x == 7 else x + 2, y] = (*shade(mid, -0.2), 255)
                        p[x, y] = (*(REDSTONE if powered else shade(mid, 0.3)), 255)
                elif y % 4 not in (1, 2) or kind == "activator":
                    p[x, y] = (*(shade(mid, 0.35) if x == 7 else mid), 255)
        if kind == "activator":
            for y in range(16):
                if y % 4 in (1, 2):
                    for x in range(4, 12):
                        if x not in (7, 8):
                            p[x, y] = (*ramp(IRON_DARK, (0.0, 0.3))[y % 4 == 1], 255)
    return img


def redstone_dust(cross=False):
    """Grayscale (the game tints by signal strength). A 4px band with a ragged edge."""
    img = new()
    p = img.load()
    for x in range(16):
        for y in range(6, 10):
            if y in (6, 9) and (x * 5) % 3 == 0:
                continue
            p[x, y] = (*((236,) * 3 if y in (7, 8) else (180,) * 3), 255)
        if cross:
            pass
    if cross:
        for y in range(16):
            for x in range(6, 10):
                if x in (6, 9) and (y * 5) % 3 == 0:
                    continue
                if p[x, y][3] == 0 or x in (7, 8):
                    p[x, y] = (*((236,) * 3 if x in (7, 8) else (180,) * 3), 255)
    return img


def torch(flame, stickc=None, lit=True):
    img = new()
    p = img.load()
    s = ramp(stickc or WOODS["oak"][0], (-0.35, 0.0, 0.25))
    for y in range(8, 16):
        p[7, y] = (*s[2], 255)
        p[8, y] = (*s[1], 255)
    f = ramp(flame, (-0.3, 0.0, 0.45))
    p[7, 6] = (*f[2], 255)
    p[8, 6] = (*f[1], 255)
    p[7, 7] = (*f[1], 255)
    p[8, 7] = (*f[0], 255)
    if not lit:
        for (x, y) in ((7, 6), (8, 6), (7, 7), (8, 7)):
            p[x, y] = (*shade(flame, -0.5 if (x + y) % 2 else -0.3), 255)
    return img


def lever():
    img = new()
    p = img.load()
    s = ramp(WOODS["oak"][0], (-0.35, 0.0, 0.25))
    for y in range(8, 16):
        p[7, y] = (*s[2], 255)
        p[8, y] = (*s[1], 255)
    for (x, y), c in (((7, 6), (190, 190, 196)), ((8, 6), (150, 150, 158)), ((7, 7), (150, 150, 158)),
                      ((8, 7), (110, 110, 118))):
        p[x, y] = (*c, 255)
    return img


def tripwire_source():
    img = new()
    p = img.load()
    r = ramp(IRON, (-0.5, -0.2, 0.2))
    for y in range(3, 9):
        for x in range(5, 11):
            ring = x in (5, 6, 9, 10) or y in (3, 4, 7, 8)
            if ring:
                p[x, y] = (*r[2 if (x < 7 or y < 5) else 1], 255)
    s = ramp(WOODS["oak"][0], (-0.35, 0.0, 0.25))
    for y in range(9, 16):
        p[7, y] = (*s[2], 255)
        p[8, y] = (*s[1], 255)
    return img


def tripwire():
    img = new()
    p = img.load()
    for y in (1, 5):
        for x in range(16):
            if (x + y) % 4 != 3:
                p[x, y] = (226, 226, 232, 255)
            else:
                p[x, y] = (180, 180, 190, 255)
    return img


def slab_device(lit, kind):
    """Repeater / comparator: smooth stone slab top, redstone track, torches. Bottom 2 rows = the slab side."""
    img = smooth_stone(seed=14)
    p = img.load()
    red = REDSTONE if lit else (110, 30, 30)
    for y in range(3, 13):
        p[7, y] = (*red, 255)
        p[8, y] = (*shade(red, -0.3), 255)
    torches = [(7, 2), (7, 11)] if kind == "repeater" else [(3, 3), (11, 3), (7, 11)]
    for (x, y) in torches:
        for dx in (0, 1):
            for dy in (0, 1):
                p[x + dx, y + dy] = (*(shade(red, 0.4) if dy == 0 else red), 255)
    if kind == "repeater":
        for x in range(4, 12):
            p[x, 7] = (*ramp(STONE, (-0.5,))[0], 255)
    for x in range(16):
        p[x, 14] = (*shade(STONE, 0.15), 255)
        p[x, 15] = (*shade(STONE, -0.45), 255)
    return img


def daylight(inverted=False):
    w = ramp(WOODS["oak"][0], (-0.55, -0.2, 0.05))
    img = new()
    p = img.load()
    glass = (52, 60, 90) if not inverted else (90, 60, 52)
    cell = (170, 200, 230) if not inverted else (200, 120, 90)
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15) or x % 5 == 0 or y % 5 == 0:
                p[x, y] = (*w[1 if (x + y) % 2 else 2], 255)
            else:
                p[x, y] = (*(cell if (x % 5, y % 5) in ((1, 1), (2, 1), (1, 2)) else glass), 255)
    side = planks("oak")
    return img, side


def redstone_lamp(lit):
    base = (240, 196, 110) if lit else (110, 70, 50)
    img = paint(cobble_pattern(seed=44, count=9), ramp(base, (-0.5, -0.2, 0.0, 0.25, 0.5)))
    return framed(img, shade(base, -0.55))


# ---------------------------------------------------------------- utility blocks
def piston():
    s = ramp(STONE, (-0.55, -0.25, -0.05, 0.15, 0.35))
    stone_side = paint(cobble_pattern(seed=51), s)
    wood = planks("oak")
    iron = ramp(IRON, (-0.5, -0.2, 0.1, 0.35))
    side = stone_side.copy()
    sp = side.load()
    wp = wood.load()
    for y in range(4):
        for x in range(16):
            sp[x, y] = wp[x, y + 4]
    for x in range(16):
        sp[x, 4] = (*s[0], 255)
    for y in range(5, 16):
        for x in (7, 8):
            sp[x, y] = (*iron[1 if x == 8 else 2], 255)
    top = wood.copy()
    tp = top.load()
    for y in range(5, 11):
        for x in range(5, 11):
            tp[x, y] = (*iron[2 if (x in (5, 10) or y in (5, 10)) else 3], 255)
    framed(top, s[1])
    sticky = top.copy()
    kp = sticky.load()
    for y in range(3, 13):
        for x in range(3, 13):
            if (x - 7.5) ** 2 + (y - 7.5) ** 2 < 22:
                kp[x, y] = (*ramp((110, 200, 90), (-0.25, 0.0, 0.3))[(x * 3 + y) % 3], 255)
    inner = stone_side.copy()
    ip = inner.load()
    for y in range(5, 11):
        for x in range(5, 11):
            ip[x, y] = (*iron[2], 255)
    bottom = stone_side.copy()
    return {"piston_side": side, "piston_top_normal": top, "piston_top_sticky": sticky, "piston_inner": inner,
            "piston_bottom": bottom}


def dispenser_fronts():
    s = ramp(STONE, (-0.55, -0.25, -0.05, 0.15, 0.35))
    base = paint(brick_pattern(8, 8, seed=13), s)
    out = {}
    for name, mouth in (("dispenser", "round"), ("dropper", "slot")):
        for orient in ("horizontal", "vertical"):
            img = base.copy()
            p = img.load()
            for y in range(16):
                for x in range(16):
                    if orient == "vertical":
                        hole = math.hypot(x - 7.5, y - 7.5) < (3.5 if mouth == "round" else 4.6)
                        rim = math.hypot(x - 7.5, y - 7.5) < (4.6 if mouth == "round" else 5.6)
                    elif mouth == "round":
                        hole = math.hypot(x - 7.5, y - 7.5) < 3.2
                        rim = math.hypot(x - 7.5, y - 7.5) < 4.4
                    else:
                        hole = 4 <= x <= 11 and 6 <= y <= 9
                        rim = 3 <= x <= 12 and 5 <= y <= 10
                    if hole:
                        p[x, y] = (22, 22, 28, 255)
                    elif rim:
                        p[x, y] = (*s[4 if y < 8 else 0], 255)
            out[f"{name}_front_{orient}"] = img
    return out


def hopper():
    r = ramp(IRON_DARK, (-0.5, -0.2, 0.0, 0.25, 0.5))
    outside = paint(bevel(soft_noise(81, (0.3, 0.4, 0.3), base=1), 4, 0), r)
    p = outside.load()
    for x in range(16):
        p[x, 5] = (*r[0], 255)
        p[x, 6] = (*r[3], 255)
    top = outside.copy()
    tp = top.load()
    m = layout_mask("blocks/hopper_top.png")
    for y in range(16):
        for x in range(16):
            if not m[y][x]:
                tp[x, y] = (0, 0, 0, 0)
            elif x in (2, 13) or y in (2, 13):
                tp[x, y] = (*r[1], 255)
    inside = paint(soft_noise(82, (0.3, 0.4, 0.3)), [r[0], r[1], mix(r[0], r[1], 0.5)])
    return outside, top, inside


def cauldron():
    r = ramp(IRON_DARK, (-0.5, -0.2, 0.0, 0.25, 0.5))
    side = paint(bevel(soft_noise(83, (0.3, 0.4, 0.3), base=1), 4, 0), r)
    sp = side.load()
    for x in range(16):
        sp[x, 2] = (*r[3], 255)
        sp[x, 3] = (*r[0], 255)
    for y in (14, 15):
        for x in range(6, 11 if y == 15 else 10):
            sp[x, y] = (0, 0, 0, 0)
    top = side.copy()
    clip(top, layout_mask("blocks/cauldron_top.png"))
    tp = top.load()
    for i in range(3, 13):
        for (x, y) in ((i, 2), (2, i)):
            tp[x, y] = (*r[1], 255)
    inner = paint(soft_noise(84, (0.3, 0.4, 0.3)), [r[0], r[1], mix(r[0], r[1], 0.5)])
    bottom = paint(soft_noise(85, (0.3, 0.4, 0.3)), [r[0], r[1], r[2]])
    return side, top, inner, bottom


def anvil():
    r = ramp(IRON_DARK, (-0.5, -0.2, 0.0, 0.25, 0.5))
    base = paint(bevel(soft_noise(86, (0.3, 0.4, 0.3), base=1), 4, 0), r)
    tops = []
    m = layout_mask("blocks/anvil_top_damaged_0.png")
    cracks = [[], [(5, 3), (6, 4), (6, 5), (7, 6), (10, 11), (9, 12)],
              [(5, 3), (6, 4), (6, 5), (7, 6), (8, 7), (8, 8), (10, 11), (9, 12), (9, 13), (11, 2), (12, 3), (4, 10),
               (5, 11)]]
    for k in range(3):
        img = paint(soft_noise(87, (0.3, 0.4, 0.3), base=1), r)
        p = img.load()
        for y in range(16):
            for x in range(16):
                if x in (3, 12):
                    p[x, y] = (*r[0 if x == 12 else 3], 255)
        for (x, y) in cracks[k]:
            p[x, y] = (20, 20, 26, 255)
            if x + 1 < 16:
                p[x + 1, y] = (*r[3], 255)
        tops.append(clip(img, m))
    return base, tops


def enchanting_table():
    obs = [(18, 14, 28), (30, 22, 46), (52, 36, 80), (92, 64, 140)]
    cloth = ramp((176, 36, 52), (-0.45, -0.15, 0.1, 0.35))
    top = paint(soft_noise(101, (0.3, 0.4, 0.3), base=1), cloth)
    tp = top.load()
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                tp[x, y] = (*obs[1], 255)
            elif (x + y) in (7, 23) or (x - y) in (8, -8):
                tp[x, y] = (230, 196, 70, 255)
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        tp[x, y] = (78, 228, 218, 255)
    side = paint(soft_noise(102, (0.35, 0.35, 0.2, 0.1), cells=(4, 2), weights=(0.6, 0.4)), obs)
    sp = side.load()
    for x in range(16):
        sp[x, 4] = (*cloth[3], 255)
        sp[x, 5] = (*cloth[1], 255)
        sp[x, 6] = (*cloth[0], 255) if x % 4 else (230, 196, 70, 255)
    clip(side, layout_mask("blocks/enchanting_table_side.png"))
    bottom = paint(soft_noise(103, (0.35, 0.35, 0.2, 0.1)), obs)
    return top, side, bottom


def brewing_stand():
    img = new()
    p = img.load()
    rod = ramp((190, 170, 120), (-0.4, 0.0, 0.3))
    for y in range(1, 16):
        p[7, y] = (*rod[2], 255)
        p[8, y] = (*rod[1], 255)
    for (a, b) in (((1, 11), (6, 6)), ((14, 11), (9, 6)), ((1, 12), (6, 7))):
        line(p, a, b, rod[1], 16, 16)
    for (x, y) in ((7, 0), (8, 0)):
        p[x, y] = (226, 196, 90, 255)
    base = paint(soft_noise(104, (0.3, 0.4, 0.3)), ramp(STONE, (-0.35, -0.1, 0.1)))
    framed(base, shade(STONE, -0.5))
    return img, base


def endframe():
    end = ramp((222, 222, 162), (-0.4, -0.15, 0.0, 0.15))
    teal = ramp((44, 120, 110), (-0.5, -0.2, 0.0, 0.3))
    top = paint(soft_noise(105, (0.3, 0.4, 0.3)), [end[1], end[2], end[3]])
    tp = top.load()
    for y in range(3, 13):
        for x in range(3, 13):
            ring = x in (3, 12) or y in (3, 12)
            tp[x, y] = (*(teal[0] if ring else teal[1 + ((x + y) % 3 == 0)]), 255)
    side = paint(soft_noise(106, (0.3, 0.4, 0.3)), [end[0], end[1], end[2]])
    sp = side.load()
    for x in range(16):
        sp[x, 3] = (*teal[2], 255)
        sp[x, 4] = (*teal[0], 255)
    clip(side, layout_mask("blocks/endframe_side.png"))
    eye = new()
    ep = eye.load()
    for y in range(4, 12):
        for x in range(4, 12):
            r = math.hypot(x - 7.5, y - 7.5)
            if r < 3.8:
                ep[x, y] = (*((20, 40, 30) if r < 1.3 else (60, 190, 130) if r < 2.6 else (30, 110, 80)), 255)
    return top, side, eye


def flower_pot():
    c = ramp((160, 82, 56), (-0.45, -0.15, 0.1, 0.3))
    img = new()
    p = img.load()
    m = layout_mask("blocks/flower_pot.png")
    for y in range(16):
        for x in range(16):
            if m[y][x]:
                p[x, y] = (*c[3 if y == 5 else 0 if x == 10 else 1 if x == 9 else 2], 255)
    return img


def cactus():
    g = ramp((70, 140, 60), (-0.5, -0.2, 0.0, 0.25))
    side = new()
    p = side.load()
    m = layout_mask("blocks/cactus_side.png")
    for y in range(16):
        for x in range(16):
            if not m[y][x]:
                continue
            v = 2 if x % 4 != 1 else 1
            if x in (1, 14):
                v = 0
            p[x, y] = (*g[v], 255)
            if m[y][x] and (x in (0, 15)):
                p[x, y] = (232, 226, 190, 255)   # spines poke out of the sides
    for (x, y) in ((4, 3), (8, 9), (12, 5), (4, 12), (10, 14)):
        p[x, y] = (232, 226, 190, 255)
    top = new()
    tp = top.load()
    for y in range(1, 15):
        for x in range(1, 15):
            v = 3 if (x, y) in ((7, 7), (8, 8), (7, 8), (8, 7)) else 2 if (x + y) % 4 else 1
            tp[x, y] = (*(g[0] if x in (1, 14) or y in (1, 14) else g[v]), 255)
    bottom = top.copy()
    return side, top, bottom


def cake():
    sponge = ramp((196, 120, 64), (-0.35, -0.1, 0.15))
    icing = ramp((246, 240, 236), (-0.12, 0.0, 0.1))
    top = new()
    tp = top.load()
    for y in range(1, 15):
        for x in range(1, 15):
            tp[x, y] = (*icing[1 if (x * 3 + y) % 7 else 0], 255)
    for (x, y) in ((4, 4), (10, 5), (7, 9), (11, 11), (3, 11)):
        tp[x, y] = (210, 40, 50, 255)
    side = new()
    sp = side.load()
    for y in range(8, 16):
        for x in range(1, 15):
            sp[x, y] = (*(icing[1] if y < 10 or (y == 10 and x % 3) else sponge[1 if (x + y) % 5 else 0]), 255)
    inner = side.copy()
    ip = inner.load()
    for y in range(10, 16):
        for x in range(1, 15):
            ip[x, y] = (*sponge[2 if (x * 7 + y * 3) % 5 else 0], 255)
    bottom = new()
    bp = bottom.load()
    for y in range(1, 15):
        for x in range(1, 15):
            bp[x, y] = (*sponge[0 if (x + y) % 3 else 1], 255)
    return top, side, inner, bottom


def pumpkin_family():
    o = ramp((222, 126, 30), (-0.5, -0.2, 0.0, 0.25))
    side = new()
    p = side.load()
    for y in range(16):
        for x in range(16):
            v = 2 if x % 4 not in (0, 3) else 1 if x % 4 == 3 else 3
            if y in (0, 15):
                v = 0
            p[x, y] = (*o[v], 255)
    top = side.copy()
    tp = top.load()
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5)
            ang = math.atan2(y - 7.5, x - 7.5)
            tp[x, y] = (*o[3 if r < 2 else 1 if abs(math.sin(ang * 4)) < 0.25 else 2], 255)
    for (x, y) in ((7, 7), (8, 7), (7, 8), (8, 8)):
        tp[x, y] = (96, 120, 40, 255)

    def face(lit):
        img = side.copy()
        fp = img.load()
        glow = (255, 220, 90) if lit else (40, 24, 12)
        glow2 = (250, 170, 40) if lit else (26, 16, 8)
        holes = ["................", "................", "................", "................",
                 "...##......##...", "..####....####..", "..####....####..", "................",
                 "................", "...##########...", "...#.##..##.#...", "....########....",
                 ".....#....#.....", "................", "................", "................"]
        for y, row in enumerate(holes):
            for x, ch in enumerate(row):
                if ch == "#":
                    fp[x, y] = (*(glow if y in (5, 10) else glow2), 255)
        return img

    return side, top, face(False), face(True)


def melon():
    g = ramp((96, 160, 40), (-0.5, -0.2, 0.0, 0.25))
    side = new()
    p = side.load()
    for y in range(16):
        for x in range(16):
            stripe = (x + (y // 4) % 2) % 4 == 0
            p[x, y] = (*(g[3] if stripe else g[1 + ((x * 7 + y) % 5 == 0)]), 255)
    top = new()
    tp = top.load()
    for y in range(16):
        for x in range(16):
            ang = math.atan2(y - 7.5, x - 7.5)
            r = math.hypot(x - 7.5, y - 7.5)
            tp[x, y] = (*(g[3] if abs(math.sin(ang * 4)) < 0.2 and r > 1.5 else g[2] if r < 2 else g[1]), 255)
    return side, top


def hay():
    y_ = ramp((206, 170, 52), (-0.5, -0.2, 0.0, 0.25))
    side = new()
    p = side.load()
    for y in range(16):
        for x in range(16):
            band = y in (3, 4, 11, 12)
            p[x, y] = (*((150, 60, 40) if band and y in (4, 12) else (176, 80, 50) if band else
                         y_[1 + (x * 5 + y) % 3]), 255)
    top = new()
    tp = top.load()
    for y in range(16):
        for x in range(16):
            tp[x, y] = (*y_[(x * 3 + y * 5) % 4], 255)
    framed(top, y_[0])
    return side, top


def mushroom_blocks():
    red = ramp((196, 44, 40), (-0.45, -0.15, 0.1, 0.3))
    brown = ramp((140, 104, 76), (-0.45, -0.15, 0.1, 0.3))
    pore = ramp((220, 196, 160), (-0.2, 0.0, 0.15))
    stem_c = ramp((222, 214, 200), (-0.25, -0.05, 0.1))
    skin_red = paint(soft_noise(111, (0.3, 0.4, 0.3), base=1), red)
    rp = skin_red.load()
    for (cx, cy) in ((4, 4), (11, 3), (8, 10), (2, 12), (13, 12)):
        for dx in (0, 1):
            for dy in (0, 1):
                rp[(cx + dx) % 16, (cy + dy) % 16] = (*((246, 242, 236) if dx + dy < 2 else (210, 206, 200)), 255)
    skin_brown = paint(soft_noise(112, (0.3, 0.4, 0.3), base=1), brown)
    stem_img = paint([[1 + (x % 3 == 0) for x in range(16)] for y in range(16)], stem_c)
    inside = paint(soft_noise(113, (0.3, 0.4, 0.3)), pore)
    ip = inside.load()
    for y in range(16):
        for x in range(16):
            if (x + y * 3) % 5 == 0:
                ip[x, y] = (*shade(pore[0], -0.2), 255)
    return skin_red, skin_brown, stem_img, inside


def jukebox_noteblock():
    side = planks("big_oak")
    sp = side.load()
    w = ramp(WOODS["big_oak"][0], (-0.55, -0.2, 0.0, 0.25))
    framed(side, w[0], w[3])
    top = side.copy()
    tp = top.load()
    for y in range(4, 12):
        for x in range(2, 14):
            tp[x, y] = (*((22, 22, 28) if y in (7, 8) else w[0]), 255)
    note = planks("oak")
    framed(note, ramp(WOODS["oak"][0], (-0.6,))[0])
    np_ = note.load()
    for (x, y) in [(9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8), (8, 9), (7, 9), (6, 9), (6, 10), (7, 10), (8, 10),
                   (10, 4), (11, 5)]:
        np_[x, y] = (30, 26, 40, 255)
    return side, top, note


def mob_spawner():
    img = new()
    p = img.load()
    r = ramp((60, 70, 90), (-0.5, -0.2, 0.1, 0.4))
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                p[x, y] = (*r[1], 255)
            elif x % 5 == 0 or y % 5 == 0:
                p[x, y] = (*r[2 if (x + y) % 2 else 3], 255)
    return img


def command_block():
    r = ramp((196, 132, 90), (-0.5, -0.2, 0.0, 0.25))
    img = paint(bevel(grid(fill=2), 3, 0), r)
    p = img.load()
    for y in range(4, 12):
        for x in range(4, 12):
            p[x, y] = (*((24, 28, 36) if not (x in (4, 11) or y in (4, 11)) else r[0]), 255)
    for (x, y) in ((5, 6), (6, 7), (5, 8), (7, 9), (8, 9), (9, 9)):
        p[x, y] = (110, 230, 140, 255)
    return img


def iron_bars():
    img = new()
    p = img.load()
    r = ramp(IRON, (-0.5, -0.2, 0.1))
    for x in (1, 5, 9, 13):
        for y in range(16):
            p[x, y] = (*r[2], 255)
            p[x + 1, y] = (*r[1], 255)
    for y in (0, 15):
        for x in range(16):
            p[x, y] = (*r[1], 255)
    return img


def itemframe_bg():
    return paint(soft_noise(121, (0.3, 0.4, 0.3)), ramp((150, 112, 80), (-0.2, 0.0, 0.15)))


def beacon_core():
    img = new()
    p = img.load()
    for y in range(16):
        for x in range(16):
            r = max(abs(x - 7.5), abs(y - 7.5))
            c = (240, 255, 255) if r < 3 else (120, 230, 230) if r < 5 else (60, 180, 200)
            if r >= 6.5:
                c = (40, 120, 150)
            p[x, y] = (*c, 255)
    return img


def dragon_egg():
    img = paint(soft_noise(131, (0.35, 0.35, 0.2, 0.1), cells=(4, 2), weights=(0.6, 0.4)),
                [(14, 8, 22), (26, 14, 40), (44, 24, 70), (110, 60, 160)])
    p = img.load()
    for (x, y) in ((3, 4), (12, 2), (7, 10), (13, 13), (2, 13)):
        p[x, y] = (200, 120, 255, 255)
    return img


def sea_lantern():
    frames = []
    for f in range(5):
        img = new()
        p = img.load()
        for y in range(16):
            for x in range(16):
                q = (x // 8, y // 8)
                lx, ly = x % 8, y % 8
                if lx in (0, 7) or ly in (0, 7):
                    c = (150, 190, 200)
                else:
                    phase = (q[0] + q[1] * 2 + f) % 5
                    glow = 0.5 + 0.5 * math.cos(2 * math.pi * phase / 5)
                    c = mix((190, 230, 230), (250, 255, 255), glow)
                    if (lx + ly) in (3, 4) and lx < 4:
                        c = (255, 255, 255)
                p[x, y] = (*c, 255)
        frames.append(img)
    return frames


PRISMARINE = (90, 168, 150)


def prismarine_rough():
    frames = []
    shifts = [(90, 168, 150), (98, 156, 168), (84, 162, 134), (104, 170, 172)]
    pat = soft_noise(141, (0.2, 0.35, 0.3, 0.15), cells=(4, 2), weights=(0.6, 0.4))
    for c in shifts:
        frames.append(paint(pat, ramp(c, (-0.45, -0.15, 0.1, 0.3))))
    return frames


def prismarine_bricks():
    return paint(brick_pattern(8, 4, seed=142), ramp((110, 182, 162), (-0.6, -0.3, -0.05, 0.15, 0.35)))


def prismarine_dark():
    r = ramp((44, 86, 76), (-0.5, -0.2, 0.0, 0.25, 0.45))
    img = paint(bevel(grid(fill=2), 3, 0), r)
    p = img.load()
    for y in range(16):
        for x in range(16):
            if x in (5, 10) or y in (5, 10):
                p[x, y] = (*r[1], 255)
            elif (x % 5, y % 5) == (2, 2):
                p[x, y] = (*r[4], 255)
    return img


def slime_block():
    img = new()
    p = img.load()
    g = ramp((110, 200, 90), (-0.45, -0.15, 0.1, 0.35))
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            core = 4 <= x <= 11 and 4 <= y <= 11
            if edge:
                p[x, y] = (*g[1], 200)
            elif core:
                p[x, y] = (*g[2 if not (x in (4, 11) or y in (4, 11)) else 0], 230)
            else:
                p[x, y] = (*g[3], 150)
    for (x, y) in ((2, 2), (3, 2), (2, 3), (6, 5)):
        p[x, y] = (230, 255, 220, 220)
    return img


def sandstone_set(base):
    """Same patterns as blocks.py's sandstone, any color: normal, top, bottom, smooth, carved."""
    ss = paint([[(0 if y in (3, 12) else 3 if y in (0, 4, 13) else 2 if y < 3 or y > 12 else 1 + (x + y) % 2)
                 for x in range(16)] for y in range(16)], ramp(base, (-0.35, -0.12, 0.0, 0.18)))
    top = paint(soft_noise(93, (0.3, 0.4, 0.3)), ramp(base, (-0.1, 0.0, 0.12)))
    bottom = paint(soft_noise(94, (0.3, 0.4, 0.3)), ramp(base, (-0.2, -0.08, 0.05)))
    smooth = paint(bevel(grid(fill=1), 2, 0), ramp(base, (-0.35, 0.0, 0.18)))
    carved = smooth.copy()
    cs = carved.load()
    for i in range(4, 12):
        for (x, y) in ((i, 4), (i, 11), (4, i), (11, i)):
            cs[x, y] = (*shade(base, -0.35), 255)
        if 5 <= i <= 10:
            cs[i, i] = (*shade(base, -0.35), 255)
    return {"normal": ss, "top": top, "bottom": bottom, "smooth": smooth, "carved": carved}


def stone_variant(base, seed):
    rough = paint(soft_noise(seed, (0.15, 0.35, 0.35, 0.15), cells=(4, 2), weights=(0.6, 0.4)),
                  ramp(base, (-0.35, -0.12, 0.05, 0.22)))
    smooth = paint(bevel(soft_noise(seed + 1, (0.3, 0.4, 0.3), base=1), 4, 0), ramp(base, (-0.45, -0.12, 0.0, 0.12, 0.3)))
    return rough, smooth


def quartz_extras():
    q = ramp((232, 228, 222), (-0.35, -0.1, 0.0, 0.1, 0.25))
    lines = paint([[1 if x in (0, 15) else 4 if x in (1, 8) else 2 if x % 7 else 3 for x in range(16)] for y in range(16)], q)
    lines_top = paint(bevel(soft_noise(150, (0.3, 0.4, 0.3), base=1), 4, 0), q)
    ltp = lines_top.load()
    for y in range(3, 13):
        for x in range(3, 13):
            if x in (3, 12) or y in (3, 12):
                ltp[x, y] = (*q[1], 255)
    chis = paint(bevel(grid(fill=2), 4, 0), q)
    cp = chis.load()
    for y in range(16):
        for x in range(16):
            if y in (2, 13) and 1 <= x <= 14:
                cp[x, y] = (*q[1], 255)
            if 4 <= y <= 11 and x in (4, 11):
                cp[x, y] = (*q[1], 255)
            if 4 <= y <= 11 and 5 <= x <= 10 and (x + y) % 3 == 0:
                cp[x, y] = (*q[3], 255)
    chis_top = lines_top.copy()
    ctp = chis_top.load()
    for y in range(5, 11):
        for x in range(5, 11):
            if (x + y) % 2 == 0:
                ctp[x, y] = (*q[0], 255)
    return lines, lines_top, chis, chis_top


def farmland(wet):
    soil = (90, 60, 40) if wet else (134, 96, 66)
    r = ramp(soil, (-0.4, -0.15, 0.05, 0.25))
    idx = grid()
    for y in range(16):
        for x in range(16):
            idx[y][x] = 0 if y % 4 == 3 else 3 if y % 4 == 0 else 1 + (x * 7 + y) % 3 // 2
    return paint(idx, r)


def grassy_top(color, seed):
    return paint(soft_noise(seed, (0.2, 0.35, 0.3, 0.15), cells=(4, 2), weights=(0.6, 0.4)), ramp(color, (-0.3, -0.1, 0.05, 0.2)))


def topped_side(top_img, accent):
    img = dirt_tex()
    p = img.load()
    tp = top_img.load()
    for x, hgt in enumerate(grass_fringe()):
        for y in range(hgt):
            p[x, y] = tp[x, y]
        p[x, hgt] = (*shade(accent, -0.4), 255)
    return img


def soul_sand():
    img = paint(soft_noise(161, (0.25, 0.35, 0.25, 0.15), cells=(4, 2), weights=(0.6, 0.4)),
                ramp((90, 68, 54), (-0.45, -0.15, 0.05, 0.25)))
    p = img.load()
    for (cx, cy) in ((4, 4), (11, 9), (5, 12)):
        for (dx, dy) in ((0, 0), (2, 0), (1, 2), (0, 2), (2, 2)):
            if (dx, dy) != (1, 2) or True:
                p[(cx + dx) % 16, (cy + dy) % 16] = (40, 28, 22, 255)
    return img


def nether_brick():
    return paint(brick_pattern(8, 4, seed=171), ramp((70, 32, 38), (-0.6, -0.3, -0.05, 0.15, 0.35)))


# ---------------------------------------------------------------- generate
def generate():
    # --- grass-like / tinted plants (grayscale, biome-tinted in game)
    save(blades(21, 10, 7, 13, GRAY_PLANT), "blocks/tallgrass.png")
    save(fern(), "blocks/fern.png")
    save(deadbush(), "blocks/deadbush.png")
    save(reeds(), "blocks/reeds.png")
    save(vine(), "blocks/vine.png")
    save(waterlily(), "blocks/waterlily.png")
    save(double_bottom(gray=True), "blocks/double_plant_grass_bottom.png")
    save(double_top("grass"), "blocks/double_plant_grass_top.png")
    save(fern(7, tall=True), "blocks/double_plant_fern_bottom.png")
    save(double_top("fern"), "blocks/double_plant_fern_top.png")
    save(stem(), "blocks/melon_stem_disconnected.png")
    save(stem(True), "blocks/melon_stem_connected.png")
    save(stem(), "blocks/pumpkin_stem_disconnected.png")
    save(stem(True), "blocks/pumpkin_stem_connected.png")

    # --- flowers (one stem, blossom shapes recolored)
    save(flower("puff", (250, 214, 50), (230, 150, 30), height=7), "blocks/flower_dandelion.png")
    save(flower("rose", (210, 34, 40), (40, 20, 20), height=6), "blocks/flower_rose.png")
    save(flower("orchid", (60, 170, 230), (230, 240, 255), height=6), "blocks/flower_blue_orchid.png")
    save(flower("ball", (170, 100, 220), height=4), "blocks/flower_allium.png")
    save(houstonia(), "blocks/flower_houstonia.png")
    for name, c in (("red", (214, 44, 44)), ("orange", (240, 130, 40)), ("white", (236, 236, 240)),
                    ("pink", (240, 160, 200))):
        save(flower("tulip", c, height=6), f"blocks/flower_tulip_{name}.png")
    save(flower("daisy", (240, 242, 246), (240, 200, 50), height=6), "blocks/flower_oxeye_daisy.png")
    save(flower("ball", (232, 150, 190), height=5), "blocks/flower_paeonia.png")
    for kind in ("rose", "syringa", "paeonia"):
        save(double_bottom(), f"blocks/double_plant_{kind}_bottom.png")
        save(double_top(kind), f"blocks/double_plant_{kind}_top.png")
    save(double_bottom(), "blocks/double_plant_sunflower_bottom.png")
    save(double_top("sunflower"), "blocks/double_plant_sunflower_top.png")
    save(sunflower_face(), "blocks/double_plant_sunflower_front.png")
    save(sunflower_face(back=True), "blocks/double_plant_sunflower_back.png")
    for kind in LEAF:
        save(sapling(kind), f"blocks/sapling_{kind}.png")
    save(mushroom((150, 110, 80)), "blocks/mushroom_brown.png")
    save(mushroom((206, 40, 40), spots=True), "blocks/mushroom_red.png")

    # --- crops
    for s in range(8):
        save(crop_wheat(s), f"blocks/wheat_stage_{s}.png")
    for s in range(4):
        save(crop_tuber(s, (236, 128, 30)), f"blocks/carrots_stage_{s}.png")
        save(crop_tuber(s, (196, 160, 90)), f"blocks/potatoes_stage_{s}.png")
    for s in range(3):
        save(nether_wart(s), f"blocks/nether_wart_stage_{s}.png")
        save(cocoa(s), f"blocks/cocoa_stage_{s}.png")

    # --- doors and trapdoors (one shape, recolored)
    for wood, name in (("oak", "wood"), ("spruce", "spruce"), ("birch", "birch"), ("jungle", "jungle"),
                       ("acacia", "acacia"), ("big_oak", "dark_oak"), (None, "iron")):
        save(door(wood, upper=False), f"blocks/door_{name}_lower.png")
        save(door(wood, upper=True), f"blocks/door_{name}_upper.png")
    save(trapdoor(), "blocks/trapdoor.png")
    save(trapdoor(iron=True), "blocks/iron_trapdoor.png")

    # --- rails and redstone
    save(rail(), "blocks/rail_normal.png")
    save(rail(turned=True), "blocks/rail_normal_turned.png")
    for kind in ("golden", "detector", "activator"):
        save(rail(kind), f"blocks/rail_{kind}.png")
        save(rail(kind, powered=True), f"blocks/rail_{kind}_powered.png")
    save(redstone_dust(), "blocks/redstone_dust_line.png")
    save(redstone_dust(cross=True), "blocks/redstone_dust_cross.png")
    save(new(), "blocks/redstone_dust_line_overlay.png")
    save(new(), "blocks/redstone_dust_cross_overlay.png")
    save(torch((255, 200, 70)), "blocks/torch_on.png")
    save(torch(REDSTONE), "blocks/redstone_torch_on.png")
    save(torch((110, 40, 40), lit=False), "blocks/redstone_torch_off.png")
    save(lever(), "blocks/lever.png")
    save(tripwire_source(), "blocks/trip_wire_source.png")
    save(tripwire(), "blocks/trip_wire.png")
    for lit, suf in ((False, "off"), (True, "on")):
        save(slab_device(lit, "repeater"), f"blocks/repeater_{suf}.png")
        save(slab_device(lit, "comparator"), f"blocks/comparator_{suf}.png")
        save(redstone_lamp(lit), f"blocks/redstone_lamp_{suf}.png")
    top, side = daylight()
    save(top, "blocks/daylight_detector_top.png")
    save(side, "blocks/daylight_detector_side.png")
    save(daylight(True)[0], "blocks/daylight_detector_inverted_top.png")
    for name, img in piston().items():
        save(img, f"blocks/{name}.png")
    for name, img in dispenser_fronts().items():
        save(img, f"blocks/{name}.png")
    out, top, inside = hopper()
    save(out, "blocks/hopper_outside.png")
    save(top, "blocks/hopper_top.png")
    save(inside, "blocks/hopper_inside.png")
    save(command_block(), "blocks/command_block.png")

    # --- utility / decoration
    side, top, inner, bottom = cauldron()
    save(side, "blocks/cauldron_side.png")
    save(top, "blocks/cauldron_top.png")
    save(inner, "blocks/cauldron_inner.png")
    save(bottom, "blocks/cauldron_bottom.png")
    base, tops = anvil()
    save(base, "blocks/anvil_base.png")
    for i, t in enumerate(tops):
        save(t, f"blocks/anvil_top_damaged_{i}.png")
    t, s, b = enchanting_table()
    save(t, "blocks/enchanting_table_top.png")
    save(s, "blocks/enchanting_table_side.png")
    save(b, "blocks/enchanting_table_bottom.png")
    stand, base = brewing_stand()
    save(stand, "blocks/brewing_stand.png")
    save(base, "blocks/brewing_stand_base.png")
    t, s, e = endframe()
    save(t, "blocks/endframe_top.png")
    save(s, "blocks/endframe_side.png")
    save(e, "blocks/endframe_eye.png")
    save(dragon_egg(), "blocks/dragon_egg.png")
    save(beacon_core(), "blocks/beacon.png")
    save(flower_pot(), "blocks/flower_pot.png")
    save(itemframe_bg(), "blocks/itemframe_background.png")
    save(iron_bars(), "blocks/iron_bars.png")
    save(web(), "blocks/web.png")
    save(mob_spawner(), "blocks/mob_spawner.png")
    side, top, note = jukebox_noteblock()
    save(side, "blocks/jukebox_side.png")
    save(top, "blocks/jukebox_top.png")
    save(note, "blocks/noteblock.png")
    s, t, b = cactus()
    save(s, "blocks/cactus_side.png")
    save(t, "blocks/cactus_top.png")
    save(b, "blocks/cactus_bottom.png")
    t, s, i, b = cake()
    save(t, "blocks/cake_top.png")
    save(s, "blocks/cake_side.png")
    save(i, "blocks/cake_inner.png")
    save(b, "blocks/cake_bottom.png")
    side, top, off, on = pumpkin_family()
    save(side, "blocks/pumpkin_side.png")
    save(top, "blocks/pumpkin_top.png")
    save(off, "blocks/pumpkin_face_off.png")
    save(on, "blocks/pumpkin_face_on.png")
    s, t = melon()
    save(s, "blocks/melon_side.png")
    save(t, "blocks/melon_top.png")
    s, t = hay()
    save(s, "blocks/hay_block_side.png")
    save(t, "blocks/hay_block_top.png")
    red, brown, stem_img, inside = mushroom_blocks()
    save(red, "blocks/mushroom_block_skin_red.png")
    save(brown, "blocks/mushroom_block_skin_brown.png")
    save(stem_img, "blocks/mushroom_block_skin_stem.png")
    save(inside, "blocks/mushroom_block_inside.png")

    # --- stone / sand variants
    for name, base, seed in (("granite", (170, 110, 90), 181), ("diorite", (200, 200, 204), 183),
                             ("andesite", (128, 130, 128), 185)):
        rough, smooth = stone_variant(base, seed)
        save(rough, f"blocks/stone_{name}.png")
        save(smooth, f"blocks/stone_{name}_smooth.png")
    slab_top = smooth_stone(seed=191)
    save(slab_top, "blocks/stone_slab_top.png")
    slab_side = smooth_stone(seed=192)
    sp = slab_side.load()
    for x in range(16):
        sp[x, 7] = (*shade(STONE, -0.45), 255)
        sp[x, 8] = (*shade(STONE, 0.25), 255)
    save(slab_side, "blocks/stone_slab_side.png")
    save(paint(soft_noise(91, (0.2, 0.4, 0.4), cells=(4, 2), weights=(0.6, 0.4)), ramp(RED_SAND, (-0.2, 0.0, 0.15))),
         "blocks/red_sand.png")
    for part, img in sandstone_set(RED_SAND).items():
        save(img, f"blocks/red_sandstone_{part}.png")
    lines, lines_top, chis, chis_top = quartz_extras()
    save(lines, "blocks/quartz_block_lines.png")
    save(lines_top, "blocks/quartz_block_lines_top.png")
    save(chis, "blocks/quartz_block_chiseled.png")
    save(chis_top, "blocks/quartz_block_chiseled_top.png")
    ice = paint(soft_noise(201, (0.3, 0.4, 0.3), cells=(8, 4), weights=(0.6, 0.4)), [(150, 186, 236), (170, 204, 244), (200, 224, 250)])
    ipx = ice.load()
    for (x, y) in [(3, 4), (4, 3), (10, 11), (11, 10), (12, 9), (7, 13)]:
        ipx[x, y] = (236, 246, 255, 255)
    save(ice, "blocks/ice_packed.png")
    wet = paint(cobble_pattern(seed=33, count=14), ramp((170, 170, 70), (-0.5, -0.25, -0.05, 0.15, 0.3)))
    save(wet, "blocks/sponge_wet.png")

    # --- terrain variants
    save(paint(soft_noise(211, (0.2, 0.35, 0.3, 0.15)), ramp((118, 86, 60), (-0.4, -0.15, 0.0, 0.2))), "blocks/coarse_dirt.png")
    pod_top = grassy_top((120, 84, 44), 213)
    save(pod_top, "blocks/dirt_podzol_top.png")
    save(topped_side(pod_top, (120, 84, 44)), "blocks/dirt_podzol_side.png")
    myc_top = grassy_top((122, 100, 124), 215)
    save(myc_top, "blocks/mycelium_top.png")
    save(topped_side(myc_top, (122, 100, 124)), "blocks/mycelium_side.png")
    save(farmland(False), "blocks/farmland_dry.png")
    save(farmland(True), "blocks/farmland_wet.png")
    save(soul_sand(), "blocks/soul_sand.png")
    save(nether_brick(), "blocks/nether_brick.png")
    save(slime_block(), "blocks/slime.png")

    # --- ocean monument
    save_anim(sea_lantern(), "blocks/sea_lantern.png", frametime=5)
    save_anim(prismarine_rough(), "blocks/prismarine_rough.png", frametime=300, interpolate=True,
              order=[0, 1, 0, 2, 0, 3, 0, 1, 2, 1, 3, 1, 0, 2, 1, 2, 3, 2, 0, 3, 1, 3])
    save(prismarine_bricks(), "blocks/prismarine_bricks.png")
    save(prismarine_dark(), "blocks/prismarine_dark.png")

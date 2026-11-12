"""Block textures for Tidal. Every family shares one pattern and only changes the palette."""
import math
import random

from lib import (fbm, grid, mix, mul, new, paint, quantize, ramp, save, shade, sprite, vnoise)

# 16 dye colors (1.8 names). Wool, clay and glass are all built from these.
DYES = {
    "white": (226, 232, 238), "orange": (238, 128, 36), "magenta": (192, 70, 196),
    "light_blue": (86, 172, 236), "yellow": (244, 206, 48), "lime": (118, 200, 46),
    "pink": (238, 138, 172), "gray": (72, 76, 84), "silver": (152, 158, 166),
    "cyan": (28, 146, 158), "purple": (124, 56, 186), "blue": (48, 70, 184),
    "brown": (118, 76, 44), "green": (70, 108, 34), "red": (196, 44, 44), "black": (30, 30, 36),
}

WOODS = {  # planks color, bark color, inner-ring color
    "oak": ((176, 136, 82), (102, 78, 48), (196, 158, 100)),
    "spruce": ((114, 82, 50), (60, 42, 28), (140, 104, 66)),
    "birch": ((212, 194, 138), (222, 222, 212), (226, 210, 160)),
    "jungle": ((168, 112, 78), (90, 70, 32), (186, 132, 92)),
    "acacia": ((182, 96, 50), (104, 98, 90), (200, 116, 66)),
    "big_oak": ((80, 54, 30), (58, 44, 28), (100, 70, 40)),
}

STONE = (126, 128, 134)


# ---------------------------------------------------------------- patterns (palette-index maps)
def bevel(idx, hi, lo):
    """Light top/left edge, dark bottom/right edge."""
    for i in range(16):
        idx[0][i] = hi
        idx[i][0] = hi
        idx[15][i] = lo
        idx[i][15] = lo
    return idx


def wool_pattern():
    """Soft knit: low-contrast noise, small stitch marks, bevelled edge. Indices 0..4."""
    idx = quantize(fbm(16, 16, 11, cells=(8, 4), weights=(0.6, 0.4)), [0.2, 0.6, 0.2], base=1)
    for y in range(16):
        for x in range(16):
            # fine diagonal weave: a light fleck and a dark fleck on alternating diagonals
            k = (x + 2 * y) % 8
            if k == 0:
                idx[y][x] = min(3, idx[y][x] + 1)
            elif k == 4:
                idx[y][x] = max(1, idx[y][x] - 1)
    return bevel(idx, 4, 0)


def clay_pattern():
    """Smooth with faint horizontal strata. Indices 0..4."""
    n = fbm(16, 16, 23, cells=(8, 4), weights=(0.7, 0.3), sx=2)
    idx = quantize(n, [0.3, 0.45, 0.25], base=1)
    for x in range(16):
        for y in (5, 11):
            if (x + y) % 5 != 0:
                idx[y][x] = max(1, idx[y][x] - 1)
    return bevel(idx, 4, 0)


def plank_pattern():
    """Four boards, 4px tall, with seams, staggered joints and grain. Indices 0..4."""
    grain = quantize(fbm(16, 16, 5, cells=(4, 2), weights=(0.6, 0.4), sx=4), [0.3, 0.45, 0.25], base=1)
    idx = [row[:] for row in grain]
    joints = [3, 11, 7, 14]
    for b in range(4):
        y0 = b * 4
        for x in range(16):
            idx[y0][x] = min(4, idx[y0][x] + 1) if idx[y0][x] < 3 else 3   # top of board catches light
            idx[y0 + 3][x] = 0                                              # seam
        j = joints[b]
        for y in range(y0, y0 + 3):
            idx[y][j] = 0
            idx[y][(j + 1) % 16] = 3
    return idx


def cobble_cells(seed, count):
    rng = random.Random(seed)
    pts = [(rng.uniform(0, 16), rng.uniform(0, 16)) for _ in range(count)]
    out = grid()
    edge = grid()
    for y in range(16):
        for x in range(16):
            ds = []
            for i, (px, py) in enumerate(pts):
                dx = min(abs(x + 0.5 - px), 16 - abs(x + 0.5 - px))
                dy = min(abs(y + 0.5 - py), 16 - abs(y + 0.5 - py))
                ds.append((math.hypot(dx, dy), i))
            ds.sort()
            out[y][x] = ds[0][1]
            edge[y][x] = ds[1][0] - ds[0][0]
    return out, edge


def cobble_pattern(seed=7, count=9):
    """Rounded stones with dark mortar, lit from the top-left. Indices 0..4."""
    cell, edge = cobble_cells(seed, count)
    idx = grid()
    for y in range(16):
        for x in range(16):
            if edge[y][x] < 0.9:
                idx[y][x] = 0
                continue
            c = cell[y][x]
            up = cell[(y - 1) % 16][x] != c or edge[(y - 1) % 16][x] < 0.9
            left = cell[y][(x - 1) % 16] != c or edge[y][(x - 1) % 16] < 0.9
            down = cell[(y + 1) % 16][x] != c or edge[(y + 1) % 16][x] < 0.9
            right = cell[y][(x + 1) % 16] != c or edge[y][(x + 1) % 16] < 0.9
            v = 2 + (c % 2 == 0 and (x + y) % 7 == 0) * -1
            if up or left:
                v = 4 if (up and left) else 3
            elif down or right:
                v = 1
            idx[y][x] = v
    return idx


def brick_pattern(bw=8, bh=4, seed=3):
    """Offset bricks with mortar. Indices 0..4 (0 = mortar)."""
    n = quantize(fbm(16, 16, seed, cells=(4, 2), weights=(0.6, 0.4)), [0.3, 0.5, 0.2], base=1)
    idx = grid()
    for y in range(16):
        row = y // bh
        off = (bw // 2) * (row % 2)
        for x in range(16):
            lx, ly = (x + off) % bw, y % bh
            if ly == bh - 1 or lx == bw - 1:
                idx[y][x] = 0
            elif ly == 0 or lx == 0:
                idx[y][x] = 4 if ly == 0 and lx == 0 else 3
            else:
                idx[y][x] = n[y][x]
    return idx


def soft_noise(seed, fractions=(0.2, 0.3, 0.3, 0.2), cells=(8, 4, 2), weights=(0.5, 0.35, 0.15), base=0, sx=1, sy=1):
    return quantize(fbm(16, 16, seed, cells=cells, weights=weights, sx=sx, sy=sy), list(fractions), base=base)


# Ore gems: one shared layout so every ore matches. 'o' outline, 'a' dark, 'b' mid, 'c' light, 'd' glint.
ORE_GEMS = [
    "................",
    "..ooo...........",
    ".obcdo......oo..",
    ".obbco.....obco.",
    "..obo.....obbbco",
    "...o.......obbo.",
    "............oo..",
    "......ooo.......",
    ".....obcco......",
    ".....obbbco.....",
    "......obbo......",
    ".......oo...ooo.",
    "..oo.......obcdo",
    ".obco......obbo.",
    ".obbo.......oo..",
    "..oo............",
]

ORES = {  # gem color
    "coal": (46, 46, 52), "iron": (222, 178, 146), "gold": (250, 206, 58),
    "diamond": (78, 228, 218), "emerald": (42, 204, 104), "lapis": (40, 82, 204),
    "redstone": (226, 30, 30), "quartz": (232, 226, 218),
}


# ---------------------------------------------------------------- builders
def stone_tex():
    return paint(soft_noise(1, (0.15, 0.35, 0.35, 0.15)), ramp(STONE, (-0.35, -0.15, 0.0, 0.18)))


def ore_tex(base_img, gem):
    img = base_img.copy()
    g = ramp(gem, (-0.55, -0.2, 0.0, 0.4))
    outline_c = shade(gem, -0.85) if gem != ORES["coal"] else (22, 22, 26)
    colors = {"o": outline_c, "a": g[0], "b": g[1], "c": g[2], "d": g[3]}
    img.alpha_composite(sprite(ORE_GEMS, colors))
    return img


def ore_block_tex(color):
    """Plated block: four bevelled 8x8 panels with a shine. Same layout for every ore block."""
    r = ramp(color, (-0.6, -0.25, 0.0, 0.3, 0.7))
    idx = grid(fill=2)
    for y in range(16):
        for x in range(16):
            lx, ly = x % 8, y % 8
            if lx == 7 or ly == 7:
                idx[y][x] = 0
            elif lx == 0 or ly == 0:
                idx[y][x] = 3
            elif lx == 6 or ly == 6:
                idx[y][x] = 1
            elif (lx + ly) in (3, 4) and lx < 5:
                idx[y][x] = 4
    return paint(idx, r)


def log_side(bark, birch=False):
    idx = quantize(fbm(16, 16, 9, cells=(4, 2), weights=(0.6, 0.4), sy=4), [0.2, 0.35, 0.3, 0.15])
    for y in range(16):
        for x in range(16):
            if x % 4 == 1 and (y + x * 3) % 7 < 5:
                idx[y][x] = 0
    if birch:
        img = paint(idx, ramp(bark, (-0.15, -0.05, 0.05, 0.2)))
        px = img.load()
        rng = random.Random(4)
        for _ in range(6):
            x, y = rng.randrange(0, 14), rng.randrange(0, 16)
            for dx in range(rng.choice((2, 3))):
                px[x + dx, y] = (54, 52, 50, 255)
        return img
    return paint(idx, ramp(bark, (-0.6, -0.3, 0.0, 0.25)))


def log_top(bark, inner):
    r = ramp(inner, (-0.35, -0.15, 0.0, 0.2))
    idx = grid()
    for y in range(16):
        for x in range(16):
            d = max(abs(x - 7.5), abs(y - 7.5)) * 0.7 + math.hypot(x - 7.5, y - 7.5) * 0.3
            ring = int(d)
            idx[y][x] = [3, 2, 1, 2, 3, 2, 1, 2][min(ring, 7)]
    img = paint(idx, r)
    px = img.load()
    br = ramp(bark, (-0.4, 0.0))
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)):
            px[x, y] = (*br[0], 255)
    for i in range(1, 15):
        for (x, y) in ((i, 1), (i, 14), (1, i), (14, i)):
            px[x, y] = (*br[1], 255)
    return img


def glass_tex(color=None):
    """Plain glass: opaque frame + glints, clear inside (cutout). Stained: translucent tint."""
    img = new()
    px = img.load()
    if color is None:
        frame, glint, fill = (222, 236, 244, 255), (240, 248, 255, 255), None
    else:
        r = ramp(color, (-0.35, 0.0, 0.5))
        frame, glint, fill = (*r[0], 235), (*r[2], 170), (*r[1], 110)
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                px[x, y] = frame
            elif fill:
                px[x, y] = fill
    for (x, y) in [(3, 4), (4, 3), (5, 2), (3, 5), (10, 12), (11, 11), (12, 10), (12, 4), (11, 5)]:
        px[x, y] = glint
    return img


def pane_top(color=None):
    img = new()
    px = img.load()
    c = (222, 236, 244, 255) if color is None else (*ramp(color, (-0.35,))[0], 235)
    for y in range(16):
        for x in (7, 8):
            px[x, y] = c
    return img


def leaves_tex(seed):
    """Grayscale (biome-tinted in game). Transparent holes keep a dark color for Fast graphics."""
    # Small leaf clusters: each 4x4 cell gets a rounded clump, lit from the top-left.
    rng = random.Random(seed)
    idx = grid(fill=-1)
    for cy in range(0, 16, 4):
        for cx in range(0, 16, 4):
            ox, oy = (cx + (2 if (cy // 4) % 2 else 0) + rng.choice((0, 1))) % 16, cy + rng.choice((0, 1))
            for dy in range(-1, 4):
                for dx in range(-1, 4):
                    if (dx, dy) in ((-1, -1), (3, -1), (-1, 3), (3, 3)):
                        continue
                    x, y = (ox + dx) % 16, (oy + dy) % 16
                    v = 2 if dx + dy < 3 else 1
                    if dx <= 0 and dy <= 0:
                        v = 3
                    if dx >= 3 or dy >= 3:
                        v = 0
                    idx[y][x] = max(idx[y][x], v)
    for _ in range(14):  # a few holes for Fancy graphics
        idx[rng.randrange(16)][rng.randrange(16)] = -1
    img = paint(idx, [(74, 74, 74), (118, 118, 118), (156, 156, 156), (190, 190, 190)])
    px = img.load()
    for y in range(16):
        for x in range(16):
            if px[x, y][3] == 0:
                px[x, y] = (44, 44, 44, 0)
    return img


def grass_top_gray():
    idx = soft_noise(31, (0.2, 0.35, 0.3, 0.15), cells=(4, 2), weights=(0.6, 0.4))
    for y in range(16):
        for x in range(16):
            if (x * 7 + y * 3) % 11 == 0:
                idx[y][x] = 3
    return paint(idx, [(138, 138, 138), (158, 158, 158), (176, 176, 176), (196, 196, 196)])


PLAINS = (145, 189, 89)


def dirt_tex():
    img = paint(soft_noise(41, (0.2, 0.35, 0.3, 0.15)), ramp((134, 96, 66), (-0.35, -0.15, 0.0, 0.18)))
    px = img.load()
    for (x, y) in [(3, 4), (11, 2), (6, 11), (13, 9), (1, 13), (9, 6)]:
        px[x, y] = (*shade((134, 96, 66), 0.35), 255)
        px[x, (y + 1) % 16] = (*shade((134, 96, 66), -0.45), 255)
    return img


def grass_fringe():
    """Heights of the grass overhang on the side texture, per column."""
    return [3, 4, 3, 2, 3, 4, 5, 4, 3, 3, 4, 3, 2, 3, 4, 3]


def grass_side(tint=PLAINS):
    img = dirt_tex()
    px = img.load()
    top = grass_top_gray().load()
    for x, hgt in enumerate(grass_fringe()):
        for y in range(hgt):
            g = top[x, y][0] / 255
            c = mul(tint, g * 1.0)
            px[x, y] = (*c, 255)
        px[x, hgt] = (*shade(mul(tint, 0.62), -0.2), 255) if hgt < 16 else px[x, hgt]
    return img


def grass_overlay():
    img = new()
    px = img.load()
    top = grass_top_gray().load()
    for x, hgt in enumerate(grass_fringe()):
        for y in range(hgt):
            px[x, y] = top[x, y]
        px[x, hgt] = (96, 96, 96, 255)
    return img


def snowy_side():
    img = dirt_tex()
    px = img.load()
    snow = snow_tex().load()
    for x, hgt in enumerate(grass_fringe()):
        for y in range(hgt):
            px[x, y] = snow[x, y]
        px[x, hgt] = (198, 210, 222, 255)
    return img


def snow_tex():
    return paint(soft_noise(51, (0.25, 0.4, 0.35), cells=(8, 4), weights=(0.6, 0.4)),
                 [(220, 230, 240), (234, 242, 250), (246, 250, 255)])


def tnt_side():
    stick = [(170, 22, 22), (214, 38, 34), (236, 64, 56), (214, 38, 34)]
    rows = []
    for y in range(16):
        r = []
        for x in range(16):
            if 5 <= y <= 10:
                r.append((250, 250, 250) if y == 5 else (186, 186, 190) if y == 10 else (226, 226, 228))
            elif y in (4, 11):
                r.append((140, 16, 18))
            else:
                r.append(stick[x % 4])
        rows.append(r)
    img = new()
    px = img.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = (*rows[y][x], 255)
    letters = [(2, ["###", ".#.", ".#.", ".#."]), (6, ["#..#", "##.#", "#.##", "#..#"]),
               (11, ["###", ".#.", ".#.", ".#."])]
    for x0, rws in letters:
        for dy, row in enumerate(rws):
            for dx, ch in enumerate(row):
                if ch == "#":
                    px[x0 + dx, 6 + dy] = (42, 42, 52, 255)
    return img


def tnt_top(bottom=False):
    img = new()
    px = img.load()
    stick = [(170, 22, 22), (214, 38, 34), (236, 64, 56), (214, 38, 34)]
    for y in range(16):
        for x in range(16):
            lx, ly = x % 4, y % 4
            # ends of the dynamite sticks: small circles
            ring = (lx in (0, 3) or ly in (0, 3))
            px[x, y] = (*(stick[0] if ring else stick[2] if (lx, ly) == (1, 1) else stick[1]), 255)
    if not bottom:
        for (x, y) in [(7, 7), (8, 7), (7, 8), (8, 8)]:
            px[x, y] = (60, 56, 52, 255)
        for (x, y) in [(8, 6), (9, 5), (9, 4)]:
            px[x, y] = (210, 200, 180, 255)
    return img


def bed_textures():
    """Vanilla 1.8 bed model: tops/sides are horizontal; foot end at x=0, head end at x=15."""
    blanket = ramp((44, 120, 214), (-0.55, -0.2, 0.0, 0.3))   # Tidal blue
    pillow = [(206, 214, 224), (232, 238, 246), (250, 252, 255)]
    wood = ramp(WOODS["oak"][0], (-0.6, -0.3, 0.0, 0.25))

    def top(head):
        idx = []
        for y in range(16):
            r = []
            for x in range(16):
                if not head and x < 2:
                    r.append(("w", 1 if x == 0 else 2))
                elif head and x > 13:
                    r.append(("w", 1 if x == 15 else 2))
                elif head and 6 <= x <= 12 and 2 <= y <= 13:
                    edge = x in (6, 12) or y in (2, 13)
                    r.append(("p", 0 if edge else (2 if (x + y) % 5 == 0 else 1)))
                else:
                    # blanket with a fold line and a soft quilted stripe
                    v = 2
                    if y in (0, 15):
                        v = 0
                    elif y in (1, 14):
                        v = 1
                    elif (x + (y // 4)) % 6 == 0:
                        v = 3
                    if head and x == 5:
                        v = 0
                    r.append(("b", v))
            idx.append(r)
        img = new()
        px = img.load()
        for y in range(16):
            for x in range(16):
                k, v = idx[y][x]
                c = {"w": wood, "p": pillow, "b": blanket}[k][v]
                px[x, y] = (*c, 255)
        return img

    def side(head):
        img = new()
        px = img.load()
        for x in range(16):
            for y in range(7, 16):
                if y <= 9:
                    if head and x >= 6:
                        c = pillow[1] if y > 7 else pillow[2]
                        if x > 13:
                            c = wood[2]
                    else:
                        c = blanket[3] if y == 7 else blanket[2]
                        if not head and x < 2:
                            c = wood[2]
                elif y <= 12:
                    c = wood[0] if y == 12 else wood[2] if y == 10 else wood[1]
                else:
                    end_leg = (not head and x < 3) or (head and x > 12)
                    if not end_leg:
                        continue
                    c = wood[1] if (x in (0, 15)) else wood[2]
                px[x, y] = (*c, 255)
        return img

    def end():
        img = new()
        px = img.load()
        for x in range(16):
            for y in range(7, 16):
                if y <= 12:
                    c = wood[3] if y == 7 else wood[0] if y == 12 else wood[2] if x % 5 else wood[1]
                elif x < 3 or x > 12:
                    c = wood[1]
                else:
                    continue
                px[x, y] = (*c, 255)
        return img

    return {"bed_feet_top": top(False), "bed_head_top": top(True), "bed_feet_side": side(False),
            "bed_head_side": side(True), "bed_feet_end": end(), "bed_head_end": end()}


def ladder_tex():
    w = ramp(WOODS["oak"][0], (-0.55, -0.2, 0.05, 0.3))
    img = new()
    px = img.load()
    for y in range(16):
        for x in (2, 3, 12, 13):
            px[x, y] = (*w[2 if x in (2, 12) else 1], 255)
        if y % 4 == 1:
            for x in range(4, 12):
                px[x, y] = (*w[3], 255)
            for x in range(4, 12):
                px[x, y + 1] = (*w[0], 255)
    return img


def destroy_stages():
    """Crack overlays. Rendered with a multiply-like blend: <128 darkens, >128 lightens."""
    rng = random.Random(99)
    # Branches radiate from the middle; each is a list of pixels in growth order.
    branches = []
    for k in range(6):
        ang = k * math.pi / 3 + rng.uniform(-0.3, 0.3)
        x, y, path = 7.5, 7.5, []
        for _ in range(9):
            ang += rng.uniform(-0.45, 0.45)
            x, y = x + math.cos(ang), y + math.sin(ang)
            p = (int(round(x)), int(round(y)))
            if 0 <= p[0] < 16 and 0 <= p[1] < 16 and p not in path:
                path.append(p)
        branches.append(path)
    # interleave so every stage grows all branches a little
    segs = []
    for i in range(max(len(b) for b in branches)):
        for b in branches:
            if i < len(b):
                segs.append(b[i])
    out = []
    for s in range(10):
        img = new()
        px = img.load()
        n = max(2, int(len(segs) * (s + 1) / 10))
        for (x, y) in [(8, 8)] + segs[:n]:
            px[x, y] = (24, 24, 28, 255)
        for (x, y) in segs[:n]:
            for dx, dy in ((1, 0), (0, 1)):
                xx, yy = x + dx, y + dy
                if xx < 16 and yy < 16 and px[xx, yy][3] == 0:
                    px[xx, yy] = (72, 72, 78, 255)
            if 0 < x and 0 < y and px[x - 1, y - 1][3] == 0:
                px[x - 1, y - 1] = (190, 190, 196, 255)   # light lip on the crack edge
        out.append(img)
    return out


def crafting_table():
    planks = paint(plank_pattern(), ramp(WOODS["oak"][0]))
    w = ramp(WOODS["big_oak"][0], (-0.5, -0.2, 0.0, 0.3))
    top = planks.copy()
    px = top.load()
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)):
            px[x, y] = (*w[1], 255)
    for i in range(2, 14):
        for (x, y) in ((i, 5), (i, 10), (5, i), (10, i)):
            px[x, y] = (*w[0], 255)
    side = planks.copy()
    sp = side.load()
    for x in range(16):
        for y in (0, 1):
            sp[x, y] = (*w[2 - y], 255)
    front = side.copy()
    fp = front.load()
    tools = sprite([
        "................",
        "................",
        "................",
        "..ooo......o....",
        "..oIIo....oSo...",
        "...oIo...oSSo...",
        "....oo..oSSo....",
        ".....oo.oho.....",
        "......oho.......",
        ".....ohoo.......",
        "....oho..o......",
        "...oho..........",
        "...oo...........",
        "................",
        "................",
        "................",
    ], {"o": (40, 30, 24), "I": (200, 204, 212), "S": (150, 152, 160), "h": (120, 84, 50)})
    front.alpha_composite(tools)
    for x in range(16):
        for y in (0, 1):
            fp[x, y] = (*w[2 - y], 255)
    return top, side, front


def furnace():
    s = ramp(STONE, (-0.5, -0.25, -0.05, 0.15, 0.35))
    side = paint(brick_pattern(8, 8, seed=13), s)
    top = paint(soft_noise(61, (0.2, 0.4, 0.4)), [s[1], s[2], s[3]])
    tp = top.load()
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)):
            tp[x, y] = (*s[0], 255)

    def front(lit):
        img = side.copy()
        px = img.load()
        for y in range(8, 14):
            for x in range(3, 13):
                edge = x in (3, 12) or y in (8, 13)
                if edge:
                    px[x, y] = (*s[0], 255)
                elif lit:
                    heat = (y - 8) / 5
                    px[x, y] = (*mix((255, 120, 30), (255, 230, 120), heat), 255)
                else:
                    px[x, y] = (24, 24, 28, 255)
        for x in range(3, 13):
            px[x, 4] = (*s[0], 255)
            px[x, 5] = (*s[4], 255)
        return img

    return top, side, front(False), front(True)


def bookshelf():
    img = paint(plank_pattern(), ramp(WOODS["oak"][0]))
    px = img.load()
    books = [(178, 52, 52), (52, 96, 178), (66, 140, 70), (196, 160, 52), (120, 60, 150), (60, 150, 160)]
    rng = random.Random(8)
    for shelf in (1, 9):
        x = 1
        while x < 15:
            bw = rng.choice((1, 2))
            c = rng.choice(books)
            hgt = rng.choice((5, 6))
            for dx in range(bw):
                if x + dx > 14:
                    break
                for y in range(shelf + 6 - hgt, shelf + 6):
                    px[x + dx, y] = (*(shade(c, 0.25) if dx == 0 else c), 255)
                px[x + dx, shelf + 6 - hgt + 1] = (*shade(c, 0.6), 255)
            x += bw
    return img


def generate():
    # --- dye families
    wp, cp = wool_pattern(), clay_pattern()
    for name, c in DYES.items():
        save(paint(wp, ramp(c, (-0.6, -0.25, 0.0, 0.22, 0.5))), f"blocks/wool_colored_{name}.png")
        clay = mix(shade(c, -0.2), (150, 100, 76), 0.28)
        save(paint(cp, ramp(clay, (-0.5, -0.2, 0.0, 0.18, 0.4))), f"blocks/hardened_clay_stained_{name}.png")
        save(glass_tex(c), f"blocks/glass_{name}.png")
        save(pane_top(c), f"blocks/glass_pane_top_{name}.png")
    save(paint(cp, ramp((152, 96, 68), (-0.5, -0.2, 0.0, 0.18, 0.4))), "blocks/hardened_clay.png")
    save(paint(soft_noise(71, (0.25, 0.5, 0.25)), ramp((158, 164, 178), (-0.15, 0.0, 0.15))), "blocks/clay.png")
    save(glass_tex(), "blocks/glass.png")
    save(pane_top(), "blocks/glass_pane_top.png")

    # --- wood
    pp = plank_pattern()
    for wood, (plank, bark, inner) in WOODS.items():
        save(paint(pp, ramp(plank, (-0.55, -0.22, 0.0, 0.2, 0.42))), f"blocks/planks_{wood}.png")
        save(log_side(bark, birch=(wood == "birch")), f"blocks/log_{wood}.png")
        save(log_top(bark, inner), f"blocks/log_{wood}_top.png")
        save(leaves_tex(hash(wood) % 1000 if False else len(wood) * 17), f"blocks/leaves_{wood}.png")

    # --- stone family
    stone = stone_tex()
    save(stone, "blocks/stone.png")
    s5 = ramp(STONE, (-0.6, -0.3, -0.05, 0.15, 0.35))
    cob = paint(cobble_pattern(), s5)
    save(cob, "blocks/cobblestone.png")
    mossy = cob.copy()
    mp = mossy.load()
    moss = fbm(16, 16, 77, cells=(8, 4), weights=(0.6, 0.4))
    for y in range(16):
        for x in range(16):
            if moss[y][x] > 0.62 and mp[x, y][0] > 60:
                mp[x, y] = (*mix(mp[x, y][:3], (86, 132, 56), 0.65), 255)
    save(mossy, "blocks/cobblestone_mossy.png")
    sb = paint(brick_pattern(8, 4, seed=17), s5)
    save(sb, "blocks/stonebrick.png")
    save(paint(brick_pattern(8, 4, seed=17), ramp((116, 126, 110), (-0.6, -0.3, -0.05, 0.15, 0.35))), "blocks/stonebrick_mossy.png")
    cracked = sb.copy()
    cp_ = cracked.load()
    for (x, y) in [(5, 1), (6, 2), (6, 3), (11, 9), (10, 10), (10, 11), (3, 13), (4, 14)]:
        cp_[x, y] = (*s5[0], 255)
    save(cracked, "blocks/stonebrick_cracked.png")
    carved = paint(bevel(grid(fill=2), 3, 0), s5)
    cv = carved.load()
    for i in range(4, 12):
        for (x, y) in ((i, 4), (i, 11), (4, i), (11, i)):
            cv[x, y] = (*s5[1], 255)
    save(carved, "blocks/stonebrick_carved.png")
    save(paint(brick_pattern(4, 4, seed=19), ramp((150, 72, 56), (-0.6, -0.3, -0.05, 0.15, 0.35))), "blocks/brick.png")
    save(paint(soft_noise(81, (0.15, 0.3, 0.35, 0.2)), ramp((88, 90, 96), (-0.6, -0.3, 0.0, 0.25))), "blocks/bedrock.png")

    # --- ores (shared gem layout) + ore blocks (shared plate layout)
    for ore, gem in ORES.items():
        if ore == "quartz":
            continue
        save(ore_tex(stone, gem), f"blocks/{ore}_ore.png")
    for ore in ("iron", "gold", "diamond", "emerald", "lapis", "redstone", "coal"):
        save(ore_block_tex(ORES[ore] if ore != "coal" else (40, 40, 46)), f"blocks/{ore}_block.png")

    # --- terrain
    save(dirt_tex(), "blocks/dirt.png")
    save(grass_top_gray(), "blocks/grass_top.png")
    save(grass_side(), "blocks/grass_side.png")
    save(grass_overlay(), "blocks/grass_side_overlay.png")
    save(snowy_side(), "blocks/grass_side_snowed.png")
    save(snow_tex(), "blocks/snow.png")
    save(paint(soft_noise(91, (0.2, 0.4, 0.4), cells=(4, 2), weights=(0.6, 0.4)), ramp((220, 206, 152), (-0.2, 0.0, 0.15))), "blocks/sand.png")
    save(paint(soft_noise(92, (0.2, 0.3, 0.3, 0.2), cells=(4, 2), weights=(0.5, 0.5)), ramp((138, 128, 126), (-0.45, -0.15, 0.1, 0.35))), "blocks/gravel.png")
    sand = (214, 198, 140)
    ss_side = paint([[(0 if y in (3, 12) else 3 if y in (0, 4, 13) else 2 if y < 3 or y > 12 else 1 + (x + y) % 2) for x in range(16)] for y in range(16)],
                    ramp(sand, (-0.35, -0.12, 0.0, 0.18)))
    save(ss_side, "blocks/sandstone_normal.png")
    save(paint(soft_noise(93, (0.3, 0.4, 0.3)), ramp(sand, (-0.1, 0.0, 0.12))), "blocks/sandstone_top.png")
    save(paint(soft_noise(94, (0.3, 0.4, 0.3)), ramp(sand, (-0.2, -0.08, 0.05))), "blocks/sandstone_bottom.png")
    save(paint(bevel(grid(fill=1), 2, 0), ramp(sand, (-0.35, 0.0, 0.18))), "blocks/sandstone_smooth.png")
    carved_ss = paint(bevel(grid(fill=1), 2, 0), ramp(sand, (-0.35, 0.0, 0.18)))
    cs = carved_ss.load()
    for i in range(4, 12):
        for (x, y) in ((i, 4), (i, 11), (4, i), (11, i), (i, i) if 5 <= i <= 10 else (4, 4)):
            cs[x, y] = (*shade(sand, -0.35), 255)
    save(carved_ss, "blocks/sandstone_carved.png")
    save(paint(soft_noise(95, (0.15, 0.25, 0.4, 0.2), cells=(4, 2), weights=(0.6, 0.4)), ramp((222, 222, 162), (-0.3, -0.12, 0.0, 0.15))), "blocks/end_stone.png")
    obs = paint(soft_noise(96, (0.35, 0.35, 0.2, 0.1), cells=(4, 2), weights=(0.6, 0.4)), [(18, 14, 28), (30, 22, 46), (52, 36, 80), (92, 64, 140)])
    save(obs, "blocks/obsidian.png")
    save(paint(soft_noise(97, (0.2, 0.35, 0.3, 0.15), cells=(4, 2), weights=(0.6, 0.4)), ramp((112, 44, 44), (-0.5, -0.2, 0.0, 0.25))), "blocks/netherrack.png")
    glow = paint(cobble_pattern(seed=21, count=10), ramp((232, 178, 96), (-0.5, -0.15, 0.1, 0.35, 0.6)))
    save(glow, "blocks/glowstone.png")
    ice = paint(soft_noise(98, (0.3, 0.4, 0.3), cells=(8, 4), weights=(0.6, 0.4)), [(150, 190, 240, 170), (170, 206, 246, 170), (200, 226, 252, 180)])
    ip = ice.load()
    for (x, y) in [(3, 4), (4, 3), (10, 11), (11, 10), (12, 9)]:
        ip[x, y] = (240, 248, 255, 210)
    save(ice, "blocks/ice.png")
    save(paint(cobble_pattern(seed=33, count=14), ramp((206, 196, 76), (-0.45, -0.2, 0.0, 0.2, 0.4))), "blocks/sponge.png")
    quartz = (232, 228, 222)
    save(paint(bevel(soft_noise(99, (0.3, 0.4, 0.3), base=1), 4, 0), ramp(quartz, (-0.35, -0.1, 0.0, 0.1, 0.25))), "blocks/quartz_block_side.png")
    save(paint(bevel(soft_noise(99, (0.3, 0.4, 0.3), base=1), 4, 0), ramp(quartz, (-0.35, -0.1, 0.0, 0.1, 0.25))), "blocks/quartz_block_top.png")
    save(paint(bevel(soft_noise(98, (0.3, 0.4, 0.3), base=1), 4, 0), ramp(quartz, (-0.4, -0.15, -0.05, 0.05, 0.2))), "blocks/quartz_block_bottom.png")
    save(ore_tex(paint(soft_noise(97, (0.2, 0.35, 0.3, 0.15), cells=(4, 2), weights=(0.6, 0.4)), ramp((112, 44, 44), (-0.5, -0.2, 0.0, 0.25))), ORES["quartz"]), "blocks/quartz_ore.png")

    # --- bedwars / utility blocks
    save(tnt_side(), "blocks/tnt_side.png")
    save(tnt_top(), "blocks/tnt_top.png")
    save(tnt_top(bottom=True), "blocks/tnt_bottom.png")
    for name, img in bed_textures().items():
        save(img, f"blocks/{name}.png")
    save(ladder_tex(), "blocks/ladder.png")
    t, s, f = crafting_table()
    save(t, "blocks/crafting_table_top.png")
    save(s, "blocks/crafting_table_side.png")
    save(f, "blocks/crafting_table_front.png")
    ft, fs, ff, ffl = furnace()
    save(ft, "blocks/furnace_top.png")
    save(fs, "blocks/furnace_side.png")
    save(ff, "blocks/furnace_front_off.png")
    save(ffl, "blocks/furnace_front_on.png")
    save(bookshelf(), "blocks/bookshelf.png")
    for i, img in enumerate(destroy_stages()):
        save(img, f"blocks/destroy_stage_{i}.png")

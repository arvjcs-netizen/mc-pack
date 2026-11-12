"""Item textures for Tidal. Each family (swords, tools, armor) is one shape recolored per material."""
import math
import sys
from pathlib import Path

from PIL import Image

from lib import (TEX, mix, new, outline, ramp, save, save_anim, shade, sprite)

INK = (22, 20, 28)  # base outline color

MATERIALS = {
    "wood": (156, 114, 66),
    "stone": (132, 134, 140),
    "iron": (214, 218, 228),
    "gold": (250, 204, 54),
    "diamond": (76, 226, 216),
}
ARMOR_MATERIALS = {
    "leather": (200, 200, 200),     # tinted by dye color in game, so keep it light gray
    "chainmail": (150, 158, 170),
    "iron": MATERIALS["iron"],
    "gold": MATERIALS["gold"],
    "diamond": MATERIALS["diamond"],
}
HANDLE = (112, 76, 44)
TIDAL_BLUE = (44, 120, 214)


def mat_ramp(c):
    return ramp(c, (-0.62, -0.3, 0.0, 0.32, 0.7))


def ink_for(c):
    return mix(INK, shade(c, -0.85), 0.35)


# ---------------------------------------------------------------- diagonal drawing
def ad(x, y):
    """Diagonal coords: a runs bottom-left -> top-right (0..30), d is the perpendicular offset."""
    return x - y + 15, x + y - 15


def diag_item(classify, ink):
    """classify(a, d) -> RGB or None for each pixel, then outline."""
    img = new()
    px = img.load()
    for y in range(16):
        for x in range(16):
            a, d = ad(x, y)
            c = classify(a, d)
            if c:
                px[x, y] = (*c, 255)
    return outline(img, ink)


def sword(mat):
    m = mat_ramp(MATERIALS[mat])
    h = ramp(HANDLE, (-0.5, -0.15, 0.2))
    guard = m if mat != "wood" else ramp(MATERIALS["wood"], (-0.62, -0.3, 0.0, 0.32, 0.7))

    def cls(a, d):
        if 1 <= a <= 3 and -1 <= d <= 1:                     # pommel
            return guard[3] if d < 0 else guard[1] if d > 0 else guard[2]
        if 4 <= a <= 7 and d == 0:                            # grip
            return h[2] if a == 6 else h[1]
        if 8 <= a <= 9 and -4 <= d <= 4:                      # crossguard
            return guard[3] if d < 0 else guard[1] if d > 0 else guard[2]
        if 10 <= a <= 24 and -1 <= d <= 1:                    # blade: 3px wide, lit edge / ridge / shadow edge
            if d < 0:
                return m[4] if a in (17, 19) else m[3]
            if d == 0:
                return m[2] if a < 22 else m[3]
            return m[1]
        if a == 25 and abs(d) == 1:                           # tip
            return m[3] if d < 0 else m[2]
        if a == 26 and d == 0:
            return m[3]
        return None

    return diag_item(cls, ink_for(MATERIALS[mat]))


def tool(kind, mat):
    m = mat_ramp(MATERIALS[mat])
    h = ramp(HANDLE, (-0.5, -0.15, 0.2))

    def head(a, d):
        if kind == "pickaxe":
            # an arc across the top of the handle whose ends curve back down
            ac = 22 - round(d * d / 7)
            if -7 <= d <= 7 and ac - 2 <= a <= ac:
                return m[3] if a == ac or (a == ac - 1 and d < 0) else m[1] if d > 3 else m[2]
        elif kind == "axe":
            # flared blade on the upper-left side of the handle (wide flat edge), small poll behind
            if -7 <= d <= -1:
                half = 1.5 + (-d - 1) * 0.85
                if 20 - half <= a <= 20 + half:
                    return m[4] if d == -7 else m[3] if d >= -6 and d <= -5 else m[2] if d <= -3 else m[1]
            if 1 <= d <= 2 and 19 <= a <= 22:
                return m[1]
        elif kind == "shovel":
            if 17 <= a <= 28 and -3 <= d <= 3:
                if a >= 27 and abs(d) > 1:
                    return None
                if a <= 18 and abs(d) > 1:
                    return None
                return m[3] if d < 0 else m[2] if d == 0 else m[1]
        elif kind == "hoe":
            if 21 <= a <= 24 and -7 <= d <= 1:
                return m[3] if a >= 23 and d < 0 else m[2] if d < 0 else m[1]
        return None

    def cls(a, d):
        c = head(a, d)
        if c:
            return c
        if 1 <= a <= 22 and d == 0:
            return h[2] if a % 6 == 0 else h[1]
        return None

    return diag_item(cls, ink_for(MATERIALS[mat]))


# ---------------------------------------------------------------- mask + auto-shade
def auto(mask, base, ts=(-0.62, -0.3, 0.0, 0.32, 0.7), ink=None):
    """'x' fill, 'd' detail line, 'g' glint, 'L' light fill, 'D' dark fill. Lit from the top-left."""
    r = ramp(base, ts)
    img = new()
    px = img.load()
    H, W = len(mask), len(mask[0])

    def filled(x, y):
        return 0 <= x < W and 0 <= y < H and mask[y][x] != "."

    for y in range(H):
        for x in range(W):
            ch = mask[y][x]
            if ch == ".":
                continue
            if ch == "d":
                c = r[0]
            elif ch == "g":
                c = r[4]
            elif ch == "L":
                c = r[3]
            elif ch == "D":
                c = r[1]
            elif not filled(x, y - 1) or not filled(x - 1, y):
                c = r[3]
            elif not filled(x, y + 1) or not filled(x + 1, y):
                c = r[1]
            else:
                c = r[2]
            px[x, y] = (*c, 255)
    return outline(img, ink or ink_for(base))


ARMOR_MASKS = {
    "helmet": [
        "................",
        "................",
        "................",
        "....xxxxxxxx....",
        "...xxgxxxxxxx...",
        "..xxgxxxxxxxxx..",
        "..xxxxxxxxxxxx..",
        "..xxxddddddxxx..",
        "..xxx......xxx..",
        "..xxx......xxx..",
        "..xx........xx..",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "chestplate": [
        "................",
        "................",
        "..xxx......xxx..",
        ".xxxxx....xxxxx.",
        ".xgxxxxxxxxxxxx.",
        ".xxxxxxxxxxxxxx.",
        ".xxxxxxxxxxxxxx.",
        "..xx.xxxxxx.xx..",
        "....xxxxxxxx....",
        "....xxxdxxxx....",
        "....xxxdxxxx....",
        "....xxxxxxxx....",
        "....xxxxxxxx....",
        "................",
        "................",
        "................",
    ],
    "leggings": [
        "................",
        "................",
        "................",
        "...xxxxxxxxxx...",
        "...dddddddddd...",
        "...xgxxxxxxxx...",
        "...xxxxxxxxxx...",
        "...xxxx..xxxx...",
        "...xxxx..xxxx...",
        "...xxxx..xxxx...",
        "...xxxx..xxxx...",
        "...xxxx..xxxx...",
        "...xxxx..xxxx...",
        "................",
        "................",
        "................",
    ],
    "boots": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "...xxx....xxx...",
        "...xgx....xgx...",
        "...xxx....xxx...",
        "..xxxx...xxxx...",
        ".xxxxx..xxxxx...",
        ".ddddd..ddddd...",
        "................",
        "................",
        "................",
        "................",
    ],
}


# ---------------------------------------------------------------- misc item sprites
def gem_diamond():
    m = mat_ramp(MATERIALS["diamond"])
    return outline(sprite([
        "................",
        "................",
        "................",
        "....bbcccdd.....",
        "...bccccddde....",
        "..bbbbccdddee...",
        "..aabbbcccdee...",
        "...aabbbccdd....",
        "....aabbbcd.....",
        ".....aabbc......",
        "......aab.......",
        ".......a........",
        "................",
        "................",
        "................",
        "................",
    ], {"a": m[0], "b": m[1], "c": m[2], "d": m[3], "e": m[4]}), ink_for(MATERIALS["diamond"]))


def gem_emerald():
    m = mat_ramp((44, 206, 104))
    return outline(sprite([
        "................",
        "................",
        "......dde.......",
        ".....cddde......",
        "....bccdddd.....",
        "....bccccdd.....",
        "....bbcccdd.....",
        "....bbcccdd.....",
        "....bbccccd.....",
        "....abbcccd.....",
        "....aabbccc.....",
        ".....aabbc......",
        "......aab.......",
        "................",
        "................",
        "................",
    ], {"a": m[0], "b": m[1], "c": m[2], "d": m[3], "e": m[4]}), ink_for((44, 206, 104)))


def ingot(color):
    m = mat_ramp(color)
    return outline(sprite([
        "................",
        "................",
        "................",
        "................",
        "......eeddddc...",
        "....edddddddcb..",
        "..eddddddddccbb.",
        "..cccccccccbbba.",
        "..bbbbbbbbbbbaa.",
        "...aaaaaaaaaaa..",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ], {"a": m[0], "b": m[1], "c": m[2], "d": m[3], "e": m[4]}), ink_for(color))


def orb(color, r=5.5, cx=7.5, cy=8.0, spec=True):
    """Shaded sphere (pearl, snowball, apple body)."""
    m = mat_ramp(color)
    img = new()
    px = img.load()
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - cx - 0.5, y + 0.5 - cy - 0.5
            if dx * dx + dy * dy <= r * r:
                lx, ly = dx + r * 0.35, dy + r * 0.35
                t = math.hypot(lx, ly) / (r * 1.3)
                i = 4 if t < 0.18 and spec else 3 if t < 0.42 else 2 if t < 0.7 else 1 if t < 0.95 else 0
                px[x, y] = (*m[i], 255)
    return outline(img, ink_for(color))


def apple(color, leaf=(70, 160, 56)):
    img = orb(color, r=5.2, cy=8.6)
    px = img.load()
    for (x, y) in [(8, 2), (8, 3)]:
        px[x, y] = (90, 62, 36, 255)
    for (x, y), c in [((9, 2), leaf), ((10, 2), leaf), ((10, 1), shade(leaf, 0.3))]:
        px[x, y] = (*c, 255)
    return img


def ender_pearl():
    img = orb((30, 150, 140), r=5.5)
    px = img.load()
    for (x, y) in [(6, 7), (7, 6), (9, 9), (9, 10), (10, 9)]:
        px[x, y] = (*shade((30, 150, 140), -0.55), 255)
    return img


def arrow():
    shaft = ramp(HANDLE, (-0.4, 0.0, 0.3))
    tip = mat_ramp(MATERIALS["stone"])

    def cls(a, d):
        if 22 <= a <= 27 and -1 <= d <= 1:  # arrowhead
            if a - 22 < abs(d) * 2 + 1 and abs(d) == 1 and a > 24:
                return None
            return tip[3] if d <= 0 else tip[1]
        if 6 <= a <= 21 and d == 0:
            return shaft[1]
        if 1 <= a <= 6 and -2 <= d <= 2 and (a + abs(d)) % 2 == 0:  # fletching
            return (232, 236, 244) if d <= 0 else (196, 200, 210)
        return None

    img = new()
    px = img.load()
    for y in range(16):
        for x in range(16):
            a, d = ad(x, y)
            c = cls(a, d)
            if c:
                px[x, y] = (*c, 255)
    return img


def stick():
    h = ramp(HANDLE, (-0.5, -0.1, 0.25))

    def cls(a, d):
        if 3 <= a <= 27 and d == 0:
            return h[2] if a % 5 == 0 else h[1]
        return None

    return diag_item(cls, ink_for(HANDLE))


def bucket(fill=None):
    m = mat_ramp(MATERIALS["iron"])
    rows = [
        "................",
        "....dddddddd....",
        "...d........d...",
        "...cddddddddc...",
        "..cbffffffffbc..",
        "..bcffffffffcb..",
        "..bccccccccccb..",
        "...bccccccccb...",
        "...bbccccccbb...",
        "...bbbccccbbb...",
        "....bbbbbbbb....",
        "....abbbbbba....",
        ".....aaaaaa.....",
        "................",
        "................",
        "................",
    ]
    cols = {"a": m[0], "b": m[1], "c": m[2], "d": m[3], "f": m[1]}
    if fill:
        f = ramp(fill, (-0.2, 0.0, 0.3))
        cols["f"] = f[1]
    img = sprite(rows, cols)
    if fill:
        px = img.load()
        for (x, y) in [(5, 4), (6, 4), (9, 5)]:
            px[x, y] = (*ramp(fill, (0.35,))[0], 255)
    return outline(img, ink_for(MATERIALS["iron"]))


def potion(splash=False):
    """Bottle glass + a grayscale liquid overlay that the game tints with the potion color."""
    glass = (210, 226, 240)
    rows_bottle = [
        "................",
        "................",
        "......kkkk......",
        "......gwwg......",
        ".......gg.......",
        ".......gg.......",
        "......g..g......",
        ".....g....g.....",
        "....g......g....",
        "....g......g....",
        "....g......g....",
        "....g......g....",
        ".....g....g.....",
        "......gggg......",
        "................",
        "................",
    ]
    if splash:
        rows_bottle = [
            "................",
            "................",
            "......kkkk......",
            "......gwwg......",
            ".......gg.......",
            "......g..g......",
            ".....g....g.....",
            "....g......g....",
            "...g........g...",
            "...g........g...",
            "...g........g...",
            "....g......g....",
            ".....gggggg.....",
            "................",
            "................",
            "................",
        ]
    bottle = sprite(rows_bottle, {"k": (150, 110, 70), "g": glass, "w": (244, 250, 255)})
    bottle = outline(bottle, (40, 50, 70), outside_only=True)
    over = new()
    op = over.load()
    bp = bottle.load()
    # liquid fills the inside of the bottle body
    top = 7 if splash else 8
    for y in range(top, 15):
        row = rows_bottle[y]
        if "g" not in row:
            continue
        l, r = row.index("g"), row.rindex("g")
        for x in range(l + 1, r):
            if bp[x, y][3] == 0:
                v = 230 if (x - l) < 3 and y < top + 3 else 200 if y < 12 else 170
                op[x, y] = (v, v, v, 255)
    empty = bottle.copy()
    return bottle, over, empty


def coal():
    m = mat_ramp((52, 52, 58))
    return auto([
        "................",
        "................",
        "................",
        "................",
        "......xxx.......",
        "....xxxgxxx.....",
        "...xxxxxxxxx....",
        "...xxxxxxxxxx...",
        "....xxxxxxxxx...",
        "....xxxxxxxx....",
        ".....xxxxxx.....",
        "................",
        "................",
        "................",
        "................",
        "................",
    ], (52, 52, 58), ink=(14, 14, 18))


def redstone():
    img = new()
    px = img.load()
    r = mat_ramp((226, 30, 30))
    for (x, y) in [(5, 5), (8, 4), (10, 7), (6, 8), (9, 10), (4, 11), (11, 11), (7, 12)]:
        px[x, y] = (*r[3], 255)
        px[x + 1, y] = (*r[2], 255)
        px[x, y + 1] = (*r[1], 255)
    return outline(img, (70, 8, 8))


def flint_and_steel():
    s = mat_ramp(MATERIALS["iron"])
    f = mat_ramp((70, 70, 78))
    return outline(sprite([
        "................",
        "................",
        "................",
        "...ssss.........",
        "..s....s........",
        "..s.....s.......",
        "..s.....s.......",
        "...s...s........",
        "....sss.........",
        "........fff.....",
        ".......ffFff....",
        "......ffFFfff...",
        "......fffffff...",
        ".......fffff....",
        "................",
        "................",
    ], {"s": s[3], "f": f[2], "F": f[3]}), INK)


def shears():
    s = mat_ramp(MATERIALS["iron"])
    h = mat_ramp((200, 50, 50))
    return outline(sprite([
        "................",
        "................",
        "...........sS...",
        "..........sSs...",
        ".........sSs....",
        "....ss..sSs.....",
        "....sSSsSs......",
        ".....sSSs.......",
        "......hh........",
        ".....h..h.......",
        "....h....h......",
        "....h....h......",
        ".....hhhh.......",
        "................",
        "................",
        "................",
    ], {"s": s[2], "S": s[3], "h": h[2]}), INK)


def fishing_rod(cast=False):
    h = ramp(HANDLE, (-0.5, -0.1, 0.25))
    img = new()
    px = img.load()
    for y in range(16):
        for x in range(16):
            a, d = ad(x, y)
            if 2 <= a <= 28 and d == 0:
                px[x, y] = (*(h[2] if a > 18 else h[1]), 255)
    img = outline(img, INK)
    px = img.load()
    if not cast:
        for y in range(2, 12):
            px[14, y] = (226, 230, 236, 255)
        px[14, 12] = (200, 200, 210, 255)
        px[13, 12] = (200, 200, 210, 255)
    return img


def bed_item():
    blanket = ramp(TIDAL_BLUE, (-0.55, -0.2, 0.0, 0.3))
    wood = ramp((176, 136, 82), (-0.6, -0.3, 0.0))
    return outline(sprite([
        "................",
        "................",
        "................",
        "................",
        "..........pppp..",
        "......bbbbpppPp.",
        "....bbbBbbbppPp.",
        "..bbbBbbbbbbbpp.",
        ".bbBbbbbbbbbbbw.",
        ".bbbbbbbbbbbbbw.",
        ".wwwwwwwwwwwwww.",
        ".W............W.",
        ".W............W.",
        "................",
        "................",
        "................",
    ], {"b": blanket[2], "B": blanket[3], "p": (232, 238, 246), "P": (206, 214, 224),
        "w": wood[2], "W": wood[1]}), INK)


def food(kind):
    if kind == "bread":
        return auto([
            "................",
            "................",
            "................",
            "................",
            "................",
            "....xxxxxxx.....",
            "..xxgxxgxxgxx...",
            ".xxxxxxxxxxxxx..",
            ".xxxxxxxxxxxxx..",
            "..xxxxxxxxxxx...",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ], (196, 140, 66))
    if kind == "beef_cooked":
        img = auto([
            "................",
            "................",
            "................",
            ".....xxxxx......",
            "...xxxxxxxxx....",
            "..xxgxxxxxxxx...",
            "..xxxxxxxxxxxx..",
            "..xxxxxxxxxxxx..",
            "...xxxxxxxxxxx..",
            "....xxxxxxxxx...",
            ".....xxxxxxx....",
            "................",
            "................",
            "................",
            "................",
            "................",
        ], (126, 74, 46))
        px = img.load()
        for (x, y) in [(5, 6), (6, 7), (7, 8), (9, 6), (10, 7)]:
            px[x, y] = (150, 104, 74, 255)
        return img
    if kind == "carrot_golden":
        m = mat_ramp(MATERIALS["gold"])

        def cls(a, d):
            if 4 <= a <= 22 and abs(d) <= (1 if a > 8 else 0):
                return m[3] if d < 0 else m[2] if d == 0 else m[1]
            if 23 <= a <= 27 and -2 <= d <= 2 and (a + d) % 2 == 0:
                return (90, 190, 70)
            return None

        return diag_item(cls, ink_for(MATERIALS["gold"]))


def snowball():
    return orb((236, 242, 250), r=5.0)


def egg():
    m = mat_ramp((232, 220, 196))
    img = new()
    px = img.load()
    for y in range(16):
        for x in range(16):
            dx, dy = (x - 7.5) / 4.5, (y - 8.5) / (5.5 if y > 8 else 6.2)
            if dx * dx + dy * dy <= 1:
                t = math.hypot(dx + 0.4, dy + 0.4)
                px[x, y] = (*m[3 if t < 0.5 else 2 if t < 0.95 else 1], 255)
    return outline(img, ink_for((232, 220, 196)))


# ---------------------------------------------------------------- animated items
def bow_frames():
    """Bow: Tidal-blue limbs that pulse bright -> deep -> bright. Returns {name: [frames]}."""
    def limbs(x, y):
        r = math.hypot(15 - x - 0.5, 15 - y - 0.5)
        return 11.3 <= r <= 13.2 and 1 <= x <= 14 and 1 <= y <= 14

    mask = [["x" if limbs(x, y) else "." for x in range(16)] for y in range(16)]
    ends = [(13, 2), (2, 13)]

    def line(px, p0, p1, color):
        (x0, y0), (x1, y1) = p0, p1
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
            if 0 <= x < 16 and 0 <= y < 16:
                px[x, y] = (*color, 255)

    pulls = {"bow_standby": 0.0, "bow_pulling_0": 1.6, "bow_pulling_1": 2.8, "bow_pulling_2": 4.0}
    bright, deep = TIDAL_BLUE, (20, 50, 130)
    out = {}
    for name, pull in pulls.items():
        frames = []
        for f in range(8):
            k = (1 - math.cos(2 * math.pi * f / 8)) / 2
            img = auto(["".join(r) for r in mask], mix(bright, deep, k))
            px = img.load()
            p = (7.5 + pull, 7.5 + pull)
            line(px, ends[0], p, (232, 236, 244))
            line(px, ends[1], p, (232, 236, 244))
            if pull:
                tip = (p[0] - 10, p[1] - 10)
                shaft = ramp(HANDLE, (-0.3, 0.1))
                line(px, (p[0] - 1, p[1] - 1), (tip[0] + 2, tip[1] + 2), shaft[1])
                for (x, y) in [(int(tip[0]) + 1, int(tip[1]) + 1), (int(tip[0]) + 2, int(tip[1]) + 1),
                               (int(tip[0]) + 1, int(tip[1]) + 2)]:
                    if 0 <= x < 16 and 0 <= y < 16:
                        px[x, y] = (*mat_ramp(MATERIALS["stone"])[3], 255)
            frames.append(img)
        out[name] = frames
    return out


def fireball_frames():
    """Reuse the original MyPack fire charge design (tools/gen_fireball.py)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import gen_fireball
    return [gen_fireball.draw_frame(i / gen_fireball.FRAMES) for i in range(gen_fireball.FRAMES)]


# ---------------------------------------------------------------- generate
def generate():
    for mat in MATERIALS:
        save(sword(mat), f"items/{mat}_sword.png")
        for kind in ("pickaxe", "axe", "shovel", "hoe"):
            save(tool(kind, mat), f"items/{mat}_{kind}.png")
    for mat, base in ARMOR_MATERIALS.items():
        for piece, mask in ARMOR_MASKS.items():
            if mat == "chainmail":
                # chain links: punch a checker of holes into the inner fill
                mask = ["".join(("." if ch == "x" and (x + y) % 2 == 0 and 0 < x < 15 and
                                 mask[y][x - 1] != "." and mask[y][x + 1] != "." and
                                 mask[y - 1][x] != "." and mask[y + 1][x] != "." else ch)
                                for x, ch in enumerate(row)) for y, row in enumerate(mask)]
            save(auto(mask, base), f"items/{mat}_{piece}.png")
            if mat == "leather":
                save(new(), f"items/leather_{piece}_overlay.png")

    save(gem_diamond(), "items/diamond.png")
    save(gem_emerald(), "items/emerald.png")
    save(ingot(MATERIALS["iron"]), "items/iron_ingot.png")
    save(ingot(MATERIALS["gold"]), "items/gold_ingot.png")
    save(coal(), "items/coal.png")
    save(redstone(), "items/redstone_dust.png")
    save(ender_pearl(), "items/ender_pearl.png")
    save(apple((210, 40, 40)), "items/apple.png")
    save(apple(MATERIALS["gold"], leaf=(240, 220, 120)), "items/apple_golden.png")
    save(arrow(), "items/arrow.png")
    save(stick(), "items/stick.png")
    save(bucket(), "items/bucket_empty.png")
    save(bucket((52, 110, 220)), "items/bucket_water.png")
    save(bucket((240, 110, 20)), "items/bucket_lava.png")
    save(bucket((244, 246, 250)), "items/bucket_milk.png")
    b, o, e = potion()
    save(b, "items/potion_bottle_drinkable.png")
    save(o, "items/potion_overlay.png")
    save(e, "items/potion_bottle_empty.png")
    sb, _, _ = potion(splash=True)
    save(sb, "items/potion_bottle_splash.png")
    save(flint_and_steel(), "items/flint_and_steel.png")
    save(shears(), "items/shears.png")
    save(fishing_rod(), "items/fishing_rod_uncast.png")
    save(fishing_rod(cast=True), "items/fishing_rod_cast.png")
    save(bed_item(), "items/bed.png")
    save(food("bread"), "items/bread.png")
    save(food("beef_cooked"), "items/beef_cooked.png")
    save(food("carrot_golden"), "items/carrot_golden.png")
    save(snowball(), "items/snowball.png")
    save(egg(), "items/egg.png")
    for name, frames in bow_frames().items():
        save_anim(frames, f"items/{name}.png", frametime=4, interpolate=True)
    save_anim(fireball_frames(), "items/fireball.png", frametime=2)

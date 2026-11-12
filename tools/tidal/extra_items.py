"""Every item texture items.py doesn't cover. Families: dyes (one powder pile x16), records (one disc x12),
doors (one door x7), minecarts (one cart + cargo), horse armor (one shape x3), seeds (one pile x3), fish, meat."""
import math

from blocks import DYES, WOODS
from items import (HANDLE, INK, MATERIALS, TIDAL_BLUE, ad, auto, diag_item, ink_for, mat_ramp, orb)
from lib import mix, new, outline, ramp, save, save_anim, shade, sprite

EMPTY = ["." * 16] * 16


def M(*rows):
    """Pad a short mask to 16x16, centered vertically."""
    rows = [r.ljust(16, ".")[:16] for r in rows]
    top = (16 - len(rows)) // 2
    return ["." * 16] * top + rows + ["." * 16] * (16 - top - len(rows))


# ---------------------------------------------------------------- shapes
DUST = M(
    "................",
    "......x.........",
    ".....xxx..x.....",
    "....xxgxxxxx....",
    "...xxxxxxxxxx...",
    "..xxxxxxxxxxxx..",
    ".xxxxxxxxxxxxxx.",
    ".dddddddddddddd.",
)

DISC = None  # built procedurally

SEEDS = M(
    "................",
    "....x.....x.....",
    "...xg...x.xg....",
    "...xx..xg.xx....",
    ".......xx.......",
    "..x.......x..x..",
    ".xg..x...xg.xg..",
    ".xx.xg...xx.xx..",
    "....xx..........",
)

STEAK = M(
    "......xxxx......",
    "....xxxxxxxx....",
    "...xxgxxxxxxx...",
    "..xxxxxxxxxxxx..",
    "..xxxxxxxxxxxx..",
    "..xxxxxxxxxxx...",
    "...xxxxxxxxx....",
    "....xxxxxxx.....",
    "......xxx.......",
)

DRUMSTICK = M(
    ".......xxxx.....",
    ".....xxxxxxxx...",
    "....xxgxxxxxxx..",
    "....xxxxxxxxxx..",
    "....xxxxxxxxxx..",
    "....xxxxxxxxx...",
    "...xxxxxxxxx....",
    "..bbxxxxxx......",
    ".bbb............",
    ".bb.............",
)

FISH = M(
    "................",
    "........xxxx....",
    "..x...xxxxxxxx..",
    "..xx.xxxgxxxxxx.",
    "..xxxxxxxxxxxexx",
    "..xxxxxxxxxxxxx.",
    "..xx.xxxxxxxxx..",
    "..x...xxxxxxx...",
    "................",
)

BOOK = M(
    "....xxxxxxxxx...",
    "...xxxxxxxxxxp..",
    "..xxxxxxxxxxxp..",
    "..xxxxxxxxxxxp..",
    "..xxxxxxxxxxxp..",
    "..xxxxxxxxxxxp..",
    "..xxxxxxxxxxxp..",
    "..xxxxxxxxxxxp..",
    "..xxxxxxxxxxpp..",
    "..ddddddddddd...",
)

CART = M(
    "................",
    "..xxxxxxxxxxxx..",
    "..xLLLLLLLLLLx..",
    "..xxxxxxxxxxxx..",
    "..xxxxxxxxxxxx..",
    "...xxxxxxxxxx...",
    "...dd......dd...",
    "..dwwd....dwwd..",
    "...dd......dd...",
)

HORSE_ARMOR = M(
    "...........xx...",
    "..........xxxx..",
    ".........xxgxxx.",
    "........xxxxxxx.",
    ".xxxxxxxxxxxxx..",
    "xxgxxxxxxxxxx...",
    "xxxxxxxxxxxxx...",
    "xxxxxxxxxxxxx...",
    ".xx.xx...xx.xx..",
    ".xx.xx...xx.xx..",
)

DOOR = [
    "................",
    "................",
    ".....xxxxxx.....",
    ".....xGGGGx.....",
    ".....xGxxGx.....",
    ".....xGGGGx.....",
    ".....xxxxxx.....",
    ".....xxxxxx.....",
    ".....xddddx.....",
    ".....xxxxhx.....",
    ".....xddddx.....",
    ".....xxxxxx.....",
    ".....xxxxxx.....",
    ".....xxxxxx.....",
    "................",
    "................",
]


def colored(mask, cols, ink):
    img = sprite(mask, cols)
    return outline(img, ink)


# ---------------------------------------------------------------- builders
def dye(color):
    img = auto(DUST, color)
    return img


def record(label):
    img = new()
    p = img.load()
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5)
            if r < 7.0:
                if r < 1.0:
                    continue
                if r < 3.2:
                    c = shade(label, 0.25 if (x < 8 and y < 8) else 0.0)
                else:
                    groove = int(r * 2) % 2
                    c = (44, 44, 52) if groove else (30, 30, 38)
                    if (x - y) in (-6, -5) and r > 3.5:
                        c = (90, 94, 110)
                p[x, y] = (*c, 255)
    return outline(img, (12, 12, 16))


def seeds(color):
    return auto(SEEDS, color)


def meat(color, raw=True, shape=STEAK, marbling=None):
    img = auto(shape, color)
    p = img.load()
    if marbling:
        for (x, y) in marbling:
            if p[x, y][3]:
                p[x, y] = (*shade(color, 0.45 if raw else 0.25), 255)
    bone = [(x, y) for y, row in enumerate(shape) for x, ch in enumerate(row) if ch == "b"]
    for (x, y) in bone:
        p[x, y] = (236, 230, 216, 255)
    return img


def fish(color, belly, eye=(20, 20, 24)):
    img = auto(FISH, color)
    p = img.load()
    for y, row in enumerate(FISH):
        for x, ch in enumerate(row):
            if ch == "e":
                p[x, y] = (*eye, 255)
            elif ch != "." and y >= 9 and x > 4:
                p[x, y] = (*belly, 255)
    return img


def book(cover, kind="normal"):
    img = auto(BOOK, cover)
    p = img.load()
    for y, row in enumerate(BOOK):
        for x, ch in enumerate(row):
            if ch == "p":
                p[x, y] = (236, 232, 220, 255)
    if kind in ("normal", "enchanted"):
        for x in range(4, 11):
            p[x, 6] = (*shade(cover, 0.5), 255)
    if kind == "writable":
        for (x, y) in ((11, 3), (10, 4), (9, 5), (8, 6), (7, 7)):
            p[x, y] = (230, 230, 236, 255)
        p[6, 8] = (40, 40, 48, 255)
    if kind == "written":
        for y in (5, 7, 9):
            for x in range(5, 10):
                p[x, y] = (236, 232, 220, 255)
    return img


def door_item(wood=None):
    base = (196, 200, 212) if wood is None else WOODS[wood][0]
    r = mat_ramp(base)
    img = sprite(DOOR, {"x": r[2], "d": r[1], "G": (150, 200, 236), "h": (50, 50, 56)})
    p = img.load()
    for y in range(2, 14):
        p[5, y] = (*r[3], 255)
        p[10, y] = (*r[1], 255)
    return outline(img, ink_for(base))


def minecart(cargo=None):
    iron = (150, 156, 168)
    img = auto(CART, iron)
    p = img.load()
    rows = CART
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "w":
                p[x, y] = (60, 62, 70, 255)
            if ch == "L":
                p[x, y] = (*shade(iron, -0.6), 255)
    if cargo:
        top = 3 + (16 - len([r for r in rows if r.strip(".")])) // 2 - 3
        cy = rows.index(next(r for r in rows if "L" in r))
        cargo_img, dy = cargo
        img.alpha_composite(cargo_img, (0, cy - dy))
    return img


def cargo_block(kind):
    img = new()
    p = img.load()
    if kind == "chest":
        r = ramp((176, 120, 60), (-0.5, -0.2, 0.0, 0.25))
        for y in range(4):
            for x in range(4, 12):
                p[x, y] = (*r[2 if y else 3], 255)
        p[7, 2] = (230, 210, 120, 255)
        p[8, 2] = (230, 210, 120, 255)
    elif kind == "furnace":
        for y in range(4):
            for x in range(4, 12):
                p[x, y] = (*((120, 122, 128) if y < 2 or not 6 <= x <= 9 else (250, 150, 40)), 255)
    elif kind == "tnt":
        for y in range(4):
            for x in range(4, 12):
                p[x, y] = (*((232, 232, 232) if y == 2 else (214, 38, 34)), 255)
    elif kind == "hopper":
        for y in range(4):
            for x in range(4 + y, 12 - y):
                p[x, y] = (*(74, 76, 86), 255)
    elif kind == "command":
        for y in range(4):
            for x in range(4, 12):
                p[x, y] = (*((196, 132, 90) if x in (4, 11) or y == 0 else (24, 28, 36)), 255)
        p[6, 2] = (110, 230, 140, 255)
    return outline(img, INK), 3


def horse_armor(color):
    return auto(HORSE_ARMOR, color)


def simple(mask, color, **kw):
    return auto(M(*mask) if len(mask) < 16 else mask, color, **kw)


def rod(color, glow=None, a0=3, a1=27, thick=False):
    m = mat_ramp(color)

    def cls(a, d):
        if a0 <= a <= a1 and (d == 0 or (thick and d == -1 and a0 + 2 <= a <= a1 - 2)):
            return m[3] if d < 0 else (m[4] if glow and a % 6 == 0 else m[2])
        return None

    return diag_item(cls, ink_for(color))


def compass_frames():
    frames = []
    for i in range(32):
        ang = -i / 32 * 2 * math.pi
        img = orb((150, 156, 168), r=6.0)
        p = img.load()
        for y in range(16):
            for x in range(16):
                if math.hypot(x - 7.5, y - 8.0) < 4.6:
                    p[x, y] = (226, 232, 240, 255)
        for t in range(-4, 5):
            x = round(7.5 + math.sin(ang) * t * 0.95)
            y = round(8.0 - math.cos(ang) * t * 0.95)
            if 0 <= x < 16 and 0 <= y < 16:
                p[x, y] = (*((226, 40, 40) if t > 0 else (60, 64, 76)), 255)
        p[7, 8] = (40, 40, 48, 255)
        frames.append(img)
    return frames


def clock_frames():
    frames = []
    gold = MATERIALS["gold"]
    for i in range(64):
        img = orb(gold, r=6.0, spec=False)
        p = img.load()
        ang = i / 64 * 2 * math.pi
        for y in range(16):
            for x in range(16):
                dx, dy = x - 7.5, y - 8.0
                if math.hypot(dx, dy) < 4.6:
                    # face: a day/night dial that rotates; top half sky, bottom half night
                    a = math.atan2(dx, -dy) + ang
                    up = math.cos(a)
                    p[x, y] = (*(mix((60, 150, 230), (250, 220, 90), 0.0) if up > 0 else (24, 30, 70)), 255)
                    if up > 0.85 and math.hypot(dx, dy) > 2.6:
                        p[x, y] = (255, 226, 90, 255)
                    if up < -0.85 and math.hypot(dx, dy) > 2.6:
                        p[x, y] = (226, 232, 246, 255)
        p[7, 3] = (40, 34, 20, 255)
        p[8, 3] = (40, 34, 20, 255)
        frames.append(img)
    return frames


# ---------------------------------------------------------------- generate
def generate():
    for name, c in DYES.items():
        save(dye(c), f"items/dye_powder_{name}.png")

    disc_labels = {"13": (240, 200, 60), "cat": (90, 200, 70), "blocks": (230, 110, 40), "chirp": (200, 50, 40),
                   "far": (140, 210, 80), "mall": (120, 90, 210), "mellohi": (220, 120, 220), "stal": (40, 40, 50),
                   "strad": (240, 240, 240), "ward": (60, 140, 80), "11": (60, 60, 70), "wait": (70, 160, 230)}
    for name, c in disc_labels.items():
        save(record(c), f"items/record_{name}.png")

    for wood, name in (("oak", "wood"), ("spruce", "spruce"), ("birch", "birch"), ("jungle", "jungle"),
                       ("acacia", "acacia"), ("big_oak", "dark_oak"), (None, "iron")):
        save(door_item(wood), f"items/door_{name}.png")

    save(minecart(), "items/minecart_normal.png")
    for kind in ("chest", "furnace", "tnt", "hopper"):
        save(minecart(cargo_block(kind)), f"items/minecart_{kind}.png")
    save(minecart(cargo_block("command")), "items/minecart_command_block.png")

    for mat in ("iron", "gold", "diamond"):
        save(horse_armor(MATERIALS[mat]), f"items/{mat}_horse_armor.png")

    save(seeds((120, 170, 60)), "items/seeds_wheat.png")
    save(seeds((90, 120, 50)), "items/seeds_melon.png")
    save(seeds((230, 210, 150)), "items/seeds_pumpkin.png")

    # --- meat: raw / cooked pairs share a shape
    marb = [(6, 6), (7, 7), (9, 6), (10, 8), (5, 9)]
    save(meat((214, 80, 84), marbling=marb), "items/beef_raw.png")
    save(meat((236, 140, 140), marbling=marb), "items/porkchop_raw.png")
    save(meat((170, 100, 64), raw=False, marbling=marb), "items/porkchop_cooked.png")
    save(meat((210, 70, 76), marbling=marb), "items/mutton_raw.png")
    save(meat((140, 84, 56), raw=False, marbling=marb), "items/mutton_cooked.png")
    save(meat((236, 190, 170), shape=DRUMSTICK), "items/chicken_raw.png")
    save(meat((196, 130, 70), raw=False, shape=DRUMSTICK), "items/chicken_cooked.png")
    save(meat((226, 150, 140), shape=DRUMSTICK), "items/rabbit_raw.png")
    save(meat((180, 110, 64), raw=False, shape=DRUMSTICK), "items/rabbit_cooked.png")
    save(meat((120, 140, 70), marbling=marb), "items/rotten_flesh.png")
    save(fish((120, 150, 170), (200, 210, 214)), "items/fish_cod_raw.png")
    save(fish((180, 150, 110), (220, 200, 160)), "items/fish_cod_cooked.png")
    save(fish((200, 70, 60), (230, 150, 130)), "items/fish_salmon_raw.png")
    save(fish((170, 100, 64), (210, 160, 110)), "items/fish_salmon_cooked.png")
    clown = fish((240, 130, 40), (240, 130, 40))
    cp = clown.load()
    for y in range(16):
        for x in (6, 10):
            if cp[x, y][3] and cp[x, y][:3] != (20, 20, 24):
                cp[x, y] = (246, 246, 246, 255)
    save(clown, "items/fish_clownfish_raw.png")
    puffer = orb((230, 200, 60), r=5.0)
    pp = puffer.load()
    for (x, y) in ((2, 8), (13, 8), (8, 2), (8, 13), (4, 4), (12, 4), (4, 12), (12, 12)):
        pp[x, y] = (236, 236, 220, 255)
    pp[10, 7] = (20, 20, 24, 255)
    save(puffer, "items/fish_pufferfish_raw.png")

    # --- books / paper / maps
    save(book((150, 60, 40)), "items/book_normal.png")
    save(book((90, 50, 160), "enchanted"), "items/book_enchanted.png")
    save(book((90, 70, 44), "writable"), "items/book_writable.png")
    save(book((60, 110, 70), "written"), "items/book_written.png")
    paper = simple(["...xxxxxxxx.....", "..xxxxxxxxxx....", "..xxxxxxxxxxx...", "..xxdxxxxxxxx...", "..xxxxxxdxxxx...",
                    "..xxxxxxxxxxx...", "..xxdxxxxxxxx...", "...xxxxxxxxxx...", "....xxxxxxxx...."], (236, 232, 220))
    save(paper, "items/paper.png")
    mp = ["...xxxxxxxxx....", "..xxxxxxxxxxx...", "..xxxxxxxxxxx...", "..xxxxxxxxxxx...", "..xxxxxxxxxxx...",
          "..xxxxxxxxxxx...", "..xxxxxxxxxxx...", "..xxxxxxxxxxx...", "...xxxxxxxxx...."]
    save(simple(mp, (226, 214, 176)), "items/map_empty.png")
    filled = simple(mp, (226, 214, 176))
    fp = filled.load()
    for (x, y) in ((5, 6), (6, 6), (6, 7), (9, 8), (10, 8), (10, 9), (7, 10), (8, 10)):
        fp[x, y] = (90, 150, 70, 255)
    for (x, y) in ((4, 9), (5, 10), (11, 6)):
        fp[x, y] = (70, 120, 200, 255)
    save(filled, "items/map_filled.png")
    save(simple(["....x...........", "...xgx..........", "...xxxx.........", "....xxxx........", ".....xxxx.......",
                 "......xxxx......", ".......xxxx.....", "........xxxx....", ".........xx....."], (236, 236, 240)),
         "items/feather.png")
    save(simple([".....xxxxxx.....", "....xxxxxxxx....", "...xxgxxxxxxx...", "...xxxxxxxxxx...", "...xxxxxxxxxx...",
                 "....xxxxxxxx....", ".....xxxxxx....."], (220, 140, 110)), "items/name_tag.png")
    nt = new()
    save(nt, "items/empty_armor_slot_helmet.png") if False else None

    # --- materials
    save(simple(["......xxx.......", ".....xgxxx......", "....xxxxxxx.....", "...xxxxxxxxx....", "...xxxxxxxxx....",
                 "....xxxxxxxx....", ".....xxxxx......"], (54, 54, 60)), "items/charcoal.png")
    save(simple(["..........xxx...", ".........xgxx...", "........xxxx....", ".......xxxx.....", "......xxxx......",
                 ".....xxxx.......", "....xxxx........", "...xxxx.........", "...xxx.........."], (236, 232, 222)),
         "items/bone.png")
    save(simple(["....xxxxxxxx....", "...xxgxxxxxxx...", "...xxxxxxxxxx...", "....dddddddd...."], (190, 120, 80)),
         "items/brick.png")
    save(simple(["....xxxxxxxx....", "...xxgxxxxxxx...", "...xxxxxxxxxx...", "....dddddddd...."], (96, 40, 46)),
         "items/netherbrick.png")
    save(simple(["......xxxx......", "....xxgxxxxx....", "...xxxxxxxxxx...", "...xxxxxxxxxx...", "....xxxxxxxx....",
                 "......xxxx......"], (164, 172, 186)), "items/clay_ball.png")
    save(simple(["......x.........", ".....xxx..x.....", "....xxgxxxxx....", "...xxxxxxxxxx...", "..xxxxxxxxxxxx..",
                 "..dddddddddddd.."], (80, 80, 84)), "items/gunpowder.png")
    save(simple(["......x.........", ".....xxx..x.....", "....xxgxxxxx....", "...xxxxxxxxxx...", "..xxxxxxxxxxxx..",
                 "..dddddddddddd.."], (246, 246, 250)), "items/sugar.png")
    save(simple(["......x.........", ".....xxx..x.....", "....xxgxxxxx....", "...xxxxxxxxxx...", "..xxxxxxxxxxxx..",
                 "..dddddddddddd.."], (250, 210, 80)), "items/glowstone_dust.png")
    save(simple(["......x.........", ".....xxx..x.....", "....xxgxxxxx....", "...xxxxxxxxxx...", "..xxxxxxxxxxxx..",
                 "..dddddddddddd.."], (250, 170, 40)), "items/blaze_powder.png")
    save(simple([".......xx.......", "......xgxx......", ".....xxxxxx.....", "....xxxxxxxx....", "....xxxxxxxx....",
                 ".....xxxxxx.....", "......xxxx......"], (60, 64, 76)), "items/flint.png")
    save(simple(["......xxxx......", ".....xgxxxx.....", "....xxxxxxxx....", "....xxxxxxxx....", ".....xxxxxx.....",
                 "......xxxx......"], (250, 214, 70)), "items/gold_nugget.png")
    save(simple([".......x........", "......xgx.......", ".....xxxxx......", "....xxxxxxx.....", ".....xxxxx......",
                 "......xxx.......", ".......x........"], (210, 236, 246)), "items/ghast_tear.png")
    save(simple(["......xxx.......", ".....xgxxx......", "....xxxxxxx.....", "....xxxxxxx.....", ".....xxxxx......"],
                (236, 230, 220)), "items/quartz.png")
    save(simple(["....xx..........", "...xgxx.........", "....xxxx........", ".....xxxx.......", "......xxxx......",
                 ".......xxxx.....", "........xxxx....", ".........xx....."], (110, 180, 170)),
         "items/prismarine_shard.png")
    save(simple(["....x...x.......", "...xgx.xgx......", "....x...x...x...", ".......x...xgx..", "......xgx...x...",
                 "..x....x.....x..", ".xgx........xgx.", "..x..........x.."], (180, 236, 220)),
         "items/prismarine_crystals.png")
    save(simple([".....xxxxxx.....", "....xxgxxxxx....", "...xxxxxxxxxx...", "...xxxxxxxxxx...", "...xxxxxxxxxx...",
                 "....xxxxxxxx....", ".....xxxxxx....."], (110, 200, 90)), "items/slimeball.png")
    save(simple([".....xxxxxx.....", "....xxgxxxxx....", "...xxxxxxxxxx...", "...xxxxxxxxxx...", "...xxxxxxxxxx...",
                 "....xxxxxxxx....", ".....xxxxxx....."], (230, 110, 40)), "items/magma_cream.png")
    save(simple(["......xxxx......", "....xxxxxxxx....", "...xxgxxxxxxx...", "...xxxxxxxxxx...", "...xxxxxxxxxx...",
                 "....xxxxxxxx....", "......xxxx......"], (40, 160, 120)), "items/ender_eye.png")
    ee = __import__("PIL.Image", fromlist=["Image"])
    save(simple([".....xxxxxx.....", "....xxxxxxxx....", "...xxgxxxxxxx...", "...xxxxxxxxxx...", "....xxxxxxxx....",
                 ".....xxxxxx....."], (150, 40, 50)), "items/spider_eye.png")
    save(simple([".....xxxxxx.....", "....xxxxxxxx....", "...xxgxxxxxxx...", "...xxxxxxxxxx...", "....xxxxxxxx....",
                 ".....xxxxxx....."], (120, 60, 90)), "items/spider_eye_fermented.png")
    save(simple(["...xxxxxxxxxx...", "..xxgxxxxxxxxx..", "..xxxxxxxxxxxx..", "..xxxxxxxxxxxx..", "..xxxxxxxxxxxx..",
                 "...xxxxxxxxxx..."], (150, 96, 60)), "items/leather.png")
    save(simple(["...xxxxxxxxxx...", "..xxgxxxxxxxxx..", "..xxxxxxxxxxxx..", "..xxxxxxxxxxxx..", "...xxxxxxxxxx..."],
                (200, 170, 130)), "items/rabbit_hide.png")
    save(simple(["......xxx.......", ".....xxgxx......", ".....xxxxx......", "......xxx.......", "......xxx.......",
                 ".....xxxxx......", "....xx.x.xx....."], (200, 170, 120)), "items/rabbit_foot.png")
    save(simple([".......x........", "......xxx.......", "..x..xxgxx..x...", "...xxxxxxxxx....", "....xxxxxxx.....",
                 "...xxxxxxxxx....", "..x..xxxxx..x...", "......xxx.......", ".......x........"], (236, 240, 246)),
         "items/nether_star.png")
    save(simple(["...........xx...", "..........xgx...", ".........xxx....", "........xxx.....", ".......xxx......",
                 "......xxx.......", ".....xxx........", "....xxx.........", "...xx..........."], (230, 230, 236)),
         "items/string.png")
    save(rod((240, 180, 50), glow=True), "items/blaze_rod.png")
    save(simple(["......x.....x...", ".....xgx...xgx..", "......xxx.xxx...", ".......xxxxx....", "........xxx.....",
                 ".......x...x....", "......x.....x..."], (150, 40, 50)), "items/nether_wart.png")

    # --- food
    save(simple(["......xxxx......", ".....xxgxxx.....", ".....xxxxxx.....", "......xxxx......", "......xxxx......",
                 ".......xx......."], (230, 130, 40)), "items/carrot.png")
    save(simple([".....xxxxx......", "....xxgxxxx.....", "...xxxxxxxxx....", "...xxxxxxxxx....", "....xxxxxxx.....",
                 ".....xxxxx......"], (200, 164, 90)), "items/potato.png")
    save(simple([".....xxxxx......", "....xxgxxxx.....", "...xxxxxxxxx....", "...xxxxxxxxx....", "....xxxxxxx.....",
                 ".....xxxxx......"], (220, 170, 70)), "items/potato_baked.png")
    save(simple([".....xxxxx......", "....xxgxxxx.....", "...xxxxxxxxx....", "...xxxxxxxxx....", "....xxxxxxx.....",
                 ".....xxxxx......"], (170, 190, 90)), "items/potato_poisonous.png")
    save(simple(["......xxxx......", "....xxgxxxxx....", "...xxxxxxxxxx...", "...xxdxxdxxxx...", "....xxxxxxxx....",
                 "......xxxx......"], (190, 130, 70)), "items/cookie.png")
    melon = simple(["..xxxxxxxxxxxx..", "...xxxxxxxxxx...", "....xxxxxxxx....", ".....xxxxxx.....", "......xxxx......",
                    ".......xx......."], (226, 60, 60))
    mpx = melon.load()
    for (x, y) in ((5, 6), (8, 6), (11, 6), (7, 8), (9, 8)):
        mpx[x, y] = (30, 20, 20, 255)
    for x in range(2, 14):
        if mpx[x, 5][3]:
            mpx[x, 5] = (100, 170, 60, 255)
    save(melon, "items/melon.png")
    glist = melon.copy()
    gp = glist.load()
    for (x, y) in ((4, 6), (10, 7), (6, 9), (9, 5)):
        gp[x, y] = (255, 230, 90, 255)
    save(glist, "items/melon_speckled.png")
    pie = simple(["....xxxxxxxx....", "...xxgxxxxxxx...", "..xxxxxxxxxxxx..", "..xxxxxxxxxxxx..", "..dddddddddddd.."],
                 (220, 150, 70))
    save(pie, "items/pumpkin_pie.png")
    bowl_mask = ["..xxxxxxxxxxxx..", "..xxxxxxxxxxxx..", "...xxxxxxxxxx...", "....xxxxxxxx....", ".....dddddd....."]
    save(simple(bowl_mask, (150, 104, 60)), "items/bowl.png")
    for name, soup in (("mushroom_stew", (200, 150, 110)), ("rabbit_stew", (190, 120, 70))):
        img = simple(bowl_mask, (150, 104, 60))
        sp = img.load()
        for x in range(3, 13):
            sp[x, 5] = (*shade(soup, 0.2), 255)
        save(img, f"items/{name}.png")
    save(simple(["....xxxxxxx.....", "...xxgxxxxxx....", "...xxxxxxxxx....", "...LLLLLLLLL....", "...xxxxxxxxx....",
                 "...dddddddddd..."], (246, 240, 236)), "items/cake.png")

    # --- tools / misc items
    save(rod(HANDLE), "items/carrot_on_a_stick.png") if False else None
    cos = rod(HANDLE)
    cp = cos.load()
    for (x, y), c in (((13, 12), (230, 230, 236)), ((13, 13), (230, 130, 40)), ((12, 14), (230, 130, 40)),
                      ((13, 14), (100, 170, 60))):
        cp[x, y] = (*c, 255)
    save(cos, "items/carrot_on_a_stick.png")
    save(compass_frames()[0], "items/compass.png")
    save_anim(compass_frames(), "items/compass.png", frametime=1)
    save_anim(clock_frames(), "items/clock.png", frametime=1)
    # the game picks clock/compass frames itself: replace the frametime with the vanilla-style empty animation block
    from lib import TEX
    for n in ("compass", "clock"):
        (TEX / f"items/{n}.png.mcmeta").write_text('{\n  "animation": {}\n}\n')
    save(simple(["..xxxxxxxxxxxx..", "..xLLLLLLLLLLx..", "..xLLLLLLLLLLx..", "..xLLLLLLLLLLx..", "..xLLLLLLLLLLx..",
                 "..xLLLLLLLLLLx..", "..xxxxxxxxxxxx.."], (150, 110, 70)), "items/painting.png")
    pt = new()
    ifr = simple(["..xxxxxxxxxxxx..", "..xDDDDDDDDDDx..", "..xDDDDDDDDDDx..", "..xDDDDDDDDDDx..", "..xDDDDDDDDDDx..",
                  "..xDDDDDDDDDDx..", "..xxxxxxxxxxxx.."], (176, 130, 80))
    save(ifr, "items/item_frame.png")
    painting = simple(["..xxxxxxxxxxxx..", "..xLLLLLLLLLLx..", "..xLLLLLLLLLLx..", "..xLLLLLLLLLLx..", "..xLLLLLLLLLLx..",
                       "..xLLLLLLLLLLx..", "..xxxxxxxxxxxx.."], (150, 110, 70))
    pp = painting.load()
    for y in range(5, 10):
        for x in range(3, 13):
            pp[x, y] = (*((90, 170, 230) if y < 8 else (90, 160, 70)), 255)
    pp[10, 6] = (250, 220, 90, 255)
    save(painting, "items/painting.png")
    save(simple(["...xxxxxxxxxx...", "...xLLLLLLLLx...", "...xxxxxxxxxx...", "...dxxxxxxxxd...", "....xxxxxxxx....",
                 ".....xxxxxx.....", ".....xx..xx....."], (74, 76, 86)), "items/cauldron.png")
    save(simple(["..xxxxxxxxxxxx..", "..xLLLLLLLLLLx..", "..xxxxxxxxxxxx..", "...xxxxxxxxxx...", ".....xxxxxx.....",
                 "......xxxx......", ".......xx......."], (74, 76, 86)), "items/hopper.png")
    save(simple([".......xx.......", ".......xx.......", "..xx...xx...xx..", "..xxxxxxxxxxxx..", "..x....xx....x..",
                 ".xxx..xxxx..xxx.", ".xxx..xxxx..xxx.", "....xxxxxxxx...."], (190, 170, 120)), "items/brewing_stand.png")
    save(simple(["....xxxxxxxx....", "....xxxxxxxx....", "...xxxxxxxxxx...", "...xLLLLLLLLx...", "...xxxxxxxxxx...",
                 "...xxxxxxxxxx...", "....xxxxxxxx...."], (160, 82, 56)), "items/flower_pot.png")
    save(simple(["......x.........", ".....xgx........", "....xxxxx.......", "...x.xxx.x......", ".....xxx........",
                 ".....xxx........", ".....xxx........", ".....xxx........", "....xxxxx......."], (150, 104, 60)),
         "items/reeds.png")
    sign = simple(["..xxxxxxxxxxxx..", "..xxgxxxxxxxxx..", "..xLLLLLLLLLLx..", "..xxxxxxxxxxxx..", "..xLLLLLLLLLLx..",
                   "..xxxxxxxxxxxx..", ".......xx.......", ".......xx.......", ".......dd......."], (176, 136, 82))
    save(sign, "items/sign.png")
    save(simple(["...xxx.....xxx..", "...xgx.....xgx..", "...xxxxxxxxxxx..", "...xxxxxxxxxxx..", "....xxxxxxxxx...",
                 ".....dddddddd..."], (150, 110, 70)), "items/saddle.png")
    lead = new()
    lp = lead.load()
    for t in range(60):
        a = t / 60 * 2 * math.pi * 1.6
        r = 2.0 + t / 60 * 4.5
        x, y = round(7.5 + math.cos(a) * r), round(7.5 + math.sin(a) * r)
        if 0 <= x < 16 and 0 <= y < 16:
            lp[x, y] = (*((190, 160, 110) if t % 4 else (150, 120, 80)), 255)
    save(outline(lead, INK), "items/lead.png")
    save(simple(["...xxxxxxxxxx...", "..xxgxxxxxxxxx..", "..xxxxxxxxxxxx..", "...xxxxxxxxxx...", "....dddddddd...."],
                (176, 136, 82)), "items/boat.png")
    stand = new()
    sp_ = stand.load()
    w = ramp((176, 136, 82), (-0.4, 0.0, 0.3))
    for y in range(2, 14):
        sp_[7, y] = (*w[2], 255)
        sp_[8, y] = (*w[1], 255)
    for x in range(4, 12):
        sp_[x, 5] = (*w[2], 255)
        sp_[x, 13] = (*w[1], 255)
    for y in range(2, 5):
        for x in range(6, 10):
            sp_[x, y] = (*w[2], 255)
    for (x, y) in ((6, 9), (9, 9), (6, 10), (9, 10)):
        sp_[x, y] = (*w[1], 255)
    save(outline(stand, INK), "items/wooden_armorstand.png")
    save(simple(["......xxxx......", ".....xxgxxx.....", ".....xxxxxx.....", "......xxxx......", ".......xx.......",
                 "......xxxx......", ".....xxxxxx....."], (240, 240, 240)), "items/fireworks_charge.png")
    over = new()
    op = over.load()
    for (x, y) in ((6, 4), (7, 4), (8, 4), (9, 4), (6, 5), (9, 5), (7, 6), (8, 6)):
        pass
    for y in range(16):
        for x in range(16):
            if (x - 7.5) ** 2 + (y - 6.5) ** 2 < 5:
                op[x, y] = (210, 210, 210, 255)
    save(over, "items/fireworks_charge_overlay.png")
    fw = new()
    fwp = fw.load()
    paper_c = ramp((214, 60, 60), (-0.4, 0.0, 0.3))
    for y in range(5, 15):
        for x in range(6, 10):
            fwp[x, y] = (*paper_c[1 if x > 7 else 2], 255)
    for x in range(6, 10):
        fwp[x, 8] = (236, 236, 236, 255)
    for y in range(1, 5):
        fwp[8, y] = (190, 160, 110, 255)
    save(outline(fw, INK), "items/fireworks.png")
    xp = new()
    xpp = xp.load()
    from items import potion
    b, _, _ = potion()
    xp.alpha_composite(b)
    xpp = xp.load()
    for y in range(8, 14):
        for x in range(5, 11):
            if xpp[x, y][3] == 0:
                xpp[x, y] = (*((150, 250, 90) if (x + y) % 3 else (230, 255, 160)), 255)
    save(xp, "items/experience_bottle.png")
    save(simple([".....xxxxxx.....", "....xxgxxxxx....", "....xxxxxxxx....", ".....xxxxxx.....", "......xxxx......",
                 "......xxxx......", "......xxxx......", ".....xxxxxx....."], (196, 140, 200)), "items/spawn_egg.png") if False else None
    egg = new()
    ep = egg.load()
    for y in range(16):
        for x in range(16):
            dx, dy = (x - 7.5) / 4.5, (y - 8.5) / (5.5 if y > 8 else 6.2)
            if dx * dx + dy * dy <= 1:
                t = math.hypot(dx + 0.4, dy + 0.4)
                v = 236 if t < 0.5 else 206 if t < 0.95 else 170
                ep[x, y] = (v, v, v, 255)
    save(outline(egg, (40, 40, 48)), "items/spawn_egg.png")
    spots = new()
    sp2 = spots.load()
    for (x, y) in ((6, 5), (7, 5), (9, 8), (10, 8), (10, 9), (5, 10), (6, 10), (8, 12), (9, 12)):
        sp2[x, y] = (220, 220, 220, 255)
    save(spots, "items/spawn_egg_overlay.png")
    save(simple(["....xxxxxxxx....", "...xxxxxxxxxx...", "...xxxxxxxxxx...", "..xxxxxxxxxxxx..", "..xxxxxxxxxxxx..",
                 "..xxxxxxxxxxxx..", ".....xxxxxx....."], (110, 70, 40)), "items/quiver.png")
    bb = new()
    bbp = bb.load()
    for y in range(1, 15):
        for x in range(4, 12):
            bbp[x, y] = (*((236, 236, 240) if x in (4, 5) else (210, 210, 214) if x < 11 else (176, 176, 182)), 255)
    for x in range(2, 14):
        bbp[x, 1] = (150, 110, 70, 255)
    save(outline(bb, INK), "items/banner_base.png")
    bo = new()
    bop = bo.load()
    for y in range(2, 15):
        for x in range(6, 12):
            bop[x, y] = (200, 200, 200, 255)
    save(bo, "items/banner_overlay.png")
    br = new()
    brp = br.load()
    for i in range(2, 14):
        brp[i, i] = (226, 40, 40, 255)
        brp[15 - i, i] = (226, 40, 40, 255)
        brp[i + 1 if i < 15 else i, i] = (226, 40, 40, 255)
        brp[14 - i, i] = (226, 40, 40, 255)
    save(br, "items/barrier.png")
    rp = simple(["......xxxxx.....", ".....xxgxxxx....", "....xxxxxxxxx...", "....xxxxxxxxx...", ".....xxxxxxx....",
                 "......xxxxx....."], (226, 40, 40))
    save(rp, "items/ruby.png")
    save(simple([".......x........", "......xxx.......", ".....xxgxx......", "......xxx.......", ".......x........",
                 ".......x........", "......xxx......."], (216, 196, 140)), "items/wheat.png") if False else None
    wheat = new()
    wp_ = wheat.load()
    g = ramp((214, 178, 74), (-0.4, 0.0, 0.3))
    for k, x0 in enumerate((5, 8, 11)):
        for y in range(3 + k % 2, 15):
            wp_[x0 - (14 - y) // 6 * (1 if x0 < 8 else -1 if x0 > 8 else 0), y] = (*g[1], 255)
        for y in range(2 + k % 2, 7 + k % 2):
            xx = x0 - (14 - y) // 6 * (1 if x0 < 8 else -1 if x0 > 8 else 0)
            wp_[xx, y] = (*g[2], 255)
            if xx + 1 < 16:
                wp_[xx + 1, y] = (*g[0], 255)
    save(outline(wheat, ink_for((214, 178, 74))), "items/wheat.png")

    # repeater / comparator: the same stone slab with redstone torches (2 vs 3)
    for name, torches in (("repeater", ((4, 6), (11, 6))), ("comparator", ((4, 5), (11, 5), (7, 9)))):
        img = simple(["................", "..xxxxxxxxxxxx..", ".xxgxxxxxxxxxxx.", ".xxxxxxxxxxxxxx.", ".dddddddddddddd."],
                     (160, 162, 168))
        ip = img.load()
        for (tx, ty) in torches:
            for k in range(3):
                ip[tx, ty + k] = (150, 110, 70, 255)
            ip[tx, ty - 1] = (240, 60, 50, 255)
            ip[tx, ty - 2] = (255, 140, 120, 255)
        save(img, f"items/{name}.png")

    # empty armor slots: light outlines of each armor piece (shown in empty inventory armor slots)
    from items import ARMOR_MASKS
    for piece, mask in ARMOR_MASKS.items():
        img = new()
        ip = img.load()
        for y, row in enumerate(mask):
            for x, ch in enumerate(row):
                if ch != ".":
                    edge = any(not (0 <= x + dx < 16 and 0 <= y + dy < 16) or mask[y + dy][x + dx] == "."
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if edge:
                        ip[x, y] = (255, 255, 255, 70)
        save(img, f"items/empty_armor_slot_{piece}.png")

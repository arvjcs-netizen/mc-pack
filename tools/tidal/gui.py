"""HUD (gui/icons.png), hotbar + buttons (gui/widgets.png), and the enchantment glint."""
import math

from lib import mix, new, ramp, save, shade, sprite

AQUA = (52, 200, 210)


HEART = [
    ".ooo.ooo.",
    "ohhfofffo",
    "ohfffffso",
    "offfffsso",
    ".offffso.",
    "..offso..",
    "...oso...",
    "....o....",
    ".........",
]


def heart(fill, flash=False, half=False, container=False, blink=False, hardcore=False):
    if container:
        cols = {"o": (236, 240, 248) if blink else (18, 18, 24), "h": (40, 40, 48), "f": (40, 40, 48), "s": (40, 40, 48)}
    else:
        r = ramp(fill, (-0.35, 0.0, 0.5))
        if flash:
            r = [mix(c, (255, 255, 255), 0.45) for c in r]
        cols = {"o": (18, 18, 24), "h": r[2], "f": r[1], "s": r[0]}
    img = sprite(HEART, cols)
    px = img.load()
    if half and not container:
        for y in range(9):
            for x in range(5, 9):
                px[x, y] = (0, 0, 0, 0)
    if hardcore and not container:
        px[2, 2] = (255, 255, 255, 255)
    return img


ARMOR_ICON = [
    ".ooo.ooo.",
    "offfofffo",
    "offfffffo",
    ".offfffo.",
    ".offfffo.",
    ".offfffo.",
    ".offfffo.",
    "..ooooo..",
    ".........",
]

DRUMSTICK = [
    "....ooo..",
    "...ommmo.",
    "..ommmmmo",
    "..ommmmso",
    "..ommmsso",
    ".oommsso.",
    "obo.ooo..",
    "obbo.....",
    ".oo......",
]

BUBBLE = [
    "..ooooo..",
    ".obbbbbo.",
    "obwbbbbbo",
    "obwbbbbbo",
    "obbbbbbbo",
    "obbbbbbbo",
    ".obbbbbo.",
    "..ooooo..",
    ".........",
]


def blit(dst, src, x, y):
    dst.alpha_composite(src, (x, y))


def bar(w, h, fill, empty=False):
    img = new(w, h)
    px = img.load()
    r = ramp(fill, (-0.45, 0.0, 0.4))
    for y in range(h):
        for x in range(w):
            if y in (0, h - 1) or x in (0, w - 1):
                px[x, y] = (14, 14, 20, 255)
            elif empty:
                px[x, y] = (38, 40, 48, 255)
            else:
                px[x, y] = (*(r[2] if y == 1 else r[0] if y == h - 2 else r[1]), 255)
    return img


def icons():
    img = new(256, 256)
    px = img.load()
    # crosshair: thin plus with an open center (game draws it inverted, so white)
    for i in range(16):
        if 3 <= i <= 5 or 9 <= i <= 11:
            px[i, 7] = (255, 255, 255, 255)
            px[7, i] = (255, 255, 255, 255)
    px[7, 7] = (255, 255, 255, 255)

    kinds = {0: AQUA, 36: (110, 170, 40), 72: (60, 56, 64)}   # normal, poison, wither
    for v, hc in ((0, False), (45, True)):
        blit(img, heart(None, container=True), 16, v)
        blit(img, heart(None, container=True, blink=True), 25, v)
        for off, col in kinds.items():
            u = 16 + off
            blit(img, heart(col, hardcore=hc), u + 36, v)
            blit(img, heart(col, half=True, hardcore=hc), u + 45, v)
            blit(img, heart(col, flash=True, hardcore=hc), u + 54, v)
            blit(img, heart(col, flash=True, half=True, hardcore=hc), u + 63, v)
        blit(img, heart((250, 200, 50), hardcore=hc), 160, v)          # absorption
        blit(img, heart((250, 200, 50), half=True, hardcore=hc), 169, v)

    # armor (y=9): empty, half, full
    steel = ramp((200, 206, 218), (-0.4, 0.0, 0.4))
    blit(img, sprite(ARMOR_ICON, {"o": (18, 18, 24), "f": (40, 40, 48)}), 16, 9)
    full = sprite(ARMOR_ICON, {"o": (18, 18, 24), "f": steel[1]})
    half = full.copy()
    hp = half.load()
    for y in range(9):
        for x in range(5, 9):
            if hp[x, y][3] and ARMOR_ICON[y][x] == "f":
                hp[x, y] = (40, 40, 48, 255)
    blit(img, half, 25, 9)
    blit(img, full, 34, 9)
    # mount hearts (y=9)
    blit(img, heart(None, container=True), 52, 9)
    blit(img, heart((236, 120, 50)), 88, 9)
    blit(img, heart((236, 120, 50), half=True), 97, 9)

    # air bubbles (y=18)
    blit(img, sprite(BUBBLE, {"o": (20, 60, 120), "b": (90, 170, 240), "w": (230, 246, 255)}), 16, 18)
    pop = sprite(BUBBLE, {"o": (20, 60, 120), "w": (230, 246, 255)})
    blit(img, pop, 25, 18)

    # hunger (y=27): container, hunger-effect container, full/half, hunger-effect full/half
    meat = ramp((196, 112, 64), (-0.35, 0.0, 0.4))
    sick = ramp((120, 150, 60), (-0.35, 0.0, 0.4))

    def stick(c, half=False, container=False):
        cols = {"o": (18, 18, 24), "b": (236, 230, 220)}
        cols.update({"m": (40, 40, 48), "s": (40, 40, 48)} if container else {"m": c[1], "s": c[0]})
        s = sprite(DRUMSTICK, cols)
        if half and not container:
            p = s.load()
            for y in range(9):
                for x in range(0, 5):
                    p[x, y] = (0, 0, 0, 0)
        return s

    blit(img, stick(None, container=True), 16, 27)
    blit(img, stick(None, container=True), 133, 27)
    blit(img, stick(meat), 52, 27)
    blit(img, stick(meat, half=True), 61, 27)
    blit(img, stick(sick), 88, 27)
    blit(img, stick(sick, half=True), 97, 27)

    # bars: xp (64/69), boss (74/79), horse jump (84/89)
    blit(img, bar(182, 5, AQUA, empty=True), 0, 64)
    blit(img, bar(182, 5, (90, 220, 120)), 0, 69)
    blit(img, bar(182, 5, AQUA, empty=True), 0, 74)
    blit(img, bar(182, 5, (200, 60, 200)), 0, 79)
    blit(img, bar(182, 5, AQUA, empty=True), 0, 84)
    blit(img, bar(182, 5, (240, 200, 60)), 0, 89)

    # ping bars for the tab list: (0, 176 + k*8), k=0 best .. 4 worst, 5 = no connection
    good, off = (70, 220, 200), (50, 54, 64)
    for k in range(6):
        y0 = 176 + k * 8
        for b in range(5):
            hgt = 2 + b
            lit = k < 5 and b < 5 - k
            c = good if lit else off
            if k == 5:
                c = off
            for y in range(8 - hgt, 8):
                px[b * 2, y0 + y] = (*c, 255)
                if k < 5:
                    px[10 + b * 2, y0 + y] = (*(good if (b + k) % 2 == 0 else off), 255)
        if k == 5:
            for i in range(5):
                px[2 + i, y0 + 1 + i] = (220, 60, 60, 255)
                px[6 - i, y0 + 1 + i] = (220, 60, 60, 255)
    save(img, "gui/icons.png")


def panel(w, h, fill, border, hi, lo):
    img = new(w, h)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                c = border
            elif y == 1:
                c = hi
            elif y == h - 2:
                c = lo
            else:
                c = fill
            px[x, y] = (*c[:3], c[3] if len(c) > 3 else 255)
    return img


def widgets():
    img = new(256, 256)
    # hotbar: 182x22, nine 20px slots
    hb = new(182, 22)
    hp = hb.load()
    for y in range(22):
        for x in range(182):
            edge = x in (0, 181) or y in (0, 21)
            sep = (x - 1) % 20 == 0 and 0 < x < 181
            if edge:
                hp[x, y] = (12, 14, 20, 230)
            elif sep:
                hp[x, y] = (26, 30, 40, 220)
            else:
                hp[x, y] = (34, 40, 54, 170) if y > 1 else (60, 70, 92, 200)
    img.alpha_composite(hb, (0, 0))
    # selected slot: 24x24 frame in Tidal aqua
    sel = new(24, 24)
    sp = sel.load()
    for y in range(24):
        for x in range(24):
            if x in (0, 23) or y in (0, 23):
                sp[x, y] = (16, 20, 28, 255)
            elif x in (1, 22) or y in (1, 22):
                sp[x, y] = (*AQUA, 255)
            elif x in (2, 21) or y in (2, 21):
                sp[x, y] = (*shade(AQUA, -0.4), 255)
    img.alpha_composite(sel, (0, 22))
    # buttons 200x20: disabled, normal, hover. Uniform horizontally so any width works.
    img.alpha_composite(panel(200, 20, (40, 42, 48), (10, 10, 14), (56, 58, 64), (30, 32, 36)), (0, 46))
    img.alpha_composite(panel(200, 20, (44, 58, 82), (10, 12, 18), (70, 90, 124), (32, 42, 60)), (0, 66))
    img.alpha_composite(panel(200, 20, (50, 112, 170), (220, 240, 255), (92, 160, 214), (36, 80, 128)), (0, 86))
    # language button (globe) normal/hover, and lock buttons
    for i, hover in enumerate((False, True)):
        base = panel(20, 20, (50, 112, 170) if hover else (44, 58, 82), (220, 240, 255) if hover else (10, 12, 18),
                     (70, 90, 124), (32, 42, 60))
        globe = sprite([
            "..ooooo..",
            ".oggbbgo.",
            "obbggbbbo",
            "obbbggbbo",
            "oggbbbbgo",
            "obgggbbbo",
            "obbbgggbo",
            ".obbbbbo.",
            "..ooooo..",
        ], {"o": (16, 30, 60), "b": (70, 150, 230), "g": (90, 200, 110)})
        base.alpha_composite(globe.resize((9, 9)), (5, 5))
        img.alpha_composite(base, (0, 106 + i * 20))
    lock_closed = ["..ooo..", ".o...o.", ".o...o.", "ooooooo", "oyyyyyo", "oyyoyyo", "oyyyyyo", "ooooooo"]
    lock_open = ["..ooo..", ".o...o.", ".....o.", "ooooooo", "oyyyyyo", "oyyoyyo", "oyyyyyo", "ooooooo"]
    for col, shape in enumerate((lock_closed, lock_open)):
        for row, state in enumerate(("normal", "hover", "disabled")):
            fill = {"normal": (44, 58, 82), "hover": (50, 112, 170), "disabled": (40, 42, 48)}[state]
            border = (220, 240, 255) if state == "hover" else (10, 12, 18)
            b = panel(20, 20, fill, border, (70, 90, 124), (32, 42, 60))
            b.alpha_composite(sprite(shape, {"o": (20, 20, 26), "y": (230, 200, 70)}), (6, 6))
            img.alpha_composite(b, (col * 20, 146 + row * 20))
    save(img, "gui/widgets.png")


def glint():
    """Enchantment shimmer (added on top of items, so dark = invisible). Soft blue diagonal bands."""
    img = new(64, 64)
    px = img.load()
    for y in range(64):
        for x in range(64):
            v = 0.5 + 0.5 * math.sin(2 * math.pi * (x + y) / 32) * math.sin(2 * math.pi * (x - y) / 64 + 1.0)
            v = max(0.0, v) ** 1.6
            px[x, y] = (round(50 + 70 * v), round(80 + 110 * v), round(150 + 105 * v), 255)
    save(img, "misc/enchanted_item_glint.png")


def generate():
    icons()
    widgets()
    glint()

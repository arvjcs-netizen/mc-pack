"""Container screens and other GUI textures. Panels are a light frosted blue (the game draws container titles in
dark gray, so panels must stay light). Panel outlines and slot positions come from the vanilla layout (geometry
only: which pixels are panel, where the 18x18 slots sit); everything is drawn here in Tidal colors."""
import math

from PIL import Image

from lib import layout_gray, layout_mask, line, mix, new, ramp, rect, save, save_meta, shade, sprite

PANEL = (198, 208, 222)
HI = (244, 248, 255)
SH = (122, 136, 162)
EDGE = (16, 20, 30)
SLOT_IN = (132, 144, 168)
SLOT_TL = (52, 60, 82)
SLOT_BR = (244, 248, 255)
DARK = (22, 26, 38)
AQUA = (52, 200, 210)
BLUE = (44, 120, 214)


# ---------------------------------------------------------------- geometry from the vanilla layout
def find_slots(rel):
    """Rectangles (x, y, w, h) of every slot frame: a dark top-left border around a flat gray interior."""
    im = layout_gray(rel)
    p = im.load()
    W, H = im.size

    def g(x, y):
        if not (0 <= x < W and 0 <= y < H):
            return None
        r, gg, b, a = p[x, y]
        return r if a and r == gg == b else None

    out = []
    seen = set()
    for y in range(H - 1):
        for x in range(W - 1):
            if g(x, y) == 55 and g(x + 1, y + 1) == 139 and g(x + 1, y) == 55 and g(x, y + 1) == 55:
                w = 0
                while g(x + 1 + w, y + 1) == 139:
                    w += 1
                h = 0
                while g(x + 1, y + 1 + h) == 139:
                    h += 1
                if w >= 16 and h >= 16 and (x, y) not in seen:
                    seen.add((x, y))
                    out.append((x, y, w + 2, h + 2))
    return out


def panel_from(rel, w, h, img=None):
    """Draw a Tidal panel on the vanilla panel's footprint (0,0,w,h)."""
    m = layout_mask(rel)
    img = img or new(256, 256)
    p = img.load()

    def inside(x, y):
        return 0 <= x < w and 0 <= y < h and m[y][x]

    for y in range(h):
        for x in range(w):
            if not inside(x, y):
                continue
            if not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c = EDGE
            elif not inside(x - 1, y) or not inside(x, y - 1) or not inside(x - 2, y) or not inside(x, y - 2) \
                    or not inside(x - 1, y - 1):
                c = HI
            elif not inside(x + 1, y) or not inside(x, y + 1) or not inside(x + 2, y) or not inside(x, y + 2) \
                    or not inside(x + 1, y + 1):
                c = SH
            else:
                c = PANEL
            p[x, y] = (*c, 255)
    return img


def slot(img, x, y, w=18, h=18):
    p = img.load()
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if xx == x or yy == y:
                c = SLOT_TL
            elif xx == x + w - 1 or yy == y + h - 1:
                c = SLOT_BR
            else:
                c = SLOT_IN
            p[xx, yy] = (*c, 255)
    if w > 18:   # big result slot: an inner bevel
        for i in range(1, w - 1):
            p[x + i, y + 1] = (*shade(SLOT_IN, -0.3), 255)
            p[x + 1, y + i] = (*shade(SLOT_IN, -0.3), 255)


def slots_from(rel, img):
    for (x, y, w, h) in find_slots(rel):
        slot(img, x, y, w, h)
    return img


def recess(img, x, y, w, h, fill=DARK):
    p = img.load()
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if xx == x or yy == y:
                c = SLOT_TL
            elif xx == x + w - 1 or yy == y + h - 1:
                c = SLOT_BR
            else:
                c = fill
            p[xx, yy] = (*c, 255)


def arrow_right(img, x, y, w=22, h=15, color=SH, fill=None):
    """Arrow pointing right inside a (w x h) box."""
    p = img.load()
    mid = y + h // 2
    shaft_end = x + w - h // 2 - 1
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            dy = abs(yy - mid)
            in_shaft = xx <= shaft_end and dy <= 2
            in_head = xx > shaft_end - 1 and (xx - (shaft_end - 1)) + dy <= h // 2 + 1
            if in_shaft or in_head:
                p[xx, yy] = (*(fill or color), 255)


def arrow_down(img, x, y, w=9, h=28, color=SH):
    p = img.load()
    cx = x + w // 2
    head = y + h - w // 2 - 1
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            dx = abs(xx - cx)
            if (yy <= head and dx <= 1) or (yy >= head and (yy - head) + dx <= w // 2):
                p[xx, yy] = (*color, 255)


def flame(img, x, y, lit, size=14):
    p = img.load()
    for yy in range(size):
        for xx in range(size):
            dx = (xx - (size - 1) / 2) / (size / 2)
            dy = (yy - size * 0.62) / (size * 0.42)
            r = dx * dx + dy * dy * (0.6 if dy < 0 else 1.0)
            tongue = abs(dx) < 0.35 * (1 - (size * 0.62 - yy) / (size * 0.62)) + 0.08 and yy < size * 0.62
            if r < 1.0 or tongue:
                if lit:
                    heat = 1 - yy / size
                    c = mix((250, 110, 30), (255, 226, 110), max(0, min(1, 1 - r)))
                else:
                    c = SH
                p[x + xx, y + yy] = (*c, 255)


def text_box(img, x, y, w, h, enabled=True):
    recess(img, x, y, w, h, fill=DARK if enabled else (70, 78, 96))


def x_mark(img, x, y, w=28, h=21):
    p = img.load()
    for t in range(14):
        for dx in (0, 1, 2):
            for (xx, yy) in ((x + 7 + t + dx, y + 3 + t), (x + 20 - t + dx, y + 3 + t)):
                if x <= xx < x + w and y <= yy < y + h:
                    p[xx, yy] = (226, 50, 50, 255)


# ---------------------------------------------------------------- containers
def basic(rel, w, h):
    img = panel_from(rel, w, h)
    return slots_from(rel, img)


def inventory():
    rel = "gui/container/inventory.png"
    img = basic(rel, 176, 166)
    recess(img, 25, 7, 52, 72)
    arrow_right(img, 122, 36, 18, 15)
    # potion effect background (0,166) 120x32 and the status-effect icons at (0,198), 18x18 each
    eff = panel_from_rect(120, 32)
    img.alpha_composite(eff, (0, 166))
    for i, drawer in enumerate(EFFECT_ICONS):
        icon = new(18, 18)
        if drawer:
            drawer(icon)
        img.alpha_composite(icon, ((i % 8) * 18, 198 + (i // 8) * 18))
    return img


def panel_from_rect(w, h):
    img = new(w, h)
    p = img.load()
    for y in range(h):
        for x in range(w):
            corner = (x in (0, w - 1)) and (y in (0, h - 1))
            if corner:
                continue
            if x in (0, w - 1) or y in (0, h - 1):
                c = EDGE
            elif x in (1, 2) or y in (1, 2):
                c = HI
            elif x in (w - 2, w - 3) or y in (h - 2, h - 3):
                c = SH
            else:
                c = PANEL
            p[x, y] = (*c, 255)
    return img


# status-effect icons, drawn on an 18x18 cell. Index = column + 8 * row (1.8 Potion icon indices).
def _icon(rows, cols):
    def draw(img):
        s = sprite(rows, cols)
        img.alpha_composite(s, ((18 - s.size[0]) // 2, (18 - s.size[1]) // 2))
    return draw


O = (22, 20, 28)
_BOOT = ["..ooo...", ".obbo...", ".obbo...", ".obbooo.", "obbbbbbo", "obbbbbbo", ".oooooo."]
_ARROW_UP = ["...o...", "..obo..", ".obbbo.", "oobbboo", "..obo..", "..obo..", "..ooo.."]
_FIST = [".oooooo.", "obbbbbbo", "obbbbbbo", "obbbbbbo", ".obbbbo.", "..oooo.."]
_HEART = [".oo.oo.", "obboboo", "obbbbbo", ".obbbo.", "..obo..", "...o..."]
_SHIELD = ["ooooooo", "obbbbbo", "obbbbbo", "obbbbbo", ".obbbo.", "..obo..", "...o..."]
_EYE = [".ooooo.", "obbbbbo", "obobobo", "obbbbbo", ".ooooo."]
_DROP = ["...o...", "..obo..", ".obbbo.", "obbbbbo", "obbbbbo", ".obbbo.", "..ooo.."]
_PICK = ["ooooooo", "obbbbbo", ".oo.oo.", "...o...", "...o...", "...o...", "...o..."]
_SKULL = [".ooooo.", "obbbbbo", "obobobo", "obbbbbo", ".obobo.", ".ooooo."]
_STAR = ["...o...", "..obo..", "oobbboo", ".obbbo.", ".ob.bo.", "oo...oo"]
_FLAME = ["...o...", "..obo..", ".obbo..", ".obbbo.", "obbbbbo", "obbbbbo", ".ooooo."]
_BUBBLE = [".ooo...", "obbbo..", "obbbo..", ".ooo.oo", ".....oo", "..oo...", "..oo..."]
_SWIRL = [".ooooo.", "o.....o", "o.ooo.o", "o.o.o.o", "o...o.o", ".oooo.o"]
_PLUS = ["..ooo..", "..obo..", "ooobooo", "obbbbbo", "ooobooo", "..obo..", "..ooo.."]


def _c(c):
    return {"o": O, "b": c}


EFFECT_ICONS = [None] * 24
for _i, _rows, _col in (
        (0, _BOOT, (110, 200, 240)),         # speed
        (1, _BOOT, (90, 100, 130)),          # slowness
        (2, _PICK, (240, 210, 60)),          # haste
        (3, _PICK, (120, 110, 90)),          # mining fatigue
        (4, _FIST, (200, 50, 50)),           # strength
        (5, _FIST, (110, 110, 120)),         # weakness
        (6, _DROP, (90, 170, 60)),           # poison
        (7, _HEART, (240, 120, 180)),        # regeneration
        (8, _EYE, (200, 210, 230)),          # invisibility
        (9, _DROP, (110, 140, 60)),          # hunger
        (10, _ARROW_UP, (120, 230, 120)),    # jump boost
        (11, _SWIRL, (150, 90, 170)),        # nausea
        (12, _EYE, (60, 80, 200)),           # night vision
        (13, _EYE, (40, 40, 48)),            # blindness
        (14, _SHIELD, (150, 160, 180)),      # resistance
        (15, _FLAME, (240, 140, 40)),        # fire resistance
        (16, _BUBBLE, (60, 140, 230)),       # water breathing
        (17, _SKULL, (60, 60, 66)),          # wither
        (18, _HEART, (250, 200, 50)),        # absorption
        (23, _PLUS, (240, 90, 90)),          # health boost
):
    EFFECT_ICONS[_i] = _icon(_rows, _c(_col))


def crafting_table():
    rel = "gui/container/crafting_table.png"
    img = basic(rel, 176, 166)
    arrow_right(img, 90, 35, 22, 15)
    return img


def furnace():
    rel = "gui/container/furnace.png"
    img = basic(rel, 176, 166)
    flame(img, 56, 36, lit=False)
    arrow_right(img, 79, 34, 24, 17)
    flame(img, 176, 0, lit=True)
    arrow_right(img, 176, 14, 24, 17, fill=(255, 255, 255))
    return img


def brewing_stand():
    rel = "gui/container/brewing_stand.png"
    img = basic(rel, 176, 166)
    p = img.load()
    for (a, b) in (((79, 30), (66, 46)), ((89, 34), (89, 52)), ((99, 30), (112, 46))):
        line(p, a, b, SH)
    arrow_down(img, 97, 16, 9, 28)
    arrow_down(img, 176, 0, 9, 28, color=(255, 255, 255))
    for k in range(5):          # bubbles: outline in the panel, filled sprite at (185,0)
        cx, cy, r = 6, 25 - k * 6, 2.4 - k * 0.25
        for yy in range(29):
            for xx in range(12):
                d = math.hypot(xx - cx, yy - cy)
                if d < r:
                    p[185 + xx, yy] = (*mix((200, 230, 255), (255, 255, 255), k / 4), 255)
                    p[65 + xx, 14 + yy] = (*SH, 255)
    return img


def enchanting_table():
    rel = "gui/container/enchanting_table.png"
    img = basic(rel, 176, 166)
    recess(img, 59, 13, 110, 59)
    for i, (y0, fill, edge) in enumerate(((166, (60, 72, 104), (120, 150, 200)), (185, (52, 56, 66), (80, 86, 98)),
                                          (204, (70, 110, 170), (200, 230, 255)))):
        b = new(108, 19)
        bp = b.load()
        for yy in range(19):
            for xx in range(108):
                c = edge if xx in (0, 107) or yy in (0, 18) else fill
                bp[xx, yy] = (*c, 255)
        img.alpha_composite(b, (0, y0))
    for l in range(3):          # level badges: 1, 2, 3 dots, enabled (y=223) and disabled (y=239)
        for y0, col in ((223, (110, 230, 140)), (239, (90, 96, 110))):
            ic = new(16, 16)
            ip = ic.load()
            for yy in range(2, 14):
                for xx in range(2, 14):
                    ip[xx, yy] = (*(shade(col, -0.5) if xx in (2, 13) or yy in (2, 13) else shade(col, -0.25)), 255)
            for k in range(l + 1):
                cx = 8 - l * 2 + k * 4
                for (dx, dy) in ((0, 0), (-1, 0), (0, -1), (-1, -1)):
                    ip[cx + dx, 8 + dy] = (*col, 255)
            img.alpha_composite(ic, (16 * l, y0))
    return img


def anvil():
    rel = "gui/container/anvil.png"
    img = basic(rel, 176, 166)
    p = img.load()
    for (x, y) in ((54, 52), (55, 51), (55, 52), (55, 53), (56, 52)):   # plus between the inputs
        p[x, y] = (*SH, 255)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if abs(dx) == 2 and abs(dy) == 2:
                continue
            if dx == 0 or dy == 0:
                p[56 + dx + 46, 52 + dy] = (*SH, 255)
    arrow_right(img, 102, 45, 22, 15)
    hammer = sprite(["oooooo....", "obbbbbo...", "obbbbbo...", "oooooooo..", "....ohho..", "....ohho..",
                     "....ohho..", "....ohho..", "....oooo.."], {"o": EDGE, "b": (150, 156, 170), "h": (130, 90, 60)})
    img.alpha_composite(hammer, (26, 18))
    text_box(img, 0, 166, 110, 16, True)
    text_box(img, 0, 182, 110, 16, False)
    x_mark(img, 176, 0)
    return img


def beacon():
    rel = "gui/container/beacon.png"
    img = panel_from(rel, 230, 219)
    slots_from(rel, img)
    p = img.load()
    for i, (fill, edge) in enumerate((((60, 72, 104), (120, 150, 200)), ((40, 120, 160), (140, 230, 255)),
                                      ((52, 56, 66), (80, 86, 98)), ((70, 110, 170), (200, 230, 255)))):
        b = new(22, 22)
        bp = b.load()
        for yy in range(22):
            for xx in range(22):
                bp[xx, yy] = (*(edge if xx in (0, 21) or yy in (0, 21) else fill), 255)
        img.alpha_composite(b, (i * 22, 219))
    check = sprite(["...........oo.", "..........obo.", ".........obo..", "oo......obo...", "obo....obo....",
                    ".obo..obo.....", "..obobo.......", "...obo........", "....o........."],
                   {"o": (20, 60, 30), "b": (110, 230, 120)})
    img.alpha_composite(check, (92, 224))
    x = new(18, 18)
    xp = x.load()
    for t in range(12):
        for d in (0, 1):
            xp[3 + t + d, 3 + t] = (230, 60, 60, 255)
            xp[14 - t + d, 3 + t] = (230, 60, 60, 255)
    img.alpha_composite(x, (112, 220))
    # pyramid level marks on the left
    for lvl in range(4):
        for k in range(lvl + 1):
            rect(p, 30 + k * 4, 30 + lvl * 25, 3, 3, BLUE)
    return img


def villager():
    rel = "gui/container/villager.png"
    img = basic(rel, 176, 166)
    for y in (24, 54):
        arrow_right(img, 86, y - 3 + 4, 22, 15)
    for i, (fill, edge) in enumerate((((60, 72, 104), (120, 150, 200)), ((70, 110, 170), (200, 230, 255)),
                                      ((52, 56, 66), (80, 86, 98)))):
        for col, flip in ((176, False), (188, True)):
            b = new(12, 19)
            bp = b.load()
            for yy in range(19):
                for xx in range(12):
                    tri = (xx - 2) <= (9 - abs(yy - 9)) * 0.9 and xx >= 2 and abs(yy - 9) <= 7
                    if flip:
                        tri = (9 - xx) <= (9 - abs(yy - 9)) * 0.9 and xx <= 9 and abs(yy - 9) <= 7
                    if tri:
                        bp[xx, yy] = (*(edge if abs(yy - 9) == 7 else fill), 255)
            img.alpha_composite(b, (col, i * 19))
    x_mark(img, 212, 0)
    return img


def horse():
    rel = "gui/container/horse.png"
    img = basic(rel, 176, 166)
    recess(img, 25, 17, 54, 54)
    grid = new(90, 54)
    for r in range(3):
        for c in range(5):
            slot(grid, c * 18, r * 18)
    img.alpha_composite(grid, (0, 166))
    s = new(18, 18)
    slot(s, 0, 0)
    img.alpha_composite(s, (0, 220))
    return img


def creative_tabs():
    img = new(256, 256)
    for col in range(6):
        for row, (selected, bottom) in enumerate(((False, False), (True, False), (False, True), (True, True))):
            t = new(28, 32)
            tp = t.load()
            for yy in range(32):
                for xx in range(28):
                    top_edge = yy == 0 if not bottom else yy == 31
                    side = xx in (0, 27)
                    if not selected and ((not bottom and yy > 29) or (bottom and yy < 2)):
                        continue
                    if top_edge or side:
                        c = EDGE
                    elif xx in (1, 2) or (yy in (1, 2) and not bottom):
                        c = HI
                    elif xx in (25, 26) or (yy in (29, 30) and bottom):
                        c = SH
                    else:
                        c = PANEL if selected else shade(PANEL, -0.18)
                    tp[xx, yy] = (*c, 255)
            img.alpha_composite(t, (col * 28, row * 32))
    for x0, col in ((232, (230, 236, 246)), (244, (150, 156, 170))):
        th = new(12, 15)
        p = th.load()
        for yy in range(15):
            for xx in range(12):
                p[xx, yy] = (*(EDGE if xx in (0, 11) or yy in (0, 14) else shade(col, -0.2) if xx > 8 or yy > 11 else col), 255)
        img.alpha_composite(th, (x0, 0))
    return img


def creative_page(rel, scroll=True, search=False):
    img = panel_from(rel, 195, 136)
    slots_from(rel, img)
    if scroll:
        recess(img, 174, 17, 14, 114, fill=(110, 120, 140))
    if search:
        text_box(img, 80, 4, 90, 12)
    if rel.endswith("tab_inventory.png"):
        recess(img, 53, 5, 54, 45)
    return img


def generic(rel, w, h):
    return basic(rel, w, h)


# ---------------------------------------------------------------- other GUI sheets
def book():
    img = new(256, 256)
    p = img.load()
    page = ramp((236, 228, 206), (-0.3, -0.1, 0.0, 0.1))
    for y in range(182):
        for x in range(20, 172):
            edge = x in (20, 171) or y in (0, 181)
            p[x, y] = (*(shade(page[0], -0.3) if edge else page[2] if (x * 3 + y) % 17 else page[1]), 255)
    for x in range(20, 30):
        for y in range(1, 181):
            p[x, y] = (*mix(page[0], page[2], (x - 20) / 10), 255)
    for i, (y0, hover) in enumerate(((192, False), (205, False))):
        for hv in (0, 1):
            col = BLUE if hv == 0 else AQUA
            a = new(23, 13)
            ap = a.load()
            for yy in range(13):
                for xx in range(23):
                    d = abs(yy - 6)
                    shaft = 2 <= xx <= 15 and d <= 1
                    head = 14 <= xx <= 21 and (xx - 14) + d <= 6
                    if shaft or head:
                        ap[xx, yy] = (*col, 255)
            if i == 1:
                a = a.transpose(Image.FLIP_LEFT_RIGHT)
            img.alpha_composite(a, (hv * 23, y0))
    return img


def arrow_icons(rel):
    """resource_packs.png / server_selection.png: 32x32 icons in columns; row 0 normal, row 1 (y=32) hover."""
    img = new(256, 256)
    dirs = ["right", "left", "up", "down"]
    for col, d in enumerate(dirs):
        for row in range(2):
            ic = new(32, 32)
            p = ic.load()
            col_c = (236, 242, 250) if row == 0 else AQUA
            for yy in range(32):
                for xx in range(32):
                    if d == "right":
                        ok = 10 <= xx <= 22 and abs(yy - 16) <= (22 - xx) * 0.75 + 0.5
                    elif d == "left":
                        ok = 10 <= xx <= 22 and abs(yy - 16) <= (xx - 10) * 0.75 + 0.5
                    elif d == "up":
                        ok = 4 <= yy <= 12 and abs(xx - 16) <= (yy - 4) + 0.5 and xx < 30
                    else:
                        ok = 20 <= yy <= 28 and abs(xx - 16) <= (28 - yy) + 0.5
                    if ok:
                        p[xx, yy] = (*col_c, 255)
            img.alpha_composite(ic, (col * 32, row * 32))
    return img


def options_background():
    img = new(16, 16)
    p = img.load()
    for y in range(16):
        for x in range(16):
            v = (x * 7 + y * 13) % 11
            c = (100, 128, 180) if v < 6 else (116, 146, 200) if v < 9 else (84, 108, 156)
            if (x + y) % 8 == 0:
                c = (150, 180, 226)
            p[x, y] = (*c, 255)
    return img


def framed_mask(rel, base=PANEL):
    """Any GUI sheet where we only know the footprint: paint a Tidal panel over each piece."""
    m = layout_mask(rel)
    h, w = len(m), len(m[0])
    return panel_from(rel, w, h, new(w, h))


# ---------------------------------------------------------------- title screen
BLOCK_FONT = {
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "I": ["###", ".#.", ".#.", ".#.", "###"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"], "E": ["####", "#...", "###.", "#...", "####"],
    "C": [".###", "#...", "#...", "#...", ".###"], "R": ["###.", "#..#", "###.", "#.#.", "#..#"],
    "A": [".##.", "#..#", "####", "#..#", "#..#"], "F": ["####", "#...", "###.", "#...", "#..."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."], "D": ["###.", "#..#", "#..#", "#..#", "###."],
    "L": ["#...", "#...", "#...", "#...", "####"],
}


def title_logo():
    """MINECRAFT in chunky blue-stone letters, split over the two 155x44 halves the game draws."""
    word = "MINECRAFT"
    s = 6
    full = new(310, 44)
    p = full.load()
    x = 6
    stone = ramp((120, 160, 210), (-0.6, -0.3, 0.0, 0.3, 0.55))
    for ch in word:
        glyph = BLOCK_FONT[ch]
        gw = len(glyph[0])
        for gy, row in enumerate(glyph):
            for gx, c in enumerate(row):
                if c != "#":
                    continue
                for yy in range(s):
                    for xx in range(s):
                        px_, py_ = x + gx * s + xx, 6 + gy * s + yy
                        if yy == 0 or xx == 0:
                            col = stone[4]
                        elif yy == s - 1 or xx == s - 1:
                            col = stone[1]
                        else:
                            col = stone[3] if (xx + yy + gx) % 5 else stone[2]
                        p[px_, py_] = (*col, 255)
        x += gw * s + 4
    # drop shadow
    shadow = new(310, 44)
    sp = shadow.load()
    for yy in range(44):
        for xx in range(310):
            if p[xx, yy][3] and xx + 3 < 310 and yy + 3 < 44:
                sp[xx + 3, yy + 3] = (*EDGE, 255)
    shadow.alpha_composite(full)
    img = new(256, 256)
    img.alpha_composite(shadow.crop((0, 0, 155, 44)), (0, 0))
    img.alpha_composite(shadow.crop((155, 0, 310, 44)), (0, 45))
    return img


def splash():
    img = Image.new("RGBA", (256, 256), (240, 246, 252, 255))
    p = img.load()
    for y in range(256):
        for x in range(256):
            wave = 150 + 14 * math.sin(x / 256 * 2 * math.pi * 1.5)
            if y > wave:
                p[x, y] = (*mix((54, 160, 220), (20, 40, 96), min(1, (y - wave) / 90)), 255)
    return img


def panorama(face):
    img = new(256, 256)
    p = img.load()
    for y in range(256):
        for x in range(256):
            if face == 4:      # up
                d = math.hypot(x - 128, y - 128) / 181
                c = mix((70, 140, 220), (140, 200, 245), d)
            elif face == 5:    # down
                c = mix((20, 50, 100), (30, 70, 130), ((x * 7 + y * 3) % 23) / 23 * 0.3)
            else:
                horizon = 128 + 4 * math.sin((x / 256 + face / 4) * 2 * math.pi * 2)
                if y < horizon:
                    c = mix((70, 140, 220), (180, 220, 250), y / 128)
                else:
                    k = (y - horizon) / 128
                    c = mix((40, 110, 180), (16, 40, 86), k)
                    if (int(x + face * 64 + y * 2.5) % 37 == 0) and k < 0.6:
                        c = mix(c, (200, 230, 250), 0.5)
                # a few soft clouds
                cl = math.sin((x / 256 + face / 4) * 2 * math.pi * 3) * math.sin(y / 40)
                if 40 < y < 100 and cl > 0.75:
                    c = mix(c, (250, 252, 255), 0.6)
            p[x, y] = (*c, 255)
    return img


def preset(kind):
    pal = {"chaos": ((140, 60, 160), (220, 100, 60)), "delight": ((120, 200, 90), (250, 200, 220)),
           "drought": ((220, 190, 110), (180, 130, 70)), "isles": ((60, 140, 220), (90, 180, 80)),
           "luck": ((90, 200, 90), (240, 210, 60)), "madness": ((200, 60, 60), (70, 70, 80)),
           "water": ((40, 110, 200), (90, 170, 240))}[kind]
    img = new(256, 256)
    p = img.load()
    for y in range(256):
        for x in range(256):
            v = math.sin(x / 30 + kind.__len__()) * math.sin(y / 23) + math.sin((x + y) / 50)
            p[x, y] = (*mix(pal[0], pal[1], max(0, min(1, (v + 2) / 4))), 255)
    return img


# ---------------------------------------------------------------- generate
def generate():
    save(inventory(), "gui/container/inventory.png")
    save(crafting_table(), "gui/container/crafting_table.png")
    save(furnace(), "gui/container/furnace.png")
    save(brewing_stand(), "gui/container/brewing_stand.png")
    save(enchanting_table(), "gui/container/enchanting_table.png")
    save(anvil(), "gui/container/anvil.png")
    save(beacon(), "gui/container/beacon.png")
    save(villager(), "gui/container/villager.png")
    save(horse(), "gui/container/horse.png")
    save(generic("gui/container/generic_54.png", 176, 222), "gui/container/generic_54.png")
    save(generic("gui/container/dispenser.png", 176, 166), "gui/container/dispenser.png")
    save(generic("gui/container/hopper.png", 176, 133), "gui/container/hopper.png")
    save(creative_tabs(), "gui/container/creative_inventory/tabs.png")
    save(creative_page("gui/container/creative_inventory/tab_items.png"), "gui/container/creative_inventory/tab_items.png")
    save(creative_page("gui/container/creative_inventory/tab_item_search.png", search=True),
         "gui/container/creative_inventory/tab_item_search.png")
    save(creative_page("gui/container/creative_inventory/tab_inventory.png", scroll=False),
         "gui/container/creative_inventory/tab_inventory.png")
    st = new(128, 128)
    m = layout_mask("gui/container/stats_icons.png")
    for cy in range(0, 128, 18):
        for cx in range(0, 128, 18):
            if cy + 18 <= 128 and cx + 18 <= 128 and any(m[cy + yy][cx + xx] for yy in range(18) for xx in range(18)):
                slot(st, cx, cy)
    save(st, "gui/container/stats_icons.png")

    save(book(), "gui/book.png")
    save(arrow_icons("gui/resource_packs.png"), "gui/resource_packs.png")
    save(arrow_icons("gui/server_selection.png"), "gui/server_selection.png")
    save(options_background(), "gui/options_background.png")
    save(panel_from("gui/demo_background.png", 248, 166), "gui/demo_background.png")
    ach = panel_from("gui/achievement/achievement_background.png", 256, 202)
    for i, (fill, edge) in enumerate(((PANEL, EDGE), ((250, 220, 120), (120, 90, 30)))):
        tile = panel_from_rect(26, 26)
        img2 = new(26, 26)
        img2.alpha_composite(tile)
        ach.alpha_composite(img2, (i * 26, 202))
    save(ach, "gui/achievement/achievement_background.png")
    save(framed_mask("gui/achievement/achievement_icons.png"), "gui/achievement/achievement_icons.png")
    save(framed_mask("gui/spectator_widgets.png"), "gui/spectator_widgets.png")
    save(framed_mask("gui/stream_indicator.png"), "gui/stream_indicator.png")
    save(title_logo(), "gui/title/minecraft.png")
    save(splash(), "gui/title/mojang.png")
    for i in range(6):
        save(panorama(i), f"gui/title/background/panorama_{i}.png")
    for kind in ("chaos", "delight", "drought", "isles", "luck", "madness", "water"):
        save(preset(kind), f"gui/presets/{kind}.png")

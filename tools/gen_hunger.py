"""Original food-bar icons for gui/icons.png: a golden roast drumstick (9x9 per icon).

Called from tools/recolor.py after the hearts, so re-running recolor.py keeps it.
Full shanks are warm amber so the bar reads clearly next to the teal hearts. Empty slots are a
dark silhouette of the same drumstick (like empty heart containers). The Hunger effect turns the
meat a sickly green.
"""
from PIL import Image

ROW_Y = 27  # hunger row in icons.png
# Shape: O outline, d dark meat, m meat, h highlight, b bone, B bone highlight (knob)
SHANK = [
    "..OOO....",
    ".OmhhO...",
    "OmhmmmO..",
    "OmmmmmO..",
    "OdmmmdO..",
    ".OddmbO..",
    "..OOObbO.",
    "....ObBBO",
    ".....OOO.",
]
HALF_FROM_X = 3  # the bar fills right-to-left, so a half shank keeps its right side

NORMAL = {"O": (64, 30, 14), "d": (182, 82, 28), "m": (230, 132, 44), "h": (255, 202, 112),
          "b": (226, 214, 186), "B": (255, 250, 236)}
FLASH = {k: tuple(min(255, c + 60) for c in v) for k, v in NORMAL.items()}  # brief flash variant
HUNGER = {"O": (30, 44, 16), "d": (84, 120, 34), "m": (120, 160, 52), "h": (176, 206, 98),
          "b": (190, 196, 150), "B": (226, 232, 196)}
EMPTY = {"O": (18, 18, 24), "fill": (52, 54, 64)}
EMPTY_FLASH = {"O": (236, 236, 244), "fill": (52, 54, 64)}
EMPTY_HUNGER = {"O": (40, 60, 20), "fill": (52, 58, 46)}


def sprite(colors, half=False, empty=False):
    img = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    for y, row in enumerate(SHANK):
        for x, ch in enumerate(row):
            if ch == "." or (half and x < HALF_FROM_X):
                continue
            c = colors["O"] if ch == "O" else (colors["fill"] if empty else colors[ch])
            img.putpixel((x, y), (*c, 255))
    return img


def draw(icons: Image.Image) -> Image.Image:
    s = icons.width // 256  # scale, in case icons.png is ever higher-res
    cells = {
        16: sprite(EMPTY, empty=True), 25: sprite(EMPTY_FLASH, empty=True),
        34: sprite(EMPTY, empty=True), 43: sprite(EMPTY_FLASH, empty=True),
        52: sprite(NORMAL), 61: sprite(NORMAL, half=True),
        70: sprite(FLASH), 79: sprite(FLASH, half=True),
        88: sprite(HUNGER), 97: sprite(HUNGER, half=True),
        106: sprite(FLASH), 115: sprite(FLASH, half=True),
        133: sprite(EMPTY_HUNGER, empty=True),
    }
    for x, spr in cells.items():
        box = (x * s, ROW_Y * s, (x + 9) * s, (ROW_Y + 9) * s)
        icons.paste(Image.new("RGBA", (9 * s, 9 * s), (0, 0, 0, 0)), box[:2])
        icons.paste(spr.resize((9 * s, 9 * s), Image.NEAREST), box[:2])
    return icons

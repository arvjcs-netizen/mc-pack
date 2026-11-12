"""Draw a clean 16x16 TNT side (blocks/tnt_side.png).

Bright red dynamite sticks top and bottom, a white label band across the middle, and
bold dark "TNT" letters. Flat colors with simple shading, no noise.

    python tools/gen_tnt.py      then press F3+T in-game
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pack" / "assets" / "minecraft" / "textures" / "blocks" / "tnt_side.png"

# Each 4px-wide stick is shaded left-to-right: edge, mid, highlight, mid
STICK = [(170, 22, 22), (214, 38, 34), (236, 64, 56), (214, 38, 34)]
RED_SHADOW = (140, 16, 18)          # row of red touching the label (paper casts a shadow)
LABEL_TOP = (250, 250, 250)
LABEL = (226, 226, 228)
LABEL_BOTTOM = (186, 186, 190)
INK = (42, 42, 52)
INK_LIGHT = (78, 78, 92)            # left edge of each stroke, for a bit of depth

LABEL_ROWS = range(5, 11)           # rows 5-10 are the white band
LETTERS = [                          # drawn on rows 6-9
    (2, ["###", ".#.", ".#.", ".#."]),
    (6, ["#..#", "##.#", "#.##", "#..#"]),
    (11, ["###", ".#.", ".#.", ".#."]),
]


def main() -> None:
    img = Image.new("RGBA", (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            if y in LABEL_ROWS:
                c = LABEL_TOP if y == LABEL_ROWS[0] else LABEL_BOTTOM if y == LABEL_ROWS[-1] else LABEL
            elif y in (4, 11):
                c = RED_SHADOW
            else:
                c = STICK[x % 4]
            px[x, y] = (*c, 255)

    for x0, rows in LETTERS:
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch == "#":
                    left_open = dx == 0 or row[dx - 1] != "#"
                    px[x0 + dx, 6 + dy] = (*(INK_LIGHT if left_open and dy > 0 else INK), 255)

    img.save(OUT)
    print(f"Wrote {OUT.name}. Press F3+T in-game.")


if __name__ == "__main__":
    main()

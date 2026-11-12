"""Draw a simple 16x16 animated fire charge (items/fireball.png + .mcmeta).

A round core with a flame tail streaming to the top-right. The tail flickers and waves
from frame to frame. Only 4 flat colors, no noise, so it reads cleanly at 16x.

    python tools/gen_fireball.py      then press F3+T in-game
"""
import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "pack" / "assets" / "minecraft" / "textures" / "items"

SIZE = 16
FRAMES = 8
FRAMETIME = 2  # game ticks per frame (20 ticks = 1 second)

OUTLINE = (112, 18, 8)
RED = (206, 52, 14)
ORANGE = (246, 134, 30)
YELLOW = (255, 214, 92)

CENTER = (6.0, 10.0)  # core of the fireball
CORE_R = 4.0
TAIL_ANGLE = -45  # degrees; tail streams toward the top-right

# Flame tongues: (angle offset from the tail, base length, root half-width, flicker phase)
TONGUES = [(-34, 7.0, 2.6, 0.0), (0, 9.5, 3.2, 0.33), (34, 7.0, 2.6, 0.66)]


def heat(x: float, y: float, t: float) -> float:
    """0 = outside, up to 1 = hottest. t goes 0..1 over the loop."""
    dx, dy = x - CENTER[0], y - CENTER[1]
    best = max(0.0, 1 - math.hypot(dx, dy) / CORE_R)  # round core
    for offset, base_len, half_w, ph in TONGUES:
        a = math.radians(TAIL_ANGLE + offset)
        along = dx * math.cos(a) + dy * math.sin(a)
        across = -dx * math.sin(a) + dy * math.cos(a)
        wave = 2 * math.pi * (t + ph)
        length = base_len + 1.6 * math.sin(wave)                 # tongue grows and shrinks
        across -= 0.8 * (along / length) * math.sin(wave * 2)    # tip sways side to side
        if 0 < along < length:
            w = half_w * (1 - along / length)
            if abs(across) < w:
                best = max(best, (1 - abs(across) / w) * (1 - along / length) * 0.9)
    return best


def draw_frame(t: float) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for y in range(SIZE):
        for x in range(SIZE):
            h = heat(x + 0.5, y + 0.5, t)
            if h > 0.62:
                px[x, y] = (*YELLOW, 255)
            elif h > 0.34:
                px[x, y] = (*ORANGE, 255)
            elif h > 0.0:
                px[x, y] = (*RED, 255)
    # 1px dark outline around the shape so it pops in the hotbar
    out = img.copy()
    opx = out.load()
    for y in range(SIZE):
        for x in range(SIZE):
            if px[x, y][3] == 0 and any(
                0 <= x + dx < SIZE and 0 <= y + dy < SIZE and px[x + dx, y + dy][3]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                opx[x, y] = (*OUTLINE, 255)
    return out


def main() -> None:
    strip = Image.new("RGBA", (SIZE, SIZE * FRAMES))
    for i in range(FRAMES):
        strip.paste(draw_frame(i / FRAMES), (0, i * SIZE))
    strip.save(ITEMS / "fireball.png")
    (ITEMS / "fireball.png.mcmeta").write_text(
        json.dumps({"animation": {"frametime": FRAMETIME, "interpolate": False}}, indent=2) + "\n"
    )
    print(f"Wrote fireball.png ({FRAMES} frames). Press F3+T in-game.")


if __name__ == "__main__":
    main()

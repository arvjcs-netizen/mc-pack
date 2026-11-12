"""Recolor textures that came from other packs.

- Hearts (gui/icons.png): blue -> diamond-sword teal, a bit lighter than the sword.
- Bed (blocks/bed_*.png + items/bed.png): red blanket -> rainbow stripes along the bed.
- Crit / arrow-trail particle (particle/particles.png): blue-centered gradient.
- Bow (items/bow_*.png): wood -> matching blue gradient; the drawn arrow stays brown.

Only the targeted pixels change; shading is kept. Originals are saved to tools/originals/ on
first run and every run works from those, so you can tweak the colors and re-run freely.
(The fire charge is drawn by tools/gen_fireball.py instead.)

    python tools/recolor.py      then press F3+T in-game
"""
import colorsys
import json
import math
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "pack" / "assets" / "minecraft" / "textures"
ORIG = ROOT / "tools" / "originals"

# Darkest -> lightest. Diamond sword teal, shifted a little lighter than the sword itself.
HEART_RAMP = [(24, 150, 158), (66, 212, 204), (146, 246, 228)]
HEART_ROWS = [(16, 0, 256, 9), (16, 45, 256, 54)]  # normal + hardcore heart rows in icons.png

RAINBOW = [(214, 52, 52), (240, 136, 40), (244, 210, 58), (78, 188, 72), (58, 122, 220), (148, 74, 204)]

# Crit / arrow-trail particle, redrawn as a thin 4-point sparkle. 4 = center (brightest) ... 1 = tips.
# In 1.8.9 a crit's blue fades x0.9 and green x0.96 every tick while red stays put, so anything
# whitish drifts to beige. Keeping red very low makes it fade toward cyan instead.
# Crit / arrow-trail particle: a hollow ring (like Dewier's), deep blue with a brighter middle band.
# Over a crit's ~6-tick life blue drops to ~53% and green to ~78% while red stays, so any whitish
# shade turns beige. Every shade keeps blue > 2.5x red and > 1.8x green so it stays blue.
CRIT_EDGE = (40, 52, 225)    # inner + outer rim of the ring
CRIT_MID = (66, 104, 255)    # brightest band through the middle of the ring
CRIT_RING = (4.6, 7.6)       # inner/outer radius in pixels of a 16x16 cell
CRIT_CELL = 65  # particles.png sprite index used by crits and fully-charged arrow trails (16x16 grid)
PARTICLE_SCALE = 2  # particles.png is upscaled (nearest) 128 -> 256 so the ring gets 16x16 pixels

# Bow + fishing rod wood: a strong gradient along the item, from violet at the bottom-left end
# (bow's lower tip / rod handle) to bright cyan at the top-right end, and the whole thing pulses
# bright -> dark -> bright. Each ramp is darkest -> lightest wood shade.
GRAD_RAMP_START = [(52, 8, 104), (112, 28, 200), (168, 76, 252), (218, 150, 255)]
GRAD_RAMP_END = [(8, 84, 160), (16, 168, 232), (70, 226, 255), (186, 252, 255)]
PULSE_DARK = 0.6       # at its darkest the pulse dims the wood to this fraction
BOW_PULSE_FRAMES = 8   # frames in one bright -> dark -> bright loop
BOW_FRAMETIME = 4      # ticks per frame (20 ticks = 1s), so one loop = 8 * 4 = 32 ticks = 1.6s
BOW_FRAMES = ["bow_standby", "bow_pulling_0", "bow_pulling_1", "bow_pulling_2"]
ROD_FRAMES = ["fishing_rod_uncast", "fishing_rod_cast"]


def original(rel: str) -> Image.Image:
    saved = ORIG / rel
    if not saved.exists():
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEX / rel, saved)
    return Image.open(saved).convert("RGBA")


def hsv(p):
    return colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)


def is_blue(p) -> bool:
    h, s, _ = hsv(p)
    return p[3] > 0 and 0.52 <= h <= 0.70 and s > 0.35


def is_red(p) -> bool:
    h, s, _ = hsv(p)
    return p[3] > 0 and (h < 0.04 or h > 0.94) and s > 0.4


def lum(p) -> float:
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def ramp_color(ramp, t: float):
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    i = min(int(t), len(ramp) - 2)
    f = t - i
    return tuple(round(ramp[i][k] + (ramp[i + 1][k] - ramp[i][k]) * f) for k in range(3))


def recolor_ramp(img, ramp, boxes):
    """Map each distinct blue shade (ranked by brightness) onto the ramp."""
    px = img.load()
    coords = [(x, y) for (x0, y0, x1, y1) in boxes for y in range(y0, y1) for x in range(x0, x1)]
    blues = sorted({px[c] for c in coords if is_blue(px[c])}, key=lum)
    lo, hi = lum(blues[0]), lum(blues[-1])
    mapping = {p: (*ramp_color(ramp, 0 if hi == lo else (lum(p) - lo) / (hi - lo)), p[3]) for p in blues}
    for c in coords:
        if px[c] in mapping:
            px[c] = mapping[px[c]]
    return img


def rainbowize(img, band_of):
    """Replace red pixels with rainbow colors, keeping each pixel's light/dark shading."""
    px = img.load()
    reds = [(x, y) for y in range(img.height) for x in range(img.width) if is_red(px[x, y])]
    mean_v = sum(hsv(px[c])[2] for c in reds) / len(reds)
    for x, y in reds:
        shade = hsv(px[x, y])[2] / mean_v
        base = RAINBOW[band_of(x, y)]
        px[x, y] = (*(min(255, round(ch * shade)) for ch in base), px[x, y][3])
    return img


def is_wood(p) -> bool:
    h, s, _ = hsv(p)
    return p[3] > 0 and 0.03 <= h <= 0.14 and s > 0.3


def crit_particle() -> None:
    img = original("particle/particles.png")
    img = img.resize((img.width * PARTICLE_SCALE, img.height * PARTICLE_SCALE), Image.NEAREST)
    cell = img.width // 16
    x0, y0 = (CRIT_CELL % 16) * cell, (CRIT_CELL // 16) * cell
    r_in, r_out = (r * cell / 16 for r in CRIT_RING)
    px = img.load()
    for y in range(cell):
        for x in range(cell):
            r = math.hypot(x + 0.5 - cell / 2, y + 0.5 - cell / 2)
            if r_in <= r <= r_out:
                t = 1 - abs((r - r_in) / (r_out - r_in) * 2 - 1)  # 0 at the rims, 1 mid-ring
                px[x0 + x, y0 + y] = (*ramp_color([CRIT_EDGE, CRIT_MID], t), 255)
            else:
                px[x0 + x, y0 + y] = (0, 0, 0, 0)
    img.save(TEX / "particle/particles.png")


def gradient_pulse(rel: str, skip=lambda x, y: False) -> None:
    """Recolor an item's wood with the violet -> cyan gradient and make it pulse."""
    base = original(rel)
    bpx = base.load()
    wood = [(x, y) for y in range(16) for x in range(16) if is_wood(bpx[x, y]) and not skip(x, y)]
    shades = sorted({bpx[c] for c in wood}, key=lum)
    lo, hi = lum(shades[0]), lum(shades[-1])
    # Both items run from bottom-left to top-right, so x - y measures how far along a pixel is.
    a0, a1 = min(x - y for x, y in wood), max(x - y for x, y in wood)

    strip = Image.new("RGBA", (16, 16 * BOW_PULSE_FRAMES))
    for f in range(BOW_PULSE_FRAMES):
        bright = 1 - (1 - PULSE_DARK) * (1 - math.cos(2 * math.pi * f / BOW_PULSE_FRAMES)) / 2
        frame = base.copy()
        fpx = frame.load()
        for x, y in wood:
            g = (x - y - a0) / (a1 - a0)
            ramp = [tuple((s + (e - s) * g) * bright for s, e in zip(sc, ec))
                    for sc, ec in zip(GRAD_RAMP_START, GRAD_RAMP_END)]
            shade = 0 if hi == lo else (lum(bpx[x, y]) - lo) / (hi - lo)
            fpx[x, y] = (*ramp_color(ramp, shade), bpx[x, y][3])
        strip.paste(frame, (0, 16 * f))
    strip.save(TEX / rel)
    (TEX / f"{rel}.mcmeta").write_text(
        json.dumps({"animation": {"frametime": BOW_FRAMETIME, "interpolate": True}}, indent=2) + "\n"
    )


def bow() -> None:
    for name in BOW_FRAMES:
        pulling = name != "bow_standby"
        # In the pulling frames an arrow runs diagonally from the grip to the string; keep it brown.
        gradient_pulse(f"items/{name}.png",
                       lambda x, y: pulling and x >= 6 and y >= 6 and -2 <= x - y <= 1)


def fishing_rod() -> None:
    for name in ROD_FRAMES:
        gradient_pulse(f"items/{name}.png")


def main() -> None:
    crit_particle()
    bow()
    fishing_rod()
    icons = recolor_ramp(original("gui/icons.png"), HEART_RAMP, HEART_ROWS)
    # Food bar (row y=27, x=16..142) from Dewier 140k. tools/gen_hunger.py has an original
    # golden-drumstick alternative: swap this for gen_hunger.draw(icons) to use it instead.
    icons.paste(Image.open(ORIG / "gui/dewier140k_hunger.png").convert("RGBA"), (16, 27))
    icons.save(TEX / "gui/icons.png")

    # Blanket runs along x on both blocks: foot block x3-15 is positions 0-12, head block x0-4 is
    # 13-17. 18 positions / 6 colors = 3 columns per color. Sides use the same x layout as tops.
    for part, offset in (("feet", -3), ("head", 13)):
        for face in ("top", "side"):
            rel = f"blocks/bed_{part}_{face}.png"
            rainbowize(original(rel), lambda x, y, o=offset: min(5, max(0, (x + o) // 3))).save(TEX / rel)

    # Item icon is drawn at an angle: foot at bottom-left, pillow at top-right, so use x - y.
    item = original("items/bed.png")
    px = item.load()
    ts = [x - y for y in range(16) for x in range(16) if is_red(px[x, y])]
    lo, hi = min(ts), max(ts)
    rainbowize(item, lambda x, y: min(5, (x - y - lo) * 6 // (hi - lo + 1))).save(TEX / "items/bed.png")

    print("Recolored crits, bow, fishing rod, hearts and bed. Press F3+T in-game.")


if __name__ == "__main__":
    main()

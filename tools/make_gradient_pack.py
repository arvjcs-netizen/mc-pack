"""Build "MyPack Gradient": a complete, standalone version of MyPack where every diamond texture
and the fireball use the same animated violet -> cyan gradient pulse as the bow and fishing rod.

    python tools/make_gradient_pack.py      then press F3+T in-game

Everything except the recolored files is a live view of MyPack (junctions + hard links, see
mirror()), so MyPack edits show up here too. Re-run this when MyPack's diamond/fireball textures
change, or when a file is added to a folder that holds recolored files (items/, blocks/, ...).

The original MyPack (pack/) is never modified. packs/mypack_gradient/ is wiped and rebuilt every
run, so change this script (or MyPack itself) instead of editing the gradient pack by hand.

- Item icons and blocks are animated (same 8 frames / 1.6s loop as the bow).
- Worn armor and horse armor are entity textures, which vanilla 1.8.9 can't animate: the texture
  has a still gradient (helmet violet down to boots cyan), and an OptiFine custom animation in
  mcpatcher/anim pulses it in-game where OptiFine-style animations are supported.
"""
import _winapi  # Windows-only: directory junctions (no admin rights needed)
import colorsys
import json
import math
import os
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recolor import (BOW_FRAMETIME, BOW_PULSE_FRAMES, GRAD_RAMP_END, GRAD_RAMP_START,  # noqa: E402
                     PULSE_DARK, lum, ramp_color)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "pack"
DST = ROOT / "packs" / "mypack_gradient"
TEX = DST / "assets" / "minecraft" / "textures"
ANIM = DST / "assets" / "minecraft" / "mcpatcher" / "anim"  # OptiFine custom animations
DESCRIPTION = "§bMy Pack §dGradient §7| 1.8.9"

DIAMOND_ITEMS = [
    "diamond", "diamond_sword", "diamond_pickaxe", "diamond_axe", "diamond_shovel", "diamond_hoe",
    "diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots", "diamond_horse_armor",
]
DIAMOND_BLOCKS = ["diamond_block", "diamond_ore"]


def is_diamond(p) -> bool:
    """Diamond-teal pixels, including the near-white highlights; not stone gray or wood."""
    h, s, v = colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)
    return p[3] > 0 and 0.40 <= h <= 0.60 and s > 0.08 and v > 0.25


def is_gold(p) -> bool:
    """Golden-apple gold, including its pale highlights; not the dark brown stem or green leaf."""
    h, s, v = colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)
    return p[3] > 0 and 0.03 <= h <= 0.18 and s > 0.15 and v > 0.5


def gradient_color(g: float, shade: float, bright: float = 1.0):
    """g: 0 = violet end, 1 = cyan end. shade: 0 = darkest, 1 = lightest. bright: pulse level."""
    ramp = [tuple((s + (e - s) * g) * bright for s, e in zip(sc, ec))
            for sc, ec in zip(GRAD_RAMP_START, GRAD_RAMP_END)]
    return ramp_color(ramp, shade)


def pulse(f: int) -> float:
    return 1 - (1 - PULSE_DARK) * (1 - math.cos(2 * math.pi * f / BOW_PULSE_FRAMES)) / 2


def shade_map(img, pixels):
    """Rank each pixel's brightness among the recolored pixels: 0 = darkest, 1 = lightest."""
    px = img.load()
    ls = [lum(px[c]) for c in pixels]
    lo, hi = min(ls), max(ls)
    return {c: 0 if hi == lo else (lum(px[c]) - lo) / (hi - lo) for c in pixels}


def write_anim(rel: str, frames, frametime: int) -> None:
    w, h = frames[0].size
    strip = Image.new("RGBA", (w, h * len(frames)))
    for i, fr in enumerate(frames):
        strip.paste(fr, (0, h * i))
    strip.save(TEX / rel)
    (TEX / f"{rel}.mcmeta").write_text(
        json.dumps({"animation": {"frametime": frametime, "interpolate": True}}, indent=2) + "\n")


def animate(rel: str, along, match=is_diamond) -> None:
    """Recolor a 16x16 texture's diamond pixels with the pulsing gradient. along(x, y) -> 0..1,
    or None to run bottom-left -> top-right across the item's own diamond pixels."""
    base = Image.open(TEX / rel).convert("RGBA")
    px = base.load()
    pixels = [(x, y) for y in range(base.height) for x in range(base.width) if match(px[x, y])]
    shades = shade_map(base, pixels)
    if along is None:  # items: stretch the full violet -> cyan range over this item's own extent
        a0, a1 = min(x - y for x, y in pixels), max(x - y for x, y in pixels)
        along = lambda x, y: (x - y - a0) / max(a1 - a0, 1)  # noqa: E731
    frames = []
    for f in range(BOW_PULSE_FRAMES):
        fr = base.copy()
        fpx = fr.load()
        for c in pixels:
            fpx[c] = (*gradient_color(along(*c), shades[c], pulse(f)), 255)
        frames.append(fr)
    write_anim(rel, frames, BOW_FRAMETIME)


def item_along(x, y):
    # Items are drawn bottom-left (handle/grip) to top-right (tip), so x - y runs along them.
    return min(max((x - y + 15) / 30, 0.0), 1.0)


def block_along(x, y):
    # Diagonal bands that repeat every 16 px in both x and y, so placed blocks tile with no seams.
    return 0.5 - 0.5 * math.cos(2 * math.pi * (x - y) / 16)


ENTITY_ANIM_FRAMES = 32  # one frame per tick over the bow's 32-tick loop, so it's smooth without
                         # needing interpolation (which older OptiFine anim files don't support)


def entity_anim(rel: str, along) -> None:
    """Worn armor / horse armor are entity textures, which vanilla 1.8.9 can't animate. The texture
    itself gets the bright gradient (what players without OptiFine see), and an OptiFine custom
    animation (mcpatcher/anim) plays the pulse on top of it, in sync with the items."""
    base = Image.open(TEX / rel).convert("RGBA")
    px = base.load()
    pixels = [(x, y) for y in range(base.height) for x in range(base.width) if is_diamond(px[x, y])]
    shades = shade_map(base, pixels)
    g = {c: along(*c, base.width, base.height) for c in pixels}

    def frame(bright):
        fr = base.copy()
        fpx = fr.load()
        for c in pixels:
            fpx[c] = (*gradient_color(g[c], shades[c], bright), px[c][3])
        return fr

    frame(1.0).save(TEX / rel)
    n = ENTITY_ANIM_FRAMES
    strip = Image.new("RGBA", (base.width, base.height * n))
    for k in range(n):
        strip.paste(frame(1 - (1 - PULSE_DARK) * (1 - math.cos(2 * math.pi * k / n)) / 2), (0, base.height * k))
    name = Path(rel).stem
    ANIM.mkdir(parents=True, exist_ok=True)
    strip.save(ANIM / f"{name}.png")
    (ANIM / f"{name}.properties").write_text(
        f"from=./{name}.png\nto=textures/{rel}\nx=0\ny=0\nw={base.width}\nh={base.height}\nduration=1\n")


HEART_ROWS = [0, 45]  # icons.png rows (y) holding the normal and hardcore hearts, 9 px tall
HEART_CELL = 9        # each heart sprite is 9x9, starting at x = 16


def hearts() -> None:
    """Give every teal heart (full, half, flashing; normal + hardcore) its own violet -> cyan
    gradient, bottom-left to top-right. icons.png is a GUI texture, which vanilla can't animate,
    so the pulse is an OptiFine custom animation, one per heart row."""
    rel = "gui/icons.png"
    base = Image.open(TEX / rel).convert("RGBA")
    px = base.load()
    pixels = [(x, y) for y0 in HEART_ROWS for y in range(y0, y0 + HEART_CELL)
              for x in range(16, base.width) if is_diamond(px[x, y])]
    shades = shade_map(base, pixels)

    def g(x, y):
        cx, cy = (x - 16) % HEART_CELL, y % 45 if y >= 45 else y
        return (cx - cy + HEART_CELL - 1) / (2 * (HEART_CELL - 1))

    def frame(bright, img):
        ipx = img.load()
        for c in pixels:
            ipx[c] = (*gradient_color(g(*c), shades[c], bright), px[c][3])
        return img

    frame(1.0, base.copy()).save(TEX / rel)
    ANIM.mkdir(parents=True, exist_ok=True)
    n = ENTITY_ANIM_FRAMES
    for y0 in HEART_ROWS:
        xs = [x for x, y in pixels if y0 <= y < y0 + HEART_CELL]
        x0, x1 = min(xs), max(xs) + 1
        strip = Image.new("RGBA", (x1 - x0, HEART_CELL * n))
        for k in range(n):
            bright = 1 - (1 - PULSE_DARK) * (1 - math.cos(2 * math.pi * k / n)) / 2
            fr = frame(bright, base.copy()).crop((x0, y0, x1, y0 + HEART_CELL))
            strip.paste(fr, (0, HEART_CELL * k))
        name = f"hearts_{y0}"
        strip.save(ANIM / f"{name}.png")
        (ANIM / f"{name}.properties").write_text(
            f"from=./{name}.png\nto=textures/{rel}\nx={x0}\ny={y0}\nw={x1 - x0}\nh={HEART_CELL}\nduration=1\n")


def armor_layer_1(x, y, w, h):
    # 64x32 layout: head (helmet) rows 0-16; body + arms (chestplate) rows 16-32 at x >= 16;
    # legs at x < 16 (boots in layer 1). Violet helmet -> cyan boots down the whole player.
    if y < 16:
        return 0.25 * y / 16
    if x >= 16:
        return 0.25 + 0.35 * (y - 16) / 16
    return 0.8 + 0.2 * (y - 16) / 16


def armor_layer_2(x, y, w, h):
    # Leggings: legs at x < 16 and the waist on the body area, rows 16-32.
    return 0.55 + 0.3 * max(y - 16, 0) / 16


def horse_armor(x, y, w, h):
    return block_along(x * 16 / w, y * 16 / h)


def fireball() -> None:
    """Recolor the flickering fireball (8 frames) with the gradient, and give it the bow's pulse.
    Its flicker loop is 8 frames x 2 ticks, so it's played twice per 32-tick pulse."""
    rel = "items/fireball.png"
    strip = Image.open(TEX / rel).convert("RGBA")
    n = strip.height // 16
    frames = [strip.crop((0, 16 * i, 16, 16 * i + 16)) for i in range(n)]
    every = [(x, y) for fr in frames for y in range(16) for x in range(16) if fr.getpixel((x, y))[3]]
    ls = sorted({lum(fr.getpixel(c)) for fr in frames for c in every if fr.getpixel(c)[3]})
    lo, hi = ls[0], ls[-1]
    steps = 2 * BOW_PULSE_FRAMES  # 16 frames x 2 ticks = 32 ticks, same loop as the bow
    out = []
    for k in range(steps):
        src = frames[k % n]
        bright = 1 - (1 - PULSE_DARK) * (1 - math.cos(2 * math.pi * k / steps)) / 2
        fr = src.copy()
        fpx = fr.load()
        for y in range(16):
            for x in range(16):
                p = fpx[x, y]
                if p[3]:
                    shade = (lum(p) - lo) / (hi - lo)
                    fpx[x, y] = (*gradient_color(item_along(x, y), shade, bright), p[3])
        out.append(fr)
    w = Image.new("RGBA", (16, 16 * steps))
    for i, fr in enumerate(out):
        w.paste(fr, (0, 16 * i))
    w.save(TEX / rel)
    (TEX / f"{rel}.mcmeta").write_text(
        json.dumps({"animation": {"frametime": 2, "interpolate": False}}, indent=2) + "\n")


RECOLORED = ([f"items/{n}.png" for n in DIAMOND_ITEMS] + [f"blocks/{n}.png" for n in DIAMOND_BLOCKS]
             + ["models/armor/diamond_layer_1.png", "models/armor/diamond_layer_2.png",
                "entity/horse/armor/horse_armor_diamond.png", "items/fireball.png", "gui/icons.png",
                "items/apple_golden.png"])


def wipe(path: Path) -> None:
    """Delete the old build WITHOUT ever touching MyPack: junctions are unlinked, never entered,
    and removing a hard link only removes this pack's name for the file."""
    for entry in os.scandir(path):
        if entry.is_junction() or entry.is_symlink():
            os.rmdir(entry.path) if entry.is_dir() else os.remove(entry.path)
        elif entry.is_dir(follow_symlinks=False):
            wipe(Path(entry.path))
            os.rmdir(entry.path)
        else:
            os.remove(entry.path)


def mirror(src: Path, dst: Path, own: set, own_dirs: set) -> None:
    """Fill dst with live views of src. A folder with nothing recolored inside becomes a junction
    to MyPack's folder (fully live, new files included). Inside the few folders that do hold
    recolored files, every other file is a hard link to MyPack's file (edits show up in both).
    Files in `own` are real copies, so recoloring them can never write into MyPack."""
    dst.mkdir(parents=True, exist_ok=True)
    for entry in os.scandir(src):
        s, d = Path(entry.path), dst / entry.name
        rel = s.relative_to(SRC).as_posix()
        if entry.is_dir():
            if rel in own_dirs:
                mirror(s, d, own, own_dirs)
            else:
                _winapi.CreateJunction(str(s.resolve()), str(d))
        elif rel in own:
            shutil.copy2(s, d)
        else:
            os.link(s, d)


def main() -> None:
    tex_rel = "assets/minecraft/textures/"
    # mcpatcher/anim is listed so mcpatcher/ becomes a real folder, not a junction into MyPack.
    own = {"pack.mcmeta", "assets/minecraft/mcpatcher/anim/x"} | {tex_rel + r for r in RECOLORED}
    own_dirs = {p.as_posix() for r in own for p in Path(r).parents if p.as_posix() != "."}
    before = sum(1 for _ in SRC.rglob("*"))

    if DST.exists():
        wipe(DST)
    mirror(SRC, DST, own, own_dirs)
    meta = json.loads((SRC / "pack.mcmeta").read_text(encoding="utf-8"))
    meta["pack"]["description"] = DESCRIPTION
    (DST / "pack.mcmeta").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for name in DIAMOND_ITEMS:
        animate(f"items/{name}.png", None)
    for name in DIAMOND_BLOCKS:
        animate(f"blocks/{name}.png", block_along)
    entity_anim("models/armor/diamond_layer_1.png", armor_layer_1)
    entity_anim("models/armor/diamond_layer_2.png", armor_layer_2)
    entity_anim("entity/horse/armor/horse_armor_diamond.png", horse_armor)
    fireball()
    hearts()
    animate("items/apple_golden.png", None, is_gold)  # also used by the enchanted apple
    assert sum(1 for _ in SRC.rglob("*")) == before, "MyPack's file count changed; check pack/!"
    print(f"Built {DST}. Enable 'MyPack Gradient' in-game (or press F3+T if it's already on).")


if __name__ == "__main__":
    main()

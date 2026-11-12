"""Build the whole Tidal pack into packs/tidal/.

    python tools/tidal/generate.py
    python build.py --pack tidal --link     (first time: links it into .minecraft/resourcepacks)

Then press F3+T in-game.
"""
import json
import shutil

from PIL import Image

import anim
import armor
import blocks
import decor
import entities
import extra_items
import gui
import items
import lib
import screens
import world
from lib import PACK, TEX


def pack_icon():
    """128x128 icon: a deep-to-light blue wave with the diamond sword on top."""
    img = Image.new("RGBA", (128, 128))
    px = img.load()
    import math
    for y in range(128):
        for x in range(128):
            wave = 64 + 10 * math.sin(x / 128 * 2 * math.pi * 1.5)
            t = y / 127
            c = lib.mix((20, 40, 96), (54, 160, 220), 1 - t)
            if y > wave:
                c = lib.mix(c, (18, 30, 70), 0.45)
            px[x, y] = (*c, 255)
    sword = Image.open(TEX / "items/diamond_sword.png").convert("RGBA").resize((96, 96), Image.NEAREST)
    img.alpha_composite(sword, (16, 16))
    img.save(PACK / "pack.png")


def main():
    # Clear the contents but keep the folder itself: .minecraft/resourcepacks/Tidal links to it.
    PACK.mkdir(parents=True, exist_ok=True)
    for child in PACK.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    TEX.mkdir(parents=True)
    blocks.generate()
    decor.generate()
    items.generate()
    extra_items.generate()
    armor.generate()
    anim.generate()   # after blocks: ore twinkles start from the static ore textures
    gui.generate()
    screens.generate()
    entities.generate()
    world.generate()
    (PACK / "pack.mcmeta").write_text(json.dumps(
        {"pack": {"pack_format": 1, "description": "§bTidal §7[§f16x§7] §8| original"}},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pack_icon()
    print(f"Tidal: {len(set(lib.WRITTEN))} textures written to {PACK}")


if __name__ == "__main__":
    main()

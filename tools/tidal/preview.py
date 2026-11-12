"""Render a contact sheet of generated textures (for checking the look). Not part of the pack."""
import sys
from pathlib import Path

from PIL import Image

from lib import TEX


def sheet(rels, out, scale=4, cols=16, bg=(58, 58, 64)):
    cell = 16 * scale + 4
    rows = (len(rels) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cell, rows * cell), (*bg, 255))
    for i, rel in enumerate(rels):
        p = TEX / rel
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA")
        im = im.crop((0, 0, im.width, im.width))  # first frame of animations
        if im.width != 16:
            im = im.resize((16, 16), Image.NEAREST) if im.width < 16 else im
        im = im.resize((16 * scale, 16 * scale), Image.NEAREST)
        img.alpha_composite(im, ((i % cols) * cell + 2, (i // cols) * cell + 2))
    img.save(out)


if __name__ == "__main__":
    folder, out = sys.argv[1], sys.argv[2]
    rels = sorted(str(p.relative_to(TEX)).replace("\\", "/") for p in (TEX / folder).glob("*.png"))
    sheet(rels, out, cols=int(sys.argv[3]) if len(sys.argv) > 3 else 16)

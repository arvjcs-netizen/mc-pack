"""Worn armor (models/armor/*_layer_1/2.png, 64x32), laid out on the 1.8 player-model UVs."""
from items import ARMOR_MATERIALS, ink_for
from lib import new, ramp, save


def box(u, v, w, h, d):
    """Face rectangles (x, y, w, h) of a model box in a 64x32 texture."""
    return {
        "top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h),
    }


HEAD = box(0, 0, 8, 8, 8)
BODY = box(16, 16, 8, 12, 4)
ARM = box(40, 16, 4, 12, 4)
LEG = box(0, 16, 4, 12, 4)


def paint_face(px, rect, r, rows=None, cols=None, chain=False, trim=None):
    """Fill part of a face. rows/cols: ranges inside the face to cover. Edges are bevelled."""
    x0, y0, w, h = rect
    rows = rows or range(h)
    cols = cols or range(w)
    rlo, rhi, clo, chi = min(rows), max(rows), min(cols), max(cols)
    for y in rows:
        for x in cols:
            c = r[2]
            if y == rlo:
                c = r[3]
            elif y == rhi:
                c = r[0] if trim is None else trim
            elif x == clo:
                c = r[3]
            elif x == chi:
                c = r[1]
            if chain and rlo < y < rhi and clo < x < chi and (x + y) % 2 == 0:
                continue
            px[x0 + x, y0 + y] = (*c, 255)


def layer1(base, chain=False):
    img = new(64, 32)
    px = img.load()
    r = ramp(base, (-0.55, -0.25, 0.0, 0.3))
    # helmet: full shell, with an opening on the face
    for face in ("top", "right", "left", "back"):
        paint_face(px, HEAD[face], r, rows=range(0, 8) if face == "top" else range(0, 7), chain=chain)
    fx, fy, _, _ = HEAD["front"]
    paint_face(px, (fx, fy, 8, 8), r, rows=range(0, 3), chain=chain)
    for side_cols in (range(0, 2), range(6, 8)):
        paint_face(px, (fx, fy, 8, 8), r, rows=range(2, 6), cols=side_cols, chain=chain)
    # chestplate: whole torso + shoulder pads on the arms
    for face in ("top", "front", "back", "right", "left"):
        paint_face(px, BODY[face], r, chain=chain)
    fx, fy, fw, fh = BODY["front"]
    for y in range(2, 10):  # center seam on the chest
        px[fx + 3, fy + y] = (*r[1], 255)
    for face in ("front", "back", "right", "left"):
        paint_face(px, ARM[face], r, rows=range(0, 5), chain=chain)
    paint_face(px, ARM["top"], r, chain=chain)
    # boots: bottom of each leg
    for face in ("front", "back", "right", "left"):
        paint_face(px, LEG[face], r, rows=range(8, 12), chain=chain, trim=ink_for(base))
    paint_face(px, LEG["bottom"], r, chain=False)
    return img


def layer2(base, chain=False):
    img = new(64, 32)
    px = img.load()
    r = ramp(base, (-0.55, -0.25, 0.0, 0.3))
    # leggings: belt at the bottom of the torso + upper legs
    for face in ("front", "back", "right", "left"):
        paint_face(px, BODY[face], r, rows=range(7, 12), chain=chain)
    fx, fy, fw, fh = BODY["front"]
    for x in range(fw):
        px[fx + x, fy + 8] = (*r[0], 255)  # belt line
    for face in ("front", "back", "right", "left"):
        paint_face(px, LEG[face], r, rows=range(0, 9), chain=chain)
    paint_face(px, LEG["top"], r, chain=chain)
    return img


def generate():
    for mat, base in ARMOR_MATERIALS.items():
        chain = mat == "chainmail"
        save(layer1(base, chain), f"models/armor/{mat}_layer_1.png")
        save(layer2(base, chain), f"models/armor/{mat}_layer_2.png")
        if mat == "leather":
            save(new(64, 32), "models/armor/leather_layer_1_overlay.png")
            save(new(64, 32), "models/armor/leather_layer_2_overlay.png")

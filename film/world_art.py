"""Reusable dressing and practical props for the ensemble stage. All meshes face -Y."""

from math import pi, sin, cos
import bpy
from animate import part, empty, label, rgb
from props import geometry, CATALOG

SKIN = {"amber": "E9AA78", "umber": "9F6048", "bronze": "BC7956", "rose": "F0BA9D"}


def costume(base, look):
    joints = {o.get("shortfilm_joint"): o for o in base.children_recursive}
    for o in base.children_recursive:
        if o.type != "MESH":
            continue
        for old, new in [
            ("skin", SKIN[look["skin"]]),
            ("skin2", SKIN[look["skin"]]),
            ("brown", look["hair"]),
            ("mahogany", look["hair"]),
        ]:
            if max(abs(a - b) for a, b in zip(o.color, rgb(old))) < 0.0002:
                o.color = rgb(new)
                break
    spine = joints["spine"]
    uniform = look["uniform"]
    if uniform in ("gown", "dress"):
        # Gathered skirt with layered hem and a short overskirt.
        for z, w, depth, h, color in [
            (-0.26, 1.04, 0.72, 0.82, "ivory"),
            (-0.56, 1.18, 0.82, 0.30, "ivory"),
            (-0.67, 1.23, 0.86, 0.12, "cream"),
            (0.08, 0.81, 0.60, 0.10, "raspberry"),
        ]:
            fabric = look["coat"] if uniform == "dress" and color == "ivory" else color
            part((0, 0, z), (w, depth, h), fabric, spine, "cylinder")
        part((0.26, -0.29, 0.07), (0.24, 0.12, 0.16), "raspberry", spine, "sphere")
    elif uniform == "apron":
        part((0, -0.291, 0.22), (0.69, 0.03, 0.57), "cream", spine)
        part((0, -0.308, 0.23), (0.35, 0.025, 0.15), "gold", spine)
    elif uniform in ("satchel", "sash"):
        part(
            (0, -0.315, 0.43),
            (0.13, 0.05, 0.88),
            "brown" if uniform == "satchel" else "gold",
            spine,
            angle=(0, -0.62, 0),
        )
        if uniform == "satchel":
            part((0.33, -0.31, 0.10), (0.3, 0.16, 0.29), "brown", spine)
            part((0.33, -0.405, 0.13), (0.08, 0.025, 0.07), "gold", spine)
    elif uniform == "bandleader":
        for h in (0.20, 0.38, 0.56):
            part((0, -0.312, h), (0.52, 0.04, 0.044), "gold", spine)
        for side in (-1, 1):
            part((0, 0, 0.015), (0.32, 0.49, 0.09), "gold", joints["arm" + str(side)])
    elif uniform == "tunic":
        for side in (-1, 1):
            part((side * 0.25, -0.3, 0.29), (0.13, 0.04, 0.38), "cream", spine)
    head = joints["head"]
    hat = look["hat"]
    coat = look["coat"]

    def piece(pos, size, color, shape="box", angle=None):
        return part(pos, size, color, head, shape, angle)

    if hat in ("cap", "visor", "helmet", "beret"):
        piece((0, 0, 0.62), (0.98, 0.83, 0.19), coat, "cylinder")
        if hat != "beret":
            piece((0, -0.35, 0.57), (0.86, 0.49, 0.08), "navy" if hat == "cap" else coat)
        piece((-0.06 if hat == "beret" else 0, 0.01, 0.7), (0.85, 0.72, 0.30), coat, "sphere")
        piece((0, -0.4, 0.66), (0.13, 0.04, 0.10), "gold")
    if hat == "veil":
        part((0, 0.36, 0.12), (0.91, 0.10, 1.08), "FFF4DD", head, angle=(-0.13, 0, 0))
        for j in range(7):
            a = j * pi / 6
            piece(
                (0.40 * cos(a), -0.28, 0.59 + 0.15 * sin(a)),
                (0.18, 0.17, 0.17),
                "raspberry" if j % 2 else "ivory",
                "sphere",
            )
    if hat == "crown":
        piece((0, 0, 0.64), (0.93, 0.78, 0.16), "gold")
        for x in [-0.33, 0, 0.33]:
            piece((x, -0.25, 0.76), (0.21, 0.18, 0.26), "gold", "cone")
    if hat in ("curls", "bun"):
        for n in range(8):
            a = n * pi / 4
            piece((0.34 * cos(a), 0.26 * sin(a), 0.56), (0.35, 0.34, 0.34), look["hair"], "sphere")
        if hat == "bun":
            piece((0, 0.25, 0.79), (0.48, 0.48, 0.45), look["hair"], "sphere")
    if hat == "bow":
        for side in (-1, 1):
            piece((0.24 + side * 0.13, -0.26, 0.64), (0.27, 0.12, 0.21), "red", angle=(0, side * 0.33, 0))
        piece((0.24, -0.3, 0.64), (0.12, 0.13, 0.13), "gold")

    form = look.get("form", "human")
    if form in ("rock", "paper"):
        stone = form == "rock"
        for obj in base.children_recursive:
            if obj.type != "MESH" or obj.get("shortfilm_joint", "").startswith(("eye", "mouth", "brow")):
                continue
            if max(abs(x - y) for x, y in zip(obj.color, rgb(SKIN[look["skin"]]))) < 0.0002:
                obj.color = rgb("A7A0A6" if stone else "FFF0D4")
        if stone:
            for side in (-1, 1):
                part(
                    (side * 0.44, 0.01, 0.40),
                    (0.45, 0.64, 0.65),
                    "8B8997",
                    spine,
                    angle=(0.06, side * 0.19, 0),
                )
                part(
                    (0, -0.04, -0.22),
                    (0.49, 0.57, 0.40),
                    "A5A2AB",
                    joints[f"arm{side}"],
                    angle=(0, side * 0.12, 0),
                )
                part(
                    (side * 0.23, -0.31, 0.46),
                    (0.18, 0.14, 0.095),
                    "BCB9B5",
                    head,
                    angle=(0, side * 0.23, 0),
                )
        else:
            part((0, -0.31, 0.38), (0.79, 0.05, 0.71), "F5E5C7", spine)
            for side in (-1, 1):
                part(
                    (side * 0.20, -0.35, 0.39),
                    (0.021, 0.026, 0.77),
                    "C6AA8C",
                    spine,
                    angle=(0, side * 0.43, 0),
                )
    elif form == "scissors":
        for side in (-1, 1):
            wrist = joints[f"wrist{side}"]
            part((0, 0.01, -0.23), (0.34, 0.32, 0.11), "raspberry", wrist, "ring", (pi / 2, 0, 0))
            part((0, 0.02, -0.63), (0.14, 0.13, 0.68), "C6D1D6", wrist, "sail", (0.03, side * 0.17, 0))


def chest_badge(rig, text):
    if not text:
        return
    spine = rig["spine"]
    part((0, -0.312, 0.46), (0.49, 0.045, 0.44), "ivory", spine)
    label(text, (0, -0.344, 0.465), 0.32, "navy", spine)


def sign(text, xyz, width, height, color="navy", ink="ivory", parent=None):
    x, y, z = xyz
    part((x, y, z), (width, 0.12, height), color, parent)
    for side in (-1, 1):
        part((x + side * (width / 2 - 0.08), y - 0.07, z), (0.04, 0.02, height * 0.71), "gold", parent)
    return label(text, (x, y - 0.075, z), min(height * 0.61, width * 1.49 / max(1, len(text))), ink, parent)


def city(place):
    from story_sets import KITS, build

    if place["kit"] in KITS:
        build(place)
        return
    if place["kit"] in ("fairground", "glasshouse"):
        from festival import district

        district(place)
        return
    if place["kit"] in ("harbor", "boathouse"):
        coast(place)
        return
    wall, trim = place["wall"], place["trim"]
    kind = place["kit"]
    part((0, 5, -0.28), (75, 65, 0.5), "9FAFA9")
    # Raised pavement, inset brass tracks and two rows of alternating paving stones.
    part((0, 1, -0.115), (29, 13, 0.22), "E0CFAC")
    for row in range(8):
        y = -4.6 + row * 1.38
        for col in range(12):
            x = (col - 5.5) * 2.5 + (row % 2) * 1.25
            part(
                (x, y, -0.016),
                (2.47, 1.35, 0.031),
                ["DECDAA", "E5D5B4", "E3D3B0", "D8C7A8"][(col * 7 + row * 3) % 4],
            )
    # A sky cyclorama keeps the vertical opening and lateral camera moves inside the world.
    part((0, 23, 22), (180, 0.5, 50), "AAD8DD")
    for x, z in [(-14, 11), (-5.3, 9.2), (5.6, 12.3), (14, 8.9), (22, 14.5)]:
        for dx, dz, r in [(-1.0, 0, 1.3), (0, 0.25, 1.8), (1.08, -0.03, 1.3)]:
            part((x + dx, 21, z + dz), (r * 1.65, 0.38, r * 0.55), "E1E8D6", shape="sphere")
    # Far roofline remains visible through the open sides and above the central civic building.
    for i in range(-8, 9):
        x = i * 2.65
        h = 5 + ((i + 12) * 7 % 11) * 0.72
        part((x, 11, h / 2), (2.46, 2.3, h), ["ACC2C3", "B7C9C2", "9DB2BE", "C7CAC0"][(i + 8) % 4])
        part((x, 11, h + 0.11), (2.60, 2.5, 0.23), "91A8AE")
        for level in range(1, int(h)):
            for dx in (-0.62, 0.62):
                part((x + dx, 9.84, level), (0.46, 0.045, 0.47), "92A9AD")
    for x in (-8.9, 8.9):
        part((x, 3.9, 1.85), (5.2, 1.5, 3.7), wall)
        for dx in (-1.45, 0, 1.45):
            part((x + dx, 3.12, 1.9), (1.12, 0.12, 2.1), "39565F")
            part((x + dx, 3.03, 1.92), (1.2, 0.05, 0.10), trim)
        for n in range(11):
            part(
                (x - 2.5 + n * 0.49, 2.85, 3.24),
                (0.50, 1, 0.15),
                trim if n % 2 else "ivory",
                angle=(0.17, 0, 0),
            )
    # Each civic building advertises its own trade at the edge of the main action.
    if kind in ("arcade", "depot"):
        for side in (-1, 1):
            x = side * 4.34
            sign(
                ("BREAD" if side < 0 else "FLOWERS")
                if kind == "arcade"
                else ("PARCELS" if side < 0 else "COLLECT"),
                (x, 3.69, 3.27),
                1.87,
                0.39,
                trim,
            )
            part((x, 3.19, 0.84), (2.05, 0.6, 0.16), "brown")
            for j in range(5):
                xp = x + (j - 2) * 0.33
                if kind == "depot":
                    hh = 0.36 + 0.12 * (j % 2)
                    part((xp, 3.10, 0.92 + hh / 2), (0.31, 0.36, hh), "C39364")
                    part((xp, 2.91, 1.06), (0.07, 0.02, 0.27), "cream")
                elif side < 0:
                    part((xp, 3.11, 1.03), (0.36, 0.44, 0.23), "D6A566", shape="sphere")
                else:
                    part((xp, 3.11, 1.04), (0.24, 0.24, 0.24), "rust", shape="cylinder")
                    part((xp, 3.11, 1.26), (0.04, 0.04, 0.32), "teal")
                    part((xp, 3.11, 1.43), (0.22, 0.20, 0.22), "red" if j % 2 else "gold", shape="sphere")
    if kind == "garden":
        for x in [-5, -2.9, 3.1, 5]:
            tree(x, 4, 1.2)
        part((0, 5.0, 0.58), (12, 0.38, 1.16), wall)
    elif kind == "theater":
        part((0, 4.9, 2.8), (13, 0.45, 5.6), "703B4F")
        for i in range(-11, 12):
            part(
                (i * 0.55, 4.58, 2.65), (0.55, 0.43, 5.3), "A84953" if i % 2 else "8D394A", shape="cylinder"
            )
        for x in (-4.75, 4.75):
            for j in range(5):
                part(
                    (x + (j - 2) * 0.32, 3.5, 2.65),
                    (0.54, 0.58, 5.3),
                    "C35A55" if j % 2 else "AE424A",
                    shape="cylinder",
                )
            part((x, 3.42, 2.7), (1.75, 0.6, 0.16), "gold")
        for i in range(-6, 7):
            part((i * 0.79, 3.35, 5.25), (0.19, 0.19, 0.19), "F7D28A", shape="sphere")
    else:
        part((0, 4.65, 2.55), (12, 0.60, 5.1), wall)
        for x in [-5.65, -3.07, 3.07, 5.65]:
            part((x, 4.15, 2.35), (0.36, 0.47, 4.7), trim)
            for z in (0.15, 4.38):
                part((x, 4.05, z), (0.58, 0.52, 0.26), "ivory")
        for side in (-1, 1):
            x = side * 4.34
            part((x, 4.29, 2.17), (2.03, 0.13, 2.20), "40565B")
            for k in range(4):
                part((x - 0.82 + k * 0.55, 4.18, 2.15), (0.055, 0.06, 2.16), "gold")
            part((x, 4.14, 2.16), (2.13, 0.08, 0.07), "gold")
        part((0, 4.05, 4.52), (12.7, 0.85, 0.33), trim)
        if kind == "arcade":
            for x in [-1.95, 1.95]:
                part((x, 3.92, 1.9), (0.17, 0.25, 3.8), "gold")
            part((0, 4.28, 1.8), (3.8, 0.14, 3.6), "3A4F56")
        else:
            for x in [-2.2, -1.45, 1.6, 2.35]:
                part((x, 3.94, 0.44), (0.65, 0.67, 0.87), "B37D56")
                part((x, 3.57, 0.43), (0.10, 0.05, 0.9), "gold")
    if kind == "arcade":
        # A threshold, actual recessed car and overhead rail put riders physically behind closing doors.
        part((0, 2.09, 0.004), (3.5, 2.33, 0.022), "CDBB8F")
        for x in (-1.70, 1.70):
            part((x, 2.42, 1.5), (0.12, 2.75, 3.0), "5B7778")
            part((x, 0.94, 1.54), (0.16, 0.20, 3.08), "gold")
            for z in (0.36, 0.88, 1.43, 2.0, 2.57):
                part((x, 0.82, z), (0.12, 0.04, 0.05), "cream")
        part((0, 1.03, 3.04), (3.66, 0.38, 0.16), trim)
        for j in range(3):
            part(((j - 1) * 1.12, 1.04, 2.94), (0.28, 0.24, 0.07), "F2D992")
        part((0, 0.80, 0.02), (3.49, 0.10, 0.04), "gold")
    if kind == "theater":
        for j in range(23):
            x = (j - 11) * 0.56
            part((x, 1.7, 0.005), (0.55, 7, 0.025), "B68965" if j % 3 else "BC9471")
        for x in (-3.7, 3.7):
            part((x, 3.18, 2.83), (0.12, 0.14, 5.66), "navy")
        part((0, 3.17, 5.47), (7.55, 0.17, 0.12), "navy")
        for x in (-2.9, -1.5, 1.5, 2.9):
            part((x, 2.99, 5.31), (0.26, 0.39, 0.27), "navy")
            part((x, 2.76, 5.27), (0.22, 0.09, 0.20), "gold")
    if kind == "depot":
        for row in range(4):
            for i in range(18):
                part(
                    ((i - 8.5) * 0.65 + (row % 2) * 0.22, 4.32, 0.32 + row * 0.24),
                    (0.63, 0.055, 0.22),
                    "B88965" if (i + row) % 3 else "C19977",
                )
        for side in (-1, 1):
            for z in (0.35, 0.95, 1.55):
                part((side * 3.91, 2.9, z), (1.46, 0.47, 0.09), "navy")
                for j in range(3):
                    x = side * 3.91 + (j - 1) * 0.44
                    part((x, 2.92, z + 0.23), (0.41, 0.37, 0.36), "B9885F")
                    part((x, 2.72, z + 0.21), (0.10, 0.025, 0.37), "cream")
    sign(place["sign"], (0, 3.65, 4.56), 6.0, 0.66, "navy")
    for side in (-1, 1):
        tree(side * 6.55, 1.3, 1.05)
        x = side * 5.55
        part((x, 2.15, 1.46), (0.14, 0.14, 2.92), "384951")
        part((x, 2.15, 2.96), (0.48, 0.48, 0.55), "F3CC84")
        part((x, 2.15, 3.30), (0.64, 0.64, 0.15), "navy")
        part((x, 2.15, 0.12), (0.4, 0.4, 0.24), "navy")
    for x in (-3, 3):
        part((x, -1.7, 0.005), (0.036, 5, 0.014), "B19568")


def coast(place):
    trim = place["trim"]
    if place["kit"] == "boathouse":
        part((0, 2, -0.16), (23, 17, 0.29), "AE876D")
        for i in range(-11, 12):
            part((i * 0.69, 1.7, -0.007), (0.67, 9, 0.022), "B88F70" if i % 3 else "C39770")
        part((0, 5.8, 6.3), (70, 1, 13), "BCACA0")
        part((0, 4.3, 2.73), (14, 0.38, 5.46), place["wall"])
        part((0, 2.6, 5.23), (16, 4, 0.25), "896C60")
        for x in (-4.6, 0, 4.6):
            part((x, 2.35, 4.92), (0.2, 3.9, 0.24), "70574E")
        for i in range(-9, 10):
            part((i * 0.7, 4.08, 1.2), (0.68, 0.14, 2.4), "9C665B" if i % 3 else "AF7864")
        for x in (-4.8, -2.8, 0.1, 3.7):
            part((x, 4, 2.63), (0.17, 0.27, 5.26), trim)
        for x in (-3.75, 3.1):
            part((x, 3.79, 2.7), (1.80, 0.20, 2.12), "gold")
            part((x, 3.65, 2.7), (1.58, 0.045, 1.91), "91B9BD")
            part((x, 3.60, 2.68), (1.6, 0.04, 0.07), "cream")
        for x in (-4.1, 3.5):
            part((x, 1.4, 0.30), (0.70, 0.65, 0.6), "navy", shape="cylinder")
            part((x, 1.4, 0.68), (0.92, 0.85, 0.23), "rust")
            part((x, 1.76, 1.04), (0.94, 0.14, 0.72), "rust")
        sign(place["sign"], (0, 3.70, 4.08), 5.7, 0.67, trim)
        return
    # The water gap spans x=-1.25 to +1.25. All movement across it must use the story's bridge.
    part((0, 1, -1.12), (100, 85, 0.45), "418D9B")
    part((0, 24, 17), (160, 0.8, 46), "E4AC95")
    part((-3.4, 20, 4.1), (3.6, 3.6, 0.16), "FFD58A", shape="cylinder", angle=(pi / 2, 0, 0))
    for j in range(9):
        color = ["F3C49E", "EFC1A5", "EBB8A4", "E5B1A4", "DCABA7", "D6A8A9", "CFA6AC", "C6A6B0", "BFA5B2"][
            j
        ]
        part((0, 22.88, 0.30 + j * 1.22), (140, 0.13, 1.24), color)
    for x, z in [(-10, 5.9), (-4.8, 6.1), (1.4, 5.8), (8.2, 7.0), (14, 4.9)]:
        for dx, dz, w in [(-0.9, 0, 2.1), (0, 0.21, 2.9), (1.08, -0.04, 2.3)]:
            part((x + dx, 18.5, z + dz), (w, 0.30, 0.54), "F4CDB8", shape="sphere")
    for j in range(72):
        x = ((j * 37) % 65 - 32) * 0.57
        y = ((j * 13) % 25 - 6) * 0.72
        part((x, y, -0.88), (1.14 + (j % 5) * 0.21, 0.12, 0.025), "71A6A8" if j % 3 else "A3BCAD")
    for side in (-1, 1):
        for j in range(18):
            x = side * (1.47 + j * 0.45)
            part((x, 0.93, -0.09), (0.44, 4.0, 0.17), "B38368" if j % 4 else "C39775")
        part((side * 5.25, -1.04, -0.26), (8.05, 0.16, 0.26), "754E4B")
        for j in range(6):
            x = side * (1.37 + j * 1.48)
            for yy in (-0.94, 2.78):
                part((x, yy, -0.56), (0.25, 0.25, 1.33), "745451")
                if j > 0 and yy > 1:
                    part((x, yy, 0.49), (0.21, 0.21, 0.99), "AE7E5F")
                    part((x, yy, 0.99), (0.31, 0.31, 0.1), "gold")
        for j in range(5):
            x = side * (3 + j * 1.50)
            part((x + side * 0.71, 2.78, 0.70), (1.47, 0.085, 0.085), "AE8F6C")
        for i in range(3):
            x = side * (4.4 + 2.9 * i)
            y = 5.2 + 0.35 * i
            part((x, y, 1.05), (2.38, 2.0, 2.4), ["A76A5B", "BB9074", "92848C"][i])
            for k in (-1, 1):
                part((x + k * 0.64, y, 2.50), (1.66, 2.22, 0.20), trim, angle=(0, k * 0.43, 0))
                part((x + k * 0.52, y - 1.02, 1.42), (0.58, 0.07, 0.63), "F3CB86")
            part((x, y - 1.04, 0.68), (0.5, 0.10, 1.36), "685159")
    for j in range(8):
        x = (j - 3.5) * 4
        part((x, 11.0, -0.32), (6.4, 2.1, 2.5 + (j % 3)), "718D94", shape="sphere")
    # Light station and striped channel buoy establish geography from across the water.
    for i in range(5):
        part(
            (3.25, 7.1, 0.47 + i * 0.76),
            (1.0 - i * 0.06, 1.0 - i * 0.06, 0.76),
            "ivory" if i % 2 == 0 else "rust",
            shape="cylinder",
        )
    part((3.25, 7.1, 4.21), (0.88, 0.88, 0.67), "F6CB78", shape="cylinder")
    part((3.25, 7.1, 4.69), (1.22, 1.22, 0.35), "navy", shape="cone")
    for x, y in [(-7, 7), (-1, 8.3), (7, 7.7)]:
        part((x, y, -0.52), (0.83, 0.83, 0.44), "rust", shape="sphere")
        part((x, y, 0.17), (0.11, 0.11, 1.15), "cream")
    sign(place["sign"], (-4.66, 2.71, 2.68), 3.5, 0.53, trim)
    for x in (-6.12, -3.2):
        part((x, 2.73, 1.34), (0.11, 0.15, 2.68), "brown")


def tree(x, y, s):
    part((x, y, 0.26), (0.87, 0.87, 0.52), "AD7257")
    part((x, y, 1.02), (0.2, 0.20, 1.6), "brown")
    for dx, dy, z, r in [(0, 0, 2.1, 1.5), (-0.42, 0.02, 1.7, 0.91), (0.44, 0.12, 1.85, 1)]:
        part(
            (x + dx * s, y + dy * s, z * s),
            (r * s, r * 0.82 * s, r * s),
            "739F83" if dx == 0 else "80AC86",
            shape="sphere",
        )


def practical(spec):
    root = empty(spec["id"], spec["at"])
    kind, col = spec["kind"], spec["color"]

    def b(p, s, c, shape="box", angle=None):
        return part(p, s, c, root, shape, angle)

    lettering = None
    center = 0.56
    from story_objects import KINDS, build

    if kind in KINDS:
        center = build(kind, b, col)
    elif kind in ("raincloud", "bouquet", "cistern", "cake"):
        from festival import weather_prop

        center = weather_prop(kind, b, root)
    elif kind == "scoreboard":
        b((0, 0, 1.52), (2.43, 0.25, 2.96), "navy")
        for side in (-1, 1):
            b((side * 1.22, -0.06, 1.51), (0.075, 0.23, 3.03), "gold")
        label("COIN RANKING", (0, -0.151, 2.75), 0.22, "gold", root)
        last = spec["text"].upper()
        places = [
            ("1. ROOK", "126"),
            ("2. MAY", "98"),
            ("3. OTIS", "84"),
            ("4. JUNE", "73"),
            ("5. ELI", "0"),
        ]
        if "FIRST" in last or "LAST ROOK" in last:
            places[0], places[-1] = ("1. ELI", "133"), ("5. ROOK", "0")
        if "--" in last:
            places[0], places[-1] = ("1. ELI", "133"), ("5. ---", "---")
        for i, (name, score) in enumerate(places):
            z = 2.33 - i * 0.38
            b(
                (0, -0.15, z),
                (2.20, 0.05, 0.32),
                "724251" if i == 4 else "344963" if i % 2 == 0 else "2A3A50",
            )
            label(name, (-0.47, -0.19, z), 0.17, "ivory", root)
            label(score, (0.79, -0.19, z), 0.17, "gold", root)
        lettering = label("", (0, -0.18, 0.28), 0.17, "gold", root)
        center = 1.52
        root["readable_width"] = 2.65 * spec["scale"]
    elif kind == "skytype":
        # World-space lettering holds the same position in reverse angles.
        text_width = max(2.1, min(4.25, 0.25 * len(spec["text"]) + 0.40))
        b((0, 0.08, 0.11), (text_width, 0.08, 0.61), "293744")
        lettering = label("", (0, -0.015, 0.13), 0.32, "ivory", root)
        b((text_width * 0.42, -0.021, -0.12), (0.14, 0.05, 0.047), "gold")
        center = 0.12
        root["readable_width"] = (text_width + 0.20) * spec["scale"]
    elif kind in ("board", "signal"):
        root["readable_width"] = 2.43 * spec["scale"]
        b((0, 0.04, 0.39), (0.15, 0.23, 0.78), "navy")
        b((0, 0.04, 0.06), (0.72, 0.49, 0.12), "navy")
        b((0, 0, 0.99), (2.23, 0.20, 1.11), col)
        b((0, -0.11, 0.99), (2.10, 0.03, 0.98), "243E47")
        for x in (-0.96, 0.96):
            b((x, -0.14, 0.99), (0.05, 0.04, 0.80), "gold")
        lettering = label("", (0, -0.15, 0.99), 0.35, "ivory", root)
        center = 0.99
    elif kind == "door":
        b((0, 0, 1.46), (1.55, 0.25, 2.92), col)
        for x in (-0.54, 0.54):
            b((x, -0.145, 1.5), (0.055, 0.04, 2.68), "gold")
        b((0, -0.15, 1.71), (0.95, 0.045, 0.76), "537981")
        for x in (-0.29, 0, 0.29):
            b((x, -0.18, 1.7), (0.035, 0.04, 0.77), "gold")
        b((0, -0.15, 0.58), (0.93, 0.05, 0.34), "navy")
        center = 1.6
    elif kind == "parcel":
        b((0, 0, 0.27), (0.74, 0.54, 0.54), col)
        b((0, -0.002, 0.275), (0.13, 0.56, 0.56), "cream")
        lettering = label("", (0.02, -0.289, 0.3), 0.27, "navy", root)
        center = 0.28
    elif kind == "trophy":
        b((0, 0, 0.10), (0.64, 0.45, 0.20), "navy")
        b((0, 0, 0.32), (0.14, 0.14, 0.28), "gold", "cylinder")
        b((0, 0, 0.55), (0.60, 0.46, 0.46), "gold", "sphere")
        for side in (-1, 1):
            b((side * 0.27, 0, 0.56), (0.31, 0.31, 0.09), "gold", "ring", (pi / 2, 0, 0))
        lettering = label("", (0, -0.245, 0.56), 0.24, "navy", root)
        center = 0.46
    elif kind == "trumpet":
        b((0, 0, 0.25), (0.70, 0.19, 0.19), "gold")
        b((0.37, 0, 0.25), (0.48, 0.48, 0.49), "gold", "horn", (0, pi / 2, 0))
        for x in (-0.16, -0.02, 0.12):
            b((x, 0, 0.39), (0.06, 0.08, 0.21), "cream")
        b((-0.37, 0, 0.25), (0.16, 0.14, 0.14), "ivory")
        center = 0.25
    elif kind == "goose":
        b((0, 0, 0.37), (0.85, 0.53, 0.58), "ivory", "sphere")
        b((0.31, 0, 0.70), (0.28, 0.35, 0.62), "ivory")
        b((0.34, -0.02, 0.98), (0.47, 0.42, 0.40), "ivory", "sphere")
        b((0.56, -0.08, 0.94), (0.33, 0.30, 0.13), "gold")
        for x in (-0.2, 0.19):
            b((x, -0.04, 0.07), (0.25, 0.32, 0.1), "gold")
        b((0.38, -0.21, 1.03), (0.065, 0.035, 0.065), "ink")
        b((0.34, 0, 1.18), (0.49, 0.44, 0.06), "navy")
        b((0.34, 0, 1.27), (0.32, 0.32, 0.17), "navy")
        center = 0.6
    elif kind == "clock":
        b((0, 0, 0.57), (1.05, 1.05, 0.20), col, "cylinder", (pi / 2, 0, 0))
        b((0, -0.12, 0.57), (0.91, 0.91, 0.052), "cream", "cylinder", (pi / 2, 0, 0))
        for j in range(12):
            a = j * pi / 6
            b(
                (sin(a) * 0.375, -0.156, 0.57 + cos(a) * 0.375),
                (0.038, 0.035, 0.08),
                "navy",
                angle=(0, a, 0),
            )
        b((0, -0.173, 0.72), (0.04, 0.035, 0.31), "navy")
        b((0.105, -0.185, 0.61), (0.23, 0.033, 0.047), "rust", angle=(0, -0.28, 0))
    elif kind == "radio":
        b((0, 0, 0.39), (1.13, 0.55, 0.69), col)
        for j in range(6):
            b((-0.20, -0.30, 0.23 + j * 0.064), (0.54, 0.038, 0.024), "navy")
        b((0.35, -0.29, 0.4), (0.18, 0.10, 0.18), "gold", "sphere")
        b((0.36, 0.02, 0.96), (0.035, 0.035, 0.69), "steel", angle=(0, 0.18, 0))
    elif kind == "mark":
        center = 0
    elif kind in ("lamp", "lantern"):
        b((0, 0, 0.08), (0.48, 0.39, 0.14), col)
        b((0, 0, 0.37), (0.34, 0.27, 0.47), "F8CE78")
        for x in (-0.20, 0.20):
            for y in (-0.145, 0.145):
                b((x, y, 0.38), (0.046, 0.04, 0.50), col)
        b((0, 0.152, 0.38), (0.39, 0.075, 0.46), col)
        b((0, -0.173, 0.38), (0.27, 0.27, 0.065), "ivory", "cylinder", (pi / 2, 0, 0))
        b((0, 0, 0.65), (0.51, 0.42, 0.13), col)
        b((0, 0, 0.77), (0.28, 0.28, 0.05), "gold", "ring", (pi / 2, 0, 0))
        center = 0.38
    elif kind == "mirror":
        b((0, 0.03, 0.53), (1.04, 0.13, 0.93), "gold")
        b((0, -0.053, 0.53), (0.91, 0.04, 0.82), "A0D3D3")
        for x, z, h in [(-0.22, 0.65, 0.36), (-0.06, 0.64, 0.58), (0.14, 0.37, 0.26)]:
            b((x, -0.081, z), (0.043, 0.02, h), "E6EEE0", angle=(0, 0.57, 0))
        b((0, 0, 0.03), (0.17, 0.13, 0.32), "brown")
        center = 0.52
    elif kind == "drum":
        b((0, 0, 0.49), (0.99, 0.99, 0.60), col, "cylinder", (pi / 2, 0, 0))
        for y in (-0.32, 0.32):
            b((0, y, 0.49), (1.04, 1.04, 0.072), "gold", "cylinder", (pi / 2, 0, 0))
        b((0, -0.367, 0.49), (0.93, 0.93, 0.045), "DBCA8E", "cylinder", (pi / 2, 0, 0))
        for x, z, h in [(-0.19, 0.66, 0.34), (-0.05, 0.56, 0.58), (0.18, 0.40, 0.25)]:
            b((x, -0.396, z), (0.038, 0.018, h), "ivory", angle=(0, 0.55, 0))
        for x in (-0.34, 0.34):
            for z in (0.24, 0.73):
                b((x, 0, z), (0.054, 0.79, 0.06), "cream")
        center = 0.49
    elif kind == "hatch":
        # Open well with a real aperture and two sliding brass leaves, built from separate side walls.
        for x in (-0.78, 0.78):
            b((x, 0, 0.46), (0.13, 1.07, 0.92), col)
            b((x, 0, 0.91), (0.18, 1.10, 0.10), "gold")
        for y in (-0.48, 0.48):
            b((0, y, 0.44), (1.48, 0.11, 0.88), col)
            b((0, y, 0.91), (1.67, 0.16, 0.10), "gold")
        b((0, 0, 0.12), (1.44, 0.90, 0.07), "ink")
        for side in (-1, 1):
            flap = b((side * 0.35, 0, 0.91), (0.70, 0.80, 0.055), "navy")
            flap["hatch_leaf"] = side
        label("RETURNS", (0, -0.545, 0.48), 0.22, "ivory", root)
        center = 0.7
    elif kind in ("stand", "bench"):
        h = 0.84 if kind == "stand" else 0.52
        b((0, 0, h), (1.64, 0.75, 0.15), col)
        for x in (-0.6, 0.6):
            b((x, 0, h / 2), (0.17, 0.54, h), "navy")
        center = h
    elif kind == "custom":
        heights = []
        for piece in spec["parts"]:
            b(
                piece["at"],
                piece["size"],
                piece["color"],
                piece["shape"],
                tuple(a * pi / 180 for a in piece["rotation"]),
            )
            heights.append(piece["at"][2] + piece["size"][2] / 2)
        center = max(heights) / 2
    elif kind in CATALOG:
        g = geometry(dict(kind=kind))
        center = 0.55
        for q in g["pieces"]:
            sh = q["shape"]
            if sh == "surface":
                sh = bpy.data.meshes.new("Inlay")
                sh.from_pydata(q["vertices"], [], q["faces"])
                sh.update()
            b(
                q["pos"],
                q["size"],
                col if q["color"] == "prop_paint" else q["color"],
                sh,
                tuple(a * pi / 180 for a in q["rotation"]),
            )
    root.scale = [spec["scale"]] * 3
    return root, lettering, center * spec["scale"]

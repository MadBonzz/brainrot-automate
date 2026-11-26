"""Blender second-unit camera and miniature locations for shots with a long sight line."""

import json
import math
import random
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import animate as art
from surface_art import finish

TAU = math.tau
STONE = ("AC786B", "C28D73", "937366", "DAAB7B", "B88978")
ROOFS = ("8B4146", "9B5E44", "3C6072", "885052", "715761")
COATS = ("CF5A49", "318A91", "F2BB51", "487BB2", "A270AF", "63A866", "E1DACB")


def box(x, y, z, w, d, h, color, shape="box", parent=None, tilt=None):
    return art.part((x, y, z), (w, d, h), color, parent, shape, tilt)


def beam(a, b, radius, color, parent=None):
    v, w = Vector(a), Vector(b)
    obj = art.part((v + w) / 2, (radius, radius, (w - v).length), color, parent, "cylinder")
    obj.rotation_euler = (w - v).to_track_quat("Z", "Y").to_euler()
    return obj


def drift(obj, change, frames, start=1):
    initial = obj.location.copy()
    obj.keyframe_insert(data_path="location", frame=start)
    obj.location = initial + Vector(change)
    obj.keyframe_insert(data_path="location", frame=frames)


def house(x, y, size, seed, base=0, night=False):
    r = random.Random(seed)
    w, d, h = 2.5 * size, 2 * size, r.uniform(1.8, 3.1) * size
    wall = r.choice(STONE) if not night else r.choice(("3F3F58", "58485C", "38495E"))
    facade = box(x, y, base + h / 2, w, d, h, wall)
    facade["surface_finish"] = "brick"
    roof = r.choice(ROOFS)
    for side in (-1, 1):
        box(
            x + side * w * 0.25,
            y,
            base + h + w * 0.095,
            w * 0.57,
            d * 1.12,
            0.15 * size,
            roof,
            tilt=(0, side * 0.35, 0),
        )
        for z in [0.46, 0.78] if h > 2.4 * size else [0.59]:
            box(
                x + side * w * 0.32,
                y - d * 0.503,
                base + h * z,
                w * 0.15,
                0.075 * size,
                h * 0.23,
                "BAE2E5" if not night else "FFBD66",
            )
            box(
                x + side * w * 0.32,
                y - d * 0.532,
                base + h * z,
                0.048 * size,
                0.06 * size,
                h * 0.24,
                "775642",
            )
    box(x, y - d * 0.51, base + 0.39 * size, 0.51 * size, 0.12 * size, 0.8 * size, "473F44")
    box(x + w * 0.29, y + d * 0.22, base + h + 0.33 * size, 0.3 * size, 0.38 * size, 0.85 * size, "71544C")


def person(x, y, z, size, i, turn=0):
    root = art.empty("Resident", (x, y, z))
    root.rotation_euler.z = turn
    c = COATS[i % len(COATS)]
    skin = ("CC946F", "DEA982", "B97E63", "E8B18A")[i % 4]
    for sign in (-1, 1):
        box(sign * 0.17 * size, 0, 0.25 * size, 0.25 * size, 0.27 * size, 0.5 * size, "344250", parent=root)
        box(sign * 0.37 * size, 0, 0.76 * size, 0.13 * size, 0.24 * size, 0.42 * size, c, parent=root)
    box(0, 0, 0.76 * size, 0.55 * size, 0.36 * size, 0.55 * size, c, parent=root)
    box(0, 0, 1.22 * size, 0.43 * size, 0.39 * size, 0.42 * size, skin, parent=root)
    box(
        0,
        0.015 * size,
        1.43 * size,
        0.48 * size,
        0.44 * size,
        0.11 * size,
        ("443842", "685046", "935E40")[i % 3],
        parent=root,
    )
    return root


def tree(x, y, s, i):
    box(x, y, 0.65 * s, 0.25 * s, 0.27 * s, 1.3 * s, "725942")
    for j in range(3):
        box(
            x + math.sin(i + j * 2) * 0.31 * s,
            y + math.cos(i + j * 2) * 0.27 * s,
            (1.24 + j * 0.15) * s,
            (1.2 - j * 0.11) * s,
            (1.1 - j * 0.07) * s,
            (1.25 - j * 0.08) * s,
            ("66915D", "81A967", "467662")[(i + j) % 3],
            "sphere",
        )


def cloud(x, y, z, s):
    for j, (a, b, h) in enumerate([(-0.6, 0, 0), (0, 0.08, 0.25), (0.61, 0, 0.06), (0, -0.25, -0.08)]):
        box(
            x + a * s,
            y + b * s,
            z + h * s,
            (1.5 - j * 0.08) * s,
            0.95 * s,
            0.63 * s,
            ("D9E6EF", "ECF1F6", "E1EDF4", "C1D4E3")[j],
            "sphere",
        )


def ribbon_mesh(name, rings, color, smooth=False):
    verts = [v for ring in rings for v in ring]
    sides = len(rings[0])
    faces = [
        (j * sides + k, j * sides + (k + 1) % sides, (j + 1) * sides + (k + 1) % sides, (j + 1) * sides + k)
        for j in range(len(rings) - 1)
        for k in range(sides)
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.color = art.rgb(color)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    return obj


def hills(tint):
    for i in range(29):
        a = i * TAU / 29
        x, y = 42 * math.sin(a), 8 + 42 * math.cos(a)
        obj = box(x, y, -1, 12 + i % 5, 11 + i % 7, 7 + i % 7, tint, "sphere")
        obj["surface_finish"] = "stone"


def serpent(frames):
    path = (
        [(x, 10) for x in range(15, 0, -1)]
        + [(0, y) for y in range(10, 0, -1)]
        + [(x, 0) for x in range(0, -6, -1)]
        + [(-6, y) for y in range(0, -5, -1)]
    )
    rings = []
    for i, (x, y) in enumerate(path):
        a = Vector(path[max(0, i - 1)])
        b = Vector(path[min(len(path) - 1, i + 1)])
        d = (b - a).normalized()
        normal = Vector((-d.y, d.x))
        radius = min(1, (i + 1) / 8) * (0.84 + 0.035 * math.sin(i))
        rings.append(
            [
                (
                    x + normal.x * radius * math.cos(k * TAU / 16),
                    y + normal.y * radius * math.cos(k * TAU / 16),
                    0.48 + radius * 0.79 * math.sin(k * TAU / 16),
                )
                for k in range(16)
            ]
        )
        if i % 2 == 0 and i > 3:
            box(x, y, 1.06, 0.46, 0.52, 0.16, "90945B", "sphere")
    skin = ribbon_mesh("A continuous body bends around the blocks", rings, "3D604D", True)
    skin["surface_finish"] = "scales"
    head = art.empty("Serpent head", (-6, -4.22, 0.64))
    box(0, -0.35, 0, 1.9, 2.1, 1.0, "42664F", "sphere", head)
    box(0, -0.72, -0.38, 1.62, 1.36, 0.32, "AD936C", "sphere", head)
    for side in (-1, 1):
        box(side * 0.67, -0.73, 0.28, 0.48, 0.39, 0.41, "F7C349", "sphere", head)
        box(side * 0.71, -0.90, 0.3, 0.12, 0.11, 0.22, "252F32", "sphere", head)
        for k in range(3):
            box(
                side * (0.48 + k * 0.13),
                -1.1 + k * 0.16,
                -0.26,
                0.14,
                0.14,
                0.30,
                "F8E5BC",
                "cone",
                head,
                (math.pi, 0, 0),
            )
    drift(head, (0, -0.78, 0.09), frames)


def town(frames, kind):
    canyon = kind in ("canyon_town", "canyon_dusk")
    dusk = kind == "lift_square"
    box(0, 8, -0.18, 130, 140, 0.36, "BF9066" if canyon else "AD9D84" if not dusk else "826874")
    for col in range(-3, 4):
        x = col * 6 + 3
        for j in range(-2, 7):
            y = j * 5.2 + 2.5
            if abs(x) < 5 and -12 < y < 6 and kind in ("clock_town", "lift_square"):
                continue
            house(x, y, 0.87 + (j + col) % 3 * 0.1, j * 56 + col + 88, night=dusk)
        box(x - 3, 8, 0.016, 1.8, 85, 0.028, "A39784" if canyon else "7F8383")
    for j in range(-2, 7):
        box(0, j * 5.2, 0.029, 63, 1.4, 0.04, "9C9282" if canyon else "858788")
    for i in range(20):
        x = (i % 5 - 2) * 3.05
        y = (i // 5) * 4.3 - 2
        if kind == "serpent_streets":
            continue
        if i % 4 == 0:
            tree(x + 0.75, y, 0.75, i)
        else:
            person(x, y, 0.06, 0.34, i)
    if not canyon:
        hills("9F9E90" if dusk else "8DA78B")
    if canyon:
        for side in (-1, 1):
            for i in range(-4, 11):
                y = i * 3.7
                edge = 10 + 0.9 * math.sin(i * 1.9)
                for tier, color in enumerate(("925B43", "B57450", "CF9866", "A96849", "D69F70")):
                    x = side * (edge + tier * 0.48)
                    h = 1.48 + 0.15 * math.sin(i * 0.6 + tier)
                    box(
                        x,
                        y,
                        (tier + 0.5) * 1.35,
                        3.3,
                        4.2,
                        h,
                        color,
                        tilt=(0.04 * math.cos(i), 0, side * 0.06),
                    )
        shade = box(
            -7 if kind == "canyon_town" else -5.2,
            10,
            0.07,
            12 if kind == "canyon_town" else 18.8,
            60,
            0.05,
            "6F584D",
        )
        drift(shade, (2.2, 0, 0), frames)
        return (7.3, -13.6, 13.7), (0, 5, 1), (1.5, 3, -1.05), 31, "9BCAD9"
    if kind == "serpent_streets":
        serpent(frames)
        hills("9AAB85")
        return (-10, -12.8, 13.2), (-1, 3.6, 0.2), (2.3, 2.1, -1.1), 34, "B6E0EE"
    if kind == "lift_square":
        for x in (-1.15, 1.15):
            box(x, 0, 2.1, 0.38, 1.65, 4.2, "AD773C")
        box(0, 0, 4.12, 2.72, 1.7, 0.29, "F8C675")
        for x in (-0.54, 0.54):
            box(x, -0.40, 1.97, 1.06, 0.25, 3.88, "BB8A47")
        box(0, -0.58, 2, 0.05, 0.08, 3.6, "5B4842")
        box(0, -1.03, 0.1, 3.4, 2.8, 0.2, "B98555")
        return (6, -11, 5), (0, 0, 1.9), (-1.6, 1.2, -0.35), 39, "F0A36C"
    box(0, 1, 4.0, 3.4, 3.2, 8, "8D765E")
    for z in (0.5, 3.0, 6.5, 8):
        box(0, 1, z, 3.72, 3.45, 0.22, "D2AD7F")
    box(0, 1, 9.0, 3.6, 3.5, 2.0, "494954", "cone")
    box(0, -0.68, 6.4, 2.42, 2.42, 0.17, "F6D794", "cylinder", tilt=(math.pi / 2, 0, 0))
    for i in range(12):
        a = i * TAU / 12
        box(0.91 * math.sin(a), -0.8, 6.4 + 0.91 * math.cos(a), 0.10, 0.065, 0.23, "4D3C3E", tilt=(0, a, 0))
    beam((0, -0.84, 6.4), (0.03, -0.84, 7.12), 0.09, "463E3F")
    beam((0, -0.85, 6.4), (-0.38, -0.85, 6.67), 0.11, "463E3F")
    return (7, -13, 8), (0, 1, 5.7), (-2.0, 1.0, 0.26), 43, "ABCFE1"


def queue(frames):
    box(0, 12, -0.35, 130, 160, 0.7, "E4B474")
    for i in range(40):
        x = (-1 if i % 2 else 1) * (6 + i % 7 * 1.5)
        y = (i // 2) * 3 - 9
        box(
            x,
            y,
            -0.15,
            5 + i % 5,
            5 + i % 9,
            1.3 + i % 3 * 0.7,
            ("DC9F66", "ECC185", "D89762")[i % 3],
            "sphere",
        )
    for i in range(89):
        y = -9 + i * 0.78
        x = 2.65 * math.sin(y * 0.18) + 0.042 * y
        p = person(x, y, 0.015, 0.52, i, -0.45 * math.cos(y * 0.18))
        if i in (7, 13, 21):
            drift(p, (0.09, 0.22, 0), frames)
    hills("C09E79")
    for i in range(7):
        x = -6 + i % 2 * 1.4
        y = i * 7 - 5
        box(x, y, 0.77, 0.34, 0.34, 1.54, "756345", "cylinder")
        for a in range(5):
            t = a * TAU / 5
            box(
                x + 0.43 * math.sin(t),
                y + 0.43 * math.cos(t),
                1.65,
                1.42,
                0.44,
                0.19,
                "788951",
                tilt=(0, 0.16, t),
            )
    return (4.5, -8.6, 7.6), (0, 6, 0.1), (-1.3, 2.8, -0.7), 34, "E6CFAB"


def balloon(x, y, z, s, i, frames):
    root = art.empty("Suspended home", (x, y, z))
    col = ("B74E51", "DDB05A", "6F8EAB", "826CA1", "DA7859", "5B9588")[i % 6]
    rings = []
    for height, radius in (
        (1.31, 0.24),
        (1.52, 0.36),
        (1.86, 0.65),
        (2.35, 0.93),
        (2.82, 0.90),
        (3.20, 0.67),
        (3.43, 0.32),
        (3.49, 0.025),
    ):
        rings.append(
            [
                (radius * s * math.cos(k * TAU / 24), radius * s * math.sin(k * TAU / 24), height * s)
                for k in range(24)
            ]
        )
    for k in range(12):
        strips = [[row[(2 * k + j) % 24] for j in range(3)] for row in rings]
        skin = ribbon_mesh("Canvas panel", strips, col if k % 3 else "EEC991")
        skin.parent = root
    if i % 4 == 0:
        rider = person(0, 0, 0.28 * s, 0.31 * s, i)
        rider.parent = root
    box(0, 0, 0.13 * s, 0.91 * s, 0.82 * s, 0.48 * s, "99704C", parent=root)
    for side in (-1, 1):
        for back in (-1, 1):
            beam(
                (side * 0.38 * s, back * 0.33 * s, 0.35 * s),
                (side * 0.31 * s, back * 0.28 * s, 1.49 * s),
                0.044 * s,
                "715A4C",
                root,
            )
    for layer in range(3):
        box(0, 0, (0.02 + 0.14 * layer) * s, 0.95 * s, 0.85 * s, 0.042 * s, "E3B47B", parent=root)
    drift(root, (0.12 * math.sin(i) * s, 0.04 * s, 0.16 * math.cos(i) * s), frames)
    return root


def sky(frames, kind):
    if kind in ("balloon_fleet", "balloon_departure"):
        for i in range(40):
            x = (i % 6 - 2.55) * 3.9 + math.sin(i) * 1.1
            y = i // 6 * 4.3 - 3.7
            z = 2.5 + 2 * math.sin(i * 1.6)
            craft = balloon(x, y, z, 0.75 + (i % 3) * 0.16, i, frames)
            if kind == "balloon_departure":
                craft.location = Vector((x, y, z))
                drift(craft, (0.55 * math.sin(i), 0.25, -1.2 - i % 3 * 0.28), frames)
        for i in range(18):
            cloud((i % 6 - 2.5) * 6, i // 6 * 11 - 5, -5.2 + 1.5 * math.sin(i), 2.0 + i % 3)
        for i in range(0 if kind == "balloon_departure" else 9):
            y = i // 3 * 5
            x = (i % 3 - 1) * 4
            beam((x, y, 1.55), (x + 3.8, y + 0.8, 1.27), 0.035, "B89568")
        return (3, -10, 6.1), (-0.7, 5, 3.0), (-1.65, 2.6, 0.38), 32, "A9DFF0"
    box(0, 0, -4.9, 170, 170, 1.8, "31374A")
    box(0, 7, 4, 12.0, 10.5, 1.75, "637288", "cylinder")
    box(0, 7, 4.89, 12.3, 10.75, 0.31, "629B79", "cylinder")
    for i in range(19):
        a = i * 2.40
        rr = math.sqrt(i) * 1.07
        x = math.sin(a) * rr
        y = 7 + math.cos(a) * rr
        h = 1.6 + (i * 7 % 9) * 0.43
        box(x, y, 5 + h / 2, 0.68, 0.73, h, ("D5EBD9", "A6D5CC", "B9DEDA")[i % 3])
        for j in range(1, int(h / 0.43)):
            box(x, y - 0.39, 5 + j * 0.43, 0.51, 0.038, 0.12, "72B3C8")
        if i % 3 == 0:
            box(x, y, 5 + h + 0.25, 0.87, 0.89, 0.62, "80BAAD", "sphere")
    for i in range(36):
        x = (i % 8 - 3.5) * 1.9
        y = (i // 8) * 2.5 - 3
        h = 1 + (i * 3 % 8) * 0.29
        box(x, y, -4 + h / 2, 1.25, 1.46, h, ("42465C", "4E4563", "354866")[i % 3])
        box(x, y - 0.74, -4 + h * 0.72, 1.18, 0.1, 0.13, ("E468BA", "59BBDD", "EE9462")[i % 3])
    for i in range(28):
        x = (i % 9 - 4) * 2.8
        y = 12 + (i // 9) * 3
        h = 2 + i % 4 * 0.9
        box(x, y, -4 + h / 2, 2, 2, h, "374862")
        for n in range(3):
            box(x, y - 1.01, -3 + n * 0.66, 1.1, 0.05, 0.13, "6288A3")
    for i in range(12):
        cloud((i % 5 - 2) * 5, 14 + i // 5 * 5, 1.5, 2.1)
    return (3.8, -11, 2.1), (0, 6.0, 3.9), (-1.4, 2.1, 1.2), 32, "8F9BCB"


def pool(frames):
    box(0, 5, -0.22, 12, 22, 0.44, "448AA6")
    box(0, 15, 3.8, 12, 0.34, 7.6, "B7C8C9")
    for side in (-1, 1):
        box(side * 6, 4, 3.7, 0.32, 23, 7.4, "AABCC7")
        box(side * 5.8, 4, 2.3, 0.19, 23, 0.24, "A23F49")
        for j in range(7):
            box(side * 5.79, 2 + j * 1.9, 4.9, 0.16, 1.45, 2.35, "A1D7E7")
            box(side * 5.67, 2 + j * 1.9, 4.9, 0.09, 0.08, 2.38, "CDD9D5")
    for i in range(48):
        x = (i % 8 - 3.5) * 1.3
        y = i // 8 * 3.1 - 3 + 0.4 * math.sin(i)
        wave = box(
            x,
            y,
            0.044,
            0.44 + i % 4 * 0.32,
            0.075,
            0.025,
            ("6FB2BE", "92C9C7", "559AAA")[i % 3],
            tilt=(0, 0, 0.11),
        )
        if i % 5 == 0:
            drift(wave, (0.26, 0.09, 0), frames)
    box(0, 14.7, 3.37, 3.1, 0.21, 1.85, "EEEEDE")
    box(0, 14.54, 3.37, 1.2, 0.10, 0.83, "BD5D4D")
    box(0, 14.44, 3.37, 0.99, 0.09, 0.64, "F4EDDD")
    box(0, 13.97, 2.91, 1.05, 1.05, 0.14, "D9533E", "ring")
    for i in range(8):
        a = i * TAU / 8
        beam(
            (0.48 * math.cos(a), 13.97 + 0.48 * math.sin(a), 2.9),
            (0.27 * math.cos(a + 0.25), 13.97 + 0.27 * math.sin(a + 0.25), 2.36),
            0.025,
            "F0DDC3",
        )
    ball = box(-0.76, 6.1, 0.30, 0.67, 0.67, 0.67, "E98B47", "sphere")
    drift(ball, (0.45, 0.19, 0.04), frames)
    return (2.75, -5.0, 2.25), (-0.2, 10.1, 1.9), (-0.65, 2.5, -0.1), 35, "B9DBE1"


def districts(frames):
    box(0, 7, -0.18, 74, 90, 0.36, "84925E")
    palette = ("77868B", "D9CBAC", "B16150")
    for col in range(3):
        x = (col - 1) * 7.1
        box(x, 5, 0.04, 6.8, 32, 0.10, palette[col])
        for j in range(6):
            y = j * 4.1 - 3
            if col == 0:
                house(x - 1.9, y, 0.64, j + col * 37)
            elif col == 1:
                box(x - 1.9, y, 0.63, 1.7, 1.4, 1.2, "ECE8D4")
                for side in (-1, 1):
                    box(x - 1.9 + side * 0.47, y, 1.54, 1.05, 1.54, 0.12, "FFFCED", tilt=(0, side * 0.53, 0))
                box(x - 1.9, y - 0.72, 0.41, 0.38, 0.04, 0.82, "877C75")
            else:
                box(x - 1.9, y, 1.0, 1.6, 1.25, 1.95, "944E46")
                for b in range(4):
                    box(x - 2.48 + b * 0.35, y, 2.23, 0.29, 0.32, 0.81, "B8C1BF", "cone")
                box(x - 1.9, y - 0.65, 0.92, 0.81, 0.08, 0.83, "473E46")
            if col == 0:
                for n in range(3):
                    box(x + 1.27 + n * 0.26, y + n * 0.33, 0.54, 0.94, 0.98, 1.07, "697783", "sphere")
            elif col == 1:
                for n in range(3):
                    box(x + 1.54, y, 0.23 + n * 0.19, 1.4, 1, 0.15, "F6E8CD", tilt=(0, 0, 0.11 * n))
            else:
                for side in (-1, 1):
                    beam((x + 1.32, y - 0.23, 0.08), (x + 1.32 + side * 0.39, y + 0.12, 1.31), 0.14, "C3C5BF")
        if col < 2:
            box(x + 3.48, 5, 0.62, 0.22, 32, 1.24, "5C6862")
            for j in range(12):
                box(x + 3.48, j * 2.4 - 7, 1.42, 0.48, 0.52, 0.39, "768171")
    hills("829C7F")
    return (-6.7, -13.6, 13.4), (0, 4.1, 0.35), (1.5, 3, -0.9), 35, "CCDDD7"


def border(frames):
    box(-7, 7, -0.22, 14, 54, 0.42, "929596")
    box(7, 7, -0.22, 14, 54, 0.42, "83B751")
    for j in range(9):
        y = -5 + j * 3.8
        for x in (-3.8, -7.4):
            box(x, y, 1.1, 2, 1.9, 2.22, ("ABABAB", "BDBDBD", "999999")[j % 3])
            for s in (-1, 1):
                box(x + s * 0.49, y - 0.96, 1.28, 0.4, 0.08, 0.62, "5E5E5E")
            box(x, y - 0.97, 0.5, 0.48, 0.1, 1, "717171")
        tree(4.5 + (j % 2) * 1.7, y, 1.4 + j % 3 * 0.18, j)
        for i in range(8):
            x = 0.8 + i * 0.44
            y2 = y + math.sin(i + j) * 0.7
            box(x, y2, 0.24, 0.045, 0.045, 0.45, "3F8151")
            box(x, y2, 0.47, 0.23, 0.23, 0.18, ("D955A7", "F5C34E", "D76DC8", "ED7461")[i % 4], "sphere")
    box(0, 7, 0.028, 0.29, 54, 0.065, "D82835")
    return (-1.8, -8.7, 4.5), (0.5, 3, 1.03), (1.5, 2.25, 0.25), 35, "B4C4CA"


def cells(frames):
    box(0, 3, -0.15, 17, 36, 0.3, "36454A")
    for side in (-1, 1):
        for floor in range(7):
            base = floor * 2.6
            box(side * 4.5, 3, base + 0.08, 2.8, 28, 0.2, ("637379", "495B61")[floor % 2])
            box(side * 5.85, 3, base + 1.3, 0.24, 28, 2.59, "3B494D")
            for n in range(9):
                y = -8 + n * 2.9
                box(side * 4.5, y, base + 1.32, 2.7, 0.14, 2.52, "4B575D")
                for b in range(5):
                    box(side * 3.52, y + 0.23 + b * 0.47, base + 1.31, 0.11, 0.10, 2.48, "839392")
                box(side * 3.51, y + 1.2, base + 1.73, 0.13, 2.51, 0.074, "718489")
                if (n + floor) % 4 == 1:
                    box(side * 5.47, y + 1.45, base + 1.75, 0.18, 0.54, 0.35, "F2CB79")
            if floor % 2 == 0:
                beam((side * 3, 13, base + 1.35), (-side * 3, 13, base + 1.35), 0.15, "88948D")
    for level in range(1, 5):
        z = level * 2.65
        box(0, 7 + level * 0.6, z, 6.9, 0.92, 0.17, "708583")
        for post in range(9):
            box(-3.2 + post * 0.8, 6.6 + level * 0.6, z + 0.47, 0.09, 0.07, 0.90, "A1AF9D")
        box(0, 6.6 + level * 0.6, z + 0.91, 6.54, 0.10, 0.11, "889C97")
    return (0.85, -8.2, 2.5), (0, 4.8, 6.9), (-0.42, 2.5, 1.0), 28, "748A92"


def shop(frames):
    box(0, 4, -0.16, 19, 31, 0.31, "566271")
    for j in range(10):
        box(0, j * 2.4 - 5, 0.018, 19, 0.035, 0.024, "92A0AA")
        box(-8 + j * 1.8, 4, 0.026, 0.03, 31, 0.025, "87949F")
    for side in (-1, 1):
        box(side * 7.8, 4, 2.99, 0.4, 27, 6, "505771")
        for n in range(5):
            y = 1.1 + n * 2.6
            box(side * 5.65, y, 1.35, 1.4, 0.14, 2.58, "394858")
            for j in range(4):
                box(side * 5.65, y - 0.15, 2.19 - j * 0.47, 1.65, 0.65, 0.11, "886D87")
            if n % 2:
                x = side * 2.85
                box(x, y - 1.76, 0.08, 0.82, 0.72, 0.16, "52616B")
                for sign in (-1, 1):
                    box(x + sign * 0.16, y - 1.76, 0.54, 0.23, 0.26, 0.89, "C9CCD0")
                    box(x + sign * 0.45, y - 1.76, 1.48, 0.18, 0.22, 0.76, "CDD0CF", tilt=(0, sign * 0.16, 0))
                box(x, y - 1.76, 1.40, 0.62, 0.41, 0.79, "CECFCE")
                box(x, y - 1.76, 2.07, 0.45, 0.43, 0.55, "D0D2CF", "sphere")
        box(side * 1.92, 7, 1.55, 0.077, 5, 0.09, "AEADB6")
        for j in range(12):
            col = ("526D88", "765A76", "826962", "465862")[j % 4]
            box(side * 1.92, 4.65 + j * 0.40, 1.15, 0.61, 0.14, 0.68, col)
    for j in range(4):
        box(0, 4 + j * 3.3, 4.95, 2.48, 0.17, 0.1, "C8D5E2")
    box(0, 14.1, 2.65, 16, 0.45, 5.3, "455067")
    box(0, 13.84, 1.45, 2.1, 0.10, 2.9, "303A4D")
    box(0, 13.70, 3.35, 1, 0.09, 0.38, "84CCB0")
    return (-1.1, -5.3, 1.61), (0.2, 5.2, 1.47), (0.65, 2.45, 0.12), 30, "566275"


def hall(frames):
    box(0, 13, -0.18, 7.1, 63, 0.36, "59485A")
    for n in range(13):
        y = n * 3.17 - 4
        for side in (-1, 1):
            box(side * 2.8, y, 1.6, 0.26, 3.18, 3.2, ("706379", "685D70")[n % 2])
            box(side * 2.6, y + 0.3, 1.26, 0.15, 1.18, 2.52, "433949")
            box(side * 2.48, y + 0.3, 2.57, 0.20, 1.32, 0.13, "AF8B7C")
            box(side * 2.46, y + 0.66, 1.18, 0.12, 0.11, 0.12, "D6AE78", "sphere")
            box(side * 1.91, y + 0.86, 2.45, 0.22, 0.25, 0.39, "ECBC80")
        box(0, y, 3.24, 5.85, 0.24, 0.23, "524A5F")
        box(0, y, 3.04, 0.78, 0.40, 0.11, "E9CAA0")
        box(0, y, 0.035, 1.8, 3.16, 0.06, ("924C56", "834653")[n % 2])
    person(0, 17, 0, 1.92, 3)
    return (0.66, -5.3, 1.62), (0, 9, 1.65), (-0.25, 3, 0.07), 32, "61586C"


def landing(frames):
    floor = box(0, 2, -0.12, 9, 13, 0.24, "6A4D47")
    floor["surface_finish"] = "wood"
    for side in (-1, 1):
        box(side * 3.15, 2, 1.7, 0.24, 13, 3.4, "B1957C")
        box(side * 3.00, 2, 1.06, 0.14, 13, 0.14, "765D4C")
    for i in range(4):
        x = (i - 1.5) * 1.54
        box(x, 6.9, 1.7, 1.56, 0.28, 3.4, "BFA381")
        box(x, 6.73, 1.17, 1.02, 0.13, 2.34, "695040")
        for z in (0.63, 1.53):
            box(x, 6.62, z, 0.76, 0.07, 0.62, "846449")
        box(x + 0.33, 6.54, 1.04, 0.12, 0.09, 0.12, "D7BA6D", "sphere")
        art.label(str(201 + i), (x, 6.51, 1.83), 0.18, "F6DFAB")
        box(x, 6.03, 0.02, 1.16, 0.61, 0.03, "955F4D")
    for i in range(3):
        box(-2.92, 1 + i * 2.6, 2.15, 0.19, 0.48, 0.43, "D3A277")
        box(-2.78, 1 + i * 2.6, 2.18, 0.16, 0.33, 0.27, "F7D99F")
    return (1.16, -1.85, 1.83), (-0.65, 6.71, 1.46), (-0.45, 1.43, 0.02), 36, "9D8376"


def detail(frames, kind, words):
    phone = kind == "phone_detail"
    box(0, 2, -0.25, 25, 25, 0.5, "715349" if not phone else "64545C")
    if phone:
        box(0, 0, 1.28, 1.34, 0.16, 2.49, "282C37")
        box(0, -0.10, 1.28, 1.21, 0.04, 2.29, "EBEEE9")
        box(0, -0.135, 2.09, 1.19, 0.02, 0.43, "486E80")
        art.label("RECENTS", (0, -0.159, 2.09), 0.17, "F8F5E9")
        box(0, -0.16, 1.72, 0.82, 0.014, 0.035, "B5CBCC")
        art.label("OUTGOING", (0, -0.16, 1.80), 0.116, "426371")
        art.label(words, (0, -0.165, 1.25), min(0.19, 1.95 / max(1, len(words))), "384A54")
        for i in range(3):
            box(-0.23 + 0.23 * i, -0.136, 0.37, 0.075, 0.022, 0.075, "8AACA8", "sphere")
        return (0.25, -2.35, 1.61), (0, 0, 1.30), (-0.16, 0.26, -0.03), 42, "655563"
    box(0, 0, 1.20, 2.02, 0.085, 1.29, "F0DEAF")
    for x in (-0.96, 0.96):
        box(x, -0.05, 1.2, 0.031, 0.018, 1.18, "B39871")
    box(0, -0.055, 1.62, 1.7, 0.02, 0.026, "B69C79")
    letters = words.split("|")
    for i, line in enumerate(letters):
        art.label(line, (0, -0.07, 1.39 - i * 0.23), min(0.25, 2.9 / max(1, len(line))), "4B3C37")
    box(-0.72, -0.059, 1.73, 0.14, 0.04, 0.14, "85623D", "sphere")
    beam((-0.72, -0.09, 1.72), (-1.12, -0.23, 2.06), 0.065, "679758")
    box(-1.11, -0.25, 2.16, 0.46, 0.45, 0.10, "CE9B46", "ring", tilt=(math.pi / 2, 0, 0))
    beam((-1.23, -0.25, 2.04), (-1.55, -0.25, 1.57), 0.092, "D5AA58")
    beam((-1.49, -0.25, 1.66), (-1.65, -0.25, 1.76), 0.096, "D5AA58")
    box(1.19, 0.15, 0.88, 0.57, 0.47, 0.53, "C38A67", tilt=(0.12, -0.13, -0.16))
    box(1.47, 0.14, 0.53, 0.68, 0.50, 0.55, "45536C", tilt=(0.12, -0.33, -0.16))
    box(0.97, -0.12, 0.85, 0.37, 0.22, 0.23, "D59E78", "sphere", tilt=(0.14, 0.17, 0))
    return (0.10, -3.15, 1.66), (-0.05, 0, 1.43), (-0.11, 0.25, -0.02), 39, "896B60"


def cinematography(scene, world, kind, width):
    # A low-bounce path-traced wide shot supplies contact shadows between the city and its inhabitants.
    if kind in (
        "paper_detail",
        "phone_detail",
        "apartment_landing",
        "endless_hall",
        "dark_shop",
        "flooded_gym",
        "cell_tower",
    ):
        # Small type, dark aisles and moving highlights must stay noiseless across frames.
        scene.display.shading.studio_light = "paint.sl"
        scene.display.shading.show_shadows = True
        scene.display.shading.shadow_intensity = 0.26
        scene.view_settings.exposure = (
            0.43 if kind in ("paper_detail", "phone_detail", "flooded_gym") else 0.08
        )
        return
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8 if width >= 1080 else 4
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 1
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.34
    world.use_nodes = True
    nodes = world.node_tree.nodes
    bg = nodes.get("Background")
    sky = nodes.new("ShaderNodeTexCoord")
    z = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    warm = kind in ("desert_queue", "lift_square", "canyon_dusk")
    ramp.color_ramp.elements[0].color = art.rgb("FFE2B2" if warm else "D9EAF3")
    ramp.color_ramp.elements[1].position = 0.61
    ramp.color_ramp.elements[1].color = art.rgb("8B94BF" if kind == "halo_city" else "629AC3")
    links = world.node_tree.links
    links.new(sky.outputs["Generated"], z.inputs[0])
    links.new(z.outputs["Z"], ramp.inputs[0])
    links.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.80
    sun = bpy.data.lights.new("Raking daylight", "SUN")
    sun.energy = 2.8
    sun.angle = math.radians(7)
    sun.color = (1, 0.88, 0.74) if warm else (1, 0.93, 0.83)
    lamp = bpy.data.objects.new("Raking daylight", sun)
    scene.collection.objects.link(lamp)
    lamp.rotation_euler = (math.radians(37), math.radians(-26), math.radians(-18))


def performance(job, view):
    from copy import deepcopy

    from ensemble_render import shoot as stage

    take = deepcopy(job["takes"][str(view["beat"])])
    shot = take["shot"]
    target = next(a for a in shot["actors"] if a["id"] == view["actor"])
    frames = take["frames"]
    first, last = view["start"], view["stop"]
    recipe_frames = job["motions"][view["action"]]["frames"]
    # Start the actor's anticipation just off camera. The incoming angle catches the change in pose.
    sec_ratio = job["fps"] / 24
    anticipation = min(6, max(1, round(recipe_frames * sec_ratio * 0.12)))
    target["cues"] = [
        {
            "action": view["action"],
            "start": max(0, (first - anticipation) / (frames - 1)),
            "end": min(1, (last + 1) / (frames - 1)),
            "play": "accent",
        }
    ]
    original = shot["cameras"][view["camera"] - 1]
    camera = {
        "start": first / (frames - 1),
        "focus": [view["actor"]],
        "size": 2.06,
        "angle": 27 if original["angle"] < 12 else -27,
        "elevation": 3,
        "drift": 0,
        "move": "punch",
    }
    # Preserve the location and performance clock. Only the lens and the actor's reply change.
    cameras = [dict(camera, start=0, move="hold"), camera] if first else [camera]
    if last < frames - 1:
        cameras.append(dict(camera, start=last / (frames - 1), move="hold"))
    shot["cameras"] = cameras
    scene = stage(take, job)
    scene.frame_start = first + 1
    scene.frame_end = last
    return scene


def write_view(scene, view):
    dst = Path(view["output"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dst.parent) as tmp:
        local = Path(tmp) / dst.name
        if "still" in view:
            scene.frame_set(
                max(scene.frame_start, min(scene.frame_end, scene.frame_start + view["still"] - 1))
            )
            scene.render.image_settings.file_format = "PNG"
            scene.render.filepath = str(local)
            bpy.ops.render.render(write_still=True)
        else:
            scene.frame_set(scene.frame_start)
            scene.render.image_settings.file_format = "FFMPEG"
            scene.render.ffmpeg.format = "MPEG4"
            scene.render.ffmpeg.codec = "H264"
            scene.render.ffmpeg.constant_rate_factor = "HIGH"
            scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
            scene.render.filepath = str(local)
            bpy.ops.render.render(animation=True)
        local.replace(dst)


def shoot(job, view):
    if view["kind"] == "reaction":
        write_view(performance(job, view), view)
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    art.mesh_cache.clear()
    art.job = job
    art.FPS = job["fps"]
    art.setup()
    scene = bpy.context.scene
    what = view["kind"]
    frames = view["stop"] - view["start"]
    if what in ("serpent_streets", "clock_town", "canyon_town", "canyon_dusk", "lift_square"):
        cam, aim, move, lens, sky_color = town(frames, what)
    elif what in ("balloon_fleet", "balloon_departure", "halo_city"):
        cam, aim, move, lens, sky_color = sky(frames, what)
    elif what in ("paper_detail", "phone_detail"):
        cam, aim, move, lens, sky_color = detail(frames, what, view.get("text", ""))
    else:
        sets = {
            "apartment_landing": landing,
            "desert_queue": queue,
            "flooded_gym": pool,
            "paper_districts": districts,
            "red_border": border,
            "cell_tower": cells,
            "dark_shop": shop,
            "endless_hall": hall,
        }
        cam, aim, move, lens, sky_color = sets[what](frames)
    scene.view_settings.exposure = 0.47 if what not in ("dark_shop", "endless_hall", "cell_tower") else 0.13
    shade = scene.display.shading
    shade.studio_light = "paint.sl"
    shade.show_shadows = True
    shade.shadow_intensity = 0.27
    shade.show_specular_highlight = False
    world = bpy.data.worlds.new("Horizon")
    world.color = art.rgb(sky_color)[:3]
    scene.world = world
    shade.background_type = "WORLD"
    # Keep far clouds behind the action so they provide parallax through the cut.
    if what not in (
        "dark_shop",
        "endless_hall",
        "cell_tower",
        "flooded_gym",
        "apartment_landing",
        "paper_detail",
        "phone_detail",
    ):
        for i in range(12):
            x = (i % 6 - 2.5) * 11
            y = 31 + (i // 6) * 13
            z = 6 + (i % 4) * 1.9
            cloud(x, y, z, 1.6 + i % 3)
    finish(scene)
    cinematography(scene, world, what, job["width"])
    camera = bpy.data.cameras.new("Location lens")
    o = bpy.data.objects.new("Location camera", camera)
    scene.collection.objects.link(o)
    camera.lens = lens
    camera.sensor_fit = "HORIZONTAL"
    scene.camera = o
    base = Vector(cam)
    target = Vector(aim)
    change = Vector(move)
    for f, t in ((1, 0.0), (frames, 1.0)):
        o.location = base + change * t
        look = target + change * (0.26 * t)
        o.rotation_euler = (look - o.location).to_track_quat("-Z", "Y").to_euler()
        o.keyframe_insert(data_path="location", frame=f)
        o.keyframe_insert(data_path="rotation_euler", frame=f)
    frame_limit = frames
    scene.frame_start = 1
    scene.frame_end = frame_limit
    scene.frame_set(1)
    write_view(scene, view)


if __name__ == "__main__":
    payload = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
    for piece in payload["pieces"]:
        shoot(payload, piece)

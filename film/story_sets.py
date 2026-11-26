"""Modular locations for enclosed and open-air narrative coverage."""

from math import pi
from animate import part, label

KITS = "bedroom vault classroom market aisle lockup belfry canyon grove dreamcourt rooftops corridor skyport undercity meadow duskfield".split()


def build(place):
    kind, trim, wall = place["kit"], place["trim"], place["wall"]

    def block(x, y, z, w, d, h, col, shape="box", angle=None):
        o = part((x, y, z), (w, d, h), col, shape=shape, angle=angle)
        if d > 40 or (w >= 13 and h < 0.5):
            o["surface_finish"] = "wood" if kind in ("bedroom", "classroom", "rooftops") else "stone"
        elif w > 100 and h > 30:
            o["surface_finish"] = "sky"
        elif shape == "box" and d >= 1 and w >= 2 and h >= 1:
            o["surface_finish"] = "stone" if kind == "canyon" else "brick"
        elif h > 4 and w > 8:
            o["surface_finish"] = "brick"
        elif w > 1 and d > 0.3 and h < 0.36:
            o["surface_finish"] = (
                "wood" if kind in ("market", "bedroom", "classroom", "rooftops") else "metal"
            )
        return o

    if kind == "undercity":
        undercity(block)
        return
    if kind in ("meadow", "duskfield"):
        meadow(block, place, kind == "duskfield")
        return
    night = place.get("light") == "night"
    sky = "313B66" if night else "62CDEE"
    if kind == "skyport":
        skyport(block, sky, trim)
        return
    outdoor = kind in ("canyon", "grove", "dreamcourt", "rooftops", "market")
    block(
        0, 7, -0.20, 100, 100, 0.40, ("B38462" if kind == "canyon" else "799B76") if outdoor else "847E8C"
    )
    block(0, 24, 17, 140, 0.5, 48, sky if outdoor else wall)
    if outdoor:
        for i in range(8):
            x = (i - 3.5) * 6
            z = 7 + (i * 7 % 5)
            for dx in (-0.92, 0, 0.92):
                block(
                    x + dx,
                    18,
                    z + (dx == 0) * 0.26,
                    2.72,
                    0.74,
                    0.90,
                    "7180A7" if night else "C6EDFF",
                    "sphere",
                )
    if kind in ("rooftops", "market"):
        for i in range(-5, 6):
            x = i * 3.8
            ht = 2.65 + (i * 3 % 4)
            brick = (wall, trim, "C98D76", "E8BA7B")[i % 4]
            block(x, 8, ht / 2, 3.55, 2.4, ht, brick)
            for side in (-1, 1):
                block(
                    x + side * 0.88,
                    8,
                    ht + 0.41,
                    2.06,
                    2.85,
                    0.21,
                    ("8D575E", "575C75")[i % 2],
                    angle=(0, side * 0.41, 0),
                )
                for level in (1.0, ht - 0.69):
                    block(x + side * 0.84, 6.74, level, 0.7, 0.12, 0.72, "FFE6AA" if night else "517F94")
                    block(x + side * 0.84, 6.64, level, 0.07, 0.04, 0.76, "cream")
        if kind == "market":
            for i, x in enumerate((-6, -3.65, 3.85, 6.30)):
                for side in (-1, 1):
                    block(x + side * 0.94, 3.62, 1.35, 0.09, 0.1, 2.67, "brown")
                block(x, 3.62, 0.74, 2.23, 0.95, 0.20, "brown")
                for k in range(7):
                    block(
                        x + (k - 3) * 0.31,
                        3.56,
                        2.68,
                        0.32,
                        1.29,
                        0.13,
                        trim if k % 2 else "cream",
                        angle=(0.15, 0, 0),
                    )
                for k in range(9):
                    block(
                        x + (k % 5 - 2) * 0.32,
                        3.48 + (k // 5) * 0.27,
                        0.96,
                        0.30,
                        0.3,
                        0.31,
                        ("gold", "raspberry", "mint")[i % 3],
                        "sphere",
                    )
        else:
            block(0, 0.9, -0.035, 22, 14, 0.09, "945E5C")
            for i in range(25):
                block((i - 12) * 0.75, 0.9, 0.014, 0.029, 14, 0.009, "AF7F71")
    elif kind in ("canyon", "grove", "dreamcourt"):
        for side in (-1, 1):
            for n in range(7):
                x = side * (5 + (n * 5 % 7))
                y = -1 + n * 2.6
                if kind == "canyon":
                    for k in range(4):
                        block(
                            x,
                            y,
                            k * 1.17 + 0.58,
                            3.2 - 0.26 * k,
                            3.17,
                            1.35,
                            ("A55544", "C77151", "E39B68", "F4BD82")[k],
                            angle=(0, side * 0.04, side * 0.10),
                        )
                elif kind == "grove":
                    block(x, y, 1.76, 0.57, 0.56, 3.52, "67483D")
                    for j in range(3):
                        block(
                            x + (j - 1) * 0.65,
                            y,
                            3.60 + (j % 2) * 0.66,
                            2.64,
                            2.40,
                            2.60,
                            (trim, wall, "498977")[j],
                            "sphere",
                        )
                else:
                    block(x, y, 1.3 + (0.7 * n), 2.1, 1.73, 0.45, ("BFA4E5", "E9C1E0")[n % 2], "sphere")
                    block(x, y, 1.52 + 0.7 * n, 0.18, 0.16, 0.34, "gold", "cone")
        if kind == "dreamcourt":
            for i in range(12):
                block(
                    -4 + i * 0.62, 6, 1.6 + i * 0.37, 0.78, 1.2, 0.23, ("mint", "lavender", "cream")[i % 3]
                )
        if kind == "canyon":
            block(0, 1, 0.007, 0.12, 10, 0.014, "red")
    else:
        block(0, 5.05, 3.0, 33, 0.32, 6, wall)
        for x in range(-12, 13, 3):
            block(x, 4.81, 2.85, 0.18, 0.23, 5.7, trim)
            block(x, 4.74, 0.30, 2.83, 0.20, 0.09, trim)
        for y in (0, 2, 4):
            block(0, y, 0.003, 30, 0.035, 0.007, "6E7984")
        if kind in ("aisle", "classroom"):
            for station in range(-3, 4):
                x = station * 2.5
                if kind == "aisle":
                    for shelf in range(4):
                        z = 0.52 + 0.67 * shelf
                        block(x, 3.78, z, 2.42, 0.76, 0.09, "cream")
                        for j in range(7):
                            col = ("C46050", "F0AE50", "54A69B", "919ADA")[(j + station + shelf) % 4]
                            block(
                                x + (j - 3) * 0.31,
                                3.64,
                                z + 0.26,
                                0.25,
                                0.32,
                                0.44,
                                col,
                                "cylinder" if j % 3 == 0 else "box",
                            )
                else:
                    block(x, 4.80, 2.78, 2.02, 0.11, 1.53, "365F5B")
                    for j in range(3):
                        block(x - 0.24, 4.72, 3.16 - 0.32 * j, 1.16 - j * 0.14, 0.04, 0.038, "B2D4BC")
        elif kind in ("vault", "lockup", "corridor", "belfry"):
            for station in range(-3, 4):
                x = station * 2.80
                block(x, 4.68, 1.53, 2.14, 0.16, 3.05, trim)
                block(x, 4.56, 1.48, 1.78, 0.10, 2.71, "27374C")
                if kind == "lockup":
                    for j in range(7):
                        block(x + (j - 3) * 0.23, 4.46, 1.52, 0.068, 0.10, 2.72, "steel")
                elif kind == "belfry":
                    block(x, 4.30, 2.42, 1.32, 1.32, 0.17, "gold", "ring", (pi / 2, 0, 0))
                    for j in range(4):
                        block(x, 4.27, 2.42, 1.34, 0.10, 0.10, "gold", angle=(0, j * pi / 4, 0))
                else:
                    block(x, 4.43, 2.07, 0.70, 0.06, 0.43, "74C0C5")
                    block(x + 0.62, 4.44, 1.14, 0.13, 0.11, 0.13, "gold", "sphere")
                block(x, 4.42, 3.54, 0.66, 0.19, 0.13, "FFCC7F")
        else:
            for x in (-4.2, 0, 4.2):
                block(x, 4.68, 2.58, 2.17, 0.19, 1.93, "cream")
                block(x, 4.54, 2.58, 1.91, 0.10, 1.63, "47577E" if night else "89CBE4")
                block(x, 4.44, 2.58, 0.08, 0.07, 1.7, "cream")
                block(x, 4.44, 2.58, 1.91, 0.07, 0.08, "cream")
                for a in (-1, 1):
                    block(x + a * 1.07, 4.40, 2.64, 0.36, 0.17, 2.16, trim)
                if x:
                    block(x, 3.72, 0.56, 1.91, 0.71, 1.10, "brown")
                    for j in range(3):
                        block(x, 3.33, 0.29 + 0.32 * j, 1.63, 0.07, 0.21, "C39773")


def skyport(block, sky, trim):
    block(0, 25, 3, 145, 0.6, 75, sky)
    block(0, 8, -8, 130, 110, 0.3, "B7DBE9")
    block(0, 0, -0.21, 10, 6, 0.42, "A27C55")
    for j in range(15):
        block((j - 7) * 0.66, 0, 0.014, 0.035, 6, 0.025, "80654C")
    for i in range(11):
        x = (i - 5) * 3.67
        y = 8 + (i % 3) * 3
        z = 3.8 + (i * 7 % 5) * 0.83
        for dx in (-1, 0, 1):
            block(x + dx, y + 2, -2.4 + (i % 4) * 0.39, 3.3, 2.5, 1.28, "DAEEF1", "sphere")
        block(x, y, z, 2.40, 2.19, 2.95, (trim, "F0B45E", "CB7975", "749BB6")[i % 4], "sphere")
        block(x, y, z - 2.35, 0.99, 0.97, 0.71, "A27B56")
        for side in (-1, 1):
            block(x + side * 0.43, y, z - 1.66, 0.043, 0.045, 1.14, "5C565C")


def undercity(block):
    # A deep, occluded street makes the cable legible between three architecture layers.
    slab = block(0, 2, -0.18, 48, 55, 0.36, "3F485E")
    slab["surface_finish"] = "stone"
    block(0, 20, 5, 130, 0.70, 43, "24223E")
    for side in (-1, 1):
        for row in range(5):
            x = side * (5.5 + (row % 2) * 1.1)
            y = -1 + row * 3.8
            high = 6.2 + (row * 7 % 5)
            block(x, y, high / 2, 2.6, 3.25, high, ("51435C", "415369", "584956")[row % 3])
            for level in range(3):
                for j in range(3):
                    color = ("B88EAE", "75C7CF", "DAAB63")[(j + level + row) % 3]
                    block(x - side * 1.34, y + (j - 1) * 0.78, 2.6 + level * 1.4, 0.10, 0.45, 0.59, color)
            c = ("F77EA6", "78D9E3", "F3BD64")[row % 3]
            block(x - side * 1.65, y - 0.65, 2.6, 0.74, 0.22, 1.7, "273647")
            for k in range(5):
                block(x - side * 1.65, y - 0.79, 2.09 + k * 0.23, 0.49 if k % 2 else 0.35, 0.026, 0.076, c)
    for i in range(5):
        x = (i - 2) * 4
        block(x, 12, 3.1 + (i % 2), 3.8, 2.3, 6.2 + (i % 2) * 2, "30374A")
        for j in range(4):
            block(x, 10.81, 2.11 + j * 1.0, 2.0, 0.06, 0.12, ("6EAABB", "B97DA0")[i % 2])
    block(2.4, 6.2, 8.3, 0.11, 0.11, 16.7, "C8EEF8")
    block(0, 9, 12.8, 30, 18, 1.14, "262941")
    for x in (-9, -4, 1, 6, 11):
        block(x, 5, 12.18, 2.2, 0.72, 0.10, "E8A56B")
    for x in (-3.45, 3.5):
        block(x, 1.6, 0.019, 0.075, 11, 0.023, "A87286")


def meadow(block, place, twilight):
    ground = block(0, 2, -0.20, 100, 100, 0.40, "6F8666" if twilight else "66935C")
    ground["surface_finish"] = "grass"
    if twilight:
        # Draw every horizon in world space so oblique coverage sees the same dusk.
        for i in range(12):
            z = -0.6 + i * 1.55
            palette = (
                "DB9379",
                "D79381",
                "CE8C8B",
                "BC8193",
                "A7779F",
                "976CA4",
                "8164A2",
                "725E9B",
                "625994",
                "56548B",
                "4C4E82",
                "45487A",
            )
            block(0, 22, z, 140, 1, 1.60, palette[i])
        for j in range(-5, 6):
            block(j * 5, 14, 0.52, 7.4, 3.2, 2.35 + abs(j) % 3 * 0.49, "6F7384", "sphere")
    else:
        sky = block(0, 24, 17, 140, 0.55, 48, "434D69" if place.get("light") == "night" else "93CBD4")
        sky["surface_finish"] = "sky"
    for side in (-1, 1):
        for j in range(7):
            x = side * (5.2 + (j * 7 % 4))
            y = -1 + j * 2.55
            block(x, y, 1.47, 0.45, 0.43, 2.94, "655042")
            for k in range(3):
                block(
                    x + (k - 1) * 0.61,
                    y,
                    3.02 + (k % 2) * 0.52,
                    2.22,
                    1.83,
                    2.20,
                    ("567B62", "6D935F", "4D705E")[k],
                    "sphere",
                )
    for j in range(41):
        x = (j * 17 % 31 - 15) * 0.61
        y = (j * 13 % 25 - 7) * 0.54
        if abs(x) < 2.4 and y < 2:
            continue
        for k in range(2):
            block(
                x + k * 0.09,
                y,
                0.14,
                0.054,
                0.045,
                0.29 + (j % 3) * 0.07,
                ("9BAA68", "7F955E")[k],
                angle=(0.06, (-1 if k else 1) * 0.23, 0),
            )

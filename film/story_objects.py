"""Silhouette-led practicals with articulated parts. Local coordinates face the lens at -Y."""

from math import cos, pi, sin

KINDS = (
    "serpent crawler stalker mannequin shadowman branchman rockboy shears paperplane ranker "
    "blindfold coin key watch tin chain cart groceries phone bed console towerclock apple hat "
    "schooldesk cage pouch paper stackstone ribbon rope book hammer bellhouse gate candle roundtimer redline giantpalm operator elevator cottage balloon halo earthbucket earthmouth flywheel ticketdrone"
).split()


def build(kind, b, color):
    from animate import label

    def box(x, y, z, w, d, h, c, shape="box", tilt=None):
        return b((x, y, z), (w, d, h), c, shape, tilt)

    def eye(x, y, z, r=0.16):
        box(x, y, z, r, r * 0.25, r, "ivory", "sphere")
        box(x, y - r * 0.15, z, r * 0.50, r * 0.09, r * 0.60, "ink", "sphere")

    def wave(o, axis, amount, phase=0, rate=3):
        o["oscillator"] = [axis, amount, phase, rate]
        return o

    if kind == "elevator":
        root = box(0, 0, 0.10, 2.80, 1.75, 0.20, "gold").parent
        box(0, -0.06, 0.22, 2.56, 1.47, 0.08, "raspberry")
        box(0, 0.67, 1.82, 2.54, 0.15, 3.24, "B8874F")
        for side in (-1, 1):
            box(side * 1.34, 0, 1.85, 0.18, 1.70, 3.50, "gold")
            box(side * 0.93, 0.59, 1.75, 0.43, 0.13, 2.49, "704F42")
            for row in range(5):
                for col in (-1, 1):
                    box(
                        side * 0.93 + col * 0.086,
                        0.49,
                        0.87 + row * 0.44,
                        0.11,
                        0.06,
                        0.11,
                        "F4CD72",
                        "sphere",
                    )
        box(0, 0, 3.69, 2.90, 1.75, 0.26, "gold")
        box(0, -0.88, 3.69, 0.74, 0.06, 0.14, "FDE997")
        label("LEVEL", (0, 0.55, 2.73), 0.25, "ivory", root)
        return 1.85
    if kind == "operator":
        for side in (-1, 1):
            wave(box(side * 0.33, 0, 0.76, 0.20, 0.28, 1.42, "charcoal"), 3, 0.085, pi * (side == 1), 2.6)
            wave(
                box(side * 0.72, 0, 1.95, 0.17, 0.22, 1.63, "charcoal", tilt=(0.09, side * 0.22, 0)),
                3,
                0.12,
                pi * (side == -1),
                2.6,
            )
        for level in (1.40, 2.69):
            box(0, 0, level, 1.22, 0.69, 0.15, "ink")
        for i in range(8):
            a = i * pi / 4
            box(0.52 * cos(a), 0.29 * sin(a), 2.02, 0.069, 0.072, 1.24, "charcoal")
        wave(box(0, -0.07, 2.14, 0.30, 0.28, 0.40, "FFEBA7", "sphere"), 0, 0.12, 0, 2.9)
        box(0, 0, 3.10, 0.70, 0.43, 0.76, "B9985A")
        for up in (0, 1):
            box(
                0,
                -0.235,
                2.94 + 0.32 * up,
                0.17,
                0.11,
                0.14,
                "F4D483" if up else "F08977",
                "cone",
                (0 if up else pi, 0, 0),
            )
        return 2.28
    if kind == "cottage":
        box(0, 0, 1.23, 2.92, 2.32, 2.46, color)
        for side in (-1, 1):
            box(side * 0.74, 0, 2.84, 1.86, 2.68, 0.18, "854E53", tilt=(0, side * 0.45, 0))
            box(side * 0.92, -1.19, 1.52, 0.65, 0.07, 0.78, "FFE29E")
            box(side * 0.92, -1.24, 1.52, 0.05, 0.04, 0.82, "cream")
        box(0, -1.19, 0.86, 0.66, 0.08, 1.70, "594F52")
        box(0.19, -1.25, 0.87, 0.11, 0.04, 0.11, "gold", "sphere")
        box(0.77, 0.43, 3.18, 0.37, 0.35, 0.99, "914F42")
        return 1.57
    if kind == "balloon":
        box(0, 0, 0.38, 0.96, 0.91, 0.73, "A37B50")
        for i in range(4):
            box(0, 0, 0.12 + i * 0.16, 0.99, 0.94, 0.046, "D5AB6C")
        for x in (-0.42, 0.42):
            for y in (-0.39, 0.39):
                box(x, y, 1.07, 0.034, 0.035, 1.01, "5C4E49")
        box(0, 0, 1.58, 0.43, 0.40, 0.21, "gold", "cylinder")
        box(0, 0, 2.59, 1.91, 1.77, 2.25, color, "sphere")
        for j in range(8):
            a = pi * j / 4
            box(0.86 * cos(a), 0.80 * sin(a), 2.57, 0.13, 0.13, 1.27, "D9AD69", "sphere")
        return 2.00
    if kind == "flywheel":
        for y in (0, 0.40):
            box(0, y, 1.78, 3.30, 3.30, 0.27, "596B82", "ring", (pi / 2, 0, 0))
            box(0, y - 0.04, 1.78, 3.12, 3.12, 0.21, color, "ring", (pi / 2, 0, 0))
        for j in range(16):
            a = 2 * pi * j / 16
            box(1.54 * cos(a), 0.2, 1.78 + 1.54 * sin(a), 0.13, 0.43, 0.13, "C4DEF2")
        box(0, 0.23, 0.18, 2.56, 0.89, 0.36, "navy")
        return 1.76
    if kind == "ticketdrone":
        box(0, 0, 0.29, 0.62, 0.42, 0.32, color)
        for side in (-1, 1):
            box(side * 0.40, 0, 0.36, 0.49, 0.14, 0.09, "steel")
            wave(box(side * 0.59, 0, 0.41, 0.57, 0.16, 0.04, "navy"), 5, 1.1, 0, 7.4)
        box(0, -0.12, 0.16, 0.15, 0.21, 0.13, "teal", "sphere")
        return 0.30
    if kind == "halo":
        box(0, 0, 0.08, 0.99, 0.83, 0.25, color, "ring")
        return 0.08
    if kind == "earthbucket":
        box(0, 0, 0.37, 0.82, 0.76, 0.68, "838F9A", "cylinder")
        box(0, -0.02, 0.68, 0.79, 0.74, 0.20, "7F573E", "sphere")
        box(0, 0, 0.83, 0.70, 0.67, 0.08, "charcoal", "ring", (pi / 2, 0, 0))
        for i in range(5):
            box(
                (i - 2) * 0.11,
                -0.04 + (i % 2) * 0.14,
                0.78 + (i % 3) * 0.025,
                0.13,
                0.14,
                0.08,
                "80AD57",
                "sphere",
            )
        return 0.52
    if kind == "earthmouth":
        box(0, 0, 0.35, 3.94, 2.00, 0.90, "608F52", "sphere")
        box(0, -0.30, 0.69, 3.28, 1.40, 0.56, "46383D", "sphere")
        for side in (-1, 1):
            for i in range(8):
                box((i - 3.5) * 0.36, side * 0.49 - 0.31, 0.85, 0.18, 0.22, 0.36, "EBD8AA", "cone")
        return 0.70
    if kind == "serpent":
        for i in range(14):
            u = i / 13
            x = i * 0.60
            section = box(
                x,
                0.20 * sin(i * 0.55),
                0.67 - 0.28 * u,
                1.19 - 0.54 * u,
                1.09 - 0.58 * u,
                0.97 - 0.47 * u,
                color,
                "sphere",
            )
            section["surface_finish"] = "scales"
            wave(section, 1, 0.22, i * -0.62, 3.2)
        # Separated jaws and a dark palate keep the bite readable head-on and in profile.
        head = box(-0.69, -0.08, 1.03, 1.61, 1.14, 0.64, color, "sphere")
        head["surface_finish"] = "scales"
        box(-0.79, -0.12, 0.76, 1.30, 1.04, 0.16, "352B36", "sphere")
        jaw = box(-0.73, -0.07, 0.44, 1.45, 1.09, 0.27, color, "sphere")
        jaw["surface_finish"] = "scales"
        box(-0.76, -0.13, 0.57, 1.28, 0.94, 0.10, "B97978", "sphere")
        for side in (-1, 1):
            for j in range(6):
                x = -1.24 + j * 0.205
                box(
                    x,
                    side * 0.40 - 0.09,
                    0.67,
                    0.091,
                    0.09,
                    0.24 if j % 3 == 0 else 0.15,
                    "ivory",
                    "cone",
                    (pi, 0, 0),
                )
            box(-0.63, side * 0.52 - 0.07, 1.20, 0.27, 0.10, 0.21, "F3BF42", "sphere")
            box(-0.67, side * 0.56 - 0.07, 1.20, 0.056, 0.045, 0.16, "ink")
            box(-1.29, side * 0.24 - 0.07, 1.12, 0.093, 0.13, 0.055, "ink", "sphere")
        return 0.91
    if kind == "crawler":
        box(0, 0, 0.56, 0.96, 0.71, 0.70, color, "sphere")
        box(0, -0.38, 0.47, 0.64, 0.41, 0.47, "charcoal", "sphere")
        for side in (-1, 1):
            for i in range(4):
                leg = box(
                    side * (0.58 + 0.075 * i),
                    -0.31 + 0.19 * i,
                    0.35,
                    0.83,
                    0.095,
                    0.13,
                    "ink",
                    tilt=(0, side * -0.43, side * (0.45 - 0.24 * i)),
                )
                wave(leg, 4, 0.25, i * 0.9 + (side == 1) * pi, 5)
            eye(side * 0.14, -0.58, 0.51, 0.12)
        return 0.5
    if kind in ("stalker", "shadowman", "branchman", "mannequin", "rockboy"):
        clay = kind == "mannequin"
        rock = kind == "rockboy"
        bark = kind == "branchman"
        flesh = "C6CBCB" if clay else "817F8C" if rock else "71513E" if bark else color
        w = 1.36 if rock else 0.73
        box(0, 0, 1.57, w, 0.52, 1.08, flesh, "box" if rock else "sphere")
        box(0, -0.03, 2.47, w * 0.89, 0.64, 0.78, flesh, "box" if rock else "sphere")
        for side in (-1, 1):
            arm = box(
                side * (w * 0.59),
                -0.05,
                1.36,
                0.25 if not rock else 0.49,
                0.38,
                1.22,
                flesh,
                tilt=(0.08, side * 0.10, 0),
            )
            leg = box(side * 0.23, 0.02, 0.64, 0.31, 0.38, 1.25, flesh)
            if not clay:
                wave(arm, 3, 0.13, pi * (side == 1), 2.7)
                wave(leg, 3, 0.075, pi * (side == -1), 2.7)
            if bark:
                box(side * 0.37, 0, 2.99, 0.12, 0.12, 0.82, "brown", tilt=(0, side * 0.44, 0))
                box(side * 0.53, -0.02, 3.13, 0.45, 0.32, 0.25, "seafoam", "sphere")
            if not clay:
                eye(side * 0.16, -0.355, 2.53, 0.16)
        if not clay:
            box(0, -0.366, 2.32, 0.39, 0.055, 0.09, "ink")
        if kind == "shadowman":
            box(0, 0, 2.91, 0.95, 0.81, 0.09, "ink", "cylinder")
            box(0, 0, 3.10, 0.67, 0.58, 0.43, "navy", "cylinder")
        return 1.85
    if kind == "redline":
        for i in range(21):
            x = (i - 10) * 0.55
            strip = box(x, 0.030 * x * x, 0.017, 0.57, 0.18, 0.033, color, tilt=(0, 0, 0.055 * x))
            if 9 <= i <= 11:
                strip["paint_gap"] = True
        return 0.03
    if kind == "giantpalm":
        box(0, 0, 0.91, 1.13, 0.40, 1.02, color, "sphere")
        for i, h in enumerate((0.70, 0.94, 1.04, 0.82)):
            box((i - 1.5) * 0.25, -0.03, 1.31 + h / 2, 0.24, 0.34, h, color, "sphere")
        box(-0.62, -0.05, 1.03, 0.32, 0.36, 0.78, color, "sphere", (0, -0.51, 0))
        return 1.36
    if kind == "roundtimer":
        hull = box(0, 0, 1.6, 3.02, 2.48, 3.08, "charcoal", "sphere")
        hull["surface_finish"] = "metal"
        for x in (-0.69, 0.69):
            box(x, 0, 0.16, 0.37, 1.32, 0.32, "navy")
        box(0, -1.18, 1.73, 1.09, 1.09, 0.14, "gold", "cylinder", (pi / 2, 0, 0))
        box(0, -1.27, 1.83, 0.23, 0.09, 0.23, "ink", "sphere")
        box(0, -1.27, 1.65, 0.13, 0.09, 0.25, "ink")
        for j in range(8):
            a = j * pi / 4
            box(0.48 * cos(a), -1.29, 1.73 + 0.48 * sin(a), 0.065, 0.055, 0.065, "cream", "sphere")
        return 1.59
    if kind == "ranker":
        root = box(0, 0, 0.13, 2.16, 1.44, 0.26, "charcoal").parent
        for z, w, d, h, c in (
            (0.34, 1.86, 1.19, 0.20, "gold"),
            (1.94, 1.41, 0.83, 3.06, color),
            (3.61, 1.70, 1.04, 0.28, "gold"),
        ):
            o = box(0, 0, z, w, d, h, c)
            o["surface_finish"] = "metal"
        for i, letter in enumerate("FDCBAS"):
            z = 0.66 + i * 0.50
            box(0, -0.448, z, 1.12, 0.08, 0.40, "253746")
            label(letter, (0, -0.501, z), 0.34, "gold" if letter == "S" else "ivory", root)
        for side in (-1, 1):
            box(side * 0.71, -0.16, 1.94, 0.13, 1.0, 3.16, "gold")
            for j in range(7):
                box(side * 0.72, -0.67, 0.44 + j * 0.46, 0.078, 0.056, 0.078, "cream", "sphere")
        box(0, -0.71, 0.48, 1.53, 0.66, 0.19, "mint", tilt=(0.13, 0, 0))
        box(0, 0, 3.94, 0.48, 0.48, 0.55, "gold", "sphere")
        return 1.95
    if kind in ("coin", "watch", "towerclock"):
        r = {"coin": 0.75, "watch": 0.64, "towerclock": 1.7}[kind]
        if kind == "towerclock":
            box(0, 0, 0.87, 1.18, 0.82, 1.74, "navy")
        z = r * 0.59 + (1.0 if kind == "towerclock" else 0)
        box(0, 0, z, r, r, 0.16, "gold", "cylinder", (pi / 2, 0, 0))
        box(
            0,
            -0.10,
            z,
            r * 0.82,
            r * 0.82,
            0.04,
            "cream" if kind != "coin" else color,
            "cylinder",
            (pi / 2, 0, 0),
        )
        if kind == "coin":
            box(0, -0.14, z, r * 0.30, 0.04, r * 0.30, "gold", tilt=(0, pi / 4, 0))
        else:
            for i in range(12):
                a = i * pi / 6
                box(
                    0.36 * r * sin(a),
                    -0.15,
                    z + 0.36 * r * cos(a),
                    0.035,
                    0.03,
                    0.07,
                    "navy",
                    tilt=(0, a, 0),
                )
            box(-0.055 * r, -0.18, z + 0.11 * r, 0.048, 0.04, r * 0.30, "navy", tilt=(0, -0.43, 0))
            box(0.09 * r, -0.18, z + 0.03 * r, 0.05, 0.04, r * 0.22, "red", tilt=(0, 1.2, 0))
        return z
    if kind == "cart":
        for x in (-0.50, 0.50):
            for y in (-0.29, 0.29):
                box(x, y, 0.16, 0.24, 0.24, 0.12, "navy", "cylinder", (pi / 2, 0, 0))
        box(0, 0, 0.43, 1.36, 0.77, 0.10, "steel")
        for y in (-0.37, 0.37):
            for i in range(8):
                box(-0.62 + i * 0.175, y, 0.74, 0.043, 0.05, 0.56, "steel")
            box(0, y, 1.03, 1.36, 0.06, 0.08, color)
        for x in (-0.66, 0.66):
            box(x, 0, 0.79, 0.065, 0.75, 0.47, "steel" if x > 0 else color)
        box(0.77, 0, 1.14, 0.10, 0.85, 0.09, color)
        for i, (x, c) in enumerate(
            [(-0.42, "raspberry"), (-0.11, "gold"), (0.20, "seafoam"), (0.40, "coral")]
        ):
            box(x, 0, 0.78, 0.26, 0.39, 0.63 - i * 0.055, c)
        return 0.77
    if kind == "groceries":
        for i in range(7):
            box(
                (i % 4 - 0.9) * 0.29,
                (i // 4) * 0.24,
                0.23 + (i % 3) * 0.07,
                0.24,
                0.25,
                0.45 + (i % 3) * 0.14,
                ("gold", "red", "cream", "mint")[i % 4],
                "cylinder" if i % 2 else "box",
            )
        return 0.32
    if kind == "key":
        box(-0.35, 0, 0.38, 0.46, 0.46, 0.11, "gold", "ring", (pi / 2, 0, 0))
        box(0.12, 0, 0.38, 0.78, 0.12, 0.12, "gold")
        for x in (0.35, 0.48):
            box(x, 0, 0.28, 0.10, 0.12, 0.26, "gold")
        box(-0.40, 0.02, 0.16, 0.09, 0.06, 0.40, color, tilt=(0, 0.37, 0))
        return 0.34
    if kind in ("phone", "book", "tin", "console", "schooldesk", "bed"):
        if kind == "phone":
            box(0, 0, 0.41, 0.44, 0.09, 0.82, "ink")
            box(0, -0.053, 0.42, 0.37, 0.02, 0.66, "77BCD2")
            for i in range(3):
                box(-0.035, -0.071, 0.58 - i * 0.12, 0.22 - i * 0.035, 0.018, 0.038, "ivory")
            return 0.41
        if kind == "book":
            box(0, 0, 0.33, 0.64, 0.14, 0.66, color)
            box(-0.27, -0.08, 0.33, 0.05, 0.03, 0.66, "gold")
            box(0.05, -0.08, 0.44, 0.33, 0.03, 0.08, "cream")
            return 0.33
        if kind == "tin":
            box(0, 0, 0.18, 0.81, 0.53, 0.34, color)
            box(0, -0.02, 0.36, 0.85, 0.56, 0.07, "cream")
            box(0, -0.28, 0.19, 0.12, 0.06, 0.11, "gold")
            return 0.22
        if kind == "schooldesk":
            box(0, 0, 0.91, 1.30, 0.85, 0.14, "brown")
            for x in (-0.52, 0.52):
                for y in (-0.30, 0.30):
                    box(x, y, 0.46, 0.09, 0.09, 0.91, "navy")
            box(-0.32, 0, 1.01, 0.43, 0.40, 0.07, color)
            return 0.94
        if kind == "bed":
            box(0, 0, 0.38, 1.4, 2.16, 0.25, "brown")
            box(0, 0, 0.62, 1.33, 2.05, 0.30, "cream")
            box(0, -0.30, 0.79, 1.36, 1.41, 0.12, color)
            box(0, 0.71, 0.84, 0.98, 0.45, 0.19, "ivory", "sphere")
            return 0.79
        box(0, 0, 0.78, 1.8, 0.9, 0.20, "charcoal")
        for x in (-0.69, 0.69):
            box(x, 0.11, 0.36, 0.12, 0.62, 0.73, "navy")
        for x in (-0.48, 0.48):
            box(x, 0.20, 1.27, 0.91, 0.13, 0.68, "ink")
            box(x, 0.115, 1.27, 0.76, 0.03, 0.54, "5DBEAE")
        for r in range(3):
            for j in range(8):
                box((j - 3.5) * 0.14, -0.21 + r * 0.11, 0.91, 0.11, 0.07, 0.03, "cream")
        return 1.23
    if kind == "chain":
        for i in range(7):
            box(
                (i - 3) * 0.18,
                0,
                0.22 + 0.05 * cos(i),
                0.33,
                0.26,
                0.095,
                "steel",
                "ring",
                (pi / 2 if i % 2 else 1, 0, 0),
            )
        box(0, -0.1, 0.16, 0.29, 0.19, 0.30, "gold")
        return 0.22
    if kind in ("cage", "gate"):
        w = 2.62 if kind == "gate" else 1.64
        h = 2.92 if kind == "gate" else 2.25
        for i in range(8):
            box(w * (i / 7 - 0.5), 0, h / 2, 0.07, 0.16, h, "steel")
        for z in (0.18, h * 0.72, h):
            box(0, 0, z, w + 0.13, 0.22, 0.13, color)
        return h * 0.55
    if kind in ("hat", "blindfold", "ribbon", "pouch"):
        if kind == "hat":
            box(0, 0, 0.08, 0.92, 0.77, 0.12, color, "cylinder")
            box(0, 0.02, 0.31, 0.65, 0.58, 0.43, color, "cylinder")
            box(0, 0.02, 0.16, 0.67, 0.60, 0.08, "gold", "cylinder")
        elif kind == "pouch":
            box(0, 0, 0.33, 0.62, 0.48, 0.63, color, "sphere")
            box(0, 0, 0.61, 0.34, 0.27, 0.10, "gold")
            box(0, 0, 0.68, 0.43, 0.34, 0.17, color, "cone", (pi, 0, 0))
        else:
            box(0, 0, 0.22, 0.85, 0.11, 0.20, color)
            for s in (-1, 1):
                box(s * 0.46, 0.04, 0.14, 0.23, 0.07, 0.28, color, tilt=(0, s * 0.47, 0))
        return 0.26
    if kind == "apple":
        for x in (-0.11, 0.11):
            box(x, 0, 0.29, 0.41, 0.46, 0.48, color, "sphere")
        box(0.03, 0, 0.56, 0.046, 0.05, 0.17, "brown", tilt=(0, 0.27, 0))
        box(0.13, 0, 0.63, 0.22, 0.12, 0.08, "mint", "sphere")
        return 0.32
    if kind in ("paper", "paperplane", "shears", "stackstone", "rope", "hammer", "candle", "bellhouse"):
        if kind == "paperplane":
            for s in (-1, 1):
                box(s * 0.20, 0, 0.25, 0.48, 1.02, 0.042, "ivory", tilt=(0.12, s * 0.28, s * 0.28))
        elif kind == "paper":
            box(0, 0, 0.41, 0.72, 0.06, 0.83, "cream")
            for i in range(4):
                box(0, -0.045, 0.66 - i * 0.14, 0.49 - i * 0.05, 0.02, 0.035, color)
        elif kind == "shears":
            for s in (-1, 1):
                box(s * 0.21, 0, 0.86, 0.15, 0.13, 1.21, "steel", tilt=(0, s * 0.37, 0))
                box(s * -0.23, 0, 0.17, 0.44, 0.44, 0.11, color, "ring", (pi / 2, 0, 0))
        elif kind == "stackstone":
            for i in range(8):
                box(
                    (i % 3 - 1) * 0.43 + (i // 3 % 2) * 0.15,
                    0,
                    0.20 + (i // 3) * 0.29,
                    0.52,
                    0.50,
                    0.37,
                    color if i % 2 else "charcoal",
                    "sphere",
                )
        elif kind == "rope":
            for i in range(5):
                box(0, 0, 0.046 + i * 0.062, 0.77, 0.64, 0.12, color, "ring")
        elif kind == "hammer":
            box(0, 0, 0.48, 0.19, 0.18, 0.91, "brown")
            box(0, 0, 0.91, 0.93, 0.38, 0.39, color)
        elif kind == "candle":
            box(0, 0, 0.38, 0.29, 0.29, 0.75, "cream", "cylinder")
            box(0, 0, 0.84, 0.16, 0.13, 0.27, "gold", "sphere")
        else:
            box(0, 0, 1.28, 1.65, 1.19, 2.54, "brown")
            box(0, 0, 2.86, 2.06, 1.66, 0.79, color, "cone")
            box(0, -0.61, 2.01, 0.63, 0.18, 0.67, "gold", "sphere")
        return 0.66
    raise ValueError(kind)

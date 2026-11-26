"""Public-space scenery, background business and weather practicals for the ensemble stage."""

from math import pi, sin, cos
import bpy
from animate import part, empty, label
from shot_rhythm import crowd_path

CORAL, ROSE, GOLD = "FF624D", "F23480", "FFD045"
TEAL, AQUA, INK = "008E98", "44D7E3", "25334D"
WHITE, LEAF = "FFF0CF", "09AA76"


def flower(x, y, z, size, color, parent=None):
    part((x, y, z + 0.23 * size), (0.055 * size, 0.055 * size, 0.5 * size), LEAF, parent)
    for n in range(5):
        a = n * 2 * pi / 5
        part(
            (x + 0.13 * size * sin(a), y, z + (0.55 + 0.13 * cos(a)) * size),
            (0.23 * size, 0.12 * size, 0.24 * size),
            color,
            parent,
            "sphere",
        )
    part(
        (x, y - 0.065 * size, z + 0.55 * size),
        (0.16 * size, 0.08 * size, 0.16 * size),
        GOLD,
        parent,
        "sphere",
    )


def district(place):
    fair = place["kit"] == "fairground"
    trim = {"raspberry": ROSE, "peacock": TEAL}.get(place["trim"], place["trim"])
    sky = {"daylight": "53BFF7", "late_sun": "FFAD82", "night": "344779"}[place.get("light", "daylight")]
    facade = ["FFC664", "FF9281", "76D7BF", "F8AEC5", "AFBFF1"]
    if place["wall"] != ("coral" if fair else "seafoam"):
        facade[::2] = [place["wall"], "cream", place["wall"]]
    part((0, 4, -0.15), (100, 85, 0.28), "FED097" if fair else "82CD65")
    part((0, 0, -0.02), (20, 4, 0.038), "FFE2B7" if fair else "DBAD74")
    if fair:
        for x in (-2.05, 2.05):
            part((x, 0.52, -0.001), (0.08, 4.25, 0.012), WHITE)
        for j in range(86):
            x = ((j * 31) % 97 - 48) * 0.080
            y = ((j * 17) % 53 - 26) * 0.071
            part(
                (x, y, 0.007),
                (0.08, 0.047, 0.011),
                [WHITE, ROSE, CORAL, GOLD][j % 4],
                angle=(0, 0, j * 0.63),
            )
    else:
        for j in range(11):
            for row in range(2):
                x = (j - 5) * 0.83 + row * 0.26
                part(
                    (x, -0.90 + row * 0.68, 0.005),
                    (0.79, 0.63, 0.018),
                    ["ECC890", "F8D399", "E9BE81"][(row + j) % 3],
                )
    part((0, 24, 17), (160, 0.3, 47), sky)
    for k in range(12):
        x = -22 + 4 * k
        z = 5.6 + (k * 7 % 5)
        for dx, dz in ((-0.8, 0), (0, 0.35), (0.85, 0.04)):
            part((x + dx, 20, z + dz), (2.7, 0.7, 1.1), "DBF3FF", shape="sphere")
    for j in range(-5, 6):
        x = j * 3.4
        h = 2.8 + (j * 7 % 4) * 0.6
        wall = facade[j % 5]
        part((x, 10, h / 2), (3.25, 2.6, h), wall)
        for side in (-1, 1):
            part(
                (x + side * 0.83, 10, h + 0.39),
                (1.88, 3.1, 0.19),
                [CORAL, TEAL, ROSE][j % 3],
                angle=(0, side * 0.44, 0),
            )
        for dx in (-0.8, 0.8):
            for z in (1.3, h - 0.55):
                part((x + dx, 8.65, z), (0.73, 0.12, 0.74), WHITE)
                part((x + dx, 8.56, z), (0.52, 0.05, 0.55), "4685A2")
                part((x + dx, 8.5, z), (0.05, 0.035, 0.56), WHITE)
    if fair:
        for x, accent in ((-4.8, trim), (4.7, TEAL)):
            for dx in (-1.25, 1.25):
                part((x + dx, 3.93, 1.40), (0.10, 0.12, 2.8), WHITE)
            for k in range(9):
                part(
                    (x + (k - 4) * 0.35, 4.25, 2.92),
                    (0.355, 1.75, 0.18),
                    accent if k % 2 else WHITE,
                    angle=(-0.16, 0, 0),
                )
                part(
                    (x + (k - 4) * 0.35, 3.40, 2.66),
                    (0.35, 0.14, 0.31),
                    accent if k % 2 else WHITE,
                    shape="sphere",
                )
            part((x, 4.35, 0.65), (2.8, 1.3, 1.30), accent)
            part((x, 4.35, 1.34), (3.0, 1.42, 0.13), WHITE)
            for k in range(7):
                part(
                    (x + (k - 3) * 0.33, 4.0, 1.58),
                    (0.27, 0.27, 0.37),
                    [GOLD, CORAL, ROSE][k % 3],
                    shape="sphere",
                )
        # Fair wheel: upright spokes and hanging cabins establish scale behind the stalls.
        for dx in (-1.45, 1.45):
            part((-3.1 + dx / 2, 7.2, 2.1), (0.18, 0.26, 4.45), TEAL, angle=(0, -dx * 0.21, 0))
        part((-3.1, 7.1, 4.2), (4.9, 4.9, 0.14), trim, shape="ring", angle=(pi / 2, 0, 0))
        for j in range(10):
            a = j * 2 * pi / 10
            part(
                (-3.1 + 1.18 * sin(a), 7.1, 4.2 + 1.18 * cos(a)),
                (0.065, 0.09, 2.40),
                WHITE,
                angle=(0, a, 0),
            )
            part(
                (-3.1 + 2.4 * sin(a), 7, 4.04 + 2.4 * cos(a)),
                (0.50, 0.47, 0.37),
                [GOLD, TEAL, CORAL][j % 3],
            )
    else:
        # Overhead ribs, suspended baskets and low beds put the nursery in three planes.
        for y in (3.50, 6.10, 8.55):
            for side in (-1, 1):
                part((side * 5.45, y, 2.25), (0.15, 0.18, 4.50), trim)
                part((side * 2.73, y, 5.03), (5.65, 0.16, 0.15), trim, angle=(0, side * 0.21, 0))
        for x in (-5.45, 0, 5.45):
            part((x, 6.35, 5.60 if x == 0 else 4.43), (0.13, 6.4, 0.14), TEAL)
        for x in (-3.85, -1.40, 1.56, 4.13):
            part((x, 4.15, 3.95), (0.035, 0.035, 1.10), WHITE)
            part((x, 4.15, 3.32), (0.61, 0.53, 0.36), "AF6743", shape="sphere")
            for j in range(5):
                part(
                    (x + 0.20 * cos(j * 1.27), 4.05 + 0.12 * sin(j), 3.47 + 0.10 * sin(j)),
                    (0.40, 0.33, 0.33),
                    LEAF,
                    shape="sphere",
                )
                part(
                    (x + 0.19 * cos(j * 1.27), 3.96, 3.38 - 0.12 * (j % 2)),
                    (0.13, 0.12, 0.17),
                    CORAL,
                    shape="sphere",
                )
        for x in (-4.7, 4.9):
            part((x, -0.75, 0.20), (1.2, 3.1, 0.40), "B87B48")
            for j in range(10):
                flower(x + 0.32 * (-1) ** j, -1.9 + j * 0.25, 0.40, 0.69, CORAL if j % 3 else GOLD)
        for x in (-6, 0, 6):
            for dx in (-2.2, 2.2):
                part((x + dx, 6.2, 1.26), (0.12, 0.15, 2.52), TEAL)
                part((x + dx / 2, 6.2, 3.04), (2.50, 0.16, 0.14), TEAL, angle=(0, dx * 0.21, 0))
            part((x, 6.22, 2.45), (4.5, 0.12, 0.1), TEAL)
        for x in (-5, 3.9):
            for j in range(3):
                y = 2.9 + j * 0.54
                part((x, y, 0.18), (3.22, 0.5, 0.35), "A46548")
                for k in range(6):
                    flower(x + (k - 2.5) * 0.47, y, 0.36, 0.56, [ROSE, CORAL, GOLD][(j + k) % 3])
        part((3.8, 7.3, 2.7), (2.15, 2.15, 2.0), AQUA, shape="cylinder")
        part((3.8, 7.3, 3.9), (2.38, 2.38, 0.6), TEAL, shape="cone")
        for dx in (-0.7, 0.7):
            part((3.8 + dx, 7.3, 0.93), (0.14, 0.18, 1.86), INK)
    # High flags crossing the street leave evidence, faces and lower captions clear.
    for j in range(31):
        x = (j - 15) * 0.49
        z = 4.35 + 0.024 * x * x
        part((x, 5.65, z), (0.51, 0.038, 0.038), WHITE, angle=(0, -0.047 * x, 0))
        if j % 2 == 0:
            part(
                (x, 5.66, z - 0.16),
                (0.35, 0.06, 0.34),
                [GOLD, CORAL, AQUA, ROSE][(j // 2) % 4],
                shape="sail",
                angle=(0, pi, 0),
            )
    label(place["sign"], (0.1, 6.08, 3.32), 0.26, INK)


def street_life(place, clock, frames, fps):
    life = place.get("life", "quiet")
    if life == "quiet":
        return
    # Outdoor lanes are behind the leads. Harbor pedestrians stay on the two timber quays.
    harbor = place["kit"] == "harbor"
    for j in range(8 if place["kit"] in ("fairground", "glasshouse") else 4):
        side = -1 if j % 2 == 0 else 1
        home = side * (1.45 + 0.78 * (j // 2)) if not harbor else side * (2.5 + 0.85 * (j // 2))
        lane = (
            2.18 + (j % 3) * 0.37
            if place["kit"] not in ("fairground", "glasshouse")
            else 2.35 + (j % 3) * 0.42
        )
        if place["kit"] == "arcade":
            home = side * (2.6 + 0.75 * (j // 2))
        root = empty("Resident", (home, lane, 0))
        color = [TEAL, ROSE, "7E64C9", CORAL, "247BD0", GOLD, "1AA97E", "E276AB"][j]
        skin = ["E9A271", "A96042", "F2BA8B", "BA7651"][j % 4]
        body = empty("Coat", (0, 0, 0.90), root)
        part((0, 0, 0.01), (0.50, 0.31, 0.59), color, body)
        part((0, -0.165, 0.03), (0.14, 0.03, 0.46), WHITE, body)
        part((0, -0.02, 0.61), (0.46, 0.39, 0.46), skin, body)
        part((0, 0.01, 0.85), (0.53, 0.45, 0.14), ["61394B", INK, "B3683D"][j % 3], body)
        if j % 2:
            part((0, -0.03, 0.92), (0.57, 0.51, 0.10), color, body, "cylinder")
        for k in (-1, 1):
            part((k * 0.10, -0.226, 0.64), (0.052, 0.03, 0.064), INK, body)
        arms = []
        legs = []
        for k in (-1, 1):
            arm = empty("Sleeve", (k * 0.32, 0, 0.22), body)
            arms.append(arm)
            part((0, 0, -0.14), (0.15, 0.20, 0.31), color, arm)
            part((0, 0, -0.33), (0.17, 0.19, 0.15), skin, arm)
            leg = empty("Stride", (k * 0.14, 0, 0.62), root)
            legs.append(leg)
            part((0, 0, -0.28), (0.20, 0.24, 0.55), INK, leg)
            part((0, -0.045, -0.53), (0.23, 0.36, 0.14), WHITE, leg)
        if life == "workers":
            part((0, -0.17, -0.31), (0.45, 0.22, 0.11), GOLD, arms[1])
        if life == "shoppers":
            part((0, 0, -0.56), (0.35, 0.20, 0.37), ROSE if j % 2 else GOLD, arms[1])
        scale = 0.87 + (j % 4) * 0.075
        root.scale = (scale,) * 3
        for frame in sorted({1, frames, *range(1, frames + 1, 4)}):
            sec = clock + (frame - 1) / fps
            x, velocity = crowd_path(sec, j, home, 0.56 if life == "shoppers" else 0.12)
            root.location.x = x
            root.rotation_euler.z = 1.28 * velocity if life == "shoppers" else -side * 0.29
            root.keyframe_insert(data_path="location", frame=frame, index=0)
            root.keyframe_insert(data_path="rotation_euler", frame=frame, index=2)
            for k, (arm, leg) in enumerate(zip(arms, legs)):
                swing = sin(sec * (4.0 + j % 3 * 0.4) + j + k * pi)
                if life == "audience":
                    arm.rotation_euler.x = -1.06 + 0.19 * swing
                    arm.rotation_euler.y = (1 if k else -1) * (0.36 + 0.29 * cos(sec * 5.4 + j))
                else:
                    arm.rotation_euler.x = -0.50 + 0.46 * swing
                leg.rotation_euler.x = 0.37 * swing * abs(velocity) if life == "shoppers" else 0
                arm.keyframe_insert(data_path="rotation_euler", frame=frame)
                leg.keyframe_insert(data_path="rotation_euler", frame=frame, index=0)


def weather_prop(kind, b, root):
    if kind == "raincloud":
        for x, y, z, r in [
            (-0.78, 0, 0.13, 1),
            (-0.36, 0, 0.36, 1.2),
            (0.17, 0.03, 0.48, 1.30),
            (0.66, 0.02, 0.29, 1.04),
            (0.98, 0.01, 0.09, 0.63),
        ]:
            b((x, y, z), (r, r * 0.79, r * 0.84), "DDF4FF", "sphere")
        b((0, 0, 0.02), (2.30, 0.83, 0.43), "80BCF2", "sphere")
        for j in range(25):
            x = ((j * 13) % 25 - 12) * 0.076
            y = ((j * 7) % 11 - 5) * 0.081
            drop = b((x, y, -0.20), (0.042, 0.058, 0.23), "4DB4F4" if j % 3 else "B5F1FF", "sphere")
            drop["rain_index"] = j
        return 0.12
    if kind == "bouquet":
        for j in range(9):
            a = j * 2.4
            flower(
                0.20 * sin(a),
                0.13 * cos(a),
                0.14 + 0.06 * (j % 3),
                0.60,
                [ROSE, "F76C6C", GOLD][j % 3],
                root,
            )
        b((0, 0, 0.12), (0.20, 0.17, 0.44), LEAF)
        b((0, -0.05, 0.21), (0.27, 0.16, 0.11), GOLD)
        for side in (-1, 1):
            hand = b((side * 0.23, -0.18, 0.38), (0.23, 0.13, 0.29), "B77C49", "box")
            hand["clap_side"] = side
            hand["rest_scale"] = list(hand.scale)
            thumb = b(
                (side * 0.37, -0.18, 0.41), (0.11, 0.13, 0.18), "B77C49", "sphere", (0, side * 0.44, 0)
            )
            thumb["clap_side"] = side
            thumb["rest_scale"] = list(thumb.scale)
            for k in range(4):
                finger = b(
                    (side * 0.23 + (k - 1.5) * 0.049, -0.17, 0.57), (0.05, 0.090, 0.17), "CCA172", "sphere"
                )
                finger["clap_side"] = side
                finger["rest_scale"] = list(finger.scale)
        return 0.44
    if kind == "cistern":
        for x in (-0.79, 0.79):
            for y in (-0.47, 0.47):
                b((x, y, 0.21), (0.36, 0.36, 0.17), INK, "cylinder", (pi / 2, 0, 0))
        b((0, 0, 0.35), (2.24, 1.30, 0.18), TEAL)
        for side in (-1, 1):
            b((side * 1.04, 0, 0.70), (0.12, 1.24, 0.78), AQUA)
            b((side * 1.04, 0, 1.11), (0.16, 1.33, 0.10), GOLD)
        b((0, 0.60, 0.72), (2.11, 0.11, 0.79), TEAL)
        b((0, -0.59, 0.54), (2.17, 0.12, 0.41), TEAL)
        for z in (0.36, 0.76):
            b((0, -0.68, z), (2.22, 0.065, 0.08), GOLD)
        water = b((0, 0, 0.42), (1.93, 1.07, 0.06), "35BCEB")
        water["water_level"] = 1
        return 0.72
    if kind == "cake":
        for z, w, h, col in (
            (0.10, 1.19, 0.12, TEAL),
            (0.28, 1.04, 0.30, ROSE),
            (0.45, 1.08, 0.12, WHITE),
            (0.58, 0.71, 0.24, CORAL),
            (0.73, 0.76, 0.14, WHITE),
        ):
            b((0, 0, z), (w, w, h), col, "cylinder")
        for j in range(9):
            a = 2 * pi * j / 9
            b((0.32 * sin(a), 0.32 * cos(a), 0.83), (0.12, 0.12, 0.15), ROSE, "sphere")
        return 0.42


def practical_motion(root, old, events, clock, frames, fps):
    for o in root.children:
        drop = o.get("rain_index")
        if drop is not None:
            # Linear falling streaks. Reset between consecutive frames at the bottom of each cycle.
            period = 14 + drop % 5
            phase = (round(clock * fps) + drop * 5) % period
            keys = {1, frames}
            for f in range(1 + (-phase) % period, frames + 1, period):
                keys.update((max(1, f - 1), f))
            # Set interpolation at insertion so both legacy and slotted Actions use linear rain.
            settings = bpy.context.preferences.edit
            old_type = settings.keyframe_new_interpolation_type
            try:
                settings.keyframe_new_interpolation_type = "LINEAR"
                for f in sorted(keys):
                    o.delta_location.z = -3.35 * ((f - 1 + phase) % period) / (period - 1)
                    o.keyframe_insert(data_path="delta_location", index=2, frame=f)
            finally:
                settings.keyframe_new_interpolation_type = old_type
        if "water_level" in o:

            def level(state):
                return {"FULL": 0.60, "HALF": 0.29}.get(state["text"], 0)

            keys = [(1, level(old))]
            previous = old
            for event in events:
                keys.append((1 + round(event["start"] * (frames - 1)), level(previous)))
                keys.append((1 + round(event["end"] * (frames - 1)), level(event)))
                previous = event
            for frame, value in keys:
                o.delta_location.z = value
                o.keyframe_insert(data_path="delta_location", index=2, frame=frame)
        if "clap_side" in o:
            for f in sorted({1, frames, *range(1, frames + 1, 2)}):
                state = old["text"]
                for e in events:
                    if f >= 1 + round(e["end"] * (frames - 1)):
                        state = e["text"]
                sec = clock + (f - 1) / fps
                openness = 0.5 + 0.5 * cos(sec * 8.5)
                o.scale = [v * (0.001 if state == "CLOSED" else 0.88) for v in o["rest_scale"]]
                o.keyframe_insert(data_path="scale", frame=f)
                o.delta_location.z = 0 if state == "CLOSED" else 0.08
                o.delta_location.x = -o["clap_side"] * (0.03 + 0.13 * openness if state == "CLAP" else 0)
                o.keyframe_insert(data_path="delta_location", frame=f)


def contact_accent(kind, origin, start, fps, last):
    """A short burst travels away from the contact point and settles in world space."""
    count, duration, colors = {
        "splash": (11, 0.46, ("58CBFC", "B9EDFF", "FFFFFF")),
        "dust": (6, 0.46, ("E1AD82", "FFCE9A", "F8DFC2")),
        "glint": (5, 0.29, ("FFF2A0", "FFD239", "FFFFFF")),
        "petals": (12, 0.85, ("FF678F", "FFD746", "FA91B6")),
    }[kind]
    for i in range(count):
        angle = i * 2.39996
        reach = 0.28 + 0.55 * ((i * 5) % 11) / 10
        lift = 0.22 + 0.42 * ((i * 7 + 2) % 13) / 12
        offset = (reach * cos(angle), reach * 0.53 * sin(angle))
        size = (0.085, 0.07, 0.18) if kind == "splash" else (0.12, 0.08, 0.10)
        if kind == "dust":
            size = (0.25, 0.17, 0.16)
        if kind == "glint":
            size = (0.08, 0.06, 0.19)
        o = part(origin, size, colors[i % len(colors)], shape="sphere" if kind != "glint" else "box")
        o.rotation_euler.y = -cos(angle) * 0.5
        end = start + max(3, round(fps * duration))
        for frame in sorted(
            {1, max(1, start - 1), start, *range(start + 2, min(last, end) + 1, 2), min(last, end), last}
        ):
            t = (frame - start) / (end - start)
            if 0 < t < 1:
                scale = sin(pi * t) ** 0.57
                o.location = (
                    origin.x + offset[0] * t,
                    origin.y + offset[1] * t,
                    origin.z + 4 * lift * t * (1 - t) - 0.16 * t,
                )
                o.rotation_euler.y = -cos(angle) * (0.28 + 1.1 * t)
            else:
                scale = 0
            o.scale = [v * scale for v in size]
            o.keyframe_insert(data_path="scale", frame=frame)
            o.keyframe_insert(data_path="location", frame=frame)
            o.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)

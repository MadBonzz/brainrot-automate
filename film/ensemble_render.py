"""Blender stage for timed multi-actor blocking, camera cuts and persistent props."""

import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import animate as art
from world_art import city, practical, chest_badge
from festival import street_life, practical_motion, contact_accent
from shot_rhythm import performance_sample, camera_width
from storage import copy_file
from math import sin, cos, pi, radians, atan2, acos, hypot


def ease(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def blend(a, b, t):
    return a + (b - a) * t


def progress(t, a, b):
    return ease((t - a) / (b - a))


def phi(v):
    return (v + pi) % (2 * pi) - pi


def position(actor, t):
    a, b = actor["at"], actor["to"]
    u = progress(t, actor["start"], actor["end"])
    return [blend(x, y, u) for x, y in zip(a, b)]


def channel(points, t):
    """Shape-preserving Hermite curves keep velocity through a passing pose and stop at a reversal."""
    if t <= points[0][0]:
        return points[0][1]

    def slope(i):
        if i == 0 or i == len(points) - 1:
            return 0
        a, x = points[i - 1]
        b, y = points[i]
        c, z = points[i + 1]
        left = (y - x) / (b - a)
        right = (z - y) / (c - b)
        return 2 * left * right / (left + right) if left * right > 0 else 0

    for i, ((a, x), (b, y)) in enumerate(zip(points, points[1:])):
        if t <= b:
            v = (t - a) / (b - a)
            v2 = v * v
            return blend(x, y, v2 * (3 - 2 * v)) + (b - a) * v * (1 - v) * (
                (1 - v) * slope(i) - v * slope(i + 1)
            )
    return points[-1][1]


def perform(a, look, asset, recipes, frames, fps, clock, sightline):
    rig = art.actor(asset, 0, 0, "calm")
    chest_badge(rig, look["badge"])
    # Keep the stock eye joints so saved characters can use the same facial performance.
    head = rig["head"]
    glints = {}
    whites = {}
    corners = {}
    for side in (-1, 1):
        eye = rig["eye" + str(side)]
        eye.location.y = -0.385
        eye.scale.x *= 1.20
        eye.scale.z *= 1.37
        whites[side] = art.part(
            (side * 0.165, -0.354, 0.247), (0.188, 0.050, 0.17), "ivory", head, "sphere"
        )
        glints[side] = art.part(
            (side * 0.165 - 0.018, -0.405, 0.274), (0.038, 0.013, 0.038), "ivory", head, "sphere"
        )
        corners[side] = art.part(
            (side * 0.081, -0.367, 0.069), (0.068, 0.022, 0.035), "ink", head, "sphere"
        )

    for side in (-1, 1):
        for piece in rig["knee" + str(side)].children:
            if (
                piece.type == "MESH"
                and abs(piece.scale.y - 0.05) < 0.001
                and abs(piece.scale.z - 0.07) < 0.001
            ):
                piece.location.y -= 0.012
    root = rig["root"]
    root.scale = [look["height"]] * 3
    phase = int(hashlib.sha256(a["id"].encode()).hexdigest()[:4], 16) / 65536 * 2 * pi
    start, end = a["start"], a["end"]
    beat_seconds = (frames - 1) / fps
    notice = [t * beat_seconds + 0.06 + phase * 0.018 for t in a.get("notice", [])]
    dx, dy = [v - u for u, v in zip(a["at"], a["to"])]
    dist = hypot(dx, dy)
    size = look["height"]
    paths = {
        (j, k) for cue in a["cues"] for j, chs in recipes[cue["action"]]["channels"].items() for k in chs
    }
    default = {k: tuple(rig[k].scale) for k in ("eye1", "eye-1", "mouth")}
    mood = a["mood"]
    # Curves sample the performed pose in seconds. Blender interpolates between knots at render cadence.
    keys = (1,) if a.get("pose") == "frozen" else sorted({1, frames, *range(1, frames + 1, 2)})
    for frame in keys:
        t = (frame - 1) / max(frames - 1, 1)
        sec = clock + (frame - 1) / fps
        u = progress(t, start, end)
        travel = dist * u / size
        angle = blend(
            radians(a["facing"]),
            radians(a["facing"]) + phi(radians(a["end_facing"] - a["facing"])),
            ease(t),
        )
        moving = 0
        if dist > 0.015:
            span = max(0.01, (end - start) * 0.17)
            moving = progress(t, start - span, start + span) * (1 - progress(t, end - span, end + span))
            angle += phi(atan2(dx, -dy) - angle) * moving
        x, y = position(a, t)
        root.location = (x, y, blend(*a.get("lift", (0, 0)), u))
        if "pitch" in a:
            root.rotation_euler.x = radians(blend(*a["pitch"], u))
            root.keyframe_insert(data_path="rotation_euler", index=0, frame=frame)
        root.rotation_euler.z = angle
        root.keyframe_insert(data_path="location", frame=frame)
        root.keyframe_insert(data_path="rotation_euler", frame=frame, index=2)
        vals = dict.fromkeys(paths, 0.0)

        def add(j, k, v):
            vals[j, k] = vals.get((j, k), 0) + v

        add("spine", "delta_rotation_euler.y", 0.025 * sin(sec * 2.2 + phase))
        target = sightline(t)
        if target is not None:
            direction = atan2(target[0] - x, y - target[1])
            yaw = max(-0.67, min(0.67, phi(direction - angle)))
            add("head", "delta_rotation_euler.z", yaw * (0.72 + 0.12 * sin(sec * 1.28 + phase)))
            if len(target) > 2:
                add("head", "delta_rotation_euler.x", max(-0.27, min(0.32, (2 * size - target[2]) * 0.19)))
        add("head", "delta_rotation_euler.z", 0.047 * sin(sec * 1.95 + phase))
        add(
            "head",
            "delta_rotation_euler.x",
            (0.075 if mood == "worried" else -0.04) + 0.027 * sin(sec * 2.6 + phase),
        )
        # A moving object draws the eyes, then the head, then the shoulders; reactions ripple through a group.
        elapsed = (frame - 1) / fps

        def pulse(delay):
            return max(
                (
                    sin(pi * (elapsed - hit - delay) / 0.54) ** 2
                    for hit in notice
                    if 0 < elapsed - hit - delay < 0.54
                ),
                default=0,
            )

        add("head", "delta_rotation_euler.x", -0.115 * pulse(0))
        add("spine", "delta_rotation_euler.x", -0.065 * pulse(0.10))
        add("spine", "delta_location.z", 0.014 * sin(sec * 2.7 + phase) + 0.024 * pulse(0.08))
        for side in (-1, 1):
            add(
                "arm" + str(side),
                "delta_rotation_euler.y",
                -side * (0.074 + 0.032 * cos(sec * 2.5 + phase)),
            )
            add(
                "elbow" + str(side), "delta_rotation_euler.x", -0.12 - 0.045 * cos(sec * 2.2 + phase + side)
            )
            # In stance the sole stays at the planted longitudinal coordinate. During swing it lifts and passes.
            stride = 1.12
            cycle = (travel / stride + 0.25 + (side == 1) * 0.5) % 1
            if cycle < 0.5:
                forward = stride * (0.25 - cycle)
                lift = 0
            else:
                v = (cycle - 0.5) * 2
                forward = stride * (-0.25 + 0.5 * ease(v))
                lift = 0.17 * sin(pi * v)
            reach = math.hypot(forward, 0.79 - lift)
            bend = acos(min(1, reach / 0.88))
            thigh = -(atan2(forward, 0.79 - lift) + bend)
            add("leg" + str(side), "delta_rotation_euler.x", moving * thigh)
            add("knee" + str(side), "delta_rotation_euler.x", moving * 2 * bend)
            add("arm" + str(side), "delta_rotation_euler.x", moving * 0.53 * cos(2 * pi * cycle))
        add("root", "delta_location.z", moving * (-0.075 + 0.025 * cos(travel / 1.12 * 4 * pi)))
        for c in a["cues"]:
            r = recipes[c["action"]]
            local, weight = performance_sample(
                (t - c["start"]) * beat_seconds,
                (c["end"] - c["start"]) * beat_seconds,
                r,
                c.get("play", "accent"),
            )
            if weight == 0:
                continue
            for j, chs in r["channels"].items():
                for k, pts in chs.items():
                    add(j, k, weight * channel(pts, local))
        for (j, k), v in vals.items():
            attr, axis = k.split(".")
            idx = "xyz".index(axis)
            o = rig[j]
            getattr(o, attr)[idx] = v
            o.keyframe_insert(data_path=attr, index=idx, frame=frame)
        blink = max(0.09, 1 - max(0, 1 - abs((sec + phase) % 3.25 - 1.5) / 0.12))
        for side in (-1, 1):
            k = "eye" + str(side)
            eye = rig[k]
            eye.scale.z = default[k][2] * blink * (1.32 if mood == "surprised" else 1)
            eye.keyframe_insert(data_path="scale", index=2, frame=frame)
            eyeshift = max(-0.020, min(0.020, vals.get(("head", "delta_rotation_euler.z"), 0) * 0.034))
            eye.delta_location.x = eyeshift
            eye.keyframe_insert(data_path="delta_location", index=0, frame=frame)
            whites[side].scale.z = 0.17 * blink
            whites[side].keyframe_insert(data_path="scale", index=2, frame=frame)
            glints[side].scale.z = 0.038 * blink
            glints[side].delta_location.x = eyeshift
            glints[side].keyframe_insert(data_path="scale", index=2, frame=frame)
            glints[side].keyframe_insert(data_path="delta_location", index=0, frame=frame)
            smile = {"proud": 0.034, "calm": 0.016, "surprised": -0.020, "worried": -0.028}[mood]
            corners[side].location = (
                side * (0.057 if mood == "surprised" else 0.090),
                -0.365,
                0.064 + smile,
            )
            corners[side].rotation_euler.y = -side * smile * 18
            brow = rig["brow" + str(side)]
            brow.rotation_euler.y = side * (
                {"worried": 0.39, "surprised": -0.24, "proud": -0.23, "calm": -0.1}[mood]
                + 0.06 * sin(sec * 2 + phase + side)
            )
            brow.delta_location.z = (0.047 if mood == "surprised" else 0.018) * sin(sec * 2.5 + phase)
            brow.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)
            brow.keyframe_insert(data_path="delta_location", index=2, frame=frame)
        mouth = rig["mouth"]
        mouth.scale.z = (
            default["mouth"][2] * ({"surprised": 3, "worried": 1.7, "proud": 1.7, "calm": 1}[mood])
        )
        # Only the on-screen actor assigned a line articulates the voiced passage.
        syllable = max((max(0, 1 - abs(t - mid) / half) for mid, half in a.get("syllables", [])), default=0)
        mouth.scale.z *= 1.45 + 2.1 * syllable + 0.15 * sin(sec * 4.3 + phase)
        mouth.keyframe_insert(data_path="scale", index=2, frame=frame)
        mouth.scale.x = default["mouth"][0] * (
            0.69 if mood == "surprised" else 1.22 if mood == "proud" else 1
        )
    return rig


def place_props(spec, props, rigs, frames):
    targets = {}
    for p in props:
        name = p["id"]
        old = spec["before"][name]
        root, letters, center = practical(p)
        for piece in root.children:
            if "oscillator" in piece and old["text"] != "STILL":
                axis, amplitude, phase, rate = piece["oscillator"]
                axis = int(axis)
                path = "delta_location" if axis < 3 else "delta_rotation_euler"
                for f in sorted({1, frames, *range(1, frames + 1, 3)}):
                    getattr(piece, path)[axis % 3] = amplitude * sin(
                        (spec.get("stage_clock", spec["clock"]) + (f - 1) / art.FPS) * rate + phase
                    )
                    piece.keyframe_insert(data_path=path, index=axis % 3, frame=f)
        events = [e for e in spec["shot"]["events"] if e["id"] == name]
        practical_motion(root, old, events, spec.get("stage_clock", spec["clock"]), frames, art.FPS)
        scene = bpy.context.scene
        states = [(1, old["text"])]

        def world_pose(state, graph):
            offset = Vector(state["to"])
            angle = radians(state["spin"])
            if not state["anchor"]:
                return offset, angle, False
            owner, joint = state["anchor"].split("@")
            if owner not in rigs:
                return offset, angle, True
            matrix = rigs[owner][joint].evaluated_get(graph).matrix_world
            return matrix @ offset, angle + matrix.to_euler().z, False

        def leaves(state, frame):
            for o in root.children:
                if o.get("paint_gap"):
                    o.delta_location.z = -0.28 if state["text"] == "GAP" else 0
                    o.keyframe_insert(data_path="delta_location", index=2, frame=frame)
                if "hatch_leaf" in o:
                    o.delta_location.x = o["hatch_leaf"] * (0.68 if state["text"] == "OPEN" else 0)
                    o.keyframe_insert(data_path="delta_location", index=0, frame=frame)

        leaves(old, 1)
        keyed = {1, frames}
        for e in events:
            f = 1 + round(e["start"] * (frames - 1))
            g = max(f + 1, 1 + round(e["end"] * (frames - 1)))
            keyed.update((f, g))
            states.append((g, e["text"]))
            leaves(old, f)
            leaves(e, g)
            old = e
        previous = spec["before"][name]
        if previous["anchor"] or any(e["anchor"] for e in events):
            keyed.update(range(1, frames + 1, 2))
        last_angle = None
        visibility = {}
        last_hidden = None
        for f in sorted(keyed):
            t = (f - 1) / max(1, frames - 1)
            scene.frame_set(f)
            graph = bpy.context.evaluated_depsgraph_get()
            source = previous
            dest = previous
            fraction = 1
            for e in events:
                if t < e["start"]:
                    break
                dest = e
                fraction = progress(t, e["start"], e["end"])
                if t <= e["end"]:
                    break
                source = e
            a, ang, hidden = world_pose(source, graph)
            b, target, hidden2 = world_pose(dest, graph)
            root.location = a.lerp(b, fraction)
            yaw = ang + phi(target - ang) * fraction
            if last_angle is not None:
                yaw = last_angle + phi(yaw - last_angle)
            root.rotation_euler.z = yaw
            last_angle = yaw
            root.keyframe_insert(data_path="location", frame=f)
            root.keyframe_insert(data_path="rotation_euler", index=2, frame=f)
            invisible = hidden if fraction < 0.5 else hidden2
            if f == 1 or invisible != last_hidden:
                visibility[f] = invisible
                for o in root.children_recursive:
                    o.hide_render = invisible
                    o.keyframe_insert(data_path="hide_render", frame=f)
            last_hidden = invisible
        if letters:
            # Font body cannot be animated. Switch the visibility of coincident text objects on the change frame.
            for i, (f, body) in enumerate(states):
                o = letters.copy()
                o.data = letters.data.copy()
                bpy.context.collection.objects.link(o)
                o.data.body = body
                o.data.size = min(letters.data.size, 2.4 / max(1, max(map(len, body.splitlines() or [""]))))
                if letters.animation_data:
                    o.animation_data_clear()
                end = states[i + 1][0] if i + 1 < len(states) else frames + 1
                hidden = False
                for frame in sorted({0, f, end, *visibility}):
                    hidden = visibility.get(frame, hidden)
                    o.hide_render = hidden or not f <= frame < end
                    o.keyframe_insert(data_path="hide_render", frame=frame)
            bpy.data.objects.remove(letters, do_unlink=True)
        if p["kind"] == "serpent":
            interest = art.empty("Serpent head", (-0.72, -0.08, 0.83), root)
            interest["camera_interest"] = True
            targets[name] = (interest, 0)
        else:
            targets[name] = (root, center)
    return targets


CAMERA_OFFSETS = (
    (0, 0),
    (-15, 2),
    (15, 2),
    (-30, 5),
    (30, 5),
    (0, 16),
    (-48, 9),
    (48, 9),
    (-63, 8),
    (63, 8),
)


def camera_clearance(scene, camera, f, end, targets, rigs, looks):
    """Test lines of sight through foreground bodies at three points without changing angle mid-shot."""
    focus = camera["focus"]
    if len(focus) > 2:
        return 0, 0
    samples = []
    for frame in sorted({f, (f + end) // 2, end}):
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        dots = [
            targets[i][0].evaluated_get(graph).matrix_world.translation + Vector((0, 0, targets[i][1]))
            for i in focus
        ]
        bodies = [
            (rig["root"].evaluated_get(graph).matrix_world.translation.copy(), looks[i]["height"])
            for i, rig in rigs.items()
            if i not in focus
        ]
        angles = []
        for yaw, pitch in CAMERA_OFFSETS:
            angle = radians(camera["angle"] + yaw)
            el = radians(camera["elevation"] + pitch)
            direction = Vector((sin(angle) * cos(el), -cos(angle) * cos(el), sin(el)))
            center = sum(dots, Vector()) / len(dots)
            origin = center + direction * camera["size"] * (34 / 36)
            blocked = 0
            for name, dot in zip(focus, dots):
                # A mark is deliberately invisible. Held props can be occluded by their own actor.
                # Test above/below center to avoid a single finger or stray petal deciding the shot.
                root = targets[name][0]
                if root.get("camera_interest"):
                    root = root.parent
                for dz in (-0.09, 0.09):
                    endpoint = dot + Vector((0, 0, dz))
                    ray = endpoint - origin
                    if ray.length < 0.01:
                        continue
                    hit, loc, normal, index, obj, matrix = scene.ray_cast(
                        graph, origin, ray.normalized(), distance=ray.length
                    )
                    if not hit or (loc - endpoint).length < 0.13:
                        continue
                    node = obj.original
                    while node and node != root:
                        node = node.parent
                    if node is None:
                        blocked += 1
            angles.append(blocked)
        samples.append((dots, bodies, angles))
    choices = []
    for index, (yaw, pitch) in enumerate(CAMERA_OFFSETS):
        angle = radians(camera["angle"] + yaw)
        el = radians(camera["elevation"] + pitch)
        direction = Vector((sin(angle) * cos(el), -cos(angle) * cos(el), sin(el)))
        score = 0.002 * abs(yaw) + 0.004 * pitch
        for dots, bodies, blocked in samples:
            score += blocked[index] * 0.48
            origin = sum(dots, Vector()) / len(dots) + direction * camera["size"] * (34 / 36)
            for dot in dots:
                ray = origin - dot
                for base, h in bodies:
                    # Test the head and the shoulders; ignore intersections behind or past the camera.
                    for z, r in ((2.10, 0.48), (1.32, 0.54)):
                        center = base + Vector((0, 0, z * h))
                        u = (center - dot).dot(ray) / max(0.001, ray.length_squared)
                        if 0.035 < u < 1:
                            gap = (dot + u * ray - center).length
                            score += max(0, 1 - gap / (r * h)) ** 2
        choices.append((score, yaw, pitch))
    _, yaw, pitch = min(choices)
    return yaw, pitch


def shoot(spec, plan):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    art.mesh_cache.clear()
    scene = bpy.context.scene
    shot = spec["shot"]
    frames = spec["frames"]
    fps = plan["fps"]
    art.job = plan
    art.FPS = fps
    art.setup()
    scene.view_settings.exposure = 0.60
    sh = scene.display.shading
    sh.studio_light = "paint.sl"
    sh.show_shadows = True
    sh.shadow_intensity = 0.12
    sh.studiolight_rotate_z = 0.1
    sh.show_specular_highlight = True
    sh.cavity_ridge_factor = 0.72
    sh.cavity_valley_factor = 0.82
    scene.display.light_direction = (0.46, 0.39, 0.8)
    sh.background_color = art.rgb("B7D0D2")[:3]
    place = plan["places"][shot["place"]]
    light = place.get("light", "daylight")
    if light != "daylight":
        sh.studio_light = "outdoor.sl" if light == "late_sun" else "studio.sl"
        scene.view_settings.exposure = 0.48 if light == "late_sun" else -0.10
        sh.studiolight_rotate_z = 1.5 if light == "late_sun" else -0.85
    city(place)
    street_life(place, spec.get("stage_clock", spec["clock"]), frames, fps)
    for poly in art.mesh("sphere").polygons:
        poly.use_smooth = True
    rigs = {}
    targets = {}
    actors = {a["id"]: a for a in shot["actors"]}

    def target_position(focus, t):
        if focus in actors:
            target = actors[focus]
            elevation = blend(*target.get("lift", (0, 0)), progress(t, target["start"], target["end"]))
            return [*position(target, t), elevation + 2 * plan["looks"][focus]["height"]]
        if focus not in spec["before"]:
            return None

        def landmark(state):
            owner = state["anchor"].partition("@")[0]
            if owner in actors:
                return [*position(actors[owner], t), 1.5 * plan["looks"][owner]["height"]]
            return [*state["to"][:2], state["to"][2] + 0.6]

        xyz = landmark(spec["before"][focus])
        for event in shot["events"]:
            if event["id"] == focus and event["start"] <= t:
                u = progress(t, event["start"], event["end"])
                xyz = [blend(x, y, u) for x, y in zip(xyz, landmark(event))]
        return xyz

    def sightline(actor, t):
        target = target_position(actor["look_at"], t)
        for glance in actor.get("gaze", []):
            if t < glance["at"]:
                break
            next_target = target_position(glance["focus"], t)
            if next_target is None:
                continue
            if target is None:
                target = next_target
                continue
            turn = ease((t - glance["at"]) * (frames - 1) / (fps * 0.24))
            target = [blend(x, y, turn) for x, y in zip(target, next_target)]
        return target

    for a in shot["actors"]:
        i = a["id"]
        look = plan["looks"][i]
        noticed = [e["end"] for e in shot["events"] if e["id"] == a["look_at"]] + [
            g["at"] for g in a.get("gaze", [])
        ]
        rigs[i] = perform(
            dict(a, notice=noticed),
            look,
            plan["assets"][i]["path"],
            plan["motions"],
            frames,
            fps,
            spec.get("stage_clock", spec["clock"]),
            lambda t: sightline(a, t),
        )
        targets[i] = (rigs[i]["root"], 1.57 * look["height"])
    props = [p for p in plan["props"] if p["place"] == shot["place"]]
    targets.update(place_props(spec, props, rigs, frames))
    for accent in shot.get("accents", []):
        frame = 1 + round(accent["at"] * (frames - 1))
        obj, height = targets[accent["focus"]]
        scene.frame_set(frame)
        origin = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.copy()
        origin.z += height
        contact_accent(accent["kind"], origin, frame, fps, frames)
    scene.frame_start = 1
    scene.frame_end = frames
    for idx, c in enumerate(shot["cameras"]):
        f = 1 + round(c["start"] * (frames - 1))
        end = (
            1 + round(shot["cameras"][idx + 1]["start"] * (frames - 1)) - 1
            if idx + 1 < len(shot["cameras"])
            else frames
        )
        lens = bpy.data.cameras.new("Lens")
        cam = bpy.data.objects.new("Camera", lens)
        scene.collection.objects.link(cam)
        marker = scene.timeline_markers.new("Cut", frame=f)
        marker.camera = cam
        if idx == 0:
            scene.camera = cam
        lens.type = "PERSP"
        lens.sensor_fit = "HORIZONTAL"
        lens.lens = 34
        if (
            len(c["focus"]) == 1
            and c["focus"][0] in rigs
            and c["size"] <= 2.5
            and place.get("finish") == "textured"
        ):
            # Choose the face side once per cut. A follow shot should never orbit mid-line.
            scene.frame_set((f + end) // 2)
            rig = rigs[c["focus"][0]]
            face = rig["head"].evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
            forward = face.to_quaternion() @ Vector((0, -1, 0))
            heading = atan2(forward.x, -forward.y)
            offset = max(-0.68, min(0.68, phi(radians(c["angle"]) - heading)))
            c = dict(c, angle=math.degrees(heading + offset))
        yaw_offset, pitch_offset = camera_clearance(scene, c, f, end, targets, rigs, plan["looks"])
        move = c.get("move", "arc" if c["drift"] else "follow")
        samples = [f] if move == "hold" else sorted({f, end, *range(f, end + 1, 3)})
        for k in samples:
            scene.frame_set(k)
            graph = bpy.context.evaluated_depsgraph_get()
            locs = [
                o.evaluated_get(graph).matrix_world.translation + Vector((0, 0, h))
                for o, h in (targets[key] for key in c["focus"])
            ]
            aim = sum(locs, Vector()) / len(locs)
            if len(c["focus"]) == 1 and c["focus"][0] in rigs and c["size"] <= 2.3:
                aim.z += 0.43 * plan["looks"][c["focus"][0]]["height"]
            v = (k - f) / max(1, end - f)
            angle = radians(
                c["angle"] + yaw_offset + (c["drift"] * (ease(v) - 0.5) if move == "arc" else 0)
            )
            el = radians(c["elevation"] + pitch_offset)
            width = camera_width(c["size"], v, move)
            if len(c["focus"]) == 1:
                subject = targets[c["focus"][0]][0]
                # Inserts of lettering must retain both edges, even during a punch-in.
                width = max(width, subject.get("readable_width", 0.0))
            if len(locs) > 1:
                right = Vector((cos(angle), sin(angle), 0))
                span = max(abs((loc - aim).dot(right)) for loc in locs) * 2
                width = max(width, span + 1.08)
            distance = width * lens.lens / lens.sensor_width
            cam.location = aim + distance * Vector((sin(angle) * cos(el), -cos(angle) * cos(el), sin(el)))
            cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
            cam.keyframe_insert(data_path="location", frame=k)
            cam.keyframe_insert(data_path="rotation_euler", frame=k)
    if shot.get("selective_color"):
        keep = set()
        for name in shot["selective_color"]:
            root = targets[name][0]
            if root.get("camera_interest"):
                root = root.parent
            keep.update(root.children_recursive)
            keep.add(root)
        for obj in scene.objects:
            if obj.type in ("MESH", "FONT") and obj not in keep:
                y = sum(a * b for a, b in zip(obj.color, (0.2126, 0.7152, 0.0722)))
                obj.color = (y, y, y, 1)
    if place.get("finish") == "textured":
        from surface_art import finish

        finish(scene)
        scene.view_settings.exposure -= 0.15
        sh.shadow_intensity = 0.31
    if "atmosphere" in shot:
        from atmosphere import stage

        stage(scene, shot["atmosphere"], frames, fps, spec.get("stage_clock", spec["clock"]))
    scene.frame_set(1)
    return scene


def run(plan):
    for s in plan["shots"]:
        clip = Path(s["clip"])
        if clip.is_file():
            continue
        scene = shoot(s, plan)
        clip.parent.mkdir(parents=True, exist_ok=True)
        if plan.get("plates"):
            for f in s["sample_frames"]:
                scene.frame_set(f)
                scene.render.image_settings.file_format = "PNG"
                scene.render.filepath = str(clip.parent / f"{clip.stem}-{f}.png")
                bpy.ops.render.render(write_still=True)
            continue
        import tempfile

        with tempfile.TemporaryDirectory(dir=clip.parent) as tmp:
            target = Path(tmp) / "clip.mp4"
            scene.render.image_settings.file_format = "FFMPEG"
            scene.render.ffmpeg.format = "MPEG4"
            scene.render.ffmpeg.codec = "H264"
            scene.render.ffmpeg.constant_rate_factor = "HIGH"
            scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
            scene.render.filepath = str(target)
            bpy.ops.render.render(animation=True)
            target.replace(clip)
        copy_file(clip, s["shared"])


if __name__ == "__main__":
    run(json.loads(Path(sys.argv[-1]).read_text(encoding="utf8")))

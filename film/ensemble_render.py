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
    dx, dy = [v - u for u, v in zip(a["at"], a["to"])]
    dist = hypot(dx, dy)
    size = look["height"]
    paths = {
        (j, k) for cue in a["cues"] for j, chs in recipes[cue["action"]]["channels"].items() for k in chs
    }
    default = {k: tuple(rig[k].scale) for k in ("eye1", "eye-1", "mouth")}
    mood = a["mood"]
    # Curves sample the performed pose in seconds. Blender interpolates between knots at render cadence.
    for frame in sorted({1, frames, *range(1, frames + 1, 2)}):
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
        root.location = (x, y, 0)
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
        add("spine", "delta_location.z", 0.014 * sin(sec * 2.7 + phase))
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
            v = (t - c["start"]) / (c["end"] - c["start"])
            if not 0 < v < 1:
                continue
            r = recipes[c["action"]]
            # Leave recovery time even for legacy clips whose last key holds the pose.
            local = min(1, v / 0.83) * r["frames"]
            weight = 1 - ease((v - 0.83) / 0.17)
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
        mouth.scale.z *= 1 + 0.26 * sin(sec * 4.3 + phase)
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
        events = [e for e in spec["shot"]["events"] if e["id"] == name]
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
        targets[name] = (root, center)
    return targets


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
    scene.view_settings.exposure = 0.36
    sh = scene.display.shading
    sh.show_shadows = True
    sh.shadow_intensity = 0.26
    sh.studiolight_rotate_z = 0.4
    sh.show_specular_highlight = False
    sh.cavity_ridge_factor = 0.72
    sh.cavity_valley_factor = 0.82
    scene.display.light_direction = (0.46, 0.39, 0.8)
    sh.background_color = art.rgb("B7D0D2")[:3]
    city(plan["places"][shot["place"]])
    rigs = {}
    targets = {}
    actors = {a["id"]: a for a in shot["actors"]}

    def sightline(actor, t):
        focus = actor["look_at"]
        if focus in actors:
            return position(actors[focus], t)
        if focus in spec["before"] and not spec["before"][focus]["anchor"]:
            xyz = spec["before"][focus]["to"]
            return [xyz[0], xyz[1], xyz[2] + 0.6]
        return None

    for a in shot["actors"]:
        i = a["id"]
        look = plan["looks"][i]
        rigs[i] = perform(
            a,
            look,
            plan["assets"][i]["path"],
            plan["motions"],
            frames,
            fps,
            spec["clock"],
            lambda t: sightline(a, t),
        )
        targets[i] = (rigs[i]["root"], 1.57 * look["height"])
    props = [p for p in plan["props"] if p["place"] == shot["place"]]
    targets.update(place_props(spec, props, rigs, frames))
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
        for k in sorted({f, end, *range(f, end + 1, 6)}):
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
            angle = radians(c["angle"] + c["drift"] * (ease(v) - 0.5))
            el = radians(c["elevation"])
            width = c["size"] * (1 - 0.045 * ease(v))
            distance = width * lens.lens / lens.sensor_width
            cam.location = aim + distance * Vector((sin(angle) * cos(el), -cos(angle) * cos(el), sin(el)))
            cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
            cam.keyframe_insert(data_path="location", frame=k)
            cam.keyframe_insert(data_path="rotation_euler", frame=k)
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

"""Photograph an existing performance from the viewpoint of someone searching with a torch."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ensemble_render import shoot as stage
from surface_art import finish
from vista_render import shoot as ordinary_view, write_view


def lamp(scene, kind, name, watts, color):
    data = bpy.data.lights.new(name, kind)
    data.energy = watts
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    return obj


def torch_scene(job, view):
    take = job["takes"][str(view["beat"])]
    scene = stage(take, job)
    if job["places"][take["shot"]["place"]].get("finish") != "textured":
        finish(scene)
    first, last = view["start"] + 1, view["stop"]
    scene.frame_start, scene.frame_end = first, last
    scene.frame_set(first)
    camera = sorted(scene.timeline_markers, key=lambda marker: marker.frame)[view["camera"] - 1].camera
    # The lamp is slightly below and to the side of the lens, as if held in the operator's hand.
    # Parenting it to the real dolly keeps highlights, occlusion and shadows consistent with the set.
    field_width = take["shot"]["cameras"][view["camera"] - 1]["size"]
    power = 130 * max(0.22, min(1.5, (field_width / 3.2) ** 2))
    torch = lamp(scene, "SPOT", "Handheld torch", power, (0.88, 0.93, 1))
    torch.parent = camera
    torch.location = (0.18, -0.24, -0.08)
    torch.data.spot_size = math.radians(24)
    torch.data.spot_blend = 0.56
    torch.data.shadow_soft_size = 0.045
    for t, pitch, yaw in ((0, -13, -22), (0.34, 0, -5), (0.68, 8, 4), (1, 12, 0)):
        torch.rotation_euler = (math.radians(pitch), math.radians(yaw), 0)
        torch.keyframe_insert(data_path="rotation_euler", frame=first + round(t * (last - first)))
    # A distant, cool practical separates the figure from the wall when the torch looks elsewhere.
    world = bpy.data.worlds.new("After hours")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.11, 0.14, 0.30, 1)
    background.inputs["Strength"].default_value = 0.15
    scene.world = world
    rim = lamp(scene, "AREA", "Light from the stockroom", 105, (0.33, 0.42, 1))
    rim.location = (-3, 4.9, 4.3)
    rim.data.shape = "DISK"
    rim.data.size = 2.5
    rim.rotation_euler = (Vector((0, 0.8, 1.7)) - rim.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8 if job["width"] >= 1080 else 4
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 1
    scene.cycles.use_denoising = False
    return scene


if __name__ == "__main__":
    payload = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text(encoding="utf8"))
    for piece in payload["pieces"]:
        if piece["kind"] == "torch_detail":
            write_view(torch_scene(payload, piece), piece)
        else:
            ordinary_view(payload, piece)

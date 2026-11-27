"""Blender entry point for an explicitly blocked take with a fixed line of action.

The shot describes world geometry, rig poses, cameras, and changes of prop ownership.
Times are seconds from the start of the take. Rotations in the authored file are degrees.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import animate as art
from world_art import city, practical, chest_badge


def radians(values):
    return [math.radians(v) for v in values]


def make_scene(plan, shot):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    art.mesh_cache.clear()
    art.job = plan
    art.FPS = plan["fps"]
    art.setup()
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = shot["frames"]
    shade = scene.display.shading
    shade.studio_light = "paint.sl"
    shade.show_shadows = True
    shade.shadow_intensity = 0.20
    shade.show_specular_highlight = False
    shade.background_color = art.rgb(shot.get("sky", "A2D7EC"))[:3]
    scene.view_settings.exposure = shot.get("exposure", 0.33)
    if shot.get("place"):
        city(plan["places"][shot["place"]])
    objects = {}
    for part in shot["objects"]:
        name = part["id"]
        if name in objects:
            raise ValueError(f"Duplicate object {name}")
        parent = objects.get(part.get("parent"))
        if part.get("parent") and parent is None:
            raise ValueError(f"Missing parent for {name}")
        pos, scale = part.get("at", [0, 0, 0]), part.get("size", [1, 1, 1])
        kind = part["kind"]
        if kind == "actor":
            identity = part["actor"]
            look = plan["looks"][identity]
            rig = art.actor(plan["assets"][identity]["path"], 0, 0, part.get("mood", "calm"))
            chest_badge(rig, look.get("badge", ""))
            for key, joint in rig.items():
                objects[name + ":" + key] = joint
            obj = rig["root"]
            obj.scale = [part.get("height",look["height"])] * 3
        elif kind == "group":
            obj = art.empty(name, pos, parent)
            obj.scale = scale
        elif kind == "text":
            obj = art.label(part["text"], pos, part["font_size"], part["color"], parent)
        elif kind == "practical":
            obj, _, _ = practical(dict(id=name, at=pos, kind=part["model"], color=part["color"],
                                       text=part.get("text",""), parts=[], scale=scale[0]))
        else:
            obj = art.part(pos, scale, part["color"], parent, kind)
        obj.name = name
        obj.parent = parent
        obj.location = pos
        if "rotation" in part:
            obj.rotation_euler = radians(part["rotation"])
        objects[name] = obj

    def keytime(seconds):
        return max(1, min(scene.frame_end, 1 + round(seconds * plan["fps"])))

    for track in shot["tracks"]:
        obj = objects[track["target"]]
        prop = track["property"]
        path = {"pos":"location", "rot":"rotation_euler", "size":"scale", "exposure":"view_settings.exposure"}[prop]
        for sec, value in track["keys"]:
            if prop == "exposure":
                scene.view_settings.exposure = value
                scene.keyframe_insert(data_path=path,frame=keytime(sec))
            else:
                setattr(obj,path,radians(value) if prop=="rot" else value)
                obj.keyframe_insert(data_path=path,frame=keytime(sec))
        if track.get("step"):
            owner = scene if prop == "exposure" else obj
            for curve in owner.animation_data.action.fcurves:
                if curve.data_path == path:
                    for key in curve.keyframe_points:
                        key.interpolation = "CONSTANT"

    for cut in shot["cameras"]:
        lens = bpy.data.cameras.new("Lens")
        lens.type = "PERSP"
        lens.sensor_fit = "HORIZONTAL"
        lens.lens = cut.get("lens", 36)
        camera = bpy.data.objects.new("Camera", lens)
        scene.collection.objects.link(camera)
        frame = keytime(cut["at"])
        marker = scene.timeline_markers.new("Camera", frame=frame)
        marker.camera = camera
        if frame == 1:
            scene.camera = camera
        for sec, position, target in cut["keys"]:
            camera.location = position
            camera.rotation_euler = (Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()
            camera.keyframe_insert(data_path="location",frame=keytime(sec))
            camera.keyframe_insert(data_path="rotation_euler",frame=keytime(sec))

    for held in shot.get("holds",[]):
        obj = objects[held["item"]]
        if obj.parent:
            raise ValueError("A transferred object must use world coordinates")
        phases = held["anchors"]
        for frame in range(1,scene.frame_end+1):
            sec = (frame-1)/plan["fps"]
            if sec < phases[0][0]:
                continue
            scene.frame_set(frame)
            left = max(i for i,phase in enumerate(phases) if phase[0] <= sec)
            def endpoint(phase):
                _, joint, offset = phase
                if joint is None:
                    return Vector(offset)
                return objects[joint].evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world @ Vector(offset)
            loc = endpoint(phases[left])
            if left+1 < len(phases):
                right=phases[left+1]
                fraction=max(0,min(1,(sec-phases[left][0])/(right[0]-phases[left][0])))
                if phases[left][1:] != right[1:]:
                    loc=loc.lerp(endpoint(right),fraction*fraction*(3-2*fraction))
            obj.location=loc
            obj.keyframe_insert(data_path="location",frame=frame)
    scene.frame_set(1)
    return scene


def main():
    request=json.loads(Path(sys.argv[-1]).read_text(encoding="utf8"))
    plan=request["plan"]
    for shot in request["shots"]:
        scene=make_scene(plan,shot)
        if shot.get("proof"):
            for sec,filename in shot["proof"]:
                scene.frame_set(max(1,min(scene.frame_end,1+round(sec*plan["fps"]))))
                scene.render.image_settings.file_format="PNG"
                scene.render.filepath=filename
                bpy.ops.render.render(write_still=True)
        else:
            out=Path(shot["output"])
            temp=out.with_suffix(".partial.mp4")
            scene.render.image_settings.file_format="FFMPEG"
            scene.render.ffmpeg.format="MPEG4"
            scene.render.ffmpeg.codec="H264"
            scene.render.ffmpeg.constant_rate_factor="HIGH"
            scene.render.ffmpeg.ffmpeg_preset="REALTIME"
            scene.render.filepath=str(temp)
            bpy.ops.render.render(animation=True)
            temp.replace(out)


if __name__=="__main__":
    main()

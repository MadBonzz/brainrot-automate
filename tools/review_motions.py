"""Blender-only motion review. Run with -- --help for options."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'film'))
import animate as animation
from performances import PRESETS, read_motions, motion_end


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    animation.mesh_cache.clear()


def at(scene, frame):
    scene.frame_set(int(frame), subframe=frame-int(frame))


def soles(rig):
    return {str(o['shortfilm_sole']):o for o in rig['root'].children_recursive if 'shortfilm_sole' in o}


def foot(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    center = sum(corners, Vector())/len(corners)
    return center, min(c.z for c in corners)


def measure(name, recipe, character, fps, landmarks):
    reset()
    animation.FPS = fps
    rig = animation.actor(str(character), 0, 0, 'calm')
    duration = recipe['frames']
    cue = 5
    repeats = 2 if recipe.get('loop') else 1
    end = math.ceil(cue+(repeats*duration+6)*fps/24)
    animation.motion(rig,name,cue,end,{})
    scene = bpy.context.scene
    scene.render.fps = fps
    boots = soles(rig)
    if set(boots) != {'-1','1'}:
        raise ValueError(f'{name} could not find the two stock shoe soles')
    errors = []
    def require(ok,message):
        if not ok and message not in errors:
            errors.append(message)
    worst = 0.
    for joint, channels in recipe['channels'].items():
        for channel, points in channels.items():
            prop, axis = channel.rsplit('.',1)
            index = 'xyz'.index(axis)
            checks = [(cue-1,0)]
            for cycle in range(repeats):
                checks.extend((cue+(cycle*duration+f)*fps/24,val) for f,val in points)
            if not recipe.get('loop'):
                checks.append((end,points[-1][1]))
            for f,expected in checks:
                at(scene,f)
                actual = getattr(rig[joint],prop)[index]
                worst = max(worst,abs(actual-expected))
    require(worst < .001, 'key/cue/hold error')
    hand_error = 0.
    hands = {o['shortfilm_hand']:o for o in rig['root'].children_recursive if 'shortfilm_hand' in o}
    for mark in landmarks:
        at(scene,cue+mark['frame']*fps/24)
        ref = rig['head'] if mark['space']=='head' else rig['spine']
        local = Vector(mark['point'])
        if mark['space']=='body':
            local.z -= .91
        distance = (hands[mark['side']].matrix_world.translation-ref.matrix_world @ local).length
        hand_error = max(hand_error,distance)
        require(distance <= mark['tolerance'],'missed hand landmark at '+str(mark['frame']))
    min_z = 100.
    max_clearance = -100.
    max_drift = 0.
    max_support_height = 0.
    anchors = {}
    for frame in range(cue,end+1):
        at(scene,frame)
        feet = {k:foot(v) for k,v in boots.items()}
        low = min(pair[1] for pair in feet.values())
        min_z = min(min_z,low)
        max_clearance = max(max_clearance,low)
        require(all(math.isfinite(v) for joint in rig.values() for v in joint.matrix_world.translation),'nonfinite geometry')
        t = (frame-cue)*24/fps
        if recipe.get('loop'):
            t %= duration
        for segment in recipe.get('plant',[]):
            side,start,stop = map(int,segment.split(':'))
            if start <= t <= stop:
                max_support_height = max(max_support_height,feet[str(side)][1])
                center = feet[str(side)][0].xy
                cycle = int((frame-cue)*24/fps//duration) if recipe.get('loop') else 0
                anchor = anchors.setdefault((segment,cycle),center.copy())
                max_drift = max(max_drift,(center-anchor).length)
    require(min_z >= -.025, 'shoe below floor')
    if recipe.get('ground'):
        require(max_clearance < .05, 'both soles float during grounded move')
    require(max_drift < .035,'planted shoe slides')
    require(max_support_height < .04,'supporting shoe leaves the floor')
    # Repeat through the normal late-cue shot-length rule. A full gesture once collapsed to a neutral frame.
    late = animation.actor(str(character), 2, 0, 'calm')
    short_end = motion_end(cue,cue+1,fps,[recipe])
    animation.motion(late,name,cue,short_end,{})
    excursion = 0.
    for frame in range(cue+1, short_end+1):
        at(scene,frame)
        excursion = max(excursion,max(j.delta_rotation_euler.to_matrix().to_quaternion().angle for j in late.values()))
    require(excursion > .12,'late cue has no readable rotation')
    return dict(fps=fps, late_cue_tail=short_end-cue, max_key_error=round(worst,6), min_sole_z=round(min_z,4),
                max_sole_clearance=round(max_clearance,4), max_plant_drift=round(max_drift,4), max_support_height=round(max_support_height,4), max_landmark_distance=round(hand_error,4), errors=errors)


def render_clip(name, recipe, character, out):
    reset()
    animation.FPS = 12
    animation.setup()
    scene = bpy.context.scene
    rig = animation.actor(str(character), 0, 0, 'calm')
    cue = 3
    cycles = 1.5 if recipe.get('loop') else 1
    end = math.ceil(cue+recipe['frames']*cycles/2+3)
    animation.motion(rig,name,cue,end,{})
    # A three-quarter view exposes elbow depth and includes a fixed floor reference.
    animation.part((0,0,-.09),(200,200,.16),'floor')
    for x in (-2,-1,0,1,2):
        animation.part((x,0,-.008),(.025,7,.01),'steel')
        animation.part((0,x,-.008),(7,.025,.01),'steel')
    animation.camera(dict(position=(3.7,-7.5,3.0),target=(0,0,1.24),span=3.5,end_zoom=1),end)
    scene.render.resolution_x=360
    scene.render.resolution_y=334
    scene.frame_start=1
    scene.frame_end=end
    views = []
    for folder,position in [('frames',None),('profile',(7.5,-1.9,2.6))]:
        if position:
            cam = scene.camera
            cam.location = position
            cam.rotation_euler = (Vector((0,0,1.24))-cam.location).to_track_quat('-Z','Y').to_euler()
        frames=out/folder/name
        frames.mkdir(parents=True,exist_ok=True)
        scene.render.filepath=str(frames/'f-')
        bpy.ops.render.render(animation=True)
        views.extend(['-framerate','12','-start_number','1','-i',str(frames/'f-%04d.png')])
    clip = out/(name+'.mp4')
    title=name.replace('_',' ')
    filters=(f"[0:v][1:v]hstack,pad=720:384:0:0:color=0x192331,"
             f"drawtext=text='{title}':fontsize=23:fontcolor=white:x=(w-tw)/2:y=346")
    subprocess.run(['ffmpeg','-v','error','-y',*views,'-frames:v',str(end),'-filter_complex',filters,
                    '-c:v','libx264','-threads','2','-crf','17','-pix_fmt','yuv420p',str(clip)],check=True)



def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch',required=True,choices=['gestures','footwork','pantomime'])
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--render',action='store_true',help='Render and label every motion as a real MP4.')
    p.add_argument('--character',type=Path,help='Check an existing compatible character file.')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    definitions=json.loads((PRESETS/'performances'/(args.batch+'.json')).read_text())
    motions=read_motions()
    character=args.character.resolve() if args.character else out/'models'/'review-cast.blend'
    if not args.character:
        animation.save_asset(dict(path=str(character),kind='character',coat='rust',role='lead'))
    report={}
    for name in definitions:
        recipe=motions[name]
        revision=hashlib.sha256(json.dumps(recipe,sort_keys=True).encode()).hexdigest()[:12]
        path=out/'models'/f'{name}-{revision}.blend'
        animation.save_asset(dict(path=str(path),kind='motions',name=name,recipe=recipe))
        animation.job=dict(motions=motions,models={'motions/'+name:{'path':str(path)}},width=360,height=334)
        report[name]=[measure(name,recipe,character,fps,definitions[name].get('landmarks',[])) for fps in (12,24)]
        if args.render:
            render_clip(name,recipe,character,out)
        print(name,report[name],flush=True)
    (out/'checks.json').write_text(json.dumps(report,indent=2))
    failed=[k for k,rows in report.items() if any(r['errors'] for r in rows)]
    if failed:
        raise RuntimeError('Motion review failures: '+', '.join(failed))


if __name__=='__main__':
    main()

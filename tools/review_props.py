"""Build, stage and inspect the prop catalog in Blender without an episode or model call."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'film'))
import animate as a
from film.props import geometry, instruments, machines, miniatures
from film.performances import read_motions
from film.prop_timing import prop_end

MOTIONS = read_motions()
ACTIONS = ('reach','point','half_turn_hop','signal_timeout')
CAMERAS = json.loads((ROOT/'film/presets/cameras.json').read_text())
SETS = ('station','archive','rooftop','hallway')
BATCHES = dict(instruments=instruments.MODELS, machines=machines.MODELS, miniatures=miniatures.MODELS)
PAINTS = ('teal','rust','blue','lavender','teal')


def reset(fps):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    a.mesh_cache.clear()
    a.FPS = fps
    a.job = dict(width=360,height=640)
    a.setup()


def vertices(objects):
    """Keep homogeneous local vertex arrays for per-frame world-space measurements."""
    result = {}
    for o in objects:
        if o.type=='MESH':
            coords = np.empty(len(o.data.vertices)*3,dtype=np.float32)
            o.data.vertices.foreach_get('co',coords)
            result[o] = np.column_stack((coords.reshape(-1,3),np.ones(len(coords)//3)))
    return result


def world(group):
    return np.vstack([coords @ np.array(o.matrix_world)[:3,:].T for o,coords in group.items()])


def pose(objects):
    return np.array([np.array(o.matrix_world) for o in objects])


def cues(path, design):
    """Exercise all cues, signed turns, hidden cuts and random-access evaluation at both rates."""
    results = {}
    for fps in (12,24):
        counts = 0
        framing = None
        for act,visible,angle,delta in [('still',True,0,0),('turn',True,32,-187),('turn',True,-15,720),
                                         ('pulse',True,71,0),('vanish',True,0,0),('still',False,0,0),
                                         ('turn',False,10,95),('pulse',False,45,0),('appear',False,77,0),('appear',True,77,0),('vanish',False,12,0)]:
            reset(fps)
            cue = 4
            end = prop_end(cue,cue+2,fps,act)
            root = a.stage_prop(str(path),design,act,cue,end,angle,delta,visible)
            preset = a.fit_clue_camera(CAMERAS['clue'],root)
            if framing is None:
                framing=preset
            assert abs(preset['span']-framing['span'])<1e-6 and np.allclose(preset['target'],framing['target']), 'zoom changed across cut'
            a.camera(preset,end)
            meshes = vertices(root.children_recursive)
            hand = next(o for o in [root,*root.children_recursive] if o.get('clue_turn'))
            label = next(o for o in bpy.context.scene.objects if o.type=='FONT')
            bpy.context.view_layer.update()
            panel = label.matrix_world.copy()
            lettering = np.array([panel @ Vector(c) for c in label.bound_box])
            scene = bpy.context.scene
            frames = {}
            scales = []
            first_angle = None
            axis = 'xyz'.index(hand.get('clue_axis','y' if design['kind']=='clock' else 'z'))
            for fr in range(1,end+1):
                scene.frame_set(fr)
                sign_uv = projected(scene,scene.camera,lettering)
                assert sign_uv.min()>.007 and sign_uv.max()<.993,(act,fr,'clipped plaque text')
                sizes = list(root.scale)
                assert max(sizes)-min(sizes)<1e-6 and min(sizes)>=-1e-7
                assert np.allclose(panel,label.matrix_world,atol=1e-6),'plaque drift'
                scales.append(sizes[0])
                if fr==1: first_angle=hand.rotation_euler[axis]
                if sizes[0]>1e-6:
                    pts = world(meshes)
                    uv=projected(scene,scene.camera,pts)
                    assert uv.min()>=.01 and uv.max()<=.99,(act,fr,'clue camera crop')
                    low = pts[:,2].min()
                    assert abs(low-1.03)<.008,(act,fr,'surface gap',low)
                    support = pts[pts[:,2]<low+.003]
                    assert np.max(abs(support[:,0]-1))<=.746 and np.max(abs(support[:,1]-.12))<=.471,(act,fr,'overhang')
                    assert np.isfinite(pts).all()
                frames[fr] = pose(meshes)
            assert abs(first_angle-math.radians(angle))<1e-5
            expected=math.radians(angle+(delta if act=='turn' else 0))
            assert abs(hand.rotation_euler[axis]-expected)<1e-5
            if act=='pulse' and visible:
                assert abs(max(scales)/scales[0]-1.15)<1e-5 and abs(scales[-1]-scales[0])<1e-6
            if act=='vanish':assert (scales[0]>.01)==visible and scales[-1]==0
            if act=='appear':assert (scales[0]>.01)==visible and scales[-1]>.01
            if not visible and act!='appear':assert max(scales)==0
            if act in ('still','turn') and visible:assert min(scales)>.01 and max(scales)-min(scales)<1e-6
            if act!='appear':assert all(abs(v-scales[0])<1e-6 for v in scales[:cue])
            for fr in [end,1,cue,(end+cue)//2,2,end]:
                scene.frame_set(fr)
                assert np.allclose(frames[fr],pose(meshes),atol=1e-6),'seek changed evaluated pose'
            if act=='turn' and visible:
                expected_pose = frames[end]
                reset(fps)
                new_root = a.stage_prop(str(path),design,'still',2,8,(angle+delta)%360,0,True)
                bpy.context.scene.frame_set(1)
                assert np.allclose(expected_pose,pose(vertices(new_root.children_recursive)),atol=1e-5),'rotation jumped at cut'
            counts += len(frames)
        results[fps]=counts
    return results


def reuse(path,design):
    reset(12)
    source = hashlib.sha256(path.read_bytes()).hexdigest()
    roots = []
    colors = ('blue','rust')
    for label,color in zip(('NORTH','SOUTH'),colors):
        roots.append(a.stage_prop(str(path),dict(design,label=label,color=color),'still',2,8,0,0))
    for root,color in zip(roots,colors):
        marked = [o for o in root.children_recursive if o.get('clue_paint')]
        if design['kind']!='custom':
            assert marked,'no paintable surfaces'
        assert all(np.allclose(o.color,a.rgb(color)) for o in marked),'paint leaked between instances'
    signs = sorted(o.data.body for o in bpy.context.scene.objects if o.type=='FONT')
    assert signs==['NORTH','SOUTH']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source,'changed cached prop file'


def aabb(objects):
    corners = np.array([o.matrix_world @ Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box])
    return corners.min(axis=0),corners.max(axis=0)


def collisions(meshes, others):
    def tree(obj):
        verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        return BVHTree.FromPolygons(verts,[p.vertices[:] for p in obj.data.polygons])
    prop_bounds = [(o,aabb([o])) for o in meshes]
    for other in others:
        low,high = aabb([other])
        for o,(lo,hi) in prop_bounds:
            if np.all(hi>low+.0001) and np.all(high>lo+.0001):
                if tree(o).overlap(tree(other)):
                    return (o.name,other.name)
    return None


def projected(scene, camera, pts):
    # Orthographic camera coordinates, matching Blender's normalized viewport.
    world_matrix = np.array(camera.matrix_world.inverted())
    cam = pts @ world_matrix[:3,:3].T + world_matrix[:3,3]
    aspect = scene.render.resolution_x/scene.render.resolution_y
    scale = camera.data.ortho_scale
    return .5+cam[:,:2]/[scale*min(1,aspect),scale/max(1,aspect)]


def has_view(scene, camera, meshes):
    """Use orthographic rays against the evaluated set and actors, including occlusion."""
    ray = camera.matrix_world.to_quaternion() @ Vector((0,0,-1))
    deps=bpy.context.evaluated_depsgraph_get()
    seen = 0
    for o in meshes:
        target=o.matrix_world.translation
        screen=world_to_camera_view(scene,camera,target)
        if 0<screen.x<1 and 0<screen.y<1 and screen.z>0:
            depth = (target-camera.location).dot(ray)
            start = target-ray*(depth-camera.data.clip_start)
            hit,_,_,_,obj,_ = scene.ray_cast(deps,start,ray,distance=camera.data.clip_end)
            if hit and obj.original in meshes: seen+=1
    return seen


def capture(scene, path):
    path.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)


def environment(path,design,assets,out,render):
    name=design['kind']
    scene_rows={}
    for index,kind in enumerate(SETS):
        reset(12)
        scene=bpy.context.scene
        set_objects=list(a.load_collection(str(assets/(kind+'.blend')),'Set').all_objects)
        a.set_sign('NORTH QUAY')
        actors=[a.actor(str(assets/'lead.blend'),-1.02,.12,'calm'),
                a.actor(str(assets/'witness.blend'),.08,1.34,'worried')]
        a.job['motions']=MOTIONS
        a.job['models']={'motions/'+n:{'path':str(assets/(n+'.blend'))} for n in ACTIONS}
        for rig in actors:a.motion(rig,ACTIONS[index],3,17,{})
        root=a.stage_prop(str(path),design,'turn',4,17,0,135)
        meshes=vertices(root.children_recursive)
        angles={}
        for camera,preset in CAMERAS.items():
            if camera=='clue':preset=a.fit_clue_camera(preset,root)
            a.camera(preset,17)
            angles[camera]=scene.camera
        # The additional view checks depth and the back of the prop.
        center=(1,.12,1.53)
        a.camera(dict(position=(3.5,1.9,2.55),target=center,span=2.95,end_zoom=1),17)
        angles['reverse']=scene.camera
        obstacles=[(o,aabb([o])) for o in set_objects if o.type=='MESH']
        row={}
        for fr in range(1,18):
            scene.frame_set(fr)
            points=world(meshes)
            lo,hi=points.min(axis=0),points.max(axis=0)
            for other,(low,high) in obstacles:
                if np.all(hi>low+.001) and np.all(high>lo+.001):
                    assert not collisions(meshes,[other]),('set intersection',kind,other.name)
            for actor in actors:
                low,high=aabb(actor['root'].children_recursive)
                if np.all(hi>low+.001) and np.all(high>lo+.001):
                    hit = collisions(meshes,[o for o in actor['root'].children_recursive if o.type=='MESH'])
                    assert not hit,('actor intersection',kind,fr,hit)
            border=projected(scene,angles['clue'],points)
            assert border.min()>=.012 and border.max()<=.988,(kind,fr,'clipped clue',border.min(),border.max())
        for camera,cam in angles.items():
            scene.frame_set(4)
            before=pose(meshes)
            scene.camera=cam
            bpy.context.view_layer.update()
            assert np.allclose(before,pose(meshes),atol=1e-7),'camera switch moved geometry'
            samples = []
            for frame in (1,6,8,17):
                scene.frame_set(frame)
                samples.append(has_view(scene,cam,meshes))
            row[camera]=min(samples)
            if camera in ('clue','wide','reverse'):
                assert row[camera]>0,('fully occluded',kind,camera,samples)
            if render:
                scene.frame_set(4)
                capture(scene,out/name/kind/(camera+'.png'))
        if render and index==0:
            # Real frame changes from a fixed production clue camera.
            scene.camera=angles['clue']
            for fr in range(1,18):
                scene.frame_set(fr)
                capture(scene,out/name/'turn'/f'{fr:03}.png')
        scene_rows[kind]=row
    return scene_rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',choices=[*BATCHES,'legacy'],required=True)
    parser.add_argument('--only',help='Review a single kind in the selected batch')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--render',action='store_true')
    opt=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=opt.out.resolve()
    assets=out/'models'
    assets.mkdir(parents=True,exist_ok=True)
    # Separate output roots can run concurrently.
    for kind in SETS:
        a.save_asset(dict(kind='sets',name=kind,path=str(assets/(kind+'.blend'))))
    for role,c in [('lead','rust'),('witness','blue')]:
        a.save_asset(dict(kind='character',role=role,coat=c,path=str(assets/(role+'.blend'))))
    for action in ACTIONS:
        a.save_asset(dict(kind='motions',name=action,recipe=MOTIONS[action],path=str(assets/(action+'.blend'))))
    kinds=([f.__name__ for f in BATCHES[opt.batch]] if opt.batch!='legacy' else ['clock','signal','radio','lantern','custom'])
    if opt.only:
        assert opt.only in kinds
        indices=[kinds.index(opt.only)]
    else:
        indices=range(len(kinds))
    checks={}
    for i in indices:
        name=kinds[i]
        title = name.replace('_',' ')
        plaque = title if len(title)<=12 else title.rsplit(' ',1)[-1]
        design=dict(kind=name,label=plaque,color=PAINTS[i%len(PAINTS)],parts=[])
        if name=='custom':
            design['parts']=[dict(shape='box',x=.2,y=.15,z=-.36,width=1.3,depth=.65,height=.48,color='blue'),
                             dict(shape='sphere',x=.17,y=.13,z=.10,width=.55,depth=.63,height=.47,color='red')]
        recipe=geometry(design)
        revision=hashlib.sha256(json.dumps(recipe,sort_keys=True).encode()).hexdigest()[:12]
        path=assets/(name+'-'+revision+'.blend')
        a.save_asset(dict(kind='props',path=str(path),geometry=recipe))
        try:
            reuse(path,design)
            checks[name]=dict(reuse=True,cue_frames=cues(path,design),views=environment(path,design,assets,out,opt.render))
        except Exception as exc:
            checks[name]={'error':repr(exc)}
        report = out/(f'checks-{opt.only}.json' if opt.only else 'checks.json')
        report.write_text(json.dumps(checks,indent=2))
        print('CHECK',name,checks[name].get('error','passed'),flush=True)
    failed=[name for name,r in checks.items() if 'error' in r]
    if failed:raise RuntimeError(', '.join(failed))


if __name__=='__main__':
    main()

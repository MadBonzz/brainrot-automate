"""Blender entry point. All dimensions are in scene units with Z up and faces toward -Y."""
import json
import math
import sys
import subprocess
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import copy_file, restore_shot

palette = dict(navy='26364F', teal='347D80', mint='A6E7CD', gold='EDB667', rust='C56742',
               red='C64D52', cream='F6E4C4', charcoal='263039', lavender='BBABDB', blue='669CBF',
               brown='80533F', skin='DDA780', skin2='A7755B', ink='26212C', steel='849AA5',
               haze='657C98', mahogany='4A3641', floor='586D78', sky='829ABD', ivory='FFF4D9')
mesh_cache = {}
serial = 0

def rgb(color):
    s = palette.get(color, color)
    def lin(v):
        p = int(v, 16)/255
        return p/12.92 if p <= .04045 else ((p+.055)/1.055)**2.4
    return (*[lin(s[i:i+2]) for i in (0, 2, 4)], 1)

def empty(name, pos, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.parent=parent
    o.location=pos
    return o

def mesh(shape):
    if shape in mesh_cache:
        return mesh_cache[shape]
    if shape == 'box':
        verts = [(x/2, y/2, z/2) for z in (-1, 1) for y in (-1, 1) for x in (-1, 1)]
        faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        m = bpy.data.meshes.new('Block')
        m.from_pydata(verts, [], faces)
        m.update()
    elif shape in ('horn','tapered_case'):
        # Revolve a hollow flared bell; four matching corners form the metronome case.
        profile = ([(.08,-.5),(.11,-.22),(.19,.06),(.32,.32),(.5,.47),(.49,.50),
                    (.46,.47),(.29,.32),(.16,.06),(.08,-.22),(.05,-.5)]
                   if shape=='horn' else [(.707,-.5),(.175,.5)])
        sides = 32 if shape=='horn' else 4
        phase = 0 if shape=='horn' else math.pi/4
        verts = [(rad*math.cos(i*math.tau/sides+phase),rad*math.sin(i*math.tau/sides+phase),z)
                 for rad,z in profile for i in range(sides)]
        faces = [(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i)
                 for j in range(len(profile)-1) for i in range(sides)]
        if shape=='tapered_case':
            faces.extend([tuple(reversed(range(4))),tuple(range(4,8))])
        m = bpy.data.meshes.new(shape)
        m.from_pydata(verts,[],faces)
        m.update()
    elif shape == 'sail':
        verts = [(x,y,z) for y in (-.5,.5) for x,z in [(-.5,-.5),(.5,-.5),(.5,.5)]]
        m = bpy.data.meshes.new('Triangular sail')
        m.from_pydata(verts,[],[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)])
        m.update()
    else:
        if shape == 'ring':
            bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8, major_radius=.46, minor_radius=.04)
            for vertex in bpy.context.object.data.vertices:
                vertex.co.z /= .08
        elif shape == 'sphere':
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=.5)
        elif shape == 'cone':
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.5, depth=1)
        else:
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=.5, depth=1)
        temp = bpy.context.object
        m = temp.data
        bpy.data.objects.remove(temp, do_unlink=True)
    mesh_cache[shape]=m
    return m

def part(pos, size, color, parent=None, shape='box', angle=None):
    global serial
    serial += 1
    o = bpy.data.objects.new('part'+str(serial), mesh(shape) if isinstance(shape,str) else shape)
    bpy.context.collection.objects.link(o)
    o.parent=parent
    o.location=pos
    o.scale=size
    if color == 'prop_paint':
        o['clue_paint'] = True
        color = 'teal'
    o.color=rgb(color)
    if angle:
        o.rotation_euler=angle
    return o

def label(words, pos, size, color='ivory', parent=None):
    f = bpy.data.curves.new('Lettering', 'FONT')
    f.body=words
    f.size=size
    f.align_x='CENTER'
    f.align_y='CENTER'
    o = bpy.data.objects.new('Sign', f)
    bpy.context.collection.objects.link(o)
    o.parent=parent
    o.location=pos
    o.rotation_euler.x=math.pi/2
    o.color=rgb(color)
    return o

def make_set(kind):
    indoor = kind != 'rooftop'
    part((0, 1, -.15), (24, 16, .3), 'floor')
    # A skyline and windows give the camera a sense of depth across all four sets.
    for i in range(15):
        x = (i-7)*1.54
        height = 2+((i*11)%7)*.48
        part((x, 9, height/2), (1.40, 1.5, height), 'haze' if i%3 else 'navy')
        for level in range(int(height)):
            part((x, 8.24, level+.55), (.85, .02, .12), 'steel' if i%2 else 'gold')
    if indoor:
        part((0, 4, 2.0), (15, .3, 4), 'teal' if kind == 'station' else 'navy')
        part((0, 3.78, .26), (15, .12, .45), 'charcoal')
        for x in [-6, -3, 0, 3, 6]:
            part((x, 3.7, 1.9), (.16, .25, 3.8), 'steel')
        for x in [-4.5, -1.5, 1.5, 4.5]:
            part((x, 3.75, 2.8), (2.65, .12, 1.28), 'charcoal')
            part((x, 3.66, 2.8), (2.47, .05, 1.08), 'haze')
            part((x, 3.57, 2.8), (.08, .08, 1.2), 'navy')
        for x in [-4, 0, 4]:
            part((x, 3.48, 3.8), (2.6, .18, .08), 'ivory')
    if kind == 'archive':
        for x in [-4.6, -2.9, 3.8]:
            for h in [.5, 1.3, 2.1]:
                part((x, 2.7, h), (1.62, .45, .08), 'brown')
                for k in range(6):
                    part((x-.57+k*.22, 2.7, h+.32), (.17, .28, .54+k%2*.12), ['rust', 'mint', 'cream', 'teal'][k%4])
    if kind == 'station':
        for x in [-4.1, 3.7]:
            for y, z in [(2.45, .63), (2.72, 1.0), (2.72, 1.19)]:
                part((x, y, z), (2.5, .39 if z<.7 else .14, .14), 'brown')
            for dx in [-.8, .8]:
                part((x+dx, 2.45, .3), (.14, .23, .6), 'charcoal')
        part((0, -1.8, .008), (22, .12, .016), 'gold')
    if kind == 'hallway':
        for x in [-3.4, 3.4]:
            part((x, 3.42, 1.28), (1.46, .18, 2.56), 'brown')
            part((x+.5, 3.29, 1.15), (.12, .12, .12), 'gold', shape='sphere')
    if not indoor:
        part((0, 3.4, .43), (16, .24, .86), 'navy')
        part((0, 3.4, .91), (16, .34, .12), 'steel')
        for x in [-3.7, 3.1]:
            part((x, 2.2, .48), (1.2, .85, .96), 'teal')
            for z in [.25, .4, .55, .7]:
                part((x, 1.76, z), (.86, .06, .045), 'charcoal')
    for x in range(-6, 7, 2):
        part((x, -.2, .003), (.018, 7, .006), 'steel')

def set_sign(title):
    if title:
        part((0, 3.28, 3.12), (3.7, .1, .52), 'charcoal')
        label(title[:20].upper(), (0, 3.2, 3.12), .215, 'gold')

def tagged(obj, joint):
    obj['shortfilm_joint'] = joint
    obj.name = joint
    return obj

def move_under(obj, pivot):
    # Both the new pivot and obj started in the same parent's coordinates.
    inverse = obj.matrix_parent_inverse.copy()
    obj.parent = pivot
    if inverse == Matrix.Identity(4):
        obj.location -= pivot.location
    else:
        obj.matrix_parent_inverse = Matrix.Translation(-pivot.location) @ inverse


def articulate(base):
    """Upgrade an original rigid cast instance in memory, including its attached accessories."""
    joints = {obj.get('shortfilm_joint'):obj for obj in base.children_recursive}
    if 'spine' in joints:
        return
    upper = [obj for obj in base.children if obj not in (joints['leg-1'], joints['leg1'])
             and obj.location.z > .85]
    spine = tagged(empty('Spine', (0, 0, .91), base), 'spine')
    for obj in upper:
        move_under(obj, spine)
    for side in (-1, 1):
        for limb, hinge, cut, length in [('arm','elbow',-.33,.56), ('leg','knee',-.41,.74)]:
            parent = joints[f'{limb}{side}']
            children = list(parent.children)
            joint = tagged(empty(hinge, (0, 0, cut), parent), f'{hinge}{side}')
            for obj in children:
                # Split only the stock rectangular sleeve/trouser. Other attachments keep their geometry.
                is_block = (obj.type == 'MESH' and len(obj.data.vertices) == 8
                            and all(abs(abs(v)-.5)<.0001 for vert in obj.data.vertices for v in vert.co)
                            and abs(obj.rotation_euler.to_matrix().to_quaternion().angle)<.0001
                            and abs(obj.scale.z-length) < .0001
                            and abs(obj.location.z-(-.27 if limb=='arm' else -.37)) < .0001)
                if is_block:
                    bottom, top = obj.location.z-length/2, obj.location.z+length/2
                    lower = obj.copy()
                    for collection in list(obj.users_collection):
                        collection.objects.link(lower)
                    lower.parent = joint
                    lower.location.z = (bottom-cut)/2
                    lower.scale.z = cut-bottom
                    obj.location.z = (top+cut)/2
                    obj.scale.z = top-cut
                elif obj.location.z < cut:
                    if limb == 'arm' and obj.type == 'MESH' and abs(obj.location.z+.61)<.001:
                        obj['shortfilm_hand'] = side
                    if limb == 'leg' and obj.type == 'MESH' and abs(obj.location.z+.80)<.001:
                        obj['shortfilm_sole'] = side
                    move_under(obj, joint)

def add_wrists(base):
    """Give both stock and previously saved articulated hands a twist pivot at the cuff."""
    descendants = list(base.children_recursive)
    joints = {o['shortfilm_joint']:o for o in descendants if 'shortfilm_joint' in o}
    for hand in descendants:
        side = hand.get('shortfilm_hand')
        if side is None or f'wrist{side}' in joints:
            continue
        forearm = hand.parent
        cuff = hand.location.copy()
        cuff.z += hand.scale.z/2
        wrist = tagged(empty('Wrist',cuff,forearm), f'wrist{side}')
        move_under(hand,wrist)


def build_character(coat, second):
    base = tagged(empty('Root', (0, 0, 0)), 'root')
    skin = 'skin2' if second else 'skin'
    hair = 'mahogany' if second else 'brown'
    head = tagged(empty('Head', (0, 0, 1.84), base), 'head')
    part((0, 0, .20), (.79, .68, .7), skin, head)
    part((0, .015, .57), (.86, .73, .16), hair, head)
    for dx, h in [(-.29, .24), (-.09, .16), (.12, .10), (.31, .17)]:
        part((dx, -.332, .50-h/2), (.22, .09, h), hair, head)
    for side in [-1, 1]:
        part((side*.40, 0, .31), (.09, .59, .34), hair, head)
        tagged(part((side*.165, -.351, .244), (.1, .027, .085), 'ink', head), f'eye{side}')
        part((side*.155-.012, -.37, .26), (.026, .012, .026), 'ivory', head)
        brow = part((side*.165, -.35, .35), (.17, .037, .035), hair, head)
        tagged(brow, f'brow{side}')
        brow.rotation_euler.y = side*-.10
    tagged(part((0, -.35, .06), (.15, .036, .028), 'ink', head), 'mouth')
    part((0, 0, 1.29), (.78, .55, .87), coat, base)
    part((0, -.285, 1.33), (.037, .018, .71), 'gold', base)
    for side in [-1, 1]:
        part((side*.20, -.288, 1.13), (.20, .022, .055), 'navy', base)
    part((0, 0, 1.73), (.67, .56, .12), 'cream', base)
    for side in [-1, 1]:
        arm = tagged(empty('Shoulder', (side*.53, 0, 1.64), base), f'arm{side}')
        part((0, 0, -.27), (.29, .48, .56), coat, arm)
        part((0, 0, -.61), (.28, .46, .16), skin, arm)
        leg = tagged(empty('Hip', (side*.212, 0, .91), base), f'leg{side}')
        part((0, 0, -.37), (.39, .51, .74), 'navy', leg)
        part((0, -.055, -.80), (.42, .64, .20), 'charcoal', leg)
        part((0, -.35, -.83), (.40, .05, .07), 'cream', leg)
    articulate(base)
    add_wrists(base)
    return base

def save_collection(name):
    objects = list(bpy.context.scene.objects)
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    for obj in objects:
        for original in list(obj.users_collection):
            original.objects.unlink(obj)
        collection.objects.link(obj)

def load_collection(path, name):
    with bpy.data.libraries.load(path, link=False) as (available, loaded):
        if name not in available.collections:
            raise ValueError(f'{path} is missing its {name} collection.')
        loaded.collections = [name]
    collection = loaded.collections[0]
    bpy.context.scene.collection.children.link(collection)
    return collection

def actor(path, x, y, face):
    collection = load_collection(path, 'Character')
    base = next(obj for obj in collection.all_objects if obj.get('shortfilm_joint') == 'root')
    articulate(base)
    add_wrists(base)
    joints = {obj['shortfilm_joint']:obj for obj in [base, *base.children_recursive] if 'shortfilm_joint' in obj}
    base.location.x += x
    base.location.y += y
    for side in (-1, 1):
        if face == 'startled':
            joints[f'eye{side}'].scale.z *= .12/.085
        elif face == 'worried':
            joints[f'brow{side}'].rotation_euler.y += side*.40
    if face == 'startled':
        joints['mouth'].scale.x *= .5
        joints['mouth'].scale.z *= .10/.028
    return joints

def key(o, attribute, frame):
    o.keyframe_insert(data_path=attribute, frame=frame)
def build_motion(name, recipe):
    base = build_character('teal', False)
    joints = {o['shortfilm_joint']:o for o in [base, *base.children_recursive] if 'shortfilm_joint' in o}
    for joint, channels in recipe['channels'].items():
        obj = joints[joint]
        for channel, points in channels.items():
            prop, axis = channel.rsplit('.', 1)
            index = 'xyz'.index(axis)
            values = getattr(obj, prop)
            for frame, value in points:
                values[index] = value
                obj.keyframe_insert(data_path=prop, index=index, frame=frame)
        action = obj.animation_data.action
        action.name = name+' '+joint
        action['shortfilm_joint'] = joint
    bpy.context.scene.frame_end = recipe['frames']
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_set(0)

def load_actions(path):
    with bpy.data.libraries.load(path, link=False) as (available, loaded):
        loaded.actions = list(available.actions)
    return {a['shortfilm_joint']:a for a in loaded.actions if 'shortfilm_joint' in a}

def clear_swing_sole(knee, corners, height):
    """Find the smallest additional knee bend that clears the support plane."""
    local = [knee.matrix_world.inverted() @ p for p in corners]
    def lowest(angle):
        matrix = knee.matrix_world @ Matrix.Rotation(angle,4,'X')
        return min((matrix @ p).z for p in local)
    lo = 0.
    limit = max(0.,math.radians(148)-knee.delta_rotation_euler.x)
    for step in range(1,25):
        hi = limit*step/24
        if lowest(hi) >= height:
            for _ in range(10):
                mid = (lo+hi)/2
                if lowest(mid) < height:
                    lo = mid
                else:
                    hi = mid
            return hi
        lo = hi
    return 0.


def place_feet(rig, recipe, cue, end, scale):
    """Solve floor height and stance-foot drift from the evaluated shoe geometry."""
    base = rig['root']
    boots = {int(o['shortfilm_sole']):o for o in base.children_recursive if 'shortfilm_sole' in o}
    if len(boots) != 2:
        raise ValueError('Foot placement requires both shoes tagged with shortfilm_sole (-1 and 1).')
    spans = [tuple(map(int,p.split(':'))) for p in recipe.get('plant',[])]
    clearance = {}
    if spans:
        for side in boots:
            knee = rig[f'knee{side}']
            children = list(knee.children)
            pivot = empty('Swing shoe clearance',(0,0,0),knee)
            for child in children:
                move_under(child,pivot)
            clearance[side] = pivot
    scene = bpy.context.scene
    old_frame, old_sub = scene.frame_current, scene.frame_subframe
    root_offset = empty('Foot placement', (0,0,0))
    base.parent = root_offset
    samples = []
    previous = anchor = None
    shift = Vector((0.,0.))
    # Sample without the correction parent animated, so previous keys cannot feed back.
    last = end if recipe.get('loop') else min(end,math.ceil(cue+recipe['frames']*scale))
    for frame in range(cue,last+1):
        scene.frame_set(frame)
        points = {side:[boot.matrix_world @ Vector(c) for c in boot.bound_box] for side,boot in boots.items()}
        floor = min(v.z for corners in points.values() for v in corners)
        if frame == cue:
            rest = floor
        t = (frame-cue)/scale
        cycle = int(t//recipe['frames']) if recipe.get('loop') else 0
        t = t%recipe['frames'] if recipe.get('loop') else min(t,recipe['frames'])
        stance = next(((side,a,b,cycle) for side,a,b in spans if a<=t<=b),None)
        bends = {side:0. for side in clearance}
        if stance:
            supporting = stance[0]
            desired = min(v.z for v in points[supporting])
            if desired-floor > .0001:
                swing = -supporting
                bend = clear_swing_sole(rig[f'knee{swing}'],points[swing],desired)
                if bend:
                    bends[swing] = bend
                    floor = desired
            corners = points[stance[0]]
            center = (sum(corners,Vector())/len(corners)).xy
            if previous != stance:
                anchor = center+shift
            shift = anchor-center
        previous = stance
        lift = rest-floor if recipe.get('ground') else max(0,rest-floor)
        samples.append((frame,(shift.x,shift.y,lift),bends))
    for frame,xyz,bends in samples:
        for side,bend in bends.items():
            clearance[side].rotation_euler.x = bend
            key(clearance[side],'rotation_euler',frame)
        root_offset.location = xyz
        key(root_offset,'location',frame)
    scene.frame_set(old_frame,subframe=old_sub)

def motion(rig, name, cue, end, library):
    recipe = job['motions'][name]
    if name not in library:
        library[name] = load_actions(job['models']['motions/'+name]['path'])
    cue = max(1, min(cue, end-1))
    duration = recipe['frames']
    scale = FPS/24
    loop = recipe.get('loop', False)
    if not loop:
        scale = min(scale, (end-cue)/duration)
    for joint, action in library[name].items():
        track = rig[joint].animation_data_create().nla_tracks.new()
        strip = track.strips.new(name, cue, action)
        if hasattr(strip, 'action_slot') and len(action.slots):
            strip.action_slot = action.slots[0]
        strip.action_frame_start = 0
        strip.action_frame_end = duration
        strip.scale = scale
        if loop:
            strip.repeat = max(0.1, (end-cue)/(duration*scale))
        strip.extrapolation = 'HOLD_FORWARD'
    if 'travel' in recipe:
        base = rig['root']
        key(base, 'location', cue)
        base.location += Vector(recipe['travel'])
        key(base, 'location', end)
    if recipe.get('ground') or recipe.get('floor'):
        place_feet(rig, recipe, cue, end, scale)

def build_prop(p):
    root = empty('Clue', (1.00, .1, .99))
    color = 'prop_paint'
    kind = p['kind']
    part((1, .12, .50), (1.40, .83, .99), 'navy')
    part((1, .12, .98), (1.49, .94, .10), 'gold')
    if kind == 'clock':
        for y, d, c in [(0, 1.04, color), (-.09, .91, 'ivory')]:
            part((0, y, .62), (d, d, .14), c, root, 'cylinder', (math.pi/2, 0, 0))
        for i in range(12):
            a = i*math.tau/12
            part((math.sin(a)*.37, -.177, .62+math.cos(a)*.37), (.034, .03, .076), 'charcoal', root, angle=(0, a, 0))
        hand = empty('Clock hands', (0, -.202, .62), root)
        part((0, 0, .16), (.039, .025, .32), 'ink', hand)
        part((-.11, -.216, .62), (.24, .03, .05), 'rust', root)
        part((0, -.238, .62), (.08, .035, .08), 'gold', root, 'sphere')
    elif kind == 'radio':
        part((0, 0, .38), (1.17, .58, .65), color, root)
        for n in range(6):
            part((-.22, -.30, .21+n*.058), (.53, .03, .023), 'charcoal', root)
        part((.33, -.31, .41), (.23, .12, .23), 'gold', root, 'sphere')
        part((.4, .04, 1.0), (.034, .034, .71), 'steel', root, angle=(0, .2, 0))
        hand = root
    elif kind == 'lantern':
        part((0, 0, .17), (.69, .52, .22), 'charcoal', root)
        part((0, 0, .58), (.51, .40, .62), color, root)
        for x in [-.30, .30]:
            part((x, 0, .59), (.07, .47, .72), 'charcoal', root)
        part((0, 0, 1.02), (.72, .60, .16), 'charcoal', root)
        hand = root
    elif kind == 'signal':
        part((0, 0, .48), (1.30, .24, .9), 'charcoal', root)
        part((0, -.14, .52), (1.16, .05, .70), color, root)
        hand = root
    elif 'pieces' in p:
        pivot = p['pivot']
        hand = empty('Working mechanism',pivot['point'],root) if pivot else root
        if pivot:
            hand['clue_axis'] = pivot['axis']
        for piece in p['pieces']:
            moving = piece['moving']
            pos = Vector(piece['pos'])
            if moving:
                pos -= Vector(pivot['point'])
            shape = piece['shape']
            if shape == 'surface':
                shape = bpy.data.meshes.new('Surface detail')
                shape.from_pydata(piece['vertices'],[],piece['faces'])
                shape.update()
            part(pos,piece['size'],piece['color'],hand if moving else root,shape,
                 tuple(map(math.radians,piece['rotation'])))
    else:
        for piece in p['parts']:
            pos = [max(-1.5, min(1.5, piece[k])) for k in ('x', 'y', 'z')]
            size = [max(.02, min(2.0, piece[k])) for k in ('width', 'depth', 'height')]
            part(pos, size, piece['color'], root, piece['shape'])
        hand = root
    root['clue_root'] = True
    hand['clue_turn'] = True

def seat_prop(objects, root, hand):
    """Place the asset on its actual plinth, including models cached by older versions."""
    meshes = [o for o in root.children_recursive if o.type == 'MESH']
    furniture = [o for o in objects if not o.parent and o.type == 'MESH']
    top = max(furniture, key=lambda o:max((o.matrix_world @ Vector(v)).z for v in o.bound_box))
    board = [top.matrix_world @ Vector(v) for v in top.bound_box]
    center = sum(board,Vector())/8
    half_x = max(p.x-center.x for p in board)
    half_y = max(p.y-center.y for p in board)
    inv = root.matrix_world.inverted()
    clouds = {}
    for obj in meshes:
        mat = inv @ obj.matrix_world
        clouds[obj] = [mat @ v.co for v in obj.data.vertices]
    points = [p for cloud in clouds.values() for p in cloud]
    bottom = min(p.z for p in points)
    # Center the contact patch. A radio antenna or long spout can be off-center.
    feet = [p for p in points if p.z <= bottom+.018]
    origin = Vector([(min(p[i] for p in feet)+max(p[i] for p in feet))/2 for i in (0,1)]+[bottom])
    radius = max((p-origin).xy.length for p in feet)
    if hand == root:
        fit = min(half_x,half_y)/max(.001,radius)
    else:
        fit = min(half_x/max(.001,max(abs(p.x-origin.x) for p in feet)),
                  half_y/max(.001,max(abs(p.y-origin.y) for p in feet)))
    # Keep the contact patch on the tabletop even at the peak of a pulse.
    fit = min(1.,fit/1.15*.97)
    # Bound a custom clue with a tiny foot and an oversized upper body as well.
    reach = max((p-origin).xy.length for p in points)
    fit = min(fit,.84/max(reach,.001),1.40/max(.001,max(p.z for p in points)-bottom))
    # A view of this asset must use the same framing at any angle, including hidden cuts.
    # Bound the swept circle around the working axle, and include the largest pulse.
    moving = set(hand.children_recursive)
    axis = 'xyz'.index(hand.get('clue_axis','y' if hand!=root else 'z'))
    pivot = origin if hand==root else inv @ hand.matrix_world.translation
    radial = [i for i in range(3) if i!=axis]
    lows, highs = [0.]*3, [0.]*3
    for obj,cloud in clouds.items():
        for v in cloud:
            lo = list(v-origin)
            hi = list(v-origin)
            if obj in moving:
                r = math.hypot(v[radial[0]]-pivot[radial[0]],v[radial[1]]-pivot[radial[1]])
                for i in radial:
                    lo[i],hi[i] = pivot[i]-origin[i]-r,pivot[i]-origin[i]+r
            for i in range(3):
                lows[i]=min(lows[i],lo[i]*fit*1.15)
                highs[i]=max(highs[i],hi[i]*fit*1.15)
    root['clue_bounds'] = lows+highs
    for child in root.children:
        child.location -= origin
    root.location = (center.x,center.y,max(p.z for p in board))
    root.scale = (fit,)*3
    return fit, center, half_y


def stage_prop(path, p, act, cue, end, angle, delta, visible=None):
    objects = load_collection(path, 'Prop').all_objects
    root = next(o for o in objects if o.get('clue_root'))
    hand = next(o for o in objects if o.get('clue_turn'))
    bpy.context.view_layer.update()
    fit, center, half_y = seat_prop(objects,root,hand)
    for obj in objects:
        if obj.get('clue_paint'):
            obj.color = rgb(p['color'])
    # The plaque is mounted on the front of the pedestal, outside the moving assembly.
    if p['label']:
        y = center.y-half_y
        z = root.location.z-.16
        part((center.x,y+.008,z),(1.27,.052,.19),'charcoal')
        lettering = label(p['label'][:12].upper(),(center.x,y-.022,z),.110,'ivory')
        bpy.context.view_layer.update()
        corners = [lettering.matrix_world @ Vector(c)-root.location for c in lettering.bound_box]
        root['plaque_bounds'] = [fn(v[i] for v in corners) for fn in (min,max) for i in range(3)]
    cue = max(1,min(cue,end-1))
    finish = min(end,cue+max(2,round(FPS*.33)))
    axis = 'xyz'.index(hand.get('clue_axis','y' if p['kind']=='clock' else 'z'))
    hand.rotation_euler[axis] = math.radians(angle)
    if act == 'turn':
        key(hand,'rotation_euler',cue)
        hand.rotation_euler[axis] = math.radians(angle+delta)
        key(hand,'rotation_euler',finish)
    if visible is None:
        visible = act != 'appear'  # Timelines written before per-shot visibility.
    initial = fit if visible else 0.
    root.scale = (initial,)*3
    if act in ('appear','vanish','pulse'):
        key(root,'scale',cue)
        target = {'appear':fit,'vanish':0.,'pulse':initial*1.15}[act]
        root.scale = (target,)*3
        key(root,'scale',finish)
        if act == 'pulse':
            root.scale = (initial,)*3
            key(root,'scale',min(end,finish+max(2,FPS//4)))
    return root


def fit_clue_camera(preset, root):
    """Frame the full swept bounds so zoom is independent of the cue, seek order, or cut."""
    scene = bpy.context.scene
    bounds = root['clue_bounds']
    target = Vector(preset['target'])
    target.z = root.location.z + (bounds[2]+bounds[5])*.5 - .045
    rotation = (target-Vector(preset['position'])).to_track_quat('-Z','Y')
    right, up = rotation @ Vector((1,0,0)), rotation @ Vector((0,1,0))
    aspect = scene.render.resolution_x/scene.render.resolution_y
    span = preset['span']
    boxes = [bounds]
    if 'plaque_bounds' in root:
        boxes.append(root['plaque_bounds'])
    for box in boxes:
        for x in (box[0],box[3]):
            for y in (box[1],box[4]):
                for z in (box[2],box[5]):
                    p = root.location + Vector((x,y,z))-target
                    span = max(span,2.18*abs(p.dot(right))/(min(1,aspect)*preset['end_zoom']),
                               2.18*abs(p.dot(up))*max(1,aspect)/preset['end_zoom'])
    return dict(preset,span=span,target=list(target))


def camera(preset, end):
    pos, aim, span = preset['position'], preset['target'], preset['span']
    data = bpy.data.cameras.new('Portrait camera')
    cam = bpy.data.objects.new('Camera', data)
    bpy.context.collection.objects.link(cam)
    cam.location=pos
    cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z', 'Y').to_euler()
    data.type='ORTHO'
    data.ortho_scale=span
    key(data, 'ortho_scale', 1)
    data.ortho_scale=span*preset['end_zoom']
    key(data, 'ortho_scale', end)
    bpy.context.scene.camera=cam

def setup():
    s = bpy.context.scene
    s.render.engine='BLENDER_WORKBENCH'
    s.render.resolution_x=job['width']
    s.render.resolution_y=job['height']
    s.render.resolution_percentage=100
    s.render.fps=FPS
    s.render.image_settings.file_format='PNG'
    d = s.display.shading
    d.light='STUDIO'
    d.color_type='OBJECT'
    d.show_shadows=False
    d.show_cavity=True
    d.cavity_type='WORLD'
    d.cavity_ridge_factor=1
    d.cavity_valley_factor=1.10
    d.background_type='VIEWPORT'
    d.background_color=rgb('sky')[:3]
    s.display.render_aa='FXAA'
    s.view_settings.view_transform='Standard'
    s.view_settings.exposure=.65

def save_asset(entry):
    path = Path(entry['path'])
    if path.is_file():
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mesh_cache.clear()
    kind = entry['kind']
    if kind == 'character':
        base = build_character(entry['coat'], entry['role']=='witness')
        base.name = path.stem
        if 'look' in entry:
            from world_art import costume
            costume(base,entry['look'])
        save_collection('Character')
    elif kind == 'motions':
        build_motion(entry['name'], entry['recipe'])
    elif kind == 'sets':
        make_set(entry['name'])
        save_collection('Set')
    elif kind == 'props':
        build_prop(entry['geometry'])
        save_collection('Prop')
    else:
        raise ValueError(f'Unknown asset kind {kind}')
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.shading.color_type = 'OBJECT'
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=path.parent) as tmp:
        draft = Path(tmp)/path.name
        bpy.ops.wm.save_as_mainfile(filepath=str(draft), compress=True)
        draft.replace(path)

if __name__ == '__main__':
    sys.modules['animate'] = sys.modules[__name__]
    args = sys.argv[sys.argv.index('--')+1:]
    job = json.loads(Path(args[-1]).read_text(encoding='utf8'))
    if args[0] == '--build-assets':
        for entry in job:
            save_asset(entry)
        sys.exit(0)
    FPS = job['fps']
    design = job['design']
    for spec in job['shots']:
        target = Path(spec['folder'])
        clip = target/'clip.mp4'
        shared = Path(spec['shared_clip'])
        if restore_shot(spec):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mesh_cache.clear()
        setup()
        s = bpy.context.scene
        shot = spec['shot']
        end = spec['frames']
        cue = spec['cue']
        load_collection(job['models']['sets/'+shot['set']]['path'], 'Set')
        set_sign(design['location_sign'])
        actions = {}
        lead = actor(job['cast']['lead']['path'], -1.02, .12, shot['face'])
        camera_preset = job['cameras'][shot['camera']]
        lead['root'].rotation_euler.z += camera_preset.get('lead_yaw', 0)
        motion(lead, shot['lead'], cue, end, actions)
        if shot['witness'] != 'absent':
            motion(actor(job['cast']['witness']['path'], .08, 1.34, 'calm'), shot['witness'], cue, end, actions)
        clue = stage_prop(job['models']['props/clue']['path'], design['prop'], shot['prop'], cue, end,
                         spec['angle'], shot['turn_degrees'], spec.get('visible'))
        if shot['camera']=='clue':
            camera_preset = fit_clue_camera(camera_preset,clue)
        camera(camera_preset, end)
        s.frame_start=1
        s.frame_end=end
        s.frame_set(1)
        target.mkdir(parents=True, exist_ok=True)
        s.render.filepath=str(target/'frame-')
        bpy.ops.render.render(animation=True)
        if not (target/f'frame-{end:04d}.png').exists():
            raise RuntimeError('Incomplete shot '+str(target))
        temp = target/'clip.partial.mp4'
        subprocess.run([job['ffmpeg'], '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(FPS),
                        '-start_number', '1', '-i', str(target/'frame-%04d.png'), '-frames:v', str(end),
                        '-an', '-c:v', 'libx264', '-threads', '3', '-crf', '16', '-pix_fmt', 'yuv420p', str(temp)], check=True)
        temp.replace(clip)
        copy_file(clip, shared)
        (target/'complete').write_text(str(end))
        for frame in range(1, end+1):
            (target/f'frame-{frame:04d}.png').unlink()

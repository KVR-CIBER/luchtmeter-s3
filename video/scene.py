"""Blender scene of the Luchtmeter S3 film. Run on lvdell:  blender -b -P scene.py -- [still FRAME | labels | anim]
Device coordinates = case CAD coordinates in mm (X right, Y up, Z towards the viewer, front face Z = 0);
the root empty turns them upright in Blender (front looks at -Y) and scales mm -> m."""
import bpy, os, sys, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline as T

HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, 'assets')
CASE = os.path.join(HERE, 'case', 'out') if os.path.isdir(os.path.join(HERE, 'case')) else os.path.join(HERE, '..', 'case', 'out')
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['anim']
PARTS = json.load(open(os.path.join(A, 'parts.json')))
Z_PCB_F, PCB_T = -14.5, 1.6
Z_PCB_B = Z_PCB_F - PCB_T

# ---------------------------------------------------------------- scene, render settings
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, T.N, T.FPS
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'OPTIX'
sc.cycles.device = 'GPU'
sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'
sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 4; sc.cycles.transmission_bounces = 6
sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.use_persistent_data = True


def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = strength
    return m


def link(ob, parent):
    bpy.context.collection.objects.link(ob) if ob.name not in bpy.context.collection.objects else None
    ob.parent = parent
    return ob


def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(e)
    e.parent = parent; e.location = loc
    return e


def box(name, size, loc, m, parent, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object; o.name = name; o.scale = size; o.location = loc; o.parent = parent
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new('bv', 'BEVEL'); bv.width = bevel; bv.segments = 3; bv.affect = 'EDGES'
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def stl(path, name, m, parent):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]; o.name = name; o.parent = parent
    o.data.materials.clear(); o.data.materials.append(m)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
    return o


# ---------------------------------------------------------------- device
ROOT = empty('ROOT', loc=(0, 0, 0.11)); ROOT.rotation_euler = (math.radians(90), 0, 0); ROOT.scale = (0.001,) * 3
WHITE = mat('wit', (0.82, 0.82, 0.80), rough=0.42, coat=0.15)
BACKM = mat('wit_achter', (0.80, 0.80, 0.78), rough=0.5)
DARK = mat('scherm_metaal', (0.05, 0.05, 0.055), rough=0.35, metal=0.6)
SHIELD = mat('shield', (0.75, 0.76, 0.78), rough=0.22, metal=1.0)
BLACK = mat('ic', (0.02, 0.02, 0.022), rough=0.35)
SUB = mat('module_pcb', (0.03, 0.07, 0.05), rough=0.4)
GREYM = mat('scd_body', (0.18, 0.19, 0.2), rough=0.4)
POUCH = mat('lipo', (0.72, 0.73, 0.75), rough=0.28, metal=1.0)
GOLD = mat('goud', (1.0, 0.77, 0.34), rough=0.2, metal=1.0)

G_SHELL = empty('g_shell', ROOT); G_SCREEN = empty('g_screen', ROOT); G_PCB = empty('g_pcb', ROOT)
G_BAT = empty('g_bat', ROOT); G_BACK = empty('g_back', ROOT)
stl(os.path.join(CASE, 'luchtmeter_voorkant.stl'), 'voorkant', WHITE, G_SHELL)
stl(os.path.join(CASE, 'luchtmeter_achterplaat.stl'), 'achterplaat', BACKM, G_BACK)
scr = stl(os.path.join(A, 'screen1.stl'), 'scherm_module', DARK, G_SCREEN); scr.location = (0, 10.0, -10.4)

# display: emissive image sequence behind a glossy coat (the screen's own cover glass)
img = bpy.data.images.load(os.path.join(HERE, 'ui', '0001.png')); img.source = 'SEQUENCE'
disp = mat('display', (0, 0, 0), rough=0.04, coat=1.0)
nt = disp.node_tree; bsdf = nt.nodes['Principled BSDF']
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
tex.image_user.frame_duration = T.N; tex.image_user.frame_start = 1; tex.image_user.use_auto_refresh = True
nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color']); bsdf.inputs['Emission Strength'].default_value = 2.2
bpy.ops.mesh.primitive_plane_add(size=1); dp = bpy.context.object; dp.name = 'display'
dp.scale = (95.0, 53.9, 1); dp.location = (0, 10.0, -1.40); dp.parent = G_SCREEN; dp.data.materials.append(disp)

box('glas', (105.6, 67.6, 0.3), (0, 10.0, -1.6), mat('glas', (0.006, 0.006, 0.008), rough=0.06, coat=1.0), G_SCREEN)

# board from KiCad (GLB, metres, already z-up with the front side at +z)
bpy.ops.import_scene.gltf(filepath=os.path.join(A, 'pcb.glb'))
PCBM = empty('pcb_glb', G_PCB, loc=(0, 0, Z_PCB_F - PCB_T)); PCBM.scale = (1000,) * 3
for o in bpy.context.selected_objects:
    if o.parent is None:
        o.parent = PCBM
for m in bpy.data.materials:                        # KiCad's see-through soldermask -> solid dark green, glossy
    bs = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    if bs and m.name.startswith('mat_'):
        c = bs.inputs['Base Color'].default_value
        if abs(c[0] - 0.08) < 0.01 and abs(c[1] - 0.2) < 0.01:
            bs.inputs['Base Color'].default_value = (0.012, 0.05, 0.03, 1); bs.inputs['Alpha'].default_value = 1.0
            bs.inputs['Roughness'].default_value = 0.32; bs.inputs['Coat Weight'].default_value = 0.4
            m.blend_method = 'OPAQUE' if hasattr(m, 'blend_method') else None

# stand-ins for the parts KiCad has no 3D model for (back side unless noted)
def at(ref, h, back=True):
    p = PARTS[ref]
    return (p['x'], -p['y'], (Z_PCB_B - h / 2) if back else (Z_PCB_F + h / 2))

x, y, z = at('U1', 3.2)
box('ESP32-S3 module', (18.0, 19.2, 0.8), (x, y, Z_PCB_B - 0.4), SUB, G_PCB)
box('ESP32-S3 shield', (15.8, 13.0, 2.4), (x, y + 2.6, Z_PCB_B - 0.8 - 1.2), SHIELD, G_PCB, bevel=0.3)
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=1.2, location=(x - 6.5, y - 6.5, Z_PCB_B - 1.4)); u = bpy.context.object
u.parent = G_PCB; u.data.materials.append(GOLD); u.name = 'U.FL'
x, y, z = at('U5', 6.5)
box('SCD41', (10.1, 10.1, 6.5), (x, y, z), GREYM, G_PCB, bevel=0.4)
bpy.ops.mesh.primitive_cylinder_add(radius=2.2, depth=0.4, location=(x, y, Z_PCB_B - 6.6)); c = bpy.context.object
c.parent = G_PCB; c.data.materials.append(SHIELD)
box('SHT45', (1.5, 1.5, 0.5), at('U6', 0.5), BLACK, G_PCB)
box('BQ24075', (3.0, 3.0, 0.9), at('U7', 0.9), BLACK, G_PCB)
box('LTR-303', (2.0, 2.0, 0.7), at('U4', 0.7, back=False), BLACK, G_PCB)
x, y, z = at('J2', 3.2)
box('USB-C', (7.35, 8.94, 3.2), (x, y, z), SHIELD, G_PCB, bevel=0.6)
box('LiPo 300 mAh', (30.0, 20.0, 4.5), (25.5, 26.5, Z_PCB_B - 0.6 - 2.25), POUCH, G_BAT, bevel=1.2)

# glow rings for the sensor close-up
GLOW = {}
for ref, r, h in (('U1', 13.5, 3.2), ('U5', 8.5, 6.5), ('U6', 3.0, 0.5), ('U10', 5.5, 1.6), ('U7', 4.0, 0.9), ('J2', 7.0, 3.2)):
    m = mat('glow_' + ref, (0, 0, 0), emit=(0.2, 0.75, 1.0), strength=0.0)
    p = at(ref, h)
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.25, location=(p[0], p[1], Z_PCB_B - h - 0.6))
    t = bpy.context.object; t.name = 'glow_' + ref; t.parent = G_PCB; t.data.materials.append(m)
    GLOW[ref] = m

# phone for the NFC tap
PHONE = empty('g_phone', ROOT)
PH = mat('telefoon', (0.015, 0.015, 0.018), rough=0.12, coat=1.0)
box('telefoon', (72.0, 150.0, 8.0), (0, 0, 0), PH, PHONE, bevel=6.0)
box('telefoon_scherm', (66.0, 142.0, 0.2), (0, 0, 4.05), mat('tel_scherm', (0, 0, 0), rough=0.05, coat=1.0,
    emit=(0.05, 0.12, 0.3), strength=0.6), PHONE)
PHONE.rotation_euler = (0, 0, math.radians(35))

# label anchors (device coordinates)
ANCH = {}
for name, ref, h in (('ESP32-S3', 'U1', 3.2), ('SCD41', 'U5', 6.5), ('SHT45', 'U6', 0.5), ('NFC-chip', 'U10', 1.6),
                     ('Laadchip', 'U7', 0.9), ('USB-C', 'J2', 3.2)):
    p = at(ref, h); ANCH[name] = empty('a_' + name, G_PCB, loc=(p[0], p[1], Z_PCB_B - h))
ANCH['LiPo'] = empty('a_LiPo', G_BAT, loc=(25.5, 26.5, Z_PCB_B - 5.4))
ANCH['Scherm'] = empty('a_Scherm', G_SCREEN, loc=(30.0, 30.0, 0.5))
ANCH['NFC'] = empty('a_NFC', G_SHELL, loc=(-9.5, -34.3, 0.2))
ANCH['Lichtsensor'] = empty('a_Licht', G_SHELL, loc=(31.5, -36.5, 0.2))

# ---------------------------------------------------------------- animation
def key(ob, f, loc=None, rot=None):
    if loc is not None:
        ob.location = loc; ob.keyframe_insert('location', frame=f)
    if rot is not None:
        ob.rotation_euler = rot; ob.keyframe_insert('rotation_euler', frame=f)


EXP = {G_SHELL: (0, 0, 40.0), G_SCREEN: (0, 0, 14.0), G_PCB: (0, 0, -22.0), G_BAT: (85.0, 0, -40.0), G_BACK: (0, 150.0, -80.0)}
for g, d in EXP.items():
    for f in (1, T.EXPLODE[0] + 20, T.CLOSE[1] - 20):
        key(g, f, loc=(0, 0, 0))
    key(g, T.EXPLODE[1] - 30, loc=d); key(g, T.SENSORS[1] + 10, loc=d)

for ref, m in GLOW.items():
    s = m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    i = list(GLOW).index(ref); f0 = T.SENSORS[0] + 8 + i * 14
    for f, v in ((T.SENSORS[0], 0), (f0, 0), (f0 + 8, 30), (f0 + 20, 10), (T.SENSORS[1] - 10, 10), (T.SENSORS[1] + 6, 0)):
        s.default_value = v; s.keyframe_insert('default_value', frame=f)

touch = (-9.5 + 62 * math.sin(math.radians(35)), -34.3 - 62 * math.cos(math.radians(35)), 8.0)   # top end on the NFC mark
far = (touch[0] + 160.0, touch[1] - 40.0, 120.0)
for f, p in ((1, far), (T.TAP[0], far), (T.TAP[0] + 32, touch), (T.TAP[0] + 52, touch), (T.TAP[1] - 8, far), (T.N, far)):
    key(PHONE, f, loc=p)

# camera on a target
TGT = empty('cam_target', loc=(0, 0, 0.11))
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 50; cam_d.sensor_width = 36
cam_d.dof.use_dof = True; cam_d.dof.focus_object = TGT; cam_d.dof.aperture_fstop = 8.0
CAM = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(CAM); sc.camera = CAM
tr = CAM.constraints.new('TRACK_TO'); tr.target = TGT; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
SHOTS = [  # frame, camera position, target (m)
    (1, (-0.20, -0.36, 0.17), (0, 0, 0.11)),
    (T.HERO[1], (0.21, -0.35, 0.14), (0, 0, 0.11)),
    (T.EXPLODE[0] + 70, (0.40, 0.06, 0.18), (0, 0.0, 0.12)),
    (T.EXPLODE[1], (-0.16, 0.42, 0.24), (0.01, 0.02, 0.13)),
    (T.SENSORS[0] + 60, (-0.02, 0.30, 0.15), (0.0, 0.03, 0.115)),
    (T.SENSORS[1], (0.10, 0.28, 0.13), (0.01, 0.03, 0.115)),
    (T.CLOSE[0] + 70, (0.30, -0.12, 0.14), (0, 0, 0.11)),
    (T.CLOSE[1], (0.0, -0.33, 0.12), (0, 0, 0.115)),
    (T.LIVE[1], (0.0, -0.25, 0.12), (0, 0, 0.115)),
    (T.SLEEP[1], (-0.07, -0.26, 0.11), (0, 0, 0.11)),
    (T.TAP[0] + 40, (0.24, -0.25, 0.19), (0.0, 0, 0.085)),
    (T.TAP[1], (0.06, -0.30, 0.10), (0, 0, 0.11)),
    (T.N, (0.0, -0.46, 0.13), (0, 0, 0.11)),
]
for f, p, t in SHOTS:
    key(CAM, f, loc=p); key(TGT, f, loc=t)

# ---------------------------------------------------------------- studio
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
hdr = os.path.join(A, 'studio.hdr')
if os.path.exists(hdr):
    env = w.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(hdr)
    w.node_tree.links.new(env.outputs['Color'], w.node_tree.nodes['Background'].inputs['Color'])
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
# the camera sees a dark studio, reflections still see the HDRI
wn = w.node_tree.nodes; lpth = wn.new('ShaderNodeLightPath'); dark = wn.new('ShaderNodeBackground')
dark.inputs['Color'].default_value = (0.004, 0.0045, 0.006, 1); mix = wn.new('ShaderNodeMixShader')
w.node_tree.links.new(lpth.outputs['Is Camera Ray'], mix.inputs[0])
w.node_tree.links.new(wn['Background'].outputs[0], mix.inputs[1]); w.node_tree.links.new(dark.outputs[0], mix.inputs[2])
w.node_tree.links.new(mix.outputs[0], wn['World Output'].inputs['Surface'])
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); floor = bpy.context.object
fm = mat('vloer', (0.02, 0.022, 0.026), rough=0.75); fm.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.2
floor.data.materials.append(fm)


def area(name, loc, size, power, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = power; l.color = color
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    c = o.constraints.new('TRACK_TO'); c.target = TGT; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    return o


area('key', (-0.5, -0.45, 0.6), 0.7, 45)
area('fill', (0.6, -0.3, 0.25), 0.9, 14, (0.85, 0.9, 1.0))
area('rim', (0.1, 0.6, 0.45), 0.5, 40, (0.7, 0.85, 1.0))
area('top', (0.0, 0.05, 0.8), 1.2, 25)

sc.render.filepath = os.path.join(HERE, 'frames', '')

# ---------------------------------------------------------------- modes
if args[0] == 'still':
    f = int(args[1]); sc.frame_set(f)
    sc.render.filepath = os.path.join(HERE, f'still_{f:04d}.png')
    if len(args) > 2:
        sc.render.resolution_percentage = int(args[2])
    bpy.ops.render.render(write_still=True)
elif args[0] == 'labels':                           # 2D positions of the label anchors per frame (for the overlays)
    out = {}
    for f in range(1, T.N + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        row = {}
        for n, e in ANCH.items():
            v = world_to_camera_view(sc, CAM, e.matrix_world.translation)
            row[n] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 4)]
        out[f] = row
    json.dump(out, open(os.path.join(HERE, 'labels.json'), 'w'))
    print('labels written')
elif args[0] == 'anim':
    bpy.ops.render.render(animation=True)

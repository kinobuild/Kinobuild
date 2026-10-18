"""Whitebox turntable — parameterized starting template for Blender 4.x/5.x.

Usage:
  blender --background --python clay_turntable.py -- \
      [--frames 96] [--fps 24] [--res 720] [--samples 18] \
      [--out /abs/path/frames_dir] [--smoke]

  --smoke  renders ONLY frame 1 as a still (scene-build validation)

After a full render, encode externally:
  ffmpeg -y -v error -framerate 24 -i <frames>/frame_%04d.png \
    -c:v libx264 -pix_fmt yuv420p -crf 18 out.mp4

Blender 5.x notes baked in (see SKILL.md section 2):
  - scene re-fetched after read_factory_settings
  - PNG output (no FFMPEG format in 5.x)
  - default BEZIER keyframes only (no action.fcurves access)
"""

import math
import os
import sys

import bpy

# ---------------- args ----------------
argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def flag(name, default=None, cast=str):
    if name not in argv:
        return cast(default) if default is not None else None
    return cast(argv[argv.index(name) + 1])


FRAMES = flag("--frames", "96", int)
FPS = flag("--fps", "24", int)
RES_H = flag("--res", "720", int)
RES_W = int(RES_H * 16 / 9)
SAMPLES = flag("--samples", "18", int)
OUT = flag("--out", os.path.expanduser("~/whitebox_out/frames"))
SMOKE = "--smoke" in argv

os.makedirs(OUT, exist_ok=True)

# ---------------- scene (re-fetch AFTER factory reset!) ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def clay(name, color, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    return m


mat_obj = clay("clay", (0.82, 0.82, 0.85))
mat_floor = clay("floor", (0.55, 0.56, 0.58))

bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(mat_floor)

# composition: swap this block for your own primitives / capsule actors
box_specs = [  # (w, d, h, x, y, rot_z_deg)
    (2.2, 2.2, 1.0, -1.5, -1.2, 0),
    (1.0, 1.0, 2.4, 1.6, 1.4, 30),
    (1.6, 0.8, 0.6, 1.2, -1.8, -15),
]
for w, d, h, x, y, rz in box_specs:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, h / 2))
    o = bpy.context.active_object
    o.scale = (w, d, h)
    o.rotation_euler[2] = math.radians(rz)
    o.data.materials.append(mat_obj)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(2.6, -0.6, 0.8))
bpy.context.active_object.data.materials.append(mat_obj)
bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.25, location=(-0.2, 2.4, 0.9))
bpy.context.active_object.data.materials.append(mat_obj)

# world + sun
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.85, 0.88, 0.92, 1.0)
bg.inputs[1].default_value = 0.6
sd = bpy.data.lights.new("sun", "SUN")
sd.energy = 3.0
sd.angle = math.radians(5)
so = bpy.data.objects.new("sun", sd)
scene.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(-12), math.radians(35))

# turntable camera: empty pivot + TRACK_TO
pivot = bpy.data.objects.new("pivot", None)
scene.collection.objects.link(pivot)
pivot.location = (0, 0, 1.0)
cd = bpy.data.cameras.new("cam")
cd.lens = 50
cam = bpy.data.objects.new("cam", cd)
scene.collection.objects.link(cam)
cam.parent = pivot
cam.location = (0, -7.5, 2.2)
tt = cam.constraints.new("TRACK_TO")
tt.target = pivot
tt.track_axis = "TRACK_NEGATIVE_Z"
tt.up_axis = "UP_Y"

scene.frame_start = 1
scene.frame_end = FRAMES
pivot.rotation_euler[2] = 0.0
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler[2] = math.radians(320)
pivot.keyframe_insert("rotation_euler", index=2, frame=FRAMES)

# ---------------- render config ----------------
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons.get("cycles")
dev = "CPU"
if prefs:
    cp = prefs.preferences
    for ctype in ("METAL", "OPTIX", "CUDA"):
        try:
            cp.compute_device_type = ctype
        except Exception:
            continue
        cp.get_devices()
        if [d for d in cp.devices if d.type != "CPU"]:
            for d in cp.devices:
                d.use = True
            scene.cycles.device = "GPU"
            dev = "GPU"
            break
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4
scene.render.resolution_x = RES_W
scene.render.resolution_y = RES_H
scene.render.fps = FPS
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(OUT, "frame_")
scene.camera = cam  # constraints alone do NOT make the camera active

print(f"WHITEBOX: dev={dev} frames={FRAMES} res={RES_W}x{RES_H} -> {OUT}", flush=True)
if SMOKE:
    scene.frame_set(1)
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("WHITEBOX: DONE", flush=True)

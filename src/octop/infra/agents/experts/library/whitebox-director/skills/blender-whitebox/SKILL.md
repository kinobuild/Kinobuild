---
name: blender-whitebox
description: >-
  Build whitebox / clay blocking 3D videos with headless Blender: scripted
  scene construction, capsule actors, camera language (over-the-shoulder,
  dolly, hard cuts, push-in), Cycles GPU render and ffmpeg encoding. Also
  reverse-engineers a live-action short film into a matching blocking
  animation. Trigger when the user asks for 白模/blocking/clay renders,
  Blender animations, camera-reference videos, or converting footage into
  3D blocking.
metadata:
  octop:
    emoji: "🧊"
---

# Blender Whitebox Blocking

Operate Blender **headlessly** (no GUI): write a Python `bpy` script →
`blender --background --python script.py` → PNG frame sequence → encode
MP4 with ffmpeg.

## 0. Preflight

```bash
blender --version        # expect 4.x / 5.x
ffmpeg -version          # encoding + video analysis
```

Missing on macOS: `brew install --cask blender` and `brew install ffmpeg`.
If `blender` is absent but the app exists, use
`/Applications/Blender.app/Contents/MacOS/Blender` or `/opt/homebrew/bin/blender`.

## 1. Core loop

1. Write a bpy script (start from `scripts/clay_turntable.py`).
2. **Smoke-test first**: patch the script to render ONE still frame
   (`scene.frame_end = 2`, `bpy.ops.render.render(write_still=True)`).
   Scene-build bugs are cheap to find on one frame, expensive on 360.
3. Full render to PNG frames, then encode:
   ```bash
   ffmpeg -y -v error -framerate 24 -i frames/frame_%04d.png \
     -c:v libx264 -pix_fmt yuv420p -crf 18 out.mp4
   ```
4. Verify with `ffmpeg -i out.mp4` (duration, resolution, fps). Visual
   composition QA: `read_file` 2–3 frames from different shots (see §8).

## 2. Blender 5.x hard pitfalls (all personally verified — do not re-discover)

- **Stale Scene reference**: `bpy.ops.wm.read_factory_settings(use_empty=True)`
  destroys the old `bpy.context.scene`. Always re-fetch AFTER the call:
  `scene = bpy.context.scene`. Otherwise:
  `ReferenceError: StructRNA of type Scene has been removed`.
- **No FFMPEG output format**: 5.x removed `FFMPEG` from
  `render.image_settings.file_format` (valid: PNG/JPEG/OPEN_EXR/WEBP...).
  Render PNG frames + encode externally. Do not set
  `scene.render.ffmpeg.*` — it raises a TypeError.
- **`scene.camera` is not keyable**: `scene.keyframe_insert("camera")`
  raises `property "camera" not animatable`. For multi-shot edits use ONE
  camera and place **adjacent keyframe pairs around each cut frame**
  (position A at frame N, position B at frame N+1) — the single-frame gap
  reads as a hard cut. Same trick for `camera.data.lens` jumps.
- **Slotted actions**: `action.fcurves` moved behind
  `action.layers[*].strips[*].channelbags[*].fcurves` in 5.x. Avoid
  touching interpolation curves from scripts; default BEZIER keyframes
  already give pleasant ease-in/out.
- **No `--exit-on-error` CLI flag** — unknown args are treated as files
  and crash startup. Detect failures via the log (`Saved:` line count) or
  frame count on disk.
- Always set `scene.camera = cam` — constraints don't make a camera active;
  otherwise `RuntimeError: Cannot render, no camera`.

## 3. Scene recipes

**Clay/whitebox material**: Principled BSDF, base color light gray
(0.80–0.90), roughness 0.6, specular 0.35. Two tones (e.g. 0.90 vs 0.60)
keep actors readable.

**Capsule actor** (parent everything to an empty "root" at floor level,
facing = root rotation_euler.z): sphere head z≈1.72 r≈0.16 · cone
shoulders z≈1.52 · cylinder torso z≈1.08 r≈0.19 · 2 arm cylinders
x=±0.27 z≈1.08 · 2 leg cylinders x=±0.11 z≈0.33. Add a child empty at
head height as camera look-target.

**Acting beats**: idle sway = tiny rot_x keys every 8 frames (±1°,
out of phase between actors); walk = location keys along a path with a
±5cm vertical bob every ~9 frames; turn = rot_z key pair over 12–16 frames.

**Night/HK mood**: world background near-black blue (0.04,0.05,0.07);
warm POINT light at the street lamp (energy ~900, color 1.0/0.78/0.5);
cool AREA fill opposite; SUN rim from behind; emissive boxes as neon
signboards (Emission shader, strength 20–40, cyan/pink/amber); floor
roughness 0.2 = wet-asphalt sheen.

## 4. Camera language

- **Over-the-shoulder (OTS)**: camera 20–40 cm behind and 30–60 cm to the
  side of the foreground actor, height ≈ their shoulder (1.55–1.70 m);
  look-target = the OTHER actor's head empty; lens 50–85 mm. The
  foreground head/shoulder must clip the frame edge — verify in a still,
  otherwise it degenerates into a close-up.
- **Push-in**: animate `camera.data.lens` (e.g. 38→52 mm) or dolly the
  location along the view axis.
- **Handheld feel**: add ±2 cm random jitter to every camera location key
  (seed `random.seed()` for determinism).
- **Dolly drift**: linear location drift per shot (e.g. 0.5–1 m creep)
  keeps static scenes alive.
- **Shot rhythm** for a dialogue: wide establish (2–3 s) → OTS A (4–5 s,
  turn/exit beat inside) → reaction medium (3–4 s) → OTS/watch-off with
  push-in (4–6 s).

## 5. Render settings baseline

```python
scene.render.engine = "CYCLES"
# GPU loop: try compute_device_type in ("METAL","OPTIX","CUDA"),
# cp.get_devices(), enable non-CPU devices, scene.cycles.device = "GPU"
scene.cycles.samples = 18          # 18–24 with denoise is plenty for clay
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 3
scene.render.resolution_x = 1280   # 720p; 1080p ≈ 2.2x slower
scene.render.fps = 24
scene.render.use_persistent_data = True
```

Expected speed: ~1.5–3 s/frame at 720p/18spp on Apple Silicon GPU →
15 s clip (360 frames) ≈ 10–20 min. Run long renders as background jobs.

## 6. Live-action short → blocking reconstruction

1. `bash scripts/analyze_video.sh input.mp4 out_dir/` → `cuts.txt`
   (shot boundary timestamps) + 3 keyframes per shot (first/middle/last).
2. **Look at every keyframe**: `read_file` each extracted frame — images
   return as multimodal blocks (§8). Note shot size (WS/MS/CU), camera
   height & angle, subject positions, foreground occluders (OTS?),
   background depth, movement direction between first→last frame of each
   shot. If your model lacks vision (§8 placeholder text), ask the USER to
   attach a contact sheet, or derive framing from ffmpeg metadata + the
   user's verbal description — never guess silently.
3. Map to durations: shot i length = cuts[i+1] − cuts[i] → frame counts
   at 24 fps.
4. Rebuild in one bpy script: set pieces approximated with boxes,
   capsule actors at the observed positions/facing, one camera with
   adjacent-pair cut keys per shot, lens chosen from the observed
   compression (WS≈24–35, MS≈50, CU/OTS≈65–85).
5. Smoke-test frame 1 of each shot (render those exact frames as stills,
   compare side-by-side with the original keyframes), then full render.

## 7. Delivery checklist

- [ ] duration/fps/resolution match the request (`ffmpeg -i`)
- [ ] frame count == expected (`ls frames | wc -l`)
- [ ] visual QA per §8 (attachment round-trip or geometry printout — never
      `read_file` on images)
- [ ] keep `frames/` dir (re-encode without re-rendering when asked to tweak)
- [ ] save the .py script next to the output — iteration = edit + re-render

## 8. KinoGuild runtime discipline (verified the hard way — do not re-discover)

**Reading images:** `read_file` on `.png/.jpg/.webp/.gif` returns the image
as a multimodal content block — vision models can look at rendered frames
directly. If the result instead says `[read_file: ... not attached because
this model does not support image content ...]`, your model has NO vision:
do NOT retry with renamed or converted files (pure token burn). Fall back to:

1. Geometry self-check: have the bpy script PRINT per-shot composition data
   (camera frustum vs actor bounding-box overlap, head-in-frame %, OTS
   foreground coverage) — framing is math, verifiable without eyes.
2. Contact-sheet round-trip: ffmpeg-tile 1 frame per shot into ONE image,
   ask the user to attach it to the chat — user uploads DO reach the
   multimodal model.
3. Neither works: deliver with a note that composition was verified
   geometrically.

**Background renders must be detached and isolated:**

```bash
pkill -f "blender.*<scene-name>" 2>/dev/null   # kill stale renders of this scene
mkdir -p render_r1 && cd render_r1             # FRESH output dir per attempt
(setsid blender -b -P script.py > render.log 2>&1 < /dev/null &)
```

- A tool-call timeout does NOT mean the render died — the process often
  survives as an orphan and keeps writing into the SAME `frames/` dir,
  mixing frame ranges (observed: 1–57 from an orphan + 368–436 from the new
  run). Before any re-render: `pgrep -f blender`, kill strays, use a NEW dir.
- Poll progress with `ls frames | wc -l` in fresh short commands; never hold
  a shell open waiting for the render (120 s tool timeout will cut you off).
- `setsid` + `</dev/null` + `&` inside `( ... )` survives session teardown.

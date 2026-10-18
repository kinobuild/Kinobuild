#!/usr/bin/env bash
# analyze_video.sh — split a live-action video into shots + keyframes.
#
# Usage: bash analyze_video.sh <video> [outdir]
# Output:
#   <outdir>/cuts.txt        shot boundary timestamps (one per line)
#   <outdir>/shotNN_a.png    first frame of shot NN
#   <outdir>/shotNN_b.png    middle frame
#   <outdir>/shotNN_c.png    last frame
#
# Feed the keyframes to a vision model to read composition/camera work,
# then rebuild as blocking (see SKILL.md section 6).
set -euo pipefail

VIDEO="${1:?usage: analyze_video.sh <video> [outdir]}"
OUT="${2:-${VIDEO%.*}_shots}"
THRESH="${SCENE_THRESHOLD:-0.3}"
FFMPEG="${FFMPEG:-ffmpeg}"

mkdir -p "$OUT"
echo "==> scene detection (threshold $THRESH)"
"$FFMPEG" -hide_banner -i "$VIDEO" \
  -vf "select='gt(scene,${THRESH})',showinfo" -f null - 2>&1 \
  | grep -oE "pts_time:[0-9.]+" | cut -d: -f2 > "$OUT/cuts.txt" || true

echo "==> extracting keyframes per shot"
python3 - "$VIDEO" "$OUT" "$FFMPEG" <<'PY'
import subprocess, sys, os
video, out, ff = sys.argv[1], sys.argv[2], sys.argv[3]
dur = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=nw=1:nk=1", video]).strip())
cuts = [float(x) for x in open(os.path.join(out, "cuts.txt")) if x.strip()]
bounds = [0.0] + [c for c in cuts if 0 < c < dur] + [dur]
shots = [(a, b) for a, b in zip(bounds, bounds[1:]) if b - a > 0.2]
print(f"{len(shots)} shots, total {dur:.2f}s")
for i, (a, b) in enumerate(shots, 1):
    span = b - a
    for tag, t in (("a", a + 0.04), ("b", a + span / 2), ("c", b - 0.08)):
        dst = os.path.join(out, f"shot{i:02d}_{tag}.png")
        subprocess.run([ff, "-y", "-v", "error", "-ss", f"{t:.3f}",
                        "-i", video, "-frames:v", "1", dst], check=True)
    print(f"  shot {i:02d}: {a:7.2f} -> {b:7.2f}  ({span:5.2f}s, "
          f"{int(round(span*24))}f@24fps)")
PY
echo "==> done: $OUT"

---
name: reference-image-handling
description: Auto-resize policy for reference images — caps every reference at ≤1024px max dimension and ≤1MB file size to prevent Cloudflare 524 timeouts observed when sending raw 2.5MB+ PNGs to gemini-3-pro-image-preview's chat-completions endpoint. Uses PIL thumbnail to preserve aspect ratio. Documents passthrough rule, multi-reference constraints (Gemini ≤9 images per call), and what this preprocessing intentionally does not do (no smart crop, no background removal, no upscale). Loaded by the parent SKILL.md's Execution Procedure Step 2.
---

# Reference Image Handling

How `--reference-image` paths are preprocessed before sending.

## Execution Procedure

```
maybe_resize(path: Path, max_dim: int = 1024, max_bytes: int = 1024*1024) → Path

if path.stat().st_size ≤ max_bytes:
    with PIL.Image.open(path) as im:
        if max(im.size) ≤ max_dim:
            return path                          # passthrough — no temp file

with PIL.Image.open(path) as im:
    im.thumbnail((max_dim, max_dim), Image.LANCZOS)
    suffix = ".jpg" if im.mode == "RGB" else path.suffix
    tmp = Path(tempfile.mktemp(prefix="ref_", suffix=suffix))
    if suffix == ".jpg":
        im.convert("RGB").save(tmp, "JPEG", quality=88, optimize=True)
    else:
        im.save(tmp, optimize=True)

log "auto-resized {path.name}: {orig_kb}KB → {new_kb}KB ({max_dim}px max)"
return tmp
```

## The 524 Finding (Why This File Exists)

**Observed in practice**: sending a 2.5MB PNG reference image to `gemini-3-pro-image-preview` via `/v1/chat/completions` reliably returns **HTTP 524** at the edge proxy. The same prompt with a downsized version of the same image (1.0MB at 768px) succeeds in ~62 seconds.

Root cause: base64 encoding inflates the payload by ~33% (2.5MB → ~3.4MB). The edge timeout (typically ~100s on most CDNs) elapses before the Gemini upstream finishes ingesting + processing + returning the generated image. The model itself never gets a chance to respond.

**Implication**: any caller passing camera-original or rendered-PNG reference images (which routinely run 5-10MB) will fail without preprocessing. All image-to-image callers in this collection (`product-shots-ad-creative`, `product-image`, `url-to-design`) inherit this safeguard automatically.

## Auto-Resize Rule (Plain English)

For every path passed via `--reference-image`:

```
if file_size ≤ 1 MB AND max_dimension ≤ 1024 px:
    passthrough — use the file as-is
else:
    resize with PIL.Image.thumbnail((1024, 1024), LANCZOS)
    save to a temp file (.jpg if RGB, original ext otherwise)
    log: "auto-resized X.png: 2520KB → 980KB (1024px max)"
    use the temp file
```

`thumbnail()` preserves aspect ratio — it scales so the longer side equals 1024 and the shorter side is computed proportionally. RGB images are saved as JPEG (quality=88) for smaller payload; non-RGB (e.g., RGBA with alpha) keep the original format.

## Multi-Reference Constraints

| Family | Max references per call | Notes |
|---|---|---|
| gemini | 9 (typical upstream limit) | Each adds a separate `image_url` block in the multimodal message |
| openai | depends on endpoint | `/v1/images/edits` accepts multiple `image[]` form fields; verify cost (token usage scales) |

For callers needing >9 references (rare; usually for character-consistency master sheets), batch into multiple calls and feed the most-recent outputs as references to subsequent calls.

## What This Skill Does NOT Do

- **Crop intelligently** — `thumbnail` is a uniform scale-down, not subject-aware cropping. If the caller needs a specific crop (e.g., face-centered), the caller is responsible for pre-cropping before passing the path.
- **Background remove** — out of scope; use a separate tool.
- **Upscale** — only ever downsamples. If the source is already small, it passes through untouched.
- **Persist resized files** — temp files are created in `tempfile.mktemp()` and not cleaned. OS cleanup handles them. Don't rely on temp paths surviving across calls.

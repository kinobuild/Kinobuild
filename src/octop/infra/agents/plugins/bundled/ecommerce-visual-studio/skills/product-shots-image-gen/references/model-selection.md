---
name: model-selection
description: OmniMaaS / Cloubic gateway image-generation catalogue (8 models) plus the family-routing logic that maps a model name to its endpoint group. Covers which model to default to for each common use case (photorealism / creative / image-to-image / cost-sensitive) and the per-family differences a caller needs to know. Loaded by the parent SKILL.md's Execution Procedure Step 1.
---

# Model Selection

The OmniMaaS / Cloubic gateway image-generation catalogue (8 models, snapshot). This document is the **single source of truth** for which model to use in which scenario.

## Execution Procedure

```
model_family(model: str) → "openai" | "gemini"

OPENAI_MODELS = {"gpt-image-1", "gpt-image-2", "dall-e-3"}
GEMINI_MODELS = {"gemini-3-pro-image-preview", "gemini-3.1-flash-image-preview",
                 "gemini-2.5-flash-image-preview", "gemini-2.5-flash-image"}

if model in OPENAI_MODELS:    return "openai"
if model in GEMINI_MODELS:    return "gemini"
exit 1 with: "Unknown model: <model>. Supported: <union of both sets>"
```

```
select_default_model(use_case: str = "general") → model_name

"text-overlay"      → "gpt-image-2"      ← any on-image text (headlines, labels,
                                            CTAs, price chips, callout labels)
"photorealistic"    → "gpt-image-2"
"creative"          → "gemini-3-pro-image-preview"
"image-to-image"    → "gemini-3-pro-image-preview"  ← unless text overlay too,
                                                      then "gpt-image-2"
"cost-sensitive"    → "gemini-3.1-flash-image-preview"
"general" (default) → "gemini-3-pro-image-preview"
```

**Trigger detection for `"text-overlay"`** — caller (or prompt-keyword scan)
sees any of: "caption", "headline", "label", "callout", "leader line",
"price tag/chip", "CTA button", "Shop Now", "$<number>", "watermark text",
"sticker overlay", "annotation". When in doubt: if the user prompt
*asks for letters or digits to appear on the image*, use `"text-overlay"`.

## Family Routing

Auto-derived from the model name string. Never ask the user.

| Family | Models | Endpoint | Body format |
|---|---|---|---|
| `openai` | `gpt-image-1`, `gpt-image-2`, `dall-e-3` | `/v1/images/generations` (text-to-image) or `/v1/images/edits` (image-to-image, multipart) | JSON or multipart/form-data |
| `gemini` | `gemini-3-pro-image-preview`, `gemini-3.1-flash-image-preview`, `gemini-2.5-flash-image-preview`, `gemini-2.5-flash-image` | `/v1/chat/completions` (always) | OpenAI chat-completions JSON with multimodal `content` array |

Other OmniMaaS / Cloubic gateway image models (`qwen-image-edit-plus`, `doubao-seedream-5-0-*`) are **not currently supported** by this skill — they use vendor-specific endpoints. Add support as needed; this skill is structured to make adding a third family straightforward.

## Model Catalogue

| Model | Family | Input cost | Output cost | Typical /image | Strength |
|---|---|---|---|---|---|
| **`gemini-3-pro-image-preview`** ⭐ | gemini | ¥0.0128/1K | ¥0.7668/1K | **¥1.00** | All-rounder. Nano Banana Pro. Strong photorealism + creative output + native image-to-image. **Default for text-free output.** Garbles on-image text — do NOT use for headlines / labels / CTAs. |
| `gpt-image-2` | openai | ¥0.0511/1K | ¥0.1917/1K | ¥0.35 | OpenAI's strongest. Excellent prompt adherence. **Required for any on-image text** (headlines, callout labels, price chips, CTA buttons) — Gemini family cannot render small text reliably. Multimodal input via Function Calling. Cheaper than Nano Banana Pro per image. |
| `gemini-3.1-flash-image-preview` | gemini | ¥0.0032/1K | ¥0.3834/1K | ¥0.20 | Nano Banana (non-Pro). Cheapest quality option. Use for high-volume / draft generation. |
| `gpt-image-1` | openai | ¥0.0319/1K | ¥0.2556/1K | ¥0.50 | Older OpenAI image model. Use only if gpt-image-2 unavailable. |
| `gemini-2.5-flash-image` / `-preview` | gemini | ¥0.0019/1K | ¥0.1917/1K | ¥0.15 | Older Nano Banana variants. Cheaper but weaker than 3.1 flash. |
| `dall-e-3` | openai | per-call | per-call | ¥0.26/call | Legacy. Avoid for new work. |

## Decision Tree

```
"What kind of image?"
├─ Image must render readable on-image text  ⭐ CHECK FIRST
│  (headlines, captions, labels, callouts, CTAs, price chips, leader-line
│   annotations, sticker overlays, watermark text)
│    → gpt-image-2  (clean small-text rendering; Gemini garbles <30pt text)
│  This rule WINS over any other branch — if the image needs text AND is
│  also photorealistic / image-to-image / creative, still use gpt-image-2.
│  For image-to-image text overlays, route via /v1/images/edits with the
│  caller's reference image; gpt-image-2 preserves composition while
│  editing in the ad copy.
│
├─ Hyper-photorealistic (product photo, editorial portrait, lifestyle)
│    → gpt-image-2  (strongest prompt adherence + clean output)
│
├─ Creative / artistic / stylised (poster, illustration, conceptual art)
│    → gemini-3-pro-image-preview  (Nano Banana Pro)
│
├─ Image-to-image with reference (background swap, character consistency)
│    → gemini-3-pro-image-preview  (native multimodal, simpler than OpenAI's /v1/images/edits)
│
├─ High-volume drafts / cost-sensitive
│    → gemini-3.1-flash-image-preview  (¥0.20/image, ~6× cheaper than the Pro)
│
└─ No preference / general use
     → gemini-3-pro-image-preview  (default)
```

## Family Differences (Caller Should Know)

| Capability | OpenAI | Gemini |
|---|---|---|
| On-image text rendering | ✓ crisp at 24pt+ (headlines, CTAs, callout labels) | ✗ garbles small text, mis-spells short words. Acceptable only for very large display text (60pt+) and even then unreliable. **Route any text-bearing request to OpenAI.** |
| Multiple variations (`n > 1`) | ✓ (one call, n results) | ✗ (one image per call; loop externally) |
| Explicit pixel sizes | ✓ (`size: "1024x1024"` etc.) | ✗ (aspect ratio embedded in prompt) |
| Image-to-image | via separate `/v1/images/edits` endpoint (multipart) | same endpoint, reference image as `image_url` content block |
| Output format | PNG (b64_json) | JPEG (data URL in markdown) |
| Typical latency | 60-300s (longer for /v1/images/edits with reference + text) | 50-70s |
| Cost per image (1024-ish) | ¥0.35-0.50 | ¥0.20-1.00 |

## Future Extensions

If new models appear on OmniMaaS / Cloubic gateway, update `OPENAI_MODELS` / `GEMINI_MODELS` sets in `scripts/generate.py` and add a row to the catalogue here. A third family (e.g., Doubao Seedream) requires a new `generate_<family>(...)` function and a dispatch branch in `main()`.

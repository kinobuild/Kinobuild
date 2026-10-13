---
name: variables-and-workflow
description: Section 1 (Variables — 14 input variables, types, extraction specs for HAIRSTYLE / OUTFIT / SKIN_TONE) and Section 3 (Workflow — analyse → confirm style → batch generate, plus user-override re-render mapping) of multi-angle-shots. Read at EP Step 2 (variable extraction) and Step 6 (override handling).
---

# Variables + Workflow

The 14-variable schema and the analyse → confirm → batch workflow that lock identity / hairstyle / outfit / accessories before any image is generated.

## Execution Procedure

```
extract_and_route(reference_image, user_overrides) → {extracted_vars, regen_targets}

# Variable extraction (Vision Model pass)
for var in 14_variables:
    if var.required:
        extracted[var] = vision_model.extract(reference_image, var.spec)
        if extraction_confidence < threshold → ask user for clarification
    else:
        extracted[var] = vision_model.extract(reference_image, var.spec) or "none"

# Apply user overrides (if any)
for key, value in user_overrides.items():
    extracted[key] = value
    regen_targets ∪= images_affected_by(key)   # see §Variable Override Logic

return extracted, regen_targets
```

## TOC

- [Section 1 — Variables (14 fields)](#section-1--variables-14-fields)
- [Variable Extraction Specifications](#variable-extraction-specifications)
- [Section 3 — Workflow](#section-3--workflow)
- [Variable Override Logic](#variable-override-logic)

---

## Section 1 — Variables (14 fields)

| # | Variable | Data Type | Source | Required | Default | Purpose |
|---|---|---|---|---|---|---|
| 1 | `REFERENCE_IMAGE` | Image URL | User upload | ✅ | none | Reference input to the image-generation model; locks identity |
| 2 | `HAIR_COLOR` | String | Image analysis | ✅ | none | Precise hue (e.g., "dark brown with red undertones") |
| 3 | `HAIRSTYLE` | String | Image analysis | ✅ | none | Structural description (tied/loose/bun, volume, texture, arrangement) |
| 4 | `HAIR_ACCESSORIES` | String | Image analysis | ❌ | `"none"` | Hair clips / bands / hoops — type, color, position |
| 5 | `SKIN_TONE` | String | Image analysis | ✅ | none | Skin tone + markers (freckles / moles / scars) |
| 6 | `EYE_COLOR` | String | Image analysis | ✅ | none | Iris color |
| 7 | `FACE_SHAPE` | String | Image analysis | ✅ | none | Facial structure description |
| 8 | `OUTFIT` | String | Image analysis | ✅ | none | All garment items (color / material / fit / layering) |
| 9 | `BAG` | String | Image analysis | ❌ | `"none"` | Type / color / material / position |
| 10 | `JEWELRY` | String | Image analysis | ❌ | `"none"` | All visible jewelry |
| 11 | `OTHER_ACCESSORIES` | String | Image analysis | ❌ | `"none"` | Other wearable accessories |
| 12 | `BACKGROUND_COLOR` | String / Hex | Image analysis or user-specified | ✅ | none | Studio backdrop color (e.g. `#f1eee9` or "light cream") |
| 13 | `PHOTOGRAPHY_STYLE` | String (long) | User-selected preset or custom | ✅ | none | Full lighting / texture / color spec |
| 14 | `ASPECT_RATIO` | String | User-specified or default | ✅ | `"3:4"` | Canvas aspect ratio |

`SUBJECT_DESCRIPTION` appears in the Task Prompts as a composed field that pulls from HAIR_COLOR + HAIRSTYLE + SKIN_TONE + OUTFIT + accessories — it is **not** a separate input variable.

---

## Variable Extraction Specifications

```
extract_variables(reference_image) → extracted{14 fields}
    for var in 14_variables:                     # see §Section 1 for the 14 fields
        extracted[var] = vision_model.extract(reference_image, var.spec)
        if var.required and confidence < threshold → ask user to clarify
    return extracted
```

This is the entry point invoked from SKILL.md EP Step 2; the per-field specs below (HAIRSTYLE / OUTFIT / SKIN_TONE) drive `var.spec`.

### `HAIRSTYLE` Extraction Spec

```
Required dimensions:
1. Structure: tied / loose / bun / braided
2. Fastening: ponytail / bun / braid / chignon
3. Position: high / mid / low / side
4. Volume: voluminous / tight / natural
5. Texture: straight / curly / wavy / messy

Wrong example: "long hair"
Correct example: "深棕色长发扎成低位马尾,紧致光滑,用黑色发圈固定,无碎发"
```

### `OUTFIT` Extraction Spec

```
Required dimensions:
1. Item list: top / pants / skirt / outerwear / shoes
2. Color: primary + accent (e.g. "off-white with light grey stripes")
3. Material: cotton / silk / leather / knit / denim
4. Fit: loose / fitted / oversized
5. Layering: inner + outer order

Wrong example: "white top and jeans"
Correct example: "米白色宽松棉质 T 恤,深蓝色修身牛仔裤,黑色皮革腰带"
```

### `SKIN_TONE` Extraction Spec

```
Required:
1. Base undertone: cool / warm / neutral
2. Lightness: light / medium / deep
3. Markers: location and density of freckles / moles / scars

Wrong example: "white skin"
Correct example: "浅暖调肤色,鼻梁和脸颊有淡雀斑,左颧骨下方有小痣"
```

---

## Section 3 — Workflow

```
┌──────────────────────────┐
│ User uploads reference   │
└────────────┬─────────────┘
             │
             ▼
┌────────────────────────────────────┐
│ Multimodal analysis: extract 14    │ ← Vision Model
│ variables (hair/outfit/accessories │
│ /skin tone...)                     │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│ Pause: present 3 photography style │ ← User interaction
│ presets (skip if style specified)  │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│ Fill 9 prompt templates; each call │
│ receives:                          │
│ - reference image (mandatory)      │
│ - text prompt (composition+style)  │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│ Single-batch generation, 9 images  │ ← Image-generation model
└────────────────────────────────────┘
```

### Style-Selection Pause Logic

```
def should_pause_for_style_selection(user_input, context):
    """
    Decide whether to pause for the user to pick a photography style.
    """
    # Has the user already specified a style?
    if has_explicit_style_specification(user_input):
        return False  # skip the picker; use the specified style

    # Did the user upload a style reference image?
    if has_style_reference_image(context):
        return False  # use the reference image's style

    # Default: pause and show 3 presets
    return True

def has_explicit_style_specification(user_input):
    """
    Detect style keywords in the user's input.
    """
    style_keywords = [
        "复古", "retro", "analog", "flash",
        "柔和", "soft", "muted", "film",
        "硬光", "hard", "editorial", "dramatic"
    ]
    return any(keyword in user_input.lower() for keyword in style_keywords)

def has_style_reference_image(context):
    """
    True when the user uploaded an image specifically tagged as a style reference
    (distinct from REFERENCE_IMAGE which anchors identity).
    """
    return bool(context.get("style_reference_image"))
```

### Single-Batch Generation Call

```
batch_generate(prompts, reference_image) → 9_images
    # Host-platform image-generation capability invoked once with all 9 filled prompts.
    # Single call locks the random-seed neighbourhood so the 9 frames inherit a
    # shared visual signature (lighting / shadow / grain). See hard-constraints.md
    # RULE_008 — Single-Batch Generation.
    assert len(prompts) == 9
    assert reference_image is not None       # RULE_001
    return image_model.generate_batch(prompts, reference_image=reference_image)
```

### Workflow Design Notes

- **Analyse first** — extract variables before any prompt is filled. Prevents the model from guessing facial features / hair structure based on partial text.
- **Style confirmation** — visualised previews lower the user's decision cost and lock the lighting / colour budget before generation.
- **Batch generation** — all 9 images in one call avoids inter-call model-state drift (which produces "this image looks more digital than the others" failures).

---

## Variable Override Logic

The user can override any extracted variable. Map each variable to the images that must be re-rendered:

```
def apply_user_overrides(extracted_variables, user_overrides):
    """
    The user can override any extracted variable.
    """
    for key, value in user_overrides.items():
        if key in extracted_variables:
            extracted_variables[key] = value
            # Mark images that must be regenerated
            mark_affected_images_for_regeneration(key)

    return extracted_variables

def mark_affected_images_for_regeneration(variable_key):
    """
    Determine which images must be regenerated based on the variable type.
    """
    if variable_key in ["HAIRSTYLE", "HAIR_COLOR", "HAIR_ACCESSORIES"]:
        # Hairstyle changes affect every image, especially Image 4 and 8
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]

    elif variable_key == "OUTFIT":
        # Outfit changes affect every image except Image 5 (extreme close-up)
        return [1, 2, 3, 4, 6, 7, 8, 9]

    elif variable_key in ["BAG", "JEWELRY"]:
        # Accessory changes affect images where the crop reveals the accessory
        return [1, 2, 3, 6, 9]

    elif variable_key == "PHOTOGRAPHY_STYLE":
        # Style changes affect every image
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

| Variable | Affected images | Reason |
|---|---|---|
| `HAIRSTYLE` / `HAIR_COLOR` / `HAIR_ACCESSORIES` | 1-9 (all) | hair is visible (or partially visible) in every frame; Image 4 + 8 are the strictest validation views |
| `OUTFIT` | 1, 2, 3, 4, 6, 7, 8, 9 | Image 5 (extreme facial close-up) does not show clothing |
| `BAG` / `JEWELRY` | 1, 2, 3, 6, 9 | the in-frame frames; other crops exclude these accessories |
| `PHOTOGRAPHY_STYLE` | 1-9 (all) | style is global by design (Rule 6); changing it requires regenerating every frame |
| `SKIN_TONE` / `EYE_COLOR` / `FACE_SHAPE` | 1-9 (all) | identity-locking variables; affect every frame |
| `BACKGROUND_COLOR` | 1-9 (all) | studio backdrop is shared across the series |
| `ASPECT_RATIO` | 1-9 (all) | canvas-level change |

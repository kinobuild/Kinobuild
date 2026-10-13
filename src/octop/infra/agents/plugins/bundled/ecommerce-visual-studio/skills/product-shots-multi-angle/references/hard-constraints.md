---
name: hard-constraints
description: The 8 MUST-level rules of multi-angle-shots (Rules section) — reference-image traversal, analyse-before-generate, hairstyle-intact, accessory fidelity, hard crop boundaries, global style unity, user-override handling, single-batch generation. Loaded by the parent skill's Execution Procedure Step 0 and re-validated at the Self-Check Gate (Step 5). Violations break identity / hairstyle / crop integrity that the validation views (Image 4 back, Image 8 side) cannot recover.
---

# Hard Constraints — The 8 Rules

These rules are MUST-level. Read at Execution Procedure Step 0; re-validate against them at Self-Check Gate (Step 5) before delivering the 9-image series. Identity / hairstyle / crop integrity cannot be recovered downstream — if any rule fails, regenerate the affected image(s).

## Execution Procedure

```
enforce_constraints(extracted_vars, prompts[], outputs[]) → pass | findings[]

# RULE_001 — Reference image traversal (Identity)
assert REFERENCE_IMAGE present in user upload
for each prompt in prompts:
    assert prompt is invoked with REFERENCE_IMAGE as image input
    assert prompt contains [Reference image: {REFERENCE_IMAGE}] header

# RULE_002 — Analyse before generate (Workflow)
assert all 14 variables extracted before any prompt is filled
assert no variable was guessed / defaulted silently

# RULE_003 — Hairstyle structure intact (Hair)
for each prompt where hairstyle is visible (images 1, 2, 3, 4, 6, 7, 8, 9):
    assert prompt contains "{HAIRSTYLE} intact"
    assert prompt contains "NO loose hair"
    assert prompt contains "NO reinterpretation"   # (image 4 + image 8 require this)

# RULE_004 — Accessory fidelity
for each prompt:
    if reference has accessory AND crop reveals it    → accessory described
    if reference has no accessory                      → no accessory added
    if accessory exists but crop excludes it           → annotated "where possible"
                                                          or "No accessories — frame doesn't reach them"

# RULE_005 — Hard crop boundaries
for each image_id, expected_crop in §Crop Boundaries:
    assert output respects crop (no body parts beyond the boundary)

# RULE_006 — Global style unity
for each prompt:
    assert prompt repeats the full {PHOTOGRAPHY_STYLE} block verbatim
for each output:
    assert lighting / shadow direction / grain / colour signature match the chosen preset
    NEVER allow an image to look cleaner / more digital / higher-contrast than the others

# RULE_007 — User override re-render
on user override:
    affected = compute_affected_images(variable_key)   # see variables-and-workflow.md §Override Logic
    re-render(affected)
    keep already-correct images unchanged

# RULE_008 — Single-batch generation
default: batch-generate all 9 images in one call
exception: user explicitly requests stepwise review
reason: avoid model-state drift across separate calls

emit findings if any assert fails
```

## TOC

- [Rule 1 — Reference Image Mandatory (Identity)](#rule-1--reference-image-mandatory-identity)
- [Rule 2 — Analyse Before Generate (Workflow)](#rule-2--analyse-before-generate-workflow)
- [Rule 3 — Hairstyle Structure Intact (Hair)](#rule-3--hairstyle-structure-intact-hair)
- [Rule 4 — Accessory Fidelity (Accessories)](#rule-4--accessory-fidelity-accessories)
- [Rule 5 — Hard Crop Boundaries (Crop)](#rule-5--hard-crop-boundaries-crop)
- [Rule 6 — Global Style Unity (Style)](#rule-6--global-style-unity-style)
- [Rule 7 — User Override Re-render (Override)](#rule-7--user-override-re-render-override)
- [Rule 8 — Single-Batch Generation (Batch)](#rule-8--single-batch-generation-batch)

---

## Rule 1 — Reference Image Mandatory (Identity)

```
RULE_001: Reference image is mandatory
- Every image-generation call MUST pass REFERENCE_IMAGE as the image input
- Violation: using text description only, without the reference image
- Consequence: identity consistency cannot be guaranteed; task fails
```

**Why** — pure text descriptions cannot transmit the high-dimensional facial features (micro-expression / bone structure / skin texture) that make the 9 frames look like the same person. The reference image is the image-generation model's image-to-image anchor; the text prompt only controls composition / pose / style.

## Rule 2 — Analyse Before Generate (Workflow)

```
RULE_002: Analyse before generate
- All 14 variables MUST be extracted before any prompt template is filled
- Forbidden: guessing variable values, using silent defaults, skipping analysis
- Validation: confirm a complete variable-extraction output exists
```

## Rule 3 — Hairstyle Structure Intact (Hair)

```
RULE_003: No reinterpretation of hairstyle structure
- If the reference shows a tied/bunned hairstyle, every angle must keep that structure
- Forbidden: rendering a structured hairstyle as loose hair
- Required prompt constraints:
  - MUST include "{HAIRSTYLE} intact"
  - MUST include "NO loose hair"
  - MUST include "NO reinterpretation"
- Validation views: Image 4 (back) and Image 8 (side)
```

**CRITICAL** — Image 4 (back view) and Image 8 (side profile) exist *specifically* to verify that the hairstyle structure survives a 180° / 90° rotation. If the model renders a tied hairstyle as loose hair on these two frames, the entire 9-image set is invalid.

## Rule 4 — Accessory Fidelity (Accessories)

```
RULE_004: Accessory add/remove constraint
- IF reference has an accessory AND the crop reveals it → MUST keep
- IF reference has no accessory → MUST NOT add
- Special case: accessories outside the crop may be omitted; annotate "where possible" in the prompt
```

For Image 5 (extreme facial close-up), accessories are physically out of frame — the prompt MUST state `No accessories — frame doesn't reach them` so the model does not hallucinate jewellery that contradicts the reference.

## Rule 5 — Hard Crop Boundaries (Crop)

```
RULE_005: Hard crop boundaries
- "crop at mid-thigh" = frame must end above the knees
- "crop at chest" = no abdomen visible
- "crop at hip line" = no thighs visible
- Violation: any body part extends past the crop boundary
- Example negative constraint: "No knees, lower legs, or feet"
```

Crop is enforced via explicit *negative constraints* in each prompt (e.g., `No knees, lower legs, or feet`). See `references/task-prompts.md` for the per-image crop boundary and the matching negative-constraint phrase.

| Image | Upper bound | Lower bound | Forbidden |
|---|---|---|---|
| 1 | top of head | mid-thigh | knees, lower legs, feet |
| 2 | top of head | upper thigh | knees, lower legs |
| 3 | top of head | upper chest | abdomen, waist |
| 4 | top of head | hip line | thighs |
| 5 | (eyes/nose/lips only) | (eyes/nose/lips only) | forehead, chin, neck, shoulders, head outline |
| 6 | top of head | upper chest | abdomen and below |
| 7 | top of head | upper waist | (only upper-body clothing visible) |
| 8 | top of head | below chest | (strict chest crop) |
| 9 | top of head | mid-thigh | knees and below |

## Rule 6 — Global Style Unity (Style)

```
RULE_006: Global style unity
- All 9 images MUST apply the same {PHOTOGRAPHY_STYLE}
- Forbidden: some images cleaner / more digital / higher-contrast than others
- Validation: confirm every prompt contains the full style description
```

Each of the 9 prompts repeats the full chosen `{PHOTOGRAPHY_STYLE}` block verbatim. Do **not** abbreviate or reference it — repetition is what keeps the model's style budget aligned across calls.

## Rule 7 — User Override Re-render (Override)

The user may override any extracted variable. Re-render only the images affected by that variable — see `references/variables-and-workflow.md §Variable Override Logic` for the full mapping (HAIRSTYLE → all 9, OUTFIT → 1/2/3/4/6/7/8/9, BAG/JEWELRY → 1/2/3/6/9, PHOTOGRAPHY_STYLE → all 9).

## Rule 8 — Single-Batch Generation (Batch)

```
RULE_008: Single-batch generation preferred
- Default: generate all 9 images in one call
- Exception: the user explicitly asks for stepwise review
- Reason: avoid model-state drift across separate calls
```

Multiple generation calls drift in style / lighting / colour temperature even with identical prompts. Single-batch generation locks the random-seed neighbourhood so the 9 frames inherit a shared visual signature.

## Why These Are MUST-level

- **Reference image absent** → identity is untraceable; the 9 frames look like 9 different people. Task fails.
- **Variable extraction skipped** → silent defaults (e.g. "long hair") lose the structural detail (low ponytail, no flyaways) that prompts need; outputs become generic.
- **Hairstyle reinterpretation** → tied hair becomes loose; the validation views (Image 4 / Image 8) flag it but only after rendering.
- **Accessory mismatch** → reference's silver chain becomes a gold pendant in Image 1, vanishes in Image 3; series is incoherent.
- **Crop boundary breach** → e-commerce / lookbook standards reject the asset (knees in a "mid-thigh" frame is an immediate fail).
- **Style drift** → some frames look filmic, others look CGI-clean → set is unusable as a single shoot.
- **Re-render of unaffected images** → wastes generation budget and risks introducing fresh drift on already-correct frames.
- **Multi-call generation** → state-difference contamination; a single batch avoids it.

---
name: consistency-rules
description: Multi-Image Generation Consistency Rules — packaged as an XML <consistency_rules> block (4 rules) — plus Conversion Rate Reference Data (5 benchmarks). Loaded at EP Step 0 and applied at EP Steps 3 and 4 to keep product appearance, style, and color identical across the main image, secondary images, and A+ Page modules.
---

# Multi-Image Consistency Rules + Conversion Rate Data

When the suite produces 7-15 separate images that must read as a single product family, consistency must be enforced explicitly through prompt-level anchoring. Without these 4 rules, AI-generated images drift in color / material / detail across calls and the suite looks like 15 different products.

## Execution Procedure

```
enforce_consistency(generation_plan) → consistent_suite

# Rule 1: Main Image First (must be generated before any secondary)
assert main_image generated BEFORE any secondary or A+ generation call

# Rule 2: Reference Main Image in every downstream call
for each downstream_image in (secondary + aplus):
    assert downstream_image.prompt.image_url_list contains main_image_url

# Rule 3: Consistent Appearance — explicit prompt-level clause
for each downstream_image in (secondary + aplus):
    assert downstream_image.prompt contains "Match product color, material, and details from reference image exactly"

# Rule 4: Unified Style — across all images
assert background_style unified across all images
assert color_scheme unified
assert font_family unified (in any in-image text)
assert icon_style unified (in any in-image iconography)
```

## TOC

- [`<consistency_rules>` — XML block (4 rules)](#consistency_rules--xml-block)
- [Per-rule explanation](#per-rule-explanation)
- [Conversion Rate Reference Data (5 benchmarks)](#conversion-rate-reference-data)

## `<consistency_rules>` — XML block

```
<consistency_rules>
  1. Main Image First
     Generate the main image first to establish the visual baseline for the entire suite.

  2. Reference Main Image
     When generating any secondary image or A+ module, reference the main image URL
     as the visual baseline (image_url_list / reference_image_urls parameter).

  3. Consistent Appearance
     Product color, material, and details MUST stay unified across all images.
     Inject the prompt clause: "Match product color, material, and details from
     reference image exactly".

  4. Unified Style
     Maintain consistent background style, color palette, font family, and icon style
     across every image in the suite.
</consistency_rules>
```

## Per-rule explanation

### Rule 1 — Main Image First

The main image is the visual baseline. Every other image in the suite (6 secondary + 8 A+ = 14 downstream images) inherits its product appearance from the main. Therefore: never generate a secondary image or A+ module before the main image exists.

If the user requests "A+ only" without a main image already in hand, the skill must first ask for or generate a main image to use as the consistency anchor.

### Rule 2 — Reference Main Image

Every downstream image-generation call must include the main image URL in the `image_url_list` (or `reference_image_urls`) parameter. This is the technical mechanism — passing the main image as a visual reference forces the image-to-image generator to match the product's visual identity.

```
generate_image(
    prompt = "...",
    image_url_list = [main_image_url],   # ← consistency anchor
    size = "1024x1024"
)
```

### Rule 3 — Consistent Appearance

Beyond the technical reference, the prompt itself must contain the explicit consistency clause:

```
"Match product color, material, and details from reference image exactly"
```

This is the prompt-level instruction that complements the visual reference. The two layers (visual reference + explicit prompt clause) together prevent appearance drift.

### Rule 4 — Unified Style

Beyond product appearance, the *style* of each image (background, color palette, fonts, icons) must read as one coherent design system across the suite. When 15 images appear together on the Amazon detail page, any style inconsistency immediately breaks the brand impression.

| Style dimension | Rule |
|---|---|
| Background style | Unified — same kind of background (clean, gradient, scene) across the suite |
| Color palette | Unified — same primary + accent colors |
| Font family | Unified — one headline font + one body font across all in-image text |
| Icon style | Unified — same iconography style (line-art, filled, flat, etc.) |

## Conversion Rate Reference Data

5 benchmark data points from Amazon A/B testing. These are the *why* behind the secondary-image-type bundles — they tell the skill which optimizations actually move conversion.

| Optimization | Conversion Rate Lift | Source |
|---|---|---|
| Lifestyle images | +18% | Amazon A/B test |
| Infographics | +8% | Amazon A/B test |
| Detail close-ups | +6% | Amazon A/B test |
| 7 images vs 4 images | +32% | Amazon official data |
| Optimized image suite | Up to +30% interaction rate | Industry average |

### How to apply this data

- **Always include lifestyle images** when scope ⊇ secondary — the +18% lift is the highest single-type return.
- **Aim for 7+ image suite** — the +32% lift from 7 vs 4 is the largest delta in the table.
- **Infographic + detail are the next two priorities** after lifestyle.
- **Combined "optimized suite" hits +30% interaction rate** — the compounding effect of all four optimizations together.

The category → secondary-type mapping (`secondary-images.md` §Section C) is calibrated to apply these conversion levers per category — every bundle includes at least lifestyle / infographic / detail in some combination.

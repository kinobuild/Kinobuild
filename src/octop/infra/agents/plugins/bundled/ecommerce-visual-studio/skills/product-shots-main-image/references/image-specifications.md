---
name: image-specifications
description: Image Specifications for Amazon main image and secondary images — dimensions, aspect ratios, file formats, color space, and mobile-readability text floor. Provides the per-image-type technical parameters loaded at EP Step 2 (main image) and EP Step 3 (secondary images) to set canonical sizes.
---

# Image Specifications — Main + Secondary

Canonical technical parameters for the main image and 7 secondary image types. These specs are sourced from Amazon's official image requirements and are non-negotiable — wrong sizes or aspect ratios cause platform-side cropping or rejection.

For A+ Content module specs (Hero Banner 21:9, standard modules 3:2, mobile safe area), see the `product-shots-detail-page` skill.

## Execution Procedure

```
get_specs(image_type) → {min_size, recommended_size, aspect_ratio, file_format, color_space}

# Main image / Secondary image
if image_type ∈ {main, secondary}:
    return {min: 1000×1000, recommended: 1024×1024, aspect: "1:1", format: "JPG", color: "sRGB"}

# Mobile readability floor
assert all in-image text size ≥ 30pt    # 36pt recommended for headline
```

## TOC

- [General technical parameters](#general-technical-parameters)
- [Main image / Secondary image specs](#main-image--secondary-image-specs)
- [Required floors](#required-floors)

## General technical parameters

| Parameter | Minimum | Recommended | Notes |
|---|---|---|---|
| Minimum size | 1000×1000 px | 1024×1024 px | Below 1000×1000 cannot zoom |
| Mobile text size | ≥30pt | ≥36pt | Smaller than 30pt is unreadable on phones |
| Standard aspect | 1:1 | 1:1 | Main and secondary images |
| File format | JPG / PNG | JPG | PNG only when transparent background is required |
| Color space | sRGB | sRGB | Other color spaces display incorrectly on Amazon |

## Main image / Secondary image specs

| Image Type | Aspect Ratio | Recommended Size | Count | Core Requirement |
|---|---|---|---|---|
| Main image | 1:1 | 1024×1024 | 1 | All `<main_image_rules>` (see hard-constraints.md) |
| Infographic | 1:1 | 1024×1024 | 1-2 | 4-6 selling points, annotation lines pointing to features, text ≥30pt |
| Multi-angle | 1:1 | 1024×1024 | 2 | Consistent lighting, clean background |
| Detail Shot | 1:1 | 1024×1024 | 1 | Macro photography emphasizing material / craftsmanship |
| Lifestyle | 1:1 | 1024×1024 | 2 | Target user + real scenario |
| Variants | 1:1 | 1024×1024 | 1 | All colors / styles arranged uniformly |
| What's in Box | 1:1 | 1024×1024 | 1 | All accessories shown clearly |
| Size Reference | 1:1 | 1024×1024 | 1 | Use a common reference object for scale |

### Required floors

| Floor | Value | Why |
|---|---|---|
| Min image dimension | 1000×1000 px | Below this, Amazon's zoom feature fails |
| Min in-image text | 30pt | Below this, unreadable on phones (where most browsing happens) |
| Headline text (recommended) | ≥36pt | First-glance readability at thumbnail size |
| Color space | sRGB | Anything else displays with color drift on Amazon's pipeline |
| Aspect ratio (main/secondary) | exactly 1:1 | Amazon's grid layout expects 1:1 — non-square images get center-cropped |

## Cross-skill note

A+ Content modules use different aspect ratios (21:9 for Hero Banner and Endorsement; 3:2 for the 6 standard modules) and have mobile safe-area constraints. Those specs live in the `product-shots-detail-page` skill — `references/aplus-specifications.md`.

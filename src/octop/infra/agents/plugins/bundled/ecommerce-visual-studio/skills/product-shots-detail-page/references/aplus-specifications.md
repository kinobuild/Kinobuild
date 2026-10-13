---
name: aplus-specifications
description: Image Specifications for Amazon A+ Content modules — Hero Banner (21:9 / 2388×1024), 6 standard modules (3:2 / 1536×1024), Endorsement (21:9), mobile safe-area rule, and mobile-readability text floor. Loaded at EP Step 2 to set canonical sizes for each A+ module generation call.
---

# Image Specifications — A+ Content Modules

Canonical technical parameters for the 8 A+ Content modules. These specs are sourced from Amazon's official A+ Content requirements and are non-negotiable — wrong aspect ratios or off-safe-area critical content cause platform-side cropping on mobile clients.

For main image and secondary image (1:1 / 1024×1024) specs, see the `product-shots-main-image` skill.

## Execution Procedure

```
get_aplus_specs(module) → {size, aspect_ratio, safe_area, color_space}

# A+ Hero Banner / A+ Endorsement
if module ∈ {hero_banner, endorsement}:
    return {size: 2388×1024, aspect: "21:9", safe_area: "outer 5%", color: "sRGB"}

# A+ Standard Module
if module ∈ {pain_points, selling_points, technology,
              data, how_to_use, variants}:
    return {size: 1536×1024, aspect: "3:2", safe_area: "outer 5%", color: "sRGB"}

# Mobile readability floor
assert all in-image text size ≥ 30pt    # 36pt recommended for headline
```

## TOC

- [General technical parameters](#general-technical-parameters)
- [A+ Page module specs](#a-page-module-specs)
- [Mobile safe-area rule](#mobile-safe-area-rule)
- [Required floors](#required-floors)

## General technical parameters

| Parameter | Minimum | Recommended | Notes |
|---|---|---|---|
| Mobile text size | ≥30pt | ≥36pt | Smaller than 30pt is unreadable on phones |
| File format | JPG / PNG | JPG | PNG only when transparent background is required |
| Color space | sRGB | sRGB | Other color spaces display incorrectly on Amazon |

## A+ Page module specs

| Module | Aspect | Exact Size | Safe Area | Purpose |
|---|---|---|---|---|
| Module 1: Hero Banner | 21:9 | 2388×1024 | outer 5% | Brand banner |
| Module 2: Pain Points | 3:2 | 1536×1024 | outer 5% | Pain points / scenarios |
| Module 3: Selling Points | 3:2 | 1536×1024 | outer 5% | Selling-point matrix |
| Module 4: Technology | 3:2 | 1536×1024 | outer 5% | Core ingredients / technology |
| Module 5: Data | 3:2 | 1536×1024 | outer 5% | Efficacy data / comparisons |
| Module 6: How to Use | 3:2 | 1536×1024 | outer 5% | Usage instructions |
| Module 7: Variants | 3:2 | 1536×1024 | outer 5% | Multi-variant / family shot |
| Module 8: Endorsement | 21:9 | 2388×1024 | outer 5% | Brand endorsement / certifications |

## Mobile safe-area rule

Amazon mobile clients clip the outer 5% of every A+ image. Critical content (headline text, product silhouette, CTA) MUST live inside the inner 90% safe area:

- 21:9 banner (2388×1024) → safe area ~2269×973 centered
- 3:2 module (1536×1024) → safe area ~1459×973 centered

Place decorative bleed (background gradients, peripheral patterns) in the outer 5% — anything that gets clipped on mobile must be visually expendable.

### Required floors

| Floor | Value | Why |
|---|---|---|
| Min in-image text | 30pt | Below this, unreadable on phones (where most browsing happens) |
| Headline text (recommended) | ≥36pt | First-glance readability at thumbnail size |
| Color space | sRGB | Anything else displays with color drift on Amazon's pipeline |
| Hero Banner aspect | exactly 21:9 (2388×1024) | A+ template expects this aspect — non-conforming images get center-cropped |
| Standard module aspect | exactly 3:2 (1536×1024) | Same template expectation as above |

## Cross-skill note

The main image (1:1 / 1024×1024) and secondary images on the Amazon detail page carousel live under the `product-shots-main-image` skill — `references/image-specifications.md`. Every A+ module references the main image URL as its consistency anchor (see `consistency-rules.md`).

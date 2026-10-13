---
name: aplus-modules
description: A+ Page Modules — the 8 modules of an Amazon Brand Content (A+) page with aspect ratio, exact size, safe-area, and per-module purpose. Loaded at EP Step 4 to compose each module's prompt and to size each generated image correctly.
---

# A+ Page Modules

Amazon A+ Content (formerly Enhanced Brand Content) is a brand-registered seller's expanded product page — 8 visual modules below the standard detail page. Unlike the main + secondary images (1:1 / 1024×1024), A+ modules use 21:9 banners and 3:2 standard modules. Every module clips its outer 5% on mobile, so safe-area discipline is mandatory.

## Execution Procedure

```
generate_aplus_suite(main_image_url, brand_assets) → 8 module images

modules = [
    Hero_Banner,     # 21:9 / 2388×1024 / brand horizontal banner
    Pain_Points,     # 3:2 / 1536×1024 / pain-point or scenario
    Selling_Points,  # 3:2 / 1536×1024 / selling-point matrix
    Technology,      # 3:2 / 1536×1024 / core ingredients / technology
    Data,            # 3:2 / 1536×1024 / efficacy data / comparisons
    How_to_Use,      # 3:2 / 1536×1024 / usage instructions
    Variants,        # 3:2 / 1536×1024 / multi-variant / family shot
    Endorsement      # 21:9 / 2388×1024 / brand endorsement / certifications
]

compose_aplus_prompt(module, reference_image, consistency_clause, safe_area) → prompt_text
    # Look up the module's purpose / layout from §Per-module purpose
    # Inject reference_image as visual anchor for product appearance fidelity
    # Inject consistency_clause and safe_area into the prompt body
    # Return composed prompt text ready for image generation

for module in modules:
    aspect = "21:9" if module ∈ {Hero_Banner, Endorsement} else "3:2"
    size   = "2388x1024" if aspect == "21:9" else "1536x1024"
    prompt = compose_aplus_prompt(
        module,
        reference_image = main_image_url,
        consistency_clause = "Match product color, material, and details from reference image exactly",
        safe_area = "All critical content must sit inside the inner 90% (mobile clips outer 5%)"
    )
    image = generate(prompt, image_url_list=[main_image_url], size=size, ratio=aspect)

# Self-check
assert all critical content inside the safe area on every module
assert visual style + color palette + typography unified across all 8 modules
```

## TOC

- [The 8 modules — spec table](#the-8-modules--spec-table)
- [Per-module purpose](#per-module-purpose)
- [Mobile safe area](#mobile-safe-area)
- [Cross-module consistency](#cross-module-consistency)

## The 8 modules — spec table

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

## Per-module purpose

### Module 1: Hero Banner (21:9)

The first module the buyer sees when scrolling into A+ Content. Functions as a brand identity statement — sets the visual tone for all 7 modules below. Typically combines a brand-context shot of the product with the brand name / tagline.

### Module 2: Pain Points (3:2)

Shows the pain point or "before" scenario the product solves. Sets up the emotional hook for the selling points that follow.

### Module 3: Selling Points (3:2)

The selling-point matrix. Usually 3-4 selling points laid out in a grid or row, each with an icon + headline + 1-line body.

### Module 4: Technology (3:2)

Spotlight on the core ingredient, technology, or differentiator. For beauty: hero ingredient. For electronics: chipset / patented mechanism. For supplements: active compound.

### Module 5: Data (3:2)

Efficacy / comparison data. Bar charts, percentages, vs-competitor comparisons. The proof layer.

### Module 6: How to Use (3:2)

Step-by-step usage instructions. 3-5 numbered steps with simple iconography.

### Module 7: Variants (3:2)

The product family — all SKUs / colors / sizes in one shot. Helps buyers see the full range and consider upsell variants.

### Module 8: Endorsement (21:9)

The closing module. Brand certifications, awards, lab results, third-party endorsements. Functions as a trust-anchor before the buyer leaves the A+ section.

## Mobile safe area

Amazon mobile clients clip the outer 5% of every A+ image. **Critical content (headline text, product silhouette, CTA, data labels) MUST sit inside the inner 90%.**

| Module aspect | Total size | Safe area (inner 90%) |
|---|---|---|
| 21:9 | 2388×1024 | ~2269×973 centered |
| 3:2 | 1536×1024 | ~1459×973 centered |

Decorative bleed (background gradients, peripheral patterns, accent shapes) goes in the outer 5% — anything that gets clipped on mobile must be visually expendable.

## Cross-module consistency

The 8 modules read as a single brand experience, not 8 disconnected images. Maintain consistency across:

- **Color palette** — same primary + accent colors across all 8 modules
- **Typography** — same font family for headline + body, consistent weights
- **Product appearance** — color, material, details match the main image exactly (use main image URL as `reference_image_urls` on every module's generation call)
- **Lighting direction** — same light source side across all product shots (main + secondary + A+)
- **Background style** — unified — if modules use a background gradient, use the same gradient family on all of them

Use the main image as the visual anchor: every A+ module's prompt should include the main image URL as `reference_image_urls` and the consistency clause `"Match product color, material, and details from reference image exactly"`.

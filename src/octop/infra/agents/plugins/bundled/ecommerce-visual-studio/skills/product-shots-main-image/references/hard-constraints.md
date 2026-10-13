---
name: hard-constraints
description: Main Image Guidelines (Mandatory Requirements) — the 9 rules that govern Amazon main image generation, packaged as an XML <main_image_rules> block (Must Comply / Absolutely Prohibited / Apparel Specific Rules). Loaded by the parent skill's Execution Procedure Step 0 and re-validated at the Self-Check Gate. Violation = Amazon delisting or review rejection.
---

# Hard Constraints — Main Image Mandatory Requirements

These rules are MUST-level. The Amazon main image is the single non-negotiable deliverable in any image suite — failure to comply means the listing is delisted or fails review. Read at EP Step 0 and re-validate at the Self-Check Gate before delivering any output.

## Execution Procedure

```
def compose_main_image_prompt(product, background, composition, lighting, prohibited, apparel_special) → prompt_text:
    # Assemble a prompt that bakes in every <main_image_rules> requirement:
    #   background = "Pure white RGB(255,255,255), no gradients or shadows"
    #   composition = "Product centered, filling ≥85% of frame"
    #   lighting = "Even, professional studio lighting"
    #   prohibited = "No text, no logos, no watermarks, no decorative elements"
    #   apparel_special (apparel only) = "Real model standing pose OR flat lay; NO mannequin"
    # Return prompt_text — must pass enforce_main_image_rules() below.

enforce_main_image_rules(prompt_text, output_image, product_category) → pass | findings[]

# Background
assert prompt_text mentions "Pure white RGB(255,255,255)" or equivalent strict white
assert no "gradient" / "shadow" / "colored background" / "textured background" in prompt

# Product ratio
assert prompt_text instructs "product fills ≥85% of frame" or equivalent

# Content type
assert no "illustration" / "rendered" / "3D render" in prompt (real photo only)
assert no "model" / "person" in prompt UNLESS product_category == apparel

# Lighting + composition
assert prompt_text instructs "even, professional studio lighting"
assert prompt_text instructs "product centered"

# Absolutely Prohibited (text overlay, branding, decoration)
for each banned_element in [text, label, description, logo, brand_mark,
                            watermark, border, color_block, decorative_graphic,
                            illustration_addon, misleading_accessory, packaging]:
    assert banned_element NOT in prompt_text

# Apparel Specific
if product_category == apparel:
    assert "real model standing pose" OR "flat lay" in prompt
    assert "mannequin" NOT in prompt
    assert "hanger" NOT in prompt

emit findings if any assert fails
```

## TOC

- [`<main_image_rules>` — XML block (Must Comply / Absolutely Prohibited / Apparel Specific)](#main_image_rules--xml-block)
- [Rule-by-rule judgment table (9 mandatory rules)](#rule-by-rule-judgment-table-9-mandatory-rules)
- [Why these are MUST-level — Amazon platform consequences](#why-these-are-must-level)

## `<main_image_rules>` — XML block

```
<main_image_rules>
  Must Comply:
    • Background: Pure white RGB(255,255,255), no gradients, no shadows, no colored backgrounds
    • Product ratio: Product must fill ≥85% of the frame
    • Content type: Real product photo only — no illustrations, no rendered images, no models (apparel excepted)
    • Lighting: Even, professional studio lighting; no harsh shadows
    • Composition: Product perfectly centered

  Absolutely Prohibited:
    • Any text, labels, or descriptions
    • Brand logos or identification marks
    • Watermarks, borders, color blocks
    • Decorative graphics, illustrations, props
    • Misleading accessories or packaging that aren't part of the product

  Apparel Specific Rules:
    • Allowed: Real models in standing pose, OR flat lay
    • Prohibited: Mannequins, hangers
</main_image_rules>
```

## Rule-by-rule judgment table (9 mandatory rules)

| # | Rule Category | Threshold / Specification | Violation Consequence |
|---|---|---|---|
| 1 | Background | Pure white RGB(255,255,255), no exceptions | Immediate delisting |
| 2 | Product ratio | Product fills ≥85% of frame | Review rejection |
| 3 | Content type | Real product photo only — no illustrations, no rendered images, no models (apparel excepted) | Immediate delisting |
| 4 | Lighting | Even, professional studio lighting; no harsh / cluttered shadows | Review rejection |
| 5 | Composition | Product perfectly centered | Review rejection |
| 6 | Text overlay | Zero tolerance — no text, labels, or descriptions | Immediate delisting |
| 7 | Brand identity | No logos, brand marks, or identification | Immediate delisting |
| 8 | Decorative elements | No watermarks, borders, color blocks, decorative graphics | Immediate delisting |
| 9 | Apparel specific | Real model (standing pose) OR flat lay only — no mannequins, no hangers | Immediate delisting |

### Critical thresholds

- **Background**: `#FFFFFF` / RGB(255, 255, 255) — strict pure white, no gradients, no shadows
- **Product ratio**: `≥85%` of frame
- **Text overlay tolerance**: `0` — absolutely prohibited
- **Apparel models**: Standing pose only

## Why these are MUST-level

- **Wrong background → immediate delisting**. Amazon's automated detection flags non-white backgrounds within hours of upload.
- **Product ratio < 85% → review rejection**. Listings are blocked from going live until corrected.
- **Text / logo / watermark in main image → immediate delisting**. Amazon treats this as rule-circumvention and removes the listing.
- **Mannequin in apparel main image → immediate delisting**. Amazon's apparel-category review rejects mannequin images on first scan.
- **Misleading accessories → immediate delisting**. Showing items not included in the product is a violation of accuracy requirements.

These are not "best practices" — they are platform rules whose violation breaks the listing. The skill enforces them by injecting them directly into the image-generation prompt and re-validating the output before the user sees it.

---
name: composition-patterns
description: Section 10 (Composition Patterns — Shared Pattern Library, 12 patterns). Description / best-for / key-element-position / industry adaptation / objective adaptation per pattern, plus the composition-selection decision tree (5 rules) used in workflow Step 4.
---

# Composition Patterns — Shared Pattern Library

12 composition patterns with industry × objective adaptation tags. The pattern is selected at workflow Step 4 by the decision tree in Section 10.2. Patterns are shared across creative skills (Composition Pattern Library is a cross-skill abstraction in this collection).

## Execution Procedure

```
def classify(visual_assets) → classified_assets
    # Inspect the brief.visual_assets payload and derive the boolean asset signals
    # consumed by select_composition_pattern's decision tree:
    #   has_product_photo / has_person_photo / has_logo_only / has_any_photo
    #   has_discount / is_app_or_software / product_count
    # Falls back to has_none=True when the user supplied nothing.
    # Returns a structured object the rest of Step 4 can read directly.

select_composition_pattern(industry, ad_objective, visual_assets) → pattern

# Decision tree priority (first match wins):
# 1. promotion_conversion + has_discount → discount_dominant
# 2. has_person_photo → face_with_product or face_forward
# 3. product_only → product_hero / device_mockup / lifestyle_in_context / flat_lay (industry-driven)
# 4. no_assets → bold_typography / carousel_narrative (objective-driven)
# 5. fitness/beauty + promotion_conversion → before_after
# default: product_hero
```

## TOC

- [Section 10.1 — 12 Composition Patterns](#section-101--12-composition-patterns)
- [Section 10.2 — Pattern Selection Logic](#section-102--pattern-selection-logic)

## Section 10.1 — 12 Composition Patterns

| Pattern | Description | Best For | Key Element Position | Industry Fit | Objective Fit |
|---|---|---|---|---|---|
| **Product Hero** | Product centered, clean / scene background, dramatic light | Tech, E-commerce, product launches | Product in center 50%, blurred or solid background | Tech, E-commerce | Brand awareness, Promotion |
| **Lifestyle In-Context** | Product used in a real, aspirational life scene | Beauty, Fashion, Food, Real Estate | Product in 1/3 of the scene, environment in 2/3 | Beauty, Fashion, Food | Brand awareness |
| **Face-Forward** | Person looks into the camera; product secondary | Testimonials, personal brand, education | Face in top 1/3, eyes on the golden ratio line | Education, Personal brand | Lead generation, Engagement |
| **Face-with-Product** | Person holds / uses the product; both visible | E-commerce, Beauty, Fitness | Face in left/right 1/3, product on the opposite side | Beauty, E-commerce, Fitness | Promotion, App download |
| **Before / After** | Split-screen composition showing a transformation | Fitness, Beauty, home renovation, SaaS | Vertical or horizontal split, arrow / vs marker | Fitness, Beauty, SaaS | Promotion, Lead generation |
| **Social Proof** | Reviews, star ratings, testimonial quotes, "as seen in" | E-commerce, SaaS, App download | Rating in top 1/4, quote in bottom 1/2 | E-commerce, SaaS | Promotion, Lead generation |
| **Discount Dominant** | Massive discount number as primary visual, product secondary | Promotion / sale, E-commerce | Discount number occupies 40-50% of canvas, in top 1/3 | E-commerce, Retail | Promotion (required) |
| **Flat Lay / Overhead** | Products arranged from above, editorial style | Beauty, Food, Lifestyle, multi-product | Overhead 90°, symmetric or asymmetric grid | Beauty, Food | Brand awareness, Promotion |
| **Device Mockup** | App/website shown inside a phone/laptop frame | SaaS, App download, Tech | Device centered, screen content clearly legible | SaaS, Tech | App download, Lead generation |
| **Carousel Narrative** | Multi-card story sequence (problem → solution → proof → CTA) | Education, SaaS, brand storytelling | One focal point per card, progressive info | Education, SaaS | Lead generation, Engagement |
| **Bold Typography** | Text as the main visual element, minimal imagery | Brand awareness, quotes, announcements | Text occupies 60-80% of canvas, high-contrast background | All industries | Brand awareness, Engagement |
| **Comparison / VS** | Two options side by side with a clear winner | Tech reviews, SaaS comparison, A/B | Vertical split with the winner side visually emphasized | Tech, SaaS | Promotion, Lead generation |

## Section 10.2 — Pattern Selection Logic

```python
def select_composition_pattern(industry, ad_objective, visual_assets):
    """
    Pick a composition pattern from industry, objective, and available assets.
    """

    # Rule 1: promotion/conversion + has discount → force Discount Dominant
    if ad_objective == "promotion_conversion" and visual_assets.has_discount:
        return "discount_dominant"

    # Rule 2: has a person photo → prefer face-driven composition
    if visual_assets.has_person_photo:
        if visual_assets.has_product_photo:
            return "face_with_product"
        else:
            return "face_forward"

    # Rule 3: product photo only → choose by industry
    if visual_assets.has_product_photo and not visual_assets.has_person_photo:
        if industry in ["tech", "saas"]:
            if visual_assets.is_app_or_software:
                return "device_mockup"
            else:
                return "product_hero"
        elif industry in ["beauty", "food"]:
            if visual_assets.product_count > 1:
                return "flat_lay_overhead"
            else:
                return "lifestyle_in_context"

    # Rule 4: no assets → choose by objective
    if not visual_assets.has_any_photo:
        if ad_objective == "brand_awareness":
            return "bold_typography"
        elif ad_objective == "lead_generation":
            return "carousel_narrative"

    # Rule 5: fitness/beauty + conversion objective → Before/After
    if industry in ["fitness", "beauty"] and ad_objective == "promotion_conversion":
        return "before_after"

    # Default
    return "product_hero"
```

The per-pattern industry / objective bindings live in the "Industry Fit" and "Objective Fit" columns of §Section 10.1. Any (industry × ad_objective × asset) triple resolves to a single pattern via the decision tree above; per-(industry × format) preferences then compose with the platform format constraints in `references/hard-constraints.md §Platform Dimensions`.

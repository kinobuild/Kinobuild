---
name: secondary-images
description: Secondary Image Types and Uses (7 types) + Secondary Image Design Principles + product-category → secondary-type mapping. Loaded at EP Step 3 to choose which secondary types to generate based on product category, then to compose each type's prompt.
---

# Secondary Images — Types, Principles, Category Mapping

The 6-7 secondary images that accompany the main image on the Amazon detail page. Unlike the main image (which is rule-locked), secondary images are conversion-rate-tuned: lifestyle imagery alone adds +18% conversion, infographics add +8%, and 7 secondary images vs 4 adds +32%. The right *type mix* depends on the product category.

## Execution Procedure

```
plan_secondary_images(product_description, main_image_url) → image_specs[]

match_category(product_description) → category_id
    # see §Section C — Category → Secondary Type Mapping
    # match by signal: product_description keywords → 1 of {electronics, apparel, home_goods, beauty, food}
    # when ambiguous, choose closest match per §Section C closing note

category_to_secondary_types(category_id) → secondary_type_list
    # see §Section C — Category → Secondary Type Mapping table
    # lookup category_id → its calibrated 4-type bundle
    # bundle is conversion-rate-tuned per Amazon A/B test data (see §Section A lifts)

# Step 1 — Identify product category
category = match_category(product_description)
    candidates: electronics / apparel / home_goods / beauty / food

# Step 2 — Get the canonical type list for that category
types = category_to_secondary_types(category)   # see §Category → Secondary Type Mapping

# Step 3 — Compose each prompt with consistency anchor
for type in types:
    prompt = compose_secondary_prompt(
        type,
        product_description = ...,
        reference_image = main_image_url,
        consistency_clause = "Match product color, material, and details from reference image exactly"
    )
    yield {type, prompt, size: "1024x1024", aspect: "1:1", reference_image: main_image_url}

def compose_secondary_prompt(type, product_description, reference_image, consistency_clause) → prompt_text:
    # Look up the type's layout / text / style spec from §Section A
    # Inject reference_image as visual anchor and consistency_clause as prompt clause
    # Return the composed prompt text ready for image generation

# Step 4 — General principles applied to all secondary images
assert all in-image text ≥ 30pt
assert background style consistent with main image
assert lighting direction consistent with main image
```

## TOC

- [Section A — 7 Secondary Image Types](#section-a--7-secondary-image-types)
- [Section B — Secondary Image Design Principles](#section-b--secondary-image-design-principles)
  - [General Principles](#general-principles)
  - [Infographic Design Essentials](#infographic-design-essentials)
- [Section C — Category → Secondary Type Mapping](#section-c--category--secondary-type-mapping)

## Section A — 7 Secondary Image Types

### 1. Infographic

- **Purpose**: Communicate 4-6 selling points with visual hierarchy.
- **Layout**: Product on left side (sourced from main image), 4-6 feature callouts on right, annotation lines / arrows pointing to specific product features.
- **Text**: Min 30pt; bold, sans-serif, high contrast.
- **Visual style**: Clean, modern, high contrast; icons to enhance hierarchy.
- **Conversion lift**: +8% (Amazon A/B test).

### 2. Multi-angle

- **Purpose**: Show the product from front / back / side / top so the buyer can fully understand its 3D form.
- **Layout**: 2 angle shots in one composition (or 2 separate images).
- **Constraint**: Lighting direction consistent across all angles; background unified.

### 3. Detail Shot

- **Purpose**: Macro view showing material, texture, craftsmanship.
- **Layout**: Single subject, tight crop on a key detail (stitching, finish, etc.).
- **Conversion lift**: +6% (Amazon A/B test).

### 4. Lifestyle

- **Purpose**: Show the product in real-world use by the target user.
- **Layout**: Target persona + product in a real environment (home, office, outdoors, etc.).
- **Constraint**: 2 images; show different use scenarios.
- **Conversion lift**: +18% (Amazon A/B test) — the highest single-type lift.

### 5. Variants

- **Purpose**: Show all available colors / styles / SKUs in one composition.
- **Layout**: All variants arranged uniformly (grid or row), consistent lighting and angle.

### 6. What's in Box

- **Purpose**: Show every accessory included with the product.
- **Layout**: Flat-lay with all components clearly visible and labeled by position.

### 7. Size Reference

- **Purpose**: Help the buyer understand the product's actual size.
- **Layout**: Product next to a common-knowledge reference object (hand, coin, household item).

## Section B — Secondary Image Design Principles

### General Principles

1. **Consistency with main image**. Every secondary image references the main image URL as the visual baseline — product color, material, and details must match exactly. Background style, lighting direction, and color palette stay unified across the suite.
2. **Conversion-rate-tuned mix**. The category-specific type bundles (Section C) are chosen to maximize conversion based on Amazon A/B testing data: lifestyle for emotional connection, infographic for utility, detail for quality reassurance.
3. **Mobile-readable text**. Any in-image text uses ≥30pt, bold, sans-serif, high contrast. Anything below 30pt is illegible on phone screens where most browsing happens.
4. **Same aspect / size as main**. All secondary images are 1:1 / 1024×1024 — same as main — so they tile cleanly in the Amazon detail-page carousel.

### Infographic Design Essentials

The infographic is the highest-density secondary image. It carries the most product information per square inch, so its layout discipline matters most.

| Element | Specification |
|---|---|
| Selling points | 4-6 (more = visual clutter; less = under-utilized) |
| Layout | Product on left, callouts on right |
| Annotation lines | Solid or arrow lines pointing from text → specific product feature |
| Text font | Bold sans-serif, ≥30pt body, ≥36pt headline |
| Icons | Optional — used to anchor each callout visually |
| Color scheme | Match brand colors if available; otherwise high-contrast neutral |
| Consistency | Product appearance (color, material, details) must match main image exactly |

## Section C — Category → Secondary Type Mapping

| Product Category | Secondary Image Type Bundle |
|---|---|
| Electronics | Infographic (functions) + Multi-angle + Detail Shot + Size Reference |
| Apparel / Footwear | Multi-angle + Detail Shot (material) + Lifestyle + Variants |
| Home Goods | Lifestyle + Size Reference + What's in Box + Infographic |
| Beauty / Personal Care | Infographic (ingredients) + Detail Shot (texture) + Lifestyle + Variants |
| Food / Supplements | Infographic (nutrition) + What's in Box + Lifestyle + Detail Shot |

Each bundle is calibrated to the category's buying-decision pattern:

- **Electronics buyers** want function spec + form factor + size → infographic + multi-angle + size reference.
- **Apparel buyers** want fit, material, lived-in look, and color options → multi-angle + detail + lifestyle + variants.
- **Home goods buyers** want spatial fit, what's included, scale → lifestyle + size + what's in box + infographic.
- **Beauty buyers** want ingredients, texture, in-use, and shade options → infographic + detail + lifestyle + variants.
- **Food / supplement buyers** want nutrition, package contents, in-use, and product detail → infographic + what's in box + lifestyle + detail.

When the user's product doesn't fit cleanly into one category, choose the closest match and adjust per the user's request.

---
name: ad-objective-rules
description: Section 8 (Ad Objective Rules — Objective Determines Information Hierarchy). The objective × visual focus × info hierarchy × CTA intensity × text density × best formats × judgment weight matrix. Drives Step 4 (Composition + Color) and is re-validated at Step 6 Check 10 (ad_objective_reflected). Includes the strictest objective: Promotion / Conversion (4 mandatory rules).
---

# Ad Objective Rules — Objective Determines Information Hierarchy

The ad objective is the most important driver of visual hierarchy. Brand Awareness wants emotion-first; Promotion wants discount-dominant; Lead Gen wants trust signals; App Download wants device mockup; Engagement wants conversation triggers. The same product, same industry, same platform produces five very different creatives across these five objectives.

## Execution Procedure

```
apply_objective_rules(creative, ad_objective) → pass | findings[]

# Step 4 — drive composition + hierarchy
hierarchy = OBJECTIVE_RULES[ad_objective].info_hierarchy
cta_intensity = OBJECTIVE_RULES[ad_objective].cta_intensity
text_density = OBJECTIVE_RULES[ad_objective].text_density

# Step 6 — Check 10
if ad_objective == "promotion_conversion":
    assert validate_promotion_ad(creative, ad_objective)   # 4 mandatory rules below
elif ad_objective == "brand_awareness":
    assert has_prominent_brand_element(creative)
elif ad_objective == "lead_generation":
    assert has_trust_signal(creative)
elif ad_objective == "app_download":
    assert has_device_mockup(creative) or has_rating(creative)
```

## TOC

- [Section 8.1 — Objective × Visual Hierarchy Matrix](#section-81--objective--visual-hierarchy-matrix)
- [Section 8.2 — Promotion / Conversion: Strictest Rules](#section-82--promotion--conversion-strictest-rules)

## Section 8.1 — Objective × Visual Hierarchy Matrix

| Objective | Visual Focus | Info Hierarchy | CTA Intensity | Text Density | Best Formats | Validation Weight |
|---|---|---|---|---|---|---|
| **Brand Awareness** | Brand world, lifestyle, emotion | Brand → emotion → soft CTA | Low: "Learn more", "Discover" | Minimal: brand name + slogan | Video, Carousel story, IG Story | `brand_prominence = 0.8` |
| **Promotion / Conversion** | Product + offer (discount %, limited time) | Offer → product → CTA → brand | High: "Shop now", "Get 50% off" | Medium: discount number dominates | Single image, Product carousel | `discount_size = 0.5` (50% of canvas) |
| **Lead Generation** | Value prop + trust signal | Benefit → social proof → CTA | Mid: "Get free guide", "Sign up" | Medium: headline + proof points | Image + form preview, Carousel | `social_proof_required = True` |
| **App Download** | App UI in a device mockup + rating | App value → UI → social proof → CTA | High: "Download free", "Try now" | Medium: name + value prop + rating | Single image, Feature video | `rating_display = True` |
| **Engagement** | Relatable, shareable, opinion-triggering | Hook → visual → soft CTA | Low: "What do you think?", "Tag a friend" | Low: visual drives the conversation | Poll, Carousel, IG Story sticker | `conversation_trigger = True` |

## Section 8.2 — Promotion / Conversion: Strictest Rules

The promotion/conversion objective has the most rigid constraints. All four rules are MANDATORY — any failure → regenerate.

```python
def validate_promotion_ad(creative, ad_objective):
    if ad_objective != "promotion_conversion":
        return True, "N/A"

    # Rule 1: discount number must be the largest text element on the canvas
    discount_element = find_element_by_type(creative, "discount_number")
    all_text_elements = find_elements_by_type(creative, "text")

    if not discount_element:
        return False, "Promotion ad MUST have visible discount number"

    for text in all_text_elements:
        if text.font_size > discount_element.font_size:
            return False, "Discount number must be the largest text element"

    # Rule 2: discount number must use a contrasting color (red/orange/yellow)
    CONTRAST_COLORS = ["#FF0000", "#FF6600", "#FFD700", "#FF8C00"]
    if discount_element.color not in CONTRAST_COLORS:
        return False, "Discount must use contrasting color (red/orange/yellow)"

    # Rule 3: discount number must sit in the top 1/3 of the canvas
    canvas_height = creative.height
    if discount_element.y_center > canvas_height / 3:
        return False, "Discount number must be in top 1/3 of canvas"

    # Rule 4: must include an urgency cue
    urgency_keywords = ["Today only", "Ends Sunday", "Limited time", "24h only"]
    if not any(keyword in creative.text_content for keyword in urgency_keywords):
        return False, "Promotion ad should include urgency cue"

    return True, "Pass"
```

### Why all four rules together

A "20% off" creative without rule 1 (discount-as-largest-text) reads like a brand ad with a price tag. Without rule 2 (contrasting color) the discount blends in. Without rule 3 (top 1/3) the discount falls below the fold on mobile. Without rule 4 (urgency) the buyer defers the decision. Promotion ads compress the urgency-funnel — every rule contributes to the funnel mechanic. Drop any one and the ad reverts to brand-awareness performance levels.

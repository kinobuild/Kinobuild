---
name: color-and-cta-strategy
description: Section 11 (Color Strategy — Industry-Based Color Guide, with Industry × Color Matrix and Color Rules) and Section 12 (CTA Strategy — Call-to-Action Design Rules). Drives Step 4 (Composition + Color) and Step 5 (Platform Adaptation), and is re-validated at Step 6 Check 6 (industry visual language) and Check 5 (CTA visible / appropriate).
---

# Color Strategy + CTA Strategy

Color and CTA are the two most-coupled-to-objective parameters. Color signals industry tone (warm food, cool tech, luxury black-gold, wellness soft-green). CTA signals ad objective (low-pressure for awareness, high-pressure for conversion). Both are loaded at workflow Step 4 and re-validated at the Self-Check Gate.

## Execution Procedure

```
def pick_color_strategy(industry, brand_kit) → color_strategy
    # Resolve the working color palette for this creative.
    # 1. start from INDUSTRY_COLOR_RULES[industry].primary_palette
    # 2. if brand_kit.colors → override primary palette; industry palette demoted to accent
    # 3. enforce max_colors / forbidden / temperature gates from INDUSTRY_COLOR_RULES[industry]
    # Returns {primary: [...], accent: [...], forbidden: [...], max_colors, temperature}.

def pick_cta_strategy(ad_objective, platform) → cta_strategy
    # 1. cta_intensity = OBJECTIVE_RULES[ad_objective].cta_intensity  (low / mid / high)
    # 2. cta_text      = pick_cta_phrase(ad_objective, industry)       (Section 12.1 / 12.2)
    # 3. in_image_required = lookup §Section 12.3 (platform CTA delivery table)
    # Returns {intensity, text, in_image_required, delivered_by_platform_ui}.

# Step 4 — Color
color_strategy = pick_color_strategy(industry, brief.brand_kit)
assert len(color_strategy.primary) ≤ color_strategy.max_colors  # default 3
assert temperature_consistent(color_strategy.primary, color_strategy.temperature)
assert no color in color_strategy.forbidden

# Step 4 — CTA
cta_strategy = pick_cta_strategy(ad_objective, platform)
if platform in {meta_feed, linkedin}: cta_provided_by_platform = True
                                       # image CTA optional
else: image_cta_required_for(promotion_conversion, app_download)

# Step 6 — Self-Check
re-validate color (Check 6) and CTA (Check 5)
```

## TOC

- [Section 11 — Color Strategy](#section-11--color-strategy)
  - [Section 11.1 — Industry × Color Matrix](#section-111--industry--color-matrix)
  - [Section 11.2 — Color Rules](#section-112--color-rules)
- [Section 12 — CTA Strategy](#section-12--cta-strategy)

## Section 11 — Color Strategy

Industry-based color palette + max 3 colors + temperature consistency + forbidden-color blacklist. The full INDUSTRY_COLOR_RULES dictionary lives in `references/industry-style-rules.md §Section 7.2` (code form) — this section summarizes the validation gates.

### Section 11.1 — Industry × Color Matrix

For the canonical industry × color palette mapping, see `references/industry-style-rules.md §Section 7.1`. Quick navigation:

- **Beauty / Fashion**: Blush / Gold / Cream / Terracotta; luxury = Black + Gold; forbid Neon, Electric blue.
- **Tech / SaaS**: Blue + White / Dark mode + accent / Green for growth; forbid warm earthy tones.
- **Food / Restaurant**: Golden / Orange / Red / Brown / Cream; warm only, forbid cool blues, greys.
- **Fitness**: Black + Neon Green or Orange.
- **Wellness**: Soft Green / Soft Blue + White.
- **Education**: Blue + Orange or Green + White; ≤2 primary colors.
- **Real Estate**: White + Gold (luxury) or Blue + White (trust).
- **E-commerce / DTC**: brand-specific; clean light backgrounds for clarity.
- **Home / Furniture**: Neutrals / Warm wood / Soft whites.

### Section 11.2 — Color Rules

Three universal color rules, applied at the Self-Check Gate (Check 6):

1. **Max colors** — at most 3 colors in the dominant palette (industry default; some industries set lower like Education ≤ 2).
2. **No forbidden color** — no color in the industry's `forbidden` list may appear in the dominant palette.
3. **Temperature consistency** — if the industry temperature is `warm`, no cool color may appear (and vice versa). Mixing temperatures dilutes the industry signal.

Brand Kit overrides supersede industry defaults: when the user's Brand Kit specifies colors, those become the primary palette and the industry colors become accent / supporting only.

```python
def validate_color_scheme(colors, industry):
    rules = INDUSTRY_COLOR_RULES[industry]
    if len(colors) > rules["max_colors"]:
        return False, f"Exceeds max {rules['max_colors']} colors"
    for color in colors:
        if color in rules["forbidden"]:
            return False, f"Color {color} is forbidden for {industry}"
    if rules["temperature"] == "warm":
        if any(is_cool_color(c) for c in colors):
            return False, "Mixing warm and cool colors"
    return True, "Pass"
```

### Promotion-objective color override

The Promotion / Conversion objective adds a fourth rule: the discount number must be in a contrasting color (red / orange / yellow). See `references/ad-objective-rules.md §Section 8.2 — Rule 2`. This may override the industry palette when a discount-dominant pattern is selected (the discount block's color is conversion-tuned, not industry-tuned).

## Section 12 — CTA Strategy

CTA design is driven by ad objective intensity and constrained by platform delivery model.

### Section 12.1 — CTA Intensity by Objective

| Objective | CTA Intensity | Example phrasing |
|---|---|---|
| Brand Awareness | low | "Learn more", "Discover" |
| Promotion / Conversion | high | "Shop now", "Get 50% off", "Buy today" |
| Lead Generation | mid | "Get free guide", "Sign up", "Download whitepaper" |
| App Download | high | "Download free", "Try now", "Get the app" |
| Engagement | low | "What do you think?", "Tag a friend", "Share if you agree" |

(Pulled from `references/ad-objective-rules.md §Section 8.1`.)

### Section 12.2 — CTA Tone by Industry

CTA phrasing also has industry conventions (from `references/industry-style-rules.md §Section 7.1`):

- **Beauty / Fashion**: "Shop the look", aspirational + exclusivity
- **Tech / SaaS**: "Start free trial", "See demo"
- **Food / Restaurant**: "Order now", "Reserve a table"
- **Fitness**: "Start your transformation"
- **Wellness**: "Begin your journey"
- **Education**: "Enroll now", "Get certified"
- **Real Estate**: "Schedule a tour", "View listing"
- **E-commerce / DTC**: "Shop now", "Add to cart"
- **Home / Furniture**: "Shop the collection"

### Section 12.3 — CTA Delivery: Image vs Platform-Provided

Some platforms provide CTA buttons via the platform UI (the image does not need to render a CTA). Some require an in-image CTA. Some allow both.

| Platform | CTA model | In-image CTA required? |
|---|---|---|
| Instagram Feed | Platform-provided button | Optional (recommended for Promotion) |
| Facebook Feed | Platform-provided button | Optional (recommended for Promotion) |
| LinkedIn | Platform-provided button | Optional |
| TikTok | Custom (in-image expected) | Required for Promotion / App Download |
| Google Display | Platform-provided + in-image text-only CTA | NO image button (zero text overlay rule) — CTA via platform UI only |
| Google Demand Gen | Custom + platform-provided | In-image CTA allowed |
| YouTube | Custom (in-image strongly recommended) | Required for Promotion |
| Pinterest | Platform-provided | Optional |
| X / Twitter | Custom | Optional |

### Section 12.4 — CTA Validation (Check 5)

The Self-Check Gate Check 5 (`cta_visible_appropriate`) enforces:

- For platforms where the image CTA is required by objective (Promotion / App Download), the CTA must be present and visible.
- The CTA intensity (low / mid / high) must match the objective.
- The CTA must not sit in a platform-occluded zone (e.g., bottom 20% of Story for the reply box, bottom 35% of Reel for the action rail, right 64px of TikTok for the interaction buttons). See `references/hard-constraints.md §Section 5.2`.

### Section 12.5 — Special Case: Google Display

Google Display **forbids** any text / button / logo overlay on the image (zero tolerance). The CTA is entirely delivered via the platform's CTA field (text-only, automated). When designing for Google Display:

- Do NOT render any CTA button or CTA text on the image.
- Do NOT render the brand name on the image (unless it is native packaging text — see `references/banned-words.md §Required Positive Instruction`).
- The CTA is delivered as ad copy, sized to char limits in `references/hard-constraints.md §Section 5.4`.

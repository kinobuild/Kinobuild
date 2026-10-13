---
name: industry-style-rules
description: Section 7 (Industry Style Rules). Industry × visual parameter matrix — color palette, composition pattern, typography, CTA tone, key forbidden elements, market share. Used in workflow Step 2 (load industry bundle) and Step 6 Check 6 (industry visual language compliance).
---

# Industry Style Rules

The industry × visual parameter matrix. Each industry preset bundles color palette, composition tendency, typography, CTA tone, and forbidden elements. Loaded at workflow Step 2 and re-validated at the Self-Check Gate (Check 6 — industry visual language).

## Execution Procedure

```
match_industry(user_request) → industry_key
    # resolve user_request to one of the INDUSTRY_RULES keys
    # (beauty_fashion / tech_saas / food_restaurant / fitness / wellness /
    #  education / real_estate / ecommerce_dtc / home_furniture)
    # fall back to ecommerce_dtc when ambiguous

load_industry_bundle(industry) → {colors, composition, typography, cta_tone, forbidden, market_share}

def parse_brand_kit(brand_kit) → kit_normalized
    # Accept a file path or inline {colors, fonts, logo}; return a normalized dict
    # {brand_colors: [...], brand_fonts: [...], brand_logo: <path|None>}.
    # Returns None when no brand_kit supplied.

apply_brand_kit_overrides(bundle, kit) → bundle
    # brand colors → primary palette (industry → accent)
    # brand fonts  → headlines (industry → secondary)
    # brand logo   → composed per platform safe-zone rules

# Step 2 — workflow input
bundle = INDUSTRY_RULES[industry]
if user.brand_kit:
    kit = parse_brand_kit(user.brand_kit)
    apply_brand_kit_overrides(bundle, kit)

# Step 6 — Self-Check Gate Check 6
dominant_colors = extract_dominant_colors(creative)
for c in dominant_colors:
    if c in bundle.forbidden_colors: FAIL
detected_pattern = detect_composition_pattern(creative)
if detected_pattern not in bundle.recommended_patterns: WARN
```

## TOC

- [Section 7.1 — Industry × Visual Parameter Matrix](#section-71--industry--visual-parameter-matrix)
- [Section 7.2 — Industry Color Rules (code form)](#section-72--industry-color-rules-code-form)

## Section 7.1 — Industry × Visual Parameter Matrix

| Industry | Color Palette | Composition Pattern | Typography | CTA Tone | Key Forbidden | Market Share |
|---|---|---|---|---|---|---|
| **Beauty / Fashion** | Blush (#F5C6C6), Gold (#D4AF37), Cream (#FFFDD0), Terracotta (#E2725B); luxury: Black + Gold | Model in lifestyle scene; close-up texture; multi-product flat lay | Serif (luxury), Sans-serif (casual), Handwritten (artisan) | "Shop the look", exclusivity | Over-smoothed skin; cluttered products | 22.9% |
| **Tech / SaaS** | Blue (#0066CC) + White (trust), Dark mode (#1A1A1A) (premium), Green (#00C853) + White (growth) | Product hero on clean background; device mockup; comparison split-screen | Geometric Sans-serif (Inter, SF Pro); bold numerals | "Start free trial", "See demo" | Too many features; unclear screenshots | 15.2% |
| **Food / Restaurant** | Golden (#FFD700), Orange (#FF8C00), Red (#DC143C), Brown (#8B4513), Cream; avoid cool blues | Overhead flat lay or 45°; finished dish as hero; warm light | Rounded warm fonts; handwritten/artisan scripts | "Order now", "Reserve a table" | Cool light; text covering the food | 5.1% |
| **Fitness** | Black (#000000) + Neon Green (#39FF14) / Orange (#FF6600) | Dynamic poses; before/after split; action freeze-frames | Bold condensed uppercase | "Start your transformation" | Conflating fitness with wellness | 3.5% (Fitness) |
| **Wellness** | Soft Green (#A8D5BA) + White, Soft Blue (#B3D9FF) | Calm scenes; soft light; natural elements | Light airy fonts | "Begin your journey" | Same energy level as fitness | 3.5% (Health) |
| **Education** | Blue (#0066CC) + Orange (#FF8C00), Green (#00C853) + White; ≤2 primary colors | Instructor face + topic visual; clear info hierarchy; stats spotlighted | Clear Sans-serif; large numerals → headline → supporting text | "Enroll now", "Get certified" | No face = no trust; wall of text | 3.1% |
| **Real Estate** | White + Gold (luxury), Blue (#0066CC) + White (trust) | Wide-angle hero; golden hour (luxury); floor plans (utility) | Elegant Serif (luxury); modern clean (commercial) | "Schedule a tour", "View listing" | Dark interiors; fisheye distortion | 2.3% |
| **E-commerce / DTC** | Brand-specific; white / light backgrounds for clarity | Product hero + lifestyle scene; review/rating overlay; unboxing feel | Modern clean; star rating as trust signal | "Shop now", "Add to cart" | No social proof; price hidden | — |
| **Home / Furniture** | Neutral tones, Warm wood, Soft whites | Interior scene; product in usage environment | Clean modern serif or sans | "Shop the collection" | Product removed from context | 2.9% |

## Section 7.2 — Industry Color Rules (code form)

The industry color matrix encoded for the color-validation pass. `max_colors`, `temperature` (warm / cool), and `forbidden` are enforced at Self-Check Gate Check 6.

```python
INDUSTRY_COLOR_RULES = {
    "beauty_fashion": {
        "primary_palette": ["#F5C6C6", "#D4AF37", "#FFFDD0", "#E2725B"],
        "luxury_variant":  ["#000000", "#D4AF37"],
        "accent":          ["#000000", "#FF6F61"],   # Black (luxury), Coral (playful)
        "forbidden":       ["#00FFFF", "#0066CC"],   # Neon, Electric blue
        "max_colors":      3,
        "temperature":     "warm"
    },
    "tech_saas": {
        "primary_palette": ["#0066CC", "#1A1A1A", "#FFFFFF"],
        "accent":          ["#0099FF", "#00C853"],   # Electric blue, Growth green
        "forbidden":       ["#8B4513", "#E2725B"],   # Warm earthy tones
        "max_colors":      3,
        "temperature":     "cool"
    },
    "food_restaurant": {
        "primary_palette": ["#FFD700", "#FF8C00", "#DC143C", "#FFFDD0"],
        "accent":          ["#00C853", "#8B4513"],   # Fresh green, Artisanal brown
        "forbidden":       ["#0066CC", "#808080"],   # Cool blue, Grey
        "max_colors":      3,
        "temperature":     "warm",
        "lighting":        "warm_natural"
    }
    # ... fitness / wellness / education / real_estate / ecommerce_dtc / home_furniture
    # follow the same shape (palette / accent / forbidden / max_colors / temperature)
}
```

### Validation logic

```python
def validate_color_scheme(colors, industry):
    rules = INDUSTRY_COLOR_RULES[industry]

    # Rule 1: at most 3 colors
    if len(colors) > rules["max_colors"]:
        return False, f"Exceeds max {rules['max_colors']} colors"

    # Rule 2: no forbidden colors
    for color in colors:
        if color in rules["forbidden"]:
            return False, f"Color {color} is forbidden for {industry}"

    # Rule 3: temperature consistency (no warm + cool mix)
    if rules["temperature"] == "warm":
        if any(is_cool_color(c) for c in colors):
            return False, "Mixing warm and cool colors"

    return True, "Pass"
```

### Cross-skill consistency

The Industry Visual DNA encoded above is **shared** with `product-shots-social-post`, `product-shots`, and other downstream creative skills. When the user's industry changes mid-session, all downstream skills must reload from the same matrix.

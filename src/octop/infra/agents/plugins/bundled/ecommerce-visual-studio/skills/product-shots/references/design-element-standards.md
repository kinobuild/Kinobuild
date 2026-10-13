---
name: design-element-standards
description: Design Element Standards. Three sub-sections covering Text Hierarchy (headline / body / cta / font_limit / contrast_rule), Color & Composition (6-3-1 rule, rule_of_thirds, center_hero, depth techniques), and Style Modifiers (minimalist / high_impact prompt additions). These rules complement industry/platform DNA at SKILL.md EP Step 5.
---

# Design Element Standards

Cross-cutting design rules: text hierarchy, color & composition ratios, and named style modifiers. These compose with industry / platform DNA to define final visual language.

## Execution Procedure

```
apply_design_element_standards(brief, style_direction) → brief
style_modifier(style_direction) → prompt_addition_string
    # lookup STYLE_MODIFIERS[style_direction]["prompt_addition"]
    # returns "" when style_direction not in STYLE_MODIFIERS
    # consumed by SKILL.md EP Step 5 (DNA injection)

# Text hierarchy — applied to any in-image text
brief.text_rules = TEXT_HIERARCHY_RULES
    # headline weight / length / position / contrast
    # body weight / length / readability
    # cta prominence / position
    # font_limit: max_fonts = 3
    # contrast_rule: text MUST have high contrast against background

# Color + composition
brief.color_ratio       = "6-3-1"        # 60% background / 30% primary / 10% accent
brief.composition_type  = pick_one(rule_of_thirds, center_hero)
    # rule_of_thirds  → balanced composition
    # center_hero     → product-centric, subject ~60% of frame
brief.depth_techniques  = [natural shadows, depth of field, layered composition]

# Style modifier
if style_direction == "minimalist":
    brief.prompt += STYLE_MODIFIERS["minimalist"]["prompt_addition"]
elif style_direction == "high_impact":
    brief.prompt += STYLE_MODIFIERS["high_impact"]["prompt_addition"]

return brief
```

## TOC

- [Text Hierarchy](#text-hierarchy)
- [Color and Composition](#color-and-composition)
- [Style Modifiers](#style-modifiers)

## Text Hierarchy

```
TEXT_HIERARCHY_RULES = {
    "headline": {
        "weight": "bold",
        "length": "5-10 words",
        "position": "visual center of gravity",
        "contrast_requirement": "high"
    },
    "body": {
        "weight": "secondary",
        "length": "1-2 lines",
        "readability": "high",
        "contrast_requirement": "medium-high"
    },
    "cta": {
        "prominence": "clear and prominent",
        "position": "strategic placement"
    },
    "font_limit": {
        "max_fonts": 3,
        "rule": "Max 2-3 fonts per design"
    },
    "contrast_rule": "Text MUST have high contrast against background"
}
```

## Color and Composition

```
COLOR_COMPOSITION_RULES = {
    "color_ratio": {
        "name": "6-3-1 rule",
        "background": "60%",
        "primary":    "30%",
        "accent":     "10%"
    },
    "composition_types": {
        "rule_of_thirds": {
            "use_case": "balanced composition",
            "description": "Divide frame into 3x3 grid, place key elements at intersections"
        },
        "center_hero": {
            "use_case": "product-centric",
            "subject_coverage": "~60%",
            "description": "Subject occupies center, dominates frame"
        }
    },
    "depth_techniques": [
        "natural shadows",
        "depth of field",
        "layered composition"
    ]
}
```

The 6-3-1 rule maps directly into `negative_space` planning and `accent_color` budget — downstream skills can read these fields from the Brief.

## Style Modifiers

Two named modifiers (composable with industry DNA at Stage 4 default-derivation):

```
STYLE_MODIFIERS = {
    "minimalist": {
        "background":     "single-color",
        "subject":        "single subject",
        "fonts":          "thin fonts",
        "negative_space": "> 40%",
        "prompt_addition": "minimalist, clean, simple, negative space"
    },
    "high_impact": {
        "colors":      "oversaturated color blocks",
        "typography":  "extra-bold type",
        "composition": "full-bleed composition",
        "effects":     "motion blur",
        "prompt_addition": "high impact, bold, vibrant, dramatic"
    }
}
```

Default style mapping (Stage 4 fallback when user did not specify a style):

```
style_direction defaults =
    Food     → lifestyle
    Beauty   → minimalist
    Tech     → minimalist
    Fashion  → editorial
    default  → modern
```

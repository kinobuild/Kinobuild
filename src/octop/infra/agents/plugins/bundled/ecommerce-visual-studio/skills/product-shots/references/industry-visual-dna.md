---
name: industry-visual-dna
description: Industry Visual DNA. Seven industry presets (Beauty, Fashion, Tech, Lifestyle, Travel, Food, Fitness) with prompt_patches, color_direction, key_avoid, composition_rules. Plus the bilingual keyword table used for industry auto-identification from content_topic. Loaded at SKILL.md EP Step 4 (industry derivation) and Step 5 (DNA injection).
---

# Industry Visual DNA

Seven industry presets. The `identify_industry()` matcher reads content_topic, hits one keyword bucket, and loads the entire bundle below into the Brief.

## Execution Procedure

```
load_industry_dna(content_topic) → bundle | None

industry = identify_industry(content_topic)
    # bilingual keyword match across 7 buckets
    # returns None if no keyword match (no DNA injection in that case)

if industry IN [Beauty, Fashion, Tech, Lifestyle, Travel, Food, Fitness]:
    return INDUSTRY_SPECS[industry]
        # bundle: prompt_patches + color_direction + key_avoid + composition_rules
else:
    return None
```

## TOC

- [Industry Matching — Keyword Tables](#industry-matching--keyword-tables)
- [Beauty](#beauty)
- [Fashion](#fashion)
- [Tech](#tech)
- [Lifestyle](#lifestyle)
- [Travel](#travel)
- [Food](#food)
- [Fitness](#fitness)

## Industry Matching — Keyword Tables

```
industry_keywords = {
    "Beauty":   ["makeup", "skincare", "cosmetics", "beauty", "化妆", "护肤"],
    "Fashion":  ["fashion", "clothing", "outfit", "style", "时尚", "服装"],
    "Tech":     ["tech", "software", "app", "gadget", "科技", "软件"],
    "Food":     ["food", "restaurant", "recipe", "coffee", "美食", "餐厅"],
    "Travel":   ["travel", "destination", "vacation", "旅行", "目的地"],
    "Fitness":  ["fitness", "workout", "gym", "健身", "运动"],
    # Lifestyle: no explicit keyword bucket — fallback for Beauty / Fashion / Travel / Food adjacent topics
}

def identify_industry(content_topic):
    topic_lower = content_topic.lower()
    for industry, keywords in industry_keywords.items():
        if any(keyword in topic_lower for keyword in keywords):
            return industry
    return None
```

## Beauty

| Field | Value |
|---|---|
| `prompt_patches` | `high-end minimalist chic, soft diffused lighting, premium matte texture, neutral tones` |
| `color_direction` | Nude, blush, taupe + single accent (rose gold / matte black) |
| `key_avoid` | Cluttered background, heavy filters |
| `composition_rules` | Minimal negative space, Product-centric |

## Fashion

| Field | Value |
|---|---|
| `prompt_patches` | `editorial fashion photography, muted color palette, sharp focus on fabric, sophisticated pose` |
| `color_direction` | Low-saturation earth tones, black-white-grey |
| `key_avoid` | Stiff poses, clashing backgrounds |
| `composition_rules` | Rule of thirds, Dynamic angles |

## Tech

| Field | Value |
|---|---|
| `prompt_patches` | `Apple-style minimalist design, clean white space, sharp geometric lines, soft shadows` |
| `color_direction` | White / light grey / space grey + brand accent |
| `key_avoid` | Decorative elements breaking minimalism |
| `composition_rules` | Extreme minimalism, Geometric precision |

## Lifestyle

| Field | Value |
|---|---|
| `prompt_patches` | `authentic film grain, natural sunlight, warm candid moments, soft focus background` |
| `color_direction` | Warm: golden, amber, cream |
| `key_avoid` | Over-retouched, too "posed" |
| `composition_rules` | Natural framing, Candid feel |

## Travel

| Field | Value |
|---|---|
| `prompt_patches` | `cinematic landscape, breathtaking wanderlust, golden hour lighting, vast perspective` |
| `color_direction` | Saturated but natural earth tones |
| `key_avoid` | Over-HDR, tilted horizon |
| `composition_rules` | Wide perspective, Leading lines |

## Food

| Field | Value |
|---|---|
| `prompt_patches` | `mouth-watering food photography, macro texture, steam and freshness, soft top-down lighting` |
| `color_direction` | Warm: golden, orange, red, brown |
| `key_avoid` | Cool/blue light (suppresses appetite) |
| `composition_rules` | 45° or top-down angle, Macro details |

## Fitness

| Field | Value |
|---|---|
| `prompt_patches` | `dynamic action shot, sweat and muscle definition, high-intensity, strong shadows` |
| `color_direction` | High contrast: black + neon green/orange/red |
| `key_avoid` | Static poses, over-bright background |
| `composition_rules` | Dynamic motion, Strong diagonals` |

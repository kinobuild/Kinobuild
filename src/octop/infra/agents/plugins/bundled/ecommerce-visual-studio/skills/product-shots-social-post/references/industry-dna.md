---
name: industry-dna
description: Section 1 — Industry Visual DNA. Seven industry presets (Beauty, Fashion, Tech, Lifestyle, Travel, Food, Fitness) each defined across six dimensions (Prompt Patch, composition, color scheme, lighting, common errors, social references). Plus the industry-matching logic that loads the full preset bundle on a single industry hit.
---

# Section 1 — Industry Visual DNA

Seven industry presets. Each preset is a six-dimension bundle that loads atomically on industry match.

## Execution Procedure

```
load_industry_dna(user_request) → bundle | nothing

match_industry(user_request, candidates) → industry_key
    scan user_request for industry signals (keywords, product type, scene cues)
    score each candidate against signals
    return highest-scoring candidate, or "no_match" if all below threshold

industry = match_industry(user_request, candidates=[Beauty, Fashion, Tech, Lifestyle, Travel, Food, Fitness])

IF industry IN [Beauty, Fashion, Tech, Lifestyle, Travel, Food, Fitness] THEN
    load full ruleset (Prompt Patch + Composition + Color + Lighting + Common Errors)
ELSE
    pick closest industry as base + adjust per user request
END IF

return bundle: {prompt_patch, composition, color, lighting, common_errors, ig_references}
```

## TOC

- [1.1 Beauty — Minimalist Chic](#11-beauty--minimalist-chic)
- [1.2 Fashion — High-End Editorial](#12-fashion--high-end-editorial)
- [1.3 Tech — Apple-style Minimal](#13-tech--apple-style-minimal)
- [1.4 Lifestyle — Film Aesthetic](#14-lifestyle--film-aesthetic)
- [1.5 Travel — Cinematic Wanderlust](#15-travel--cinematic-wanderlust)
- [1.6 Food — Gourmet Texture](#16-food--gourmet-texture)
- [1.7 Fitness — Dynamic Power](#17-fitness--dynamic-power)
- [Industry Matching Logic](#industry-matching-logic)

## 1.1 Beauty — Minimalist Chic

| Dimension | Rule |
|---|---|
| Prompt Patch | `high-end minimalist chic, soft diffused lighting, premium matte texture, neutral tones, luxury cosmetic photography, clean composition` |
| Composition | Product centered or rule-of-thirds; abundant negative space; macro texture close-ups (cream texture, powder splash); for portraits use half-face / lips / eye close-ups |
| Color Scheme | Nude tones (nude, blush, taupe) + a single accent (rose gold / matte black); avoid high saturation |
| Lighting | Soft diffused light, no hard shadows; aim for "creamy" light quality |
| Common Errors | Cluttered backgrounds break the high-end feel; product too small to show texture; over-filtering distorts color |
| Social Reference | @glossier, @rfrancisbeauty |

## 1.2 Fashion — High-End Editorial

| Dimension | Rule |
|---|---|
| Prompt Patch | `editorial fashion photography, muted color palette, sharp focus on fabric, minimalist studio setting, sophisticated pose, high-end aesthetic` |
| Composition | Full-body or 3/4 portrait; fabric texture clearly visible; solid / gradient backgrounds isolate the subject; negative space ≥ 30% |
| Color Scheme | Low-saturation earth tones or black-white-grey; seasonal palette (spring/summer: pink-blue; autumn/winter: camel-brown); each outfit ≤ 3 colors |
| Lighting | Side light or Rembrandt lighting, emphasizing fabric texture and drape |
| Common Errors | Stiff poses (common AI failure); background colors clash with garment; cropping cuts off shoes or accessories |
| Social Reference | @cos, @therow |

## 1.3 Tech — Apple-style Minimal

| Dimension | Rule |
|---|---|
| Prompt Patch | `Apple-style minimalist design, clean white space, sharp geometric lines, soft shadows, futuristic but simple, premium hardware finish` |
| Composition | Product at 45° floating angle or flat-front view; solid / gradient background; abundant negative space; on-screen content must be legible |
| Color Scheme | White / light grey / space grey + a single brand accent; tech blue (`#007AFF`) or minimal black-and-white |
| Lighting | Soft ambient light + precise product highlights; product edges sharp |
| Common Errors | Background elements interfere with product silhouette; on-screen content blurry; too much decoration breaks the minimalism |
| Social Reference | @apple, @nothing.tech |

## 1.4 Lifestyle — Film Aesthetic

| Dimension | Rule |
|---|---|
| Prompt Patch | `authentic film grain, natural sunlight, warm candid moments, soft focus background, cinematic storytelling, organic feel` |
| Composition | Snapshot-style framing (slight tilt, imperfect crop); subject interacting with environment; shallow depth-of-field blurring background |
| Color Scheme | Warm tones (gold, amber, cream); subtle film fade; avoid over-processing |
| Lighting | Primarily natural light (window light, golden hour); slight overexposure permitted to feel airy |
| Common Errors | Over-editing kills the realism; scenes look too staged; film grain too heavy harms clarity |
| Social Reference | @kinfolk, @cereal_mag |

## 1.5 Travel — Cinematic Wanderlust

| Dimension | Rule |
|---|---|
| Prompt Patch | `cinematic landscape, breathtaking wanderlust vibe, golden hour lighting, vast perspective, vibrant but natural colors, high-resolution travel photography` |
| Composition | Wide-angle panorama + a small human figure for scale; leading-line composition (roads, rivers, railings); horizon at the upper or lower 1/3 |
| Color Scheme | Saturated but natural earth tones; golden-hour warmth; cool-warm contrast between sky and land |
| Lighting | Shoot during golden hour or blue hour; backlit silhouettes; shafts of light through clouds |
| Common Errors | Over-HDR looks unnatural; tilted horizon; figure too large blocks the landscape |
| Social Reference | @natgeotravel, @beautifuldestinations |

## 1.6 Food — Gourmet Texture

| Dimension | Rule |
|---|---|
| Prompt Patch | `mouth-watering food photography, macro texture, steam and freshness, rustic or modern plating, soft top-down lighting, vibrant organic colors` |
| Composition | Top-down flat-lay or 45° angle; the main dish occupies 60-70% of the frame; ingredients / utensils dressed at the edges |
| Color Scheme | Warm tones (gold, orange, red, brown); food's natural color stays the hero; backgrounds use natural materials — wood / marble / linen |
| Lighting | Side light or back-side light to render surface gloss and steam; avoid direct top-down flash |
| Common Errors | Cool light makes food look unappetizing; composition too crowded with no breathing space; sauces / soups over-reflective |
| Social Reference | @foodminimalist, @symmetrybreakfast |

## 1.7 Fitness — Dynamic Power

| Dimension | Rule |
|---|---|
| Prompt Patch | `dynamic action shot, sweat and muscle definition, high-intensity atmosphere, gritty but clean texture, strong shadows, motivational lighting` |
| Composition | Low-angle upward shot for power; capture peak action (jump, exertion moment); muscle definition through light-shadow contrast |
| Color Scheme | High contrast (black + neon green / orange / red); dark background highlights the subject; saturated accent colors permitted |
| Lighting | Hard side lighting to sculpt muscle shadows and silhouette; smoke / dust effects allowed for atmosphere |
| Common Errors | Stiff motion kills the dynamism (common AI failure); background too bright weakens power; sweat / mist overdone looks fake |
| Social Reference | @niketraining, @crossfit |

## Industry Matching Logic

```
IF user-described industry / category IN [Beauty, Fashion, Tech, Lifestyle, Travel, Food, Fitness] THEN
    auto-load the full ruleset for that industry
    (Prompt Patch + Composition + Color Scheme + Lighting + Common Errors)
ELSE
    pick the closest industry as base + adjust per user-specific request
END IF
```

The seven-industry list is **shared** with `product-shots` and `product-shots-ad-creative` — same Prompt Patches, same color rules, same composition logic. Cross-skill consistency depends on this list staying canonical.

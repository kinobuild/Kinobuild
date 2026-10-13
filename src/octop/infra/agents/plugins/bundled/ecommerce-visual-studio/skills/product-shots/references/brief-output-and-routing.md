---
name: brief-output-and-routing
description: Standard Brief Output (with Brief Template) + Routing Rules. Defines the STANDARD_BRIEF_TEMPLATE, the weighted brief-completeness scoring (threshold 0.8), and the 5 routing targets (product-shots-main-image / product-shots-detail-page / product-shots-multi-angle / product-shots-ad-creative / product-shots-social-post) with their boolean conditions. Activates at SKILL.md EP Step 7.
---

# Brief Output and Routing

This module owns the final assembly: render the Brief, score completeness, pick the route.

## Execution Procedure

```
finalize_and_route(state) → brief, downstream_skill_id
build_brief(state) → brief
    # render(STANDARD_BRIEF_TEMPLATE, state)
    # carries platform / topic / assets / optimization / audience / style / variant_count
    # caller appends platform_dna + industry_dna + style_modifier + negative_prompt

# 1. Score completeness (Brief Output §Completeness)
completeness = calculate_brief_completeness(state)

# 2. Render Brief (STANDARD_BRIEF_TEMPLATE)
brief = build_brief(state)

# 3. Match routing rule
for skill_name, rule in ROUTING_RULES.items():
    if all(eval(condition, {"brief": brief}) for condition in rule["conditions"]):
        return brief, skill_name

# 4. No specialised skill matched — Brief is the final output for the host
return brief, None
```

## TOC

- [Standard Brief Template](#standard-brief-template)
- [Brief Completeness Scoring](#brief-completeness-scoring)
- [Routing Rules](#routing-rules)
- [Routing Decision Function](#routing-decision-function)

## Standard Brief Template

```
STANDARD_BRIEF_TEMPLATE = """
Confirmed:
- Platform: {platform}
- Format & dimensions: {format} {dimensions} ({ratio})
- Content topic: {topic}
- Visual assets: {assets}
- Optimization target: {optimization}
- Target audience: {audience}
- Style direction: {style}
- Variant count: {count}

Visual DNA applied:
- Platform patch: {platform_patch}
- Industry patch: {industry_patch}
- Style modifier: {style_modifier}

Negative constraints: {negative_constraints}

ready_for_generation: true
route_to: {next_skill}
"""
```

The two trailing lines (`ready_for_generation: true` + `route_to: <skill>`) are the handshake contract with downstream skills.

## Brief Completeness Scoring

```
def calculate_brief_completeness(state):
    """Calculate Brief information completeness (0.0 - 1.0)"""
    required_fields = {
        "platform":       0.25,    # weight 25%
        "content_topic":  0.20,    # weight 20%
        "visual_assets":  0.15,    # weight 15%
        "optimization":   0.15,    # weight 15%
        "audience":       0.10,    # weight 10%
        "style":          0.10,    # weight 10%
        "variant_count":  0.05     # weight 5%
    }
    completeness = 0.0
    for field, weight in required_fields.items():
        if state.get(field) is not None:
            completeness += weight
    return completeness

# Threshold
COMPLETENESS_THRESHOLD = 0.8       # 80% information complete → ready to generate
```

## Routing Rules

The product-shots ecosystem has 5 specialised downstream skills covering the cross-border e-commerce production line: upstream (Amazon listing imagery), midstream (apparel multi-angle), downstream (paid ads + organic social).

```
ROUTING_RULES = {
    "main-image": {
        "conditions": [
            "asset_type IN {'main_image', 'secondary_image', 'carousel'}",
            "platform IN {'Amazon', 'Shopify', 'AliExpress', 'TikTok Shop', 'Independent Site'}",
            "is_promotion != True"
        ]
    },
    "detail-page": {
        "conditions": [
            "asset_type IN {'aplus', 'detail_page', 'hero_banner', 'brand_content'}",
            "platform IN {'Amazon', 'Shopify', 'AliExpress', 'TikTok Shop', 'Independent Site'}"
        ]
    },
    "multi-angle": {
        "conditions": [
            "asset_type IN {'multi_angle', 'lookbook', 'model_series', '9_angle_portrait'}",
            "product_category IN {'apparel', 'footwear', 'accessory', 'bag'}"
        ]
    },
    "ad-creative": {
        "conditions": [
            "asset_type == 'ad' OR is_promotion == True"
        ]
    },
    "social-post": {
        "conditions": [
            "asset_type IN {'post', 'feed', 'story', 'reel', 'carousel_post'}",
            "platform IN {'Instagram', 'TikTok', 'Facebook', 'Pinterest', 'RedNote', 'LinkedIn', 'X'}",
            "is_promotion != True"
        ]
    }
}
```

| Target | Trigger summary |
|---|---|
| `product-shots-main-image` | Amazon-compliant main product image and the 7 secondary-image types (1:1 carousel) |
| `product-shots-detail-page` | Amazon A+ Content modules (21:9 Hero Banner + 3:2 standard modules) |
| `product-shots-multi-angle` | Apparel / accessory model 9-angle consistency series |
| `product-shots-ad-creative` | Paid promotion / ad creative across IG, FB, TikTok, LinkedIn, Google, YouTube, Pinterest, X |
| `product-shots-social-post` | Organic social-platform post (Feed / Story / Reel / Carousel) |

Total: **5 specialised downstream skills (or no further routing if Brief is the final output).**

## Routing Decision Function

```
def route_to_next_skill(brief):
    """Route to downstream skill based on Brief contents.

    Returns the matching skill_name string when a routing rule fires, or
    None when no specialised skill matched — in that case the caller
    treats the Brief itself as the final output for the host.
    """
    for skill_name, rule in ROUTING_RULES.items():
        if all(eval(condition, {"brief": brief}) for condition in rule["conditions"]):
            return skill_name
    return None   # no specialised skill matched, Brief is final output
```

The order of evaluation in `ROUTING_RULES` matters — `product-shots-main-image` / `product-shots-detail-page` / `product-shots-multi-angle` are checked before `product-shots-ad-creative` so an ad-objective request for an apparel product still routes to `product-shots-ad-creative` (the `is_promotion != True` clause excludes the upstream paths). `product-shots-social-post` activates only when the request is organic-social (non-promotional), after the upstream and ad branches have been ruled out. When none of the rules fire, the function returns `None` and the caller emits the Brief as the final output.

## Common ambiguity resolution

- **"Amazon listing image" — main vs A+?** Carousel (1:1) → `product-shots-main-image`. Below-carousel module imagery (21:9 / 3:2) → `product-shots-detail-page`.
- **"Lookbook for my dress" — multi-angle vs social-post?** If the user wants a 9-angle identity-locked model series from one reference → `product-shots-multi-angle`. If the user wants a Carousel social post repurposing existing lookbook images → `product-shots-social-post`.
- **"Instagram product post with discount tag" — social-post vs ad-creative?** If it's an organic post (no paid campaign objective) → `product-shots-social-post`. If it's tied to a paid campaign (Facebook Ads / Meta Ads Manager / TikTok Ads Manager) → `product-shots-ad-creative`.
- **"Multi-platform fan-out from one creative" — within ad-creative or another skill?** Single-creative multi-platform fan-out lives inside `product-shots-ad-creative` itself (Step 5: Platform Adaptation Layer). No separate cross-platform adapter is exposed in this ecosystem.

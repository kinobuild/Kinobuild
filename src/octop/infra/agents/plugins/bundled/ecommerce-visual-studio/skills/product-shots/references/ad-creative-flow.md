---
name: ad-creative-flow
description: Ad Creative Special Flow. Trigger detection (explicit keywords / asset_type / NLU intent), the 6-stage ad-clarification priority queue (Platform / Ad objective / Visual assets / Industry / Brand guidelines / CTA & core message), AD_PLATFORM_CONSTRAINTS for Google Display / TikTok / multi-platform, and the AD_BRIEF_TEMPLATE with `route_to: ad-creative`. Activates at SKILL.md EP Step 6 when `is_ad_creative_flow()` returns True.
---

# Ad Creative Special Flow

When the request is detected as an ad / promotion, the standard 4-stage clarification is replaced by this 6-stage ad questionnaire. Output uses `AD_BRIEF_TEMPLATE` and routes to `product-shots-ad-creative`.

## Execution Procedure

```
run_ad_creative_flow(user_request, asset_type) → ad_brief

# Step 0 — Detect ad flow
if is_ad_creative_flow(user_request, asset_type):
    enter ad-clarification
else:
    return None   # falls back to standard flow

# Step 1-6 — Walk the 6-stage priority queue
for stage in AD_CLARIFICATION_PRIORITY:
    question, options = stage.compose()
    emit question wrapped in <suggestion> tags
    state.update(user_answer)

# Apply platform-specific ad constraints
for platform in state.platforms:
    apply AD_PLATFORM_CONSTRAINTS[platform] (if defined)

# Emit AD_BRIEF_TEMPLATE with route_to = ad-creative
return render(AD_BRIEF_TEMPLATE, state)
```

## TOC

- [Trigger](#trigger)
- [6-Stage Ad Clarification Priority](#6-stage-ad-clarification-priority)
- [Platform-Specific Ad Constraints](#platform-specific-ad-constraints)
- [Ad Brief Template](#ad-brief-template)

## Trigger

```
AD_CREATIVE_TRIGGER = {
    "explicit_keywords": ["ad", "advertisement", "promotion", "campaign"],
    "asset_type":        "ad",
    "user_intent":       "advertising/promotion (detected by NLU)"
}

def is_ad_creative_flow(user_input, asset_type):
    return asset_type == "ad" or
           any(keyword in user_input.lower() for keyword in AD_CREATIVE_TRIGGER["explicit_keywords"])
```

Chinese trigger keywords are also detected (`广告` etc.) per the bilingual matching pattern in `references/industry-visual-dna.md`.

## 6-Stage Ad Clarification Priority

```
AD_CLARIFICATION_PRIORITY = [
    {
        "stage": 1,
        "question": "Platform (multi-select)",
        "options": [
            "Instagram", "Facebook", "TikTok", "LinkedIn",
            "YouTube", "Pinterest", "Google Display", "X"
        ]
    },
    {
        "stage": 2,
        "question": "Ad objective",
        "options": [
            "Brand awareness",
            "Promotion-conversion",
            "Lead generation",
            "App download",
            "Engagement"
        ]
    },
    {
        "stage": 3,
        "question": "Visual assets",
        "options": [
            "Product photo",
            "Person photo",
            "Logo",
            "Screenshot",
            "Reference",
            "None"
        ]
    },
    {
        "stage": 4,
        "question": "Industry",
        "options": [
            "Beauty-Fashion", "Tech-SaaS", "Food",
            "Fitness-Health", "Education", "Real Estate",
            "E-commerce-DTC", "Other"
        ]
    },
    {
        "stage": 5,
        "question": "Brand guidelines",
        "sub_questions": [
            "Brand colors?",
            "Fonts?",
            "Logo?",
            "Visual constraints?"
        ]
    },
    {
        "stage": 6,
        "question": "CTA / core message",
        "type": "open_ended",
        "prompt": "What should the viewer do after seeing this?"
    }
]
```

Note: Stage 1 is **multi-select** (one ad campaign frequently spans multiple platforms). When `len(platforms) > 1`, the eventual route may end at `ad-creative multi-platform fan-out` after `product-shots-ad-creative` produces base versions.

## Platform-Specific Ad Constraints

```
AD_PLATFORM_CONSTRAINTS = {
    "Google Display": {
        "text_overlay":              "ZERO text overlay allowed",
        "policy":                    "Image must have NO text (policy violation if present)",
        "negative_prompt_addition":  "text overlay, words, letters, typography"
    },
    "TikTok": {
        "style_recommendation":      "phone-shot / UGC style",
        "avoid":                     "polished studio production",
        "prompt_addition":           "authentic, raw, user-generated feel"
    },
    "multi_platform": {
        "rule":                      "Each platform gets independently designed version",
        "forbidden":                 "Simple resize across platforms"
    }
}
```

The Google Display rule forces appending `, text overlay` to the unified Negative Constraints prompt patch (see `references/hard-constraints.md`).

## Ad Brief Template

```
AD_BRIEF_TEMPLATE = """
Confirmed:
- Platform(s): {platforms}
- Ad objective: {objective}
- Content topic / product: {topic}
- Industry: {industry}
- Visual assets: {assets}
- CTA / core message: {cta}
- Brand guidelines: {brand_guidelines}
- Style direction: {style}
- Variant count: {count}

Defaults assumed:
{defaults_list}

Visual DNA applied:
- Platform patch: {platform_patches}
- Industry patch: {industry_patches}
- Ad-specific optimization: {ad_optimization}

Negative constraints: {negative_constraints}

ready_for_generation: true
route_to: ad-creative
"""
```

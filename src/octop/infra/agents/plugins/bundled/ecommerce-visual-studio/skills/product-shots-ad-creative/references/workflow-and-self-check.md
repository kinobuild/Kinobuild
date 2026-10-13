---
name: workflow-and-self-check
description: Section 6 (Core Workflow — Six-Step Process). The procedural backbone of ad-creative — Step 1 Platform+Objective, Step 2 Industry+Brand, Step 3 Visual Asset Audit, Step 4 Composition+Color, Step 5 Platform Adaptation Layer, Step 6 Self-Check Gate (Quality Check Before Delivery, the 11-item mandatory checklist).
---

# Core Workflow — Six-Step Process

The procedural backbone of `product-shots-ad-creative`. The workflow is **self-contained** — it runs entirely inside this skill. The only external dependency is conditional pre-fill via `product-shots` if any of the 7 Quick Start fields is missing.

## Execution Procedure

```
run_workflow(brief) → variant[] + self_check

# Step 1: Platform + Objective
platform, format, ad_objective = brief.platform, brief.format, brief.ad_objective
load references/hard-constraints.md  → dimensions / safe zones / text overlay / char limits

# Step 2: Industry + Brand
industry_bundle = load references/industry-style-rules.md[brief.industry]
if brief.brand_kit:
    apply_brand_kit_overrides(industry_bundle, brief.brand_kit)
        # brand colors → primary palette
        # brand fonts  → headlines
        # brand logo   → composed per platform safe-zone rules

# Step 3: Visual Asset Audit  ("Available assets determine the creative ceiling")
asset_class = classify(brief.visual_assets)
    ∈ {has_product_photo, has_model_photo, has_logo_only, has_none}

# Step 4: Composition + Color  (Industry × Objective cross-decision)
composition = select_composition_pattern(industry, ad_objective, asset_class)
              # references/composition-patterns.md
color       = pick_color_strategy(industry, brief.brand_kit)
              # references/color-and-cta-strategy.md §Color
cta         = pick_cta_strategy(ad_objective, platform)
              # references/color-and-cta-strategy.md §CTA

# Step 5: Platform Adaptation Layer  (inject platform-specific differences)
for plat in brief.platforms:
    apply references/platform-style-profiles.md[plat]
    apply references/multi-platform-output.md
    sanitize_prompt(prompt, brief.copy)
        # filter banned words; preserve user copy verbatim
        # inject Required Positive Instruction (preserve native packaging text)

# Step 6: Self-Check Gate  (Quality Check Before Delivery)
for variant in candidates:
    pass = run_11_checks(variant, platform, industry, ad_objective, brief)
    if not pass → regenerate
emit variant[] + self_check_score
```

## TOC

- [Step 1 — Platform + Objective](#step-1--platform--objective)
- [Step 2 — Industry + Brand](#step-2--industry--brand)
- [Step 3 — Visual Asset Audit](#step-3--visual-asset-audit)
- [Step 4 — Composition + Color](#step-4--composition--color)
- [Step 5 — Platform Adaptation Layer](#step-5--platform-adaptation-layer)
- [Step 6 — Self-Check Gate (11-Item Mandatory Checklist)](#step-6--self-check-gate-11-item-mandatory-checklist)

## Step 1 — Platform + Objective

Lock the (platform, format, ad_objective) tuple before any creative decision. Without it the safe zone is unknown, the char limit is unknown, the text overlay policy is unknown, and the visual hierarchy cannot be determined.

- Platform → load `references/hard-constraints.md §Platform Dimensions` for exact px and ratio.
- Format → resolves to one of the 21 platform×format combinations.
- Ad objective → drives information hierarchy (`references/ad-objective-rules.md`).

Refuse to proceed if the platform is ambiguous (e.g., "social media" is too vague — ask which platform).

## Step 2 — Industry + Brand

Match the user's industry to one of the presets in `references/industry-style-rules.md`. Load the bundle: color palette, composition pattern, typography, CTA tone, forbidden colors/elements.

If the user supplies a Brand Kit, integrate it as **hard constraints** that override industry defaults:

> If the user has Brand Kit (colors, fonts, logo), integrate it as hard constraints.

Brand Kit overrides:

- Brand colors → primary palette (industry colors become accent / supporting).
- Brand fonts → headlines (industry typography becomes secondary).
- Brand logo → composed per platform safe-zone rules (never in occluded regions).

The user's Brand Kit is parsed here when present — file path or inline fields. See `SKILL.md §Cross-Skill Notes (Brand Kit)`.

## Step 3 — Visual Asset Audit

> Available assets determine the creative ceiling.

Classify what the user has:

| Asset Class | Trigger | Composition Implication |
|---|---|---|
| `has_product_photo` | Product image only | Product Hero / Lifestyle In-Context / Flat Lay |
| `has_model_photo` | Person/model image | Face-Forward / Face-with-Product |
| `has_both` | Product + model | Face-with-Product (priority) |
| `has_logo_only` | Just brand logo | Bold Typography / Carousel Narrative |
| `has_none` | Nothing — AI generates everything | Bold Typography or industry-default lifestyle |

The asset audit is the input to Step 4's composition selection.

## Step 4 — Composition + Color

Use the **Industry × Objective × Asset** cross-decision logic in `references/composition-patterns.md` to pick the composition pattern. Then load the color strategy from `references/color-and-cta-strategy.md §Color Strategy` (industry color palette + max color count + temperature consistency + forbidden colors).

CTA strategy: pick CTA intensity from `references/color-and-cta-strategy.md §CTA Strategy` based on ad objective (low for Brand Awareness, high for Promotion / App Download).

The promotion/conversion objective has the strictest rules (discount number must dominate, must be in top 1/3, must use contrasting color, must include urgency cue) — see `references/ad-objective-rules.md`.

## Step 5 — Platform Adaptation Layer

For each target platform, inject platform-specific differences:

- **Tone & production level** — `references/platform-style-profiles.md` (TikTok = anti-ad / lo-fi; LinkedIn = professional authority; Pinterest = aspirational; etc.)
- **Text style** — TikTok native overlay; LinkedIn ≥60pt; Google Display zero text; YouTube big bold sans + drop shadow.
- **Refresh cadence** — TikTok 3-7 days; FB monthly; Pinterest weeks-months. See `references/multi-platform-output.md §Refresh Cadence`.
- **Prompt sanitation** — filter banned words from the generator prompt; inject the Required Positive Instruction. See `references/banned-words.md`.

Multi-platform output rules (consistent core message, platform-native style adaptation per plat) live in `references/multi-platform-output.md §Multi-Platform Output`.

## Step 6 — Self-Check Gate (11-Item Mandatory Checklist)

Every variant MUST pass all 11 checks before delivery. Any failure → revise prompt and regenerate.

```
QUALITY_CHECKLIST = [
    "dimensions_correct",           # dimensions exactly match the platform spec
    "safe_zones_respected",         # critical content avoids occluded zones
    "text_rules_compliant",         # complies with the platform's text policy
    "one_dominant_focal_point",     # one clear visual focal point
    "cta_visible_appropriate",      # CTA is visible and intensity matches the objective
    "industry_visual_language",     # matches the industry's visual language
    "platform_tone_matched",        # matches the platform's tone
    "brand_kit_applied",            # brand kit applied where supplied
    "mobile_first_readable",        # readable on a phone screen
    "ad_objective_reflected",       # ad objective is reflected
    "user_content_preserved"        # all user-specified content preserved verbatim
]
```

### Check 1 — Dimensions Correct

```
expected = PLATFORM_DIMENSIONS[platform]
actual   = (creative.width, creative.height)
FAIL if actual != expected
```

### Check 2 — Safe Zones Respected

- IG Reel / FB Reel / YouTube Shorts → bottom 35% (y > height × 0.65) is forbidden zone for text / logo / CTA / product / face.
- TikTok → right 64px is forbidden zone for text / logo / CTA.
- Pinterest → logo must not sit in the bottom-right (search-icon overlap).

### Check 3 — Text Rules Compliant

- `google_display` → if any text overlay AND not natural product packaging text → FAIL ("CRITICAL: Google Display prohibits ALL text overlays").
- `instagram_feed` / `facebook_feed` / `twitter` → soft-warn if `text_area_ratio > 0.20` (won't fail, increases CPM).
- `tiktok` → FAIL if QR code or any other-platform watermark present.
- `linkedin` → FAIL if any text element has `font_size < 60pt` or `contrast_ratio < 4.5:1`.

### Check 4 — One Dominant Focal Point

```
focal_points = detect_focal_points(creative)
if len(focal_points) == 0: FAIL "No clear focal point detected"
if len(focal_points) > 1:
    primary, secondary = focal_points[0], focal_points[1]
    if primary.visual_weight / secondary.visual_weight < 1.5: FAIL "Multiple competing focal points"
```

### Check 5 — CTA Visible and Intensity-Appropriate

- Some platforms (`instagram_feed`, `facebook_feed`, `linkedin`) provide CTAs via the platform UI — image CTA not required.
- For `promotion_conversion` and `app_download` objectives, a visible image CTA is REQUIRED.
- CTA intensity must match the objective (low / mid / high — see `references/ad-objective-rules.md`).

### Check 6 — Industry Visual Language

- Dominant colors must NOT include any color in the industry's `forbidden_colors` list.
- Composition pattern should be in the industry's `recommended_patterns` list (warn if not).

### Check 7 — Platform Tone Matched

- TikTok: `production_quality > 0.7` → FAIL ("Production too polished, use lo-fi aesthetic").
- LinkedIn / Pinterest: `production_quality < 0.6` → FAIL.
- Production quality factors: lighting (studio vs natural), composition precision, color grading sophistication, camera stability.

### Check 8 — Brand Kit Applied

If user supplied a Brand Kit:

- Brand colors → must appear in the dominant color set.
- Brand fonts → must be used in at least one text element.
- Brand logo → must be present.

If no Brand Kit supplied → check N/A (auto-pass).

### Check 9 — Mobile-First Readable

```
mobile_width  = 375  # iPhone SE reference
scale_factor  = mobile_width / creative.width
for text in creative.text_elements:
    scaled_pt = text.font_size * scale_factor
    if scaled_pt < 12: FAIL "Text too small on mobile"
```

### Check 10 — Ad Objective Reflected

- `promotion_conversion` → must have a visible discount/offer; the discount number must be the largest text element on the canvas.
- `brand_awareness` → must have a prominent brand element (logo / brand name / signature visual).
- `lead_generation` → must include a trust signal (review / rating / testimonial / "as seen in").
- `app_download` → must include either a device mockup OR an app rating display.

### Check 11 — User Content Preserved (MUST-level)

This check is at the same priority as `dimensions_correct`. Every protected user phrase must be present:

- `brand_name` if supplied → must appear verbatim in the deliverable.
- `slogan` if supplied → must appear verbatim.
- `cta_message` if supplied → must appear verbatim.
- `price_or_offer` if supplied → must appear verbatim.

Any missing phrase = FAIL → regenerate. See `references/quick-start-and-fidelity.md §Section 5` for the fidelity rule.

### Self-Check Output

When all 11 checks pass, emit a self-check score block alongside the variant (per `references/failures-defaults-output.md §Output Format`). When any check fails, surface the failure reason to the agent and regenerate the prompt before re-running the gate.

---
name: platform-style-profiles
description: Section 9 (Platform Style Profiles — Quick Reference). Per-platform tone / production level / what works / text style / key insight / what to avoid / creative lifespan / refresh cadence. Drives Step 5 (Platform Adaptation Layer) and is re-validated at Step 6 Check 7 (platform_tone_matched). Includes the TikTok native-aesthetic paradox (lo-fi visual + complete brand info) and the most-counterintuitive validation logic.
---

# Platform Style Profiles — Quick Reference

Per-platform tone, production level, and what-works / what-to-avoid pairs. These are not stylistic suggestions — they are constraints. The same creative content rendered in TikTok-style on LinkedIn looks unprofessional; the same content rendered LinkedIn-style on TikTok looks like a tone-deaf ad.

## Execution Procedure

```
apply_platform_profile(prompt, platform) → adapted_prompt

# Step 5 — Platform Adaptation Layer
profile = PLATFORM_STYLE_PROFILES[platform]
inject(prompt, profile.tone)
inject(prompt, profile.production_level)
inject(prompt, profile.text_style)
respect(profile.avoid)

# Step 6 — Check 7 (platform_tone_matched)
production_quality = analyze_production_quality(creative)
if platform == "tiktok":
    if production_quality > 0.7: FAIL "TikTok: Production too polished"
    if missing_required_info: FAIL "TikTok: Lo-fi style ≠ missing information"
elif platform in {"linkedin", "pinterest"}:
    if production_quality < 0.6: FAIL f"{platform}: Production quality too low"
```

## TOC

- [Section 9.1 — Platform × Tone Matrix](#section-91--platform--tone-matrix)
- [Section 9.2 — TikTok Native Aesthetic Paradox (most counterintuitive)](#section-92--tiktok-native-aesthetic-paradox)
- [Section 9.3 — Production Quality Scoring](#section-93--production-quality-scoring)

## Section 9.1 — Platform × Tone Matrix

| Platform | Tone | Production Level | What Works | Text Style | Key Insight | Avoid | Creative Lifespan | Refresh Cadence |
|---|---|---|---|---|---|---|---|---|
| **IG** | Polished, aspirational | Mid-high | UGC-upgraded, product-in-life, carousel narrative | Clear bold overlays, IG-native fonts | Carousel ads have the highest engagement (2026) | Stock photos, small text, landscape | 2-4 weeks | Bi-weekly refresh |
| **FB** | Informative, direct | Medium | Problem-solution, before/after, clear info hierarchy | Headline + description below the image carry the load | FB headline limit 27 chars (13 shorter than IG's 40) | Over-artistic with no clear value prop | 3-6 weeks | Monthly refresh |
| **TikTok** | Anti-ad aesthetic, raw, authentic | Low visual polish, high info density | Testimonial, unboxing, UGC, GRWM | Native text overlay, 5-10 words/sec | Phone-shot footage converts 63% better than studio. **Lo-fi style ≠ missing information**. Brand name, product name, price/offer, and CTA must ALL be present | Polished production, QR codes, other-platform watermarks, and: dropping brand/product info under the excuse of "authenticity" | 3-7 days | 2-3 new variants/week |
| **LinkedIn** | Professional authority | High | Data-driven, expert faces, gradient backgrounds | Sans-serif ≥60pt, high contrast | Thought-leader ads outperform brand-page ads | Stock photos, casual tone, salesy language | 4-6 weeks | Monthly refresh |
| **Pinterest** | Inspirational, calm | High aesthetic | Product in aspirational settings, soft light, step-by-step | Minimal ≤10 words, subtle overlays | Content lifespan: weeks to months (evergreen) | Hard-sell language, cluttered visuals | Weeks to months | Quarterly refresh |
| **Google Display** | Clean, product-focused | Medium | Single product on clean background, natural shadow | **Zero text overlay (policy: violations are rejected)** | Subject in center 80% (may auto-crop 5%) | Text / logo / buttons on the image | 4-8 weeks | Monthly refresh |
| **YouTube** | Attention-grabbing | Mid-high | Thumbnail: focal point + high contrast + 3-5 words; pre-roll: brand in first 5 sec | Massive bold sans-serif + drop shadow | **76% will skip — put product in the first 5 sec** | Slow openings, tiny text on Discovery ads | 2-4 weeks (pre-roll); longer (Discovery) | Bi-weekly to monthly |
| **X/Twitter** | Conversation-starting | Medium | Bold high-contrast graphics, strong copy | <20% image area; let the tweet carry info | Joining trending topics = +30% engagement | Wall of text, neutral corporate voice | Hours to days | Real-time, reactive |

## Section 9.2 — TikTok Native Aesthetic Paradox

TikTok's profile is the most counterintuitive of the eight platforms. The platform requires:

- **Visually**: anti-ad aesthetic — low production polish, phone-shot feel, raw / authentic.
- **Informationally**: high completeness — brand name, product name, value prop, CTA must ALL be present.

These two requirements are not in conflict. They are the resolution to a recurring failure: agents see "anti-ad" and strip out brand info; agents see "complete info" and over-polish. The paradox is the prescription.

### Validation logic

```python
def validate_tiktok_native_aesthetic(creative):
    """
    TikTok's core paradox:
    - Visually: low production polish (anti-ad aesthetic)
    - Informationally: high completeness (brand/product/CTA must be present)
    """

    # Check 1: visual production level (should be "low")
    production_score = analyze_production_quality(creative)
    if production_score > 0.7:  # 0-1 scale, >0.7 means too polished
        return False, "TikTok: Production too polished. Use phone-shot aesthetic."

    # Check 2: information completeness (should be "high")
    required_info = ["brand_name", "product_name", "value_prop", "cta"]
    missing_info = []

    for info_type in required_info:
        if not has_element(creative, info_type):
            missing_info.append(info_type)

    if missing_info:
        return False, f"TikTok: Missing required info: {missing_info}. Lo-fi style ≠ missing information."

    # Check 3: forbidden elements
    if has_qr_code(creative):
        return False, "TikTok: QR codes are prohibited"

    if has_other_platform_watermark(creative):
        return False, "TikTok: Other platform watermarks are prohibited"

    # Check 4: text style (should be TikTok-native)
    text_elements = find_elements_by_type(creative, "text")
    for text in text_elements:
        if not is_tiktok_native_font(text.font):
            return False, "TikTok: Use TikTok-native text overlay style"

    return True, "Pass"
```

## Section 9.3 — Production Quality Scoring

The `production_quality` score (used in Check 7 — platform_tone_matched) is a 0-1 scalar averaging four factors:

```python
def analyze_production_quality(creative):
    """
    Analyse visual production level
    - High (0.7-1.0): studio lighting, precision composition, color graded
    - Low (0.0-0.3): phone-shot, natural light, raw feel
    """
    factors = {
        "lighting":         analyze_lighting_setup(creative),       # studio vs natural
        "composition":      analyze_composition_precision(creative), # precision vs casual
        "color_grading":    analyze_color_grading(creative),         # graded vs raw
        "camera_stability": analyze_camera_stability(creative)       # stabilized vs handheld
    }
    return sum(factors.values()) / len(factors)
```

| Platform | Required Score Band | Notes |
|---|---|---|
| TikTok | < 0.7 | High polish breaks the anti-ad illusion. |
| LinkedIn | ≥ 0.6 | Low polish reads as unprofessional / spam. |
| Pinterest | ≥ 0.6 | Low polish breaks the aspirational mood. |

For platforms outside this table, derive the production level from §Section 9.1 ("Production Level" column).

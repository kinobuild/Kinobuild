---
name: hard-constraints
description: Section 5 (Hard Constraints — Must Not Be Violated, 4 sub: Platform Dimensions / Safe Zones / Text Overlay Rules / Ad Copy Character Limits). Loaded by the parent skill's Execution Procedure Step 0 alongside references/banned-words.md — together they define what every output MUST honor and what words MUST never enter the image generator prompt. Violation produces fake UI artifacts, watermarks, occluded CTAs, character truncation, or platform-policy takedowns.
---

# Hard Constraints

These rules are MUST-level. Read them at Execution Procedure Step 0 and re-validate against them at the Self-Check Gate (Step 6) before delivering any output. There is no soft version of these — the ad is either platform-correct or it is rejected by the platform.

## Execution Procedure

```
enforce_constraints(format, output_text, prompt_text, user_copy) → pass | findings[]

# Section 5.1 — Platform Dimensions
assert (width, height, ratio) match canonical px from §Platform Dimensions
    no approximation, no stretch, no naive crop
if platform ∈ {Google Display RDA, Google Demand Gen}:
    assert all 3 required ratios provided

# Section 5.2 — Safe Zones
if format ∈ {Story, Reel, Shorts, TikTok, ...}:
    assert critical content (text / logo / CTA / product / face)
        sits inside the canonical safe zone for that platform
    assert TikTok right side ≥ 64px clear of text/logo/CTA
    assert IG/FB Reel + YouTube Shorts: nothing critical in bottom 35%

# Section 5.3 — Text Overlay Rules
if platform == "google_display":
    assert NO text/logo/button overlay (zero tolerance)
        exception: native printed text on product packaging is allowed
elif platform == "tiktok":
    assert NO QR code, NO other-platform watermark
elif platform == "linkedin":
    assert text font size ≥ 60pt AND contrast ratio ≥ 4.5:1
elif platform ∈ {meta, twitter}:
    warn if text_area_ratio > 20% (soft: increases CPM)

# Section 5.4 — Ad Copy Character Limits
assert per-platform headline + description char limits
    Google: count CJK chars as 2

# Section 20 — Prompt Banned Words sanitation (see references/banned-words.md)
for each banned_word in banned-words.md §Banned Words List:
    assert banned_word NOT in prompt_text   # case-insensitive
inject banned-words.md §Required Positive Instruction (Preserve Native Packaging Text)
preserve user_copy verbatim (brand_name, slogan, cta, price/offer)

emit findings if any assert fails → revise prompt and regenerate
```

## TOC

- [Section 5.1 — Platform Dimensions Specification](#section-51--platform-dimensions-specification)
- [Section 5.2 — Safe Zone Specifications](#section-52--safe-zone-specifications)
- [Section 5.3 — Text Overlay Policies](#section-53--text-overlay-policies)
- [Section 5.4 — Ad Copy Character Limits](#section-54--ad-copy-character-limits)
- Section 20 (Prompt Banned Words + Required Positive Instruction) — see `references/banned-words.md`

## Section 5.1 — Platform Dimensions Specification

Platform × Format combinations (8 platforms × 21 formats):

| # | Platform × Format | Dimensions (px) | Aspect Ratio | Purpose | Performance Notes |
|---|---|---|---|---|---|
| 1 | IG Feed Ad | 1080 × 1350 (recommend 1440×1800) | 4:5 | Maximum mobile screen coverage | CTR ~15% higher than square |
| 2 | IG Story Ad | 1080 × 1920 (recommend 1440×2560) | 9:16 | Full-screen vertical | Immersive experience |
| 3 | IG Reel Ad | 1080 × 1920 (recommend 1440×2560) | 9:16 | Full-screen vertical | Bottom 35% occluded |
| 4 | IG Carousel Ad | 1080 × 1080 | 1:1 | All cards must share the same ratio | 3:4 supported as of 2026 |
| 5 | FB Feed Ad (Mobile) | 1080 × 1080 | 1:1 | Mobile-first | 4:5 recommended for mobile |
| 6 | FB Feed Ad (Desktop) | 1200 × 628 | 1.91:1 | Desktop | — |
| 7 | FB Story Ad | 1080 × 1920 | 9:16 | Same as IG Story | — |
| 8 | FB Reel Ad | 1080 × 1920 | 9:16 | Same as IG Reel | Bottom 35% occluded |
| 9 | TikTok In-Feed Ad | 1080 × 1920 | 9:16 | Vertical is the only correct choice | Creative lifespan 3-7 days |
| 10 | TikTok Carousel Ad | 1080 × 1920 or 1080 × 1080 | 9:16 / 1:1 | 2-35 images | — |
| 11 | LinkedIn Image Ad | 1200 × 1200 or 1200 × 628 | 1:1 / 1.91:1 | Square stands out more on mobile | — |
| 12 | LinkedIn Carousel Ad | 1080 × 1080 | 1:1 | 1:1 only | — |
| 13 | Google Display (RDA) | 1200×628 + 1200×1200 + 960×1200 | 1.91:1 + 1:1 + 4:5 | All three ratios required | Responsive Display Ads |
| 14 | Google Demand Gen | 1200×628 + 1200×1200 + 1080×1920 | 1.91:1 + 1:1 + 9:16 | Vertical for Shorts placements | — |
| 15 | YouTube Discovery Ad | 1280 × 720 | 16:9 | Thumbnail style | — |
| 16 | YouTube Shorts Ad | 1080 × 1920 | 9:16 | Vertical | Bottom 35% occluded |
| 17 | X/Twitter Image Ad | 1200 × 1200 or 1200 × 628 | 1:1 / 1.91:1 | — | — |
| 18 | Pinterest Standard Ad | 1000 × 1500 | 2:3 | The only recommended ratio for Pinterest | Creative lifespan weeks to months |
| 19 | Pinterest Carousel Ad | 1000 × 1500 | 2:3 | 2-5 images | — |

### Critical Rules

- ✅ Must match pixel dimensions exactly — no approximations
- ✅ Google Display (RDA) must supply all 3 ratios
- ✅ Google Demand Gen must supply all 3 ratios (including vertical)
- ❌ No "simple cropping" or "stretching" to fit other ratios

## Section 5.2 — Safe Zone Specifications

### Section 5.2.1 — Full-Screen Vertical Formats (9:16, based on 1080 × 1920 canvas)

| Platform | Top (px / %) | Bottom (px / %) | Left (px) | Right (px) | Usable Safe Area | Key Constraint |
|---|---|---|---|---|---|---|
| IG Story | 270px (14%) | 380px (20%) | 65px | 65px | ~1080 × 1420px centered | Username/time at top, reply bar at bottom |
| IG Reel | 270px (14%) | 670px (35%) | 65px | 65px | ~950 × 970px centered | **Bottom 35% fully occluded** |
| FB Story | 270px (14%) | 380px (20%) | 65px | 65px | Same as IG Story | — |
| FB Reel | 270px (14%) | 670px (35%) | 65px | 65px | Same as IG Reel | **Bottom 35% fully occluded** |
| TikTok | 130px (7%) | 350px (18%) | 48px | 64px | ~900 × 1200px centered | **Right 64px is the interaction rail** |
| TikTok Shopping | 130px (7%) | 450px (24%) | 48px | 64px | ~900 × 1100px centered | Larger bottom CTA area |
| YouTube Shorts | 288px (15%) | 672px (35%) | 48px | 192px (10%) | ~840 × 960px centered | **Bottom 35% occluded** |

#### Critical Content Zone (IG Reel / FB Reel / YouTube Shorts)

```
CRITICAL_CONTENT_ZONE = {
    "y_start": 270,          # top 14%
    "y_end": 1920 - 670,     # bottom 35% forbidden zone
    "safe_height": 980       # only 51% of canvas height is usable
}
```

Validation rule (Reel / Shorts):

```
forbidden_zone_start = canvas_height - 670
for element in {text, logo, cta, product}:
    if element.y_center > forbidden_zone_start:
        FAIL: "Critical element '{name}' in bottom 35% forbidden zone"
```

Validation rule (TikTok right side):

```
forbidden_zone_start = canvas_width - 64
for element in {text, logo, cta}:
    if element.x_center > forbidden_zone_start:
        FAIL: "Element '{name}' overlaps TikTok interaction buttons"
```

### Section 5.2.2 — Feed Format Safe Areas

Feed ads have UI controls vertically separated from the image (no overlap occlusion), but cropping still applies:

| Platform | Safe Area Recommendation | Reason |
|---|---|---|
| Meta (IG/FB Feed) | Center 80% region | Advantage+ may auto-crop up to 5% |
| LinkedIn Feed | 10% margin | Slight aspect-ratio variance across devices |
| X/Twitter Feed | 10% margin | Same as above |
| Pinterest | Avoid bottom-right | Search icon overlays the bottom-right |

## Section 5.3 — Text Overlay Policies

| Platform | Policy Type | Detailed Rule | Violation | Code Check |
|---|---|---|---|---|
| Meta (IG/FB) | ⚠️ Soft limit | The 20% text rule has been removed, but less text → lower CPM and higher delivery priority | Not rejected, but cost increases | `text_area_ratio < 0.20` is optimal |
| **Google Display (RDA)** | 🚫 **Strictly forbidden** | **No text, logo, or button overlay allowed on the image** | **Immediate rejection** | `has_text_overlay() == False` |
| Google Demand Gen | ⚠️ Soft limit | Text overlays allowed, but supply at least 1 text-free image | Not rejected | Provide a text-free variant |
| TikTok | ✅ Native text encouraged | Use TikTok-native text styling; QR codes and other-platform watermarks forbidden | QR codes/watermarks → rejection | `has_qr_code() == False` |
| LinkedIn | ✅ Allowed | Recommend <20% area, **font ≥60pt, high contrast** | Not rejected | `font_size >= 60 and contrast_ratio >= 4.5` |
| X/Twitter | ⚠️ Soft guideline | <20% text area; let the tweet copy carry the main message | Not rejected | `text_area_ratio < 0.20` is optimal |
| Pinterest | ⚠️ Aesthetic limit | Showcase/Quiz limited to 10 words; no hard limit elsewhere but excess text suppresses algorithmic distribution | Affects algorithmic recommendation | `word_count <= 10` (Showcase) |
| YouTube | ✅ Allowed | Thumbnails: 3-5 words, large bold with drop shadow for shrunk-down readability | Not rejected | `word_count <= 5 and has_drop_shadow == True` |

### Google Display: ZERO text overlay allowed

```
def validate_google_display_text_policy(image):
    """
    Google Display's text policy is the strictest hard constraint.
    Any text overlay results in ad rejection.
    """
    if detect_text_on_image(image):
        # Exception: native text on product packaging (e.g. logo on a Coke can)
        if is_natural_product_text(image):
            return True, "Natural product text is exempt"
        else:
            return False, "CRITICAL: Google Display prohibits ALL text overlays"
    return True, "Pass"
```

The "natural product text" exception:

- Text is on a 3D object surface (perspective distortion present)
- Text is part of the product's intrinsic design (e.g., Coca-Cola can logo)
- Text is NOT a flat post-production overlay

## Section 5.4 — Ad Copy Character Limits

| Platform | Headline | Primary Text / Description | CTA | Special Rules |
|---|---|---|---|---|
| IG Feed Ad | 40 chars | 125 chars visible (up to 2,200) | System preset | Over 125 chars truncated as "...more" |
| FB Feed Ad | 27 chars | 125 chars visible (truncated) | System preset | 13 chars shorter than IG |
| FB Reels Ad | 55 chars | 40 chars | System preset | Body copy is very short |
| TikTok | — | 100 chars (40-50 visible) | Custom | No headline field |
| Google RDA | 30 chars (short) / 90 chars (long) | 90 chars | Auto-generated | **CJK characters count as 2** |
| Google PMax | 30 chars (short) / 90 chars (long) | 90 chars | Auto-generated | **CJK characters count as 2** |
| LinkedIn | 70 chars (recommended) / 200 chars (max) | 150 chars (mobile visible) | System preset | — |
| X/Twitter | 70 chars | 280 chars (each link uses 23) | Custom | Links consume character count |
| Pinterest | 100 chars (40 visible) | 800 chars (algorithm-driven, rarely displayed) | System preset | Headline truncated heavily |
| YouTube In-Feed | 40 chars × 2 lines | 35 chars × 2 lines | — | Two-line display |

### Validation Logic

```python
def validate_ad_copy_length(platform, headline, description):
    LIMITS = {
        "instagram_feed": {"headline": 40, "description": 125},
        "facebook_feed": {"headline": 27, "description": 125},
        "google_display": {"headline_short": 30, "headline_long": 90, "description": 90},
        "linkedin": {"headline": 70, "description": 150},
        # ...
    }

    limit = LIMITS[platform]

    # Special handling: Google Ads counts CJK characters as 2
    if platform.startswith("google"):
        headline_length = count_chars_google(headline)
        description_length = count_chars_google(description)
    else:
        headline_length = len(headline)
        description_length = len(description)

    if headline_length > limit["headline"]:
        return False, f"Headline exceeds {limit['headline']} chars"
    if description_length > limit["description"]:
        return False, f"Description exceeds {limit['description']} chars"

    return True, "Pass"


def count_chars_google(text):
    """Google Ads: CJK characters count as 2 chars."""
    count = 0
    for char in text:
        if is_cjk(char):
            count += 2
        else:
            count += 1
    return count


def is_cjk(char):
    """Detect CJK (Chinese/Japanese/Korean) characters."""
    code = ord(char)
    return (0x4E00 <= code <= 0x9FFF or   # CJK Unified Ideographs
            0x3400 <= code <= 0x4DBF or   # CJK Extension A
            0x20000 <= code <= 0x2A6DF)   # CJK Extension B
```

## Section 20 — Prompt Banned Words

See `references/banned-words.md` for the full banned-words list, Exception (User-Specified Content Passthrough), and Required Positive Instruction (Preserve Native Packaging Text). Loaded at EP Step 0 alongside this file.

## Why These Are MUST-level

- **Wrong dimensions** → ad rejected by the platform, or destructively cropped at delivery.
- **Safe-zone violation** → CTA / brand name / face hidden behind UI on real devices (TikTok right rail, Reel bottom 35%, Shorts bottom 35%).
- **Text overlay violation on Google Display** → **immediate ad rejection** (zero tolerance — there is no warning, no review).
- **TikTok QR code or other-platform watermark** → **immediate ad rejection**.
- **LinkedIn font < 60pt or contrast < 4.5:1** → unreadable on feed scroll, brand looks unprofessional.
- **Char limit overrun** → ad copy truncated mid-sentence with "..." (especially harsh on FB at 27 chars vs IG 40).
- **Google CJK miscount** → ad copy fails preflight check (Chinese / Japanese / Korean chars cost double).
- **Banned word in prompt** → image contaminated with fake platform UI, fake username, fake like-counts, fake "Sponsored" tags. Looks like a screenshot, not a designed visual. May trigger platform takedowns for impersonation.
- **Missing Required Positive Instruction** → product packaging text gets erased by the image model, brand name disappears from the bottle / box / label.

---
name: multi-platform-output
description: Section 13 (Multi-Platform Output Rules) and Section 14 (Creative Fatigue & Refresh Cadence). Cross-platform consistency rules + per-platform refresh cadence and creative lifespan. Drives Step 5 (Platform Adaptation) and the multi-platform fan-out hand-off to ad-creative multi-platform fan-out.
---

# Multi-Platform Output Rules + Creative Fatigue & Refresh Cadence

When a single campaign needs to ship across multiple platforms, the outputs are NOT a single asset reformatted by aspect-ratio crop. They are platform-specific re-compositions of the same underlying brand message, each respecting the platform's safe zone, text policy, char limits, tone, and lifespan.

## Execution Procedure

```
multi_platform_fanout(brief, platforms[]) → variant[platform]

# Step 5 — Platform Adaptation Layer (per platform)
for plat in platforms:
    profile      = PLATFORM_STYLE_PROFILES[plat]
    constraints  = HARD_CONSTRAINTS[plat]
    variant      = render(brief, profile, constraints)
    # Cross-platform consistency: same hero / same brand / same CTA semantics
    # Per-platform adaptation: tone / production / text style / cadence

# Refresh cadence planning
for plat in platforms:
    cadence = PLATFORM_STYLE_PROFILES[plat].refresh_cadence
    schedule_refresh(plat, cadence)
    # TikTok: 2-3 new variants per week
    # FB: monthly refresh
    # Pinterest: quarterly refresh
```

For batch fan-out across many platforms, hand off to `ad-creative multi-platform fan-out` after the primary creative is delivered. The ad-creative multi-platform fan-out consumes the same user-provided Brand Kit and Industry Visual DNA so the cross-platform variants stay brand-consistent. See `SKILL.md §Cross-Skill Notes (Brand Kit)`.

## TOC

- [Section 13 — Multi-Platform Output Rules](#section-13--multi-platform-output-rules)
- [Section 14 — Creative Fatigue & Refresh Cadence](#section-14--creative-fatigue--refresh-cadence)

## Section 13 — Multi-Platform Output Rules

The same brief produces N platform-specific creatives with three required properties:

### Rule 1 — Consistent core message

Across all variants:

- Same **brand name** rendered identically (verbatim per fidelity rule — see `references/quick-start-and-fidelity.md §Section 5`).
- Same **product** as the visual hero.
- Same **value proposition** (the "what" — even if the "how it's said" adapts to platform tone).
- Same **CTA semantics** (a "Shop now" creative on FB stays a "Shop now" creative on TikTok — even if TikTok's CTA reads in native text style and FB's CTA is the platform-provided button).

### Rule 2 — Platform-native style adaptation

Adaptation is NOT cropping. The composition, lighting, text style, and production polish are re-rendered per platform:

- **TikTok variant**: lo-fi / phone-shot / native text overlay / vertical / casual.
- **LinkedIn variant**: professional / studio / ≥60pt text / horizontal or square / authoritative.
- **Google Display variant**: clean product / no text overlay / horizontal banner.
- **Pinterest variant**: aspirational scene / soft light / minimal text / 2:3.
- **YouTube thumbnail variant**: bold contrast / 3-5 word headline / drop shadow.

### Rule 3 — Per-platform char limit + text policy

Re-validate ad copy length per platform from `references/hard-constraints.md §Section 5.4`:

- IG Feed 40 char headline / FB Feed 27 char headline → headline rewritten per platform if too long, NEVER silent-truncated.
- Google: count CJK as 2 chars.
- LinkedIn: ≥60pt font.
- Google Display: zero text overlay.

### Rule 4 — Visual asset re-use rule

The same product photo can appear in multiple variants, BUT:

- Recompose around it per platform safe zone (TikTok = product upper-60%; Reel = product upper-65%; Pinterest = product in aspirational scene).
- The same underlying photo MAY be reframed, color-graded, or composited per platform tone.
- The exact same flat creative MUST NOT be uploaded to all platforms — it will fail the platform-tone check on at least one.

### Multi-platform fan-out

When the user wants to fan out to additional platforms after the primary creative is delivered, use the fan-out routine with:

- Brief (industry, brand, ad_objective, copy)
- Brand Kit (the user-provided file path or fields, shared across consumer skills)
- Source variant (anchor for visual consistency)
- Target platforms list

The fan-out routine runs the same per-platform adaptation logic for every target platform.

## Section 14 — Creative Fatigue & Refresh Cadence

Creative lifespan varies dramatically by platform. The same creative that works for 4 weeks on Facebook is dead in 5 days on TikTok.

| Platform | Creative Lifespan | Refresh Cadence | Fatigue Driver |
|---|---|---|---|
| **TikTok** | 3-7 days | 2-3 new variants per week | Algorithmic boost decay; native-aesthetic sameness fatigue |
| **IG** | 2-4 weeks | bi-weekly refresh | Feed scroll repetition |
| **FB** | 3-6 weeks | monthly refresh | Audience exposure saturation |
| **LinkedIn** | 4-6 weeks | monthly refresh | Professional audience low-frequency exposure |
| **Pinterest** | weeks-to-months (evergreen) | quarterly refresh | Pinterest is search/discovery — long tail |
| **Google Display** | 4-8 weeks | monthly refresh | Frequency cap protection |
| **YouTube In-stream** | 2-4 weeks | bi-weekly to monthly | Skip-rate climbs with repetition |
| **YouTube Discovery** | longer | monthly+ | Thumbnail-driven, slower fatigue |
| **X / Twitter** | hours-to-days | real-time / reactive | News-cycle relevance |

### Refresh planning rule

When a campaign launches on multiple platforms, schedule refresh assets at platform-native cadence — NOT a single calendar refresh. A "monthly campaign refresh" calendar will leave TikTok with 3-4 weeks of dead creative.

Recommended:

- TikTok track: 8-12 variants per month (2-3/week).
- IG track: 2 variants every 2 weeks.
- FB track: 1 variant every month.
- LinkedIn track: 1 variant every month.
- Pinterest track: 1 variant per quarter.
- Google Display track: 1 variant per month, watching frequency caps.

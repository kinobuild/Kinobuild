---
name: failures-defaults-output
description: Section 15 (Common Failure Modes), Section 16 (Defaults — Fallback Values When User Doesn't Specify), Section 17 (Output Format — Standard Output per Variant), Section 18 (Performance Benchmarks — Key Data Reference). The "what goes wrong / what to fall back to / what to ship / how to measure" tail of the skill.
---

# Failures + Defaults + Output Format + Performance Benchmarks

The tail of the skill: the failure-mode catalog (what to refuse), the default values (what to fall back to when the user defers), the output-format spec (what every variant looks like on delivery), and the performance benchmark reference (how to know it worked).

## Execution Procedure

```
# Section 15 — at any step
if matches(user_request, COMMON_FAILURE_MODES):
    surface_warning + offer_correction

# Section 16 — at Step 1 / Step 2
for field in required_fields:
    if not provided(field) and user_deferred(field):
        use DEFAULTS[field]

# Section 17 — at end of workflow
emit variant per VARIANT_OUTPUT_SCHEMA

# Section 18 — post-delivery
report against PERFORMANCE_BENCHMARKS for the (platform, format, objective)
```

## TOC

- [Section 15 — Common Failure Modes](#section-15--common-failure-modes)
- [Section 16 — Defaults: Fallback Values When User Doesn't Specify](#section-16--defaults-fallback-values-when-user-doesnt-specify)
- [Section 17 — Output Format: Standard Output per Variant](#section-17--output-format-standard-output-per-variant)
- [Section 18 — Performance Benchmarks: Key Data Reference](#section-18--performance-benchmarks-key-data-reference)

## Section 15 — Common Failure Modes

Per the skill body section index. The catalog of specific failure modes is enforced through the 11-item Self-Check Gate (`references/workflow-and-self-check.md §Step 6`), the four mandatory Promotion validation rules (`references/ad-objective-rules.md §Section 8.2`), the TikTok native-aesthetic paradox check (`references/platform-style-profiles.md §Section 9.2`), the Google Display zero-text-overlay rule (`references/hard-constraints.md §Section 5.3`), the banned-words sanitation pass and Required Positive Instruction (`references/banned-words.md`), and the Brand Name & User Copy Fidelity rule (`references/quick-start-and-fidelity.md §Section 5`). A failure on any of these triggers regenerate.

## Section 16 — Defaults: Fallback Values When User Doesn't Specify

When the user defers on a Quick Start field with "use defaults", apply:

| Field | Default Value | When to apply |
|---|---|---|
| **platform** | Instagram Feed | User says "any platform" / "all platforms" / no platform signal in request. Most-common ad surface for SMB. |
| **format** | 4:5 (1080 × 1350) | When `platform == Instagram` (default above). For other platforms, fall back to that platform's primary feed format from `references/hard-constraints.md §Section 5.1`. |
| **ad_objective** | Conversion | The most-common SMB objective. Use only when the user explicitly defers; otherwise infer from request keywords (`awareness`, `traffic`, `leads`, `engagement`, `app installs`, `sales`, `conversion`). |
| **industry** | — (must ask) | Industry drives composition + color via `references/industry-style-rules.md`. Do NOT default — emit `<suggestion>` chips of the 7 supported industries (Beauty / Fashion / Tech / SaaS / Food / Restaurant / Fitness / Health / Education / Home / Furniture / Real Estate). |
| **visual_assets** | `none` | When user uploads no image. Drives composition pattern selection in Step 4 toward typography-led / illustration-led patterns; emit a one-line note in the brief that recommends the user add a product photo for higher CTR. |
| **brand_kit** | omitted | Skip the Brand Kit integration step. Use industry-default colors / typography from `references/industry-style-rules.md`. |
| **copy** | — (must ask) | Cannot default. `brand_name` / `slogan` / `cta` / `price_or_offer` MUST come from the user verbatim per `references/quick-start-and-fidelity.md §Section 5` (Brand Name & User Copy Fidelity Rule). If absent, route to `product-shots` to collect. |

## Section 17 — Output Format: Standard Output per Variant

Each generated variant ships with the deliverable plus the 11-item self-check score block (`references/workflow-and-self-check.md §Step 6`) so the downstream agent (Planner / user) can audit at a glance.

### VARIANT_OUTPUT_SCHEMA

```yaml
variant:
  variant_id: <int>                     # 1, 2, 3 ... (per Step 4 fan-out)
  platform: <string>                    # canonical name from §Section 5.1
  format: <string>                      # e.g. "Feed Ad", "Story Ad", "Reel Ad"
  dimensions:
    width: <int>                        # px
    height: <int>                       # px
    aspect_ratio: <string>              # "4:5", "9:16", "1:1", "1.91:1", etc.
  industry: <string>                    # canonical name from §Section 7
  ad_objective: <string>                # awareness | traffic | leads | engagement | app_installs | sales | conversion
  composition_pattern: <string>         # one of the 12 patterns from §Section 10
  color_strategy:
    primary: <hex>
    secondary: <hex>
    accent: <hex>
  prompt:
    text: <string>                      # final sanitized prompt sent to image generator
    banned_words_filtered: <bool>       # §Section 20 sanitation pass result
    positive_instruction_injected: <bool>  # Required Positive Instruction present
  copy:
    brand_name: <string>                # verbatim from user
    slogan: <string>                    # verbatim from user
    cta: <string>                       # verbatim from user
    price_or_offer: <string|null>       # verbatim from user
  asset_url: <url>                      # generated image URL
  self_check_score:                     # the 11-item gate result
    dimensions_match: <pass|fail>
    safe_zone_clear: <pass|fail>
    text_overlay_policy: <pass|fail>
    char_limits: <pass|fail>
    brand_copy_fidelity: <pass|fail>
    industry_color_alignment: <pass|fail>
    objective_info_hierarchy: <pass|fail>
    platform_tone_alignment: <pass|fail>
    banned_words_clean: <pass|fail>
    positive_instruction_present: <pass|fail>
    overall: <pass|regenerate>
```

A variant is delivered only when `self_check_score.overall == pass`. On `regenerate`, revise the prompt against the failing items and re-run Step 4 + Step 6.

## Section 18 — Performance Benchmarks: Key Data Reference

2026 baseline metrics for ad creative performance — used to validate that delivered creatives are at or above platform-native baselines.

- **IG Feed Ad CTR**: 4:5 portrait performs ~+15% over 1:1 square.
- **TikTok phone-shot**: ~+63% conversion rate vs studio-shot creative.
- **TikTok creative lifespan**: 3-7 days; refresh cadence 2-3 new variants per week.
- **Pinterest creative lifespan**: weeks-to-months (evergreen — Pinterest is search-driven, slower fatigue).
- **YouTube ad skip rate**: ~76% of viewers skip → first 5 seconds must contain the brand.
- **X/Twitter trending-topic engagement**: ~+30% engagement when participating in trending topics.
- **IG Carousel Ad**: highest engagement format on IG (2026 reference).

### Industry market share reference (from `references/industry-style-rules.md §Section 7.1`)

- Beauty / Fashion: 22.9%
- Tech / SaaS: 15.2%
- Food / Restaurant: 5.1%
- Fitness: 3.5% / Health: 3.5%
- Education: 3.1%
- Home / Furniture: 2.9%
- Real Estate: 2.3%

---
name: workflow-and-self-check
description: Section 2 (Core Workflow seven steps) + Section 4 (Common Mistakes and Self-Audit, 14 mandatory items + self-check output format) + Section 6 (Output Format — six design-description items, caption block, seven-line self-check score). The procedural backbone of social-post.
---

# Workflow + Self-Audit + Output Format

The procedural backbone of `product-shots-social-post`. Section 2 (Core Workflow) is the linear seven-step decision flow; Section 4 (Common Mistakes / Self-Audit) is the mandatory gate before delivery; Section 6 (Output Format) is the deliverable shape.

## Execution Procedure

```
run_workflow(user_request) → audited_output

# Section 2 — Core Workflow (linear)
format, dimensions, safe_zone   = step_1_confirm_format(user_request)        # see §Step 1
industry_bundle                 = step_2_identify_industry(user_request)     # see §Step 2
engagement_goal                 = step_3_define_goal(user_request)           # see §Step 3
hook_type                       = step_4_define_hook(content_type)           # see §Step 4
composition, color, lighting,
text_strategy                   = step_5_compose(industry_bundle, format)    # see §Step 5
output                          = generate(...)
audit_result                    = step_6_self_check_gate(output)             # see §Section 4
emit_output                     = step_7_iterative_refinement(output)        # see §Step 7

# Section 4 — Mandatory Self-Check Gate
for each item in 14_mandatory_checks:
    if FAIL → revise prompt and regenerate
emit self_check_score (7 lines)

# Section 6 — Output Format
emit design_description (6 items)
emit caption (separate text block, never rendered onto image)
emit self_check_score
```

## TOC

- [Section 2 — Core Workflow](#section-2--core-workflow)
- [Section 4 — Common Mistakes and Self-Audit (Mandatory Gate)](#section-4--common-mistakes-and-self-audit-mandatory-gate)
- [Section 6 — Output Format](#section-6--output-format)

## Section 2 — Core Workflow

### Step 1: Confirm Format and Scenario — Lock Dimensions First

**Input**: user request. **Output**: chosen format + matching dimensions + safe zone.

```
IF user explicitly specified format THEN
    use the specified format
ELSE
    apply default selection logic (see references/hard-constraints.md §Section 0.1 Default Format Selection)
END IF

From the dimensions table extract:
- recommended dimensions
- aspect ratio
- safe-zone constraints (if applicable)
```

### Step 2: Identify Industry — Auto-Load Visual DNA

**Input**: user-described industry / category. **Output**: matched industry ruleset.

```
Match against Section 1 Industry Visual DNA (references/industry-dna.md).
Auto-load the bundle:
- Prompt Patch
- Composition rules
- Color scheme
- Lighting rules
- Common error checks
```

### Step 3: Define Engagement Goal

**Input**: user goal. **Output**: engagement strategy.

| Goal | Trigger Question | Design Strategy |
|---|---|---|
| SHARE (viral) | "Does this resonate?" | High-contrast, meme-style layout, "this is me"-style quotes, bold emotional visuals |
| SAVE (utility) | "Is this useful?" | Infographic style, step-by-step carousel, lists, clear data viz |
| COMMENT (community) | "Does this provoke an opinion?" | "A vs B" comparison layout, controversial questions, poll-style visuals |

```
IF user explicitly stated goal THEN
    use it
ELSE
    infer from context:
        IF content type = education / how-to       → SAVE
        IF content type = lifestyle / humor / vibe → SHARE
        IF content type = opinion / debate         → COMMENT
END IF
```

### Step 4: Define the Hook — 3-Second Rule

**Input**: content type. **Output**: hook type.

| Hook Type | Example | Best For |
|---|---|---|
| Bold Claim | "Stop doing X." / "This is wrong." | Counter-mainstream views, myth-busting, authority content |
| Curiosity Gap | "The secret of …" / "Nobody talks about this" | Tutorials, insider knowledge, save-worthy content |
| Visual Shock | Unusual color combinations, unexpected composition, pattern interrupts | Art / editorial content, brand differentiation |

```
The chosen hook type drives:
- Carousel Slide 1 design
- Single-image headline strategy
```

### Step 5: Composition and Color — Industry × Format Cross-Decision

| Decision Dimension | Source |
|---|---|
| Composition pattern | Industry Visual DNA (Section 1) + format safe-zone constraints |
| Color scheme | Industry color rule applied first; if a brand color exists, brand color overrides the industry default |
| Lighting style | Industry lighting rule |
| Text strategy | Determined by format (see references/hard-constraints.md §Section 0.3 Text Overlay Rules) |

### Step 6: Self-Check Gate

Must pass every Section 4 audit item before delivery (see §Section 4 below).

### Step 7: Iterative Refinement

When the user is satisfied:

- Offer style variants (different colors, composition, mood)
- Suggest multi-platform adaptation (re-optimize the same content for Story, Reel Cover, etc.)
- Propose Carousel expansion (if a single image, suggest splitting into Carousel format)
- Provide caption (if not already supplied — see Section 7)

When the user requests changes:

- **Color adjustment**: update the color scheme while preserving the Color Integrity rule
- **Composition change**: adjust subject position, negative space, or text-overlay region
- **Style swap**: swap style keywords (e.g., from "minimalist chic" to "editorial bold")
- **Format switch**: regenerate with a different aspect ratio and format-specific constraints
- **Hook tuning**: strengthen the 3-second hook based on user feedback

Local adjustments (recolor, edit text, tweak composition) are supported without a full regenerate.

## Section 4 — Common Mistakes and Self-Audit (Mandatory Gate)

Every output must pass the following 14 checks before delivery.

| Error Type | Symptom | Fix |
|---|---|---|
| Weak Hook | Slide 1 too plain, no swipe motivation | Rewrite as bold claim or counter-intuitive question |
| Information Overload | Text exceeds 40 words | Force-reduce; one insight per slide |
| Visual Discontinuity | Style inconsistent across slides | Lock background color, lighting direction, font family |
| Missing CTA | Last slide has no call-to-action | Add a save / share / follow prompt |
| Wrong Dimensions | Ratio is not 4:5 or 1:1 | Verify against the dimensions table |
| Safe-Zone Violation | Story / Reel critical content occluded by UI | Move core elements into the safe zone |
| Unreadable Text | Text blurry at thumbnail size | Font size ≥ 48pt; add contrast stroke or shadow |
| Color Drift | Colors look faded or shifted | Confirm color space is sRGB |
| Grid Disharmony | New post clashes with existing profile grid aesthetic | Apply Feed grid rules |
| Platform UI Artifact | Image contains fake like button, follow button, comment box, "Sponsored" tag, user avatar, or other IG UI element | Prompt must not contain Instagram / IG / feed / story or any platform name / UI term (see Banned Words) |
| Watermark / Logo Render | Image contains "Instagram", a brand name, or a tool name as a text watermark | Prompt must not contain any platform name or brand name |
| Screenshot Look | Image looks like a phone screenshot rather than a native design — status bar, phone frame, low-res pixelation | Do not describe "image on a phone screen" or "screenshot" in the prompt; describe the visual content directly |
| Fake Account Info | Image contains fictional username, avatar, follower count, like count, or other social media interaction info | Do not mention any social media interaction elements in the prompt |
| Garbled Text | AI-generated text is unreadable, misspelled, or garbled | Reduce the amount of text requested in the prompt; use quotes to specify key text; check readability after generation |

### Self-Check Output Format

```
Self-Check:
- Dimensions: [Pass / Fail]
- Safe Zone: [Pass / Needs Adjustment]
- Industry Visual DNA: [Strong Match / Moderate / Weak]
- Engagement Goal Alignment: [Strong / Moderate / Weak]
- Text Readability: [Pass / Needs Adjustment]
- Visual Quality: [Pass / Needs Adjustment] (Color Integrity, Depth, Cleanliness)
- Grid Harmony: [Considered / N/A]
```

## Section 6 — Output Format

### 6.1 Design Description (6 items)

1. **Design Direction** — one-sentence style positioning summary
2. **Engagement Goal & Hook** — which goal this variant targets (SHARE / SAVE / COMMENT) and which hook type (Bold Claim / Curiosity Gap / Visual Shock)
3. **Composition Layout** — subject position, focal-point routing, element arrangement
4. **Color Scheme** — color choices and rationale
5. **Text Strategy** — in-image text content, font size, font style, position (if applicable)
6. **Lighting and Mood** — light source direction, overall mood

### 6.2 Caption

Returned as a separate text block after the design description (or analyzed if the user supplied one). See Section 7 in `references/grid-and-caption.md`.

### 6.3 Self-Check Score

```
Self-Check:
- Dimensions: [Pass / Fail]
- Safe Zone: [Pass / Needs Adjustment]
- Industry Visual DNA: [Strong Match / Moderate / Weak]
- Engagement Goal Alignment: [Strong / Moderate / Weak]
- Text Readability: [Pass / Needs Adjustment]
- Visual Quality: [Pass / Needs Adjustment] (Color Integrity, Depth, Cleanliness)
- Grid Harmony: [Considered / N/A]
```

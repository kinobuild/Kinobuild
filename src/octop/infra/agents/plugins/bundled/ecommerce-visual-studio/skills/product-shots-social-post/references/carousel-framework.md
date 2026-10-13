---
name: carousel-framework
description: 'Section 3 — Carousel Standards. The 7-Slide Framework (Hook / Context / Value × 4 / CTA), Swipe Psychology, and Visual Consistency and Typography rules including the verbatim cross-slide consistency anchor template that must be repeated at the start of every slide''s prompt. EP: build_carousel(content, hook_type, industry_bundle, brand_color, engagement_goal) → 7 slide prompts.'
---

# Section 3 — Carousel Standards

Applies when format = Carousel. Carousel is the highest-failure-rate format because each slide is generated independently — without explicit per-slide consistency anchoring, fonts / colors / layouts drift between slides.

## Execution Procedure

```
build_carousel(content, hook_type, industry_bundle, brand_color, engagement_goal) → 7 slide prompts

# A. Map content to the 7-slide framework
slide_1 = render_hook(hook_type)                                      # Bold Claim / Curiosity Gap / Visual Shock
slide_2 = build_context(content)                                      # establish pain or promise
slide_3..slide_6 = expand_value(content, ascending_value=True)        # one insight per slide; strongest at slide 6
slide_7 = build_cta(engagement_goal)                                  # save / share / follow

# B. Apply Swipe Psychology
assert slide_1 promises an answer that requires swipe to reveal
assert "cross-slide elements" hint at swipe (visual continuity)
assert strongest insight placed at slide 6

# C. Visual Consistency and Typography
anchor = build_consistency_anchor(industry_bundle, brand_color)       # see §C
for n in 1..7:
    slide_n.prompt = anchor.replace("[N]", n) + slide_n.body_prompt   # anchor REPEATED verbatim per slide
    assert font family + weight identical across slides
    assert text alignment identical across slides
    assert background color / style identical across slides

# Other rules
assert each slide < 40 words text, body < 5 lines
assert ratio = 4:5 (preferred 1080×1350) and ALL cards share the same ratio
```

## TOC

- [A. The 7-Slide Framework](#a-the-7-slide-framework)
- [B. Swipe Psychology](#b-swipe-psychology)
- [C. Visual Consistency and Typography](#c-visual-consistency-and-typography)
- [Other Rules](#other-rules)

## A. The 7-Slide Framework

| Slide | Function | Technical Requirement |
|---|---|---|
| Slide 1: Hook | Apply the hook type chosen in Step 4 (Bold Claim / Curiosity Gap / Visual Shock) | Must stand alone in the profile grid |
| Slide 2: Context | Establish the pain point or promise | Reinforce why the viewer should keep swiping |
| Slide 3-6: Value | One insight per slide, numbered | Ascending value — strongest insight on Slide 6 |
| Slide 7: CTA | Explicit call-to-action: save / share / follow | CTA matches the engagement goal (SAVE → "Save this for later"; SHARE → "Tag someone who needs this"; COMMENT → "Which one are you?") |

## B. Swipe Psychology

| Principle | Implementation |
|---|---|
| Curiosity Gap | Slide 1 must promise an answer that can only be revealed by swiping |
| Visual Continuity | Ask the AI to design "cross-slide elements" that hint at swipe |
| Ascending Value | Strongest insight goes on Slide 6 (not Slide 7 — Slide 7 is the CTA) |

## C. Visual Consistency and Typography

> **Warning**: Cross-slide consistency is the most common Carousel failure. AI models generate each Carousel slide independently and will not preserve cross-slide visual unity by default. The constraints below **must be repeated verbatim in every slide's prompt**.

### Font Consistency Rules

- All slides must use **the same font family and weight** for headlines (e.g., `bold sans-serif` or `light serif`) — repeat this declaration in every slide's prompt.
- All slides must use **the same font family** for body, at the same size.
- Specify font specs explicitly per slide, e.g.:
  `title: 60pt bold sans-serif white, body: 32pt regular sans-serif light gray`

### Alignment Rules

- Once alignment is established in Slide 1's prompt, all subsequent slides must follow the same alignment.
- **Left-aligned recommended** (natural reading flow, most stable across slides); centered alignment is acceptable for headline and CTA slides.
- State explicitly per slide: `text left-aligned` or `text centered` — do not let the model decide.

### Background Consistency Rules

- All slides must use **the same background color or background style** — repeat the background description in every slide's prompt.
- For gradients, specify exact color values, e.g., `background: linear gradient from #1a1a2e to #16213e`.

### Cross-Slide Prompt Template (Consistency Anchor)

Every slide's prompt should begin with a fixed "consistency anchor", e.g.:

```
Carousel slide [N] of 7. Consistent style: white background,
bold black sans-serif title (60pt, left-aligned),
regular gray sans-serif body (32pt, left-aligned),
accent color #E53E3E for highlights.
Same layout grid as all other slides.
```

This anchor is **repeated verbatim in every slide's prompt**, ensuring the model honors the same visual specs while generating each slide independently.

## Other Rules

- **Typography**: < 40 words per slide, body < 5 lines.
- **Aspect Ratio**: prefer 4:5 (1080×1350); **all cards must share the same ratio** (see Dimensions table in `references/hard-constraints.md`).

---
name: grid-and-caption
description: Section 5 (Feed Grid Aesthetics — five grid strategies + grid rules) and Section 7 (Caption & Copywriting — in-image text vs caption distinction, caption logic, Social Caption Persona with example).
---

# Feed Grid + Caption

## Execution Procedure

```
finalize_grid_and_caption(format, user_supplied_caption, brand_account_context) → grid_strategy + caption

# Section 5 — Feed Grid Aesthetics
if brand_account_series:
    confirm grid consistency need
    if user has existing posts → reference their tone / style / palette
strategy = pick_grid_strategy(brand_intent)   # see §Common Grid Strategies
apply_grid_rules(format, strategy)            # carousel only Slide 1 visible; reel cover center-cropped to 4:5

# Section 7 — Caption & Copywriting
in_image_text   = bounded by §In-Image Text vs Caption
if user_supplied_caption:
    extract emotion + tone for visual prompt
    do NOT modify or regenerate unless asked
else:
    generate caption per §Social Caption Persona
```

## TOC

- [Section 5 — Feed Grid Aesthetics](#section-5--feed-grid-aesthetics)
- [Section 7 — Caption & Copywriting](#section-7--caption--copywriting)

## Section 5 — Feed Grid Aesthetics

### Common Grid Strategies

| Strategy | Description | Best For |
|---|---|---|
| Unified Tone | All content uses the same filter / color preset for overall harmony | Safe choice for most brand accounts |
| Checkerboard | Alternates two styles (e.g., product photo + text-graphic) | Knowledge accounts, coaches / consultants |
| Row Theme | Every 3 posts form one row with the same theme / palette | Product launches, series content |
| Gradient | Tone gradually shifts (e.g., warm → cool) across the grid | High-aesthetic lifestyle accounts |
| Puzzle | One large image is split across 3 / 6 / 9 grid tiles to form a complete picture | Major brand campaigns, product launches |

### Grid Rules

- Confirm whether the user needs grid consistency (one-off output vs. brand-account series).
- For a series, ask about — or reference — the existing posts' tone / style.
- **Carousel shows only Slide 1 in the grid** — Slide 1 must satisfy both the "grid aesthetic" and the "Carousel hook" requirements.
- **Reel Cover renders in the grid as a 4:5 center-crop** — make sure the cropped frame stands alone.

## Section 7 — Caption & Copywriting

### 7.1 In-Image Text vs. Caption

| Type | Definition | Rule |
|---|---|---|
| Graphic Text (in-image) | Short, high-impact headline rendered onto the visual | Max 8-10 words; obey Section 0 Text Overlay Rules (see `references/hard-constraints.md`) |
| Caption (post text) | Long copy returned as a separate chat message | **Never rendered onto the visual** |

> Only "graphic text" is allowed to appear on the image. The full caption is always a separate text output.

### 7.2 Caption Logic

```
IF user supplied a caption THEN
    analyze it to extract "mood" and tone for the visual prompt
    do NOT modify or regenerate unless explicitly asked
ELSE
    generate caption using the Social Caption Persona below
END IF
```

### 7.3 Social Caption Persona

- **Tone**: short, aesthetic, each line as an independent micro-statement.
- **Structure**: hook line → 2-3 value lines (with line breaks) → CTA → 3-5 hashtags.
- **Line breaks**: use frequent line breaks for breathing space — social aesthetic favors whitespace in captions.
- **Hashtags**: mix high-traffic (500K+ posts) with niche-specific tags; **3-5 total, never 30**.

Example:

```
This changed everything.

The one ingredient dermatologists actually agree on →
Niacinamide. Not the trendy kind. The proven kind.

Save this for your next restock ↓

#skincaretips #niacinamide #skinbarrier
```

> **Note**: "Social Caption Persona" is a caption-tone rule, not a skill-level Persona. The skill itself does not declare a persona name.

---
name: hard-constraints
description: Section 0 platform spec constraints (Dimensions, Safe Zones, Text Overlay Rules, Design Quality Baseline) and Section 9 Prompt Banned Words. Loaded by the parent skill's Execution Procedure Step 0 — these define what every output MUST honor and what words MUST never enter the image generator prompt. Violation produces fake UI artifacts, watermarks, occluded CTAs, or platform-policy breaks.
---

# Hard Constraints

These rules are MUST-level. Read them at Execution Procedure Step 0 and validate against them at the Self-Check Gate (Step 6) before delivering any output. There is no soft version of these — the image is either platform-correct or it is wrong.

## Execution Procedure

```
lookup(format) → dimensions, ratio, safe_zone

# Resolve canonical spec for a given format key
assert format ∈ {Feed Square, Feed Portrait, Feed Landscape, Carousel,
                 Story, Reel Cover, Profile Picture, Feed Ad, Story/Reel Ad}
dimensions = canonical px from §Dimensions
ratio      = canonical ratio from §Dimensions
safe_zone  = §Safe Zones row if format ∈ {Story, Reel Cover} else null
return dimensions, ratio, safe_zone

enforce_constraints(format, output_text, prompt_text) → pass | findings[]

# Sizing
assert format ∈ {Feed Square, Feed Portrait, Feed Landscape, Carousel,
                 Story, Reel Cover, Profile Picture, Feed Ad, Story/Reel Ad}
assert dimensions match canonical px from §Dimensions
assert ratio matches canonical ratio from §Dimensions

# Safe zones (only Story / Reel)
if format ∈ {Story, Reel Cover}:
    assert critical content sits inside the canonical safe zone (§Safe Zones)
    assert CTA not placed in bottom 20% (Story) / bottom 35% (Reel)

# Text overlay
assert text overlay obeys §Text Overlay Rules (word cap + min font size)

# Design Quality Baseline (applies to ALL outputs)
assert color integrity, visual cleanliness, readability, depth, subject-centered layout

# Prompt sanitation
for each banned_word in §Banned Words:
    assert banned_word NOT in prompt_text   # case-insensitive substring check
emit findings if any assert fails
```

## TOC

- [Section 0.1 — Dimensions](#section-01--dimensions)
- [Section 0.2 — Safe Zones](#section-02--safe-zones)
- [Section 0.3 — Text Overlay Rules](#section-03--text-overlay-rules)
- [Section 0.4 — Design Quality Baseline](#section-04--design-quality-baseline)
- [Section 9 — Prompt Banned Words](#section-9--prompt-banned-words)

## Section 0.1 — Dimensions

| Format | Min Dimensions (px) | Recommended (px) | Aspect Ratio | Notes |
|---|---|---|---|---|
| Feed Square | 1080×1080 | 1440×1440 | 1:1 | Classic format, brand / product display |
| Feed Portrait | 1080×1350 | 1440×1800 | 4:5 | Default first choice — largest mobile screen share, CTR ~15% higher than square |
| Feed Landscape | 1080×566 | 1440×754 | 1.91:1 | Smallest screen share in Feed; not recommended |
| Carousel | 1080×1350 | 1440×1800 | 4:5 | All cards must share the same ratio; 1:1 also supported |
| Story | 1080×1920 | 1440×2560 | 9:16 | Full-screen vertical |
| Reel Cover | 1080×1920 | 1440×2560 | 9:16 | Displayed in Feed as 4:5 center-crop — keep critical content inside the central 4:5 region |
| Profile Picture | 320×320 | 720×720 | 1:1 | Rendered as a circular crop |
| Feed Ad | 1080×1350 | 1440×1800 | 4:5 | Same as Feed Portrait |
| Story / Reel Ad | 1080×1920 | 1440×2560 | 9:16 | Same as Story |

### Default Format Selection

```
resolve_format(user_request) → format

IF user specified a format THEN return that format
ELSE
    IF scenario = single-image content              THEN Feed Portrait 4:5
    IF scenario = multi-page knowledge / tutorial   THEN Carousel 4:5
    IF scenario = short-lived content / ad          THEN Story 9:16
    IF scenario = short-video cover                 THEN Reel Cover 9:16
END IF
```

## Section 0.2 — Safe Zones

9:16 full-screen formats (canvas reference: 1080×1920).

| Format | Top Occlusion | Bottom Occlusion | Side Margin | Usable Safe Zone |
|---|---|---|---|---|
| Story 9:16 | 270px (14%) — username + progress bar | 380px (20%) — reply bar + message field | 65px | ~950×1270px centered |
| Reel 9:16 | 270px (14%) — username + music info | 670px (35%) — like / comment / share buttons + caption area | 65px | ~950×980px centered |

### Critical Rules

- Reel bottom 35% is occluded by UI → **core text and visual focal points must sit in the top 65% region**.
- Story bottom 20% is the reply box → **CTA must NOT be placed at the bottom**.
- Reel cover renders in the Feed grid as 4:5 center-crop → **important elements must live inside the central 1080×1350 area**.
- Feed formats (4:5 / 1:1) have no UI occlusion, but maintain a 5% margin to prevent device-side cropping.

## Section 0.3 — Text Overlay Rules

| Format | Text Strategy |
|---|---|
| Feed Image | social aesthetic favors minimal text; headline ≤ 8 words, body ≤ 2 lines; font size ≥ 48pt for thumbnail readability |
| Carousel | < 40 words per slide, body < 5 lines; headline font size ≥ 60pt |
| Story | Use platform-native text styles; ≤ 3 text blocks per screen; avoid dense paragraphs |
| Reel Cover | ≤ 5 words headline, must sit inside the central 4:5 safe zone; bold + high contrast |

## Section 0.4 — Design Quality Baseline

Mandatory pass-checks for every output:

| Rule | Description |
|---|---|
| Color Integrity | User-specified colors (e.g., "deep navy blue") must be the dominant visual theme — auto-fill or default colors must not override them |
| Visual Cleanliness | Never render platform UI elements (buttons, share icons, follower counts) or technical metadata (resolution text, file size) onto the image, unless explicitly requested |
| High Readability | Text must "pop" rather than look like a low-quality sticker. On busy backgrounds, use a soft drop shadow or subtle gradient |
| Visual Depth | Avoid flat / sticker aesthetic. Use layering, shadows, lighting variation, and texture to create dimensionality |
| Subject-Centered Layout | The subject (product / person) should occupy the central 60% of the visual field. Maintain at least 15% empty margin from the canvas edges; for high-end / luxury vibes enforce 40% negative space |

## Section 9 — Prompt Banned Words

The following words are **banned in image-generation prompts**. AI image models render them as fake in-image UI, watermarks, or screenshot artifacts. They are allowed inside the skill (for format selection / industry matching) but **must never appear in the text sent to the generator**.

### Platform Names (strictly forbidden)

```
Instagram, IG, Facebook, TikTok, Twitter, X, Pinterest, LinkedIn
RedNote, Xiaohongshu
```

### UI / Interaction Terms (forbidden)

```
feed, story, reel, post, carousel                         — trigger platform UI mockups
like button, heart icon, comment, share, follow, save     — generate fake interaction buttons
sponsored, ad, promoted                                   — render ad-tag overlays
profile, username, avatar, follower count                 — generate fake account info
notification, DM, inbox                                   — generate message-notification UI
```

### Screenshot-related (forbidden)

```
screenshot, phone screen, mobile mockup                   — generate phone frames + status bars
app interface, UI design                                  — generate app interfaces instead of content
```

### Brand / Tool Names (forbidden)

```
Canva, product-shots, Photoshop, Figma, Lightroom, etc.
```

### The Correct Approach

| Wrong | Right |
|---|---|
| `Instagram feed post, lifestyle aesthetic` | `Social media image, vertical 4:5, lifestyle aesthetic` |
| `Story 9:16 with swipe up` | `Vertical 9:16 image with call-to-action text at bottom` |
| `Instagram carousel slide` | `Vertical 4:5 content card, consistent with series` |

> Platform names are used **only for internal Skill format selection and industry matching** — they must never enter the prompt sent to the image generation model.

## Why These Are MUST-level

- **Wrong dimensions** → user output is rejected by Instagram, or center-cropped destructively.
- **Safe-zone violation** → CTA / key text is hidden behind UI on real devices.
- **Text overlay overflow** → unreadable at thumbnail size, defeats the engagement goal.
- **Quality baseline failure** → output looks AI-generic, fails brand handoff.
- **Banned word in prompt** → image is contaminated with fake UI, fake usernames, fake like-counts; appears as a screenshot rather than a designed visual; may trigger platform takedowns for impersonation.

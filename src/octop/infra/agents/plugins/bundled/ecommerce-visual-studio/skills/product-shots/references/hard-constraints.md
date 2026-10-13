---
name: hard-constraints
description: Negative Constraints. Four forbidden categories (no UI simulation / no device frames / no fake interactions / no watermarks-garbled-text) plus the unified 19-word prompt patch that MUST be appended to every generated Brief and the platform-specific extension for Google Display ("text overlay"). Loaded by the parent skill's Execution Procedure Step 0 — these are the only MUST-level constraints in the hub body and they propagate downstream into every Brief.
---

# Hard Constraints — Negative Constraints

These rules are MUST-level. The unified prompt patch is appended to every Brief produced by Design Guide and must reach the downstream skill / generator unchanged. The four category lists below define what counts as forbidden output.

## Execution Procedure

```
inject_negative_constraints(brief, platform) → brief

# Always-on: append the unified prompt patch
brief.negative_prompt = NEGATIVE_CONSTRAINTS["unified_prompt_patch"]

# Platform-specific extension
if platform == "Google Display":
    brief.negative_prompt += ", text overlay"   # Google policy: image must have NO text overlay

return brief

# Validation (run at SKILL.md EP Self-Check Gate)
assert brief.negative_prompt CONTAINS "social media UI"
assert brief.negative_prompt CONTAINS "screenshot"
assert brief.negative_prompt CONTAINS "watermark"
assert brief.negative_prompt CONTAINS "phone frame"
assert brief.negative_prompt CONTAINS "app interface"
emit findings if any assert fails
```

## TOC

- [Unified Prompt Patch](#unified-prompt-patch)
- [Category 1 — No UI Simulation](#category-1--no-ui-simulation)
- [Category 2 — No Device Frames](#category-2--no-device-frames)
- [Category 3 — No Fake Interactions](#category-3--no-fake-interactions)
- [Category 4 — No Watermarks / Garbled Text](#category-4--no-watermarks--garbled-text)
- [Platform-Specific Extension — Google Display](#platform-specific-extension--google-display)
- [Why MUST-level](#why-must-level)

## Unified Prompt Patch

The single string that is appended to every Brief's `negative_prompt`:

```
social media UI, screenshot, watermark, messy background, distorted text, phone frame, app interface
```

This is the **19-word patch**. Receiving downstream skills inherit this string and append their own platform-specific extensions; they do not regenerate it.

## Category 1 — No UI Simulation

Reason: output is creative content, not a UI mockup.

Forbidden elements:

```
like icons, comment icons, share buttons,
usernames, follow buttons, notification badges,
heart icons, bookmark icons, send icons
```

## Category 2 — No Device Frames

Reason: content should be frame-agnostic.

Forbidden elements:

```
phone bezels, app chrome, status bars,
home indicators, notches, device shadows,
screen reflections
```

## Category 3 — No Fake Interactions

Reason: static visual, not interactive prototype.

Forbidden elements:

```
search boxes, input fields, navigation bars,
tab bars, menu icons, hamburger menus,
dropdown menus, sliders
```

## Category 4 — No Watermarks / Garbled Text

Reason: professional output quality.

Forbidden elements:

```
meaningless text, watermarks, distorted platform logos,
lorem ipsum, garbled characters, unreadable text,
stock photo watermarks
```

## Platform-Specific Extension — Google Display

When `platform == "Google Display"`, append `, text overlay` to the unified prompt patch. Google Display policy forbids in-image text — violation triggers ad-policy rejection.

```
brief.negative_prompt += ", text overlay"
# additional negative_prompt_addition: "text overlay, words, letters, typography"
```

## Why MUST-level

- Without the unified patch, AI image models hallucinate fake Instagram UI, fake usernames, fake like-counts — output looks like a screenshot rather than a designed visual; may trigger platform takedowns for impersonation.
- Without the Google Display extension, `product-shots-ad-creative` output may be rejected by Google Ads policy review.
- The patch propagates downstream — `product-shots-social-post`, `product-shots-ad-creative` all inherit it; if Design Guide drops it, every downstream skill is contaminated.

---
name: banned-words
description: Section 20 — Prompt Banned Words + Required Positive Instruction. The list of platform names, ad-UI terms, brand-tool names that must NEVER enter the image generator prompt (they trigger fake UI / watermarks / screenshot artifacts), plus the positive-preservation instruction that protects native packaging text on the product itself. Loaded by the parent skill's Execution Procedure Step 0 and re-validated at the Self-Check Gate alongside hard-constraints.md.
---

## Execution Procedure

```
def register_protected_phrase(phrase) → registered_id
    # Called by quick-start-and-fidelity preflight for each non-null copy field
    # (brand_name / slogan / cta_text / price_or_offer).
    # Appends the phrase to the session's protected_phrases registry. Returns the
    # registry id used by sanitize_prompt() to swap the phrase in / out around
    # banned-word filtering. Idempotent — re-registering the same phrase returns
    # the existing id.

def sanitize_prompt(prompt, protected_phrases) → sanitized_prompt
    # 1. swap each protected_phrase with __USER_CONTENT_i__ placeholder
    # 2. apply PROMPT_SAFE_REPLACEMENTS (banned phrase → safe paraphrase)
    # 3. remove remaining PROMPT_BANNED_WORDS (case-insensitive whole-word)
    # 4. restore __USER_CONTENT_i__ placeholders with the original phrases (quoted)
    # 5. inject the Required Positive Instruction (Preserve Native Packaging Text)
    # 6. collapse extra whitespace and return.
    # Called by SKILL.md EP Step 5 for every per-platform prompt before image-gen dispatch.
```

## Section 20 — Prompt Banned Words

The following words are **banned in image-generation prompts**. AI image models render them as fake in-image UI, watermarks, or screenshot artifacts. They are allowed inside the skill (for format selection / industry matching / routing) but **must never appear in the text sent to the generator**.

### Exception: User-Specified Content Passthrough

User-supplied content is **never filtered**. The following user-provided values are protected and passed through verbatim:

```
"user_content_exceptions": [
    "brand_name",   # user-supplied brand name
    "slogan",       # user-supplied slogan
    "cta_text",     # user-supplied CTA copy
    "price_offer"   # user-supplied price / offer
]
```

Sanitation algorithm (high-level):

```
1. Extract user-specified content (brand_name, slogan, cta_text, price_offer)
2. Temporarily replace user content with placeholders __USER_CONTENT_i__
3. Apply replacement rules (banned phrase → safe paraphrase) — see PROMPT_SAFE_REPLACEMENTS
4. Remove remaining banned words (case-insensitive whole-word match)
5. Restore user content — wrap in quotes
6. Collapse extra whitespace
```

### Banned Words List

```python
PROMPT_BANNED_WORDS = {
    # Platform names (strictly forbidden)
    "platform_names": [
        "instagram", "ig", "facebook", "fb", "tiktok", "youtube",
        "linkedin", "pinterest", "google display", "x", "twitter",
        "rednote", "xiaohongshu", "小红书"
    ],

    # Ad UI terms (forbidden)
    "ad_ui_terms": [
        "ad", "advertisement", "sponsored", "promoted",
        "feed ad", "story ad", "reel ad",
        "like button", "share button", "comment section", "follow button",
        "ad manager", "boost post", "campaign"
    ],

    # Brand / tool names (forbidden)
    "brand_tool_names": [
        "meta", "google ads", "canva", "lovart", "figma",
        "adobe", "photoshop"
    ]
}
```

#### Safe Replacements

```python
PROMPT_SAFE_REPLACEMENTS = {
    "Instagram Feed Ad":     "Product promotion image, vertical 4:5, polished lifestyle aesthetic",
    "Instagram Story Ad":    "Vertical 9:16 full-screen image, dynamic mobile-first design",
    "Facebook ad":           "Product showcase image for social media",
    "TikTok ad":             "Vertical 9:16 product video still, casual handheld phone aesthetic, raw authentic feel",
    "Google Display banner ad": "Product-focused banner image, horizontal 1.91:1, clean composition, no text overlay",
    "LinkedIn ad":           "Professional business image, square or landscape format",
    "with Shop Now button":  "with bold CTA text 'Shop Now'",
    "with like button":      "with engagement prompt",
    "sponsored post style":  "promotional content style"
}
```

### Required Positive Instruction — Preserve Native Packaging Text

This is the **positive companion** to the banned-words filter. When the prompt instructs "no text overlay" (e.g., for Google Display), the AI image model may incorrectly delete printed text on the product packaging itself (brand name on a bottle, ingredient list on a box, volume label, etc.). The Required Positive Instruction prevents that.

Verbatim instruction to inject:

```
clean product shot with no added graphic text, captions, or button overlays,
BUT fully preserve all native printed text on the product packaging —
brand name, product name, label, volume, and any markings as they physically
appear on the product.
```

**Rationale**: prevents the AI from misinterpreting "no text" as "delete brand name from product packaging". This dual-direction constraint (negative banned-words filter + positive preservation rule) is the defining defensive prompt-engineering pattern of this skill.

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

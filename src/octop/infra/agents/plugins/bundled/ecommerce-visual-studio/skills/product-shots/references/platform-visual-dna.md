---
name: platform-visual-dna
description: Platform Visual DNA. E-commerce platforms (Amazon as primary listing surface, plus Shopify / AliExpress / TikTok Shop / Independent Site) and social platforms (Instagram, X/Twitter, YouTube, LinkedIn, Facebook, TikTok, Pinterest) plus two conditional Chinese platforms (RedNote, WeChat) gated by language or explicit mention. Each platform carries default format, dimensions, ratio, core_vibe, composition rule, and prompt_patches string. Loaded at SKILL.md EP Step 5 (Inject Visual DNA).
---

# Platform Visual DNA

E-commerce platforms (where product-shots originate) + social platforms (where assets get repurposed). Each entry is an atomic bundle: matching the platform name loads the entire `formats + visual_dna` block.

## Execution Procedure

```
load_platform_dna(platform_name, user_context) → bundle | None

ecommerce_platforms = [Amazon, Shopify, AliExpress, TikTokShop, IndependentSite]

primary_platforms = [Instagram, X_Twitter, YouTube, LinkedIn,
                     Facebook, TikTok, Pinterest]

conditional_platforms = [RedNote, WeChat]
    # display_condition: user language is Chinese OR
    #                    user explicitly mentions "小红书 / 微信 / RedNote / WeChat"

if user_context.language == "Chinese" or
   any(keyword in user_context.input for keyword in ["小红书", "微信", "RedNote", "WeChat"]):
    candidates = ecommerce_platforms + primary_platforms + conditional_platforms
else:
    candidates = ecommerce_platforms + primary_platforms

if platform_name in candidates:
    return PLATFORM_SPECS[platform_name]   # bundle: formats + visual_dna
else:
    return None
```

## TOC

- [Platform Display Logic](#platform-display-logic)
- [Amazon (e-commerce primary)](#amazon-e-commerce-primary)
- [Shopify / Independent Site (e-commerce)](#shopify--independent-site-e-commerce)
- [Instagram](#instagram)
- [X (Twitter)](#x-twitter)
- [YouTube](#youtube)
- [LinkedIn](#linkedin)
- [Facebook](#facebook)
- [TikTok](#tiktok)
- [Pinterest](#pinterest)
- [RedNote (conditional)](#rednote-conditional)
- [WeChat (conditional)](#wechat-conditional)

## Platform Display Logic

E-commerce platforms always shown (Amazon, Shopify, AliExpress, TikTok Shop, Independent Site). Social primary platforms always shown. RedNote and WeChat shown only when:
- `user_context.language == "Chinese"`, OR
- user input contains any of: `小红书`, `微信`, `RedNote`, `WeChat`

## Amazon (e-commerce primary)

| Field | Value |
|---|---|
| Main image format | `square` (1024×1024, 1:1) |
| Secondary image format | `square` (1024×1024, 1:1) |
| A+ Hero Banner | `wide_banner` (2388×1024, 21:9) |
| A+ Standard module | `landscape_module` (1536×1024, 3:2) |
| `core_vibe` | Clean, evidence-based, conversion-optimized |
| `composition` | Centered subject, ≥85% frame fill (main image), pure white RGB(255,255,255) background |
| `prompt_patches` | `studio product photography, pure white background, even soft lighting, e-commerce listing aesthetic` |
| Routing | `product-shots-main-image` (1:1 carousel) / `product-shots-detail-page` (21:9 + 3:2 A+ modules) |

## Shopify / Independent Site (e-commerce)

| Field | Value |
|---|---|
| Default format | `square_or_portrait` (1080×1080 or 1080×1350) |
| `core_vibe` | Lifestyle + product clarity, brand-led |
| `composition` | More compositional freedom than Amazon (no white-background rule) |
| `prompt_patches` | `lifestyle product photography, brand-aligned color palette, premium retail aesthetic` |
| Routing | `product-shots-main-image` (when 1:1 carousel images requested) |

## Instagram

| Field | Value |
|---|---|
| Default format | `feed_portrait` (1080×1350, 4:5) |
| Alternate format | `story_reel` (1080×1920, 9:16) |
| `core_vibe` | Emotional, high-aesthetic, lifestyle |
| `composition` | Center focus, shallow depth of field |
| `prompt_patches` | `trending on instagram, modern aesthetic, lifestyle photography, warm tones` |

## X (Twitter)

| Field | Value |
|---|---|
| Default format | `standard` (1200×675, 16:9) |
| `core_vibe` | Minimal, fast, high-contrast, opinionated |
| `composition` | Minimal composition, bold color blocks |
| `prompt_patches` | `bold design, high contrast, quick visual impact, minimalist` |

## YouTube

| Field | Value |
|---|---|
| Default format | `thumbnail` (1280×720, 16:9) |
| `core_vibe` | Exaggerated, high-tension, story-driven |
| `composition` | Rule of thirds, face close-up |
| `prompt_patches` | `high tension, storytelling, vibrant colors, eye-catching` |

## LinkedIn

| Field | Value |
|---|---|
| Default format | `feed_post` (1200×627, 1.91:1) |
| `core_vibe` | Professional, authoritative, business |
| `composition` | Stable grid, left-aligned |
| `prompt_patches` | `corporate quality, authoritative, business-focused, clean` |

## Facebook

| Field | Value |
|---|---|
| Default format | `feed_post` (1200×630, 1.91:1) |
| `core_vibe` | Community, warm, informational |
| `composition` | Clear hierarchy, CTA-forward |
| `prompt_patches` | `approachable, warm, clear information hierarchy` |

## TikTok

| Field | Value |
|---|---|
| Default format | `post` (1080×1920, 9:16) |
| `core_vibe` | Raw, authentic, trend-aware |
| `composition` | Phone-shot feel, casual framing |
| `prompt_patches` | `authentic, natural lighting, slightly imperfect, UGC style` |

## Pinterest

| Field | Value |
|---|---|
| Default format | `standard` (1000×1500, 2:3) |
| `core_vibe` | Inspirational, soft, save-worthy |
| `composition` | Vertical flow, airy space |
| `prompt_patches` | `soft tones, editorial quality, aspirational, clean composition` |

## RedNote (conditional)

| Field | Value |
|---|---|
| Default format | `cover` (1080×1440, 3:4) |
| `display_condition` | `user_mentions_explicitly OR chinese_audience` |
| `core_vibe` | Authentic, lifestyle, aspirational |
| `composition` | Natural, relatable |
| `prompt_patches` | `xiaohongshu style, natural lighting, clean aesthetic` |

## WeChat (conditional)

| Field | Value |
|---|---|
| Default format | `article_cover` (900×383, 2.35:1) |
| `display_condition` | `user_mentions_explicitly OR chinese_audience` |
| `core_vibe` | Informational, trustworthy |
| `composition` | Clear focal point |
| `prompt_patches` | `clean, professional, readable` |

> Note: Platform Visual DNA defines 7 primary platforms with prompt patches; RedNote and WeChat appear in the Stage-1 selection list under the conditional rule but their full Visual DNA bundles are minimal compared to the primary 7.

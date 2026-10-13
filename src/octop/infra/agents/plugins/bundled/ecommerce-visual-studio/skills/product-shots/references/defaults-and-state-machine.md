---
name: defaults-and-state-machine
description: Default value system + BriefState field-list + state-machine transition table. Supporting module for SKILL.md EP Step 1 (initialise state) and Step 3 (apply defaults). Captures DEFAULT_VALUES (optimization_target, target_audience, style_direction map, variant_count, format) and the full BriefState schema (Stage 1-4 fields + derived fields + metadata).
---

# Defaults and State Machine

Supporting module: defines the BriefState shape (Stage 1-4 fields), default values applied when fields are missing, and the state-machine derived-field rules.

## Execution Procedure

```
init_state() → BriefState
apply_defaults(state) → state

# 1. Initialise empty BriefState
state = BriefState()

# 2. Run clarification loop (per references/clarification-stages.md)

# 3. Fill missing fields with defaults
if state.optimization_target is None: state.optimization_target = "engagement"
if state.target_audience    is None: state.target_audience    = "general"
if state.variant_count      is None: state.variant_count      = 3
if state.format             is None: state.format             = platform_default(state.platform)
if state.style_direction    is None:
    state.style_direction = STYLE_DEFAULTS_BY_INDUSTRY.get(state.industry, "modern")

# 4. Derive routing-helper fields (consumed by references/brief-output-and-routing.md)
state.single_platform = (len(state.platforms) == 1)
state.is_promotion    = (state.asset_type == "ad") or has_promotion_keywords(user_request)
```

## TOC

- [BriefState Schema](#briefstate-schema)
- [Default Values](#default-values)
- [Style Default by Industry](#style-default-by-industry)
- [Asset Type Identification](#asset-type-identification)
- [Routing Helper Inference](#routing-helper-inference)

## BriefState Schema

```python
class BriefState:
    """Full state object held during clarification."""

    def __init__(self):
        # Stage 1: Task Skeleton
        self.platform = None           # required
        self.format = None             # auto-derived from platform
        self.dimensions = None         # auto-derived from format
        self.ratio = None              # auto-derived from format
        self.content_topic = None      # required

        # Stage 2: Visual Assets
        self.visual_assets = None      # decision required (incl. "Upload Brand Kit")
        self.asset_urls = []           # optional

        # Stage 3: Business Goal
        self.optimization_target = None  # default "engagement"
        self.target_audience = None      # default "general"

        # Stage 4: Style and Brand
        self.style_direction = None    # default per industry table
        self.brand_colors = None       # optional
        self.brand_fonts = None        # optional
        self.brand_logo = None         # optional

        # Derived fields
        self.industry = None           # derived from content_topic
        self.asset_type = None         # derived from intent
        self.variant_count = 3         # default
        self.single_platform = None    # derived: len(platforms) == 1
        self.is_promotion = None       # derived: asset_type == 'ad' or promotion keywords

        # Metadata
        self.round_count = 0
        self.completeness = 0.0
```

## Default Values

```
DEFAULT_VALUES = {
    "optimization_target": "engagement",
    "target_audience":     "general",
    "variant_count":       3,
    "format":              "platform_default",   # use platform's default format

    "style_direction": {
        "Food":    "lifestyle",
        "Beauty":  "minimalist",
        "Tech":    "minimalist",
        "Fashion": "editorial",
        "default": "modern"
    }
}
```

## Style Default by Industry

| Industry | Default `style_direction` |
|---|---|
| Food | `lifestyle` |
| Beauty | `minimalist` |
| Tech | `minimalist` |
| Fashion | `editorial` |
| All others | `modern` |

This table is consumed by `apply_defaults()` when the user has not specified a style_direction by the end of Stage 4.

## Asset Type Identification

```python
def identify_asset_type(user_input, platform):
    """Identify asset type."""
    if any(keyword in user_input.lower() for keyword in ["ad", "advertisement", "promotion", "广告"]):
        return "ad"
    if platform == "YouTube" and "thumbnail" in user_input.lower():
        return "thumbnail"
    if "carousel" in user_input.lower():
        return "carousel"
    return "post"   # default
```

## Routing Helper Inference

`references/brief-output-and-routing.md §Routing Rules` evaluates two boolean fields that are not asked for in the clarification loop — they are derived from already-collected state.

```python
PROMOTION_KEYWORDS = [
    "ad", "advertisement", "promotion", "promo", "campaign", "launch", "sale",
    "广告", "推广", "促销", "活动"
]

def has_promotion_keywords(user_input):
    """True when the original request contains promotion / campaign signal words."""
    text = user_input.lower()
    return any(keyword in text for keyword in PROMOTION_KEYWORDS)

def derive_routing_helpers(state, user_input):
    """Populate single_platform + is_promotion before route_to_next_skill()."""
    state.single_platform = (len(state.platforms) == 1)
    state.is_promotion    = (state.asset_type == "ad") or has_promotion_keywords(user_input)
    return state
```

Both fields MUST be resolved before `route_to_next_skill(brief)` runs, otherwise the routing rules silently fall through (`single_platform == True` / `is_promotion == True` evaluate to False on missing attributes).

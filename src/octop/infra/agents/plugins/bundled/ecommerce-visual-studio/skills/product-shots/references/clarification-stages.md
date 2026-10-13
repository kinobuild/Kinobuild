---
name: clarification-stages
description: Clarification Mechanism + Clarification State Machine. Defines the 0-5-round clarification loop, completeness threshold (0.8), termination conditions, the four ordered stages (Task Skeleton / Visual Assets / Business Goal & Audience / Style & Brand Constraints), the question-priority principle, and the typical-rounds heuristic per request type.
---

# Clarification Mechanism + State Machine

This module owns the multi-turn dialogue logic: how many rounds to run, when to stop, what to ask in each round, and in what order. Keep these constants in working memory while orchestrating the loop in SKILL.md EP Step 2.

## Execution Procedure

```
clarify(state) → next_question | brief_ready
detect_language(user_request) → "zh" | "en"
    # auto-detect script class of user input
    # locks all subsequent replies to this language
select_next_stage(state) → stage_id
    # return first incomplete stage in [Stage 1, Stage 2, Stage 3, Stage 4]
    # see Stage Selection below
generate_question(stage, state) → (question_text, options)
    # render the stage's question template + suggestion options
    # delegates to stage.generate_question(state)

# Termination (CLARIFICATION_RULES)
min_rounds = 0           # info already complete → skip questions
max_rounds = 5           # absolute cap
threshold  = 0.8         # brief_completeness > 0.8 → stop and emit Brief

# Per request-type heuristic (typical_rounds)
if request_type == social_media       → expect 1-2 rounds
if request_type == underspecified     → expect 3-4 rounds
if request_type == high_stakes        → expect up to 5 rounds
    # high_stakes covers: YouTube Thumbnail, Carousel, Ad Creative

# Termination condition
should_continue =
    state.round_count < 5 AND
    calculate_completeness(state) <= 0.8

# Stage selection — fixed ordering
next_stage = select_next_stage(state)
question, options = generate_question(next_stage, state)

emit question wrapped in <suggestion> tags
collect user_answer
state.update(user_answer)
state.round_count += 1
```

## TOC

- [Clarification Rules](#clarification-rules)
- [Question Priority Principle](#question-priority-principle)
- [Stage 1 — Task Skeleton (Platform + Asset Type + Topic)](#stage-1--task-skeleton-platform--asset-type--topic)
- [Stage 2 — Visual Assets (Key Visual Materials)](#stage-2--visual-assets-key-visual-materials)
- [Stage 3 — Business Goal and Audience (Optimization Direction)](#stage-3--business-goal-and-audience-optimization-direction)
- [Stage 4 — Style and Brand Constraints (Visual Style Rules)](#stage-4--style-and-brand-constraints-visual-style-rules)
- [State Transitions](#state-transitions)

## Clarification Rules

```
CLARIFICATION_RULES = {
    "min_rounds": 0,                # information complete → direct generate
    "max_rounds": 5,                # absolute cap
    "typical_rounds": {
        "social_media":     [1, 2],
        "underspecified":   [3, 4],
        "high_stakes":      5        # YouTube Thumbnail, Carousel, Ad Creative
    },
    "termination_condition": "rounds >= 5 OR brief_completeness > 0.8"
}
```

Decision logic:

```
def should_continue_clarification(state, round_count):
    if round_count >= 5:
        return False                 # hard stop
    completeness = calculate_completeness(state)
    if completeness > 0.8:
        return False                 # info sufficient
    return True
```

## Question Priority Principle

> Ask in order of "how much it changes the creative direction":
> Platform choice > Style preference > Variant count

Stages 1 → 4 are arranged in descending impact-on-direction order. NEVER ask Stage 4 questions while Stage 1 is incomplete. NEVER ask multiple stages in one turn.

## Stage 1 — Task Skeleton (Platform + Asset Type + Topic)

Required fields:

| Field | Type | Required |
|---|---|---|
| `platform` | enum (Instagram / X / YouTube / LinkedIn / Facebook / TikTok / Pinterest / RedNote / WeChat) | yes |
| `format` | derived from platform default | auto |
| `dimensions` | derived from format | auto |
| `ratio` | derived from format | auto |
| `content_topic` | string | yes |

Question pattern (English example):

```
Got it. Which platform is this for?

<suggestion><label>Instagram</label><prompt>Instagram</prompt></suggestion>
<suggestion><label>Facebook</label><prompt>Facebook</prompt></suggestion>
<suggestion><label>TikTok</label><prompt>TikTok</prompt></suggestion>
<suggestion><label>X (Twitter)</label><prompt>X (Twitter)</prompt></suggestion>
<suggestion><label>LinkedIn</label><prompt>LinkedIn</prompt></suggestion>
<suggestion><label>Other platform</label><prompt>Other platform</prompt></suggestion>
```

## Stage 2 — Visual Assets (Key Visual Materials)

Required fields:

| Field | Type | Required |
|---|---|---|
| `visual_assets` | enum decision | yes (decision must be made) |
| `asset_urls` | list of URLs | optional |

Structured options:

- Upload product photo
- Upload reference image
- **Use Brand Kit** ← user-provided file path or inline fields, see `SKILL.md §Brand Kit Reference`
- No assets — create from concept

Question pattern (English example):

```
Okay, Instagram post, defaulting to Feed portrait 1080×1350 (4:5).
Do you have any assets to use?

<suggestion><label>Upload product photo</label><prompt>I have product photos</prompt></suggestion>
<suggestion><label>Upload reference image</label><prompt>I have reference images</prompt></suggestion>
<suggestion><label>Upload Brand Kit</label><prompt>Use Brand Kit</prompt></suggestion>
<suggestion><label>No assets</label><prompt>No assets, create from concept</prompt></suggestion>
```

## Stage 3 — Business Goal and Audience (Optimization Direction)

Required fields:

| Field | Type | Default if missing |
|---|---|---|
| `optimization_target` | enum (engagement / awareness / conversion / lead) | `engagement` |
| `target_audience` | string or persona | `general` |

## Stage 4 — Style and Brand Constraints (Visual Style Rules)

Required fields:

| Field | Type | Default if missing |
|---|---|---|
| `style_direction` | enum (minimalist / editorial / lifestyle / high_impact / modern) | derived from industry table |
| `brand_colors` | list of hex | optional |
| `brand_fonts` | list of font names | optional |
| `brand_logo` | URL | optional |

Termination of Stage 4 transitions the state to `OUTPUT_BRIEF`.

## State Transitions

```
INIT
  → STAGE_1_TASK_SKELETON              (always)

STAGE_1_TASK_SKELETON
  → STAGE_2_VISUAL_ASSETS               (platform AND content_topic are set)
  → OUTPUT_BRIEF                        (skip if completeness > 0.8)

STAGE_2_VISUAL_ASSETS
  → STAGE_3_BUSINESS_GOAL               (visual_assets decision made)
  → OUTPUT_BRIEF                        (skip if completeness > 0.8)

STAGE_3_BUSINESS_GOAL
  → STAGE_4_STYLE_BRAND                 (optimization_target set)
  → OUTPUT_BRIEF                        (skip if completeness > 0.8)

STAGE_4_STYLE_BRAND
  → OUTPUT_BRIEF                        (style_direction set OR round_count >= 5)

OUTPUT_BRIEF
  → terminal: generate_brief_and_route
```

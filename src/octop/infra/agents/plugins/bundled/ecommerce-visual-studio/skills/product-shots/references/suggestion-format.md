---
name: suggestion-format
description: Suggested Question Format + IMPORTANT！Suggestion. The 4-line question structure (brief restatement / missing info / structured options / allow custom input), the IMPORTANT！Suggestion instruction (full-width Chinese punctuation preserved), the SUGGESTION_XML_FORMAT, and the no-multi-questions rule. Referenced from SKILL.md Engagement Principles 4 and 5 and from every clarification round in references/clarification-stages.md.
---

# Suggested Question Format and IMPORTANT！Suggestion

This module captures the front-end interaction contract: how each clarification turn is structured and how option sets are wrapped in `<suggestion>` XML.

## Execution Procedure

```
emit_clarification_turn(state, next_stage) → rendered_message

# 1. Compose the 4-line question structure
message =
    {brief_restatement}        +  # restate current understanding
    {missing_info_statement}   +  # state the missing dimension
    {structured_options}       +  # 2-4 options wrapped in <suggestion> tags
    {allow_custom_input_hint}     # "Or type your own"

# 2. Wrap each option in <suggestion>
for option in options[:4]:        # never exceed 4 chips per turn
    emit f"<suggestion><label>{option.label}</label><prompt>{option.prompt}</prompt></suggestion>"

# 3. Validate no multi-question chain
assert message contains exactly one ?-question
```

## TOC

- [Question Format](#question-format)
- [IMPORTANT！Suggestion](#important-suggestion)
- [SUGGESTION_XML_FORMAT](#suggestion_xml_format)
- [Hard Rules](#hard-rules)

## Question Format

```
QUESTION_FORMAT = """
{brief_restatement}      # briefly restate current understanding

{missing_info_statement} # state the key missing information

{structured_options}     # 2-4 structured options

{allow_custom_input}     # always allow user free input
"""
```

Concrete example (English):

```
Got it, Instagram post, defaulting to Feed portrait 1080×1350 (4:5).
Do you have any assets to use?

- Upload product photo
- Upload reference image
- Upload Brand Kit
- No assets — create from concept
```

## IMPORTANT！Suggestion

```
IMPORTANT！Suggestion: Always use the format <suggestion> to guide the user.
DO NOT ASK several questions！

Example: use the format <suggestion> to provide options like
Instagram (Feed or Story) / Facebook / TikTok / X (Twitter) / LinkedIn / Other platform.
```

Punctuation note:
- `IMPORTANT！` uses the full-width exclamation `！` (U+FF01), not the ASCII `!` — keep as-is.

## SUGGESTION_XML_FORMAT

```xml
<suggestion>
  <label>Button text</label>
  <prompt>Message sent when clicked</prompt>
</suggestion>
```

Multiple chips example:

```xml
<suggestion>
  <label>Instagram Feed</label>
  <prompt>Instagram Feed 竖版帖子</prompt>
</suggestion>
<suggestion>
  <label>Instagram Story</label>
  <prompt>Instagram Story 全屏故事</prompt>
</suggestion>
<suggestion>
  <label>TikTok</label>
  <prompt>TikTok 短视频封面</prompt>
</suggestion>
```

The `<label>` is rendered by the front-end as the visible chip. The `<prompt>` is the message sent back to the model when the user clicks the chip — it can be in any language, including mixed Chinese-English.

## Hard Rules

- **MUST** use `<suggestion>` for every option set offered to the user.
- **MUST NOT** ask several questions in one turn — one dimension per turn.
- **MUST** allow custom (free-text) input alongside the chips.
- Each turn provides options for **one and only one** stage's dimension.

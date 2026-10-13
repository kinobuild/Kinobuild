---
name: photography-style-presets
description: Section 2 of multi-angle-shots — the 3 Photography Style Presets (Preset A Retro Analog Flash, Preset B Soft Muted Film, Preset C Hard Flash Editorial) verbatim, plus the style-selection output format (3 preset images + 5 <suggestion> chips). Read at EP Step 3 when the user has not specified a style. Each preset is a long-form photography spec block (lighting / shadow / film grain / colour / material) that is repeated verbatim into every one of the 9 task prompts.
---

# Photography Style Presets

3 standardised photography styles, each a long-form `{PHOTOGRAPHY_STYLE}` block that is **repeated verbatim into every one of the 9 task prompts**. The presets cover three commercially distinct lighting moods (retro analog flash / soft muted film / hard flash editorial). Their implementation is a Markdown rendering convention — the agent emits the 3 preview images + 5 `<suggestion>` chips, and the front-end renders them as clickable cards.

## Execution Procedure

```
select_or_emit_presets(user_input, context) → chosen_style | pause_for_user

# Step 1 — does the user want to skip preset selection?
if has_explicit_style_specification(user_input)   → return user-described style
if has_style_reference_image(context)             → return derived-from-reference style

# Step 2 — pause and emit the 3-image + 5-chip selector (no code fence)
emit (verbatim, NO code-fence wrapper):
    **Photography Style Presets**:
    1. Retro Analog Flash: ![Retro Analog Flash](https://a.lovart.ai/artifacts/agent/0Z7LGqnS3z5aFBiE.png)
    2. Soft Muted Film:    ![Soft Muted Film](https://a.lovart.ai/artifacts/agent/IMKquu2RRK4EZg4Y.png)
    3. Hard Flash Editorial: ![Hard Flash Editorial](https://a.lovart.ai/artifacts/agent/haF9p4hEv08D5457.png)

    <suggestion>Use Preset A — Retro Analog Flash</suggestion>
    <suggestion>Use Preset B — Soft Muted Film</suggestion>
    <suggestion>Use Preset C — Hard Flash Editorial</suggestion>
    <suggestion>I'll describe my own style</suggestion>
    <suggestion>I'll upload a style reference image</suggestion>

# Step 3 — wait for user click; do NOT auto-pick a default
on user response → return chosen preset block (verbatim, full text)
```

## TOC

- [Selection Output (front-end rendering)](#selection-output-front-end-rendering)
- [Preset A — Retro Analog Flash](#preset-a--retro-analog-flash)
- [Preset B — Soft Muted Film](#preset-b--soft-muted-film)
- [Preset C — Hard Flash Editorial](#preset-c--hard-flash-editorial)

---

## Selection Output (front-end rendering)

When pausing for the user to choose a style, emit the following content **as plain Markdown — no code-fence wrapper**. The front-end parses this exact Markdown structure to render the three preset images as a clickable selector.

```
**Photography Style Presets**:
1. Retro Analog Flash: ![Retro Analog Flash](https://a.lovart.ai/artifacts/agent/0Z7LGqnS3z5aFBiE.png)
2. Soft Muted Film: ![Soft Muted Film](https://a.lovart.ai/artifacts/agent/IMKquu2RRK4EZg4Y.png)
3. Hard Flash Editorial: ![Hard Flash Editorial](https://a.lovart.ai/artifacts/agent/haF9p4hEv08D5457.png)
```

Then emit the 5 suggestion chips (also verbatim, no code fence):

```
<suggestion>Use Preset A — Retro Analog Flash</suggestion>
<suggestion>Use Preset B — Soft Muted Film</suggestion>
<suggestion>Use Preset C — Hard Flash Editorial</suggestion>
<suggestion>I'll describe my own style</suggestion>
<suggestion>I'll upload a style reference image</suggestion>
```

The 3 preset image URLs are hard-coded CDN assets owned by the skill (no external Kit / Brand Kit reference).

---

## Preset A — Retro Analog Flash

**适用场景**: 复古时尚、街头品牌、Y2K 风格

### 光源配置

```
主光源:
  类型: 机顶直射闪光灯
  色温: 5500K（略偏冷）
  功率: 中高档（模拟老式闪光灯过曝倾向）

辅助光:
  类型: 环境反射光（轻微）
  作用: 提亮阴影,避免纯黑

闪光灯特征:
  - 高光溢出区域: 额头/鼻梁/颧骨
  - 眼神光: 小而直接,非环形
```

### 阴影规范

```
投影特征:
  方向: 单一方向（与闪光灯一致）
  边缘: 清晰但柔化
  密度: 轻度（主体靠近背景板）

面部阴影:
  可见度: 可见
  提亮程度: 中度（避免死黑）
  对比度: 低（复古胶片特征）
```

### 后期效果

```
胶片模拟:
  颗粒: 细腻,ISO 400-800 等效
  暗角: 轻微,四角自然衰减
  色偏: 轻微暖调或冷调漂移

质感约束:
  - 禁止: CGI 感、过度锐化、数字清洁感
  - 保留: 皮肤毛孔、织物纹理、背景瑕疵
```

### 负面约束（禁止出现）

```
- 多方向阴影（表明多光源）
- 纯黑阴影（不符合胶片宽容度）
- 过度清晰的数字感
- 环形眼神光（表明使用环形灯）
```

---

## Preset B — Soft Muted Film

**适用场景**: 高端时尚、极简主义品牌、艺术摄影

### 光源配置

```
主光源:
  类型: 大型柔光箱（120cm+）
  位置: 正面偏上 45°
  扩散程度: 极高

环境光:
  强度: 高（显著环境填充）
  作用: 压缩动态范围,消除硬阴影
```

### 色彩规范

```
背景色:
  标准值: #f1eee9（浅奶油色）
  容差: ±5% 明度/饱和度

肤色处理:
  基调: 中性暖米灰
  与背景关系: 色调融合,无强烈分离
  饱和度: 降低 15-25%

整体色调:
  特征: 高调（high-key）
  动态范围: 压缩（无深黑/纯白）
```

### 材质规范

```
表面处理:
  反射类型: 完全漫反射
  高光: 禁止（所有材质哑光化）

视觉效果:
  质感: 扁平、绘画感
  胶片颗粒: 全画面均匀分布
```

### 情绪定位

```
氛围: 情感疏离、冷静、艺术化
照明特征: 极度均匀,无戏剧性
```

---

## Preset C — Hard Flash Editorial

**适用场景**: 时尚杂志、高端电商、视觉冲击力需求

### 光源配置

```
主光源:
  类型: 强方向性硬光（裸灯或窄角反射罩）
  方向性: 极强
  对比度: 高

关键约束:
  - 高光/阴影边界必须锐利
  - 阴影区域必须保留色彩信息（禁止纯黑）
```

### 阴影技术规范（核心）

```
阴影透明度:
  要求: 必须透明（luminous）
  色彩信息: 保留暖色调底色（深棕/红棕）
  细节保留: 阴影区域仍可见纹理

环境反射:
  作用: 填充阴影,防止信息丢失
  强度: 中度（不破坏硬光特征）

禁止状态:
  - 纯黑阴影（crushed blacks）
  - 泥泞色调（muddy tonality）
  - 阴影细节丢失
```

### 皮肤质感规范

```
表面特征:
  油光: 明显（模拟汗液/油脂）
  毛孔: 高清可见（受光区和阴影区均可见）

色彩对比:
  阴影区: 深棕色调
  受光区: 饱和度提升
  局部红润: 脸颊/鼻尖显示血色（sun-flushed）

高光处理:
  密度: 高（多处高光点）
  质感: 湿润、轻微过曝
  分布: 额头/鼻梁/颧骨/下巴
```

### 动态范围

```
宽容度: 类胶片宽容度（保留高光和阴影细节）
曝光倾向: 高调（high-key）但保留对比
```

---
name: task-prompts
description: Section 4 of multi-angle-shots — the 9 image task-prompt templates verbatim (Image 1 Three-Quarter Fashion Portrait through Image 9 Medium Portrait Opposing Torso Twist). Each entry carries its lens / crop / pose / hairstyle / accessory rules and the full English prompt template using {VARIABLE} placeholders. Read at EP Step 4 (template filling). Image 4 (back view) and Image 8 (side profile) are the CRITICAL hairstyle-validation views.
---

# Task Prompts — The 9 Images

The 9 image templates that compose the Model Consistency Series. Each carries:

- **Lens / camera spec** — focal length, depth-of-field, aspect ratio.
- **Crop spec** — upper/lower bounds with explicit forbidden body parts.
- **Pose spec** — body / hand / head / gaze rules.
- **Hairstyle / accessory spec** — what to assert verbatim (`{HAIRSTYLE} intact`, `NO loose hair`).
- **Prompt template** — the full English text with `{VARIABLE}` placeholders, ready for `.format(**extracted_vars)`.

> **CRITICAL** — Image 4 (back view) and Image 8 (side profile) are the dedicated **hairstyle-structure validation views**. Their prompts MUST include `NO loose hair, NO reinterpretation`. If either fails, the whole 9-image set is invalid (see `references/hard-constraints.md` Rule 3).

## Execution Procedure

```
fill_task_prompts(extracted_vars, photography_style) → prompts[1..9]

for image_id in 1..9:
    template = TASK_PROMPT[image_id]            # see §Image 1 ... §Image 9
    prompt = template.format(
        REFERENCE_IMAGE      = extracted_vars["REFERENCE_IMAGE"],
        SUBJECT_DESCRIPTION  = compose(extracted_vars),     # composed string, not a separate var
        HAIR_COLOR           = extracted_vars["HAIR_COLOR"],
        HAIRSTYLE            = extracted_vars["HAIRSTYLE"],
        SKIN_TONE            = extracted_vars["SKIN_TONE"],
        OUTFIT               = extracted_vars["OUTFIT"],
        BAG                  = extracted_vars["BAG"],
        JEWELRY              = extracted_vars["JEWELRY"],
        ASPECT_RATIO         = extracted_vars["ASPECT_RATIO"],
        BACKGROUND_COLOR     = extracted_vars["BACKGROUND_COLOR"],
        PHOTOGRAPHY_STYLE    = photography_style,           # full block, repeated verbatim
    )
    prompts.append(prompt)

# Mandatory invariants per prompt (see hard-constraints.md):
#   - [Reference image: {REFERENCE_IMAGE}] header present
#   - {PHOTOGRAPHY_STYLE} block repeated VERBATIM
#   - hairstyle-visible images carry "{HAIRSTYLE} intact" + "NO loose hair"
#   - image 4 + image 8 additionally carry "NO reinterpretation"
#   - image 5 carries "No accessories — frame doesn't reach them"

return prompts
```

## TOC

- [Image 1 — Three-Quarter Fashion Portrait](#image-1--three-quarter-fashion-portrait)
- [Image 2 — High-Angle Bird's-Eye View](#image-2--high-angle-birds-eye-view)
- [Image 3 — Over-the-Shoulder Close-Up](#image-3--over-the-shoulder-close-up)
- [Image 4 — Back View with Hairstyle Visible](#image-4--back-view-with-hairstyle-visible)
- [Image 5 — Extreme Facial Close-Up](#image-5--extreme-facial-close-up)
- [Image 6 — Over-Right-Shoulder Glance](#image-6--over-right-shoulder-glance)
- [Image 7 — Low-Angle Upward Gaze, Contrapposto](#image-7--low-angle-upward-gaze-contrapposto)
- [Image 8 — Side Profile, Chest Crop](#image-8--side-profile-chest-crop)
- [Image 9 — Medium Portrait, Opposing Torso Twist](#image-9--medium-portrait-opposing-torso-twist)

---

## Image 1 — Three-Quarter Fashion Portrait

**Purpose**: Editorial anchor shot (the lead frame of the series).

### Specs

```
镜头: 85mm 定焦
焦距等效: 中长焦人像镜头
景深: 中等（f/2.8-f/5.6）
画幅: {ASPECT_RATIO} 竖构图

裁切规范
上边界: 头顶上方留白 5-10% 画面高度
下边界: 大腿中部（膝盖以上 15-20cm）
裁切类型: 硬裁切（hard truncation）
禁止出现: 膝盖、小腿、脚

姿态规范
站姿:
  重心: 偏向一侧（非对称）
  躯干: 略微旋转（非正面平行）

手部:
  位置: 背后
  状态: 不对称（一手弯曲,一手伸展）

头部:
  朝向: 直视镜头
  表情: 疏离冷静

发型约束:
  状态: {HAIRSTYLE} 完整保持
  强制约束: "NO loose hair"
```

### Prompt Template (verbatim)

```
[Reference image: {REFERENCE_IMAGE}]

{SUBJECT_DESCRIPTION} — {HAIR_COLOR} hair in {HAIRSTYLE}, {SKIN_TONE}, wearing {OUTFIT}. Accessories: {BAG} over shoulder, {JEWELRY}.

85mm prime lens, {ASPECT_RATIO} vertical. Framed top of head to mid-thigh — hard truncation through thighs. No knees, lower legs, or feet.
Stable upright posture, weight shifted to one side. Torso rotated left for asymmetric silhouette. Hands behind back, asymmetric — one bent, one extended.
Direct eye contact, distant calm expression. {HAIRSTYLE} intact — NO loose hair.

{PHOTOGRAPHY_STYLE}
Studio backdrop: {BACKGROUND_COLOR}. No added accessories beyond reference.
```

---

## Image 2 — High-Angle Bird's-Eye View

### Specs

```
镜头: 35mm 广角
视角: 高角度 60-75°
透视: 广角畸变（foreshortening）

拍摄角度规范
相机位置:
  高度: 主体上方 1.5-2m
  水平偏移: 右上方偏移

光源对齐:
  闪光灯: 与相机同轴
  阴影方向: 单一方向（禁止多方向阴影）

姿态约束
身体状态:
  姿势: 站立（禁止平躺）
  验证方式: 检查重力方向（衣物下垂方向应向下）

手部:
  位置: 叉腰
  状态: 放松不对称

裁切规范
下边界: 大腿上部
裁切类型: 硬裁切
构图: 偏心（off-centered）

负面约束
禁止:
  - 水平躺姿（身体与地面平行）
  - 多方向阴影（表明多光源）
  - 正中心构图
```

---

## Image 3 — Over-the-Shoulder Close-Up

### Specs

```
镜头: 85mm 人像定焦
景深: 浅（f/1.8-f/2.8）
焦点: 眼睛

裁切规范
上边界: 头顶
下边界: 上胸部（严格胸部裁切）
禁止出现: 腹部、腰部

姿态规范
身体朝向: 背对镜头（显示背部/肩部）
头部动作: 急转向右,越过肩膀看镜头
转头幅度: 大角度（接近 90°）

表情: 冷静坚定
发型细节: 允许少量发丝拂过面部
发型约束: {HAIRSTYLE} 结构完整 — NO loose hair
```

---

## Image 4 — Back View with Hairstyle Visible

**Purpose (CRITICAL)**: 验证性构图 — 专门用于检验发型结构在背面视角的一致性。

### Specs

```
镜头: 85mm 定焦
画幅: {ASPECT_RATIO} 竖构图

裁切规范
上边界: 头顶
下边界: 臀线（hip line）
裁切类型: 严格臀线裁切
禁止出现: 大腿

姿态规范
身体朝向: 完全背对镜头（180° 背面）
站姿: 直立
手臂: 自然下垂于身体两侧
```

### 关键约束（CRITICAL）

```
发型验证:
  要求: {HAIRSTYLE} 从背面必须清晰可见且结构完整
  禁止: 散发、重新诠释发型结构
  Prompt 强制约束: "NO loose hair, NO reinterpretation"
```

---

## Image 5 — Extreme Facial Close-Up

### Specs

```
镜头: 105mm+ 微距镜头
景深: 极浅（f/1.4-f/2.0）
焦点: 眼睛

裁切规范（极端）
包含区域: 仅眼睛/鼻子/嘴唇
裁切掉: 额头、下巴、头部轮廓、肩膀、颈部
裁切类型: 超紧特写（ultra-tight）

构图规范
对称性: 非中心（off-center editorial asymmetry）
视线: 直视镜头
表情: 中性冷静

细节要求
皮肤纹理:
  清晰度: 高度细节化
  可见元素: 毛孔、细纹、睫毛、痣、雀斑

发丝处理:
  允许: {HAIR_COLOR} 发丝可能在画面边缘少量出现
  禁止: 显示完整发型轮廓

配饰约束
配饰显示: 无
原因: 画面范围未触及配饰位置
Prompt 说明: "No accessories — frame doesn't reach them"
```

---


---

## Images 6-9

Split into `references/task-prompts-6-9.md` to keep this file under the 300-line cap. Same {VARIABLE} substitution rules apply.

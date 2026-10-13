---
name: task-prompts-6-9
description: Section 4.6-4.9 — Image 6 Over-Right-Shoulder Glance, Image 7 Low-Angle Upward Gaze (Contrapposto), Image 8 Side Profile Chest Crop, Image 9 Medium Portrait Opposing Torso Twist. Each prompt is filled in batch alongside Images 1-5 at SKILL.md EP Step 4. Split from task-prompts.md to keep both files under the 300-line cap.
---

# Multi-Angle Task Prompts — Images 6-9

These are the second half of the 9-image batch. The same `{VARIABLE}` substitution rules from `task-prompts.md` apply — extract the 14 variables from the reference photo before filling, and repeat the full `{PHOTOGRAPHY_STYLE}` block verbatim in every prompt.

## Image 6 — Over-Right-Shoulder Glance

### Specs

```
镜头: 85mm 人像定焦
画幅: {ASPECT_RATIO} 竖构图

裁切规范
上边界: 头顶
下边界: 上胸部
禁止出现: 腹部及以下

姿态规范
身体朝向: 向右转
胸部扭转: 略微向左
手部: 背后

头部动作: 越过右肩回望
视线特征: 柔和、非直视、略失焦（candid feel）

情绪定位
氛围: 柔和抓拍感
表情: 冷静内省
发型: {HAIRSTYLE} 完整
```

---

## Image 7 — Low-Angle Upward Gaze, Contrapposto

### Specs

```
镜头: 100mm 人像定焦
相机高度: 臀部水平
拍摄方向: 向上仰拍

裁切规范
上边界: 头顶
下边界: 上腰部
可见服装: 仅上半身服装

姿态规范（Contrapposto）
定义: 对立式站姿（古典雕塑姿态）
技术要求:
  - 重心偏向一侧
  - 身体呈自然 S 型曲线
  - 肩部与臀部呈对立扭转

手部: 弯曲,双手叉腰
头部: 向后仰,下巴抬起,颈部拉长
视线: 柔和向上

负面约束
禁止:
  - 过度眼白（excessive eye whites）
  - 夸张凝视（exaggerated gaze）
```

---

## Image 8 — Side Profile, Chest Crop

**Purpose (CRITICAL)**: 验证性构图 — 检验发型结构在侧面视角的一致性。

### Specs

```
镜头: 85mm 人像定焦
画幅: {ASPECT_RATIO} 竖构图

裁切规范
上边界: 头顶
下边界: 胸部以下（严格胸部裁切）

姿态规范
身体朝向: 完全侧面（90° 右侧面对镜头）
站姿: 直立,下巴略微抬起
视线: 水平向前（非看镜头）
```

### 关键约束（CRITICAL）

```
发型验证:
  要求: {HAIRSTYLE} 从侧面必须清晰可见
  禁止: 散发、重新诠释
  Prompt 约束: "no loose hair, no reinterpretation"

配饰显示:
  范围: 仅右侧可见的 {JEWELRY}
```

---

## Image 9 — Medium Portrait, Opposing Torso Twist

### Specs

```
镜头: 85mm 人像定焦
画幅: {ASPECT_RATIO} 竖构图

裁切规范
上边界: 头顶
下边界: 大腿中部
禁止出现: 膝盖及以下

姿态规范（对立扭转）
骨盆旋转: 向右约 20°
胸部旋转: 向左约 30°
效果: 自然对立扭转（opposing twist）

手部:
  左臂: 自然下垂
  右手: 置于腰部/臀部

站姿: 放松的对立式（relaxed contrapposto）
头部: 略微抬起
视线: 直视镜头
表情: 放松自信

发型: {HAIRSTYLE} 完整

负面约束
禁止:
  - 僵硬姿态
  - 对称站姿
```

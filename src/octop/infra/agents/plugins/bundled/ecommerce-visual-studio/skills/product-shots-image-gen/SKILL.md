---
name: product-shots-image-gen
description: "出图引擎。把一个 prompt 转成一次内置 generate_image 调用。"

license: MIT
metadata:
  author: motiful (adapted for KinoGuild)
  source: product-shots ecosystem
  skill_id: product_shots_image_gen
  adapter: octop-native
  version: "1.0-octop"
  octop:
    emoji: "⚙️"
---

# Image Gen — KinoGuild 原生出图引擎

其他 product-shots 技能（main-image / detail-page / ad-creative / social-post / multi-angle）
最终都会走到这一步：**把写好的 prompt 交给内置 `generate_image` 工具**。

**没有网关、没有 API key、没有脚本。** 出图后端由管理员在
「设置 → 模型 → 生成模型」里统一配置，本技能只负责把 prompt 写对、把参数传对。

## 唯一要做的事

```
generate_image(
    prompt            = "<主 prompt>。Avoid: <负向约束>",
    reference_images  = ["<参考图路径>", ...],   # 只在图生图/改图时需要
    size              = "<1:1 | 3:4 | 4:3 | 16:9 | 9:16 | 1024x1024 | ...>",
    count             = <张数>,
    watermark         = False,                   # 上架用图必须关水印
)
```

**参数映射**（生态内契约 → KinoGuild 工具）：

| 生态契约里的字段 | KinoGuild 工具参数 | 说明 |
|---|---|---|
| `prompt` | `prompt` | 直接传 |
| `negative_prompt` | 合并进 `prompt` | 写成 `。Avoid: a, b, c` 追加在末尾 |
| `model` | **省略** | 用默认路由；不要指定模型名 |
| `aspect_ratio` | `size` | `"1:1"` / `"3:4"` / `"16:9"` 等原样传 |
| `reference_images` | `reference_images` | 传工作区内的文件路径列表 |
| `output` / `output_path` | **省略** | 工具返回的图由媒体管线自动交付给用户 |
| 批量张数 | `count` | **用户指定了就照做**，没说才默认 4 |

## 三条硬规则

1. **工具不可见时先 `tool_search`。** 它可能以「延迟引用」形式出现（描述末尾带
   `[Deferred reference: call tool_search before use.]`）。载入后再调用。
2. **绝不自己写脚本调图像 API。** 读 `~/.octop/octop.db`、解密凭据、`httpx` 下载、
   自己拼输出路径——这些产物不受媒体管线管理，**交付不出去**，用户什么都收不到。
   历史上就是这样空烧 85 万 token 的。
3. **不要拼输出路径。** 工具的返回值就是交付物，不要再用 `send_file_to_user`
   去发一个自己算出来的路径（`stem[-13:]` 之类的截断会把目录名拼错）。

## 工具确实不存在时

说明媒体生成没启用，或当前会话是在启用前开的。**直接告诉用户**：

> 需要先在「设置 → 模型 → 生成模型」里启用媒体生成并配置一个出图供应商，
> 然后新开一个对话再试。

然后停下。不要找替代方案。

## 参考图处理

- 图生图**必须**带 `reference_images`，路径用工作区相对路径（如 `inbound/xxx.png`）。
- 提示词里把**保真声明放在最前面**，逐项列明不许变的商品特征——写法见
  `product-shots-main-image` 与 `fission-pattern` 的示例：它们把「不变」拆成了
  可核对的具体项（形状、比例、镜头开孔、logo 拼写、配件数量）。
- 图像模型可能不遵守 `size`（曾出现请求 1024×1024 返回 2048×2048）。**交付前核对实际像素**，
  需要平台规格就基于已交付的图做规格化，而不是自己重新下载出图。

## 交付

出图后**用工具返回的图片交付**，并说清：出了几张、什么规格、加没加文案。

本技能被其他技能调用时，交付话术由**调用方**负责，本技能只交出图片。

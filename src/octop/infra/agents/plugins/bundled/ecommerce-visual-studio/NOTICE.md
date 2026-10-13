# 第三方技能来源与许可

本插件中的以下技能由第三方开源项目改编而来，均为 **MIT License**，原始版权归原作者所有。
按 MIT 条款，此处保留版权声明与许可说明。

## motiful/product-shots

- 来源：https://github.com/motiful/product-shots
- 许可：MIT — Copyright (c) 2026 motiful
- 改编内容：`product-shots`、`product-shots-main-image`、`product-shots-detail-page`、
  `product-shots-multi-angle`、`product-shots-ad-creative`、`product-shots-social-post`。
  在每份技能头部加入 Octop 调用映射说明；`product-shots-image-gen` 由原网关脚本版
  重写为内置 `generate_image` 适配版（原 `scripts/generate.py` 已移除）。

## dlazy-ai/ecommerce-skills

- 来源：https://github.com/dlazy-ai/ecommerce-skills
- 许可：MIT — Copyright (c) 2026 dlazy
- 改编内容：`item-detail`、`platform-compliance`、`fission-pattern`。
  在每份技能头部加入 Octop 调用映射说明；移除 dlazy CLI 网关脚本
  （`gen.mjs` / `brand.mjs` / `lib/providers.mjs` / `lib/miniyaml.mjs` / `lib/tasks.json`）。
  `platform-compliance/scripts/check_listing.py` **原样保留** —— 它只依赖标准库与 Pillow，
  与出图后端无关，可直接独立运行。

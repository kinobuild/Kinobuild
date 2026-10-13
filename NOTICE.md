# 修改声明（NOTICE）

本仓库是 **Octop**（https://github.com/TencentCloud/Octop）的修改版，按 MIT License 分发。
原始版权归 Octop 及其贡献者所有，完整许可文本见 `LICENSE`。

本仓库对其做出的修改如下（按 MIT 要求声明）：

## 1. 品牌更名与资产替换

用户可见的品牌由 `Octop` 改为 `KinoGuild`。涉及：

- 前端与后端 locale 文案（`dashboard/src/locales/`、`src/octop/i18n/`）
- 站点标题、PWA manifest、应用名
- Logo、图标、托盘图标、PWA 图标、飞牛 NAS 图标等品牌资产
- 头像菜单中的外部链接（帮助反馈 / 项目地址）改为构建期可配置，
  未配置时隐藏，不再指向上游站点

内部技术标识符（`octop` CLI 命令、`~/.octop` 数据目录、`OCTOP_*` 环境变量、
`octop-*` 依赖包名、技能包 id 等）**刻意保留**，以保证升级路径与用户数据不受影响。

## 2. 新增：OpenAI 兼容出图供应商

新增 `src/octop/infra/agents/settings/openai_media_provider.py`，使媒体生成可接入
任意 OpenAI 格式的图片中转站（`/v1/images/generations` 与 `/v1/images/edits`），
并在 `media_generation.py` 中注册 `openai` 预设。

## 3. 修复：模型能力元数据丢失

`src/octop/infra/agents/providers/probe.py` 原先在解析供应商 `/models` 响应时
只保留 `id` 与 `name`，丢弃了 `input_modalities`（视觉能力）、`context_window`、
`max_output_tokens`。这导致支持图像输入的模型被当作纯文本模型，带图片的对话
不会被路由到它。现已保留这些字段。

## 4. 修改：PWA 更新策略

`dashboard/vite.config.ts` 的 Workbox `skipWaiting` 由 `false` 改为 `true`，
使新版本 Service Worker 自行激活，避免用户不点更新横幅就永远停留在旧缓存。

## 5. 新增：电商视觉专家与插件

- 专家：`src/octop/infra/agents/experts/library/ecommerce-visual/`
- 插件：`src/octop/infra/agents/plugins/bundled/ecommerce-visual-studio/`

该插件集成了以下第三方技能（均为 MIT，署名见插件内 `NOTICE.md`）：

- https://github.com/motiful/product-shots — Copyright (c) 2026 motiful
- https://github.com/dlazy-ai/ecommerce-skills — Copyright (c) 2026 dlazy

## 6. 文档

- `README.md` 替换为 KinoGuild 的说明。
- 上游原始 README 保留为 `README_UPSTREAM.md` 与 `README_UPSTREAM_CN.md`，未作改动。

## 7. 移除：`general-assistant` 的 `octop-assistant` 技能

**改动**：删除 `src/octop/infra/agents/experts/library/general-assistant/skills/octop-assistant/`
（623 行），该专家不再携带任何技能。

**原因**：`general-assistant` 是 `DEFAULT_EXPERT_ID`，每个新用户的第一个 agent 都是它。
上游给这个专家只配了一个技能，而这份 623 行文档的前 ~80 行是产品 README 的逐字搬运
（亮点表、入口、安装）。控制台的「个性化 → 技能」会原样渲染 SKILL.md，
于是终端用户打开就能看到一份上游产品宣传册 —— 对一个已改名的 fork 来说观感很差，
而且对普通用户毫无用处：他们既不是管理员，也改不了模型与通道，那份文档的后 500 行
CLI 配置指导对他们不适用。

**合并提示**：上游在持续维护该技能（例如 #1311）。合并回来时目录会被 git 还原，
需要再次删除。`tests/unit/agents/test_general_assistant_template.py` 中有一条
`test_upstream_product_brochure_skill_is_not_shipped` 会因此失败 —— **不要删这条测试**，
删掉技能目录即可。

**已建 agent**：模板改动只影响新建 agent。已存在的 agent 工作区里是拷贝，
需要通过 `DELETE /api/agents/{agent_id}/skills/octop-assistant` 软删除
（写 `removed: true` 标记，列表即不再显示）。

## 版权归属

- 基础代码：Copyright (c) 2026 Octop（Tencent Cloud）— 完整 MIT 文本见 `LICENSE`
- 本仓库的修改：Copyright (c) 2026 kinobuild

MIT 许可不包含商标授权；「KinoGuild」名称与标识不随代码一并授予。

## 上游同步

本仓库不追踪上游。如需合并上游改动，请手动处理。

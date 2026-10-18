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

## 8. 新增：知识工作专家模板（来源 Apache-2.0）

上游在本仓库中加入了四个专家模板，`manifest.json` 自带来源标记
`{"type": "knowledge-work-plugins", "plugin": "<名称>"}`：

- `productivity`、`design`、`engineering`、`cowork-plugin-management`

**来源与许可**：`https://github.com/anthropics/knowledge-work-plugins`，
**Apache License 2.0**（官方仓库根目录 `LICENSE`，且 `productivity/`、
`cowork-plugin-management/` 各自带有同版本的 `LICENSE` 文件）。
Apache-2.0 允许修改与再分发，条件是随附许可副本并注明改动 ——
官方转换进本仓库时没有把 `LICENSE` 带过来，本节即为补齐。

**本仓库对其中两份做的修改**（Apache-2.0 §4(b) 要求注明）：

- `library/productivity/`（6 个文件）：把技能里要求在工作区创建的
  `CLAUDE.md` 一律改为本平台的 `MEMORY.md`；`${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html`
  改为工作区相对路径 `skills/dashboard.html`（该变量在本平台没有任何地方注入，
  原样保留会让技能里那一步永远失败）；技能正文中以第三方产品名自称的措辞改为
  中性表述；`skills/dashboard.html` 内与之配对的 JS 标识符同步改名。
- `library/ai-coding-coach/`（3 个文件）：同样把 `CLAUDE.md` 改为
  `AGENTS.md` / `MEMORY.md`。该专家正文中把「Claude Code」等作为**评测对象**
  提及的内容未作改动 —— 那是它的职责所在。

## 9. 办公文档技能：第三方 source-available，本仓库未修改

`library/office-automation/skills/{docx,xlsx,pptx,pdf}/`（186 个文件）来自
`https://github.com/anthropics/skills` 的文档技能。**这些目录不是开源代码**：
官方 README 明确写为 *source-available, not open source*，每个目录内自带
`LICENSE.txt`（© 2025 Anthropic, PBC），其中禁止制作衍生作品与再分发。

因此：

- 本仓库**没有修改**这些文件，逐字节与上游一致（`pack.py`、`LICENSE.txt`
  的 SHA 已核对）。第 1 节的整体 MIT 声明**不覆盖**这几个目录，
  它们的许可以目录内的 `LICENSE.txt` 为准。
- 需要调整它们的行为时，改 `office-automation/SOUL.md`（在受限目录之外，
  归本仓库管辖），不要改技能文件本身 —— 见第 10 节。
- 商用适配性由本项目方另行核实；本节只作事实标注。

## 10. 修改：办公专家交付文档的署名规则

`library/office-automation/SOUL.md` 增加一条 sign-off 规则：交付文档的修订与
批注必须显式署名（`--author` / `--initials` / `w:author` 由模型自己填），
不得沿用受限技能脚本的内置默认值或示例里的占位名；`w:date` 用真实时间。

**原因**：`docx` 技能的脚本与示例把作者默认值写成了第三方产品名，
用户导出的 `.docx` 在 Word 的审阅窗格里会显示那个名字。那些文件受第 9 节的
许可约束不能改，所以在专家层拦住。

## 版权归属

- 基础代码：Copyright (c) 2026 Octop（Tencent Cloud）— 完整 MIT 文本见 `LICENSE`
- 本仓库的修改：Copyright (c) 2026 kinobuild
- **例外**：`library/office-automation/skills/{docx,xlsx,pptx,pdf}/` 按其目录内
  `LICENSE.txt`（Anthropic source-available）分发，不在上述 MIT 声明范围内；
  `library/{productivity,design,engineering,cowork-plugin-management}/` 的原始
  材料为 Apache-2.0（见第 8 节）。

MIT 许可不包含商标授权；「KinoGuild」名称与标识不随代码一并授予。

## 上游同步

本仓库不追踪上游（`upstream` 仅作参考）。合并上游改动时按下面五步走：

1. **合并**：`git merge --no-ff upstream/main`。保留合并提交，日后才分得清
   哪些来自上游、哪些是本仓库的改动。
2. **删回上游宣传技能**：上游会把 `general-assistant/skills/octop-assistant/`
   带回来（见第 7 节）。`tests/unit/agents/test_general_assistant_template.py`
   会因此失败——**删目录，不要删测试**。
3. **跑品牌兜底测试**：`pytest tests/unit/agents/test_content_branding.py`。
   它覆盖后端 i18n、专家与插件模板、前端 `dashboard/src/locales/`、
   连接器描述 `src/octop/infra/connectors/catalog.json`，命中上游品牌名即失败。
   同一文件还守**竞品痕迹**（`CLAUDE.md`、`${CLAUDE_PLUGIN_ROOT}`）：上游会把
   为 Claude 生态写的模板直接搬进来，这类内容会让模型在**用户的工作区**里创建
   竞品命名的文件，界面上用户看得见。
   上游有时会用**测试**钉住品牌字样（b9 的 `test_business_operations_template.py`
   就断言每个 `SKILL.md` 含「已为 Octop 改编」），于是和第 3 步对撞。改测试里的
   **字样**、保留断言本身（署名意图仍然被守），不要反过来在交付文案里留上游品牌名。
4. **核对锁文件**：`pytest tests/unit/test_lockfile_matches_pyproject.py`。
   上游抬高了 `pyproject.toml` 里 `octop-*` 的下限，而合并冲突很容易把
   `uv.lock` 解成我们的旧版；`docker/Dockerfile` 用 `uv sync --frozen`，
   它完全信任锁文件，装错版本等于启动即错。
5. **重扫没有测试守着的用户可见文案**：CLI 帮助与横幅（`src/octop/cli/**`）、
   首启向导横幅（`src/octop/infra/server.py`）、飞书机器人问候语
   （`src/octop/infra/gateway/bot_creators/`），以及前端里硬编码的字符串。
   这几处目前没有人守，只能靠人看。
6. **复核专家抑制名单**：`src/octop/infra/agents/experts/catalog.py` 的
   `_SUPPRESSED_EXPERT_IDS`。上游新带的专家如果在本平台交付不出可用产物
   （例如只产出一个 Claude 插件包的 `cowork-plugin-management`），把 id 加进
   名单，**不要改那个专家自己的 `manifest.json`** —— 改了下次合并会被上游覆盖，
   卡片会悄悄重新上架。名单同时决定第 3 步竞品扫描的范围：被抑制的专家不对外
   提供，其文案因此不在检查之列。
7. **核对迁移号**：迁移号是两个仓库各写各的，**撞号必炸而 git 不会报冲突**（文件名不
   同）—— `_list_migrations` 见到重复号直接抛 `RuntimeError`
   （`src/octop/infra/db/migrate.py:57`），服务启动即失败。本仓库的
   `021_invite_multi_use` 已随 1.0.2b8 上到生产、库里水位就是 21，因此上游 b9 的
   `021_skill_package_download` 改名为 `022_…`。要跟着一起改：两份 SQL 里的
   `UPDATE _schema_version SET version = 22`、`migrate.py` 的 SQLite 分支与水位钳回阶梯
   （`max_version >= 22`）、`tests/unit/db/*` 和 `tests/unit/backup/test_system_archive.py`
   的版本断言。**不要反过来改我们的 021**：生产库已经应用过它，重跑
   `ALTER TABLE … ADD COLUMN` 会报重复列。上线后核对
   `select version from _schema_version` 应为 22、`skill_packages` 应多出 `allow_download`。

第 2～4 步、第 6 步和第 7 步都有测试兜底；第 5 步没有。合并后若 `uv.lock` 有变化，部署时
必须把锁文件一起同步到服务器（见 `DEPLOY.md` 第 3.5 节）。

**许可核对**：上游每次带进第三方技能，先看它目录里有没有 `LICENSE.txt`，再决定
能不能改。`anthropics/skills` 是**混合许可**仓库 —— 大部分技能是 Apache-2.0
（可改、可分发，需保留声明），但 `docx`/`xlsx`/`pptx`/`pdf` 这四个文档技能是
source-available，明文禁止衍生作品与再分发（见第 9 节）。撞见后者的正确做法是
**在专家层（`SOUL.md`）拦住行为，不动技能文件本身**。

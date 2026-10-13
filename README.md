# KinoGuild

**面向企业私有化部署的自托管 AI 助手平台 —— 中文电商视觉是它的一等公民能力。**

单进程部署，一个 `octop run` 同时跑起 Dashboard、CLI、IM 通道与定时任务，
全部数据落在 `~/.octop/`。不需要外部队列，除 LLM 供应商外无强制依赖。

> 本项目基于 [Octop](https://github.com/TencentCloud/Octop)（Tencent Cloud，MIT）二次开发。
> 对上游的修改逐项列在 [NOTICE.md](NOTICE.md)。

---

## 和上游的区别

| | Octop | KinoGuild |
|---|---|---|
| 品牌与界面 | Octop | **KinoGuild**（含 Logo / 图标 / PWA 应用名） |
| 出图后端 | 火山方舟 / 百炼 / MiniMax | **额外支持任意 OpenAI 格式中转站**（`/v1/images/generations` + `/v1/images/edits`） |
| 视觉模型识别 | 只按模型名关键词猜测 | **读取供应商 `/models` 的 `input_modalities`** —— 带图片的对话能正确路由到视觉模型 |
| 电商视觉 | — | **11 个技能包 + 「图匠」专家**，覆盖主图 / 详情页 / 多角度 / 广告图 / 社媒图 / 合规校验 |
| PWA 更新 | 用户不点横幅就永远停在旧缓存 | **新版本 Service Worker 自动激活** |
| 头像菜单外链 | 硬编码指向上游官网与仓库 | **构建期可配置**，未配置则隐藏 |

内部技术标识（`octop` 命令、`~/.octop` 数据目录、`OCTOP_*` 环境变量、`octop-*` 依赖包名）
**刻意保持原样**，以保证升级路径与既有用户数据不受影响。

---

## 核心能力：中文电商视觉

电商主图最容易被忽略的一点：**AI 能不能把中文写对**。KinoGuild 的默认路线是
**把文案写进 prompt，让生图模型连同商品、背景、光线一起渲染** —— 字和画面共用同一套
光影与透视，而不是后期贴上去的贴纸。

实测（`gpt-image-2.5`，经 OpenAI 格式中转站）：

> prompt：`上方粗黑体大字「军工级防摔」，下方小字「1.5米跌落无损 · 亲肤不沾灰」，中文字必须清晰、笔画完整、无错字、无乱码`
>
> 结果：字字正确、笔画完整、排版规整。

### 内置技能包

| 技能 | 用途 |
|---|---|
| `ecommerce-main-image` | 主图 / 场景图，商品保真红线 + 平台规格 |
| `item-detail` | 带中文排版的详情页模块 |
| `fission-pattern` | 一张商品图裂变成整套素材 |
| `product-shots-main-image` | 亚马逊主图 + 7 种副图 |
| `product-shots-detail-page` | A+ 详情页模块 |
| `product-shots-multi-angle` | 多角度商品图 |
| `product-shots-ad-creative` | 广告创意图 |
| `product-shots-social-post` | 社媒图 |
| `platform-compliance` | 上架前平台合规校验（含可独立运行的检查脚本） |
| `product-shots-image-gen` | 出图引擎，对接内置 `generate_image` |
| `product-shots` | 意图路由 |

技能包默认**全局关闭**，管理员在 Dashboard 的插件页启用后，再按 Agent 逐个开启。

### 「图匠」专家

内置的电商视觉专家人格（`ecommerce-visual`），职责是**守住商品保真**：

- 商品的颜色、材质、纹理、结构、logo 与文字**一个像素都不许改**
- 拿不到真实卖点就**问用户**，不编功效词（防摔 / 防水写错就是虚假宣传）
- 拿不到真实卖点也**不拿"新品上架"充数** —— 那不是卖点
- 出图后做**视觉自检与 OCR 复检**，发现跑偏就重出

---

## 快速开始

### 环境要求

- Python **3.12+**
- Node.js 20+（仅从源码构建前端时需要）

### 1. 安装

```bash
git clone https://github.com/kinobuild/legendary-octo-couscous.git
cd legendary-octo-couscous
uv sync
```

或使用 pip：

```bash
pip install .
```

### 2. 初始化

```bash
octop init
```

首次运行会引导创建管理员账号，初始密码写入 `~/octop-login.txt`。

### 3. 启动

```bash
octop run                          # 默认 127.0.0.1:8088
octop run --host 0.0.0.0 --port 8088   # 对外提供服务
```

打开 `http://127.0.0.1:8088` 即可使用。

### 4. 配置出图（可选）

「设置 → 模型 → 生成模型」→ 启用媒体生成 → 添加供应商。

选择 **OpenAI 兼容中转站**，填 API 地址（形如 `https://your-relay.example.com/v1`）
与 API Key，再选图像模型即可。中转站需支持 `/v1/images/generations`
（图生图还需 `/v1/images/edits`）。

---

## 常用命令

```bash
octop run                 # 启动服务
octop plugin list         # 查看插件
octop plugin install <路径>  # 安装插件
octop agent list          # 列出智能体
octop chats send --agent <id> "…"   # 命令行发消息
octop user passwd <用户名> --password <新密码>
```

## 从源码构建

```bash
make build-frontend   # dashboard/ → src/octop/dashboard/
make build-wheel      # 打包
make test             # 测试
```

---

## 目录结构

```
src/octop/            Python 包
  api/                FastAPI 路由
  cli/                Click 命令行
  infra/              领域核心（agents / db / gateway / …）
  i18n/               后端文案（zh / en）
  dashboard/          前端构建产物（由 dashboard/ 生成，不入库）
dashboard/            前端源码（React + TS + Vite）
tests/                pytest
docs/                 参考文档
```

---

## 许可

本项目以 **MIT License** 分发，见 [LICENSE](LICENSE)。

- 基础代码：Copyright (c) 2026 **Octop**（Tencent Cloud）
- 本仓库的修改：Copyright (c) 2026 **kinobuild**

对上游的修改逐项声明见 [NOTICE.md](NOTICE.md)。

MIT 许可**不包含商标授权** —— 「KinoGuild」名称与标识不随代码一并授予。

## 致谢

本项目的电商视觉能力建立在以下开源项目之上，均为 MIT 许可：

- [motiful/product-shots](https://github.com/motiful/product-shots) — Copyright (c) 2026 motiful
- [dlazy-ai/ecommerce-skills](https://github.com/dlazy-ai/ecommerce-skills) — Copyright (c) 2026 dlazy

完整署名见 `src/octop/infra/agents/plugins/bundled/ecommerce-visual-studio/NOTICE.md`。

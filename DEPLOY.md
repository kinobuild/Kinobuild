# KinoGuild 部署交接说明

> 本文档面向负责服务器运维的智能体/工程师。读完本文应能独立完成一次公网部署。

## 1. 项目信息

| 项 | 值 |
|---|---|
| 仓库 | `git@github.com:kinobuild/Kinobuild.git` |
| 分支 | `main` |
| 本机路径 | `/Users/mima1234/Documents/deepseek-harness/default-workspace/Octop` |
| 上游 | `TencentCloud/Octop`（MIT 许可，本项目为其 fork 并改名 KinoGuild） |
| 版本 | `pyproject.toml` → `1.0.2b8` |
| 语言栈 | Python 3.12+ / FastAPI / uvicorn；前端 React 18 + TS + Vite + AntD |
| 数据库 | SQLite（WAL，默认）或 PostgreSQL，单进程 |

## 2. 这是什么

自托管的多用户 AI 助手平台。本次部署的核心用途是让**外部用户试用「一句话出电商主图」**能力。

关键能力：
- 多用户 + 角色 + 配额（token 配额、**生图张数配额**）
- 邀请码注册（管理员生成码，受邀者自己设用户名密码）
- 出图专家模板：`快图`（一句话出图）、`图匠`（详情页/批量）
- 电商视觉插件（内置，含 11 个技能）

## 3. 部署方式

推荐 **Docker Compose**。仓库已自带：

```
docker/docker-compose.yml           # 主入口（SQLite）
docker/docker-compose.postgres.yml  # PostgreSQL 变体
docker/Dockerfile                   # 多阶段构建：node 打前端 → python 运行时
docker/docker-entrypoint.sh         # 首次启动自动 octop init
docker/README_CN.md                 # 官方部署说明
```

### 3.1 构建与启动

```bash
git clone git@github.com:kinobuild/Kinobuild.git
cd Kinobuild

# 国内加速（建议，否则 npm/pip 很慢）
PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple \
PIP_TRUSTED_HOST=mirrors.cloud.tencent.com \
NPM_REGISTRY=https://mirrors.cloud.tencent.com/npm/ \
APT_MIRROR=mirrors.cloud.tencent.com \
docker compose -f docker/docker-compose.yml up -d --build
```

**构建资源**：前端构建阶段需要约 2GB 内存（`NODE_MAX_OLD_SPACE_SIZE=2048`，可通过 build arg 调整）。运行阶段很轻。

### 3.2 配置文件

在 `docker/` 下建 `.env`：

```ini
OCTOP_PORT=8088
OCTOP_ADMIN_USERNAME=admin
OCTOP_DEFAULT_PASSWORD=<强密码：≥8 位且含字母和数字>
OCTOP_DATA=/opt/octop-data
OCTOP_LOG_LEVEL=info
```

⚠️ **密码必须满足策略**（≥8 位 + 字母 + 数字），否则会被拒绝并**静默回退为随机密码**写入 `/data/.octop/credential.txt`。不设 `OCTOP_DEFAULT_PASSWORD` 时也会随机生成。

⚠️ `docker/.env` 只参与 Compose 插值。**变量必须出现在 `docker-compose.yml` 的 `environment:` 块里才会进容器** —— 新增变量时要两处都改。

### 3.3 数据持久化

Compose 把宿主机 `${OCTOP_DATA}` 挂载到容器 `/data/.octop`。**这个目录就是全部状态**：数据库、用户、agent 工作区、上传文件。备份=备份这个目录。

### 3.4 健康检查

镜像内置 `HEALTHCHECK`，探测 `GET /api/health`。

### 3.5 `uv.lock` 的正确处理（重要）

`uv.lock` 里 246 个包全部指向 `pypi.org`。**这是对的，不要改写它。**

### 为什么不要「套镜像源」

镜像加速是**构建时**的事，不是源码的事。把 `uv.lock` 改成镜像地址会带来两个问题：

1. **服务器上的锁与仓库不一致** —— 排查依赖问题时无法判断实际装的是哪一份。
2. **每次部署都要手工套源** —— 漏一步就会退回 `pypi.org`（慢）或停留在旧锁（更糟：装了旧 `octop-harness`）。

实测（干净 `uv` 缓存 + 把 `UV_INDEX_URL` 指向不存在的域名）：

```
error sending request for url (https://<fake-host>/simple/setuptools/)
```

⇒ `UV_INDEX_URL` **确实能重定向 `--frozen` 安装**，即使锁里写的是 `pypi.org`。
因此保留 canonical 锁 + 构建参数即可，无需改写锁文件。

### 部署要点

- **`uv.lock` 必须同步到服务器**。若 rsync 规则里有 `--exclude uv.lock`，**去掉它**。
  `uv sync --frozen` 完全信任锁文件；不同步 = 永远安装旧依赖（本次升级的
  `octop-harness 1.0.2` / `octop-memory 1.0.1` 就装不上）。
- 构建时用镜像参数，不改文件：

```bash
docker compose -f docker/docker-compose.yml build \
  --build-arg PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple \
  --build-arg PIP_TRUSTED_HOST=mirrors.cloud.tencent.com \
  --build-arg NPM_REGISTRY=https://mirrors.cloud.tencent.com/npm/
```

Dockerfile 会把 `PIP_INDEX_URL` 转成 `UV_INDEX_URL`（见 `docker/Dockerfile` 的 `uv sync` 步骤）。

### 3.6 实际部署布局与构建耗时（2026-10-16 ~ 10-17 实测）

**本服务器不是 git clone**，而是一份同步过去的源码副本 + 固定叠加的 override：

```
/opt/kinoguild/src/                      # 源码副本（不是 git 仓库）
/opt/kinoguild/src/docker/.env                       # 服务器独有，不在 git 里
/opt/kinoguild/src/docker/docker-compose.override.yml # 服务器独有，不在 git 里
/opt/kinoguild/data/  →  容器 /data/.octop            # 全部状态，别动
/opt/kinoguild/compose.sh                # 固定 -f docker-compose.yml -f …override.yml
```

同步用 `git archive HEAD | ssh … tar -x` 到 `src.new`，**先把 `.env` 和
`docker-compose.override.yml` 拷回去**再换目录 —— 这两个文件不在 git 里，
`rsync --delete` 会把它们删掉。构建走 `docker/docker_build.sh`（已含镜像参数），
换镜像前先 `docker tag octop:latest octop:rollback-<短 id>` 留回滚锚点。

⚠️ **`git archive` 的保护只在"没被跟踪"时才成立。** 实测踩过：合并上游时用
`git add -A` 暂存冲突解决结果，把只应留在本机的 `whitebox-director`（需要 headless
Blender + ffmpeg，服务器两样都没有）一起提交并推送了 —— 它因此上了货架，而用户一点
就交付不出东西。所以：**暂存冲突一律按路径 `git add <file>`，不要用 `-A`**；本地专用
目录另加进 `.git/info/exclude`（只影响本机，不进仓库）；换目录前的自检要确认新 `src`
里没有本地专用专家目录，并核对 `library` 目录数符合预期。

**构建慢的地方是下载依赖，不是编译**（服务器只有 2 核，实测构建期间负载 0.02、
没有 cc1/gcc 在跑，瓶颈全在网络）：

- 同一时刻取同一个 wheel 对比：阿里云 654 KB/s、腾讯云 413 KB/s、PyPI 官方 47 KB/s。
- 但**带宽随时段波动很大**：凌晨那次 `uv sync` 1.3 秒就开始下 `pydantic-core`，
  整场构建 6 分钟；当晚 23:22 重跑同一阶段，`uv` 实测长时间只有 110–150 KB/s，
  中途突然涨到 3 MB/s 又回落，55 分钟还没走完。
- 所以：**动手前先花 20 秒测一次速**（从 `uv.lock` 里取一个 wheel 的真实地址，
  分别对三个源 `curl -o /dev/null -w '%{speed_download}'`），别默认某个源快。
- 判断有没有卡住看 `/proc/<uv pid>/io` 的 `write_bytes` 涨不涨，别看日志 ——
  `uv sync` 只在**开始**下载某个包时打一行，长时间无输出是正常的。
- ⚠️ **但闸门只测单连接，它会骗人**（2026-10-18 实测）：19:53 测出 5.9 MB/s、
  20:07 测出 10.9 MB/s，同一时刻 `uv` 的持续写盘只有 **118 → 224 KB/s**，网卡收包
  58 KB/s，而 `uv` 只握着 2 条 TCP 连接、CPU 占用 0.3%（说明在等网络，不是编译慢）。
  镜像源对少量连接逐连接限速时，就会出现「curl 飞快、uv 爬」。**决定要不要重来一律看
  `write_bytes` 的持续速率**，用它估剩余时间（依赖全集约 500 MB ⇒ 200 KB/s ≈ 40 分钟）；
  已经跑下去的进度在未完成层里，换源重启等于从零再下，所以慢也别随手杀。

**第二个下载坑是 Playwright 的 Chromium，`Dockerfile` 已经留好开关。**
`runtime 12/13` 那步从 `cdn.playwright.dev` 拉 177 MB Chrome，这个地址国内极慢
（实测 84 KB/s ⇒ 约 30 分钟；进度条原地刷新，日志里只留一行 `0%`，看着像卡死）。
`docker/docker_build.sh:47` 会把 `PLAYWRIGHT_DOWNLOAD_HOST` 转发成 build-arg，
构建时一起设上（npmmirror 实测 1.6 MB/s ⇒ 2 分钟，目录结构完全对得上）：

```bash
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ PIP_TRUSTED_HOST=mirrors.aliyun.com \
NPM_REGISTRY=https://registry.npmmirror.com APT_MIRROR=mirrors.aliyun.com \
PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright \
bash docker/docker_build.sh octop:latest
```

⚠️ **别随手 `docker builder prune -f`**：它把这 177 MB 的下载缓存一起清掉，
清完的第一次构建必然重演这次慢下载。实测对比：缓存命中时整场 5 分 1 秒，
清掉后同一阶段跑了 25 分钟还没下完，换上上面的镜像源才回到 2 分钟。
回收磁盘前先想清楚这一步值不值。

⚠️ **`docker/Dockerfile` 的 uv 缓存挂载曾经不生效**（1.0.2b9 上线时修）：挂载点是
`--mount=type=cache,target=/root/.cache/uv`，而镜像里 `HOME=/data`，
uv 实际读写的是 `/data/.cache/uv` —— 于是每次构建都重新下载并解包全部依赖
（锁文件 248 个包，约 500 MB），而且第 6 步和第 8 步两次 `uv sync` **各下一遍**。
修法是在两个 uv 步骤前加 `ENV UV_CACHE_DIR=/root/.cache/uv`（不动 `HOME`，
避免影响运行时读 `/data` 下的配置）。它会让整个依赖层失效重来一次，所以正好借
这次「上游新增 extras 已经必然重装依赖」的上线一起验证，不额外付代价。
验证办法：第二次 `uv sync` 应该几十秒结束、不再刷 `Downloading`；
`docker buildx du` 里那个 uv 缓存卷应当稳定占位而不是每次归零。

同一次还加了 `ENV UV_HTTP_TIMEOUT=300`：默认 30 秒在这条线上撑不住 —— 实测
`uv sync` 跑满一小时后死在 `pillow` 上（`Failed to extract archive …
network timeout (current value: 30s)`），而同一时刻单文件 curl 阿里云有 10.9 MB/s。
两次 `Downloading` 之间隔 3-5 分钟也算正常。**缓存修好之后失败的构建会保留已下载的
部分**，重跑是从断点继续，不再是从零开始。

**怎么确认缓存真的写进去了（`docker buildx du` 会骗人）**：它把 cache mount 记录报成
`Size: 0B`，看着像没生效。决定性办法是拿同一路径的挂载做一次探针构建，直接 `du`：

```bash
mkdir -p /tmp/probe && cat > /tmp/probe/Dockerfile <<'EOF'
FROM python:3.12-slim
RUN --mount=type=cache,target=/root/.cache/uv du -sh /root/.cache/uv; \
    find /root/.cache/uv -name "*pillow*" | head -2
EOF
cd /tmp/probe && docker build --progress=plain -f Dockerfile . 2>&1 | tail -6
```

2026-10-18 实测：构建被中途 `pkill` 之后探针仍读出 **897M**，且
`/root/.cache/uv/wheels-v5/pypi/pillow` 在 —— 说明挂载生效、且缓存卷**跨构建存活**。
所以慢窗口里可以放心停手，不必硬等到天亮。


### 本地开发

本机若配置了 `UV_DEFAULT_INDEX`，`uv run` 会按该源重新解析并**改写 `uv.lock`**，
使工作区莫名其妙变脏。加 `UV_FROZEN=1` 即可禁止改写，同时镜像源仍然生效：

```bash
UV_FROZEN=1 uv run pytest -q
```


## 4. HTTPS —— 必须做

公网 HTTP 意味着**登录密码明文传输**。两种做法：

**A. Caddy（推荐，自动申请续期证书）**

```
your-domain.com {
    reverse_proxy 127.0.0.1:8088
}
```

**B. 应用自带自签证书**（仅适合内部使用，浏览器会告警）

```bash
octop run --host 0.0.0.0 --port 8088 --ssl
```

**C. Cloudflare Tunnel**（无需公网 IP、无需开端口，自带 HTTPS）

```bash
cloudflared tunnel --url http://127.0.0.1:8088
```

## 5. ⚠️ 部署后必须做的配置（最容易漏）

**新部署的数据库是空的。** 专家模板和电商插件打包在镜像里（自带），但**模型配置存在数据库里，必须手动配**，否则什么都跑不起来：

1. 登录 `https://your-domain.com`（管理员账号见第 3.2 节）
2. `管理 → 模型 → 添加提供商`：填入 OpenAI 兼容中转站地址 + API Key
3. 切到 **「生成模型」** 标签：把**生图模型**设为 `gpt-image-2.5`
4. 把**对话模型**指到支持图片输入的模型（快图需要读参考图）
5. `专家 → 从模板创建`：建一个 **`快图`**（一句话出图）

## 6. 安全底线（上线前）

| 事项 | 说明 |
|---|---|
| **限制中转站额度** | 生图按张计费。整站共用一把 key，**必须在 New API 后台给该 key 设额度上限**，否则单个账号可烧光预算 |
| **轮换 API Key** | 部署用的中转站 key 可能在开发过程中泄漏过，上线前换新的 |
| **邀请码发完后吊销** | 一次性码，`管理 → 用户 → 邀请` |
| **给体验角色设生图配额** | `管理 → 用户 → 角色` → 勾「生图额度」填张数。这是**唯一**能按人限制生图成本的机制 |

### 成本防护的三层

```
第 1 层  Octop「生图额度」   按用户限张数    管理 → 角色
第 2 层  Octop「Token 配额」 按用户限 token  同上
第 3 层  中转站 key 额度     整站兜底        New API 后台
```

前两层应用内解决；第三层是唯一能防「绕过应用直接打 key」的地方。

## 7. 已知注意事项

- **服务默认只绑 `127.0.0.1`**，容器里通过 `OCTOP_BIND_HOST=0.0.0.0` 已覆盖。
- **邀请链接用的是「浏览器地址栏的 origin」**（`localInviteUrl()`）。所以**必须用最终对外域名打开后台再生成邀请码**，否则链接里会是 `127.0.0.1` 或内网 IP，外部用户打不开。
- **升级时**：`git pull` 后重新 `up -d --build`。数据卷不动，不会丢数据。
- **`uv.lock` 常被本地 `uv run` 改写**为镜像源，提交前应 `git checkout uv.lock`。部署构建不受影响。
- **插件技能会随版本号覆盖工作区副本**（版本号变了才同步）。如果用户手工改过插件技能，升级会覆盖。

## 8. 快速验收清单

部署完成后逐项确认：

- [ ] `https://your-domain.com` 能打开登录页
- [ ] 管理员能登录
- [ ] `管理 → 模型` 里能看到已配置的提供商，且**生图模型已选**
- [ ] `专家 → 从模板创建` 能建出「快图」
- [ ] 用快图发一句话，**能出一张带文案的主图**
- [ ] 建一个带「生图额度=1」的角色，用它建测试用户，出第二张图时被拒绝并提示额度用完
- [ ] `管理 → 用户 → 邀请` 生成的链接里是**对外域名**，不是 `127.0.0.1`
- [ ] 手机 4G 网络下打开该邀请链接，能正常注册

## 8.5 桌面端下载（内测）

安装包和下载页是**服务器上的静态文件**：既不在仓库里，也不进容器镜像。

| 路径 | 内容 |
|---|---|
| `/opt/kinoguild/downloads/index.html` | 下载页（含安装步骤、SHA-256） |
| `/opt/kinoguild/downloads/files/*.dmg` | 安装包（arm64 = Apple 芯片，amd64 = Intel） |
| `https://kinoguild.xingtudesign.com/download` | 对外地址 |

nginx（`/etc/nginx/conf.d/kinoguild.conf` 的 443 段）里加了两个 location：
`location = /download` 指向页面、`location /downloads/` 指向文件目录；
改完必须 `nginx -t && systemctl reload nginx`（配置文件在服务器上，不在仓库里）。

**发新版**：

```bash
cd desktop/src
wails3 task darwin:package THIN=true VERSION=<ver> ARCH=arm64   # 再打一次 ARCH=amd64
scp bin/KinoGuild-desktop-darwin-arm64-<ver>.dmg kinotv:/opt/kinoguild/downloads/files/KinoGuild-<ver>-arm64.dmg
scp bin/KinoGuild-desktop-darwin-amd64-<ver>.dmg kinotv:/opt/kinoguild/downloads/files/KinoGuild-<ver>-amd64.dmg
# 同步更新下载页上的版本号、体积、SHA-256
curl -sI https://kinoguild.xingtudesign.com/downloads/KinoGuild-<ver>-arm64.dmg   # 期望 200
```

**当前是内测版**：ad-hoc 签名、未公证 → 用户下载后必须「右键 → 打开」才能启动，
下载页已写明这一点。**对外公开发布前必须做 Developer ID 签名 + 公证**，
否则 Gatekeeper 会拦（见 §10 上线记录里的桌面端条目）。

## 9. 排障入口

- 应用日志：`docker logs -f octop`
- 健康检查：`GET /api/health`
- 数据目录：`${OCTOP_DATA}`
- 首次密码（未显式设置时）：`${OCTOP_DATA}/credential.txt`
- **对话时控制台报 `insertBefore … is not a child of this node`**：不是后端问题，
  也不进 `docker logs`。这是浏览器翻译类扩展（Chrome 内置翻译、沉浸式翻译、划词翻译）
  在流式输出期间把文字节点包进自己的标签，React 手里的兄弟参照因此失效。服务端无关，
  用户侧表现是弹一条错误提示、聊天还能继续。已在代码里治理：
  `MessageList.tsx` 在流式期间给消息区加 `translate="no"` + `notranslate`，
  输出结束自动撤掉（历史消息仍可翻译）；`Markdown/index.tsx` 的 mermaid 清理也只删
  自身容器外的残留节点，避免删掉 React 树里带同名 id 的 `<svg>`。
  **别把这两个属性/注释当冗余删掉** —— 删了报错就会回来（2026-10-19 用户实测修好）。

## 10. 上线记录

以后每次上线在这里加一行（提交、镜像 id、schema 水位、回滚锚点、耗时反常点）。

- **2026-10-19 05:04 · 1.0.2b9**（合并上游 b9，253 文件 +15364/−581）
  运行代码 = `ba4232a7`，镜像 `95ee0a7af122` 2.86GB，**schema 21 → 22**（上游的
  `021_skill_package_download` 与我们的 `021_invite_multi_use` 撞号，重命名为 022，
  依据见 `NOTICE.md` 第 7 步），依赖升 harness 1.0.4 / gateway 1.0.3，
  货架 24 → **25**（新增 `business-operations`）。
  回滚锚点 `octop:rollback-13db9dee` = `134312b05de2`；迁移前备份
  `backup/octop-pre-b9-20261018-1953.db.gz`。验收过项：`/api/health` ok、22 agents /
  17 threads 与备份一致、0 错误行、Chromium 烤在镜像内可启动渲染、
  `cv2/fastembed/rapidocr/onnxruntime/pymupdf` 全部可 import。
  **耗时反常点值得记**：同一份源码，晚上 21:09–23:30 跑了 2h20m 没走完依赖（37 KB/s），
  凌晨 05:00 起 **7 分钟**构建成功 —— 差别是 1485 KB/s 的窗口 + 修好的 uv 缓存卷复用
  897MB。"慢窗口里停手不丢进度"现在是实测结论，不是推测。

- **2026-10-26 17:45 · 桌面端下载入口 + health 版本字段**（仍是 1.0.2，无迁移）
  提交 `c987eab7`，镜像 `95004f6f902c`，回滚锚点 `octop:rollback-pre-download`
  （= 上一版 `99076b45c593`）。schema 仍 22。
  - `/api/health` 增加 `version`：桌面端握手依据（低于 minServerVersion 直接拒绝）。
    上线后桌面端日志确认「已连接 …（服务器版本 1.0.2）」。
  - 登录页底部 + 用户菜单加「下载桌面端」，指向 `/download`（静态托管，见 §8.5）。
  - `desktop/` 薄客户端代码入库（Wails v3，THIN 打包，见 §8.5）。
  **这次构建耗时反常（约 30 分钟）的根因**：Dockerfile 里 apt 装中文字体（60MB）与
  playwright Chromium（177MB）都排在 `COPY src/` **之后** —— 只改前端一行也会重下这
  240MB。待优化：把这两层挪到 COPY src/ 之前（只依赖 pyproject/uv.lock），并给
  Chromium 加 `--mount=type=cache,target=/root/.cache/ms-playwright`；改完代码级部署
  应回到 2~3 分钟。优化要单独一次上线（会触发全量构建，挑网速好的时段）。

- **2026-10-19 15:32 · 1.0.2**（上游正式版，8 个实质提交）
  提交 `ec11d09b`，镜像 `99076b45c593` 2.86GB，**schema 仍 22**（上游这次没有新迁移，
  我们的 022 继续独占），依赖未变（harness 1.0.4 / gateway 1.0.3），货架 25 不变。
  回滚锚点 `octop:rollback-1.0.2b9` = `95ee0a7af122`；迁移前备份
  `backup/octop-pre-1.0.2-20261019-1528.db.gz`（893420B）。
  **本次唯一会写生产数据的是启动时的一次性授权**：`migrate.py` 的
  `_grant_permission_keys_once` 给老账号补 `granted_nav_page_permissions` 和
  `granted_personalization_tab_permissions`（后者把个性化页拆成 skills/subagents/
  tools/agent_plugins/mbti/memory 六项）。上线后已核对两个 flag 都落到了 `settings` 表。
  新功能：一次性定时任务（复用 `cron_jobs`，触发条件写成 `date:<墙钟>` 前缀，
  未执行的一次会 `mark_missed` 置为 missed 并停用，**不需要新表**）、钉钉 CLI (dws)
  连接器、`shell_output.py`（按宿主代码页解码 grep/shell 输出）。
  风险点：`infra/bridge/manager.py` 601 行重写（修「团队成员流刷新即断」），
  这属于运行时行为，单测覆盖不了，**上线后要做一次 IM 多成员 + 刷新实测**。
  构建耗时 ~5 分钟：uv.lock 只改了版本号那几行，但 COPY 层失效仍会重跑 `uv sync`，
  靠修好的缓存卷（897MB）16 秒装完 218 个包 —— 这就是上次修缓存挂载的长期收益。

---

**交接联系人**：本项目开发方。部署中遇到问题请回传：`docker logs octop` 的报错段落 + 出问题的完整 URL。

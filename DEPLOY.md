# KinoGuild 部署交接说明

> 本文档面向负责服务器运维的智能体/工程师。读完本文应能独立完成一次公网部署。

## 1. 项目信息

| 项 | 值 |
|---|---|
| 仓库 | `git@github.com:kinobuild/Kinobuild.git` |
| 分支 | `main` |
| 本机路径 | `/Users/mima1234/Documents/deepseek-harness/default-workspace/Octop` |
| 上游 | `TencentCloud/Octop`（MIT 许可，本项目为其 fork 并改名 KinoGuild） |
| 版本 | `pyproject.toml` → `1.0.2b6` |
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

## 9. 排障入口

- 应用日志：`docker logs -f octop`
- 健康检查：`GET /api/health`
- 数据目录：`${OCTOP_DATA}`
- 首次密码（未显式设置时）：`${OCTOP_DATA}/credential.txt`

---

**交接联系人**：本项目开发方。部署中遇到问题请回传：`docker logs octop` 的报错段落 + 出问题的完整 URL。

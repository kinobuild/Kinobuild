# syntax=docker/dockerfile:1
# =============================================================================
# Octop — 多阶段 Docker 构建
#
# 阶段 1: 构建 React/TypeScript 前端
# 阶段 2: Python 运行时 + 预构建前端
#
# 用法（在仓库根目录执行，构建上下文为根目录）:
#   docker build -f docker/Dockerfile -t octop:latest .
#   docker run -d -p 8088:8088 -v octop-data:/data/.octop -e HOME=/data octop:latest
#
# 国内加速（可选，需 BuildKit，docker/docker_build.sh 默认已开启）:
#   PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple \
#   PIP_TRUSTED_HOST=mirrors.cloud.tencent.com \
#   NPM_REGISTRY=https://mirrors.cloud.tencent.com/npm/ \
#   APT_MIRROR=mirrors.cloud.tencent.com \
#   PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright \
#   bash docker/docker_build.sh
#
# 或直接传 build-arg:
#   docker build \
#     -f docker/Dockerfile \
#     --build-arg PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple \
#     --build-arg PIP_TRUSTED_HOST=mirrors.cloud.tencent.com \
#     --build-arg NPM_REGISTRY=https://mirrors.cloud.tencent.com/npm/ \
#     --build-arg APT_MIRROR=mirrors.cloud.tencent.com \
#     --build-arg NODE_MAX_OLD_SPACE_SIZE=1024 \
#     -t octop:latest .
#
# 或使用 Compose:
#   docker compose -f docker/docker-compose.yml up -d
# =============================================================================

# ---------------------------------------------------------------------------
# 阶段 1 — 前端构建
# ---------------------------------------------------------------------------
FROM node:20-slim AS frontend-builder

ARG NPM_REGISTRY=
# Node heap ceiling for the vite build. Lower this (e.g. 1024) on low-memory
# build hosts (< 4G RAM) to avoid OOM kills — the value only caps the max,
# it is not pre-allocated.
ARG NODE_MAX_OLD_SPACE_SIZE=2048
WORKDIR /build/dashboard

COPY dashboard/package.json dashboard/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    set -eu; \
    if [ -n "$NPM_REGISTRY" ]; then npm config set registry "$NPM_REGISTRY"; fi; \
    npm ci --no-audit \
    || { echo "npm ci failed — retrying clean"; rm -rf node_modules; npm ci --no-audit; }; \
    test -x node_modules/.bin/vite

COPY dashboard/ ./

RUN mkdir -p ../src/octop/dashboard

# 镜像构建跳过完整 tsc；生产打包由 vite/esbuild 完成（使用 lockfile 中的 vite，不用 npx）
RUN NODE_ENV=production NODE_OPTIONS="--max-old-space-size=${NODE_MAX_OLD_SPACE_SIZE}" npm run build:docker


# ---------------------------------------------------------------------------
# 阶段 2 — Python 运行时
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="OrcaKit Team"
LABEL org.opencontainers.image.title="Octop"
LABEL org.opencontainers.image.description="Smarter self-hosted AI assistant — multi-user, multi-agent."
LABEL org.opencontainers.image.source="https://github.com/TencentCloud/orca"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/data \
    OCTOP_BIND_HOST=0.0.0.0 \
    OCTOP_PORT=8088 \
    OCTOP_LOG_LEVEL=info \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

ARG PIP_INDEX_URL=
ARG PIP_TRUSTED_HOST=
ARG APT_MIRROR=

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    if [ -n "$APT_MIRROR" ]; then \
        printf 'Types: deb\nURIs: https://%s/debian\nSuites: trixie trixie-updates\nComponents: main contrib non-free non-free-firmware\n\nTypes: deb\nURIs: https://%s/debian-security\nSuites: trixie-security\nComponents: main contrib non-free non-free-firmware\n' \
            "$APT_MIRROR" "$APT_MIRROR" > /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libgl1 \
        libglib2.0-0 \
        curl \
        git \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/

WORKDIR /app

# 先安装锁定依赖，仅改源码时可复用此层缓存
COPY pyproject.toml uv.lock README.md LICENSE ./

# Two build-time-only settings, placed here (right before the uv steps that need
# them) so earlier layers keep their cache:
#
# UV_CACHE_DIR — this stage sets HOME=/data for the running container, so without
# this uv reads/writes /data/.cache/uv while the --mount below is attached to
# /root/.cache/uv and never gets used: every build re-downloaded the whole ~500 MB
# dependency set, and the two `uv sync` steps each did it again. Pointing uv at the
# mounted path makes the cache real — step 138 reuses step 109's downloads, and a
# failed build keeps its partial progress for the next attempt.
#
# UV_HTTP_TIMEOUT — the default 30 s is not enough on a throttled link: an hour-long
# `uv sync` died on `pillow` with "Failed to extract archive: … network timeout
# (current value: 30s)" while a single-file curl to the same mirror reported 10 MB/s
# (uv only holds ~2 paced connections). 300 s rides out the stall instead of failing
# the whole layer.
ENV UV_CACHE_DIR=/root/.cache/uv \
    UV_HTTP_TIMEOUT=300

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -n "$PIP_INDEX_URL" ]; then \
        export UV_INDEX_URL="$PIP_INDEX_URL"; \
        if [ -n "$PIP_TRUSTED_HOST" ]; then export UV_INSECURE_HOST="$PIP_TRUSTED_HOST"; fi; \
    fi \
    && uv sync --frozen --no-install-project --no-dev \
        --extra browser --extra local-embedding --extra knowledge-ocr

ENV PATH="/app/.venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# --- 重资产层：中文字体 + Playwright Chromium -------------------------------
# 这两样加起来约 240 MB，而且只依赖 venv 和 apt，**不依赖源码**。把它们放在
# COPY src/ 之前，改一行代码就不会触发重下 —— 之前它们排在最后，导致晚高峰一次
# 前端改动要重下 60MB 字体 + 177MB 浏览器，把 3 分钟的部署拖成 30 分钟。
# 注意：**不要**给 /root/.cache/ms-playwright 加 cache mount —— cache mount 不进镜像，
# 浏览器就被留在缓存里，镜像里目录是空的，playwright 启动会直接报找不到浏览器。
# 浏览器必须烤进镜像层（重建容器会清掉可写层，靠它才能活下来）。
# build-essential 在这里就清掉（而不是留到最后）：playwright --with-deps 装的系统
# 库必须排在 purge 之后，否则会被 --auto-remove 顺手删掉。
# ARG 放在本层正前方：它若声明在更早的位置，换镜像源会连带使依赖层失效。
ARG PLAYWRIGHT_DOWNLOAD_HOST=

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && apt-get purge -y --auto-remove build-essential \
    && if [ -n "$PLAYWRIGHT_DOWNLOAD_HOST" ]; then export PLAYWRIGHT_DOWNLOAD_HOST="$PLAYWRIGHT_DOWNLOAD_HOST"; fi \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY src/ ./src/
COPY --from=frontend-builder /build/src/octop/dashboard/ ./src/octop/dashboard/

COPY .env.example ./
COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 只装项目本体：依赖层、字体、浏览器都已在前面的层里，这里仅剩「把 octop 装进
# venv + 导入自检」，因此只改 src/ 时代价很小。
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -n "$PIP_INDEX_URL" ]; then \
        export UV_INDEX_URL="$PIP_INDEX_URL"; \
        if [ -n "$PIP_TRUSTED_HOST" ]; then export UV_INSECURE_HOST="$PIP_TRUSTED_HOST"; fi; \
    fi \
    && uv sync --frozen --no-dev \
        --extra browser --extra local-embedding --extra knowledge-ocr \
    && .venv/bin/python -c "import cv2, fastembed, huggingface_hub, rapidocr, onnxruntime, pymupdf" \
    && rm -rf /tmp/*

RUN mkdir -p /data/.octop

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD ["sh", "-c", "curl -f http://localhost:${OCTOP_PORT:-8088}/api/health || exit 1"]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD []

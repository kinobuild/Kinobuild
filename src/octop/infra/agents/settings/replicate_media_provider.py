"""面向 Replicate 的图像生成适配器。

Replicate 与 OpenAI 图像协议**完全不同**，所以无法靠改 base_url 复用
``OpenAIMediaProvider``：

- 提交：``POST /v1/models/{owner}/{name}/predictions``，立刻返回一个 prediction
  （HTTP 202，``status: starting``），而不是图像本身；
- 取结果：``GET /v1/predictions/{id}`` 轮询，直到 ``status: succeeded``，
  此时 ``output`` 是一组**图片 URL**。

因此这里走 harness 的异步路径（``MediaSubmission(task=…)`` + ``_poll_task``），
与 volcengine / dashscope 同一套机制。

质量档位固定为 ``low``：本项目的出图场景（电商主图，中文卖点文案直接由模型渲染）
在 low 档下实测文案清晰、单张约 12 秒，成本最低。Replicate 的
``MediaProviderConfig`` 没有携带额外参数的字段，所以不做成配置项 —— 需要改档位时
改 ``_QUALITY`` 即可。
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from octop_harness.media.errors import MediaGenerationError
from octop_harness.media.http import BearerJsonMediaProvider, provider_payload_error
from octop_harness.media.models import (
    ImageGenerationRequest,
    MediaCapabilities,
    MediaJobUpdate,
    MediaSubmission,
    ProviderTask,
    RemoteArtifact,
)

PROVIDER_NAME = "replicate"

DEFAULT_BASE_URL = "https://api.replicate.com/v1"
DEFAULT_IMAGE_MODEL = "openai/gpt-image-2"

#: 固定走最低档。见模块 docstring：本项目实测该档中文文案渲染正确。
_QUALITY = "low"

#: Replicate 的 gpt-image-2 只认这些尺寸/比例，其余一律交给模型自己选。
_ALLOWED_ASPECT_RATIOS = frozenset(
    {
        "1:1",
        "3:2",
        "2:3",
        "4:3",
        "3:4",
        "16:9",
        "9:16",
        "auto",
        "1024x1024",
        "1536x1024",
        "1024x1536",
        "1536x1152",
        "1152x1536",
        "2048x2048",
        "2048x1152",
        "1152x2048",
        "3840x2160",
        "2160x3840",
    }
)

_OUTPUT_FORMAT = "png"
_MAX_REFERENCE_IMAGES = 4
#: Replicate 的图片数量上限（模型 schema 写的是 1-10）。
_MAX_IMAGES = 10

#: 提交与轮询的阶段名 → harness 的作业状态。
_RUNNING_STATUSES = frozenset({"processing"})
_TERMINAL_FAILURES = frozenset({"failed", "canceled", "aborted"})


def _aspect_ratio(size: str | None) -> str | None:
    """把工具层传来的尺寸映射成 Replicate 认的值，不认就返回 None。"""
    value = (size or "").strip()
    if not value:
        return None
    # 工具层可能给 "1024X1024"（大写 X）或 "1024*1024"。
    normalized = value.replace("X", "x").replace("*", "x").lower()
    return normalized if normalized in _ALLOWED_ASPECT_RATIOS else None


def _reference_data_uri(data: bytes, media_type: str) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{media_type or 'image/png'};base64,{encoded}"


def _load_reference_data(reference: str) -> str:
    """把参考图转成 Replicate 接受的形式。

    ``input_images`` 收 URL 或 data URI。参考图可能是内联 data URL、远程 http(s)、
    ``file://`` 或裸路径。远程图直接交给 Replicate 拉取；本地文件读成字节再编码成
    data URI —— 否则 Replicate 反过来访问我们的内网地址必然失败。
    """
    value = (reference or "").strip()
    if not value:
        raise MediaGenerationError("A reference image was empty.", code="provider_request_invalid")

    if value.startswith("data:"):
        if "," not in value:
            raise MediaGenerationError(
                "A reference image data URL was malformed.",
                code="provider_request_invalid",
            )
        return value  # 已经是 data URI，直接用

    if value.startswith(("http://", "https://")):
        return value

    path = value
    if value.lower().startswith("file://"):
        path = urlsplit(value).path

    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise MediaGenerationError(
            f"Could not read reference image {path!r}.", code="provider_request_invalid"
        ) from exc
    suffix = Path(path).suffix.lower().lstrip(".")
    media_type = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(suffix, "image/png")
    return _reference_data_uri(raw, media_type)


class ReplicateMediaProvider(BearerJsonMediaProvider):
    """Replicate 上的图像生成（提交 + 轮询）。"""

    provider_id = PROVIDER_NAME
    capabilities = MediaCapabilities(
        image_generation=True,
        video_generation=False,
        image_references=True,
    )

    async def _submit_video(
        self,
        client: httpx.AsyncClient,
        request: Any,
    ) -> MediaSubmission:
        # 基类把 _submit_video 声明为抽象方法，即使 capabilities 关掉了视频也必须给出实现。
        # 该适配器只做图像；上游的 Replicate 视频模型与本项目的出图场景无关。
        del client, request
        raise MediaGenerationError(
            "The configured media provider does not support video generation.",
            code="provider_unsupported",
        )

    async def _submit_image(
        self,
        client: httpx.AsyncClient,
        request: ImageGenerationRequest,
    ) -> MediaSubmission:
        model = (self.image_model or DEFAULT_IMAGE_MODEL).strip().strip("/")
        if not model or "/" not in model:
            raise MediaGenerationError(
                f"Replicate needs an owner/name model, got {model!r}.",
                code="provider_request_invalid",
            )

        payload_in: dict[str, Any] = {
            "prompt": request.prompt,
            "quality": _QUALITY,
            "output_format": _OUTPUT_FORMAT,
            "number_of_images": max(1, min(int(request.count or 1), _MAX_IMAGES)),
        }
        ratio = _aspect_ratio(request.size)
        if ratio:
            payload_in["aspect_ratio"] = ratio
        if request.seed is not None:
            payload_in["seed"] = request.seed
        if request.reference_images:
            images = []
            for reference in request.reference_images[:_MAX_REFERENCE_IMAGES]:
                images.append(_load_reference_data(reference))
            payload_in["input_images"] = images

        payload = await self._request_json(
            client,
            "POST",
            f"/models/{model}/predictions",
            json={"input": payload_in},
        )
        task_id = payload.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise provider_payload_error(
                payload, fallback="Replicate did not return a prediction id"
            )
        return MediaSubmission(
            task=ProviderTask(task_id=task_id, kind="image", model=model),
        )

    async def _poll_task(
        self,
        client: httpx.AsyncClient,
        task: ProviderTask,
    ) -> MediaJobUpdate:
        payload = await self._request_json(
            client,
            "GET",
            f"/predictions/{task.task_id}",
            provider_task_id=task.task_id,
        )
        status = str(payload.get("status") or "").lower()

        if status == "succeeded":
            artifacts = _output_artifacts(payload.get("output"))
            if not artifacts:
                raise MediaGenerationError(
                    "Replicate finished without an image URL.",
                    code="provider_response_invalid",
                    provider_task_id=task.task_id,
                )
            return MediaJobUpdate(status="succeeded", artifacts=artifacts)

        if status in _TERMINAL_FAILURES:
            raise provider_payload_error(
                payload,
                fallback=f"Replicate prediction {task.task_id} {status}",
                provider_task_id=task.task_id,
            )

        return MediaJobUpdate(status="running" if status in _RUNNING_STATUSES else "pending")


def _output_artifacts(output: Any) -> tuple[RemoteArtifact, ...]:
    """``output`` 可能是单个 URL 字符串，也可能是一组 URL。"""
    urls: list[str] = []
    if isinstance(output, str):
        urls = [output]
    elif isinstance(output, (list, tuple)):
        urls = [item for item in output if isinstance(item, str) and item]
    elif isinstance(output, Mapping):
        # 少数模型返回 {"images": [...]} 这类包装。
        for key in ("images", "image", "url", "output"):
            value = output.get(key)
            if isinstance(value, str) and value:
                urls = [value]
                break
            if isinstance(value, (list, tuple)):
                urls = [item for item in value if isinstance(item, str) and item]
                break

    return tuple(RemoteArtifact(url=url, media_type="image/png", extension="png") for url in urls)


def register_replicate_media_provider() -> None:
    """把适配器注入 harness 注册表。幂等，可在导入期重复调用。

    与 ``register_openai_media_provider`` 同理，要注入**两处**，缺一个都会在运行时被拒：

    1. ``BUILTIN_MEDIA_PROVIDERS`` —— 工厂据此选择适配器类；
    2. ``_MEDIA_PROVIDER_DEFAULTS`` —— ``MediaProviderConfig`` 与
       ``MediaGenerationConfig`` 的 ``__post_init__`` 都拿它当供应商白名单。

    两者都是裸 dict（后者还是私有名），必须写在**我们自己的**代码里 ——
    写在依赖里会在下次 ``uv sync`` 时丢失。
    """
    from octop_harness import config as harness_config
    from octop_harness.media.registry import BUILTIN_MEDIA_PROVIDERS

    BUILTIN_MEDIA_PROVIDERS.setdefault(PROVIDER_NAME, ReplicateMediaProvider)

    defaults = getattr(harness_config, "_MEDIA_PROVIDER_DEFAULTS", None)
    if isinstance(defaults, dict):
        # 元组顺序与内置项一致：(api_key_env, base_url, image_model, video_model)。
        # 该适配器不做视频，第四项留空。
        defaults.setdefault(
            PROVIDER_NAME,
            ("REPLICATE_API_TOKEN", DEFAULT_BASE_URL, DEFAULT_IMAGE_MODEL, ""),
        )


__all__ = [
    "PROVIDER_NAME",
    "DEFAULT_BASE_URL",
    "DEFAULT_IMAGE_MODEL",
    "ReplicateMediaProvider",
    "register_replicate_media_provider",
]

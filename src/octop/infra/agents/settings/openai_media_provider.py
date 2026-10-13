"""OpenAI 格式的媒体供应商适配器 —— 支持 OpenAI 兼容中转站。

Octop 内置的三家适配器（火山方舟 / 阿里百炼 / MiniMax）协议各不相同，而国内大量
中转站走的是 OpenAI 图像协议。harness 的注册表 ``BUILTIN_MEDIA_PROVIDERS`` 是个
裸 dict、没有注册钩子，适配器类又在依赖包里；所以这里把适配器写在**我们自己的**
代码里，再注入那个 dict —— 这样 ``uv sync`` 重新安装依赖后依然生效，不需要打补丁。

两条路径（对应 OpenAI 图像协议的两套语义）：

* 无参考图 → ``POST /images/generations``（JSON）
* **有参考图** → ``POST /images/edits``（``multipart/form-data``）

第二条是电商做图的关键：「保持商品不变、只换场景」在协议上属于 edit，不属于
generate。很多中转站只实现了前者，那样就只能文生图。
"""

from __future__ import annotations

import base64
import binascii
import mimetypes
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from octop_harness.media.errors import MediaGenerationError
from octop_harness.media.http import BearerJsonMediaProvider, provider_payload_error, response_error
from octop_harness.media.models import (
    ImageGenerationRequest,
    MediaCapabilities,
    MediaJobUpdate,
    MediaSubmission,
    ProviderTask,
    RemoteArtifact,
    VideoGenerationRequest,
)

PROVIDER_NAME = "openai"

# OpenAI 的 edits 端点一次接受多张参考图，但超过这个数量几乎都是误传。
_MAX_REFERENCE_IMAGES = 4
_MAX_REFERENCE_BYTES = 20 * 1024 * 1024

# 工具层传下来的是比例（如 "1:1"）或像素（如 "1024x1024"）。OpenAI 图像接口只认
# 像素串或 "auto"，所以这里把常见比例映射到兼容的像素尺寸。
_RATIO_SIZES = {
    "1:1": "1024x1024",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "2:3": "1024x1536",
    "3:2": "1536x1024",
    "9:16": "1024x1536",
    "16:9": "1536x1024",
}


class OpenAIMediaProvider(BearerJsonMediaProvider):
    """面向 OpenAI 兼容中转站的图像生成适配器（文生图 + 图生图）。"""

    provider_id = PROVIDER_NAME
    capabilities = MediaCapabilities(
        image_generation=True,
        video_generation=False,
        image_references=True,
    )

    async def _submit_image(
        self,
        client: httpx.AsyncClient,
        request: ImageGenerationRequest,
    ) -> MediaSubmission:
        if request.reference_images:
            return await self._submit_edit(client, request)
        return await self._submit_generation(client, request)

    async def _submit_generation(
        self,
        client: httpx.AsyncClient,
        request: ImageGenerationRequest,
    ) -> MediaSubmission:
        """无参考图：走 JSON 的文生图端点。"""
        body: dict[str, Any] = {
            "model": self.image_model,
            "prompt": request.prompt,
            "n": max(1, int(request.count)),
        }
        size = _openai_size(request.size)
        if size:
            body["size"] = size

        payload = await self._request_json(client, "POST", "/images/generations", json=body)
        return _submission_from_payload(payload, fallback="图像生成")

    async def _submit_edit(
        self,
        client: httpx.AsyncClient,
        request: ImageGenerationRequest,
    ) -> MediaSubmission:
        """有参考图：走 multipart 的图生图端点。

        不能复用 ``_request_json``：它写死了 ``Content-Type: application/json``，
        而 edits 端点要求 multipart。所以这里自己发请求，但仍复用同一套错误分类。
        """
        references = request.reference_images[:_MAX_REFERENCE_IMAGES]
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for index, reference in enumerate(references):
            data, media_type, suffix = await _load_reference(client, reference)
            files.append(("image", (f"reference-{index}{suffix}", data, media_type)))

        form: dict[str, str] = {
            "model": self.image_model,
            "prompt": request.prompt,
            "n": str(max(1, int(request.count))),
        }
        size = _openai_size(request.size)
        if size:
            form["size"] = size

        try:
            response = await client.post(
                f"{self._config.base_url.rstrip('/')}/images/edits",
                headers={"Authorization": f"Bearer {self._config.resolve_api_key()}"},
                data=form,
                files=files,
            )
        except httpx.TimeoutException as exc:
            raise MediaGenerationError(
                "The media provider request timed out.",
                code="provider_timeout",
                retryable=True,
                safe_to_resubmit=False,
                remediation="retry_later",
                model_instruction=(
                    "Do not retry this tool call manually because the provider may have accepted it. "
                    "Tell the user the request timed out."
                ),
            ) from exc
        except httpx.RequestError as exc:
            raise MediaGenerationError(
                "The media provider could not be reached.",
                code="provider_unavailable",
                retryable=True,
                safe_to_resubmit=False,
                remediation="retry_later",
                model_instruction=(
                    "Do not retry this tool call manually. Tell the user the provider is temporarily unavailable."
                ),
            ) from exc

        if response.is_error:
            raise response_error(response, provider_task_id=None)
        try:
            payload = response.json()
        except ValueError as exc:
            raise MediaGenerationError(
                "The media provider returned invalid JSON.",
                code="provider_response_invalid",
            ) from exc
        if not isinstance(payload, dict):
            raise MediaGenerationError("The media provider returned an unexpected response")
        return _submission_from_payload(payload, fallback="图像编辑")

    async def _submit_video(
        self,
        client: httpx.AsyncClient,
        request: VideoGenerationRequest,
    ) -> MediaSubmission:
        del client, request
        raise MediaGenerationError(
            "The configured media provider does not generate video.",
            code="capability_unsupported",
            category="configuration",
            remediation="configure_model",
            model_instruction="Do not retry. Tell the user this provider only supports image generation.",
        )

    async def _poll_task(
        self,
        client: httpx.AsyncClient,
        task: ProviderTask,
    ) -> MediaJobUpdate:
        # OpenAI 图像接口是同步的：结果在提交响应里就已经返回，没有可轮询的任务。
        del client, task
        raise MediaGenerationError(
            "The configured media provider has no asynchronous task to poll.",
            code="capability_unsupported",
            model_instruction="Do not retry. This provider returns images synchronously.",
        )


def _submission_from_payload(payload: dict[str, Any], *, fallback: str) -> MediaSubmission:
    """把 OpenAI 风格的 ``{data:[{b64_json|url}]}`` 响应转成产物列表。"""
    error = payload.get("error")
    if isinstance(error, Mapping) and error:
        raise provider_payload_error(error, fallback=f"{fallback} failed")

    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise MediaGenerationError(f"The media provider returned no images from {fallback}.")

    artifacts: list[RemoteArtifact] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        encoded = row.get("b64_json")
        if isinstance(encoded, str) and encoded:
            try:
                data = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise MediaGenerationError(
                    "The media provider returned invalid base64 image data."
                ) from exc
            artifacts.append(RemoteArtifact(data=data, media_type="image/png", extension="png"))
            continue
        url = row.get("url")
        if isinstance(url, str) and url:
            artifacts.append(RemoteArtifact(url=url, media_type="image/png", extension="png"))

    if not artifacts:
        raise MediaGenerationError(f"The media provider returned no usable images from {fallback}.")
    return MediaSubmission(artifacts=tuple(artifacts))


def _openai_size(requested: str | None) -> str | None:
    """把工具层传来的比例或像素转成 OpenAI 能接受的尺寸串。"""
    value = (requested or "").strip()
    if not value:
        return None
    mapped = _RATIO_SIZES.get(value)
    if mapped:
        return mapped
    lowered = value.lower()
    if lowered == "auto":
        return "auto"
    head, separator, tail = lowered.partition("x")
    if separator and head.isdigit() and tail.isdigit():
        return lowered
    return None


async def _load_reference(
    client: httpx.AsyncClient,
    reference: str,
) -> tuple[bytes, str, str]:
    """把参考图取成字节，供 multipart 上传。

    参考图可能是四种形态：``data:`` 内联、``http(s)://`` 远程、``file://`` 本地、
    或裸文件路径。edits 端点是文件上传，必须拿到真实字节，所以四种都要认。
    """
    value = (reference or "").strip()
    if not value:
        raise MediaGenerationError("A reference image was empty.", code="provider_request_invalid")

    if value.startswith("data:"):
        header, _, encoded = value.partition(",")
        if not encoded:
            raise MediaGenerationError(
                "A reference image data URL was malformed.", code="provider_request_invalid"
            )
        try:
            data = base64.b64decode(encoded, validate=False)
        except (binascii.Error, ValueError) as exc:
            raise MediaGenerationError(
                "A reference image data URL was not valid base64.", code="provider_request_invalid"
            ) from exc
        media_type = header[5:].split(";", 1)[0] or "image/png"
        return data, media_type, _suffix_for(media_type)

    scheme = urlsplit(value).scheme.lower()
    if scheme in {"http", "https"}:
        try:
            response = await client.get(value, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise MediaGenerationError(
                "A reference image could not be downloaded.", code="provider_unavailable"
            ) from exc
        if response.is_error or not response.content:
            raise MediaGenerationError(
                f"A reference image download failed with HTTP {response.status_code}.",
                code="download_failed",
                http_status=response.status_code,
            )
        media_type = response.headers.get("content-type", "").split(";", 1)[0] or "image/png"
        return response.content, media_type, _suffix_for(media_type)

    path = Path(value[7:]) if scheme == "file" else Path(value)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise MediaGenerationError(
            f"The reference image could not be read: {path.name}",
            code="provider_request_invalid",
        ) from exc
    if not data:
        raise MediaGenerationError(
            "A reference image file was empty.", code="provider_request_invalid"
        )
    if len(data) > _MAX_REFERENCE_BYTES:
        raise MediaGenerationError(
            "A reference image is too large to upload.", code="provider_request_invalid"
        )
    media_type = mimetypes.guess_type(path.name)[0] or "image/png"
    return data, media_type, _suffix_for(media_type)


def _suffix_for(media_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return mapping.get(media_type, ".png")


#: harness 侧 ``_MEDIA_PROVIDER_DEFAULTS`` 的条目：(api_key_env, base_url,
#: image_model, video_model)。该适配器不做视频，所以 video_model 留空——只有当
#: ``MediaGenerationConfig.providers`` 为空时 harness 才会要求它非空，而 Octop 始终
#: 传入至少一个 provider 实例，所以这里是安全的。
_OPENAI_DEFAULTS = (
    "OPENAI_API_KEY",
    "https://api.openai.com/v1",
    "gpt-image-1",
    "",
)


def register_openai_media_provider() -> None:
    """把适配器注入 harness 注册表。幂等，可在导入期重复调用。

    要注入**两处**，缺一个都会在运行时被拒：

    1. ``BUILTIN_MEDIA_PROVIDERS`` —— 工厂据此选择适配器类；
    2. ``_MEDIA_PROVIDER_DEFAULTS`` —— ``MediaProviderConfig`` 与
       ``MediaGenerationConfig`` 的 ``__post_init__`` 都拿它当供应商白名单。

    两个都是裸 dict、没有注册钩子（后者还是私有名），所以只能直接写入。这也是
    为什么这段代码必须放在**我们自己的**代码里：写在依赖里会在下次 ``uv sync`` 时丢失。
    """
    from octop_harness import config as harness_config
    from octop_harness.media.registry import BUILTIN_MEDIA_PROVIDERS

    BUILTIN_MEDIA_PROVIDERS.setdefault(PROVIDER_NAME, OpenAIMediaProvider)

    defaults = getattr(harness_config, "_MEDIA_PROVIDER_DEFAULTS", None)
    if isinstance(defaults, dict):
        defaults.setdefault(PROVIDER_NAME, _OPENAI_DEFAULTS)


__all__ = ["PROVIDER_NAME", "OpenAIMediaProvider", "register_openai_media_provider"]

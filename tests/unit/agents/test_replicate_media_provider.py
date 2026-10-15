"""Replicate 图像适配器的单元测试（全部 mock，不发真实请求）。"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from octop_harness.config import MediaProviderConfig
from octop_harness.media.errors import MediaGenerationError
from octop_harness.media.models import ImageGenerationRequest, ProviderTask

from octop.infra.agents.settings.media_generation import MEDIA_PROVIDER_PRESETS
from octop.infra.agents.settings.replicate_media_provider import (
    ReplicateMediaProvider,
    _aspect_ratio,
    _output_artifacts,
    _reference_data_uri,
)


def _provider(**overrides: Any) -> ReplicateMediaProvider:
    cfg = MediaProviderConfig(
        id="replicate-default",
        provider="replicate",
        api_key="r8_test",
        base_url="https://api.replicate.com/v1",
        image_model=overrides.pop("image_model", "openai/gpt-image-2"),
        image_enabled=True,
        video_enabled=False,
        **overrides,
    )
    return ReplicateMediaProvider(cfg)


def test_replicate_is_registered_in_presets() -> None:
    preset = MEDIA_PROVIDER_PRESETS["replicate"]
    assert preset.base_url == "https://api.replicate.com/v1"
    assert "openai/gpt-image-2" in preset.image_models
    # 只做图像：前端据此不展示视频选项。
    assert preset.video_models == ()
    assert preset.default_video_model == ""


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        ("1024x1024", "1024x1024"),
        ("1024X1024", "1024x1024"),
        ("3:2", "3:2"),
        ("16:9", "16:9"),
        ("auto", "auto"),
        (None, None),
        ("", None),
        ("999x999", None),
    ],
)
def test_aspect_ratio_accepts_only_known_values(size: str | None, expected: str | None) -> None:
    assert _aspect_ratio(size) == expected


def test_output_artifacts_handles_str_list_and_wrapper() -> None:
    assert _output_artifacts("https://x/a.png")[0].url == "https://x/a.png"
    assert len(_output_artifacts(["https://x/a.png", "https://x/b.png"])) == 2
    assert _output_artifacts({"images": ["https://x/c.png"]})[0].url == "https://x/c.png"
    assert _output_artifacts(None) == ()
    # 非字符串项必须被丢掉，否则会把 None 当成 URL 传下去。
    assert _output_artifacts([None, "https://x/d.png"]) == (
        _output_artifacts(["https://x/d.png"])[0],
    )


def test_reference_data_uri_prefixes_media_type() -> None:
    assert _reference_data_uri(b"\x89PNG", "image/png").startswith("data:image/png;base64,")
    # 空 media_type 退回 png，不能产出 "data:;base64,"。
    assert _reference_data_uri(b"x", "").startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_submit_image_posts_input_and_returns_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_request_json(
        self: Any, client: Any, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any]:
        captured.update(method=method, path=path, body=kwargs.get("json"))
        return {"id": "pred-1", "status": "starting"}

    monkeypatch.setattr(ReplicateMediaProvider, "_request_json", fake_request_json)

    provider = _provider()
    async with httpx.AsyncClient() as client:
        sub = await provider._submit_image(
            client,
            ImageGenerationRequest(prompt="mug", size="1024x1024", count=2, seed=7),
        )

    assert sub.task is not None
    assert sub.task.task_id == "pred-1"
    assert sub.task.kind == "image"
    assert captured["method"] == "POST"
    assert captured["path"] == "/models/openai/gpt-image-2/predictions"

    payload = captured["body"]["input"]
    assert payload["prompt"] == "mug"
    # 本项目固定 low 档：实测中文卖点文案渲染正确且成本最低。
    assert payload["quality"] == "low"
    assert payload["aspect_ratio"] == "1024x1024"
    assert payload["number_of_images"] == 2
    assert payload["seed"] == 7
    # 没有参考图时不应出现该字段。
    assert "input_images" not in payload


@pytest.mark.asyncio
async def test_submit_image_requires_owner_slash_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _provider(image_model="gpt-image-2")
    async with httpx.AsyncClient() as client:
        with pytest.raises(MediaGenerationError) as exc:
            await provider._submit_image(client, ImageGenerationRequest(prompt="x"))
    assert exc.value.code == "provider_request_invalid"


@pytest.mark.asyncio
async def test_submit_image_missing_id_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_request_json(self: Any, client: Any, method: str, path: str, **kw: Any):
        return {"status": "starting"}  # 没有 id

    monkeypatch.setattr(ReplicateMediaProvider, "_request_json", fake_request_json)
    provider = _provider()
    async with httpx.AsyncClient() as client:
        with pytest.raises(MediaGenerationError):
            await provider._submit_image(client, ImageGenerationRequest(prompt="x"))


@pytest.mark.asyncio
async def test_submit_image_sends_local_reference_as_data_uri(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG-ref")

    captured: dict[str, Any] = {}

    async def fake_request_json(self: Any, client: Any, method: str, path: str, **kwargs: Any):
        captured.update(kwargs.get("json"))
        return {"id": "pred-ref"}

    monkeypatch.setattr(ReplicateMediaProvider, "_request_json", fake_request_json)
    provider = _provider()
    async with httpx.AsyncClient() as client:
        await provider._submit_image(
            client,
            ImageGenerationRequest(prompt="x", reference_images=(str(ref),)),
        )

    images = captured["input"]["input_images"]
    assert len(images) == 1
    # 本地文件必须转成 data URI，Replicate 访问不到我们的内网路径。
    assert images[0].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_submit_image_passes_remote_reference_through() -> None:
    from octop.infra.agents.settings.replicate_media_provider import _load_reference_data

    url = "https://example.com/a.png"
    assert _load_reference_data(url) == url


@pytest.mark.asyncio
async def test_poll_task_status_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        {"status": "starting"},
        {"status": "processing"},
        {"status": "succeeded", "output": ["https://x/a.png"]},
    ]

    async def fake_request_json(self: Any, client: Any, method: str, path: str, **kw: Any):
        assert path == "/predictions/pred-9"
        return responses.pop(0)

    monkeypatch.setattr(ReplicateMediaProvider, "_request_json", fake_request_json)
    provider = _provider()
    task = ProviderTask(task_id="pred-9", kind="image", model="openai/gpt-image-2")

    async with httpx.AsyncClient() as client:
        assert (await provider._poll_task(client, task)).status == "pending"
        assert (await provider._poll_task(client, task)).status == "running"
        done = await provider._poll_task(client, task)

    assert done.status == "succeeded"
    assert done.artifacts[0].url == "https://x/a.png"
    assert done.artifacts[0].extension == "png"


@pytest.mark.asyncio
async def test_poll_task_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_request_json(self: Any, client: Any, method: str, path: str, **kw: Any):
        return {"status": "failed", "error": "boom"}

    monkeypatch.setattr(ReplicateMediaProvider, "_request_json", fake_request_json)
    provider = _provider()
    task = ProviderTask(task_id="pred-bad", kind="image", model="openai/gpt-image-2")

    async with httpx.AsyncClient() as client:
        with pytest.raises(MediaGenerationError):
            await provider._poll_task(client, task)


@pytest.mark.asyncio
async def test_poll_task_succeeded_without_output_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_request_json(self: Any, client: Any, method: str, path: str, **kw: Any):
        return {"status": "succeeded", "output": None}

    monkeypatch.setattr(ReplicateMediaProvider, "_request_json", fake_request_json)
    provider = _provider()
    task = ProviderTask(task_id="pred-empty", kind="image", model="openai/gpt-image-2")

    async with httpx.AsyncClient() as client:
        with pytest.raises(MediaGenerationError) as exc:
            await provider._poll_task(client, task)
    assert exc.value.code == "provider_response_invalid"


@pytest.mark.asyncio
async def test_video_submission_is_rejected() -> None:
    provider = _provider()
    async with httpx.AsyncClient() as client:
        with pytest.raises(MediaGenerationError) as exc:
            await provider._submit_video(client, object())
    assert exc.value.code == "provider_unsupported"

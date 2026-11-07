"""End-to-end attachment pipeline tests (no WebSocket — direct API calls)."""

from __future__ import annotations

import base64
import re
import tempfile
from pathlib import Path
from typing import Any

import pytest
from deepagents.backends.local_shell import LocalShellBackend
from octop_gateway.models import InboundMessage
from octop_harness.backends.workspace import BackendWorkspace

from octop.api.common.attachments import save_attachment
from octop.api.routers.chat.models import ChatTurnBody
from octop.api.routers.chat.turn import (
    content_parts_from_dashboard_turn,
)
from octop.infra.backend.resolver import default_agent_backend_spec
from octop.infra.gateway.media.attachment_hints import content_blocks_need_vision
from octop.infra.gateway.media.ingress import AgentBackedMediaBackend
from octop.infra.gateway.process.harness_request import build_content_from_message
from octop.infra.gateway.threads import ThreadRegistry
from octop.infra.gateway.ws import WS_CHANNEL_ID

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _has_image_url(content: Any) -> bool:
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "image_url" for b in content
    )


def _image_ref_path(content: Any) -> str | None:
    if not isinstance(content, list):
        return None
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "image_url":
            continue
        path = str(block.get("workspace_path") or "").strip()
        if path:
            return path
        url_field = block.get("image_url") or {}
        url = url_field.get("url") if isinstance(url_field, dict) else None
        if isinstance(url, str) and url.startswith("workspace://"):
            return url[len("workspace://") :]
    return None


def _image_bytes(content: Any) -> bytes | None:
    if not isinstance(content, list):
        return None
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "image_url":
            continue
        url_field = block.get("image_url") or {}
        url = url_field.get("url") if isinstance(url_field, dict) else None
        if isinstance(url, str) and ";base64," in url:
            return base64.b64decode(url.split(",", 1)[1])
    return None


@pytest.mark.asyncio
async def test_file_in_workspace_with_workspace_path_reaches_llm() -> None:
    """Upload → turn with workspace_path → harness content has path-only image_url ref."""
    with tempfile.TemporaryDirectory() as ws_dir:
        workspace = BackendWorkspace(
            LocalShellBackend(root_dir=ws_dir, virtual_mode=False),
            ws_dir,
        )
        stored = await save_attachment(
            workspace,
            owner_id=1,
            filename="chart.png",
            media_type="image/png",
            data=_PNG,
        )
        assert stored.data_path.startswith("inbound/")
        assert re.search(r"inbound/\d{10,}_chart\.png$", stored.data_path)
        assert await workspace.adownload_bytes(stored.data_path) == _PNG

        preview = f"/api/agents/agent-1/media/preview?source={stored.data_path}"
        turn = ChatTurnBody(
            text="what is this?",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "what is this?"},
                        {
                            "type": "image",
                            "source": {"type": "url", "url": preview, "media_type": "image/png"},
                            "preview_url": preview,
                            "workspace_path": stored.data_path,
                            "filename": "chart.png",
                        },
                    ],
                }
            ],
        )
        parts = content_parts_from_dashboard_turn(turn)
        assert any(getattr(p, "local_path", None) == stored.data_path for p in parts)

        msg = InboundMessage(
            channel_id=WS_CHANNEL_ID,
            channel_type=ThreadRegistry.CHANNEL_DASHBOARD,
            content=parts,
        )
        backend = AgentBackedMediaBackend(workspace)
        content = await build_content_from_message(msg, media_backend=backend)
        assert _has_image_url(content)
        assert content_blocks_need_vision(content)
        assert _image_ref_path(content) == stored.data_path
        assert _image_bytes(content) is None
        from octop.infra.gateway.media.attachment_hints import expand_workspace_image_ref

        img = next(b for b in content if isinstance(b, dict) and b.get("type") == "image_url")
        expanded = await expand_workspace_image_ref(img, workspace=workspace)
        assert base64.b64decode(expanded["image_url"]["url"].split(",", 1)[1]) == _PNG


@pytest.mark.asyncio
async def test_file_in_workspace_preview_only_drops_image_for_llm() -> None:
    """File exists in workspace but turn lacks workspace_path → no vision for LLM."""
    with tempfile.TemporaryDirectory() as ws_dir:
        workspace = BackendWorkspace(
            LocalShellBackend(root_dir=ws_dir, virtual_mode=False),
            ws_dir,
        )
        stored = await save_attachment(
            workspace,
            owner_id=1,
            filename="shot.png",
            media_type="image/png",
            data=_PNG,
        )
        assert await workspace.adownload_bytes(stored.data_path) == _PNG

        preview = f"/api/agents/agent-1/media/preview?source={stored.data_path}"
        turn = ChatTurnBody(
            text="describe",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "describe"},
                        {
                            "type": "image",
                            "source": {"type": "url", "url": preview, "media_type": "image/png"},
                            "preview_url": preview,
                        },
                    ],
                }
            ],
        )
        parts = content_parts_from_dashboard_turn(turn)
        assert not any(getattr(p, "local_path", None) for p in parts)

        msg = InboundMessage(
            channel_id=WS_CHANNEL_ID,
            channel_type=ThreadRegistry.CHANNEL_DASHBOARD,
            content=parts,
        )
        backend = AgentBackedMediaBackend(workspace)
        content = await build_content_from_message(msg, media_backend=backend)
        assert not _has_image_url(content)
        assert not content_blocks_need_vision(content)


@pytest.mark.asyncio
async def test_default_backend_materialize_still_inlines_image() -> None:
    """Production default backend: path ref in content; expand yields vision bytes."""
    from octop_harness.backends import resolve_backend

    with tempfile.TemporaryDirectory() as ws_dir:
        workspace = BackendWorkspace(
            resolve_backend(default_agent_backend_spec(Path(ws_dir)), workspace_dir=ws_dir),
            ws_dir,
        )
        stored = await save_attachment(
            workspace,
            owner_id=1,
            filename="chart.png",
            media_type="image/png",
            data=_PNG,
        )
        assert await workspace.adownload_bytes(stored.data_path) == _PNG

        turn = ChatTurnBody(
            text="see",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "workspace_path": stored.data_path,
                            "media_type": "image/png",
                            "filename": "chart.png",
                        },
                    ],
                }
            ],
        )
        parts = content_parts_from_dashboard_turn(turn)
        msg = InboundMessage(
            channel_id=WS_CHANNEL_ID,
            channel_type=ThreadRegistry.CHANNEL_DASHBOARD,
            content=parts,
        )
        content = await build_content_from_message(
            msg,
            media_backend=AgentBackedMediaBackend(workspace),
        )
        assert _has_image_url(content)
        assert _image_ref_path(content) == stored.data_path
        assert _image_bytes(content) is None
        from octop.infra.gateway.media.attachment_hints import expand_workspace_image_ref

        img = next(b for b in content if isinstance(b, dict) and b.get("type") == "image_url")
        expanded = await expand_workspace_image_ref(img, workspace=workspace)
        assert base64.b64decode(expanded["image_url"]["url"].split(",", 1)[1]) == _PNG


@pytest.mark.asyncio
async def test_no_media_backend_degrades_to_path_hint_not_vision() -> None:
    """Agent stopped (media_backend=None): file readable but LLM gets text hint only."""
    with tempfile.TemporaryDirectory() as ws_dir:
        workspace = BackendWorkspace(
            LocalShellBackend(root_dir=ws_dir, virtual_mode=False),
            ws_dir,
        )
        stored = await save_attachment(
            workspace,
            owner_id=1,
            filename="chart.png",
            media_type="image/png",
            data=_PNG,
        )
        turn = ChatTurnBody(
            text="see",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "workspace_path": stored.data_path,
                            "media_type": "image/png",
                        },
                    ],
                }
            ],
        )
        parts = content_parts_from_dashboard_turn(turn)
        msg = InboundMessage(
            channel_id=WS_CHANNEL_ID,
            channel_type=ThreadRegistry.CHANNEL_DASHBOARD,
            content=parts,
        )
        content = await build_content_from_message(msg, media_backend=None)
        assert not _has_image_url(content)
        assert isinstance(content, str)
        assert stored.data_path in content or "inbound/" in content


def _inline_png_block(payload: bytes) -> dict[str, Any]:
    """A ready-made inline vision block (already base64) for budget tests."""
    return {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64," + base64.b64encode(payload).decode()},
    }


def test_vision_limits_are_configurable_and_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCTOP_VISION_MAX_COUNT accepts sane values and falls back on bad ones."""
    from octop.infra.gateway.media.attachment_hints import _env_int

    monkeypatch.setenv("OCTOP_TEST_VISION_COUNT", "20")
    assert _env_int("OCTOP_TEST_VISION_COUNT", 12, low=1, high=32) == 20
    monkeypatch.setenv("OCTOP_TEST_VISION_COUNT", "999")
    assert _env_int("OCTOP_TEST_VISION_COUNT", 12, low=1, high=32) == 32
    monkeypatch.setenv("OCTOP_TEST_VISION_COUNT", "lots")
    assert _env_int("OCTOP_TEST_VISION_COUNT", 12, low=1, high=32) == 12
    monkeypatch.delenv("OCTOP_TEST_VISION_COUNT")
    assert _env_int("OCTOP_TEST_VISION_COUNT", 12, low=1, high=32) == 12


def test_default_vision_count_covers_multi_shot_flows() -> None:
    """A product/storyboard turn needs more than the old four-image cap."""
    from octop.infra.gateway.media.attachment_hints import VISION_MAX_COUNT

    assert VISION_MAX_COUNT >= 8


@pytest.mark.asyncio
async def test_images_beyond_count_cap_degrade_to_path_hints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Image parts past the per-turn cap keep a path hint instead of vision bytes."""
    from octop.infra.gateway.process import harness_request

    monkeypatch.setattr(harness_request, "VISION_MAX_COUNT", 2)
    with tempfile.TemporaryDirectory() as ws_dir:
        workspace = BackendWorkspace(
            LocalShellBackend(root_dir=ws_dir, virtual_mode=False),
            ws_dir,
        )
        stored = [
            await save_attachment(
                workspace,
                owner_id=1,
                filename=f"shot{i}.png",
                media_type="image/png",
                data=_PNG,
            )
            for i in range(3)
        ]
        preview = f"/api/agents/agent-1/media/preview?source={stored[0].data_path}"
        content: list[dict[str, Any]] = [{"type": "text", "text": "four shots"}]
        for item in stored:
            content.append(
                {
                    "type": "image",
                    "source": {"type": "url", "url": preview, "media_type": "image/png"},
                    "preview_url": preview,
                    "workspace_path": item.data_path,
                    "filename": item.filename,
                }
            )
        turn = ChatTurnBody(text="four shots", messages=[{"role": "user", "content": content}])
        msg = InboundMessage(
            channel_id=WS_CHANNEL_ID,
            channel_type=ThreadRegistry.CHANNEL_DASHBOARD,
            content=content_parts_from_dashboard_turn(turn),
        )
        built = await build_content_from_message(
            msg, media_backend=AgentBackedMediaBackend(workspace)
        )
        assert isinstance(built, list)
        images = [b for b in built if isinstance(b, dict) and b.get("type") == "image_url"]
        assert len(images) == 2
        joined = "\n".join(
            str(b.get("text") or "")
            for b in built
            if isinstance(b, dict) and b.get("type") == "text"
        )
        assert stored[2].data_path in joined


def test_workspace_image_middleware_enforces_total_byte_budget() -> None:
    """One request never inlines more than the byte budget; excess becomes text."""
    from langchain_core.messages import HumanMessage

    from octop.infra.agents.middleware.workspace_image import (
        WorkspaceImageMaterializeMiddleware,
    )

    payload = b"x" * 300_000  # 300 KB decoded per block
    blocks = [_inline_png_block(payload) for _ in range(4)]
    middleware = WorkspaceImageMaterializeMiddleware(
        workspace=None,  # inline blocks never touch the workspace
        total_max_bytes=700_000,
    )
    messages = [HumanMessage(content=list(blocks))]
    out = middleware._expand_messages_sync(messages)
    prepared = out[0].content
    assert isinstance(prepared, list)
    kept = [b for b in prepared if isinstance(b, dict) and b.get("type") == "image_url"]
    omitted = [
        b
        for b in prepared
        if isinstance(b, dict) and b.get("type") == "text" and "byte budget" in str(b.get("text"))
    ]
    assert len(kept) == 2
    assert len(omitted) == 2

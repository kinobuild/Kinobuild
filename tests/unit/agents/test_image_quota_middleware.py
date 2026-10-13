"""Image quota agent middleware tests.

Covers the per-item media cap that the token quota cannot express: image and
video generation are billed per item and never appear in the token ledger.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from langchain_core.messages import ToolMessage

from octop.infra.agents.middleware.image_quota import (
    ImageQuotaMiddleware,
    requested_items,
)
from octop.infra.errors import ErrorCode, OctopError


def _request(name: str, *, args: dict[str, Any] | None = None) -> Any:
    return SimpleNamespace(tool_call={"name": name, "id": "call-1", "args": args or {}})


async def _handler_ok(request: Any) -> ToolMessage:
    return ToolMessage(content="done", tool_call_id="call-1")


async def _handler_error(request: Any) -> ToolMessage:
    return ToolMessage(content="boom", tool_call_id="call-1", status="error")


def _patch_user(monkeypatch: pytest.MonkeyPatch, user: Any) -> None:
    monkeypatch.setattr(
        "octop.infra.agents.middleware.token_quota.get_config",
        lambda: {"configurable": {"user": user}},
    )


def test_requested_items_reads_count_aliases() -> None:
    assert requested_items({"count": 4}) == 4
    assert requested_items({"n": 2}) == 2
    assert requested_items({"num_images": 3}) == 3
    assert requested_items({}) == 1
    assert requested_items(None) == 1
    assert requested_items({"count": 0}) == 1
    assert requested_items({"count": True}) == 1


@pytest.mark.asyncio
async def test_blocks_generation_once_quota_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policies = Mock()
    policies.get.return_value = SimpleNamespace(enabled=True, value="30")
    usage = Mock()
    usage.media_calls_for_user.return_value = 30
    _patch_user(monkeypatch, "7")

    middleware = ImageQuotaMiddleware(policy_repo=policies, usage_repo=usage)
    result = await middleware.awrap_tool_call(_request("generate_image"), _handler_ok)

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    policies.get.assert_called_once_with(7, "image_quota")
    usage.media_calls_for_user.assert_called_once_with(7)
    # Nothing is generated, so nothing is recorded.
    usage.record_media_call.assert_not_called()


@pytest.mark.asyncio
async def test_allows_and_records_when_under_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policies = Mock()
    policies.get.return_value = SimpleNamespace(enabled=True, value="30")
    usage = Mock()
    usage.media_calls_for_user.return_value = 4
    _patch_user(monkeypatch, 7)

    middleware = ImageQuotaMiddleware(policy_repo=policies, usage_repo=usage, agent_id="AG1")
    result = await middleware.awrap_tool_call(
        _request("generate_image", args={"count": 3}), _handler_ok
    )

    assert isinstance(result, ToolMessage)
    assert result.status != "error"
    usage.record_media_call.assert_called_once_with(
        agent_id="AG1", user_id=7, tool="generate_image", images=3
    )


@pytest.mark.asyncio
async def test_unlimited_user_bypasses_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policies = Mock()
    policies.get.return_value = None
    usage = Mock()
    usage.media_calls_for_user.return_value = 0
    _patch_user(monkeypatch, 8)

    middleware = ImageQuotaMiddleware(policy_repo=policies, usage_repo=usage)
    await middleware.awrap_tool_call(_request("generate_image"), _handler_ok)

    usage.media_calls_for_user.assert_not_called()
    usage.record_media_call.assert_called_once()


@pytest.mark.asyncio
async def test_failed_generation_does_not_consume_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policies = Mock()
    policies.get.return_value = None
    usage = Mock()
    usage.media_calls_for_user.return_value = 0
    _patch_user(monkeypatch, 9)

    middleware = ImageQuotaMiddleware(policy_repo=policies, usage_repo=usage)
    result = await middleware.awrap_tool_call(_request("generate_image"), _handler_error)

    assert result.status == "error"
    usage.record_media_call.assert_not_called()


@pytest.mark.asyncio
async def test_non_media_tools_are_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policies = Mock()
    usage = Mock()
    _patch_user(monkeypatch, 9)

    middleware = ImageQuotaMiddleware(policy_repo=policies, usage_repo=usage)
    await middleware.awrap_tool_call(_request("read_file"), _handler_ok)

    policies.get.assert_not_called()
    usage.media_calls_for_user.assert_not_called()
    usage.record_media_call.assert_not_called()


def test_image_quota_policy_normalisation() -> None:
    from octop.infra.users.resource_policy import (
        image_quota_of,
        normalize_image_quota,
        public_policy_fields,
    )

    assert image_quota_of(None) is None
    assert image_quota_of({"image_quota": "25"}) == 25
    assert image_quota_of(SimpleNamespace(enabled=True, value="25")) == 25
    assert image_quota_of(SimpleNamespace(enabled=False, value="25")) is None
    assert normalize_image_quota(None) is None
    assert normalize_image_quota(0) == 0
    with pytest.raises(OctopError) as exc:
        normalize_image_quota(-1)
    assert exc.value.code is ErrorCode.FORBIDDEN

    fields = public_policy_fields({"image_quota": "12", "token_quota": "900"})
    assert fields["image_quota"] == 12
    assert fields["token_quota"] == 900

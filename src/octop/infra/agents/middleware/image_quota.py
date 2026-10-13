"""Reject media generation once the acting user has exhausted their image quota.

``TokenQuotaMiddleware`` cannot cover this: image and video generation are billed
per item by the upstream provider and never land in ``usage_log``'s token columns.
With one shared relay key for a whole deployment, a single account could therefore
spend the entire media budget without the token quota ever noticing.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

from octop.i18n.domains.errors import error_message
from octop.infra.agents.middleware.token_quota import configurable_user_id
from octop.infra.errors import ErrorCode
from octop.infra.users.resource_policy import POLICY_IMAGE_QUOTA, image_quota_of

logger = logging.getLogger(__name__)

#: Tools that spend money per generated item.
MEDIA_TOOLS: frozenset[str] = frozenset({"generate_image", "generate_video"})

#: Argument names providers use for the item count.
_COUNT_KEYS = ("count", "n", "num_images", "num_videos")


def requested_items(args: Any) -> int:
    """How many media items this call asks for (defaults to 1)."""
    if not isinstance(args, dict):
        return 1
    for key in _COUNT_KEYS:
        raw = args.get(key)
        if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
            return raw
    return 1


class ImageQuotaMiddleware(AgentMiddleware[Any, Any]):
    """Count media items per user and refuse generation past the configured cap."""

    def __init__(
        self,
        *,
        policy_repo: Any,
        usage_repo: Any,
        user_repo: Any = None,
        agent_id: str = "",
    ) -> None:
        super().__init__()
        self._policies = policy_repo
        self._usage = usage_repo
        self._users = user_repo
        self._agent_id = agent_id

    def _locale(self, user_id: int) -> str:
        if self._users is None or user_id <= 0:
            return "zh"
        try:
            row = self._users.get(user_id)
        except Exception:  # pragma: no cover - locale is cosmetic here
            return "zh"
        raw = getattr(row, "locale", None)
        return str(raw) if raw else "zh"

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        tool_call = request.tool_call
        tool_name = str(tool_call.get("name") or "")
        if tool_name not in MEDIA_TOOLS:
            return await handler(request)

        user_id = configurable_user_id()
        if user_id is None:
            return await handler(request)

        quota = image_quota_of(self._policies.get(user_id, POLICY_IMAGE_QUOTA))
        # Only pay for the usage query when a cap is actually configured: an
        # unlimited user (the default) must not cost a DB round-trip per image.
        if quota is not None:
            used = int(self._usage.media_calls_for_user(user_id))
            if used >= quota:
                logger.info(
                    "ImageQuota blocked %s for user %s (%s/%s)",
                    tool_name,
                    user_id,
                    used,
                    quota,
                )
                return ToolMessage(
                    content=error_message(
                        ErrorCode.IMAGE_QUOTA_EXCEEDED,
                        self._locale(user_id),
                        used=used,
                        quota=quota,
                    ),
                    tool_call_id=str(tool_call.get("id") or ""),
                    status="error",
                )

        result = await handler(request)

        # Only successful generations spend budget — a rejected or failed call
        # must not consume the user's allowance.
        if isinstance(result, ToolMessage) and str(getattr(result, "status", "")) == "error":
            return result
        try:
            self._usage.record_media_call(
                agent_id=self._agent_id,
                user_id=user_id,
                tool=tool_name,
                images=requested_items(tool_call.get("args")),
            )
        except Exception:  # pragma: no cover - bookkeeping must not fail the tool
            logger.warning("failed to record media call for user %s", user_id, exc_info=True)
        return result


__all__ = ["ImageQuotaMiddleware", "MEDIA_TOOLS", "requested_items"]

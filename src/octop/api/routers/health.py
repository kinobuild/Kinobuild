"""Liveness probe (no auth)."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version
from typing import Any

from fastapi import APIRouter, Depends

from octop.api.deps import get_server

router = APIRouter()


def _app_version() -> str:
    """Installed package version, or ``""`` when running from an uninstalled tree.

    The desktop client reads this to refuse a server that is older than the APIs
    it needs, instead of failing later with scattered 404s.
    """
    try:
        return _package_version("octop")
    except PackageNotFoundError:
        return ""


@router.get("", summary="Health check")
async def health(server: Any = Depends(get_server)) -> dict[str, Any]:
    """Liveness probe: database reachability, user count, and loaded agents. No auth required."""
    bound = server.database_bound
    users = server.user_manager.count() if server.user_manager is not None else 0
    agents = (
        len(server.app_runtime.agent_registry.list_rows()) if server.app_runtime is not None else 0
    )
    return {
        "ok": True,
        "started_at": server._started_at,
        "db": bound,
        "users_loaded": users,
        "agents_running": agents,
        "version": _app_version(),
    }

"""Prepaid token vouchers — admin generation and user redemption."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from octop.api.deps import current_user, get_server, require_permission
from octop.infra.errors import ErrorCode, OctopError
from octop.infra.users.identity import User
from octop.infra.users.quota_redeem import generate_codes, normalize_code, redeem_code
from octop.infra.users.resource_policy import POLICY_TOKEN_QUOTA, token_quota_of

router = APIRouter()


class GenerateCodesBody(BaseModel):
    count: int = Field(default=10, ge=1, le=200, description="How many vouchers to mint.")
    tokens: int = Field(
        gt=0,
        description="Token value of each voucher; redeem adds this to the account quota.",
    )
    note: str = Field(default="", max_length=200, description="Internal note (order id, buyer).")


class RedeemBody(BaseModel):
    code: str = Field(min_length=1, max_length=64, description="Voucher code.")


class RevokeBody(BaseModel):
    code: str = Field(min_length=1, max_length=64)


def _code_payload(row: Any) -> dict[str, Any]:
    return {
        "code": row.code,
        "tokens": row.tokens,
        "note": row.note,
        "status": row.status,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "redeemed_by": row.redeemed_by,
        "redeemed_at": row.redeemed_at,
        "revoked_at": row.revoked_at,
    }


def _quota_payload(server: Any, user_id: int) -> dict[str, Any]:
    quota = token_quota_of(server.services.user_policy_repo.get(user_id, POLICY_TOKEN_QUOTA))
    used = int(server.services.usage_repo.total_tokens_for_user(user_id))
    return {
        "token_quota": quota,
        "quota_used": used,
        "quota_remaining": None if quota is None else max(0, quota - used),
    }


@router.get("", summary="Current account token quota")
async def get_quota(
    user: Any = Depends(current_user),
    server: Any = Depends(get_server),
) -> dict[str, Any]:
    return _quota_payload(server, int(user.id))


@router.post("/redeem", summary="Redeem a token voucher")
async def redeem(
    body: RedeemBody,
    user: Any = Depends(current_user),
    server: Any = Depends(get_server),
) -> dict[str, Any]:
    result = redeem_code(
        repo=server.services.quota_redeem_code_repo,
        policy_repo=server.services.user_policy_repo,
        usage_repo=server.services.usage_repo,
        user_id=int(user.id),
        raw_code=body.code,
    )
    return {"ok": True, **result}


@router.post("", summary="Generate token vouchers (admin)")
async def create_codes(
    body: GenerateCodesBody,
    admin: User = Depends(require_permission("users")),
    server: Any = Depends(get_server),
) -> dict[str, Any]:
    rows = generate_codes(
        server.services.quota_redeem_code_repo,
        count=body.count,
        tokens=body.tokens,
        note=body.note.strip(),
        created_by=int(admin.id),
    )
    return {
        "codes": [_code_payload(row) for row in rows],
        "count": len(rows),
        "tokens_each": body.tokens,
        "total_tokens": body.tokens * len(rows),
    }


@router.get("/codes", summary="List token vouchers (admin)")
async def list_codes(
    status: str | None = None,
    limit: int = 100,
    _: User = Depends(require_permission("users")),
    server: Any = Depends(get_server),
) -> dict[str, Any]:
    rows = server.services.quota_redeem_code_repo.list_recent(
        limit=max(1, min(limit, 500)), status=status
    )
    return {"codes": [_code_payload(row) for row in rows]}


@router.post("/codes/revoke", summary="Revoke an unused voucher (admin)")
async def revoke_code(
    body: RevokeBody,
    _: User = Depends(require_permission("users")),
    server: Any = Depends(get_server),
) -> dict[str, Any]:
    code = normalize_code(body.code)
    if not server.services.quota_redeem_code_repo.revoke(code):
        raise OctopError(ErrorCode.QUOTA_CODE_INVALID, "code not found or already used", status=404)
    return {"ok": True, "code": code}

"""Prepaid token vouchers: code generation and redemption."""

from __future__ import annotations

import secrets
from typing import Any, cast

from octop.infra.errors import ErrorCode, OctopError
from octop.infra.users.resource_policy import POLICY_TOKEN_QUOTA, token_quota_of

# Ambiguous glyphs (I, O, 0, 1) are excluded so codes survive being read aloud.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_BODY_LENGTH = 12
_CODE_GROUP = 4
MAX_CODES_PER_REQUEST = 200


def new_code() -> str:
    """Return one ``KG-XXXX-XXXX-XXXX`` voucher code."""
    body = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_BODY_LENGTH))
    groups = [body[i : i + _CODE_GROUP] for i in range(0, _CODE_BODY_LENGTH, _CODE_GROUP)]
    return "KG-" + "-".join(groups)


def normalize_code(raw: str) -> str:
    """Upper-case and strip whitespace so a typed code always matches storage."""
    return str(raw or "").strip().upper()


def generate_codes(
    repo: Any,
    *,
    count: int,
    tokens: int,
    note: str,
    created_by: int | None,
) -> list[Any]:
    """Create *count* unused vouchers worth *tokens* each."""
    if tokens <= 0:
        raise OctopError(ErrorCode.QUOTA_CODE_INVALID, "tokens must be positive", status=400)
    if count <= 0 or count > MAX_CODES_PER_REQUEST:
        raise OctopError(
            ErrorCode.QUOTA_CODE_INVALID,
            f"count must be between 1 and {MAX_CODES_PER_REQUEST}",
            status=400,
        )
    codes: list[str] = []
    seen: set[str] = set()
    while len(codes) < count:
        code = new_code()
        if code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return cast(
        "list[Any]",
        repo.create_many(codes=codes, tokens=tokens, note=note, created_by=created_by),
    )


def redeem_code(
    *,
    repo: Any,
    policy_repo: Any,
    usage_repo: Any,
    user_id: int,
    raw_code: str,
) -> dict[str, Any]:
    """Spend one voucher and raise the account's lifetime token quota.

    Quota is a lifetime cap: an account with no quota yet starts from what it has
    already spent, so the voucher adds exactly its face value of new headroom.
    """
    code = normalize_code(raw_code)
    if not code:
        raise OctopError(ErrorCode.QUOTA_CODE_INVALID, "code required", status=400)
    row = repo.get(code)
    if row is None:
        raise OctopError(ErrorCode.QUOTA_CODE_INVALID, "code not found", status=404)
    if row.revoked_at is not None:
        raise OctopError(ErrorCode.QUOTA_CODE_REVOKED, "code revoked", status=409)
    if row.redeemed_at is not None:
        raise OctopError(ErrorCode.QUOTA_CODE_ALREADY_USED, "code already used", status=409)
    if not repo.claim(code, user_id=user_id):
        # Lost the race with another redemption of the same code.
        raise OctopError(ErrorCode.QUOTA_CODE_ALREADY_USED, "code already used", status=409)

    current = token_quota_of(policy_repo.get(user_id, POLICY_TOKEN_QUOTA))
    used = int(usage_repo.total_tokens_for_user(user_id))
    base = used if current is None else current
    new_quota = base + int(row.tokens)
    policy_repo.merge(user_id, {POLICY_TOKEN_QUOTA: str(new_quota)})
    return {
        "tokens": int(row.tokens),
        "token_quota": new_quota,
        "quota_used": used,
        "quota_remaining": max(0, new_quota - used),
    }

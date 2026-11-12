"""Prepaid token vouchers: generation, redemption, and quota arithmetic."""

from __future__ import annotations

from pathlib import Path

import pytest

from octop.infra.db.migrate import run_migrations
from octop.infra.db.pool import SqlitePool
from octop.infra.db.services import RepoBundle
from octop.infra.errors import ErrorCode, OctopError
from octop.infra.users.quota_redeem import generate_codes, normalize_code, redeem_code
from octop.infra.users.resource_policy import POLICY_TOKEN_QUOTA


@pytest.fixture
def repos(tmp_path: Path) -> RepoBundle:
    pool = SqlitePool(tmp_path / "octop.db")
    run_migrations(pool)
    return RepoBundle.from_pool(pool)


def _user(repos: RepoBundle, name: str = "ada") -> int:
    return repos.user_repo.create(
        username=name, password_hash=None, role="user", display_name=None, locale="zh"
    )


def _redeem(repos: RepoBundle, user_id: int, code: str) -> dict[str, object]:
    return redeem_code(
        repo=repos.quota_redeem_code_repo,
        policy_repo=repos.user_policy_repo,
        usage_repo=ReposUsage(repos),
        user_id=user_id,
        raw_code=code,
    )


class ReposUsage:
    """Thin adapter: the real UsageRepo takes the pool; tests only need the total."""

    def __init__(self, repos: RepoBundle) -> None:
        self._repo = repos.usage_repo

    def total_tokens_for_user(self, user_id: int) -> int:
        return int(self._repo.total_tokens_for_user(user_id))


def test_generate_creates_unique_unused_codes(repos: RepoBundle) -> None:
    rows = generate_codes(
        repos.quota_redeem_code_repo, count=5, tokens=3_000_000, note="order-42", created_by=1
    )
    assert len(rows) == 5
    assert len({row.code for row in rows}) == 5
    for row in rows:
        assert row.code.startswith("KG-")
        assert row.tokens == 3_000_000
        assert row.status == "unused"
        assert row.note == "order-42"


def test_redeem_raises_quota_by_face_value(repos: RepoBundle) -> None:
    uid = _user(repos)
    code = generate_codes(
        repos.quota_redeem_code_repo, count=1, tokens=1_000_000, note="", created_by=1
    )[0].code

    result = _redeem(repos, uid, code)

    assert result["tokens"] == 1_000_000
    assert result["token_quota"] == 1_000_000
    assert result["quota_used"] == 0
    assert result["quota_remaining"] == 1_000_000
    stored = repos.user_policy_repo.get(uid, POLICY_TOKEN_QUOTA)
    assert stored is not None and int(stored.value) == 1_000_000


def test_redeem_is_case_insensitive(repos: RepoBundle) -> None:
    uid = _user(repos)
    code = generate_codes(repos.quota_redeem_code_repo, count=1, tokens=10, note="", created_by=1)[
        0
    ].code

    result = _redeem(repos, uid, code.lower())

    assert result["token_quota"] == 10
    assert normalize_code(code.lower()) == code


def test_redeem_twice_fails_with_already_used(repos: RepoBundle) -> None:
    uid = _user(repos)
    code = generate_codes(repos.quota_redeem_code_repo, count=1, tokens=10, note="", created_by=1)[
        0
    ].code
    _redeem(repos, uid, code)

    with pytest.raises(OctopError) as excinfo:
        _redeem(repos, uid, code)
    assert excinfo.value.code == ErrorCode.QUOTA_CODE_ALREADY_USED


def test_unknown_code_is_invalid(repos: RepoBundle) -> None:
    uid = _user(repos)
    with pytest.raises(OctopError) as excinfo:
        _redeem(repos, uid, "KG-AAAA-BBBB-CCCC")
    assert excinfo.value.code == ErrorCode.QUOTA_CODE_INVALID


def test_revoked_code_is_rejected(repos: RepoBundle) -> None:
    uid = _user(repos)
    code = generate_codes(repos.quota_redeem_code_repo, count=1, tokens=10, note="", created_by=1)[
        0
    ].code
    assert repos.quota_redeem_code_repo.revoke(code) is True

    with pytest.raises(OctopError) as excinfo:
        _redeem(repos, uid, code)
    assert excinfo.value.code == ErrorCode.QUOTA_CODE_REVOKED


def test_second_code_stacks_on_top_of_first(repos: RepoBundle) -> None:
    uid = _user(repos)
    first, second = generate_codes(
        repos.quota_redeem_code_repo, count=2, tokens=1_000_000, note="", created_by=1
    )
    _redeem(repos, uid, first.code)
    result = _redeem(repos, uid, second.code)
    assert result["token_quota"] == 2_000_000


def test_unlimited_account_starts_from_what_it_already_spent(repos: RepoBundle) -> None:
    uid = _user(repos)
    spent = 500_000

    class SpendingUsage:
        def total_tokens_for_user(self, _uid: int) -> int:
            return spent

    code = generate_codes(
        repos.quota_redeem_code_repo, count=1, tokens=1_000_000, note="", created_by=1
    )[0].code
    result = redeem_code(
        repo=repos.quota_redeem_code_repo,
        policy_repo=repos.user_policy_repo,
        usage_repo=SpendingUsage(),
        user_id=uid,
        raw_code=code,
    )
    # Unlimited before: the voucher must add new headroom, not retro-cap the spend.
    assert result["token_quota"] == 1_500_000
    assert result["quota_remaining"] == 1_000_000

"""Unit tests for invite code helpers and repo redeem."""

from __future__ import annotations

from pathlib import Path

import pytest

from octop.infra.db.migrate import run_migrations
from octop.infra.db.pool import SqlitePool
from octop.infra.db.repos._base import now_ts
from octop.infra.db.repos.invites import InviteRepo
from octop.infra.db.repos.users import UserRepo
from octop.infra.users.invites import (
    DEFAULT_EXPIRES_DAYS,
    generate_invite_code,
    invite_path,
)
from octop.infra.users.password import hash_password


@pytest.fixture
def db(tmp_path: Path) -> SqlitePool:
    pool = SqlitePool(tmp_path / "octop.db")
    run_migrations(pool)
    return pool


def test_generate_invite_code_shape() -> None:
    code = generate_invite_code()
    assert len(code) == 11
    assert code.isalnum()
    assert invite_path(code) == f"/invite?code={code}"


def test_invite_repo_redeem_once(db: SqlitePool) -> None:
    users = UserRepo(db)
    invites = InviteRepo(db)
    admin_id = users.create(
        username="admin",
        password_hash=hash_password("AdminPass12"),
        role="admin",
    )
    invite = invites.create(
        code="AbCdEfGhIjK",
        created_by=admin_id,
        expires_at=now_ts() + DEFAULT_EXPIRES_DAYS * 86400,
        note="n1",
    )
    assert invite.status() == "pending"

    uid, used = invites.redeem_creating_user(
        code="AbCdEfGhIjK",
        username="newbie",
        password_hash=hash_password("NewbiePass12"),
        display_name="N",
        locale="zh",
    )
    assert uid > 0
    assert used.status() == "used"
    assert users.get_by_username("newbie") is not None

    with pytest.raises(ValueError, match="used"):
        invites.redeem_creating_user(
            code="AbCdEfGhIjK",
            username="other",
            password_hash=hash_password("OtherPass12"),
            display_name=None,
            locale="en",
        )


def test_invite_repo_revoke(db: SqlitePool) -> None:
    users = UserRepo(db)
    invites = InviteRepo(db)
    admin_id = users.create(
        username="admin2",
        password_hash=hash_password("AdminPass12"),
        role="admin",
    )
    invite = invites.create(
        code="ZzYyXxWwVvU",
        created_by=admin_id,
        expires_at=now_ts() + 86400,
    )
    revoked = invites.revoke(invite.id)
    assert revoked is not None
    assert revoked.status() == "revoked"


def _redeem(invites: InviteRepo, code: str, username: str) -> tuple[int, object]:
    return invites.redeem_creating_user(
        code=code,
        username=username,
        password_hash=hash_password("MemberPass12"),
        display_name=None,
        locale="zh",
    )


def test_invite_repo_redeem_respects_max_uses(db: SqlitePool) -> None:
    users = UserRepo(db)
    invites = InviteRepo(db)
    admin_id = users.create(
        username="multiadmin",
        password_hash=hash_password("AdminPass12"),
        role="admin",
    )
    invite = invites.create(
        code="MultiUse001",
        created_by=admin_id,
        expires_at=now_ts() + 86400,
        max_uses=2,
    )
    assert invite.max_uses == 2
    assert invite.used_count == 0
    assert invite.status() == "pending"

    _uid1, after_first = _redeem(invites, "MultiUse001", "member_a")
    assert after_first.used_count == 1
    assert after_first.status() == "pending"

    _uid2, after_second = _redeem(invites, "MultiUse001", "member_b")
    assert after_second.used_count == 2
    assert after_second.status() == "used"

    with pytest.raises(ValueError, match="used"):
        _redeem(invites, "MultiUse001", "member_c")


def test_invite_repo_unlimited_redemptions(db: SqlitePool) -> None:
    users = UserRepo(db)
    invites = InviteRepo(db)
    admin_id = users.create(
        username="openadmin",
        password_hash=hash_password("AdminPass12"),
        role="admin",
    )
    invite = invites.create(
        code="OpenEnded01",
        created_by=admin_id,
        expires_at=now_ts() + 86400,
        max_uses=None,
    )
    assert invite.max_uses is None

    for index in range(3):
        _uid, row = _redeem(invites, "OpenEnded01", f"open_member_{index}")
        assert row.used_count == index + 1
        assert row.status() == "pending"


def test_invite_repo_revoke_partially_used_multi_use(db: SqlitePool) -> None:
    """A leaked team link must still be revocable after a few people joined."""
    users = UserRepo(db)
    invites = InviteRepo(db)
    admin_id = users.create(
        username="revokeadmin",
        password_hash=hash_password("AdminPass12"),
        role="admin",
    )
    invite = invites.create(
        code="RevokeMulti",
        created_by=admin_id,
        expires_at=now_ts() + 86400,
        max_uses=5,
    )
    _uid, after_first = _redeem(invites, "RevokeMulti", "joined_before_revoke")
    assert after_first.status() == "pending"

    revoked = invites.revoke(invite.id)
    assert revoked is not None
    assert revoked.status() == "revoked"
    assert revoked.used_count == 1

    with pytest.raises(ValueError, match="revoked"):
        _redeem(invites, "RevokeMulti", "joined_after_revoke")


def test_legacy_invite_rows_pinned_to_single_use(db: SqlitePool) -> None:
    """Upgrading must not turn a pre-v21 one-time code into an unlimited one."""
    users = UserRepo(db)
    admin_id = users.create(
        username="legacyadmin",
        password_hash=hash_password("AdminPass12"),
        role="admin",
    )
    ts = now_ts()
    with db.transaction() as conn:
        conn.execute("ALTER TABLE user_invites DROP COLUMN max_uses")
        conn.execute("ALTER TABLE user_invites DROP COLUMN used_count")
        conn.execute(
            "INSERT INTO user_invites(code, created_by, note, created_at, expires_at, "
            "role_name, role) VALUES (?, ?, NULL, ?, ?, NULL, NULL)",
            ("LegacyCode1", admin_id, ts, ts + 86400),
        )
        conn.execute(
            "INSERT INTO user_invites(code, created_by, note, created_at, expires_at, "
            "used_at, used_by_user_id, role_name, role) VALUES (?, ?, NULL, ?, ?, ?, ?, NULL, NULL)",
            ("LegacyUsed1", admin_id, ts, ts + 86400, ts, admin_id),
        )

    run_migrations(db)
    invites = InviteRepo(db)
    pending = invites.get_by_code("LegacyCode1")
    assert pending is not None
    assert (pending.max_uses, pending.used_count, pending.status()) == (1, 0, "pending")
    spent = invites.get_by_code("LegacyUsed1")
    assert spent is not None
    assert (spent.max_uses, spent.used_count, spent.status()) == (1, 1, "used")

    unlimited = invites.create(
        code="KeepOpen001",
        created_by=admin_id,
        expires_at=ts + 86400,
        max_uses=None,
    )
    assert unlimited.max_uses is None
    run_migrations(db)
    assert invites.get_by_code("KeepOpen001").max_uses is None

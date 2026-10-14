"""User invite table access."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from octop.infra.db.pool import DatabasePool
from octop.infra.db.repos._base import DbRow, insert_returning_id, map_rows, now_ts
from octop.infra.utils.ulid import new_ulid


def _optional_text(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


@dataclass(frozen=True)
class InviteRow:
    id: int
    code: str
    created_by: int
    note: str | None
    created_at: int
    expires_at: int
    used_at: int | None
    used_by_user_id: int | None
    revoked_at: int | None
    role_name: str | None = None
    role: str | None = None
    max_uses: int | None = 1
    used_count: int = 0

    @classmethod
    def from_row(cls, row: DbRow) -> InviteRow:
        keys = set(row.keys())
        # Columns absent (pre-v21 physical schema) fall back to single-use.
        raw_max_uses = row["max_uses"] if "max_uses" in keys else 1
        raw_used_count = row["used_count"] if "used_count" in keys else 0
        return cls(
            id=int(row["id"]),
            code=str(row["code"]),
            created_by=int(row["created_by"]),
            note=row["note"],
            created_at=int(row["created_at"]),
            expires_at=int(row["expires_at"]),
            used_at=int(row["used_at"]) if row["used_at"] is not None else None,
            used_by_user_id=(
                int(row["used_by_user_id"]) if row["used_by_user_id"] is not None else None
            ),
            revoked_at=int(row["revoked_at"]) if row["revoked_at"] is not None else None,
            role_name=_optional_text(row["role_name"]) if "role_name" in keys else None,
            role=_optional_text(row["role"]) if "role" in keys else None,
            max_uses=int(raw_max_uses) if raw_max_uses is not None else None,
            used_count=int(raw_used_count) if raw_used_count is not None else 0,
        )

    def is_exhausted(self) -> bool:
        """True once the invite has admitted ``max_uses`` users (``NULL`` = unlimited)."""
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return True
        # Pre-v21 rows only carried ``used_at``; a missing counter still means used.
        return self.used_count <= 0 and self.used_at is not None

    def status(self, *, now: int | None = None) -> str:
        ts = now if now is not None else now_ts()
        if self.revoked_at is not None:
            return "revoked"
        if self.is_exhausted():
            return "used"
        if self.expires_at <= ts:
            return "expired"
        return "pending"


class InviteRepo:
    def __init__(self, db: DatabasePool) -> None:
        self._db = db

    def create(
        self,
        *,
        code: str,
        created_by: int,
        expires_at: int,
        note: str | None = None,
        role_name: str | None = None,
        role: str | None = None,
        max_uses: int | None = 1,
    ) -> InviteRow:
        ts = now_ts()
        with self._db.transaction() as conn:
            invite_id = insert_returning_id(
                conn,
                "INSERT INTO user_invites("
                "code, created_by, note, created_at, expires_at, role_name, role, max_uses"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (code, created_by, note, ts, expires_at, role_name, role, max_uses),
            )
        row = self.get(invite_id)
        assert row is not None
        return row

    def get(self, invite_id: int) -> InviteRow | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM user_invites WHERE id = ?", (invite_id,)).fetchone()
        return InviteRow.from_row(row) if row else None

    def get_by_code(self, code: str) -> InviteRow | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM user_invites WHERE code = ?", (code,)).fetchone()
        return InviteRow.from_row(row) if row else None

    def list_all(self) -> list[InviteRow]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM user_invites ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return map_rows(rows, InviteRow)

    def revoke(self, invite_id: int) -> InviteRow | None:
        ts = now_ts()
        with self._db.transaction() as conn:
            row = conn.execute("SELECT * FROM user_invites WHERE id = ?", (invite_id,)).fetchone()
            if row is None:
                return None
            invite = InviteRow.from_row(row)
            # Partially redeemed multi-use codes can still be revoked: that is
            # how an admin kills a link that leaked into a group chat.
            if invite.revoked_at is not None or invite.is_exhausted():
                return invite
            conn.execute(
                "UPDATE user_invites SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL "
                "AND (max_uses IS NULL OR used_count < max_uses)",
                (ts, invite_id),
            )
        return self.get(invite_id)

    def redeem_creating_user(
        self,
        *,
        code: str,
        username: str,
        password_hash: str,
        display_name: str | None,
        locale: str,
        email: str | None = None,
        account_role: str = "user",
        permissions: list[str] | None = None,
        policies: list[tuple[str, str]] | None = None,
        role_name: str | None = None,
    ) -> tuple[int, InviteRow]:
        """Create a user and mark the invite used in one transaction.

        ``account_role`` is the role-template public id written to ``users.role``.

        Returns ``(user_id, invite)``. Caller must hold any in-memory locks.
        Raises ``LookupError`` when the invite is missing, ``ValueError`` with
        status ``used`` / ``expired`` / ``revoked`` / ``username_taken`` /
        ``email_taken``.
        """
        ts = now_ts()
        with self._db.transaction() as conn:
            row = conn.execute("SELECT * FROM user_invites WHERE code = ?", (code,)).fetchone()
            if row is None:
                raise LookupError("invite not found")
            invite = InviteRow.from_row(row)
            status = invite.status(now=ts)
            if status != "pending":
                raise ValueError(status)

            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing is not None:
                raise ValueError("username_taken")
            if email:
                email_owner = conn.execute(
                    "SELECT id FROM users WHERE email = ?", (email,)
                ).fetchone()
                if email_owner is not None:
                    raise ValueError("email_taken")

            perm_list = list(permissions or [])
            user_id = insert_returning_id(
                conn,
                "INSERT INTO users(username, password_hash, role, display_name, locale, "
                "email, sso_provider_id, sso_subject, disabled, created_at, permissions, "
                "role_name) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, 0, ?, ?, ?)",
                (
                    username,
                    password_hash,
                    account_role,
                    display_name,
                    locale,
                    email,
                    ts,
                    json.dumps(perm_list, ensure_ascii=False),
                    role_name if role_name is not None else invite.role_name,
                ),
            )
            if policies:
                _insert_named_policies(conn, user_id=user_id, policies=policies, ts=ts)
            updated = conn.execute(
                "UPDATE user_invites "
                "SET used_count = used_count + 1, used_at = ?, used_by_user_id = ? "
                "WHERE id = ? AND revoked_at IS NULL AND expires_at > ? "
                "AND (max_uses IS NULL OR used_count < max_uses)",
                (ts, user_id, invite.id, ts),
            )
            if getattr(updated, "rowcount", 1) == 0:
                raise ValueError("used")
            fresh = conn.execute("SELECT * FROM user_invites WHERE id = ?", (invite.id,)).fetchone()
            assert fresh is not None
            return user_id, InviteRow.from_row(fresh)


def _insert_named_policies(
    conn: Any,
    *,
    user_id: int,
    policies: list[tuple[str, str]],
    ts: int,
) -> None:
    for name, value in policies:
        conn.execute(
            """
            INSERT INTO user_policies(
              policy_id, user_id, name, enabled, value, created_at, updated_at
            )
            VALUES (?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(user_id, name) DO UPDATE SET
              enabled = 1,
              value = excluded.value,
              updated_at = excluded.updated_at
            """,
            (new_ulid(), user_id, name, value, ts, ts),
        )


def invite_status_payload(invite: InviteRow, *, now: int | None = None) -> dict[str, Any]:
    ts = now if now is not None else now_ts()
    return {
        "id": invite.id,
        "code": invite.code,
        "note": invite.note,
        "created_by": invite.created_by,
        "created_at": invite.created_at,
        "expires_at": invite.expires_at,
        "used_at": invite.used_at,
        "used_by_user_id": invite.used_by_user_id,
        "revoked_at": invite.revoked_at,
        "status": invite.status(now=ts),
        "role_name": invite.role_name,
        "role": invite.role,
        "max_uses": invite.max_uses,
        "used_count": invite.used_count,
    }

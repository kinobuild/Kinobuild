"""Prepaid token top-up codes — one row per voucher."""

from __future__ import annotations

from dataclasses import dataclass

from octop.infra.db.pool import DatabasePool
from octop.infra.db.repos._base import DbRow, now_ts


@dataclass(frozen=True)
class QuotaRedeemCodeRow:
    pk: int
    code: str
    tokens: int
    note: str
    created_by: int | None
    created_at: int
    redeemed_by: int | None
    redeemed_at: int | None
    revoked_at: int | None

    @property
    def status(self) -> str:
        if self.revoked_at is not None:
            return "revoked"
        if self.redeemed_at is not None:
            return "redeemed"
        return "unused"

    @classmethod
    def from_row(cls, row: DbRow) -> QuotaRedeemCodeRow:
        redeemed_by = row["redeemed_by"]
        return cls(
            pk=int(row["id"]),
            code=str(row["code"]),
            tokens=int(row["tokens"]),
            note=str(row["note"] or ""),
            created_by=None if row["created_by"] is None else int(row["created_by"]),
            created_at=int(row["created_at"]),
            redeemed_by=None if redeemed_by is None else int(redeemed_by),
            redeemed_at=None if row["redeemed_at"] is None else int(row["redeemed_at"]),
            revoked_at=None if row["revoked_at"] is None else int(row["revoked_at"]),
        )


class QuotaRedeemCodeRepo:
    """Storage for redeemable token vouchers."""

    def __init__(self, db: DatabasePool) -> None:
        self._db = db

    def create_many(
        self,
        *,
        codes: list[str],
        tokens: int,
        note: str,
        created_by: int | None,
    ) -> list[QuotaRedeemCodeRow]:
        ts = now_ts()
        with self._db.connect() as conn:
            for code in codes:
                conn.execute(
                    "INSERT INTO quota_redeem_codes (code, tokens, note, created_by, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (code, int(tokens), note, created_by, ts),
                )
        return self.get_many(codes)

    def get(self, code: str) -> QuotaRedeemCodeRow | None:
        with self._db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM quota_redeem_codes WHERE code = ?", (code,)
            ).fetchone()
        return None if row is None else QuotaRedeemCodeRow.from_row(row)

    def get_many(self, codes: list[str]) -> list[QuotaRedeemCodeRow]:
        if not codes:
            return []
        placeholders = ",".join("?" for _ in codes)
        with self._db.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM quota_redeem_codes WHERE code IN ({placeholders})",  # noqa: S608
                tuple(codes),
            ).fetchall()
        by_code = {str(row["code"]): QuotaRedeemCodeRow.from_row(row) for row in rows}
        return [by_code[c] for c in codes if c in by_code]

    def list_recent(
        self, *, limit: int = 100, status: str | None = None
    ) -> list[QuotaRedeemCodeRow]:
        where = ""
        if status == "unused":
            where = " WHERE redeemed_at IS NULL AND revoked_at IS NULL"
        elif status == "redeemed":
            where = " WHERE redeemed_at IS NOT NULL"
        elif status == "revoked":
            where = " WHERE revoked_at IS NOT NULL"
        with self._db.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM quota_redeem_codes{where} ORDER BY id DESC LIMIT ?",  # noqa: S608
                (int(limit),),
            ).fetchall()
        return [QuotaRedeemCodeRow.from_row(row) for row in rows]

    def claim(self, code: str, *, user_id: int) -> bool:
        """Mark *code* redeemed by *user_id*; False when it was already spent."""
        with self._db.connect() as conn:
            cursor = conn.execute(
                "UPDATE quota_redeem_codes SET redeemed_by = ?, redeemed_at = ?"
                " WHERE code = ? AND redeemed_at IS NULL AND revoked_at IS NULL",
                (user_id, now_ts(), code),
            )
            return int(cursor.rowcount or 0) == 1

    def revoke(self, code: str) -> bool:
        with self._db.connect() as conn:
            cursor = conn.execute(
                "UPDATE quota_redeem_codes SET revoked_at = ?"
                " WHERE code = ? AND redeemed_at IS NULL AND revoked_at IS NULL",
                (now_ts(), code),
            )
            return int(cursor.rowcount or 0) == 1

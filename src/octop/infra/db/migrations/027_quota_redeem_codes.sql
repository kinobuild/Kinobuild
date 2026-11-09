-- Schema v27: prepaid token top-up codes.
--
-- A row is a single-use voucher worth ``tokens``; redeeming it raises the
-- account's lifetime token quota by that amount. ``redeemed_by`` / ``redeemed_at``
-- record the redemption, ``revoked_at`` retires an unsold code. Codes are stored
-- upper-cased and compared upper-cased so case never causes a support ticket.

CREATE TABLE IF NOT EXISTS quota_redeem_codes (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  code         TEXT NOT NULL UNIQUE,
  tokens       INTEGER NOT NULL,
  note         TEXT NOT NULL DEFAULT '',
  created_by   INTEGER,
  created_at   INTEGER NOT NULL,
  redeemed_by  INTEGER,
  redeemed_at  INTEGER,
  revoked_at   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_quota_redeem_codes_redeemed_by
  ON quota_redeem_codes(redeemed_by);
CREATE INDEX IF NOT EXISTS idx_quota_redeem_codes_created_at
  ON quota_redeem_codes(created_at);

UPDATE _schema_version SET version = 27;

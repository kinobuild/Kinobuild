-- Schema v31: invitations keep a cumulative use counter plus one redemption row
-- per account, replacing the legacy single-use markers.
--
-- Upstream cut this as its 026; KinoGuild had already shipped 026~030. Our own
-- 021 already added ``max_uses`` / ``used_count``, so this version adds
-- ``enabled`` and ``use_count`` (backfilled from ``used_count``), records existing
-- redemptions, and then drops the legacy ``used_at`` / ``used_by_user_id`` /
-- ``revoked_at`` columns. SQLite applies it through the idempotent
-- ``_ensure_invite_redemptions_schema`` helper.

ALTER TABLE user_invites ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1;
ALTER TABLE user_invites ADD COLUMN use_count INTEGER NOT NULL DEFAULT 0;

UPDATE user_invites SET enabled = 0 WHERE used_at IS NOT NULL OR revoked_at IS NOT NULL;
UPDATE user_invites SET use_count = COALESCE(used_count, 0);

CREATE TABLE IF NOT EXISTS user_invite_redemptions (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  invite_id    INTEGER NOT NULL REFERENCES user_invites(id) ON DELETE CASCADE,
  user_id      INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  redeemed_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_invite_redemptions_invite
  ON user_invite_redemptions(invite_id, redeemed_at, id);

INSERT INTO user_invite_redemptions(invite_id, user_id, redeemed_at)
SELECT id, used_by_user_id, used_at FROM user_invites
WHERE used_by_user_id IS NOT NULL AND used_at IS NOT NULL
ON CONFLICT(user_id) DO NOTHING;

ALTER TABLE user_invites DROP COLUMN used_at;
ALTER TABLE user_invites DROP COLUMN used_by_user_id;
ALTER TABLE user_invites DROP COLUMN revoked_at;

UPDATE _schema_version SET version = 31;

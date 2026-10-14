-- Schema v21: reusable invite codes (PostgreSQL variant, see the SQLite file).

ALTER TABLE user_invites ADD COLUMN IF NOT EXISTS max_uses INTEGER;
ALTER TABLE user_invites ADD COLUMN IF NOT EXISTS used_count INTEGER NOT NULL DEFAULT 0;

UPDATE user_invites SET max_uses = 1 WHERE max_uses IS NULL;
UPDATE user_invites SET used_count = 1 WHERE used_at IS NOT NULL AND used_count = 0;

UPDATE _schema_version SET version = 21;


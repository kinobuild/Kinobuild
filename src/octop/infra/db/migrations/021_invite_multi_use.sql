-- Schema v21: reusable invite codes.
--
-- ``max_uses`` NULL means unlimited; ``used_count`` counts successful
-- redemptions. Every invite that existed before this migration was
-- single-use, so the backfill pins them to ``max_uses = 1`` and keeps
-- ``used_count`` in sync with the legacy ``used_at`` marker.
--
-- SQLite applies this version through ``_ensure_invite_usage_schema`` (an
-- idempotent helper) rather than executing this file: clamped-watermark
-- repairs re-run the version over an already-current physical schema.

ALTER TABLE user_invites ADD COLUMN max_uses INTEGER;
ALTER TABLE user_invites ADD COLUMN used_count INTEGER NOT NULL DEFAULT 0;

UPDATE user_invites SET max_uses = 1;
UPDATE user_invites SET used_count = 1 WHERE used_at IS NOT NULL;

UPDATE _schema_version SET version = 21;


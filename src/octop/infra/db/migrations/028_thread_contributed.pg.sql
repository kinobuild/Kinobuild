-- Schema v28: mark conversations a user contributed to on a shared expert.
--
-- Upstream folded this column into its unreleased 025 (_user_mfa); KinoGuild had
-- already shipped 026 (MFA) and 027 (top-up codes), so the change is cut as its
-- own version. SQLite applies it through ``_ensure_thread_contributed_schema``
-- (idempotent) because a clamped-watermark repair can replay the version over an
-- already-current physical schema.

ALTER TABLE threads ADD COLUMN IF NOT EXISTS contributed INTEGER NOT NULL DEFAULT 0;

UPDATE _schema_version SET version = 28;

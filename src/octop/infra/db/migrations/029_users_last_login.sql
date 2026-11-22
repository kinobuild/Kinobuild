-- Schema v29: record when each account last signed in.
--
-- Upstream folded this into its unreleased 025 (_user_mfa); KinoGuild had already
-- shipped 026/027/028, so it is cut as its own version. Blank rows are backfilled
-- from login audit entries so existing accounts start with a real value.
--
-- SQLite applies this through ``_ensure_user_last_login_schema`` (idempotent)
-- because a clamped-watermark repair can replay the version over an already
-- current physical schema.

ALTER TABLE users ADD COLUMN last_login_at INTEGER;

UPDATE users
SET last_login_at = (
  SELECT MAX(ts) FROM audit_log
  WHERE actor = users.username
    AND action IN ('auth.login', 'auth.ldap_login', 'auth.oidc_login', 'auth.passkey_login')
)
WHERE last_login_at IS NULL
  AND EXISTS (
    SELECT 1 FROM audit_log
    WHERE actor = users.username
      AND action IN ('auth.login', 'auth.ldap_login', 'auth.oidc_login', 'auth.passkey_login')
  );

UPDATE _schema_version SET version = 29;

-- Schema v22 (upstream shipped this as 021; KinoGuild owns 021 = invite_multi_use, already applied in production): skill packages can disable ZIP download for non-owners.

ALTER TABLE skill_packages ADD COLUMN allow_download INTEGER NOT NULL DEFAULT 1;

UPDATE _schema_version SET version = 22;

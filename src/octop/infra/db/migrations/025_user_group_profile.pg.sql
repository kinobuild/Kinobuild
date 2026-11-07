-- KinoGuild 的 022 已被「技能包下载开关」占用（线上水位已到 22），上游此文件顺延为 25。
-- Schema v25: user groups can be disabled and can carry a preset avatar;
-- knowledge bases and bridge connections gain an optional uploaded/remote icon_url;
-- bridge connections gain shared (who can use the link).

ALTER TABLE user_group ADD COLUMN IF NOT EXISTS enabled INTEGER NOT NULL DEFAULT 1;
ALTER TABLE user_group ADD COLUMN IF NOT EXISTS avatar_icon TEXT;
ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS icon_url TEXT NOT NULL DEFAULT '';
ALTER TABLE bridge_connections ADD COLUMN IF NOT EXISTS icon_url TEXT NOT NULL DEFAULT '';
ALTER TABLE bridge_connections ADD COLUMN IF NOT EXISTS shared INTEGER NOT NULL DEFAULT 0;

UPDATE _schema_version SET version = 25;

-- KinoGuild 的 022 已被「技能包下载开关」占用（线上水位已到 22），上游此文件顺延为 23。
-- Schema v23: skill packages can be private or shared with other users.

ALTER TABLE skill_packages ADD COLUMN IF NOT EXISTS shared INTEGER NOT NULL DEFAULT 0;

UPDATE _schema_version SET version = 23;

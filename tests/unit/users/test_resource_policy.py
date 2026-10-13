"""tests/unit/users/test_resource_policy.py"""

from __future__ import annotations

from pathlib import Path

import pytest

from octop.infra.db.migrate import run_migrations
from octop.infra.db.pool import SqlitePool
from octop.infra.db.repos.agents import AgentRepo
from octop.infra.db.repos.usage import UsageRepo
from octop.infra.db.repos.user_policies import UserPolicyRepo
from octop.infra.db.repos.users import UserRepo
from octop.infra.errors import ErrorCode, OctopError
from octop.infra.users.resource_policy import (
    POLICY_MAX_AGENTS,
    POLICY_TOKEN_QUOTA,
    POLICY_WORKSPACE_ROOT_DIR,
    assert_agent_quota_available,
    assert_backend_within_user_root,
    assert_token_quota_available,
    normalize_workspace_root_dir,
    public_policy_fields,
)


@pytest.fixture
def db(tmp_path: Path) -> SqlitePool:
    pool = SqlitePool(tmp_path / "octop.db")
    run_migrations(pool)
    return pool


def test_normalize_workspace_root_dir_unlimited(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCTOP_IN_CONTAINER", "0")
    assert normalize_workspace_root_dir(None) is None
    assert normalize_workspace_root_dir("  ") is None


def test_normalize_workspace_root_dir_must_be_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OCTOP_IN_CONTAINER", "0")
    root = tmp_path / "jail"
    root.mkdir()
    assert normalize_workspace_root_dir(str(root)) == root.resolve().as_posix()
    file_path = tmp_path / "not-a-dir"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(OctopError) as exc:
        normalize_workspace_root_dir(str(file_path))
    assert exc.value.code is ErrorCode.WORKSPACE_ROOT_RESTRICTED


def test_normalize_workspace_root_dir_rejected_in_container(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from octop.infra.users.resource_policy import effective_workspace_root_dir

    root = tmp_path / "jail"
    root.mkdir()
    monkeypatch.setenv("OCTOP_IN_CONTAINER", "1")
    assert normalize_workspace_root_dir(None) is None
    with pytest.raises(OctopError) as exc:
        normalize_workspace_root_dir(str(root))
    assert exc.value.code is ErrorCode.WORKSPACE_ROOT_CONTAINER_UNSUPPORTED
    assert effective_workspace_root_dir(str(root)) is None


def test_assert_backend_within_user_root(tmp_path: Path) -> None:
    jail = tmp_path / "jail"
    nested = jail / "proj"
    outside = tmp_path / "other"
    jail.mkdir()
    nested.mkdir()
    outside.mkdir()
    allowed = jail.resolve().as_posix()
    assert_backend_within_user_root(
        {"type": "local_shell", "root_dir": nested.as_posix(), "virtual_mode": True},
        allowed,
    )
    with pytest.raises(ValueError, match="path outside allowed workspace root"):
        assert_backend_within_user_root(
            {"type": "local_shell", "root_dir": outside.as_posix(), "virtual_mode": True},
            allowed,
        )
    assert_backend_within_user_root(
        {"type": "docker"},
        allowed,
    )


def test_assert_token_quota_available(db: SqlitePool) -> None:
    users = UserRepo(db)
    policies = UserPolicyRepo(db)
    usage = UsageRepo(db)
    uid = users.create(username="alice", password_hash="h", role="user")
    AgentRepo(db).create(agent_id="a1", user_id=uid, name="a")
    assert_token_quota_available(policies, usage, uid)
    policies.set(uid, POLICY_TOKEN_QUOTA, "10")
    usage.record(
        agent_id="a1",
        user_id=uid,
        input_tokens=6,
        output_tokens=4,
        model="m",
        thread_id="t1",
    )
    with pytest.raises(OctopError) as exc:
        assert_token_quota_available(policies, usage, uid)
    assert exc.value.code is ErrorCode.TOKEN_QUOTA_EXCEEDED
    assert exc.value.details["used"] == 10
    assert exc.value.details["quota"] == 10
    policies.set(uid, POLICY_TOKEN_QUOTA, "11")
    assert_token_quota_available(policies, usage, uid)


def test_assert_agent_quota_available(db: SqlitePool) -> None:
    users = UserRepo(db)
    policies = UserPolicyRepo(db)
    agents = AgentRepo(db)
    uid = users.create(username="alice", password_hash="h", role="user")
    assert_agent_quota_available(policies, agents, uid)

    policies.set(uid, POLICY_MAX_AGENTS, "1")
    agents.create(agent_id="a1", user_id=uid, name="a", kind="expert")
    with pytest.raises(OctopError) as exc:
        assert_agent_quota_available(policies, agents, uid)
    assert exc.value.code is ErrorCode.AGENT_QUOTA_EXCEEDED
    assert exc.value.details == {"used": 1, "quota": 1}

    # Teams do not count toward the expert quota.
    agents.create(agent_id="t1", user_id=uid, name="team", kind="team")
    with pytest.raises(OctopError) as exc2:
        assert_agent_quota_available(policies, agents, uid)
    assert exc2.value.details["used"] == 1

    policies.set(uid, POLICY_MAX_AGENTS, "2")
    assert_agent_quota_available(policies, agents, uid)


def test_user_policy_repo_named_rows(db: SqlitePool, tmp_path: Path) -> None:
    users = UserRepo(db)
    policies = UserPolicyRepo(db)
    uid = users.create(username="alice", password_hash="h", role="user")
    jail = tmp_path / "jail"
    jail.mkdir()

    assert policies.list_for_user(uid) == []
    policies.merge(
        uid,
        {POLICY_WORKSPACE_ROOT_DIR: str(jail), POLICY_TOKEN_QUOTA: "42"},
    )
    kv = policies.enabled_values(uid)
    assert kv[POLICY_WORKSPACE_ROOT_DIR] == str(jail)
    assert kv[POLICY_TOKEN_QUOTA] == "42"
    assert public_policy_fields(policies.list_for_user(uid)) == {
        "workspace_root_dir": str(jail),
        "token_quota": 42,
        "image_quota": None,
        "max_agents": None,
    }
    root = policies.get(uid, POLICY_WORKSPACE_ROOT_DIR)
    assert root is not None
    assert root.policy_id
    assert root.enabled is True

    with db.connect() as conn:
        user_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        policy_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(user_policies)").fetchall()
        }
    assert "workspace_root_dir" not in user_columns
    assert "token_quota" not in user_columns
    assert policy_columns == {
        "id",
        "policy_id",
        "user_id",
        "name",
        "enabled",
        "value",
        "created_at",
        "updated_at",
    }

    policies.set(uid, "future_flag", "1")
    policies.merge(uid, {POLICY_WORKSPACE_ROOT_DIR: None, POLICY_TOKEN_QUOTA: None})
    assert policies.enabled_values(uid) == {"future_flag": "1"}
    disabled = {row.name: row.enabled for row in policies.list_for_user(uid)}
    assert disabled[POLICY_WORKSPACE_ROOT_DIR] is False
    assert disabled[POLICY_TOKEN_QUOTA] is False
    assert disabled["future_flag"] is True

    other = users.create(username="bob", password_hash="h", role="user")
    policies.merge(other, {POLICY_WORKSPACE_ROOT_DIR: str(jail), POLICY_TOKEN_QUOTA: "7"})
    mapped = policies.enabled_values_by_user_ids([uid, other, uid + 99])
    assert mapped[uid] == {"future_flag": "1"}
    assert mapped[other][POLICY_TOKEN_QUOTA] == "7"
    assert uid + 99 not in mapped


def test_migration_moves_legacy_user_columns_to_policy_table(tmp_path: Path) -> None:
    db = SqlitePool(tmp_path / "legacy.db")
    run_migrations(db)
    users = UserRepo(db)
    uid = users.create(username="alice", password_hash="h", role="user")
    with db.connect() as conn:
        conn.execute("ALTER TABLE users ADD COLUMN workspace_root_dir TEXT")
        conn.execute("ALTER TABLE users ADD COLUMN token_quota INTEGER")
        conn.execute(
            "UPDATE users SET workspace_root_dir = ?, token_quota = ? WHERE id = ?",
            (tmp_path.as_posix(), 99, uid),
        )

    run_migrations(db)

    kv = UserPolicyRepo(db).enabled_values(uid)
    assert kv[POLICY_WORKSPACE_ROOT_DIR] == tmp_path.as_posix()
    assert kv[POLICY_TOKEN_QUOTA] == "99"
    with db.connect() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
        tables = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert "workspace_root_dir" not in columns
    assert "token_quota" not in columns
    assert "user_policies" in tables
    assert "user_resource_policies" not in tables


def test_migration_moves_wide_resource_policy_table(tmp_path: Path) -> None:
    db = SqlitePool(tmp_path / "wide.db")
    run_migrations(db)
    users = UserRepo(db)
    uid = users.create(username="alice", password_hash="h", role="user")
    with db.connect() as conn:
        conn.execute("DROP TABLE user_policies")
        conn.execute(
            """
            CREATE TABLE user_resource_policies (
              user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
              workspace_root_dir TEXT,
              token_quota INTEGER
            )
            """
        )
        conn.execute(
            "INSERT INTO user_resource_policies(user_id, workspace_root_dir, token_quota) "
            "VALUES (?, ?, ?)",
            (uid, tmp_path.as_posix(), 12),
        )

    run_migrations(db)

    kv = UserPolicyRepo(db).enabled_values(uid)
    assert kv[POLICY_WORKSPACE_ROOT_DIR] == tmp_path.as_posix()
    assert kv[POLICY_TOKEN_QUOTA] == "12"
    with db.connect() as conn:
        tables = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(user_policies)")}
    assert "user_policies" in tables
    assert "user_resource_policies" not in tables
    assert "policy_id" in cols


def test_migration_rebuilds_legacy_kv_table(tmp_path: Path) -> None:
    db = SqlitePool(tmp_path / "kv.db")
    run_migrations(db)
    users = UserRepo(db)
    uid = users.create(username="alice", password_hash="h", role="user")
    with db.connect() as conn:
        conn.execute("DROP TABLE user_policies")
        conn.execute(
            """
            CREATE TABLE user_policies (
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              key TEXT NOT NULL,
              value TEXT NOT NULL,
              PRIMARY KEY (user_id, key)
            )
            """
        )
        conn.execute(
            "INSERT INTO user_policies(user_id, key, value) VALUES (?, ?, ?)",
            (uid, POLICY_TOKEN_QUOTA, "8"),
        )

    run_migrations(db)

    row = UserPolicyRepo(db).get(uid, POLICY_TOKEN_QUOTA)
    assert row is not None
    assert row.enabled is True
    assert row.value == "8"
    assert row.policy_id
    with db.connect() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(user_policies)")}
    assert "key" not in cols
    assert "policy_id" in cols


def test_every_known_policy_is_wired_through_the_stack() -> None:
    """A policy name alone is not a feature — every layer must know it.

    Regression guard: ``image_quota`` was added to this module and to the
    dashboard, but the role router kept its own whitelist that was never
    updated. Admins saw "没有权限" (no permission) when saving a role, which
    pointed at the wrong subsystem entirely.

    Adding a name to ``KNOWN_POLICIES`` without wiring it up now fails here.
    """
    import inspect

    from octop.infra.users.manager import UserManager
    from octop.infra.users.resource_policy import KNOWN_POLICIES, public_policy_fields

    assert KNOWN_POLICIES, "expected at least one policy"

    # 1) every name is exposed on the HTTP surface
    exposed = public_policy_fields(dict.fromkeys(sorted(KNOWN_POLICIES), "1"))
    missing_from_reader = sorted(set(KNOWN_POLICIES) - set(exposed))
    assert not missing_from_reader, f"{missing_from_reader} missing from public_policy_fields"

    # 2) every name can be written through the setter
    params = set(inspect.signature(UserManager.set_resource_policy).parameters)
    missing_from_setter = sorted(set(KNOWN_POLICIES) - params)
    assert not missing_from_setter, f"{missing_from_setter} missing from set_resource_policy"


def test_role_router_has_no_private_policy_whitelist() -> None:
    """The router must consume the shared name set, not its own copy.

    A duplicate list is what let the two definitions drift apart.
    """
    from octop.api.routers import user_roles
    from octop.infra.users.resource_policy import KNOWN_POLICIES

    assert not hasattr(user_roles, "_KNOWN_POLICIES"), (
        "role router must use KNOWN_POLICIES from resource_policy"
    )
    assert user_roles.KNOWN_POLICIES is KNOWN_POLICIES


def test_user_http_bodies_accept_every_known_policy() -> None:
    """A policy the request body cannot carry is a policy admins cannot set.

    Regression guard: ``image_quota`` reached the store, the manager, the role
    router and the dashboard, but ``UserPatchBody`` never declared the field.
    Pydantic dropped it from the PATCH payload, so 管理 → 用户 → 「生图额度」
    saved without effect and the account stayed unlimited.
    """
    from octop.api.routers.users import UserBatchBody, UserCreateBody, UserPatchBody
    from octop.infra.users.resource_policy import KNOWN_POLICIES, POLICY_WORKSPACE_ROOT_DIR

    # The batch endpoint has no "move the workspace root" action, so it carries
    # every policy except that one.
    for model, expected in (
        (UserCreateBody, KNOWN_POLICIES),
        (UserPatchBody, KNOWN_POLICIES),
        (UserBatchBody, KNOWN_POLICIES - {POLICY_WORKSPACE_ROOT_DIR}),
    ):
        missing = sorted(expected - set(model.model_fields))
        assert not missing, f"{model.__name__} rejects {missing}"

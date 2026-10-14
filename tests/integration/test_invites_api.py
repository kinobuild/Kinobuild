"""Integration tests for one-time user invites."""

from __future__ import annotations

import json

from octop.infra.agents.experts.default_agent import default_home_local_backend
from octop.infra.utils.host_dirs import host_fs_tree_root


async def test_invite_create_list_redeem_and_one_time(env) -> None:
    c, srv, auth = env

    r = await c.post(
        "/api/users/invites",
        headers=auth,
        json={"note": "for bob", "expires_in_days": 7},
    )
    assert r.status_code == 201, r.text
    invite = r.json()
    assert invite["status"] == "pending"
    assert invite["note"] == "for bob"
    assert invite["code"]
    assert invite["invite_path"].startswith("/invite?code=")
    assert invite["invite_url"].endswith(invite["invite_path"])
    code = invite["code"]

    listed = await c.get("/api/users/invites", headers=auth)
    assert listed.status_code == 200
    assert any(row["code"] == code for row in listed.json())

    # Public validate — no auth
    v = await c.post("/api/auth/invite/validate", json={"code": code})
    assert v.status_code == 200
    assert v.json()["ok"] is True

    redeem = await c.post(
        "/api/auth/invite/redeem",
        json={
            "code": code,
            "username": "bob_invitee",
            "password": "InvitePass12",
            "display_name": "Bob",
        },
    )
    assert redeem.status_code == 200, redeem.text
    body = redeem.json()
    assert body["access_token"]
    assert body["user"]["username"] == "bob_invitee"
    assert body["user"]["role"] == "user"
    assert body["user"]["permissions"] == []

    me = await c.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "bob_invitee"

    # Same default expert as setup wizard (general-assistant), not pinned to ``main``.
    agents = await c.get(
        "/api/agents",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert agents.status_code == 200, agents.text
    bob_agents = agents.json()
    assert len(bob_agents) == 1
    assert bob_agents[0]["template_name"] == "general-assistant"
    assert bob_agents[0]["agent_id"] != "main"
    assert srv.app_runtime is not None
    bob_row = srv.app_runtime.agent_registry.get_row(bob_agents[0]["agent_id"])
    assert bob_row is not None
    bob_cfg = json.loads(bob_row.config_json or "{}")
    assert bob_cfg["backend"] == default_home_local_backend()
    assert bob_cfg["backend"]["root_dir"] == host_fs_tree_root()
    assert bob_cfg["workspace_dir"] == str(
        srv.paths.agent_workspace(bob_agents[0]["agent_id"]).resolve()
    )

    again = await c.post(
        "/api/auth/invite/redeem",
        json={
            "code": code,
            "username": "other_user",
            "password": "InvitePass12",
        },
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "INVITE_USED"

    listed2 = await c.get("/api/users/invites", headers=auth)
    row = next(x for x in listed2.json() if x["code"] == code)
    assert row["status"] == "used"


async def test_invite_revoke(env) -> None:
    c, _srv, auth = env
    created = await c.post("/api/users/invites", headers=auth, json={})
    assert created.status_code == 201
    invite_id = created.json()["id"]
    code = created.json()["code"]

    revoked = await c.post(f"/api/users/invites/{invite_id}/revoke", headers=auth)
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    v = await c.post("/api/auth/invite/validate", json={"code": code})
    assert v.status_code == 410
    assert v.json()["error"]["code"] == "INVITE_REVOKED"


async def test_invite_admin_requires_users_permission(env) -> None:
    c, _srv, auth = env
    r = await c.post(
        "/api/users",
        headers=auth,
        json={"username": "normie", "password": "TestPass12", "role": "user"},
    )
    assert r.status_code == 201
    tok = (
        await c.post(
            "/api/auth/login",
            json={"username": "normie", "password": "TestPass12"},
        )
    ).json()["access_token"]
    denied = await c.get(
        "/api/users/invites",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert denied.status_code == 403


async def test_invite_multi_use_code_exhausts(env) -> None:
    c, _srv, auth = env

    created = await c.post(
        "/api/users/invites",
        headers=auth,
        json={"note": "team link", "expires_in_days": 7, "max_uses": 2},
    )
    assert created.status_code == 201, created.text
    invite = created.json()
    assert invite["max_uses"] == 2
    assert invite["used_count"] == 0
    assert invite["status"] == "pending"
    code = invite["code"]

    for index, username in enumerate(("team_member_a", "team_member_b"), start=1):
        redeem = await c.post(
            "/api/auth/invite/redeem",
            json={"code": code, "username": username, "password": "InvitePass12"},
        )
        assert redeem.status_code == 200, redeem.text
        listed = await c.get("/api/users/invites", headers=auth)
        row = next(r for r in listed.json() if r["code"] == code)
        assert row["used_count"] == index
        assert row["status"] == ("pending" if index < 2 else "used")

    # The same code is reusable while slots remain, and rejected once spent.
    third = await c.post(
        "/api/auth/invite/redeem",
        json={"code": code, "username": "team_member_c", "password": "InvitePass12"},
    )
    assert third.status_code == 409
    assert third.json()["error"]["code"] == "INVITE_USED"

    validate = await c.post("/api/auth/invite/validate", json={"code": code})
    assert validate.status_code == 409
    assert validate.json()["error"]["code"] == "INVITE_USED"


async def test_invite_unlimited_code(env) -> None:
    c, _srv, auth = env

    created = await c.post(
        "/api/users/invites",
        headers=auth,
        json={"expires_in_days": 7, "max_uses": None},
    )
    assert created.status_code == 201, created.text
    assert created.json()["max_uses"] is None
    code = created.json()["code"]

    for username in ("open_member_a", "open_member_b", "open_member_c"):
        redeem = await c.post(
            "/api/auth/invite/redeem",
            json={"code": code, "username": username, "password": "InvitePass12"},
        )
        assert redeem.status_code == 200, redeem.text

    listed = await c.get("/api/users/invites", headers=auth)
    row = next(r for r in listed.json() if r["code"] == code)
    assert row["max_uses"] is None
    assert row["used_count"] == 3
    assert row["status"] == "pending"


async def test_invite_max_uses_rejects_out_of_range(env) -> None:
    c, _srv, auth = env
    for value in (0, -3, 1001):
        r = await c.post("/api/users/invites", headers=auth, json={"max_uses": value})
        assert r.status_code == 422, (value, r.text)

"""Sanity checks for the bundled general-assistant template."""

from __future__ import annotations

import json

from octop.infra.agents.experts.catalog import default_library_root

_DIR = default_library_root() / "general-assistant"


def test_all_required_files_present() -> None:
    for name in ("SOUL.md", "manifest.json"):
        assert (_DIR / name).is_file(), f"missing {name}"


def test_upstream_product_brochure_skill_is_not_shipped() -> None:
    """``octop-assistant`` must not be seeded into the default expert.

    ``general-assistant`` is ``DEFAULT_EXPERT_ID`` — every new user gets it as
    their first agent. Upstream ships that expert with a single 623-line skill
    whose first ~80 lines are the product README verbatim, so the dashboard's
    personalisation tab rendered an upstream product brochure to end users.

    Re-adding it is not a silent change: this assertion fails, and the reason is
    here. If an upstream merge brings the directory back, delete it again rather
    than deleting this test.
    """
    assert not (_DIR / "skills" / "octop-assistant").exists(), (
        "octop-assistant is upstream product copy and must not ship in the "
        "default expert — see this test's docstring"
    )


def test_meta_yaml_has_id_and_display_name() -> None:
    meta = json.loads((_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert meta["id"] == "general-assistant"
    label = meta.get("label")
    assert isinstance(label, dict) and isinstance(label.get("en"), str) and label["en"]


def test_skills_json_is_a_list() -> None:
    meta = json.loads((_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(meta.get("prompt_files", []), list)

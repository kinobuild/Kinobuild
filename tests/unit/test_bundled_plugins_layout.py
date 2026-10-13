"""Bundled plugin tree must be complete enough for marketplace install and UI."""

from __future__ import annotations

import json
from pathlib import Path

from octop.infra.agents.plugins.bundled import default_bundled_plugins_root
from octop.infra.agents.plugins.manager import PluginManager
from octop.infra.agents.plugins.seed import seed_bundled_plugins


def _catalog_ids() -> set[str]:
    root = default_bundled_plugins_root()
    found: set[str] = set()
    for child in root.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "plugin.yaml").is_file():
            found.add(child.name)
    return found


def test_bundled_plugin_dirs_have_manifest_and_entry() -> None:
    root = default_bundled_plugins_root()
    found = _catalog_ids()
    assert found, "expected at least one catalog plugin"
    for name in found:
        child = root / name
        assert (child / "plugin.yaml").is_file(), child
        assert (child / "main.py").is_file(), child


def test_bundled_plugin_ui_declarations_are_complete() -> None:
    """A declared ``ui:`` block must be backed by real files.

    Not every bundled plugin ships a UI: a ``kind: skill`` plugin only contributes
    SKILL.md files and has no tool result to renderize, so it declares no ``ui:``.
    What must hold is that whenever a plugin *does* declare one, both the entry
    and the manifest exist.
    """
    root = default_bundled_plugins_root()
    found = _catalog_ids()
    assert found, "expected at least one catalog plugin"

    declaring = 0
    for name in found:
        child = root / name
        yaml_text = (child / "plugin.yaml").read_text(encoding="utf-8")
        if "ui:" not in yaml_text:
            continue
        declaring += 1
        assert (child / "ui" / "index.js").is_file(), child
        assert (child / "ui" / "manifest.json").is_file(), child
    assert declaring, "expected at least one catalog plugin to declare a ui block"


def test_seed_does_not_auto_install_real_catalog(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    config_path = tmp_path / "config.json"
    copied = seed_bundled_plugins(
        bundled_root=default_bundled_plugins_root(),
        plugins_dir=plugins_dir,
        config_path=config_path,
    )
    assert copied == []
    assert list(plugins_dir.iterdir()) == [] if plugins_dir.exists() else True


def test_market_install_copies_from_catalog(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    config_path = tmp_path / "config.json"
    mgr = PluginManager(plugins_dir=plugins_dir, config_path=config_path)
    catalog = mgr.list_market()
    assert catalog
    sample = next(item for item in catalog if not item.get("error"))
    plugin_id = str(sample["id"])
    loaded = mgr.install_from_market(plugin_id)
    assert loaded.manifest.id == plugin_id
    assert (plugins_dir / plugin_id / "plugin.yaml").is_file()
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    assert raw["plugins"][plugin_id]["enabled"] is True
    market = mgr.list_market()
    row = next(item for item in market if item.get("id") == plugin_id)
    assert row["installed"] is True
    assert row["update_available"] is False


def test_offline_bundled_plugins_load() -> None:
    from octop_harness.plugins import PluginRegistry, load_plugin_dir

    PluginRegistry.reset()
    root = default_bundled_plugins_root()
    try:
        for name in ("fortune", "pomodoro", "mini-games", "qrcode", "tetris"):
            loaded = load_plugin_dir(root / name, install_deps=False)
            assert loaded.manifest.id == name
            assert loaded.tools
    finally:
        PluginRegistry.reset()

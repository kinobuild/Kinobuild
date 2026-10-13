"""``uv.lock`` must satisfy the runtime pins declared in ``pyproject.toml``.

An upstream merge silently kept *our* (older) lockfile once: ``pyproject.toml``
came across from upstream asking for ``octop-harness>=1.0.2`` while ``uv.lock``
still pinned ``1.0.1``. The Docker build runs ``uv sync --frozen``, and
``--frozen`` trusts the lock completely — so the image would have shipped the
old runtime against the new code. Nothing in the suite noticed; it only turned
up by reading the merge diff by hand.

These assertions make that failure loud at test time instead of at first boot.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _locked_versions() -> dict[str, list[str]]:
    data = tomllib.loads((_REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    versions: dict[str, list[str]] = {}
    for package in data["package"]:
        versions.setdefault(str(package["name"]), []).append(str(package["version"]))
    return versions


def _project_dependencies() -> list[str]:
    data = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return [str(item) for item in data["project"]["dependencies"]]


def test_lockfile_satisfies_pyproject_runtime_pins() -> None:
    locked = _locked_versions()
    problems: list[str] = []
    checked = 0
    for raw in _project_dependencies():
        requirement = Requirement(raw)
        if not requirement.name.startswith("octop-"):
            continue
        checked += 1
        versions = locked.get(requirement.name)
        if not versions:
            problems.append(f"{requirement.name} 在 uv.lock 里找不到")
            continue
        for version in versions:
            if Version(version) not in requirement.specifier:
                problems.append(
                    f"{requirement.name}: 锁的是 {version}，不满足 pyproject 的 {requirement.specifier}"
                )

    assert not problems, (
        "uv.lock 与 pyproject.toml 对不上 —— 多半是合并上游时把锁文件解成了我们自己的旧版。\n"
        "docker/Dockerfile 用的是 `uv sync --frozen`，它完全信任锁文件，"
        "于是镜像会装旧运行时、跑新代码（启动即错）。\n"
        + "\n".join(problems)
        + "\n\n修法：取上游的锁文件 `git checkout <上游 tip> -- uv.lock`。"
    )
    assert checked >= 2, f"只检查到 {checked} 个 octop-* 依赖，这条测试可能没生效"


def test_lockfile_scan_reads_the_real_files() -> None:
    """Guard the guard: a wrong repo root would make the assertions vacuous."""
    assert (_REPO_ROOT / "pyproject.toml").is_file()
    assert (_REPO_ROOT / "uv.lock").is_file()
    assert "octop-harness" in _locked_versions()

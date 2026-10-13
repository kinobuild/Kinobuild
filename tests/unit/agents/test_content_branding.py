"""Shipped product copy must not name the upstream brand.

The dashboard renders expert files verbatim — 「灵魂设定」 shows ``SOUL.md``,
the skill cards show ``SKILL.md``, the expert library shows ``manifest.json``
prose — and the model reads the same text as prompt. A file that still calls
the product ``Octop`` therefore ships the upstream brand to users, which is
exactly what happened once: the last rename pass covered i18n strings and code
but not the content templates, so the personalisation page was full of Octop.
It happened again from the other direction: merging upstream re-introduced
``Octop`` into the dashboard locale catalog and the connector cards, neither of
which was scanned at the time.

All four surfaces are covered here — backend i18n, content templates, dashboard
locales and connector descriptions — so the next rename or upstream merge fails
loudly instead of silently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


def _content_roots() -> tuple[Path, ...]:
    import octop
    from octop.infra.agents import plugins
    from octop.infra.agents.experts import catalog as expert_catalog

    package_dir = Path(octop.__file__).resolve().parent
    experts_dir = Path(expert_catalog.__file__).resolve().parent
    plugins_dir = Path(plugins.__file__).resolve().parent
    roots: list[Path] = [
        experts_dir / "library",
        experts_dir / "manifest_generator_skill.md",
        plugins_dir / "bundled",
        package_dir / "i18n" / "en.json",
        package_dir / "i18n" / "zh.json",
        # Connector cards render these descriptions verbatim in the dashboard.
        package_dir / "infra" / "connectors" / "catalog.json",
    ]
    # Dashboard i18n is front-end source; a slim runtime image may not carry it.
    dashboard_locales = package_dir.parent.parent / "dashboard" / "src" / "locales"
    if dashboard_locales.is_dir():
        roots.extend(sorted(dashboard_locales.glob("*.json")))
    return tuple(roots)


#: Text file types that carry prose. Anything else (icons, fonts) cannot.
_TEXT_SUFFIXES = frozenset({".md", ".json", ".py", ".js", ".ts", ".txt", ".yaml", ".yml"})

#: ``Octop``/``OCTOP`` as a standalone word. Deliberately case-sensitive: the
#: lowercase form is how the package, the ``octop`` command, ``~/.octop/`` and
#: ``octop_ui`` appear in code, and flagging every one of those would drown the
#: signal. A lowercase product mention in prose would slip through — acceptable,
#: because Chinese prose about the product capitalises it.
_BRAND_RE = re.compile(r"\bOctop\b|\bOCTOP\b")

#: Phrases that may keep the upstream name, each with the reason it must stay.
#: Matched against the line before the brand check, so allowlisting one phrase
#: does not excuse a *different* mention on the same line.
_ALLOWED = (
    # Layout names: the framework a KinoGuild install actually runs on. Calling
    # them KinoGuild would make the architecture description wrong.
    (r"Octop Harness", "runtime package name"),
    (r"Octop Gateway", "runtime package name"),
    # Upstream project home, kept for bug reports and the MIT attribution.
    (r"TencentCloud/Octop", "upstream repository link"),
    (r"本项目基于 Octop 二次开发", "MIT attribution"),
    # Signature sent to third-party APIs; renaming it buys nothing and risks
    # breaking whatever already recognises it.
    (r"""_UA\s*=\s*["']Octop-[^"']*["']""", "third-party User-Agent string"),
    # Same reason, written inline as a request header rather than a module-level
    # constant (arxiv-search builds its headers in a dict).
    (r""""User-Agent"\s*:\s*["']Octop-[^"']*["']""", "third-party User-Agent string"),
)


def _without_allowed_mentions(line: str) -> str:
    scrubbed = line
    for pattern, _reason in _ALLOWED:
        scrubbed = re.sub(pattern, "", scrubbed)
    return scrubbed


def _content_files() -> list[Path]:
    files: list[Path] = []
    for root in _content_roots():
        if root.is_file():
            files.append(root)
            continue
        files.extend(
            path
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.suffix.lower() in _TEXT_SUFFIXES
        )
    return files


def test_shipped_copy_never_names_the_upstream_brand() -> None:
    offenders: list[str] = []
    for path in _content_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _BRAND_RE.search(_without_allowed_mentions(line)):
                offenders.append(f"{path}:{lineno}: {line.strip()}")

    assert not offenders, (
        "用户可见的文案里出现了上游品牌名 Octop，个性化页面、技能卡片和界面文案"
        "都会原样渲染它：\n"
        + "\n".join(offenders)
        + "\n\n改成 KinoGuild。若该处是真实标识符、协议头或 MIT 署名，"
        "把它加进 _ALLOWED 并写明原因。"
    )


def test_brand_scan_reads_the_real_content_tree() -> None:
    """Guard the guard: a wrong path would make the check vacuously pass."""
    files = _content_files()
    names = {path.name for path in files}
    assert len(files) > 50, f"only {len(files)} files scanned"
    assert "SOUL.md" in names
    assert "SKILL.md" in names
    assert "manifest.json" in names
    assert "catalog.json" in names
    assert {"en.json", "zh.json"} <= names


@pytest.mark.parametrize(
    "line",
    [
        "底层是 Python 3.12+、FastAPI，Agent 运行时为 Octop Harness，IM 桥接为 Octop Gateway。",
        "| **上游** | https://github.com/TencentCloud/Octop | 本项目基于 Octop 二次开发，遵循 MIT |",
        '_UA = "Octop-github-trending/0.1.0"',
    ],
)
def test_allowlisted_upstream_names_stay_tolerated(line: str) -> None:
    assert not _BRAND_RE.search(_without_allowed_mentions(line))


def test_allowlist_does_not_excuse_a_second_mention_on_the_same_line() -> None:
    """The allowlist is phrase-level: an unrelated mention still fails."""
    line = "运行时是 Octop Harness，而 Octop 是本产品的新名字"
    assert _BRAND_RE.search(_without_allowed_mentions(line))

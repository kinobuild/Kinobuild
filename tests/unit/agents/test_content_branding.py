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
#: ``.html`` is here because a bundled skill ships a generated board
#: (``productivity/skills/dashboard.html``) that renders file names and button
#: labels straight to the user — prose absolutely lives in that extension, and
#: leaving it out hid a ``CLAUDE.md`` reference from the first version of this
#: scan.
_TEXT_SUFFIXES = frozenset({".md", ".json", ".py", ".js", ".ts", ".txt", ".yaml", ".yml", ".html"})

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


#: Templates merged from upstream were written *for* Claude's own tooling, and
#: two concrete forms of that ship into a KinoGuild install: a file the agent is
#: told to create inside the user's workspace (``CLAUDE.md`` — our platform's own
#: working-memory file is ``MEMORY.md``), and a path variable that no KinoGuild
#: runtime substitutes (``${CLAUDE_PLUGIN_ROOT}``), which silently breaks every
#: skill that uses it. Both are matched by exact token rather than as a bare
#: word: ``Claude Code`` legitimately appears as one of the tools the coding
#: coach compares, so a broad scan would teach agents to ignore the finding.
_CLAUDE_TOKEN_RE = re.compile(r"CLAUDE\.md|CLAUDE_PLUGIN_ROOT")


def _shipped_expert_files() -> list[Path]:
    """Content a KinoGuild user can reach — the library minus suppressed experts.

    Suppressed templates (``catalog._SUPPRESSED_EXPERT_IDS``) stay on disk so
    agents already created from them keep resolving, but they are not offered to
    new users, so their prose is not shipped copy. Reading the list from the
    catalog instead of hard-coding it here means ③ and this guard cannot drift
    apart: hiding an expert automatically stops scanning its text, and un-hiding
    it automatically puts it back under the check.
    """
    from octop.infra.agents.experts.catalog import _SUPPRESSED_EXPERT_IDS

    files: list[Path] = []
    for path in _content_files():
        parts = path.parts
        if "library" in parts:
            index = parts.index("library")
            if len(parts) > index + 1 and parts[index + 1] in _SUPPRESSED_EXPERT_IDS:
                continue
        files.append(path)
    return files


def test_shipped_copy_never_names_competitor_files_or_paths() -> None:
    offenders: list[str] = []
    for path in _shipped_expert_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _CLAUDE_TOKEN_RE.search(line):
                offenders.append(f"{path}:{lineno}: {line.strip()}")

    assert not offenders, (
        "交付内容里出现了 Claude 专属的文件名或路径变量——模型会照着在用户工作区"
        "创建以竞品命名的文件，或拼出一个永远解析不到的路径：\n"
        + "\n".join(offenders)
        + "\n\n工作记忆文件改用平台的 MEMORY.md；技能内引用改用工作区相对路径"
        "（例如 skills/dashboard.html）。若这个专家本就不该上架，把它加进 "
        "catalog._SUPPRESSED_EXPERT_IDS，本扫描会自动跳过它。"
    )


def test_competitor_scan_reaches_generated_html_boards() -> None:
    """Guard the guard: the generated ``.html`` board is where this hid first."""
    files = _shipped_expert_files()
    assert len(files) > 50, f"only {len(files)} files scanned"
    assert "dashboard.html" in {path.name for path in files}, (
        "生成的看板不在扫描范围内——CLAUDE.md 曾正好藏在它里面"
    )

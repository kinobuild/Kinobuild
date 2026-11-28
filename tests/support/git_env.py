"""Hermetic environment for tests that create throwaway git repositories.

A commit hook runs the suite with ``GIT_DIR`` / ``GIT_INDEX_FILE`` /
``GIT_AUTHOR_*`` exported for the *outer* checkout. Inheriting them makes
``git init`` / ``git commit`` inside ``tmp_path`` write to the outer repository
or record the hook's identity instead of the fixture's.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

#: Variables that re-scope or re-identify git for another repository. Credentials
#: and transport settings (``GIT_SSH_COMMAND``, ``SSH_AUTH_SOCK``, …) are kept.
_SCOPED = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_AUTHOR_DATE",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
        "GIT_COMMITTER_DATE",
    }
)


def git_env() -> dict[str, str]:
    """Current environment minus the variables that point at another repository."""
    return {key: value for key, value in os.environ.items() if key not in _SCOPED}


def run_git(cwd: Path, *args: str) -> None:
    """Run one git command in ``cwd`` with a hermetic environment."""
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, env=git_env())

"""Keep the container, CI, and documented Python versions aligned."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _docker_python_version() -> str:
    match = re.search(
        r"^FROM python:(\d+\.\d+)-slim", _read("Dockerfile"), re.MULTILINE
    )
    assert match, "Dockerfile must use a python:<version>-slim base image"
    return match.group(1)


def _ci_python_versions() -> set[str]:
    return set(
        re.findall(
            r'python-version:\s*"(\d+\.\d+)"',
            _read(".github/workflows/ci.yml"),
        )
    )


def _readme_python_versions() -> set[str]:
    return set(re.findall(r"Python[- ](\d+\.\d+)\+", _read("README.md")))


def test_dockerfile_matches_ci_python_version():
    version = _docker_python_version()
    assert _ci_python_versions() == {version}


def test_readme_matches_ci_python_version():
    version = _docker_python_version()
    assert _readme_python_versions() == {version}

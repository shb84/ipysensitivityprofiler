"""Test project metadata."""

from importlib.metadata import version

import ipysensitivityprofiler


def test_version_is_exported() -> None:
    """The package exposes a version string."""
    assert isinstance(ipysensitivityprofiler.__version__, str)
    assert ipysensitivityprofiler.__version__


def test_version_matches_distribution() -> None:
    """`__version__` is the single source of truth for the built distribution.

    `pyproject.toml` declares `dynamic = ["version"]` and reads it from
    `ipysensitivityprofiler.__version__`, and the release workflow gates on the
    git tag matching that same attribute. This test keeps the three in sync.
    """
    assert version("ipysensitivityprofiler") == ipysensitivityprofiler.__version__


def test_public_api() -> None:
    """The documented public API is importable from the top-level package."""
    for name in ipysensitivityprofiler.__all__:
        assert hasattr(ipysensitivityprofiler, name), name

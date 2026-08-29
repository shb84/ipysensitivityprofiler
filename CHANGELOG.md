<!--
feat: A new feature.

fix: A bug fix.

docs: Documentation changes.

style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).

refactor: A code change that neither fixes a bug nor adds a feature.

perf: A code change that improves performance.

test: Changes to the test framework.

build: Changes to the build process or tools.
-->

# Changelog

## v0.0.2 (Unreleased)

### Build

- Reworked the development and release setup to match the one used by
  [JENN](https://github.com/shb84/JENN). `pixi` configuration moved out of
  `pyproject.toml` into a standalone `pixi.toml` with a feature/environment matrix, and
  the single CI workflow was split into `ci.yml`, `docs.yml`, `notebooks.yml` and
  `release.yml`.

- The CI test matrix now runs on a real per-Python environment (`py310` … `py314`). The
  previous workflow declared a `python-version` matrix that was never used — every leg
  ran the same interpreter.

- Releases now publish through PyPI Trusted Publishing (OIDC) instead of stored API
  tokens, and are gated on the full CI matrix, a tag-vs-`__version__` check, a smoke
  install of the built wheel, and a smoke install from TestPyPI. The final PyPI publish
  requires manual approval, and GitHub Release notes are generated from this file.

- `__version__` in `src/ipysensitivityprofiler/__init__.py` is now the single source of
  truth for the version; `pyproject.toml` reads it dynamically.

- Minimum supported Python is now 3.10.

### Fix

- Coverage was measured against the `jenn` package instead of this one, so the reported
  coverage was always empty.

- Notebook tests silently skipped `notebooks/openmdao_example/`.

- `make_figure` used a mutable default argument for `tick_style`.

### Test

- `tests/test_meta.py` now checks that `__version__`, the installed distribution version
  and the public API all agree, instead of asserting `True`.

### Docs

- Documentation restructured into `index` + `sections/` (quickstart, API, appendix), and
  now builds strictly (`sphinx-build -W`).

## v0.0.1 (2024-11-18)

- First release of `ipysensitivityprofiler`

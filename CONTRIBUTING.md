# CONTRIBUTING

Contributions are welcome. Thank you for helping make the project better!

## Installation

This project uses [`pixi`](https://pixi.sh/latest/), which must be installed.

__Linux & macOS__
```
curl -fsSL https://pixi.sh/install.sh | bash
```

__Windows__
```
powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"
```

_That's it. You are now ready to go!_

## Running

To display a list of available tasks, type `pixi run`.

__Example usage__
```
pixi run test
```
OR
```
pixi run lab
```

The workspace defines several environments (see `pixi.toml`):

| Environment | Purpose |
|---|---|
| `dev` | everything — lint, test, docs, build, Jupyter Lab |
| `py310` … `py314` | one per supported Python, used by the CI test matrix |

Run a task in a specific environment with `pixi run -e py311 test-unit`.

## Making Changes

- [ ] Fork the repo
- [ ] Make code changes
- [ ] Update package dependencies in `pyproject.toml` as necessary
- [ ] Update project dependencies in `pixi.toml` as necessary
- [ ] Ensure QA passes locally: `pixi run all`
- [ ] Commit and push changes to GitHub (this automatically triggers CI)
- [ ] Create pull request when ready

`pixi run all` chains `setup`, `fix`, `lint`, `build`, `test` and `docs` — the same
steps CI runs. Note that the docs build is strict (`sphinx-build -W`), so a warning
is a failure.

## Binder

`environment.yml` is the environment [mybinder.org](https://mybinder.org) builds when
someone opens the notebooks from the README badge. It is maintained by hand and installs
the *released* package from PyPI — it is deliberately minimal, and is not the same thing
as the `pixi` development environment.

## Continuous Integration

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | every push and PR | lint, then unit tests on py310–py314 |
| `notebooks.yml` | push to `main` | runs the example notebooks (slow, so not on every push) |
| `docs.yml` | push to `main` and `v*` tags | builds and deploys docs to GitHub Pages |
| `release.yml` | `v*` tags | the full release pipeline (below) |

## Release

*Only project owners and administrators can make new releases.*

A new release is created by pushing a new tag to the remote (e.g. `v0.0.2`). This
triggers a __test-build-deploy__ workflow that publishes to `pypi.org`, `GitHub Pages`
and `GitHub Release`. Tag pattern must be `v*`.

Before anything is published, the release pipeline runs two gates on the tagged commit:

- the **full CI matrix** (lint + unit tests on py310–py314, reused from `ci.yml`), and
- a **tag/version check** — the tag (minus its `v`) must equal `__version__` in
  `src/ipysensitivityprofiler/__init__.py`, or the release fails fast.

It then publishes to TestPyPI and **smoke-installs the package from TestPyPI and imports it**
before the real PyPI publish. The PyPI publish sits behind the `pypi` GitHub Environment's
manual-approval gate. GitHub Release notes are filled automatically from the matching
`## v<version>` section of `CHANGELOG.md`.

### Prerequisites

Publishing uses
[trusted publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
(OIDC): GitHub proves the workflow's identity to PyPI directly, so no API tokens are
stored in CI. This needs a one-time setup across three separate services — see the
cheatsheet below.

### Trusted Publishing Cheatsheet

**The binding.** A "trusted publisher" is a record on PyPI that says which workflow is
allowed to publish. It is four values, and all four must match exactly:

| Field | Value for this repo |
|---|---|
| Owner | `shb84` |
| Repository | `ipysensitivityprofiler` |
| Workflow | `release.yml` — the *filename*, not the display name |
| Environment | `pypi` on PyPI · `testpypi` on TestPyPI |

**What "environment" means here.** A GitHub *deployment environment*: a named permission
gate in repository settings. It has nothing to do with a `pixi`, conda or `virtualenv`
environment despite the name — nothing is installed. It is owned by this repository, not
by PyPI; PyPI only reads the name out of the identity token and compares it. Note the
split: the name appears in `release.yml`, but its **protection rules live in GitHub
settings and are not in version control**, so reading the workflow file tells you nothing
about whether a gate is actually active.

**Trusted publishing is per project, not per account.** Configuring it for one package
does nothing for another — every PyPI project carries its own publisher list.

Do step 1 first; see the trap below.

**1. GitHub environments** — Settings → Environments

  - `testpypi` — create it, no rules.
  - `pypi` — create it, tick **Required reviewers**, add yourself, then
    **Save protection rules**. The reviewer list does not persist without that save.

**2. PyPI** — Manage → Publishing on the project → add a GitHub publisher, using the four
values above with environment `pypi`. If the project does not exist on PyPI yet, use the
*pending publisher* flow under Account → Publishing instead; it converts to a normal
publisher on first upload.

**3. TestPyPI** — the same again, with environment `testpypi`. Separate site, separate
login. Configuring only PyPI leaves the pipeline failing at its first publish job.

**4. Verify with a real tag.** The jobs confirm the three pieces in order:

  1. `publish-testpypi` succeeds → the TestPyPI publisher matches.
  2. `publish-pypi` **pauses for approval** → the `pypi` protection rule is live.
  3. approve, and the PyPI publish succeeds → the PyPI publisher matches.

  Only once all three hold, delete any leftover `PYPI_TOKEN` / `TESTPYPI_TOKEN` from
  Settings → Secrets — they are the fallback until then. The local `.pypirc` token
  described at the end of this file is a different mechanism and stays.

> **Trap: a missing environment fails open.** Per GitHub's documentation, running a
> workflow that references an environment which does not exist *creates* it — with no
> protection rules. So skipping step 1 does not raise an error: it publishes straight to
> PyPI with no approval prompt and no sign the gate was bypassed. Create them
> deliberately rather than letting the first release create them for you.

### Mock Release

It's a good idea to do a mock release using `testpypi` from a local install:

```bash
pixi run testpypi
```

_Check that the package appears on `testpypi` and try manually installing it in a fresh
virtual environment to ensure it runs as expected, as an extra layer of precaution. If
not, please help update the CI procedure to catch the newly found issues._

### Procedure

`__version__` in `src/ipysensitivityprofiler/__init__.py` is the single source of truth —
`pyproject.toml` reads it dynamically, and the release pipeline gates on it. Assuming
`main` is locally up-to-date, update it:

```bash
__version__ = "0.0.2"
```

Add a matching `## v0.0.2` section to `CHANGELOG.md` (its contents become the GitHub
Release notes), then push the version change to the remote:

```bash
git add -u
git commit -m "changed version to v0.0.2"
git push
```

Tag the commit for release and push to trigger the release pipeline:

```bash
git tag v0.0.2
git push origin v0.0.2
```

Once the pipeline reaches the `publish-pypi` job it will wait for manual approval. After
it succeeds, check that there is a new release on `pypi.org`, `GitHub Pages` and
`GitHub Release`.

_To delete the tag if needed (e.g. a step failed in CI)_:

```bash
git tag -d v0.0.2
git push origin --delete v0.0.2
```

### TestPyPI API token (local mock releases only)

Unrelated to trusted publishing above: this token is for `pixi run testpypi` from
your own machine, which uploads directly rather than through GitHub Actions.

- [ ] In account settings on [testpypi.org](https://test.pypi.org/), go to the API tokens
      section and select "Add API token"
- [ ] Then use that token to configure your local
      [`.pypirc`](https://packaging.python.org/en/latest/specifications/pypirc/) file:

```bash
[distutils]
index-servers =
    testpypi

[testpypi]
repository: https://test.pypi.org/legacy/
username: __token__
password: pypi-...
```

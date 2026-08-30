# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Everything runs through [`pixi`](https://pixi.sh). **Most task names exist in several
environments, so a bare `pixi run <task>` fails as ambiguous** — pass `-e dev` for
ordinary work (`py310` … `py314` exist for the CI matrix):

```bash
pixi run -e dev all         # setup, fix, lint, build, test, docs — what CI runs
pixi run -e dev lint        # ruff format --check, ruff check, mypy, docformatter
pixi run -e dev test-unit   # pytest with coverage
pixi run -e dev test-nb     # executes the example notebooks via nbmake
pixi run -e dev docs        # sphinx, strict (-W): a warning is a failure
pixi run -e dev lab         # Jupyter Lab, for looking at the widget
```

A single test — the pixi tasks add coverage and report plumbing, so call pytest
directly. Pixi caches task results by input hash and will report a cache hit when
nothing it tracks changed; the direct call also sidesteps that:

```bash
.pixi/envs/dev/bin/python -m pytest tests/test_profiler.py::test_dot_matches_x0 -q
```

`ruff` runs with `select = ["ALL"]`. `docformatter` runs `--in-place`, so it will
reflow docstrings you just wrote — re-read a file after linting before editing it again.

## Architecture

Four modules form one reactive pipeline. The dataflow is the thing worth understanding;
it is not visible from any single file.

```
profiler()          _model.py    builds everything, wraps user models in `evaluate`
  └─ View           _view.py     owns bounds, x0, the figure grid, and redraws
       ├─ Data      _data.py     owns x (the grid) and y (model outputs)
       └─ Controller _controller.py  sliders that write back into View
                     _utils.py   grid construction + bqplot figure assembly
```

**Traitlets drives everything.** `View.x0`/`xmin`/`xmax`/`resolution` are observed by
`_update_data`, which rebuilds `Data.x`; a dlink on `Data` recomputes `Data.y`; `View`
observes `Data.y` and redraws. `Data.y` is deliberately the *single* redraw trigger —
every path that invalidates the plot flows through it, which is what keeps redraws from
depending on observer registration order. Do not add a redraw observer on `x0` or the
bounds; route it through `y`.

**The grid contract.** `create_grid` returns `n_x * resolution + 1` rows. The first
`n_x * resolution` sweep one input at a time; **the final row is `x0` itself**, so the
red dot's value comes back from the same model call as the curves. `grid_size(n_x,
resolution)` is the one place that arithmetic lives. Rows for input `j` are
`batch_slice(j, resolution)` — a slice, not an index list, so lookups stay views.

**The model-call budget is a tested invariant.** One call per model per interaction.
`tests/test_profiler.py` asserts the exact call and row counts, because the bugs this
guards against are invisible at small scale and dominate latency for expensive models
(the OpenMDAO example runs a full `problem.run_model()` per call). If a change makes
those tests fail on counts, that is a real regression, not a stale expectation.

**`hold_sync()` is not `hold_trait_notifications()`.** The first batches widget comm
traffic; only the second suppresses traitlets observers. Writing a pair of bounds under
`hold_sync()` re-runs every model twice. This caused a real bug — see issue #4.

**Figure marks are interleaved** `[line, dot, line, dot, ...]`, one pair per model, so
`marks[0::2]` are the lines and `marks[1::2]` the dots. Each column shares one x
`LinearScale` and each row one y scale (`View._xscales` / `_yscales`), so limit updates
are O(n_x + n_y); do not reach for `grid[i, j].axes[k].scale` to set limits.

**Styling is per model, by position, cycled.** `colors`, `line_styles`, `model_labels`
and `show_legend` are `View` traits and `profiler()` arguments. Color alone is never the
only encoding — line style is a deliberate secondary channel. `DEFAULT_COLORS` is
colorblind-safe and **validated**; do not reorder or substitute it casually, as the slot
ordering is the safety mechanism. `DARK_COLORS` is the same hues stepped for dark themes.

**traittypes suppresses no-op notifications**: assigning an array equal to the current
value does not fire observers. Useful, and a trap when a test expects a change event.

## Gotchas

- **The next version is already set; do not bump it as part of ordinary work.** The top
  of `CHANGELOG.md` is always `## vX.Y.Z (Unreleased)` and `__version__` in
  `src/ipysensitivityprofiler/__init__.py` already matches it — it is preset right after
  each release. Add changelog entries under that existing section. The preset defaults
  to the next patch (`Z + 1`), so raise it only if what you did warrants more: `Y + 1`
  for a backwards-compatible feature, `X + 1` for a breaking API change. If you do,
  change `__init__.py` and the changelog heading together and flag it. A released
  section still marked `(Unreleased)` means the post-release preset step was missed —
  fix the stale heading rather than adding to it. See CONTRIBUTING.md → Versioning.
- `__version__` is the single source of truth (`pyproject.toml` reads it dynamically;
  the release pipeline gates on it). `tests/test_meta.py` compares it against the
  *installed* distribution — if it does change, run `pixi run -e dev pip-e` or that test
  fails. That task is cached by input hash and may report a cache hit without actually
  reinstalling; if the test still fails, run `.pixi/envs/dev/bin/python -m pip install
  -e . --no-deps --no-build-isolation` directly.
- `notebooks/openmdao_example/_openmdao_profiler.py` sets `num_nodes` at `setup()` time
  and it must equal `grid_size(len(inputs), resolution)`. Changing the grid contract
  breaks it, and `test-nb` is its only coverage.
- Running notebook tests rewrites kernel-version metadata in the `.ipynb` files, and
  `pixi` may re-solve `pixi.lock`. Neither is a real change — check `git status` before
  committing.

## Reference

`CONTRIBUTING.md` covers environment setup, the CI workflows, and the full release
procedure. `CHANGELOG.md` uses conventional-commit categories (its header comment lists
them) and its `## v<version>` sections become GitHub Release notes.

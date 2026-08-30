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

## v0.0.4 (Unreleased)

## v0.0.3 (2026-08-30)

### Fix

- A model taking more than a couple of seconds rendered the widget as a completely
  blank cell in JupyterLab -- no axes, no frame, nothing. The models were evaluated
  while `View` was still being constructed, so the browser was told to display the
  widget before any of the figure widgets it needed had been registered. The whole
  widget tree is now built first and the models run exactly once afterwards, so a slow
  model shows an empty set of axes while it works instead of nothing at all.

### Feat

- `View.refresh()` evaluates the models and redraws. Constructing a `View` now draws
  flat placeholder curves rather than evaluating, so that no model can block before the
  figures exist; `profiler()` calls `refresh()` for you once the widget is assembled.
  Code building a `View` directly should call it after construction. The number of
  models is carried by the new `View.n_models` trait instead of being read back out of
  the model output.

## v0.0.2 (2026-08-29)

### Feat

- Models are now drawn in distinct colors as well as distinct line styles. Previously
  every curve used the same grey and differed only by dash pattern, which at high
  `resolution` and a 3px stroke is indistinguishable on screen -- two models looked
  identical in the usage notebook.

- `profiler` accepts `colors`, `line_styles`, `model_labels` and `show_legend`, each
  assigned to models by position and cycled if shorter than `models`. The same values
  are traits on `View`, so an existing widget can be restyled in place.

- The default palette is colorblind-safe, validated for the adjacent-pair gates in
  both light and dark modes (worst CVD dE 9.1 light / 8.4 dark against a >= 8 target,
  worst normal-vision dE 19.6 / 19.3 against a >= 15 floor). Line style is kept as a
  secondary encoding so models stay separable without relying on hue alone, in
  greyscale print or under forced-colors. `_utils.DARK_COLORS` holds the same eight
  hues stepped for a dark notebook theme.

- A legend keys models to their color and stroke, labelled with each model's function
  name by default. It is shown once for the whole grid rather than in every cell, and
  only when there is more than one model.

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

### Perf

- User models are now evaluated once per interaction instead of two to three times.
  `create_grid` appends the profiled point `x0` as the grid's final row, so the value
  behind the red dot comes back from the same call as the curves rather than costing a
  separate single-row call. Measured on a two-model, two-input profiler at
  `resolution=25`: startup went from 6 model calls to 2, an x0 slider drag from 4 to 2,
  and an x-range drag from 4 calls over 200 rows to 2 over 102.

- `Controller` used `hold_sync()` when writing a pair of bounds, which batches widget
  comm traffic but not traitlets notifications, so each of `xmin`/`xmax` separately
  rebuilt the grid and re-ran every model. It now uses `hold_trait_notifications()`.

- `View` linked `predict` to `Data` bidirectionally, which fired `Data`'s observer twice
  during setup and evaluated the whole grid an extra time. It is now a one-way `dlink`,
  and `Data` computes `y` once when its `x -> y` link is registered.

- Row lookups in the redraw path use slices rather than lists of indices, so they are
  views instead of copies (~13x faster indexing).

- Every figure in a column now shares one x scale, and every figure in a row one y
  scale, instead of each cell owning a private pair. On a 5x4 grid this is 9 scale
  objects rather than 40, and updating the axis limits is O(n_x + n_y) writes instead
  of O(n_x * n_y).

### Fix

- Changing an input's range recomputed the grid and re-evaluated every model, then
  discarded the result: `_update_figs` observed only `x0`, so the axis rescaled while
  the curve still spanned the old window. Redraws are now driven by `Data.y`, which
  every invalidating path already flows through.

- `_batches` was cached as a trait default and never invalidated, so after a change to
  `resolution` each column plotted the wrong input entirely -- at `resolution=50`,
  column 1 replayed input 0's sweep. The offset is now computed on demand.

- The red dot showed the grid's first row rather than `f(x0)` in the OpenMDAO example,
  because that model is set up with a fixed `num_nodes` and ignored the row count of the
  single-point call the profiler used to make.

- `_update_labels` was registered as a traitlets observer but declared without a
  parameter for the change argument, so assigning `xlabels` or `ylabels` raised
  `TypeError`.

- `profiler(xlabels=None)` raised `TraitError` instead of falling back to `x1, x2, ...`
  as documented; `None` reached the `T.List` trait before its validator could substitute
  the default.

- `Data.__init__` passed `self` positionally to `super().__init__`, emitting a traitlets
  `DeprecationWarning` that is slated to become an error.

- `save_png` overwrote its `filename` argument, so an explicit filename was ignored.

- `_validate_width` sized the default width from the number of outputs rather than the
  number of inputs.

- Profiling more than four models raised `IndexError`; line styles now cycle.

- Coverage was measured against the `jenn` package instead of this one, so the reported
  coverage was always empty.

- Notebook tests silently skipped `notebooks/openmdao_example/`.

- `make_figure` used a mutable default argument for `tick_style`.

### Test

- `tests/test_meta.py` now checks that `__version__`, the installed distribution version
  and the public API all agree, instead of asserting `True`.

- Added `tests/test_profiler.py`, the first functional coverage of the widget: how many
  times user models are called per interaction, that curves and the red dot match the
  model, and regressions for each of the crashes above.

### Docs

- Documentation restructured into `index` + `sections/` (quickstart, API, appendix), and
  now builds strictly (`sphinx-build -W`).

## v0.0.1 (2024-11-18)

- First release of `ipysensitivityprofiler`

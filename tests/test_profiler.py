"""Functional tests for the profiler widget.

These cover the behaviour that the audit in issue #4 found broken: how often user
models are evaluated, and whether what gets plotted actually reflects the data.
"""

import warnings
from typing import Any

import bqplot as bq
import numpy as np
import pytest

import ipysensitivityprofiler as isp
from ipysensitivityprofiler import _model, _view
from ipysensitivityprofiler._data import Data
from ipysensitivityprofiler._utils import grid_size

NX = 2
NY = 1
RESOLUTION = 25
XMIN = [-5.0, -5.0]
XMAX = [5.0, 5.0]
YMIN = [-1000.0]
YMAX = [1000.0]
X0 = [1.0, 2.0]

# Distinct per-input weights, so a curve reveals *which* input it was swept over.
WEIGHTS = np.array([1.0, 100.0])


@pytest.fixture
def counter() -> dict[str, int]:
    """Tally of calls into the user model and rows evaluated."""
    return {"calls": 0, "rows": 0}


def make_model(counter: dict[str, int], scale: float = 1.0) -> Any:
    """Build a counting model with output that identifies the swept input."""

    def f(x: np.ndarray) -> np.ndarray:
        counter["calls"] += 1
        counter["rows"] += x.shape[0]
        return np.column_stack([scale * (x * WEIGHTS).sum(axis=1)])

    return f


def make_profiler(counter: dict[str, int], n_models: int = 2, **kwargs: Any) -> Any:
    """Build a profiler over `n_models` counting models."""
    models = [make_model(counter, scale=k + 1.0) for k in range(n_models)]
    params: dict[str, Any] = dict(
        models=models,
        xmin=XMIN,
        xmax=XMAX,
        ymin=YMIN,
        ymax=YMAX,
        x0=X0,
        resolution=RESOLUTION,
        xlabels=["x1", "x2"],
        ylabels=["y"],
    )
    params.update(kwargs)
    return isp.profiler(**params)


def marks_of(view: Any, i: int, j: int) -> tuple[list, list]:
    """Return (lines, dots) of the figure at row i, column j."""
    marks = view.grid[i, j].marks
    lines = [m for m in marks if isinstance(m, bq.marks.Lines)]
    dots = [m for m in marks if isinstance(m, bq.marks.Scatter)]
    return lines, dots


#####################################
# When models are called (issue #6) #
#####################################


def test_widgets_are_built_before_any_model_runs(monkeypatch: Any) -> None:
    """No user model may run until the whole widget tree exists.

    Issue #6: the models used to run while `View` was still under construction,
    so with a slow model the frontend received the cell's display message before
    a single figure widget had been registered, and rendered a blank cell.
    """
    order: list[str] = []
    real_make_grid = _view.make_grid
    real_controller = _model.Controller

    def spy_make_grid(*args: Any, **kwargs: Any) -> Any:
        order.append("grid")
        return real_make_grid(*args, **kwargs)

    def spy_controller(*args: Any, **kwargs: Any) -> Any:
        order.append("controller")
        return real_controller(*args, **kwargs)

    monkeypatch.setattr(_view, "make_grid", spy_make_grid)
    monkeypatch.setattr(_model, "Controller", spy_controller)

    def f(x: np.ndarray) -> np.ndarray:
        order.append("model")
        return np.column_stack([x.sum(axis=1)])

    isp.profiler(
        models=[f],
        xmin=XMIN,
        xmax=XMAX,
        ymin=YMIN,
        ymax=YMAX,
        x0=X0,
        resolution=RESOLUTION,
    )

    assert order == ["grid", "controller", "model"]


def make_evaluate(counter: dict[str, int], n_models: int = 2) -> Any:
    """Build the multi-model callback that `profiler()` hands to `View`."""
    models = [make_model(counter, scale=k + 1.0) for k in range(n_models)]

    def evaluate(x: np.ndarray) -> np.ndarray:
        return np.concatenate([f(x).reshape((-1, NY, 1)) for f in models], axis=2)

    return evaluate


def test_view_infers_model_count_when_not_given(counter: dict[str, int]) -> None:
    """A bare `View` still works: it probes for the count with a single row.

    `profiler()` passes `n_models` so that nothing runs before the widgets exist,
    but `View` is public and must stay constructible on its own.
    """
    view = isp.View(
        predict=make_evaluate(counter),
        xmin=XMIN,
        xmax=XMAX,
        ymin=YMIN,
        ymax=YMAX,
        x0=X0,
        resolution=RESOLUTION,
        xlabels=["x1", "x2"],
        ylabels=["y"],
    )

    assert counter["rows"] == 2  # one row per model, not the whole grid
    assert len(marks_of(view, 0, 0)[0]) == 2


def test_view_construction_does_not_evaluate(counter: dict[str, int]) -> None:
    """Building a `View` draws flat placeholders; `refresh()` runs the models."""
    view = isp.View(
        predict=make_evaluate(counter),
        n_models=2,
        xmin=XMIN,
        xmax=XMAX,
        ymin=YMIN,
        ymax=YMAX,
        x0=X0,
        resolution=RESOLUTION,
        xlabels=["x1", "x2"],
        ylabels=["y"],
        width=600,
        height=300,
    )

    assert counter["calls"] == 0
    lines, _ = marks_of(view, 0, 0)
    assert len(lines) == 2  # one placeholder curve per model, drawn flat
    np.testing.assert_allclose(lines[0].y, np.zeros(RESOLUTION))

    view.refresh()

    assert counter["calls"] == 2
    grid = np.tile(np.array(X0, dtype=float), (RESOLUTION, 1))
    grid[:, 0] = np.linspace(XMIN[0], XMAX[0], RESOLUTION)
    np.testing.assert_allclose(lines[0].y, (grid * WEIGHTS).sum(axis=1))


###############################
# How often models are called #
###############################


def test_startup_evaluates_each_model_once(counter: dict[str, int]) -> None:
    """Construction evaluates the grid once per model, not two or three times."""
    make_profiler(counter)
    assert counter["calls"] == 2
    assert counter["rows"] == 2 * grid_size(NX, RESOLUTION)


def test_x0_slider_evaluates_each_model_once(counter: dict[str, int]) -> None:
    """Moving an x0 slider costs one grid evaluation per model.

    The value at x0 rides along as the grid's final row rather than requiring a
    separate single-row call.
    """
    p = make_profiler(counter)
    counter.update(calls=0, rows=0)

    p.controller.sliders[0].value = 2.0

    assert counter["calls"] == 2
    assert counter["rows"] == 2 * grid_size(NX, RESOLUTION)


def test_x_range_slider_evaluates_each_model_once(counter: dict[str, int]) -> None:
    """An x-range change rebuilds the grid exactly once, not once per bound."""
    p = make_profiler(counter)
    counter.update(calls=0, rows=0)

    p.controller.range_sliders["x"][0].value = (-4.0, 4.0)

    assert counter["calls"] == 2
    assert counter["rows"] == 2 * grid_size(NX, RESOLUTION)


def test_y_range_slider_does_not_evaluate(counter: dict[str, int]) -> None:
    """Output limits are display-only and must not re-run the models."""
    p = make_profiler(counter)
    counter.update(calls=0, rows=0)

    p.controller.range_sliders["y"][0].value = (-800.0, 800.0)

    assert counter["calls"] == 0


##########################
# What actually gets drawn #
##########################


def test_range_change_redraws_lines(counter: dict[str, int]) -> None:
    """Changing xmin/xmax redraws the curve, not just the axis."""
    p = make_profiler(counter)
    p.controller.range_sliders["x"][0].value = (-2.0, 2.0)

    lines, _ = marks_of(p.view, 0, 0)
    assert lines[0].x.min() == pytest.approx(-2.0)
    assert lines[0].x.max() == pytest.approx(2.0)


def test_resolution_change_keeps_columns_aligned(counter: dict[str, int]) -> None:
    """After a resolution change every column still plots its own input.

    A stale batch offset silently makes column 1 replay input 0's sweep.
    """
    p = make_profiler(counter)
    p.view.resolution = 50

    for j in range(NX):
        lines, _ = marks_of(p.view, 0, j)
        expected = np.linspace(XMIN[j], XMAX[j], 50)
        assert lines[0].x.size == 50
        np.testing.assert_allclose(lines[0].x, expected)


def test_curves_match_the_model(counter: dict[str, int]) -> None:
    """Each curve equals its own model swept over its own input."""
    p = make_profiler(counter)

    for j in range(NX):
        lines, _ = marks_of(p.view, 0, j)
        grid = np.tile(np.array(X0, dtype=float), (RESOLUTION, 1))
        grid[:, j] = np.linspace(XMIN[j], XMAX[j], RESOLUTION)
        for k, line in enumerate(lines):
            expected = (k + 1.0) * (grid * WEIGHTS).sum(axis=1)
            np.testing.assert_allclose(line.y, expected)


def test_dot_matches_x0(counter: dict[str, int]) -> None:
    """The red dot sits at f(x0), not at the grid's first row."""
    p = make_profiler(counter)
    x0 = np.array([X0], dtype=float)

    for j in range(NX):
        _, dots = marks_of(p.view, 0, j)
        for k, dot in enumerate(dots):
            expected = (k + 1.0) * (x0 * WEIGHTS).sum(axis=1)
            np.testing.assert_allclose(dot.y, expected)
            np.testing.assert_allclose(dot.x, [X0[j]])


def test_slider_dot_link_terminates(counter: dict[str, int]) -> None:
    """The bidirectional dot/slider link must not drive a redraw loop."""
    p = make_profiler(counter)
    counter.update(calls=0, rows=0)

    _, dots = marks_of(p.view, 0, 0)
    dots[0].x = np.array([3.0])

    assert counter["calls"] <= 2
    assert p.controller.sliders[0].value == pytest.approx(3.0)


######################
# Crash regressions  #
######################


def test_labels_can_be_reassigned(counter: dict[str, int]) -> None:
    """`_update_labels` is an observer and must accept a change argument."""
    p = make_profiler(counter)
    p.view.xlabels = ["a", "b"]
    assert p.view.grid[0, 0].axes[0].label == "a"


def test_labels_default_when_omitted(counter: dict[str, int]) -> None:
    """The documented `None` default for labels works."""
    p = make_profiler(counter, xlabels=None, ylabels=None)
    assert len(p.view.xlabels) == NX
    assert len(p.view.ylabels) == NY


def test_data_construction_is_warning_free() -> None:
    """`Data.__init__` must not pass `self` positionally to traitlets."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        Data(
            xlabels=["a"],
            ylabels=["b"],
            predict=lambda x: x.reshape(-1, 1, 1),
            x=np.zeros((3, 1)),
        )


def test_more_than_four_models(counter: dict[str, int]) -> None:
    """Line styles cycle rather than raising IndexError."""
    p = make_profiler(counter, n_models=6)
    lines, _ = marks_of(p.view, 0, 0)
    assert len(lines) == 6


def test_save_png_honours_filename(tmp_path: Any, counter: dict[str, int]) -> None:
    """`save_png` must not discard an explicit filename."""
    p = make_profiler(counter)
    target = tmp_path / "custom.png"
    captured: dict[str, Any] = {}

    def fake_get_png_data(callback: Any, _scale: Any = None) -> None:
        captured["callback"] = callback

    p.view.grid[0, 0].get_png_data = fake_get_png_data
    p.view.save_png("x1", "y", filename=str(target))
    captured["callback"](b"stub")

    assert target.read_bytes() == b"stub"


def test_scales_are_shared_per_column_and_row(counter: dict[str, int]) -> None:
    """One scale per column and per row, not a private pair per cell."""
    p = make_profiler(counter)
    view = p.view

    scales = {
        id(view.grid[i, j].axes[k].scale)
        for i in range(NY)
        for j in range(NX)
        for k in (0, 1)
    }
    assert len(scales) == NX + NY

    view.xmin = np.array([-2.0] * NX)
    view.xmax = np.array([2.0] * NX)
    assert view.grid[0, 0].axes[0].scale.min == pytest.approx(-2.0)


#####################
# Per-model styling #
#####################


def test_models_get_distinct_colors_and_strokes(counter: dict[str, int]) -> None:
    """Two models must not render identically."""
    p = make_profiler(counter, n_models=2)
    lines, _ = marks_of(p.view, 0, 0)

    assert lines[0].colors != lines[1].colors
    assert lines[0].line_style != lines[1].line_style


def test_style_assignment_is_consistent_across_the_grid(
    counter: dict[str, int],
) -> None:
    """Model k looks the same in every cell, so one legend describes them all."""
    p = make_profiler(counter, n_models=3)
    reference = [
        (line.colors[0], line.line_style) for line in marks_of(p.view, 0, 0)[0]
    ]

    for j in range(NX):
        lines, _ = marks_of(p.view, 0, j)
        assert [(x.colors[0], x.line_style) for x in lines] == reference


def test_styles_cycle_past_the_palette(counter: dict[str, int]) -> None:
    """More models than palette slots cycles rather than raising."""
    p = make_profiler(counter, n_models=10)
    lines, _ = marks_of(p.view, 0, 0)

    assert len(lines) == 10
    assert lines[8].colors == lines[0].colors  # 8-slot palette wrapped
    assert lines[4].line_style == lines[0].line_style  # 4 styles wrapped


def test_legend_appears_once_and_only_for_multiple_models(
    counter: dict[str, int],
) -> None:
    """A legend keys the models, but one copy is enough for the whole grid."""
    p = make_profiler(counter, n_models=2)
    showing = [
        line.display_legend
        for i in range(NY)
        for j in range(NX)
        for line in marks_of(p.view, i, j)[0]
    ]
    assert sum(showing) == 2  # one entry per model, in a single cell

    solo = make_profiler(counter, n_models=1)
    assert not any(
        line.display_legend for line in marks_of(solo.view, 0, 0)[0]
    )  # a lone curve needs no key


def test_model_labels_default_to_function_names() -> None:
    """The legend names the models rather than numbering them."""

    def alpha(x: np.ndarray) -> np.ndarray:
        return np.column_stack([x.sum(axis=1)])

    def beta(x: np.ndarray) -> np.ndarray:
        return np.column_stack([2 * x.sum(axis=1)])

    p = isp.profiler(
        models=[alpha, beta],
        xmin=XMIN,
        xmax=XMAX,
        ymin=YMIN,
        ymax=YMAX,
        x0=X0,
        resolution=RESOLUTION,
    )
    lines, _ = marks_of(p.view, 0, 0)
    assert [line.labels[0] for line in lines] == ["alpha", "beta"]


def test_explicit_styles_are_honoured(counter: dict[str, int]) -> None:
    """Callers can supply their own palette, strokes and legend keys."""
    p = make_profiler(
        counter,
        n_models=2,
        colors=["#111111", "#e34948"],
        line_styles=["dotted", "solid"],
        model_labels=["baseline", "variant"],
    )
    lines, _ = marks_of(p.view, 0, 0)

    assert [line.colors[0] for line in lines] == ["#111111", "#e34948"]
    assert [line.line_style for line in lines] == ["dotted", "solid"]
    assert [line.labels[0] for line in lines] == ["baseline", "variant"]


def test_styles_can_be_changed_after_construction(counter: dict[str, int]) -> None:
    """Restyling an existing widget updates the marks already on screen."""
    p = make_profiler(counter, n_models=2)
    p.view.colors = ["#000000", "#ff00ff"]

    for j in range(NX):
        lines, _ = marks_of(p.view, 0, j)
        assert [line.colors[0] for line in lines] == ["#000000", "#ff00ff"]

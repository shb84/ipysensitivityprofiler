from collections.abc import Callable
from typing import Any

import ipywidgets as W
import numpy as np

from ._controller import Controller
from ._view import DEFAULT_RESOLUTION, DEFAULT_WIDTH, View


class Profiler(W.VBox):
    """Profiler Widget.

    Attributes:
        view: :py:class:`View`
            Profiler widget controlled by controller.

        controller: :py:class:`Controller`
            Widget to control profilers
    """

    def __init__(self, view: View, controller: Controller, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.view = view
        self.controller = controller
        self.children = [view, controller]


def profiler(
    models: list[Callable],
    xmin: list[float] | np.ndarray,
    xmax: list[float] | np.ndarray,
    ymin: list[float] | np.ndarray,
    ymax: list[float] | np.ndarray,
    x0: list[float] | np.ndarray | None = None,
    resolution: int = DEFAULT_RESOLUTION,
    width: int = DEFAULT_WIDTH,
    height: int | None = None,
    xlabels: list[str] | None = None,
    ylabels: list[str] | None = None,
    colors: list[str] | None = None,
    line_styles: list[str] | None = None,
    model_labels: list[str] | None = None,
    show_legend: bool | None = None,
) -> Profiler:
    """Create sensitivity profilers for given models.

    Example:
        .. code-block:: python

            import ipysensitivityprofiler as isp

            def f1(x):
                return -0.1 * x[:, 0] ** 3 - 0.5 * x[:, 1] ** 2

            def f2(x):
                return -0.2 * x[:, 0] ** 3 - 0.25 * x[:, 1] ** 2

            isp.profiler(
                models=[f1, f2],
                xmin=[-5, -5],
                xmax=[5, 5],
                ymin=[-10],
                ymax=[10],
                x0=[1, 1],
                resolution=100,
                xlabels=["x1", "x2"],
                ylabels=["y"],
            )

    Args:
        models: List[callable]
            List of callable functions with the same
            signature y = f(x). There will be one
            profile per model. x must be a numpy array
            of shape (-1, nx) and y an array of shape (-1, ny).

        xmin: Union[List[float], np.ndarray]
            Lower bounds of inputs.

        xmax: Union[List[float], np.ndarray]
            Upper bounds of inputs.

        ymin: Union[List[float], np.ndarray]
            Lower bounds of outputs.

        ymax: Union[List[float], np.ndarray]
            Upper bounds of outputs.

        x0: Union[List[float], np.ndarray]
        Defaults to use for initial x0 (red dot in plots).
        Default is None (which turns into mean of range).

        resolution: int, optional
            Line resolution. Default is 25 points.

        width: int, optional
            Width of each plot. Default is 300 pixels.

        height: int, optional
            Height of each plot. Default is None (match width).

        xlabels: List[str]
            Labels to use for inputs. Default is None (which becomes x1, x2, ...)

        ylabels: Union[List[float], np.ndarray]
            Labels to use for outputs. Default is None (which becomes y1, y2, ...)

        colors: List[str], optional
            Line color per model, by position, as any CSS color. Cycled if
            shorter than `models`. Default is None, which uses a colorblind-safe
            categorical palette. Pass
            `ipysensitivityprofiler._utils.DARK_COLORS` under a dark theme.

        line_styles: List[str], optional
            Line style per model, by position: one of "solid", "dashed",
            "dotted", "dash_dotted". Cycled if shorter than `models`. Default is
            None, which cycles all four so models stay distinguishable without
            relying on color alone.

        model_labels: List[str], optional
            Legend label per model. Default is None, which uses each model's
            function name.

        show_legend: bool, optional
            Show a legend keying models to their color and stroke. Default is
            None, which shows one when there is more than one model.

    Returns:
        Profiler: Jupyter Widget.

    """
    if height is None:
        height = width

    nx = len(xmin)
    ny = len(ymin)

    if x0 is None:
        x0 = [0.5 * (xmin[i] + xmax[i]) for i in range(nx)]

    def evaluate(x: np.ndarray) -> np.ndarray:
        # NOTE: concatenate + reshape benchmarks faster here than np.stack; see
        # https://github.com/shb84/ipysensitivityprofiler/issues/4 (item 3.2).
        outputs = [f(x).reshape((-1, ny, 1)) for f in models]
        return np.concatenate(outputs, axis=2)

    if model_labels is None:
        # A named function is a better legend key than "model 1"; lambdas and other
        # anonymous callables have no useful __name__, so fall back for those.
        model_labels = [
            name
            if (name := getattr(f, "__name__", "<lambda>")) != "<lambda>"
            else f"model {k + 1}"
            for k, f in enumerate(models)
        ]

    # NOTE: `None` would be rejected by the `T.List` / `T.Bool` traits before their
    # validators get a chance to substitute the documented defaults, so omit the
    # keys entirely.
    optional: dict[str, Any] = {
        "xlabels": xlabels,
        "ylabels": ylabels,
        "colors": colors,
        "line_styles": line_styles,
        "model_labels": model_labels,
        "show_legend": show_legend,
    }
    labels = {key: value for key, value in optional.items() if value is not None}

    view = View(
        predict=evaluate,
        **labels,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        x0=x0,
        width=width * len(xmin),  # total width
        height=height * len(ymin),  # total height
        resolution=resolution,
    )

    controller = Controller(view)

    return Profiler(view, controller)

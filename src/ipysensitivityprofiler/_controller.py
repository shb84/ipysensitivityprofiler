from functools import partial
from typing import Any

import bqplot as bq
import ipywidgets as W
import numpy as np
import traitlets as T

from ._view import View


def _update_ylim(view: View, index: int, proposal: T.Bunch) -> None:
    if proposal.new != proposal.old:
        ymin = view.ymin.tolist()
        ymax = view.ymax.tolist()
        ymin[index] = proposal.new[0]
        ymax[index] = proposal.new[1]
        with view.hold_trait_notifications():
            view.ymax = ymax
            view.ymin = ymin


def _update_xlim(view: View, index: int, proposal: T.Bunch) -> None:
    if proposal.new != proposal.old:
        xmin = view.xmin.tolist()
        xmax = view.xmax.tolist()
        xmin[index] = proposal.new[0]
        xmax[index] = proposal.new[1]
        with view.hold_trait_notifications():
            view.xmax = xmax
            view.xmin = xmin


def _update_x0(view: View, index: int, proposal: T.Bunch) -> None:
    if proposal.new != proposal.old:
        x0 = view.x0.copy()
        x0[0, index] = proposal.new
        view.x0 = x0


def _create_sliders(view: View) -> list[W.FloatSlider]:
    sliders = []
    for i in range(view.data.n_x):
        slider = W.FloatSlider(
            value=view.x0[0, i],
            min=view.xmin[i],
            max=view.xmax[i],
            step=(view.xmax[i] - view.xmin[i]) / view.resolution,
            description=view.xlabels[i],
        )
        sliders.append(slider)
    return sliders


def _create_range_sliders(view: View) -> dict[str, list[W.FloatRangeSlider]]:
    sliders: dict[str, list[W.FloatRangeSlider]] = {"x": [], "y": []}

    for i in range(view.data.n_y):
        slider = W.FloatRangeSlider(
            value=(view.ymin[i], view.ymax[i]),
            min=view.ymin[i],
            max=view.ymax[i],
            description=view.ylabels[i],
            step=(view.ymax[i] - view.ymin[i]) / view.resolution,
            orientation="horizontal",
            readout=True,
            # readout_format='.2f',
        )
        sliders["y"].append(slider)

    for i in range(view.data.n_x):
        slider = W.FloatRangeSlider(
            value=(view.xmin[i], view.xmax[i]),
            min=view.xmin[i],
            max=view.xmax[i],
            description=view.xlabels[i],
            step=(view.xmax[i] - view.xmin[i]) / view.resolution,
            orientation="horizontal",
            readout=True,
            # readout_format='.2f',
        )
        sliders["x"].append(slider)

    return sliders


class Controller(W.VBox):
    """Control panel for profiler.

    Attributes:
        range_sliders: Dict[str, List[W.FloatRangeSlider]]:
            Range sliders to control axis limits of inputs and outputs:

        .. code-block:: python

            range_sliders = {
                "x": [...],  # list of range sliders associated with inputs
                "y": [...],  # list of range sliders associated with outputs
            }

        sliders: List[W.FloatSlider]
            Sliders to control input values (and automatically update view).

    """

    def __init__(self, view: View, **kwargs: Any):
        """Public constructor.

        view: :py:class:`View`
            Profiler widget to be controlled by controller.
        """
        super().__init__(**kwargs)

        self.range_sliders = _create_range_sliders(view)

        for i, range_slider in enumerate(self.range_sliders["y"]):
            range_slider.observe(partial(_update_ylim, view, i), "value")

        for j, range_slider in enumerate(self.range_sliders["x"]):
            range_slider.observe(partial(_update_xlim, view, j), "value")

        self.sliders = _create_sliders(view)

        for j, slider in enumerate(self.sliders):
            slider.observe(partial(_update_x0, view, j), "value")
            for i in range(view.data.n_y):
                marks = view.grid[i, j].marks
                for mark in marks:
                    if isinstance(mark, bq.marks.Scatter):
                        dot = mark
                        W.link(
                            (dot, "x"),
                            (slider, "value"),
                            transform=(
                                lambda x: x.squeeze(),
                                lambda value: np.array([value]),
                            ),
                        )

        self.children = [
            *self.sliders,
            *self.range_sliders["x"],
            *self.range_sliders["y"],
        ]

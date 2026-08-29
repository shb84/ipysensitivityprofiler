import bqplot as bq
import ipywidgets as W
import numpy as np
from numpy.typing import NDArray

DOT_COLOR = "#CD0000"
LINE_WIDTH = 3

# Categorical palette, assigned to models in this fixed order. Validated for the
# adjacent-pair gates in both modes: worst CVD dE 9.1 light / 8.4 dark (>=8 target),
# worst normal-vision dE 19.6 light / 19.3 dark (>=15 floor). Do not reorder -- the
# ordering is what makes it colorblind-safe, not cosmetics.
DEFAULT_COLORS = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]

# The same eight hues stepped for a dark surface. Pass as `colors=` when running
# under a dark notebook theme; aqua, yellow and magenta fall below 3:1 contrast on
# a light surface and these do not.
DARK_COLORS = [
    "#3987e5",
    "#d95926",
    "#199e70",
    "#c98500",
    "#d55181",
    "#008300",
    "#9085e9",
    "#e66767",
]

# Secondary encoding, so models stay distinguishable without relying on hue alone
# (colorblind readers, greyscale printing, forced-colors mode).
DEFAULT_LINE_STYLES = [
    "solid",
    "dashed",
    "dotted",
    "dash_dotted",
]

LINE_COLOR = DEFAULT_COLORS[0]  # retained for backwards compatibility
LINE_STYLE = DEFAULT_LINE_STYLES  # retained for backwards compatibility
FIG_MARGIN = dict(top=45, bottom=45, left=45, right=45)
BETWEEN_SPACE = 5


def grid_size(n_x: int, resolution: int) -> int:
    """Number of rows in a grid built by :py:func:`create_grid`.

    Callers that must pre-size buffers for a fixed number of evaluation
    points (such as an OpenMDAO problem's ``num_nodes``) should size
    them with this.
    """
    return n_x * resolution + 1


def create_grid(
    x0: NDArray, xmin: NDArray, xmax: NDArray, resolution: int = 10
) -> NDArray:
    """Generate grid data for sensitivity profilers.

    Args:
        x0: NDArray
            Local point about which to plot sensivities.
            Array of shape (n,) where n is the
            number of input variables.

        xmin: NDArray
            Min bound for plotting sensitivities.
            Array of shape (n,)

        xmax: NDArray
            Max bound for plotting sensitivities.
            Array of shape (n,)

        resolution: int, optional
            Number of points between xmin and xmax.
            Default is 10.

    Returns:
        NDArray
            Array of shape (resolution * n + 1, n). The first ``resolution * n``
            rows sweep one input at a time; the final row is ``x0`` itself.

    Example:
        .. code-block:: python

                x = create_grid(
                    x0=[ 0, 1, 2],
                    xmin=[-5, -5, -5],
                    xmax=[ 5, 5, 5],
                    resolution=10,
                )

                >> x = [[-5,  1,  2],
                        [-3,  1,  2],
                        [-2,  1,  2],
                        [-1,  1,  2],
                        [ 0,  1,  2],
                        [ 0,  1,  2],
                        [ 1,  1,  2],
                        [ 2,  1,  2],
                        [ 3,  1,  2],
                        [ 5,  1,  2],
                        [ 0, -5,  2],
                        [ 0, -3,  2],
                        [ 0, -2,  2],
                        [ 0, -1,  2],
                        [ 0,  0,  2],
                        [ 0,  0,  2],
                        [ 0,  1,  2],
                        [ 0,  2,  2],
                        [ 0,  3,  2],
                        [ 0,  5,  2],
                        [ 0,  1, -5],
                        [ 0,  1, -3],
                        [ 0,  1, -2],
                        [ 0,  1, -1],
                        [ 0,  1,  0],
                        [ 0,  1,  0],
                        [ 0,  1,  1],
                        [ 0,  1,  2],
                        [ 0,  1,  3],
                        [ 0,  1,  5],
                        [ 0,  1,  2]]  # <- x0

    """
    ##########
    # Checks #
    ##########

    x0 = np.asarray(x0, dtype=np.float64).ravel()
    xmin = np.asarray(xmin, dtype=np.float64).ravel()
    xmax = np.asarray(xmax, dtype=np.float64).ravel()

    assert x0.size == xmin.size == xmax.size

    #########
    # Setup #
    #########

    n = x0.size
    m = resolution

    ########
    # Data #
    ########

    # One extra row holds x0 itself, so the value at the profiled point comes back
    # from the same model call as the curves instead of costing a second one.
    x = np.tile(x0.reshape((1, -1)), (grid_size(n, m), 1))

    for i in range(n):
        start = i * m
        stop = (i + 1) * m
        x[start:stop, i] = np.linspace(xmin[i], xmax[i], m)

    return x


def batch_slice(index: int, resolution: int) -> slice:
    """Return the rows of a grid that sweep input `index`.

    Grids from :py:func:`create_grid` lay out one contiguous sweep per input, so the
    rows for a given input are a plain slice. Using a slice rather than a list of
    indices keeps the lookup a view instead of a copy, which matters because this sits
    in the redraw path.

    Args:
        index: int
            Index of the input variable.

        resolution: int
            Number of points per sweep.

    Returns:
        slice
            Row slice corresponding to one grid permutation.
    """
    return slice(index * resolution, (index + 1) * resolution)


def make_figure(
    N: int,
    num_x_ticks: int = 3,
    num_y_ticks: int = 3,
    tick_style: dict | None = None,
    xmin: float | None = None,
    xmax: float | None = None,
    ymin: float | None = None,
    ymax: float | None = None,
    xs: bq.LinearScale | None = None,
    ys: bq.LinearScale | None = None,
    colors: list[str] | None = None,
    line_styles: list[str] | None = None,
    labels: list[str] | None = None,
    show_legend: bool = False,
) -> bq.Figure:
    """Create initial figure for profiler trait (data will be replaced).

    Pass `xs` / `ys` to share a scale with the other figures in the same
    column / row; omit them and the figure owns a private scale built
    from the bounds.

    `colors` and `line_styles` are assigned to models by position and
    cycled if shorter than `N`, so each model is distinguishable by hue
    and by stroke.
    """
    if tick_style is None:
        tick_style = {"font-size": 10}
    if colors is None:
        colors = DEFAULT_COLORS
    if line_styles is None:
        line_styles = DEFAULT_LINE_STYLES
    x = np.array([0, 1])
    y = np.array([0, 1])
    x0 = np.array([0.5])
    y0 = np.array([0.5])
    if xs is None:
        xs = bq.LinearScale(min=xmin, max=xmax)
    if ys is None:
        ys = bq.LinearScale(min=ymin, max=ymax)
    marks = []
    for k in range(N):
        line = bq.Lines(
            x=x,
            y=y,
            scales={"x": xs, "y": ys},
            colors=[colors[k % len(colors)]],
            stroke_width=LINE_WIDTH,
            line_style=line_styles[k % len(line_styles)],
            labels=[labels[k]] if labels else [],
            display_legend=show_legend,
        )
        dot = bq.marks.Scatter(
            x=x0,
            y=y0,
            marker="circle",
            scales={"x": xs, "y": ys},
            colors=[DOT_COLOR],
            tooltip=W.HTML(),
            enable_move=True,
            # restrict_x=True,
        )

        def _on_hover(mark: bq.Mark, event: dict) -> None:
            x = event["data"]["x"]
            y = event["data"]["y"]
            mark.tooltip.value = f"({x:.4f}, {y:.4f})"

        dot.on_hover(_on_hover)
        marks.extend([line, dot])
    xax = bq.Axis(
        scale=xs,
        grid_lines="solid",
        num_ticks=num_x_ticks,
        tick_style=tick_style,
    )
    yax = bq.Axis(
        scale=ys,
        grid_lines="solid",
        orientation="vertical",
        num_ticks=num_y_ticks,
        tick_style=tick_style,
    )
    layout = W.Layout(
        display="flex",
        flex_flow="column",
        border="solid 2px",
        align_items="stretch",
        width="auto",
        height="auto",
    )
    fig = bq.Figure(marks=marks, axes=[xax, yax], layout=layout, fig_margin=FIG_MARGIN)
    return fig


def make_grid(
    n_x: int,
    n_y: int,
    N: int,
    width: int | None = None,
    height: int | None = None,
    xscales: list[bq.LinearScale] | None = None,
    yscales: list[bq.LinearScale] | None = None,
    colors: list[str] | None = None,
    line_styles: list[str] | None = None,
    labels: list[str] | None = None,
    show_legend: bool = False,
) -> W.GridspecLayout:
    """Create grid layout of specified width and height.

    Every figure in column `j` shows the same input and every figure in
    row `i` the same output, so `xscales` / `yscales` let one scale per
    column / row be shared across the whole grid rather than each cell
    owning a private pair.
    """
    if width:
        fig_width = f"{width / n_x - BETWEEN_SPACE}px"
    if height:
        fig_height = f"{height / n_y - BETWEEN_SPACE}px"
    grid = W.GridspecLayout(n_y, n_x)
    for j in range(n_x):
        for i in range(n_y):
            grid[i, j] = make_figure(
                N,
                xs=xscales[j] if xscales else None,
                ys=yscales[i] if yscales else None,
                colors=colors,
                line_styles=line_styles,
                labels=labels,
                # Every cell shares one model -> style mapping, so a legend in
                # each would be n_x * n_y copies of the same key. One is enough.
                show_legend=show_legend and i == 0 and j == 0,
            )
            if width:
                grid[i, j].layout.width = fig_width
            if height:
                grid[i, j].layout.height = fig_height
    return grid

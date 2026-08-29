import bqplot as bq
import ipywidgets as W
import numpy as np
from numpy.typing import NDArray

DOT_COLOR = "#CD0000"
LINE_COLOR = "#797a7a"
LINE_WIDTH = 3
LINE_STYLE = [
    "solid",
    "dashed",
    "dotted",
    "dash_dotted",
]  # TODO: handle more than 4 curves and add legends
FIG_MARGIN = dict(top=45, bottom=45, left=45, right=45)
BETWEEN_SPACE = 5


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
            Array of shape (resolution * n, n)

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
                        [ 0,  1,  5]]

    """
    ##########
    # Checks #
    ##########

    x0 = x0.ravel()
    xmax = xmax.ravel()
    xmin = xmin.ravel()

    assert x0.size == xmin.size == xmax.size

    #########
    # Setup #
    #########

    x0 = x0.reshape((1, -1))
    n = x0.size
    m = resolution

    ########
    # Data #
    ########

    x = np.tile(x0, (n * m, 1))

    for i in range(n):
        start = i * m
        stop = (i + 1) * m
        x[start:stop, i] = np.linspace(xmin[i], xmax[i], m)

    return x


def create_batches(n: int, m: int) -> list[list[int]]:
    """Create n batches containing m examples each.

    Given an array x of shape (n * m, -1), this method
    returns a list of list in which each list are the
    indices of x for each batch.

    Args:
        n: int
            Number of batches.

        m: int
            Number of examples per batch.

    Example usage:

        n=3
        m=5
        x = np.arange(n*m,)

        batches = create_batches(n, m)

        for batch in batches:
            print(x[batch])

    This method is meant as a support function for
    the sensitivity profilers. It helps collect the
    indices associated with the data for each curve
    in the curve.

    Args:
        n: int, optional
            Number of batches

        n: int, optional
            Number of examples per batch

    Returns:
        list
            List of row indices corresponding to one
            grid permutation.

    """
    batches = []

    for i in range(n):
        start = i * m
        stop = (i + 1) * m
        batch = list(range(start, stop))
        batches.append(batch)

    return batches


def make_figure(
    N: int,
    num_x_ticks: int = 3,
    num_y_ticks: int = 3,
    tick_style: dict | None = None,
    xmin: float | None = None,
    xmax: float | None = None,
    ymin: float | None = None,
    ymax: float | None = None,
) -> bq.Figure:
    """Create initial figure for profiler trait (data will be replaced)."""
    if tick_style is None:
        tick_style = {"font-size": 10}
    x = np.array([0, 1])
    y = np.array([0, 1])
    x0 = np.array([0.5])
    y0 = np.array([0.5])
    xs = bq.LinearScale(min=xmin, max=xmax)
    ys = bq.LinearScale(min=ymin, max=ymax)
    marks = []
    for k in range(N):
        line = bq.Lines(
            x=x,
            y=y,
            scales={"x": xs, "y": ys},
            colors=[LINE_COLOR],
            stroke_width=LINE_WIDTH,
            line_style=LINE_STYLE[k],
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
) -> W.GridspecLayout:
    """Create grid layout of specified width and height."""
    if width:
        fig_width = f"{width / n_x - BETWEEN_SPACE}px"
    if height:
        fig_height = f"{height / n_y - BETWEEN_SPACE}px"
    grid = W.GridspecLayout(n_y, n_x)
    for j in range(n_x):
        for i in range(n_y):
            grid[i, j] = make_figure(N)
            if width:
                grid[i, j].layout.width = fig_width
            if height:
                grid[i, j].layout.height = fig_height
    return grid

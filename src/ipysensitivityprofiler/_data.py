"""Data.

Module in charge of data structure from which sensitivity profiles are
plotted.
"""

from typing import Any, Callable, List

import numpy as np
import traitlets as T
import traittypes as TT


class Data(T.HasTraits):
    """Automatically evaluate outputs whenever inputs change."""

    xlabels: List[str] = T.List(allow_none=False)  # type: ignore [assignment]
    ylabels: List[str] = T.List(allow_none=False)  # type: ignore [assignment]
    predict: Callable = T.Callable(allow_none=False)  # type: ignore [assignment]

    x: np.ndarray = TT.Array(allow_none=False)
    y: np.ndarray = TT.Array()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(self, **kwargs)

        def update(change: T.Bunch) -> None:
            self.y = self.predict(self.x)

        self.observe(update, "predict")

        T.dlink((self, "x"), (self, "y"), self.predict)

    @property
    def n_x(self) -> int:
        """Number of inputs."""
        return len(self.xlabels)

    @property
    def n_y(self) -> int:
        """Number of outputs."""
        return len(self.ylabels)

    @property
    def N(self) -> int:
        """Number of models (i.e. number of lines on plot)."""
        return self.y.shape[2]

    @T.validate("x")
    def _validate_x(self, proposal: T.Bunch) -> np.ndarray:
        x = proposal.value
        if (
            x.ndim != 2  # noqa: PLR2004
            or x.shape[1] != self.n_x
            or x.dtype != np.float64
        ):
            return x.astype(np.float64).reshape(-1, self.n_x)  # require shape (m, n_x)
        assert x.shape[1] == self.n_x
        assert x.dtype == np.float64
        return x

    @T.validate("y")
    def _validate_y(self, proposal: T.Bunch) -> np.ndarray:
        y = proposal.value
        assert y.ndim == 3  # noqa: PLR2004 # require shape (m, n_y, N)
        assert y.shape[1] == self.n_y
        assert y.dtype == np.float64
        return y
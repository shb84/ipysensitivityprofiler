from collections.abc import Callable
from typing import Any

import numpy as np
import traitlets as T
import traittypes as TT
from numpy.typing import NDArray


class Data(T.HasTraits):
    """Automatically evaluate outputs whenever inputs change.

    This class is in charge of managing source data and calling user
    prediction models as needed.
    """

    xlabels: list[str] = T.List(allow_none=False)  # type: ignore [assignment]
    ylabels: list[str] = T.List(allow_none=False)  # type: ignore [assignment]
    predict: Callable = T.Callable(
        allow_none=False,
        help="Callback that calls user provided models to update data as needed.",
    )  # type: ignore [assignment]

    x: NDArray = TT.Array(allow_none=False)
    y: NDArray = TT.Array()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(self, **kwargs)

        def update(_change: T.Bunch) -> None:
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
    def N(self) -> int:  # ruff: ignore[invalid-function-name]  (public API name kept for backwards compat)
        """Number of models (i.e. number of lines on plot)."""
        return self.y.shape[2]

    @T.validate("x")
    def _validate_x(self, proposal: T.Bunch) -> NDArray:
        x = proposal.value
        if x.ndim != 2 or x.shape[1] != self.n_x or x.dtype != np.float64:
            return x.astype(np.float64).reshape(-1, self.n_x)  # require shape (m, n_x)
        assert x.shape[1] == self.n_x
        assert x.dtype == np.float64
        return x

    @T.validate("y")
    def _validate_y(self, proposal: T.Bunch) -> NDArray:
        y = proposal.value
        assert y.ndim == 3  # require shape (m, n_y, N)
        assert y.shape[1] == self.n_y
        assert y.dtype == np.float64
        return y

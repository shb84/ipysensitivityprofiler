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

    Construction deliberately does *not* evaluate: `y` starts as a
    placeholder of the right shape and the models run only once
    :py:meth:`refresh` is called. See :py:meth:`refresh`.
    """

    xlabels: list[str] = T.List(allow_none=False)  # type: ignore [assignment]
    ylabels: list[str] = T.List(allow_none=False)  # type: ignore [assignment]
    n_models: int = T.Int(
        1, help="Number of models, i.e. the number of curves in each figure."
    )  # type: ignore [assignment]
    predict: Callable = T.Callable(
        allow_none=False,
        help="Callback that calls user provided models to update data as needed.",
    )  # type: ignore [assignment]

    x: NDArray = TT.Array(allow_none=False)
    y: NDArray = TT.Array()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # NOTE: a plain observer rather than a `T.dlink`. A dlink fires the moment it
        # is registered, which used to run the user's models here -- before `View` had
        # created a single figure widget, so a slow model rendered a blank cell (#6).
        # An observer defers that first evaluation to `refresh()`, which `profiler()`
        # calls once the whole widget tree exists. Reading `self.predict` inside the
        # callback (rather than binding it now) also keeps the old dlink lambda's
        # property: `predict` is itself a reassignable trait, and the callback must
        # always use whatever model is current, not the one set at construction.
        self.observe(self._recompute, ["x", "predict"])

    def refresh(self) -> None:
        """Evaluate the models over the current grid."""
        self.y = self.predict(self.x)

    def _recompute(self, _change: T.Bunch) -> None:
        self.refresh()

    @T.default("y")
    def _create_y(self) -> NDArray:
        # Placeholder, so that `N` -- and therefore the whole figure grid -- is
        # answerable before any model has run (#6).
        return np.zeros((self.x.shape[0], self.n_y, self.n_models))

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
            # require shape (m, n_x); asarray is a no-op when it already matches
            return np.asarray(x, dtype=np.float64).reshape(-1, self.n_x)
        assert x.shape[1] == self.n_x
        assert x.dtype == np.float64
        return x

    @T.validate("y")
    def _validate_y(self, proposal: T.Bunch) -> NDArray:
        y = proposal.value
        assert y.ndim == 3  # require shape (m, n_y, N)
        assert y.shape[1] == self.n_y
        # Fail here rather than as an opaque `zip(..., strict=True)` error inside
        # `View._update_figs`, which has one mark pair per model.
        assert y.shape[2] == self.n_models
        assert y.dtype == np.float64
        return y

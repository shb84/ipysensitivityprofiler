[![CI](https://github.com/shb84/ipysensitivityprofiler/actions/workflows/ci.yml/badge.svg)](https://github.com/shb84/ipysensitivityprofiler/actions/workflows/ci.yml)
[![Docs](https://github.com/shb84/ipysensitivityprofiler/actions/workflows/docs.yml/badge.svg)](https://shb84.github.io/ipysensitivityprofiler/)
[![PyPI version](https://badge.fury.io/py/ipysensitivityprofiler.svg)](https://pypi.org/project/ipysensitivityprofiler/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/shb84/ipysensitivityprofiler.git/main)

# ipysensitivityprofiler

Jupyter Widgets for visualizing local sensitivities of vectorized functions with
signature `y = f(x)` where `x, y` are arrays.

<div align="center">

![](https://github.com/shb84/ipysensitivityprofiler/raw/main/docs/pics/basic_usage.gif)

</div>

# Main Features

* Visualize multiple outputs against multiple inputs interactively
* Overlay more than one model at once
* Download pictures of individual plots (by clicking on the red dot)

# Installation

    pip install ipysensitivityprofiler

# Example Usage

_See the [example notebooks](https://github.com/shb84/ipysensitivityprofiler/tree/main/notebooks),
or run them without installing anything on [binder](https://mybinder.org/v2/gh/shb84/ipysensitivityprofiler.git/main)._

Import the library and define one or more vectorized models:

    import numpy as np
    import ipysensitivityprofiler as isp

    def quadratic1(x):
        """y = x1**2 + x2**2 + x1*x2"""
        return np.prod(x, axis=1) + np.power(x, 2).sum(axis=1)

    def quadratic2(x):
        """y = 10 + x1**2 + x2**2 - 2 * x1*x2"""
        return 10 - 2 * np.prod(x, axis=1) + np.power(x, 2).sum(axis=1)

Then profile them:

    isp.profiler(
        models=[quadratic1, quadratic2],
        xmin=[0, 0],
        xmax=[2, 1],
        ymin=[0],
        ymax=[20],
        x0=[1.5, 0.75],
        resolution=10_000,
        xlabels=["x1", "x2"],
        ylabels=["y"],
    )

# Use Case

A local sensitivity profile is the trace of a function obtained by holding all
dimensions fixed but one. Profiling a model interactively is useful for **debugging
models** (spotting obviously wrong trends early), for **robust design** (seeing how
performance changes when the design is perturbed away from nominal), and for **model
comparison** (overlaying a high-fidelity model, a low-fidelity one, and ground truth
on the same plot to see where they disagree).

# Limitations

Models must be fast for interactivity: they must be able to evaluate thousands of
datapoints on the order of milliseconds. This is a non-issue for empirical regressions
(e.g. neural nets) or first-order physics-based models.

The other limitation is screen real estate. Beyond a certain number of inputs and
outputs, humans become overwhelmed and the screen runs out of room, so this library is
best suited for targeted studies on a subspace of a larger problem.

# Documentation

Documentation is available [here](https://shb84.github.io/ipysensitivityprofiler/)
(generated using [`sphinx`](https://www.sphinx-doc.org/en/master/)).

# Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for how to set up
the development environment (`pixi`) and run the QA pipeline.

# License

Distributed under the terms of the MIT License.

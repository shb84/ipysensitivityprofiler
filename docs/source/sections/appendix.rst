Audience
--------

The present library is intended for engineers who rely on modeling and simulation
to make engineering design decisions. For example, developing physics-based or
empirical models (e.g. neural net) to make predictions about some system of interest
or run optimization on it.

Use Cases
---------

**Debugging models**. The ability to quickly interrogate the model(s) and
get instantaneous feedback goes a long way in spotting obviously wrong trends early
on. This is especially helpful when developing physics-based models, before using them
for optimization or design decision-making. It's often easier to look at trends
to understand what is going on, rather than infer the issue from stack error messages.

**Robust design**. Upon convergence, the design team might be
interested in understanding how system performance would change if the design was
perturbed away from nominal. This could be the result of noise in the process, requirement
changes down the road, or operational uncertainty. Perturbing inputs allows
engineers to verify whether system outputs would stay within desired limits based on their model(s).

**Model comparison**. Taking advantage of the tool's ability to render multiple
models of the same thing on the same plot, this enables two or more models to be compared against
each other. For example, one model might be the high fidelity model, the other some low-fidelity
version, and perhaps the third is ground truth. Provided each model has the same signature, one
can very quickly observe where they disagree.

Limitations
-----------

Models must be fast for interactivity. Concretely, they must be
able to evaluate thousands of datapoints on the order of milliseconds. This is a
non-issue when the model at hand is some empirical regression (e.g. neural net) or even some first-order
physics-based model.

The other limitation is screen real estate. This library is helpful for understanding how multiple
responses and factors interact but, beyond a certain point, the number of inputs and outputs might
be so big that humans become overwhelmed with information and screen real estate runs out. Hence,
this library is best suited for targeted studies on a subspace of a larger problem.

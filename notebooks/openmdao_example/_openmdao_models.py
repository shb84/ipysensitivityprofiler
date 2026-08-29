"""OpenMDAO Sellar Problem.

REF: https://openmdao.org/newdocs/versions/latest/basic_user_guide/multidisciplinary_optimization/sellar.html

..note:

    It is important that all models be vectorized (like Dymos) in order to
    for sensitivity profilers to work efficiently.
"""

import numpy as np
import openmdao.api as om

###############
# Disciplines #
###############


class SellarDis1(om.ExplicitComponent):
    """Component containing Discipline 1 -- no derivatives version."""

    def initialize(self):
        self.options.declare("num_nodes", types=int, default=1)

    def setup(self):
        nn = self.options["num_nodes"]

        # Global Design Variable
        self.add_input("z1", val=np.zeros(nn))
        self.add_input("z2", val=np.zeros(nn))

        # Local Design Variable
        self.add_input("x", val=np.zeros(nn))

        # Coupling parameter
        self.add_input("y2", val=np.ones(nn))

        # Coupling output
        self.add_output("y1", val=np.ones(nn))

    def setup_partials(self):
        # Finite difference all partials.
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        """Evaluate the equation ``y1 = z1**2 + z2 + x1 - 0.2*y2``."""
        z1 = inputs["z1"]
        z2 = inputs["z2"]
        x1 = inputs["x"]
        y2 = inputs["y2"]

        outputs["y1"] = z1**2 + z2 + x1 - 0.2 * y2


class SellarDis2(om.ExplicitComponent):
    """Component containing Discipline 2 -- no derivatives version."""

    def initialize(self):
        self.options.declare("num_nodes", types=int, default=1)

    def setup(self):
        nn = self.options["num_nodes"]

        # Global Design Variable
        self.add_input("z1", val=np.zeros(nn))
        self.add_input("z2", val=np.zeros(nn))

        # Coupling parameter
        self.add_input("y1", val=np.ones(nn))

        # Coupling output
        self.add_output("y2", val=np.ones(nn))

    def setup_partials(self):
        # Finite difference all partials.
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        """Evaluate the equation ``y2 = y1**(.5) + z1 + z2``."""
        z1 = inputs["z1"]
        z2 = inputs["z2"]
        y1 = inputs["y1"]

        # Note: this may cause some issues. However, y1 is constrained to be
        # above 3.16, so lets just let it converge, and the optimizer will
        # throw it out
        # if y1.real < 0.0:
        #     y1 *= -1
        mask = y1.real < 0.0
        y1[mask] = -y1[mask]

        outputs["y2"] = y1**0.5 + z1 + z2


###############
# Connections #
###############


class SellarMDA(om.Group):
    """Group containing connected models w/ a root finding solver."""

    def initialize(self):
        self.options.declare("num_nodes", types=int, default=1)

    def setup(self):
        nn = self.options["num_nodes"]
        cycle = self.add_subsystem("cycle", om.Group(), promotes=["*"])
        cycle.add_subsystem(
            "d1",
            SellarDis1(num_nodes=nn),
            promotes_inputs=["x", "z1", "z2", "y2"],
            promotes_outputs=["y1"],
        )
        cycle.add_subsystem(
            "d2",
            SellarDis2(num_nodes=nn),
            promotes_inputs=["z1", "z2", "y1"],
            promotes_outputs=["y2"],
        )

        cycle.set_input_defaults("x", val=np.ones(nn))
        cycle.set_input_defaults("z1", val=np.ones(nn) * 5.0)
        cycle.set_input_defaults("z2", val=np.ones(nn) * 2.0)

        # Nonlinear Block Gauss Seidel is a gradient free solver
        cycle.nonlinear_solver = om.NonlinearBlockGS()

        self.add_subsystem(
            "obj_cmp",
            om.ExecComp(
                "obj = x**2 + z1 + y1 + exp(-y2)",
                x=np.zeros(nn),
                z1=np.zeros(nn),
                y1=np.zeros(nn),
                y2=np.zeros(nn),
                obj=np.zeros(nn),
            ),
            promotes=["x", "z1", "y1", "y2", "obj"],
        )
        self.add_subsystem(
            "con_cmp1",
            om.ExecComp("con1 = 3.16 - y1", y1=np.zeros(nn), con1=np.zeros(nn)),
            promotes=["con1", "y1"],
        )
        self.add_subsystem(
            "con_cmp2",
            om.ExecComp("con2 = y2 - 24.0", y2=np.zeros(nn), con2=np.zeros(nn)),
            promotes=["con2", "y2"],
        )

        # `x`, `z1` and `z2` are promoted both out of `cycle` and by `obj_cmp`,
        # which declares them as zeros. Without a default at this level the
        # promoted value is ambiguous and OpenMDAO refuses to set up the model.
        self.set_input_defaults("x", val=np.ones(nn))
        self.set_input_defaults("z1", val=np.ones(nn) * 5.0)
        self.set_input_defaults("z2", val=np.ones(nn) * 2.0)


class SellarView(om.Group):
    """Group containing connected models w/o a root finding solver.

    .. note:

        In order to observe local sensitivities, we need to be able
        to independently vary the inputs to each disipline, including
        coupling variables. Hence, we won't use a root finding solver.
        Instead, we will return the residuals. This can help a user
        understand local sensitivities around a root for example.
    """

    def initialize(self):
        self.options.declare("num_nodes", types=int, default=100)

    def setup(self):
        nn = self.options["num_nodes"]
        self.add_subsystem(
            "d1",
            SellarDis1(num_nodes=nn),
            promotes_inputs=["x", "z1", "z2", "y2"],
            promotes_outputs=[("y1", "y1_out")],
        )
        self.add_subsystem(
            "d2",
            SellarDis2(num_nodes=nn),
            promotes_inputs=["z1", "z2", "y1"],
            promotes_outputs=[("y2", "y2_out")],
        )

        self.set_input_defaults("x", val=np.ones(nn))
        self.set_input_defaults("y1", val=np.ones(nn))
        self.set_input_defaults("y2", val=np.ones(nn))
        self.set_input_defaults("z1", val=np.ones(nn) * 5.0)
        self.set_input_defaults("z2", val=np.ones(nn) * 2.0)

        self.add_subsystem(
            "res1",
            om.ExecComp(
                "Residual1 = y1_out - y1",
                Residual1=np.zeros(nn),
                y1_out=np.zeros(nn),
                y1=np.zeros(nn),
            ),
            promotes=["Residual1", "y1_out", "y1"],
        )
        self.add_subsystem(
            "res2",
            om.ExecComp(
                "Residual2 = y2_out - y2",
                Residual2=np.zeros(nn),
                y2_out=np.zeros(nn),
                y2=np.zeros(nn),
            ),
            promotes=["Residual2", "y2_out", "y2"],
        )
        self.add_subsystem(
            "obj_cmp",
            om.ExecComp(
                "obj = x**2 + z1 + y1 + exp(-y2)",
                x=np.zeros(nn),
                z1=np.zeros(nn),
                y1=np.zeros(nn),
                y2=np.zeros(nn),
                obj=np.zeros(nn),
            ),
            promotes=["x", "z1", "y1", "y2", "obj"],
        )
        self.add_subsystem(
            "con_cmp1",
            om.ExecComp("con1 = 3.16 - y1", y1=np.zeros(nn), con1=np.zeros(nn)),
            promotes=["con1", "y1"],
        )
        self.add_subsystem(
            "con_cmp2",
            om.ExecComp("con2 = y2 - 24.0", y2=np.zeros(nn), con2=np.zeros(nn)),
            promotes=["con2", "y2"],
        )

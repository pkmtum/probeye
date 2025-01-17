"""
              Linear model in time and space with three different sensors
----------------------------------------------------------------------------------------
                       ---> Additive model prediction error <---
----------------------------------------------------------------------------------------
The model equation is y(x,t) = a * x + b * t + c with a, b, c being the model parameters
while x and t represent position and time respectively. From the three model parameters
a and b are latent ones while c is a constant. Measurements are made at three different
positions (x-values) each of which is associated with an own zero-mean, uncorrelated
normal model error with the standard deviations to infer. This results in five latent
parameters (parameters to be inferred). The problem is approached with a maximum
likelihood estimation.
"""

# standard library imports
import unittest

# third party imports
import numpy as np

# local imports (problem definition)
from probeye.definition.inverse_problem import InverseProblem
from probeye.definition.forward_model import ForwardModelBase
from probeye.definition.sensor import Sensor
from probeye.definition.likelihood_model import GaussianLikelihoodModel

# local imports (testing related)
from tests.integration_tests.subroutines import run_inference_engines


class TestProblem(unittest.TestCase):
    def test_multiple_sensors(
        self,
        n_steps: int = 200,
        n_initial_steps: int = 100,
        n_walkers: int = 20,
        plot: bool = False,
        show_progress: bool = False,
        run_scipy: bool = True,
        run_emcee: bool = False,  # intentionally False for faster test-runs
        run_dynesty: bool = False,  # intentionally False for faster test-runs
    ):
        """
        Integration test for the problem described at the top of this file.

        Parameters
        ----------
        n_steps
            Number of steps (samples) to run. Note that the default number is rather low
            just so the test does not take too long.
        n_initial_steps
            Number of steps for initial (burn-in) sampling.
        n_walkers
            Number of walkers used by the estimator.
        plot
            If True, the data and the posterior distributions are plotted. This is
            deactivated by default, so that the test does not stop until the generated
            plots are closed.
        show_progress
            If True, progress-bars will be shown, if available.
        run_scipy
            If True, the problem is solved with scipy (maximum likelihood est).
            Otherwise, no maximum likelihood estimate is derived.
        run_emcee
            If True, the problem is solved with the emcee solver. Otherwise, the emcee
            solver will not be used.
        run_dynesty
            If True, the problem is solved with the dynesty solver. Otherwise, the
            dynesty solver will not be used.
        """

        # ============================================================================ #
        #                              Set numeric values                              #
        # ============================================================================ #

        # 'true' value of A, and its normal prior parameters
        a_true = 1.3
        mean_a = 1.0
        std_a = 1.0

        # 'true' value of B, and its normal prior parameters
        b_true = -1.0
        mean_b = -2.0
        std_b = 1.5

        # 'true' value of sd_S1, and its uniform prior parameters
        sd_s1_true = 0.2
        low_s1 = 0.0
        high_s1 = 0.7

        # 'true' value of sd_S2, and its uniform prior parameters
        sd_s2_true = 0.4
        low_s2 = 0.0
        high_s2 = 0.7

        # 'true' value of sd_S3, and its uniform prior parameters
        sd_s3_true = 0.6
        low_s3 = 0.0
        high_s3 = 0.7

        # define sensor positions
        pos_s1 = 0.2
        pos_s2 = 0.5
        pos_s3 = 1.0

        # define global constants
        sigma_m = 0.1
        c = 0.5

        # ============================================================================ #
        #                           Define the Forward Model                           #
        # ============================================================================ #

        class LinearModel(ForwardModelBase):
            def interface(self):
                self.parameters = ["a", "b", {"c": "const"}]
                self.input_sensors = Sensor("time")
                self.output_sensors = [
                    Sensor(
                        "y1", x=pos_s1, std_model="sigma_1", std_measurement="sigma_m"
                    ),
                    Sensor(
                        "y2", x=pos_s2, std_model="sigma_2", std_measurement="sigma_m"
                    ),
                    Sensor(
                        "y3", x=pos_s3, std_model="sigma_3", std_measurement="sigma_m"
                    ),
                ]

            def response(self, inp: dict) -> dict:
                t = inp["time"]
                a = inp["a"]
                b = inp["b"]
                const = inp["const"]
                response = dict()
                for os in self.output_sensors:
                    response[os.name] = a * os.x + b * t + const
                return response

        # ============================================================================ #
        #                         Define the Inference Problem                         #
        # ============================================================================ #

        # initialize the inverse problem with a useful name
        problem = InverseProblem("Linear model with three sensors")

        # add all parameters to the problem
        problem.add_parameter(
            "a",
            "model",
            prior=("normal", {"mean": mean_a, "std": std_a}),
            info="Slope of the graph in x",
            tex="$A$",
        )
        problem.add_parameter(
            "b",
            "model",
            prior=("normal", {"mean": mean_b, "std": std_b}),
            info="Slope of the graph in t",
            tex="$B$",
        )
        problem.add_parameter(
            "sigma_1",
            "likelihood",
            domain="(0, +oo)",
            prior=("uniform", {"low": low_s1, "high": high_s1}),
            info="Standard deviation, of zero-mean additive model error for S1",
            tex=r"$\sigma_1$",
        )
        problem.add_parameter(
            "sigma_2",
            "likelihood",
            domain="(0, +oo)",
            prior=("uniform", {"low": low_s2, "high": high_s2}),
            info="Standard deviation, of zero-mean additive model error for S2",
            tex=r"$\sigma_2$",
        )
        problem.add_parameter(
            "sigma_3",
            "likelihood",
            domain="(0, +oo)",
            prior=("uniform", {"low": low_s3, "high": high_s3}),
            info="Standard deviation, of zero-mean additive model error S3",
            tex=r"$\sigma_3$",
        )
        problem.add_parameter(
            "sigma_m",
            "likelihood",
            const=sigma_m,
            info="Standard deviation, of zero-mean additive measurement error",
        )
        problem.add_parameter(
            "c",
            "model",
            const=c,
            info="Known model constant of forward model",
        )

        # add the forward model to the problem
        linear_model = LinearModel("LinearModel")
        problem.add_forward_model(linear_model)

        # ============================================================================ #
        #                    Add test data to the Inference Problem                    #
        # ============================================================================ #

        # add the experimental data
        np.random.seed(1)
        sd_dict = {
            linear_model.output_sensors[0].name: sd_s1_true,
            linear_model.output_sensors[1].name: sd_s2_true,
            linear_model.output_sensors[2].name: sd_s3_true,
        }

        def generate_data(n_time_steps, idx=None):
            time_steps = np.linspace(0, 1, n_time_steps)
            inp = {"a": a_true, "b": b_true, "const": c, "time": time_steps}
            sensors = linear_model(inp)
            for key, val in sensors.items():
                sensors[key] = val + np.random.normal(
                    0.0, np.sqrt(sd_dict[key] ** 2 + sigma_m**2), size=n_time_steps
                )
            sensors[linear_model.input_sensor.name] = time_steps
            problem.add_experiment(
                f"TestSeries_{idx}", sensor_values=sensors, fwd_model_name="LinearModel"
            )

        for i, n_t in enumerate([101, 51]):
            generate_data(n_t, idx=i + 1)

        # ============================================================================ #
        #                           Add likelihood model(s)                            #
        # ============================================================================ #

        # add the likelihood models to the problem
        problem.add_likelihood_model(
            GaussianLikelihoodModel(
                experiment_name="TestSeries_1",
                prms_def=["sigma_1", "sigma_2", "sigma_3", "sigma_m"],
                additive_measurement_error=True,
            )
        )
        problem.add_likelihood_model(
            GaussianLikelihoodModel(
                experiment_name="TestSeries_2",
                prms_def=["sigma_1", "sigma_2", "sigma_3", "sigma_m"],
                additive_measurement_error=True,
            )
        )

        # give problem overview
        problem.info()

        # ============================================================================ #
        #                    Solve problem with inference engine(s)                    #
        # ============================================================================ #

        # this routine is imported from another script because it it used by all
        # integration tests in the same way
        true_values = {
            "a": a_true,
            "b": b_true,
            "sigma_1": sd_s1_true,
            "sigma_2": sd_s2_true,
            "sigma_3": sd_s3_true,
        }
        run_inference_engines(
            problem,
            true_values=true_values,
            n_steps=n_steps,
            n_initial_steps=n_initial_steps,
            n_walkers=n_walkers,
            plot=plot,
            show_progress=show_progress,
            run_scipy=run_scipy,
            run_emcee=run_emcee,
            run_dynesty=run_dynesty,
        )


if __name__ == "__main__":
    unittest.main()

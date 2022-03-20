# standard library imports
import unittest
import copy

# third party imports
import numpy as np

# local imports
from probeye.definition.sensor import Sensor
from probeye.inference.scipy.likelihood_models import ScipyLikelihoodBase
from probeye.inference.scipy.likelihood_models import (
    AdditiveUncorrelatedModelError,
    MultiplicativeUncorrelatedModelError,
)


class TestProblem(unittest.TestCase):
    def test_ScipyLikelihoodBase(self):
        # check the base class initialization and loglike-method
        scipy_likelihood_base = ScipyLikelihoodBase(
            "a", Sensor("y"), "Exp_1", {}, False, "x", "exp", "L1"
        )
        with self.assertRaises(NotImplementedError):
            scipy_likelihood_base.loglike({}, {})

    def test_AdditiveUncorrelatedModelError(self):

        # prepare the dummy problem experiments
        n_data_points_exp = 100
        dummy_data = np.linspace(-1, 1, n_data_points_exp)
        sensor_values = {"y": dummy_data}
        problem_experiments = {
            "Exp_1": {"forward_model": "FwdModel", "sensor_values": sensor_values},
            "Exp_2": {"forward_model": "FwdModel", "sensor_values": sensor_values},
        }
        n_data_points = len(problem_experiments) * n_data_points_exp

        # checks for additive_measurement_error=False
        like_model = AdditiveUncorrelatedModelError(
            prms_def=["std_model"],
            sensors=[Sensor("y")],
            experiment_names=["Exp_1", "Exp_2"],
            problem_experiments=problem_experiments,
            additive_measurement_error=False,
            correlation_variables="",
            correlation_model="exp",
            name="L1",
        )
        # the dummy-response is chosen identical to the dummy-data, resulting in zero
        # residuals; this allows a simple check if the computation works as expected
        std_model = 2.0
        dummy_response = dummy_data
        expected_ll = -n_data_points / 2 * np.log(2 * np.pi * std_model ** 2)
        model_response_dict = {
            "Exp_1": {"y": dummy_response},
            "Exp_2": {"y": dummy_response},
        }
        computed_ll = like_model.loglike(model_response_dict, {"std_model": std_model})
        self.assertAlmostEqual(computed_ll, expected_ll)

        # check now, if a negative std_model is handled correctly
        std_model = -2.0
        dummy_response = dummy_data
        expected_ll = -np.infty
        model_response_dict = {
            "Exp_1": {"y": dummy_response},
            "Exp_2": {"y": dummy_response},
        }
        computed_ll = like_model.loglike(model_response_dict, {"std_model": std_model})
        self.assertAlmostEqual(computed_ll, expected_ll)

        # checks for additive_measurement_error=True
        like_model = AdditiveUncorrelatedModelError(
            prms_def=["std_model"],
            sensors=[Sensor("y")],
            experiment_names=["Exp_1", "Exp_2"],
            problem_experiments=problem_experiments,
            additive_measurement_error=True,
            correlation_variables="",
            correlation_model="exp",
            name="L1",
        )
        # the dummy-response is chosen identical to the dummy-data, resulting in zero
        # residuals; this allows a simple check if the computation works as expected
        std_model = 2.0
        std_measurement = 2.0
        dummy_response = dummy_data
        std = np.sqrt(std_model ** 2 + std_measurement ** 2)
        expected_ll = -n_data_points / 2 * np.log(2 * np.pi * std ** 2)
        model_response_dict = {
            "Exp_1": {"y": dummy_response},
            "Exp_2": {"y": dummy_response},
        }
        computed_ll = like_model.loglike(
            model_response_dict,
            {"std_model": std_model, "std_measurement": std_measurement},
        )
        self.assertAlmostEqual(computed_ll, expected_ll)

        # check now, if a negative std_measurement is handled correctly
        std_model = 2.0
        std_measurement = -2.0
        dummy_response = dummy_data
        std = np.sqrt(std_model ** 2 + std_measurement ** 2)
        expected_ll = -np.infty
        model_response_dict = {
            "Exp_1": {"y": dummy_response},
            "Exp_2": {"y": dummy_response},
        }
        computed_ll = like_model.loglike(
            model_response_dict,
            {"std_model": std_model, "std_measurement": std_measurement},
        )
        self.assertAlmostEqual(computed_ll, expected_ll)

    def test_MultiplicativeUncorrelatedModelError(self):

        # prepare the dummy problem experiments
        n_data_points_exp = 100
        dummy_data = np.linspace(-1, 1, n_data_points_exp)
        sensor_values = {"y": dummy_data}
        problem_experiments = {
            "Exp_1": {"forward_model": "FwdModel", "sensor_values": sensor_values},
            "Exp_2": {"forward_model": "FwdModel", "sensor_values": sensor_values},
        }
        n_data_points = len(problem_experiments) * n_data_points_exp

        # checks for additive_measurement_error=False
        like_model = MultiplicativeUncorrelatedModelError(
            prms_def=["std_model"],
            sensors=[Sensor("y")],
            experiment_names=["Exp_1", "Exp_2"],
            problem_experiments=problem_experiments,
            additive_measurement_error=False,
            correlation_variables="",
            correlation_model="exp",
            name="L1",
        )
        # the dummy-response is chosen identical to the dummy-data, resulting in zero
        # residuals; this allows a simple check if the computation works as expected
        std_model = 2.0
        dummy_response = dummy_data
        dummy_response_total = np.concatenate(
            [dummy_data for _ in range(len(problem_experiments))]
        )
        expected_ll = -0.5 * (
            n_data_points * np.log(2.0 * np.pi)
            + np.sum(np.log(np.power(dummy_response_total * std_model, 2)))
        )
        model_response_dict = {
            "Exp_1": {"y": dummy_response},
            "Exp_2": {"y": dummy_response},
        }
        computed_ll = like_model.loglike(model_response_dict, {"std_model": std_model})
        self.assertAlmostEqual(computed_ll, expected_ll)


if __name__ == "__main__":
    unittest.main()

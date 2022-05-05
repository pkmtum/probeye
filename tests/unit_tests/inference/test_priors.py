# standard library imports
import unittest

# third party imports
from scipy import stats
import numpy as np

# local imports
from probeye.inference.priors import PriorNormal
from probeye.inference.priors import PriorMultivariateNormal
from probeye.inference.priors import PriorTruncnormal
from probeye.inference.priors import PriorLognormal
from probeye.inference.priors import PriorUniform
from probeye.inference.priors import PriorWeibull
from probeye.inference.priors import translate_prior


class TestProblem(unittest.TestCase):
    def test_prior_normal(self):
        prior_normal = PriorNormal("a", ["mean_a", "std_a"], "a_normal")
        # check the evaluation of the log-pdf
        prms = {"a": 1.0, "mean_a": 0.0, "std_a": 1.0}
        self.assertEqual(
            stats.norm.logpdf(prms["a"], prms["mean_a"], prms["std_a"]),
            prior_normal(prms, "logpdf"),
        )
        # check the sampling-method (samples are checked one by one)
        prms = {"mean_a": 0.0, "std_a": 1.0}
        prior_samples = prior_normal.generate_samples(prms, 10, seed=1)
        sp_samples = stats.norm.rvs(
            loc=prms["mean_a"], scale=prms["std_a"], size=10, random_state=1
        )
        for s1, s2 in zip(prior_samples, sp_samples):
            self.assertEqual(s1, s2)
        # test multivariate version
        prior_normal = PriorMultivariateNormal("a", ["mean_a", "std_a"], "a_normal")
        prms = {"mean_a": [0.0, 0.0], "cov_a": [1.0, 1.0]}
        sample = prior_normal(prms, method="rvs", use_ref_prm=False, size=10)
        self.assertEqual(len(sample), 10)
        # test requesting an invalid method
        with self.assertRaises(AttributeError):
            prior_normal(prms, method="invalid method")

    def test_prior_truncnormal(self):
        prior_truncnormal = PriorTruncnormal(
            "sigma", ["mean_sigma", "std_sigma"], "sigma_normal"
        )
        # check the evaluation of the log-pdf
        prms = {
            "sigma": 1.0,
            "mean_sigma": 0.0,
            "std_sigma": 1.0,
            "a_sigma": 0.0,
            "b_sigma": 5.0,
        }
        self.assertEqual(
            stats.truncnorm.logpdf(
                prms["sigma"],
                a=prms["a_sigma"],
                b=prms["b_sigma"],
                loc=prms["mean_sigma"],
                scale=prms["std_sigma"],
            ),
            prior_truncnormal(prms, "logpdf"),
        )
        # check the evaluation of the mean
        mean = prior_truncnormal(prms, method="mean", use_ref_prm=False)
        self.assertAlmostEqual(
            mean,
            stats.truncnorm.mean(
                prms["a_sigma"],
                prms["b_sigma"],
                loc=prms["mean_sigma"],
                scale=prms["std_sigma"],
            ),
        )
        # check the sampling-method (samples are checked one by one)
        prms = {"mean_sigma": 0.0, "std_sigma": 1.0, "a_sigma": 0.0, "b_sigma": 5.0}
        prior_samples = prior_truncnormal.generate_samples(prms, 10, seed=1)
        sp_samples = stats.truncnorm.rvs(
            a=prms["a_sigma"],
            b=prms["b_sigma"],
            loc=prms["mean_sigma"],
            scale=prms["std_sigma"],
            size=10,
            random_state=1,
        )
        for s1, s2 in zip(prior_samples, sp_samples):
            self.assertEqual(s1, s2)

    def test_prior_lognormal(self):
        prior_lognormal = PriorLognormal("a", ["mean_a", "std_a"], "a_lognormal")
        # check the evaluation of the log-pdf
        prms = {"a": 2.0, "mean_a": 1.0, "std_a": 1.0}
        self.assertEqual(
            stats.lognorm.logpdf(
                prms["a"], scale=np.exp(prms["mean_a"]), s=prms["std_a"]
            ),
            prior_lognormal(prms, "logpdf"),
        )
        # check the evaluation of the mean
        mean = prior_lognormal(prms, method="mean", use_ref_prm=False)
        self.assertAlmostEqual(mean, stats.lognorm.mean(s=1.0, scale=np.exp(1.0)))
        # check the sampling-method (samples are checked one by one)
        prms = {"mean_a": 1.0, "std_a": 1.0}
        prior_samples = prior_lognormal.generate_samples(prms, 10, seed=1)
        sp_samples = stats.lognorm.rvs(
            1.0,  # this is scipy's shape parameter
            scale=np.exp(prms["mean_a"]),
            size=10,
            random_state=1,
        )
        for s1, s2 in zip(prior_samples, sp_samples):
            self.assertEqual(s1, s2)

    def test_prior_uniform(self):
        prior_uniform = PriorUniform("a", ["low_a", "high_a"], "a_uniform")
        # check the evaluation of the log-pdf
        prms = {"a": 0.5, "low_a": 0.0, "high_a": 1.0}
        self.assertEqual(
            stats.uniform.logpdf(prms["a"], prms["low_a"], prms["high_a"]),
            prior_uniform(prms, "logpdf"),
        )
        # check the sampling-method (samples are checked one by one)
        prms = {"low_a": 0.0, "high_a": 1.0}
        prior_samples = prior_uniform.generate_samples(prms, 10, seed=1)
        sp_samples = stats.uniform.rvs(
            loc=prms["low_a"],
            scale=prms["low_a"] + prms["high_a"],
            size=10,
            random_state=1,
        )
        for s1, s2 in zip(prior_samples, sp_samples):
            self.assertEqual(s1, s2)

    def test_prior_weibull(self):
        prior_weibull = PriorWeibull("a", ["loc_a", "scale_a", "shape_a"], "a_weibull")
        # check the evaluation of the log-pdf
        prms = {"a": 1.0, "loc_a": 1.0, "scale_a": 1.0, "shape_a": 2.0}
        self.assertEqual(
            stats.weibull_min.logpdf(
                prms["a"], prms["shape_a"], prms["loc_a"], prms["scale_a"]
            ),
            prior_weibull(prms, "logpdf"),
        )
        # check the sampling-method (samples are checked one by one)
        prms = {"loc_a": 1.0, "scale_a": 1.0, "shape_a": 2.0}
        prior_samples = prior_weibull.generate_samples(prms, 10, seed=1)
        sp_samples = stats.weibull_min.rvs(
            prms["shape_a"],
            loc=prms["loc_a"],
            scale=prms["scale_a"],
            size=10,
            random_state=1,
        )
        for s1, s2 in zip(prior_samples, sp_samples):
            self.assertEqual(s1, s2)
        # check the evaluation of the mean
        mean = prior_weibull(prms, method="mean", use_ref_prm=False)
        self.assertAlmostEqual(mean, stats.weibull_min.mean(2, loc=1, scale=1))

    def test_translate_prior(self):
        # check the invalid prior_classes type
        prior_uniform = PriorUniform("a", ["low_a", "high_a"], "a_uniform")
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            translate_prior(prior_uniform, prior_classes=[1, 2, 3])


if __name__ == "__main__":
    unittest.main()
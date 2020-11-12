from unittest import TestCase

import numpy as np

from diffprivlib.tools.quantiles import quantile
from diffprivlib.utils import PrivacyLeakWarning, BudgetError, DiffprivlibCompatibilityWarning


class TestQuantile(TestCase):
    def test_not_none(self):
        mech = quantile
        self.assertIsNotNone(mech)

    def test_no_params(self):
        a = np.array([1, 2, 3])
        with self.assertWarns(PrivacyLeakWarning):
            res = quantile(a, 0.5)
        self.assertIsNotNone(res)

    def test_no_epsilon(self):
        a = np.array([1, 2, 3])
        self.assertIsNotNone(quantile(a, 0.5, bounds=(0, 1)))

    def test_no_bounds(self):
        a = np.array([1, 2, 3])
        with self.assertWarns(PrivacyLeakWarning):
            res = quantile(a, 0.5, epsilon=1)
        self.assertIsNotNone(res)

    def test_bad_quantile(self):
        with self.assertRaises(ValueError):
            quantile([1], -0.5, epsilon=1, bounds=(0, 1))

        with self.assertRaises(ValueError):
            quantile([1], 1.5, epsilon=1, bounds=(0, 1))

    def test_bad_bounds(self):
        a = np.array([1, 2, 3])
        with self.assertRaises(ValueError):
            quantile(a, 0.5, epsilon=1, bounds=(0, -1))

    def test_missing_bounds(self):
        a = np.array([1, 2, 3])
        with self.assertWarns(PrivacyLeakWarning):
            res = quantile(a, 0.5, epsilon=1, bounds=None)
        self.assertIsNotNone(res)

    def test_large_epsilon(self):
        a = np.random.random(1000)
        res = float(np.quantile(a, 0.5))
        res_dp = quantile(a, 0.5, epsilon=5, bounds=(0, 1))

        self.assertAlmostEqual(res, res_dp, delta=0.01)

    def test_output_type(self):
        res = quantile([1, 2, 3], 0.5, bounds=(1, 3))
        self.assertTrue(isinstance(res, float))

    def test_simple(self):
        a = np.random.random(1000)
        for q in [0.1, 0.25, 0.5, 0.75, 0.9]:
            res = quantile(a, q, epsilon=5, bounds=(0, 1))
            self.assertAlmostEqual(res, q, delta=0.05)

    def test_normal(self):
        a = np.random.normal(size=2000)
        res = quantile(a, 0.5, epsilon=3, bounds=(-3, 3))
        self.assertAlmostEqual(res, 0, delta=0.1)

    def test_multiple_q(self):
        a = np.random.random(1000)
        q = [0.1, 0.25, 0.5, 0.75, 0.9]
        res = quantile(a, q, epsilon=5, bounds=(0, 1))

        self.assertEqual(len(q), len(res))
        self.assertTrue(np.isclose(res, q, atol=0.05).all())

    def test_axis(self):
        with self.assertWarns(DiffprivlibCompatibilityWarning):
            quantile([1], 0.5, epsilon=1, bounds=(0, 1), axis=0)

    def test_array_like(self):
        self.assertIsNotNone(quantile([1, 2, 3], 0.5, bounds=(1, 3)))
        self.assertIsNotNone(quantile((1, 2, 3), 0.5, bounds=(1, 3)))

    def test_clipped_output(self):
        a = np.random.random((10,))

        for i in range(100):
            self.assertTrue(0 <= quantile(a, 0.5, epsilon=1e-5, bounds=(0, 1)) <= 1)

    def test_nan(self):
        a = np.random.random((5, 5))
        a[2, 2] = np.nan

        res = quantile(a, 0.5, bounds=(0, 1))
        self.assertTrue(np.isnan(res))

    def test_accountant(self):
        from diffprivlib.accountant import BudgetAccountant
        acc = BudgetAccountant(1.5, 0)

        a = np.random.random((1000, 5))
        quantile(a, 0.5, epsilon=1, bounds=(0, 1), accountant=acc)
        self.assertEqual((1.0, 0), acc.total())

        with acc:
            with self.assertRaises(BudgetError):
                quantile(a, 0.5, epsilon=1, bounds=(0, 1))

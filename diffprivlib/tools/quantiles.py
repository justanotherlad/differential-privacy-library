# MIT License
#
# Copyright (C) IBM Corporation 2019
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
Quantile functions with differential privacy
"""
import warnings

import numpy as np

from diffprivlib.accountant import BudgetAccountant
from diffprivlib.mechanisms import Exponential
from diffprivlib.utils import warn_unused_args, PrivacyLeakWarning
from diffprivlib.validation import clip_to_bounds, check_bounds


def quantile(array, q, epsilon=1.0, bounds=None, keepdims=False, accountant=None, **unused_args):
    r"""
    Compute the differentially private quartile of the array.

    Returns the specified quartile with differential privacy.  The quartile is calculated over the flattened array.
    Differential privacy is achieved with the :class:`.Exponential` mechanism, using the method first proposed by
    Smith, 2011.

    Paper link: https://dl.acm.org/doi/pdf/10.1145/1993636.1993743

    Parameters
    ----------
    array : array_like
        Array containing numbers whose quartile is sought.  If `array` is not an array, a conversion is attempted.

    q : float or array-like
        Quartile or list of quartiles sought.  Each quartile must be in the unit interval [0, 1].

    epsilon : float, default: 1.0
        Privacy parameter :math:`\epsilon`.

    bounds : tuple, optional
        Bounds of the values of the array, of the form (min, max).

    keepdims : bool, optional
        If this is set to True, the axes which are reduced are left in the result as dimensions with size one.  With
        this option, the result will broadcast correctly against the input array.

        If the default value is passed, then `keepdims` will not be passed through to the `mean` method of sub-classes
        of `ndarray`, however any non-default value will be.  If the sub-class' method does not implement `keepdims` any
        exceptions will be raised.

    accountant : BudgetAccountant, optional
        Accountant to keep track of privacy budget.

    Returns
    -------
    m : ndarray
        Returns a new array containing the mean values.

    """
    warn_unused_args(unused_args)

    if bounds is None:
        warnings.warn("Bounds have not been specified and will be calculated on the data provided. This will "
                      "result in additional privacy leakage. To ensure differential privacy and no additional "
                      "privacy leakage, specify bounds for each dimension.", PrivacyLeakWarning)
        bounds = (np.min(array), np.max(array))

    bounds = check_bounds(bounds)

    qs = np.atleast_1d(q)

    if len(qs) > 1:
        return np.array([quantile(array, q_i, epsilon=epsilon / len(qs), bounds=bounds, keepdims=keepdims)
                         for q_i in qs])

    accountant = BudgetAccountant.load_default(accountant)
    accountant.check(epsilon, 0)

    q = qs[0]

    if not 0 <= q <= 1:
        raise ValueError("Quantile must be in [0, 1], got {}.".format(q))

    array = clip_to_bounds(np.ravel(array), bounds)

    k = array.size
    array = np.append(array, list(bounds))
    array.sort()

    interval_sizes = np.diff(array)

    if np.any(np.isnan(interval_sizes)):
        return np.nan

    mech = Exponential(epsilon=epsilon, sensitivity=1, utility=list(-np.abs(np.arange(0, k + 1) - q * k)),
                       measure=list(interval_sizes))
    idx = mech.randomise()

    accountant.spend(epsilon, 0)

    return mech._rng.random() * (array[idx+1] - array[idx]) + array[idx]

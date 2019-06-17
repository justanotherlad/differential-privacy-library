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
General utilities and tools for performing differentially private operations on data.
"""
import warnings
from numbers import Real
import numpy as np
from numpy.core import multiarray as mu
from numpy.core import umath as um

from diffprivlib.mechanisms import Laplace, LaplaceBoundedDomain
from diffprivlib.utils import PrivacyLeakWarning

_range = range


def mean(a, epsilon=1.0, range=None, axis=None, dtype=None, out=None, keepdims=np._NoValue):
    """
    Calculates the differentially private mean of a numpy array. Same functionality as numpy's mean.

    :param a: Numpy array for which the mean is sought.
    :param epsilon: Differential privacy parameter epsilon.
    :param range: Range of each dimension of the returned mean.
    :type range: float or array-like, same shape as np.mean(a, axis=axis)
    :param axis: See np.mean.
    :param dtype: See np.mean.
    :param out: See np.mean.
    :param keepdims: See np.mean.
    :return: Differentially private mean of `a`.
    """
    if isinstance(axis, tuple):
        temp_axis = axis
    elif axis is not None:
        try:
            temp_axis = tuple(axis)
        except TypeError:
            temp_axis = (axis,)
    else:
        temp_axis = tuple(_range(len(a.shape)))

    num_datapoints = 1
    for i in temp_axis:
        num_datapoints *= a.shape[i]

    actual_mean = np.mean(a, axis=axis, dtype=dtype, out=out, keepdims=keepdims)

    if range is None:
        warnings.warn("Range parameter hasn't been specified, so falling back to determining range from the data.\n"
                      "This will result in additional privacy leakage. To ensure differential privacy with no "
                      "additional privacy loss, specify `range` for each valued returned by np.mean().",
                      PrivacyLeakWarning)

        ranges = np.maximum(np.max(a, axis=axis) - np.min(a, axis=axis), 1e-5)
    elif isinstance(range, Real):
        ranges = np.ones_like(actual_mean) * range
    else:
        ranges = np.array(range)

    if not (ranges > 0).all():
        raise ValueError("Ranges must be specified for each value returned by np.mean(), and must be non-negative")
    if ranges.shape != actual_mean.shape:
        raise ValueError("Shape of range must be same as shape of np.mean")

    if isinstance(actual_mean, np.ndarray):
        # Extra np.array() a temporary fix for PyLint bug: https://github.com/PyCQA/pylint/issues/2747
        dp_mean = np.array(np.zeros_like(actual_mean))
        iterator = np.nditer(actual_mean, flags=['multi_index'])

        while not iterator.finished:
            dp_mech = Laplace().set_epsilon(epsilon).set_sensitivity(ranges[iterator.multi_index] / num_datapoints)

            dp_mean[iterator.multi_index] = dp_mech.randomise(float(iterator[0]))
            iterator.iternext()

        return dp_mean

    range = np.ravel(ranges)[0]
    dp_mech = Laplace().set_epsilon(epsilon).set_sensitivity(range / num_datapoints)

    return dp_mech.randomise(actual_mean)


def var(a, epsilon=1.0, range=None, axis=None, dtype=None, out=None, ddof=0, keepdims=np._NoValue):
    """
    Calculates the differentially private variance of a numpy array. Same functionality as numpy's var.

    :param a: Numpy array for which the variance is sought.
    :param epsilon: Differential privacy parameter epsilon.
    :param range: Range of each dimension of the returned variance.
    :type range: float or array-like, same shape as np.var(a, axis=axis)
    :param axis: See np.var.
    :param dtype: See np.var.
    :param out: See np.var.
    :param ddof: See np.var.
    :param keepdims: See np.var.
    :return:
    """
    if isinstance(axis, tuple):
        temp_axis = axis
    elif axis is not None:
        try:
            temp_axis = tuple(axis)
        except TypeError:
            temp_axis = (axis,)
    else:
        temp_axis = tuple(_range(len(a.shape)))

    num_datapoints = 1
    for i in temp_axis:
        num_datapoints *= a.shape[i]

    actual_var = np.var(a, axis=axis, dtype=dtype, out=out, ddof=ddof, keepdims=keepdims)

    if range is None:
        warnings.warn("Range parameter hasn't been specified, so falling back to determining range from the data.\n"
                      "This will result in additional privacy leakage. To ensure differential privacy with no "
                      "additional privacy loss, specify `range` for each valued returned by np.mean().",
                      PrivacyLeakWarning)

        ranges = np.maximum(np.max(a, axis=axis) - np.min(a, axis=axis), 1e-5)
    elif isinstance(range, Real):
        ranges = np.ones_like(actual_var) * range
    else:
        ranges = np.array(range)

    if not (ranges > 0).all():
        raise ValueError("Ranges must be specified for each value returned by np.var(), and must be non-negative")
    if ranges.shape != actual_var.shape:
        raise ValueError("Shape of range must be same as shape of np.var()")

    if isinstance(actual_var, np.ndarray):
        # Extra np.array() a temporary fix for PyLint bug: https://github.com/PyCQA/pylint/issues/2747
        dp_var = np.array(np.zeros_like(actual_var))
        iterator = np.nditer(actual_var, flags=['multi_index'])

        while not iterator.finished:
            dp_mech = LaplaceBoundedDomain().set_epsilon(epsilon).set_bounds(0, float("inf"))\
                .set_sensitivity((ranges[iterator.multi_index] / num_datapoints) ** 2 * (num_datapoints - 1))

            dp_var[iterator.multi_index] = dp_mech.randomise(float(iterator[0]))
            iterator.iternext()

        return dp_var

    range = np.ravel(ranges)[0]
    dp_mech = LaplaceBoundedDomain().set_epsilon(epsilon).set_bounds(0, float("inf")).\
        set_sensitivity(range ** 2 / num_datapoints)

    return dp_mech.randomise(actual_var)


def std(a, epsilon=1.0, range=None, axis=None, dtype=None, out=None, ddof=0, keepdims=np._NoValue):
    """
    Calculates the differentially private standard deviation of an array.

    :param a:
    :param epsilon:
    :param range:
    :param axis:
    :param dtype:
    :param out:
    :param ddof:
    :param keepdims:
    :return:
    """
    ret = var(a, epsilon=epsilon, range=range, axis=axis, dtype=dtype, out=out, ddof=ddof, keepdims=keepdims)

    if isinstance(ret, mu.ndarray):
        ret = um.sqrt(ret, out=ret)
    elif hasattr(ret, 'dtype'):
        ret = ret.dtype.type(um.sqrt(ret))
    else:
        ret = um.sqrt(ret)

    return ret

"""
here goes statistics functions/class for sampling distributions
"""

import numpy as np


def sample_from_gauss(mean, std, size):
    return np.random.normal(mean, std, size)


def sample_from_t(df, size):
    return np.random.standard_t(df, size)


def sample_from_triangular(left, mode, right, size):
    return np.random.triangular(left, mode, right, size)


def sample_from_exponential(scale, size):
    return np.random.exponential(scale, size)


def sample_from_custom_discrete(values, probabilities, size):
    return np.random.choice(values, size, p=probabilities)

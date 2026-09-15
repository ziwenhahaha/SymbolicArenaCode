import numpy as np

pi = np.pi


def div(x1, x2):
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return np.where(np.abs(x2) > 0.001, np.divide(x1, x2), 1.0)


def exp(x1):
    with np.errstate(over="ignore"):
        return np.where(x1 < 100, np.exp(x1), 0.0)


def log(x1):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(np.abs(x1) > 0.001, np.log(np.abs(x1)), 0.0)


def sqrt(x1):
    return np.sqrt(np.abs(x1))


def sin(x1):
    return np.sin(x1)


def cos(x1):
    return np.cos(x1)


def tan(x1):
    return np.tan(x1)


def abs(x1):
    return np.abs(x1)


def target(x1, x2, x3, x4, x5):
    return 0.13*sin(x3)-2.3

import numpy as np


# Source relation: Hubble law v = H0 * D.
# This historical dataset is noisy; the formula is the literature reference.
H0 = 73.3


def target(D):
    distance_mpc = np.asarray(D, dtype=float)
    return H0 * distance_mpc

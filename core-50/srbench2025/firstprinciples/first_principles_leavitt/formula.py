import numpy as np


# Source form: SRBench 2025 first-principles notebook.
# Linear period-luminosity relation on log10(P), with constants matched to the
# benchmark's extracted series.
ALPHA = -2.084
DELTA = 15.65


def target(logP):
    log_period = np.asarray(logP, dtype=float)
    return ALPHA * log_period + DELTA

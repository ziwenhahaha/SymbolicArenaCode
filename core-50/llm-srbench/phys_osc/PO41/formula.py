# ===== GROUND TRUTH REFERENCE =====
# NOTE: This ground truth serves as a reference answer for symbolic regression tasks
# This expression is NOT the original function used to generate the training data
# It is provided solely for evaluation and comparison of large model outputs
# DO NOT use this expression as the basis for data generation

def dv_dt(x, t, v):
    mu = 0.3254156367450257
    omega0 = 0.3333333333333333
    return -mu*(1 - x**2)*v - omega0**2*x*np.exp(-np.abs(x))

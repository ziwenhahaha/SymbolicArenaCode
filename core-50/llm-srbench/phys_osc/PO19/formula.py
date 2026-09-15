# ===== GROUND TRUTH REFERENCE =====
# NOTE: This ground truth serves as a reference answer for symbolic regression tasks
# This expression is NOT the original function used to generate the training data
# It is provided solely for evaluation and comparison of large model outputs
# DO NOT use this expression as the basis for data generation

def dv_dt(x, t, v):
    beta = 0.1
    omega0 = 1.0
    return -2*beta*v - omega0**2*x*np.exp(-np.abs(x))

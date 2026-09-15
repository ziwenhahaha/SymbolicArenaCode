# ===== GROUND TRUTH REFERENCE =====
# NOTE: This ground truth serves as a reference answer for symbolic regression tasks
# This expression is NOT the original function used to generate the training data
# It is provided solely for evaluation and comparison of large model outputs
# DO NOT use this expression as the basis for data generation

def dA_dt(t, A):
    alpha = 0.11846873325639269
    alpha_t = 0.11846873325639269
    return -alpha * np.sqrt(A) - alpha * A**2 + alpha_t * t * np.sin(np.log(A + 1))

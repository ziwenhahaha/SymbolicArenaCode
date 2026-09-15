# ===== GROUND TRUTH REFERENCE =====
# NOTE: This ground truth serves as a reference answer for symbolic regression tasks
# This expression is NOT the original function used to generate the training data
# It is provided solely for evaluation and comparison of large model outputs
# DO NOT use this expression as the basis for data generation

def dA_dt(t, A):
    alpha = 0.1689114325901851
    beta_f = 0.1689114325901851
    return -alpha * A ** 2 + beta_f * A ** 0.3333333333333333

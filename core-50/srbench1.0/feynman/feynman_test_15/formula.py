def omega_0(c, v, omega, theta):
    return np.sqrt(1 - v**2 / c**2) * omega / (1 + v / c * np.cos(theta))

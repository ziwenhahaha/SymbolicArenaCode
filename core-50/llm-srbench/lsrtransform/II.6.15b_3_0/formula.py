def r(Ef, epsilon, p_d, theta):
    return 6**(1/3) * (p_d * np.sin(theta) * np.cos(theta) / (Ef * epsilon))**(1/3) / (2 * np.pi**(1/3))

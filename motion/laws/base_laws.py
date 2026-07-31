import numpy as np


def _cycloidal(tau):
    two_pi = 2 * np.pi
    x = tau - np.sin(two_pi * tau) / two_pi
    dx = 1 - np.cos(two_pi * tau)
    ddx = two_pi * np.sin(two_pi * tau)
    dddx = (two_pi**2) * np.cos(two_pi * tau)
    return x, dx, ddx, dddx, "cicloidale"


def _poly_345(tau):
    x = 10*tau**3 - 15*tau**4 + 6*tau**5
    dx = 30*tau**2 - 60*tau**3 + 30*tau**4
    ddx = 60*tau - 180*tau**2 + 120*tau**3
    dddx = 60 - 360*tau + 360*tau**2
    return x, dx, ddx, dddx, "3-4-5"


def _poly_4567(tau):
    x = 35*tau**4 - 84*tau**5 + 70*tau**6 - 20*tau**7
    dx = 140*tau**3 - 420*tau**4 + 420*tau**5 - 140*tau**6
    ddx = 420*tau**2 - 1680*tau**3 + 2100*tau**4 - 840*tau**5
    dddx = 840*tau - 5040*tau**2 + 8400*tau**3 - 4200*tau**4
    return x, dx, ddx, dddx, "S-curve"


def _trapezoidal(tau, lam=0.25):
    x = np.zeros_like(tau)
    dx = np.zeros_like(tau)
    ddx = np.zeros_like(tau)
    dddx = np.zeros_like(tau)

    vmax = 1.0 / (1.0 - lam)
    acc = vmax / lam

    m1 = tau < lam
    m2 = (tau >= lam) & (tau <= 1.0 - lam)
    m3 = tau > 1.0 - lam

    x[m1] = 0.5 * acc * tau[m1]**2
    dx[m1] = acc * tau[m1]
    ddx[m1] = acc

    x_lam = 0.5 * acc * lam**2

    x[m2] = x_lam + vmax * (tau[m2] - lam)
    dx[m2] = vmax
    ddx[m2] = 0

    x[m3] = 1 - 0.5 * acc * (1 - tau[m3])**2
    dx[m3] = acc * (1 - tau[m3])
    ddx[m3] = -acc

    return x, dx, ddx, dddx, "trapezoidale"

def _trapezoidal_generalized(tau, params=None):
    import numpy as np

    # =========================
    # PARAMETRI
    # =========================
    default_profile = [10, 20, 10, 0, 10, 20, 10]
    if params is None:
        profile = default_profile
    else:
        profile = params.get("profile", params.get("proportions", default_profile))

    profile = np.array(profile, dtype=float)

    if len(profile) != 7 or profile.sum() == 0:
        profile = np.array(default_profile, dtype=float)

    # normalizza a [0..1]
    profile = profile / profile.sum()

    # breakpoint
    b = np.concatenate(([0.0], np.cumsum(profile)))

    # =========================
    # JERK
    # =========================
    jerk_pattern = np.array([1, 0, -1, 0, -1, 0, 1], dtype=float)

    j = np.zeros_like(tau)

    for i in range(7):
        mask = (tau >= b[i]) & (tau < b[i+1])
        j[mask] = jerk_pattern[i]

    # includi ultimo punto
    j[tau == 1.0] = 0.0

    # =========================
    # INTEGRAZIONE
    # =========================
    dt = tau[1] - tau[0]

    a = np.zeros_like(tau)
    v = np.zeros_like(tau)
    x = np.zeros_like(tau)

    for i in range(1, len(tau)):
        a[i] = a[i-1] + j[i-1] * dt
        v[i] = v[i-1] + a[i-1] * dt
        x[i] = x[i-1] + v[i-1] * dt

    # =========================
    # NORMALIZZAZIONE
    # =========================

    # posizione → 0..1
    if x[-1] != 0:
        x = x / x[-1]

    # velocità → scala coerente
    vmax = np.max(np.abs(v))
    if vmax > 0:
        v = v / vmax

    # accelerazione → scala coerente
    amax = np.max(np.abs(a))
    if amax > 0:
        a = a / amax

    # jerk → già normalizzato (±1)

    return x, v, a, j, "trapezoidale_generalizzata"

def _dwell(tau):
    x = np.zeros_like(tau)
    dx = np.zeros_like(tau)
    ddx = np.zeros_like(tau)
    dddx = np.zeros_like(tau)
    return x, dx, ddx, dddx, "sosta"

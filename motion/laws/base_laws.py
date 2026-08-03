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


def _trapezoidal(tau, params=None):
    import numpy as np
    default_profile = [10, 20, 10, 0, 10, 20, 10]
    if params is None:
        profile = default_profile
    else:
        profile = params.get("profile", params.get("proportions", default_profile))
    profile = np.array(profile, dtype=float)
    if len(profile) != 7 or profile.sum() == 0:
        profile = np.array(default_profile, dtype=float)
    profile = profile / profile.sum()
    b = np.concatenate(([0.0], np.cumsum(profile)))

    jerk_pattern = np.array([1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 1.0], dtype=float)
    j = np.zeros_like(tau)
    for i in range(7):
        if i == 6:
            mask = (tau >= b[i]) & (tau <= b[i+1])
        else:
            mask = (tau >= b[i]) & (tau < b[i+1])
        j[mask] = jerk_pattern[i]

    dt = tau[1] - tau[0] if len(tau) > 1 else 1.0
    a = np.zeros_like(tau)
    v = np.zeros_like(tau)
    x = np.zeros_like(tau)
    for i in range(1, len(tau)):
        a[i] = a[i-1] + j[i-1] * dt
        v[i] = v[i-1] + a[i-1] * dt
        x[i] = x[i-1] + v[i-1] * dt

    v[-1] = 0.0
    a[-1] = 0.0
    a[0] = 0.0

    if x[-1] != 0:
        x = x / x[-1]
    vmax = np.max(np.abs(v))
    if vmax > 0:
        v = v / vmax
    amax = np.max(np.abs(a))
    if amax > 0:
        a = a / amax

    return x, v, a, j, "trapezoidale"


def _trapezoidal_generalized(tau, params=None):
    import numpy as np

    try:
        from scipy.integrate import cumulative_trapezoid
    except ImportError:
        cumulative_trapezoid = None

    default_profile = [10, 20, 10, 0, 10, 20, 10]

    if params is None:
        profile = default_profile
    else:
        profile = params.get(
            "profile",
            params.get("proportions", default_profile)
        )

    profile = np.array(profile, dtype=float)

    if len(profile) != 7 or profile.sum() == 0:
        profile = np.array(default_profile, dtype=float)

    profile = profile / profile.sum()

    b = np.concatenate(([0.0], np.cumsum(profile)))

    j = np.zeros_like(tau, dtype=float)

    # ------------------------------------------------------------------
    # Normalized jerk definition
    # ------------------------------------------------------------------

    for i in range(7):

        if i == 6:
            mask = (tau >= b[i]) & (tau <= b[i + 1])
        else:
            mask = (tau >= b[i]) & (tau < b[i + 1])

        dur = b[i + 1] - b[i]

        if dur > 0:
            tau_local = (tau[mask] - b[i]) / dur
        else:
            tau_local = np.zeros_like(tau[mask])

        if i == 0:
            # 0 -> +Amax
            j[mask] = np.cos(np.pi * tau_local / 2)

        elif i == 1:
            # +Amax plateau
            j[mask] = 0.0

        elif i == 2:
            # +Amax -> 0
            j[mask] = -np.sin(np.pi * tau_local / 2)

        elif i == 3:
            # constant velocity
            j[mask] = 0.0

        elif i == 4:
            # 0 -> -Amax
            j[mask] = -np.cos(np.pi * tau_local / 2)

        elif i == 5:
            # -Amax plateau
            j[mask] = 0.0

        elif i == 6:
            # -Amax -> 0
            j[mask] = np.sin(np.pi * tau_local / 2)

    # ------------------------------------------------------------------
    # Integration
    # ------------------------------------------------------------------

    if len(tau) < 2:
        return (
            np.array([0.0]),
            np.array([0.0]),
            np.array([0.0]),
            np.array([0.0]),
            "trapezoidale_generalizzata",
        )

    if cumulative_trapezoid is not None:
        a = cumulative_trapezoid(j, tau, initial=0.0)
        v = cumulative_trapezoid(a, tau, initial=0.0)
        x = cumulative_trapezoid(v, tau, initial=0.0)
    else:
        # fallback if scipy unavailable
        dt = tau[1] - tau[0]

        a = np.zeros_like(tau)
        v = np.zeros_like(tau)
        x = np.zeros_like(tau)

        for k in range(1, len(tau)):
            a[k] = a[k - 1] + 0.5 * (j[k - 1] + j[k]) * dt

        for k in range(1, len(tau)):
            v[k] = v[k - 1] + 0.5 * (a[k - 1] + a[k]) * dt

        for k in range(1, len(tau)):
            x[k] = x[k - 1] + 0.5 * (v[k - 1] + v[k]) * dt

    # ------------------------------------------------------------------
    # Remove tiny numerical drift without introducing discontinuities
    # ------------------------------------------------------------------

    a -= np.linspace(0.0, a[-1], len(a))
    v -= np.linspace(0.0, v[-1], len(v))

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    if abs(x[-1]) > 1e-12:
        #x = x / x[-1]
        scale = x[-1]

        x /= scale
        v /= scale
        a /= scale
        j /= scale

    #vmax = np.max(np.abs(v))
    #if vmax > 1e-12:
    #    v = v / vmax

    #amax = np.max(np.abs(a))
    #if amax > 1e-12:
    #    a = a / amax

    #jmax = np.max(np.abs(j))
    #if jmax > 1e-12:
    #    j = j / jmax

    return x, v, a, j, "trapezoidale_generalizzata"

def _dwell(tau):
    x = np.zeros_like(tau)
    dx = np.zeros_like(tau)
    ddx = np.zeros_like(tau)
    dddx = np.zeros_like(tau)
    return x, dx, ddx, dddx, "sosta"

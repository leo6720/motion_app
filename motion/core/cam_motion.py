import numpy as np
from motion.laws.dispatcher import get_law

def compute_cam_motion(segments, n_points=1000):

    t_all, s_all, v_all, a_all, j_all = [], [], [], [], []

    t_offset = 0.0
    s_current = 0.0

    for seg in segments:

        tau = np.linspace(0.0, 1.0, n_points)

        x, dx, ddx, dddx, _ = get_law(seg.law, tau, seg.params)

        T = seg.duration
        dS = seg.stroke

        s = s_current + dS * x
        v = (dS / T) * dx
        a = (dS / T**2) * ddx
        j = (dS / T**3) * dddx

        t = tau * T + t_offset

        t_all.append(t)
        s_all.append(s)
        v_all.append(v)
        a_all.append(a)
        j_all.append(j)

        t_offset = t[-1]
        s_current = s[-1]

    return (
        np.concatenate(t_all),
        np.concatenate(s_all),
        np.concatenate(v_all),
        np.concatenate(a_all),
        np.concatenate(j_all)
    )

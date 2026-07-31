from .base_laws import _cycloidal, _poly_345, _poly_4567, _trapezoidal, _dwell, _trapezoidal_generalized

def get_law(law, tau, params=None):
    law = law.strip().lower()

    if law in ("cicloidale", "cycloidal"):
        return _cycloidal(tau)
    elif law in ("polinomiale 3-4-5", "poly_345"):
        return _poly_345(tau)
    elif law in ("s-curve 4-5-6-7", "poly_4567"):
        return _poly_4567(tau)
    elif law in ("trapezoidale", "trapezoidal"):
        return _trapezoidal(tau)
    elif law in ("triangolare", "triangular"):
        return _trapezoidal(tau, 0.5)
    elif law in ("trap_gen", "trapezoidal_generalized"):
        return _trapezoidal_generalized(tau, params)
    elif law in ("sosta", "dwell"):
        return _dwell(tau)
    else:
        raise ValueError(f"Legge non riconosciuta: {law}")

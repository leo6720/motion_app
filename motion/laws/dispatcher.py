from .base_laws import _cycloidal, _poly_345, _poly_4567, _trapezoidal, _dwell, _trapezoidal_generalized

def get_law(law, tau, params=None):
    law = law.lower()

    if law in ("cicloidale", "cycloidal"):
        return _cycloidal(tau)
    elif law in ("polinomiale 3-4-5", "poly_345"):
        return _poly_345(tau)
    elif law == "s-curve 4-5-6-7":
        return _poly_4567(tau)
    elif law == "trapezoidale":
        return _trapezoidal(tau)
    elif law == "triangolare":
        return _trapezoidal(tau, 0.5)
    elif law == "trap_gen":
        return _trapezoidal_generalized(tau, params)
    elif law in ("sosta", "dwell"):
        return _dwell(tau)
    else:
        raise ValueError(f"Legge non riconosciuta: {law}")

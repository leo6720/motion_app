def plot_motion_result(result, axes):
    """
    Disegna posizione, velocità, accelerazione e jerk su 4 assi Matplotlib.

    axes: array/lista di 4 assi.
    """

    labels = [
        ("Posizione", result.s, "s"),
        ("Velocità", result.v, "v"),
        ("Accelerazione", result.a, "a"),
        ("Jerk", result.j, "j"),
    ]

    for ax, (title, y, ylabel) in zip(axes, labels):
        ax.clear()
        ax.plot(result.t, y)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(True)

    axes[-1].set_xlabel("Tempo [s]")

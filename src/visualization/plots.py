import matplotlib.pyplot as plt


def plot_objective_history(history, title="", out_path=None, show=False):
    #Plot nilai objective function terhadap iterasi utnk HC dan SA
    fig, ax = plt.subplots(figsize=(8, 4.5))
    iterations = range(len(history))

    ax.plot(iterations, history, color="#1f77b4", lw=1.5, label="Objective value")
    ax.set_xlabel("Iterasi")
    ax.set_ylabel("Objective Value")
    ax.set_title(title or "Objective Value terhadap Iterasi")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best")
    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return fig


def plot_ga_history(best_history, avg_history, title="", out_path=None, show=False):
    #Plot nilai objective maksimum dan rata-rata populasi per generasi GA
    fig, ax = plt.subplots(figsize=(8, 4.5))
    generations = range(len(best_history))

    ax.plot(generations, best_history, color="#1f77b4", lw=1.8, label="Max (Best)")
    ax.plot(generations, avg_history, color="#ff7f0e", lw=1.5, linestyle="--", label="Average")
    ax.set_xlabel("Generasi (Iterasi)")
    ax.set_ylabel("Objective Value")
    ax.set_title(title or "Genetic Algorithm - Objective Value per Generasi")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best")
    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return fig


def plot_sa_acceptance(prob_history, title="", out_path=None, show=False):
    #Plot probabilitas penerimaan exp terhadap iterasi SA
    fig, ax = plt.subplots(figsize=(8, 4.5))
    iterations = range(len(prob_history))

    ax.plot(
        iterations,
        prob_history,
        color="#9467bd",
        lw=0.8,
        alpha=0.8,
        label=r"$e^{\Delta E / T}$",
    )
    ax.set_xlabel("Iterasi")
    ax.set_ylabel(r"Acceptance Probability ($e^{\Delta E / T}$)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(title or r"Simulated Annealing - $e^{\Delta E / T}$ terhadap Iterasi")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best")
    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return fig


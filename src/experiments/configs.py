"""Konfigurasi eksperimen."""

DATASET = "data/fixed_packages.json"
FILL_RATIO = 0.7
SEEDS = [0, 1, 2]

# Parameter tiap varian Hill-Climbing.
HC_PARAMS = {
    "hc_steepest": dict(n_neighbors=30, max_iter=1000),
    "hc_stochastic": dict(patience=100, max_iter=1000),
    "hc_sideways": dict(max_sideways=20, n_neighbors=30, max_iter=1000),
    "hc_random_restart": dict(max_restart=5, n_neighbors=30, max_iter_per_restart=500),
}
HC_ALGORITHMS = list(HC_PARAMS.keys())

# Simulated Annealing.
SA_PARAMS = dict(
    t0=100.0,
    cooling_rate=0.995,
    t_min=1e-3,
    max_iter=100_000,
    stuck_threshold=500,
)

# Genetic Algorithm:
#  - kontrol jumlah populasi  -> generations tetap, populasi divariasikan
#  - kontrol banyak iterasi   -> populasi tetap, generations divariasikan
GA_FIXED_GENERATIONS = 30
GA_POPULATIONS = [10, 30, 50]
GA_FIXED_POPULATION = 30
GA_GENERATIONS = [10, 30, 50]

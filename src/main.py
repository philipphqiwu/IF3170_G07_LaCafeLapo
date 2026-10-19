"""Entrypoint CLI untuk pencarian konfigurasi muatan truk.

Contoh pemakaian:
    python src/main.py --algorithm hc_steepest --dataset data/fixed_packages.json
    python src/main.py --algorithm ga --runs 3 --seed 42 --param population_size=50
"""

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from core import Evaluator, Truck, load_packages, load_truck, random_state
from core.models import State

ALGORITHM_CHOICES = [
    "hc_steepest",
    "hc_stochastic",
    "hc_sideways",
    "hc_random_restart",
    "sa",
    "ga",
]


@dataclass
class SearchResult:
    """Kontrak hasil pencarian yang akan dipakai semua algoritma."""

    algorithm: str
    initial_value: float
    final_value: float
    final_state: State
    history: list
    duration: float
    iterations: int = None
    initial_state: State = None
    extra: dict = field(default_factory=dict)


# --------------------------------------------------------------------- dummies


def _dummy_run(name, state0, evaluator, seed, **params):
    """Stub algoritma: kembalikan state awal tanpa pencarian.

    Placeholder sampai algoritma asli diimplementasikan. Menerima **params
    agar parameter tiap algoritma sudah bisa dilewatkan lewat CLI.
    """
    value = evaluator.evaluate(state0)
    return SearchResult(
        algorithm=name,
        initial_value=value,
        final_value=value,
        final_state=state0,
        history=[value],
        duration=0.0,
        iterations=0,
        initial_state=state0,
        extra={"params": params, "stub": True},
    )


def run_hc_steepest(state0, evaluator, seed, **params):
    return _dummy_run("hc_steepest", state0, evaluator, seed, **params)


def run_hc_stochastic(state0, evaluator, seed, **params):
    return _dummy_run("hc_stochastic", state0, evaluator, seed, **params)


def run_hc_sideways(state0, evaluator, seed, **params):
    return _dummy_run("hc_sideways", state0, evaluator, seed, **params)


def run_hc_random_restart(state0, evaluator, seed, **params):
    return _dummy_run("hc_random_restart", state0, evaluator, seed, **params)


def run_sa(state0, evaluator, seed, **params):
    from algorithms.simulated_annealing import simulated_annealing
    from core.neighbors import random_neighbor

    r = simulated_annealing(
        state0,
        objective=evaluator.evaluate,
        neighbor=random_neighbor,
        t0=params.get("t0", 100.0),
        cooling_rate=params.get("cooling_rate", 0.995),
        t_min=params.get("t_min", 1e-3),
        max_iter=params.get("max_iter", 100_000),
        stuck_threshold=params.get("stuck_threshold", 500),
        seed=seed,
    )
    return SearchResult(
        algorithm="sa",
        initial_value=r.initial_value,
        final_value=r.final_value,
        final_state=r.final_state,
        history=r.value_history,
        duration=r.duration,
        iterations=r.iterations,
        initial_state=r.initial_state,
        extra={
            "best_value": r.best_value,
            "stuck_count": r.stuck_count,
            "prob_history": r.prob_history,
            "temp_history": r.temp_history,
        },
    )


def run_ga(state0, evaluator, seed, **params):
    from algorithms.genetic_algorithm import run as ga_run

    packages = [pp.package for pp in state0.placed]
    population_size = params.get("population_size", 20)
    generations = params.get("generations", 50)
    r = ga_run(
        packages,
        state0.truck,
        population_size=population_size,
        generations=generations,
        seed=seed,
    )
    return SearchResult(
        algorithm="ga",
        initial_value=r.initial_best_value,
        final_value=r.final_value,
        final_state=r.final_state,
        history=r.best_history,
        duration=r.duration,
        iterations=r.generations,
        initial_state=r.initial_best,
        extra={"avg_history": r.avg_history, "population_size": population_size},
    )


ALGORITHMS = {
    "hc_steepest": run_hc_steepest,
    "hc_stochastic": run_hc_stochastic,
    "hc_sideways": run_hc_sideways,
    "hc_random_restart": run_hc_random_restart,
    "sa": run_sa,
    "ga": run_ga,
}


# ---------------------------------------------------------------- visualization


def visualize_state(state, evaluator, out_path=None, title=""):
    """Render 3D state (truk + paket dalam/luar)."""
    from visualization import render_state

    return render_state(state, evaluator=evaluator, title=title, out_path=out_path)


def plot_search_history(result, out_path=None, prob_out_path=None):
    """Plot objective terhadap iterasi (serta acceptance prob khusus SA)."""
    from visualization import (
        plot_ga_history,
        plot_objective_history,
        plot_sa_acceptance,
    )

    if result.algorithm == "ga" and "avg_history" in result.extra:
        fig = plot_ga_history(
            result.history,
            result.extra["avg_history"],
            title=f"GA Objective Value (pop={result.extra.get('population_size')})",
            out_path=out_path,
        )
    else:
        fig = plot_objective_history(
            result.history,
            title=f"{result.algorithm} - Objective Value terhadap Iterasi",
            out_path=out_path,
        )

    if result.algorithm == "sa" and "prob_history" in result.extra and prob_out_path:
        plot_sa_acceptance(
            result.extra["prob_history"],
            title=r"SA - $e^{\Delta E / T}$ terhadap Iterasi",
            out_path=prob_out_path,
        )
    return fig


# ------------------------------------------------------------------- plumbing


def _coerce(value):
    """Ubah string CLI menjadi int/float/bool bila memungkinkan."""
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_params(pairs):
    """Parse daftar 'KEY=VALUE' menjadi dict dengan tipe yang sesuai."""
    params = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"param harus KEY=VALUE: {pair!r}")
        key, value = pair.split("=", 1)
        params[key.strip()] = _coerce(value.strip())
    return params


def build_initial_state(packages, truck, seed, fill_ratio):
    return random_state(packages, truck, seed=seed, fill_ratio=fill_ratio)


def _serialize_placements(state):
    return [
        {
            "id": pp.package.id,
            "inside": pp.inside,
            "position": list(pp.position),
            "orientation": list(pp.orientation),
        }
        for pp in state.placed
    ]


def save_result(result, seed, params, output_dir):
    """Simpan ringkasan hasil satu run ke JSON di output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result.algorithm}_seed{seed}.json"

    payload = {
        "algorithm": result.algorithm,
        "seed": seed,
        "params": params,
        "initial_value": result.initial_value,
        "final_value": result.final_value,
        "duration": result.duration,
        "iterations": result.iterations,
        "history": list(result.history),
        "extra": result.extra,
        "initial_placements": (
            _serialize_placements(result.initial_state)
            if result.initial_state is not None
            else []
        ),
        "placements": _serialize_placements(result.final_state),
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Mejiro Express - optimasi muatan truk dengan local search."
    )
    parser.add_argument(
        "--dataset", default="data/fixed_packages.json", help="path JSON paket"
    )
    parser.add_argument(
        "--algorithm", choices=ALGORITHM_CHOICES, help="algoritma yang dijalankan"
    )
    parser.add_argument("--truck", default=None, help="path JSON konfigurasi truk")
    parser.add_argument("--seed", type=int, default=42, help="random seed dasar")
    parser.add_argument("--runs", type=int, default=1, help="jumlah run")
    parser.add_argument(
        "--fill-ratio",
        type=float,
        default=0.7,
        help="peluang paket dimasukkan saat inisialisasi",
    )
    parser.add_argument(
        "--output-dir", default="output", help="direktori untuk menyimpan hasil"
    )
    parser.add_argument(
        "--param",
        action="append",
        help="parameter algoritma KEY=VALUE (boleh diulang)",
    )
    parser.add_argument(
        "--list-algorithms",
        action="store_true",
        help="tampilkan daftar algoritma lalu keluar",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.list_algorithms:
        print("\n".join(ALGORITHM_CHOICES))
        return 0

    if not args.algorithm:
        raise SystemExit(
            "error: --algorithm wajib diisi (atau pakai --list-algorithms)"
        )

    packages = load_packages(args.dataset)
    truck = load_truck(args.truck) if args.truck else Truck()
    evaluator = Evaluator(truck)
    params = parse_params(args.param)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    algorithm = ALGORITHMS[args.algorithm]

    for run in range(args.runs):
        seed = args.seed + run
        state0 = build_initial_state(packages, truck, seed, args.fill_ratio)

        start = time.perf_counter()
        result = algorithm(state0, evaluator, seed=seed, **params)
        result.duration = time.perf_counter() - start

        valid, reason = evaluator.validate(result.final_state)
        print(
            f"[{result.algorithm}] run={run} seed={seed} "
            f"initial={result.initial_value:.0f} final={result.final_value:.0f} "
            f"valid={valid}({reason}) duration={result.duration:.4f}s"
        )

        prefix = output_dir / f"{result.algorithm}_seed{seed}"
        init_state = result.initial_state if result.initial_state is not None else state0
        visualize_state(
            init_state,
            evaluator,
            out_path=f"{prefix}_initial.png",
            title=f"{result.algorithm} (seed={seed}) - Initial State",
        )
        visualize_state(
            result.final_state,
            evaluator,
            out_path=f"{prefix}_final.png",
            title=f"{result.algorithm} (seed={seed}) - Final State",
        )
        plot_search_history(
            result,
            out_path=f"{prefix}_history.png",
            prob_out_path=f"{prefix}_prob.png" if result.algorithm == "sa" else None,
        )

        path = save_result(result, seed, params, output_dir)
        print(f"  -> saved {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

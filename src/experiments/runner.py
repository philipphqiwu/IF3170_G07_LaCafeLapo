"""Orkestrasi eksperimen untuk semua algoritma local search.

Menjalankan setiap konfigurasi beberapa kali, menyimpan hasil (JSON + PNG)
dan merangkumnya ke summary.{json,csv,md}.

Contoh pemakaian:
    python src/experiments/runner.py
    python src/experiments/runner.py --algorithms hc,sa --seeds 0,1,2
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

# Backend non-interaktif wajib diset sebelum matplotlib/pyplot diimpor.
os.environ.setdefault("MPLBACKEND", "Agg")

# Pastikan folder src ada di sys.path agar bisa `import main`, `from core ...`.
SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core import Evaluator, Truck, load_packages, load_truck  # noqa: E402
from main import (  # noqa: E402
    ALGORITHMS,
    build_initial_state,
    plot_search_history,
    save_result,
    visualize_state,
)

from experiments import configs  # noqa: E402


def _load(dataset, truck_path=None):
    packages = load_packages(dataset)
    truck = load_truck(truck_path) if truck_path else Truck()
    return packages, truck, Evaluator(truck)


def _notes(algorithm, result):
    """Ringkasan info tambahan per algoritma untuk tabel."""
    extra = result.extra or {}
    if algorithm == "hc_sideways":
        return f"sideways={extra.get('sideways_count')}"
    if algorithm == "hc_random_restart":
        per = extra.get("iterations_per_restart", [])
        return f"restarts={extra.get('restarts')} per_restart={per}"
    if algorithm == "sa":
        return f"stuck={extra.get('stuck_count')} best={extra.get('best_value')}"
    if algorithm == "ga":
        return f"pop={extra.get('population_size')} gens={result.iterations}"
    return ""


def run_one(algorithm, packages, truck, evaluator, seed, params, out_dir, config_label):
    """Jalankan satu konfigurasi sekali, simpan artefak, kembalikan record."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    state0 = build_initial_state(packages, truck, seed, configs.FILL_RATIO)

    start = time.perf_counter()
    result = ALGORITHMS[algorithm](state0, evaluator, seed=seed, **params)
    result.duration = time.perf_counter() - start

    valid, reason = evaluator.validate(result.final_state)

    prefix = out_dir / f"{algorithm}_seed{seed}"
    init_state = result.initial_state if result.initial_state is not None else state0
    visualize_state(
        init_state, evaluator,
        out_path=f"{prefix}_initial.png",
        title=f"{algorithm} ({config_label}, seed={seed}) - Initial State",
    )
    visualize_state(
        result.final_state, evaluator,
        out_path=f"{prefix}_final.png",
        title=f"{algorithm} ({config_label}, seed={seed}) - Final State",
    )
    plot_search_history(
        result,
        out_path=f"{prefix}_history.png",
        prob_out_path=f"{prefix}_prob.png" if algorithm == "sa" else None,
    )
    save_result(result, seed, params, out_dir)

    print(
        f"[{algorithm:18s}] {config_label:20s} seed={seed} "
        f"init={result.initial_value:6.0f} final={result.final_value:6.0f} "
        f"it={result.iterations:5d} dur={result.duration:.3f}s valid={valid}"
    )

    return {
        "algorithm": algorithm,
        "config": config_label,
        "seed": seed,
        "population_size": params.get("population_size", ""),
        "generations": params.get("generations", ""),
        "initial_value": result.initial_value,
        "final_value": result.final_value,
        "iterations": result.iterations,
        "duration": result.duration,
        "valid": valid,
        "reason": reason,
        "notes": _notes(algorithm, result),
    }


def run_hc(packages, truck, evaluator, seeds, out_root):
    records = []
    for algorithm in configs.HC_ALGORITHMS:
        params = configs.HC_PARAMS[algorithm]
        for seed in seeds:
            records.append(
                run_one(
                    algorithm, packages, truck, evaluator, seed, params,
                    out_root / algorithm, algorithm,
                )
            )
    return records


def run_sa(packages, truck, evaluator, seeds, out_root):
    records = []
    for seed in seeds:
        records.append(
            run_one(
                "sa", packages, truck, evaluator, seed, configs.SA_PARAMS,
                out_root / "sa", "sa",
            )
        )
    return records


def run_ga(packages, truck, evaluator, seeds, out_root):
    records = []

    # Kontrol populasi: generations tetap, populasi divariasikan.
    for population in configs.GA_POPULATIONS:
        params = dict(
            population_size=population,
            generations=configs.GA_FIXED_GENERATIONS,
        )
        label = f"pop={population},gen={configs.GA_FIXED_GENERATIONS}"
        for seed in seeds:
            records.append(
                run_one(
                    "ga", packages, truck, evaluator, seed, params,
                    out_root / "ga" / f"pop{population}_gen{configs.GA_FIXED_GENERATIONS}",
                    label,
                )
            )

    # Kontrol iterasi: populasi tetap, generations divariasikan.
    for generations in configs.GA_GENERATIONS:
        params = dict(
            population_size=configs.GA_FIXED_POPULATION,
            generations=generations,
        )
        label = f"pop={configs.GA_FIXED_POPULATION},gen={generations}"
        for seed in seeds:
            records.append(
                run_one(
                    "ga", packages, truck, evaluator, seed, params,
                    out_root / "ga" / f"pop{configs.GA_FIXED_POPULATION}_gen{generations}",
                    label,
                )
            )
    return records


CSV_FIELDS = [
    "algorithm",
    "config",
    "seed",
    "population_size",
    "generations",
    "initial_value",
    "final_value",
    "iterations",
    "duration",
    "valid",
    "notes",
]


def write_summary(records, out_root):
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    (out_root / "summary.json").write_text(
        json.dumps(records, indent=2, default=str)
    )

    with open(out_root / "summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for rec in records:
            writer.writerow({k: rec.get(k, "") for k in CSV_FIELDS})

    lines = ["| " + " | ".join(CSV_FIELDS) + " |"]
    lines.append("|" + "|".join(["---"] * len(CSV_FIELDS)) + "|")
    for rec in records:
        lines.append(
            "| " + " | ".join(str(rec.get(k, "")) for k in CSV_FIELDS) + " |"
        )
    (out_root / "summary.md").write_text("\n".join(lines) + "\n")

    return out_root / "summary.md"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Runner eksperimen local search.")
    parser.add_argument("--dataset", default=configs.DATASET, help="path JSON paket")
    parser.add_argument("--truck", default=None, help="path JSON konfigurasi truk")
    parser.add_argument(
        "--algorithms",
        default="hc,sa,ga",
        help="subset algoritma yang dijalankan (hc,sa,ga)",
    )
    parser.add_argument(
        "--seeds",
        default=",".join(str(s) for s in configs.SEEDS),
        help="daftar seed dipisah koma",
    )
    parser.add_argument(
        "--output-dir",
        default="output/experiments",
        help="direktori hasil eksperimen",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    algorithms = [a.strip() for a in args.algorithms.split(",") if a.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    out_root = Path(args.output_dir)

    packages, truck, evaluator = _load(args.dataset, args.truck)
    print(f"dataset={args.dataset} seeds={seeds} output={out_root}")

    records = []
    if "hc" in algorithms:
        records += run_hc(packages, truck, evaluator, seeds, out_root)
    if "sa" in algorithms:
        records += run_sa(packages, truck, evaluator, seeds, out_root)
    if "ga" in algorithms:
        records += run_ga(packages, truck, evaluator, seeds, out_root)

    path = write_summary(records, out_root)
    print(f"\nTotal {len(records)} run -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

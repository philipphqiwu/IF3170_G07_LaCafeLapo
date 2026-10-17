"""Generator dataset paket random yang reproducible.

Contoh pemakaian:
    python data/generate.py --n 30 --seed 42 --out data/random_packages.json
"""

import argparse
import json
import random


def generate_packages(n: int, seed: int, max_dim: int = 6, max_eta: int = 5):
    rng = random.Random(seed)
    packages = []
    for i in range(n):
        w = rng.randint(1, max_dim)
        l = rng.randint(1, max_dim)
        h = rng.randint(1, 3)
        volume = w * l * h
        packages.append(
            {
                "id": f"PKG-{i + 1:02d}",
                "w": w,
                "l": l,
                "h": h,
                # value kasar sebanding volume + sedikit variasi
                "value": int(volume * rng.uniform(3.0, 7.0)),
                # weight kasar sebanding volume + variasi
                "weight": int(volume * rng.uniform(1.5, 3.5)) + rng.randint(1, 5),
                "is_fragile": rng.random() < 0.2,
                "eta": rng.randint(1, max_eta),
            }
        )
    return packages


def main():
    parser = argparse.ArgumentParser(description="Generate random package dataset.")
    parser.add_argument("--n", type=int, default=20, help="jumlah paket")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--max-dim", type=int, default=6, help="dimensi maksimum")
    parser.add_argument("--max-eta", type=int, default=5, help="ETA maksimum")
    parser.add_argument("--out", type=str, default=None, help="path output JSON")
    args = parser.parse_args()

    packages = generate_packages(args.n, args.seed, args.max_dim, args.max_eta)
    text = json.dumps(packages, indent=2)

    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")
        print(f"Wrote {len(packages)} packages to {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

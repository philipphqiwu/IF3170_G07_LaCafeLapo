"""Inisialisasi state random yang valid."""

import random

import numpy as np

from .evaluator import Evaluator
from .models import ALL_ORIENTATIONS, PlacedPackage, State, Truck


def find_lowest_valid_z(
    evaluator: Evaluator,
    grid: np.ndarray,
    package,
    x: int,
    y: int,
    orientation: tuple,
    fragile_grid_values: set,
):
    """Cari z terendah yang valid untuk paket di (x, y) dengan orientasi tertentu.

    Parameters
    ----------
    grid : occupancy grid saat ini (0 = kosong).
    fragile_grid_values : set nilai grid (i+1) yang menandai paket fragile.

    Returns
    -------
    int z jika berhasil, None jika tidak ada posisi valid.
    """
    pp = PlacedPackage(
        package=package, position=(x, y, 0), orientation=orientation, inside=True
    )
    dx, dy, dz = pp.dims()

    if dz > evaluator.truck.h:
        return None
    if x < 0 or y < 0 or x + dx > evaluator.truck.w or y + dy > evaluator.truck.l:
        return None

    for z in range(evaluator.truck.h - dz + 1):
        # Cek tumpang tindih
        if np.any(grid[x : x + dx, y : y + dy, z : z + dz] != 0):
            continue

        # Cek penyangga (anti-melayang): minimal satu titik alas bersandar
        if z > 0 and not np.any(grid[x : x + dx, y : y + dy, z - 1] != 0):
            continue

        # Cek tidak duduk di atas paket fragile
        if z > 0:
            on_fragile = False
            for fx in range(x, x + dx):
                for fy in range(y, y + dy):
                    cell_val = int(grid[fx, fy, z - 1])
                    if cell_val > 0 and cell_val in fragile_grid_values:
                        on_fragile = True
                        break
                if on_fragile:
                    break
            if on_fragile:
                continue

        return z

    return None


def random_state(
    packages,
    truck: Truck,
    seed: int = None,
    rng: random.Random = None,
    fill_ratio: float = 0.7,
) -> State:
    """Buat state awal random yang valid.

    - Setiap paket punya peluang `fill_ratio` untuk masuk truk.
    - Posisi dan orientasi dipilih random, lalu dicari z terendah yang valid.
    - Jika tidak bisa ditempatkan, paket tetap di luar.
    """
    if rng is None:
        rng = random.Random(seed)

    evaluator = Evaluator(truck)
    shuffled = list(packages)
    rng.shuffle(shuffled)

    placed: list[PlacedPackage] = []
    inside_placed: list[PlacedPackage] = []
    grid = np.zeros(evaluator.shape, dtype=np.int32)
    fragile_grid_values: set[int] = set()
    current_weight = 0

    for pkg in shuffled:
        # Putuskan apakah paket ini mau dimasukkan
        if rng.random() > fill_ratio:
            placed.append(PlacedPackage(package=pkg, inside=False))
            continue

        # Coba taruh dengan orientasi random
        orientation = rng.choice(ALL_ORIENTATIONS)
        raw = (pkg.w, pkg.l, pkg.h)
        dx = raw[orientation[0]]
        dy = raw[orientation[1]]

        if dx > truck.w or dy > truck.l or raw[orientation[2]] > truck.h:
            placed.append(PlacedPackage(package=pkg, inside=False))
            continue

        max_attempts = 50
        placed_ok = False

        for _ in range(max_attempts):
            x = rng.randint(0, truck.w - dx)
            y = rng.randint(0, truck.l - dy)

            z = find_lowest_valid_z(
                evaluator, grid, pkg, x, y, orientation, fragile_grid_values
            )
            if z is None:
                continue

            # Cek kapasitas berat
            if current_weight + pkg.weight > truck.max_capacity:
                break

            pp = PlacedPackage(
                package=pkg,
                position=(x, y, z),
                orientation=orientation,
                inside=True,
            )
            pdx, pdy, pdz = pp.dims()
            grid_val = len(inside_placed) + 1
            grid[x : x + pdx, y : y + pdy, z : z + pdz] = grid_val

            if pkg.is_fragile:
                fragile_grid_values.add(grid_val)

            inside_placed.append(pp)
            placed.append(pp)
            current_weight += pkg.weight
            placed_ok = True
            break

        if not placed_ok:
            placed.append(PlacedPackage(package=pkg, inside=False))

    return State(truck=truck, placed=placed)

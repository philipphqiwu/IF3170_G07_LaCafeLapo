"""Neighbor moves: swap, move, rotate.

Semua move diusahakan menghasilkan state yang VALID (tidak melayang, tidak
menembus dinding, tidak menimpa paket fragile, dan tidak melebihi kapasitas).
Penempatan memakai find_lowest_valid_z() dari core.initializer.
"""

import random

from .evaluator import Evaluator
from .initializer import find_lowest_valid_z
from .models import ALL_ORIENTATIONS, PlacedPackage, State


def _context(state, exclude_ids):
    """Bangun konteks penempatan dari paket selain `exclude_ids`.

    Return (evaluator, grid, fragile_values, total_weight, next_marker).
    """
    ev = Evaluator(state.truck)
    others = [
        q for q in state.placed if q.inside and q.package.id not in exclude_ids
    ]
    grid = ev.build_grid(others)
    fragile = {i + 1 for i, q in enumerate(others) if q.package.is_fragile}
    weight = sum(q.package.weight for q in others)
    return ev, grid, fragile, weight, len(others) + 1


def _stamp(grid, fragile, marker, pp):
    """Tandai sel yang ditempati pp pada grid (dan catat bila fragile)."""
    dx, dy, dz = pp.dims()
    x, y, z = pp.position
    grid[x : x + dx, y : y + dy, z : z + dz] = marker
    if pp.package.is_fragile:
        fragile.add(marker)


def _place_at(ev, grid, fragile, pkg, x, y, orientation):
    """Taruh pkg di (x, y) dengan orientasi tertentu, kembalikan (x,y,z) / None."""
    t = ev.truck
    raw = (pkg.w, pkg.l, pkg.h)
    dx, dy, dz = raw[orientation[0]], raw[orientation[1]], raw[orientation[2]]
    if dx > t.w or dy > t.l or dz > t.h:
        return None
    if x < 0 or y < 0 or x + dx > t.w or y + dy > t.l:
        return None
    z = find_lowest_valid_z(ev, grid, pkg, x, y, orientation, fragile)
    if z is None:
        return None
    return (x, y, z)


def _place_random(ev, grid, fragile, pkg, rng, attempts=12):
    """Cari posisi valid acak untuk pkg.  Return ((x,y,z), orientation) / (None, None)."""
    t = ev.truck
    raw = (pkg.w, pkg.l, pkg.h)
    for _ in range(attempts):
        orientation = rng.choice(ALL_ORIENTATIONS)
        dx, dy, dz = raw[orientation[0]], raw[orientation[1]], raw[orientation[2]]
        if dx > t.w or dy > t.l or dz > t.h:
            continue
        x = rng.randint(0, t.w - dx)
        y = rng.randint(0, t.l - dy)
        z = find_lowest_valid_z(ev, grid, pkg, x, y, orientation, fragile)
        if z is not None:
            return (x, y, z), orientation
    return None, None


def swap(state: State, rng: random.Random) -> State:
    """Tukar penempatan dua paket, lalu tempatkan ulang secara valid."""
    nxt = state.copy()
    if len(nxt.placed) < 2:
        return nxt

    i, j = rng.sample(range(len(nxt.placed)), 2)
    pi, pj = nxt.placed[i], nxt.placed[j]

    ev, grid, fragile, weight, marker = _context(
        nxt, {pi.package.id, pj.package.id}
    )
    cap = ev.truck.max_capacity

    old_i = (pi.inside, pi.position, pi.orientation)
    old_j = (pj.inside, pj.position, pj.orientation)

    # Tukar status in/out: pi mengambil slot pj, dan sebaliknya.
    pi.inside, pj.inside = old_j[0], old_i[0]

    total_weight = weight
    for p, slot in ((pi, old_j), (pj, old_i)):
        if not p.inside:
            p.position = (0, 0, 0)
            continue
        if total_weight + p.package.weight > cap:
            p.inside = False
            p.position = (0, 0, 0)
            continue

        pos = _place_at(ev, grid, fragile, p.package, slot[1][0], slot[1][1], slot[2])
        orientation = slot[2]
        if pos is None:
            pos, orientation = _place_random(ev, grid, fragile, p.package, rng)

        if pos is None:
            p.inside = False
            p.position = (0, 0, 0)
        else:
            p.inside = True
            p.position = pos
            p.orientation = orientation
            total_weight += p.package.weight
            _stamp(grid, fragile, marker, p)
            marker += 1

    return nxt


def move(state: State, rng: random.Random) -> State:
    """Pindahkan satu paket ke koordinat valid lain, atau keluarkan dari truk."""
    nxt = state.copy()
    if not nxt.placed:
        return nxt

    p = rng.choice(nxt.placed)
    ev, grid, fragile, weight, _ = _context(nxt, {p.package.id})

    # Tidak mungkin masuk kalau beratnya bikin overload.
    if weight + p.package.weight > ev.truck.max_capacity:
        return nxt

    # Kadang keluarkan paket agar pencarian bisa turun dari local optimum.
    if p.inside and rng.random() < 0.25:
        p.inside = False
        p.position = (0, 0, 0)
        return nxt

    pos, orientation = _place_random(ev, grid, fragile, p.package, rng)
    if pos is None:
        return nxt

    p.inside = True
    p.position = pos
    p.orientation = orientation
    return nxt


def _rotated(orientation: tuple, axis: str) -> tuple:
    a, b, c = orientation
    if axis == "x":
        return (a, c, b)
    if axis == "y":
        return (c, b, a)
    return (b, a, c)


def rotate(state: State, rng: random.Random) -> State:
    """Rotasi satu paket 90 derajat terhadap sumbu x, y, atau z (hasil valid)."""
    nxt = state.copy()
    inside = [p for p in nxt.placed if p.inside]
    if not inside:
        return nxt

    p = rng.choice(inside)
    ev, grid, fragile, _, _ = _context(nxt, {p.package.id})

    new_orientation = _rotated(p.orientation, rng.choice(["x", "y", "z"]))

    # Coba pertahankan (x, y), cari z valid untuk orientasi baru.
    pos = _place_at(ev, grid, fragile, p.package, p.position[0], p.position[1], new_orientation)
    if pos is not None:
        p.orientation = new_orientation
        p.position = pos
        return nxt

    # Kalau gagal, coba beberapa (x, y) acak dengan orientasi baru.
    t = ev.truck
    raw = (p.package.w, p.package.l, p.package.h)
    dx, dy, dz = (
        raw[new_orientation[0]],
        raw[new_orientation[1]],
        raw[new_orientation[2]],
    )
    if dx <= t.w and dy <= t.l and dz <= t.h:
        for _ in range(6):
            x = rng.randint(0, t.w - dx)
            y = rng.randint(0, t.l - dy)
            z = find_lowest_valid_z(ev, grid, p.package, x, y, new_orientation, fragile)
            if z is not None:
                p.orientation = new_orientation
                p.position = (x, y, z)
                return nxt

    # Tidak ada penempatan valid: biarkan state tidak berubah.
    return nxt


def random_neighbor(state: State, rng: random.Random) -> State:
    """Pilih salah satu move secara acak."""
    return rng.choice([swap, move, rotate])(state, rng)

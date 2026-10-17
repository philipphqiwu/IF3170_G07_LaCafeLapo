"""Neighbor moves: swap, move, rotate."""

import random

from .models import ALL_ORIENTATIONS, State


def swap(state: State, rng: random.Random) -> State:
    """Tukar penempatan dua paket."""
    nxt = state.copy()
    if len(nxt.placed) < 2:
        return nxt
    a, b = rng.sample(range(len(nxt.placed)), 2)
    pa, pb = nxt.placed[a], nxt.placed[b]
    pa.position, pb.position = pb.position, pa.position
    pa.orientation, pb.orientation = pb.orientation, pa.orientation
    pa.inside, pb.inside = pb.inside, pa.inside
    return nxt


def move(state: State, rng: random.Random) -> State:
    """Pindahkan satu paket ke koordinat lain."""
    nxt = state.copy()
    if not nxt.placed:
        return nxt
    p = rng.choice(nxt.placed)
    t = nxt.truck
    old_pos = p.position
    for _ in range(10):
        pos = (
            rng.randint(0, max(0, t.w - 1)),
            rng.randint(0, max(0, t.l - 1)),
            rng.randint(0, max(0, t.h - 1)),
        )
        if pos != old_pos:
            break
    p.position = pos
    p.inside = rng.choice([True, False])
    return nxt


def _rotated(orientation: tuple, axis: str) -> tuple:
    a, b, c = orientation
    if axis == "x":
        return (a, c, b)
    if axis == "y":
        return (c, b, a)
    return (b, a, c)


def rotate(state: State, rng: random.Random) -> State:
    """Rotasi satu paket 90 derajat terhadap sumbu x, y, atau z."""
    nxt = state.copy()
    if not nxt.placed:
        return nxt
    p = rng.choice(nxt.placed)
    axis = rng.choice(["x", "y", "z"])
    p.orientation = _rotated(p.orientation, axis)
    assert p.orientation in ALL_ORIENTATIONS
    return nxt


def random_neighbor(state: State, rng: random.Random) -> State:
    """Pilih salah satu move secara acak."""
    return rng.choice([swap, move, rotate])(state, rng)

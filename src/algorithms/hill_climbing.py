"""Algoritma Hill-Climbing dan variannya.

Semua fungsi memakai kontrak yang sama:
    f(state0, evaluator, seed=None, **params) -> HCResult

Neighbor dibangkitkan lewat core.neighbors.random_neighbor, objective dinilai
lewat evaluator.evaluate (state tidak valid bernilai -1).  Untuk menghemat
waktu, "steepest" tidak menelusuri seluruh ruang tetangga, melainkan mengambil
sampel `n_neighbors` tetangga acak per iterasi lalu memilih yang terbaik.
"""

import random
import time
from dataclasses import dataclass, field

from core.evaluator import Evaluator
from core.initializer import random_state
from core.neighbors import random_neighbor


@dataclass
class HCResult:
    variant: str
    initial_state: object
    initial_value: float
    final_state: object
    final_value: float
    iterations: int
    duration: float
    value_history: list = field(default_factory=list)
    sideways_count: int = 0
    restarts: int = 0
    iterations_per_restart: list = field(default_factory=list)


def _best_neighbor(state, evaluator, rng, n_neighbors):
    """Ambil sampel tetangga acak, kembalikan yang objective-nya tertinggi."""
    best, best_value = None, None
    for _ in range(n_neighbors):
        cand = random_neighbor(state, rng)
        value = evaluator.evaluate(cand)
        if best_value is None or value > best_value:
            best, best_value = cand, value
    return best, best_value


def steepest_ascent(
    state0,
    evaluator: Evaluator,
    seed=None,
    n_neighbors: int = 30,
    max_iter: int = 1000,
    **params,
):
    """Steepest Ascent Hill-Climbing.

    Tiap iterasi mengambil sampel `n_neighbors` tetangga dan berpindah ke yang
    terbaik.  Berhenti saat tidak ada tetangga yang lebih baik, atau `max_iter`
    tercapai.
    """
    rng = random.Random(seed)
    start = time.perf_counter()

    current = state0
    current_value = evaluator.evaluate(current)
    history = [current_value]

    it = 0
    while it < max_iter:
        it += 1
        best, best_value = _best_neighbor(current, evaluator, rng, n_neighbors)
        if best_value is not None and best_value > current_value:
            current, current_value = best, best_value
            history.append(current_value)
        else:
            history.append(current_value)
            break

    return HCResult(
        variant="steepest_ascent",
        initial_state=state0,
        initial_value=history[0],
        final_state=current,
        final_value=current_value,
        iterations=it,
        duration=time.perf_counter() - start,
        value_history=history,
    )


def stochastic(
    state0,
    evaluator: Evaluator,
    seed=None,
    patience: int = 100,
    max_iter: int = 1000,
    **params,
):
    """Stochastic Hill-Climbing.

    Tiap iterasi mengambil SATU tetangga acak dan menerimanya bila lebih baik.
    Berhenti setelah `patience` iterasi berturut-turut tanpa perbaikan, atau
    `max_iter` tercapai.
    """
    rng = random.Random(seed)
    start = time.perf_counter()

    current = state0
    current_value = evaluator.evaluate(current)
    history = [current_value]

    it = 0
    no_improve = 0
    while it < max_iter:
        it += 1
        cand = random_neighbor(current, rng)
        cand_value = evaluator.evaluate(cand)

        if cand_value > current_value:
            current, current_value = cand, cand_value
            no_improve = 0
        else:
            no_improve += 1

        history.append(current_value)

        if no_improve >= patience:
            break

    return HCResult(
        variant="stochastic",
        initial_state=state0,
        initial_value=history[0],
        final_state=current,
        final_value=current_value,
        iterations=it,
        duration=time.perf_counter() - start,
        value_history=history,
    )


def sideways(
    state0,
    evaluator: Evaluator,
    seed=None,
    max_sideways: int = 20,
    n_neighbors: int = 30,
    max_iter: int = 1000,
    **params,
):
    """Hill-Climbing with Sideways Move.

    Seperti steepest ascent, tapi mengizinkan perpindahan ke tetangga bernilai
    SAMA (sideways) hingga `max_sideways` kali berturut-turut.  Berhenti saat
    tidak ada tetangga lebih baik maupun sama, atau batas sideways terlampaui.
    """
    rng = random.Random(seed)
    start = time.perf_counter()

    current = state0
    current_value = evaluator.evaluate(current)
    history = [current_value]

    it = 0
    sideways_count = 0
    streak = 0
    while it < max_iter:
        it += 1
        best, best_value = _best_neighbor(current, evaluator, rng, n_neighbors)

        if best_value is not None and best_value > current_value:
            current, current_value = best, best_value
            streak = 0
            history.append(current_value)
        elif best_value is not None and best_value == current_value:
            current, current_value = best, best_value
            streak += 1
            sideways_count += 1
            history.append(current_value)
            if streak >= max_sideways:
                break
        else:
            history.append(current_value)
            break

    return HCResult(
        variant="sideways",
        initial_state=state0,
        initial_value=history[0],
        final_state=current,
        final_value=current_value,
        iterations=it,
        duration=time.perf_counter() - start,
        value_history=history,
        sideways_count=sideways_count,
    )


def random_restart(
    state0,
    evaluator: Evaluator,
    seed=None,
    max_restart: int = 5,
    n_neighbors: int = 30,
    max_iter_per_restart: int = 500,
    **params,
):
    """Random Restart Hill-Climbing.

    Menjalankan steepest ascent berulang kali.  Tiap local optimum dicapai,
    pencarian diulang dari state awal random yang baru.  Berhenti setelah
    `max_restart` restart.
    """
    rng = random.Random(seed)
    start = time.perf_counter()

    packages = [pp.package for pp in state0.placed]
    truck = state0.truck

    best_state = state0
    best_value = evaluator.evaluate(state0)
    history = [evaluator.evaluate(state0)]
    iterations_per_restart = []

    current_start = state0
    restarts = 0
    for _ in range(max_restart):
        restarts += 1
        res = steepest_ascent(
            current_start,
            evaluator,
            seed=rng.randint(0, 2**31 - 1),
            n_neighbors=n_neighbors,
            max_iter=max_iter_per_restart,
        )
        iterations_per_restart.append(res.iterations)
        history.extend(res.value_history[1:])

        if res.final_value > best_value:
            best_state, best_value = res.final_state, res.final_value

        current_start = random_state(packages, truck, rng=rng)

    return HCResult(
        variant="random_restart",
        initial_state=state0,
        initial_value=history[0],
        final_state=best_state,
        final_value=best_value,
        iterations=sum(iterations_per_restart),
        duration=time.perf_counter() - start,
        value_history=history,
        restarts=restarts,
        iterations_per_restart=iterations_per_restart,
    )

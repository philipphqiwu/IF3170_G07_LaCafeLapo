import copy
import math
import random
import time
from dataclasses import dataclass, field


@dataclass
class SAResult:
    initial_state: object
    initial_value: float
    final_state: object          # last search state
    final_value: float
    best_state: object           # best search state
    best_value: float
    iterations: int
    duration: float              # seconds
    stuck_count: int             # stuck count di local optima
    value_history: list = field(default_factory=list)  
    prob_history: list = field(default_factory=list)   
    temp_history: list = field(default_factory=list)


def simulated_annealing(
    initial_state,
    objective,
    neighbor,
    t0=100.0,
    cooling_rate=0.995,
    t_min=1e-3,
    max_iter=100_000,
    stuck_threshold=500,
    seed=None,
):
    """
    Schedule suhu pakai geometric cooling: T(k+1) = T(k) * cooling_rate.
    Berhenti kalau T < t_min atau iterasi udah max_iter.

    Stuck terjadi ketika ada stuck_threshold iterasi berturut-turut tanpa
    perbaikan nilai current. Tiap kali streak-nya nyentuh threshold, dihitung
    1 kali stuck (terus streak di-reset).
    """
    rng = random.Random(seed)
    start = time.perf_counter()

    current = initial_state
    current_value = objective(current)
    best, best_value = current, current_value

    result = SAResult(
        initial_state=copy.deepcopy(initial_state),
        initial_value=current_value,
        final_state=None, final_value=None,
        best_state=None, best_value=None,
        iterations=0, duration=0.0, stuck_count=0,
    )

    t = t0
    no_improve = 0
    it = 0
    while t > t_min and it < max_iter:
        it += 1
        cand = neighbor(current, rng)
        cand_value = objective(cand)
        delta = cand_value - current_value 

        if delta > 0:  # dE > 0 berarti state tetangga better
            prob = 1.0
            accept = True
        else:
            # makin dingin -> makin kecil peluang diterima
            prob = math.exp(delta / t)
            accept = rng.random() < prob

        if accept:
            current, current_value = cand, cand_value

        if delta > 0:
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= stuck_threshold:
                result.stuck_count += 1
                no_improve = 0

        if current_value > best_value:
            best, best_value = current, current_value

        result.value_history.append(current_value)
        result.prob_history.append(prob)
        result.temp_history.append(t)

        t *= cooling_rate

    result.final_state, result.final_value = current, current_value
    result.best_state, result.best_value = best, best_value
    result.iterations = it
    result.duration = time.perf_counter() - start
    return result

import copy
import random
import time
from dataclasses import dataclass, field

from core.evaluator import Evaluator
from core.initializer import random_state
from core.models import State
from core.neighbors import random_neighbor


def select(population, fitnesses, rng):
    """
    Roulette-wheel: yang fitnessnya gede peluang kepilihnya juga gede.

    Fitness negatif dihitung nol. Kalau semuanya nol (tidak ada yang valid),
    ya pilih acak aja biar tetap jalan.
    """
    total = 0
    for f in fitnesses:
        if f > 0:
            total = total + f

    if total <= 0:
        return rng.choice(population)

    pick = rng.uniform(0, total)
    jalan = 0
    for individu, f in zip(population, fitnesses):
        if f > 0:
            jalan = jalan + f
        if jalan >= pick:
            return individu
    return population[-1]


def crossover(p1, p2, rng):
    """
    Kawin silang satu titik: potong urutan paket di titik acak,
    bagian depan ikut p1, sisanya ikut p2.
    """
    ids = []
    for p in p1.placed:
        ids.append(p.package.id)

    if len(ids) < 2:
        return p1.copy()

    # titik potong jangan di ujung biar beneran nyampur
    titik = rng.randint(1, len(ids) - 1)
    depan = ids[:titik]

    anak = []
    for p in p1.placed:
        if p.package.id in depan:
            anak.append(p.copy())
    for p in p2.placed:
        if p.package.id not in depan:
            anak.append(p.copy())

    return State(truck=p1.truck, placed=anak)


def mutate(state, rng):
    """
    Mutasi: satu move acak aja, numpang fungsi neighbor yang udah ada.
    """
    return random_neighbor(state, rng)


def evaluate_population(population, evaluator):
    """
    Nilai semua individu satu-satu, hasilnya list sejajar sama populasi.
    """
    hasil = []
    for s in population:
        hasil.append(evaluator.evaluate(s))
    return hasil


@dataclass
class GAResult:
    initial_best: object  # individu terbaik generasi 0
    initial_best_value: float
    final_state: object  # individu terbaik generasi terakhir
    final_value: float
    best_state: object  # individu terbaik sepanjang jalan
    best_value: float
    generations: int
    population_size: int
    duration: float  # detik
    best_history: list = field(default_factory=list)
    avg_history: list = field(default_factory=list)


def run(
    packages,
    truck,
    population_size=20,
    generations=50,
    seed=None,
):
    """
    Loop GA: tiap generasi dinilai, lalu generasi baru
    dibuat dari anak (seleksi + crossover + mutasi). Elitism:
    individu terbaik tiap generasi dibawa ke generasi berikut
    biar tidak hilang.

    Berhenti kalau generasi udah nyentuh batas.
    """
    rng = random.Random(seed)
    start = time.perf_counter()
    evaluator = Evaluator(truck)

    population = []
    for _ in range(population_size):
        population.append(random_state(packages, truck, rng=rng))

    result = GAResult(
        initial_best=None,
        initial_best_value=None,
        final_state=None,
        final_value=None,
        best_state=None,
        best_value=None,
        generations=0,
        population_size=population_size,
        duration=0.0,
    )

    best, best_value = None, None

    for _ in range(generations):
        fitnesses = evaluate_population(population, evaluator)

        # yang terbaik generasi ini
        top = 0
        for i in range(1, len(population)):
            if fitnesses[i] > fitnesses[top]:
                top = i

        rata = sum(fitnesses) / len(fitnesses)
        result.best_history.append(fitnesses[top])
        result.avg_history.append(rata)

        if result.initial_best is None:
            result.initial_best = copy.deepcopy(population[top])
            result.initial_best_value = fitnesses[top]

        if best_value is None or fitnesses[top] > best_value:
            best, best_value = population[top], fitnesses[top]

        # elitism: yang terbaik dibawa + sisanya anak
        elite = copy.deepcopy(population[top])
        anak_baru = [elite]
        while len(anak_baru) < population_size:
            bapak = select(population, fitnesses, rng)
            ibu = select(population, fitnesses, rng)
            anak = crossover(bapak, ibu, rng)
            anak = mutate(anak, rng)
            anak_baru.append(anak)
        population = anak_baru

    # nilai generasi terakhir sekali lagi buat hasil akhir
    fitnesses = evaluate_population(population, evaluator)
    top = 0
    for i in range(1, len(population)):
        if fitnesses[i] > fitnesses[top]:
            top = i

    result.final_state = copy.deepcopy(population[top])
    result.final_value = fitnesses[top]
    result.best_state = copy.deepcopy(best)
    result.best_value = best_value
    result.generations = generations
    result.duration = time.perf_counter() - start
    return result

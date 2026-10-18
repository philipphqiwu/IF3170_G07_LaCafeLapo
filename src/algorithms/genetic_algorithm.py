import random

from core.evaluator import Evaluator
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

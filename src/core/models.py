"""Bentuk state yang dipakai oleh semua algoritma."""

from dataclasses import dataclass, field


@dataclass
class Package:
    # data mentah paket, belum ditaruh di mana-mana
    id: str
    w: int
    l: int
    h: int
    value: int
    weight: int
    is_fragile: bool
    eta: int


@dataclass
class Truck:
    # ukuran peti + batas berat, defaultnya ngikutin spek
    w: int = 10
    l: int = 20
    h: int = 5
    max_capacity: int = 500


@dataclass
class PlacedPackage:
    # paket + posisinya. inside=False artinya lagi di luar peti.
    # position itu titik sudut kiri-bawah-belakangnya, isinya bilangan bulat.
    # orientation itu urutan sumbunya, misal (1, 0, 2) berarti w sama l ketuker.
    package: Package
    position: tuple = (0, 0, 0)
    orientation: tuple = (0, 1, 2)
    inside: bool = False

    def dims(self):
        # ukuran paket setelah diputar-putar
        d = (self.package.w, self.package.l, self.package.h)
        return (d[self.orientation[0]], d[self.orientation[1]], d[self.orientation[2]])


@dataclass
class State:
    # satu state = kondisi semua paket + truknya
    truck: Truck = field(default_factory=Truck)
    placed: list = field(default_factory=list)

    def inside_packages(self):
        return [p for p in self.placed if p.inside]

    def outside_packages(self):
        return [p for p in self.placed if not p.inside]

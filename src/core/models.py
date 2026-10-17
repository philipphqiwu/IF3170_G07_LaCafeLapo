"""Bentuk state yang dipakai oleh semua algoritma."""

from dataclasses import dataclass, field

# Enam kemungkinan orientasi = semua permutasi dari sumbu (w, l, h).
# orientation (a, b, c) berarti: sumbu x mengambil dimensi raw[a],
# sumbu y mengambil raw[b], sumbu z mengambil raw[c].
ALL_ORIENTATIONS = [
    (0, 1, 2),  # default
    (1, 0, 2),  # rotasi 90 derajat sumbu z
    (0, 2, 1),  # rotasi 90 derajat sumbu x
    (2, 1, 0),  # rotasi 90 derajat sumbu y
    (1, 2, 0),  # rotasi lain
    (2, 0, 1),  # rotasi lain
]


@dataclass
class Package:
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
    w: int = 10
    l: int = 20
    h: int = 5
    max_capacity: int = 500


@dataclass
class PlacedPackage:
    package: Package
    position: tuple = (0, 0, 0)
    orientation: tuple = (0, 1, 2)
    inside: bool = False

    def dims(self):
        d = (self.package.w, self.package.l, self.package.h)
        return (d[self.orientation[0]], d[self.orientation[1]], d[self.orientation[2]])

    def copy(self):
        return PlacedPackage(
            package=self.package,
            position=self.position,
            orientation=self.orientation,
            inside=self.inside,
        )


@dataclass
class State:
    truck: Truck = field(default_factory=Truck)
    placed: list = field(default_factory=list)

    def inside_packages(self):
        return [p for p in self.placed if p.inside]

    def outside_packages(self):
        return [p for p in self.placed if not p.inside]

    def total_weight(self):
        return sum(p.package.weight for p in self.inside_packages())

    def total_value(self):
        return sum(p.package.value for p in self.inside_packages())

    def get_by_id(self, pkg_id):
        for p in self.placed:
            if p.package.id == pkg_id:
                return p
        return None

    def copy(self):
        return State(
            truck=self.truck,
            placed=[p.copy() for p in self.placed],
        )

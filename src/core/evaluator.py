"""Evaluator: objective function + semua pengecekan constraint."""

import numpy as np

from .models import PlacedPackage, State, Truck


class Evaluator:
    def __init__(self, truck: Truck):
        self.truck = truck
        self.shape = (truck.w, truck.l, truck.h)

    # ------------------------------------------------------------------ grid

    def build_grid(self, inside_placed):
        """Bangun occupancy grid dari daftar paket yang di dalam truk.

        Nilai sel: 0 = kosong, i+1 = indeks paket ke-i (1-based).
        """
        grid = np.zeros(self.shape, dtype=np.int32)
        for i, pp in enumerate(inside_placed):
            dx, dy, dz = pp.dims()
            x, y, z = pp.position
            grid[x : x + dx, y : y + dy, z : z + dz] = i + 1
        return grid

    # ------------------------------------------------------- cek per paket

    def check_bounds(self, pp: PlacedPackage) -> bool:
        dx, dy, dz = pp.dims()
        x, y, z = pp.position
        return (
            0 <= x
            and 0 <= y
            and 0 <= z
            and x + dx <= self.truck.w
            and y + dy <= self.truck.l
            and z + dz <= self.truck.h
        )

    def check_collision(self, grid: np.ndarray, pp: PlacedPackage) -> bool:
        """True jika ada tumpang tindih dengan sel terisi."""
        dx, dy, dz = pp.dims()
        x, y, z = pp.position
        return bool(np.any(grid[x : x + dx, y : y + dy, z : z + dz] != 0))

    def check_support(self, grid: np.ndarray, pp: PlacedPackage) -> bool:
        """Cek anti-melayang

        melayang = TIDAK ADA satupun titik alas yang punya support.
        Jadi paket valid bila minimal SATU titik alas bersandar pada lantai
        (z == 0) atau pada sel di z-1 yang terisi paket lain.
        """
        dx, dy, dz = pp.dims()
        x, y, z = pp.position
        if z == 0:
            return True
        return bool(np.any(grid[x : x + dx, y : y + dy, z - 1] != 0))

    def check_nothing_on_top(self, grid: np.ndarray, pp: PlacedPackage) -> bool:
        """True jika tidak ada paket di atas paket ini.

        Dipakai untuk paket fragile: tidak boleh menjadi support.
        """
        if not pp.package.is_fragile:
            return True
        dx, dy, dz = pp.dims()
        x, y, z = pp.position
        z_top = z + dz
        if z_top >= self.truck.h:
            return True
        return bool(np.all(grid[x : x + dx, y : y + dy, z_top] == 0))

    def check_weight(self, inside_placed) -> bool:
        total = sum(pp.package.weight for pp in inside_placed)
        return total <= self.truck.max_capacity

    # ------------------------------------------------------- validasi state

    def validate(self, state: State):
        """Validasi seluruh state.  Return (is_valid, reason)."""
        inside = state.inside_packages()

        # 1. Kapasitas berat
        if not self.check_weight(inside):
            return False, "weight_exceeded"

        # 2. Bangun grid sambil cek bounds + collision
        grid = np.zeros(self.shape, dtype=np.int32)
        for i, pp in enumerate(inside):
            if not self.check_bounds(pp):
                return False, f"bounds:{pp.package.id}"
            if self.check_collision(grid, pp):
                return False, f"collision:{pp.package.id}"
            dx, dy, dz = pp.dims()
            x, y, z = pp.position
            grid[x : x + dx, y : y + dy, z : z + dz] = i + 1

        # 3. Support (anti-melayang) + fragile
        for pp in inside:
            if not self.check_support(grid, pp):
                return False, f"support:{pp.package.id}"
            if not self.check_nothing_on_top(grid, pp):
                return False, f"fragile:{pp.package.id}"

        return True, "valid"

    # ----------------------------------------------------- objective & eval

    def objective(self, state: State) -> int:
        """Total value paket yang di dalam truk."""
        return state.total_value()

    def evaluate(self, state: State) -> float:
        """Nilai objective.  State tidak valid mendapat penalti -1."""
        valid, _ = self.validate(state)
        if not valid:
            return -1.0
        return float(self.objective(state))

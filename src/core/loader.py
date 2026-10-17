"""Loader dataset paket dari file JSON."""

import json

from .models import Package, Truck


def load_packages(path: str):
    """Baca file JSON dan kembalikan list[Package]."""
    with open(path) as f:
        raw = json.load(f)
    return [
        Package(
            id=item["id"],
            w=item["w"],
            l=item["l"],
            h=item["h"],
            value=item["value"],
            weight=item["weight"],
            is_fragile=item["is_fragile"],
            eta=item["eta"],
        )
        for item in raw
    ]


def load_truck(path: str) -> Truck:
    """Baca konfigurasi truk dari file JSON (opsional)."""
    with open(path) as f:
        raw = json.load(f)
    return Truck(
        w=raw["w"],
        l=raw["l"],
        h=raw["h"],
        max_capacity=raw["max_capacity"],
    )

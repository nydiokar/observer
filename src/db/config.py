from pathlib import Path
from typing import Any

import yaml

from .models import BasketEntry, InstrumentEntry, SeriesEntry, SourceEntry

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def load_yaml(filename: str) -> Any:
    path = CONFIG_DIR / filename
    with open(path) as f:
        return yaml.safe_load(f)


def load_sources() -> list[SourceEntry]:
    data = load_yaml("sources.yaml")
    return [SourceEntry(**s) for s in data["sources"]]


def load_series_registry() -> list[SeriesEntry]:
    data = load_yaml("series_registry.yaml")
    return [SeriesEntry(**s) for s in data["series"]]


def load_instruments() -> list[InstrumentEntry]:
    data = load_yaml("instruments.yaml")
    return [InstrumentEntry(**i) for i in data["instruments"]]


def load_baskets() -> list[BasketEntry]:
    data = load_yaml("baskets.yaml")
    return [BasketEntry(**b) for b in data["baskets"]]

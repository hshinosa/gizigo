from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .models import NUTRIENT_KEYS, AkgCategory, Region


@dataclass(frozen=True)
class Ingredient:
    ingredient_id: str
    display_name: str
    food_group: str
    food_type: str
    nutrients_per_100g: dict[str, float]


@dataclass(frozen=True)
class Catalog:
    catalog_hash: str
    ingredients: tuple[Ingredient, ...]

    def by_id(self) -> dict[str, Ingredient]:
        return {i.ingredient_id: i for i in self.ingredients}


@dataclass(frozen=True)
class PriceTable:
    region: Region
    prices_per_100g: dict[str, float]


@dataclass(frozen=True)
class AkgRecord:
    category: AkgCategory
    label_id: str
    requirements: dict[str, float]


@dataclass(frozen=True)
class AkgTable:
    schema_version: str
    by_category: dict[AkgCategory, AkgRecord]


@dataclass(frozen=True)
class SubstituteEntry:
    from_id: str
    to_ids: tuple[str, ...]
    reason: str


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


@functools.lru_cache(maxsize=1)
def load_catalog(path: str | None = None) -> Catalog:
    p = (_project_root() / (path or "data/normalized/ingredients.json")).resolve()
    payload = json.loads(p.read_text(encoding="utf-8"))
    raw = payload["ingredients"]
    items = tuple(
        Ingredient(
            ingredient_id=r["ingredient_id"],
            display_name=r["display_name"],
            food_group=r["food_group"],
            food_type=r.get("food_type", ""),
            nutrients_per_100g={k: float(r["nutrients_per_100g"][k]) for k in NUTRIENT_KEYS},
        )
        for r in raw
    )
    return Catalog(
        catalog_hash=payload.get("catalog_hash", "unknown"),
        ingredients=items,
    )


@functools.lru_cache(maxsize=8)
def load_prices(region: Region) -> PriceTable:
    fname = f"data/prices/{region}.yaml"
    p = (_project_root() / fname).resolve()
    if not p.exists():
        p = (_project_root() / "data/prices/national_baseline.yaml").resolve()
    payload = yaml.safe_load(p.read_text(encoding="utf-8"))
    prices = {iid: float(v["price_per_100g_idr"]) for iid, v in payload.get("ingredients", {}).items()}
    return PriceTable(region=region, prices_per_100g=prices)


@functools.lru_cache(maxsize=1)
def load_akg(path: str | None = None) -> AkgTable:
    p = (_project_root() / (path or "data/akg/permenkes-28-2019.json")).resolve()
    payload = json.loads(p.read_text(encoding="utf-8"))
    cats = payload["categories"]
    out: dict[AkgCategory, AkgRecord] = {}
    for k, v in cats.items():
        out[k] = AkgRecord(
            category=k,
            label_id=v["label_id"],
            requirements={n: float(v[n]) for n in NUTRIENT_KEYS},
        )
    return AkgTable(schema_version=payload["schema_version"], by_category=out)


@functools.lru_cache(maxsize=1)
def load_substitutes(path: str | None = None) -> tuple[SubstituteEntry, ...]:
    p = (_project_root() / (path or "data/substitutes.yaml")).resolve()
    payload = yaml.safe_load(p.read_text(encoding="utf-8"))
    return tuple(
        SubstituteEntry(from_id=e["from"], to_ids=tuple(e.get("to", [])), reason=e.get("reason", ""))
        for e in payload.get("substitutes", [])
    )


@functools.lru_cache(maxsize=1)
def load_cooking_method(path: str | None = None) -> dict[str, Any]:
    p = (_project_root() / (path or "data/cooking-method.yaml")).resolve()
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def aggregate_household_akg(members_categories: list[AkgCategory], akg: AkgTable) -> dict[str, float]:
    totals = {k: 0.0 for k in NUTRIENT_KEYS}
    for cat in members_categories:
        rec = akg.by_category[cat]
        for k in NUTRIENT_KEYS:
            totals[k] += rec.requirements[k]
    return totals

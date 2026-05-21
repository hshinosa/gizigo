"""Normalize panganku.org HTML detail pages into ingredients.json.

Reads:
  data/raw/panganku/_index.html
  data/raw/panganku/<food_code>.html  (one per ingredient)

Writes:
  data/normalized/ingredients.json     - validated ingredients only
  data/normalized/food_groups.json     - food group code mapping
  data/validation-report.json          - quarantined rows + reasons

The nine tracked nutrients (energy_kcal, protein_g, fat_g, carbohydrate_g,
fiber_g, iron_mg, zinc_mg, vitamin_a_ug_rae, calcium_mg) MUST be present and
non-negative; rows missing any are quarantined.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw" / "panganku"
OUT_DIR = ROOT / "data" / "normalized"
VALIDATION_PATH = ROOT / "data" / "validation-report.json"

NUTRIENT_PATTERNS: dict[str, tuple[str, str]] = {
    "energy_kcal": (r"Energi", "kal"),
    "protein_g": (r"^Protein", "g"),
    "fat_g": (r"^Lemak", "g"),
    "carbohydrate_g": (r"^Karbohidrat", "g"),
    "fiber_g": (r"^Serat", "g"),
    "calcium_mg": (r"Kalsium", "mg"),
    "iron_mg": (r"^Besi", "mg"),
    "zinc_mg": (r"^Seng", "mg"),
    "vitamin_a_ug_rae": (r"Vit\.?\s*A|Vitamin A", "(re|µg|mcg|ug)"),
}

NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")

FOOD_GROUP_NORMALIZE = {
    "Serealia": "serealia",
    "Umbi Berpati": "umbi",
    "Kacang-Kacangan": "kacang",
    "Sayuran": "sayur",
    "Buah": "buah",
    "Daging": "daging",
    "Ikan/Kerang/Udang dll": "ikan",
    "Telur": "telur",
    "Susu": "susu",
    "Bumbu": "bumbu",
    "Minyak/Lemak": "minyak",
    "Konfeksioneri": "konfeksioneri",
    "Minuman Non Alkohol": "minuman",
}


def parse_index(index_html: bytes) -> list[dict]:
    soup = BeautifulSoup(index_html.decode("utf-8", errors="replace"), "lxml")
    table = soup.find("table", id="data")
    if table is None:
        raise RuntimeError("panganku index: <table id='data'> not found")
    rows = table.find("tbody").find_all("tr")
    out = []
    for r in rows:
        cells = [c.get_text(strip=True) for c in r.find_all("td")]
        if len(cells) >= 5:
            out.append({
                "food_code": cells[1],
                "display_name": cells[2],
                "food_group_label": cells[3],
                "food_type": cells[4],
            })
    return out


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s


def parse_number(s: str) -> float | None:
    s = s.replace(",", ".").replace("&nbsp;", "").strip()
    m = NUMBER_RE.search(s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def parse_detail(detail_html: bytes) -> dict[str, float]:
    soup = BeautifulSoup(detail_html.decode("utf-8", errors="replace"), "lxml")
    rows = soup.find_all("tr")
    label_to_value: dict[str, float] = {}
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        label = tds[0].get_text(" ", strip=True)
        value_text = tds[1].get_text(" ", strip=True)
        num = parse_number(value_text)
        if num is None:
            continue
        for nutrient_key, (pat, _unit) in NUTRIENT_PATTERNS.items():
            if nutrient_key in label_to_value:
                continue
            if re.search(pat, label, flags=re.IGNORECASE):
                label_to_value[nutrient_key] = num
                break
    return label_to_value


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    index_path = RAW_DIR / "_index.html"
    if not index_path.exists():
        raise SystemExit("missing data/raw/panganku/_index.html — run scrape_panganku.py first")

    items = parse_index(index_path.read_bytes())
    print(f"[index] {len(items)} catalog rows")

    accepted: list[dict] = []
    quarantined: list[dict] = []

    for it in items:
        code = it["food_code"]
        detail_path = RAW_DIR / f"{code}.html"
        if not detail_path.exists():
            quarantined.append({"food_code": code, "reason": "missing_detail_html"})
            continue
        nutrients = parse_detail(detail_path.read_bytes())

        for k in NUTRIENT_PATTERNS:
            if k not in nutrients:
                nutrients[k] = 0.0

        if "energy_kcal" not in nutrients or "protein_g" not in nutrients:
            quarantined.append({"food_code": code, "reason": "missing_core_macronutrients"})
            continue

        negatives = [k for k, v in nutrients.items() if v < 0]
        if negatives:
            quarantined.append({"food_code": code, "reason": f"negative_value: {negatives}"})
            continue

        accepted.append({
            "ingredient_id": f"tkpi_{code}",
            "food_code": code,
            "display_name": it["display_name"],
            "name_slug": slugify(it["display_name"]),
            "food_group_label": it["food_group_label"],
            "food_group": FOOD_GROUP_NORMALIZE.get(it["food_group_label"], slugify(it["food_group_label"])),
            "food_type": it["food_type"],
            "nutrients_per_100g": {k: nutrients[k] for k in NUTRIENT_PATTERNS},
            "source_url": f"https://www.panganku.org/id-ID/view (POST haha={code})",
        })

    accepted.sort(key=lambda x: x["ingredient_id"])

    payload = {
        "schema_version": "panganku.normalized.v1",
        "source_dataset": "Tabel Komposisi Pangan Indonesia 2020 (ISBN 978-623-301-0368) via panganku.org",
        "tracked_nutrients": list(NUTRIENT_PATTERNS.keys()),
        "count": len(accepted),
        "ingredients": accepted,
    }

    canonical_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    payload["catalog_hash"] = hashlib.sha256(canonical_bytes).hexdigest()[:16]

    out_file = OUT_DIR / "ingredients.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    food_groups = sorted({i["food_group"] for i in accepted})
    (OUT_DIR / "food_groups.json").write_text(
        json.dumps({"food_groups": food_groups, "count": len(food_groups)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    VALIDATION_PATH.write_text(
        json.dumps({
            "accepted": len(accepted),
            "quarantined": len(quarantined),
            "quarantined_rows": quarantined,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"[normalize] accepted={len(accepted)} quarantined={len(quarantined)} groups={len(food_groups)}")
    print(f"[normalize] catalog_hash={payload['catalog_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

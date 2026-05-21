"""Scrape Tabel Komposisi Pangan Indonesia from panganku.org.

Outputs:
  data/raw/panganku/_index.html        - the catalog page
  data/raw/panganku/<food_code>.html   - per-ingredient detail
  data/raw/panganku/_meta.json         - {scrape_started, scrape_finished, count, errors}

Idempotent: if a detail file already exists, it is reused.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw" / "panganku"
INDEX_URL = "https://www.panganku.org/id-ID/semua_nutrisi"
DETAIL_URL = "https://www.panganku.org/id-ID/view"
USER_AGENT = "GiziGo/0.1 (+https://github.com/gizigo; hackathon-algofest)"
DELAY_S = 0.3


def fetch_index(client: httpx.Client) -> Path:
    out = RAW_DIR / "_index.html"
    if out.exists() and out.stat().st_size > 100_000:
        print(f"[index] cached: {out}")
        return out
    print(f"[index] GET {INDEX_URL}")
    resp = client.get(INDEX_URL, timeout=30.0)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    return out


def parse_index(index_html: bytes) -> list[dict]:
    soup = BeautifulSoup(index_html.decode("utf-8", errors="replace"), "lxml")
    table = soup.find("table", id="data")
    rows = table.find("tbody").find_all("tr")
    out = []
    for r in rows:
        cells = [c.get_text(strip=True) for c in r.find_all("td")]
        if len(cells) >= 5:
            out.append({
                "food_code": cells[1],
                "display_name": cells[2],
                "food_group": cells[3],
                "type": cells[4],
            })
    return out


def fetch_detail(client: httpx.Client, food_code: str) -> bool:
    out = RAW_DIR / f"{food_code}.html"
    if out.exists() and out.stat().st_size > 1_000:
        return True
    try:
        resp = client.post(DETAIL_URL, data={"haha": food_code}, timeout=30.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"[detail {food_code}] FAIL: {exc}", file=sys.stderr)
        return False
    out.write_bytes(resp.content)
    return True


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,*/*"}

    started = time.time()
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        index_path = fetch_index(client)
        items = parse_index(index_path.read_bytes())
        print(f"[index] parsed {len(items)} items")

        ok = 0
        errors = []
        for i, it in enumerate(items, 1):
            success = fetch_detail(client, it["food_code"])
            if success:
                ok += 1
            else:
                errors.append(it["food_code"])
            if i % 50 == 0 or i == len(items):
                elapsed = time.time() - started
                print(f"[detail] {i}/{len(items)} ok={ok} err={len(errors)} elapsed={elapsed:.1f}s")
            if not (RAW_DIR / f"{it['food_code']}.html").stat().st_size > 1_000:
                pass
            time.sleep(DELAY_S)

    meta = {
        "scrape_started_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "scrape_finished_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "expected": len(items),
        "ok": ok,
        "errors": errors,
        "source_index_url": INDEX_URL,
        "source_detail_url": DETAIL_URL,
    }
    (RAW_DIR / "_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"[done] ok={ok}/{len(items)} errors={len(errors)}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

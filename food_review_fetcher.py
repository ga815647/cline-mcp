#!/usr/bin/env python3
"""
food_review_fetcher.py — 抓 GMap 低星評論 + PTT 食記，輸出 markdown 報告。

用 SerpAPI 的兩個 engine：
  - google_maps           → 找店家拿 data_id
  - google_maps_reviews   → 依 ratingLow 抓低星評論
  - google                → site:ptt.cc 搜 PTT 食物板

範例：
  export SERPAPI_KEY=xxx
  python food_review_fetcher.py \\
      --topic "屏東 黑鮪魚" \\
      --stores "佳珍海產,王匠黑鮪魚,曾鮮黑鮪魚,漁郎生魚片" \\
      --location "Pingtung, Taiwan" \\
      --out report.md

  # 只看會打哪些 request、不真的打：
  python food_review_fetcher.py --topic "屏東 黑鮪魚" --stores "佳珍海產" --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

SERPAPI_BASE = "https://serpapi.com/search.json"
DEFAULT_TIMEOUT = 30


# ── HTTP ──────────────────────────────────────────────────────


def serpapi_get(params: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{SERPAPI_BASE}?{qs}"
    if dry_run:
        print(f"  [dry-run] GET {url[:120]}{'...' if len(url) > 120 else ''}", file=sys.stderr)
        return {}
    req = urllib.request.Request(url, headers={"User-Agent": "food-review-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


# ── GMap ──────────────────────────────────────────────────────


@dataclass
class Review:
    rating: int | None
    date: str | None
    user: str | None
    text: str

    def to_md(self) -> str:
        head = f"  - **{self.rating}★** · {self.user or '匿名'} · {self.date or '?'}"
        body = (self.text or "").strip().replace("\n", " ")
        return f"{head}\n    > {body}" if body else head


@dataclass
class StoreResult:
    name: str
    place_id: str | None = None
    data_id: str | None = None
    address: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    gmap_url: str | None = None
    low_reviews: list[Review] = field(default_factory=list)
    ptt_hits: list[dict[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def find_place(api_key: str, name: str, location: str | None, dry_run: bool) -> dict[str, Any] | None:
    """Use google_maps engine to resolve store → data_id."""
    params = {
        "engine": "google_maps",
        "q": f"{name} {location}".strip() if location else name,
        "type": "search",
        "hl": "zh-tw",
        "api_key": api_key,
    }
    data = serpapi_get(params, dry_run=dry_run)
    if dry_run:
        return None
    # google_maps engine returns either `place_results` (single) or `local_results` (list)
    if "place_results" in data and data["place_results"]:
        return data["place_results"]
    if "local_results" in data and data["local_results"]:
        return data["local_results"][0]
    return None


def fetch_low_reviews(
    api_key: str, data_id: str, want: int, dry_run: bool
) -> list[Review]:
    out: list[Review] = []
    next_token: str | None = None
    while len(out) < want:
        params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "sort_by": "ratingLow",
            "hl": "zh-tw",
            "api_key": api_key,
            "next_page_token": next_token,
        }
        data = serpapi_get(params, dry_run=dry_run)
        if dry_run:
            return []
        for r in data.get("reviews", []):
            out.append(
                Review(
                    rating=r.get("rating"),
                    date=r.get("date") or r.get("iso_date"),
                    user=(r.get("user") or {}).get("name") if isinstance(r.get("user"), dict) else r.get("user"),
                    text=r.get("snippet") or r.get("extracted_snippet", {}).get("original") or "",
                )
            )
            if len(out) >= want:
                break
        next_token = (data.get("serpapi_pagination") or {}).get("next_page_token")
        if not next_token:
            break
        time.sleep(0.5)
    # Belt-and-braces: only keep ≤3-star ones.
    return [r for r in out if (r.rating or 5) <= 3][:want]


# ── PTT via Google site search ────────────────────────────────


def fetch_ptt_hits(api_key: str, store_name: str, topic: str, want: int, dry_run: bool) -> list[dict[str, str]]:
    # Food, Pingtung, Kaohsiung 板 + 鏡像。命中後再過濾。
    q = f'site:ptt.cc ("{store_name}" OR {store_name}) {topic}'
    params = {
        "engine": "google",
        "q": q,
        "num": want,
        "hl": "zh-tw",
        "api_key": api_key,
    }
    data = serpapi_get(params, dry_run=dry_run)
    if dry_run:
        return []
    hits = []
    for item in data.get("organic_results", [])[:want]:
        hits.append(
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
        )
    return hits


# ── Pipeline ──────────────────────────────────────────────────


def process_store(
    api_key: str,
    name: str,
    topic: str,
    location: str | None,
    gmap_n: int,
    ptt_n: int,
    dry_run: bool,
) -> StoreResult:
    res = StoreResult(name=name)
    print(f"→ {name}", file=sys.stderr)

    place = find_place(api_key, name, location, dry_run)
    if place:
        res.place_id = place.get("place_id")
        res.data_id = place.get("data_id")
        res.address = place.get("address")
        res.rating = place.get("rating")
        res.reviews_count = place.get("reviews")
        res.gmap_url = place.get("link") or place.get("place_id_url")
    elif not dry_run:
        res.notes.append("找不到 Google Maps 對應店家")

    if res.data_id and gmap_n > 0:
        try:
            res.low_reviews = fetch_low_reviews(api_key, res.data_id, gmap_n, dry_run)
        except Exception as e:
            res.notes.append(f"GMap 評論抓取失敗: {e}")
    elif dry_run:
        fetch_low_reviews(api_key, "DRY", gmap_n, dry_run)

    if ptt_n > 0:
        try:
            res.ptt_hits = fetch_ptt_hits(api_key, name, topic, ptt_n, dry_run)
        except Exception as e:
            res.notes.append(f"PTT 搜尋失敗: {e}")

    return res


def render_markdown(topic: str, results: list[StoreResult]) -> str:
    lines = [f"# {topic} — 抓樣報告", ""]
    for r in results:
        lines.append(f"## {r.name}")
        meta = []
        if r.address:
            meta.append(f"地址：{r.address}")
        if r.rating is not None:
            meta.append(f"GMap：{r.rating}★ ({r.reviews_count or '?'} 則)")
        if r.gmap_url:
            meta.append(f"[Maps]({r.gmap_url})")
        if meta:
            lines.append(" · ".join(meta))
        for n in r.notes:
            lines.append(f"> ⚠️ {n}")
        lines.append("")

        lines.append(f"### Google Maps 低星 ({len(r.low_reviews)} 則)")
        if r.low_reviews:
            for rev in r.low_reviews:
                lines.append(rev.to_md())
        else:
            lines.append("  _（無 ≤3 星評論或抓取失敗）_")
        lines.append("")

        lines.append(f"### PTT site search ({len(r.ptt_hits)} 則)")
        if r.ptt_hits:
            for h in r.ptt_hits:
                lines.append(f"  - [{h['title']}]({h['link']})")
                if h.get("snippet"):
                    snippet = h["snippet"].replace("\n", " ")
                    lines.append(f"    > {snippet}")
        else:
            lines.append("  _（無命中）_")
        lines.append("")
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--topic", required=True, help='主題詞，例如 "屏東 黑鮪魚"')
    ap.add_argument("--stores", required=True, help="逗號分隔店名，或 @path 從檔案讀（一行一家）")
    ap.add_argument("--location", default=None, help='Google Maps 地點 hint，例如 "Pingtung, Taiwan"')
    ap.add_argument("--gmap-reviews", type=int, default=15, help="每家抓幾則低星評論（預設 15）")
    ap.add_argument("--ptt-results", type=int, default=8, help="每家抓幾則 PTT 命中（預設 8）")
    ap.add_argument("--out", default="report.md", help="輸出 markdown 路徑")
    ap.add_argument("--dry-run", action="store_true", help="只印要打的 request，不真的呼叫")
    args = ap.parse_args()

    api_key = os.environ.get("SERPAPI_KEY", "")
    if not api_key and not args.dry_run:
        print("ERROR: 請設定環境變數 SERPAPI_KEY，或加 --dry-run", file=sys.stderr)
        return 2

    if args.stores.startswith("@"):
        with open(args.stores[1:], encoding="utf-8") as f:
            stores = [s.strip() for s in f if s.strip() and not s.startswith("#")]
    else:
        stores = [s.strip() for s in args.stores.split(",") if s.strip()]

    if not stores:
        print("ERROR: 沒有店名", file=sys.stderr)
        return 2

    print(f"主題: {args.topic} / {len(stores)} 家店 / dry_run={args.dry_run}", file=sys.stderr)

    results = [
        process_store(
            api_key,
            name=name,
            topic=args.topic,
            location=args.location,
            gmap_n=args.gmap_reviews,
            ptt_n=args.ptt_results,
            dry_run=args.dry_run,
        )
        for name in stores
    ]

    md = render_markdown(args.topic, results)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ 寫入 {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

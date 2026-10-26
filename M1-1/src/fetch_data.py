"""Collect Naver's daily price series; keep responses for offline reproduction.

Run: python3 src/fetch_data.py
Refresh source snapshots explicitly: python3 src/fetch_data.py --refresh
Requires Python 3.10+ and only the standard library.
"""

import argparse
import csv
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_START = "2023-01-01"
ANALYSIS_END = "2026-09-30"
PREPARATION_START = "2022-07-01"
SERIES = (
    ("samsung", "005930", "삼성전자", "KRW"),
    ("sk_hynix", "000660", "SK하이닉스", "KRW"),
    ("kospi", "KOSPI", "코스피", "points"),
)
FIELDS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_series(key, symbol, name, unit, refresh):
    source_dir = ROOT / "data" / "source"
    raw_dir = ROOT / "data" / "raw"
    source_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    snapshot = source_dir / f"naver_{key}.xml"
    receipt = source_dir / f"naver_{key}.json"
    url = ("https://fchart.stock.naver.com/sise.nhn?"
           f"timeframe=day&count=1600&requestType=0&symbol={symbol}")
    if refresh or not snapshot.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type")
        encoding_match = re.search(br'encoding=["\']([^"\']+)', body[:150])
        encoding = encoding_match.group(1).decode("ascii") if encoding_match else "utf-8"
        # ElementTree's bytes parser cannot decode EUC-KR. Decode explicitly first.
        tree = ET.fromstring(body.decode(encoding))
        if not tree.findall(".//item"):
            raise ValueError(f"No daily observations returned for {symbol}")
        snapshot.write_bytes(body)
        write_json(receipt, {
            "url": url,
            "fetched_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "content_type": content_type,
            "encoding": encoding,
            "sha256": digest(snapshot),
        })
    metadata = json.loads(receipt.read_text(encoding="utf-8"))
    if digest(snapshot) != metadata["sha256"]:
        raise ValueError(f"Source snapshot hash changed: {snapshot}")
    tree = ET.fromstring(snapshot.read_bytes().decode(metadata["encoding"]))
    chart = tree.find("chartdata")
    if chart is None or chart.attrib.get("symbol") != symbol:
        raise ValueError(f"Unexpected source symbol for {symbol}")
    rows = []
    for item in tree.findall(".//item"):
        values = item.attrib["data"].split("|")
        if len(values) != len(FIELDS):
            raise ValueError(f"Unexpected row shape for {symbol}: {values}")
        date = datetime.strptime(values[0], "%Y%m%d").date().isoformat()
        if PREPARATION_START <= date <= ANALYSIS_END:
            rows.append([date, *values[1:]])
    rows.sort(key=lambda row: row[0])
    selected = [r for r in rows if ANALYSIS_START <= r[0] <= ANALYSIS_END]
    if len(selected) < 100:
        raise ValueError(f"Insufficient analysis observations for {symbol}: {len(selected)}")
    csv_path = raw_dir / f"{key}_daily.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(FIELDS)
        writer.writerows(rows)
    years = Counter(r[0][:4] for r in selected)
    return {
        "key": key, "symbol": symbol, "name": name, "price_unit": unit,
        "provider": "NAVER Finance",
        "source_url": metadata["url"], "fetched_at_kst": metadata["fetched_at_kst"],
        "source_snapshot": str(snapshot.relative_to(ROOT)), "source_sha256": digest(snapshot),
        "source_rows": len(tree.findall(".//item")),
        "csv": str(csv_path.relative_to(ROOT)), "csv_sha256": digest(csv_path),
        "saved_rows": len(rows), "saved_first_date": rows[0][0], "saved_last_date": rows[-1][0],
        "preparation_rows": len(rows) - len(selected),
        "analysis_rows": len(selected), "analysis_first_date": selected[0][0],
        "analysis_last_date": selected[-1][0], "analysis_rows_by_year": dict(sorted(years.items())),
        "date_set": set(r[0] for r in selected),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Replace snapshots with fresh source responses")
    args = parser.parse_args()
    results = [collect_series(*item, args.refresh) for item in SERIES]
    dates = set.union(*(r["date_set"] for r in results))
    collection_check = {
        "same_analysis_dates_for_all_series": all(r["date_set"] == dates for r in results),
        "analysis_union_dates": len(dates),
        "note": "Only collection coverage is checked here; independent trading-calendar and price-quality checks belong to step 3.",
    }
    for result in results:
        result["missing_dates_vs_other_series"] = sorted(dates - result.pop("date_set"))
    manifest = {
        "analysis_start": ANALYSIS_START, "analysis_end": ANALYSIS_END,
        "preparation_start": PREPARATION_START,
        "columns": FIELDS,
        "price_basis": "NAVER supplied OHLC values; no further price adjustment or dividend reinvestment applied by this script. Source XML does not label adjustment policy; this must be confirmed before final return interpretation.",
        "index_basis": "Published KOSPI index series obtained through NAVER; not a locally reconstructed index.",
        "volume_basis": "Provider values retained; index volume unit unverified, excluded from planned analysis.",
        "collection_check": collection_check, "series": results,
    }
    write_json(ROOT / "data" / "manifest.json", manifest)
    for result in results:
        print(f"{result['name']}: {result['analysis_first_date']} ~ {result['analysis_last_date']}, "
              f"analysis {result['analysis_rows']} rows, preparation {result['preparation_rows']} rows")
    print("Same analysis dates:", collection_check["same_analysis_dates_for_all_series"])


if __name__ == "__main__":
    main()

"""Resolve provider discrepancies against KRX-origin marcap data.

The upstream commit is pinned. Downloaded annual data remain in .cache/;
only the two selected stocks and comparison results are kept for this project.
"""

import csv
import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "9d890e304238340a9d40a08e680e276c8d80ceab"
FILES = {
    2022: "60ee136c6309671fb112b32ff190f7b774c3fad8",
    2023: "ecc188b0bad196701da3a0defded60c13b50ff43",
    2024: "b69c5222d015c81f19f90f581faabe4dd1a919b4",
    2025: "e817f0729b787fe03904982a37b1d84d26d70206",
    2026: "6b4bf92bcc83c6ba9a809da2eb73d112340e84f8",
}


def load_year(year):
    folder = ROOT / ".cache/marcap" / COMMIT
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"marcap-{year}.parquet"
    url = f"https://raw.githubusercontent.com/FinanceData/marcap/{COMMIT}/data/{file.name}"
    if not file.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            raw = response.read()
        digest = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if digest != FILES[year]:
            raise ValueError(f"Upstream Git blob hash mismatch: {year}")
        file.write_bytes(raw)
    raw = file.read_bytes()
    digest = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if digest != FILES[year]:
        raise ValueError(f"Cached data changed: {year}")
    frame = pd.read_parquet(file)
    if "Date" not in frame:
        frame = frame.reset_index()
    frame["Code"] = frame["Code"].astype(str).str.zfill(6)
    selected = frame.loc[frame["Code"].isin(["005930", "000660"]), ["Date", "Code", "Close"]].copy()
    selected["Date"] = pd.to_datetime(selected["Date"]).dt.strftime("%Y-%m-%d")
    selected = selected.loc[selected["Date"].between("2022-07-01", "2026-09-30")]
    print(year, "selected rows", len(selected), flush=True)
    return selected, {"year": year, "url": url, "git_blob_sha": digest, "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    loaded = list(ThreadPoolExecutor(max_workers=3).map(load_year, FILES))
    frame = pd.concat([item[0] for item in loaded]).sort_values(["Date", "Code"])
    if frame.duplicated(["Date", "Code"]).any():
        raise ValueError("Duplicate KRX-origin dates")
    records = []
    source_check = json.loads((ROOT / "results/source_verification.json").read_text())
    for key, code in [("samsung", "005930"), ("sk_hynix", "000660")]:
        with (ROOT / f"data/raw/{key}_daily.csv").open(encoding="utf-8-sig", newline="") as stream:
            naver = {row["Date"]: float(row["Close"]) for row in csv.DictReader(stream)}
        krx = dict(zip(frame.loc[frame["Code"] == code, "Date"], frame.loc[frame["Code"] == code, "Close"].astype(float)))
        mismatches = [{"Date": day, "naver_close": naver[day], "krx_close": krx[day]}
                      for day in sorted(set(naver) & set(krx)) if naver[day] != krx[day]]
        yahoo_diff = next(s for s in source_check["series"] if s["key"] == key)["price_mismatches"]
        yahoo_cases = [{**row, "krx_close": krx.get(row["Date"]),
                        "naver_matches_krx": krx.get(row["Date"]) == row["naver_close"],
                        "yahoo_matches_krx": krx.get(row["Date"]) == row["yahoo_close"]} for row in yahoo_diff]
        result = {"key": key, "code": code, "compared_rows": len(set(naver) & set(krx)),
                  "naver_krx_mismatches": mismatches, "naver_only_dates": sorted(set(naver) - set(krx)),
                  "krx_only_dates": sorted(set(krx) - set(naver)), "yahoo_discrepancy_resolution": yahoo_cases}
        records.append(result)
        print(key, "NAVER/KRX mismatches", len(mismatches), "date gaps", len(result["naver_only_dates"]), len(result["krx_only_dates"]), flush=True)
    report = {"checked_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
              "source": "FinanceData/marcap (KRX-origin daily quotes)", "commit": COMMIT,
              "upstream_files": [item[1] for item in loaded], "series": records}
    target = ROOT / "data/reference/krx_selected_close.json"
    target.write_text(frame.to_json(orient="records", force_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "results/krx_comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

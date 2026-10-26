"""Compare NAVER prices with Yahoo Finance and the XKRX calendar.

Run with the project environment: .venv/bin/python src/verify_sources.py
Existing Yahoo snapshots are reused. --refresh explicitly replaces them.
"""

import argparse
import csv
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as xcals

ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = {"samsung": "005930.KS", "sk_hynix": "000660.KS", "kospi": "^KS11"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    folder = ROOT / "data/reference"
    folder.mkdir(exist_ok=True)
    start = manifest["preparation_start"]
    end = manifest["analysis_end"]
    calendar = xcals.get_calendar("XKRX", start=start, end=end)
    expected = {day.strftime("%Y-%m-%d") for day in calendar.sessions_in_range(start, end)}
    base_calendar_count = len(expected)
    exceptions = json.loads((folder / "calendar_exceptions.json").read_text(encoding="utf-8"))
    expected -= {entry["date"] for entry in exceptions["additional_closures"]}
    calendar_data = {"provider": "exchange_calendars", "version": xcals.__version__, "calendar": "XKRX",
                     "start": start, "end": end, "sessions": sorted(expected),
                     "base_calendar_sessions": base_calendar_count,
                     "notice_confirmed_closures": exceptions["additional_closures"],
                     "source": "https://github.com/gerrymanoim/exchange_calendars"}
    (folder / "xkrx_sessions.json").write_text(json.dumps(calendar_data, indent=2) + "\n", encoding="utf-8")
    comparisons = []
    for item in manifest["series"]:
        key = item["key"]
        symbol = SYMBOLS[key]
        snapshot = folder / f"yahoo_{key}.json"
        receipt = folder / f"yahoo_{key}_receipt.json"
        begin_ts = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
        end_ts = int(datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp())
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol, safe='')}?"
               f"period1={begin_ts}&period2={end_ts}&interval=1d&events=div%2Csplits&includeAdjustedClose=true")
        if args.refresh or not snapshot.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
            data = json.loads(raw)
            if data["chart"].get("error") or not data["chart"].get("result"):
                raise ValueError(f"No Yahoo data for {symbol}")
            snapshot.write_bytes(raw)
            receipt.write_text(json.dumps({
                "url": url, "fetched_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }, indent=2) + "\n", encoding="utf-8")
        stored_receipt = json.loads(receipt.read_text(encoding="utf-8"))
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != stored_receipt["sha256"]:
            raise ValueError(f"Snapshot hash changed for {symbol}")
        result = json.loads(snapshot.read_text(encoding="utf-8"))["chart"]["result"][0]
        market_tz = ZoneInfo(result["meta"]["exchangeTimezoneName"])
        quote = result["indicators"]["quote"][0]
        yahoo = {}
        for timestamp, close in zip(result["timestamp"], quote["close"]):
            day = datetime.fromtimestamp(timestamp, market_tz).date().isoformat()
            if start <= day <= end and close is not None:
                if day in yahoo:
                    raise ValueError(f"Duplicate Yahoo date: {symbol}, {day}")
                yahoo[day] = float(close)
        with (ROOT / item["csv"]).open(encoding="utf-8-sig", newline="") as stream:
            source_rows = list(csv.DictReader(stream))
        naver = {row["Date"]: float(row["Close"]) for row in source_rows}
        tolerance = 0.02 if key == "kospi" else 0.5
        shared = sorted(set(naver) & set(yahoo))
        different = [{"Date": day, "naver_close": naver[day], "yahoo_close": yahoo[day],
                      "difference": naver[day] - yahoo[day]}
                     for day in shared if abs(naver[day] - yahoo[day]) > tolerance]
        split_events = result.get("events", {}).get("splits", {})
        splits_in_period = [event for event in split_events.values()
                            if start <= datetime.fromtimestamp(event["date"], market_tz).date().isoformat() <= end]
        record = {
            "name": item["name"], "key": key, "symbol": symbol, "compared_rows": len(shared),
            "max_absolute_difference": max((abs(naver[day] - yahoo[day]) for day in shared), default=None),
            "tolerance": tolerance, "price_mismatches": different,
            "naver_only_dates": sorted(set(naver) - set(yahoo)), "yahoo_only_dates": sorted(set(yahoo) - set(naver)),
            "missing_vs_calendar": sorted(expected - set(naver)),
            "extra_vs_calendar": sorted(set(naver) - expected), "reported_splits_in_period": splits_in_period,
            "source_snapshot": str(snapshot.relative_to(ROOT)), "source_receipt": str(receipt.relative_to(ROOT)),
        }
        comparisons.append(record)
        print(item["name"], "compared", len(shared), "price mismatches", len(different),
              "missing/extra calendar dates", len(record["missing_vs_calendar"]), len(record["extra_vs_calendar"]))
    report = {
        "checked_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "calendar": {k: v for k, v in calendar_data.items() if k != "sessions"},
        "expected_sessions": len(expected), "series": comparisons,
        "price_basis": "NAVER supplied Close compared with Yahoo Close, not Adj Close. Dividend reinvestment is excluded. Agreement supports the price series used here but does not establish the provider's adjustment rules for every corporate action.",
    }
    (ROOT / "results/source_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 추가 출처·거래일 확인", "", f"검사 시각: {report['checked_at_kst']}", "",
             "## 별도 제공처의 종가와 비교", "",
             "Yahoo Finance의 Close와 네이버 Close를 비교했다. 두 제공처의 상류 원천이 완전히 독립적이라는 의미는 아니다.", "",
             "| 대상 | 대조 날짜 수 | 허용 차이 | 차이 초과 날짜 |", "|---|---:|---:|---:|"]
    for r in comparisons:
        lines.append(f"| {r['name']} | {r['compared_rows']} | {r['tolerance']} | {len(r['price_mismatches'])} |")
    lines += ["", "## 거래일 달력 비교", "",
              f"exchange_calendars {xcals.__version__}의 XKRX 달력에 시장 공지로 확인한 2026-06-03·2026-07-17 휴장 2건을 반영했다. 준비·분석 기간은 {len(expected)}거래일이다.",
              "이 달력은 데이터의 빈 날짜를 보고 역으로 만든 것이 아닌 별도 라이브러리 기준이다. 거래소 공식 확인서를 대신하지는 않는다.", ""]
    for r in comparisons:
        lines.append(f"- {r['name']}: 달력 대비 누락 {r['missing_vs_calendar']}, 추가 {r['extra_vs_calendar']}")
    lines += ["", "## 가격 기준과 한계", "",
              "- 배당을 재투자하지 않은 가격 변화 분석이며, 배당 포함 총수익률로 표현하지 않는다.",
              "- Yahoo의 분할 이벤트도 확인했다. 실제 이벤트 목록은 JSON 결과에 기록했다.",
              "- 네이버 응답에 수정주가 정책이 명시되어 있지는 않다. 별도 제공처와의 종가 일치·이벤트 확인 결과를 근거로 사용하고 이 한계를 보고서에 남긴다.",
              "- 원본 스냅샷과 수집 시각·해시는 data/reference/에 보관했다.", "",
              "## 참고", "", "- https://github.com/gerrymanoim/exchange_calendars",
              "- https://finance.yahoo.com/quote/005930.KS/history/",
              "- https://finance.yahoo.com/quote/000660.KS/history/",
              "- https://finance.yahoo.com/quote/%5EKS11/history/", ""]
    lines += ["## 달력 보완 근거", ""]
    for exception in exceptions["additional_closures"]:
        lines.append(f"- {exception['date']} {exception['reason']}: " + ", ".join(exception["sources"]))
    (ROOT / "results/source_verification.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

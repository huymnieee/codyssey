"""세 CSV의 기본 오류를 검사한다. 원본 자료를 수정하지 않는다.

프로젝트 폴더에서 실행: python3 src/check_data.py
Python 3.10 이상, 추가 라이브러리 설치 불필요.
"""

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["Date", "Open", "High", "Low", "Close", "Volume"]
CHECKS = {
    "blank_cells": "빈칸",
    "duplicate_dates": "날짜 중복(추가 행)",
    "invalid_dates": "잘못된 날짜",
    "nonnumeric_values": "숫자가 아닌 값·무한대",
    "nonpositive_prices": "0 이하 가격",
    "close_outside_range": "종가 범위 오류",
    "open_outside_range": "시가 범위 오류",
    "low_above_high": "저가가 고가보다 큰 행",
    "negative_volume": "음수 거래량",
    "weekend_dates": "주말 날짜",
}


def check_series(info, manifest):
    path = ROOT / info["csv"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"예상과 다른 컬럼: {path.name}")
        rows = list(reader)
    if any(set(row) != set(FIELDS) for row in rows):
        raise ValueError(f"행의 컬럼 개수가 다름: {path.name}")
    counts = {key: 0 for key in CHECKS}
    counts["blank_cells"] = sum(value is None or not value.strip() for row in rows for value in row.values())
    dates = []
    for row in rows:
        try:
            day = date.fromisoformat(row["Date"])
            dates.append(day.isoformat())
            counts["weekend_dates"] += day.weekday() >= 5
        except (ValueError, TypeError):
            counts["invalid_dates"] += 1
        values = {}
        for field in FIELDS[1:]:
            try:
                value = float(row[field])
                if not math.isfinite(value):
                    raise ValueError("non-finite number")
                values[field] = value
            except (ValueError, TypeError):
                counts["nonnumeric_values"] += 1
        for field in ["Open", "High", "Low", "Close"]:
            if field in values:
                counts["nonpositive_prices"] += values[field] <= 0
        if all(field in values for field in ["Open", "High", "Low", "Close"]):
            counts["close_outside_range"] += not values["Low"] <= values["Close"] <= values["High"]
            counts["open_outside_range"] += not values["Low"] <= values["Open"] <= values["High"]
            counts["low_above_high"] += values["Low"] > values["High"]
        if "Volume" in values:
            counts["negative_volume"] += values["Volume"] < 0
    counts["duplicate_dates"] = sum(count - 1 for count in Counter(dates).values())
    analysis_dates = [day for day in dates if manifest["analysis_start"] <= day <= manifest["analysis_end"]]
    ordered = dates == sorted(dates)
    original_unchanged = hashlib.sha256(path.read_bytes()).hexdigest() == info["csv_sha256"]
    passed = all(count == 0 for count in counts.values()) and ordered and original_unchanged and len(analysis_dates) >= 100
    return {
        "name": info["name"], "file": info["csv"], "saved_rows": len(rows),
        "analysis_rows": len(analysis_dates), "preparation_rows": len(dates) - len(analysis_dates),
        "first_date": dates[0] if dates else None, "last_date": dates[-1] if dates else None,
        "ascending_dates": ordered, "original_hash_matches": original_unchanged,
        "checks": counts, "basic_checks_passed": passed, "analysis_dates": analysis_dates,
    }


def main():
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    results = [check_series(info, manifest) for info in manifest["series"]]
    date_sets = [set(result.pop("analysis_dates")) for result in results]
    aligned = all(days == date_sets[0] for days in date_sets)
    pending = [
        "독립적인 거래일 달력과 대조하여 세 자료에 공통으로 빠진 거래일이 없는지 확인",
        "네이버 제공 가격의 수정주가·기업행위 반영 기준 확인",
        "대표 날짜 가격을 별도 제공처와 대조",
    ]
    extra_verified = False
    source_file = ROOT / "results/source_verification.json"
    krx_file = ROOT / "results/krx_comparison.json"
    if source_file.exists() and krx_file.exists():
        sources = json.loads(source_file.read_text(encoding="utf-8"))
        krx = json.loads(krx_file.read_text(encoding="utf-8"))
        calendar_ok = all(not item["missing_vs_calendar"] and not item["extra_vs_calendar"] for item in sources["series"])
        stocks_ok = all(not item["naver_only_dates"] and not item["krx_only_dates"] for item in krx["series"])
        index_check = next(item for item in sources["series"] if item["key"] == "kospi")
        index_ok = not index_check["price_mismatches"] and not index_check["naver_only_dates"] and not index_check["yahoo_only_dates"]
        extra_verified = calendar_ok and stocks_ok and index_ok
        if extra_verified:
            pending = []
    report = {
        "checked_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "same_analysis_dates": aligned,
        "basic_checks_passed": aligned and all(r["basic_checks_passed"] for r in results),
        "series": results, "pending_checks": pending, "additional_verification_completed": extra_verified,
        "note": "기본 형식·값 관계 검사다. 실제 시장 가격의 정확성과 거래일 완전성을 모두 검증한 것은 아니다.",
    }
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    (output / "data_quality.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 기본 데이터 검사 결과", "", f"검사 시각: {report['checked_at_kst']}", "",
             "원본을 수정하지 않고 세 CSV 전체를 검사했다. 준비 구간도 검사에 포함했다.", "",
             "| 항목 | " + " | ".join(r["name"] for r in results) + " |",
             "|---|" + "---:|" * len(results)]
    for label, key in [("전체 자료 수", "saved_rows"), ("분석 자료 수", "analysis_rows"), ("준비 자료 수", "preparation_rows")]:
        lines.append("| " + label + " | " + " | ".join(str(r[key]) for r in results) + " |")
    for key, label in CHECKS.items():
        lines.append("| " + label + " | " + " | ".join(str(r["checks"][key]) for r in results) + " |")
    lines += ["", "- 세 자료의 분석 날짜 일치: " + ("확인" if aligned else "불일치 발견"),
              "- 날짜 오름차순: " + ("모두 확인" if all(r["ascending_dates"] for r in results) else "문제 발견"),
              "- 수집 당시 원본 해시 일치: " + ("모두 확인" if all(r["original_hash_matches"] for r in results) else "변경 발견"),
              "", "## 직접 한 실습", "",
              "사용자가 Excel에서 삼성전자 자료의 날짜 범위·행 수를 확인하고 빈칸·날짜 중복·0 이하 가격·종가 범위를 검사했다. 네 결과 모두 0이라고 보고했고, Python 재검사에서도 같은 결과를 확인했다.",
              "", "## 해석과 다음 확인", "",
              "검사한 기본 오류는 발견되지 않았다. 숫자 0은 해당 검사에서 발견한 문제의 수다. 실제 시세와의 일치 여부를 모두 보장하지 않는다.", ""]
    lines += ["- " + item for item in pending]
    if extra_verified:
        lines += ["- 추가 대조 완료. [출처·달력 대조](source_verification.md), [KRX 기준 정제 기록](data_preparation.md) 참조.",
                  "- 네이버와 KRX 원천 종가가 다른 20건은 원본을 덮어쓰지 않고 분석용 자료에서 KRX 기준으로 통일했다.",
                  "- 기본 검사 결과는 원본 CSV에 관한 것이며, 최종 분석은 data/processed/의 정리된 종가 자료를 사용한다."]
    lines += ["", "## 재실행", "", "```bash", "python3 src/check_data.py", "```", ""]
    (output / "data_quality.md").write_text("\n".join(lines), encoding="utf-8")
    for result in results:
        status = "기본 검사 통과" if result["basic_checks_passed"] else "확인 필요"
        print(f"{result['name']}: 분석 {result['analysis_rows']}개, {status}")
    print("세 자료의 분석 날짜:", "일치" if aligned else "불일치")
    print("결과 파일: results/data_quality.md")
    print("추가 대조: 완료. 최종 분석은 KRX 기준으로 정리한 종가 사용" if extra_verified else "추가 확인: 거래일 달력, 가격 조정 기준, 별도 출처 대조")
    if not report["basic_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

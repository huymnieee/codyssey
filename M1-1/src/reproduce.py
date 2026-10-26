"""Reproduce locally or collect the omitted source data for a public checkout.

Offline with stored inputs: .venv/bin/python src/reproduce.py
First public checkout:     .venv/bin/python src/reproduce.py --collect
Source snapshots and market data stay local; no automatic refresh is performed.
"""

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    "data/manifest.json",
    "data/raw/samsung_daily.csv",
    "data/raw/sk_hynix_daily.csv",
    "data/raw/kospi_daily.csv",
    "data/reference/krx_selected_close.json",
    "data/reference/xkrx_sessions.json",
    "results/source_verification.json",
    "results/krx_comparison.json",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect", action="store_true",
                        help="수집·출처 대조를 먼저 실행. 처음에는 인터넷과 약 118MB 다운로드 필요")
    args = parser.parse_args()
    (ROOT / "results").mkdir(exist_ok=True)
    scripts = []
    if args.collect:
        scripts += ["fetch_data.py", "verify_sources.py", "compare_krx.py"]
    else:
        missing = [name for name in INPUTS if not (ROOT / name).is_file()]
        if missing:
            parser.error("공개본에 포함하지 않은 입력이 필요합니다. 먼저 같은 명령 뒤에 --collect를 붙여 실행하세요. 누락: "
                         + ", ".join(missing))
    scripts += ["check_data.py", "analyze.py"]
    for script in scripts:
        print(f"\n실행: {script}", flush=True)
        subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=ROOT, check=True)
    print("\n완료: results/의 결과표와 images/의 그래프 5개를 확인하세요.", flush=True)


if __name__ == "__main__":
    main()

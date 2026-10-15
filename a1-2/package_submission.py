#!/usr/bin/env python3
"""제출에 필요한 파일만 ZIP에 담습니다. 비밀 설정 파일은 포함하지 않습니다."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from travel_planner import ROOT, clean_secrets, load_env, parse_recommendation, valid_report

SOURCE_FILES = [
    "travel_planner.py", "setup_keys.py", "package_submission.py", "README.md",
    "처음읽기.md", "여행추천_시작.command", "requirements.txt", ".env.example", ".gitignore",
    "examples/demo_fixture.json", "tests/test_pipeline.py",
    "동료평가_설명.md", "평가체크리스트.md",
]


def completed_run(results):
    if not results.exists():
        return None
    for raw in sorted(results.glob("*_raw.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(raw.read_text(encoding="utf-8"))
            if (data.get("mode") != "live" or data.get("status") != "completed"
                    or data.get("report_source") != "gemini"):
                continue
            parse_recommendation(json.dumps(data["recommendation"]))
            if not isinstance(data["restaurants"], list) or not isinstance(data["errors"], list):
                continue
            report = raw.with_name(raw.name.replace("_raw.json", "_travel_plan.md"))
            text = report.read_text(encoding="utf-8")
            if not valid_report(text, data["recommendation"], data["restaurants"]):
                continue
            return raw, report
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            continue
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="비밀 설정을 제외하고 제출 ZIP 생성")
    parser.add_argument("--starter", action="store_true", help="실제 결과 없는 준비용 코드 ZIP (완료 제출물 아님)")
    args = parser.parse_args(argv)
    try:
        load_env(ROOT / ".env")
        files = [ROOT / name for name in SOURCE_FILES]
        if not args.starter:
            run = completed_run(ROOT / "results")
            if run is None:
                print("아직 실제 API로 완성한 결과가 없습니다. 키 설정 후 --demo 없이 실행하세요.")
                print("제출용 ZIP을 만들지 않았습니다. 준비용 코드는 --starter로 묶을 수 있습니다.")
                return 1
            files.extend(run)
        for path in files:
            text = path.read_text(encoding="utf-8")
            if clean_secrets(text) != text:
                print("파일에서 설정된 비공개 키가 감지되어 ZIP 생성을 중단했습니다. 키를 출력하지 않습니다.")
                return 1
        output = ROOT / "output"
        output.mkdir(exist_ok=True)
        target = output / ("a1-2_starter.zip" if args.starter else "a1-2_submission.zip")
        with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(ROOT).as_posix())
            if args.starter:
                archive.writestr("준비상태.txt", "준비용 코드입니다. 실제 API 실행 결과가 포함되지 않았습니다.\n실제 키 설정 후 실행하고 package_submission.py로 제출 ZIP을 만드세요.\n")
        print(f"{'준비용 (실제 실행 결과 없음)' if args.starter else '제출 준비용'} ZIP: {target}")
        return 0
    except (OSError, ValueError):
        print("파일을 읽거나 ZIP을 만들 수 없습니다. 파일과 폴더 권한, .env 형식을 확인하세요.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

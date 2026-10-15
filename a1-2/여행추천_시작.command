#!/bin/zsh
# Finder에서 더블클릭해 실행할 수 있는 macOS 시작 메뉴입니다.
cd "${0:A:h}" || exit 1

finish() {
  printf '\n창을 닫아도 됩니다. Enter를 누르면 종료합니다. '
  read -r answer
}

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Python 3가 필요합니다. Python 설치 상태를 확인해 주세요.\n'
  finish
  exit 1
fi

printf '\n=== 날짜로 만드는 국내 여행 추천 ===\n\n'
printf '1. 연습 실행 (키 없이 가능, 제출용 결과 아님)\n'
printf '2. 실제 실행 + 제출 ZIP 만들기 (본인 API 키 필요)\n'
printf '3. API 키 입력 / 변경\n\n'
printf '번호를 입력하고 Enter를 누르세요 [기본: 1]: '
read -r choice

case "${choice:-1}" in
  1|2)
    if [[ "$choice" == 2 && ! -f .env ]]; then
      printf '\n먼저 본인 Gemini 키와 Kakao REST API 키를 입력하세요.\n'
      printf '키를 아직 발급받지 않았다면 Ctrl+C로 취소하고 README.md의 3번을 확인하세요.\n'
      python3 setup_keys.py || { finish; exit 1; }
    fi
    printf '\n여행 날짜를 입력하세요 (예: 2026-11-01 또는 20261101) [기본: 2026-10-20]: '
    read -r travel_date
    travel_date="${travel_date:-2026-10-20}"
    if [[ "$travel_date" == [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9] ]]; then
      travel_date="${travel_date[1,4]}-${travel_date[5,6]}-${travel_date[7,8]}"
    fi
    if [[ "$choice" == 2 ]]; then
      if python3 travel_planner.py --date "$travel_date"; then
        python3 package_submission.py
        open results
      fi
    else
      if python3 travel_planner.py --date "$travel_date" --demo; then
        open examples/demo_results
      fi
    fi
    ;;
  3)
    python3 setup_keys.py
    ;;
  *)
    printf '\n1, 2, 3 중 하나를 입력해 다시 실행해 주세요.\n'
    ;;
esac
finish

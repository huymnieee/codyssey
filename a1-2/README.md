# 날짜로 만드는 국내 여행 추천

여행 날짜를 입력하면 Gemini가 국내 도시를 추천하고, Kakao Local에서 맛집을 최대 5곳 검색한 뒤, Gemini가 여행 보고서를 작성하는 Python 프로그램입니다.

**동료평가 준비라면 [쉬운 설명과 예상 질문](동료평가_설명.md)을 먼저 읽으세요.** 처음 실행하는 분은 [처음읽기](처음읽기.md)를 참고하세요. `results/`에는 실제 API 실행 결과가 있고, `examples/`는 별도의 가상 연습 데이터입니다.

Mac에서는 `여행추천_시작.command`를 더블클릭하면 연습 실행, 실제 실행과 제출 ZIP 생성, 키 설정을 메뉴에서 선택할 수 있습니다.

검증 상태 (2026-10-15): 자동 점검 16개 통과. 저장된 실제 실행은 Gemini 추천 → Kakao 맛집 검색 → Gemini 최종 보고서를 완료했습니다. `2026-11-01` 여행 날짜로 경주 추천과 맛집 5곳을 포함한 JSON/Markdown을 생성했습니다. 완료 결과는 `mode=live`, `status=completed`, `report_source=gemini`이며 오류 목록은 비어 있습니다. [필수 요구사항 대조와 확인 근거](평가체크리스트.md)를 함께 확인할 수 있습니다. 교육기관 사이트에서의 최종 제출은 별도입니다.

## 평가자가 빠르게 확인할 내용

```text
날짜 입력 → Gemini 추천 JSON → 도시 이름 추출 → Kakao 맛집 검색
          → 추천 + 맛집을 Gemini에 전달 → Markdown 보고서 + 원본 JSON 저장
```

- 첫 번째 AI 호출은 여행지 추천, 두 번째 AI 호출은 추천과 장소 데이터를 합친 보고서 작성입니다.
- 맛집은 카카오 응답에서 가져옵니다. 검색 실패/0건은 "데이터 없음"으로 처리하고 보고서는 계속 생성합니다.
- 추천 JSON의 필수 키/타입이 틀리면 한 번만 다시 요청합니다.
- 최종 보고서는 제목뿐 아니라 각 섹션의 내용과 제공된 식당 이름/주소/분류/URL, 오전/오후/저녁 일정도 검사합니다.
- 코드 구현과 설명서 작성/점검에는 AI 도구의 도움을 받았습니다. 동작과 한계는 실제 파일을 근거로 설명합니다.

## GitHub에서 확인하고 실행하기

프로젝트 위치: [huymnieee/codyssey의 a1-2 폴더](https://github.com/huymnieee/codyssey/tree/main/a1-2)

- 실제 결과 데이터: [JSON](results/20261015_164421_456121_2026-11-01_raw.json)
- 실제 여행 보고서: [Markdown](results/20261015_164421_456121_2026-11-01_travel_plan.md)
- 제출용 묶음: [a1-2_submission.zip](output/a1-2_submission.zip)

Git이 설치된 컴퓨터에서는 아래와 같이 내려받을 수 있습니다.

```bash
git clone https://github.com/huymnieee/codyssey.git
cd codyssey/a1-2
python3 travel_planner.py --date "2026-11-01" --demo
```

실제 API를 다시 실행하려면 아래 3번에 따라 본인 키를 설정합니다. 저장소와 ZIP에는 실제 키가 포함되어 있지 않습니다.

## 1. 준비물

- Python 3.10 이상 (이 컴퓨터에서 확인한 버전: 3.11.3)
- 인터넷 연결
- Gemini API 키와 Kakao REST API 키
- 외부 Python 패키지 설치 불필요: `argparse`, `urllib`, `json` 등 표준 라이브러리만 사용

## 2. 먼저 연습 실행

다운로드/복제한 프로젝트의 `a1-2` 폴더에서 실행합니다. `git clone`을 이용했다면 위의 `cd codyssey/a1-2`로 이동합니다.

```bash
python3 travel_planner.py --date "2026-10-20" --demo
```

연습에는 키와 인터넷이 필요 없습니다. 날짜를 바꿔도 같은 가상 예제를 사용하며, `examples/demo_results/`에 JSON과 Markdown이 생깁니다. 파일에 연습용 표시가 들어갑니다. 이 파일을 실제 검색 결과로 제출하면 안 됩니다.

## 3. API 키 발급 및 설정

### Gemini

1. [Google AI Studio API 키 화면](https://aistudio.google.com/app/apikey)에 본인 Google 계정으로 로그인합니다.
2. API 키 만들기(Create API key)를 선택하고 사용할 프로젝트를 고릅니다. 화면의 동의/프로젝트 생성 절차를 완료합니다.
3. 키를 복사합니다. 계정에서 해당 모델 사용이 가능한지, 사용량 한도와 비용 조건을 확인합니다. 무료 사용 가능 여부는 계정/모델/현재 정책에 따라 다릅니다.
4. [Google 공식 키 안내](https://ai.google.dev/gemini-api/docs/api-key)를 참고할 수 있습니다.

### Kakao

1. [Kakao Developers](https://developers.kakao.com/)에 본인 Kakao 계정으로 로그인합니다.
2. 앱을 생성하거나 사용할 앱을 선택합니다.
3. 앱 관리에서 **카카오맵 → 사용 설정 → 상태 ON**으로 설정합니다.
4. 앱의 키 설정에서 **REST API 키**를 확인합니다. JavaScript 키나 어드민 키를 쓰지 않습니다. REST API 키에 필요한 사용 설정/제한도 확인합니다.
5. 2026-10-15에 확인한 [공식 사용 안내](https://developers.kakao.com/docs/ko/kakaomap/common)에 따르면 계정에서 처음 카카오맵을 활성화한 앱에 무료 쿼터가 제공됩니다. 다른 앱/한도 초과 사용은 조건이 다르니 화면을 확인합니다.

### 키를 내 컴퓨터에만 저장

아래 명령을 실행한 뒤 각 키를 한 번만 붙여 넣고 Enter를 누릅니다. **입력할 때 글자가 보이지 않는 것이 정상입니다. 반복해서 붙여 넣지 마세요.**

```bash
python3 setup_keys.py
```

이 도구는 숨김 파일 `.env`를 생성하며, 현재 사용자만 읽고 쓸 수 있는 권한으로 저장합니다. 키는 채팅에 보내지 마세요.

직접 설정하려면 `.env.example`을 `.env`로 복사한 뒤 값을 입력해도 됩니다. 한 줄에 `이름=값`으로 작성하고, 값 뒤에 주석을 붙이지 않습니다. 환경변수가 이미 있다면 `.env`보다 우선합니다.

사용하는 설정 이름:

| 설정 | 용도 |
| --- | --- |
| `GEMINI_API_KEY` | Gemini 인증 |
| `KAKAO_REST_API_KEY` | Kakao 장소 검색 인증 |
| `GEMINI_MODEL` | Gemini 모델 이름. 기본값 `gemini-3.1-flash-lite` |

모델 이름은 [Google 공식 모델 목록](https://ai.google.dev/gemini-api/docs/models)과 본인 AI Studio에서 확인하고 바꿀 수 있습니다. 이 프로그램은 Google 공식 문서의 `generateContent` REST API를 사용합니다.

## 4. 실제 실행

```bash
python3 travel_planner.py -date "2026-10-20"
```

`-date`와 `--date`를 모두 지원합니다. 반드시 날짜를 입력해야 합니다.

```text
[1/3] AI가 여행지를 추천하는 중...
  - 추천 지역: (실제 AI 추천 지역)
[2/3] 카카오에서 맛집을 검색하는 중...
  - 맛집 5곳
[3/3] AI가 최종 보고서를 작성하는 중...
원본 데이터: .../results/실행시각_여행날짜_raw.json
여행 보고서: .../results/실행시각_여행날짜_travel_plan.md
완료! 저장된 두 파일을 확인하세요.
```

위 로그는 형식 설명입니다. 검색 결과 수와 추천 지역은 실제 응답에 따라 달라집니다. 한 번 실행할 때 기본적으로 Gemini 2회와 Kakao 1회를 호출하며, 추천 JSON 오류가 있으면 Gemini를 1회 추가 호출합니다.

## 5. 저장되는 결과

실제 실행은 `results/`에 저장합니다. 기본 경로는 프로그램 파일이 있는 폴더 기준입니다. 파일명은 실행 날짜/시간과 여행 날짜를 모두 포함하며, 재실행해도 이전 결과를 덮어쓰지 않습니다.

- `*_raw.json`: 여행 날짜, 실행 시각, `mode`, `status`, `recommendation`, `restaurants`, `errors`, 제공자 원본 응답(`provider_responses`), 보고서 생성 방식(`report_source`)
- `*_travel_plan.md`: 추천 지역/이유, 일반적 날씨, 행사 후보, 맛집, 오전/오후/저녁 일정, 오류 요약

JSON에서 `mode: "live"`, `status: "completed"`, `report_source: "gemini"`인지 확인합니다. 지도 검색 실패/0건은 허용하며 `errors`에 남고 맛집은 "데이터 없음"으로 표시합니다. `mode: "demo"`는 연습 결과입니다. `incomplete`/`failed`는 오류를 해결하고 재실행해야 합니다.

추천 날씨는 실시간 예보가 아니고, 행사는 실제 개최를 확인하지 않은 후보입니다. 본 과제는 API 연결과 데이터 전달 구조를 구현하는 데 초점을 둡니다.

## 6. 오류 처리

| 상황 | 프로그램 동작 / 해결 |
| --- | --- |
| 날짜 누락/형식 오류/없는 날짜 | argparse가 사용법을 출력하고 종료 (종료 코드 2) |
| 키가 없거나 비어 있음 | API 호출 전에 종료, `.env` 설정 안내 (종료 코드 1) |
| Gemini 추천 JSON 파싱/스키마 오류 | 수정 지시 후 최대 1회 재요청, 재실패하면 오류 JSON 저장 후 종료 |
| 지도 인증/한도/네트워크/응답 오류 | `errors` 기록, 빈 맛집 목록으로 보고서 생성 계속 |
| 지도 결과 0건 | `EMPTY_RESULT` 기록, 보고서에 "데이터 없음" |
| 최종 AI 보고서 생성 실패/필수 내용 누락 | 임시 보고서와 JSON 저장, 미완료 표시 및 종료 코드 1. 재실행 필요. 제출 ZIP에서도 제외 |
| 401/403 | 키 종류, 키 값, 서비스 사용 권한, 카카오맵 ON 여부 확인 |
| 429 | 사용량/요청 한도 확인 후 나중에 재실행 |
| 404 | `GEMINI_MODEL`과 계정에서 사용할 수 있는 모델 확인 |
| 네트워크/인증서 문제 | 인터넷/Python 인증서 설정 점검. 인증서 검증을 끄지 않음 |

프로그램은 HTTP 오류의 원문/인증 헤더를 출력하지 않습니다. 결과 저장 전에도 설정된 키 값을 제거합니다.

## 7. API 키 보안

- 실제 키는 코드, README, 결과 파일에 적지 않습니다.
- `.env`는 `.gitignore`로 Git 추적에서 제외합니다. `.env.example`에는 키 값이 없습니다.
- **ZIP을 직접 만들거나 GitHub 웹에 업로드할 때도 `.env`를 제외해야 합니다.** `.gitignore`는 수동 업로드까지 막아주지 않습니다.
- `python3 package_submission.py`는 지정된 코드/설명서와 실제 결과만 묶으며 `.env`, 데모, 임시 파일을 제외합니다.
- 키가 공개되었다면 발급 서비스에서 폐기하고 새 키를 발급받습니다.
- 키를 코드와 분리하면 공유 시 노출을 줄이고 키 교체 시 코드를 고치지 않아도 됩니다.

## 8. 제출

PDF의 필수 산출물은 프로그램, 실행 결과(JSON + Markdown), README입니다. PDF에는 제출 사이트/저장소/ZIP 여부가 지정되어 있지 않으므로 교육기관의 제출 화면을 확인하세요.

```bash
python3 package_submission.py
```

`mode=live`, `status=completed`, `report_source=gemini`인 최근 실행 결과 1쌍을 찾아 코드/설명서와 함께 `output/a1-2_submission.zip`에 넣습니다. 실제 완료 결과가 없으면 ZIP을 만들지 않고 이유를 알려줍니다. 키가 들어 있는 `.env`는 포함하지 않습니다.

GitHub를 이용한다면 과제용 폴더에 같은 파일을 올리세요. 다른 과제나 기존 저장소의 README를 덮어쓰지 않도록 주의하세요.

## 9. 코드 설명과 점검

`recommend()`가 1차 JSON을 만들고 타입을 검증합니다. `search_restaurants()`는 그 JSON의 `recommended_city`로 Kakao에 GET 요청을 보냅니다. `make_report()`는 추천 JSON과 맛집 목록을 Gemini에 POST로 보내 Markdown 보고서를 만듭니다. `valid_report()`는 필수 섹션의 내용과 식당 정보, 하루 일정을 검사하며 제출 ZIP에서도 같은 검사를 사용합니다. `save_results()`는 오류 목록과 결과를 파일에 기록합니다.

```bash
python3 -m unittest discover -s tests -v
```

테스트는 외부 호출을 대체해 정상 흐름과 실패 처리를 점검합니다. 실제 키/네트워크/API 사용 권한까지 검증하는 테스트는 아닙니다.

## 공식 참고 문서

- [Gemini 구조화 출력](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
- [Kakao 장소 검색 REST API](https://developers.kakao.com/docs/ko/kakaomap/rest-api)

과제의 선택 보너스(복수 도시/캐싱)는 구현하지 않았습니다. 필수 흐름을 먼저 완성하는 범위입니다.

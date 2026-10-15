# 공부한입 · a1-3 AI 웹 개발 과제

어려운 개념을 입력하면 Gemini가 쉬운 설명, 일상 속 비유, 핵심 3가지와 확인 퀴즈를 만들어 주는 학습 웹 서비스입니다. AI와 프로그래밍을 처음 배우는 수강생을 위해 만들었습니다.

**처음이라면 [쉬운 과제 설명과 내가 할 일](docs/처음읽기.md)을 먼저 읽으세요.**

**동료평가·발표·노션 정리는 [한 번에 읽는 과제 설명과 예상 질문 26개](docs/노션용_과제설명_동료평가.md)를 이용하세요.** 과제 조건 대조, 쉬운 용어 풀이, 실제 역할, 시연 순서, 30초/2분 대본을 담은 Markdown 문서입니다.

API 질문을 실제로 실행한 [쉬운 API 학습 시연](docs/API학습시연.md)도 준비했습니다. 질문·AI 답변·퀴즈·화면 증빙을 포함하며, 사용자의 요청으로 Codex가 대신 실행한 기록입니다.

- GitHub: [huymnieee/codyssey/a1-3](https://github.com/huymnieee/codyssey/tree/main/a1-3)
- **공개 서비스: [공부한입](https://gongbu-hanip.vercel.app)**
- 로컬 미리보기: `http://127.0.0.1:8003` (이 컴퓨터에서 서버 실행 중일 때만 접속 가능)
- 2026-10-15 공개 배포 완료. 로그인 없는 접속, 실제 Gemini 답변, 300자 질문, 메뉴 이동, 모바일 화면, 학습 노트 다운로드를 확인했습니다. 본인의 사용·이해 확인과 학원 제출은 직접 진행합니다.

## 기능과 기술

- 메뉴로 이동하는 4개 구역: 소개 / AI 학습 / 사용 방법 / 도움말
- 2~500자 질문과 설명 수준 3가지 선택
- 실제 Gemini API 답변, 정답 펼치기, TXT 학습 노트 다운로드
- 데스크톱/태블릿/모바일 화면에 맞춰 조정하는 반응형 CSS
- 입력 누락, AI 오류, 네트워크, 지연/시간 초과 안내. 요청 중 중복 클릭 방지
- 프론트엔드: 순수 HTML/CSS/JavaScript. React/Vue 등 프레임워크 사용 안 함
- 백엔드: Vercel Python Serverless Function, `urllib`/`http`/`json` 표준 라이브러리
- AI: Gemini REST `generateContent`, 기본 모델 `gemini-3.1-flash-lite`
- 외부 Python 패키지가 없어 `requirements.txt`에는 이 사실을 명시

```text
a1-3/
├── index.html               화면 구조와 4개 구역
├── css/style.css            디자인과 모바일 배치
├── js/app.js                입력·fetch·결과·다운로드
├── api/learn.py             Python 백엔드와 Gemini 호출
├── images/icon.svg          직접 만든 사이트 아이콘
├── requirements.txt         외부 패키지 없음
├── vercel.json              배포·시간 제한·보안 헤더
├── .env.example             비밀 값 없는 환경 변수 예시
├── dev_server.py            로컬 연습용 서버
├── 공부한입_시작.command      Mac 실행 파일
├── docs/                    쉬운 안내·기획서·배포 가이드
├── evidence/                스크린샷·실제 API 결과·검증·AI 사용 기록
└── tests/test_api.py        API 검증 및 오류 재현 테스트
```

## 실행

Python 3.10 이상이 필요합니다. 이 컴퓨터의 로컬 검증은 Python 3.11에서 진행합니다. Vercel은 지원되는 기본 Python 런타임을 사용합니다.

Mac에서는 `공부한입_시작.command`를 더블클릭합니다. 터미널로 실행한다면:

```bash
git clone https://github.com/huymnieee/codyssey.git
cd codyssey/a1-3
cp .env.example .env
# 편집기로 .env에 본인 Gemini 키를 입력합니다.
python3 dev_server.py
```

브라우저에서 `http://127.0.0.1:8003`을 엽니다. 종료는 터미널에서 `Ctrl+C`입니다. HTML 파일만 더블클릭하거나 일반 정적 서버만 실행하면 Python API가 작동하지 않습니다.

## 환경 변수와 키

| 이름 | 역할 | 기본값 |
| --- | --- | --- |
| `GEMINI_API_KEY` | Gemini 서비스를 호출하는 비밀 키. 필수 | 없음 |
| `GEMINI_MODEL` | 사용할 모델 이름 | `gemini-3.1-flash-lite` |

로컬에서는 `.env`에서, 배포에서는 Vercel의 Environment Variables에서 읽습니다. 로컬 파일을 만들었다고 Vercel에도 자동 설정되는 것은 아닙니다. 실제 `.env`는 `.gitignore`와 `.vercelignore`로 제외합니다. 코드·README·스크린샷에 키를 넣지 않습니다.

키를 바꿀 때는 코드 수정 대신 해당 환경의 설정을 바꿉니다. 유출되면 제공자에서 폐기·재발급하고 Git 이력에도 남았는지 확인합니다. AI 호출은 계정의 비용/할당량 조건이 적용되므로 제공자 콘솔에서 확인합니다. 브라우저는 키를 보유하지 않고 우리 Python 서버만 호출합니다.

## Vercel 배포

[배포 가이드](docs/배포가이드.md)의 순서대로 GitHub 저장소를 Import하고 **Framework: Other / Root Directory: `a1-3`**를 선택합니다. 환경 변수를 Production에 등록한 뒤 Deploy합니다. 환경 변수 변경 뒤에는 Redeploy가 필요합니다.

GitHub 연동 후 코드 변경을 저장하면 Vercel이 다시 배포합니다. 실제 URL에서 메뉴, 모바일 배치, AI 답변을 재확인하고 이 README의 배포 URL과 검증 기록을 갱신합니다.

## 작동 흐름과 오류 처리

질문 → `js/app.js`의 `fetch('/api/learn')` → `api/learn.py` → Gemini → JSON 검증 → 화면 표시

클라이언트와 서버가 모두 질문 길이와 선택값을 확인합니다. 서버는 JSON 본문을 8KB로 제한합니다. AI 출력도 필수 필드와 타입을 검증하고, 프론트는 `textContent`로 표시합니다. 요청 중 버튼을 잠그고, 12초 후 지연 안내, 서버 요청 35초 제한, 브라우저 요청 48초 제한을 둡니다. 키 누락/인증/한도/네트워크/응답 형식 오류는 사용자 안내로 바꿉니다. 실패하면 이전 결과임을 표시하고 이전 학습 노트를 복원합니다.

공개 API에 전체 서버 호출 제한이나 사용자 인증은 아직 없습니다. 입력/출력 제한과 버튼 잠금은 과도한 이용을 완전히 막지 못합니다. 학원 시연 범위를 넘어 운영한다면 제공자 사용량 제한과 Vercel 방화벽/요청 제한을 추가해야 합니다. 사용자 입력은 Gemini에 전송되며 별도 서비스 DB에는 저장하지 않습니다.

## 검증과 제출물

```bash
python3 -m unittest discover -s tests -v
```

자동 테스트는 외부 호출을 대체해 정상 응답 형식과 실패 상황을 확인합니다. 실제 API 사용 가능 여부와 공개 배포 성공은 별도 검증입니다. 실행 결과, 화면 크기, 증빙의 범위와 미완료 사항은 [검증 기록](evidence/검증기록.md)에 적습니다.

| 필수 제출물 | 위치 / 현재 처리 |
| --- | --- |
| 실제 Vercel URL | https://gongbu-hanip.vercel.app |
| GitHub 코드 | 이 a1-3 폴더 |
| README | 이 문서. 실제 배포 URL과 실행/설정 방법 포함 |
| 서비스 기획서 | [기획서](docs/서비스기획서.md) |
| 화면 증빙과 AI 사용 과정 | [공개 환경 검증과 증빙](evidence/검증기록.md), [AI 사용 요약](evidence/AI사용기록.md), [실제 대화 발췌](evidence/대화발췌.md) |

추가로 [제출 전 체크리스트](docs/제출체크리스트.md)를 확인합니다. [제출 ZIP](output/a1-3_submission.zip)에도 코드·문서·공개 배포 증빙을 담았습니다. 실제 키는 포함하지 않습니다. 학원 최종 제출과 본인의 학습 확인은 직접 진행해야 합니다.

## 공식 참고

- [Gemini 텍스트 생성](https://ai.google.dev/gemini-api/docs/text-generation)
- [Gemini 구조화 출력](https://ai.google.dev/gemini-api/docs/structured-output)
- [Vercel Python API 폴더](https://vercel.com/docs/functions/runtimes/python/api-directory)
- [Vercel 하위 폴더 배포](https://vercel.com/docs/monorepos)

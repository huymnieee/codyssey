# 삼성전자·SK하이닉스 주가 비교 분석

2023년부터 2026년 9월까지 두 기업의 주가 흐름을 코스피와 비교하는 학습 프로젝트다.

- [분석 보고서](REPORT.md)
- [확보한 데이터와 출처](data/README.md)
- [수집 코드](src/fetch_data.py)
- [기본 데이터 검사 결과](results/data_quality.md)
- [검사 코드](src/check_data.py)
- [가격 기준과 정제 기록](results/data_preparation.md)
- [분석 코드](src/analyze.py)
- [첫 비교 그래프](images/01_relative_performance.png)

## 현재 진행 상태

1. 주제·기간·질문 확정: 완료
2. 데이터 수집·원본·출처 보관: 완료
3. 데이터 품질 점검·정제: 완료. 두 기업은 KRX 원천 종가로 통일하고 원본 보관
4. 분석·그래프: 지표와 그래프 5개 생성·검증 완료. 사용자 이동평균·상승률·낙폭·월별 수익률 관찰 완료
5. 리포트: REPORT.md 작성 완료. 사용자가 핵심 발견 세 가지를 본인 말로 설명
6. 검증: 계산·그래프·문서 링크와 별도 복사본 재실행 점검 완료

GitHub 위치: [huymnieee/codyssey의 M1-1](https://github.com/huymnieee/codyssey/tree/main/M1-1).

## 공개 저장소에서 처음 실행하기

공개본에는 보고서·그래프·코드·요약 결과·출처/검증 기록을 포함한다. 원본 가격 응답, 전체 일별 가격과 분석 입력은 재배포하지 않고 수집 방법을 제공한다. 아래 명령은 저장소를 받은 뒤 `M1-1` 폴더에서 실행한다. Python 3.12.14에서 검증했으며 새 환경은 Python 3.12를 권장한다.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/reproduce.py --collect
```

처음에는 인터넷이 필요하다. NAVER 원본 수집 → Yahoo·거래일 대조 → 고정한 커밋의 KRX 자료 대조 → 기본 검사 → 지표·그래프 생성 순서로 실행한다. KRX 연도별 자료는 처음 한 번 약 118MB를 내려받고 `.cache/`에 보관한다. 의존성 설치 용량은 별도다.

제공처 접근 제한이나 응답 변경 시 해당 단계에서 오류를 내고 중단한다. 수집 URL의 최신 1,600개 조회 범위는 시간이 지나면 이동하므로, 나중에 재수집한 자료가 수집 당시의 보관본과 항상 같다고 보장하지 않는다. 검증·재현 기록은 [로컬 점검 결과](results/submission_validation.json)와 [공개본 재현 점검](results/public_reproduction_validation.json)을 참조한다.

## 입력을 이미 보관한 환경에서 다시 실행하기

입력 수집이 한 번 완료되었거나 로컬 보관본을 사용하는 경우 다음 명령은 저장한 입력으로 검사·분석을 실행한다. 이 단계는 인터넷이 필요 없다.

```bash
.venv/bin/python src/reproduce.py
```

CSV만 원본 XML에서 다시 만들려면 `python3 src/fetch_data.py`를 실행한다. 기존 응답과 수집 기록이 있으면 재조회하지 않는다. 원본을 교체하는 `--refresh` 사용법과 가격 기준의 확인 범위는 [데이터 설명](data/README.md)을 참조한다.

## 데이터 기본 검사

```bash
python3 src/check_data.py
```

추가 라이브러리 설치 없이 세 자료를 검사하고 `results/data_quality.md`와 `results/data_quality.json`을 생성한다. 원본 CSV는 수정하지 않는다.

## 그래프만 재생성

필요한 입력과 라이브러리가 이미 있는 환경에서 실행한다. 공개 저장소를 처음 받았다면 위의 `--collect` 과정을 먼저 수행해야 한다.

```bash
.venv/bin/python src/analyze.py
```

저장된 선택 종가와 대조 기록으로 그래프 5개와 결과표를 재생성한다. 이 단계는 인터넷이 필요 없다. 처음 받은 NAVER CSV와 최종 분석 자료는 구분한다.

- 원본: `data/raw/`
- 분석용 자료: `data/processed/`
- 결과표·지표: `results/`
- 시각화: `images/`

## 추가 출처 대조 재실행 (선택)

```bash
.venv/bin/python src/verify_sources.py
.venv/bin/python src/compare_krx.py
```

Yahoo 응답은 로컬에 보관한 스냅샷을 재사용한다. KRX 원천의 연도별 전체 파일은 `.cache/`에 보관하고 Git에는 포함하지 않는다. 이 캐시가 없으면 고정한 커밋의 파일 약 118MB를 처음 한 번 다운로드한다. 두 기업만 선택한 종가는 실행 후 `data/reference/krx_selected_close.json`에 생성된다.

## 분석 기준

첫 비교 그래프의 출발값은 2023-01-02 종가=100이다. 전체 기간 수익률도 같은 날을 기준으로 한다. 월별·연도별 수익률은 직전 월·연도 마지막 거래일을 기준으로 하므로, 전체 기간 기준일과 구분한다. 2026년은 1~9월 자료만 포함한다. 배당을 포함한 총수익률은 계산하지 않았다.

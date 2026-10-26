# 추가 출처·거래일 확인

검사 시각: 2026-10-27T04:11:16+09:00

## 별도 제공처의 종가와 비교

Yahoo Finance의 Close와 네이버 Close를 비교했다. 두 제공처의 상류 원천이 완전히 독립적이라는 의미는 아니다.

| 대상 | 대조 날짜 수 | 허용 차이 | 차이 초과 날짜 |
|---|---:|---:|---:|
| 삼성전자 | 1037 | 0.5 | 24 |
| SK하이닉스 | 1037 | 0.5 | 21 |
| 코스피 | 1038 | 0.02 | 0 |

## 거래일 달력 비교

exchange_calendars 4.13.2의 XKRX 달력에 시장 공지로 확인한 2026-06-03·2026-07-17 휴장 2건을 반영했다. 준비·분석 기간은 1038거래일이다.
이 달력은 데이터의 빈 날짜를 보고 역으로 만든 것이 아닌 별도 라이브러리 기준이다. 거래소 공식 확인서를 대신하지는 않는다.

- 삼성전자: 달력 대비 누락 [], 추가 []
- SK하이닉스: 달력 대비 누락 [], 추가 []
- 코스피: 달력 대비 누락 [], 추가 []

## 가격 기준과 한계

- 배당을 재투자하지 않은 가격 변화 분석이며, 배당 포함 총수익률로 표현하지 않는다.
- Yahoo의 분할 이벤트도 확인했다. 실제 이벤트 목록은 JSON 결과에 기록했다.
- 네이버 응답에 수정주가 정책이 명시되어 있지는 않다. 별도 제공처와의 종가 일치·이벤트 확인 결과를 근거로 사용하고 이 한계를 보고서에 남긴다.
- 원본 스냅샷과 수집 시각·해시는 data/reference/에 보관했다.

## 참고

- https://github.com/gerrymanoim/exchange_calendars
- https://finance.yahoo.com/quote/005930.KS/history/
- https://finance.yahoo.com/quote/000660.KS/history/
- https://finance.yahoo.com/quote/%5EKS11/history/

## 달력 보완 근거

- 2026-06-03 지방선거일 휴장: https://strn.krx.co.kr/corebbs5/BHPSTRN0401/list, https://invest.kiwoom.com/inv/calendar?date=20260628
- 2026-07-17 제헌절 휴장: https://strn.krx.co.kr/corebbs5/BHPSTRN0401/list, https://securities.miraeasset.com/bbs/board/message/view.do?categoryId=1539&messageId=2340801
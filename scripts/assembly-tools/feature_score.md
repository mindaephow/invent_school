# 조립도 기능 점수 (수정요청 기반, 기록된 범위 안)

| 점수 | 기능 | 쓴 번호 | 수정요청 받은 번호 |
|---|---|---|---|
| 99 | 손으로 읽은 점(manual) | 69 | 0 |
| 95 | 다음 번호 책 대조(via) | 40 | 1 — autotarget 47 |
| 95 | 겹침 증명(overlay_check) | 99 | 4 — autotarget 15, autotarget 47, dropchecker 27, dropchecker 29 |
| 94 | 링 중심 점 | 32 | 1 — autotarget 47 |
| 93 | 격자 보조(blob·plate_match) | 10 | 0 |
| 91 | 앵커 점 PnP | 43 | 3 — autotarget 14, autotarget 15, autotarget 47 |
| 91 | 링↔구멍 대조 그림 | 51 | 4 — autotarget 47, dropchecker 24, dropchecker 27, dropchecker 29 |
| 91 | 카메라 fit 오차 >2px | 72 | 6 — autotarget 15, autotarget 47, dropchecker 8, dropchecker 9, dropchecker 11, dropchecker 27 |
| 86 | 책↔화면 비교 증거(record_check) | 214 | 29 — autotarget 14, autotarget 15, autotarget 47, catapult 24, catapult 26, catapult 34 … |
| 83 | 카메라 fit 오차 ≤2px | 139 | 23 — autotarget 14, catapult 24, catapult 26, catapult 34, catapult 35, dropchecker 1 … |
| 77 | 홀라인 자동(holefit) | 100 | 23 — catapult 4, catapult 24, catapult 26, catapult 34, catapult 35, dropchecker 1 … |
| 45 | 유추(infer_grid) | 7 | 5 — dropchecker 24, dropchecker 27, dropchecker 28, dropchecker 29, dropchecker 32 |

수정요청이 기록된 조립도: airplane(1번), autotarget(3번), battlerobot(1번), catapult(6번), dropchecker(23번), rollingbot(2번)
※ 점수 = (수정 없는 번호+3)/(쓴 번호+4)×100. 요청차이·수정저장차이 에 적힌 것만 수정요청으로 센다 — 기록이 없는 번호는 '문제 없음'으로 보인다(기록 범위의 한계).

## 빠뜨리면 어떻게 되나 (쓴 번호 대비 안 쓴 번호의 수정요청 비율)

| 기능 | 쓴 번호 수정률 | 안 쓴 번호 수정률 | 안 쓴 번호 수 | 차이 |
|---|---|---|---|---|
| 손으로 읽은 점(manual) | 0% | 19% (31/161) | 161 | +19%p |
| 겹침 증명(overlay_check) | 4% | 21% (27/131) | 131 | +17%p |
| 격자 보조(blob·plate_match) | 0% | 14% (31/220) | 220 | +14%p |
| 다음 번호 책 대조(via) | 2% | 16% (30/190) | 190 | +13%p |
| 링 중심 점 | 3% | 15% (30/198) | 198 | +12%p |
| 앵커 점 PnP | 7% | 15% (28/187) | 187 | +8%p |
| 카메라 fit 오차 >2px | 8% | 16% (25/158) | 158 | +7%p |
| 링↔구멍 대조 그림 | 8% | 15% (27/179) | 179 | +7%p |
| 책↔화면 비교 증거(record_check) | 14% | 12% (2/16) | 16 | -1%p |
| 카메라 fit 오차 ≤2px | 17% | 9% (8/91) | 91 | -8%p |
| 홀라인 자동(holefit) | 23% | 6% (8/130) | 130 | -17%p |
| 유추(infer_grid) | 71% | 12% (26/223) | 223 | -60%p |

## 어긴 규칙 유형 (요청차이 항목 수, 한 항목이 여러 유형에 걸칠 수 있음)

- 방향·기준 판독 오류: 13건
- 알고도 반영 안 함(앞뒤 번호·이미 있는 정보를 읽고도 적용 못 함 — 기능 미사용이 아님): 10건
- 도구·절차를 건너뜀(눈대중·우회): 5건
- 결합 상태(끝까지 안 꽂음·떨어짐): 5건
- 사용자 지정값 어김(되돌리기·덮어쓰기): 4건
- 확인 없이 맞다고 단정: 3건

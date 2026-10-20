---
name: feedback-survey-every-number-six-views-next-compare
description: "조립도를 하면서 계속 조사(기능 사용·수정요청 기록)하고, 번호를 끝낼 때 앞·뒤·좌·우·위·아래 6방향 확인과 다음 번호에서 같은 부분 비교를 꼭 한다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ecc3b44f-861f-4475-ab4b-28d20bbcba56
  modified: 2026-10-20T09:14:30.095Z
---

사용자 지시(2026-10-20): 앞으로 조립도를 하면서 계속 조사한다. 특히 번호를 끝낼 때 **앞·뒤·좌·우·위·아래 6방향으로 돌려 보기**와 **다음 번호에서 같은 부분 비교**는 꼭 한다. 오토타깃 47번(T축 헤드)·52~53번(결합·떨어짐)에서 이 확인이 빠져 수정요청이 나왔다.

**Why:** 한 시점만 보거나 저장된 숫자만 보고 "맞다"고 하면 떠 있는 부품·축이 따로 남는 문제(53번)를 놓친다. 기능별 점수를 매기려면 번호마다 뭘 했는지 기록이 있어야 한다.

**How to apply:** 번호를 끝내면 `python track.py <이름> <번호> --views 앞,뒤,좌,우,위,아래 --next "N+1번 책: 같은 부분 비교 내용"` 로 기록하고(빠진 방향이 출력된다), `feature_score.py` 로 점수·누락 영향을 본다. 화면 확인은 사용자 화면을 덮지 않고 기본 시점으로 되돌린다([[feedback-dont-touch-users-screen]]). 관련: [[feedback-check-all-angles-no-excuses]], [[feedback-verify-by-next-book-first]].

---
name: feedback_last_numbers_lift_and_joints
description: "끝 번호·완성에도 화면 올림(lift)을 이어 가고, 도는 부품이 나오는 번호에서 바로 관절 등록 — 검사(asmlib 끝 두 번호+완성 바닥 검사, build.py 관절 0개 경고)로 막음 (조향자동차 완성 2026-11-01)"
metadata:
  type: feedback
---

조향자동차 완성이 또 바닥 아래로 내려갔고 관절이 0개였다. 33~43번만 lift 30 으로 올리고 44·45·완성은 값이 없었으며, 자동 검사는 부품이 새로 놓이는 번호만 재서 못 잡았다.

**Why:** 사용자가 "완성 또 바닥아래", "움직이는 관절들 표시안했지?" 라고 두 번 지적. 관절 규칙은 있었으나 도구가 안 막아 내가 빠뜨렸다.

**How to apply:** 바퀴처럼 바닥 아래로 나가는 부품이 나오면 lift(xform 포함)를 마지막 번호·완성(마지막+1)까지 같은 값으로. 도는 부품이 나오는 그 번호에서 관절·묶음 등록(`_jpost_steercar.py` 본보기). 경고는 build 출력의 `바닥 아래…46단계 제자리`, `관절이 0개`.

관련: [[feedback_mark_rotating_joints]] · [[feedback_fix_rules_when_broken]]

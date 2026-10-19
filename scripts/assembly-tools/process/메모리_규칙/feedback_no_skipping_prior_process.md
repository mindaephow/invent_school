---
name: feedback-no-skipping-prior-process
description: 조립도 작업은 02→03→04→05 과정과 번호 순서를 건너뛰지 않는다 — 도구 목록이 아니라 process 파일 순서가 기준
metadata:
  node_type: memory
  type: feedback
  originSessionId: 36b84870-230b-4782-a248-9a2189fd918c
  modified: 2026-10-12T03:19:21.298Z
---

드롭체커 1번에서 04 창고 정리를 건너뛰고 격자부터 시작해 사용자가 "왜 안 해?", "규칙을 족같이 보는구나"라고 화냄(2026-10-12).

**Why:** `number_start` 의 "다음에 할 일" 목록(가위→구멍 점→방향→격자)을 순서로 착각했고, 04 가 번호 하나 안에서 해결되는 일이라고 제멋대로 판단했다. 또 SKILL 0번(판이 서 있는지 눕는지 책에서 읽기)을 안 하고 눕힌 판을 가정해 축을 계산했고, 오른쪽 위 xyz 표시판은 "그리지 않기로" 이미 코드에 있었는데 그렸다.

**How to apply:** 번호 시작 전 02·03·04 가 끝났는지부터 본다(이제 `number_start.py` 가 막는다). 판 자세는 책에서 먼저 읽는다(열이 수직이면 서 있는 판 → 줄 −Y, `axes_fit.py … +X -Y`). 오른쪽 위 방향 표시판은 삭제됨(local 만 남음) — 다시 만들지 않는다. 안 쓰는 방법은 "그리지 않는다"가 아니라 코드·문서에서 삭제한다. 관련: [[feedback_reread_rules_before_each_number]] [[feedback_hole_line_first_button]]

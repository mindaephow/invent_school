---
name: feedback-user-set-values-take-priority
description: "조립도에서 사용자가 화면에 저장한 ❄ 모습 기록·📷 카메라는 코드·내 계산보다 무조건 우선 — 번호 시작 때 먼저 읽고, 고치라고 하면 코드와 기록을 함께 맞춘다(pose_edit.py)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f9809eb2-e4fa-4aad-a01f-31235cb23c65
  modified: 2026-10-13T14:54:15.466Z
---

"무조건 사용자가 지정해놓은 걸 우선으로 해", "내가 수정해놓은 거 미리 확인해", "리벳 분리상태로 수정하라고" (드롭체커 29번).

**Why:** 사용자는 화면에서 ❄(부품 위치·자세)·📷(카메라)를 저장해 두는데, 화면은 이 기록이 코드 값(hover·cam)을 덮는다. 코드만 고치면 사용자 화면은 안 바뀌고, 내 값으로 비교 화면을 덮으면 사용자가 정해 둔 시점을 무시하게 된다. 29번에서 둘 다 해서 반복 지적받았다.
**How to apply:** ① 번호를 시작할 때 `number_start` 의 "사용자 ❄ 기록 위치가 코드와 다른 부품"·"사용자 📷 카메라"를 먼저 읽는다 ② 사용자 값이 내 값과 다르면 사용자 값을 따른다(코드 `cam` 도 맞춘다, 비교 화면에서 `br.camera` 로 덮어쓰지 않는다) ③ 사용자가 고치라고 한 부품은 코드와 ❄ 기록 둘 다 맞춘다 — `python pose_edit.py <이름> N "라벨:x,y,z"`(백업 자동), 시키지 않은 기록은 건드리지 않는다 ④ "분리해줘"는 책이 꽂힌 모양이어도 지시대로(결합 전 hover). 연관: [[feedback_separate_means_pre_assembly]], [[feedback_run_tools_before_judging]]

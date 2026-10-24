---
name: feedback_reuse_existing_assembly_sets
description: 다른 조립도에 이미 만든 반복 세트(스프라켓 바퀴 등)는 새로 계산하지 말고 가져온다 — 기본 조립세트로 등록
metadata:
  type: feedback
---

트레일러 25번 스프라켓 바퀴를 새로 계산(반지름 35)해 링크가 톱니와 안 맞았다. 드롭체커 12번에 사용자와 다듬은 배치(반지름 25.8, 링크 축 −9)가 이미 있었다. "드롭체커 때도 이렇게 했어? 같으면 가져오면 되잖아", "이 바퀴도 기본 조립세트로 등록해놔".

**Why:** 같은 부품은 항상 같은 모양이라 사용자가 한 번 다듬은 값이 정답이다. 새로 계산하면 같은 실수를 반복한다.

**How to apply:** 새 번호에서 부품 묶음을 만들기 전에 `grep 부품이름 scripts/assembly-tools/*.py` 로 다른 조립도를 먼저 본다. 있으면 그대로 옮기고, 반복될 것 같으면 asmlib 에 함수로 등록한다(스프라켓 바퀴 = `step.sprocket_wheel(중심)`). 관련: [[feedback_rivet_frames_flush]], [[feedback_port_reference_exactly]].

**스프라켓 방향(2026-10-24):** 스프라켓 돌기(+y 허브 관)는 대칭 양쪽 바퀴 모두 몸통(가운데) 쪽을 본다. 바깥에는 평평한 십자 허브 판. 26번에서 바퀴를 돌려 관이 바깥을 봐 지적받음.

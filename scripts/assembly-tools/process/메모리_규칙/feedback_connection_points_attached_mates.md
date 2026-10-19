---
name: feedback-connection-points-attached-mates
description: "연결점(초록 점·화살표)은 부품에 붙은 고정 자리 — 맞물림(mates) 방식이 새 조립도 기본, 손 보정 값(marks 등) 쓰지 않는다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 244e9d78-5086-47fd-86e5-53fbbaab0aeb
  modified: 2026-10-04T04:04:49.147Z
---

연결점은 항상 부품의 같은 자리(구멍 = 두께 가운데, 돌기 = 끝)이고 본드로 붙인 것처럼 부품과 함께 움직인다. 평소엔 안 보이고 결합할 자리일 때만 보인다. 2026-10-04 `guideMode="mates"` 로 도입해 푸시했다(7ce698e). 점·화살표는 제자리 자세로 돌기↔구멍이 맞물리는 쌍(IVS_MATES.check)에서 자동으로 만들고, 떨어져 있는 쌍만 그린다.

**Why:** 옛 방식은 단계마다 marks/faceMarks/pegDepth/thick 를 손으로 적어 화면 코드가 더하고 빼서 위치를 계산했다. 부품이 떠 있거나 옆자리에 있으면 값이 어긋나서 "점이 공중에 떠 있다", "29프레임 점이 아래 표면에 있다" 같은 지적이 6~10번 내내 반복됐다. 사용자: "연결점은 항상 똑같은 곳인데 왜 이런 문제가 발생하는지 모르겠다 / 붙어 있지만 평소에 안 보이고 결합할 장소가 있을 때만 노출".

**How to apply:** 새 조립도 뼈대(new_assembly.py)는 이미 guideMode="mates". 순서는 joinOrder(작을수록 먼저)·settleOrder·settleHover 로, 단계 이름표는 Asm.step(..., label="창고"/"불러오기"). 옛 조립도(오토건·토끼 등)는 옛 방식 그대로이니 사용자가 말하기 전엔 옮기지 않는다. 관련: [[feedback-textbook-reading-sequential]], [[project-airplane-assembly-status]].

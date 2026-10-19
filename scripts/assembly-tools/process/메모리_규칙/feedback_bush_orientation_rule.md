---
name: feedback-bush-orientation-rule
description: "bush (부시) rule — wide side outward, narrow side joins axle first and faces the clamped plate; same way every time"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 9ac604cf-f2ec-4f86-ad8a-747d4ea683cb
  modified: 2026-10-11T06:29:42.711Z
---

부시는 **넓은 쪽(모델 −y, 지름 r6)이 바깥**, **좁은 쪽(모델 +y, r5, 길이 4)이 축과 먼저 결합하고 판 쪽을 향한다**. 사용자(2026-10-11): "이건 규칙이야", "축에 결합하는 부시는 항상 같은 방식".

**Why:** 투석기 4번에서 부시2·3·4 뒤집기를 몇 번 어긋나게 읽었고(3·4 → 2·4 → 2·3), 5번·11번에서도 되풀이될 뻔했다. 방향을 말로 정하지 않고 화면에서 바로 확인해 규칙으로 못 박은 것.

**How to apply:** 부시를 놓을 때 모델 +y 가 조여 주는 판을 보게 R 을 정한다(R_AX = +y→+z, 뒤집기 R_AXF = +y→−z). 제자리는 판 바깥 면에 닿게, 띄운 시작 위치는 축 끝 바로 앞, 화살표는 축 끝으로만. 11·20·21·31·32번 부시에 같은 규칙. 가이드 ★★★★ 9번에 기록함. 관련: [[feedback-same-line-parts-check]], [[project-catapult-status]]

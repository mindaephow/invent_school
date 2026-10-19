---
name: feedback-rules-are-the-fast-way
description: "사용자의 \"빨리/10번까지\"는 규칙을 건너뛰라는 뜻이 아니다 — 규칙을 지켜야 실수가 없어 더 빠르다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2642ae62-1c8a-4475-817f-8b0fc23f8fb0
  modified: 2026-10-18T10:53:13.614Z
---

오토타깃 2~10번을 "10번까지"라는 지시에 홀라인 미달·카메라 복사·돌기↔구멍 미확인으로 밀어붙였다가 사용자가 크게 화냈다(2026-10-18): "규칙을 지키면서 10번까지 하라고 했는데", "내가 말하는 빨리는 규칙을 지켜야 실수를 하지 않고 더 빠르다는 말".

**Why:** 건너뛴 것(8번 왼쪽 블록 방향, 9번 T축 위치)이 나중에 전부 되돌려졌다. 규칙을 건너뛴 속도는 가짜다.

**How to apply:** 범위 지시("N번까지")가 와도 번호마다 규칙 전부(홀라인 → 축·카메라 → 돌기↔구멍 대응표 `_mates_table.py` → 화면 비교 → 증거)를 한다. 홀라인이 막히면 그 번호에서 멈추고 보고한다. 이웃 번호 카메라 복사·짐작은 쓰지 않는다. [[feedback-stop-when-big-mismatch]] [[feedback-new-warehouse-at-origin]]

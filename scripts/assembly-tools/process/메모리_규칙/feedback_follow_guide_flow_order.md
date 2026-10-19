---
name: follow-guide-flow-order
description: "새 조립도는 안내서 \"작업 흐름\"(단계 0→1 번호등록⏸→2 창고정리⏸→3 쪽작업) 순서 그대로 — 쪽 작업으로 먼저 뛰어들지 않는다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0e930da7-539d-497e-a20f-22a9b8cdd84d
  modified: 2026-10-05T10:29:08.700Z
---

배틀로봇을 시작할 때 안내서 "작업 흐름"을 안 읽고 쪽(91·92)부터 읽고 뼈대만 만든 뒤 "1~8단계"라고 말해 관리자가 크게 화냄("자동화·MCP를 만들어도 총감독이 병신") — 번호 등록·창고 정리 ⏸ 두 번을 건너뛴 것.

**Why:** 이 순서 규칙을 관리자가 직접 만들어 둠. 지키지 않으면 앞 단계 보고·확인 없이 뒤로 가서 다 뒤엎게 된다.
**How to apply:** 새 조립도 요청이 오면 첫 행동 = get_assembly_guide(또는 app/lib/cubo-assembly-guide.js "작업 흐름" 절) 읽기. 단계 1(전 쪽 훑어 번호·번호표·"뒤집기" 표 → noPart 뼈대 전부 등록 → ⏸ 보고) → 단계 2(창고 표 → ⏸) → 그 다음 쪽 작업. 사용자가 "N쪽까지"라고 해도 단계 1·2 를 먼저 한다. 관련: [[feedback-do-only-the-stated-step]]

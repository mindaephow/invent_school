---
name: feedback-rulecheck-no-workarounds
description: 막히면 도구·기준을 바꿔 지나가지 않는다 — 05_조립 0-1 순서(holefit→infer_grid…)로 풀고, 못 풀어도 멈추지 않고 책을 뒤져 해답을 찾는다(rulecheck.py 가 자동 판정)
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3dd4888b-70a4-43c3-90e6-2b93bfcaa7b9
  modified: 2026-11-02T00:00:00.000Z
---

holefit 옵션 추가·손으로 만든 격자·추정 카메라로 기준을 우회하지 않는다. `rulecheck.py` 가 격자 출처·카메라 오차(≤2px)·증거·읽기 표를 자동 판정한다. (2026-11-02 정정: 예전 "막히면 멈춰 사용자에게 보고"는 삭제 — 멈추지 않고 규칙 순서 확인 → 05_조립 0-1 순서 → 책 뒤지기 → 정할 수 없는 것만 ⚠ + 한 줄 질문.)

**Why:** 우회하면 틀린 격자가 뒤 번호로 번진다. 멈추면 시간만 쓴다.

**How to apply:** `00_규칙.md` C3·B5·B6. 새 교정은 이 파일에 적는다.

---
name: feedback-reread-rules-before-each-number
description: "before starting each cubo-assembly number, re-read SKILL.md from the top (not from memory) and state 3 rules to keep; don't jump into grid-fitting before scanning the picture"
metadata:
  node_type: memory
  type: feedback
  originSessionId: dfe39b7f-605d-4b04-8107-e8cc1f917f3b
  modified: 2026-10-11T11:32:15.315Z
---

사용자(2026-10-11, 투석기 17번): "규칙은 규칙을 먼저 다시 보는 거야." 17번에서 책 그림을 훑어 세기 전에 격자부터 맞추기 시작하자 "규칙이 격자야?"라고 지적.

**Why:** 같은 세션에서 규칙을 기억으로만 따라 순서를 건너뛰고(16번 axes 복사, 창고 확인 누락, noGuide·hideMade 우회성 수정), 매번 사용자가 지적해서야 고쳤다.

**How to apply:** 번호를 시작할 때마다 ① `.claude/skills/cubo-assembly/SKILL.md` 를 처음부터 다시 읽고 ② 안내서 단계 4·6-1 과 직전 번호 위반 사례를 확인한 뒤 ③ 첫 보고 한 줄에 "이번 번호에서 지킬 규칙 3개"를 적는다. 순서: 그림 훑어 세기(왼→오·위→아래) → 카메라 면 → 격자 → axes_fit → 읽기 표 → 놓기 → 빌드 → 화면 비교 → 증거. 검사를 끄는 표시(noGuide 등)는 달지 않고 경고는 끄지 말고 보고. 관련: [[feedback-fix-rules-when-broken]], [[feedback-no-bypass-options]]

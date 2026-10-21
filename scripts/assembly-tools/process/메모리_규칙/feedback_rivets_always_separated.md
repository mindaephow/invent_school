---
name: feedback-rivets-always-separated
description: "조립도에서 리벳·T축·부시·볼트·너트는 책이 꽂은 모양이어도 항상 결합 전(띄워 화살표)으로 — seated 쓰지 않음, 사용자 지시를 기다리지 않는다"
metadata:
  type: feedback
---

리벳 등 체결 부품은 모든 번호에서 결합 전 모습(hover 24 + 화살표)으로 만든다. 05_조립.md 표 4번·가이드 6-1 13번에 이미 있는 규칙이다.

**Why:** 바이킹 21~25번에서 `seated`(꽂힌 채)로 만들었다 — 05_조립.md 의 다른 줄("책이 꽂아 둔 리벳은 seated")을 근거로 삼았기 때문. 사용자가 7·15·20번에 이어 21·22번에서 "왜 자꾸 합쳐놓는거야? 규칙에 내용이 없어?"라고 화냄(2026-10-22). 규칙은 있었고 내가 모순된 줄을 골랐다.
**How to apply:** 새 리벳은 `attach(..., rivet=True, hover=24)`(또는 Part 직접 추가 시 dir·hover·marks). 번호를 시작할 때 05 표 4번을 읽는다. `seated` 는 사용자가 "꽂힌 채로"라고 명시했을 때만. [[feedback_separate_means_pre_assembly]] [[feedback_fix_rules_when_broken]]

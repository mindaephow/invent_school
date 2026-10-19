---
name: feedback-fix-rules-when-broken
description: "when I break a cubo-assembly rule, find why it happened and rewrite the rule/tool (guide + SKILL.md + helper script) in the same turn so it can't recur; don't just apologize"
metadata:
  node_type: memory
  type: feedback
  originSessionId: dfe39b7f-605d-4b04-8107-e8cc1f917f3b
  modified: 2026-10-11T08:06:17.943Z
---

사용자(2026-10-11, 투석기 16번): "매번 규칙을 안 지키면 왜 안 지켰는지 파악해서 규칙을 지키도록 수정해서 덮어써줘."

**Why:** 같은 종류의 위반이 번호마다 되풀이됐다(우회 옵션, 앞 번호 값 복사 등). 사과·다짐은 소용없고, 규칙 문구가 빈틈이 있었거나 확인 장치가 없었던 것이 원인이라는 판단.

**How to apply:** 위반이 드러나면 ① 원인을 한 줄로 찾는다(조건부 문구, 확인 장치 부재, 번거로운 절차 등) ② `app/lib/cubo-assembly-guide.js`(백틱은 \` 로 이스케이프, `node --check`) 와 `.claude/skills/cubo-assembly/SKILL.md` 에 조건 없는 문장으로 덮어쓰고 ③ 가능하면 값을 손으로 안 쓰게 하는 도구를 만든다 ④ 사용자에게 원인·고친 곳을 보고한다. build.py·stepchecks.py 의 검사는 사용자가 지시할 때만 고친다([[feedback-no-bypass-options]]).

예: 16번 `_axes.json` 을 15번 값에서 출발해 적음 → 가이드 ★★★★ 7번·SKILL 에 "카메라·축은 번호마다 그 번호 격자에서 계산, 복사 금지" 추가, `axes_fit.py` 신설([[project-catapult-status]]).

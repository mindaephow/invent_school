---
name: feedback-automate-decide-and-send-photos
description: 조립도 번호는 내가 판단해 멈추지 않고 이어 가고, 번호마다 책 그림+우리 화면을 폰으로 보내 비차단 허락을 받는다; 사용자 ✓ 대기 때문에 멈추지 않는다
metadata:
  type: feedback
---

"막힌 게 없는데 왜 멈춰, 바로바로 진행해야지", "내가 체크한 거 필요 없다", "니가 판단을 해야 자동화", "아니면 바로바로 책 모습과 완성 모습을 핸드폰으로 보내주고 허락을 받던가" (드롭체커 30번, 2026-10-14).

**Why:** 28~30번에서 규칙 점검이 "유추 격자는 사용자 ✓ 필요"로 ❌ 를 내서 번호마다 멈추고 보고했더니 사용자가 자동화가 아니라고 화냈다. 사용자는 ✓ 를 누르는 일이 필요 없길 원한다.
**How to apply:** 번호를 끝내면(빌드 0건·비교 증거·읽기 표·DB 그림) 사용자 ✓ 를 기다리지 않고 다음 번호로 간다. 번호마다 `SendUserFile`(status proactive)로 책 `refs/<이름>/NN.jpg` + 비교 화면 `refs/<이름>/cmp/NN.png` 를 보내 "이상하면 말씀해 주세요, 답 없으면 계속"이라고 알린다. 사용자가 이상하다고 하면 그 번호만 고친다. 규칙 점검 ❌ 는 묻지 말고 근거로 판단해 고친다(검사 코드 수정은 사용자가 지시했을 때만 — 이번엔 "✓ 필요 없다"가 지시). 연관: [[feedback_run_tools_before_judging]], [[feedback_user_set_values_take_priority]], [[feedback_windmill_finish_all_no_stepwise_confirm]]

---
name: feedback-fix-means-keep-edit-and-request-unlock
description: "사용자가 '수정해'라고 했는데 ✓ 잠금에 막히면 코드 수정은 되돌리지 말고 그대로 두고, 사용자에게 ✓ 해제를 요청한다"
metadata:
  type: feedback
---

드롭체커 31번 T축(윗끝이 큰기어 윗면 +1mm) 수정 지시가 ✓ 잠금에 막히자 내가 코드를 되돌렸고, 사용자가 "내가 수정하라고 했을 땐 되돌리지 말고 요청을 해"라고 함.

**Why:** 지시는 이미 내려졌다. 되돌리면 지시를 취소한 것이 되고 사용자가 같은 말을 반복해야 한다.
**How to apply:** 수정 지시 → 코드는 수정한 채 둔다. 빌드가 ✓ 잠금으로 막히면 어느 번호의 ✓ 해제가 필요한지 한 줄로 요청하고 기다린다(우회 금지). 연관: [[feedback_no_bypass_options]], [[feedback_follow_admin_fix_instructions]]

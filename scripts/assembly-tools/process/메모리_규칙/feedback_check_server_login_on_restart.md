---
name: feedback-check-server-login-on-restart
description: 조립도 작업을 (다시) 시작할 때 첫 단계로 개발서버(3178)와 설계 화면 로그인 상태를 확인하고 사용자에게 먼저 요청한다
metadata:
  node_type: memory
  type: feedback
  originSessionId: f7b8fed8-ac05-44b1-b7d0-7be5f9b52042
  modified: 2026-10-13T02:25:08.521Z
---

세션을 새로 시작하거나 번호 작업을 다시 시작할 때, 규칙 읽기·계산에 들어가기 **전에** 개발서버(`npm run dev -- -p 3178`)가 떠 있는지와 설계 화면 로그인이 되어 있는지 확인하고, 안 되어 있으면 사용자에게 먼저 요청한다. (2026-10-13 드롭체커 24번 재작업 시작 때 건너뛰어 지적받음 — "항상 다시 시작하면 개발서버와 로그인을 체크해서 먼저 요청을 해야지")

**Why:** 화면 비교(05 5-5)와 증거(record_check)에 로그인된 화면이 필요하고, 계산을 다 한 뒤에야 서버·로그인이 없다고 알리면 흐름이 끊긴다. 비밀번호는 대신 입력하지 않으므로 로그인은 사용자 몫이다.

**How to apply:** 첫 도구 호출 묶음에 서버 응답 확인(curl localhost:3178), `.env.local` 존재, (브라우저 pane 이 있으면) 로그인 여부를 넣고, 빠진 것은 한 줄로 요청한 뒤 계산 작업은 계속 진행한다. [[feedback_exact_clicks_one_step]]

---
name: feedback-dont-stop-for-gate-confirmations
description: "조립도 작업 중 \"사용자 확인\" 문턱(방향선 그림 등)에서 멈춰 묻지 않는다 — 추정은 추정으로 표시하고 끝까지 이어 간다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2642ae62-1c8a-4475-817f-8b0fc23f8fb0
  modified: 2026-10-17T05:33:27.204Z
---

어보이더 24~30번·배틀로봇 7차시에서 "특별한 문제 없으면 그냥 끝까지 계속 이어서 하는 거야, 한 페이지 단위로"라고 지시했는데, 배틀로봇 방향선 그림 확인 앞에서 wrap_up 으로 멈춰 물었다. 사용자가 "돌았어?", "왜 이게 자꾸 반복될까?"라고 화냄(2026-10-17).

**Why:** 사용자는 자동화를 원한다. 절차 문서(number_start 의 "사용자 확인" 문턱, 02 3-2 방향선)는 내가 판단해 표시하고 넘어가면 되는 것이지 멈출 이유가 아니다. 긴 대화가 요약되면서 이 지시가 약해져 반복됨.

**How to apply:** 번호·차시 작업 중 사용자가 꼭 정해야 하는 사실(책 그림으로 못 정하는 하나)이 아니면 질문·wrap_up 으로 멈추지 않는다. 방향선·읽기 표·USED 같은 건 내가 정해 "추정"으로 적고 계속하며, 확인 요청은 한 번호가 끝났을 때 결과 보고에 한 줄로만 붙인다. 게이트가 막으면 `--연속` 같은 표시 옵션이나 우회가 아니라 막힌 항목을 실제로 채운다(우회 옵션 금지는 그대로). 푸시는 여전히 "업로드"라고 할 때만. [[feedback_windmill_finish_all_no_stepwise_confirm]] [[feedback_automate_decide_and_send_photos]]

---
name: feedback-run-tools-before-judging
description: "조립도 번호가 막힐 때 눈으로 \"안 된다\" 판단하고 건너뛰지 말고 도구를 먼저 돌린다; 앞 번호에서 우리가 만든 조립(모델)과 책 그림은 3D 확정 앵커·검증 점이다; 칸 선택은 순방향 투영"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f9809eb2-e4fa-4aad-a01f-31235cb23c65
  modified: 2026-10-13T14:48:45.442Z
---

드롭체커 29번에서 판이 가려져 보인다고 `holefit` 을 돌리지 않고 "앵커 5개뿐"이라 보고했다가 사용자가 "28번 조립을 우리가 했잖아", "역투영을 왜 해", "그 정보를 알고도 유추가 안 돼?"라고 화냈다.

**Why:** 사용자는 이미 확정된 앞 번호 정보(모델 3D, 책 그림, 읽기 표)를 새 번호의 출발점으로 쓰길 원한다. 눈 판단·질문·"안 됩니다" 보고는 시간을 낭비하고 지치게 한다.
**How to apply:** ① 막히면 도구(holefit → `plate_match.py` → `infer_grid` 앵커)를 실제로 돌려 숫자로 말한다 ② 앞 번호에서 놓은 부품의 3D 는 앵커·검증 점(리벳 끝·블록 돌기·판 모서리) ③ 구멍 무늬 반복으로 칸이 밀리면 앵커를 **순방향 투영**(모델 3D → 픽셀)한 오차로 고른다 ④ 유추 격자는 규칙 점검이 사용자 ✓ 를 요구하니 나머지를 다 끝낸 뒤 "격자만 ✓ 대기"로 한 번에 보고한다. 연관: [[project_dropchecker_28_status]], [[feedback_rulecheck_no_workarounds]], [[feedback_separate_means_pre_assembly]]

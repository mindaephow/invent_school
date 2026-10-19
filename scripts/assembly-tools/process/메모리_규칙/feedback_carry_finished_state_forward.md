---
name: feedback-carry-finished-state-forward
description: "완성·승인된 단계의 모양은 뒤 단계(창고 작업 뒤·반대쪽 작업)에도 이어 간다; 알면서 \"물어보기만\" 하지 말고 바로 적용"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d3ad27b4-eef8-49b6-b222-f6d8c762fbd3
  modified: 2026-10-06T20:36:09.290Z
---

한 단계에서 완성한 모양(예: 24번 기울인 다리+작은 판+회색 판)은 이후 단계에서 되돌아가면 안 된다. 반대쪽을 만든 뒤에도 앞쪽 완성 모양이 이어져야 한다.

**Why:** 꼬마기사 26~36번에서 왼쪽 다리가 서 있는 자세로 돌아갔고, 29→30번에서 오른쪽도 같은 일이 났다. 두 번째는 제가 알고도 "적용할까요?"로 물어서 "아까 했던 병신짓을 또 반복하는 거냐"는 말을 들었다.
**How to apply:** 새 단계/반대쪽을 만들 때 앞 단계 완성 모양의 poseAt·lift·noFreeze 가 뒤 단계에 이어지는지 먼저 센다. 같은 종류의 누락을 발견하면 묻지 말고 바로 적용하고 보고한다(질문은 관리자 지시와 충돌할 때만). See [[feedback-do-only-the-stated-step]], [[project-kidknight-status]].

---
name: project-bush-rule-cleanup-deferred
description: "부시 방향 규칙을 DB 로 강제하려던 작업 — 보류(2026-10-11); 어긋난 부시 9개 목록, DB 변경 시 11개 조립도 깨짐, ❄ 기록 반영 코드는 푸시됨"
metadata:
  node_type: memory
  type: project
  originSessionId: 9ac604cf-f2ec-4f86-ad8a-747d4ea683cb
  modified: 2026-10-11T12:44:58.165Z
---

2026-10-11. 부시를 항상 규칙대로(좁은 쪽 모델 +y 가 판 쪽) 조립되게 하려고 DB 연결점을 손봤으나 **보류**. 사용자: "나머지 9개 나중에 해도 돼, 지금 중요한 게 아님".

- 완료·푸시(b53524b): 135도 프레임·작은기어·큰기어·축·T축·부시 연결점 `checked`(구조는 사용자 확인), 양팔저울 8번 부시 뒤집음, `applyPoseRotations`(❄ 회전을 validate_assembly·연결점 영향 검사에 반영, 위치는 hover 자리라 안 씀).
- **DB 부시 구멍을 through=false 로 바꾸면 안 됨**: 완료 조립도 11개에서 부시 40여 개가 "허공에 뜸"으로 표시됨(원인 둘: 실제 반대 방향 부시 + 축이 돌기 한 개만 기록돼 축 방향에 따라 판정이 갈림). 되돌려 둠(through=true).
- 남은 어긋남(❄ 반영 후, 눈 확인 전): 풍차 20, 로봇팽이 26, 3륜바이크 26, 축구로봇 6(2개), 오토건 11, 꼬마기사 10(2개). 불분명(닿는 부품 안 잡힘): 포뮬러원 9·10, 스피드바이크 34~37 등.
- 하려면: 어긋난 부시를 화면에서 확인·뒤집기 → 축을 양 끝 돌기 2개로 기록 + 부시 through=false. 대안: asmlib `bush()` 함수(앞으로 만드는 것만).
- 분석 스크립트: 임시 `bush3.py`(scratchpad/TEMP, 저장소 아님).

**Why:** 사용자가 "DB 수정하면 이상하게 되는 게 문제 아니냐", "내가 수정한 기록(❄)이 적용 안 되는 것 같다"고 지적 — 두 말이 다 맞았음. **How to apply:** 부시/축 연결점을 다시 건드리기 전에 위 목록과 ❄ 반영 여부를 확인하고, 한 번에 바꾸지 말고 영향 검사 결과를 먼저 본다. 관련: [[feedback-bush-orientation-rule]], [[project-catapult-status]].

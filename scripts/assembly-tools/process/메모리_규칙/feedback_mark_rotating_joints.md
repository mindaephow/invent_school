---
name: feedback-mark-rotating-joints
description: 조립도에서 도는 곳(바퀴·기어·팔 축·핀)은 번호를 만들 때 바로 관절로 등록해 항상 표시 — 모터 직결 축만 [모터직결] 형광라임
metadata:
  type: feedback
---

회전하는 곳은 항상 관절(ivs_assembly_joints + joint_groups)로 표시한다. 사마귀로봇 37~38번에서 바퀴(모터 동력 회전)가 표시 안 돼 있다고 지적받음(2026-10-16) — 관절 기능이 새로 들어왔는데 35~40번 작업 때 빠뜨림.

**Why:** 사용자가 조립도에서 어디가 도는지 색으로 바로 보길 원함. 모터에 직접 연결된 회전만 형광라임, 다른 회전은 분홍 유지.

**How to apply:** 번호를 끝내기 전 "도는 부품 있나? 관절 등록했나?" 확인. 모터 직결 구동 축은 관절 note 에 `[모터직결]`. 저장소 CLAUDE.md·process/05_조립.md 에도 적어 둠. 관련: [[feedback_dont_touch_users_screen]].

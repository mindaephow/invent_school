---
name: project-viking-status
description: "큐보 2권 9차시 바이킹 조립도 — 1~28번 완료(2026-10-22), 29번부터 남음; 상세 인계는 저장소 진행기록 파일"
metadata:
  node_type: memory
  type: project
  modified: 2026-10-21T03:28:28.915Z
  originSessionId: 2ef35a69-c7cb-41c6-af90-e703a7ea8781
---

바이킹(cubo-2-viking, 2권 9차시, 교재 81~87쪽, 36번) 조립도: 2026-10-22 기준 **1~28번 완료**(증거·5방향·DB 그림·via), **29번부터 남음**. 리벳은 모든 번호에서 결합 전(분리) — 21~25번을 seated 로 했다가 지적받아 고침([[feedback_rivets_always_separated]]). 리벳은 6~25번 전부 분리로 고침. 26번 = 창고 3 바퀴 세트 둘, 27번 = 그 둘을 배 끝 기운 3단블록 돌기에 끼움(3.8px ⚠), 28번 = 배를 90° 돌려 문틀에 넣고 축·큰기어·부시(2.6px ⚠). 관절 DB 등록함(바퀴 축·큰기어 축).

**Why:** 사용자가 번호에서 멈추거나 변명하면 크게 화냄. 번호마다 화면에서 직접 확인하고 넘어가길 원함.
**How to apply:** 시작은 `invent_school/scripts/assembly-tools/process/진행기록_viking.md` 맨 위 "★ 다음 세션 인계". 서버 3178·로그인(포트별) 먼저. 새 창고 판은 숨은 부품 돌기와 5mm 넘게 떨어지게 놓고(안 그러면 잠금 기록이 붙어 빌드마다 위치가 바뀜), 앞 번호 내용이 바뀌면 낡은 증거를 다시 남긴다(진행기록 "함정" 참고). 판 구멍 격자는 `latgrow.py`. [[feedback_stop_when_big_mismatch]] [[feedback_check_all_angles_no_excuses]]

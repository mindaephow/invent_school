---
name: project-bowling-status
description: "볼링머신 조립도 — 1~36번 완료·37번은 케이블 연결(부품 없음)(2026-10-25, 푸시 전; 22·24~36번 격자·카메라 기준 미달 — 사용자 허락으로 진행), 남은 것은 사용자 확인·푸시"
metadata:
  node_type: memory
  type: project
  originSessionId: 90e536e8-f2e7-428d-b903-722980c8e109
  modified: 2026-10-25T05:33:13.674Z
---

볼링머신(큐보 2권 11차시, cubo-2-bowling) 1~27번 모델·증거·읽기 표·DB 그림까지 끝(22·24~26번은 격자·카메라 기준 미달), 푸시 전. 상세·다음 할 일은 저장소 `scripts/assembly-tools/process/진행기록_bowling.md` 맨 위.

**Why:** 사용자가 "20번까지 해줘"(2026-10-25)라고 해서 15~20번을 이어서 만들었다. 27번부터와 16~26번 둘째 벌(복사) 처리가 남음. bowling.py RELOCK=True 고정(빌드 뒤집힘 방지).

**How to apply:** 일부만 보이는 판의 holefit 격자는 한 칸 밀릴 수 있으니 판 위 확정 3D 점(모터 특징점)을 투영해 밀림을 확인하고, 3단블록 돌기 면(±z)·큰 구멍 면(±y)은 뒤 번호의 같은 면 돌기로 확정한다. [[feedback_run_tools_before_judging]] 참고.

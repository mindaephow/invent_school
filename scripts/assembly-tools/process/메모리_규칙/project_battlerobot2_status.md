---
name: project-battlerobot2-status
description: 큐보 2권 7차시 배틀로봇(cubo-2-battlerobot) 조립도 1~37번 완성 상태·추정 목록·도구 함정 (2026-10-17)
metadata:
  node_type: memory
  type: project
  originSessionId: 2642ae62-1c8a-4475-817f-8b0fc23f8fb0
  modified: 2026-10-17T11:24:29.948Z
---

배틀로봇 조립도 1~37번을 모두 만들고 번호별 비교 증거를 남겼다(2026-10-17). 관절 6개 DB 등록, 책 그림 148장 DB 업로드 완료. **푸시는 안 했다(사용자가 "업로드"라고 할 때만)** — 변경 파일: battlerobot2.py·_read.json·fits·refs 외 pnp.py·overlay_check.py·새 도구(_xfer·_tick·_rd·_jpost 등), public/design-assemblies.js.

**Why:** 사용자가 "끝까지 이어서, 막히면 추정으로 표시하고 계속"을 지시했다([[feedback-dont-stop-for-gate-confirmations]]).

**How to apply:** 이어서 할 때 `scripts/assembly-tools/process/진행기록_battlerobot2.md` 를 먼저 읽는다. 추정·불확실: 32·36번(큰 판이 팔 끝에 붙는 자세, PnP 못 풀어 눈 카메라), 34번 판 펼침 방향, 29번 거울 해, 카메라 오차 큰 번호들. 함정: `battlerobot2_links.json` 의 `place` 잠금이 낡으면 부품이 옛 위치로 끌려간다(이름으로 지워서 해결); `build --write` 는 새 번호면 부품 없는 합치기 번호도 NN_1/NN_2(refs_rect)·읽기 표 부품 "없음(…)" 이 있어야 통과.

---
name: project-probo-connect-parts-workflow
description: "프로보 커넥트 3D 부품 만들 때 반복된 실수 — 기존 생성기 읽기, 부품 관리에서 보여주기, 숫자 오타 해석"
metadata:
  node_type: memory
  type: project
  originSessionId: d23b294b-4abb-4fbf-963d-542f38772228
  modified: 2026-10-29T17:31:28.964Z
---

치수·모양은 저장소(`scripts/make-proboconnect-*.mjs`)와 DB 에 있으니 여기엔 적지 않는다.

- 새 프로보 부품은 **먼저 `scripts/make-proboconnect-*.mjs` 와 `register-proboconnect-parts.mjs` 를 읽고** 같은 방식으로 만든다(안 읽고 내 방식으로 만들다 시간 낭비, 2026-10-30).
- 보여 줄 땐 **부품 관리 화면**에서. 부품 수리실에 임시 화면을 띄우면 화냄.
- 사용자 숫자는 오타가 잦다: "38블록"=3X8, "18블럭"=1X8(구멍 8개). "유추해봐"는 되묻지 말고 계산으로 정하라는 뜻. "눕혀서"=바닥에 눕힌 채.
- 근거 없이 넣은 구조(예: 아치 끝 단차)는 쓰지 않는다. 틀렸다고 하면 묻지 말고 고치고 숫자로 보고, 단순 질문엔 답만.

**Why:** 같은 부품을 여러 번 다시 만들게 된 원인이 전부 위 네 가지였다.
**How to apply:** 프로보 부품 요청이 오면 DB 행·교재 부품표 → 기존 생성기 → 등록 → 부품 관리에서 보여 주기 순서로.

**시작 도구(2026-10-30)**: invent_school 에 `.claude/skills/part-3d/SKILL.md` + `node scripts/part-start.mjs <부품이름>` + `process/06_3D부품_만들기_등록.md` 가 있다. 사용자가 "3D 부품 등록할 거야"라고 하면 이것부터(조립도의 cubo-assembly·number_start 와 같은 역할). 새로 배운 규칙은 06 문서에 적는다.

**진행 방식(사용자 2026-10-30)**: 부품은 만들어서 **그 로봇의 부품 리스트(부품 관리 → 로봇 탭)에 바로 등록한 뒤 거기서 보여 준다.** 등록 전 따로 미리보기·오버레이·부품 수리실 화면을 띄우지 않는다.
순서 확정: 등록 → ✅ 골라서 그리기(새 부품 id 만) → 부품 리스트에서 3D 창으로 보여 주기(사용자 2026-10-30).

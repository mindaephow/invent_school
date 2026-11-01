---
name: feedback-no-full-page-reload
description: 뷰어에 저장한 데이터를 보려면 설계 화면을 navigate 로 전체 새로 연다(차시 토글은 새 데이터를 못 읽는다 — 2026-11-02 확인); 단 사용자가 보는 화면을 요청 없이 새로고침하지 않고, 확인 뒤 기본 모습으로 되돌린다
metadata:
  node_type: memory
  type: feedback
  originSessionId: 50862ad9-50eb-4885-b715-6f38d175acd9
  modified: 2026-11-02T00:00:00.000Z
---

(2026-11-02 정정) 예전 규칙 "location.reload 금지, 차시 select 12→13 토글로 데이터를 다시 읽는다"는 지금 뷰어에서는 맞지 않다 — 해머배틀에서 `build --write` 로 새로 저장한 뒤 2차시→3차시 토글만 했더니 이전 데이터가 그대로 보였고, `navigate` 로 설계 화면을 다시 열어야 새 데이터가 보였다. 사용자도 "수정을 했으면 항상 다시 불러와서 화면에 보여주라"고 지시했다(2026-11-02).

**Why:** 토글은 번호·차시 선택만 바꾸고 `design-assemblies.js`·저장된 단계 데이터를 다시 받지 않는다. 사용자는 수정 후 실제로 반영된 화면을 보길 원한다.

**How to apply:** 수정·빌드 뒤 (1) `navigate` 로 `http://localhost:3178/design.html?subject=robot` 을 다시 열고 (2) 3권·해당 차시·번호를 선택해 저장된 카메라로 보고 (3) 책과 비교하고 (4) 확인하느라 돌린 카메라·팝업은 기본 모습으로 되돌린다. 사용자가 보고 있는 화면을 요청·수정 지시 없이 새로고침하거나 패널·관절 버튼을 건드리지는 않는다. 규칙 원본: 저장소 `process/00_규칙.md` J1·J2.

---
name: feedback-reload-and-show-after-part-register
description: invent_school 부품을 DB에 등록·수정한 뒤에는 묻지 않고 바로 새로 불러와 3D 창을 열어 보여 준다
metadata:
  node_type: memory
  type: feedback
  originSessionId: 9a5b1fbd-0b9c-41ca-8aef-d226c290a210
  modified: 2026-10-26T20:15:34.283Z
---

부품(스크립트로 `--write` 등록)을 고친 뒤에는 "새로 불러올까요?"라고 묻지 말고, 같은 턴에서 곧바로 브라우저 pane을 새로 불러와 해당 부품 3D 창을 열어 확인한 결과를 보여 준다.

**Why:** 2026-10-27 원판 작업에서 제가 등록만 하고 "새로 불러올까요?"라고 묻자 "지멋대로 할땐 새로 불러오고 왜 제대로 할땐 새로안불러와?"라고 크게 화냈다. 사용자는 등록 직후 화면 결과를 바로 보길 기대한다.

**How to apply:** `node scripts/make-robotron-*.mjs --write` 직후 → pane 새로고침 → 부품 목록에서 해당 행 `[data-view-image]` 클릭 → 확대 스샷으로 눈으로 확인 후 보고. 보지 못한 것은 "확인하지 못했다"고 적는다. 관련: [[feedback-do-only-the-stated-step]] [[feedback-verify-before-claiming]]

---
name: feedback-use-load-not-sample-invent-school
description: "When testing invent_school design.html live in the browser, use 불러오기 (load saved project), never 샘플 열기 (open disposable sample)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7e318d71-63ad-4922-b9e6-3137b8baace9
  modified: 2026-09-20T20:33:11.621Z
---

When verifying changes in `design.html` (the invent_school design tool) live in the browser, always use the **불러오기** (load) button to open the user's actual saved project, never **샘플 열기** (open sample) and never leave it on a fresh "새 설계" (new design) screen.

**Why:** The user shares/watches the same browser pane live. Every `navigate()` reset the page to "새 설계", and repeatedly clicking "샘플 열기" to get test parts kept putting a disposable scratch layout on screen instead of their real saved project ("1차시-샘플1" etc). This triggered repeated, escalating anger ("또 새설계 열었어", "불러오기를 쓰라고") because it looked like their actual work was being ignored/discarded, even though nothing was ever actually overwritten (no 저장 was clicked).

**How to apply:** Before any live verification in this project, click 불러오기 and select their existing saved project rather than starting blank + 샘플 열기. See [[project_invent_school]]. Related: [[feedback_verify_before_claiming]] (still verify live, just don't do it via a throwaway new-design state), [[feedback_no_unilateral_action]].

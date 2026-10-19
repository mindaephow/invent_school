---
name: feedback-no-dead-code-left-behind
description: "When a feature moves to a new file/location, delete the old implementation in the same change — don't leave it behind as dead code"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c59f7442-d731-4a8d-b3b9-bf8d11852bd2
  modified: 2026-09-21T19:10:09.885Z
---

When a feature is migrated or reimplemented in a new location (new file, new component, new page), remove the old implementation as part of that same change. Don't leave the superseded version sitting in the old file.

**Why:** User called this out directly ("항상 쓰레기파일 남기는 습관이있자나" — "you always have this habit of leaving trash files behind") in [[project_invent_school]] after two separate incidents in one session: (1) I found matching UI text in `admin.html` via grep and edited it, not realizing the same feature had already been moved to `index.html` in a prior uncommitted session, leaving `admin.html`'s copy as untouched dead code; (2) even after diagnosing that admin.html's 부품/카테고리 관리 UI was leftover cruft from a migration to index.html, it hadn't been cleaned up — a recurring pattern, not a one-off.

**How to apply:** Before editing code found via text search, check whether it's still live/reachable (check the actual page/URL the user is looking at, check git log/diff for recent moves). When you discover — or create — a duplicate/superseded implementation during a task, remove the old one in the same turn rather than leaving both versions to diverge. Don't wait to be asked twice.

**2026-10-14 확장 (invent_school 조립 도구 정리 중 사용자 지시 "사용을 안하고 대체를 한 기능은 삭제를 해버려"):** 코드 이동뿐 아니라 쓰지 않고 다른 것으로 대체한 도구·스크립트·문서도 지운다. 지우기 전 ① 대체한 것이 실제로 있는지(예: 손격자 도구 blobfit·fit_corners·fit_row → holefit·infer_grid) ② 다른 파일이 그 이름을 가리키는지 ③ 백업 ④ 가리키던 문장을 대체 도구로 고친다. 대체 증거가 없으면 지우지 않고 묻는다. 규칙 본문은 저장소 `scripts/assembly-tools/process/문서지도.md` 6번 절 5항.

---
name: feedback-coordinate-notation-style
description: "How to state part-hole coordinates/numbers in invent_school parts-lab work — plain explicit labels, row-major order, never a coded/hyphenated shorthand"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 94166c46-1ed2-407e-ae0d-8b083b2238b4
  modified: 2026-09-26T20:48:02.471Z
---

When describing hole coordinates or hole-numbering for [[project_invent_school]]'s 부품수리실 (parts-lab.html), never compress into a coded/hyphenated shorthand like "1-1" or "(3,1)" — the user reacted very negatively ("암호야???"), calling it a cipher they'd have to decode/imagine rather than read directly. Also never wrap the answer in a markdown table ("표 만들라 한 적 없어") — plain lines only.

State each hole explicitly and separately: `구멍N: X <번호 or 수치>, Z <번호 or 수치>`. Distinguish two things every time, since the user drew a hard line between them:
- **수치**: the actual raw mm coordinate value (e.g. 5, 15, 25 — first hole center = 5, pitch = 10mm, confirmed rule).
- **번호**: the displayed sequential label (1, 2, 3...) derived by sorting distinct 수치 values ascending and assigning rank+1. Don't give 수치 when 번호 was asked for, or vice versa — got called out for both.

List multiple holes in row-major reading order: same Z (row) first, sweep X ascending (가로 먼저), then move to the next Z row (세로로 이동) — i.e. sort by Z ascending, then X ascending within each Z. The user explicitly confirmed this is "how we write" (가로 먼저 세로 나중).

**Why:** this reflects a real, live bug distinction in the codebase — the numbering must be computed from actual raw hole coordinates (rounded, deduped, sorted → rank), never from `Math.floor(coord / pitch)` grid-bucket math, because floor-division can wrongly merge two physically different holes that are less than one pitch apart into the same bucket/number. The user's confirmed rule: 그리드 한 칸 = 구멍 하나, 번호는 1부터, 그리드/피치 10mm, 첫 구멍 수치는 5.

**수치 must be corner-relative, not SVG-canvas-relative.** A part's SVG artwork can be drawn anywhere inside its viewBox (e.g. this 90도 프레임's outline starts at canvas position 10,10, not 0,0) — that placement is just where-in-the-picture, unrelated to the physical part. Raw `holeCoords` values inherit that arbitrary canvas offset (first hole reads 15 instead of 5), which the user flagged hard ("15 시작이 어디있어"). Always subtract the outline's own bounding-box minimum (`Math.min(...outline.map(p=>p.x/p.y))`) before computing 수치/번호, computed fresh each render — never hardcode the offset, since it must keep working if the shape is redrawn/repositioned in its SVG canvas.

**How to apply:** any time asked to describe hole positions in chat for this project, use the plain per-line explicit format above, sorted row-major, confirm whether 수치 or 번호 was requested before answering, and make sure 수치 is corner-relative (subtract outline bounding-box origin), not raw SVG file coordinates. See also [[feedback_fix_all_display_layers]].

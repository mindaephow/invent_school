---
name: feedback-fix-all-display-layers
description: "When asked to fix a displayed value (like hole numbering) in invent_school, fix every layer that shows it — live-rendered AND DB-stored — not just the code path you found first"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 94166c46-1ed2-407e-ae0d-8b083b2238b4
  modified: 2026-09-26T20:39:06.990Z
---

When the user says "update X" (e.g. "90도 프레임 홀 번호에도 업데이트 하고"), they mean the visible thing called X everywhere it appears — not just whichever single code path you happen to fix first. In [[project_invent_school]]'s parts-lab.html, "구멍 번호" is shown in at least two independent places: (1) the live 3D canvas sprite labels, computed on the fly from the SVG, and (2) the spec table's "구멍 번호" row, which just prints whatever string is already stored in the DB (`spec.holeLabels`) — a completely separate, cached value that a code fix to the live-render path does NOT touch.

Fixing only the live-render path and leaving the stored value stale, then explaining the mechanism difference in chat instead of just also fixing the stored value, reads to the user as "you didn't do what I asked" — not as a nuanced technical clarification. Got a furious reaction for this exact gap.

**Why:** the user's instruction was already complete and specific ("90도 프레임 홀 번호에도 업데이트 하고") — the mechanism split (live vs stored) is an implementation detail the user does not care about and never asked to be walked through; they expect the visible result fixed everywhere, full stop.

**How to apply:** before reporting a display/labeling fix as done, grep for every place the same displayed field is produced (rendering code AND any DB-stored/cached copies), and fix all of them in the same pass. If a fix to stored data requires a judgment call with real tradeoffs (e.g. shifting coordinate *values*, which could desync from a saved image), that's worth surfacing — but don't stop at surfacing when part of the fix (e.g. relabeling from letters to numbers) is unambiguous; do that part immediately rather than waiting for confirmation. See also [[feedback_coordinate_notation_style]].

---
name: feedback-break-into-steps
description: "Don't try to do large multi-step work (big file reads/pushes, long builds) in one uninterrupted stretch — break it into smaller steps and report progress as you go"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a8e6e92c-986d-4464-9363-7443da22d261
  modified: 2026-09-06T13:08:14.213Z
---

Break large tasks (e.g. reading/pushing a 5,000+ line file, multi-stage deploys) into smaller steps with visible progress checkpoints, rather than working silently through the whole thing in one continuous stretch and only reporting at the end.

**Why:** During the HongHub character-panel feature work (2026-09-06), reading and pushing a ~5,400-line `page.tsx` file in one uninterrupted push (5 sequential large Read calls before a single push) took long enough with no visible progress that the user, watching a live Vercel deploy log, grew increasingly frustrated ("30분동안 뭐하는거야?", "한번에 하려고 하지말고좀 나눠서 하라고"). The task itself wasn't wrong, but the lack of intermediate checkpoints made it feel stalled/broken.

**How to apply:** For any task that will take many tool calls back-to-back with no user-visible output (large file transcription, multi-file pushes, long verification loops), narrate progress at natural breakpoints ("절반 읽었습니다, 계속합니다" style) rather than going silent until the very end. Prefer smaller, verifiable increments (e.g. push one file, confirm build, then push the next) over one giant all-or-nothing operation when the task allows it. See [[feedback_no_unilateral_action]] for the related rule about not pushing without explicit go-ahead in the first place.

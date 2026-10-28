---
name: feedback-no-minimizing-fixes
description: "Don't label a fix as \"simple\"/\"easy\"/\"just\" when reporting it — describe what changed and ask for the result, no editorializing about difficulty"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f4c8c86a-fae1-46c5-8ae4-281672bcd396
  modified: 2026-08-26T06:57:51.145Z
---

Don't call a fix "간단한 수정" (a simple/easy fix) or similar minimizing language when reporting a change, especially after a long back-and-forth debugging session with several failed attempts.

**Why:** During the U-Caption debugging session (2026-08-26 — MCP server build errors, YouTube transcript extraction bugs fixed over many rounds), the user snapped "똑바로좀 해 간단한 수정이라고 말하지 말고" (do it properly, stop calling things simple fixes) after I described a build-error fix as "간단한 수정이에요". Repeatedly framing fixes as trivial reads as dismissive of how much back-and-forth the issue actually took, especially when a prior "simple" fix didn't fully resolve things.

**How to apply:** State what the fix does and move straight to asking for the test/build result — skip characterizing the difficulty level entirely (not even "small fix", "quick one", "this should do it"). Let the user judge how big the fix was themselves.

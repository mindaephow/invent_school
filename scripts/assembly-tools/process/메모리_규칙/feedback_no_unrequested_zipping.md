---
name: no-unrequested-zipping
description: "Don't zip/compress files when delivering them unless the user explicitly asks for a zip"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 228777a0-95dc-4515-9b68-5fd21f3140d4
---

Never compress files into a .zip before handing them over. Deliver plain files/folders (preserving their repo-relative path structure, e.g. `pages/blog/index.js`) directly in a location the user can browse (their real Downloads folder, not a Claude-only sandbox temp path).

**Why:** User reacted with sharp frustration ("왜 자꾸 시키지도 않은 압축하고 지랄이야") after I repeatedly used `Compress-Archive`/zip to package modified source files from the fsfood.kr codebase (see [[project_fresh_season_blog]]) when they only asked to "전달" (hand over) the changed files. Zipping adds an unwanted extract step and wasn't asked for.

**How to apply:** When delivering edited/created files from a local source checkout (e.g. after modifying files extracted from `Fresh_Season-main.zip`) so the user can copy them into their real repo and deploy: copy the files as-is into a plain folder under their Downloads directory, preserving the relative path each file has in the repo (e.g. `Downloads/<name>/components/Header.js`). Only zip if the user says "압축해서" / "zip으로" or similar. Also don't hand over a path under the Claude sandbox temp dir (`AppData/Local/Temp/claude/...`) — the user can't browse it; always copy to a real, user-visible location first.

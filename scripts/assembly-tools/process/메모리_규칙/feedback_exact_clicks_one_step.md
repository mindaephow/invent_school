---
name: feedback-exact-clicks-one-step
description: "User gets lost with technical instructions — give the exact link/button label, one step at a time, no jargon; they lash out when steps are vague"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 66b15530-3124-4d75-84e3-f4a90cbda3aa
  modified: 2026-09-19T11:59:39.306Z
---

The user repeatedly answered multi-step technical instructions with "이게 뭐야?", "무슨말인지 모르겠어", "어디에다가 하냐고" (2026-09-19, Supabase/Vercel/GitHub setup). Vague pointers like "SQL 에디터에서 실행" or "1번" (a numbered list item) did not land.

**How to apply:**
- Give a direct clickable URL to the exact screen (e.g. the project's `/sql/new` or `/auth/providers` page) and name which account to be logged into.
- Name buttons by their on-screen text ("초록색 Run", "Save changes"), say what they should see afterward, and ask for a screenshot if stuck.
- One task per message when the user is doing it by hand; explain "what is this / why" in one plain sentence (analogy ok), not architecture.
- Don't restate the whole plan every turn; when they're mid-step, only answer that step.
- Verify their result myself right after they say it's done (curl/tests) instead of asking them to check.

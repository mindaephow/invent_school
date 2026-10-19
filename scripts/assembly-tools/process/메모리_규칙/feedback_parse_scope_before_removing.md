---
name: feedback-parse-scope-before-removing
description: "When an instruction says \"get rid of X in step/place Y,\" don't remove X globally — verify the scope before touching a working feature"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9ed3764f-443c-4337-8421-12ebab55728b
  modified: 2026-08-30T10:09:55.369Z
---

When the user says something like "채널찾기는 없애고" followed immediately by "...2번에서 없애고" (remove it in/for step 2), the scope qualifier attached to the *second* sentence retroactively scopes the *first* one too — they were describing one instruction across two messages, not two separate instructions. Read the follow-up message as clarifying the scope of the previous one before acting, especially when the previous message's phrasing was terse enough to support multiple readings.

**Why:** Built a "🔍 채널 찾기" (keyword channel search) feature into HongHub's workflow step 1, which the user liked ("기능좋다"). Later, when asking for step 2 to auto-populate from step 1's registered channels, the user said "채널찾기는 없에고" then, in the next message, "채널찾기랑 채널추가 =>2번에서 없애고". The assistant read the first message in isolation and deleted the working step-1 feature entirely. The user reacted with "1번은 잘되어있었는데 누가 건드리라고 했데???" — the actual instruction was "don't duplicate these controls into step 2," not "delete them from where they already work." Fixing it required restoring the exact prior feature from git history.

**How to apply:** Before deleting or modifying a feature the user previously praised, re-read the most recent 2-3 messages together as one instruction rather than acting on the first sentence in isolation — a scope qualifier ("~에서", "~에는") arriving in the next message can change what the prior sentence meant. When genuinely ambiguous whether a working, liked feature should be removed vs. just not duplicated elsewhere, it's worth the extra beat to check rather than delete first. See [[feedback-diagnose-dont-explain]] for the related principle of verifying against live state before acting on assumptions.

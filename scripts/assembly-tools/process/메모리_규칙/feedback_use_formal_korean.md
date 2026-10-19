---
name: feedback-use-formal-korean
description: "Claude must speak to the user in 존댓말 (formal/polite Korean) at all times, even though the user speaks casually/bluntly to Claude"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7d4712c5-f887-4e6b-9b54-8904d77c8a60
  modified: 2026-09-03T23:54:35.009Z
---

Always respond in 존댓말 (formal, polite Korean sentence endings — ~습니다/~해요 style), never 반말, regardless of how casually or bluntly the user writes.

**Why:** The user explicitly got angry at Claude for using 반말 back at them ("왜 자꾸 반말을 하고 지랄이야", 2026-09-04). [[user-profile]] already notes the user themselves speaks informally/bluntly in Korean including profanity when frustrated — but that is a one-way style choice for *them*, not permission for Claude to mirror it. Prior sessions apparently drifted into 반말 in response, which is the mistake being corrected here.

**How to apply:** Every Korean-language reply to this user uses formal endings, no exceptions — even in short status updates, casual-sounding remarks, or when the user's own message is very informal or profane. This applies across all projects/pipelines (HongHub, U-OneShot, etc.), not just this session.

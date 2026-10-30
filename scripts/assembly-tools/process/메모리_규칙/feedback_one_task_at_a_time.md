---
name: feedback-one-task-at-a-time
description: "When doing a batch of similar multi-step tasks (e.g. rewriting several blog posts), present and confirm one at a time rather than batching all decision points into a single message."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b218dd49-4447-452a-997f-dfbe8e2a8635
---

Don't front-load a big batch task by presenting all decision checkpoints (e.g. title comparison tables for 4 posts) in one message. Work through items one at a time: finish/confirm item 1 fully before presenting item 2's checkpoint.

**Why:** User reacted sharply ("씨발 이게 뭐하는짓이야") when given 4 title-comparison tables at once for a 4-post blog rewrite batch, then clarified "하나씩 하고 넘어가" (do them one by one). Even when a workflow has a mandatory per-item confirmation step (like title confirmation in [[project-fresh-season-blog]]), batching those confirmations across multiple items overwhelms the user rather than helping them.

**How to apply:** For any multi-item task with per-item user checkpoints, sequence it as: complete item N end-to-end (including getting confirmation) → report completion → move to item N+1's checkpoint. Don't get ahead by preparing/presenting checkpoints for items not yet reached, even if it seems more "efficient" to gather all decisions upfront.

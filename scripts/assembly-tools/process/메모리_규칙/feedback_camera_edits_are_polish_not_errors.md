---
name: feedback_camera_edits_are_polish_not_errors
description: "User's saved 📷 camera values are final visibility polish, not error corrections; don't count camera diffs as mistakes when analyzing 수정저장차이"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 8fa0a66a-214f-4658-9e9d-e43f62ef5f9b
  modified: 2026-10-14T02:03:54.412Z
---

When analyzing `user_diffs/수정저장차이.md`, I read the camera (📷) differences (avg ~31° guess / ~21° eye) as "the camera is what I get most wrong" and proposed predicting camera initial values. User corrected: the camera is a last-step tweak made so the whole assembly looks good, so the difference isn't an error signal.

**Why:** camera edits are aesthetic framing; part pose (❄) edits (10 of 435) and the 요청차이 entries are the real error signals.
**How to apply:** when measuring "what I get wrong", use ❄ pose corrections and 요청차이 types only; treat 📷 as the user's preference. Related: [[reference-user-diffs]], [[feedback-user-set-values-take-priority]].

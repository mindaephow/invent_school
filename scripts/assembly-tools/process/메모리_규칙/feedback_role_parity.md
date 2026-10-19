---
name: feedback-role-parity
description: "When building a feature for one user role, give the other role (teacher/student) the same capability by default — don't silently ship a stripped-down version like \"teacher mode without saving\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 66b15530-3124-4d75-84e3-f4a90cbda3aa
  modified: 2026-09-19T21:01:54.255Z
---

Don't hand one role a reduced version of a feature without asking. On the 발명융합과학교실 design tool I first made the logged-in teacher's mode "no saving" and the user reacted: "선생님 계정은 왜 저장을 안 해??? 이상한 짓을 하고 있어?" (and earlier "선생님은 그냥 돼야지, 로그인 상태니까").

**Why:** the user thinks in terms of "the teacher uses the same tool as the student, plus extras (review, admin)", not "teacher gets a demo". A missing capability reads as a mistake, not a design choice. It also cost several extra round trips (schema change + rework).

**How to apply:** when a feature touches multiple roles (teacher/student/admin), default to the same capabilities for each, adding role-specific extras (submit for students, review for teachers). If a difference is truly needed (e.g. new table for teacher projects because student projects are tied to student accounts), do the extra plumbing instead of dropping the feature, or ask first. Related: [[feedback-no-unilateral-action]] is about writes; this one is about scope of capability.

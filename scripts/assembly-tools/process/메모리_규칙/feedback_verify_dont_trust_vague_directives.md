---
name: feedback-verify-dont-trust-vague-directives
description: "When writing instructions (for myself or into a project's own system prompt), prose like \"actively look for X\" is unenforceable — replace it with a concrete, checkable action (e.g. a specific query that must actually run) so future sessions can't perform lip-service compliance."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b218dd49-4447-452a-997f-dfbe8e2a8635
---

Don't write instructions/rules as prose directives like "적극적으로 찾아본다" (actively look for it) / "consider multiple angles." These read fine but are unverifiable — an agent (including a future instance of me) can claim to have followed them without doing any real work, because there's no artifact proving the search happened.

**Why:** In the fresh-season blog project ([[project-fresh-season-blog]]), the coupang-banner-matching rule went through several rounds of drift specifically because it was phrased as "찾아본다" — a future session (angrily called out by the user: "너 너의 클로드들 이 하는 짓 몰라?" / "you don't know what your Claudes do?") would just declare "no related ingredient found" without ever running a query to check. The fix that stuck was replacing the prose with two mandatory `run_sql` queries that must actually execute and whose results must be inspected before concluding "nothing found." The user separately rejected the opposite failure mode too — turning it into a fixed enumerated checklist (e.g. "지역·효능·느낌 3개 축") — because a rigid taxonomy just becomes a new thing to mechanically declare compliance with, rather than genuinely explore.

**How to apply:** When a rule needs "explore broadly before concluding X isn't there," don't phrase it as an attitude ("try harder," "look actively," "consider several angles"). Phrase it as a required action with an inspectable output: a specific command/query to run, whose result must be shown or referenced before the negative conclusion is allowed. This applies broadly, not just to this project — any time I'm tempted to write "make sure to thoroughly check" as a standalone instruction, ask what concrete, auditable step would actually force that checking to happen.

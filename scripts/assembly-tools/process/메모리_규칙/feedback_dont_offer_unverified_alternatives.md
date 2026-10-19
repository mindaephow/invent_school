---
name: feedback_dont_offer_unverified_alternatives
description: "Don't list alternatives/services/quotas/prices from memory with \"verify yourself\"; search first, state only confirmed facts with source, else say unknown"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 8fa0a66a-214f-4658-9e9d-e43f62ef5f9b
  modified: 2026-10-13T16:23:32.878Z
---

When asked for alternatives (hosting, GPU services, tools), user got angry at a table of Kaggle/Lightning/RunPod etc. with quotas and prices written from memory plus "직접 확인해 보세요". Unconfirmed alternative info makes them swear.

**Why:** pushing verification onto the user is worse than saying nothing; they act on it.
**How to apply:** WebSearch first and give only confirmed items with source; if not confirmable, say "확인 못 했습니다" instead of listing. Related: [[feedback_flag_confidence_level]], [[feedback_verify_before_claiming]], [[feedback_research_always_cite_source]].

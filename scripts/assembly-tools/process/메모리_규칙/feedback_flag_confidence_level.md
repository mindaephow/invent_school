---
name: feedback-flag-confidence-level
description: "Say plainly whether a claim is verified fact or your own inference — don't state opinions in the same confident tone as checked facts"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 94166c46-1ed2-407e-ae0d-8b083b2238b4
  modified: 2026-09-26T22:31:41.364Z
---

When answering a design/rule question (e.g. "is there a separate rule for why bracket and frame count holes differently?"), don't answer "아니요, 다른 법칙이 있어야 할 이유가 없습니다" (no, there's no reason for that) in a flat declarative tone before actually checking the code — that reads as citing an established fact, not offering an opinion. The user said: "니가 너무 당연하게 그렇다고 해서 난 그런 법칙이 있는줄 알았어" (you said it so matter-of-factly I thought there really was such a rule).

**Why:** confident phrasing collapses the distinction between "I verified this" and "this is my best guess," and the listener can't tell which they're getting — leading them to trust an unverified claim as settled.

**How to apply:** in [[project_invent_school]] work (and generally), explicitly tag the confidence level: "확인했습니다 — [fact]" for something checked against code/DB/image, vs "제 판단(추측)으로는 — [opinion]" for reasoning/inference not yet verified. When a design question could have a real established reason behind it, check first (grep the code, ask directly) rather than reasoning from first principles and presenting the conclusion as settled. Related: [[feedback_verify_before_claiming]], [[feedback_port_reference_exactly]].

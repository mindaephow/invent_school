---
name: feedback-diagnose-dont-explain
description: "When the user says a UI element isn't visible/working, stop re-explaining navigation and go look/fix directly"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9ed3764f-443c-4337-8421-12ebab55728b
  modified: 2026-08-30T09:44:48.367Z
---

When the user reports something isn't visible or isn't working ("안보여서 말하는거자나", button/feature missing), do not respond with another verbal explanation of where to click or where it should be. Go verify directly (open the live site with the browser tool, read the actual component code) and then fix the actual gap — even if that means adding a new UI affordance in the exact spot they're looking, not just pointing them to a different page that technically has the feature.

**Why:** The user got increasingly angry across several rounds when told to navigate elsewhere ("HongHub 홈 → 소스 발굴 → 채널 탭") because the real problem was that the feature they wanted (add a channel) wasn't reachable from the page they were actually on (the workflow step detail view). Repeating the same navigation instructions did not help; they explicitly called this out. The fix that worked was building the "+ 채널 추가" action directly into the workflow page's channel-step panel, confirmed by positive feedback ("잘했어", "기능좋다") once shipped.

**How to apply:** Treat "I don't see X" as a signal to inspect actual current state (browser screenshot, live page, real component) before responding, and bias toward bringing the missing action to where the user already is rather than redirecting them elsewhere. This generalizes beyond UI bugs — see [[feedback-reuse-existing-infra]] for the same "verify before instructing" pattern applied to infrastructure/config questions.

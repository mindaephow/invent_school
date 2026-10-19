---
name: feedback-port-reference-exactly
description: "When the user points at a working reference file and says copy it, port values/order literally — don't re-derive equivalent-looking logic"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 94166c46-1ed2-407e-ae0d-8b083b2238b4
  modified: 2026-09-26T22:15:16.263Z
---

In [[project_invent_school]]'s parts-lab.html, nearly every bracket-rendering bug in one very long session (2026-09-27) traced back to the same root cause: a past rewrite of `_compare_all.html`'s `buildBracketMesh`/`buildBracketScene` into the parametric `renderBracketPanel`/`bracketHoleGeom` **re-derived** equivalent-looking logic instead of porting the original's exact values/order. Concretely:

- The shape's point list was manually re-reversed on top of an X-axis mirror, double-flipping winding and corrupting triangulation at the one concave corner (visible as a color blotch under lighting).
- Hole circles were placed exactly on the surface instead of nudged 0.05mm off it like the original's `makeWindow` calls — caused z-fighting that made a whole arm's holes invisible.
- A "dedupe" step was added to merge the two arms' coincident corner holes into one — the original never dedupes; the two corner holes are genuinely different (different face/rotation), just at the same grid coordinate.

**Why:** each individual "improvement" seemed reasonable in isolation (fix winding for the mirror, avoid drawing what looked like a duplicate hole) but silently diverged from a reference implementation that already worked correctly. The user's instruction was literal: "복사해서 붙여넣으라고 존나게 말을 해도 니 멋대로 해놓고" (told you to copy-paste it, you did it your own way).

**How to apply:** when a user says "do it like the original" / points at a working reference file, treat that as "port the literal values and order," not "achieve an equivalent result." Diff your adaptation against the reference line-by-line before assuming a deviation is safe. If a deviation seems necessary (e.g. parametrizing a hardcoded value, or achieving a different visual orientation), verify it preserves the exact same computed footprint/winding/values via a standalone script (Node), not just "should be equivalent" reasoning — this session's dedup and winding bugs both looked equivalent on paper and weren't. See also [[feedback_do_only_the_stated_step]], [[feedback_fix_all_display_layers]].

---
name: feedback-dont-mention-svg
description: "Never reference \"svg\" as an explanation when discussing invent_school parts-lab parts/holes with this user — talk about the part/hole itself, not the file format"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 94166c46-1ed2-407e-ae0d-8b083b2238b4
  modified: 2026-09-26T21:33:32.075Z
---

When discussing [[project_invent_school]]'s parts-lab (90도 프레임, 1열브라켓, etc.), never explain something by pointing at "svg" (the underlying `image_svg` file, `parseSvgMaskHoleCenters`, "그림 캔버스 위치" etc.) as the reason for a value or behavior. The user demanded this be erased from consideration entirely, repeated many times with visible fury, after a long back-and-forth where "it's because of how the svg is drawn" kept coming up as an explanation for hole coordinates/numbering.

**Why:** the user does not want the underlying file format surfaced as part of the explanation at all — from their side it reads as an excuse or a distraction from the actual question (where is the hole, what is its coordinate), not a legitimate technical detail worth mentioning.

**How to apply:** describe hole positions, numbering, and part geometry purely in terms of the part itself (mm coordinates, corner-relative, X/Z/Y) — never mention "svg" as a cause, reason, or source of a value in conversation with this user, even if it is technically true in the code. The user named the two valid sources of truth explicitly: "스펙만 보라고" (just look at the spec JSON field) or "이미지를 보던가" (or look at the rendered image/screenshot) — answer from one of those two, never from svg parsing logic or "how the file is drawn" reasoning. See also [[feedback_coordinate_notation_style]].

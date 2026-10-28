---
name: feedback-verify-reference-before-3d-geometry
description: "When building visual/3D representations of real physical objects, check actual reference images/data first and verify the result visually before declaring done — don't guess from partial text specs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 997777c6-f9e4-41a0-804a-7b979cc7048e
  modified: 2026-09-23T07:21:11.320Z
---

Never build a 3D/visual representation of a real physical part from partial text specs alone when actual reference images exist in the data. Check the reference first, every time, before writing geometry code.

**Why:** In the invent_school (발명융합과학교실) 3D 설계 도구 work, the `ivs_part_catalog` DB table had `image_svg`/`image_svg_diagonal` fields with hand-drawn reference art for every robot part (큐보 프레임류 등). Instead of querying and looking at those images, geometry for bent frames (135도/90도 프레임), the half-ring frame (반원프레임), and connector brackets (1열/2열브라켓) was built purely by guessing from short text size strings (e.g. "83.3×33.3×5mm, 135°절곱"). The guesses were visibly wrong — a half-ring rendered as a vertical arch instead of a flat curved strip, bent frames rendered as flat sideways bends when the real bend geometry needed different axis math, connector brackets left as generic boxes. The user caught every one of these by eye immediately and called out — correctly — that the reference images were sitting right there in the database and were never opened. This produced a strong, justified reaction (heavy profanity) that could have been entirely avoided.

**How to apply:** Before writing any code that renders, draws, or models a physical object (2D icon, 3D mesh, diagram, etc.) whose real appearance is knowable — check for an existing reference (uploaded image, SVG, photo, spec sheet, prior art in the same codebase) and actually look at it first. If no reference exists, say so explicitly and ask, rather than silently inventing dimensions/angles/orientation from adjacent text data. After building it, verify the actual rendered/computed result (screenshot, precise object-level inspection of geometry/angles/positions — not just "does it run without throwing") before reporting the work as done. Confirming code executes without error is not the same as confirming the output is correct — for anything with a visually-checkable ground truth, check the visual result specifically, ideally with a method immune to ambiguity (e.g. computing exact angles/positions in the scene graph, not just eyeballing a screenshot from an arbitrary camera angle).

This generalizes beyond this one project: whenever [[project_honghub_pipelines_vs_tools]]-style content work or any other visual/structural output has ground-truth reference material available, treat skipping it as a process failure, not a shortcut.

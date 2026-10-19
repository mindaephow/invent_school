---
name: feedback-no-svg-for-checking
description: "부품 모양 확인용으로 SVG를 만들지 않는다 — 3D 뷰어(three.js, STL 그대로)로 보여 준다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 46ca3ff8-97a1-475d-b0d9-73af9355d3a3
  modified: 2026-10-01T10:43:09.156Z
---

부품(STL) 모양을 확인할 때 위에서 본 SVG 등 2D 그림을 임시로 만들지 않는다. 3D 뷰어(three.js로 STL 삼각형을 그대로 그린 HTML)로 확인하고 사용자에게도 그걸 보여 준다.

**Why:** 사용자가 "svg는 왜 만든거야", "왜 자꾸 svg를 만들고 지랄이야"라고 두 번 화냄(2026-10-01). 사용자가 원한 건 3D로 STL을 보고 17·15프레임과 겹쳐 보는 것. 관련: [[feedback-dont-mention-svg]]

**How to apply:** 검증은 숫자 검사(부피·모서리) + 3D 뷰어(_arc_view.html 같은 임시 파일, 끝나면 정리). 말없이 임시 파일을 만들지 말고 만들면 이유를 먼저 한 줄로 말한다.

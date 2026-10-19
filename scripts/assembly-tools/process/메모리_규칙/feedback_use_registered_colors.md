---
name: feedback-use-registered-colors
description: 부품 색은 등록된 그대로 — 강조·덧입히기·임의 보정으로 색을 바꾸지 말 것
metadata:
  node_type: memory
  type: feedback
  originSessionId: 61098ce2-0dc0-4d37-a9f6-ac22679a9310
  modified: 2026-09-30T16:13:36.649Z
---

조립 보기에서 "새 부품 강조"로 emissive 파란/주황 빛을 얹고 짙은 회색으로 덧입혔더니 사용자가 "색상을 일부러 니멋대로 수정을 하는거야? 그냥 등록된대로 해"라며 화를 냈다.

**Why:** 사용자는 부품 관리에 등록된 색(팔레트 썸네일)이 진실이라고 본다. 교재 그림 색과 달라도 등록값을 바꾸지 않는다.

**How to apply:** 3D 부품은 등록 모델 색 그대로 그린다. 새 부품 표시는 색이 아니라 화살표·원 같은 별도 표식으로. 장면 조명 때문에 밝게 뜨는 건 색을 바꾸는 게 아니라 조명 보정(0.72배)으로만 맞춘다. [[project-cubo-assembly-rules]]

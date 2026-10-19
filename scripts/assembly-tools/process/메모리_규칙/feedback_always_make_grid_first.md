---
name: feedback-always-make-grid-first
description: "조립도 단계마다 격자(refs)를 먼저 확인·제작·등록한다; \"격자 불필요/불가\"를 클로드가 혼자 정하지 않는다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d3ad27b4-eef8-49b6-b222-f6d8c762fbd3
  modified: 2026-10-06T20:43:47.714Z
---

단계를 만들기 전에 격자 저장소(ivs_assembly_refs)에 그 단계 격자 2장이 있는지 보고, 없으면 만든다. 보이는 구멍만 맞추면 대부분 가능하다. 정말 안 되면 빼는 이유를 보고하고 확인받는다. 만든 뒤 DB 에 바로 등록한다.

**Why:** 꼬마기사 25번을 격자 없이 짐작해 방향·칸이 틀렸고, 20번은 안내서가 "격자 불가" 예로 적어 둔 걸 믿고 안 만들었다가 "건방떨지 말고 격자 다시 다 만들라", "규칙을 안 지킬 때마다 조립도를 족같이 그린다"는 말을 들었다.
**How to apply:** 안내서 6-0-2 ⓓ-4. 격자를 만들면 칸을 세어 단계를 만들고 화면에서 다시 대조한다. See [[feedback-checklist-before-done]], [[project-kidknight-status]].

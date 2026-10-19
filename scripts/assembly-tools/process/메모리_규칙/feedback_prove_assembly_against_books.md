---
name: feedback-prove-assembly-against-books
description: 조립한 결과가 맞는지 책 그림(이전·다음 번호·완성 사진)에 겹쳐 증명하고 그 증명을 이미지 작업(18_3 같은 그림+읽기 표)에 남긴다
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2642ae62-1c8a-4475-817f-8b0fc23f8fb0
  modified: 2026-10-16T17:51:08.879Z
---

어보이더 18번 팔 결합 위치가 틀렸다는 지적에 "19번 봤어?", "정보를 다 안 쓰면서 뭘 조립하는 거야", "맞는 이유를 증명해야 한다", "그걸 이미지 작업에 다 남겨"까지 이어졌다. 눈으로 맞춘 카메라·한 장만 본 읽기로 만든 걸 "했다"고 보고해서 화를 냈다.

**Why:** 눈대중으로 만든 번호는 몸 폭(x ±30 vs ±45)·팔 높이(31mm)가 통째로 틀려도 화면만 봐서는 안 잡힌다. 사용자가 틀린 걸 대신 찾아 주게 된다.

**How to apply:** 번호를 끝내기 전에 (1) 앞·뒤 번호(15·16·19·20번 등)와 완성 사진을 다 읽는다 (2) 그 번호 책 그림의 점(구멍·돌기·링)으로 PnP 카메라를 풀고(pnp.py fit), 모델 부품 상자를 같은 카메라로 책 그림 위에 겹쳐 오차(px)를 숫자로 본다 — 가설(예: 안쪽 블록 x±30 vs 바깥 블록 x±45)을 오차로 가른다 (3) 판이 가려져 holefit 가 안 되면 놓인 모델의 돌기·링 3D 점을 써서 푼다 (4) 겹침 그림·브래킷 구멍 배치 같은 증명을 `refs/<이름>/NN_3.jpg`·`NN_4.jpg`(+index.json, refStore.save 로 DB)와 읽기 표 판단과정에 남긴다. 새 부품이 없는 번호(8·10·18)에도 작업 점검 블록이 붙도록 stepchecks.py 를 고쳐 둠. [[feedback_checklist_before_done]] [[feedback_run_tools_before_judging]]

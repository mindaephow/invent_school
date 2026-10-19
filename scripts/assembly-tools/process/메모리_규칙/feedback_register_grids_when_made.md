---
name: feedback-register-grids-when-made
description: "격자(교재 그림) 이미지는 만들면 바로 DB(ivs_assembly_refs)에 등록 — \"업로드\" 말을 기다리지 않는다"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 50862ad9-50eb-4885-b715-6f38d175acd9
  modified: 2026-10-08T15:43:13.194Z
---

강아지로봇 23번 격자가 화면 🖼 에 없다고 사용자가 화냈고("규칙대로 안 한 거야?"), 이어서 "DB는 만들면 등록하는 거야"라고 정정함(2026-10-09). 안내서의 "모아서 업로드(단계 5의 3번)"는 푸시·커밋 쪽이지, 격자 이미지 DB 등록은 만든 즉시(안내서 0-2 ⓓ-4 ⑤).

**Why:** 화면의 🖼 버튼은 DB 에서 읽으므로 로컬 refs/ 에만 있으면 사용자가 격자를 못 본다 → "안 만들었다"로 보인다.

**How to apply:** 번호 격자(NN_1·NN_2)를 render 한 직후 등록한다. 방법: public/_refs_tmp/<이름>/ 로 refs 복사 → 열려 있는 조립 보기 화면에서 refs_upload.js 내용을 javascript_tool 로 정의(파일은 서버에 안 열림, 본문 붙여넣기)한 뒤 `__ivsRefsUpload('dog','cubo-1-dog',[번호들])` → run_sql 로 `ivs_assembly_refs` idx 0,1,2 확인 → _refs_tmp 삭제(커밋 금지). 푸시·커밋은 여전히 "업로드" 말 뒤. 관련: [[project-dog-robot-restart]]

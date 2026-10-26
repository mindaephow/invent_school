---
name: project-cubo3-chapter-order
description: 큐보 3권 차시 순서 — 0 준비 · 1 배틀바이크(13~19쪽) · 2 조향자동차(22~30쪽) …; 앱 차시 번호는 DB chapters 배열 인덱스(0부터)
metadata:
  node_type: memory
  type: project
  originSessionId: 66834b43-607f-4ed6-ac65-6449d2cbea4e
  modified: 2026-10-26T02:50:19.166Z
---

앱의 "N차시"는 `ivs_textbooks.data.chapters` 배열의 **0부터 센 인덱스**다(design.html fillSessions/update). 0차시에서만 큐보 부품 전체 리스트·결합원리·조립방법 버튼이 뜬다. 큐보 1·2권은 처음부터 `0:준비…`로 시작한다.

큐보3단계(id c461670d-6fc5-493b-b884-64d1650a0742)는 원래 `0:배틀바이크 | 1:조향자동차 …`로 준비 차시가 없었다. 2026-10-26 사용자 지시로 맨 앞에 `ch_cubo3_prep "준비"` 를 넣어 현재 `0:준비 | 1:배틀바이크 | 2:조향자동차 | 3:해머배틀 | 4:장갑차 | 5:미니덤프 | 6:창작로봇1 | 7:석궁봇 | 8:빅핸드 | 9:집게로봇 | 10:오토투석기 | 11:큐보바이크 | 12:창작로봇2`. 백업: 세션 scratchpad `ivs_textbooks_cubo3_backup.json`(되돌리려면 첫 항목만 제거).

**Why:** 처음에 SQL `with ordinality`(1부터)를 앱 번호로 잘못 읽고, 책의 "0차시 배틀바이크"만 보고 조향자동차를 1차시로 착각해 steercar 를 먼저 만들었다. 조립도 id: cubo-3-steercar(2차시), cubo-3-battlebike(1차시, 번호 등록까지).

**How to apply:** "N권 M차시"는 DB chapters 를 `ordinality-1` 로 세어 확인한다. DB 수정은 run_sql 로 안 되고(조회만), 큰 행은 `.env.local` 서비스 키로 로컬 스크립트(GET→백업→PATCH)로 했다 — 사용자가 명시적으로 수정하라고 한 뒤에만. 관련 [[project-invent-school]].

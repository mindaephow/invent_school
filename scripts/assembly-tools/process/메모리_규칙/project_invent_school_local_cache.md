---
name: project-invent-school-local-cache
description: invent_school 로컬 캐시(IndexedDB) 구조·측정값·주의점 — 부품 목록·교재·3D 모델을 브라우저에 저장해 로딩을 줄임
metadata:
  node_type: memory
  type: project
  originSessionId: 61098ce2-0dc0-4d37-a9f6-ac22679a9310
  modified: 2026-09-30T21:44:31.384Z
---

2026-10-01 사용자 요청("부품관리 부품 불러오기, 조립도 들어올 때 부품 불러오기가 느리고 매번 새로 받는 것 같다")으로 구현. 파일: `public/local-cache.js`(window.IVS_CACHE: get/set/del/clear/keys/stats/hash), 적용: `design.html`(loadRobotPartsFromDb/loadTextbooksFromDb/ensureRobotModel), `index.html`(부품 관리 탭 openPartsTab). 방식은 stale-while-revalidate(캐시로 먼저 그리고 뒤에서 최신 받아 달라졌으면 갱신).

**키**: `robot-catalog:v1`(light 목록+썸네일+연결점, ver=내용 지문), `robot-textbooks:v1`, `robot-model:<partId>`({ver=thumbnail3d 지문, data=만들어 둔 점·면 데이터}), 부품 관리 탭 `ivs-parts-tab-cache-v1`(원래 localStorage였는데 썸네일 때문에 5MB 초과로 저장이 조용히 실패했을 가능성 → IndexedDB로 이전). **무효화**: 부품을 고치면 썸네일이 바뀌므로 그 부품의 model 캐시를 지운다. 문제 시 콘솔에서 `IVS_CACHE.clear()`.

**측정(로컬)**: 부품 목록 표시 1.88s→0.88s(페이지 시작 0.6s 제외하면 사실상 즉시), 3D 모델 불러오기 ~1s→24ms, 부품 36개 다시 놓기 523ms→41ms(3D 모델이 메모리에 있으면 SVG 단순 모양 생략 + 한꺼번에 놓을 땐 목록·선택을 마지막에 한 번만), 조립도 열기 1.5s→0.39s. `window.__ivsPerf`에 측정 시각이 남는다.

**주의**: 로컬 개발 서버는 /api/admin 이 500이라 부품 관리 탭(index.html) 캐시는 로컬에서 검증 못 했다(배포 사이트에서 확인 필요). 조립 보기 바(#asmBar, .asm-stage-bar)는 `hidden`이 display:flex에 눌리던 버그가 있어 CSS로 고침.
**How to apply:** 부품/교재 데이터 형식을 바꾸면 캐시 키 버전(:v1)을 올린다. 새 무거운 자료도 같은 패턴(IVS_CACHE + 지문)으로 캐시한다. [[project_invent_school]]

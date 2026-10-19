---
name: project-cubo-parts-status-1001
description: 2026-10-01 큐보 부품 3D·연결점 작업 마무리 상태 — 새 세션에서 조립도 만들 때 시작점
metadata:
  type: project
---

2026-10-01 큐보 부품 마무리: 로봇 과목 부품 52종 중 49종이 3D 모델+연결점(connectors)을 모두 가짐. 빠진 3종(고무밴드·3P 케이블·리모컨)은 사용자가 "안 해도 됨"이라 함.
이번에 새로 만든·기록한 것: 반원프레임(구멍 9개, 호 위 10mm 현·양 끝 60mm), 서보혼·둥근서보혼(아래 면 1mm만 막고 나사 구멍), 8볼트·12볼트·너트·서보고정볼트(cubo-bolt-mesh.js), 센서 3종(IR·LED·터치, 바닥 돌기 3개)·캐터필러(링크 1개, 속 빈 돌기 2개), 215·515·713프레임, 육각큰기어, 스프라켓·중간바퀴(가운데 십자 구멍), 서보모터(출력축 돌기 1개).
**Why:** 사용자가 "새 세션에서 조립도 만들자"고 함 — 조립도(교재 단계별 3D 조립 보기)는 부품 연결점이 있어야 하므로 이 상태가 출발점.
**How to apply:** 새 세션은 먼저 get_assembly_guide(MCP) 읽기, 조립도 목록은 list_assemblies. 양팔저울 조립도는 "1차: 반원프레임·눈블록 머리 부분 제외"라 이제 반원프레임이 있으니 교재 9~11단계(머리 부분)를 넣을 수 있다. 교재 큐보1단계 PDF 19쪽 그림 11이 반원프레임 끼우는 장면(리벳이 반원 4·6번 구멍=직선 프레임 바깥 열 ±10). 반복 규칙: [[feedback-infer-parts-from-base-rules]] [[feedback-no-svg-for-checking]] [[project-cubo-part-standard]]
기술 메모: 로그인한 브라우저 탭(sessionStorage 'ivs-teacher-auth' 의 access_token)으로 /api/admin get_part 를 호출하면 STL 원본(fileDataUrl)을 읽어 페이지 안에서 측정할 수 있다(SQL 로는 시간 초과). 서보모터 출력축 반지름 3 vs 서보혼 육각 구멍 2.5 불일치는 미확인.

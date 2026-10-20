---
name: project_assembly_edit_and_paint
description: invent_school 조립 보기 관리자 도구(표시 옮기기·수정스샷)와 부품 색칠(paint) 기능·DC모터 적용 내용
metadata:
  type: project
---

조립 보기(design.html + design-assembly.js + design-notes.js)에 관리자 전용 버튼 2개(스케치북 아래, 그리기 왼쪽):
"📍 표시 옮기기"(초록 구멍 점을 잡아 10mm 칸으로 옮기면 주황 점+번호) / "📸 수정스샷"(번호·이동목록이 박힌 PNG를 클립보드 복사+다운로드). 저장은 안 하고 사용자가 캡처를 보내면 내가 데이터에 반영한다.

부품 색칠: spec.shapes 의 `paint:true` 도형은 CSG에 안 합치고 자기 색으로 얹는다(parts-lab-viewer.js, design.html). 이미 열어 본 PC는 로컬 모델 캐시(ver `...|paint2`) 때문에 안 바뀌므로 색칠 바꾼 뒤엔 ver를 올리거나 캐시를 지운다.

DC모터(id 26551cb8-0032-4936-96e1-e0b06518f631) 칠: 위·아래 십자 축 구멍 = 빨간 부시(원+어두운 십자), 돌기 6개 회색, 케이블 나오는 +z 끝 돌출부 흰색. 사용자 확인 완료("맞아").
모델 좌표(칠 도형 기준): x ±20, y 0..38(몸통 0..33, 윗돌기 33..38), z ±26.5; 축 구멍 중심 (0, y, −12.5); 몸통 옆면 x ±15.

**Why:** 사용자가 색을 보고 모터 방향·위치를 판단하는 조립도를 만들기 위해.
**How to apply:** 부품 spec를 /api/admin update_part 로 바꿀 땐 image/volumes 등 기존 필드를 같이 보내야 지워지지 않는다(list_parts로 받은 값 재전송).

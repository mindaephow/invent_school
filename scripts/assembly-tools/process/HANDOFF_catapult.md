# 투석기(cubo-2-catapult) 인수인계 — 2026-10-12 기준

이 문서와 같은 폴더의 `00_개선규칙.md`~`05_조립.md`(조립 과정 규칙, 원본은 사용자 Downloads 폴더), `.claude/skills/cubo-assembly/SKILL.md`, `scripts/assembly-tools/user_diffs/요청차이.md`(사용자가 바로잡은 것 19건)를 **처음부터 읽고** 시작한다.

## 상태
- 1~15번: 사용자 ✓ (DB `ivs_assembly_status`). 내용을 바꾸지 않는다(빌드가 막는다).
- 16번: 코드·읽기 표·방향/회전/격자 그림(DB 등록) 완료. 사용자 ✓ 없음, 책과 화면 비교 증거(`record_check.py`)는 리벳 분리 수정 때문에 낡았다 → 화면 비교 후 증거를 다시 남긴다. 리벳 4개는 검은 판에서 14mm 띄워 끼운다(`seated` 없음). 알려진 경고: 흰 판이 뜨는 길에 숨은 2단블록(9.0)과 겹침 — 끄지 말고 보고.
- 17번: 그림 3장(17_1/17_2/axes, fits/17_W 흰 판 9×5)만 만들어 DB 등록함. **읽기 표(catapult_read.json 17)와 catapult.py 코드는 아직 없다.** 방향: 칸 +X·줄 −Z (axes_fit, 16번과 같은 시점).
- 18~35번: 미착수(뼈대 + 창고 slot/history 계획만 있음).

## 17번 읽기 (이미 읽은 사실 — 책 refs/catapult/17.jpg, 17_2.jpg)
- 창고 3의 판 세트(16번: 흰 59프레임 + 검은 37프레임)를 창고 2의 L 묶음(14·15번 BL14·1열브라켓)에 합친다(번호가 작은 창고 2에서 합침, `move_group`). 새 2단블록 2개.
- 흰 판(9×5) 위 초록 링 12개 ↔ 구멍: 왼쪽 L = 칸1줄1·칸2줄1·칸3줄1·칸1줄2 / 오른쪽 L = 칸7줄1·칸8줄1·칸9줄1·칸9줄2 / 새 2단블록 = 칸1줄4·칸1줄5, 칸9줄4·칸9줄5.
- 못 정한 것: L이 판에 놓이는 방향(어느 돌기가 어느 링), 새 2단블록 자세.

## 도구 순서 (번호 하나)
`python number_start.py catapult N` → 05 의 5-1(그림 읽기: fits → `axes_fit.py` → `<NN>_axes.json` 에 `rotate_to` → `refs_rect.py`) → 읽기 표 → 코드(catapult.py, `stepchecks.apply` 앞) → `PYTHONIOENCODING=utf-8 python build.py catapult --write` → 화면 비교 → `record_check.py catapult N <캡처> "<결과>"`.
- 이미지 DB 등록: `public/_refs_tmp/catapult/` 에 파일+index.json 복사 → 로그인된 설계 화면에서 `__ivsRefsUpload('catapult','cubo-2-catapult',[N])` → 폴더 삭제.
- 화면 반영: build 후 `design-assemblies.js` 를 fetch+eval 로 다시 읽고 차시 select 3→2 토글, 번호 버튼 클릭(전체 새로고침 금지).
- 윈도우 콘솔은 cp949 → `PYTHONIOENCODING=utf-8`.

## 지킬 것
존댓말·짧게. ✓/완료 버튼 절대 누르지 않기. 푸시는 사용자가 "업로드"라고 할 때만. 빌드 게이트 우회 금지(`build.py` 는 --write 뿐). 확인한 것/추정 구분해서 정직하게 보고. 사용자가 바로잡은 것은 `요청차이.md` 에 한 항목 추가.

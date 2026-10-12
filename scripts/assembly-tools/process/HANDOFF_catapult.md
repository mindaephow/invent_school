# 투석기(cubo-2-catapult) 인수인계 — 2026-10-12 기준

이 문서와 같은 폴더의 `00_개선규칙.md`~`05_조립.md`(조립 과정 규칙 — 이 저장소 사본이 기준), `.claude/skills/cubo-assembly/SKILL.md`, `scripts/assembly-tools/user_diffs/요청차이.md`(사용자가 바로잡은 것 19건)를 **처음부터 읽고** 시작한다.

## 상태
- 1~19번: 사용자 ✓ (DB). 내용을 바꾸지 않는다(빌드가 막는다). `number_start.py catapult N` 이 ✓ 현황을 DB 에서 읽어 보여 주므로 이 문서의 숫자보다 그것을 믿는다.
- 20번: 코드·읽기 표·그림(DB 등록)·증거 완료(2026-10-12). 긴 팔은 `move_made`(제자리), T축·부시는 결합하는 모습(떠서 화살표). 카메라는 눈으로 정함(camSrc guess, theta 1.3). 칸14·브라켓 h2 구멍은 추정.
- 21번: 코드·읽기 표·그림(DB)·증거 완료(2026-10-12). 14~20번 조립 전체를 `move_made` 로 몸의 세운 판 사이로 옮김(여러 번 이동 지원: `moves`, `IVS_moveAt`). 팔은 29프레임 두 장 사이에 끼워지고 T축은 판·팔·판을 꿴다. **19·20번(✓)의 팔은 두 판 사이가 3mm 떠 있어(13mm) 맞닿은 10mm 가 맞다 — 사용자가 ✓ 를 풀어 줄 때 고친다.**
- 22번: 고무밴드(3D 모델 없음)라 설명만 둠. 23번(3단블록 3 ㅍ 조립, 새 창고 2)·24번(ㅍ 조립을 몸 윗판 515프레임에 얹고 3단블록 1 추가) 완료·증거 남김. 24번 칸·줄 위치는 추정(책에서 판 구멍을 세지 못함, 링 6+2). 25번부터 미착수.

## 17번에서 배운 것(다음 번호에 적용)
- ✓ 한 앞 번호 부품을 옮겨 붙이는 번호(21·24·30번 등 합치기)는 `move_group` 대신 `s.move_made(...)` 를 쓴다(05 의 5-3).
- 묶음 둘이 서로 거울 모양이면 한 개씩 다른 자리(왼쪽 L·오른쪽 L)에 같은 회전으로 들어간다 — 돌기 모양으로 먼저 수치 확인.

## 도구 순서 (번호 하나)
`python number_start.py catapult N` → 05 의 5-1(그림 읽기: fits → `axes_fit.py` → `<NN>_axes.json` 에 `rotate_to` → `refs_rect.py`) → 읽기 표 → 코드(catapult.py, `stepchecks.apply` 앞) → `PYTHONIOENCODING=utf-8 python build.py catapult --write` → 화면 비교 → `record_check.py catapult N <캡처> "<결과>"`.
- 이미지 DB 등록: `public/_refs_tmp/catapult/` 에 파일+index.json 복사 → 로그인된 설계 화면에서 `__ivsRefsUpload('catapult','cubo-2-catapult',[N])` → 폴더 삭제.
- 화면 반영: build 후 `design-assemblies.js` 를 fetch+eval 로 다시 읽고 차시 select 3→2 토글, 번호 버튼 클릭(전체 새로고침 금지).
- 윈도우 콘솔은 cp949 → `PYTHONIOENCODING=utf-8`.

## 지킬 것
존댓말·짧게. ✓/완료 버튼 절대 누르지 않기. 푸시는 사용자가 "업로드"라고 할 때만. 빌드 게이트 우회 금지(`build.py` 는 --write 뿐). 확인한 것/추정 구분해서 정직하게 보고. 사용자가 바로잡은 것은 `요청차이.md` 에 한 항목 추가.

## 환경
저장소 루트 `CLAUDE.md` 의 "환경에서 사람이 줘야 하는 것"(.env.local 키, 로그인) 참고. 로컬 서버는 `npm run dev -- -p 3177`(README 새 PC 절), 화면 확인·이미지 등록은 로그인된 브라우저 패널이 필요하다.

## 이번 세션에서 배운 것(2026-10-12 — 요청차이.md 에도 있음)
- 그림 격자·축선은 흰 판(아래 부품)의 실제 구멍을 검출해 맞추고(Hough/밝기), 선↔구멍 거리(px)를 보고한다. 줄이 둘인 프레임은 `center_row`. 사용자가 "회전"을 말하면 `level` 로 실제 회전(각도 보고).
- 새 부품이 있는 번호는 화면에서 화살표가 나오는지 직접 본다(`IVS_MATES.check`, 부품 DB 구멍 `len`). 리벳·T축·부시는 항상 결합하는 모습(띄워서 화살표)으로.
- `build.py --write` 가 읽기 표 빈 번호 때문에 조용히 막힐 수 있다 — 출력 끝의 ❌ 줄과 `기존 항목을 바꿨다` 를 확인한다.

# eq-robot 스크립트

EQ로봇 교재·부품을 발명교실 DB(Supabase)에 올릴 때 한 번씩 돌린 일회용 스크립트 모음입니다.
**전부 이미 한 번 실행했고 데이터는 DB에 들어가 있습니다.** 다시 돌릴 일은 거의 없고, 다른 PC/세션에서 "무엇을 어떻게 했는지" 이어받기 위한 기록입니다.

## 준비

- 저장소 루트의 `.env.local` 에 `SUPABASE_URL`(또는 `NEXT_PUBLIC_SUPABASE_URL`)과 `SUPABASE_SERVICE_ROLE_KEY` 가 있어야 합니다. 경로는 스크립트 위치 기준으로 계산합니다(`scripts/eq-robot` → 두 단계 위).
- 운영 DB에 직접 씁니다. 실행 전에 코드를 읽고, 중복 방지 장치가 있는 것만 다시 돌리세요.
- 내려받는 파일은 `~/Downloads/<폴더>` 로 저장됩니다 (eq_levels, eq_extra, eq_old2, eq_thinking, eq_uncontact, eq_basic_edu, eqkids_dl).
- 임시 파일은 시스템 임시 폴더(`tempfile.gettempdir()`)를 씁니다.
- 자료 원본(PDF 등 22MB)은 저장소에 넣지 않았습니다. 필요하면 아래 EQ 사이트에서 다시 받으세요.

## 스크립트

| 파일 | 한 일 |
|---|---|
| `eq_parts.py` | EQ로봇 부품 194행 등록(이름·단계·수량만, 3D 없음). `--write` 를 줘야 실제 등록, 대상 카테고리에 이미 부품이 있으면 assert 로 멈춤(재실행 안전) |
| `eq_dl.py` | EQ로봇교실 1~5단계 자료를 emsv6.eqrobot.com 에서 `~/Downloads/eq_levels` 로 내려받고 `eq_manifest/catalog.json` 작성. 이미 받은 파일은 건너뜀(재실행 안전) |
| `eq_up.py` | 내려받은 EQ 자료를 Storage 에 올리고 교재에 연결 |
| `eq_extra.py` | EQ 추가 모델 자료 내려받기·올리기. 이미 있는 파일명은 건너뜀(재실행 안전) |
| `split_extra.py` | 추가 모델을 1-1차시처럼 분리(전 상태를 `~/Downloads/eqkids_dl/1808/row_before_split.json` 에 백업) |
| `add_prep.py` | 교재마다 0차시 "준비" 추가(전 상태를 `row_before_prep.json` 에 백업). 이미 "준비"가 있으면 skip(재실행 안전) |
| `thinking.py` | EQ씽킹 자료를 발명 교재로 등록 |
| `think_video.py` | EQ씽킹 영상 안내 PDF 만들어 올리기 |
| `think_links.py` | EQ씽킹 차시에 유튜브 링크 연결 |
| `uncontact.py` | 비대면교육 PPT 를 EQ로봇교실 1~4단계에 연결. `dry` 인자는 확인만, 이미 같은 이름 파일이 있으면 건너뜀(재실행 안전) |
| `old_eq2.py` | (구)EQ2 별도 교재 등록 |
| `open_class.py` | 공개수업 교재 등록 |
| `basic_edu.py` | EQ로봇 기초교육(공개수업) 이미지 내려받기·교재 등록. 이미 있는 이미지는 건너뜀 |
| `verify_edu.py` | 기초교육 교재가 DB·Storage 와 맞는지 확인(읽기 전용) |
| `verify_unc.py` | 비대면교육 연결이 맞는지 확인(읽기 전용) |
| `sheet.py`, `ps2.py`, `cmp.py` | 새 조립도 GIF/PDF 와 옛 것을 나란히 붙인 대조 시트·유사도 비교(도우미, DB 안 씀). 입력은 임시 폴더의 `eq1808`, `eqold` 등 로컬 파일 |
| `recv.py` | 브라우저에서 보낸 파일을 받는 작은 로컬 서버(`python recv.py <저장폴더>`, 도우미) |

`eq_manifest/` = 내려받기 목록(eq1~eq5.json, eq3_prog.json, catalog.json). `eq_dl.py`·`eq_up.py` 가 읽습니다. `old_urls.txt` = (구)EQ 주소 목록.

위 표에서 "재실행 안전"이라고 적지 않은 것은 중복 방지 장치를 코드에서 확인하지 못했으니 다시 돌리지 마세요.

## 같이 옮긴 것

- `scripts/assembly-tools/큐보/조립도/2권/speedbike/tools/` : `approve_hover.sh`(스크린샷은 PC마다 달라 다시 찍어야 함), `del_old_refs.py`(speedbike 34~37번 옛 참조 그림 삭제) — EQ와 무관한 speedbike 일회용.

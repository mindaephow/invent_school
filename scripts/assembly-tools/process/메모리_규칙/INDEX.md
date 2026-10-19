# 메모리 규칙 사본 — 다른 PC 의 Claude 도 같은 규칙으로 일하게 하는 곳 (2026-10-19)

이 폴더는 사용자 PC 의 Claude 메모리(`~/.claude/projects/.../memory`)에서 **조립도·invent_school 에 관한 것만** 복사한 사본이다.
메모리는 PC 마다 따로라서, 외부 PC 의 Claude 는 이 교정들을 모른 채 규칙을 어긴다(2026-10-19 외부 PC 에서 5시간 동안 한 번호도 못 끝낸 사고). 그래서 git 에 둔다.

## 외부 PC 의 Claude 는 이렇게 쓴다
1. 번호 작업을 시작하기 전에 **아래 "필독" 파일 전부를 읽는다**(짧다). 읽었다는 증거로 첫 보고에 "이번 번호에서 지킬 규칙 3개"를 적는다.
2. 막히거나 사용자가 화낼 만한 상황(방향·구멍·카메라·부시·모터·거울·검증 우회 등)이 오면 아래 표에서 해당 파일을 찾아 읽는다.
3. 이 사본이 원본보다 오래됐을 수 있다 — 사용자 PC 에서 `process/메모리_규칙/동기화.md` 절차로 갱신한다. 새 교정을 받으면 이 폴더의 같은 이름 파일에 적고 사용자가 푸시한다(메모리에만 적지 않는다).

## 필독 (번호 시작 전 매번)
- `feedback_reread_rules_before_each_number.md` — SKILL.md 처음부터 다시 읽고 규칙 3개 적고 시작
- `feedback_rules_are_the_fast_way.md` — 규칙 생략 금지, 번호마다 전부
- `feedback_no_bypass_options.md` · `feedback_rulecheck_no_workarounds.md` — 검증 우회·몰래 사용 금지
- `feedback_run_tools_before_judging.md` — 막히면 도구(holefit→plate_match→infer)부터, 눈 판단 금지
- `feedback_hole_line_first_button.md` · `feedback_holeline_both_parts.md` — 홀라인이 첫 단추, 양쪽 부품 모두
- `feedback_placement_first_button.md` · `feedback_no_skipping_prior_process.md` — 놓기 전 방향 사실을 책에서 읽기, 앞 과정 건너뛰지 않기
- `feedback_verify_by_next_book_first.md` · `feedback_prove_assembly_against_books.md` · `feedback_check_all_angles_no_excuses.md` — 끝내기 전 검증
- `feedback_stop_when_big_mismatch.md` · `feedback_dont_stop_for_gate_confirmations.md` — 멈출 때와 멈추지 않을 때
- `feedback_dont_touch_users_screen.md` · `feedback_no_full_page_reload.md` · `feedback_answer_questions_dont_change_things.md` — 화면·확인된 것은 건드리지 않음
- `feedback_user_set_values_take_priority.md` · `feedback_follow_admin_fix_instructions.md` — 사용자 지정값·수정 지시 우선
- `feedback_fix_rules_when_broken.md` · `feedback_checklist_before_done.md` — 규칙 어기면 규칙을 고침, 끝내기 전 체크리스트
- `feedback_use_formal_korean.md` · `feedback_flag_confidence_level.md` — 존댓말, 확인한 것/추정 구분
- `feedback_dont_prebuild_dont_push_often.md` · `feedback_no_unilateral_action.md` — 요청 안 한 것·푸시 금지

## 전체 색인
- [Diagnose, don't re-explain](feedback_diagnose_dont_explain.md) — when user says a UI element is missing, go look/fix, don't repeat navigation instructions
- [Parse scope before removing](feedback_parse_scope_before_removing.md) — a scope qualifier in the next message can change what a prior "remove X" meant; don't delete a liked feature on a first-message reading
- [No unilateral action](feedback_no_unilateral_action.md) — sharing a reference isn't authorization to act on it; propose and wait for go-ahead before writes
- [Verify before claiming](feedback_verify_before_claiming.md) — don't say "now it shows/renders" without actually looking at the live page first
- [Policy statement vs execution](feedback_policy_statement_vs_execution.md) — "앞으로 이렇게 해야지" is a design principle, not a command to execute now
- [Use formal Korean](feedback_use_formal_korean.md) — Claude always replies in 존댓말, never mirrors user's 반말/informality
- [Break into steps](feedback_break_into_steps.md) — don't silently grind through large multi-call tasks; checkpoint progress, push in smaller increments
- [발명융합과학교실 (invent_school)](project_invent_school.md) — live at invent-school-sigma.vercel.app; teacher approval + HQ admin + Google login, design tool save/load/rating; HongHub plan is the full write-up; user pushes, test accounts pending cleanup
- [Role parity](feedback_role_parity.md) — give teacher and student the same tool capabilities by default (teacher "no-save mode" got "why isn't the teacher saving?!"); add role-specific extras, don't strip features
- [Verify security of what I recommend](feedback_verify_security_of_what_i_recommend.md) — SECURITY DEFINER run_sql_query was open to the public key; revoke + test with anon key after every DB change
- [Exact clicks, one step](feedback_exact_clicks_one_step.md) — user gets lost with vague technical steps; give direct URL + button names, one step at a time, verify their result myself
- [Do only the stated step](feedback_do_only_the_stated_step.md) — "add part X before I show the result" = add X only; don't invent its interactions (clip join mechanic got "무슨 병신짓")
- [Use 불러오기 not 샘플 열기](feedback_use_load_not_sample_invent_school.md) — live-test design.html by loading the user's saved project, never the disposable sample
- [No dead code left behind](feedback_no_dead_code_left_behind.md) — when a feature moves to a new file, delete the old copy in the same change, don't leave superseded code behind
- [Coordinate notation style](feedback_coordinate_notation_style.md) — invent_school hole coords: plain "구멍N: X.., Z.." lines only, no "1-1"/tuple codes or tables, row-major order, 수치 vs 번호 are distinct
- [Fix all display layers](feedback_fix_all_display_layers.md) — a numbering/label fix must cover every place it's shown (live render AND DB-stored copies), not just the first code path found
- [Don't mention svg](feedback_dont_mention_svg.md) — invent_school parts: explain from spec JSON or the rendered image only, never from svg parsing/file-position reasoning
- [Port reference exactly](feedback_port_reference_exactly.md) — when told to copy a working reference file (_compare_all.html), port literal values/order, don't re-derive equivalent logic — that's how the bracket winding/z-fighting/dedup bugs happened
- [Flag confidence level](feedback_flag_confidence_level.md) — say "확인했습니다" only for checked facts vs "제 판단으로는" for inference; stating opinions flatly reads as citing an established rule
- [큐보 조립 규칙·진행](project_cubo_assembly_rules.md) — 조립 보기(토끼 22단계) 규칙·현재 배치(머리 −x/뒤 +x)·표시 방식·남은 일; 전 단계 사용자와 다듬어 올림
- [등록된 색 그대로](feedback_use_registered_colors.md) — 부품 색 강조·덧입히기 금지, 화살표/원으로 표시
- [방향·위치·홀 직접 검증](feedback_check_direction_position_hole.md) — 겹침 없음≠정답; 결합 검사+확대 화면+구멍 수 세기, DB 설명 틀리면 바로 수정
- [invent_school 로컬 캐시](project_invent_school_local_cache.md) — IndexedDB 캐시 구조·측정(부품 목록 즉시, 3D 모델 24ms, 36부품 41ms)·무효화·주의점
- [큐보 3D 디자인 MCP](project_cubo_design_mcp.md) — 자유 배치용 도구 8개(compute_attach 등), 저장 형식, 한계·미정
- [큐보 부품 만들기 규격](project_cubo_part_standard.md) — 프레임·블록 확정 규격, scripts/make-part-stl.mjs 로 STL 생성, 사용자가 직접 등록
- [포뮬러원 조립도 진행](project_formula1_status_1008.md) — 저장소 process/진행기록_formula1.md 로 옮김(포인터)
- [조립도: 멈추지 말고 끝까지](feedback_windmill_finish_all_no_stepwise_confirm.md) — "N번부터 진행해"=끝 번호까지 이어서; 번호별 절차(격자·표·비교)는 하되 확인 기다리며 멈추지 않음(풍차·포뮬러원 2번 화냄). 안내서의 멈춤 문구는 2026-10-07 삭제함, 푸시·승인잠금·DB등록만 사용자 말 대기
- [풍차 조립도 진행](project_windmill_assembly.md) — 저장소 process/진행기록_windmill.md 로 옮김(포인터)
- [규칙 없는 부품도 유추해서 만들기](feedback_infer_parts_from_base_rules.md) — 기어·T축 등 '규칙 없음' 금지, 기본 규격으로 유추해 먼저 만들고 보여 주기
- [확인용 SVG 금지](feedback_no_svg_for_checking.md) — 부품 모양 확인은 3D 뷰어로, 임시 2D SVG 만들지 말 것
- [큐보 부품 마무리 상태 10/1](project_cubo_parts_status_1001.md) — 49/52종 모델+연결점, 새 세션 조립도 출발점
- [축구로봇 조립도 진행](project_soccer_robot_assembly.md) — 저장소 process/진행기록_soccer.md 로 옮김(포인터)
- [끝내기 전 규칙 체크리스트](feedback_checklist_before_done.md) — 자동 검사 0건≠완료; 안내서 규칙을 항목별로 맞추고 한 것/안 한 것 나눠 보고
- [오토건 조립도 진행](project_autogun_status_1002.md) — 저장소 process/진행기록_autogun.md 로 옮김(포인터)
- [관리자 수정 지시는 그대로 따른다](feedback_follow_admin_fix_instructions.md) — 설득 5시간 낭비 사례; 우려는 근거 한 줄 한 번, 범위 확장 금지, 앞 단계 수정은 뒤가 따라오게
- [큐보 스튜디오 용어](project_cubo_studio_vocabulary.md) — 교재→조립도 만들기/수정/검토 작업 공간의 이름; 이 말이 나오면 안내서 절차로
- [교재는 순서대로 읽는다](feedback_textbook_reading_sequential.md) — 쓴 부품·남은 부품·빈 구멍으로 후보를 좁힘; 중간 쪽 한 장만 붙들고 튜닝 금지
- [미리 하지 말고 푸시는 모아서](feedback_dont_prebuild_dont_push_often.md) — 요청 안 한 업로드·푸시 금지, 푸시는 사용자가 말했을 때 한 번에
- [연결점은 부품에 붙은 맞물림 방식](feedback_connection_points_attached_mates.md) — guideMode="mates" 기본, 손 보정 값(marks 등) 쓰지 않음; 7ce698e
- [비행기 조립도 진행](project_airplane_assembly_status.md) — 저장소 process/진행기록_airplane.md 로 옮김(포인터)
- [질문엔 답만, 확인된 단계는 건드리지 않음](feedback_answer_questions_dont_change_things.md) — 질문 중 화면을 바꾸거나 좋다고 한 카메라를 다시 바꿔 크게 화냄
- [대각선 그림은 돌려서 읽기](feedback_rotate_diagonal_images.md) — 모든 책이 대각선 샷; 처음부터 축이 가로가 되게 회전·확대해 구멍 수를 센다
- [롤링봇 조립도 진행](project_rollingbot_status.md) — 저장소 process/진행기록_rollingbot.md 로 옮김(포인터)
- [꼬마기사 조립도 진행](project_kidknight_status.md) — 저장소 process/진행기록_kidknight.md 로 옮김(포인터)
- [완성 모양은 뒤 단계로 이어 간다](feedback_carry_finished_state_forward.md) — 알면서 물어보지 말고 바로 적용; 26~36·30~36 누락 사례
- [격자는 먼저 만든다](feedback_always_make_grid_first.md) — 단계마다 격자 확인·제작·등록, 불필요/불가를 혼자 정하지 않음(25번 짐작·20번 불가 문구 사례)
- [앞·뒤 번호와 완성 사진을 같이 본다](feedback_read_neighbors_and_finished_photo.md) — 한 장만 보고 모델에 맞춰 읽다 11·12번 틀림; 링이 안 맞으면 내 모델이 틀린 것
- [강아지로봇 조립도 진행](project_dog_robot_restart.md) — 저장소 process/진행기록_dog.md 로 옮김(포인터)
- [메인보드는 결합 방법부터 확인](feedback_check_mainboard_method.md) — measure_part 실측+교재 뒷모습으로 방향 맞춤, 칸은 관리자 지시 따름(35번 위아래 거꾸로 사례)
- [격자는 만들면 바로 DB 등록](feedback_register_grids_when_made.md) — 🖼 는 DB 를 읽으므로 render 직후 등록, 푸시만 "업로드" 뒤
- [카메라 방향은 책에서 읽어 맞춘다](feedback_camera_direction_from_book.md) — theta 규약, 읽기 표 방향 칸·작업 점검, 짐작 금지(28·29번 거울 사고)
- [전체 새로고침 금지](feedback_no_full_page_reload.md) — build 뒤 차시 select 12→13 토글 + 번호 클릭, location.reload 쓰지 않음
- [부품은 제자리에 바른 방향으로](feedback_placement_first_button.md) — 첫 단추: 놓기 전 방향 사실을 책 격자에서 읽고 놓은 뒤 좌표로 대조(34 거울·36 강체·41 브래킷 사례)
- [스피드바이크 조립도 진행](project_speedbike_status.md) — 저장소 process/진행기록_speedbike.md 로 옮김(포인터)
- [방향은 X·Y·Z 축으로](feedback_direction_xyz_axes.md) — 수평선 대신 번호마다 _axes.json 축선·방향 표시판, 처음 놓을 때·창고 꺼낼 때·모터/메인보드 방향 카드, 센 값만, DB 는 바로 업로드
- [투석기 조립도 진행](project_catapult_status.md) — 저장소 process/진행기록_catapult.md 로 옮김(포인터)
- [축선·격자로 위치 읽기](feedback_same_line_parts_check.md) — 투석기 5번 리벳(축과 한 줄인데 칸3으로 읽음); 이미 놓은 부품을 지나는 축선+격자를 먼저 보고 환산은 그 다음
- [부시 방향 규칙](feedback_bush_orientation_rule.md) — 넓은 쪽 바깥, 좁은 쪽(모델 +y)이 축에 먼저 들어가며 판을 향함; 늘 같은 방식
- [검증 우회 옵션 삭제](feedback_no_bypass_options.md) — build.py 는 --write 뿐, 확인 근거는 사용자 ✓(DB), 마지막 번호 하나만 ✓ 없이 저장; 우회·몰래 사용 금지
- [규칙 어기면 규칙을 고쳐 덮어쓴다](feedback_fix_rules_when_broken.md) — 위반 원인(조건부 문구·확인 장치 없음)을 찾아 가이드·SKILL·도구에 반영, 16번 axes 복사 사례, axes_fit.py
- [번호 시작 전 규칙부터 다시 읽기](feedback_reread_rules_before_each_number.md) — SKILL.md 를 처음부터 다시 읽고 지킬 규칙 3개 적은 뒤 시작, 격자부터 들어가지 않음(17번)
- [부시 규칙 정리 보류 10/11](project_bush_rule_cleanup_deferred.md) — 어긋난 부시 9개·DB through=false 시 11개 조립도 깨짐·❄ 반영 푸시됨, 나중에
- [사용자 교정 기록 두 파일](reference_user_diffs.md) — 요청차이·수정저장차이(collect_diffs.py), 번호 시작 전 훑기
- [움직이기 전 막는 부품 계산](feedback_check_blocking_parts_before_moving.md) — 22번 팔 90° 가 2단블록 뚫음; 책 먼저 보고 한계각 계산, 고무줄은 bands(바깥·통과·8자·팽팽)
- [홀라인 맞추기가 첫 단추](feedback_hole_line_first_button.md) — holefit.py 로 격자 맞추고 hf 그림 눈으로 확인 후 축·방향
- [앞 과정 건너뛰지 않기](feedback_no_skipping_prior_process.md) — 드롭체커 1번: 04 창고 정리 건너뜀·눕힌 판 가정·오른쪽 위 xyz 그림; 이제 number_start 가 막음, 판 자세는 책에서 먼저 읽기
- [드롭체커 조립도 진행](project_dropchecker_status_1012.md) — 저장소 process/진행기록_dropchecker.md 로 옮김(포인터)
- [막히면 우회하지 않고 멈춘다](feedback_rulecheck_no_workarounds.md) — holefit 옵션·손 격자·추정 카메라 금지, rulecheck.py 가 자동 판정, 승인은 사용자 말씀만
- [재시작 시 서버·로그인 먼저](feedback_check_server_login_on_restart.md) — 번호 작업을 (다시) 시작할 때 개발서버 3178·설계 화면 로그인부터 확인하고 요청
- [원본 그림+구멍 점 축선](feedback_image_original_axes_from_holes.md) — 이미지 회전은 해도 되고 안 해도 된다(2026-10-14) — 기준은 조립도를 잘 그리는 문제 해결; rotate_to·level·no_rotate 모두 선택지로 유지
- [분리 = 결합 전 모습](feedback_separate_means_pre_assembly.md) — "분리해줘"는 부품마다 띄워 화살표 표시; 제자리는 돌기-구멍 거리 0, 드롭체커 27번(p3→프레임, 프레임→25프레임→블록 순서)
- [드롭체커 28~30번 진행(옛)](project_dropchecker_28_status.md) — 저장소 process/진행기록_dropchecker.md 로 옮김(포인터, 위 항목과 같은 조립도)
- [도구 먼저, 눈 판단 금지](feedback_run_tools_before_judging.md) — 막히면 holefit→plate_match→infer 앵커를 돌려 숫자로; 앞 번호 모델 = 3D 앵커; 칸 선택은 순방향 투영; 유추 격자는 사용자 ✓ 필요
- [사용자가 지정한 값이 무조건 우선](feedback_user_set_values_take_priority.md) — ❄ 모습 기록·📷 카메라는 코드·내 계산을 덮는다: 번호 시작 때 먼저 읽고, 고치라면 코드+기록 함께(pose_edit.py)
- [자동화: 내가 판단·폰으로 사진 보내기](feedback_automate_decide_and_send_photos.md) — ✓ 대기 때문에 멈추지 않는다; 번호마다 책+화면을 폰으로 보내 비차단 허락
- [수정 지시는 되돌리지 말고 요청](feedback_fix_means_keep_edit_and_request_unlock.md) — ✓ 잠금에 막혀도 수정은 유지하고 ✓ 해제를 요청
- [확인 안 된 대안 제시 금지](feedback_dont_offer_unverified_alternatives.md) — 대안·한도·요금은 검색으로 확인한 것만 출처와 함께, 기억 기반 표+"직접 확인하세요"는 욕먹음
- [카메라 수정은 오류가 아님](feedback_camera_edits_are_polish_not_errors.md) — 사용자 📷 값은 마지막 보기 좋게 다듬은 것, 오류 분석에 넣지 않음(❄·요청차이만)
- [배틀로봇 조립도 진행](project_battlerobot_status.md) — 저장소 process/진행기록_battlerobot.md 로 옮김(포인터)
- [사용자 화면 조작 금지](feedback_dont_touch_users_screen.md) — pane 패널 접기·카메라·관절 토글·전체 새로고침을 요청 없이 하지 말고, 필요하면 먼저 허락(2026-10-16 화냄)
- [회전하는 곳은 항상 관절 표시](feedback_mark_rotating_joints.md) — 도는 부품은 번호 만들 때 바로 관절 등록, 모터 직결 축만 [모터직결] 형광라임(2026-10-16)
- [조립 결과는 책에 겹쳐 증명](feedback_prove_assembly_against_books.md) — PnP 카메라로 모델을 책 그림에 겹쳐 오차로 가설 가르고, 증명 그림(NN_3·4)+읽기 표에 남김(어보이더 18번)
- [게이트 확인에서 멈추지 않기](feedback_dont_stop_for_gate_confirmations.md) — 방향선 등 '사용자 확인' 문턱에서 wrap_up 으로 멈추지 말고 추정 표시하고 끝까지(2026-10-17 '돌았어?' 화냄)
- [배틀로봇 조립도 상태](project_battlerobot2_status.md) — 1~37번 완성·증거·관절·그림 업로드 끝, 푸시 전, 32·36번 자세 추정
- [크게 어긋나면 멈춘다](feedback_stop_when_big_mismatch.md) — 책과 모델이 크게 안 맞으면 추정으로 넘기지 말고 그 번호에서 멈추고 보고(배틀로봇 32번)
- [새 창고는 원점에](feedback_new_warehouse_at_origin.md) — slot 2 번호를 멀리(x200·z250~800) 놓지 않기, 어두운 판은 holesearch 먼저(배틀로봇 2026-10-18 화냄)
- [규칙이 곧 빠른 길](feedback_rules_are_the_fast_way.md) — '10번까지'는 규칙 생략이 아님, 번호마다 홀라인·돌기↔구멍 표·증거 전부(2026-10-18 화냄)
- [번호 검증 도구 verify_step.py](project_verify_step_tool.md) — 번호를 끝내기 전에 돌려 홀라인·카메라·돌기↔구멍·대조 그림·증거를 ✅/⚠/❌ 표로 확인
- [invent_school 푸시 원격](reference_invent_school_push_remote.md) — origin 없음, git push newrepo main
- [홀라인은 양쪽 부품 모두](feedback_holeline_both_parts.md) — 받는 쪽·끼우는 쪽 격자 둘 다, 책 링 칸을 양쪽에서 세고 recv 에 구멍 id 명시(오토타깃 18번 2026-10-19)
- [검증은 책 비교 → 다음 책 비교 먼저](feedback_verify_by_next_book_first.md) — 도구 목록 설명 말고 어느 책과 무엇이 같은지부터, 안 맞을 때만 규칙 점검(오토타깃 19번)
- [카메라 돌려 직접 확인, 핑계 금지](feedback_check_all_angles_no_excuses.md) — 끝내기 전 4방향 스샷 확인(상시 허락), 되묻지 말고, 핑계는 스샷 증거로; 떠 있는 리벳=seated(오토타깃 18·19번)
- [메모리→저장소 동기화](feedback_sync_memory_rules_to_repo.md) — 조립도 메모리를 고치면 sync_memory_rules.py 로 저장소 사본 갱신(외부 PC 용, 2026-10-19)

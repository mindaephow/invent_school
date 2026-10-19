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


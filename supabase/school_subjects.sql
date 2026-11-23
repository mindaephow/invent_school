-- 학교별 허용 과목: 학교 달력 문서(ivs_school_calendars.data)에 subjects(['goldberg','robot',...])로 저장한다.
-- 학생이 자기 학교의 설정을 읽어 접근 가능한 과목을 알 수 있게, 학생 본인의 수업과 같은 학교·같은 선생님의 문서만 조회를 허용한다.
-- 개인별 추가 허용 과목은 ivs_students.data.subjects 에 저장되므로(학생이 이미 자기 행을 읽을 수 있음) 여기서 따로 열 것이 없다.
-- Supabase SQL 에디터에서 한 번 실행하면 된다(여러 번 실행해도 안전).

drop policy if exists school_calendars_student_read on public.ivs_school_calendars;
create policy school_calendars_student_read on public.ivs_school_calendars for select to authenticated
  using (exists (
    select 1
    from public.ivs_students s
    join public.ivs_courses c on c.id = s.course_id
    where s.user_id = auth.uid()
      and c.teacher_id = ivs_school_calendars.teacher_id
      and c.data->>'school' = ivs_school_calendars.data->>'school'
  ));

-- 학교별 허용 과목: 학교 달력 문서(ivs_school_calendars.data)에 subjects(['goldberg','robot',...])로 저장한다.
-- 학생이 자기 학교의 설정을 읽어 접근 가능한 과목을 알 수 있게, 학생 본인의 수업과 같은 학교·같은 선생님의 문서만 조회를 허용한다.
-- 개인별 추가 허용 과목은 ivs_students.data.subjects 에 저장되므로(학생이 이미 자기 행을 읽을 수 있음) 여기서 따로 열 것이 없다.
-- 정책 안에서 ivs_courses 를 직접 조회하면 학생은 수업을 못 읽어(RLS) 항상 거짓이 되므로, 보안 정의자(security definer) 함수로 확인한다.
-- Supabase SQL 에디터에서 한 번 실행하면 된다(여러 번 실행해도 안전).

create or replace function public.student_in_school(p_teacher uuid, p_school text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.ivs_students s
    join public.ivs_courses c on c.id = s.course_id
    where s.user_id = auth.uid()
      and c.teacher_id = p_teacher
      and c.data->>'school' = p_school
  );
$$;

revoke all on function public.student_in_school(uuid, text) from public;
grant execute on function public.student_in_school(uuid, text) to authenticated;

drop policy if exists school_calendars_student_read on public.ivs_school_calendars;
create policy school_calendars_student_read on public.ivs_school_calendars for select to authenticated
  using (public.student_in_school(teacher_id, data->>'school'));

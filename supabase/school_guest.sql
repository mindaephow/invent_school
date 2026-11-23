-- 학교 QR 로 들어온 "손님"(로그인 없음)이 조립도를 볼 수 있게 한다. 아이디·비밀번호는 과제를 낼 때만 필요하다.
-- 1) 학교가 열어 둔 과목 목록만 돌려주는 함수(보안 정의자): 학교 달력 문서 전체를 열지 않고 과목 이름 배열만 알려 준다.
--    설정이 한 번도 저장되지 않은 학교는 null 을 돌려주고, 화면은 그때 모든 과목을 연다.
-- 2) 조립도 화면이 읽는 회사 공통 자료(부품·교재·로봇 종류)를 로그인 없이도 읽게 연다(읽기만).
-- Supabase SQL 에디터에서 한 번 실행하면 된다(여러 번 실행해도 안전).

create or replace function public.school_subjects(p_school text)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  select d.data->'subjects'
  from public.ivs_school_calendars d
  where d.data->>'school' = p_school
    and jsonb_typeof(d.data->'subjects') = 'array'
  order by d.created_at desc
  limit 1;
$$;

revoke all on function public.school_subjects(text) from public;
grant execute on function public.school_subjects(text) to anon, authenticated;

grant select on public.ivs_part_catalog, public.ivs_textbooks, public.ivs_robot_categories to anon;

drop policy if exists "ivs_part_catalog anon select" on public.ivs_part_catalog;
create policy "ivs_part_catalog anon select" on public.ivs_part_catalog for select to anon using (true);

drop policy if exists "ivs_textbooks anon select" on public.ivs_textbooks;
create policy "ivs_textbooks anon select" on public.ivs_textbooks for select to anon using (true);

drop policy if exists "ivs_robot_categories anon select" on public.ivs_robot_categories;
create policy "ivs_robot_categories anon select" on public.ivs_robot_categories for select to anon using (true);

-- 학교별 안내문: 학교 달력 문서(ivs_school_calendars.data.notice = {text, updatedAt})에 저장한다.
-- 학교 QR 로 들어온 손님(로그인 없음)이 첫 화면에서 안내문을 읽을 수 있게, 안내문 글만 돌려주는 함수(보안 정의자)를 연다.
-- Supabase SQL 에디터에서 한 번 실행하면 된다(여러 번 실행해도 안전).
create or replace function public.school_notice(p_school text)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  select d.data->'notice'
  from public.ivs_school_calendars d
  where d.data->>'school' = p_school
    and jsonb_typeof(d.data->'notice') = 'object'
  order by d.created_at desc
  limit 1;
$$;

revoke all on function public.school_notice(text) from public;
grant execute on function public.school_notice(text) to anon, authenticated;

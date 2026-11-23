-- 학교 달력: 수업(ivs_courses.data.school)별로 학기/분기 기간·텀(기간 안의 소구간)·휴강일을 설정해둔다.
-- 출석부 탭 위쪽에서 선생님이 직접 관리한다. 이 파일은 Supabase SQL 에디터에서 한 번 실행하면 됨.
-- data 모양: { school: '청계초', periods: [{ id, label:'1학기', start:'2026-03-02', end:'2026-07-19',
--   subterms: [{ id, label:'1텀', start:'2026-03-02', end:'2026-03-27' }, ...] }, ...],
--   closedDates: ['2026-05-05', ...] }

create table if not exists public.ivs_school_calendars (
  id uuid primary key default gen_random_uuid(),
  teacher_id uuid not null default auth.uid() references public.ivs_teachers(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists ivs_school_calendars_teacher_id_idx on public.ivs_school_calendars (teacher_id);

alter table public.ivs_school_calendars enable row level security;

drop policy if exists school_calendars_own on public.ivs_school_calendars;
create policy school_calendars_own on public.ivs_school_calendars for all to authenticated
  using (teacher_id = auth.uid()) with check (teacher_id = auth.uid());

grant all on public.ivs_school_calendars to service_role;
revoke all on public.ivs_school_calendars from anon;
grant select on public.ivs_school_calendars to authenticated;
grant insert (data), update (data), delete on public.ivs_school_calendars to authenticated;

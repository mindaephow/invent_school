-- 로봇 커리큘럼 카테고리(브랜드별 권 수). 본사 관리자 페이지(admin.html)의 "로봇 카테고리 관리"에서 등록·수정·삭제.
-- 이 파일은 Supabase SQL 에디터에서 한 번 실행하면 됨.

create table if not exists public.ivs_robot_categories (
  id uuid primary key default gen_random_uuid(),
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.ivs_robot_categories enable row level security;

drop policy if exists "ivs_robot_categories select" on public.ivs_robot_categories;
create policy "ivs_robot_categories select" on public.ivs_robot_categories
  for select to authenticated using (true);

grant select on public.ivs_robot_categories to authenticated;
grant all on public.ivs_robot_categories to service_role;

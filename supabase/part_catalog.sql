-- 로봇·항공 등 새 과목의 부품 카탈로그(이름·아이콘만 등록, 실제 3D 모양은 코드로 별도 구현).
-- 본사 관리자 페이지(admin.html)의 "부품 등록"에서 씀. 이 파일은 Supabase SQL 에디터에서 한 번 실행하면 됨.

create table if not exists public.ivs_part_catalog (
  id uuid primary key default gen_random_uuid(),
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.ivs_part_catalog enable row level security;

drop policy if exists "ivs_part_catalog select" on public.ivs_part_catalog;
create policy "ivs_part_catalog select" on public.ivs_part_catalog
  for select to authenticated using (true);

grant select on public.ivs_part_catalog to authenticated;
grant all on public.ivs_part_catalog to service_role;

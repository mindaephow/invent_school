-- 조립 보기: 창고 카드 썸네일. 관리자가 단계 화면에서 📷 를 누르면 그 단계·작업 창고의 3D 화면 사진이 저장되고,
-- 이후 그 창고 카드(작업 중·보관 중 모두)에 가장 최근에 저장한 사진이 나온다.
-- Supabase SQL 에디터에서 한 번 실행하면 됩니다. (사용자가 직접 실행)
--   · 읽기: 로그인한 사람 누구나 / 쓰기: 본사 관리자(app_metadata.role = 'admin')만

create table if not exists public.ivs_assembly_thumbs (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id. 예: cubo-1-airplane
  step int not null,                  -- 사진을 찍은 단계 번호
  slot int not null,                  -- 그 단계의 작업 창고 번호(0~5)
  img text not null,                  -- JPEG data URL(작은 사진)
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  unique (assembly_id, step, slot)
);

alter table public.ivs_assembly_thumbs enable row level security;

drop policy if exists "ivs_assembly_thumbs select" on public.ivs_assembly_thumbs;
create policy "ivs_assembly_thumbs select" on public.ivs_assembly_thumbs
  for select to authenticated using (true);

drop policy if exists "ivs_assembly_thumbs admin write" on public.ivs_assembly_thumbs;
create policy "ivs_assembly_thumbs admin write" on public.ivs_assembly_thumbs
  for all to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

grant select, insert, update, delete on public.ivs_assembly_thumbs to authenticated;
grant all on public.ivs_assembly_thumbs to service_role;

-- 조립 보기: 관리자가 화면에서 끌어 맞춰 둔 "부품 모습"(부품마다 위치·회전)을 단계별로 기록한다(❄ 모습 기록 버튼).
-- 기록한 단계는 열 때 그 모습으로 보인다. 조립도를 다시 빌드해도 지워지지 않는다.
-- Supabase SQL 에디터에서 한 번 실행하면 됩니다. (사용자가 직접 실행)
--   · 읽기: 로그인한 사람 누구나 / 쓰기: 본사 관리자(app_metadata.role = 'admin')만

create table if not exists public.ivs_assembly_poses (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id. 예: cubo-1-airplane
  step int not null,                  -- 모습을 기록한 단계
  poses jsonb not null,               -- { "부품 이름 번호": { "p": [x,y,z], "q": [x,y,z,w], "r": [rx,ry,rz] } }
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  unique (assembly_id, step)
);

alter table public.ivs_assembly_poses enable row level security;

drop policy if exists "ivs_assembly_poses select" on public.ivs_assembly_poses;
create policy "ivs_assembly_poses select" on public.ivs_assembly_poses
  for select to authenticated using (true);

drop policy if exists "ivs_assembly_poses admin write" on public.ivs_assembly_poses;
create policy "ivs_assembly_poses admin write" on public.ivs_assembly_poses
  for all to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

grant select, insert, update, delete on public.ivs_assembly_poses to authenticated;
grant all on public.ivs_assembly_poses to service_role;

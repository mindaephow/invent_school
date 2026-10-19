-- 조립 보기: 단계마다 관리자가 맞춰 둔 카메라 시점(방향·높이각·보는 중심·거리).
-- 조립도 데이터 파일(public/design-assemblies.js)은 코드라서 화면에서 못 고치므로, 관리자가 📷 로 저장한 시점은 이 표에 두고
-- 조립 보기를 열 때 겹쳐서 쓴다. 조립도를 다시 빌드해도 이 표의 값은 지워지지 않는다.
-- Supabase SQL 에디터에서 한 번 실행하면 됩니다. (사용자가 직접 실행)
--   · 읽기: 로그인한 사람 누구나
--   · 쓰기(저장·덮어쓰기·삭제): 본사 관리자(app_metadata.role = 'admin')만 — app_metadata 는 서버만 바꿀 수 있어서 화면에서 속일 수 없다

create table if not exists public.ivs_assembly_cams (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id. 예: cubo-1-autogun
  step int not null,                  -- 조립도 단계 번호(1부터)
  cam jsonb not null,                 -- { "theta": 라디안, "phi": 라디안, "radius": 거리, "target": [x, y, z] }
  updated_by uuid,
  updated_at timestamptz not null default now(),
  unique (assembly_id, step)
);

alter table public.ivs_assembly_cams enable row level security;

drop policy if exists "ivs_assembly_cams select" on public.ivs_assembly_cams;
create policy "ivs_assembly_cams select" on public.ivs_assembly_cams
  for select to authenticated using (true);

drop policy if exists "ivs_assembly_cams admin insert" on public.ivs_assembly_cams;
create policy "ivs_assembly_cams admin insert" on public.ivs_assembly_cams
  for insert to authenticated
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

drop policy if exists "ivs_assembly_cams admin update" on public.ivs_assembly_cams;
create policy "ivs_assembly_cams admin update" on public.ivs_assembly_cams
  for update to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

drop policy if exists "ivs_assembly_cams admin delete" on public.ivs_assembly_cams;
create policy "ivs_assembly_cams admin delete" on public.ivs_assembly_cams
  for delete to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

grant select, insert, update, delete on public.ivs_assembly_cams to authenticated;
grant all on public.ivs_assembly_cams to service_role;

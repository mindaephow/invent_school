-- 조립 보기: 단계마다 관리자가 적는 작업 상태(수정중 / 완료). 관리자 화면에서만 보이고 단계 번호 버튼에 ✓(완료)·🛠(수정중)로 표시된다.
-- Supabase SQL 에디터에서 한 번 실행하면 됩니다. (사용자가 직접 실행)
--   · 읽기·쓰기 모두 본사 관리자(app_metadata.role = 'admin')만

create table if not exists public.ivs_assembly_status (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id. 예: cubo-1-airplane
  step int not null,                  -- 조립도 단계 번호(1부터)
  status text not null check (status in ('edit', 'done')),   -- edit = 수정중, done = 완료 (상태 없음 = 행 없음)
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  unique (assembly_id, step)
);

alter table public.ivs_assembly_status enable row level security;

drop policy if exists "ivs_assembly_status admin all" on public.ivs_assembly_status;
create policy "ivs_assembly_status admin all" on public.ivs_assembly_status
  for all to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

grant select, insert, update, delete on public.ivs_assembly_status to authenticated;
grant all on public.ivs_assembly_status to service_role;

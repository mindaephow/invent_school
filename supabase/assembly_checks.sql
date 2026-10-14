-- 조립 보기: 자동 검사(끼움/분리 가능 검사)가 낸 경고를 관리자가 보고 고른 결과(문제없음 / 해결요청).
-- 관리자 화면에서만 보인다. Supabase SQL 에디터에서 한 번 실행하면 됩니다. (사용자가 직접 실행)
--   · 읽기·쓰기 모두 본사 관리자(app_metadata.role = 'admin')만
--   · issue_key = 경고마다 정해지는 이름(부품·막은 부품 조합). 데이터를 고쳐서 경고가 사라지면 이 행은 그냥 남아도 된다.

create table if not exists public.ivs_assembly_checks (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id. 예: cubo-1-kidknight
  step int not null,                  -- 조립도 단계 번호(1부터)
  issue_key text not null,            -- 경고 이름
  verdict text not null check (verdict in ('ok', 'fix')),   -- ok = 문제없음, fix = 해결요청 (아직 안 골랐으면 행 없음)
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  unique (assembly_id, step, issue_key)
);

alter table public.ivs_assembly_checks enable row level security;

drop policy if exists "ivs_assembly_checks admin all" on public.ivs_assembly_checks;
create policy "ivs_assembly_checks admin all" on public.ivs_assembly_checks
  for all to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

grant select, insert, update, delete on public.ivs_assembly_checks to authenticated;
grant all on public.ivs_assembly_checks to service_role;

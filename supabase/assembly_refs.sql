-- 조립 보기: 교재 참고 그림(관리자와 Claude 만 본다).
-- 조립 순서 목록 오른쪽 "🖼" 버튼과 "조립 순서" 제목 오른쪽 "🖼 완성 사진" 버튼이 이 표를 읽는다.
--   step 0  = 교재 맨 앞 완성품 사진(앞·뒤·정면을 확인하는 기준), step 99 = 교재 마지막 쪽 "완성" 그림
--   step 1~ = 그 단계 그림(idx 0), idx 1 이상 = 돌리거나 확대해서 칸을 센 그림
-- Supabase SQL 에디터에서 한 번 실행하면 됩니다. (사용자가 직접 실행)
--   · 읽기·쓰기 모두 본사 관리자(app_metadata.role = 'admin')만 — Claude 는 MCP(서비스 키)로 읽고 쓴다
--   · 그림은 JPEG data URL(작은 사진)로 이 표에 둔다. 원본 파일은 scripts/assembly-tools/refs/<이름>/ 에도 있다(refs_make.py)

create table if not exists public.ivs_assembly_refs (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id. 예: cubo-1-kidknight
  step int not null,                  -- 0 = 완성품 사진, 1~ = 조립 단계, 99 = 교재의 "완성" 그림
  idx int not null default 0,         -- 같은 단계의 그림 순서(0 = 교재에서 잘라 낸 그림, 1~ = 돌리거나 확대한 그림)
  img text not null,                  -- JPEG data URL
  note text not null default '',      -- 그림 설명(예: "33° 돌려 판을 수평으로 — 판 3줄×9칸")
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  unique (assembly_id, step, idx)
);

alter table public.ivs_assembly_refs enable row level security;

drop policy if exists "ivs_assembly_refs admin" on public.ivs_assembly_refs;
create policy "ivs_assembly_refs admin" on public.ivs_assembly_refs
  for all to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

grant select, insert, update, delete on public.ivs_assembly_refs to authenticated;
grant all on public.ivs_assembly_refs to service_role;

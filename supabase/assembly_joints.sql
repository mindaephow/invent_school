-- 조립 보기: 회전 관절(중심점으로 움직이는 곳)과 움직이는 묶음. 관리자가 적고, 빌드 검사·화면이 읽는다.
-- Supabase SQL 에디터에서 한 번 실행하면 됩니다. (사용자가 직접 실행)
--   · 읽기·쓰기 모두 본사 관리자(app_metadata.role = 'admin')만, 서버(service_role)는 전부
--   · 묶음(joint_groups) = 한 덩어리로 같이 움직이는 부품들(예: 팔 묶음, 기어 크랭크 묶음). 묶음 안에 묶음을 넣을 수 있다(parent_group_id).
--   · 관절(joints) = 그 묶음이 도는 중심점. 결합 검사에서는 "회전 허용"으로 다룬다.

-- 1) 움직이는 묶음
create table if not exists public.ivs_assembly_joint_groups (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id. 예: cubo-2-mantis
  group_id text not null,             -- 묶음 이름표(조립도 안에서 하나). 예: arm1, gear_crank1
  name text not null,                 -- 화면에 보일 이름. 예: 첫째 유닛 팔 묶음
  parent_group_id text,               -- 이 묶음이 들어 있는 바깥 묶음(없으면 null)
  kind text not null default 'body' check (kind in ('body', 'link')),   -- body = 축 기준으로 도는 덩어리(기어·팔), link = 양 끝 관절 사이를 잇는 막대(19프레임)
  link_length double precision,       -- kind = link 일 때 막대 길이(mm). 예: 19프레임 80
  root_joint_id text,                 -- 이 묶음이 도는 중심 관절(joints.joint_id)
  members jsonb not null default '[]'::jsonb,   -- 묶음에 든 부품들: [{"name":"215프레임 1번"}, ...] (조립도 부품 이름·번호)
  note text,
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  unique (assembly_id, group_id)
);

-- 2) 회전 관절
create table if not exists public.ivs_assembly_joints (
  id uuid primary key default gen_random_uuid(),
  assembly_id text not null,          -- 조립도 id
  joint_id text not null,             -- 관절 이름표(조립도 안에서 하나). 예: gear_pin1, arm_rivet1
  name text not null,                 -- 화면에 보일 이름. 예: 기어 T축 핀(첫째 유닛)
  step int not null,                  -- 이 관절이 처음 생기는 번호(1부터)
  group_id text,                      -- 이 관절이 움직이는 묶음(joint_groups.group_id)
  kind text not null default 'axis' check (kind in ('axis', 'pin')),    -- axis = 판에 고정된 축(위치 안 변함), pin = 묶음을 따라 움직이는 핀
  rides_group_id text,                -- kind = pin 일 때 이 핀이 올라타 움직이는 묶음(joint_groups.group_id). 예: gear_pin 은 기어 묶음
  is_driver boolean not null default false,   -- 구동 관절(기어 축처럼 돌려 주는 쪽)
  part_a text not null,               -- 관절로 이어진 부품 A(조립도 부품 이름·번호). 예: 215프레임 1번
  part_b text not null,               -- 부품 B. 예: 19프레임 2번
  pivot_x double precision not null,  -- 회전 중심(조립도 좌표, mm)
  pivot_y double precision not null,
  pivot_z double precision not null,
  axis_x double precision not null default 0,   -- 회전축 방향(단위벡터)
  axis_y double precision not null default 0,
  axis_z double precision not null default 1,
  min_angle double precision,         -- 움직일 수 있는 각도(도). 제한 없으면 null
  max_angle double precision,
  note text,
  updated_by uuid default auth.uid(),
  updated_at timestamptz not null default now(),
  unique (assembly_id, joint_id)
);

create index if not exists ivs_assembly_joints_asm_step on public.ivs_assembly_joints (assembly_id, step);

alter table public.ivs_assembly_joint_groups enable row level security;
alter table public.ivs_assembly_joints enable row level security;

drop policy if exists "ivs_assembly_joint_groups admin all" on public.ivs_assembly_joint_groups;
create policy "ivs_assembly_joint_groups admin all" on public.ivs_assembly_joint_groups
  for all to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

drop policy if exists "ivs_assembly_joints admin all" on public.ivs_assembly_joints;
create policy "ivs_assembly_joints admin all" on public.ivs_assembly_joints
  for all to authenticated
  using (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
  with check (coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin');

grant select, insert, update, delete on public.ivs_assembly_joint_groups to authenticated;
grant select, insert, update, delete on public.ivs_assembly_joints to authenticated;
grant all on public.ivs_assembly_joint_groups to service_role;
grant all on public.ivs_assembly_joints to service_role;

-- 이미 앞 버전을 실행한 경우: 아래 컬럼만 추가된다(여러 번 실행해도 안전)
alter table public.ivs_assembly_joint_groups add column if not exists kind text not null default 'body';
alter table public.ivs_assembly_joint_groups add column if not exists link_length double precision;
alter table public.ivs_assembly_joints add column if not exists kind text not null default 'axis';
alter table public.ivs_assembly_joints add column if not exists rides_group_id text;
alter table public.ivs_assembly_joints add column if not exists is_driver boolean not null default false;

-- 선생님도 3D 설계 프로젝트를 저장/이어하기 할 수 있도록 선생님 전용 테이블 (SQL 에디터에서 한 번 실행)
-- 학생 프로젝트(ivs_projects)와 분리 — 제출/출석부와 무관한 선생님 본인 작업 저장용

create table public.ivs_teacher_projects (
  id uuid primary key default gen_random_uuid(),
  teacher_id uuid not null default auth.uid() references public.ivs_teachers(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index on public.ivs_teacher_projects (teacher_id);

alter table public.ivs_teacher_projects enable row level security;

-- 승인된 선생님 본인만
create policy teacher_projects_own on public.ivs_teacher_projects for all to authenticated
  using (teacher_id = auth.uid() and exists (select 1 from public.ivs_teachers t where t.id = auth.uid() and t.approved))
  with check (teacher_id = auth.uid() and exists (select 1 from public.ivs_teachers t where t.id = auth.uid() and t.approved));

grant all on public.ivs_teacher_projects to service_role;
revoke all on public.ivs_teacher_projects from anon;
grant select on public.ivs_teacher_projects to authenticated;
grant insert (data), update (data), delete on public.ivs_teacher_projects to authenticated;

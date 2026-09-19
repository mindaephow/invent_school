-- 선생님의 과제 평가·조언 (SQL 에디터에서 한 번 실행)
-- 프로젝트 안(data)이 아니라 별도 테이블에 두는 이유: 학생이 자기 프로젝트는 고칠 수 있으므로, 선생님이 남긴 평가를 학생이 바꾸지 못하게 하기 위해서.
-- 과제(프로젝트) 하나에 평가 하나. 선생님은 담당 수업 학생의 과제에만 쓸 수 있고, 학생은 자기 것만 읽을 수 있음.

create table public.ivs_feedback (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null unique references public.ivs_projects(id) on delete cascade,
  course_id uuid not null references public.ivs_courses(id) on delete cascade,
  student_id uuid not null references public.ivs_students(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,   -- { projectId, rating(1~5), advice, updatedAt }
  created_at timestamptz not null default now()
);
create index on public.ivs_feedback (course_id);
create index on public.ivs_feedback (student_id);

-- 권한 판단용 컬럼은 data.projectId로 찾은 프로젝트에서 채운다 (호출한 선생님의 권한으로 조회하므로 남의 수업 프로젝트는 찾을 수 없음)
create function public.ivs_feedback_derive() returns trigger language plpgsql as $$
declare p public.ivs_projects;
begin
  select * into p from public.ivs_projects where id = (new.data->>'projectId')::uuid;
  if not found then raise exception 'project not found'; end if;
  new.project_id := p.id;
  new.course_id := p.course_id;
  new.student_id := p.student_id;
  return new;
end $$;
create trigger ivs_feedback_derive before insert or update on public.ivs_feedback
  for each row execute function public.ivs_feedback_derive();

alter table public.ivs_feedback enable row level security;

-- 담당 선생님: 읽기/쓰기/삭제 (수업은 승인된 선생님만 가질 수 있음)
create policy feedback_teacher on public.ivs_feedback for all to authenticated
  using (exists (select 1 from public.ivs_courses c where c.id = ivs_feedback.course_id and c.teacher_id = auth.uid()))
  with check (exists (select 1 from public.ivs_courses c where c.id = ivs_feedback.course_id and c.teacher_id = auth.uid()));

-- 학생: 자기 과제에 달린 평가만 읽기
create policy feedback_student_read on public.ivs_feedback for select to authenticated
  using (exists (select 1 from public.ivs_students s where s.id = ivs_feedback.student_id and s.user_id = auth.uid()));

grant all on public.ivs_feedback to service_role;
revoke all on public.ivs_feedback from anon;
grant select on public.ivs_feedback to authenticated;
grant insert (data), update (data), delete on public.ivs_feedback to authenticated;

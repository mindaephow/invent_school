-- 발명학교 새 Supabase 프로젝트 초기 설정 (SQL 에디터에서 한 번 실행)
-- 전제: 프로젝트 생성 시 "Automatically expose new tables" 해제, "Enable automatic RLS" 체크.
-- 로그인 계정 2종: 선생님(이메일+비밀번호) / 학생(선생님이 발급한 아이디+숫자 6자리, 서버 API가 생성)
-- 저장 형식: 예전과 같은 (id, data jsonb) 문서 저장소 + 권한 판단용 실제 컬럼(트리거가 data에서 채움)

-- ============ 0. 관리용 SQL 실행 함수 (MCP용) — service_role만 호출 가능 ============
create or replace function public.run_sql_query(sql text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare result jsonb;
begin
  execute format('select coalesce(jsonb_agg(t), ''[]''::jsonb) from (%s) t', sql) into result;
  return result;
end;
$$;
revoke all on function public.run_sql_query(text) from public, anon, authenticated;
grant execute on function public.run_sql_query(text) to service_role;

-- ============ 1. 테이블 ============
create table public.ivs_teachers (
  id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.ivs_courses (
  id uuid primary key default gen_random_uuid(),
  teacher_id uuid not null default auth.uid() references public.ivs_teachers(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index on public.ivs_courses (teacher_id);

create table public.ivs_students (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references public.ivs_courses(id) on delete cascade,
  user_id uuid unique references auth.users(id) on delete set null,
  login_id text unique,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index on public.ivs_students (course_id);

create table public.ivs_records (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references public.ivs_courses(id) on delete cascade,
  student_id uuid not null references public.ivs_students(id) on delete cascade,
  date date not null,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (student_id, date)
);
create index on public.ivs_records (course_id, date);

create table public.ivs_curriculum (
  id uuid primary key default gen_random_uuid(),
  teacher_id uuid not null default auth.uid() references public.ivs_teachers(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index on public.ivs_curriculum (teacher_id);

create table public.ivs_projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  student_id uuid not null references public.ivs_students(id) on delete cascade,
  course_id uuid not null references public.ivs_courses(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index on public.ivs_projects (user_id);
create index on public.ivs_projects (course_id);

-- ============ 2. 트리거: 권한 판단용 컬럼을 data에서 채움 ============
create function public.ivs_students_derive() returns trigger language plpgsql as $$
begin
  new.course_id := (new.data->>'courseId')::uuid;
  return new;
end $$;
create trigger ivs_students_derive before insert or update on public.ivs_students
  for each row execute function public.ivs_students_derive();

create function public.ivs_records_derive() returns trigger language plpgsql as $$
begin
  new.course_id := (new.data->>'courseId')::uuid;
  new.student_id := (new.data->>'studentId')::uuid;
  new.date := (new.data->>'date')::date;
  return new;
end $$;
create trigger ivs_records_derive before insert or update on public.ivs_records
  for each row execute function public.ivs_records_derive();

-- 프로젝트 소유자는 data가 아니라 로그인한 학생 본인으로 고정 (조작 방지)
create function public.ivs_projects_owner() returns trigger
language plpgsql security definer set search_path = public as $$
declare s public.ivs_students;
begin
  select * into s from public.ivs_students where user_id = auth.uid();
  if not found then raise exception 'student account required'; end if;
  new.user_id := auth.uid();
  new.student_id := s.id;
  new.course_id := s.course_id;
  return new;
end $$;
create trigger ivs_projects_owner before insert on public.ivs_projects
  for each row execute function public.ivs_projects_owner();

-- ============ 3. RLS ============
alter table public.ivs_teachers enable row level security;
alter table public.ivs_courses enable row level security;
alter table public.ivs_students enable row level security;
alter table public.ivs_records enable row level security;
alter table public.ivs_curriculum enable row level security;
alter table public.ivs_projects enable row level security;

-- 선생님: 본인 행만. 학생 계정(app_metadata.role = 'student', 서버만 설정 가능)은 선생님으로 등록할 수 없음
create policy teachers_select on public.ivs_teachers for select to authenticated
  using (id = auth.uid());
create policy teachers_update on public.ivs_teachers for update to authenticated
  using (id = auth.uid()) with check (id = auth.uid());
create policy teachers_insert on public.ivs_teachers for insert to authenticated
  with check (id = auth.uid() and coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') <> 'student');

-- 수업: 담당 선생님만
create policy courses_own on public.ivs_courses for all to authenticated
  using (teacher_id = auth.uid()) with check (teacher_id = auth.uid());

-- 학생: 담당 선생님은 전체, 학생 본인은 자기 행 조회만
create policy students_teacher on public.ivs_students for all to authenticated
  using (exists (select 1 from public.ivs_courses c where c.id = ivs_students.course_id and c.teacher_id = auth.uid()))
  with check (exists (select 1 from public.ivs_courses c where c.id = ivs_students.course_id and c.teacher_id = auth.uid()));
create policy students_self_read on public.ivs_students for select to authenticated
  using (user_id = auth.uid());

-- 출석·과제 기록: 담당 선생님만 (학생의 제출은 아래 submit_assignment 함수로만)
create policy records_teacher on public.ivs_records for all to authenticated
  using (exists (select 1 from public.ivs_courses c where c.id = ivs_records.course_id and c.teacher_id = auth.uid()))
  with check (
    exists (select 1 from public.ivs_courses c where c.id = ivs_records.course_id and c.teacher_id = auth.uid())
    and exists (select 1 from public.ivs_students s where s.id = ivs_records.student_id and s.course_id = ivs_records.course_id)
  );

-- 커리큘럼: 담당 선생님만
create policy curriculum_own on public.ivs_curriculum for all to authenticated
  using (teacher_id = auth.uid()) with check (teacher_id = auth.uid());

-- 프로젝트: 학생 본인은 전체, 담당 선생님은 조회만
create policy projects_student on public.ivs_projects for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy projects_teacher_read on public.ivs_projects for select to authenticated
  using (exists (select 1 from public.ivs_courses c where c.id = ivs_projects.course_id and c.teacher_id = auth.uid()));

-- ============ 4. 권한 (anon에는 아무것도 열지 않음. 컬럼 단위로 data만 쓰기 허용) ============
revoke all on public.ivs_teachers, public.ivs_courses, public.ivs_students,
  public.ivs_records, public.ivs_curriculum, public.ivs_projects from anon;

grant select on public.ivs_teachers, public.ivs_courses, public.ivs_students,
  public.ivs_records, public.ivs_curriculum, public.ivs_projects to authenticated;
grant insert (data), update (data) on public.ivs_teachers to authenticated;
grant insert (data), update (data), delete on public.ivs_courses to authenticated;
grant insert (data), update (data), delete on public.ivs_students to authenticated;
grant insert (data), update (data), delete on public.ivs_records to authenticated;
grant insert (data), update (data), delete on public.ivs_curriculum to authenticated;
grant insert (data), update (data), delete on public.ivs_projects to authenticated;

-- ============ 5. 학생 과제 제출 (출석부의 과제 칸에 반영) ============
create function public.submit_assignment(p_project uuid) returns void
language plpgsql security definer set search_path = public as $$
declare
  p public.ivs_projects;
  d date := (now() at time zone 'Asia/Seoul')::date;
  ms bigint := (extract(epoch from now()) * 1000)::bigint;
begin
  select * into p from public.ivs_projects where id = p_project and user_id = auth.uid();
  if not found then raise exception 'not your project'; end if;

  update public.ivs_projects
    set data = data || jsonb_build_object('submitted', true, 'submittedAt', ms)
    where id = p.id;

  insert into public.ivs_records (course_id, student_id, date, data)
  values (p.course_id, p.student_id, d, jsonb_build_object(
    'courseId', p.course_id, 'studentId', p.student_id, 'date', d,
    'assignment', 'submitted', 'projectId', p.id, 'updatedAt', ms))
  on conflict (student_id, date) do update
    set data = public.ivs_records.data || jsonb_build_object('assignment', 'submitted', 'projectId', p.id, 'updatedAt', ms);
end $$;
revoke all on function public.submit_assignment(uuid) from public, anon;
grant execute on function public.submit_assignment(uuid) to authenticated;

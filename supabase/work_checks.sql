-- 작품 검사 요청: 학생이 만든 작품의 사진·영상을 올리면 선생님이 "통과" 또는 답변을 남긴다.
-- 파일은 Storage 버킷 student-works 에(학생은 자기 폴더에만 올림), DB 에는 주소와 선생님 답변만 저장한다.
-- 공개 읽기 버킷이지만 파일 이름이 추측 불가능한 무작위 값이라 주소를 아는 사람만 열 수 있다.
-- Supabase SQL 에디터에서 한 번 실행하면 된다(여러 번 실행해도 안전).

create table if not exists public.ivs_work_checks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  student_id uuid not null references public.ivs_students(id) on delete cascade,
  course_id uuid not null references public.ivs_courses(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists ivs_work_checks_user_idx on public.ivs_work_checks (user_id);
create index if not exists ivs_work_checks_course_idx on public.ivs_work_checks (course_id);

-- 소유자는 data 가 아니라 로그인한 학생 본인으로 고정(조작 방지) — ivs_projects 와 같은 방식
create or replace function public.ivs_work_checks_owner() returns trigger
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
drop trigger if exists ivs_work_checks_owner on public.ivs_work_checks;
create trigger ivs_work_checks_owner before insert on public.ivs_work_checks
  for each row execute function public.ivs_work_checks_owner();

alter table public.ivs_work_checks enable row level security;

drop policy if exists work_checks_student on public.ivs_work_checks;
create policy work_checks_student on public.ivs_work_checks for select to authenticated using (user_id = auth.uid());
drop policy if exists work_checks_student_insert on public.ivs_work_checks;
create policy work_checks_student_insert on public.ivs_work_checks for insert to authenticated with check (user_id = auth.uid());
drop policy if exists work_checks_teacher_read on public.ivs_work_checks;
create policy work_checks_teacher_read on public.ivs_work_checks for select to authenticated
  using (exists (select 1 from public.ivs_courses c where c.id = ivs_work_checks.course_id and c.teacher_id = auth.uid()));
drop policy if exists work_checks_teacher_update on public.ivs_work_checks;
create policy work_checks_teacher_update on public.ivs_work_checks for update to authenticated
  using (exists (select 1 from public.ivs_courses c where c.id = ivs_work_checks.course_id and c.teacher_id = auth.uid()))
  with check (exists (select 1 from public.ivs_courses c where c.id = ivs_work_checks.course_id and c.teacher_id = auth.uid()));
drop policy if exists work_checks_teacher_delete on public.ivs_work_checks;
create policy work_checks_teacher_delete on public.ivs_work_checks for delete to authenticated
  using (exists (select 1 from public.ivs_courses c where c.id = ivs_work_checks.course_id and c.teacher_id = auth.uid()));

grant select, insert (data), update (data), delete on public.ivs_work_checks to authenticated;
grant all on public.ivs_work_checks to service_role;
revoke all on public.ivs_work_checks from anon;

-- 사진·영상 저장 버킷. 로그인한 사용자는 자기 id 폴더(student-works/<내 id>/...)에만 올릴 수 있다.
insert into storage.buckets (id, name, public) values ('student-works', 'student-works', true) on conflict (id) do nothing;
drop policy if exists "student-works read" on storage.objects;
create policy "student-works read" on storage.objects for select to public using (bucket_id = 'student-works');
drop policy if exists "student-works insert" on storage.objects;
create policy "student-works insert" on storage.objects for insert to authenticated
  with check (bucket_id = 'student-works' and (storage.foldername(name))[1] = auth.uid()::text);

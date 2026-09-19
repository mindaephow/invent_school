-- 선생님 승인제: 가입한 선생님은 본사(관리자)가 승인해야 수업·학생 등록 등을 쓸 수 있음 (SQL 에디터에서 한 번 실행)

-- 1) 승인 여부 컬럼. 선생님 본인은 이 컬럼을 쓸 수 없음(권한이 data 컬럼에만 열려 있음).
alter table public.ivs_teachers add column if not exists approved boolean not null default false;

-- 2) 지금까지 가입해 쓰던 선생님(테스트 계정 포함)은 승인된 것으로 처리
update public.ivs_teachers set approved = true;

-- 3) 승인된 선생님만 수업·커리큘럼을 만들고 볼 수 있음
--    (학생·출석 기록은 "내 수업"에 딸려 있어서 함께 막힘)
drop policy if exists courses_own on public.ivs_courses;
create policy courses_own on public.ivs_courses for all to authenticated
  using (teacher_id = auth.uid() and exists (select 1 from public.ivs_teachers t where t.id = auth.uid() and t.approved))
  with check (teacher_id = auth.uid() and exists (select 1 from public.ivs_teachers t where t.id = auth.uid() and t.approved));

drop policy if exists curriculum_own on public.ivs_curriculum;
create policy curriculum_own on public.ivs_curriculum for all to authenticated
  using (teacher_id = auth.uid() and exists (select 1 from public.ivs_teachers t where t.id = auth.uid() and t.approved))
  with check (teacher_id = auth.uid() and exists (select 1 from public.ivs_teachers t where t.id = auth.uid() and t.approved));

-- 본사 관리자 지정은 별도 (관리자 계정을 먼저 선생님 등록 화면에서 가입한 뒤 실행):
--   update auth.users set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb) || '{"role":"admin"}'::jsonb where email = '관리자@이메일';
--   update public.ivs_teachers set approved = true where id = (select id from auth.users where email = '관리자@이메일');

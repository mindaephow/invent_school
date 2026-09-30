-- 교재관리(ivs_textbooks): 부품 카탈로그와 같은 방식으로 모든 선생님이 공유하는 회사 공통 자료.
-- 과목(로봇은 카테고리·권까지) 단위로 교재를 등록하고, 그 안에 차시 제목·필요 부품·첨부파일을 관리한다.
create table if not exists public.ivs_textbooks (
  id uuid primary key default gen_random_uuid(),
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.ivs_textbooks enable row level security;

drop policy if exists "ivs_textbooks select" on public.ivs_textbooks;
create policy "ivs_textbooks select" on public.ivs_textbooks
  for select to authenticated using (true);

grant select on public.ivs_textbooks to authenticated;
grant all on public.ivs_textbooks to service_role;

-- 차시·교재 첨부파일(PDF/엑셀 등) 저장용 Storage 버킷. 공개 읽기(다운로드 링크 그대로 열람)로 만들고,
-- 업로드는 로그인한 사용자만 가능하게 한다(관리자 API가 아니라 브라우저에서 Supabase Storage로 직접
-- 올리므로 storage.objects에 별도 RLS가 필요).
insert into storage.buckets (id, name, public)
values ('textbook-files', 'textbook-files', true)
on conflict (id) do nothing;

drop policy if exists "textbook-files read" on storage.objects;
create policy "textbook-files read" on storage.objects
  for select to public using (bucket_id = 'textbook-files');

drop policy if exists "textbook-files insert" on storage.objects;
create policy "textbook-files insert" on storage.objects
  for insert to authenticated with check (bucket_id = 'textbook-files');

drop policy if exists "textbook-files update" on storage.objects;
create policy "textbook-files update" on storage.objects
  for update to authenticated using (bucket_id = 'textbook-files');

drop policy if exists "textbook-files delete" on storage.objects;
create policy "textbook-files delete" on storage.objects
  for delete to authenticated using (bucket_id = 'textbook-files');

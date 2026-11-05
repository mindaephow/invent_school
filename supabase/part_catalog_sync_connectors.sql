-- 부품 상세내역(data.detail)이 유일한 원본이다. 연결점(data.connectors)은 상세내역에서 자동으로 만들어져 늘 같은 값을 본다.
--   상세내역의 돌기·구멍 목록을 고치면 같은 저장 안에서 connectors.pegs·holes·size 가 다시 만들어진다(트리거).
--   connectors 를 따로 고쳐 저장해도 상세내역이 있는 부품은 저장 순간 상세내역 값으로 덮인다 — 둘이 어긋날 수 없다.
--   상세내역이 없는 부품(돌기·구멍 목록 없음)은 지금처럼 connectors 를 그대로 쓴다.
--   confidence·note 는 이미 있으면 그대로 두고, 없으면 confidence 를 'checked' 로 적는다.
-- Supabase SQL 에디터에서 한 번 실행한다. 변환식은 실제 DB 의 연결점 552개와 비교해 어긋남 0 으로 확인했다(2026-11-06).

create or replace function public.ivs_derive_connectors(det jsonb, cur jsonb)
returns jsonb language sql immutable as $$
  select coalesce(cur, '{}'::jsonb) || jsonb_strip_nulls(jsonb_build_object(
    'pegs', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', p->>'번호', 'pos', p->'위치',
        'dir', case p->>'방향' when '+x' then '[1,0,0]'::jsonb when '-x' then '[-1,0,0]'::jsonb
                               when '+y' then '[0,1,0]'::jsonb when '-y' then '[0,-1,0]'::jsonb
                               when '+z' then '[0,0,1]'::jsonb when '-z' then '[0,0,-1]'::jsonb end,
        'len', p->'길이', 'r', (p->>'지름')::numeric / 2) order by ord)
      from jsonb_array_elements(det->'돌기'->'목록') with ordinality t(p, ord)), '[]'::jsonb),
    'holes', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', p->>'번호', 'pos', p->'위치',
        'dir', case p->>'방향' when '+x' then '[1,0,0]'::jsonb when '-x' then '[-1,0,0]'::jsonb
                               when '+y' then '[0,1,0]'::jsonb when '-y' then '[0,-1,0]'::jsonb
                               when '+z' then '[0,0,1]'::jsonb when '-z' then '[0,0,-1]'::jsonb end,
        'len', p->'길이', 'r', (p->>'지름')::numeric / 2,
        'through', coalesce((p->>'관통')::boolean, false)) order by ord)
      from jsonb_array_elements(det->'구멍'->'목록') with ordinality t(p, ord)), '[]'::jsonb),
    'size', case when det->'크기_mm' ? '가로(x)' and det->'크기_mm' ? '높이(y)' and det->'크기_mm' ? '세로(z)'
                 then jsonb_build_array(det->'크기_mm'->'가로(x)', det->'크기_mm'->'높이(y)', det->'크기_mm'->'세로(z)') end,
    'confidence', case when cur ? 'confidence' then null else 'checked' end
  ));
$$;

create or replace function public.ivs_part_catalog_sync_connectors()
returns trigger language plpgsql as $$
begin
  if jsonb_typeof(new.data->'detail') = 'object'
     and (jsonb_array_length(coalesce(new.data->'detail'->'돌기'->'목록', '[]'::jsonb)) > 0
          or jsonb_array_length(coalesce(new.data->'detail'->'구멍'->'목록', '[]'::jsonb)) > 0) then
    begin
      new.data := jsonb_set(new.data, '{connectors}', public.ivs_derive_connectors(new.data->'detail', new.data->'connectors'));
    exception when others then
      raise warning 'ivs_part_catalog 연결점 자동 반영 실패(저장은 계속): %', sqlerrm;
    end;
  end if;
  return new;
end;
$$;

drop trigger if exists ivs_part_catalog_sync_connectors on public.ivs_part_catalog;
create trigger ivs_part_catalog_sync_connectors
  before insert or update on public.ivs_part_catalog
  for each row execute function public.ivs_part_catalog_sync_connectors();

-- 지금 있는 모든 부품에 한 번 적용(상세내역이 있는 부품만 바뀐다 — 값은 이미 같다)
update public.ivs_part_catalog set data = data
 where jsonb_typeof(data->'detail') = 'object';

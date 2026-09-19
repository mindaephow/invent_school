// app/api/mcp/route.js
//
// 발명학교(invent_school) MCP 서버 — teacher-dashboard(public/index.html)와
// 3D 설계 도구(public/design.html)가 쓰는 Supabase 테이블(ivs_teachers/courses/
// students/records/curriculum)을 향후 세션에서 직접 조회·수정할 수 있게 하는
// 범용 CRUD 도구 + GitHub 저장소 확인 도구. 다른 사이트들의 MCP 서버(예:
// minsiljang0/Fresh_Season의 app/api/mcp/route.js)와 동일하게, 메인 사이트와
// 같은 Next.js 프로젝트·같은 Vercel 배포 안에 들어있다 (static HTML은
// public/에 두고, Next.js가 라우팅 없이 그대로 서빙).
//
// 노출 툴 7개:
//   - list_tables       : Supabase DB 테이블 목록 조회
//   - get_rows          : 임의 테이블 행 조회 (필터·검색·정렬·페이징)
//   - upsert_row        : 임의 테이블 행 추가·수정
//   - delete_row        : 임의 테이블 행 삭제 (되돌릴 수 없음)
//   - run_sql           : SQL 직접 실행 (위험 DDL 자동 차단, run_sql_query RPC 필요)
//   - list_github_files : GitHub 저장소(mindaephow/invent_school) 경로별 파일 목록 조회
//   - get_github_file   : GitHub 저장소 특정 파일 내용 조회
//
// 필요한 환경변수 (Vercel 프로젝트 설정 > Environment Variables, 메인 사이트와 같은 프로젝트):
//   SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY  - public/index.html·public/design.html이 쓰는 것과 같은 프로젝트,
//                                                단 여기는 서버 전용 SERVICE_ROLE 키(절대 브라우저에 노출 금지)
//   MCP_SHARED_SECRET                          - claude.ai 커넥터 등록 시 ?key= 값으로 사용
//   GITHUB_TOKEN (선택)                        - GitHub API 호출 제한(시간당 60회)을 늘려줌, 없어도 동작함
//
// list_tables/run_sql 완전 동작을 위한 Postgres RPC (선택, 없으면 일부 기능만 제한):
// ⚠️ 임의 SQL을 실행할 수 있는 함수라 위험도가 높다 — 필요할 때만 생성할 것.
//
// create or replace function run_sql_query(sql text)
// returns jsonb
// language plpgsql
// security definer
// as $$
// declare
//   result jsonb;
// begin
//   execute format('select coalesce(jsonb_agg(t), ''[]''::jsonb) from (%s) t', sql) into result;
//   return result;
// end;
// $$;
//
// claude.ai 커넥터 등록 주소:
//   https://invent-school.vercel.app/api/mcp?key=여기에_MCP_SHARED_SECRET_값

import { createMcpHandler } from 'mcp-handler'
import { createClient } from '@supabase/supabase-js'
import { z } from 'zod'

// Lazily created on first use (not at module load) so `next build` doesn't
// crash when env vars aren't present at build time — only at request time.
let _supabase = null
function getSupabase() {
  if (!_supabase) {
    _supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY)
  }
  return _supabase
}

const GITHUB_REPO = 'mindaephow/invent_school'

const baseHandler = createMcpHandler(
  (server) => {

    server.registerTool(
      'list_github_files',
      {
        title: 'GitHub 저장소 파일 목록 조회',
        description: `${GITHUB_REPO} 저장소의 특정 경로에 어떤 파일·폴더가 있는지 조회한다. path를 비우면 저장소 루트를 본다.`,
        inputSchema: {
          path: z.string().optional().describe('조회할 경로. 예: "mcp/app/api/mcp". 비우면 루트'),
          ref: z.string().optional().describe('브랜치/커밋. 기본: main'),
        },
      },
      async ({ path = '', ref = 'main' }) => {
        const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${path}?ref=${encodeURIComponent(ref)}`
        const headers = { Accept: 'application/vnd.github+json', 'User-Agent': 'invent-school-mcp' }
        if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`
        const res = await fetch(url, { headers })
        if (!res.ok) {
          const text = await res.text().catch(() => '')
          return { content: [{ type: 'text', text: `❌ GitHub API 오류 (${res.status}): ${text}` }], isError: true }
        }
        const data = await res.json()
        const list = Array.isArray(data) ? data : [data]
        const lines = list.map(f => `${f.type === 'dir' ? '📁' : '📄'} ${f.path}${f.type === 'file' ? ` (${f.size} bytes)` : ''}`)
        return { content: [{ type: 'text', text: lines.join('\n') }] }
      }
    )

    server.registerTool(
      'get_github_file',
      {
        title: 'GitHub 저장소 파일 내용 조회',
        description: `${GITHUB_REPO} 저장소의 특정 파일 내용을 텍스트로 가져온다. list_github_files로 경로 확인 후 사용.`,
        inputSchema: {
          path: z.string().describe('파일 경로. 예: "index.html"'),
          ref: z.string().optional().describe('브랜치/커밋. 기본: main'),
        },
      },
      async ({ path, ref = 'main' }) => {
        const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${path}?ref=${encodeURIComponent(ref)}`
        const headers = { Accept: 'application/vnd.github+json', 'User-Agent': 'invent-school-mcp' }
        if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`
        const res = await fetch(url, { headers })
        if (!res.ok) {
          const text = await res.text().catch(() => '')
          return { content: [{ type: 'text', text: `❌ GitHub API 오류 (${res.status}): ${text}` }], isError: true }
        }
        const data = await res.json()
        if (data.type !== 'file') return { content: [{ type: 'text', text: `❌ "${path}"는 파일이 아니라 ${data.type}입니다` }], isError: true }
        const content = Buffer.from(data.content, data.encoding || 'base64').toString('utf-8')
        return { content: [{ type: 'text', text: `[${path}] (${data.size} bytes)\n\n${content}` }] }
      }
    )

    server.registerTool(
      'list_tables',
      {
        title: 'DB 테이블 목록 조회',
        description: 'list_tables — DB 테이블 목록 조회. Supabase DB에 있는 테이블 목록을 반환한다.',
        inputSchema: {
          schema: z.string().optional().describe('스키마 이름. 기본값: public'),
        },
      },
      async ({ schema = 'public' }) => {
        const { data: d2, error: e2 } = await getSupabase()
          .from('information_schema.tables')
          .select('table_name')
          .eq('table_schema', schema)
          .eq('table_type', 'BASE TABLE')
          .order('table_name')
        if (e2) {
          const { data: d3, error: e3 } = await getSupabase().rpc('run_sql_query', {
            sql: `SELECT table_name FROM information_schema.tables WHERE table_schema = '${schema}' AND table_type = 'BASE TABLE' ORDER BY table_name`
          })
          if (e3) return { content: [{ type: 'text', text: `❌ ${e3.message}` }], isError: true }
          return { content: [{ type: 'text', text: JSON.stringify(d3, null, 2) }] }
        }
        const names = (d2 || []).map(r => r.table_name).join('\n')
        return { content: [{ type: 'text', text: `테이블 목록 (${schema} 스키마):\n${names}` }] }
      }
    )

    server.registerTool(
      'get_rows',
      {
        title: 'DB 테이블 데이터 조회',
        description: 'get_rows — DB 테이블 데이터 조회. ivs_teachers/ivs_courses/ivs_students/ivs_records/ivs_curriculum/ivs_projects는 (id, data jsonb, created_at)에 소유자 컬럼(teacher_id, course_id, student_id, user_id 등)이 붙은 구조라 내용은 data에 있다. ivs_students에는 login_id(학생 로그인 아이디)도 있다. 필터·정렬·페이징 지원, 최대 500행.',
        inputSchema: {
          table:   z.string().describe('테이블 이름. 예: ivs_teachers, ivs_courses, ivs_students, ivs_records, ivs_curriculum'),
          select:  z.string().optional().describe('가져올 컬럼 (쉼표 구분). 비우면 전체(*)'),
          filter:  z.record(z.string()).optional().describe('eq 필터. 예: {"id":"..."}. jsonb 필드로 거르려면 run_sql을 쓸 것'),
          order_by: z.string().optional().describe('정렬 기준 컬럼. 기본: created_at'),
          ascending: z.boolean().optional().describe('오름차순 여부. 기본: false (최신순)'),
          limit:   z.number().int().min(1).max(500).optional().describe('가져올 행 수. 기본: 50, 최대: 500'),
          offset:  z.number().int().min(0).optional().describe('건너뛸 행 수 (페이징). 기본: 0'),
        },
      },
      async ({ table, select = '*', filter, order_by = 'created_at', ascending = false, limit = 50, offset = 0 }) => {
        let q = getSupabase().from(table).select(select)
        if (filter) {
          for (const [col, val] of Object.entries(filter)) q = q.eq(col, val)
        }
        q = q.order(order_by, { ascending }).range(offset, offset + limit - 1)
        const { data, error } = await q
        if (error) return { content: [{ type: 'text', text: `❌ ${error.message}` }], isError: true }
        if (!data?.length) return { content: [{ type: 'text', text: `(결과 없음) 테이블: ${table}` }] }
        return { content: [{ type: 'text', text: `[${table}] ${data.length}행 반환 (offset:${offset})\n${JSON.stringify(data, null, 2)}` }] }
      }
    )

    server.registerTool(
      'upsert_row',
      {
        title: 'DB 행 추가·수정',
        description: 'upsert_row — DB 행 추가·수정. id를 포함하면 수정, 없으면 새 행 추가. ivs_* 테이블은 실제 값을 data(jsonb) 필드에 담는다 — 예: {"id":"...", "data":{"name":"홍길동","phone":"010-..."}}. 소유자 컬럼은 트리거가 data에서 채우거나(courseId 등) 로그인 계정 기준이라 서비스 키로 직접 넣을 땐 함께 지정해야 할 수 있다. 수정 전 get_rows로 기존 data를 먼저 확인할 것.',
        inputSchema: {
          table: z.string().describe('테이블 이름'),
          row:   z.record(z.any()).describe('추가·수정할 데이터 객체. ivs_* 테이블이면 {"id":"...", "data":{...}} 형태'),
        },
        annotations: { destructiveHint: true },
      },
      async ({ table, row }) => {
        const { data, error } = await getSupabase()
          .from(table)
          .upsert([row], { onConflict: 'id' })
          .select()
          .single()
        if (error) return { content: [{ type: 'text', text: `❌ ${error.message}` }], isError: true }
        return { content: [{ type: 'text', text: `✅ [${table}] upsert 완료\n${JSON.stringify(data, null, 2)}` }] }
      }
    )

    server.registerTool(
      'delete_row',
      {
        title: 'DB 행 삭제',
        description: 'delete_row — DB 행 삭제. 테이블에서 특정 id의 행을 삭제한다. 삭제 전 존재 자동 확인, 되돌릴 수 없음.',
        inputSchema: {
          table: z.string().describe('테이블 이름'),
          id:    z.string().describe('삭제할 행의 id'),
        },
        annotations: { destructiveHint: true },
      },
      async ({ table, id }) => {
        const { data: existing } = await getSupabase().from(table).select('id').eq('id', id).maybeSingle()
        if (!existing) return { content: [{ type: 'text', text: `❌ [${table}] id="${id}" 행을 찾을 수 없음` }], isError: true }
        const { error } = await getSupabase().from(table).delete().eq('id', id)
        if (error) return { content: [{ type: 'text', text: `❌ ${error.message}` }], isError: true }
        return { content: [{ type: 'text', text: `✅ [${table}] id="${id}" 삭제 완료` }] }
      }
    )

    server.registerTool(
      'run_sql',
      {
        title: 'SQL 직접 실행',
        description: 'run_sql — SQL 직접 실행. jsonb 필드(data)로 필터링하는 등 get_rows로 안 되는 조회에 사용. 예: SELECT id, data->>\'name\' AS name FROM ivs_students WHERE data->>\'courseId\' = \'...\'. DROP·TRUNCATE·ALTER 등 위험 DDL은 자동 차단. run_sql_query RPC 함수가 DB에 있어야 동작한다.',
        inputSchema: {
          sql: z.string().describe('실행할 SQL 쿼리'),
        },
        annotations: { destructiveHint: true },
      },
      async ({ sql }) => {
        const upper = sql.trim().toUpperCase()
        const dangerous = ['DROP ', 'TRUNCATE ', 'ALTER TABLE', 'CREATE TABLE', 'GRANT ', 'REVOKE ']
        if (dangerous.some(kw => upper.startsWith(kw) || upper.includes('\n' + kw))) {
          return { content: [{ type: 'text', text: `⛔ 위험한 DDL/권한 쿼리는 차단됩니다: ${sql.slice(0, 80)}` }], isError: true }
        }
        const { data, error } = await getSupabase().rpc('run_sql_query', { sql })
        if (error) return { content: [{ type: 'text', text: `❌ ${error.message}\n\nSQL: ${sql}` }], isError: true }
        return { content: [{ type: 'text', text: `✅ SQL 실행 완료\n${JSON.stringify(data, null, 2)}` }] }
      }
    )

  },
  {
    instructions:
      '발명학교(골드버그 출석부 + 3D 설계 도구) MCP 서버. ' +
      'Supabase DB 직접 조회·수정 도구(list_tables/get_rows/upsert_row/delete_row/run_sql — ' +
      'ivs_teachers/courses/students/records/curriculum/projects 테이블, 내용은 data jsonb에 있고 권한용 소유자 컬럼이 붙어 있음), ' +
      'GitHub 저장소(' + GITHUB_REPO + ') 파일 확인 도구(list_github_files/get_github_file)를 제공한다. ' +
      '선생님/수업/학생/출석기록/커리큘럼 데이터를 조회·수정하거나 index.html·design.html 코드를 확인할 때 이 서버의 도구를 사용한다.',
  },
  { basePath: '/api', maxDuration: 30, verboseLogs: true }
)

// ── 공유 비밀키 보호 (다른 사이트들과 동일한 방식) ─────────────────────
async function authedHandler(request) {
  const url = new URL(request.url)
  const key = url.searchParams.get('key')
  if (!process.env.MCP_SHARED_SECRET || key !== process.env.MCP_SHARED_SECRET) {
    return new Response(JSON.stringify({ error: '인증 필요 (key 파라미터 확인)' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    })
  }
  return baseHandler(request)
}

export { authedHandler as GET, authedHandler as POST }

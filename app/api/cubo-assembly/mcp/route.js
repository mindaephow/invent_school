// app/api/cubo-assembly/mcp/route.js
//
// 큐보 조립 MCP 서버 — 설계 화면의 "조립 보기"(교재 단계별 3D 조립도)를 기억 없는 클로드도 이어서 만들 수 있게,
// 조립 규칙·좌표계·부품 측정 사실·작업 절차(조립 안내서)와 조립 단계 데이터, 겹침 검사, 부품 돌기·구멍 연결점 기록을 제공한다.
// 메인 사이트와 같은 Next.js 프로젝트·같은 Vercel 배포 안에 들어 있다(다른 MCP와 같은 방식, 공유 비밀키 ?key= 보호).
//
// 노출 툴 6개:
//   - get_assembly_guide   : 조립 안내서(규칙·좌표계·부품 사실·교재 구조·작업 절차) — 가장 먼저 읽을 것
//   - list_assemblies      : 조립 데이터가 있는 교재 차시 목록
//   - get_assembly         : 한 차시의 조립 단계 데이터(부품 위치·회전·끼우는 방향·구멍 자리)
//   - validate_assembly    : 조립 데이터의 부품 몸통 겹침 검사(돌기·리벳·축이 구멍에 들어가는 것만 예외)
//   - get_part_connectors  : 부품의 돌기·구멍 연결점(ivs_part_catalog.data.connectors) 조회
//   - set_part_connectors  : 부품의 돌기·구멍 연결점 기록
//
// 조립 규칙과 단계 데이터, 겹침 검사 코드는 배포된 public/design-assemblies.js·design-collision.js 를 읽어 온다 —
// 화면과 같은 파일이 원본이라 둘이 어긋나지 않는다.
//
// 환경변수: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY / MCP_SHARED_SECRET, (선택) SITE_ORIGIN(기본 https://invent-school-sigma.vercel.app)
// claude.ai 커넥터 등록 주소:
//   https://<사이트 주소>/api/cubo-assembly/mcp?key=MCP_SHARED_SECRET_값

import { createMcpHandler } from 'mcp-handler'
import { createClient } from '@supabase/supabase-js'
import { z } from 'zod'
import { buildGuide, dimsOf } from '../../../lib/cubo-assembly-guide.js'

let _supabase = null
function getSupabase() {
  if (!_supabase) _supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY)
  return _supabase
}
const text = (t) => ({ content: [{ type: 'text', text: t }] })
const fail = (t) => ({ content: [{ type: 'text', text: `❌ ${t}` }], isError: true })
const SITE_ORIGIN = () => (process.env.SITE_ORIGIN || 'https://invent-school-sigma.vercel.app').replace(/\/$/, '')

// 배포된 화면용 자바스크립트(window.* 에 값을 넣는 파일)를 가짜 window 로 실행해서 값을 꺼낸다 — 1분 캐시.
let _site = null, _siteAt = 0
async function loadSite() {
  if (_site && Date.now() - _siteAt < 60_000) return _site
  const win = {}
  for (const file of ['design-assemblies.js', 'design-collision.js']) {
    const res = await fetch(`${SITE_ORIGIN()}/${file}?t=${Date.now()}`)
    if (!res.ok) throw new Error(`${file} 를 못 읽었어요 (${res.status})`)
    new Function('window', await res.text())(win) // 같은 저장소의 파일만 읽는다
  }
  _site = win
  _siteAt = Date.now()
  return win
}

// 오일러(도, ZYX: R = Rz·Ry·Rx) → 쿼터니언
function quatFromEulerZYX(r) {
  const h = (d) => (d * Math.PI) / 360
  const ax = (a, d) => { const s = Math.sin(h(d)), c = Math.cos(h(d)); return a === 'x' ? [s, 0, 0, c] : a === 'y' ? [0, s, 0, c] : [0, 0, s, c] }
  const mul = (a, b) => [a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1], a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0], a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3], a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]]
  const q = mul(ax('z', r[2]), mul(ax('y', r[1]), ax('x', r[0])))
  return { x: q[0], y: q[1], z: q[2], w: q[3] }
}

// 조립 데이터의 모든 부품을 "제자리" 배치로 모아 몸통 겹침을 검사한다
function checkOverlaps(steps, COL, tol) {
  const items = []
  const skipped = new Set()
  steps.forEach((s, si) => (s.parts || []).forEach((pt) => {
    const dims = dimsOf(pt.n)
    const cores = dims ? COL.coreBoxes(pt.n, dims) : null
    if (!cores) { skipped.add(pt.n); return }
    items.push({ step: si + 1, name: pt.n, cores, pos: { x: pt.p[0], y: pt.p[1], z: pt.p[2] }, q: quatFromEulerZYX(pt.r || [0, 0, 0]) })
  }))
  const overlaps = []
  for (let a = 0; a < items.length; a++) for (let b = a + 1; b < items.length; b++) {
    if (COL.boxesOverlap(items[a].cores, items[a].pos, items[a].q, items[b].cores, items[b].pos, items[b].q, tol)) {
      overlaps.push(`${items[a].step}단계 ${items[a].name} × ${items[b].step}단계 ${items[b].name}`)
    }
  }
  return { checked: items.length, overlaps, skipped: [...skipped] }
}

const baseHandler = createMcpHandler(
  (server) => {
    server.registerTool(
      'get_assembly_guide',
      {
        title: '큐보 조립 안내서 읽기',
        description: '큐보 조립도(설계 화면 "조립 보기") 작업을 시작하기 전에 가장 먼저 읽을 것. 조립 규칙, 좌표계·단위, 3D 모델로 측정한 부품 사실(돌기 위치·방향), 교재 구조, 작업 절차, 데이터 형식, 코드 위치를 돌려준다.',
        inputSchema: {},
      },
      async () => {
        try { const site = await loadSite(); return text(buildGuide(site.IVS_ASSEMBLY_RULES)) }
        catch (e) { return text(buildGuide(null) + `\n\n(화면 파일을 못 읽어 규칙은 생략: ${e.message})`) }
      }
    )

    server.registerTool(
      'list_assemblies',
      {
        title: '조립 데이터 목록',
        description: '조립 단계 데이터가 있는 교재 차시 목록(id, 카테고리, 권, 차시, 단계 수, 부품 수).',
        inputSchema: {},
      },
      async () => {
        try {
          const site = await loadSite()
          const lines = (site.IVS_ASSEMBLIES || []).map((a) => `- ${a.id}: ${a.category} ${a.volume}권 · ${a.chapter} (${a.steps.length}단계, 부품 ${a.steps.reduce((n, s) => n + (s.parts || []).length, 0)}개) — ${a.book || ''}`)
          return text(lines.length ? lines.join('\n') : '(조립 데이터 없음)')
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'get_assembly',
      {
        title: '조립 단계 데이터 조회',
        description: '한 차시의 조립 단계 데이터(JSON)를 돌려준다: 단계별 부품 이름, 위치 p, 회전 r, 끼우는 방향 dir, 꽂히는 구멍 자리 marks, 옆자리 조립 side. 수정은 저장소의 public/design-assemblies.js 를 고쳐서 올린다.',
        inputSchema: { assemblyId: z.string().describe('list_assemblies 의 id. 예: cubo-1-rabbit') },
      },
      async ({ assemblyId }) => {
        try {
          const site = await loadSite()
          const a = (site.IVS_ASSEMBLIES || []).find((x) => x.id === assemblyId)
          if (!a) return fail(`id="${assemblyId}" 조립 데이터를 찾을 수 없어요. list_assemblies 로 확인하세요.`)
          return text(JSON.stringify(a, null, 1))
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'validate_assembly',
      {
        title: '조립 데이터 겹침 검사',
        description: '조립 데이터의 모든 부품(제자리 배치)을 몸통 상자로 근사해 서로 겹치는지 검사한다. 돌기·리벳·축이 구멍에 들어가는 것은 겹침으로 세지 않는다. 크기/몸통 규칙이 없는 부품은 검사하지 않고 목록으로 알려 준다. assemblyId(저장된 데이터) 또는 steps(직접 작성한 단계 배열) 중 하나를 준다.',
        inputSchema: {
          assemblyId: z.string().optional().describe('저장된 조립 데이터 id'),
          steps: z.array(z.any()).optional().describe('직접 만든 단계 배열. 각 단계 { parts: [{ n, p:[x,y,z], r:[rx,ry,rz] }] }'),
          tolerance: z.number().optional().describe('겹침 허용 깊이(mm). 기본 0.6'),
        },
      },
      async ({ assemblyId, steps, tolerance = 0.6 }) => {
        try {
          const site = await loadSite()
          let list = steps
          if (!list) {
            const a = (site.IVS_ASSEMBLIES || []).find((x) => x.id === assemblyId)
            if (!a) return fail('assemblyId 또는 steps 를 주세요 (list_assemblies 로 id 확인).')
            list = a.steps
          }
          const r = checkOverlaps(list, site.IVS_COLLISION, tolerance)
          const lines = [`검사한 부품 ${r.checked}개 / 겹침 ${r.overlaps.length}건`]
          if (r.overlaps.length) lines.push(...r.overlaps.map((o) => `⚠ ${o}`))
          else lines.push('✅ 겹침 없음(몸통 상자 기준)')
          if (r.skipped.length) lines.push(`검사 안 한 부품(크기·몸통 규칙 없음 또는 체결 부품): ${r.skipped.join(', ')}`)
          lines.push('※ 몸통 상자 근사이므로 돌기가 홀이 아닌 솔리드를 지나가는 것은 잡지 못한다. 화면(조립 보기)에서도 눈으로 확인할 것.')
          return text(lines.join('\n'))
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'get_part_connectors',
      {
        title: '부품 돌기·구멍 연결점 조회',
        description: '로봇 부품의 돌기(pegs)·구멍(holes) 연결점(ivs_part_catalog.data.connectors)을 조회한다. name 또는 partId 를 주면 그 부품의 연결점을, 생략하면 연결점이 기록된 부품/안 된 부품 목록을 돌려준다.',
        inputSchema: {
          name: z.string().optional().describe('부품 이름. 예: 눈블록'),
          partId: z.string().optional().describe('ivs_part_catalog 행 id'),
        },
      },
      async ({ name, partId }) => {
        const sb = getSupabase()
        if (!name && !partId) {
          const { data, error } = await sb.from('ivs_part_catalog').select('id, name:data->>name, subject:data->>subject, connectors:data->connectors').eq('data->>subject', 'robot').order('created_at')
          if (error) return fail(error.message)
          const has = data.filter((r) => r.connectors), no = data.filter((r) => !r.connectors)
          return text(`연결점 기록됨 ${has.length}개: ${has.map((r) => r.name).join(', ') || '-'}\n기록 안 됨 ${no.length}개: ${no.map((r) => r.name).join(', ') || '-'}`)
        }
        let q = sb.from('ivs_part_catalog').select('id, name:data->>name, connectors:data->connectors')
        q = partId ? q.eq('id', partId) : q.eq('data->>name', name).eq('data->>subject', 'robot')
        const { data, error } = await q
        if (error) return fail(error.message)
        if (!data.length) return fail('부품을 찾을 수 없어요.')
        return text(data.map((r) => `${r.name} (id=${r.id})\n${r.connectors ? JSON.stringify(r.connectors, null, 1) : '(연결점 기록 없음)'}`).join('\n\n'))
      }
    )

    server.registerTool(
      'set_part_connectors',
      {
        title: '부품 돌기·구멍 연결점 기록',
        description: '로봇 부품의 돌기(pegs)·구멍(holes) 연결점을 ivs_part_catalog.data.connectors 에 기록한다(다른 필드는 그대로). 좌표는 3D 모델 bbox 가운데를 원점으로 한 모델 로컬 좌표(y 위). 형식은 get_assembly_guide 7장 참고.',
        inputSchema: {
          partId: z.string().describe('ivs_part_catalog 행 id'),
          connectors: z.object({
            pegs: z.array(z.object({ id: z.string(), pos: z.array(z.number()).length(3), dir: z.array(z.number()).length(3), len: z.number().optional(), r: z.number().optional() })).optional(),
            holes: z.array(z.object({ id: z.string(), pos: z.array(z.number()).length(3), dir: z.array(z.number()).length(3), r: z.number().optional(), through: z.boolean().optional() })).optional(),
            note: z.string().optional(),
          }).describe('연결점'),
        },
      },
      async ({ partId, connectors }) => {
        const sb = getSupabase()
        const { data: existing, error: getErr } = await sb.from('ivs_part_catalog').select('data').eq('id', partId).maybeSingle()
        if (getErr) return fail(getErr.message)
        if (!existing) return fail(`id="${partId}" 부품을 찾을 수 없어요.`)
        const { error } = await sb.from('ivs_part_catalog').update({ data: { ...existing.data, connectors } }).eq('id', partId)
        if (error) return fail(error.message)
        return text(`✅ ${existing.data?.name || partId} 연결점 기록 (돌기 ${(connectors.pegs || []).length}개, 구멍 ${(connectors.holes || []).length}개)`)
      }
    )
  },
  {
    instructions:
      '큐보 조립 MCP — 설계 화면의 교재 단계별 3D 조립도("조립 보기")를 만드는 데 필요한 조립 규칙·좌표계·부품 측정 사실·작업 절차·조립 단계 데이터·겹침 검사·부품 돌기/구멍 연결점을 제공한다. ' +
      '조립도 작업을 시작하면 먼저 get_assembly_guide 를 읽을 것. 단계 데이터는 get_assembly, 검증은 validate_assembly, 부품 연결점은 get_part_connectors/set_part_connectors. ' +
      '조립 단계 수정은 저장소(mindaephow/invent_school)의 public/design-assemblies.js 를 고쳐서 올리는 방식이며, 사용자는 한 단계씩 고치고 확인받는 방식을 원한다.',
  },
  { basePath: '/api/cubo-assembly', maxDuration: 30, verboseLogs: true }
)

async function authedHandler(request) {
  const url = new URL(request.url)
  const key = url.searchParams.get('key')
  if (!process.env.MCP_SHARED_SECRET || key !== process.env.MCP_SHARED_SECRET) {
    return new Response(JSON.stringify({ error: '인증 필요 (key 파라미터 확인)' }), { status: 401, headers: { 'Content-Type': 'application/json' } })
  }
  return baseHandler(request)
}

export { authedHandler as GET, authedHandler as POST }

// 큐보 조립 도구 6개 — 기존 발명학교 MCP(app/api/mcp/route.js)에 함께 등록된다.
// 설계 화면의 "조립 보기"(교재 단계별 3D 조립도)를 기억 없는 클로드도 이어서 만들 수 있게,
// 조립 안내서(규칙·좌표계·부품 측정 사실·작업 절차)와 조립 단계 데이터, 겹침 검사, 부품 돌기·구멍 연결점 기록을 제공한다.
//   - get_assembly_guide / list_assemblies / get_assembly / validate_assembly / get_part_connectors / set_part_connectors
// 조립 규칙·단계 데이터·겹침 검사 코드는 배포된 public/design-assemblies.js·design-collision.js 를 읽어 온다 —
// 화면과 같은 파일이 원본이라 둘이 어긋나지 않는다. (선택 환경변수 SITE_ORIGIN, 기본 https://invent-school-sigma.vercel.app)
import { z } from 'zod'
import { buildGuide, dimsOf } from './cubo-assembly-guide.js'

const text = (t) => ({ content: [{ type: 'text', text: t }] })
const fail = (t) => ({ content: [{ type: 'text', text: `❌ ${t}` }], isError: true })
const SITE_ORIGIN = () => (process.env.SITE_ORIGIN || 'https://invent-school-sigma.vercel.app').replace(/\/$/, '')

// 배포된 화면용 자바스크립트(window.* 에 값을 넣는 파일)를 가짜 window 로 실행해서 값을 꺼낸다 — 1분 캐시.
let _site = null, _siteAt = 0
export async function loadSite() {
  if (_site && Date.now() - _siteAt < 60_000) return _site
  const win = {}
  for (const file of ['design-assemblies.js', 'design-collision.js', 'design-mates.js']) {
    const res = await fetch(`${SITE_ORIGIN()}/${file}?t=${Date.now()}`)
    if (!res.ok) throw new Error(`${file} 를 못 읽었어요 (${res.status})`)
    new Function('window', await res.text())(win) // 같은 저장소의 파일만 읽는다
  }
  _site = win
  _siteAt = Date.now()
  return win
}

// 오일러(도, ZYX: R = Rz·Ry·Rx) → 쿼터니언
export function quatFromEulerZYX(r) {
  const h = (d) => (d * Math.PI) / 360
  const ax = (a, d) => { const s = Math.sin(h(d)), c = Math.cos(h(d)); return a === 'x' ? [s, 0, 0, c] : a === 'y' ? [0, s, 0, c] : [0, 0, s, c] }
  const mul = (a, b) => [a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1], a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0], a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3], a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]]
  const q = mul(ax('z', r[2]), mul(ax('y', r[1]), ax('x', r[0])))
  return { x: q[0], y: q[1], z: q[2], w: q[3] }
}

// 조립 데이터의 모든 부품을 "제자리" 배치로 모아 몸통 겹침을 검사한다
export function checkOverlaps(steps, COL, tol) {
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


export function registerCuboAssemblyTools(server, getSupabase) {
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
        description: '한 차시의 조립 단계 데이터(JSON)를 돌려준다: 단계별 설명 note·카메라 각도 view, 부품 이름, 위치 p, 회전 r, 끼우는 방향 dir, 안내 위치 marks(recv 부품은 고정된 돌기 끝), 구멍 받는 쪽 recv, 옆자리 조립 side·settleDir, 결합 전 표시 explode, 결합 순서 joinOrder, 띄우는 거리 hover 등(필드 설명은 get_assembly_guide). 수정은 저장소의 public/design-assemblies.js 를 고쳐서 올리고, 고친 뒤 validate_assembly 로 문제 0건을 확인한다.',
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
        title: '조립 데이터 검사(겹침·결합·안내 위치·설명)',
        description: '조립 데이터를 고친 뒤 반드시 돌려서 "문제 0건"을 확인할 것(겹침 없음만으로는 제대로 조립된 게 아니다). 몸통 겹침 + 돌기↔구멍 결합 + 단계별 정밀 검사(새 부품이 실제 구멍에 끼는지, 초록 안내 위치가 실제 구멍/돌기와 맞는지, 리벳 양 끝, T축 머리 방향, 단계 설명의 "N개"가 데이터와 맞는지). 겹침은 조립 데이터의 모든 부품(제자리 배치)을 몸통 상자로 근사해 서로 겹치는지 본다. 돌기·리벳·축이 구멍에 들어가는 것은 겹침으로 세지 않는다. 크기/몸통 규칙이 없는 부품은 검사하지 않고 목록으로 알려 준다. assemblyId(저장된 데이터) 또는 steps(직접 작성한 단계 배열) 중 하나를 준다.',
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
          // 돌기↔구멍 결합 검사: 부품 DB의 연결점(data.connectors)으로 각 돌기가 다른 부품 구멍에 들어가 있는지 본다
          const partsFinal = []
          list.forEach((s, si) => (s.parts || []).forEach((pt, k) => partsFinal.push({ key: `${si + 1}단계 ${pt.n}#${k}`, n: pt.n, p: pt.p, r: pt.r || [0, 0, 0] })))
          const names = [...new Set(partsFinal.map((p) => p.n))]
          const { data: rows, error: cErr } = await getSupabase().from('ivs_part_catalog').select('name:data->>name, connectors:data->connectors').eq('data->>subject', 'robot').in('data->>name', names)
          const conn = {}
          ;(rows || []).forEach((row) => { if (row.connectors) conn[row.name] = row.connectors })
          const mates = cErr ? null : site.IVS_MATES.check(partsFinal, conn)
          const lines = [`검사한 부품 ${r.checked}개 / 겹침 ${r.overlaps.length}건`]
          if (r.overlaps.length) lines.push(...r.overlaps.map((o) => `⚠ ${o}`))
          else lines.push('✅ 겹침 없음(몸통 상자 기준)')
          if (r.skipped.length) lines.push(`검사 안 한 부품(크기·몸통 규칙 없음 또는 체결 부품): ${r.skipped.join(', ')}`)
          if (mates) {
            const linked = new Set(); mates.mated.forEach((m) => { linked.add(m.part); linked.add(m.into) })
            const loose = partsFinal.filter((p) => conn[p.n] && !linked.has(p.key)).map((p) => p.key)
            lines.push(`돌기↔구멍 결합 ${mates.mated.length}건 / 안 들어간 돌기 ${mates.free.length}개 / 연결 안 된 부품 ${loose.length}개`)
            if (loose.length) lines.push(...loose.map((k) => `⚠ 어디에도 연결 안 됨: ${k}`))
            if (mates.free.length) lines.push('비어 있는 돌기(블록 양 끝처럼 원래 비는 곳이면 정상): ' + mates.free.map((f) => `${f.part} ${f.peg}`).join(', '))
            if (mates.noData.length) lines.push(`연결점 기록 없는 부품(결합 검사 못 함): ${[...new Set(mates.noData.map((k) => k.replace(/^\d+단계 /, '').replace(/#\d+$/, '')))].join(', ')}`)
          } else lines.push('(연결점을 못 읽어 결합 검사는 생략)')
          if (mates) {
            const stepIssues = site.IVS_MATES.checkSteps(list, conn)
            lines.push(stepIssues.length ? `단계별 정밀 검사 ${stepIssues.length}건 문제:` : '✅ 단계별 정밀 검사 통과(새 부품 결합·안내 위치·리벳 양 끝·T축 방향·설명 개수)')
            lines.push(...stepIssues.map((x) => `⚠ ${x}`))
          }
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
}

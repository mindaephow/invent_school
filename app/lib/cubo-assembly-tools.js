// 큐보 조립 도구 — 기존 발명학교 MCP(app/api/mcp/route.js)에 함께 등록된다.
// 설계 화면의 "조립 보기"(교재 단계별 3D 조립도)를 기억 없는 클로드도 이어서 만들 수 있게,
// 조립 안내서(규칙·좌표계·부품 측정 사실·작업 절차)와 조립 단계 데이터, 겹침 검사, 부품 돌기·구멍 연결점 기록을 제공한다.
//   - get_assembly_guide / list_assemblies / get_assembly / validate_assembly / get_part_faces / get_part_connectors / set_part_connectors
// 조립 규칙·단계 데이터·겹침 검사 코드는 배포된 public/design-assemblies.js·design-collision.js 를 읽어 온다 —
// 화면과 같은 파일이 원본이라 둘이 어긋나지 않는다. (선택 환경변수 SITE_ORIGIN, 기본 https://invent-school-sigma.vercel.app)
import { z } from 'zod'
import { buildGuide, buildReference, dimsOf } from './cubo-assembly-guide.js'
import { autoAssemble, autoCamera } from './cubo-auto-assemble.js'
import { stlFromDataUrl, measureModel, formatMeasure } from './cubo-part-measure.js'
import { stepContext } from './cubo-step-context.js'

const text = (t) => ({ content: [{ type: 'text', text: t }] })
const fail = (t) => ({ content: [{ type: 'text', text: `❌ ${t}` }], isError: true })
const SITE_ORIGIN = () => (process.env.SITE_ORIGIN || 'https://invent-school-sigma.vercel.app').replace(/\/$/, '')

// 배포된 화면용 자바스크립트(window.* 에 값을 넣는 파일)를 가짜 window 로 실행해서 값을 꺼낸다 — 1분 캐시.
let _site = null, _siteAt = 0
export async function loadSite() {
  if (_site && Date.now() - _siteAt < 60_000) return _site
  const win = {}
  for (const file of ['design-assemblies.js', 'design-collision.js', 'design-mates.js', 'design-verify.js', 'design-faces.js']) {
    const res = await fetch(`${SITE_ORIGIN()}/${file}?t=${Date.now()}`)
    if (!res.ok) throw new Error(`${file} 를 못 읽었어요 (${res.status})`)
    new Function('window', await res.text())(win) // 같은 저장소의 파일만 읽는다
  }
  _site = win
  _siteAt = Date.now()
  return win
}

// 연결점 이름 → 연결점 id (사용자 지시 2026-10-03): "홀면 +y 열5·줄1", "돌기면 +z 1" 처럼 면 이름으로 쓰면 id(h3, p2 …)로 바꿔 준다.
// 이미 id 면 그대로 돌려주고, 이름 규칙(design-faces.js facesOf 와 같은 면·번호)에 맞는데 없는 번호면 가능한 번호를 알려 주는 오류를 낸다.
export function resolveConnectorName(F, partConn, name, partLabel = '') {
  if (typeof name !== 'string') return name
  const c = partConn || {}
  if ([...(c.pegs || []), ...(c.holes || [])].some((q) => q.id === name)) return name
  const m = /^(홀면|돌기면)\s*\(?\s*([+\-−])\s*([xyz])\s*\)?\s*(.*)$/.exec(name.trim())
  if (!m) return name // 이름 규칙이 아니면 그대로(id 로 보고 아래에서 "없어요" 오류가 난다)
  const key = `${m[1]} ${m[2] === '+' ? '+' : '-'}${m[3]}`
  const faces = F.facesOf(c)
  const f = faces.find((x) => x.key === key)
  if (!f) throw new Error(`${partLabel} "${name}": 그런 면이 없어요. 있는 면: ${faces.map((x) => x.key).join(', ')}`)
  let label = m[4].trim().replace(/\s+/g, '').replace(/^열(\d+)[·,]?줄(\d+)$/, '열$1·줄$2')
  if (!label && f.items.length === 1) return f.items[0].id
  const it = f.items.find((x) => x.label === label)
  if (!it) throw new Error(`${partLabel} "${name}": 이 면에 '${label}' 이(가) 없어요. 가능한 번호: ${f.items.map((x) => x.label).join(', ')}`)
  return it.id
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



// 교재(ivs_textbooks)의 해당 차시 부품 LIST → { 부품이름: 개수 }
async function textbookList(sb, def) {
  if (!def || !def.chapter) return null
  const { data: tbs } = await sb.from('ivs_textbooks').select('data')
  const tb = (tbs || []).map((r) => r.data).find((d) => d && d.subject === 'robot' && Number(d.volume) === Number(def.volume) && (d.chapters || []).some((c) => c.title === def.chapter))
  if (!tb) return null
  const ch = tb.chapters.find((c) => c.title === def.chapter)
  const ids = (ch.parts || []).map((p) => p.partId)
  if (!ids.length) return null
  const { data: rows } = await sb.from('ivs_part_catalog').select('id, name:data->>name').in('id', ids)
  const nm = Object.fromEntries((rows || []).map((r) => [r.id, r.name]))
  const out = {}
  ch.parts.forEach((p) => { const n = nm[p.partId]; if (n) out[n] = (out[n] || 0) + Number(p.qty || 0) })
  return out
}

// 조립 데이터(steps)의 부품을 "제자리" 배치로 모은다(validate_assembly 와 같은 규칙).
export function partsFinalOf(list) {
  const out = []
  list.forEach((s, si) => (s.parts || []).forEach((pt, k) => out.push({ key: `${si + 1}단계 ${pt.n}#${k}`, n: pt.n, p: (pt.move && (pt.move.p || pt.move.by)) ? (pt.move.p || pt.p.map((x, q) => x + pt.move.by[q])) : pt.p, r: (pt.move && pt.move.r) || pt.r || [0, 0, 0] })))
  return out
}

// 연결점 기준 조립 요약: 결합 건수, 어디에도 연결 안 된 부품, 단계별 정밀 검사 문제. 부품 연결점을 바꾸기 전·후를 비교하는 데 쓴다.
export function connectorSummary(site, steps, conn) {
  const partsFinal = partsFinalOf(steps)
  const mates = site.IVS_MATES.check(partsFinal, conn)
  const linked = new Set(); mates.mated.forEach((m) => { linked.add(m.part); linked.add(m.into) })
  const loose = partsFinal.filter((p) => conn[p.n] && !linked.has(p.key)).map((p) => p.key)
  let stepIssues = []
  try { stepIssues = site.IVS_MATES.checkSteps(steps, conn) } catch (e) { stepIssues = ['(단계별 정밀 검사를 못 돌렸어요: ' + e.message + ')'] }
  return { mated: mates.mated.length, loose, stepIssues }
}

// 두 요약의 차이를 사람이 읽는 줄로 만든다(같으면 한 줄).
export function diffSummary(label, before, after) {
  const lines = []
  const newLoose = after.loose.filter((x) => !before.loose.includes(x)), fixedLoose = before.loose.filter((x) => !after.loose.includes(x))
  const newIssues = after.stepIssues.filter((x) => !before.stepIssues.includes(x)), fixedIssues = before.stepIssues.filter((x) => !after.stepIssues.includes(x))
  const same = before.mated === after.mated && !newLoose.length && !fixedLoose.length && !newIssues.length && !fixedIssues.length
  if (same) return [`✓ ${label}: 변화 없음 (결합 ${after.mated}건, 연결 안 된 부품 ${after.loose.length}개, 단계별 문제 ${after.stepIssues.length}건)`]
  const head = (newLoose.length || newIssues.length) ? '⚠' : '✓'
  lines.push(`${head} ${label}: 결합 ${before.mated}건 → ${after.mated}건`)
  newLoose.forEach((x) => lines.push(`   ⚠ 새로 생김 — 어디에도 연결 안 됨: ${x}`))
  newIssues.forEach((x) => lines.push(`   ⚠ 새로 생김 — ${x}`))
  fixedLoose.forEach((x) => lines.push(`   ✓ 해결됨 — 연결 안 됨이던 ${x}`))
  fixedIssues.forEach((x) => lines.push(`   ✓ 해결됨 — ${x}`))
  return lines
}

// 작업 공간(창고) 규칙 검사(안내서 6-5): slot·history·보관(hideAt/store/storeThumb)·뼈대 단계. status = { 단계: 'done'|'edit' } (ivs_assembly_status)
export function checkWorkspace(steps, status = {}) {
  const issues = [], notes = [], noThumb = new Set()
  const slots = steps.map((st) => st.slot)
  const useSlots = slots.some((v) => v !== undefined && v !== null)
  steps.forEach((st, i) => {
    const k = i + 1
    if ((st.note || '').includes('(채우는 중)')) issues.push(`${k}단계: 설명에 "(채우는 중)"이 남은 뼈대 단계`)
    if (st.noPart && (st.parts || []).length) issues.push(`${k}단계: noPart 인데 부품이 ${st.parts.length}개 있어요`)
    if (!st.noPart && !(st.parts || []).length && !(st.parts || []).length) {
      const moved = steps.some((o) => (o.parts || []).some((pt) => (pt.move && pt.move.at === k) || (pt.side && pt.side.until === k)))
      if (!moved) issues.push(`${k}단계: 부품이 하나도 없는데 noPart 도, 합치기(move.at/side.until)도 아니에요 — 단계 코드가 지워졌는지 확인`)
    }
    if (useSlots) {
      if (st.slot === undefined || st.slot === null) issues.push(`${k}단계: slot(작업 창고 번호)이 없어요`)
      else if (!Number.isInteger(st.slot) || st.slot < 0 || st.slot > 5) issues.push(`${k}단계: slot=${st.slot} 은 0~5 가 아니에요`)
      else if (k > 1 && slots[i - 1] !== undefined && slots[i - 1] !== null && st.slot !== slots[i - 1] && !st.history) issues.push(`${k}단계: 작업 자리가 ${slots[i - 1]}→${st.slot} 로 바뀌는데 history(불러온/보관한 곳)가 없어요`)
    }
    ;(st.parts || []).forEach((pt) => {
      ;(pt.hideAt || []).forEach((h) => {
        if (!pt.store || !pt.store[String(h)]) issues.push(`${k}단계 ${pt.n}: ${h}단계에서 숨기는데 store(보관 설명)가 없어요`)
        else if (!pt.storeThumb || !pt.storeThumb[String(h)]) noThumb.add(h)
      })
    })
  })
  if (noThumb.size) notes.push(`보관 사진(storeThumb)이 없는 단계: ${[...noThumb].sort((x, y) => x - y).join(', ')} (관리자 📷 썸네일 저장 — 사진이 필요한 곳만)`)
  const done = Object.keys(status).filter((x) => status[x] === 'done').map(Number).sort((a, b) => a - b)
  const edit = Object.keys(status).filter((x) => status[x] === 'edit').map(Number).sort((a, b) => a - b)
  const none = steps.map((_, i) => i + 1).filter((k) => !status[k])
  return { issues, notes: [...new Set(notes)], done, edit, none }
}

export function registerCuboAssemblyTools(server, getSupabase) {
    server.registerTool(
      'get_assembly_guide',
      {
        title: '큐보 스튜디오 안내서 읽기',
        description: '사용자가 "큐보 스튜디오"(교재를 보고 조립도를 만들고·고치고·검토하는 곳)를 말하거나 큐보 조립도(설계 화면 "조립 보기") 작업을 시작하기 전에 가장 먼저 읽을 것 - 만들기·수정·검토 절차가 맨 앞에 있다. 조립 규칙, 좌표계·단위, 3D 모델로 측정한 부품 사실(돌기 위치·방향), 작업 흐름을 돌려준다. 수정·검토 절차, 새 PC 준비, 부품 DB 기록, 화면 기능 같은 참고 자료는 get_assembly_reference 에 따로 있다.',
        inputSchema: {},
      },
      async () => {
        try { const site = await loadSite(); return text(buildGuide(site.IVS_ASSEMBLY_RULES)) }
        catch (e) { return text(buildGuide(null) + `\n\n(화면 파일을 못 읽어 규칙은 생략: ${e.message})`) }
      }
    )

    server.registerTool(
      'get_assembly_reference',
      {
        title: '큐보 스튜디오 참고 문서 읽기',
        description: '조립할 때는 안 봐도 되는 참고 자료(get_assembly_guide 에서 분리): 조립도 수정·검토 절차, 새 PC 준비, 옛 작업 절차, 로봇팽이 사례, 자동 조립(auto_assemble), 부품 DB 연결점 기록 방법(7장), 부품 측정 계획과 안 쓰는 부품 메모, 화면·코드 위치, 화면 기능, 지난 조립도(토끼~비행기) 기록. 규칙이 아니라 필요할 때만 읽는 자료다.',
        inputSchema: {},
      },
      async () => text(buildReference())
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
          // 관리자가 화면의 📷 로 저장한 단계별 시점(ivs_assembly_cams)을 합쳐서 보여 준다 — 있으면 그 단계 cam 을 이걸로 보고 camSrc 는 'admin'(사용자가 맞춘 값)이다
          let saved = {}
          try {
            const { data: rows } = await getSupabase().from('ivs_assembly_cams').select('step, cam, updated_at').eq('assembly_id', assemblyId)
            ;(rows || []).forEach((r) => { saved[r.step] = { ...r.cam, saved_at: r.updated_at } })
          } catch (e) { /* 표가 아직 없으면 저장된 시점 없음 */ }
          const merged = { ...a, steps: a.steps.map((st, i) => saved[i + 1] ? { ...st, cam: { ...(st.cam || {}), theta: saved[i + 1].theta, phi: saved[i + 1].phi, radius: saved[i + 1].radius, target: saved[i + 1].target }, camSrc: 'admin' } : st) }
          const n = Object.keys(saved).length
          return text((n ? `※ 관리자가 화면에서 저장한 시점 ${n}개를 합쳤어요(단계 ${Object.keys(saved).join(', ')} — camSrc: 'admin'). 조립 프로그램의 CAMS 를 만들 때 이 값의 theta·phi 를 쓰세요.
` : '') + JSON.stringify(merged, null, 1))
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
          const partsFinal = partsFinalOf(list)
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
          if (mates && site.IVS_VERIFY) {
            // 단계별 검증 절차(방향 확인 → 구멍 위치 → 앞뒤 단계 비교 → 바닥·개수·카메라)
            const def = assemblyId ? (site.IVS_ASSEMBLIES || []).find((x) => x.id === assemblyId) : { steps: list }
            const dims = {}; names.forEach((n) => { const d = dimsOf(n); if (d) dims[n] = d })
            let listCounts = null
            try { listCounts = await textbookList(getSupabase(), def) } catch (e) { /* 교재 LIST 를 못 읽어도 나머지는 진행 */ }
            const v = site.IVS_VERIFY.verify(def, conn, dims, { list: listCounts })
            lines.push(v.issues.length ? `단계별 검증 절차 ${v.issues.length}건 문제:` : '✅ 단계별 검증 절차 통과(띄우는 방향·바닥 기준·같은 자리 중복·교재 LIST·카메라 지정)')
            lines.push(...v.issues.map((x) => `⚠ ${x}`))
            lines.push('── 단계별 보고서(교재 그림과 하나씩 대조: 구멍 번호는 양쪽 끝에서 센 값) ──', ...v.report)
          }
          lines.push('※ 몸통 상자 근사이므로 돌기가 홀이 아닌 솔리드를 지나가는 것은 잡지 못한다. 화면(조립 보기)에서도 눈으로 확인할 것.')
          return text(lines.join('\n'))
        } catch (e) { return fail(e.message) }
      }
    )


    server.registerTool(
      'auto_assemble',
      {
        title: '자동 조립(공간→판단→검사→수정 반복으로 부품 자세·카메라 확정)',
        description: '부품마다 받는 구멍(또는 돌기)을 지정하면 자세 후보(끼우는 면 앞/뒤 × 롤 0/90/180/270°)를 만들고, 연결·겹침·띄우는 방향 검사를 돌려 통과한 자세를 확정한다(전부 실패하면 어느 검사에서 막혔는지 로그로 돌려줌 → joins 를 고쳐 다시 호출). 카메라도 받는 구멍이 가려지지 않고 끼우는 방향이 잘 보이는 각도로 자동 선택한다(camSrc:"auto" — 교재 그림에서 맞춘 값이 있으면 그것을 우선). placed 는 앞에서 확정된 부품 {key,n,p,r}, plan 은 이번에 놓을 부품 목록 [{ n, key?, joins:[{ mine:내 연결점 id, host:placed 의 key, theirs:받는 연결점 id 또는 theirsGrid:[길이방향 i, 폭방향 j](프레임)}], dirHint:[x,y,z](=조립 데이터의 dir) }]. 연결점 id 는 get_part_connectors 로 본다.',
        inputSchema: {
          assemblyId: z.string().optional().describe('이 차시의 앞 단계 부품을 placed 로 쓴다(afterStep 까지)'),
          afterStep: z.number().optional().describe('assemblyId 와 함께: 이 단계까지의 부품을 놓인 것으로 본다'),
          placed: z.array(z.any()).optional().describe('직접 준 놓인 부품 [{ key, n, p, r }]'),
          plan: z.array(z.any()).describe('이번에 놓을 부품들(위 설명 형식)'),
          camera: z.boolean().optional().describe('카메라 자동 선택도 할지(기본 true)'),
          prevCam: z.object({ az: z.number(), el: z.number() }).optional().describe('앞 단계 카메라(방위·고도, 도) — 연속성 점수에 쓴다'),
        },
      },
      async ({ assemblyId, afterStep, placed, plan, camera = true, prevCam }) => {
        try {
          const site = await loadSite()
          let base = placed || []
          if (!placed && assemblyId) {
            const a = (site.IVS_ASSEMBLIES || []).find((x) => x.id === assemblyId)
            if (!a) return fail('assemblyId 를 찾을 수 없어요.')
            base = []
            a.steps.slice(0, afterStep == null ? a.steps.length : afterStep).forEach((st, k) => (st.parts || []).forEach((pt, i) => base.push({ key: `${k + 1}.${i}`, n: pt.n, p: pt.p, r: pt.r || [0, 0, 0] })))
          }
          const names = [...new Set([...base.map((b) => b.n), ...plan.map((q) => q.n)])]
          const { data: rows, error } = await getSupabase().from('ivs_part_catalog').select('name:data->>name, connectors:data->connectors').eq('data->>subject', 'robot').in('data->>name', names)
          if (error) return fail(error.message)
          const conn = {}; (rows || []).forEach((r) => { if (r.connectors) conn[r.name] = r.connectors })
          const dims = {}; names.forEach((n) => { const d = dimsOf(n); if (d) dims[n] = d })
          // 연결점 이름("홀면 +y 열5·줄1")·부품 번호("315프레임 3번")를 id·key 로 바꾼다
          const alias = {}
          if (!placed && assemblyId) { const cnt = {}; base.forEach((b) => { cnt[b.n] = (cnt[b.n] || 0) + 1; alias[`${b.n} ${cnt[b.n]}번`] = b.key }) }
          const keyOf = new Map(base.map((b) => [b.key, b]))
          for (const q of plan) {
            for (const j of (q.joins || [])) {
              if (alias[j.host]) j.host = alias[j.host]
              j.mine = resolveConnectorName(site.IVS_FACES, conn[q.n], j.mine, q.n)
              const h = keyOf.get(j.host)
              if (h && j.theirs) j.theirs = resolveConnectorName(site.IVS_FACES, conn[h.n], j.theirs, `${h.n}(${j.host})`)
            }
          }
          const ctx = { M: site.IVS_MATES, COL: site.IVS_COLLISION, conn, dims, placed: base }
          const res = autoAssemble(ctx, plan)
          const out = [res.ok ? `✅ 자동 조립 완료: ${res.placed.length}개 부품 확정` : `❌ ${res.stoppedAt + 1}번째 부품(${plan[res.stoppedAt] && plan[res.stoppedAt].n})에서 막힘 — 아래 로그의 [오류]를 보고 joins 를 고쳐 다시 호출하세요`, ...res.log]
          if (res.ok) {
            const step = res.placed.map((q) => ({ n: q.n, p: q.p, r: q.r }))
            out.push('', '── 조립 데이터에 넣을 부품(복사용) ──', JSON.stringify(step))
            const alts = res.placed.filter((q) => q.alternatives && q.alternatives.length).map((q) => `${q.n}(${q.key}): ${q.alternatives.map((a) => a.label).join(', ')}`)
            if (alts.length) out.push('다른 통과 후보(교재 그림과 비교해서 고를 것): ' + alts.join(' / '))
            if (camera) {
              const marks = []
              plan.forEach((q, i) => (q.joins || []).forEach((j) => {
                const h = base.concat(res.placed).find((b) => b.key === j.host); const th = h && conn[h.n] && [...(conn[h.n].holes || []), ...(conn[h.n].pegs || [])].find((c) => c.id === (j.theirs || ''))
                if (h && th) { const Rm = site.IVS_MATES.matFromEuler(h.r || [0, 0, 0]); const w = [0, 1, 2].map((r) => h.p[r] + Rm[r][0] * th.pos[0] + Rm[r][1] * th.pos[1] + Rm[r][2] * th.pos[2]); marks.push(w) }
              }))
              const dir = plan[0] && plan[0].dirHint
              const cam = autoCamera({ M: site.IVS_MATES, COL: site.IVS_COLLISION, dims, placed: base }, { marks, dir, focus: marks }, prevCam)
              out.push('', `── 카메라 ── ${cam.note}`, `step.cam = { theta: ${cam.theta}, phi: ${cam.phi} }, camSrc: 'auto'  // 교재 그림과 대조해서 다르면 교재 방향으로 고칠 것`)
            }
          }
          return text(out.join('\n'))
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'check_workspace',
      {
        title: '작업 공간(창고) 규칙 검사',
        description: '큐보 스튜디오 작업 공간 규칙(안내서 6-5)을 검사한다: 모든 단계에 slot(작업 창고 0~5)이 있는지, 자리가 바뀌는 단계에 history(불러온/보관한 곳)가 있는지, 숨기는 부품에 store(보관 설명)·storeThumb(사진)이 있는지, "(채우는 중)" 뼈대·부품이 사라진 빈 단계가 없는지. 그리고 사용자가 ✅ 완료/🛠 수정중으로 체크한 단계(ivs_assembly_status)를 알려 준다 - 완료 단계는 사용자가 말하기 전에 고치지 말 것. 조립도 작업을 시작할 때와 끝낼 때 돌린다.',
        inputSchema: { assemblyId: z.string().describe('list_assemblies 의 id. 예: cubo-1-airplane') },
      },
      async ({ assemblyId }) => {
        try {
          const site = await loadSite()
          const a = (site.IVS_ASSEMBLIES || []).find((x) => x.id === assemblyId)
          if (!a) return fail(`id="${assemblyId}" 조립 데이터를 찾을 수 없어요. list_assemblies 로 확인하세요.`)
          const status = {}
          let statusErr = ''
          try {
            const { data: rows, error } = await getSupabase().from('ivs_assembly_status').select('step, status').eq('assembly_id', assemblyId)
            if (error) statusErr = error.message
            ;(rows || []).forEach((r) => { status[r.step] = r.status })
          } catch (e) { statusErr = e.message }
          const r = checkWorkspace(a.steps, status)
          const L = [r.issues.length ? `작업 공간 문제 ${r.issues.length}건:` : `✅ 작업 공간 규칙 통과(${a.steps.length}단계)`]
          L.push(...r.issues.map((x) => `⚠ ${x}`))
          if (r.notes.length) L.push('참고:', ...r.notes.map((x) => `· ${x}`))
          if (statusErr) L.push(`(단계 상태 표를 못 읽었어요: ${statusErr})`)
          else L.push(`사용자 체크 — ✅ 완료 ${r.done.length}개: ${r.done.join(', ') || '없음'} / 🛠 수정중: ${r.edit.join(', ') || '없음'} / 표시 없음: ${r.none.join(', ') || '없음'}`, '※ 완료 단계는 사용자가 고치라고 하기 전에는 내용(부품 위치·카메라·설명)을 바꾸지 않는다.')
          return text(L.join(String.fromCharCode(10)))
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'get_part_faces',
      {
        title: '부품의 면·구멍·돌기 번호 조회(월드 좌표 포함)',
        description: '조립도의 부품 하나를 "35프레임 2번" 같은 부품 번호로 지정하면, 그 부품의 면(홀면/돌기면 ±x ±y ±z)과 면 안의 구멍·돌기 번호(열·줄), 부품 축이 지금 월드 어느 방향(+X −X +Y −Y +Z −Z)인지, 각 번호의 월드 좌표를 돌려준다. 스크린샷이나 좌표를 눈으로 읽는 대신 이 값을 읽을 것. 번호는 부품에 고정돼 있어서 부품을 돌려 놓아도 같은 면·같은 구멍이다. 부품 번호는 조립도 전체에서 같은 이름 부품이 나온 순서(단계 → 부품 순). joins 는 이 부품의 돌기가 다른 부품의 어느 구멍에 들어가 있는지(추정 — 좌표·방향이 맞는 것).',
        inputSchema: {
          assemblyId: z.string().describe('list_assemblies 의 id. 예: cubo-1-autogun'),
          part: z.string().describe('부품 번호. 예: "35프레임 2번", "리벳 14번"(옛 표기 "35프레임 2/2"도 받음). 이름만 주면(예: "35프레임") 그 이름의 부품 번호 목록을 돌려준다'),
          step: z.number().optional().describe('이 단계에서의 자세로 계산(옆자리·옮김 반영). 생략하면 완성 자세'),
        },
      },
      async ({ assemblyId, part, step }) => {
        try {
          const site = await loadSite()
          const a = (site.IVS_ASSEMBLIES || []).find((x) => x.id === assemblyId)
          if (!a) return fail(`id="${assemblyId}" 조립 데이터를 찾을 수 없어요. list_assemblies 로 확인하세요.`)
          const F = site.IVS_FACES
          if (!F) return fail('design-faces.js 를 못 읽었어요(배포 전일 수 있어요).')
          const { total, numOf } = F.numberParts(a.steps)
          const m = String(part).trim().match(/^(.+?)\s+(\d+)\s*(?:번|\/\s*(\d+))?$/)
          const name = m ? m[1] : String(part).trim()
          if (!total[name]) return fail(`"${name}" 부품이 이 조립도에 없어요. 있는 부품: ${Object.keys(total).join(', ')}`)
          const all = []
          a.steps.forEach((s, si) => (s.parts || []).forEach((pt) => { if (pt.n === name) all.push({ pt, k: numOf.get(pt), step: si + 1 }) }))
          if (!m) return text(`${name} 는 ${total[name]}개: ` + all.map((x) => `${name} ${x.k}번 (${x.step}단계 등장)`).join(', ') + '\n번호를 붙여 다시 부르세요. 예: "' + name + ' 1번"')
          const hit = all.find((x) => x.k === Number(m[2]))
          if (!hit || (m[3] && Number(m[3]) !== total[name])) return fail(`"${part}" 없음. ${name} 는 총 ${total[name]}개예요(${name} 1번 ~ ${name} ${total[name]}번).`)
          const { data: rows, error } = await getSupabase().from('ivs_part_catalog').select('name:data->>name, connectors:data->connectors').eq('data->>subject', 'robot')
          if (error) return fail(error.message)
          const conn = {}; (rows || []).forEach((r) => { if (r.connectors) conn[r.name] = r.connectors })
          if (!conn[name]) return fail(`${name} 의 연결점 기록이 없어요(get_part_connectors 로 확인).`)
          // 단계 step 에서의 자세: 옆자리(side.until 전) → 제자리, move.at 이후는 옮긴 자리
          const upTo = step || a.steps.length
          const poseOf = (pt) => (pt.side && upTo < pt.side.until) ? { p: pt.side.p, r: pt.side.r } : (pt.move && upTo >= pt.move.at && pt.move.p) ? { p: pt.move.p, r: pt.move.r || pt.r } : { p: pt.p, r: pt.r }
          const pose = poseOf(hit.pt)
          const d = F.describe({ n: name, p: pose.p, r: pose.r }, conn[name], hit.k, total[name])
          // 결합 추정: 이 부품의 돌기 ↔ 다른 부품의 구멍
          const joins = []
          const me = F.worldConnectors({ n: name, p: pose.p, r: pose.r }, conn[name])
          a.steps.slice(0, upTo).forEach((s, si) => (s.parts || []).forEach((q) => {
            if (q === hit.pt || !conn[q.n]) return
            const qp = poseOf(q), w = F.worldConnectors({ n: q.n, p: qp.p, r: qp.r }, conn[q.n])
            const qd = F.describe({ n: q.n, p: qp.p, r: qp.r }, conn[q.n], numOf.get(q), total[q.n])
            const pairs = (pegs, holes, mineIsPeg) => pegs.forEach((pg) => holes.forEach((ho) => {
              if (F.mates(pg, ho)) {
                const sel = (rec, holeLike) => F.nameWorldItem(rec, holeLike)
                joins.push(mineIsPeg ? { 내_돌기: sel(d, pg), 상대: `${qd.name} ${F.nameWorldItem(qd, ho, pg.dir)}`, 단계: si + 1 } : { 내_구멍: F.nameWorldItem(d, ho, pg.dir), 상대: `${qd.name} ${F.nameWorldItem(qd, pg)}`, 단계: si + 1 })
              }
            }))
            pairs(me.pegs, w.holes, true); pairs(w.pegs, me.holes, false)
          }))
          return text(JSON.stringify({ ...d, 단계: upTo, 이름_규칙: '번호는 부품 모델 축에 고정(부품을 돌려도 같은 면·같은 구멍). 열=첫째 축, 줄=둘째 축, 각 축 − 끝부터 1.', 결합_추정: joins }, null, 1))
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'measure_part',
      {
        title: '부품 3D 모델 실측(크기·대칭·돌기·구멍)과 등록된 연결점 대조',
        description: '부품 이름을 주면 DB 의 3D 모델(STL)을 서버에서 읽어 ① 크기 ② 가운데 면 기준 대칭도 ③ 둥근 돌기·구멍의 위치·반지름·길이/깊이·방향을 재고, 등록된 연결점(get_part_connectors)과 하나씩 대조해 일치/차이/없음을 알려 준다. 새 부품을 등록하거나 연결점이 auto 인 부품을 확인할 때 눈으로 세는 대신 먼저 부른다. 좌표는 연결점과 같은 모델 로컬(bbox 가운데 기준, y 위)이라 나온 숫자를 set_part_connectors 에 그대로 쓸 수 있다. 한계: 둥근 벽만 찾는다(십자 + 소켓·네모 구멍은 못 찾음), STL 로 만든 부품만 된다(도형으로 만든 프레임은 대상 아님).',
        inputSchema: {
          name: z.string().describe('부품 이름. 예: 서보모터'),
        },
      },
      async ({ name }) => {
        try {
          const sb = getSupabase()
          const { data, error } = await sb.from('ivs_part_catalog').select('id, name:data->>name, shape:data->spec->shapes->0, connectors:data->connectors').eq('data->>subject', 'robot').eq('data->>name', name)
          if (error) return fail(error.message)
          if (!data || !data.length) return fail(name + ' 부품을 못 찾았어요(list_design_parts 로 이름 확인).')
          const r = data[0]
          const sh = r.shape
          if (!sh || sh.type !== 'import' || !sh.fileDataUrl) return fail(name + ' 은 STL 모델이 아니라(' + (sh ? sh.type : '모양 없음') + ') 실측 대상이 아니에요.')
          const num = (v) => { const x = Number(v); return Number.isFinite(x) ? x : 0 }
          const raw = stlFromDataUrl(sh.fileDataUrl)
          const m = measureModel(raw, { x: num(sh.x), y: num(sh.y), z: num(sh.z), rx: num(sh.rx), ry: num(sh.ry), rz: num(sh.rz) }, r.connectors || null)
          return text(formatMeasure(name, m, !!r.connectors) + '\n\n좌표는 부품 연결점과 같은 기준(bbox 가운데, y 위). 돌기 pos 는 돌기 가운데, 구멍 pos 는 구멍 깊이의 가운데(입구는 따로 표시).')
        } catch (e) { return fail(e.message) }
      }
    )

    // ── 교재 쪽 이미지: 서버 PDF 는 원본 절반 해상도라, 원본에서 뽑은 쪽 이미지를 저장소에 올려 두고 꺼내 본다 ──
    const PAGE_BUCKET = 'textbook-files'
    const pagePath = (volume, page, small) => 'pages/cubo' + volume + '/p' + String(page).padStart(3, '0') + (small ? '_s' : '') + '.jpg'
    server.registerTool(
      'upload_textbook_page',
      {
        title: '교재 쪽 이미지 올리기(원본 해상도 + 작은 판)',
        description: '교재 PDF 원본에서 뽑은 쪽 이미지를 저장소(textbook-files/pages/cubo<권>/p<쪽>.jpg 와 p<쪽>_s.jpg)에 올린다. 보통 scripts/assembly-tools/textbook_pages.py 가 쪽마다 이 도구를 불러 올린다(직접 부를 일은 거의 없다). 이미 있으면 덮어쓴다.',
        inputSchema: {
          volume: z.number().int().describe('권'),
          page: z.number().int().describe('PDF 쪽 번호(1부터)'),
          hi: z.string().describe('원본 해상도 JPEG 의 base64'),
          small: z.string().describe('작은 판(가로 약 1262px) JPEG 의 base64'),
        },
      },
      async ({ volume, page, hi, small }) => {
        try {
          const sb = getSupabase()
          for (const [data, isSmall] of [[hi, false], [small, true]]) {
            const buf = Buffer.from(data, 'base64')
            if (buf.length < 1000 || buf[0] !== 0xff || buf[1] !== 0xd8) return fail('JPEG 가 아니에요(' + (isSmall ? 'small' : 'hi') + ').')
            const { error } = await sb.storage.from(PAGE_BUCKET).upload(pagePath(volume, page, isSmall), buf, { contentType: 'image/jpeg', upsert: true })
            if (error) return fail(error.message)
          }
          return text('✅ ' + volume + '권 ' + page + '쪽 올림: ' + sb.storage.from(PAGE_BUCKET).getPublicUrl(pagePath(volume, page, false)).data.publicUrl)
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'get_textbook_page',
      {
        title: '교재 쪽 이미지 보기(원본 해상도 쪽에서 뽑은 작은 판 + 확대용 주소)',
        description: '교재의 한 쪽을 이미지로 돌려준다(큐보 1권 등 올려 둔 권). 돌려주는 그림은 가로 약 1262px 작은 판이라 한 단계 그림 전체는 보이지만 작은 구멍을 세기엔 모자랄 수 있다 → 같이 돌려주는 원본 해상도(가로 2524px) 주소를 scripts/assembly-tools/textbook_view.py 로 내려받아 필요한 곳만 크게 잘라 보고, 흰 구멍을 자동으로 찾아 번호를 붙일 수 있다(--holes). PDF 쪽 번호 = 교재 쪽 번호. 올려 두지 않은 쪽은 올리는 방법을 알려 준다.',
        inputSchema: {
          page: z.number().int().describe('PDF 쪽 번호. 예: 66(오토건 교재 12~13)'),
          volume: z.number().int().optional().describe('권. 기본 1'),
        },
      },
      async ({ page, volume = 1 }) => {
        try {
          const sb = getSupabase()
          const pub = (small) => sb.storage.from(PAGE_BUCKET).getPublicUrl(pagePath(volume, page, small)).data.publicUrl
          const res = await fetch(pub(true))
          if (!res.ok) return fail(volume + '권 ' + page + '쪽 이미지가 아직 안 올라가 있어요. 교재 PDF 원본이 있는 PC 에서: python scripts/assembly-tools/textbook_pages.py upload "<PDF 경로>" ' + volume + ' ' + page + ' ' + page + '  (IVS_MCP_URL 환경변수 필요)')
          const b64 = Buffer.from(await res.arrayBuffer()).toString('base64')
          return {
            content: [
              { type: 'text', text: volume + '권 ' + page + '쪽 (작은 판). 원본 해상도: ' + pub(false) + '\n크게 잘라 보기: python scripts/assembly-tools/textbook_view.py ' + volume + ' ' + page + ' 0.1 0.2 0.6 0.5   (가로·세로를 0~1 비율로: 왼쪽 위 x y, 오른쪽 아래 x y — 결과 PNG 경로가 출력되면 Read 도구로 본다)\n구멍 자동 찾기: 같은 명령 끝에 --holes' },
              { type: 'image', data: b64, mimeType: 'image/jpeg' },
            ],
          }
        } catch (e) { return fail(e.message) }
      }
    )

    // ── 교재 참고 그림(관리자와 Claude 만 본다): 표 ivs_assembly_refs(supabase/assembly_refs.sql). step 0 = 교재 맨 앞 완성품 사진, 99 = 교재의 "완성" 그림 ──
    server.registerTool(
      'get_step_refs',
      {
        title: '교재 참고 그림 보기(완성품 사진·단계 그림, 돌리거나 확대한 그림 포함)',
        description: '조립도(assemblyId)에 등록해 둔 교재 그림을 이미지로 돌려준다. step 0 = 교재 맨 앞 완성품 사진(앞·뒤·정면·팔·방패가 어느 쪽인지 기준 — 조립도를 만들거나 검토하기 전에 먼저 본다), 99 = 교재 마지막 쪽 "완성" 그림, 1~ = 그 단계 그림(교재 쪽에서 잘라 낸 것, 칸을 세려고 돌리거나 확대한 그림은 설명과 함께 따로). step 을 생략하면 어느 단계에 그림이 있는지 목록만 준다. 같은 그림 파일은 scripts/assembly-tools/refs/<이름>/ 에도 있다(refs_make.py).',
        inputSchema: {
          assemblyId: z.string().describe('조립 데이터 id (list_assemblies). 예: cubo-1-kidknight'),
          step: z.number().int().optional().describe('보려는 단계(0 = 완성품 사진, 99 = 교재 "완성" 그림). 생략하면 목록만'),
        },
      },
      async ({ assemblyId, step }) => {
        try {
          const sb = getSupabase()
          if (step === undefined || step === null) {
            const { data, error } = await sb.from('ivs_assembly_refs').select('step, idx, note').eq('assembly_id', assemblyId).order('step').order('idx')
            if (error) return fail(error.message + ' — 표가 없으면 supabase/assembly_refs.sql 을 Supabase SQL 에디터에서 실행해야 해요.')
            if (!data || !data.length) return text('등록된 교재 그림이 없어요. scripts/assembly-tools/refs_make.py 로 만들고 화면(관리자)에서 올려요.')
            return text(data.map((r) => (r.step === 0 ? '완성품 사진' : r.step === 99 ? '교재 "완성" 그림' : r.step + '단계') + (r.idx ? ' 그림' + (r.idx + 1) : '') + (r.note ? ' — ' + r.note : '')).join('\n'))
          }
          const { data, error } = await sb.from('ivs_assembly_refs').select('step, idx, note, img').eq('assembly_id', assemblyId).eq('step', step).order('idx')
          if (error) return fail(error.message)
          if (!data || !data.length) return fail(assemblyId + ' ' + step + '번 그림이 없어요(목록은 step 을 빼고 부른다).')
          const content = []
          data.forEach((r) => {
            const m = /^data:(image\/[a-z]+);base64,(.+)$/.exec(r.img || '')
            content.push({ type: 'text', text: (step === 0 ? '교재 맨 앞 완성품 사진' : step === 99 ? '교재 마지막 쪽 "완성" 그림' : step + '단계 그림' + (r.idx ? ' ' + (r.idx + 1) : '')) + (r.note ? ' — ' + r.note : '') })
            if (m) content.push({ type: 'image', data: m[2], mimeType: m[1] })
          })
          return { content }
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'set_step_ref',
      {
        title: '교재 참고 그림 올리기(한 장)',
        description: '교재 그림 한 장(JPEG base64)을 조립도·단계·순서(idx)에 등록한다. 이미 있으면 덮어쓴다. 보통은 scripts/assembly-tools/refs/<이름>/ 의 파일을 화면(관리자 로그인)에서 올리므로 직접 부를 일은 거의 없다.',
        inputSchema: {
          assemblyId: z.string(), step: z.number().int().describe('0 = 완성품 사진, 99 = 교재 "완성" 그림, 1~ = 단계'), idx: z.number().int().optional().describe('같은 단계의 그림 순서(0 = 교재에서 잘라 낸 그림, 1~ = 돌리거나 확대한 그림). 기본 0'),
          jpegBase64: z.string().describe('JPEG 의 base64(작게: 가로 1000px 안팎)'), note: z.string().optional().describe('그림 설명'),
        },
      },
      async ({ assemblyId, step, idx = 0, jpegBase64, note = '' }) => {
        try {
          const buf = Buffer.from(jpegBase64, 'base64')
          if (buf.length < 1000 || buf[0] !== 0xff || buf[1] !== 0xd8) return fail('JPEG 가 아니에요.')
          const { error } = await getSupabase().from('ivs_assembly_refs').upsert({ assembly_id: assemblyId, step, idx, img: 'data:image/jpeg;base64,' + jpegBase64, note, updated_at: new Date().toISOString() }, { onConflict: 'assembly_id,step,idx' })
          if (error) return fail(error.message)
          return text('✅ ' + assemblyId + ' ' + step + '단계 그림 ' + idx + ' 저장(' + Math.round(buf.length / 1024) + 'KB)')
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'get_step_context',
      {
        title: '단계 직전 상태(쓴 부품·남은 부품·빈 구멍) — 교재 그림 읽기 전에 부른다',
        description: '조립은 순서대로만 쌓이므로, 단계 k 를 만들거나 검토하기 전에 이 도구로 k−1 단계까지의 상태를 본다: ① 이미 쓴 부품 ② 교재 부품 목록(LIST)에서 남은 부품(이번에 들어올 부품) ③ 부품마다 빈 구멍·빈 돌기(면 이름·번호) ④ 조립 데이터에 이 단계가 있으면 새 부품과 이 단계에서 생긴 결합. 앞 단계가 맞다면 이번 초록 원은 빈 구멍에만 있을 수 있고, 새 부품은 돌기 수만큼의 빈 구멍이 같은 간격으로 있는 자리에만 들어가므로 교재 그림에서 구멍을 일일이 세지 않고 후보 중 하나를 고르면 된다. step 이 조립 데이터 단계 수 + 1 이면 아직 없는 새 단계(만드는 중)로 본다.',
        inputSchema: {
          assemblyId: z.string().describe('조립 데이터 id (list_assemblies). 예: cubo-1-autogun'),
          step: z.number().int().describe('보려는 단계 번호(1부터). 이 단계 직전까지의 상태를 계산한다.'),
        },
      },
      async ({ assemblyId, step }) => {
        try {
          const site = await loadSite()
          const a = (site.IVS_ASSEMBLIES || []).find((x) => x.id === assemblyId)
          if (!a) return fail('assemblyId 를 찾을 수 없어요(list_assemblies 로 id 확인).')
          if (step < 1 || step > a.steps.length + 1) return fail('step 은 1~' + (a.steps.length + 1) + ' 사이여야 해요(' + (a.steps.length + 1) + ' = 아직 없는 새 단계).')
          const sb = getSupabase()
          const names = [...new Set(a.steps.slice(0, step).flatMap((st) => (st.parts || []).map((pt) => pt.n)))]
          const { data: rows, error } = await sb.from('ivs_part_catalog').select('name:data->>name, connectors:data->connectors').eq('data->>subject', 'robot').in('data->>name', names)
          if (error) return fail(error.message)
          const conn = {}; (rows || []).forEach((r) => { if (r.connectors) conn[r.name] = r.connectors })
          let listCounts = null
          try { listCounts = await textbookList(sb, a) } catch (e) { /* LIST 를 못 읽어도 나머지는 계산 */ }
          return text(stepContext({ steps: a.steps, step, conn, F: site.IVS_FACES, M: site.IVS_MATES, listCounts }).text)
        } catch (e) { return fail(e.message) }
      }
    )

    server.registerTool(
      'check_chapter_parts',
      {
        title: '새 조립도 시작 점검(교재 부품 목록 ↔ 부품 DB)',
        description: '새 조립도를 시작할 때 맨 먼저 부른다. 권(volume)과 차시 제목(chapter)을 주면 교재관리(ivs_textbooks)의 그 차시 부품 목록(LIST)을 읽어 부품마다 ① 부품 DB 에 있는지 ② 3D 모델이 있는지 ③ 돌기·구멍 연결점이 있는지·신뢰도(checked/auto) ④ 면 이름이 확정된 부품인지를 한 번에 보여 주고, 이미 만든 조립도가 있는지, 앞으로 등록·확인해야 할 부품 목록을 정리해 준다. 없는 부품은 멈추지 말고 교재를 보고 직접 등록한 뒤 진행한다(get_assembly_guide 의 "첫 30분").',
        inputSchema: {
          chapter: z.string().describe('차시 제목. 예: 조종형비행기 (띄어쓰기는 무시하고 찾는다)'),
          volume: z.number().int().optional().describe('권. 기본 1'),
          category: z.string().optional().describe('카테고리 id. 기본 큐보(6fa8abd9-7684-47a2-bd7f-2bc9a6e3fbe6)'),
        },
      },
      async ({ chapter, volume = 1, category = '6fa8abd9-7684-47a2-bd7f-2bc9a6e3fbe6' }) => {
        try {
          const sb = getSupabase()
          const { data: books, error } = await sb.from('ivs_textbooks').select('id, data').eq('data->>category', category).eq('data->>volume', String(volume))
          if (error) return fail(error.message)
          if (!books || !books.length) return fail('그 권의 교재가 교재관리에 없어요(category=' + category + ', volume=' + volume + ').')
          const norm = (x) => String(x || '').replace(/\s+/g, '')
          const book = books[0].data || {}
          const chapters = book.chapters || []
          const idx = chapters.findIndex((c) => norm(c.title) === norm(chapter))
          const idx2 = idx >= 0 ? idx : chapters.findIndex((c) => norm(c.title).includes(norm(chapter)) || norm(chapter).includes(norm(c.title)))
          if (idx2 < 0) return fail('차시 "' + chapter + '" 를 못 찾았어요. 있는 차시: ' + chapters.map((c, i) => i + '차시 ' + c.title).join(', '))
          const ch = chapters[idx2]
          const pdf = ((book.files || [])[0] || {}).url || null
          const lines = []
          lines.push('■ ' + ch.title + ' — 큐보 ' + volume + '권 ' + idx2 + '차시 (책의 ' + (idx2 + 1) + '번째 차시)')
          lines.push('교재 PDF: ' + (pdf || '(등록된 파일 없음)') + '  ← curl 로 받아 Read 도구 pages 로 쪽을 본다(서버 PDF 는 원본 절반 해상도)')
          const parts = ch.parts || []
          if (!parts.length) { lines.push('⚠ 이 차시에는 부품 목록(LIST)이 등록돼 있지 않아요 — 교재 그림에서 부품을 읽어 교재관리에 먼저 적어야 해요.') }
          const ids = parts.map((q) => q.partId)
          const { data: rows, error: e2 } = ids.length
            ? await sb.from('ivs_part_catalog').select('id, name:data->>name, shape:data->spec->shapes->0->>type, connectors:data->connectors').in('id', ids)
            : { data: [], error: null }
          if (e2) return fail(e2.message)
          const byId = new Map((rows || []).map((r) => [r.id, r]))
          const site = await loadSite()
          const CONF = site.IVS_FACES && site.IVS_FACES.CONFIRMED
          const needRegister = [], needConnectors = [], needConfirm = [], noModel = []
          let total = 0
          parts.forEach((q) => {
            total += q.qty || 0
            const r = byId.get(q.partId)
            if (!r) { lines.push('✗ ' + q.qty + '개  (partId ' + q.partId + ') — 부품 DB 에 없어요'); needRegister.push(q.partId); return }
            const c = r.connectors
            const np = c ? (c.pegs || []).length : 0, nh = c ? (c.holes || []).length : 0
            const hasModel = !!r.shape
            const conf = c ? (c.confidence || '기록됨') : '연결점 없음'
            const confirmed = CONF ? CONF.test(r.name) : false
            const flags = []
            if (!hasModel) { flags.push('3D 모델 없음'); noModel.push(r.name) }
            if (!c) { flags.push('연결점 없음'); if (hasModel) needConnectors.push(r.name) }
            else if (c.confidence === 'auto') { flags.push('연결점 자동탐지(확인 필요)'); needConnectors.push(r.name) }
            if (hasModel && c && !confirmed) needConfirm.push(r.name)
            lines.push((flags.length ? '⚠ ' : '✓ ') + q.qty + '개  ' + r.name + ' — 돌기 ' + np + ' 구멍 ' + nh + ' [' + conf + ']' + (confirmed ? ' · 면 이름 확정' : ' · 면 이름 미확정') + (flags.length ? ' · ' + flags.join(', ') : ''))
          })
          lines.push('부품 ' + parts.length + '종 · 총 ' + total + '개')
          const existing = (site.IVS_ASSEMBLIES || []).filter((a) => norm(a.chapter) === norm(ch.title) && Number(a.volume) === Number(volume))
          lines.push(existing.length ? '이미 있는 조립도: ' + existing.map((a) => a.id + ' (' + a.steps.length + '단계)').join(', ') + ' → 수정(B)/검토(C) 절차' : '이 차시의 조립도는 아직 없어요 → 새로 만들기(A) 절차. 조립도 id 는 cubo-' + volume + '-영문이름, chapter 는 "' + ch.title + '" 와 글자까지 똑같이.')
          lines.push('')
          lines.push('── 해야 할 일 ──')
          lines.push(needRegister.length ? '1) DB 에 없는 부품 ' + needRegister.length + '종: 교재 그림·치수를 보고 직접 등록(get_part_standard → make_part_stl → apply_part_to_db → set_part_connectors)' : '1) 부품 등록: 필요 없음')
          lines.push(needConnectors.length ? '2) 연결점 없음/자동탐지 부품: ' + [...new Set(needConnectors)].join(', ') + ' — 3D 뷰어(?subject=robot → 큐보 부품 전체 리스트)에서 구멍·돌기 개수와 위치를 세어 확인하고 필요하면 set_part_connectors' : '2) 연결점 확인: 모두 checked')
          lines.push(needConfirm.length ? '3) 면 이름 미확정 부품: ' + [...new Set(needConfirm)].join(', ') + ' — get_assembly_guide 4-1절 "확정 메모"가 있으면 따르고, 없으면 모양을 보고 앞뒤를 정해 기록' : '3) 면 이름: 모두 확정')
          if (noModel.length) lines.push('4) 3D 모델 없는 부품(조립도에서 제외 대상): ' + [...new Set(noModel)].join(', '))
          lines.push('다음: get_assembly_guide 의 "큐보 스튜디오 A" 절 3번(스크립트 작성)부터.')
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
        title: '부품 돌기·구멍 연결점 기록(이 부품을 쓰는 조립도 영향 검사 포함)',
        description: '로봇 부품의 돌기(pegs)·구멍(holes) 연결점을 ivs_part_catalog.data.connectors 에 기록한다(다른 필드는 그대로). 좌표는 3D 모델 bbox 가운데를 원점으로 한 모델 로컬 좌표(y 위). 형식은 get_assembly_reference 7장 참고.',
        inputSchema: {
          partId: z.string().describe('ivs_part_catalog 행 id'),
          connectors: z.object({
            pegs: z.array(z.object({ id: z.string(), pos: z.array(z.number()).length(3), dir: z.array(z.number()).length(3), len: z.number().optional(), r: z.number().optional() }).passthrough()).optional(),
            holes: z.array(z.object({ id: z.string(), pos: z.array(z.number()).length(3), dir: z.array(z.number()).length(3), len: z.number().optional(), r: z.number().optional(), through: z.boolean().optional() }).passthrough()).optional(),
            size: z.array(z.number()).optional(),
            confidence: z.string().optional().describe('checked(눈으로 확인) 또는 auto(자동 탐지)'),
            note: z.string().optional(),
          }).passthrough().describe('연결점 (구멍 len·부품 size·confidence 도 그대로 저장된다)'),
        },
      },
      async ({ partId, connectors }) => {
        const sb = getSupabase()
        const { data: existing, error: getErr } = await sb.from('ivs_part_catalog').select('data').eq('id', partId).maybeSingle()
        if (getErr) return fail(getErr.message)
        if (!existing) return fail(`id="${partId}" 부품을 찾을 수 없어요.`)
        const partName = existing.data?.name || partId
        // 이 부품을 쓰는 조립도: 바꾸기 전·후의 결합 검사를 비교해서 어긋남이 생기는지 바로 알려 준다(사용자 지시 2026-10-03)
        let impact = []
        try {
          const site = await loadSite()
          const users = (site.IVS_ASSEMBLIES || []).filter((a) => (a.steps || []).some((st) => (st.parts || []).some((pt) => pt.n === partName)))
          if (users.length) {
            const names = [...new Set(users.flatMap((a) => a.steps.flatMap((st) => (st.parts || []).map((pt) => pt.n))))]
            const { data: rows } = await sb.from('ivs_part_catalog').select('name:data->>name, connectors:data->connectors').eq('data->>subject', 'robot').in('data->>name', names)
            const base = {}; (rows || []).forEach((r) => { if (r.connectors) base[r.name] = r.connectors })
            const connBefore = { ...base }; if (existing.data?.connectors) connBefore[partName] = existing.data.connectors
            const connAfter = { ...base, [partName]: connectors }
            users.forEach((a) => { impact.push(...diffSummary(`${a.id} (${a.chapter})`, connectorSummary(site, a.steps, connBefore), connectorSummary(site, a.steps, connAfter))) })
          }
        } catch (e) { impact = ['(영향받는 조립도 검사를 못 했어요: ' + e.message + ')'] }
        const { error } = await sb.from('ivs_part_catalog').update({ data: { ...existing.data, connectors } }).eq('id', partId)
        if (error) return fail(error.message)
        const head = `✅ ${partName} 연결점 기록 (돌기 ${(connectors.pegs || []).length}개, 구멍 ${(connectors.holes || []).length}개)`
        return text(impact.length ? head + '\n── 이 부품을 쓰는 조립도 검사 (바꾸기 전 → 후) ──\n' + impact.join('\n') + '\n※ 조립도 데이터(위치)는 그대로이니 ⚠ 가 새로 생겼다면 해당 조립도 스크립트를 다시 빌드해야 한다(python build.py 이름 --write).' : head + '\n(이 부품을 쓰는 조립도는 없어요)')
      }
    )
}

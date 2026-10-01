// 큐보 3D 디자인 도구 — 클로드가 "설계 화면"에 놓을 큐보 부품 배치(디자인)를 직접 만들고 검사하고 저장할 수 있게 한다.
// 기존 발명학교 MCP(app/api/mcp/route.js)에 함께 등록된다.
//   get_design_guide / list_design_parts / compute_attach / validate_design / save_design / list_designs / get_design / list_teachers
//   (부품 만들기) get_part_standard / make_part_stl / apply_part_to_db — 규격은 cubo-part-maker.js, 생성기는 cubo-frame-mesh.js·cubo-block-mesh.js
// 핵심은 compute_attach: "이 부품의 이 돌기를 저 부품의 이 구멍에 꽂으면 위치·회전이 어떻게 되나"를 부품 DB의 연결점으로 계산해 준다
// (방향·위치·구멍을 손으로 짐작해서 틀리던 문제를 없앤다). 배치 형식은 조립 데이터와 같다: { n: 부품 이름, p: [x,y,z], r: [rx,ry,rz](도) }.
// 검사·좌표 코드는 배포된 public/design-mates.js·design-collision.js 를 읽어 쓴다(화면과 같은 코드).
import { z } from 'zod'
import { dimsOf, PART_DIMS } from './cubo-assembly-guide.js'
import { loadSite, quatFromEulerZYX, checkOverlaps } from './cubo-assembly-tools.js'
import { CUBO_FRAME_STD, CUBO_BLOCK_STD, PART_STANDARD_TEXT } from './cubo-part-maker.js'
import { frameTriangles } from './cubo-frame-mesh.js'
import { blockTriangles } from './cubo-block-mesh.js'
import { trianglesToStl } from './cubo-mesh-kit.js'

const text = (t) => ({ content: [{ type: 'text', text: t }] })
const fail = (t) => ({ content: [{ type: 'text', text: `❌ ${t}` }], isError: true })
const round = (v, k = 100) => Math.round(v * k) / k

// ── 작은 벡터·행렬 도구(3×3, 열벡터 곱) ──
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
const norm = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l] }
const mulv = (m, v) => [m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2], m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2], m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]]
const mulm = (a, b) => a.map((_, i) => [0, 1, 2].map((j) => a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]))
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
const scale = (a, k) => [a[0] * k, a[1] * k, a[2] * k]
// 축 n(단위) 둘레로 deg 도 회전하는 행렬(로드리게스)
function axisAngle(n, deg) {
  const t = (deg * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t), [x, y, z] = n
  return [[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s], [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s], [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]]
}
// 벡터 a → b 로 돌리는 행렬(둘 다 단위벡터)
function rotateTo(a, b) {
  const d = dot(a, b)
  if (d > 0.999999) return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
  if (d < -0.999999) { // 정반대: a 에 수직인 아무 축으로 180°
    const ref = Math.abs(a[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0]
    return axisAngle(norm(cross(a, ref)), 180)
  }
  const ax = norm(cross(a, b))
  return axisAngle(ax, (Math.acos(d) * 180) / Math.PI)
}
// 행렬 → 오일러(도, ZYX: R = Rz·Ry·Rx) — 화면·조립 데이터와 같은 규약
function eulerFromMat(m) {
  const D = 180 / Math.PI
  let sy = -m[2][0]; sy = Math.max(-1, Math.min(1, sy))
  const ry = Math.asin(sy)
  let rx, rz
  if (Math.abs(sy) > 0.99999) { rz = 0; rx = Math.atan2(m[0][1] / sy, m[0][2] / sy) }
  else { rx = Math.atan2(m[2][1], m[2][2]); rz = Math.atan2(m[1][0], m[0][0]) }
  const f = (v) => { v = Math.round(v * D * 10) / 10; return Object.is(v, -0) ? 0 : v }
  return [f(rx), f(ry), f(rz)]
}

// 부품 DB(연결점·id·크기) — 한 번에 읽어 1분 캐시
let _catalog = null, _catalogAt = 0
async function loadCatalog(sb) {
  if (_catalog && Date.now() - _catalogAt < 60_000) return _catalog
  const { data, error } = await sb.from('ivs_part_catalog').select('id, name:data->>name, category:data->>category, volumes:data->volumes, color:data->>color, connectors:data->connectors').eq('data->>subject', 'robot')
  if (error) throw new Error(error.message)
  const byName = {}, byId = {}
  ;(data || []).forEach((r) => { byName[r.name] = r; byId[r.id] = r })
  _catalog = { rows: data || [], byName, byId }
  _catalogAt = Date.now()
  return _catalog
}
const connOf = (cat) => { const o = {}; cat.rows.forEach((r) => { if (r.connectors) o[r.name] = r.connectors }); return o }

// 배치 목록 정리: [{ n, p, r }] → 검증된 배열(이름이 DB에 있는지)
function cleanParts(parts, cat) {
  const out = [], errs = []
  ;(parts || []).forEach((pt, i) => {
    if (!pt || !cat.byName[pt.n]) { errs.push(`#${i} 부품 이름 "${pt && pt.n}" 이(가) 부품 DB에 없어요(list_design_parts 로 확인).`); return }
    if (!Array.isArray(pt.p) || pt.p.length !== 3 || !pt.p.every(Number.isFinite)) { errs.push(`#${i} ${pt.n}: p 는 [x,y,z] 숫자 3개여야 해요.`); return }
    const r = Array.isArray(pt.r) && pt.r.length === 3 && pt.r.every(Number.isFinite) ? pt.r : [0, 0, 0]
    out.push({ n: pt.n, p: pt.p, r })
  })
  return { parts: out, errs }
}

const DESIGN_GUIDE = `# 큐보 3D 디자인 도구 안내

## 무엇을 하나
설계 화면(design.html, 큐보 1권 등)의 스케치북에 놓을 **부품 배치**를 만들고 검사하고 저장한다. 저장한 디자인은 선생님 계정의 "불러오기"에서 열린다.
조립 보기(교재 단계 재생)와는 다르다 — 조립 데이터는 get_assembly_guide / get_assembly 를 쓴다. 이 도구는 자유 디자인용이다.

## 배치 형식(조립 데이터와 같음)
{ n: 부품 이름(부품 관리에 등록된 이름 그대로), p: [x,y,z](mm, 부품 **가운데** 위치), r: [rx,ry,rz](도, 오일러 ZYX — 화면과 같음) }
- 좌표: 위 = +y, 바닥 모눈 = y=0, 원점 (0,0,0)이 스케치북 정가운데. 구멍은 10mm 격자. 조립 보기 바닥에 +X·−X·+Z·−Z 방향선이 있다.
- 바닥에 그냥 놓은 프레임은 두께 5 → 가운데 y=2.5. (조립 보기 배치는 다리 높이 때문에 y 가 15 더 높다 — 자유 디자인은 바닥 기준으로 잡는다.)

## 작업 순서(실수 방지)
1. **get_assembly_guide** 를 먼저 읽는다(규칙: 돌기↔구멍, 겹침 금지, 리벳·브라켓·T축 사실, 실수 체크리스트). 이 안내서는 자유 디자인에도 그대로 적용된다.
2. **list_design_parts** 로 쓸 부품과 돌기·구멍 수, 크기를 본다.
3. 첫 부품(보통 바닥 프레임)은 직접 놓는다: 예) 35프레임 p=[0,2.5,0] r=[0,0,0].
4. 나머지는 **compute_attach** 로 놓는다: "고정된 부품의 구멍 h3 에 새 부품의 돌기 p2 를 꽂기"를 계산해서 p·r 을 돌려준다. 손으로 위치·회전을 짐작하지 않는다. roll 로 돌기 축 둘레 회전(0/90/180/270)을 고른다(프레임 모양·방향 때문에).
5. **validate_design** 으로 검사한다: 이름·좌표 오류, 몸통 겹침, 새 부품이 실제로 끼워졌는지(허공 부품), 리벳 양 끝, T축 머리 방향. 문제 0건일 때까지 고친다.
6. **save_design** 으로 저장한다(선생님 계정 지정). 겹침이 있으면 저장을 거부한다.
7. 사용자에게 "설계 화면 → 불러오기 → 이름"으로 열어 보라고 안내하고, 화면에서 눈으로 확인받는다.

## 새 부품 만들기(프레임·블록)
배치가 아니라 부품 자체의 3D 모양을 새로 만들 땐 **get_part_standard** 를 먼저 읽는다(규격 숫자, STL 만드는 방법).

## 주의
- 부품 방향이 헷갈리면(눈블록 원판 바깥, T축 머리 위, 브라켓 세로 판 밖) get_assembly_guide 4장을 본다. compute_attach 는 돌기가 구멍으로 들어가는 방향을 맞춰 주지만, 모양(접시 머리 위 등)은 roll 과 guide 로 직접 확인한다.
- 통과 구멍(through)은 양쪽에서 끼울 수 있다: compute_attach 의 side 로 고른다.
- 검사는 몸통 상자 근사라 돌기가 솔리드를 지나가는 것은 못 잡는다. 화면에서 확인한다.
`

export function registerCuboDesignTools(server, getSupabase) {
  server.registerTool(
    'get_design_guide',
    {
      title: '큐보 3D 디자인 안내서',
      description: '큐보 부품 배치(3D 디자인) 작업을 시작하기 전에 읽을 것. 배치 형식·좌표·작업 순서(compute_attach 로 놓고 validate_design 으로 검사한 뒤 save_design)를 알려 준다. 조립 규칙 자체는 get_assembly_guide 를 함께 읽는다.',
      inputSchema: {},
    },
    async () => text(DESIGN_GUIDE)
  )

  server.registerTool(
    'get_part_standard',
    {
      title: '큐보 부품 만들기 기본 규격',
      description: '큐보 부품(프레임 등)을 새로 만들 때 쓰는 기본 규격(판 두께, 홀 테두리, 제일 작은 홀, 폭, 여백, 간격). 등록된 15프레임을 실측해 정한 값이다. 부품 만들기 도형을 설계하기 전에 읽는다.',
      inputSchema: {},
    },
    async () => text(PART_STANDARD_TEXT)
  )

  const partTris = (kind, n) => (kind === 'block' ? blockTriangles(n) : frameTriangles(n))

  server.registerTool(
    'make_part_stl',
    {
      title: '부품 STL 크기 확인(프레임·블록)',
      description: '기본 규격(get_part_standard)대로 프레임 또는 블록을 삼각형으로 직접 짜서(자르기 계산 없음) 크기를 알려 준다: 삼각형 수, STL 용량, 가로·높이·폭. 저장하지 않는다. 실제 STL 파일은 저장소의 scripts/make-part-stl.mjs 로 만든다(get_part_standard 참고).',
      inputSchema: {
        kind: z.enum(['frame', 'block']).describe('frame=직선 프레임, block=스냅핏 돌기 블록'),
        count: z.number().int().min(1).max(30).describe('프레임은 구멍 수(15프레임=5), 블록은 칸 수(3단블록=3)'),
      },
    },
    async ({ kind, count }) => {
      const tris = partTris(kind, count)
      const stl = trianglesToStl(tris)
      const dims = kind === 'block'
        ? `${count * 10 + 10}(양 끝 돌기 포함) × ${CUBO_BLOCK_STD.height} × ${CUBO_BLOCK_STD.width + 10}(앞뒤 돌기 포함)`
        : `${count * CUBO_FRAME_STD.pitch} × ${CUBO_FRAME_STD.total} × ${CUBO_FRAME_STD.width}`
      return text(`${kind === 'block' ? '블록' : '프레임'} ${count}칸: 길이×높이×폭 ${dims}mm, 삼각형 ${tris.length / 9}개, STL ${(stl.length / 1024).toFixed(0)}KB.`)
    }
  )

  server.registerTool(
    'apply_part_to_db',
    {
      title: '규격 부품 STL 을 부품 DB 에 넣기',
      description: '기본 규격으로 만든 프레임/블록 STL 을 부품 DB(ivs_part_catalog) 행의 data.spec.shapes 에 넣는다(프레임이면 pitch·margin·thickness·boreRadius·maxHolesPerArm·holeCoords·holeLabels 도). 그 부품의 다른 필드(이름, 색, 연결점 등)는 그대로 둔다. **부품 DB 를 바꾸므로 사용자가 허락한 뒤에만 쓴다** — 보통은 STL 파일을 만들어 주고 사용자가 직접 등록한다. 넣은 뒤 썸네일은 부품 관리에서 열어 저장하면 다시 만들어진다.',
      inputSchema: {
        partId: z.string().describe('ivs_part_catalog 행 id'),
        kind: z.enum(['frame', 'block']),
        count: z.number().int().min(1).max(30).describe('프레임은 구멍 수, 블록은 칸 수'),
        color: z.string().optional().describe('색. 생략하면 프레임 빨강, 블록 회색'),
        confirm: z.literal(true).describe('사용자가 부품 DB 수정을 허락했을 때만 true'),
      },
    },
    async ({ partId, kind, count, color }) => {
      try {
        const sb = getSupabase()
        const { data: existing, error: getErr } = await sb.from('ivs_part_catalog').select('data').eq('id', partId).maybeSingle()
        if (getErr) return fail(getErr.message)
        if (!existing) return fail('그 id 의 부품을 찾을 수 없어요.')
        const S = CUBO_FRAME_STD
        const stl = trianglesToStl(partTris(kind, count))
        const name = existing.data.name || (kind === 'block' ? '블록' : '프레임')
        const base = typeof existing.data.spec === 'object' && existing.data.spec ? existing.data.spec : {}
        const frameFields = kind === 'frame' ? {
          pitch: S.pitch, margin: S.margin, thickness: S.total, boreRadius: S.boreR, maxHolesPerArm: count,
          holeCoords: Array.from({ length: count }, (_, i) => ({ x: S.margin, z: S.margin + i * S.pitch, face: null, label: `X1Z${i + 1}` })),
          holeLabels: Array.from({ length: count }, (_, i) => `X1Z${i + 1}`),
        } : {}
        const spec = {
          ...base, ...frameFields,
          shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: color || (kind === 'block' ? '#555555' : '#e03b2b'), fileName: `${name}.stl`, brightness: 100, fileDataUrl: 'data:application/octet-stream;base64,' + Buffer.from(stl).toString('base64') }],
        }
        const { error } = await sb.from('ivs_part_catalog').update({ data: { ...existing.data, spec } }).eq('id', partId)
        if (error) return fail(error.message)
        return text(`✅ "${name}"(id=${partId}) 의 3D 모델을 규격 ${kind === 'block' ? '블록' : '프레임'} ${count}칸으로 바꿨어요(STL ${(stl.length / 1024).toFixed(0)}KB). 부품 관리에서 열어 저장하면 썸네일이 다시 만들어져요.`)
      } catch (e) { return fail(e.message) }
    }
  )

  server.registerTool(
    'list_design_parts',
    {
      title: '디자인에 쓸 부품 목록',
      description: '부품 DB의 로봇 부품 목록: 이름, 크기(mm), 돌기·구멍 개수, 연결점 신뢰도(checked/auto). volume(권)·category 로 거를 수 있다. name 을 주면 그 부품의 돌기·구멍 id 와 위치까지 자세히 보여 준다(compute_attach 의 connector id 를 고를 때 사용).',
      inputSchema: {
        name: z.string().optional().describe('부품 이름(주면 연결점 상세)'),
        volume: z.number().optional().describe('권 번호(그 권까지 쓸 수 있는 부품만)'),
        category: z.string().optional().describe('카테고리 id'),
      },
    },
    async ({ name, volume, category }) => {
      try {
        const cat = await loadCatalog(getSupabase())
        if (name) {
          const r = cat.byName[name]
          if (!r) return fail(`"${name}" 부품이 없어요.`)
          const c = r.connectors || {}
          const fmt = (a) => `[${a.map((v) => round(v, 10)).join(', ')}]`
          const lines = [`${r.name} (id=${r.id}) 크기 ${c.size ? c.size.join('×') : (dimsOf(r.name) || []).join('×') || '?'} confidence=${c.confidence || '기록 없음'}`]
          if (c.note) lines.push(`설명: ${c.note}`)
          ;(c.pegs || []).forEach((p) => lines.push(`돌기 ${p.id}: pos ${fmt(p.pos)} dir ${fmt(p.dir)} len ${p.len} r ${p.r}`))
          ;(c.holes || []).forEach((h) => lines.push(`구멍 ${h.id}: pos ${fmt(h.pos)} dir ${fmt(h.dir)} len ${h.len} ${h.through ? '관통' : '막힘'}`))
          lines.push('(좌표는 부품 가운데 기준 모델 로컬 좌표. dir 은 구멍은 "들어가는 방향", 돌기는 "뻗는 방향")')
          return text(lines.join('\n'))
        }
        const rows = cat.rows.filter((r) => (!category || r.category === category) && (volume == null || !Array.isArray(r.volumes) || !r.volumes.length || r.volumes.some((v) => Number(v.volume) <= volume)))
        const lines = rows.map((r) => {
          const c = r.connectors || {}
          return `- ${r.name}: ${c.size ? c.size.join('×') : (dimsOf(r.name) || []).join('×') || '크기 ?'} / 돌기 ${(c.pegs || []).length} 구멍 ${(c.holes || []).length} [${c.confidence || '연결점 없음'}]`
        })
        return text(`부품 ${rows.length}종\n${lines.join('\n')}`)
      } catch (e) { return fail(e.message) }
    }
  )

  server.registerTool(
    'compute_attach',
    {
      title: '부품 끼우기 위치·회전 계산',
      description: '고정된 부품의 연결점(구멍 또는 돌기)에 새 부품의 연결점을 끼웠을 때 새 부품의 p·r 을 계산한다. "돌기를 구멍에 꽂기"(moving 이 돌기, fixed 가 구멍) 또는 "구멍을 돌기에 끼우기"(moving 이 구멍, fixed 가 돌기)를 지원한다. roll 은 끼우는 축 둘레 회전(도)이라 프레임을 돌려 놓을 때 고른다 — 4방향(0/90/180/270) 결과를 모두 돌려주고 각 결과를 결합 검사로 확인한다. list_design_parts(name=…) 로 connector id 를 본다.',
      inputSchema: {
        fixed: z.object({ n: z.string(), p: z.array(z.number()).length(3), r: z.array(z.number()).length(3).optional() }).describe('이미 놓인 부품'),
        fixedConnector: z.string().describe('고정 부품의 연결점 id (예: h3 또는 p2)'),
        movingName: z.string().describe('새로 놓을 부품 이름'),
        movingConnector: z.string().describe('새 부품의 연결점 id (예: p1 또는 h4)'),
        side: z.enum(['front', 'back']).optional().describe('관통 구멍에서 들어가는 쪽. 기본 front(구멍 dir 방향), back 은 반대편에서'),
        roll: z.number().optional().describe('끼우는 축 둘레 회전(도). 생략하면 0/90/180/270 모두 계산'),
      },
    },
    async ({ fixed, fixedConnector, movingName, movingConnector, side = 'front', roll }) => {
      try {
        const site = await loadSite()
        const cat = await loadCatalog(getSupabase())
        const conn = connOf(cat)
        if (!conn[fixed.n]) return fail(`${fixed.n} 의 연결점이 DB에 없어요.`)
        if (!conn[movingName]) return fail(`${movingName} 의 연결점이 DB에 없어요.`)
        const fx = { n: fixed.n, p: fixed.p, r: fixed.r || [0, 0, 0] }
        const W = site.IVS_MATES.worldConnectors(fx, conn[fx.n])
        const fh = W.holes.find((h) => h.id === fixedConnector), fp = W.pegs.find((p) => p.id === fixedConnector)
        const mc = conn[movingName]
        const mp = (mc.pegs || []).find((p) => p.id === movingConnector), mh = (mc.holes || []).find((h) => h.id === movingConnector)
        if (!fh && !fp) return fail(`${fx.n} 에 연결점 "${fixedConnector}" 가 없어요.`)
        if (!mp && !mh) return fail(`${movingName} 에 연결점 "${movingConnector}" 가 없어요.`)
        let aLocal, bWorld, anchorLocal, anchorWorld, kind
        if (fh && mp) {
          // 새 부품의 돌기를 고정 구멍에: 돌기 방향 = 구멍에 들어가는 방향, 돌기 뿌리 = 구멍 입구
          if (side === 'back' && !fh.through) return fail('이 구멍은 관통이 아니라 반대편(back)에서 끼울 수 없어요.')
          const hd = side === 'back' ? scale(fh.dir, -1) : fh.dir
          const entrance = sub(fh.pos, scale(hd, (side === 'back' ? -1 : 1) * (fh.len || 0) / 2))
          aLocal = norm(mp.dir); bWorld = norm(hd)
          anchorLocal = mp.pos; anchorWorld = add(entrance, scale(bWorld, (mp.len || 0) / 2)); kind = '돌기→구멍'
        } else if (fp && mh) {
          // 새 부품의 구멍을 고정 돌기에: 구멍 입구 = 돌기 뿌리, 구멍 들어가는 방향 = 돌기 방향
          aLocal = norm(mh.dir); bWorld = norm(fp.dir)
          const localEntrance = sub(mh.pos, scale(aLocal, (mh.len || 0) / 2))
          anchorLocal = localEntrance; anchorWorld = sub(fp.pos, scale(bWorld, (fp.len || 0) / 2)); kind = '구멍←돌기'
        } else return fail('돌기↔구멍 짝이어야 해요(구멍끼리·돌기끼리는 계산하지 않아요).')
        const R0 = rotateTo(aLocal, bWorld)
        const rolls = roll != null ? [roll] : [0, 90, 180, 270]
        const results = rolls.map((rl) => {
          const R = mulm(axisAngle(bWorld, rl), R0)
          const t = sub(anchorWorld, mulv(R, anchorLocal))
          const r = eulerFromMat(R)
          const moving = { n: movingName, p: t.map((v) => round(v, 100)), r }
          // 결합 검사로 확인
          const parts = [{ key: 'fixed', ...fx }, { key: 'moving', ...moving }]
          const mates = site.IVS_MATES.check(parts, conn)
          const n = mates.mated.filter((m) => m.part === 'moving' || m.into === 'moving').length
          return { roll: rl, p: moving.p, r, 결합수: n }
        })
        const lines = [`${kind}: ${fx.n}.${fixedConnector} ← ${movingName}.${movingConnector}${side === 'back' ? ' (반대편)' : ''}`]
        results.forEach((x) => lines.push(`roll ${x.roll}°: { n: '${movingName}', p: [${x.p.join(', ')}], r: [${x.r.join(', ')}] }  — 돌기↔구멍 결합 ${x.결합수}건${x.결합수 ? '' : ' ⚠ 결합 안 잡힘(깊이·방향 확인)'}`))
        lines.push('같은 돌기 축 둘레 회전만 다르다. 모양(프레임이 눕는지, 브라켓 세로 판 바깥 등)에 맞는 roll 을 고르고 validate_design 으로 확인한다.')
        return text(lines.join('\n'))
      } catch (e) { return fail(e.message) }
    }
  )

  async function runValidate(parts, sb) {
    const site = await loadSite()
    const cat = await loadCatalog(sb)
    const { parts: clean, errs } = cleanParts(parts, cat)
    const conn = connOf(cat)
    const issues = [...errs]
    const info = []
    if (!clean.length) return { issues: issues.length ? issues : ['부품이 하나도 없어요.'], info, clean }
    const ov = checkOverlaps([{ parts: clean }], site.IVS_COLLISION, 0.6)
    ov.overlaps.forEach((o) => issues.push(`겹침: ${o.replace(/1단계 /g, '')}`))
    if (ov.skipped.length) info.push(`겹침 검사 안 한 부품(몸통 규칙 없음): ${ov.skipped.join(', ')}`)
    const keyed = clean.map((pt, i) => ({ key: `#${i} ${pt.n}`, ...pt }))
    const res = site.IVS_MATES.check(keyed, conn)
    const linked = new Set(); res.mated.forEach((m) => { linked.add(m.part); linked.add(m.into) })
    keyed.filter((k) => conn[k.n] && !linked.has(k.key)).forEach((k) => issues.push(`허공에 떠 있음(어디에도 안 끼워짐): ${k.key} p=[${k.p}]`))
    keyed.filter((k) => k.n === '리벳').forEach((k) => {
      const pegs = new Set(res.mated.filter((m) => m.part === k.key).map((m) => m.peg))
      if (pegs.size < 2) issues.push(`${k.key}: 리벳 한쪽 끝만 구멍에 들어감(${pegs.size}/2)`)
    })
    keyed.filter((k) => k.n === 'T축').forEach((k) => {
      const m = site.IVS_MATES.matFromEuler(k.r)
      if (!(m[1][1] < -0.9)) info.push(`${k.key}: T축 접시 머리가 위로 오지 않음(머리가 위면 r=[180,0,0])`)
    })
    info.push(`돌기↔구멍 결합 ${res.mated.length}건 / 비어 있는 돌기 ${res.free.length}개(블록 양 끝 등은 정상)`)
    return { issues, info, clean }
  }

  server.registerTool(
    'validate_design',
    {
      title: '디자인 검사',
      description: '배치 목록 [{ n, p, r }]을 검사한다: 부품 이름·좌표 오류, 몸통 겹침, 허공에 떠 있는 부품(어디에도 안 끼워짐), 리벳 양 끝, T축 머리 방향. "문제 0건"이 될 때까지 고친 뒤 save_design 을 쓴다. designId 를 주면 저장된 디자인을 검사한다.',
      inputSchema: {
        parts: z.array(z.object({ n: z.string(), p: z.array(z.number()).length(3), r: z.array(z.number()).length(3).optional() })).optional(),
        designId: z.string().optional().describe('저장된 디자인 id(list_designs)'),
      },
    },
    async ({ parts, designId }) => {
      try {
        const sb = getSupabase()
        let list = parts
        if (!list) {
          if (!designId) return fail('parts 또는 designId 를 주세요.')
          list = await loadDesignParts(sb, designId)
          if (!list) return fail('디자인을 찾을 수 없어요.')
        }
        const r = await runValidate(list, sb)
        const lines = [`부품 ${r.clean.length}개 검사 — 문제 ${r.issues.length}건`]
        lines.push(...(r.issues.length ? r.issues.map((x) => `⚠ ${x}`) : ['✅ 문제 없음']))
        lines.push(...r.info.map((x) => `· ${x}`))
        lines.push('※ 몸통 상자 근사라 돌기가 솔리드를 지나가는 것은 못 잡는다. 설계 화면에서 눈으로 확인할 것.')
        return text(lines.join('\n'))
      } catch (e) { return fail(e.message) }
    }
  )

  // 저장된 디자인(ivs_teacher_projects) → 배치 목록
  async function loadDesignParts(sb, id) {
    const cat = await loadCatalog(sb)
    const { data, error } = await sb.from('ivs_teacher_projects').select('id, data').eq('id', id).maybeSingle()
    if (error) throw new Error(error.message)
    if (!data) return null
    return (data.data?.parts || []).map((pt) => {
      const pid = String(pt.type || '').replace(/^robot:/, '')
      const row = cat.byId[pid]
      return { n: row ? row.name : `(알 수 없는 ${pt.type})`, p: pt.pos, r: pt.rot || [0, 0, 0] }
    })
  }

  server.registerTool(
    'list_teachers',
    {
      title: '선생님 목록',
      description: '디자인을 저장할 선생님 계정 목록(id, 이름, 승인 여부). save_design 의 teacherId 를 고를 때 쓴다.',
      inputSchema: {},
    },
    async () => {
      const { data, error } = await getSupabase().from('ivs_teachers').select('id, name:data->>name, approved')
      if (error) return fail(error.message)
      return text((data || []).map((t) => `- ${t.name || '(이름 없음)'} id=${t.id} ${t.approved ? '승인' : '미승인'}`).join('\n') || '(선생님 없음)')
    }
  )

  server.registerTool(
    'list_designs',
    {
      title: '저장된 디자인 목록',
      description: '선생님 계정의 저장된 3D 디자인(ivs_teacher_projects) 목록: id, 이름, 부품 수, 수정 시각.',
      inputSchema: { teacherId: z.string().optional().describe('선생님 id(list_teachers). 생략하면 전체 최근 20개') },
    },
    async ({ teacherId }) => {
      let q = getSupabase().from('ivs_teacher_projects').select('id, teacher_id, name:data->>name, parts:data->parts, updated:data->>updatedAt, created_at').order('created_at', { ascending: false }).limit(20)
      if (teacherId) q = q.eq('teacher_id', teacherId)
      const { data, error } = await q
      if (error) return fail(error.message)
      return text((data || []).map((d) => `- ${d.name || '(이름 없음)'} id=${d.id} 부품 ${Array.isArray(d.parts) ? d.parts.length : 0}개 teacher=${d.teacher_id} 수정 ${d.updated ? new Date(Number(d.updated)).toISOString() : d.created_at}`).join('\n') || '(저장된 디자인 없음)')
    }
  )

  server.registerTool(
    'get_design',
    {
      title: '저장된 디자인 읽기',
      description: '저장된 디자인 하나를 [{ n, p, r }] 배치 목록으로 돌려준다(부품 이름으로 풀어서). 이어서 고치거나 validate_design 으로 검사할 때 쓴다.',
      inputSchema: { designId: z.string() },
    },
    async ({ designId }) => {
      try {
        const sb = getSupabase()
        const parts = await loadDesignParts(sb, designId)
        if (!parts) return fail('디자인을 찾을 수 없어요.')
        return text(`부품 ${parts.length}개\n` + JSON.stringify(parts))
      } catch (e) { return fail(e.message) }
    }
  )

  server.registerTool(
    'save_design',
    {
      title: '디자인 저장',
      description: '배치 목록 [{ n, p, r }]을 선생님 계정의 디자인으로 저장한다(설계 화면 "불러오기"에서 열림; 계정은 teacherId, 생략 시 기본 계정 환경변수 DESIGN_DEFAULT_TEACHER_ID). designId 를 주면 그 디자인을 덮어쓰고, 없으면 새로 만든다. 저장 전에 validate_design 과 같은 검사를 하고 문제가 있으면 저장하지 않는다(force=true 는 사용자가 허락했을 때만).',
      inputSchema: {
        teacherId: z.string().optional().describe('저장할 선생님 id(list_teachers). 생략하면 환경변수 DESIGN_DEFAULT_TEACHER_ID 의 계정'),
        name: z.string().describe('디자인 이름'),
        parts: z.array(z.object({ n: z.string(), p: z.array(z.number()).length(3), r: z.array(z.number()).length(3).optional() })),
        designId: z.string().optional().describe('덮어쓸 디자인 id'),
        force: z.boolean().optional().describe('검사 문제가 있어도 저장(사용자 허락 시에만)'),
      },
    },
    async ({ teacherId, name, parts, designId, force }) => {
      try {
        const sb = getSupabase()
        const owner = teacherId || process.env.DESIGN_DEFAULT_TEACHER_ID
        if (!owner && !designId) return fail('저장할 선생님 계정을 정해야 해요. list_teachers 로 id 를 골라 teacherId 로 주거나, 서버 환경변수 DESIGN_DEFAULT_TEACHER_ID 에 기본 계정 id 를 등록하세요.')
        const r = await runValidate(parts, sb)
        if (r.issues.length && !force) return fail(`검사에서 문제 ${r.issues.length}건이라 저장하지 않았어요:\n${r.issues.map((x) => `⚠ ${x}`).join('\n')}\n고친 뒤 다시 저장하세요.`)
        const cat = await loadCatalog(sb)
        const saved = r.clean.map((pt) => {
          const q = quatFromEulerZYX(pt.r)
          const row = cat.byName[pt.n]
          return { type: `robot:${row.id}`, mount: 'floor', pos: pt.p.map((v) => round(v, 1000)), rot: pt.r, quat: [q.x, q.y, q.z, q.w].map((v) => round(v, 100000)) }
        })
        const now = Date.now()
        if (designId) {
          const { data: ex, error: e1 } = await sb.from('ivs_teacher_projects').select('id, data').eq('id', designId).maybeSingle()
          if (e1) return fail(e1.message)
          if (!ex) return fail('덮어쓸 디자인을 찾을 수 없어요.')
          const { error } = await sb.from('ivs_teacher_projects').update({ data: { ...ex.data, name, parts: saved, updatedAt: now } }).eq('id', designId)
          if (error) return fail(error.message)
          return text(`✅ 덮어썼어요: "${name}" 부품 ${saved.length}개 (id=${designId}). 설계 화면 → 불러오기에서 열어 확인하세요.${r.issues.length ? `\n(검사 문제 ${r.issues.length}건을 force 로 저장함)` : ''}`)
        }
        const { data, error } = await sb.from('ivs_teacher_projects').insert({ teacher_id: owner, data: { name, parts: saved, createdAt: now, updatedAt: now } }).select('id').single()
        if (error) return fail(error.message)
        return text(`✅ 저장했어요: "${name}" 부품 ${saved.length}개 (id=${data.id}). 설계 화면 → 불러오기에서 열어 확인하세요.${r.issues.length ? `\n(검사 문제 ${r.issues.length}건을 force 로 저장함)` : ''}`)
      } catch (e) { return fail(e.message) }
    }
  )
}

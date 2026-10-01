// 자동 조립 프로그램 — 사람이 하던 "공간 파악 → 판단 → 사고 → 확정 → 오류 → 판단 → 수정"을 반복해서 부품 자세를 정한다.
//   공간: 받는 쪽 구멍(또는 돌기)의 월드 위치·축을 계산한다
//   판단: 새 부품의 돌기(구멍)를 거기에 맞추는 자세 후보를 만든다(끼우는 면 앞/뒤 × 축 둘레 0/90/180/270°)
//   사고: 후보마다 ① 모든 연결(joins)이 실제로 들어가는지 ② 이미 놓인 부품과 몸통이 겹치지 않는지 ③ 띄우는 방향(dirHint = 조립 데이터의 dir)과 돌기 방향이 반대인지 검사
//   확정/오류/수정: 통과한 후보 중 점수가 높은 것을 확정하고, 전부 실패하면 어느 검사에서 막혔는지 적어서 돌려준다(그 로그를 보고 joins 를 고쳐 다시 돌린다)
// 순수 계산 모듈 — 배포된 design-mates.js(IVS_MATES)·design-collision.js(IVS_COLLISION)를 받아서 쓴다.
const D2R = Math.PI / 180
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k]
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
const unit = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l] }
const mm = (a, b) => [0, 1, 2].map((i) => [0, 1, 2].map((j) => a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]))
const mv = (m, v) => [0, 1, 2].map((i) => m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2])
const I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
const r1 = (v) => Math.round(v * 10) / 10

function rotBetween(a, b) {
  a = unit(a); b = unit(b)
  const v = cross(a, b), c = dot(a, b)
  if (Math.hypot(...v) < 1e-9) {
    if (c > 0) return I3
    const ax = unit(cross(a, Math.abs(a[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0]))
    return [0, 1, 2].map((i) => [0, 1, 2].map((j) => 2 * ax[i] * ax[j] - (i === j ? 1 : 0)))
  }
  const K = [[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]
  const K2 = mm(K, K), k = 1 / (1 + c)
  return [0, 1, 2].map((i) => [0, 1, 2].map((j) => (i === j ? 1 : 0) + K[i][j] + K2[i][j] * k))
}
function rotAxis(axis, deg) {
  const a = unit(axis), t = deg * D2R, s = Math.sin(t), c = Math.cos(t)
  const K = [[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]
  const K2 = mm(K, K)
  return [0, 1, 2].map((i) => [0, 1, 2].map((j) => (i === j ? 1 : 0) + s * K[i][j] + (1 - c) * K2[i][j]))
}
function eulerFromMat(R) { // ZYX (R = Rz·Ry·Rx)
  const sy = Math.max(-1, Math.min(1, -R[2][0])), ry = Math.asin(sy)
  let rx, rz
  if (Math.abs(sy) < 0.99999) { rx = Math.atan2(R[2][1], R[2][2]); rz = Math.atan2(R[1][0], R[0][0]) } else { rx = Math.atan2(-R[1][2], R[1][1]); rz = 0 }
  return [rx / D2R, ry / D2R, rz / D2R].map((v) => Math.round(v * 1e4) / 1e4 + 0)
}
function quat(R) { // 회전행렬 → {x,y,z,w}
  const t = R[0][0] + R[1][1] + R[2][2]
  let w, x, y, z
  if (t > 0) { const s = Math.sqrt(t + 1) * 2; w = s / 4; x = (R[2][1] - R[1][2]) / s; y = (R[0][2] - R[2][0]) / s; z = (R[1][0] - R[0][1]) / s }
  else if (R[0][0] > R[1][1] && R[0][0] > R[2][2]) { const s = Math.sqrt(1 + R[0][0] - R[1][1] - R[2][2]) * 2; w = (R[2][1] - R[1][2]) / s; x = s / 4; y = (R[0][1] + R[1][0]) / s; z = (R[0][2] + R[2][0]) / s }
  else if (R[1][1] > R[2][2]) { const s = Math.sqrt(1 + R[1][1] - R[0][0] - R[2][2]) * 2; w = (R[0][2] - R[2][0]) / s; x = (R[0][1] + R[1][0]) / s; y = s / 4; z = (R[1][2] + R[2][1]) / s }
  else { const s = Math.sqrt(1 + R[2][2] - R[0][0] - R[1][1]) * 2; w = (R[1][0] - R[0][1]) / s; x = (R[0][2] + R[2][0]) / s; y = (R[1][2] + R[2][1]) / s; z = s / 4 }
  return { x, y, z, w }
}
const findConn = (conn, name, id) => {
  const c = conn[name]
  if (!c) return null
  for (const k of ['pegs', 'holes']) {
    const x = (c[k] || []).find((q) => q.id === id)
    if (x) return { kind: k === 'pegs' ? 'peg' : 'hole', c: x }
  }
  return null
}

// 한 연결(내 연결점 → 받는 쪽 연결점)을 만족하는 자세 후보
function candidateFor(M, conn, name, join, host, roll, side) {
  const mine = findConn(conn, name, join.mine)
  const theirs = findConn(conn, host.n, join.theirs)
  if (!mine || !theirs) return null
  const Rh = M.matFromEuler(host.r || [0, 0, 0])
  const tpos = add(host.p, mv(Rh, theirs.c.pos))
  const tdir = unit(mv(Rh, theirs.c.dir))
  if (mine.kind === 'peg' && theirs.kind === 'hole') {
    const pdir = mul(tdir, side)
    const Lh = theirs.c.len || 0, Lp = mine.c.len || 0
    const pcenter = add(sub(tpos, mul(pdir, Lh / 2)), mul(pdir, Lp / 2))
    const R = mm(rotAxis(pdir, roll), rotBetween(mine.c.dir, pdir))
    return { R, p: sub(pcenter, mv(R, mine.c.pos)) }
  }
  if (mine.kind === 'hole' && theirs.kind === 'peg') {
    const pdir = tdir
    const Lh = mine.c.len || 0, Lp = theirs.c.len || 0
    const R = mm(rotAxis(pdir, roll), rotBetween(mine.c.dir, pdir))
    const hcenter = add(tpos, mul(pdir, (Lh - Lp) / 2))
    return { R, p: sub(hcenter, mv(R, mine.c.pos)) }
  }
  return null
}

/**
 * @param ctx   { M: IVS_MATES, COL: IVS_COLLISION, conn: {이름: connectors}, dims: {이름: [x,y,z]}, placed: [{key, n, p, r}] }
 * @param spec  { n: 부품 이름, joins: [{ mine: 연결점 id, host: placed 의 key, theirs: 받는 연결점 id }], dirHint?: [x,y,z](조립 데이터의 dir 과 같은 뜻 — 부품을 띄워 두는 방향, 돌기는 그 반대로 향함), sides?: [1,-1], rolls?: [..] }
 * @returns { ok, pose: {p, r}, alternatives, log, tried }
 */
export function autoPlace(ctx, spec) {
  const { M, COL, conn, dims, placed } = ctx
  const log = []
  const joins = spec.joins || []
  if (!joins.length) return { ok: false, log: ['joins 가 비었어요 — 어느 연결점을 어느 부품 구멍에 끼울지 적어 주세요'] }
  const byKey = new Map(placed.map((q) => [q.key, q]))
  // 프레임 구멍은 번호 대신 칸으로 적을 수 있다: theirsGrid: [길이방향 i번째, 폭방향 j번째] (1부터, 프레임 로컬 기준)
  for (const j of joins) {
    if (j.theirs || !j.theirsGrid) continue
    const h = byKey.get(j.host)
    const m = h && String(h.n).match(/^(\d)(\d+)프레임$/)
    if (!m) return { ok: false, log: [`theirsGrid 는 프레임(예: 35프레임)에만 쓸 수 있어요: ${j.host}`] }
    const W = Number(m[1]), L = Number(m[2])
    const x = (j.theirsGrid[0] - 1) * 10 - (L - 1) * 5, z = (j.theirsGrid[1] - 1) * 10 - (W - 1) * 5
    const hole = ((conn[h.n] || {}).holes || []).find((q) => Math.abs(q.pos[0] - x) < 1 && Math.abs(q.pos[2] - z) < 1)
    if (!hole) return { ok: false, log: [`${h.n} 에 길이 ${j.theirsGrid[0]}번째·폭 ${j.theirsGrid[1]}번째 구멍이 없어요`] }
    j.theirs = hole.id
  }
  const first = joins[0]
  const host0 = byKey.get(first.host)
  if (!host0) return { ok: false, log: [`받는 부품 "${first.host}" 이(가) 놓인 부품 목록에 없어요`] }
  const th = findConn(conn, host0.n, first.theirs)
  const Rh = M.matFromEuler(host0.r || [0, 0, 0])
  if (th) log.push(`[공간] 받는 쪽 ${host0.n}(${first.host}) ${first.theirs}: 월드 위치 [${add(host0.p, mv(Rh, th.c.pos)).map(r1)}] · 축 [${unit(mv(Rh, th.c.dir)).map((v) => Math.round(v * 100) / 100)}]`)
  const sides = spec.sides || (th && th.kind === 'hole' && th.c.through ? [1, -1] : [1])
  const rolls = spec.rolls || [0, 90, 180, 270]
  const cands = []
  for (const side of sides) {
    for (const roll of rolls) {
      const cand = candidateFor(M, conn, spec.n, first, host0, roll, side)
      if (!cand) return { ok: false, log: [...log, '[오류] 연결점 id 를 DB 연결점에서 못 찾음(부품 이름·id 확인)'] }
      const r = eulerFromMat(cand.R)
      const part = { key: '__new__', n: spec.n, p: cand.p.map((v) => Math.round(v * 1000) / 1000), r }
      const label = `면${side > 0 ? '앞' : '뒤'}·롤${roll}°`
      // 사고 ① 모든 연결이 실제로 들어가는지
      const res = M.check([...placed, part], conn)
      const bad = []
      for (const j of joins) {
        const host = byKey.get(j.host)
        const ok = host && res.mated.some((m) => (m.part === '__new__' && m.into === host.key && m.peg === j.mine && m.hole === j.theirs) || (m.into === '__new__' && m.part === host.key && m.hole === j.mine && m.peg === j.theirs))
        if (!ok) bad.push(`${j.mine}→${j.host}.${j.theirs}`)
      }
      // 사고 ② 겹침
      let overlap = null
      if (COL && dims[spec.n]) {
        const cores = COL.coreBoxes(spec.n, dims[spec.n])
        if (cores) {
          const q = quat(cand.R)
          for (const o of placed) {
            const oc = dims[o.n] ? COL.coreBoxes(o.n, dims[o.n]) : null
            if (!oc) continue
            const oq = quat(M.matFromEuler(o.r || [0, 0, 0]))
            if (COL.boxesOverlap(cores, { x: part.p[0], y: part.p[1], z: part.p[2] }, q, oc, { x: o.p[0], y: o.p[1], z: o.p[2] }, oq, 0.6)) { overlap = `${o.n}(${o.key})`; break }
          }
        }
      }
      // 사고 ③ 끼우는 방향
      let dirScore = 0
      let dirBad = false
      if (spec.dirHint) {
        const w = M.worldConnectors(part, conn[spec.n] || {})
        const used = joins.map((j) => w.pegs.find((q) => q.id === j.mine)).filter(Boolean)
        if (used.length) { dirScore = Math.min(...used.map((q) => -dot(unit(q.dir), unit(spec.dirHint)))); dirBad = dirScore < 0.9 }
      }
      const score = -100 * bad.length + (overlap ? -50 : 0) + (dirBad ? -30 : dirScore)
      const why = bad.length ? `연결 안 됨: ${bad.join(', ')}` : overlap ? `겹침: ${overlap}` : dirBad ? `끼우는 방향 어긋남(내적 ${Math.round(dirScore * 100) / 100})` : '통과'
      log.push(`[판단] ${label} → ${why}`)
      cands.push({ part, score, ok: !bad.length && !overlap && !dirBad, label, why })
    }
  }
  cands.sort((a, b) => b.score - a.score)
  const good = cands.filter((c) => c.ok)
  if (good.length) {
    const best = good[0]
    log.push(`[확정] ${best.label} — 통과한 후보 ${good.length}개 중 1순위${good.length > 1 ? ' (나머지: ' + good.slice(1).map((c) => c.label).join(', ') + ' — 교재 그림과 맞는 쪽을 고를 것)' : ''}`)
    return { ok: true, pose: { p: best.part.p, r: best.part.r }, alternatives: good.slice(1).map((c) => ({ label: c.label, p: c.part.p, r: c.part.r })), log, tried: cands.length }
  }
  log.push(`[오류] 후보 ${cands.length}개 전부 실패 — 가장 가까운 후보 ${cands[0].label}: ${cands[0].why}. joins 의 연결점·받는 구멍 id, dirHint 를 고쳐 다시 돌리세요`)
  return { ok: false, closest: { p: cands[0].part.p, r: cands[0].part.r, why: cands[0].why }, log, tried: cands.length }
}

// 여러 부품을 순서대로 배치(앞에서 확정한 부품이 뒤 부품의 받는 쪽이 된다). 실패하면 그 부품에서 멈추고 로그를 돌려준다.
export function autoAssemble(ctx, plan) {
  const placed = [...ctx.placed]
  const out = []
  const logs = []
  for (let i = 0; i < plan.length; i++) {
    const spec = plan[i]
    const r = autoPlace({ ...ctx, placed }, spec)
    logs.push(`── ${i + 1}/${plan.length} ${spec.n}${spec.key ? ' (' + spec.key + ')' : ''} ──`, ...r.log)
    if (!r.ok) return { ok: false, stoppedAt: i, placed: out, log: logs }
    const key = spec.key || `p${i + 1}`
    placed.push({ key, n: spec.n, p: r.pose.p, r: r.pose.r })
    out.push({ key, n: spec.n, p: r.pose.p, r: r.pose.r, alternatives: r.alternatives })
  }
  return { ok: true, placed: out, log: logs }
}
export { eulerFromMat, rotBetween, rotAxis, mm, mv }

// ── 카메라 자동 선택 ──
// 후보 방향(방위 az × 고도 el)마다 점수: ① 받는 구멍 자리(marks)가 다른 부품에 가려지지 않는 비율 ② 끼우는 방향이 화면에서 잘 보이는지(시선과 끼우는 방향이 30~70°)
// ③ 고도 35~50° 선호 ④ 앞 단계 각도와 크게 튀지 않기(연속성). 교재 그림에서 맞춘 값(fit)이 있으면 그것이 항상 우선이다 — 이 값은 camSrc:'auto'(짐작보다 근거는 있지만 교재와 대조 필요).
function rayHitsObb(o, d, box, t0) { // o + t·d 가 (월드) 상자와 t∈(t0, ∞)에서 만나는가
  const rel = sub(o, box.c)
  let tmin = t0, tmax = 1e9
  for (let k = 0; k < 3; k++) {
    const ax = box.axes[k]
    const e = dot(rel, ax), f = dot(d, ax), h = box.h[k]
    if (Math.abs(f) < 1e-9) { if (Math.abs(e) > h) return false; continue }
    let t1 = (-h - e) / f, t2 = (h - e) / f
    if (t1 > t2) { const s = t1; t1 = t2; t2 = s }
    tmin = Math.max(tmin, t1); tmax = Math.min(tmax, t2)
    if (tmin > tmax) return false
  }
  return true
}
export function autoCamera(ctx, info, prev) {
  const { M, COL, dims } = ctx
  const placed = ctx.placed || []
  const marks = (info.marks || []).filter(Boolean)
  const dir = info.dir ? unit(info.dir) : null
  const boxes = []
  if (COL) {
    placed.forEach((o) => {
      const cores = dims[o.n] ? COL.coreBoxes(o.n, dims[o.n]) : null
      if (!cores) return
      const q = quat(M.matFromEuler(o.r || [0, 0, 0]))
      cores.forEach((b) => boxes.push({ key: o.key, ...COL.worldBox(b, { x: o.p[0], y: o.p[1], z: o.p[2] }, q) }))
    })
  }
  const focus = info.focus && info.focus.length ? info.focus : marks
  let best = null
  for (let az = 0; az < 360; az += 15) {
    for (let el = 25; el <= 65; el += 5) {
      const a = az * D2R, e = el * D2R
      const toCam = [Math.sin(a) * Math.cos(e), Math.sin(e), Math.cos(a) * Math.cos(e)]
      let vis = 1
      if (marks.length && boxes.length) {
        let seen = 0
        marks.forEach((m) => { const o = dir ? add(m, mul(dir, 6)) : m; if (!boxes.some((bx) => rayHitsObb(o, toCam, bx, 0.5))) seen++ })
        vis = seen / marks.length
      }
      let dirTerm = 0.5
      if (dir) { const c = Math.abs(dot(toCam, dir)); const ang = Math.acos(Math.min(1, c)) / D2R; dirTerm = ang >= 25 && ang <= 75 ? 1 : Math.max(0, 1 - Math.min(Math.abs(ang - 25), Math.abs(ang - 75)) / 40) }
      const elTerm = el >= 35 && el <= 50 ? 1 : 0.6
      let cont = 1
      if (prev) { let d = Math.abs(az - prev.az) % 360; if (d > 180) d = 360 - d; cont = 1 - Math.min(1, d / 180) * 0.7 - Math.min(1, Math.abs(el - prev.el) / 40) * 0.3 }
      const score = vis * 3 + dirTerm * 1.2 + elTerm * 0.5 + cont * (prev ? 1.5 : 0)
      if (!best || score > best.score) best = { az, el, score, vis, dirTerm, cont }
    }
  }
  return { theta: Math.round(best.az * D2R * 1000) / 1000, phi: Math.round((90 - best.el) * D2R * 1000) / 1000, az: best.az, el: best.el, visible: Math.round(best.vis * 100) + '%', camSrc: 'auto', note: `카메라 자동 선택: 방위 ${best.az}° · 고도 ${best.el}° (받는 구멍 ${Math.round(best.vis * 100)}% 보임)` }
}

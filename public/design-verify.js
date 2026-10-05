// 조립 데이터 "단계별 검증 절차" — 사람이 단계마다 하던 확인을 자동으로 한다 (화면과 validate_assembly 가 같은 코드를 쓴다).
//   1) 위치가 옮겨질 때마다 끼우는 방향부터 확인(돌기가 향한 방향 = 끼우는 방향 dir, 받는 쪽 구멍 축과 평행)
//   2) 그 방향 기준으로 받는 구멍이 몇 번째 칸인지(양쪽 끝에서 센 번호) 목록으로 보여 준다 — 교재 그림과 하나씩 대조용
//   3) 단계가 끝나면 앞 단계·뒤 단계와 비교: 새로 생긴 부품·연결된 기존 부품, 같은 자리 중복, 바닥 기준, 부품 개수(교재 LIST)
//   4) 카메라가 단계마다 지정됐는지, 교재에서 맞춘 값인지 짐작한 값인지(step.camSrc: 'fit' | 'guess' | 'user')
// 사용: IVS_VERIFY.verify(def, conn, dims, { list: { 부품이름: 개수 } }) → { issues: [...], report: [...] }
(function () {
  const M = () => window.IVS_MATES
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
  const mul3 = (a, k) => [a[0] * k, a[1] * k, a[2] * k]
  const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l] }
  const axisName = (v) => {
    const n = [['+x', [1, 0, 0]], ['−x', [-1, 0, 0]], ['+y(위)', [0, 1, 0]], ['−y(아래)', [0, -1, 0]], ['+z', [0, 0, 1]], ['−z', [0, 0, -1]]]
    let best = n[0], bd = -2
    n.forEach((c) => { const d = dot(norm(v), c[1]); if (d > bd) { bd = d; best = c } })
    return bd > 0.97 ? best[0] : `(${v.map((x) => Math.round(x * 100) / 100).join(', ')})`
  }
  // 프레임 구멍 위치 → "길이방향 i번째(반대쪽에서 n번째) · 폭방향 j번째(반대쪽에서 m번째)"
  function holeLabel(name, localPos) {
    const m = String(name).match(/^(\d)(\d+)프레임$/)
    if (!m) return null
    const W = Number(m[1]), L = Number(m[2])
    const i = Math.round((localPos[0] + (L - 1) * 5) / 10) + 1
    const j = Math.round((localPos[2] + (W - 1) * 5) / 10) + 1
    if (i < 1 || i > L || j < 1 || j > W) return null
    return `길이방향 ${i}번째(반대쪽 ${L - i + 1}번째)·폭방향 ${j}번째(반대쪽 ${W - j + 1}번째)`
  }
  function obbMinY(pt, dims, xf) {
    if (!dims) return null
    const R = M().matFromEuler(pt.r || [0, 0, 0])
    const h = dims.map((d) => d / 2)
    let c = pt.p.slice()
    let Rm = R
    if (xf) {
      const mv = (m, v) => [0, 1, 2].map((i) => m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2])
      const w = mv(xf.m, c); c = [w[0] + xf.t[0], w[1] + xf.t[1], w[2] + xf.t[2]]
      Rm = [0, 1, 2].map((i) => [0, 1, 2].map((j) => xf.m[i][0] * R[0][j] + xf.m[i][1] * R[1][j] + xf.m[i][2] * R[2][j]))
    }
    // 몸통 상자의 월드 y 반폭 = Σ|R[1][k]|·h[k]
    let hy = Math.abs(Rm[1][0]) * h[0] + Math.abs(Rm[1][1]) * h[1] + Math.abs(Rm[1][2]) * h[2]
    // 바퀴는 원판이다(허브 축 = 모델 y): 기울어도 상자 모서리가 아니라 원 둘레가 바닥에 닿는다 — 상자로 보면 기운 바퀴가 바닥 아래로 잘못 나온다
    if (/바퀴/.test(String(pt.n || ''))) { const ay = Math.abs(Rm[1][1]); hy = h[0] * Math.sqrt(Math.max(0, 1 - ay * ay)) + h[1] * ay }
    return { min: c[1] - hy, max: c[1] + hy }
  }

  function verify(def, conn, dims, opt) {
    opt = opt || {}
    const issues = [], report = []
    const steps = def.steps || []
    const mates = M()
    const worldOf = (pt) => (conn[pt.n] ? mates.worldConnectors({ p: pt.p, r: pt.r || [0, 0, 0] }, conn[pt.n]) : null)
    const all = []
    steps.forEach((st, k) => (st.parts || []).forEach((pt, i) => all.push({ key: `${k + 1}.${i} ${pt.n}`, n: pt.n, p: pt.p, r: pt.r || [0, 0, 0], ref: pt, step: k + 1, idx: i })))
    let byKey = new Map(all.map((a) => [a.key, a]))
    // move{at,p|by,r}: 그 단계부터는 옮긴 자세로 검사한다
    const poseNow = (pt, stp) => (pt.move && stp >= pt.move.at ? { p: pt.move.p || pt.p.map((x, q) => x + (pt.move.by || [0, 0, 0])[q]), r: pt.move.r || pt.r || [0, 0, 0] } : { p: pt.p, r: pt.r || [0, 0, 0] })

    // ── 단계별: 방향 확인 → 구멍 위치 목록 → 앞뒤 비교 ──
    const counts = {}
    steps.forEach((st, k) => {
      const si = k + 1
      const upto = all.filter((a) => a.step <= si).map((a) => ({ ...a, ...poseNow(a.ref, si) }))
      byKey = new Map(upto.map((a) => [a.key, a]))
      const res = mates.check(upto, conn)
      const mine = upto.filter((a) => a.step === si)
      const added = {}
      mine.forEach((a) => { added[a.n] = (added[a.n] || 0) + 1; counts[a.n] = (counts[a.n] || 0) + 1 })
      const addTxt = Object.keys(added).map((n) => `${n} ${added[n]}`).join(', ') || '(부품 없음 — 합치기/옮기기 단계)'
      const lines = [`${si}단계 · 추가: ${addTxt}`]
      const hosts = new Set()
      mine.forEach((a) => {
        const pt = a.ref
        const eff = pt.side || pt.move || pt.explode ? null : pt.dir // 옆자리·옮기기 단계는 방향 검사 제외
        const myPegs = res.mated.filter((m) => m.part === a.key)
        const myHoles = res.mated.filter((m) => m.into === a.key)
        // 1) 방향 확인: dir 은 부품을 띄워 두는 방향이라 돌기는 그 반대(−dir)로 향해야 한다 / 받는 쪽(recv)이면 고정된 돌기가 +dir 쪽을 향해야 한다
        if (eff && conn[a.n]) {
          const d = norm(eff)
          const w = worldOf(a)
          // 끼워 넣는 쪽 돌기 중 하나라도 올바른 방향이면 통과(리벳처럼 양 끝이 서로 다른 부품에 들어가는 부품은 앞 단계 쪽 돌기도 함께 잡히므로 "전부"가 아니라 "하나 이상")
          if (!pt.recv && myPegs.length) {
            const okAny = myPegs.some((m) => { const peg = w.pegs.find((q) => q.id === m.peg); return peg && dot(norm(peg.dir), d) <= -0.9 })
            if (!okAny) issues.push(`${si}단계 ${a.n}: 띄우는 방향 dir=${axisName(d)} 이면 돌기가 반대(${axisName(mul3(d, -1))})로 향해야 하는데 연결된 돌기(${myPegs.map((m) => m.peg).join(', ')})가 모두 다른 쪽을 향함(방향 어긋남)`)
          }
          if (pt.recv && myHoles.length) {
            const okAny = myHoles.some((m) => { const host = byKey.get(m.part); const hw = host && worldOf(host); const peg = hw && hw.pegs.find((q) => q.id === m.peg); return peg && (dot(norm(peg.dir), d) >= 0.9 || (peg.len >= 30 && dot(norm(peg.dir), d) <= -0.9)) }) // 축처럼 긴 돌기는 양 끝 어느 쪽에서도 끼운다(안쪽 부시)
            if (!okAny) issues.push(`${si}단계 ${a.n}: 띄우는 방향 dir=${axisName(d)} 이면 고정된 돌기가 ${axisName(d)} 쪽을 향해야 하는데 연결된 돌기가 모두 다른 쪽을 향함(방향 어긋남)`)
          }
        }
        // 2) 구멍 위치 목록 (받는 쪽 기준)
        const pairs = myPegs.map((m) => ({ from: a, to: byKey.get(m.into), hole: m.hole, peg: m.peg }))
          .concat(myHoles.map((m) => ({ from: byKey.get(m.part), to: a, hole: m.hole, peg: m.peg })))
        const seen = new Set()
        pairs.forEach((p) => {
          if (!p.to || !p.from) return
          const hw = worldOf(p.to); const hh = hw && hw.holes.find((q) => q.id === p.hole)
          const lh = conn[p.to.n] && conn[p.to.n].holes.find((q) => q.id === p.hole)
          const lab = lh ? holeLabel(p.to.n, lh.pos) : null
          const keyp = `${p.from.key}>${p.to.key}>${p.hole}`
          if (seen.has(keyp)) return; seen.add(keyp)
          hosts.add(p.from === a ? p.to.key : p.from.key)
          lines.push(`   · ${p.from.n}(${p.from.key.split(' ')[0]}) ${p.peg} → ${p.to.n}(${p.to.key.split(' ')[0]}) ${p.hole}${lab ? ' = ' + lab : ''}${hh ? ' · 구멍 축 ' + axisName(hh.dir) : ''}`)
        })
      })
      // 3) 앞뒤 비교: 같은 자리 중복
      for (let i = 0; i < mine.length; i++) for (let j = i + 1; j < mine.length; j++) {
        const a = mine[i], b = mine[j]
        if (a.n === b.n && Math.hypot(...sub(a.p, b.p)) < 0.5 && JSON.stringify(a.r) === JSON.stringify(b.r)) issues.push(`${si}단계: ${a.n} 이 같은 자리에 두 번 놓임`)
      }
      const prevSet = all.filter((a) => a.step < si)
      mine.forEach((a) => {
        const dup = prevSet.find((b) => b.n === a.n && Math.hypot(...sub(a.p, b.p)) < 0.5 && JSON.stringify(b.r) === JSON.stringify(a.r))
        if (dup) issues.push(`${si}단계: ${a.n} 이 ${dup.step}단계 부품과 같은 자리(중복)`)
      })
      if (hosts.size) lines.push(`   → 이번 단계가 붙은 기존 부품: ${[...hosts].map((h) => h.replace(/^\d+\.\d+ /, '') + '(' + h.split('.')[0] + '단계)').join(', ')}`)
      // 4) 카메라
      const cs = st.camSrc || (st.cam || st.view ? '지정' : '미지정')
      // 안내 화살표: 앞 단계에 있던 부품과 결합하는 새 부품(옆자리에서 합쳐지거나 옮겨 붙는 부품 포함)은 그 단계의 안내점이 있어야 한다.
      // 화면의 "끌면 화살표가 따라가는" 기능이 이 값(marks / 합칠 땐 settleMarks / 옮길 땐 move.marks)을 읽는다 — 토끼(검토 완료)는 리벳까지 전부 있었다.
      {
        const arriving = all.filter((a) => { const q = a.ref; return (a.step === si && !q.side) || (q.side && q.side.until === si) || (q.move && q.move.at === si) })
        const arrSet = new Set(arriving.map((a) => a.key))
        const prior = new Set(all.filter((a) => a.step < si).map((a) => a.key))
        const outside = (k) => prior.has(k) && !arrSet.has(k) // 같이 합쳐지는 묶음 안의 결합은 뺀다
        const lack = arriving.filter((a) => {
          const q = a.ref
          if (q.noGuide) return false // 우연히 맞닿아 보일 뿐 결합이 아닌 부품(안내 화살표 없음)
          if (!res.mated.some((m) => (m.part === a.key && outside(m.into)) || (m.into === a.key && outside(m.part)))) return false
          const got = q.move && q.move.at === si ? (q.move.marks || []) : q.side && q.side.until === si ? (q.settleMarks || []) : (q.marks || [])
          return !got.length
        })
        if (lack.length) { const nm = {}; lack.forEach((a) => { nm[a.n] = (nm[a.n] || 0) + 1 }); issues.push(`${si}단계: 안내 화살표(marks)가 없는 부품 ${lack.length}개 — ${Object.keys(nm).map((n) => n + ' ' + nm[n]).join(', ')}`) }
      }
      if (!st.cam && !st.view && si > 1) issues.push(`${si}단계: 카메라 각도(cam) 미지정 — 교재 그림과 같은 방향으로 지정할 것`)
      lines.push(`   카메라: ${st.cam ? `theta ${Math.round(st.cam.theta * 57.3)}° / phi ${Math.round(st.cam.phi * 57.3)}°` : '기본'} (${cs})`)
      report.push(...lines)
    })

    // ── 전체: 바닥 기준 ── 각 단계 구간(뒤집기 단계 범위/그 밖)의 마지막 단계에서, 그 구간이 보여 주는 방향으로 가장 낮은 부품이 바닥(y=0)에 닿는지 본다
    const flipR = (def.flip && def.flip.ranges) || []
    const segEnds = []
    if (!flipR.length) segEnds.push({ end: steps.length, flip: false })
    else {
      const marks = new Set(); flipR.forEach((r) => { marks.add(r[0]); marks.add(r[1] + 1) }); marks.add(1); marks.add(steps.length + 1)
      const ms = [...marks].filter((x) => x >= 1 && x <= steps.length + 1).sort((x, y) => x - y)
      for (let i = 0; i < ms.length - 1; i++) { const st = ms[i], en = ms[i + 1] - 1; segEnds.push({ end: en, flip: flipR.some((r) => st >= r[0] && en <= r[1]), start: st }) }
    }
    const poseAt = (pt, step) => { // 그 단계에서 실제로 놓인 자리(옆자리·옮기기 반영)
      if (pt.side && step < pt.side.until) return { p: pt.side.p, r: pt.side.r }
      if (pt.move && step >= pt.move.at) return { p: pt.move.p || [pt.p[0] + pt.move.by[0], pt.p[1] + pt.move.by[1], pt.p[2] + pt.move.by[2]], r: pt.move.r || pt.r }
      return { p: pt.p, r: pt.r }
    }
    const flipPose = (po, end) => { const f = def.flip; const rg = (f.ranges || []).find((r) => end >= r[0] && end <= r[1]); const fy = rg && rg[2] != null ? rg[2] : f.y; const R = M().matFromEuler(po.r || [0, 0, 0]); const R2 = [R[0], [-R[1][0], -R[1][1], -R[1][2]], [-R[2][0], -R[2][1], -R[2][2]]]
      const sy = Math.max(-1, Math.min(1, -R2[2][0])), ry = Math.asin(sy); let rx, rz
      if (Math.abs(sy) < 0.99999) { rx = Math.atan2(R2[2][1], R2[2][2]); rz = Math.atan2(R2[1][0], R2[0][0]) } else { rx = Math.atan2(-R2[1][2], R2[1][1]); rz = 0 }
      return { p: [po.p[0], fy - po.p[1], f.z - po.p[2]], r: [rx * 57.29578, ry * 57.29578, rz * 57.29578] } }
    segEnds.forEach((sg) => {
      let lo = 1e9, loPart = '', hi = -1e9
      all.filter((a) => a.step <= sg.end).forEach((a) => {
        const d = dims[a.n]; if (!d || /도 프레임$/.test(a.n)) return // 꺾인 프레임은 상자 근사가 실제보다 커서 바닥 검사에서 뺀다
        let po = poseAt(a.ref, sg.end)
        if (sg.flip && !a.ref.noflip) po = flipPose(po, sg.end)
        const xf = def.xform && sg.end >= def.xform.at ? def.xform : null
        const bx = obbMinY({ n: a.n, p: po.p, r: po.r }, d, xf)
        if (bx) { if (bx.min < lo) { lo = bx.min; loPart = a.key } if (bx.max > hi) hi = bx.max }
      })
      if (lo > 1e8) return
      const tag = `${sg.start ? sg.start : 1}~${sg.end}단계${sg.flip ? '(뒤집은 방향)' : ''}`
      report.push(`바닥 기준 ${tag}: 가장 낮은 부품 바닥 y=${Math.round(lo * 10) / 10} (${loPart}), 가장 높은 곳 y=${Math.round(hi * 10) / 10}`)
      if (lo < -1) issues.push(`바닥 기준 ${tag}: ${loPart} 이 바닥(y=0) 아래로 ${Math.round(-lo * 10) / 10}mm 내려가 있음 — 그 방향에서 가장 낮은 부품이 y=0이 되게 맞출 것`)
    })

    // ── 전체: 리벳이 끼운 부품 반대쪽으로 튀어나오지 않는가(결합 후) ──
    {
      const fin = all.map((a) => ({ ...a, ...poseNow(a.ref, 1e9) }))
      const finRes = mates.check(fin, conn)
      const wo = (a) => (conn[a.n] ? mates.worldConnectors({ p: a.p, r: a.r }, conn[a.n]) : null)
      const byK = new Map(fin.map((a) => [a.key, a]))
      const seenR = new Set()
      const cnt = {}; finRes.mated.forEach((m) => { cnt[m.part + m.peg] = (cnt[m.part + m.peg] || 0) + 1 })
      finRes.mated.forEach((m) => {
        if (cnt[m.part + m.peg] > 1) return // 한 돌기가 겹친 두 구멍에 같이 걸리면(프레임+블록) 판정 생략
        const a = byK.get(m.part), b = byK.get(m.into)
        if (!a || !b || a.n !== '리벳' || seenR.has(m.part + m.peg + m.hole)) return
        seenR.add(m.part + m.peg + m.hole)
        const pg = wo(a).pegs.find((q) => q.id === m.peg), hl = wo(b).holes.find((q) => q.id === m.hole)
        if (!pg || !hl) return
        const ax = norm(hl.dir)
        const sgn = dot(norm(pg.dir), ax) > 0 ? 1 : -1       // 돌기가 구멍 축 +방향으로 들어가는가
        const rel = sub(pg.pos, hl.pos), along = dot(rel, ax) * sgn
        const tip = along + (pg.len || 0) / 2, half = (hl.len || 0) / 2
        if (tip - half > 0.6) issues.push(`리벳 ${a.key} 끝이 ${b.n}(${b.key}) 구멍 반대쪽 면 밖으로 ${Math.round((tip - half) * 10) / 10}mm 튀어나옴 — 결합 후 프레임 두께 안에 들어가야 함`)
      })
    }
    // ── 전체: 교재 부품 LIST 대조 ──
    if (opt.list) {
      const diffs = []
      const names = new Set([...Object.keys(opt.list), ...Object.keys(counts)])
      names.forEach((n) => { const a = counts[n] || 0, b = opt.list[n] || 0; if (a !== b) diffs.push(`${n}: 조립도 ${a}개 / 교재 ${b}개`) })
      const mult = def.listNote ? ` (${def.listNote})` : ''
      report.push(diffs.length ? `교재 부품 LIST 대조: 불일치 ${diffs.length}종${mult} — ${diffs.join(', ')}` : '교재 부품 LIST 대조: 전부 일치')
      if (diffs.length && !def.listNote) issues.push(`교재 부품 LIST 와 개수 불일치 ${diffs.length}종: ${diffs.join(', ')} (의도적이면 def.listNote 에 이유를 적을 것)`)
    }
    // ── 카메라 출처 요약 ──
    const guess = steps.filter((s) => s.camSrc === 'guess').length, fit = steps.filter((s) => s.camSrc === 'fit').length, user = steps.filter((s) => s.camSrc === 'user').length
    report.push(`카메라 출처: 교재에서 맞춤 ${fit} · 사용자 확인 ${user} · 짐작 ${guess} · 표시 없음 ${steps.length - fit - user - guess} (짐작/표시 없음 단계는 교재 그림으로 다시 맞출 것)`)
    return { issues, report, counts }
  }
  window.IVS_VERIFY = { verify, holeLabel }
})()

// 단계 직전의 상태를 계산한다 (MCP get_step_context 의 계산 부분).
// 사용자 설명(2026-10-03): 조립은 순서대로만 쌓인다 → 단계 k 에서 ① 어떤 부품을 이미 썼는지 ② 교재 부품 목록(LIST)에서 뭐가 남았는지
// ③ 어떤 구멍·돌기가 이미 찼는지를 알고 있다. 앞이 틀리지 않았다면 이번 초록 원은 "빈 구멍"에만 있을 수 있고,
// 새 부품이 들어왔다면 그 돌기 수만큼의 빈 구멍이 같은 간격으로 나란히 있는 자리에만 들어간다.
// 그래서 교재 그림에서 구멍을 일일이 세지 않고, 부품 양 끝 사이 비율로 후보 중 하나만 고르면 된다.

const r1 = (v) => Math.round(v * 10) / 10

// 조립 데이터의 부품을 "제자리" 배치로 모은다(validate_assembly 와 같은 규칙).
function finalPose(pt) {
  const moved = pt.move && (pt.move.p || pt.move.by)
  const p = moved ? (pt.move.p || pt.p.map((x, q) => x + pt.move.by[q])) : pt.p
  const r = (pt.move && pt.move.r) || pt.r || [0, 0, 0]
  return { p, r }
}

// 꽉 찬/빈 번호를 사람이 읽기 좋게 줄인다: ["열1·줄1", "열2·줄1", …] → "열1~13·줄1" 처럼 묶는 대신, 더 적은 쪽만 나열한다.
function pickShort(free, used) {
  if (!used.length) return '전부 비어 있음'
  if (!free.length) return '전부 찼음'
  return used.length <= free.length
    ? '찬 곳: ' + used.join(', ')
    : '빈 곳: ' + free.join(', ')
}

export function stepContext({ steps, step, conn, F, M, listCounts }) {
  const before = steps.slice(0, step - 1)
  const parts = []
  const seq = {}
  before.forEach((s, si) => (s.parts || []).forEach((pt, k) => {
    const pose = finalPose(pt)
    seq[pt.n] = (seq[pt.n] || 0) + 1
    parts.push({ key: si + 1 + '단계 ' + pt.n + '#' + k, n: pt.n, p: pose.p, r: pose.r, no: seq[pt.n], step: si + 1 })
  }))
  // 전체 개수(번호 앞에 붙는 총개수 계산은 필요 없다 — 번호는 부품 이름 안의 n번째)
  const used = {}
  parts.forEach((q) => { used[q.n] = (used[q.n] || 0) + 1 })
  const remaining = {}
  if (listCounts) Object.keys(listCounts).forEach((n) => { const left = listCounts[n] - (used[n] || 0); if (left !== 0) remaining[n] = left })
  const lines = []
  lines.push('■ ' + step + '단계 직전 상태 (앞 ' + (step - 1) + '단계까지 부품 ' + parts.length + '개)')
  // ① 이미 쓴 부품 ② 남은 부품
  lines.push('이미 쓴 부품: ' + (Object.keys(used).length ? Object.entries(used).map(([n, c]) => n + ' ' + c).join(', ') : '(없음 — 첫 단계)'))
  if (listCounts) {
    const rem = Object.entries(remaining).filter(([, c]) => c > 0).map(([n, c]) => n + ' ' + c)
    const over = Object.entries(remaining).filter(([, c]) => c < 0).map(([n, c]) => n + ' ' + -c + '개 초과')
    lines.push('교재 부품 목록에서 남은 부품(이번 단계부터 들어올 부품): ' + (rem.length ? rem.join(', ') : '(없음 — 다 썼다)'))
    if (over.length) lines.push('⚠ 목록보다 많이 쓴 부품: ' + over.join(', ') + ' — 앞 단계에서 틀린 곳이 있는지 먼저 본다')
  } else lines.push('(교재 부품 목록(LIST)을 못 읽어 남은 부품은 계산 못 함)')

  // ③ 찬 구멍·돌기
  const res = M.check(parts, conn)
  const occHole = new Set(), occPeg = new Set()
  res.mated.forEach((m) => { occHole.add(m.into + ':' + m.hole); occPeg.add(m.part + ':' + m.peg) })
  lines.push('')
  lines.push('부품별 빈 구멍·빈 돌기 (찬 곳은 앞 단계에서 이미 끼운 곳):')
  let shown = 0
  parts.forEach((q) => {
    const c = conn[q.n]
    if (!c) return
    const rec = F.describe({ n: q.n, p: q.p, r: q.r }, c, q.no)
    const ents = []
    rec.faces.forEach((f) => {
      const free = [], usedL = []
      f.items.forEach((it) => {
        const taken = f.kind === '홀' ? occHole.has(q.key + ':' + it.id) : occPeg.has(q.key + ':' + it.id)
        ;(taken ? usedL : free).push(it.label)
      })
      if (!free.length) return
      ents.push({ f, free, usedL, sig: f.kind + '|' + f.부품축.slice(1) + '|' + free.join(',') + '|' + usedL.join(',') })
    })
    // 관통 구멍은 위·아래 두 면에 똑같이 나오므로 같은 내용이면 한 줄로 합친다
    const out = [], seen = new Set()
    ents.forEach((e) => {
      if (seen.has(e.sig) && e.f.kind === '홀') return
      seen.add(e.sig)
      const twin = e.f.kind === '홀' && ents.some((o) => o !== e && o.sig === e.sig)
      const face = twin ? e.f.key.replace(/ [+-]/, ' ±') + ' (양면 같음)' : e.f.key + ' (' + e.f.월드방향 + ' 쪽)'
      out.push('   ' + face + ': 총 ' + e.f.items.length + '개 · 빈 ' + e.free.length + '개 — ' + pickShort(e.free, e.usedL))
    })
    if (out.length) { shown++; lines.push('· ' + rec.name + ' (' + q.step + '단계에 놓음)'); lines.push(...out) }
  })
  if (!shown) lines.push('(빈 구멍·돌기가 있는 부품이 없음)')

  // ④ 이번 단계 데이터에 들어 있는 것(검토할 때): 새 부품과 그 결합
  const thisStep = steps[step - 1]
  if (thisStep) {
    const newOnes = (thisStep.parts || []).map((pt) => pt.n)
    const counts = {}; newOnes.forEach((n) => { counts[n] = (counts[n] || 0) + 1 })
    lines.push('')
    lines.push('이 단계 조립 데이터의 새 부품: ' + (newOnes.length ? Object.entries(counts).map(([n, c]) => n + ' ' + c).join(', ') : '(없음 — 기존 부품끼리 결합·옮김 단계)'))
    // 이 단계 부품을 놓은 뒤의 결합 중 이 단계 부품이 낀 것
    const after = []
    const seq2 = {}
    steps.slice(0, step).forEach((s, si) => (s.parts || []).forEach((pt, k) => {
      const pose = finalPose(pt); seq2[pt.n] = (seq2[pt.n] || 0) + 1
      after.push({ key: si + 1 + '단계 ' + pt.n + '#' + k, n: pt.n, p: pose.p, r: pose.r, no: seq2[pt.n], step: si + 1 })
    }))
    const res2 = M.check(after, conn)
    const recOf = new Map(after.map((q) => [q.key, conn[q.n] ? F.describe({ n: q.n, p: q.p, r: q.r }, conn[q.n], q.no) : null]))
    const world = new Map(after.map((q) => [q.key, conn[q.n] ? F.worldConnectors({ n: q.n, p: q.p, r: q.r }, conn[q.n]) : null]))
    const mine = res2.mated.filter((m) => m.part.startsWith(step + '단계 ') || m.into.startsWith(step + '단계 '))
    if (mine.length) {
      lines.push('이 단계에서 생긴 결합 ' + mine.length + '건:')
      mine.forEach((m) => {
        const wp = world.get(m.part), wh = world.get(m.into)
        const peg = wp && wp.pegs.find((x) => x.id === m.peg), hole = wh && wh.holes.find((x) => x.id === m.hole)
        const a = recOf.get(m.part), b = recOf.get(m.into)
        if (peg && hole && a && b) lines.push('   ' + a.name + ' ' + F.nameWorldItem(a, peg) + '  →  ' + b.name + ' ' + F.nameWorldItem(b, hole, peg.dir))
      })
    } else lines.push('이 단계 부품이 낀 결합이 없음(떠 있거나 옮김 단계) — 검토 필요')
  } else {
    lines.push('')
    lines.push('(이 단계는 아직 조립 데이터에 없음 — 새로 만들 단계)')
  }

  // ⑤ 읽는 방법
  lines.push('')
  lines.push('── 교재 그림 읽는 법 (사용자 지시 2026-10-03) ──')
  lines.push('· 앞 단계가 맞다면 이번 초록 원이 있을 수 있는 곳은 위의 "빈 구멍"뿐이다. 구멍을 일일이 세지 말고, 원이 받는 부품의 양 끝(경계) 사이에서 어디쯤인지(예: 정가운데 = 5칸 중 3번째)만 본다.')
  lines.push('· 새 부품이 들어왔다면 이유가 있다: 그 부품의 돌기 수만큼 빈 구멍이 같은 간격으로 나란히 있는 자리에만 들어간다(3단블록은 양 끝 돌기 2개 = 20mm 간격 빈 구멍 2곳). 새 부품이 없으면 기존 조립품끼리 결합하는 단계다.')
  lines.push('· 방향이 바뀌어 헷갈리면 완성 전체샷과 다음 단계 그림으로 거꾸로 유추한다. 앞에서 틀린 곳이 나오면 거기서 멈추고 고친다.')
  return { text: lines.join('\n'), used, remaining, freeShown: shown }
}

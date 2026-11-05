// 큐보 부품 크기 [x, y, z] mm — 원본은 부품 DB 의 상세내역(ivs_part_catalog.data.detail 의 크기_mm)이다. 이 파일에 숫자를 따로 적지 않는다.
// (옛 cubo-assembly-guide.js 에서 옮겨 왔다 — 안내서 글은 규칙 파일(큐보 부품결합규칙.md)과 DB 상세내역으로 정리하고 이 계산 함수만 남겼다.)
export function detailDims(detail) {
  const s = detail && detail['크기_mm']
  if (!s) return null
  const d = [s['가로(x)'], s['높이(y)'], s['세로(z)']]
  return d.every(Number.isFinite) ? d : null
}
// rows: [{ name, detail }] (같은 이름이 여러 행이면 상세내역이 있는 행을 쓴다) → { 부품이름: [x, y, z] }
export function dimsMap(rows) {
  const o = {}
  ;(rows || []).forEach((r) => { const d = detailDims(r.detail); if (d && !o[r.name]) o[r.name] = d })
  return o
}

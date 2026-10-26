// 로버트론 부품(에이스랩·로보타미주니어) 테두리 선 색: 부품 색이 어두우면 조금 밝게, 밝으면 조금 어둡게 얇게(0.1mm) 긋는다(사용자 2026-10-27).
export function lineColorFor(hex) {
  const n = parseInt(hex.replace('#', ''), 16), c = [n >> 16, (n >> 8) & 255, n & 255]
  const lum = (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255
  const mix = lum < 0.5 ? c.map((v) => v + (255 - v) * 0.45) : c.map((v) => v * 0.78)
  return '#' + mix.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('')
}
export const LINE_THICKNESS = 0.1

# 조립도 전체 뒤집기 xform 고르기 — 파이썬 도구 공용(JS 쪽 짝: public/design-mates.js 의 IVS_MATES.xformAt, 같은 규칙).
# xform 은 딕셔너리 {at, m, t}(기존) 하나이거나 [{at, m, t}, ...] 목록이다.
# 단계 n 에서 적용할 변환 = at <= n 인 항목 중 at 이 가장 큰 하나(같은 at 이면 목록에서 뒤에 있는 것).
# 그 항목의 m·t 는 "스크립트(뒤집기 전) 좌표 → 화면 좌표" 변환 전체다 — 앞 항목과 합성하지 않고 대체한다(합성된 m·t 는 적는 쪽이 직접 적는다).
# at 이 없는 항목은 어느 단계에도 걸리지 않는다.

def xform_at(meta, n):
    """meta(조립도 meta 딕셔너리, 또는 xform 키를 가진 def/조립도 딕셔너리)의 xform 중 n번 단계에 적용할 항목(없으면 None)."""
    x = (meta or {}).get("xform")
    if not x: return None
    best = None
    for e in (x if isinstance(x, (list, tuple)) else [x]):
        if not e or "at" not in e: continue
        if e["at"] <= n and (best is None or e["at"] >= best["at"]): best = e
    return best

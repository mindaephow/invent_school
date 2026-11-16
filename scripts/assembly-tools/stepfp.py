# 단계 내용 지문(build.py 의 ✓ 단계 보호와 record_check.py 의 비교 증거가 같은 함수를 쓴다).
# 자동으로 다시 계산되는 "━ 작업 점검 ━" 체크 블록(☑/☐)은 뺀다 — 점검 결과가 바뀌어도 내용이 바뀐 것으로 잡히지 않게.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import hashlib, json

def fp(st):
    st = dict(st); st.pop("review", None); st.pop("reviewWhy", None)   # 번호판 색(주황/파랑) 표시용 플래그는 내용이 아니다 — 검증 상태가 바뀔 때마다 증거·✓ 지문이 깨지지 않게 뺀다(2026-10-18)
    st["note"] = str(st.get("note", "")).split("\n━ 작업 점검 ━")[0]
    if any((pt.get("poseAt") or {}) for pt in st.get("parts") or [] if isinstance(pt, dict)):   # 완성(마지막 화면) 전용 자세(poseAt 항목에 "final": true)는 이 번호 모양이 아니다 — 1~N번 증거 지문이 깨지지 않게 뺀다(2026-11-09 로봇팽이 완성)
        st = json.loads(json.dumps(st))
        for pt in st.get("parts") or []:
            pa = pt.get("poseAt") if isinstance(pt, dict) else None
            if pa:
                for k in [k for k, v in pa.items() if isinstance(v, dict) and v.get("final")]: pa.pop(k)
                if not pa: pt.pop("poseAt")
    return hashlib.sha1(json.dumps(st, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


# ── 조립 모양 지문(사용자 2026-11-05: "증거는 조립 모양을 남기려는 것이지 조립 위치를 남기려는 게 아니다") ──
# 조립 전체가 같이 옮겨진 것(예: 1번을 원점 중심으로 옮김)은 모양이 같으므로 증거가 무효가 되지 않는다.
# 절대 좌표 필드(p·marks·faceMarks·settleMarks·holeMarks)에서 1번 첫 부품의 p(기준점)를 빼고 지문을 만든다. 부품 사이 위치·회전·띄움은 그대로 들어가 있어 모양이 바뀌면 지문도 바뀐다.
# 번호 하나만 통째로 옮기면 기준점은 그대로라 지문이 바뀐다(모양이 달라진 것).
_ABS_PT = ("marks", "faceMarks", "settleMarks", "holeMarks")

def anchor(steps):
    try: return [float(v) for v in steps[0]["parts"][0]["p"]]
    except Exception: return [0.0, 0.0, 0.0]

def _incoming(steps, idx):
    """다른 번호의 부품에 적힌 "idx 번 화면에서의 자리"(move.at == idx · poseAt[idx]) — idx 번의 모양이므로 idx 번 지문에 넣는다."""
    out = []
    for j, s_ in enumerate(steps or [], 1):
        for i, p in enumerate(s_.get("parts") or []):
            if not isinstance(p, dict): continue
            mv = p.get("move")
            if isinstance(mv, dict) and str(mv.get("at")) == str(idx): out.append(["%d:%d" % (j, i), "move", mv.get("p"), mv.get("r")])
            po = (p.get("poseAt") or {}).get(str(idx))
            if isinstance(po, dict) and not po.get("final"): out.append(["%d:%d" % (j, i), "poseAt", po.get("p"), po.get("r")])
    return out

def shape_fp(st, anc, idx=None, steps=None):
    """조립 모양 지문. idx(번호)를 주면 "그 번호 화면의 모양"만 남긴다:
      · 이 번호 부품에 적힌 뒤 번호 자리(move.at > idx · poseAt 키 > idx)는 뺀다 — 뒤 번호 때문에 조립을 옮겨도 앞 번호 증거가 깨지지 않는다(2026-11-15 꼬마기사: 9~13번 세트를 원점으로 옮기자 1~8번 증거가 전부 ❌).
      · steps 도 주면 다른 번호 부품이 이 번호 화면에서 갖는 자리(_incoming)를 넣는다 — 빼기만 하면 그 자리를 바꿔도 어느 증거도 안 깨지는 구멍이 생긴다.
    idx 없이 부르면 옛 정의(부품에 적힌 것 전부)다."""
    d = json.loads(json.dumps(st))
    if idx:
        for p in d.get("parts") or []:
            if isinstance(p.get("move"), dict) and str(p["move"].get("at", 0)).isdigit() and int(p["move"]["at"]) > idx: p.pop("move")
            if p.get("poseAt"):
                p["poseAt"] = {k: v for k, v in p["poseAt"].items() if not str(k).isdigit() or int(k) <= idx}
                if not p["poseAt"]: p.pop("poseAt")
    def sub(pt): return [round(float(a) - float(b), 3) for a, b in zip(pt, anc)]
    if idx and steps:
        inc = [[k_, t_, sub(p_) if p_ else p_, r_] for k_, t_, p_, r_ in _incoming(steps, idx)]   # 자리는 기준점(1번 첫 부품)을 뺀 값 — 조립 전체를 같이 옮긴 것은 모양이 같다
        if inc: d["_incoming"] = inc
    for p in d.get("parts") or []:
        if "p" in p: p["p"] = sub(p["p"])
        for k in _ABS_PT:
            if k == "marks" and p.get("side"): continue   # 옆자리(창고 2)로 옮겨 놓은 부품의 안내점은 원점 기준이라 기준점을 빼지 않는다(새 창고는 원점, A4)
            if p.get(k): p[k] = [sub(m) for m in p[k]]
    return fp(d)

def step_index(st, steps):
    """st 가 steps 의 몇 번인가(1부터) — 같은 객체를 먼저 찾고, 없으면 내용이 같은 것."""
    return next((i + 1 for i, s_ in enumerate(steps) if s_ is st), None) or next((i + 1 for i, s_ in enumerate(steps) if s_ == st), None)

def same(ev, st, steps):
    """저장된 증거(ev)가 이 번호의 지금 모양과 같은가 — 정확한 지문이 같거나, 모양 지문이 같으면 같다.
    모양 지문은 지금 정의(번호 화면 모양: idx + 들어오는 자리)와 앞선 두 정의(idx 만 · 옛 정의)로 남긴 증거를 모두 받는다 — 이미 남긴 증거를 다시 찍게 하지 않는다."""
    if not ev: return False
    if ev.get("fp") == fp(st): return True
    if not ev.get("shape"): return False
    idx = step_index(st, steps); anc = anchor(steps)
    return ev["shape"] in {shape_fp(st, anc, idx, steps), shape_fp(st, anc, idx), shape_fp(st, anc)}


# ── 조립이 같은지 숫자로 비교(동일 확인 재서명, record_check.py --재서명) ──
# 코드·플래그·설명만 바뀌고 그 번호 화면의 부품 위치·회전·안내점이 그대로면 증거를 다시 찍지 않고 지문만 새로 서명한다.
# 지문은 한 글자만 달라도 바뀌므로, 재서명은 지문이 아니라 아래 값(geo)을 허용 오차 안에서 비교해 같을 때만 한다.
GEO_TOL_MM, GEO_TOL_DEG = 0.5, 0.5   # 부품 자리·회전·안내점: 결합(돌기↔구멍)이 그대로인지 보는 값이라 좁게 둔다(맞물림 검사의 축 어긋남 한계 1.2mm 보다 작게)
GEO_TOL_VIEW_MM, GEO_TOL_VIEW_DEG = 5.0, 15.0   # 보는 방향·구도(카메라 방향, 결합 전에 띄운 거리·방향): 시계 한 칸(30°)의 절반까지는 같은 구도로 본다(사용자 2026-11-15)
_GEO_PT = _ABS_PT + ("by",)

def geo(st, anc, idx, steps):
    """idx 번 화면의 조립 값 {라벨: {p, r, marks…, dir, hover}} — 이 번호 부품(자리·옆자리·옮김·그 번호까지의 poseAt)·다른 번호 부품이 이 화면에서 갖는 자리(_incoming)·moveMade. 자리는 기준점(1번 첫 부품)을 뺀 값."""
    out = {}
    def sub(pt): return [round(float(a) - float(b), 4) for a, b in zip(pt, anc)]
    def put(key, d):
        e = {}
        if d.get("p") is not None: e["p"] = sub(d["p"])
        if d.get("r") is not None: e["r"] = [float(v) for v in d["r"]]
        for k in _GEO_PT:
            v = d.get(k)
            if v: e[k] = [sub(m) for m in v] if isinstance(v[0], (list, tuple)) else [[float(x) for x in v]]
        if d.get("dir") is not None: e["dir"] = [float(v) for v in d["dir"]]
        if d.get("hover") is not None: e["hover"] = float(d["hover"])
        out[key] = e
    for i, p in enumerate(st.get("parts") or []):
        if not isinstance(p, dict): continue
        key = "%d:%d %s" % (idx, i, p.get("n")); put(key, p)
        if isinstance(p.get("side"), dict): put(key + " side", p["side"])
        for m in ([p["move"]] if isinstance(p.get("move"), dict) else []) + [m for m in (p.get("moves") or []) if isinstance(m, dict)]:
            if str(m.get("at", 0)).isdigit() and int(m["at"]) <= idx: put("%s move@%s" % (key, m["at"]), m)
        for k, v in (p.get("poseAt") or {}).items():
            if isinstance(v, dict) and not v.get("final") and str(k).isdigit() and int(k) <= idx: put("%s poseAt@%s" % (key, k), v)
        if isinstance(p.get("explode"), dict) and p["explode"].get("offset") is not None: out[key + " explode"] = {"by": [[float(x) for x in p["explode"]["offset"]]]}
    if isinstance(st.get("cam"), dict) and st["cam"].get("theta") is not None and st["cam"].get("phi") is not None: out["카메라"] = {"cam": [float(st["cam"]["theta"]), float(st["cam"]["phi"])]}
    for k_, t_, p_, r_ in _incoming(steps, idx): put("들어옴 %s %s" % (k_, t_), {"p": p_, "r": r_})
    for k_, e_ in (st.get("moveMade") or {}).items():
        if isinstance(e_, dict): put("moveMade %s" % k_, e_)
    return out

def geo_diff(a, b, tol_mm=GEO_TOL_MM, tol_deg=GEO_TOL_DEG, view_mm=GEO_TOL_VIEW_MM, view_deg=GEO_TOL_VIEW_DEG):
    """두 geo 가 허용 오차 안에서 같은가 → (같음, 가장 큰 위치 차 mm, 가장 큰 회전 차 °, 다른 곳 목록)."""
    import math
    import numpy as np
    from asmlib import euler_to_R
    bad = []; mp = 0.0; mr = 0.0
    for k in sorted(set(a) | set(b)):
        if k not in a or k not in b: bad.append("%s: %s" % (k, "새로 생김" if k not in a else "없어짐")); continue
        x, y = a[k], b[k]
        for f in sorted(set(x) | set(y)):
            if f not in x or f not in y: bad.append("%s.%s: 한쪽에만 있음" % (k, f)); continue
            if f == "r":
                R = np.array(euler_to_R(x[f]), float).T @ np.array(euler_to_R(y[f]), float)
                d = math.degrees(math.acos(max(-1.0, min(1.0, (float(np.trace(R)) - 1) / 2)))); mr = max(mr, d)
                if d > tol_deg: bad.append("%s.r: %.2f° 다름" % (k, d))
            elif f == "cam":
                u, v = ([math.sin(c[1]) * math.cos(c[0]), math.cos(c[1]), math.sin(c[1]) * math.sin(c[0])] for c in (x[f], y[f]))
                d = math.degrees(math.acos(max(-1.0, min(1.0, sum(p_ * q_ for p_, q_ in zip(u, v))))))
                if d > view_deg: bad.append("%s: 보는 방향이 %.1f° 다름" % (k, d))
            elif f == "dir":
                u, v = np.array(x[f], float), np.array(y[f], float); nu, nv = np.linalg.norm(u), np.linalg.norm(v)
                d = math.degrees(math.acos(max(-1.0, min(1.0, float(u @ v) / (nu * nv))))) if nu and nv else (0.0 if nu == nv else 180.0)
                if d > view_deg: bad.append("%s.dir: %.2f° 다름" % (k, d))
            elif f == "hover":
                d = abs(x[f] - y[f])
                if d > view_mm: bad.append("%s.hover: %.2f mm 다름" % (k, d))
            else:
                pa, pb = (x[f], y[f]) if f != "p" else ([x[f]], [y[f]])
                if len(pa) != len(pb): bad.append("%s.%s: 점 개수 %d → %d" % (k, f, len(pa), len(pb))); continue
                for u, v in zip(pa, pb):
                    d = float(np.linalg.norm(np.array(u, float) - np.array(v, float))); mp = max(mp, d)
                    if d > tol_mm: bad.append("%s.%s: %.2f mm 다름" % (k, f, d))
    return (not bad), round(mp, 3), round(mr, 3), bad

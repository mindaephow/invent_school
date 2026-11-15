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

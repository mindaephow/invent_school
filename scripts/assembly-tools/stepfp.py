# 단계 내용 지문(build.py 의 ✓ 단계 보호와 record_check.py 의 비교 증거가 같은 함수를 쓴다).
# 자동으로 다시 계산되는 "━ 작업 점검 ━" 체크 블록(☑/☐)은 뺀다 — 점검 결과가 바뀌어도 내용이 바뀐 것으로 잡히지 않게.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import hashlib, json

def fp(st):
    st = dict(st); st.pop("review", None); st.pop("reviewWhy", None)   # 번호판 색(주황/파랑) 표시용 플래그는 내용이 아니다 — 검증 상태가 바뀔 때마다 증거·✓ 지문이 깨지지 않게 뺀다(2026-10-18)
    st["note"] = str(st.get("note", "")).split("\n━ 작업 점검 ━")[0]
    return hashlib.sha1(json.dumps(st, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


# ── 조립 모양 지문(사용자 2026-11-05: "증거는 조립 모양을 남기려는 것이지 조립 위치를 남기려는 게 아니다") ──
# 조립 전체가 같이 옮겨진 것(예: 1번을 원점 중심으로 옮김)은 모양이 같으므로 증거가 무효가 되지 않는다.
# 절대 좌표 필드(p·marks·faceMarks·settleMarks·holeMarks)에서 1번 첫 부품의 p(기준점)를 빼고 지문을 만든다. 부품 사이 위치·회전·띄움은 그대로 들어가 있어 모양이 바뀌면 지문도 바뀐다.
# 번호 하나만 통째로 옮기면 기준점은 그대로라 지문이 바뀐다(모양이 달라진 것).
_ABS_PT = ("marks", "faceMarks", "settleMarks", "holeMarks")

def anchor(steps):
    try: return [float(v) for v in steps[0]["parts"][0]["p"]]
    except Exception: return [0.0, 0.0, 0.0]

def shape_fp(st, anc):
    d = json.loads(json.dumps(st))
    def sub(pt): return [round(float(a) - float(b), 3) for a, b in zip(pt, anc)]
    for p in d.get("parts") or []:
        if "p" in p: p["p"] = sub(p["p"])
        for k in _ABS_PT:
            if k == "marks" and p.get("side"): continue   # 옆자리(창고 2)로 옮겨 놓은 부품의 안내점은 원점 기준이라 기준점을 빼지 않는다(새 창고는 원점, A4)
            if p.get(k): p[k] = [sub(m) for m in p[k]]
    return fp(d)

def same(ev, st, steps):
    """저장된 증거(ev)가 이 번호의 지금 모양과 같은가 — 정확한 지문이 같거나, 모양 지문이 같으면 같다."""
    if not ev: return False
    if ev.get("fp") == fp(st): return True
    return bool(ev.get("shape")) and ev.get("shape") == shape_fp(st, anchor(steps))

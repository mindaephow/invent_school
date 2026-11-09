# 큐보 부품 결합규칙 점검기 — 사용자가 정한 규칙(큐보/규칙/큐보 부품결합규칙.md)을 조립도 번호마다 잰다. 큐보 조립도(cubo-*) 전용.
#   python cubo_joint_check.py <이름|all> [번호 …]
#   규칙 1    프레임과 프레임을 잇는 부품은 리벳·블록(볼트·너트는 규칙 14·15)뿐
#   규칙 4    블록·모터 돌기 끝이 프레임 먼 쪽 면 밖으로 0.5mm 넘게 나가면 위반
#   규칙 2·8  리벳으로 이은 두 부품(프레임·블록·브라켓·기어…) 사이 틈 0 (틈 >0.3, 겹침 >1.0 이면 위반)
#   규칙 3    프레임끼리는 겹치지 않는다(돌기 부분을 뺀 판 두께 침투 >0.5mm)
#   규칙 5~7  돌기 하나는 프레임 한 장의 구멍에만 든다(구멍 안에 완전히 든 구멍이 서로 다른 프레임 둘 이상이면 위반)
#   규칙 10   방향 있는 부품(메인보드…): 책에서 읽은 특징 방향(<이름>_orient.json)과 모델이 같아야 하고, 기록이 없으면 위반
#   규칙 13   블록·모터·메인보드 돌기를 프레임에 바로 꽂을 때 몸체와 프레임 면 사이 틈 0
#   규칙 14·15 8볼트=프레임 2장(두께 합 10), 12볼트=프레임 3장(15)이 틈 없이 딱 붙어야 함
#   규칙 9    볼트·너트: 머리·너트가 판에서 떠 있거나(틈) 볼트 끝이 판 밖으로 나오면 위반
# 앞 번호 부품이 같은 자리에 겹쳐 잡히는 중복(새 부품과 같은 이름·같은 자세)은 지우고 잰다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, glob, runpy
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE); sys.path.insert(0, HERE)
import coupling_catalog as cc, stepchecks, obb
from asmlib import _mate
dims = stepchecks._dims()
_orig = cc.view
PEGGED = ("DC모터", "서보모터", "메인보드", "IR센서", "LED센서", "터치센서")   # 프레임에 돌기로 바로 꽂는 부품 — 돌기·깊이가 블록과 같아 블록 규칙(4·5~7·13)을 따른다(센서는 사용자 2026-11-06)

def view(A, k):
    vs = _orig(A, k)
    return [o for o in vs if not any(q is not o and q.new and not o.new and q.n == o.n and np.allclose(q.p, o.p, atol=0.01) and np.allclose(q.R, o.R, atol=1e-3) for q in vs)]
cc.view = view

# 규칙 10: 방향 있는 부품의 "특징 방향"(부품 로컬 축, 설명). 부품 실측(measure_part)에서 확인한 것만 적는다 — 새 부품은 실측 뒤에 추가.
DIRECTIONAL = {"메인보드": ((0, 0, 1), "버튼 줄 쪽(+z)")}
_AX = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}
def _axis_vec(s): return np.array(_AX[s], float) if s in _AX else None
def _axis_name(w):
    k = max(_AX, key=lambda a: float(np.array(_AX[a], float) @ w)); return k if float(np.array(_AX[k], float) @ w) > 0.9 else "기울어짐%s" % np.round(w, 2).tolist()
def _find_part(A, vs, name, no):   # 기준 부품: 이름 + 그 이름이 조립도 전체에서 나온 순서(get_part_faces 의 "N번"과 같다)
    n = 0
    for st in A.steps:
        for q in st.parts:
            if q.n == name:
                n += 1
                if n == no:
                    return next((o for o in vs if o.src is q), None)
    return None
_orient_cache = {}
def _orient(aid):   # <이름>_orient.json = {"robot": {"back_ref": "로봇 뒤쪽 기준 부품", "back_no": 번호, "bottom_ref": "로봇 바닥 기준 부품", "bottom_no": 번호}, "번호": {"부품이름": {"face": "앞|뒤|위|아래" (또는 ref·ref_no·relation), "evidence": "책 N번에서 읽은 근거"}}}
    nm = aid.split("-")[-1]
    if nm not in _orient_cache:
        p = nm + "_orient.json"
        _orient_cache[nm] = __import__("json").load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return _orient_cache[nm]

def inside(pg, ho):   # 돌기 중심이 구멍 안에 완전히 들었는가(느슨한 _mate 와 달리 엄격)
    rel = pg["pos"] - ho["pos"]; al = float(rel @ ho["dir"]); lat = float(np.linalg.norm(rel - al * ho["dir"]))
    return lat < 0.4 and abs(al) <= (ho.get("len", 5) or 5) / 2 + 0.1

def _pen(pa, Ra, ha, pb, Rb, hb):   # 두 회전 상자(OBB)의 침투 깊이(분리축 정리의 가장 얕은 겹침, 떨어져 있으면 0)
    A_, B_ = [Ra[:, i] for i in range(3)], [Rb[:, i] for i in range(3)]
    axes = A_ + B_ + [np.cross(a, b) for a in A_ for b in B_]; best = 1e9; d = pb - pa
    for ax in axes:
        n = float(np.linalg.norm(ax))
        if n < 1e-6: continue
        ax = ax / n
        ra = sum(abs(float(ax @ A_[i])) * ha[i] for i in range(3)); rb = sum(abs(float(ax @ B_[i])) * hb[i] for i in range(3))
        ov = ra + rb - abs(float(ax @ d))
        if ov <= 0: return 0.0
        best = min(best, ov)
    return best

LAST = {}   # 메시지 → 화면 부품 키["만든번호:부품순서"…] — violations.py 가 화면에 칠할 때 쓴다(사용자 지시 2026-11-08)
def _ky(*os_): return ["%d:%d" % (o.src.step.index, o.src.step.parts.index(o.src)) for o in os_ if getattr(o, "src", None) is not None]
def _em(out, msg, *os_):
    out.append(msg); LAST[msg] = _ky(*os_)

def check(A, k):
    out = []; vs = view(A, k); pf = {id(o): cc.feats(o, "pegs") for o in vs}; hf = {id(o): cc.feats(o, "holes") for o in vs}
    # 규칙 2·8
    for r in [o for o in vs if o.new and o.n == "리벳"]:
        c = r.R @ np.array(r.conn["pegs"][0]["dir"], float); best = {}
        for pg in pf[id(r)]:
            for a in vs:
                if a is r or a.n not in dims: continue
                for ho in hf[id(a)]:
                    if _mate(pg, ho):
                        rel = pg["pos"] - ho["pos"]; al = float(rel @ ho["dir"]); lat = float(np.linalg.norm(rel - al * ho["dir"])); sc = abs(al) + lat
                        if pg["id"] not in best or sc < best[pg["id"]][0]: best[pg["id"]] = (sc, a, ho)
        if "p1" in best and "p2" in best and best["p1"][1] is not best["p2"][1]:
            A1, A2 = best["p1"][1], best["p2"][1]
            def _sp(Aq, pid):   # 판 구간: 프레임·블록은 상자, 브라켓은 L자라 리벳이 들어간 구멍의 두께 5mm 날개 조각
                if "브라켓" in Aq.n:
                    ho_ = best[pid][2]; z_ = float(ho_["pos"] @ c); return (z_ - 2.5, z_ + 2.5)
                return obb.span(obb.corners(Aq.p, Aq.R, np.array(dims[Aq.n], float) / 2), c)
            s1 = _sp(A1, "p1"); s2 = _sp(A2, "p2")
            g = float(max(s2[0] - s1[1], s1[0] - s2[1]))
            if g > 0.3 or g < -1.0: _em(out, "규칙8 리벳 틈: %s↔%s %+.1fmm" % (A1.n, A2.n, g), A1, A2)
    # 규칙 3 (프레임은 물리적으로 겹칠 수 없다 — 판 높이가 겹치는 나란한 두 프레임의 구멍 중심이 피치(10mm)보다 훨씬 가까우면 위반. 구부러진 프레임도 구멍 기준이라 상자 크기에 속지 않는다)
    _sl = A.steps[k - 1].kw.get("slot", 1); _k0 = k
    while _k0 > 1 and A.steps[_k0 - 2].kw.get("slot", 1) == _sl: _k0 -= 1
    # 현재 창고를 시작하기 전에 만든 부품(다른 창고의 14~18번 조립 등)은 화면에 같이 놓이지 않는다 — 화면 확인: catapult 19번(2026-11-03)
    frs = [o for o in vs if "프레임" in o.n and o.n in dims and (o.new or A.steps.index(o.src.step) + 1 >= _k0)]
    for a in [o for o in frs if o.new]:
        for b in frs:
            if b is a or (b.new and id(b) < id(a)): continue
            na = a.R @ np.array((0, 1, 0), float); nb = b.R @ np.array((0, 1, 0), float)
            if abs(abs(float(na @ nb)) - 1) > 1e-3 or abs(float((b.p - a.p) @ na)) >= 4.5: continue   # 나란하고 판 두께 구간이 0.5mm 넘게 겹치는 두 프레임만
            ha = [h["pos"] for h in hf[id(a)]]; hb = [h["pos"] for h in hf[id(b)]]
            if not ha or not hb: continue
            d_ = min(float(np.linalg.norm(x - y)) for x in ha for y in hb)
            if d_ < 9.0: _em(out, "규칙3 %s↔%s 겹침: 구멍 중심 간격 %.1fmm (프레임은 겹칠 수 없음 — 이어지면 10)" % (a.n, b.n, d_), a, b)
    # 규칙 16 (프레임과 프레임이 옆에 같은 판 높이로 이어질 때는 방향이 어떻든 맞닿은 구멍 사이 피치가 10mm — 사용자 확정 2026-11-03)
    for a in [o for o in frs if o.new]:
        for b in frs:
            if b is a or (b.new and id(b) < id(a)): continue
            na = a.R @ np.array((0, 1, 0), float); nb = b.R @ np.array((0, 1, 0), float)
            if abs(abs(float(na @ nb)) - 1) > 1e-3 or abs(float((b.p - a.p) @ na)) > 0.3: continue   # 같은 판 높이로 나란한 두 프레임만
            if _pen(a.p, a.R, np.array(dims[a.n], float) / 2 + 3.0, b.p, b.R, np.array(dims[b.n], float) / 2 + 3.0) <= 0: continue   # 3mm 안쪽으로 가까이 있지 않으면 이어진 게 아님
            ha = [h["pos"] for h in hf[id(a)]]; hb = [h["pos"] for h in hf[id(b)]]
            if not ha or not hb: continue
            if not any(c is not a and c is not b and any(inside(pg, ho) for pg in pf[id(c)] for ho in hf[id(a)]) and any(inside(pg, ho) for pg in pf[id(c)] for ho in hf[id(b)]) for c in vs):
                continue   # 같은 부품(블록·리벳·볼트·모터)의 돌기가 두 프레임 구멍에 다 들어가야 이어진 것 — 따로 걸려 모서리만 닿는 프레임(홀수 줄·짝수 줄이 같은 중심선에 놓인 경우 등)은 줄이 반 칸 어긋나는 게 정상(사용자 2026-11-03)
            d_ = min(float(np.linalg.norm(x - y)) for x in ha for y in hb)
            if abs(d_ - 10.0) > 0.3: _em(out, "규칙16 옆 프레임 %s↔%s 맞닿은 구멍 피치 %.1fmm (10 이어야 함)" % (a.n, b.n, d_), a, b)
    # 규칙 5~7
    for b in [o for o in vs if o.new and (("블록" in o.n) or o.n in PEGGED or o.n == "리벳")]:
        for pg in pf[id(b)]:
            fr = sorted({a.n for a in vs if a is not b and "프레임" in a.n and any(inside(pg, ho) for ho in hf[id(a)])})
            if len(fr) >= 2: _em(out, "규칙5~7 %s %s 돌기가 프레임 두 장에: %s" % (b.n, pg["id"], "+".join(fr)), b)
    # 규칙 1 (프레임과 프레임을 잇는 부품은 리벳·블록 — 볼트·너트는 규칙 14·15): 새 부품의 돌기가 서로 다른 프레임 둘 이상의 구멍에 들어가 있으면 그 부품이 잇는 것
    for c_ in [o for o in vs if o.new and pf[id(o)] and "프레임" not in o.n]:
        fr = sorted({a.n + "#" + str(id(a)) for a in vs if a is not c_ and "프레임" in a.n and any(inside(pg, ho) for pg in pf[id(c_)] for ho in hf[id(a)])})
        if len(fr) >= 2 and not (c_.n == "리벳" or "블록" in c_.n or c_.n in ("8볼트", "12볼트", "너트", "축")):   # 축은 구멍을 지나가는 막대(G21)라 프레임을 잇는 부품이 아니다
            _em(out, "규칙1 %s 가 프레임 %d장을 이음(프레임끼리는 리벳·블록으로 잇는다)" % (c_.n, len(fr)), c_)
    # 규칙 4 (블록·모터 돌기는 프레임에 끼워질 때 프레임의 먼 쪽 면 밖으로 나가지 않는다 — 돌기 끝이 구멍 반대편 면을 0.5mm 넘으면 위반)
    for b_ in [o for o in vs if o.new and (("블록" in o.n) or o.n in PEGGED)]:
        for pg in pf[id(b_)]:
            for a in vs:
                if a is b_ or "프레임" not in a.n: continue
                for ho in hf[id(a)]:
                    if not inside(pg, ho): continue
                    tip = pg["pos"] + pg["dir"] * (pg.get("len", 5) or 5) / 2; tal = float((tip - ho["pos"]) @ ho["dir"])
                    hl = (ho.get("len", 5) or 5) / 2
                    for s_ in (1.0, -1.0):   # 돌기가 어느 쪽으로 꽂혔든 끝이 그쪽 면을 넘는지
                        if float(pg["dir"] @ ho["dir"]) * s_ > 0.9 and s_ * tal > hl + 0.5:
                            _em(out, "규칙4 %s %s 돌기 끝이 %s 면 밖으로 %.1fmm" % (b_.n, pg["id"], a.n, s_ * tal - hl), b_, a)
    # 규칙 10 (방향 있는 부품: 책 그림의 부품 모양·특징 방향과 같아야 한다 — 기준은 월드 X·Y·Z 가 아니라 같은 로봇 안의 다른 부품과의 상대 관계)
    od = _orient(A.id)
    for o in [o for o in vs if o.new and o.n in DIRECTIONAL]:
        loc, what = DIRECTIONAL[o.n]; dec = (od.get(str(k)) or {}).get(o.n)
        w = o.R @ np.array(loc, float)
        if not dec: _em(out, "규칙10 %s 방향 미기록 — 책에서 %s 이 어느 부품 쪽인지/반대쪽인지 읽어 %s_orient.json 에 적을 것" % (o.n, what, A.id.split("-")[-1]), o); continue
        if "face" in dec:   # 로봇 기준 방향: 앞/뒤 = 버튼 줄(+z)이 로봇 뒤쪽 기준 부품(robot.back_ref)에서 먼/가까운 쪽, 위/아래 = 윗면(+y)이 로봇 바닥 기준 부품(robot.bottom_ref)에서 먼/가까운 쪽
            rb = od.get("robot") or {}; fa = dec["face"]; key = "back" if fa in ("앞", "뒤") else "bottom"
            if key + "_ref" not in rb: out.append("규칙10 %s_orient.json 에 robot.%s_ref (로봇 %s 기준 부품)가 없음" % (A.id.split("-")[-1], key, "뒤쪽" if key == "back" else "바닥")); continue
            if key == "bottom": w = o.R @ np.array((0, 1, 0), float)
            dec = dict(dec, ref=rb[key + "_ref"], ref_no=rb.get(key + "_no"), relation=("away" if fa in ("앞", "위") else "toward"))
        ref = _find_part(A, vs, dec["ref"], dec.get("ref_no"))
        if ref is None: out.append("규칙10 %s 기준 부품 %s %s번을 이 번호에서 못 찾음" % (o.n, dec["ref"], dec.get("ref_no"))); continue
        d = float(w @ (ref.p - o.p)); toward = d > 0
        if toward != (dec["relation"] == "toward"): _em(out, "규칙10 %s %s 이 책(%s)과 다름: 책 %s %s 쪽 / 모델 %s" % (o.n, what, dec.get("evidence", "근거 없음"), dec["ref"], dec["relation"] == "toward" and "을 향함" or "반대쪽", toward and "향함" or "반대쪽"), o)
    # 규칙 13 (돌기로 프레임에 바로 꽂는 부품 — 블록·모터·메인보드·센서: 몸체와 프레임 면 사이 틈 0)
    for P in [o for o in vs if o.new and o.conn["pegs"] and o.n in dims and (("블록" in o.n) or o.n in PEGGED)]:
        done = set()
        for pg in pf[id(P)]:
            for F in vs:
                if F is P or "프레임" not in F.n or F.n not in dims or id(F) in done: continue
                for ho in hf[id(F)]:
                    if inside(pg, ho):
                        done.add(id(F)); ax = ho["dir"]
                        s1 = obb.span(obb.corners(P.p, P.R, np.array(dims[P.n], float) / 2), ax); s2 = obb.span(obb.corners(F.p, F.R, np.array(dims[F.n], float) / 2), ax)
                        g = float(max(s2[0] - s1[1], s1[0] - s2[1])) + float(pg.get("len", 5) or 5)   # 상자에 돌기 길이가 들어 있어서 딱 붙으면 −돌기길이 → 보정
                        if g > 0.3: _em(out, "규칙13 %s↔%s 직접 결합 틈 %+.1fmm" % (P.n, F.n, g), P, F)
                        elif g < -1.0: _em(out, "규칙13 %s↔%s 겹침 %+.1fmm" % (P.n, F.n, g), P, F)
                        break
    # 규칙 9 (볼트·너트)
    rows = []; fast = []; cc.scan(A, k, dims, rows, fast)
    for x in fast:
        if x.get("kind") in ("8볼트", "12볼트"):
            if not (-0.3 <= x["head_off"] <= 0.3): out.append("규칙9 %s 머리 %+.1fmm (머리는 홀라인에 딱 끼워져 프레임·브라켓 면 밖으로 넘치면 안 됨 — 사용자 2026-11-03. 넘치거나 떠 있으면 위반)" % (x["kind"], x["head_off"]))
            if x["tip_off"] > (0.05 if x.get("nut") else 5.0): out.append("규칙9 %s 끝이 판 밖으로 %+.1fmm" % (x["kind"], x["tip_off"]))
            want = {"8볼트": 10.0, "12볼트": 15.0}[x["kind"]]   # 규칙 14·15: 8볼트=프레임 2장, 12볼트=프레임 3장 — 틈 없이 딱 붙으면 판 두께 합이 10·15
            if x.get("nut") and not x.get("gear") and abs(x["stack"] - want) > 0.3: out.append("규칙14·15 %s 가 지나는 판 두께 합 %.1fmm (프레임 %d장 = %.0fmm 이어야 함 — 틈이 있거나 판 수가 다름, 블록이 낀 번호는 확인)" % (x["kind"], x["stack"], 2 if x["kind"] == "8볼트" else 3, want))
        elif "nut_off" in x and not (-1.2 <= x["nut_off"] <= 0.3): out.append("규칙9 너트가 판에서 %+.1fmm (너트 아래 턱은 프레임 홀 테두리에 1mm 들어가는 게 정상 — 사용자 2026-11-03. 떠 있거나 더 깊이 파묻히면 위반)" % x["nut_off"])
    return sorted(set(out))

STORED_JS = os.path.join(HERE, "..", "..", "public", "design-assemblies.js")

def stored_ids():
    """스크립트 없이 저장 데이터(design-assemblies.js)로만 있는 큐보 조립도 이름(id 의 마지막 토막: cubo-1-balance → balance)."""
    import re
    ids = re.findall(r"id: '(cubo-\d-[^']+)'", open(STORED_JS, encoding="utf-8").read())
    return [i.split("-", 2)[2] for i in ids if not os.path.exists(i.split("-", 2)[2] + ".py")]

def load_asm(nm):
    """조립도를 읽는다 — 스크립트(<이름>.py)가 있으면 그것을, 없으면 저장 데이터를 그대로 asmlib 부품으로 놓는다(모든 조립도를 같은 점검기로 잰다)."""
    if os.path.exists(nm + ".py"): return runpy.run_path(nm + ".py", run_name="probe")["A"]
    import json, subprocess
    from asmlib import Asm, euler_to_R
    code = "global.window={};require(%s);const a=window.IVS_ASSEMBLIES.find(x=>x.id.endsWith('-'+%s));process.stdout.write(JSON.stringify(a||null));" % (json.dumps(os.path.abspath(STORED_JS)), json.dumps(nm))
    a = json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True, encoding="utf-8").stdout or "null")
    if not a: raise FileNotFoundError(nm)
    A = Asm(a["id"], a["chapter"], a["book"], camera=a.get("camera"))
    for st in a["steps"]:
        S = A.step(st["note"])
        for pt in st["parts"]: S.place(pt["n"], euler_to_R(pt["r"]), pt["p"], **{k: v for k, v in pt.items() if k not in ("n", "p", "r")})
    return A

def main():
    want = sys.argv[1:]; name = want[0] if want else "all"; steps = [int(a) for a in want[1:]]
    names = [os.path.basename(p)[:-3] for p in sorted([asmpath.ap(_n, ".py") for _n in asmpath.names()]) if not os.path.basename(p).startswith(("scratch", "new_assembly", "_")) and any(l.startswith("A = Asm(\"cubo-") for l in open(p, encoding="utf-8", errors="ignore"))] + stored_ids() if name == "all" else [name]
    total = 0
    for nm in names:
        try: A = load_asm(nm)
        except BaseException as e: print("⚠ %s 건너뜀: %s" % (nm, repr(e)[:80])); continue
        n_ = 0
        for k in (steps or range(1, len(A.steps) + 1)):
            try: res = check(A, k)
            except BaseException as e: print("⚠ %s %d번 점검 오류: %s" % (nm, k, repr(e)[:70])); continue
            for r in res: print("❌ %s %d번 %s" % (nm, k, r)); n_ += 1
        print("== %s: %d건" % (nm, n_)); total += n_
    print("합계 %d건" % total)

if __name__ == "__main__": main()

# 사용자가 화면에서 고쳐 저장한 것(❄ 모습 기록·📷 카메라)과 내 코드 값의 차이를 모아 user_diffs/수정저장차이.md 로 쓴다(DB 는 읽기만 한다).
#   python collect_diffs.py
# 목적: 내가 반복해서 틀리는 부품·번호를 찾아 검사·규칙으로 옮긴다(00_개선규칙 5번). 몸 뒤집기(xform)는 회전을 보정하고, 옆자리·noFreeze 부품은 뺀다.
import json, math, os, subprocess, sys, urllib.request
from collections import Counter, defaultdict
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import userdone
here = os.path.dirname(os.path.abspath(__file__))
env = userdone._env(); URL = (env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")).rstrip("/"); KEY = env["SUPABASE_SERVICE_ROLE_KEY"]
def rest(path):
    return json.loads(urllib.request.urlopen(urllib.request.Request(URL + "/rest/v1/" + path, headers={"apikey": KEY, "Authorization": "Bearer " + KEY}), timeout=60).read().decode("utf-8"))
js = os.path.abspath(os.path.join(here, "..", "..", "public", "design-assemblies.js")).replace("\\", "/")
out = subprocess.run(["node", "-e", "global.window={};const fs=require('fs');new Function('window',fs.readFileSync(%r,'utf8'))(window);process.stdout.write(JSON.stringify(window.IVS_ASSEMBLIES))" % js], capture_output=True, check=True).stdout.decode("utf-8")
A = {a["id"]: a for a in json.loads(out)}
def R(r):
    a, b, c = np.radians(r)
    Rx = np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]]); Ry = np.array([[np.cos(b),0,np.sin(b)],[0,1,0],[-np.sin(b),0,np.cos(b)]]); Rz = np.array([[np.cos(c),-np.sin(c),0],[np.sin(c),np.cos(c),0],[0,0,1]])
    return Rz @ Ry @ Rx
poses = rest("ivs_assembly_poses?select=assembly_id,step,poses&order=assembly_id,step"); cams = rest("ivs_assembly_cams?select=assembly_id,step,cam&order=assembly_id,step")
fix = []; tot = Counter(); chg = Counter(); angs = defaultdict(list)
for row in poses:
    a = A.get(row["assembly_id"])
    if not a: continue
    k = row["step"]; xf = a.get("xform"); M = np.array(xf["m"], float) if (xf and k >= xf.get("at", 10**9)) else np.eye(3)
    cnt, code = {}, {}
    for si, st in enumerate(a["steps"], 1):
        for q in st.get("parts", []):
            cnt[q["n"]] = cnt.get(q["n"], 0) + 1
            if si == k: code["%s %d번" % (q["n"], cnt[q["n"]])] = q
    for lab, o in row["poses"].items():
        q = code.get(lab)
        if not q or not o.get("r") or q.get("noFreeze") or (q.get("side") and k < q["side"].get("until", 0)): continue
        rel = (M @ R(q.get("r") or [0, 0, 0])).T @ R(o["r"]); ang = math.degrees(math.acos(max(-1, min(1, (np.trace(rel) - 1) / 2))))
        tot[q["n"]] += 1
        if ang > 3: chg[q["n"]] += 1; angs[q["n"]].append(round(ang)); fix.append((row["assembly_id"].split("-", 2)[-1], k, lab, round(ang)))
cam_rows = []; per = defaultdict(list)
for row in cams:
    a = A.get(row["assembly_id"]); c = (a["steps"][row["step"] - 1].get("cam") if a and row["step"] <= len(a["steps"]) else None)
    if isinstance(c, dict) and c.get("theta") is not None:
        u = row["cam"]; dt = (u["theta"] - c["theta"] + math.pi) % (2 * math.pi) - math.pi; dp = u["phi"] - c["phi"]
        src = a["steps"][row["step"] - 1].get("camSrc", "?"); cam_rows.append((row["assembly_id"].split("-", 2)[-1], row["step"], c["theta"], c["phi"], src, u["theta"], u["phi"], dt, dp)); per[src].append((abs(dt), abs(dp)))
import datetime
L = ["# 수정저장 차이 — 내 코드 값과 사용자가 화면에서 고쳐 저장한 값(❄·📷)의 차이", "", "(`python collect_diffs.py` 로 DB 에서 다시 만든다. 만든 때: %s. 몸 뒤집기(xform)는 보정, 옆자리·noFreeze 부품은 제외.)" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "",
     "## 1. 자세(❄): 비교 %d건 중 사용자가 고친 것 %d건" % (sum(tot.values()), sum(chg.values())), "", "| 부품 | 비교 | 고침 | 비율 |", "|---|---|---|---|"]
for n, c in sorted(tot.items(), key=lambda x: -chg[x[0]]):
    if chg[n]: L.append("| %s | %d | %d | %d%% |" % (n, c, chg[n], 100 * chg[n] // c))
L += ["", "고친 부품 목록(조립도 · 번호 · 부품 · 돌린 각도):", ""] + ["- %s · %d번 · %s · %d°" % x for x in fix] + ["", "안 고친 부품(자세가 코드와 같음): " + ", ".join("%s %d" % (n, c) for n, c in sorted(tot.items()) if not chg[n]), ""]
L += ["## 2. 카메라(📷): 내 코드 값과 사용자 값의 차이(라디안)", "", "| camSrc(내 출처) | 번호 수 | 평균 |Δtheta| | 평균 |Δphi| |", "|---|---|---|---|"]
for s, v in per.items(): L.append("| %s | %d | %.2f | %.2f |" % (s, len(v), np.mean([x[0] for x in v]), np.mean([x[1] for x in v])))
L += ["", "| 조립도 | 번호 | 내 theta·phi(출처) | 사용자 theta·phi | Δtheta | Δphi |", "|---|---|---|---|---|---|"] + ["| %s | %d | %.2f %.2f (%s) | %.2f %.2f | %+.2f | %+.2f |" % (a, k, t, p, s, ut, up, dt, dp) for a, k, t, p, s, ut, up, dt, dp in cam_rows if abs(dt) > 0.15 or abs(dp) > 0.15]
os.makedirs(os.path.join(here, "user_diffs"), exist_ok=True); open(os.path.join(here, "user_diffs", "수정저장차이.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
# 기계가 읽는 통계(2026-10-14): number_start.py 가 번호를 시작할 때 이 번호의 부품별로 "사용자가 자세를 고친 비율·돌린 각도"를 경고로 보여 준다. 사용자가 고쳐 저장하고 이 도구를 돌릴 때마다 저절로 갱신된다.
json.dump({"만든때": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "자세": {n: {"비교": tot[n], "고침": chg[n], "각도": sorted(Counter(angs[n]).items(), key=lambda x: -x[1])} for n in tot if chg[n]}}, open(os.path.join(here, "user_diffs", "pose_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("수정저장차이.md 작성: 자세 %d/%d건 고침, 카메라 비교 %d건(차이 큰 %d건)" % (sum(chg.values()), sum(tot.values()), len(cam_rows), sum(1 for r in cam_rows if abs(r[7]) > 0.15 or abs(r[8]) > 0.15)))

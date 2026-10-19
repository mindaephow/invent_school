# 사용자가 화면에서 저장한 ❄ 모습 기록(ivs_assembly_poses)의 부품 위치를 고친다 — 사용자가 고치라고 지시했을 때만 쓴다(사용자 지정이 무조건 우선: 2026-10-13 "무조건 사용자가 지정해놓은 걸 우선으로 해").
#   python pose_edit.py <이름> <번호> "리벳 15번:x,y,z;리벳 16번:x,y,z"      → 그 라벨의 p 를 바꾼다(회전 r·q 는 그대로). 바꾸기 전 기록 전체를 refs/<이름>/_pose_backup/NN_<시각>.json 에 저장한다.
#   python pose_edit.py <이름> <번호> --보기 [라벨 일부]                         → 기록된 위치를 코드 최종 위치와 같이 보여 준다(읽기만).
# 배경: 사용자 ❄ 기록이 있으면 화면은 코드 위치(hover 포함)가 아니라 기록된 p 를 쓴다 — 코드를 고쳐도 사용자 화면에서 안 바뀌는 이유(드롭체커 29번 "리벳 분리해줘": 기록에 리벳이 제자리로 저장돼 있었다).
import json, os, re, sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import userdone
if len(sys.argv) < 4: sys.exit(__doc__)
name, k = sys.argv[1], int(sys.argv[2])
env = userdone._env(); url = (env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")).rstrip("/"); key = env["SUPABASE_SERVICE_ROLE_KEY"]
H = {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json", "Prefer": "return=representation"}
def req(method, path, body=None):
    r = urllib.request.Request(url + "/rest/v1/" + path, data=(json.dumps(body).encode("utf-8") if body is not None else None), headers=H, method=method)
    return json.loads(urllib.request.urlopen(r, timeout=20).read().decode("utf-8"))
mid = re.search(r'id: "(cubo-\d+-[A-Za-z0-9_]+)"', open(os.path.join(HERE, name + "_entry.js"), encoding="utf-8").read()).group(1)
q = "ivs_assembly_poses?assembly_id=eq.%s&step=eq.%d" % (mid, k); rows = req("GET", q)
if not rows: sys.exit("이 번호에 사용자 ❄ 기록이 없다")
poses = rows[0]["poses"]
if sys.argv[3] == "--보기":
    flt = sys.argv[4] if len(sys.argv) > 4 else ""
    asm = json.load(open(os.path.join(HERE, name + "_asm.json"), encoding="utf-8"))["steps"]; cnt, code = {}, {}
    for si, st in enumerate(asm, 1):
        for p in st.get("parts", []):
            cnt[p["n"]] = cnt.get(p["n"], 0) + 1
            if si == k: code["%s %d번" % (p["n"], cnt[p["n"]])] = p
    for lab in sorted(poses):
        if flt in lab and lab in code:
            c = code[lab]; print("  %-14s 기록 p=%s | 코드 최종 p=%s hover=%s" % (lab, [round(v, 1) for v in poses[lab].get("p", [])], [round(v, 1) for v in c["p"]], c.get("hover")))
    sys.exit(0)
bdir = os.path.join(HERE, "refs", name, "_pose_backup"); os.makedirs(bdir, exist_ok=True)
bk = os.path.join(bdir, "%02d_%s.json" % (k, time.strftime("%Y%m%d_%H%M%S"))); json.dump(rows[0], open(bk, "w", encoding="utf-8"), ensure_ascii=False); print("백업:", bk)
for tok in sys.argv[3].split(";"):
    lab, xyz = tok.rsplit(":", 1); p = [float(v) for v in xyz.split(",")]
    if lab not in poses: sys.exit("❌ 기록에 없는 라벨: " + lab)
    print("  %s: %s → %s" % (lab, poses[lab].get("p"), p)); poses[lab]["p"] = p
print("DB 갱신:", len(req("PATCH", q, {"poses": poses})), "행")

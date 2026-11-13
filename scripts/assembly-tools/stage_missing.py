# DB 에 안 올라간 그림(dbimgcheck ❌)을 public/_refs_tmp/<이름>/ 에 모아 staged.json 에 적는다 — 브라우저에서 viewer_snippets 3 의 올리기를 한 번에 돌린다(올린 뒤 폴더는 지운다).
#   python stage_missing.py <이름>   → 올릴 (번호, idx) 목록 출력
import asmpath
import json, os, re, shutil, subprocess, sys
name = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
out = subprocess.run([sys.executable, os.path.join(HERE, "dbimgcheck.py"), name], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8")).stdout
m = re.search(r"안 올림\(로컬에만 있음\): (.*)", out); items = [x.strip() for x in m.group(1).split(",")] if m and "없음" not in m.group(1) else []
idx = json.load(open(os.path.join(HERE, "refs", name, "index.json"), encoding="utf-8")); dst = os.path.join(HERE, "..", "..", "public", "_refs_tmp", name); os.makedirs(os.path.join(dst, "obs"), exist_ok=True)
shutil.copy(os.path.join(HERE, "refs", name, "index.json"), dst); want = []
for it in items:
    s, i = it.split("_"); r = [x for x in idx if x["step"] == int(s) and x["idx"] == int(i)]
    if r:
        f = r[0]["file"]; os.makedirs(os.path.dirname(os.path.join(dst, f)), exist_ok=True); shutil.copy(os.path.join(HERE, "refs", name, f), os.path.join(dst, f)); want.append([int(s), int(i)])
json.dump(want, open(os.path.join(dst, "staged.json"), "w")); print(json.dumps(want))

# 끝 점검(D14): 올릴 그림만 다루므로, 아직 만들지 않은 필수 산출물(격자·홀라인 그림 …)이 있는 번호를 끝에 보여 준다 — 이 도구 하나만 돌리고 끝난 줄 알지 않게.
try:
    import rulecheck as _rcq
    _res, _ = _rcq.check(name)
    _mm = {k_: [t_ for s_, t_, w_ in it_ if s_ == "❌" and _rcq.is_artifact(t_) and not t_.startswith("그림DB")] for k_, it_ in _res.items()}
    _mm = {k_: v_ for k_, v_ in _mm.items() if v_}
    print("빠진 필수 산출물(번호: 항목):", _mm if _mm else "없음")
except Exception as _e_: print("필수 산출물 점검을 못 했다:", str(_e_)[:80])

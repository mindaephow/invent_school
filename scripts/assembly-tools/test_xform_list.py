# xform(조립도 전체 뒤집기) 목록 지원 테스트: python test_xform_list.py
#   - xformlib.xform_at(meta, n) (파이썬 도구가 쓰는 공통 함수) 와
#   - public/design-mates.js 의 IVS_MATES.xformAt(def, step) (뷰어·검증이 쓰는 공통 함수, node 로 실행)
#   가 같은 규칙으로 고르는지 본다: 딕셔너리(기존) 그대로 · 목록이면 at <= 단계 인 항목 중 at 이 가장 큰 하나 · 없으면 None.
import json, os, shutil, subprocess, sys
import xformlib
HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.normpath(os.path.join(HERE, "..", "..", "public"))
A = {"at": 11, "m": [[1, 0, 0], [0, -1, 0], [0, 0, -1]], "t": [0, 83, 75]}
B = {"at": 40, "m": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "t": [0, 0, 0]}
# (이름, xform 값, 단계, 기대하는 at 또는 None)
CASES = [
    ("없음", None, 5, None),
    ("딕셔너리 경계 전", A, 10, None),
    ("딕셔너리 경계(at)", A, 11, 11),
    ("딕셔너리 경계 뒤", A, 99, 11),
    ("목록 첫 at 전", [A, B], 10, None),
    ("목록 첫 at", [A, B], 11, 11),
    ("목록 사이", [A, B], 39, 11),
    ("목록 둘째 at 경계", [A, B], 40, 40),
    ("목록 둘째 뒤", [A, B], 41, 40),
    ("목록 순서 뒤바뀜", [B, A], 39, 11),
    ("목록 순서 뒤바뀜 40", [B, A], 40, 40),
    ("빈 목록", [], 50, None),
    ("목록 한 개", [A], 11, 11),
]
fails = 0
def check(label, got_at, want):
    global fails
    ok = got_at == want
    if not ok: fails += 1
    print("%s %s: got %s want %s" % ("PASS" if ok else "FAIL", label, got_at, want))
for name, xf, n, want in CASES:
    meta = {} if xf is None else {"xform": xf}
    r = xformlib.xform_at(meta, n)
    check("py " + name + " n=%d" % n, None if r is None else r["at"], want)
# 같은 항목 객체를 돌려주는지(합성 없이 대체) — 40번 항목의 m·t 가 그대로여야 한다
r = xformlib.xform_at({"xform": [A, B]}, 40)
check("py 대체(합성 아님) t", r["t"], B["t"])
# JS 쪽
node = shutil.which("node")
if not node:
    print("SKIP js: node 없음")
else:
    js = r"""
const fs=require('fs');global.window={};
eval(fs.readFileSync(process.argv[1]+'/design-mates.js','utf8'));
const f=window.IVS_MATES.xformAt;
const cases=JSON.parse(process.argv[2]);
console.log(JSON.stringify(cases.map(c=>{const r=f(c.xform===null?{}:{xform:c.xform},c.n);return r?r.at:null})));
"""
    cases = [{"xform": xf, "n": n} for _, xf, n, _ in CASES]
    out = subprocess.run([node, "-e", js, PUB, json.dumps(cases)], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        fails += 1; print("FAIL js 실행:", out.stderr[:500])
    else:
        got = json.loads(out.stdout.strip().splitlines()[-1])
        for (name, xf, n, want), g in zip(CASES, got): check("js " + name + " n=%d" % n, g, want)
print("결과:", "모두 통과" if not fails else "%d건 실패" % fails)
sys.exit(1 if fails else 0)

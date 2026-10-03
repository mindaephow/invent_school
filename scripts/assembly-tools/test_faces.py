# faces.py(파이썬)와 public/design-faces.js(화면·MCP)가 모든 부품에서 같은 면·번호를 내는지 대조한다.
# 규칙을 바꿀 때(양쪽을 같이 고친 뒤) 반드시 돌린다:  python test_faces.py
import json, os, subprocess, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import partlib, faces

conn, _ = partlib.build_all()
JS = r"""
const fs=require('fs');const win={};new Function('window',fs.readFileSync('../../public/design-faces.js','utf8'))(win);
const conn=JSON.parse(fs.readFileSync('conn.json','utf8'));const out={};
for(const [n,c] of Object.entries(conn)){out[n]={};win.IVS_FACES.facesOf(c).forEach(f=>{out[n][f.key]=Object.fromEntries(f.items.map(i=>[i.id+'@'+i.label,[f.cols,f.rows]]))})}
console.log(JSON.stringify(out));
"""
json.dump(conn, open("conn.json", "w", encoding="utf-8"), ensure_ascii=False)   # JS 쪽이 같은 연결점 파일을 읽게
js = json.loads(subprocess.run(["node", "-e", JS], capture_output=True, text=True, encoding="utf-8").stdout)

bad = 0
for n, c in conn.items():
    py = {}
    for f in faces.faces_of(c):
        py[f["key"]] = {f"{it['id']}@{it['label']}": [f["cols"], f["rows"]] for it in f["items"]}
    if py != js.get(n):
        bad += 1
        print("불일치:", n)
        for k in sorted(set(py) | set(js.get(n, {}))):
            if py.get(k) != js.get(n, {}).get(k): print("  ", k, "파이썬", py.get(k), "/ JS", js.get(n, {}).get(k))
print(f"부품 {len(conn)}종 대조 — 불일치 {bad}종")
sys.exit(1 if bad else 0)

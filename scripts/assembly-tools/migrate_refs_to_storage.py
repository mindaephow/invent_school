# ivs_assembly_refs 의 base64 그림을 Storage 버킷 assembly-refs 로 옮긴다: 경로 <id>/<NN>_<idx>.jpg.
# PNG 는 JPEG 품질 90 으로 바꾸고(규칙 I1), 올린 것을 확인한 뒤에만 img 를 'storage:경로'로 바꾼다.
# data:image 가 아닌 행은 건너뛰므로 다시 돌려도 안전하다.
# 사용: python migrate_refs_to_storage.py [--limit N] <assembly_id> ...
# 2026-11-19 에 조립도 26개 전부 이 도구로 이전했다.
# ivs_assembly_refs 의 base64 그림(data:image/...)을 Storage(assembly-refs)로 옮기고 img 를 'storage:경로'로 바꾼다.
# 경로 규칙은 design.html refStore.save 와 같다: <assembly_id>/<NN>_<idx>.<jpg|png>. updated_at 은 건드리지 않는다.
import os, sys, io, json, base64, urllib.request, urllib.parse
from PIL import Image
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env.local"), encoding="utf-8"):
    if "=" in l and not l.startswith("#"): k, v = l.strip().split("=", 1); env[k] = v.strip('"')
U, K = env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]
H = {"apikey": K, "Authorization": "Bearer " + K}

def req(method, url, body=None, headers=None):
    r = urllib.request.Request(url, data=body, method=method, headers={**H, **(headers or {})})
    with urllib.request.urlopen(r, timeout=120) as resp: return resp.status, resp.read()

args = sys.argv[1:]; limit = None
if args and args[0] == "--limit": limit = int(args[1]); args = args[2:]
for aid in args:
    q = urllib.parse.urlencode({"assembly_id": "eq." + aid, "select": "id,step,idx", "order": "step,idx"})
    rows = json.loads(req("GET", f"{U}/rest/v1/ivs_assembly_refs?{q}")[1])
    if limit: rows = rows[:limit]
    ok = fail = skip = 0; conv = [0]
    for row in rows:
        try:
            img = json.loads(req("GET", f"{U}/rest/v1/ivs_assembly_refs?id=eq.{row['id']}&select=img")[1])[0]["img"]
            if not (img or "").startswith("data:image"): skip += 1; continue
            head, b64 = img.split(",", 1)
            mime = head[5:].split(";")[0] or "image/jpeg"
            data = base64.b64decode(b64)
            if mime != "image/jpeg":   # 규칙 I1: PNG 금지 → JPEG 품질 90·색 압축 없음(투명은 흰 바탕)
                im = Image.open(io.BytesIO(data))
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3]); im = bg
                else: im = im.convert("RGB")
                buf = io.BytesIO(); im.save(buf, "JPEG", quality=90, subsampling=0); data = buf.getvalue(); mime = "image/jpeg"; conv[0] += 1
            path = f"{aid}/{row['step']:02d}_{row['idx']}.jpg"
            req("POST", f"{U}/storage/v1/object/assembly-refs/" + "/".join(urllib.parse.quote(p) for p in path.split("/")),
                data, {"Content-Type": mime, "x-upsert": "true"})
            # 올라간 파일 크기 확인 뒤에만 경로를 바꾼다
            got = req("GET", f"{U}/storage/v1/object/authenticated/assembly-refs/{path}")[1]
            if got != data: raise RuntimeError(f"올린 파일이 다름 {len(got)} != {len(data)}")
            req("PATCH", f"{U}/rest/v1/ivs_assembly_refs?id=eq.{row['id']}", json.dumps({"img": "storage:" + path}).encode(),
                {"Content-Type": "application/json", "Prefer": "return=minimal"})
            ok += 1
        except Exception as e:
            fail += 1; print("  ❌", aid, row["step"], row["idx"], str(e)[:150], flush=True)
    print(aid, "옮김", ok, "(PNG→JPEG", conv[0], ") 건너뜀", skip, "실패", fail, "/", len(rows), flush=True)

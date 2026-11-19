# Storage 에 올라간 그림이 진짜 JPEG 인지 표본 점검. 사용: python spotcheck_storage_refs.py <{조립도:경로}.json>
import os, sys, io, json, urllib.request, urllib.parse
from PIL import Image
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env.local"), encoding="utf-8"):
    if "=" in l and not l.startswith("#"):
        k, v = l.strip().split("=", 1); env[k] = v.strip('"')
U, K = env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]
H = {"apikey": K, "Authorization": "Bearer " + K}
paths = json.load(open(sys.argv[1], encoding="utf-8"))  # {assembly: path}
for aid, p in paths.items():
    try:
        url = f"{U}/storage/v1/object/authenticated/assembly-refs/" + "/".join(urllib.parse.quote(x) for x in p.split("/"))
        with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
            b = r.read()
        im = Image.open(io.BytesIO(b)); im.load()
        print(aid, p, "FFD8" if b[:2] == b"\xff\xd8" else "NOT-JPEG", im.format, f"{im.width}x{im.height}", len(b))
    except Exception as e:
        print(aid, p, "ERR", type(e).__name__, str(e)[:80])

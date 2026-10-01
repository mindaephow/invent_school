# 부품 3D(STL)·연결점을 DB에서 내려받아 로컬 작업 폴더(parts/*.npy, conn.json, dims.json, viewer/parts.js)를 만든다.
# 사용: MCP URL(홍허브 발명학교-Mcp)을 환경변수 IVS_MCP_URL 에 두고  python extract_parts.py
import os,json,base64,struct,re,urllib.request,numpy as np
URL=os.environ["IVS_MCP_URL"]
def call(name,args):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":args}}).encode()
    req=urllib.request.Request(URL,body,{"Content-Type":"application/json","Accept":"application/json, text/event-stream"})
    t=urllib.request.urlopen(req,timeout=120).read().decode()
    if "data:" in t[:20]: t=[l[5:].strip() for l in t.splitlines() if l.startswith("data:")][-1]
    return json.loads(t)["result"]["content"][0]["text"]
def Rx(a):c,s=np.cos(a),np.sin(a);return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def Ry(a):c,s=np.cos(a),np.sin(a);return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rz(a):c,s=np.cos(a),np.sin(a);return np.array([[c,-s,0],[s,c,0],[0,0,1]])
os.makedirs("parts",exist_ok=True); os.makedirs("viewer",exist_ok=True)
rows=json.loads((lambda t:t[t.index("\n")+1:])(call("get_rows",{"table":"ivs_part_catalog","select":"id,data","limit":500})))
conn,dims,pj={},{},{}
for r in rows:
    d=r["data"]; n=d["name"]
    if not d.get("connectors") or not d.get("spec") or not d["spec"].get("shapes"): continue
    sh=[s for s in d["spec"]["shapes"] if s.get("type")=="import"]
    if not sh: continue
    sh=sh[0]; raw=base64.b64decode(sh["fileDataUrl"].split(",",1)[1]); nt=struct.unpack("<I",raw[80:84])[0]
    if 84+nt*50==len(raw): V=np.frombuffer(raw,dtype=np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")]),count=nt,offset=84)["v"].reshape(-1,3).astype(float)
    else: V=np.array(re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)",raw.decode("ascii","ignore")),dtype=float)
    V=np.stack([V[:,0],V[:,2],-V[:,1]],1)                       # STLLoader + rotateX(-90°)
    if (V.max(0)-V.min(0)).max()<5: V*=1000
    mn,mx=V.min(0),V.max(0); V=V-np.array([(mn[0]+mx[0])/2,mn[1],(mn[2]+mx[2])/2])
    V=V@(Rx(sh.get("rx",0))@Ry(sh.get("ry",0))@Rz(sh.get("rz",0))).T+np.array([sh.get("x",0),sh.get("y",0),sh.get("z",0)])
    V=V-(V.max(0)+V.min(0))/2                                     # bbox 가운데 = 부품 위치
    np.save(f"parts/{n}.npy",V.astype(np.float32)); conn[n]=d["connectors"]; dims[n]=[round(float(x),2) for x in V.max(0)-V.min(0)]
    pj[n]={"color":sh["color"],"pos":base64.b64encode(V.astype(np.float32).tobytes()).decode()}
json.dump(conn,open("conn.json","w",encoding="utf-8"),ensure_ascii=False); json.dump(dims,open("dims.json","w",encoding="utf-8"),ensure_ascii=False)
open("viewer/parts.js","w",encoding="utf-8").write("window.PARTS="+json.dumps(pj,ensure_ascii=False)+";")
open("viewer/conn.js","w",encoding="utf-8").write("window.CONN="+json.dumps(conn,ensure_ascii=False)+";")
print(len(conn),"parts")

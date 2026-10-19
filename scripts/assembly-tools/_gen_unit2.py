import re,sys,json
sys.stdout.reconfigure(encoding="utf-8")
p='battlerobot2.py'; s=open(p,encoding='utf-8').read()
a=s.index("# ── 1 ── 교재 60쪽 1"); b=s.index("# ── 11 ── 교재 62쪽 11")
src=s[a:b]
blocks=re.split(r"(?m)^(?=# ── \d+ ── )",src); blocks=[x for x in blocks if x.strip()]
names=["PL1","DC1","TA2","GR2","TA3","GR3","GR4","BU4","AX5","BU5","BL6","GR6","PL7","BU8","WH9","BU9","BL10A","BL10B","BL10C"]
pages={12:62,13:62,14:62,15:63,16:63,17:63,18:63,19:63,20:63,21:64}
def mx(mo): return "X2 - (%s)"%mo.group(1)
out={}
for blk in blocks:
    n=int(re.match(r"# ── (\d+) ──",blk).group(1)); m=n+11
    new=[]
    for ln in blk.split("\n"):
        if re.match(r"(R_X90|R_DC1|Y0|R_TM|R_PL7|R_BL10) =",ln) or ln.startswith("#") or "A.meta[" in ln or ".cam = (" in ln or not ln.strip(): continue
        ln=re.sub(r"SKEL\[%d\]"%(n-1),"SKEL[%d]"%(m-1),ln)
        ln=re.sub(r"\bs%d\b"%n,"s%d"%m,ln)
        ln=ln.replace("[교재 %d]"%n,"[교재 %d]"%m)
        ln=re.sub(r"np\.array\(\[(-?[\d.]+),",lambda mo:"np.array([X2 - (%s),"%mo.group(1),ln)
        ln=re.sub(r"p=\((-?[\d.]+),",lambda mo:"p=(X2 - (%s),"%mo.group(1),ln)
        ln=ln.replace("(0.0, Y0, 0.0)","(X2, Y0, 0.0)")
        ln=re.sub(r'"h(\d+)_(\d+)"',lambda mo:'"h%d_%s"'%(10-int(mo.group(1)),mo.group(2)),ln)   # 둘째 유닛은 첫째 유닛의 좌우 거울 — 판 칸 c → 10−c
        for nm in names: ln=re.sub(r"\b%s\b"%nm,nm+"U",ln)
        new.append(ln)
        if ln.startswith("s%d = SKEL"%m): new.append('s%d.kw["hideMade"] = {str(_i): "첫째 바퀴 유닛(1~11번)" for _i in range(1, 12)}'%m)
    out[m]="# ── %d ── 교재 %d쪽 %d (둘째 유닛: 첫째 유닛 %d번의 좌우 거울 — 같은 부품·같은 띄움, 판 칸 c→10−c, x 거울. 책 그림 시점은 번호마다 읽음. 창고 2 에서 만든다)\n"%(m,pages[m],m,n)+"\n".join(new)+"\n"
json.dump(out,open("_unit2_blocks.json","w",encoding="utf-8"),ensure_ascii=False)
print(out[12])

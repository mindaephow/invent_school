# 책 이미지 작업(새 방식, 관리자 지시 2026-10-09): 로봇은 똑바로 세운 채 회전만(늘이기·펴기 없음) 한 그림이고
# 파란 수직선(판 가운데 열)·수평선(판 가운데 줄)을 긋는다. 그림 전체를 옆으로 눕히지(90° 돌리지) 않는다. 방향은 원본의 위·아래·좌·우를 최대한 유지(거울 금지).
#   python refs_rect.py <이름> [번호 ...]   번호를 안 주면 fits 가 있는 모든 번호.  입력: refs/<이름>/NN.jpg(원본), NN_lv.json(자르기 영역 crop), fits/NN_<라벨>.json(구멍 점, 원본 좌표)
#   출력: refs/<이름>/NN_1.jpg(보정한 그림 + 수직·수평선), NN_2.jpg(+ 격자 점·칸·줄 번호), index.json 의 ③·④ 설명 갱신. 점이 없는 번호(한 줄 막대)는 막대 축이 수직/수평이 되게 회전만 한다.
import json, os, glob, re, sys, math
import cv2, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
NAME = sys.argv[1]
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', NAME) + os.sep
INDEX=json.load(open(D+'index.json',encoding='utf-8'))
ORANGE=(255,140,0)
def oldnames(step):
    for r in INDEX:
        if r['step']==step and r['idx']==2: return r.get('names') or []
    return []
def pick_orientation(pts,cols,rows):
    best=None
    src=np.array([[p[2],p[3]] for p in pts],np.float32)
    for swap in (False,True):
        for fa in (False,True):
            for fb in (False,True):
                dst=[]
                for p in pts:
                    c=(cols-1-(p[0]-1)) if fa else p[0]-1
                    r=(rows-1-(p[1]-1)) if fb else p[1]-1
                    dst.append([r,c] if swap else [c,r])
                dst=np.array(dst,np.float32)
                A,_=cv2.estimateAffine2D(src,dst,method=cv2.LMEDS)
                if A is None: continue
                L=A[:,:2]
                if np.linalg.det(L)<=0: continue
                ang=math.degrees(math.atan2(L[1,0]-L[0,1],L[0,0]+L[1,1]))
                key=abs(ang)
                if best is None or key<best[0]: best=(key,swap,fa,fb)
    return best
def pitch(pts):
    d=defaultdict(dict) if False else {}
    for p in pts: d[(p[0],p[1])]=(p[2],p[3])
    ds=[]
    for (c,r),v in d.items():
        for k in ((c+1,r),(c,r+1)):
            if k in d: ds.append(math.hypot(v[0]-d[k][0],v[1]-d[k][1]))
    return float(np.mean(ds)) if ds else 34.0
def side(vals_by_idx, axis):
    pass
def process(step):
    nm='%02d'%step
    if not os.path.exists(D+nm+'_lv.json'):   # 새 번호: 쪽 테두리를 뺀 기본 자르기(글씨·배지는 crop 을 고쳐 다시)
        _h,_w=cv2.imread(D+nm+'.jpg').shape[:2]; json.dump({'M':[[1,0,0],[0,1,0]],'size':[_w-50,_h-50],'angle':0.0,'crop':[25,25,_w-25,_h-25],'erase':[['c',_w,_h,150]]},open(D+nm+'_lv.json','w'))   # 오른쪽 아래 번호 배지 지움
    Mj=json.load(open(D+nm+'_lv.json')); cx0,cy0,cx1,cy1=Mj['crop']
    full=cv2.imread(D+nm+'.jpg')
    for e in Mj.get('erase',[]):   # 글씨·번호 배지·아이콘 지우기: ['r',x0,y0,x1,y1] 사각형 / ['c',cx,cy,r] 원(원본 좌표)
        if e[0]=='r': full[int(e[2]):int(e[4]),int(e[1]):int(e[3])]=255
        else: cv2.circle(full,(int(e[1]),int(e[2])),int(e[3]),(255,255,255),-1)
    crop=full[cy0:cy1,cx0:cx1]; h,w=crop.shape[:2]
    fits=[]
    for f in sorted(glob.glob(D+'fits/%s_*.json'%nm)):
        j=json.load(open(f,encoding='utf-8')); fits.append((os.path.basename(f)[3:-5],j))
    names=oldnames(step)
    if not fits:   # 점이 없는 단계(32번 한 줄 막대): 막대 축이 수직/수평이 되도록 회전만
        ang=Mj['angle']; res=ang-90.0*round(ang/90.0)
        Mx=cv2.getRotationMatrix2D((w/2,h/2),res,1.0); cs,sn=abs(Mx[0,0]),abs(Mx[0,1]); W,H=int(h*sn+w*cs)+1,int(h*cs+w*sn)+1
        Mx[0,2]+=W/2-w/2; Mx[1,2]+=H/2-h/2
        out=cv2.warpAffine(crop,Mx,(W,H),flags=cv2.INTER_CUBIC,borderValue=(255,255,255)); vx,hy=W/2,H/2
        info={'err':0.0,'canvas':(W,H),'c1':'-','r1':'-','ref':'(점 없음)','res':round(res,2)}
        base=out.copy(); g=None
    else:
        ref=max(fits,key=lambda t:len(t[1]['pts'])); rl,rj=ref; pts=rj['pts']; cols,rows=rj['cols'],rj['rows']
        if not names: names=[rj.get('name') or '기준 판']   # fits 파일에 name 을 적어 두면 설명에 그 이름을 쓴다(판이 아닌 L 브래킷 등)
        # ★ 회전만(관리자 지시 2026-10-09 — "회전을 하라고 했는데 왜 이미지를 뭉개 놓았나"): 판의 칸 방향(구멍이 늘어선 방향)이 수평(또는 수직)에 가장 가까워지도록 작은 각도만 돌린다. 늘이거나 기울여 펴지 않아 화질이 그대로다. 그림 전체를 90° 눕히지도 않는다.
        swap=False; fa=fb=False
        _P={(q[0],q[1]):(q[2],q[3]) for q in pts}; _vs=[(_P[(c+1,r)][0]-_P[(c,r)][0],_P[(c+1,r)][1]-_P[(c,r)][1]) for (c,r) in _P if (c+1,r) in _P]; _off=0.0
        if not _vs: _vs=[(_P[(c,r+1)][0]-_P[(c,r)][0],_P[(c,r+1)][1]-_P[(c,r)][1]) for (c,r) in _P if (c,r+1) in _P]; _off=90.0
        _a=math.degrees(math.atan2(np.mean([v[1] for v in _vs]),np.mean([v[0] for v in _vs]))) - _off
        _res=_a-90.0*round(_a/90.0)                     # 가장 가까운 수평·수직까지의 작은 각도
        Mr=cv2.getRotationMatrix2D((w/2.0,h/2.0),_res,1.0); _cs,_sn=abs(Mr[0,0]),abs(Mr[0,1]); W,H=int(h*_sn+w*_cs)+1,int(h*_cs+w*_sn)+1
        Mr[0,2]+=W/2.0-w/2.0; Mr[1,2]+=H/2.0-h/2.0
        A2=Mr.astype(np.float32); sc=1.0
        out=cv2.warpAffine(crop,A2,(W,H),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
        MASK=cv2.warpAffine(np.full((h,w),255,np.uint8),A2,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)   # 그림이 있는 영역(다른 평면 판의 점이 그림 밖에 찍히지 않게)
        T=lambda x,y: A2@np.array([x-cx0,y-cy0,1.0])
        err=0.0; _ov=False
        # 가운데 열(수직선)·가운데 줄(수평선): 격자 가운데 칸/줄
        _cv=sorted({q[0] for q in pts}); _rv=sorted({q[1] for q in pts}); cc=_cv[(len(_cv)-1)//2]; rc=_rv[(len(_rv)-1)//2]   # 있는 칸·줄 번호 중 가운데(일부 칸만 있는 판도 된다)
        tp={ (p[0],p[1]):T(p[2],p[3]) for p in pts }
        _cn=min(tp.items(),key=lambda kv: abs(kv[0][0]-cc)+abs(kv[0][1]-rc))[1]   # 가운데 칸·줄에 가장 가까운 노드
        vx=float(_cn[0]); hy=float(_cn[1])                                          # 수직선 = 그 노드의 x, 수평선 = 그 노드의 y
        xax,yax=0,1
        # 칸1·줄1 위치(위/아래/왼/오른)
        def where(ax):  # ax 0=칸 1=줄
            _m=min((c,r)[ax] for (c,r) in tp); v1=np.mean([vv for (c,r),vv in tp.items() if (c,r)[ax]==_m],axis=0); vm=np.mean([vv for (c,r),vv in tp.items()],axis=0)
            dx,dy=v1[0]-vm[0],v1[1]-vm[1]
            return ('왼쪽' if dx<0 else '오른쪽')+' 끝' if abs(dx)>=abs(dy) else ('위' if dy<0 else '아래')+' 끝'
        info={'err':round(err/sc,2),'canvas':(W,H),'c1':where(0),'r1':where(1),'ref':rl,'res':None,'cols':cols,'rows':rows,'overlay':_ov}
        base=out.copy()
        g=base.copy()
    # 선 긋기(수평·수직)
    _axf0=D+nm+'_axes.json'; _AX0=json.load(open(_axf0,encoding='utf-8')) if os.path.exists(_axf0) else {}
    def lines(im):
        Hh,Ww=im.shape[:2]
        if _AX0.get('replace_lines') and _AX0.get('global'):   # 수평·수직선 대신 기준 점(vx,hy)을 지나는 X(빨강)·Z(파랑)·Y(초록) 축선(관리자 제안 2026-10-11: 방향은 x,y,z 축으로)
            _Lx=(A2[:,:2] if fits else Mx[:,:2]).astype(np.float64); _C={'X':(40,40,230),'Y':(40,170,40),'Z':(230,110,20)}
            for k_,v_ in _AX0['global'].items():
                d_=_Lx@np.array(v_,float); n_=float(np.hypot(*d_)) or 1.0; d_=d_/n_
                t_=max(Ww,Hh)*2; cv2.line(im,(int(vx-d_[0]*t_),int(hy-d_[1]*t_)),(int(vx+d_[0]*t_),int(hy+d_[1]*t_)),_C[k_],2,cv2.LINE_AA)
                # 화면 안 가장자리 가까이에 축 이름
                for sg in (1,-1):
                    ex,ey=vx+sg*d_[0]*min(Ww,Hh)*0.42,hy+sg*d_[1]*min(Ww,Hh)*0.42
                    if 20<ex<Ww-40 and 30<ey<Hh-20: cv2.putText(im,('+' if sg==1 else '-')+k_,(int(ex),int(ey)),cv2.FONT_HERSHEY_SIMPLEX,0.7,_C[k_],2,cv2.LINE_AA)
            return
        cv2.line(im,(0,int(round(hy))),(Ww,int(round(hy))),ORANGE,2,cv2.LINE_AA); cv2.putText(im,'horizontal',(Ww-130,int(hy)-8),cv2.FONT_HERSHEY_SIMPLEX,0.55,ORANGE,2)
        cv2.line(im,(int(round(vx)),0),(int(round(vx)),Hh),ORANGE,2,cv2.LINE_AA); cv2.putText(im,'vertical',(int(vx)+8,28),cv2.FONT_HERSHEY_SIMPLEX,0.55,ORANGE,2)
    lines(base)
    if g is not None:
        g=base.copy()
        gray=cv2.cvtColor(out,cv2.COLOR_BGR2GRAY)
        def on_picture(j):   # 다른 평면에 있어 이 보정에서는 그림 밖 빈 곳에 찍히는 판은 그리지 않는다(구멍 점 주변이 판 색이어야 한다)
            ok=0
            for p in j['pts']:
                x,y=T(p[2],p[3]); x,y=int(x),int(y)
                if 0<=x<W and 0<=y<H and MASK[y,x]>128 and gray[max(0,y-14):y+15,max(0,x-14):x+15].min()<225: ok+=1
            return ok>=0.6*len(j['pts'])
        for lab,j in fits:
            if lab!=rl and not on_picture(j): continue
            P_={(q[0],q[1]):T(q[2],q[3]) for q in j['pts']}   # 격자선: 같은 칸끼리·같은 줄끼리 번호 순서로 이웃한 점을 잇는다(번호가 건너뛰어도, 줄 번호가 소수여도 된다)
            for key_,idx_ in ((0,1),(1,0)):
                grp_={}
                for k_ in P_: grp_.setdefault(k_[key_],[]).append(k_)
                for ks_ in grp_.values():
                    ks_.sort(key=lambda k: k[idx_])
                    for a_,b_ in zip(ks_,ks_[1:]): cv2.line(g,(int(P_[a_][0]),int(P_[a_][1])),(int(P_[b_][0]),int(P_[b_][1])),(0,0,255),1,cv2.LINE_AA)
            for p in j['pts']:
                x,y=T(p[2],p[3])
                if not (0<=int(x)<W and 0<=int(y)<H and MASK[int(y),int(x)]>128): continue
                cv2.circle(g,(int(x),int(y)),3,(0,0,255),-1)
                if p[1]==1: cv2.putText(g,str(p[0]),(int(x)-7,int(y)-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,0,0),2)
                if p[0]==1: cv2.putText(g,'j%d'%p[1],(int(x)-30,int(y)+5),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,140,0),2)
    else: g=base.copy()
    # ── 방향 화살표(선택, 관리자 제안 2026-10-11): <번호>_axes.json 이 있으면 X(빨강)·Y(초록)·Z(파랑) 방향을 오른쪽 위에 한 번(전체), 필요한 곳(local)에 또 그린다. 그림은 변형하지 않고 덧그리기만 한다.
    #   {"global": {"X": [dx,dy], "Y": [dx,dy], "Z": [dx,dy]}, "local": [{"at": [x,y], "label": "DC모터", "X": [dx,dy], "Y": [...], "Z": [...]}]}  — 벡터와 at 은 원본 그림(NN.jpg) 화면 좌표(오른쪽 +x, 아래 +y), 안 쓰는 축은 빼도 된다.
    axf=D+nm+'_axes.json'
    if os.path.exists(axf):
        AXJ=json.load(open(axf,encoding='utf-8')); _L=(A2[:,:2] if fits else Mx[:,:2]).astype(np.float64)
        _COL={'X':(40,40,230),'Y':(40,170,40),'Z':(230,110,20)}   # BGR: 빨강·초록·파랑(조립 보기 화면의 +X·+Y·+Z 색과 같다)
        def _gizmo(im,ox,oy,vecs,size,title=None):
            if title: cv2.putText(im,title,(int(ox)-int(size)-6,int(oy)-int(size)-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(60,60,60),2,cv2.LINE_AA)
            mx=max(float(np.hypot(*(_L@np.array(v,float)))) for v in vecs.values()) or 1.0
            for k_,v_ in vecs.items():
                w_=_L@np.array(v_,float)*(size/mx); ex,ey=ox+w_[0],oy+w_[1]
                cv2.arrowedLine(im,(int(ox),int(oy)),(int(ex),int(ey)),_COL[k_],4,cv2.LINE_AA,tipLength=0.22)
                cv2.putText(im,'+'+k_,(int(ex+(8 if w_[0]>=0 else -34)),int(ey+(8 if w_[1]>=0 else -4))),cv2.FONT_HERSHEY_SIMPLEX,0.8,_COL[k_],2,cv2.LINE_AA)
            cv2.circle(im,(int(ox),int(oy)),4,(60,60,60),-1)
        for im_ in (base,g):
            if AXJ.get('global'): _gizmo(im_,im_.shape[1]-120,100,AXJ['global'],70,'방향')
            for lc in AXJ.get('local',[]):
                _o=(T(lc['at'][0],lc['at'][1]) if fits else Mx@np.array([lc['at'][0]-cx0,lc['at'][1]-cy0,1.0]))
                _gizmo(im_,float(_o[0]),float(_o[1]),{k:lc[k] for k in 'XYZ' if k in lc},float(lc.get('size',45)),lc.get('label'))
    cv2.imwrite(D+nm+'_1.jpg',base,[cv2.IMWRITE_JPEG_QUALITY,88]); cv2.imwrite(D+nm+'_2.jpg',g,[cv2.IMWRITE_JPEG_QUALITY,88])
    return info,names
def sentence(step,info,names):
    if not names and info.get('cols'): names=['%d칸×%d줄 판'%(info['cols'],info['rows'])]
    nm=' / '.join(names) if names else '판'
    if info['ref']=='(점 없음)':
        n1="③ 단계 %d — 로봇(부품)은 똑바로 세운 채, 한 줄 막대의 축이 수직·수평이 되도록 회전만 %.1f° 한 그림 + 파란 수직선·수평선(점 없음)."%(step,info['res'])
        n2="④ 단계 %d — 한 줄 프레임은 구멍 점이 일직선이라 격자 점을 만들지 않았다(③과 같은 그림)."%step
    else:
        if info.get('overlay'):
            n1="③ 단계 %d — 판을 아주 비스듬히 본 그림이라 펴지 않고(보정하면 뭉개짐) 원본 그대로 두고 수직선·수평선(화면 기준선)을 그은 그림. 칸1 = %s, 줄1 = %s (격자 번호는 ④ 에서)."%(step,info['c1'],info['r1'])
            n2="④ 단계 %d — 원본 위의 격자: %s. 빨강 점 = 구멍 중심, 초록 숫자 = 칸, j1~ = 줄(구멍 중심을 검출해 맞춘 점, 칸·줄 번호가 점 옆에 적힘)."%(step,nm)
            return n1,n2
        n1="③ 단계 %d — 로봇(부품)은 똑바로 세운 채, %s 의 구멍 줄이 수평에 가깝도록 회전만 한 그림(늘이거나 펴지 않음)(구멍 흰 틈 점으로 맞춤, 평균 오차 %.1fpx). 파란 수직선 = 판 가운데 열, 파란 수평선 = 판 가운데 줄. 칸1 = %s, 줄1 = %s."%(step,names[0] if names else '기준 판',info['err'],info['c1'],info['r1'])
        n2="④ 단계 %d — 같은 그림 위의 격자: %s. 빨강 점 = 구멍 중심, 초록 숫자 = 칸, j1~ = 줄. 칸1 = %s, 줄1 = %s."%(step,nm,info['c1'],info['r1'])
    return n1,n2
if __name__=='__main__':
    steps=[int(s) for s in sys.argv[2:]]
    if not steps: steps=sorted({int(os.path.basename(f)[:2]) for f in glob.glob(D+'fits/*.json')}|{r['step'] for r in INDEX if r['idx']==2 and os.path.exists(D+'%02d_lv.json'%r['step'])})
    for s in steps:
        info,names=process(s); print(s,info)
        n1,n2=sentence(s,info,names)
        for _i,_f in ((1,'%02d_1.jpg'%s),(2,'%02d_2.jpg'%s)):
            if not any(r['step']==s and r['idx']==_i for r in INDEX): INDEX.append({'step':s,'idx':_i,'file':_f,'note':''})
        for r in INDEX:
            if r['step']==s and r['idx']==0 and not str(r.get('note','')).startswith('①'): r['note']='① '+str(r.get('note',''))
            if r['step']==s and r['idx']==1: r['note']=n1
            if r['step']==s and r['idx']==2: r['note']=n2
    INDEX.sort(key=lambda r:(r['step'],r['idx'])); json.dump(INDEX,open(D+'index.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

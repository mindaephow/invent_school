# 책 이미지 작업(새 방식, 관리자 지시 2026-10-09): 로봇은 똑바로 세운 채 회전만(늘이기·펴기 없음) 한 그림이고
# X(빨강)·Z(파랑)·Y(초록) 축선을 긋는다. 그림 전체를 옆으로 눕히지(90° 돌리지) 않는다. 방향은 원본의 위·아래·좌·우를 최대한 유지(거울 금지).
#   python refs_rect.py <이름> [번호 ...]   번호를 안 주면 fits 가 있는 모든 번호.  입력: refs/<이름>/NN.jpg(원본), NN_lv.json(자르기 영역 crop), fits/NN_<라벨>.json(구멍 점, 원본 좌표)
#   axes.json 의 "column_axis": "Y" = 서 있는 판처럼 가운데 열이 Z 가 아니라 Y 선을 따를 때 그 축을 적는다.
#   출력: refs/<이름>/NN_1.jpg(보정한 그림 + X·Y·Z 축선), NN_2.jpg(+ 격자 점·칸·줄 번호), index.json 의 ③·④ 설명 갱신. 점이 없는 번호(한 줄 막대)는 막대 축이 수직/수평이 되게 회전만 한다.
import json, os, glob, re, sys, math
import cv2, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
NAME = sys.argv[1]
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', NAME) + os.sep
INDEX=json.load(open(D+'index.json',encoding='utf-8'))
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
LV_ROT=None   # <번호>_axes.json 에 "level": true 가 있으면 판 구멍 줄이 수평이 되게 그림을 돌리고(1번 그림처럼), 축선·방향 표시도 같은 회전을 따라간다
def _rotg(d):
    return {k:(list(LV_ROT@np.array(v,float)) if LV_ROT is not None else v) for k,v in d.items()}

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
        _axr=D+nm+'_axes.json'; _AXj=json.load(open(_axr,encoding='utf-8')) if os.path.exists(_axr) else {}; _Xv=(_AXj.get('global') or {}).get(_AXj.get('rotate_to') or '')
        _res=_a-90.0*round(_a/90.0)                     # 가장 가까운 수평·수직까지의 작은 각도
        if _Xv:
            # 가운데 줄·가운데 열 구멍을 지나는 직선의 방향으로 맞춘다 — 줄들은 원근 때문에 부채꼴로 퍼져 줄마다 각도가 다르므로(첫 줄 41°·가운데 줄 38°) 줄 평균이나 첫 줄이 아니라 축선이 지나는 가운데 줄·가운데 열을 쓴다
            _cs0=sorted({q[0] for q in pts}); _rs0=sorted({q[1] for q in pts}); _cm=_cs0[(len(_cs0)-1)//2]; _rm=_rs0[(len(_rs0)-1)//2]
            def _ln(sel):
                V_=np.array([(q[2],q[3]) for q in pts if sel(q)],float)
                if len(V_)<2: return None
                u_,s_,vt_=np.linalg.svd(V_-V_.mean(0)); return math.degrees(math.atan2(vt_[0][1],vt_[0][0]))
            _wr=lambda d_:((d_+90.0)%180.0)-90.0
            _aR=_ln(lambda q:q[1]==_rm); _aC=_ln(lambda q:q[0]==_cm); _oth=_AXj.get('column_axis') or {'X':'Z','Z':'X'}.get(_AXj.get('rotate_to')); _Ov=(_AXj.get('global') or {}).get(_oth) if _oth else None
            _eR=_wr(_aR-math.degrees(math.atan2(_Xv[1],_Xv[0]))) if _aR is not None else None; _eC=_wr(_aC-math.degrees(math.atan2(_Ov[1],_Ov[0]))) if (_aC is not None and _Ov and len(_rs0)>=2) else None
            _es=[e_ for e_ in (_eR,_eC) if e_ is not None]; _res=sum(_es)/len(_es) if _es else _res
            print('  회전 근거: 가운데 줄 어긋남 %s° / 가운데 열 어긋남 %s° → 회전 %.2f°'%('-' if _eR is None else '%.2f'%_eR,'-' if _eC is None else '%.2f'%_eC,_res))
        global LV_ROT; LV_ROT=None
        if _AXj.get('level'): _res=_wr(_a) if _a is not None else _res
        if _AXj.get('no_rotate'): _res=0.0   # no_rotate: 구멍 줄이 없는 번호(링 점만 찍는 그림)는 회전하지 않는다(투석기 24번)   # 가운데 줄이 아니라 판 전체 구멍 줄 방향(_a)을 수평으로 — 원근 부채꼴이라 줄마다 다르지만 평균 방향
        Mr=cv2.getRotationMatrix2D((w/2.0,h/2.0),_res,1.0); _cs,_sn=abs(Mr[0,0]),abs(Mr[0,1]); W,H=int(h*_sn+w*_cs)+1,int(h*_cs+w*_sn)+1
        Mr[0,2]+=W/2.0-w/2.0; Mr[1,2]+=H/2.0-h/2.0
        A2=Mr.astype(np.float32); sc=1.0
        if _AXj.get('level'): LV_ROT=A2[:2,:2].astype(float)
        out=cv2.warpAffine(crop,A2,(W,H),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
        MASK=cv2.warpAffine(np.full((h,w),255,np.uint8),A2,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)   # 그림이 있는 영역(다른 평면 판의 점이 그림 밖에 찍히지 않게)
        T=lambda x,y: A2@np.array([x-cx0,y-cy0,1.0])
        err=0.0; _ov=bool(_AXj.get('no_rotate'))
        # 가운데 열·가운데 줄: 격자 가운데 칸/줄
        _cv=sorted({q[0] for q in pts}); _rv=sorted({q[1] for q in pts}); cc=_cv[(len(_cv)-1)//2]; rc=_rv[(len(_rv)-1)//2]   # 있는 칸·줄 번호 중 가운데(일부 칸만 있는 판도 된다)
        tp={ (p[0],p[1]):T(p[2],p[3]) for p in pts }
        _cn=min(tp.items(),key=lambda kv: abs(kv[0][0]-cc)+abs(kv[0][1]-rc))[1]   # 가운데 칸·줄에 가장 가까운 노드
        vx=float(_cn[0]); hy=float(_cn[1])                                          # 축선 원점 = 그 노드
        if _Xv:   # rotate_to 를 정했으면 축선 중심을 기준 판(점이 가장 많은 판)의 중심으로 둔다 — 축선이 그 판의 가운데 줄·가운데 열 위로 지나게(판이 둘이면 두 판의 점을 합친 평균이 아니다: 중심이 기준 판에서 벗어났었다)
            _cs=sorted({q[0] for q in pts}); _rs=sorted({q[1] for q in pts}); _mc={_cs[(len(_cs)-1)//2],_cs[len(_cs)//2]}; _mr={_rs[(len(_rs)-1)//2],_rs[len(_rs)//2]}; _mr={_AXj['center_row']} if _AXj.get('center_row') else _mr   # center_row: 줄이 짝수(2줄 프레임)면 가운데가 구멍 줄 사이라 선이 구멍을 안 지난다 — 그 줄 번호를 정하면 선이 그 구멍 줄의 구멍 중심을 지난다(투석기 20번)   # 가운데 칸·가운데 줄의 구멍(짝수면 가운데 두 개의 중점) — 점 전체의 평균은 원근 때문에 가운데 구멍에서 벗어난다
            _tc=np.mean([T(q[2],q[3]) for q in pts if q[0] in _mc and q[1] in _mr],axis=0); vx=float(_tc[0]); hy=float(_tc[1])
        _oc=rj.get('origin_cell') or _AXj.get('origin_cell')   # 판 가운데가 다른 부품에 가려져 있으면(드롭체커 24번 — 모터 밑) 축선 원점을 눈에 보이는 구멍 위로 옮긴다(축선은 보이는 구멍 줄의 구멍 중심을 지난다 — 사용자 지적 2026-10-13)
        LOCDIR={}
        if _oc and tuple(_oc) in tp:
            vx,hy=float(tp[tuple(_oc)][0]),float(tp[tuple(_oc)][1])
            # 원점 구멍 가까이에서 구멍이 실제로 늘어선 방향으로 X·Z 축선을 긋는다 — 판 가운데에서 계산한 전역 방향을 평행 이동하면 원근 때문에 보이는 홀라인과 어긋난다(사용자 지적 2026-10-13: 보이는 쪽 홀라인에 맞춘다)
            _c0,_r0=tuple(_oc); _fit=(_AXj.get('fit') or {})
            for _ax_,_nm_ in ((_fit.get('cols'),'c'),(_fit.get('rows'),'r')):
                if _ax_ in ('+X','-X','+Z','-Z'):
                    _a=((_c0-1,_r0),(_c0+1,_r0)) if _nm_=='c' else ((_c0,_r0-1),(_c0,_r0+1))
                    if _a[0] in tp and _a[1] in tp:
                        _d=np.array(tp[_a[1]],float)-np.array(tp[_a[0]],float); _d=_d*(1.0 if _ax_[0]=='+' else -1.0)
                        LOCDIR[_ax_[1]]=[float(_d[0]),float(_d[1])]
        xax,yax=0,1
        # 칸1·줄1 위치(위/아래/왼/오른)
        def where(ax):  # ax 0=칸 1=줄
            _m=min((c,r)[ax] for (c,r) in tp); v1=np.mean([vv for (c,r),vv in tp.items() if (c,r)[ax]==_m],axis=0); vm=np.mean([vv for (c,r),vv in tp.items()],axis=0)
            dx,dy=v1[0]-vm[0],v1[1]-vm[1]
            return ('왼쪽' if dx<0 else '오른쪽')+' 끝' if abs(dx)>=abs(dy) else ('위' if dy<0 else '아래')+' 끝'
        info={'err':round(err/sc,2),'canvas':(W,H),'c1':where(0),'r1':where(1),'ref':rl,'res':None,'cols':cols,'rows':rows,'overlay':_ov,'split':bool((json.load(open(D+nm+'_axes.json',encoding='utf-8')) if os.path.exists(D+nm+'_axes.json') else {}).get('split'))}
        base=out.copy()
        g=base.copy()
    # 축선 긋기
    _axf0=D+nm+'_axes.json'; _AX0=json.load(open(_axf0,encoding='utf-8')) if os.path.exists(_axf0) else {}
    _RLB=_AX0.get('relabel') or {}   # 축 이름 바꿔 보이기(완성 사진 방향 기준, 2026-10-14): {"X":["Z",-1],"Z":["X",1]} = 원래 X 선은 새 Z(부호 반대), 원래 Z 선은 새 X. 선 위치·벡터는 그대로 두고 글자·색만 바꾼다
    _rn=lambda k:_RLB.get(k,[k,1])[0]; _rs=lambda k:_RLB.get(k,[k,1])[1]
    def lines(im):
        Hh,Ww=im.shape[:2]
        if not _AX0.get('global'): print('  ⚠ %s_axes.json 에 global(X·Y·Z 화면 방향)이 없어 축선을 못 그렸다'%nm); return
        _Lx=LV_ROT if LV_ROT is not None else np.eye(2);   # 가운데 축선은 이미지 회전과 같이 돌리지 않는다(관리자 지시 2026-10-12) — 읽은 원래 화면 방향 그대로. 단 level 옵션이면 같이 돌린다
        _C={'X':(40,40,230),'Y':(40,170,40),'Z':(230,110,20)}
        for k_,v_ in _AX0['global'].items():
            d_=np.array(LOCDIR[k_],float) if k_ in LOCDIR else _Lx@np.array(v_,float); n_=float(np.hypot(*d_)) or 1.0; d_=d_/n_
            t_=max(Ww,Hh)*2; cv2.line(im,(int(vx-d_[0]*t_),int(hy-d_[1]*t_)),(int(vx+d_[0]*t_),int(hy+d_[1]*t_)),_C[_rn(k_)],2,cv2.LINE_AA)
            # 화면 안 가장자리 가까이에 축 이름
            for sg in (1,-1):
                ex,ey=vx+sg*d_[0]*min(Ww,Hh)*0.42,hy+sg*d_[1]*min(Ww,Hh)*0.42
                if 20<ex<Ww-40 and 30<ey<Hh-20: cv2.putText(im,('+' if sg*_rs(k_)==1 else '-')+_rn(k_),(int(ex),int(ey)),cv2.FONT_HERSHEY_SIMPLEX,0.7,_C[_rn(k_)],2,cv2.LINE_AA)
    _SPLIT=bool(_AX0.get('split'))   # split: NN_1 = 홀라인용(구멍 점 + 구멍 줄 직선, 축선 없음), NN_2 = 카메라 판단용(X·Y·Z 축선만, 점 없음)
    _plain=base.copy()
    lines(base)
    if fits and _AX0.get('rotate_to') and _AX0.get('global'):   # 화면에 그린 축선(가운데 구멍을 지남)과 가운데 줄·가운데 열 구멍 사이의 실제 거리(px)
        _gl=_rotg(_AX0['global']); _d2=lambda v_:(lambda d_:d_/(np.hypot(*d_) or 1.0))(np.array(v_,float))
        _ax_=_AX0['rotate_to']; _oth_=_AX0.get('column_axis') or {'X':'Z','Z':'X'}.get(_ax_)
        def _off(sel,vec):
            dd_=_d2(vec); nn_=np.array([-dd_[1],dd_[0]]); return [round(float((np.array(tp[k],float)-np.array([vx,hy]))@nn_),1) for k in sorted(tp) if sel(k)]
        print('  축선↔구멍 거리 px — 가운데 줄 구멍 vs %s 선:'%_ax_,_off(lambda k:k[1]==_rm,_gl[_ax_]),'| 가운데 열 구멍 vs %s 선:'%_oth_,_off(lambda k:k[0]==_cm,_gl[_oth_]) if (_oth_ and _oth_ in _gl and len(_rs0)>=2) else '-')
    if g is not None:
        g=(_plain if _SPLIT else base).copy()
        gray=cv2.cvtColor(out,cv2.COLOR_BGR2GRAY)
        def on_picture(j):   # 다른 평면에 있어 이 보정에서는 그림 밖 빈 곳에 찍히는 판은 그리지 않는다(구멍 점 주변이 판 색이어야 한다)
            ok=0
            for p in j['pts']:
                x,y=T(p[2],p[3]); x,y=int(x),int(y)
                if 0<=x<W and 0<=y<H and MASK[y,x]>128 and gray[max(0,y-14):y+15,max(0,x-14):x+15].min()<225: ok+=1
            return ok>=0.6*len(j['pts'])
        for lab,j in fits:
            if lab!=rl and not on_picture(j): continue
            P_={(q[0],q[1]):T(q[2],q[3]) for q in j['pts'] if not (_AX0.get('hide_est') and [q[0],q[1]] in j.get('est',[]))}   # 격자선: 같은 칸끼리·같은 줄끼리 번호 순서로 이웃한 점을 잇는다(번호가 건너뛰어도, 줄 번호가 소수여도 된다)
            for key_,idx_ in (() if _AX0.get('no_lines') else (((1,0),) if _AX0.get('grid_rows_only') else ((0,1),(1,0)))):   # no_lines: 점과 번호만(칸·줄 격자가 아닌 링 점 모음)   # grid_rows_only: 줄이 둘뿐이거나 옆면을 비스듬히 본 프레임은 칸 사이 세로선이 기울어 평행사변형처럼 보이므로 구멍 줄(홀 라인)만 긋는다(투석기 20번)
                grp_={}
                for k_ in P_: grp_.setdefault(k_[key_],[]).append(k_)
                for ks_ in grp_.values():
                    ks_.sort(key=lambda k: k[idx_])
                    for a_,b_ in zip(ks_,ks_[1:]): cv2.line(g,(int(P_[a_][0]),int(P_[a_][1])),(int(P_[b_][0]),int(P_[b_][1])),(0,0,255),1,cv2.LINE_AA)
            _est_=set(map(tuple,j.get('est',[]))) if _AX0.get('hide_est') else set()   # hide_est: 가려서 안 보이는 구멍(연장한 점)은 그리지 않는다(투석기 20번: 칸13~15 가 브라켓 위에 그려짐)
            for p in j['pts']:
                if (p[0],p[1]) in _est_: continue
                x,y=T(p[2],p[3])
                if not (0<=int(x)<W and 0<=int(y)<H and MASK[int(y),int(x)]>128): continue
                cv2.circle(g,(int(x),int(y)),3,(0,0,255),-1)
                if p[1]==1: cv2.putText(g,str(p[0]),(int(x)-7,int(y)-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,0,0),2)
                if p[0]==1: cv2.putText(g,'j%d'%p[1],(int(x)-30,int(y)+5),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,140,0),2)
        if _SPLIT:   # 홀라인: 점들을 지나는 직선 하나(점이 한 줄일 때)
            for lab,j in fits:
                _q=np.array([T(q[2],q[3]) for q in j['pts']],np.float32)
                if len(_q)>=2:
                    _vx,_vy,_x0,_y0=cv2.fitLine(_q,cv2.DIST_L2,0,0.01,0.01).ravel()[:4]; _t=max(W,H)*2
                    if float(np.max(np.abs((_q[:,0]-_x0)*_vy-(_q[:,1]-_y0)*_vx)))>5.0: continue   # 점이 한 줄이 아니면(꺾인 프레임) 직선은 긋지 않고 점을 이은 선만 둔다
                    cv2.line(g,(int(_x0-_vx*_t),int(_y0-_vy*_t)),(int(_x0+_vx*_t),int(_y0+_vy*_t)),(0,0,255),2,cv2.LINE_AA)
        if os.environ.get('RR_CHECK'):   # 확인용: 실제 가운데 줄·가운데 열 구멍을 잇는 선(청록·보라)을 겹쳐 그려 축선이 그 선과 겹치는지 눈으로 본다
            for key_,val_,col_ in ((1,rc,(200,200,0)),(0,cc,(200,0,200))):
                ks_=sorted([k for k in tp if k[key_]==val_]); q_=[(int(round(float(tp[k][0]))),int(round(float(tp[k][1])))) for k in ks_]
                for a_,b_ in zip(q_,q_[1:]): cv2.line(g,a_,b_,col_,2,cv2.LINE_AA)
    else: g=base.copy()
    # ── 방향 화살표(선택, 관리자 제안 2026-10-11): <번호>_axes.json 이 있으면 필요한 곳(local)에 X(빨강)·Y(초록)·Z(파랑) 방향을 그린다. 그림은 변형하지 않고 덧그리기만 한다.
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
                cv2.arrowedLine(im,(int(ox),int(oy)),(int(ex),int(ey)),_COL[_rn(k_)],4,cv2.LINE_AA,tipLength=0.22)
                cv2.putText(im,('+' if _rs(k_)==1 else '-')+_rn(k_),(int(ex+(8 if w_[0]>=0 else -34)),int(ey+(8 if w_[1]>=0 else -4))),cv2.FONT_HERSHEY_SIMPLEX,0.8,_COL[_rn(k_)],2,cv2.LINE_AA)
            cv2.circle(im,(int(ox),int(oy)),4,(60,60,60),-1)
        for im_ in (base,g):
            for lc in AXJ.get('local',[]):
                _o=(T(lc['at'][0],lc['at'][1]) if fits else Mx@np.array([lc['at'][0]-cx0,lc['at'][1]-cy0,1.0]))
                _gizmo(im_,float(_o[0]),float(_o[1]),{k:lc[k] for k in 'XYZ' if k in lc},float(lc.get('size',45)),lc.get('label'))
    # notes: <번호>_axes.json 의 "notes":[{"at":[x,y](원본 좌표),"text":"글자","size":28}] — 그림에 한글 글자를 크게 적어 목표 구멍·부품 이름을 눈에 띄게 한다(투석기 20번 "글자를 잘 보이게")
    _nt=(_AX0.get('notes') or []) if '_AX0' in dir() else []
    if _nt:
        from PIL import Image, ImageDraw, ImageFont
        _ff=next((p for p in ('C:/Windows/Fonts/malgunbd.ttf','C:/Windows/Fonts/malgun.ttf') if os.path.exists(p)),None)
        def _notes(im_):
            pil=Image.fromarray(cv2.cvtColor(im_,cv2.COLOR_BGR2RGB)); dr=ImageDraw.Draw(pil)
            for nt in _nt:
                p_=nt['at'] if nt.get('px') else (T(nt['at'][0],nt['at'][1]) if fits else Mx@np.array([nt['at'][0]-cx0,nt['at'][1]-cy0,1.0]))   # px: true 면 at 이 돌린 그림 좌표(빈 공간에 두기 쉽다)
                ft=ImageFont.truetype(_ff,int(nt.get('size',26))) if _ff else ImageFont.load_default()
                tx,ty=int(p_[0]),int(p_[1]); bb=dr.textbbox((tx,ty),nt['text'],font=ft)
                if nt.get('to'):   # to: 가리킬 구멍(원본 좌표) — 글자 상자에서 그 구멍까지 선을 긋는다(글자가 부품·번호를 덮지 않게 빈 공간에 둔다)
                    q_=T(nt['to'][0],nt['to'][1]) if fits else Mx@np.array([nt['to'][0]-cx0,nt['to'][1]-cy0,1.0]); cx_=(bb[0]+bb[2])/2.0; cy_=(bb[1]+bb[3])/2.0
                    dr.line((cx_,cy_,float(q_[0]),float(q_[1])),fill=(220,0,0),width=3); dr.ellipse((float(q_[0])-9,float(q_[1])-9,float(q_[0])+9,float(q_[1])+9),outline=(220,0,0),width=3)
                dr.rectangle((bb[0]-6,bb[1]-4,bb[2]+6,bb[3]+4),fill=(255,255,255),outline=(220,0,0),width=2); dr.text((tx,ty),nt['text'],font=ft,fill=(220,0,0))
            return cv2.cvtColor(np.array(pil),cv2.COLOR_RGB2BGR)
        base=_notes(base); g=_notes(g)
    if _SPLIT: base,g=g,base
    cv2.imwrite(D+nm+'_1.jpg',base,[cv2.IMWRITE_JPEG_QUALITY,88]); cv2.imwrite(D+nm+'_2.jpg',g,[cv2.IMWRITE_JPEG_QUALITY,88])
    return info,names
def sentence(step,info,names):
    if not names and info.get('cols'): names=['%d칸×%d줄 판'%(info['cols'],info['rows'])]
    nm=' / '.join(names) if names else '판'
    if info['ref']=='(점 없음)':
        n1="③ 단계 %d — 로봇(부품)은 똑바로 세운 채, 한 줄 막대의 축이 수직·수평이 되도록 회전만 %.1f° 한 그림 + X·Y·Z 축선(점 없음)."%(step,info['res'])
        n2="④ 단계 %d — 한 줄 프레임은 구멍 점이 일직선이라 격자 점을 만들지 않았다(③과 같은 그림)."%step
    else:
        if info.get('split'):
            n1="③ 단계 %d — 홀라인용: %s 의 구멍 점(빨강)과 그 구멍 줄을 지나는 직선. 번호 = 칸. 회전·보정 없는 원본 그림."%(step,nm)
            n2="④ 단계 %d — 카메라 판단용: 원본 그림 위의 X(빨강)·Z(파랑)·Y(초록) 축선(구멍 점 없음). 시점(보는 방향)을 판단하는 그림."%step
            return n1,n2
        if info.get('overlay'):
            n1="③ 단계 %d — 회전하지 않고 펴지 않은 원본 그대로 X·Y·Z 축선을 그은 그림. 칸1 = %s, 줄1 = %s (격자 번호는 ④ 에서)."%(step,info['c1'],info['r1'])
            n2="④ 단계 %d — 원본 위의 격자: %s. 빨강 점 = 구멍 중심, 초록 숫자 = 칸, j1~ = 줄."%(step,nm)
            return n1,n2
        n1="③ 단계 %d — 로봇(부품)은 똑바로 세운 채, %s 의 구멍 줄이 수평에 가깝도록 회전만 한 그림(늘이거나 펴지 않음)(구멍 흰 틈 점으로 맞춤, 평균 오차 %.1fpx). X(빨강)·Z(파랑)·Y(초록) 축선이 판 가운데를 지난다. 칸1 = %s, 줄1 = %s."%(step,names[0] if names else '기준 판',info['err'],info['c1'],info['r1'])
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

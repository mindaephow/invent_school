# 책 이미지 작업(새 방식, 관리자 지시 2026-10-09): 로봇은 똑바로 세운 채, 기준 판의 칸 열이 수직선·줄이 수평선과 나란한 직사각형 격자가 되도록 기울임(어파인)만 보정하고
# 파란 수직선(판 가운데 열)·수평선(판 가운데 줄)을 긋는다. 그림 전체를 옆으로 눕히지(90° 돌리지) 않는다. 방향은 원본의 위·아래·좌·우를 최대한 유지(거울 금지).
#   python refs_rect.py <이름> [번호 ...]   번호를 안 주면 fits 가 있는 모든 번호.  입력: refs/<이름>/NN.jpg(원본), NN_lv.json(자르기 영역 crop), fits/NN_<라벨>.json(구멍 점, 원본 좌표)
#   출력: refs/<이름>/NN_1.jpg(보정한 그림 + 수직·수평선), NN_2.jpg(+ 격자 점·칸·줄 번호), index.json 의 ③·④ 설명 갱신. 점이 없는 번호(한 줄 막대)는 막대 축이 수직/수평이 되게 기울임만 보정.
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
    Mj=json.load(open(D+nm+'_lv.json')); cx0,cy0,cx1,cy1=Mj['crop']
    crop=cv2.imread(D+nm+'.jpg')[cy0:cy1,cx0:cx1]; h,w=crop.shape[:2]
    fits=[]
    for f in sorted(glob.glob(D+'fits/%s_*.json'%nm)):
        j=json.load(open(f,encoding='utf-8')); fits.append((os.path.basename(f)[3:-5],j))
    names=oldnames(step)
    if not fits:   # 점이 없는 단계(32번 한 줄 막대): 막대 축이 수직/수평이 되도록 기울임만 보정
        ang=Mj['angle']; res=ang-90.0*round(ang/90.0)
        Mx=cv2.getRotationMatrix2D((w/2,h/2),res,1.0); cs,sn=abs(Mx[0,0]),abs(Mx[0,1]); W,H=int(h*sn+w*cs)+1,int(h*cs+w*sn)+1
        Mx[0,2]+=W/2-w/2; Mx[1,2]+=H/2-h/2
        out=cv2.warpAffine(crop,Mx,(W,H),flags=cv2.INTER_CUBIC,borderValue=(255,255,255)); vx,hy=W/2,H/2
        info={'err':0.0,'canvas':(W,H),'c1':'-','r1':'-','ref':'(점 없음)','res':round(res,2)}
        base=out.copy(); g=None
    else:
        ref=max(fits,key=lambda t:len(t[1]['pts'])); rl,rj=ref; pts=rj['pts']; cols,rows=rj['cols'],rj['rows']
        key,swap,fa,fb=pick_orientation(pts,cols,rows)
        P=pitch(pts)
        def dstof(p,cols=cols,rows=rows):
            c=(cols-1-(p[0]-1)) if fa else p[0]-1; r=(rows-1-(p[1]-1)) if fb else p[1]-1
            return [r*P,c*P] if swap else [c*P,r*P]
        src=np.array([[p[2]-cx0,p[3]-cy0] for p in pts],np.float32); dst=np.array([dstof(p) for p in pts],np.float32)
        A,_=cv2.estimateAffine2D(src,dst,method=cv2.LMEDS)
        corn=np.array([[0,0],[w,0],[w,h],[0,h]],np.float32); tc=(A[:,:2]@corn.T).T+A[:,2]
        mn=tc.min(0)-5; mx=tc.max(0)+5; W,H=[int(v) for v in np.ceil(mx-mn)]
        sc=1.0
        if max(W,H)>1800: sc=1800.0/max(W,H)
        A2=A.copy(); A2[:,2]-=mn; A2*=sc; W,H=int(W*sc),int(H*sc)
        out=cv2.warpAffine(crop,A2,(W,H),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
        T=lambda x,y: A2@np.array([x-cx0,y-cy0,1.0])
        pa=(A2[:,:2]@src.T).T+A2[:,2]; err=float(np.sqrt(((pa-dst*sc-(-mn*sc))**2).sum(1)).mean())
        # 가운데 열(수직선)·가운데 줄(수평선): 격자 가운데 칸/줄
        cc=(cols+1)//2; rc=(rows+1)//2
        tp={ (p[0],p[1]):T(p[2],p[3]) for p in pts }
        # x축 방향 격자축 = (swap? 줄 : 칸), y축 = 반대
        if not swap: xax,yax=0,1   # x ← 칸, y ← 줄
        else: xax,yax=1,0
        mid=[(cc,rc)[xax],(cc,rc)[yax]]
        vx=float(np.mean([v[0] for (c,r),v in tp.items() if (c,r)[xax]==mid[0]]))
        hy=float(np.mean([v[1] for (c,r),v in tp.items() if (c,r)[yax]==mid[1]]))
        # 칸1·줄1 위치(위/아래/왼/오른)
        def where(ax):  # ax 0=칸 1=줄
            v1=np.mean([vv for (c,r),vv in tp.items() if (c,r)[ax]==1],axis=0); vm=np.mean([vv for (c,r),vv in tp.items()],axis=0)
            dx,dy=v1[0]-vm[0],v1[1]-vm[1]
            return ('왼쪽' if dx<0 else '오른쪽')+' 끝' if abs(dx)>=abs(dy) else ('위' if dy<0 else '아래')+' 끝'
        info={'err':round(err/sc,2),'canvas':(W,H),'c1':where(0),'r1':where(1),'ref':rl,'res':None,'cols':cols,'rows':rows}
        base=out.copy()
        g=base.copy()
    # 선 긋기(수평·수직)
    def lines(im):
        Hh,Ww=im.shape[:2]
        cv2.line(im,(0,int(round(hy))),(Ww,int(round(hy))),ORANGE,2,cv2.LINE_AA); cv2.putText(im,'horizontal',(Ww-130,int(hy)-8),cv2.FONT_HERSHEY_SIMPLEX,0.55,ORANGE,2)
        cv2.line(im,(int(round(vx)),0),(int(round(vx)),Hh),ORANGE,2,cv2.LINE_AA); cv2.putText(im,'vertical',(int(vx)+8,28),cv2.FONT_HERSHEY_SIMPLEX,0.55,ORANGE,2)
    lines(base)
    if g is not None:
        g=base.copy()
        for lab,j in fits:
            for p in j['pts']:
                x,y=T(p[2],p[3]); cv2.circle(g,(int(x),int(y)),3,(0,0,255),-1)
                if p[1]==1: cv2.putText(g,str(p[0]),(int(x)-6,int(y)-9),cv2.FONT_HERSHEY_SIMPLEX,0.42,(255,0,0),1)
                if p[0]==1: cv2.putText(g,'j%d'%p[1],(int(x)+7,int(y)+4),cv2.FONT_HERSHEY_SIMPLEX,0.42,(0,140,0),1)
    else: g=base.copy()
    cv2.imwrite(D+nm+'_1.jpg',base,[cv2.IMWRITE_JPEG_QUALITY,88]); cv2.imwrite(D+nm+'_2.jpg',g,[cv2.IMWRITE_JPEG_QUALITY,88])
    return info,names
def sentence(step,info,names):
    nm=' / '.join(names) if names else '판'
    if info['ref']=='(점 없음)':
        n1="③ 단계 %d — 로봇(부품)은 똑바로 세운 채, 한 줄 막대의 축이 수직·수평이 되도록 기울임만 %.1f° 보정한 그림 + 파란 수직선·수평선(점 없음)."%(step,info['res'])
        n2="④ 단계 %d — 한 줄 프레임은 구멍 점이 일직선이라 격자 점을 만들지 않았다(③과 같은 그림)."%step
    else:
        n1="③ 단계 %d — 로봇(부품)은 똑바로 세운 채, %s 의 칸 열이 수직선·줄이 수평선과 나란하도록 기울임만 보정한 그림(구멍 흰 틈 점으로 맞춤, 평균 오차 %.1fpx). 파란 수직선 = 판 가운데 열, 파란 수평선 = 판 가운데 줄. 칸1 = %s, 줄1 = %s."%(step,names[0] if names else '기준 판',info['err'],info['c1'],info['r1'])
        n2="④ 단계 %d — 같은 그림 위의 격자: %s. 빨강 점 = 구멍 중심, 초록 숫자 = 칸, j1~ = 줄. 칸1 = %s, 줄1 = %s."%(step,nm,info['c1'],info['r1'])
    return n1,n2
if __name__=='__main__':
    steps=[int(s) for s in sys.argv[2:]]
    if not steps: steps=sorted({int(os.path.basename(f)[:2]) for f in glob.glob(D+'fits/*.json')}|{r['step'] for r in INDEX if r['idx']==2 and os.path.exists(D+'%02d_lv.json'%r['step'])})
    for s in steps:
        info,names=process(s); print(s,info)
        n1,n2=sentence(s,info,names)
        for r in INDEX:
            if r['step']==s and r['idx']==0 and not str(r.get('note','')).startswith('①'): r['note']='① '+str(r.get('note',''))
            if r['step']==s and r['idx']==1: r['note']=n1
            if r['step']==s and r['idx']==2: r['note']=n2
    json.dump(INDEX,open(D+'index.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

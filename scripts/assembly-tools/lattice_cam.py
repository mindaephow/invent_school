# 교재 그림의 판 구멍(흰 타원) 중심을 검출 → 이웃 구멍 간격 벡터(가로 v1, 세로 v2)로 카메라 방위·고도를 구한다.
# 직교 근사: +x → s(cos az, −sin az·sin el), +z → s(−sin az, −cos az·sin el) (화면 오른쪽·위쪽). D = a1 b2 − a2 b1 = −s² sin el, T = |v1|²+|v2|² = s²(1+sin²el)
import cv2, numpy as np, math
def holes(path, region=None, amin=150, amax=4000):
    im=cv2.imread(path); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    white=(g>238).astype(np.uint8)*255
    n,lab,st,cen=cv2.connectedComponentsWithStats(white)
    big=np.argmax(st[1:,4])+1
    out=[]
    for i in range(1,n):
        if i==big: continue
        x,y,w,h,a=st[i]
        if amin<=a<=amax and 0.3<w/max(h,1)<4:
            cx,cy=cen[i]
            if region is None or (region[0]<=cx<=region[2] and region[1]<=cy<=region[3]): out.append((cx,cy,a))
    return out
def angles(v1,v2):
    """v1: +x 방향 화면 벡터(오른쪽, 위쪽), v2: +z 방향 화면 벡터(오른쪽, 위쪽)"""
    a1,b1=v1; a2,b2=v2
    T=a1*a1+b1*b1+a2*a2+b2*b2; D=a1*b2-a2*b1
    r=-D/T                                    # = q/(1+q²), q = sin el
    if abs(r)>0.5: r=math.copysign(0.5,r)
    q=(1-math.sqrt(1-4*r*r))/(2*r) if abs(r)>1e-9 else 0
    s2=T/(1+q*q); s=math.sqrt(s2)
    az=math.degrees(math.atan2(-a2,a1)); el=math.degrees(math.asin(max(-1,min(1,q))))
    return az,el,s

def grid_assign(h, nrows=3):
    """검출된 구멍 (cx,cy,area) 을 nrows 줄로 나눠 (줄, 칸) 번호를 붙인다. 줄은 화면에서 위(먼 쪽)→아래(가까운 쪽), 칸은 줄 안에서 왼쪽→오른쪽."""
    P=np.array([(x,y) for x,y,a in h],float)
    # 줄 방향: 가장 긴 방향을 PCA 로
    c=P.mean(0); u,s,vt=np.linalg.svd(P-c); d=vt[0]
    if d[0]<0: d=-d
    n=np.array([-d[1],d[0]])                      # 줄에 수직(화면 아래쪽이 +)
    if n[1]<0: n=-n
    t=(P-c)@d; w=(P-c)@n
    # 줄 나누기: w 를 k-means(nrows)
    from sklearn.cluster import KMeans
    km=KMeans(nrows,n_init=10,random_state=0).fit(w.reshape(-1,1))
    order=np.argsort(km.cluster_centers_.ravel()); rank={int(o):i for i,o in enumerate(order)}
    rows=[rank[int(l)] for l in km.labels_]
    return P,t,rows

def lattice_vectors(h, dmin=35, dmax=140):
    """검출된 구멍 중심들에서 이웃 간격 벡터를 모아 두 방향(가로 v1, 세로 v2)의 중앙값을 구한다. 반환: (v1, v2) 화면 벡터(오른쪽, 위쪽)."""
    P=np.array([(x,y) for x,y,a in h],float)
    vs=[]
    for i in range(len(P)):
        for j in range(len(P)):
            if i==j: continue
            d=P[j]-P[i]; L=np.hypot(*d)
            if dmin<=L<=dmax and d[0]>=0 and not (abs(d[0])<1e-6 and d[1]<0): vs.append(d)
    vs=np.array(vs)
    ang=np.degrees(np.arctan2(vs[:,1],vs[:,0]))            # 화면 y 아래가 +
    # 두 방향 군집: 가로에 가까운 것(−45°~+30° 근처)과 나머지
    hor=vs[(ang>-40)&(ang<25)]; ver=vs[(ang>=25)&(ang<100)]
    def med(a):
        if len(a)==0: return None
        # 가장 짧은 군집(한 칸 간격)만: 길이 하위 40%
        L=np.hypot(a[:,0],a[:,1]); k=a[L<=np.percentile(L,45)]
        return np.median(k,axis=0)
    v1=med(hor); v2=med(ver)
    return (v1[0],-v1[1]),(v2[0],-v2[1])                  # (오른쪽, 위쪽)

def solve_angles(v1,v2):
    """+x 방향 화면 벡터 v1, +z 방향 화면 벡터 v2 → 방위 az(−90~90), 고도 el, 척도 s 를 격자 탐색(직교 근사)."""
    best=None
    for az in np.arange(-89,89.5,0.5):
        for el in np.arange(5,86,0.5):
            a=math.radians(az); e=math.radians(el); se=math.sin(e)
            m1=(math.cos(a),-math.sin(a)*se); m2=(-math.sin(a),-math.cos(a)*se)
            # 최적 s (최소제곱)
            num=v1[0]*m1[0]+v1[1]*m1[1]+v2[0]*m2[0]+v2[1]*m2[1]; den=sum(t*t for t in (*m1,*m2)); s=num/den
            err=(v1[0]-s*m1[0])**2+(v1[1]-s*m1[1])**2+(v2[0]-s*m2[0])**2+(v2[1]-s*m2[1])**2
            if best is None or err<best[0]: best=(err,az,el,s)
    return best

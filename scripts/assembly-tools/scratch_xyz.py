# usage: python scratch_xyz.py name N "LABEL:cx,ytop,cz[:swapxz]" ...   first label = P file receiving all points
import sys, json
name, N = sys.argv[1], int(sys.argv[2]); specs=sys.argv[3:]
D='refs/%s/fits/%02d_%s.json'
P=json.load(open(D%(name,N,specs[0].split(':')[0]),encoding='utf-8'))
xyz=[];img=[]
for sp in specs:
    lab,c=sp.split(':')[0],sp.split(':')[1]; cx,yt,cz=[float(v) for v in c.split(',')]
    f=json.load(open(D%(name,N,lab),encoding='utf-8')); cols,rows=f['cols'],f['rows']
    est=set(tuple(e) for e in f.get('est',[]))
    for cc,rr,x,y in f['pts']:
        if (cc,rr) in est: continue    # 실제로 찾은 구멍만(격자로 채운 점은 제외)
        xyz.append([round(cx+(cc-(cols+1)/2)*10,1),yt,round(cz+(rr-(rows+1)/2)*10,1)]); img.append([x,y])
P['xyz3d']=xyz; P['xyz3d_img']=img
json.dump(P,open(D%(name,N,specs[0].split(':')[0]),'w',encoding='utf-8'),ensure_ascii=False)
print(len(xyz),'점')

// usage: node check_local.js asm.json   (cwd 에 conn.json·dims.json — python partlib.py 로 만든다)
// 화면·validate_assembly 와 같은 public/design-mates.js · design-collision.js 로 단계별 정밀 검사 + 몸통 겹침을 돌린다.
const fs=require('fs'),path=require('path');
global.window={};
const pub=path.join(__dirname,'..','..','public');
eval(fs.readFileSync(path.join(pub,'design-mates.js'),'utf8'));
eval(fs.readFileSync(path.join(pub,'design-collision.js'),'utf8'));
const conn=JSON.parse(fs.readFileSync('conn.json','utf8')), dims=JSON.parse(fs.readFileSync('dims.json','utf8'));
const asm=JSON.parse(fs.readFileSync(process.argv[2],'utf8')), steps=asm.steps;
const issues=window.IVS_MATES.checkSteps(steps,conn);
console.log('단계별 정밀 검사 문제:',issues.length); issues.forEach(i=>console.log('  ',i));
const C=window.IVS_COLLISION,M=window.IVS_MATES;
function quat(r){const m=M.matFromEuler(r);const t=m[0][0]+m[1][1]+m[2][2];let w,x,y,z;
 if(t>0){const s=Math.sqrt(t+1)*2;w=s/4;x=(m[2][1]-m[1][2])/s;y=(m[0][2]-m[2][0])/s;z=(m[1][0]-m[0][1])/s;}
 else if(m[0][0]>m[1][1]&&m[0][0]>m[2][2]){const s=Math.sqrt(1+m[0][0]-m[1][1]-m[2][2])*2;w=(m[2][1]-m[1][2])/s;x=s/4;y=(m[0][1]+m[1][0])/s;z=(m[0][2]+m[2][0])/s;}
 else if(m[1][1]>m[2][2]){const s=Math.sqrt(1+m[1][1]-m[0][0]-m[2][2])*2;w=(m[0][2]-m[2][0])/s;x=(m[0][1]+m[1][0])/s;y=s/4;z=(m[1][2]+m[2][1])/s;}
 else{const s=Math.sqrt(1+m[2][2]-m[0][0]-m[1][1])*2;w=(m[1][0]-m[0][1])/s;x=(m[0][2]+m[2][0])/s;y=(m[1][2]+m[2][1])/s;z=s/4;}
 return {x,y,z,w};}
const all=[];steps.forEach((s,k)=>(s.parts||[]).forEach((pt,i)=>all.push({k:k+1,i,pt})));
const items=all.map(a=>({a,boxes:C.coreBoxes(a.pt.n,dims[a.pt.n]||[0,0,0]),q:quat(a.pt.r||[0,0,0]),pos:{x:a.pt.p[0],y:a.pt.p[1],z:a.pt.p[2]}}));
let n=0;
for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){const A=items[i],B=items[j];if(!A.boxes||!B.boxes)continue;
 if(C.boxesOverlap(A.boxes,A.pos,A.q,B.boxes,B.pos,B.q,0.6)){n++;if(n<=40)console.log('  겹침',A.a.k+'.'+A.a.i,A.a.pt.n,'<>',B.a.k+'.'+B.a.i,B.a.pt.n);}}
console.log('몸통 겹침:',n);
// 바닥 기준: 가장 낮은 부품 바닥
const cnt={};all.forEach(a=>cnt[a.pt.n]=(cnt[a.pt.n]||0)+1);console.log('부품 개수:',JSON.stringify(cnt));
// 단계별 검증 절차(design-verify.js): 띄우는 방향·바닥 기준·같은 자리 중복·교재 LIST·카메라 지정. 사용: node check_local.js asm.json list.json [def.json]
if (process.argv[3]) {
  eval(fs.readFileSync(path.join(pub,'design-verify.js'),'utf8'));
  const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
  const def=Object.assign({steps},process.argv[4]?JSON.parse(fs.readFileSync(process.argv[4],'utf8')):{});
  const v=window.IVS_VERIFY.verify(def,conn,dims,{list});
  console.log('단계별 검증 절차 문제:',v.issues.length); v.issues.forEach(i=>console.log('  ',i));
  if (process.env.REPORT) v.report.forEach(l=>console.log(l));
}

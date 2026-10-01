// usage: node check.js asm.json
const fs=require('fs');
global.window={};
eval(fs.readFileSync('site/design-mates.js','utf8'));
eval(fs.readFileSync('site/design-collision.js','utf8'));
const conn=JSON.parse(fs.readFileSync('conn.json','utf8'));
const dims=JSON.parse(fs.readFileSync('dims.json','utf8'));
const asm=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const steps=asm.steps;
const issues=window.IVS_MATES.checkSteps(steps,conn);
console.log('checkSteps issues:',issues.length);issues.forEach(i=>console.log('  ',i));
// overlap in final (side parts at their final spot)
const all=[];steps.forEach((s,k)=>(s.parts||[]).forEach((pt,i)=>all.push({k:k+1,i,pt})));
const C=window.IVS_COLLISION, M=window.IVS_MATES;
function quat(r){const m=M.matFromEuler(r);// matrix->quat
 const t=m[0][0]+m[1][1]+m[2][2];let w,x,y,z;
 if(t>0){const s=Math.sqrt(t+1)*2;w=s/4;x=(m[2][1]-m[1][2])/s;y=(m[0][2]-m[2][0])/s;z=(m[1][0]-m[0][1])/s;}
 else if(m[0][0]>m[1][1]&&m[0][0]>m[2][2]){const s=Math.sqrt(1+m[0][0]-m[1][1]-m[2][2])*2;w=(m[2][1]-m[1][2])/s;x=s/4;y=(m[0][1]+m[1][0])/s;z=(m[0][2]+m[2][0])/s;}
 else if(m[1][1]>m[2][2]){const s=Math.sqrt(1+m[1][1]-m[0][0]-m[2][2])*2;w=(m[0][2]-m[2][0])/s;x=(m[0][1]+m[1][0])/s;y=s/4;z=(m[1][2]+m[2][1])/s;}
 else{const s=Math.sqrt(1+m[2][2]-m[0][0]-m[1][1])*2;w=(m[1][0]-m[0][1])/s;x=(m[0][2]+m[2][0])/s;y=(m[1][2]+m[2][1])/s;z=s/4;}
 return {x,y,z,w};}
const upto=+(process.argv[3]||999);
const items=all.filter(a=>a.k<=upto).map(a=>({a,boxes:C.coreBoxes(a.pt.n,dims[a.pt.n]),q:quat(a.pt.r||[0,0,0]),pos:{x:a.pt.p[0],y:a.pt.p[1],z:a.pt.p[2]}}));
let n=0;
for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){
 const A=items[i],B=items[j];if(!A.boxes||!B.boxes)continue;
 if(A.a.pt.side||B.a.pt.side)continue;
 if(C.boxesOverlap(A.boxes,A.pos,A.q,B.boxes,B.pos,B.q,0.6)){n++;if(n<=25)console.log('  overlap',A.a.k+'.'+A.a.i,A.a.pt.n,'<>',B.a.k+'.'+B.a.i,B.a.pt.n);}
}
console.log('overlaps:',n);

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
const fin=(pt)=>{ const mv=pt.move; if(!mv) return {p:pt.p,r:pt.r||[0,0,0]}; return {p:mv.p||pt.p.map((v,k)=>v+mv.by[k]), r:mv.r||pt.r||[0,0,0]}; }; // 옮겨 붙는 부품은 마지막 자세(제자리)로 겹침을 본다
const items=all.map(a=>{const f=fin(a.pt);return {a,boxes:C.coreBoxes(a.pt.n,dims[a.pt.n]||[0,0,0]),q:quat(f.r),pos:{x:f.p[0],y:f.p[1],z:f.p[2]}};});
let n=0;
for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){const A=items[i],B=items[j];if(!A.boxes||!B.boxes)continue;
 if(/(135|90)도/.test(A.a.pt.n+B.a.pt.n))continue; // 꺾인 프레임은 몸통 상자가 실제보다 커서 오탐
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
// ── 안내 화살표 검사: 앞 단계 부품과 결합하는 새 부품은 그 단계에 안내점(marks, 옆자리에서 합칠 땐 settleMarks, 옮길 땐 move.marks)이 있어야 한다
// (화면의 "끌면 화살표가 따라가는" 기능은 이 값을 쓴다 — 값이 없으면 화살표가 안 나온다. 3륜바이크 14단계 브라켓에서 빠뜨린 실수를 잡는다)
{
  const stepsAll = steps, miss = [];
  const keyOf = (k, i, n) => `${k}.${i} ${n}`;
  stepsAll.forEach((st, si) => {
    const step = si + 1;
    const upto = []; stepsAll.slice(0, step).forEach((s, k) => (s.parts || []).forEach((pt, i) => {
      const mv = pt.move && pt.move.at <= step; const p = mv ? (pt.move.p || pt.p.map((v, j) => v + pt.move.by[j])) : pt.p;
      upto.push({ key: keyOf(k + 1, i, pt.n), n: pt.n, p, r: (mv && pt.move.r) ? pt.move.r : (pt.r || [0, 0, 0]), step: k + 1, ref: pt });
    }));
    const res = M.check(upto, conn);
    const prior = new Set(upto.filter(u => u.step < step).map(u => u.key));
    // 이 단계에 "도착"하는 부품: 이 단계에 넣었고 옆자리 없음, 옆자리에서 이 단계에 합쳐짐(side.until), 이 단계에 옮겨 붙음(move.at)
    const arriving = [];
    stepsAll.forEach((s, k) => (s.parts || []).forEach((pt, i) => {
      const own = k + 1 === step && !pt.side && !(pt.move && pt.move.at <= step && false);
      const settle = pt.side && pt.side.until === step, moved = pt.move && pt.move.at === step;
      if (own || settle || moved) arriving.push({ key: keyOf(k + 1, i, pt.n), pt, mode: moved ? 'move' : (settle ? 'settle' : 'own') });
    }));
    const arrSet = new Set(arriving.map(a => a.key));
    arriving.forEach(({ key, pt, mode }) => {
      if (pt.n === '리벳' || pt.noGuide) return; // noGuide = 우연히 맞닿아 보일 뿐 결합이 아닌 부품(안내 화살표 없음). 리벳은 교재도 화살표 없이 꽂힌 채로 그린다(같이 도착하는 묶음 안의 결합도 제외)
      const outside = (k) => prior.has(k) && !arrSet.has(k); // 같이 합쳐지는 묶음 안의 결합은 빼고, 이미 있던 부품과의 결합만 본다
      const hasPrior = res.mated.some(m => (m.part === key && outside(m.into)) || (m.into === key && outside(m.part)));
      if (!hasPrior) return;
      const ok = mode === 'move' ? (pt.move.marks || []).length : mode === 'settle' ? (pt.settleMarks || []).length : (pt.marks || []).length;
      if (!ok) miss.push(`${step}단계 ${pt.n}(${key}): 앞 부품과 결합하는데 안내점(${mode === 'move' ? 'move.marks' : mode === 'settle' ? 'settleMarks' : 'marks'})이 없음 → 화살표가 안 나옴`);
    });
  });
  console.log('안내 화살표 없는 부품:', miss.length); miss.slice(0, 40).forEach(m => console.log('  ', m));
}
// ── 띄우는 길 검사: 새 부품이 끼우기 전 띄워진 자리(제자리 + 띄우는 방향 × 거리)에서 제자리로 내려오는 길에 이미 놓인 부품이 있으면 부품이 다른 부품을 뚫고 들어오는 것처럼 보인다
// (오토건 8단계: 합치는 방향(settleDir)을 모터 쪽으로 잘못 줘서 기어판이 모터를 뚫고 내려왔다 — 사용자 지적).
{
  const norm = (v) => { const l = Math.hypot(...v) || 1; return v.map((x) => x / l); };
  const issuesPath = [];
  steps.forEach((st, si) => {
    const step = si + 1;
    const placedAt = (pt, stp) => { // stp 단계가 끝난 뒤 pt 의 자세
      if (pt.side && stp < pt.side.until) return { p: pt.side.p, r: pt.side.r };
      if (pt.move && stp >= pt.move.at) return { p: pt.move.p || pt.p.map((v, k) => v + pt.move.by[k]), r: pt.move.r || pt.r || [0, 0, 0] };
      return { p: pt.p, r: pt.r || [0, 0, 0] };
    };
    const arriving = [];
    steps.forEach((s2, k) => (s2.parts || []).forEach((pt, i) => {
      const own = k + 1 === step && !pt.side;
      const settle = pt.side && pt.side.until === step, moved = pt.move && pt.move.at === step;
      if (own || settle || moved) arriving.push({ pt, k: k + 1, i, mode: moved ? 'move' : (settle ? 'settle' : 'own') });
    }));
    const prior = [];
    steps.forEach((s2, k) => (s2.parts || []).forEach((pt, i) => {
      if (k + 1 > step) return;
      if (arriving.some((a) => a.pt === pt)) return;
      prior.push({ pt, ...placedAt(pt, step - 1), k: k + 1, i });
    }));
    arriving.forEach(({ pt, mode, k, i }) => {
      const boxes = C.coreBoxes(pt.n, dims[pt.n] || [0, 0, 0]); if (!boxes) return;
      const fin = mode === 'move' ? { p: pt.move.p || pt.p.map((v, j) => v + pt.move.by[j]), r: pt.move.r || pt.r || [0, 0, 0] } : { p: pt.p, r: pt.r || [0, 0, 0] };
      const dir = mode === 'move' ? pt.move.dir : (mode === 'settle' ? (pt.settleDir || pt.dir) : pt.dir);
      if (!dir) return;
      const hov = mode === 'move' ? (pt.move.hover || 22) : (pt.hover || (pt.recv ? 20 : 22));
      const d = norm(dir), q = quat(fin.r);
      for (const t of [1, 0.66, 0.33]) {
        const pos = { x: fin.p[0] + d[0] * hov * t, y: fin.p[1] + d[1] * hov * t, z: fin.p[2] + d[2] * hov * t };
        const hit = prior.find((o) => { const ob = C.coreBoxes(o.pt.n, dims[o.pt.n] || [0, 0, 0]); return ob && C.boxesOverlap(boxes, pos, q, ob, { x: o.p[0], y: o.p[1], z: o.p[2] }, quat(o.r), 2.5); });
        if (hit) { issuesPath.push(`${step}단계 ${pt.n}(${k}.${i}): 띄우는 방향 ${JSON.stringify(dir)}(거리 ${hov}) 쪽에 이미 놓인 ${hit.pt.n}(${hit.k}.${hit.i})가 있어 내려오는 길에 뚫고 들어옴`); break; }
      }
    });
  });
  console.log('띄우는 길에 다른 부품이 있는 부품:', issuesPath.length); issuesPath.slice(0, 40).forEach((m) => console.log('  ', m));
}

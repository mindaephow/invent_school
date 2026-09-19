export const metadata = {
  title: '발명융합과학교실',
  description:
    '이론을 전달하는 수업이 아니라 직접 발명해보는 수업. 문제를 발견하는 관점과 실패를 두려워하지 않고 만들어보는 과정을 설계합니다.',
}

const COMPARE = {
  left: ['이론과 지식을 설명으로 듣는다', '정해진 답과 순서를 따라간다', '실패하면 틀린 것으로 끝난다'],
  right: ['문제를 스스로 발견하는 데서 시작한다', '만들어보고 고쳐보며 답을 찾아간다', '실패는 다음 아이디어의 재료가 된다'],
}

const FLOW = [
  ['다양한 경험하기', '과학, 항공, 우주, 로봇 등 다양한 활동을 직접 해봅니다. 경험이 쌓여야 문제도 보입니다.'],
  ['불편함 마주하기', '해보는 과정에서 생기는 불편함, 막히는 순간을 많이많이 겪어봅니다. 불편함이 곧 발명의 출발점입니다.'],
  ['문제 해결해보기', '브레인스토밍, 마인드맵, SCAMPER 같은 도구로 아이디어를 내고 직접 만들어봅니다.'],
  ['고쳐보기', '안 되면 왜 안 됐는지 살펴보고 다시 만들어봅니다. 실패는 다음 아이디어의 재료입니다.'],
]

const SCAMPER = [
  ['S', '대체하기', 'Substitute', '재료나 부분을 다른 것으로 바꿔봅니다.', '플라스틱 빨대 → 종이 빨대'],
  ['C', '결합하기', 'Combine', '서로 다른 것을 하나로 합쳐봅니다.', '지우개가 달린 연필'],
  ['A', '응용하기', 'Adapt', '다른 분야의 아이디어를 가져와 써봅니다.', '도꼬마리 열매에서 떠올린 벨크로(찍찍이)'],
  ['M', '변형하기', 'Modify', '크기, 모양, 색을 바꾸거나 키우고 줄여봅니다.', '작게 접어 들고 다니는 접이식 우산'],
  ['P', '다른 용도로 쓰기', 'Put to another use', '원래 목적과 다르게 써봅니다.', '낡은 타이어로 만든 화분'],
  ['E', '제거하기', 'Eliminate', '없어도 되는 부분을 덜어내봅니다.', '날개 없는 선풍기'],
  ['R', '뒤집기 · 재배열', 'Reverse', '순서, 위치, 방향을 거꾸로 바꿔봅니다.', '거꾸로 세워두는 케첩 용기'],
]

const ADDSUB = {
  add: {
    title: '더하기',
    desc: '이미 있는 물건 두 개를 합쳐 새로운 쓸모를 만들어봅니다.',
    ex: ['지우개 + 연필', '알람 + 라디오', '우산 + 손전등'],
  },
  sub: {
    title: '빼기',
    desc: '핵심 기능만 남기고 나머지를 과감하게 덜어내봅니다. 정말 필요한 것이 무엇인지 보이기 시작합니다.',
    ex: ['우산에서 무엇을 뺄 수 있을까?', '버튼이 딱 하나뿐인 리모컨을 만든다면?', '이 물건의 가장 중요한 기능은 무엇일까?'],
  },
}

const METHODS = [
  ['브레인스토밍', '비판하지 않고, 떠오르는 아이디어를 되도록 많이 자유롭게 쏟아내는 방법입니다. 엉뚱한 생각이 좋은 아이디어의 출발점이 되기도 합니다.'],
  ['마인드맵', '중심 주제에서 가지를 뻗어가며 떠오른 생각을 그림처럼 정리하는 방법입니다. 생각의 연결과 빈틈이 눈에 보입니다.'],
  ['코딩', '아이디어를 컴퓨터가 이해하는 명령으로 옮겨 실제로 작동하게 만드는 방법입니다.'],
  ['기초 발명 10대 원리', '여러 발명에서 반복해서 나타나는 기본적인 발상 원리를 정리한 것으로, 발명을 시작하는 첫 도구가 됩니다.'],
  ['트리즈(TRIZ)의 40가지 발명원리', '수많은 특허를 분석해 정리한 창의적 문제해결 이론(러시아 알트슐러)의 핵심 도구로, 문제를 푸는 40가지 발명 원리를 배웁니다.'],
]

const SUBJECTS = [
  ['항공', '발명의 눈으로 만나는 항공'],
  ['우주', '발명의 눈으로 만나는 우주'],
  ['과학실험', '발명의 눈으로 해보는 과학실험'],
  ['로봇과학', '발명의 눈으로 만나는 로봇과학'],
]

const ROOM_STEPS = [
  ['로그인', '선생님이 알려준 아이디와 비밀번호로 들어갑니다.'],
  ['프로젝트 만들기', '이름을 붙여 새 프로젝트를 시작하거나, 저장해 둔 작업을 이어서 합니다.'],
  ['설계하기', '타공판, 기둥, 경첩, ㄱ자 연결대, 종이테이프, 직선길을 3D 공간에 놓고 공을 굴려 목표 깃발까지 보내봅니다.'],
  ['저장하고 제출', '나갈 때 작업이 저장되고, 완성하면 과제를 제출합니다.'],
]

const css = `
:root{
  --bg:#F4F7FB; --panel:#FFFFFF; --border:#DCE4F0; --ink:#202A3C; --ink-soft:#57647A;
  --blue:#2F6FED; --blue-soft:#DCE7FF; --accent:#FF6A3D; --accent-ink:#FFFFFF; --grid:#C9D6EC;
  --shadow:0 10px 28px rgba(32,42,60,0.08);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0E1626; --panel:#141F35; --border:#24314F; --ink:#E8EDF5; --ink-soft:#96A3BC;
    --blue:#6FA0FF; --blue-soft:#1C2C4D; --accent:#FF8659; --accent-ink:#1A0F08; --grid:#22304F;
    --shadow:0 10px 28px rgba(0,0,0,0.45);
  }
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:'Rubik', 'Apple SD Gothic Neo', 'Malgun Gothic', system-ui, sans-serif; line-height:1.65;
  word-break:keep-all; overflow-wrap:break-word;
}
a{color:inherit;}
.wrap{max-width:1040px; margin:0 auto; padding:0 20px;}
.nav{display:flex; align-items:center; justify-content:space-between; gap:12px; padding:18px 0;}
.brand{font-family:'Kalam','Rubik',cursive; font-weight:700; font-size:26px; text-decoration:none;}
.brand span{color:var(--blue);}
.nav-actions{display:flex; gap:8px; flex-wrap:wrap;}
.btn{
  display:inline-block; text-decoration:none; font-weight:600; font-size:14px; padding:10px 16px;
  border-radius:10px; border:1px solid var(--border); background:var(--panel); color:var(--ink);
}
.btn:hover{filter:brightness(0.97);}
.btn.primary{background:var(--accent); border-color:var(--accent); color:var(--accent-ink);}
.btn.big{font-size:16px; padding:14px 22px;}

.hero{
  position:relative; margin:8px 0 0; padding:56px 28px 60px; border-radius:22px; overflow:hidden;
  border:1px solid var(--border); box-shadow:var(--shadow);
  background-color:var(--panel);
  background-image:linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size:28px 28px; background-position:-1px -1px;
}
.hero::after{content:""; position:absolute; inset:0; background:linear-gradient(180deg, transparent 40%, var(--panel) 100%); pointer-events:none;}
.hero-inner{position:relative; z-index:1; max-width:560px;}
.kicker{display:inline-block; font-size:13px; font-weight:600; color:var(--blue); background:var(--blue-soft); padding:6px 12px; border-radius:999px;}
h1{font-size:clamp(30px, 5.4vw, 48px); line-height:1.25; margin:16px 0 14px; letter-spacing:-0.01em; text-wrap:balance;}
h1 em{font-style:normal; color:var(--blue);}
.lead{font-size:clamp(16px, 2.2vw, 19px); color:var(--ink-soft); margin:0 0 26px; text-wrap:pretty;}
.hero-cta{display:flex; gap:10px; flex-wrap:wrap;}
.ball-art{position:absolute; right:-10px; bottom:-6px; width:min(46%, 420px); z-index:1; opacity:0.95;}
@media (max-width:1100px){ .ball-art{display:none;} .hero-inner{max-width:680px;} }
@media (max-width:760px){ .hero{padding:40px 20px 44px;} }

.summary{
  margin:22px 0 0; padding:22px 26px; border-radius:18px; background:var(--blue-soft);
  border:1px solid var(--border); font-size:clamp(17px, 2.4vw, 21px); line-height:1.6; font-weight:600;
}
.summary em{font-style:normal; color:var(--blue);}

section{padding:64px 0 0;}
.eyebrow{font-size:13px; font-weight:700; color:var(--blue); letter-spacing:0.04em; margin:0 0 6px;}
h2{font-size:clamp(24px, 3.6vw, 32px); line-height:1.3; margin:0 0 12px; text-wrap:balance;}
.section-lead{color:var(--ink-soft); margin:0 0 26px; max-width:720px;}

.two{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
@media (max-width:760px){ .two{grid-template-columns:1fr;} }
.card{background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:22px; box-shadow:var(--shadow);}
.card h3{margin:0 0 6px; font-size:18px;}
.card p{margin:0; color:var(--ink-soft);}
.card .big-title{font-size:22px; line-height:1.4; margin:0;}
.card .ex{margin-top:10px; font-size:14px; color:var(--ink); background:var(--blue-soft); border-radius:10px; padding:8px 12px; display:inline-block;}

.scamper{display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:12px; margin-top:18px;}
.letter{
  background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:16px;
  display:flex; align-items:center; gap:14px;
}
.letter b{
  flex:none; width:44px; height:44px; border-radius:12px; display:grid; place-items:center;
  font-family:'Kalam',cursive; font-size:24px; background:var(--blue); color:#fff;
}
.letter div{font-weight:600;}
.letter small{display:block; font-weight:400; color:var(--ink-soft); font-size:12px;}

.list{display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:12px;}
.item{background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:18px;}
.item h3{margin:0 0 4px; font-size:16px;}
.item p{margin:0; font-size:14px; color:var(--ink-soft);}
.tag{display:inline-block; margin:0 8px 8px 0; padding:8px 14px; border-radius:999px; background:var(--panel); border:1px solid var(--border); font-weight:600; font-size:15px;}
.tag.feature{background:var(--blue); border-color:var(--blue); color:#fff;}
.feature-note{margin:6px 0 0; color:var(--ink-soft); font-size:14px;}

.compare{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
@media (max-width:760px){ .compare{grid-template-columns:1fr;} }
.col{background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:22px;}
.col.hl{border-color:var(--blue); box-shadow:var(--shadow);}
.col h3{margin:0 0 12px; font-size:17px;}
.col.hl h3{color:var(--blue);}
.col ul{list-style:none; margin:0; padding:0; display:grid; gap:10px;}
.col li{display:flex; gap:10px; align-items:flex-start; color:var(--ink-soft);}
.col li::before{content:"–"; color:var(--ink-soft); font-weight:700;}
.col.hl li{color:var(--ink); font-weight:500;}
.col.hl li::before{content:"✓"; color:var(--blue);}

.steps{display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px; counter-reset:step;}
.step{background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:20px; position:relative;}
.step::before{
  counter-increment:step; content:counter(step);
  display:grid; place-items:center; width:32px; height:32px; border-radius:50%;
  background:var(--blue); color:#fff; font-weight:700; margin-bottom:12px; font-family:'Kalam',cursive; font-size:18px;
}
.step h3{margin:0 0 6px; font-size:17px;}
.step p{margin:0; color:var(--ink-soft); font-size:14.5px;}

.scamper{display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:12px; margin-top:16px;}
.sc{background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:18px; display:flex; gap:14px;}
.sc b{
  flex:none; width:48px; height:48px; border-radius:13px; display:grid; place-items:center;
  font-family:'Kalam',cursive; font-size:26px; background:var(--blue); color:#fff;
}
.sc h3{margin:0; font-size:17px;}
.sc small{display:block; color:var(--ink-soft); font-size:12px; margin-bottom:6px;}
.sc p{margin:0 0 8px; color:var(--ink-soft); font-size:14.5px;}
.sc .ex{margin:0; display:inline-block; font-size:13px; color:var(--ink); background:var(--blue-soft); border-radius:8px; padding:5px 10px;}

.addsub{display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:14px;}
@media (max-width:760px){ .addsub{grid-template-columns:1fr;} }
.addsub .card ul{list-style:none; margin:12px 0 0; padding:0; display:flex; flex-wrap:wrap; gap:8px;}
.addsub .card li{font-size:13.5px; background:var(--blue-soft); color:var(--ink); border-radius:999px; padding:6px 12px;}

.methods{display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:12px;}
.method{background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:20px;}
.method h3{margin:0 0 8px; font-size:18px; color:var(--blue);}
.method p{margin:0; color:var(--ink-soft); font-size:14.5px;}

.subjects{display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px;}
.subject{background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:20px;}
.subject h3{margin:0 0 4px; font-size:18px;}
.subject p{margin:0; color:var(--ink-soft); font-size:14px;}
.goldberg{
  grid-column:1 / -1; background:var(--blue); color:#fff; border-color:var(--blue);
  display:grid; grid-template-columns:1.1fr 1fr; gap:22px; align-items:center; padding:26px;
}
@media (max-width:760px){ .goldberg{grid-template-columns:1fr;} }
.goldberg h3{color:#fff; font-size:24px; margin:0 0 8px;}
.goldberg p{color:rgba(255,255,255,0.92); font-size:15.5px; margin:0 0 10px;}
.goldberg .badge{display:inline-block; font-size:12px; font-weight:700; background:rgba(255,255,255,0.18); border-radius:999px; padding:4px 10px; margin-bottom:10px;}
.goldberg ul{list-style:none; margin:0; padding:0; display:grid; gap:8px;}
.goldberg li{background:rgba(255,255,255,0.14); border-radius:10px; padding:9px 12px; font-size:14.5px;}

.ops{display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); gap:12px;}
.op{background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:22px;}
.op h3{margin:0 0 14px; font-size:15px; color:var(--blue); letter-spacing:0.02em;}
.op .chips{display:flex; flex-wrap:wrap; gap:8px;}
.op .chip{background:var(--blue-soft); color:var(--ink); border-radius:999px; padding:8px 16px; font-weight:700; font-size:16px;}
.op dl{margin:0; display:grid; gap:12px;}
.op dt{font-size:13px; color:var(--ink-soft); margin:0;}
.op dd{margin:0; font-size:22px; font-weight:700; line-height:1.3;}
.op dd small{font-size:14px; font-weight:500; color:var(--ink-soft); margin-left:4px;}
.op.wide{grid-column:span 2;}
@media (max-width:640px){ .op.wide{grid-column:auto;} }

.cta{
  margin:72px 0 0; padding:34px 26px; border-radius:20px; text-align:center;
  background:var(--blue); color:#fff;
}
.cta h2{color:#fff; margin-bottom:6px;}
.cta p{margin:0 0 20px; opacity:0.9;}
.cta .btn{border-color:transparent;}
.cta-actions{display:flex; gap:10px; justify-content:center; flex-wrap:wrap;}
footer{padding:28px 0 44px; text-align:center; color:var(--ink-soft); font-size:13px;}
`

function BallArt() {
  return (
    <svg className="ball-art" viewBox="0 0 420 260" fill="none" aria-hidden="true">
      <path d="M20 40 L190 96" stroke="var(--blue)" strokeWidth="10" strokeLinecap="round" />
      <path d="M170 132 L330 96" stroke="var(--blue)" strokeWidth="10" strokeLinecap="round" opacity="0.85" />
      <path d="M250 190 L410 236" stroke="var(--blue)" strokeWidth="10" strokeLinecap="round" opacity="0.7" />
      <circle cx="46" cy="20" r="14" fill="var(--accent)" />
      <path d="M62 30 C 96 44, 128 44, 150 56" stroke="var(--accent)" strokeWidth="3" strokeDasharray="2 9" strokeLinecap="round" />
      <path d="M198 106 C 214 120, 196 124, 176 128" stroke="var(--accent)" strokeWidth="3" strokeDasharray="2 9" strokeLinecap="round" />
      <path d="M326 108 C 344 130, 300 150, 262 184" stroke="var(--accent)" strokeWidth="3" strokeDasharray="2 9" strokeLinecap="round" />
      <rect x="380" y="200" width="6" height="34" rx="3" fill="var(--ink-soft)" />
      <path d="M386 200 L410 209 L386 218 Z" fill="var(--accent)" />
    </svg>
  )
}

export default function Home() {
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: css }} />
      <div className="wrap">
        <header className="nav">
          <a className="brand" href="/">
            <span>⚙</span> 발명융합과학교실
          </a>
          <nav className="nav-actions">
            <a className="btn" href="/design.html">학생 로그인</a>
            <a className="btn" href="/index.html">선생님 로그인</a>
          </nav>
        </header>

        <div className="hero">
          <div className="hero-inner">
            <span className="kicker">발명융합과학교실 수업 소개</span>
            <h1>
              이론을 전달하는 수업이 아니라, <em>직접 발명해보는</em> 수업입니다
            </h1>
            <p className="lead">
              발명 수업의 성패는 거창한 재료보다, 문제를 발견하는 관점과 실패를 두려워하지 않고 만들어보는 과정을 설계하는 데 달려 있습니다.
            </p>
            <div className="hero-cta">
              <a className="btn primary big" href="/design.html">학생 로그인</a>
              <a className="btn big" href="#how">수업 방식 보기</a>
            </div>
          </div>
          <BallArt />
        </div>

        <p className="summary">
          결국 발명융합과학교실은 <em>다양한 경험</em>을 하면서 <em>불편함</em>을 많이많이 겪어보고, 그 <em>문제를 스스로 해결</em>해보는 수업입니다.
        </p>

        <section id="how">
          <p className="eyebrow">다른 수업과 무엇이 다른가요</p>
          <h2>비슷해 보이지만, 수업을 진행하는 방식이 다릅니다</h2>
          <p className="section-lead">
            발명융합과학교실은 다양한 과학 수업과 비슷해 보이지만, 지식을 전달하는 데서 끝나지 않습니다. 발명 수업의 성패는 거창한 재료보다 문제를 발견하는 관점과, 실패를 두려워하지 않고 만들어보는 과정을 설계하는 데 달려 있다고 생각하기 때문입니다.
          </p>
          <div className="compare">
            <div className="col">
              <h3>지식 전달 중심 수업</h3>
              <ul>{COMPARE.left.map((t) => <li key={t}>{t}</li>)}</ul>
            </div>
            <div className="col hl">
              <h3>발명융합과학교실</h3>
              <ul>{COMPARE.right.map((t) => <li key={t}>{t}</li>)}</ul>
            </div>
          </div>
        </section>

        <section>
          <p className="eyebrow">수업의 흐름</p>
          <h2>경험하고, 불편함을 만나고, 해결해봅니다</h2>
          <p className="section-lead">문제를 해결하는 방식을 배워보는 것이 수업의 중심입니다. 다양한 경험 속에서 마주친 불편함이 그대로 문제 해결의 재료가 됩니다.</p>
          <div className="steps">
            {FLOW.map(([title, desc]) => (
              <div className="step" key={title}>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <p className="eyebrow">발상법</p>
          <h2>기존 사물을 비틀어서 새로운 것을 떠올립니다</h2>
          <p className="section-lead">
            <b>SCAMPER(스캠퍼) 기법</b>은 기존 사물을 비틀어보는 대표적인 발상법입니다. 일곱 가지 질문을 던지며 익숙한 물건을 새롭게 바라봅니다.
          </p>
          <div className="scamper">
            {SCAMPER.map(([letter, ko, en, desc, ex]) => (
              <div className="sc" key={letter}>
                <b>{letter}</b>
                <div>
                  <h3>{ko}</h3>
                  <small>{en}</small>
                  <p>{desc}</p>
                  <span className="ex">예) {ex}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="addsub">
            {[ADDSUB.add, ADDSUB.sub].map((a) => (
              <div className="card" key={a.title}>
                <p className="eyebrow">기초 발상 연습</p>
                <h3>{a.title} 기법</h3>
                <p>{a.desc}</p>
                <ul>{a.ex.map((e) => <li key={e}>{e}</li>)}</ul>
              </div>
            ))}
          </div>
        </section>

        <section>
          <p className="eyebrow">문제 해결 방법</p>
          <h2>문제를 해결하는 방식을 배웁니다</h2>
          <p className="section-lead">아이디어를 넓히고, 정리하고, 실제로 움직이게 만드는 다섯 가지 도구를 배웁니다.</p>
          <div className="methods">
            {METHODS.map(([title, desc]) => (
              <div className="method" key={title}>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <p className="eyebrow">수업 과목</p>
          <h2>다양한 과목으로 구성되어 있습니다</h2>
          <div className="subjects">
            <div className="subject goldberg">
              <div>
                <span className="badge">대표 수업</span>
                <h3>골드버그 장치 만들기</h3>
                <p>골드버그 장치는 아주 간단한 일을 일부러 여러 단계의 연쇄 작동으로 해내는 장치입니다.</p>
                <p>3D 설계 도구로 먼저 설계해보고, 그대로 실물로 만들어봅니다. 만들다 보면 생각대로 되지 않는 순간이 오고, 그때 고쳐보는 경험이 수업의 핵심입니다.</p>
              </div>
              <ul>
                <li>3D 공간에서 부품을 놓고 공을 굴려보기</li>
                <li>타공판 · 기둥 · 경첩 · ㄱ자 연결대 · 직선길</li>
                <li>설계한 그대로 실물로 만들어보기</li>
              </ul>
            </div>
            {SUBJECTS.map(([name, desc]) => (
              <div className="subject" key={name}>
                <h3>{name}</h3>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="ops">
          <p className="eyebrow">수업 운영</p>
          <h2>특강형도 방과후형도 모두 가능합니다</h2>
          <p className="section-lead">기관과 대상에 맞춰 수업을 운영할 수 있습니다.</p>
          <div className="ops">
            <div className="op">
              <h3>수업 형태</h3>
              <div className="chips">
                <span className="chip">특강형</span>
                <span className="chip">방과후형</span>
              </div>
            </div>
            <div className="op wide">
              <h3>방과후 운영</h3>
              <dl>
                <div>
                  <dt>분기제</dt>
                  <dd>12회 × 4분기</dd>
                </div>
                <div>
                  <dt>학기제</dt>
                  <dd>24회 × 2학기</dd>
                </div>
                <div>
                  <dt>방학</dt>
                  <dd>방학특강</dd>
                </div>
              </dl>
            </div>
            <div className="op">
              <h3>진행 장소</h3>
              <div className="chips">
                <span className="chip">방과후</span>
                <span className="chip">문화센터</span>
              </div>
            </div>
            <div className="op wide">
              <h3>수업 대상</h3>
              <div className="chips">
                <span className="chip">초등</span>
                <span className="chip">중등</span>
                <span className="chip">고등</span>
                <span className="chip">대학</span>
                <span className="chip">기업</span>
              </div>
            </div>
          </div>
        </section>

        <section>
          <p className="eyebrow">발명융합과학교실 온라인 설계실</p>
          <h2>내 계정으로 들어가서 설계하고, 이어서 만듭니다</h2>
          <p className="section-lead">학교에서도 집에서도, 선생님이 만들어준 내 계정으로 들어가 3D 설계를 이어갈 수 있습니다.</p>
          <div className="steps">
            {ROOM_STEPS.map(([title, desc]) => (
              <div className="step" key={title}>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="cta">
          <h2>발명융합과학교실에 들어가기</h2>
          <p>선생님이 알려준 아이디와 비밀번호로 로그인하세요.</p>
          <div className="cta-actions">
            <a className="btn primary big" href="/design.html">학생 로그인</a>
            <a className="btn big" href="/index.html">선생님 로그인</a>
          </div>
        </div>
        <footer>발명융합과학교실</footer>
      </div>
    </>
  )
}

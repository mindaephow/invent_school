import Tabs from './Tabs'
import LoginLinks from './LoginLinks'

export const metadata = {
  title: '발명융합과학교실',
  description:
    '이론을 전달하는 주입식 수업이 아니라, 원리를 전달하고 스스로 실습하고 느끼며 실패를 통해 문제해결방법을 찾아보는 체험형 수업입니다.',
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

const ROOM_STEPS = [
  ['로그인', '선생님이 알려준 아이디와 비밀번호로 들어갑니다.'],
  ['프로젝트 만들기', '이름을 붙여 새 프로젝트를 시작하거나, 저장해 둔 작업을 이어서 합니다.'],
  ['설계하기', '타공판, 기둥, 경첩, ㄱ자 연결대, 종이테이프, 직선길을 3D 공간에 놓고 공을 굴려 목표 깃발까지 보내봅니다.'],
  ['저장하고 제출', '나갈 때 작업이 저장되고, 완성하면 과제를 제출합니다.'],
]

const CONTACT_PHONE = '010-2704-0307'

const FAQ = [
  ['1회 수업은 몇 분인가요?', '초등학교 방과후의 경우 일주일에 한 번, 80분~100분 수업이 기본입니다.'],
  ['특강은 보통 몇 시간, 몇 회인가요?', '수업 형태에 따라 다릅니다.'],
  ['한 반은 몇 명까지인가요?', '인원 제한은 없으며, 진행 장소나 상황에 따라 결정됩니다.'],
  ['학생이 따로 준비할 것이 있나요? 교구와 재료는 누가 제공하나요?', '준비할 것은 없습니다. 특이사항이 없는 경우 교구와 재료는 모두 선생님이 준비합니다.'],
  ['코딩이나 과학 지식이 없어도 들을 수 있나요?', '네, 수업 특성상 사전 지식이 없어도 수업이 가능합니다.'],
  ['분기나 학기마다 어떤 과목을 어떤 순서로 배우나요?', '항공과학, 우주과학, 과학실험, 로봇과학, 발명과학, 생활과학을 분기나 학기 진행 상황에 따라 골고루 진행합니다.'],
  ['만든 작품은 가져갈 수 있나요?', '당일 수업에 따라 가져갈 결과물이 있기도 합니다. 다만 골드버그 장치는 부피가 커서 결과물을 분해하기 때문에 가져갈 수 없습니다.'],
  ['발표나 전시가 있나요?', '학교 일정에 따라 진행하기도 합니다.'],
  ['수업은 어떻게 신청하나요?', '방과후의 경우 학교에서 신청 안내가 나갑니다.'],
  ['학교, 문화센터, 기업에서 수업을 요청하려면 어떻게 하나요?', 'PHONE'],
  ['집에서도 온라인 설계실을 쓸 수 있나요?', '수업에 참여하는 학생은 집에서도 설계가 가능합니다.'],
  ['결석하면 보강이 되나요?', '학교 규정에 따릅니다.'],
  ['수강료는 얼마인가요?', '수업을 진행하는 단체와 협의합니다.'],
]

const OPS_TABS = [
  {
    id: 'type',
    label: '수업 형태',
    content: (
      <div className="bigchips">
        <span className="bigchip">특강형</span>
        <span className="bigchip">방과후형</span>
      </div>
    ),
  },
  {
    id: 'after',
    label: '방과후 운영',
    content: (
      <div className="stats">
        {[
          ['분기제', '12회 × 4분기'],
          ['학기제', '24회 × 2학기'],
          ['방학', '방학특강'],
        ].map(([label, value]) => (
          <div className="stat" key={label}>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'place',
    label: '진행 장소',
    content: (
      <div className="bigchips">
        <span className="bigchip">방과후</span>
        <span className="bigchip">문화센터</span>
      </div>
    ),
  },
  {
    id: 'level',
    label: '수업 대상',
    content: (
      <div className="bigchips">
        {['초등', '중등', '고등', '대학', '기업'].map((c) => (
          <span className="bigchip" key={c}>{c}</span>
        ))}
      </div>
    ),
  },
]

// 과목별 활동은 웹에서 조사한 일반적인 방과후 수업 내용을 바탕으로 정리한 것이다(실제 수업과 다르면 수정).
const SUBJECTS = [
  {
    id: 'air',
    label: '항공과학',
    desc: '하늘을 나는 원리를 발명의 눈으로 만나고, 직접 만들어 날려보는 수업',
    topics: [
      '종이비행기를 접어 날리며 날개 모양과 각도에 따라 달라지는 비행 관찰하기',
      '글라이더와 고무동력기를 만들어 멀리, 오래 날려보기',
      '뜨는 힘(양력)과 앞으로 나아가는 힘(추력) 알아보기',
      '드론을 조립해보고 기본 비행 원리 체험하기',
    ],
  },
  {
    id: 'space',
    label: '우주과학',
    desc: '태양계에서 우주 탐사까지, 우주를 발명의 눈으로 만나는 수업',
    topics: [
      '공기의 힘으로 날아가는 로켓을 만들어 발사해보기',
      '태양계 행성의 크기와 거리를 몸으로 비교해보기',
      '별자리와 북극성을 찾아보기',
      '우주 탐사기지를 설계하고 누리호 모형 만들어보기',
    ],
  },
  {
    id: 'exp',
    label: '과학실험',
    desc: '직접 보고 만지고 실험하며 원리를 알아가는 수업',
    topics: [
      '풍선 로켓, 낙하산, 고무줄 자동차처럼 원리가 담긴 작품 만들어보기',
      '병 속 회오리, 용암 램프처럼 눈으로 확인하는 실험 해보기',
      '공기, 물질의 상태 변화, 전기와 자석, 지구와 우주 등 교과와 이어지는 주제 탐구하기',
    ],
  },
  {
    id: 'robot',
    label: '로봇과학',
    desc: '로봇이 움직이는 원리를 배우고 내가 생각한 로봇을 만드는 수업',
    topics: [
      '부품을 조립해 단계별로 다양한 로봇 만들어보기',
      '로봇의 구조와 동작 원리 익히기',
      '미션, 경주, 배틀로 만든 로봇 시험해보기',
      '공구 사용법과 기초 코딩을 익히고 창작 로봇 만들어보기',
    ],
  },
  {
    id: 'invent',
    label: '발명과학',
    desc: '발명의 눈으로 문제를 찾고 직접 만들어보는 수업',
    topics: [
      'SCAMPER와 더하기·빼기 기법으로 익숙한 물건 비틀어보기',
      '브레인스토밍과 마인드맵으로 아이디어 넓히기',
      '트리즈의 발명원리로 문제 해결 방법 배우기',
    ],
    feature: {
      title: '대표 활동 · 골드버그 장치 만들기',
      lines: [
        '골드버그 장치는 아주 간단한 일을 일부러 여러 단계의 연쇄 작동으로 해내는 장치입니다.',
        '3D 설계 도구로 먼저 설계해보고, 그대로 실물로 만들어봅니다. 만들다 보면 생각대로 되지 않는 순간이 오고, 그때 고쳐보는 경험이 수업의 핵심입니다.',
      ],
      bullets: ['3D 공간에서 부품을 놓고 공을 굴려보기', '타공판 · 기둥 · 경첩 · ㄱ자 연결대 · 직선길', '설계한 그대로 실물로 만들어보기'],
    },
  },
  {
    id: 'life',
    label: '생활과학',
    desc: '우리 주변 생활 속 현상에 숨은 과학 원리를 찾아보는 수업',
    topics: [
      '우유에 색소와 세제를 떨어뜨려 표면장력이 달라지는 모습 관찰하기',
      '접은 종이꽃이 물에서 펼쳐지는 모세관 현상 실험하기',
      '물질의 성질, 전기와 자석, 빛 같은 교과 개념을 생활 속 사례로 만나기',
    ],
  },
]

const SUBJECT_TABS = SUBJECTS.map((sub) => ({
  id: sub.id,
  label: sub.label,
  content: (
    <div className="subject-panel">
      <h3>{sub.label}</h3>
      <p className="subject-desc">{sub.desc}</p>
      {sub.topics && (
        <ul className="topic-list">
          {sub.topics.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      )}
      {sub.feature && (
        <div className="subject-feature">
          <h4>{sub.feature.title}</h4>
          {sub.feature.lines.map((l) => (
            <p key={l}>{l}</p>
          ))}
          <ul>
            {sub.feature.bullets.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  ),
}))

const css = `
:root{
  --font:'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', system-ui, sans-serif;
  --bg:#F7F8FB; --panel:#FFFFFF; --soft:#F1F3F9; --line:#E4E8F1;
  --ink:#0F1729; --ink-2:#4A5568; --ink-3:#8A94A8;
  --blue:#2D5BFF; --blue-ink:#2449D6; --blue-soft:#EEF2FF; --blue-line:#D5DEFF; --hl:rgba(45,91,255,0.16);
  --accent:#FF6A3D;
  --primary:#0F1729; --on-primary:#FFFFFF;
  --dark:#0F1729; --dark-2:#1B2540; --on-dark:#FFFFFF; --on-dark-2:rgba(255,255,255,0.72);
  --shadow-s:0 1px 2px rgba(15,23,41,0.04);
  --shadow-m:0 1px 2px rgba(15,23,41,0.04), 0 14px 32px -16px rgba(15,23,41,0.16);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0A0F1E; --panel:#111A30; --soft:#16203A; --line:#222D48;
    --ink:#EEF1F8; --ink-2:#A9B3C8; --ink-3:#6F7A93;
    --blue:#7F9CFF; --blue-ink:#9DB3FF; --blue-soft:#161F3D; --blue-line:#2A3866; --hl:rgba(127,156,255,0.22);
    --accent:#FF8659;
    --primary:#EEF1F8; --on-primary:#0A0F1E;
    --dark:#16203A; --dark-2:#1D2A4A; --on-dark:#FFFFFF; --on-dark-2:rgba(255,255,255,0.72);
    --shadow-s:none;
    --shadow-m:0 14px 32px -16px rgba(0,0,0,0.6);
  }
}
*{box-sizing:border-box;}
button, input, summary{font-family:inherit;}
html{scroll-behavior:smooth; scroll-padding-top:76px;}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--font); font-size:16px; line-height:1.7; letter-spacing:-0.012em;
  word-break:keep-all; overflow-wrap:break-word;
  -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; text-rendering:optimizeLegibility;
}
a{color:inherit;}
.wrap{max-width:1080px; margin:0 auto; padding:0 24px;}
@media (max-width:520px){ .wrap{padding:0 16px;} }

.topbar{position:sticky; top:0; z-index:50; background:color-mix(in srgb, var(--bg) 82%, transparent); backdrop-filter:saturate(180%) blur(14px); -webkit-backdrop-filter:saturate(180%) blur(14px); border-bottom:1px solid transparent;}
.nav{display:flex; align-items:center; gap:24px; height:64px;}
.brand{display:inline-flex; align-items:center; gap:10px; font-weight:800; font-size:19px; letter-spacing:-0.04em; text-decoration:none; white-space:nowrap;}
.logo{flex:none; width:32px; height:32px; border-radius:10px; display:block;}
.nav-links{display:flex; gap:4px; margin-left:8px;}
.nav-links a{font-size:14.5px; font-weight:500; color:var(--ink-2); text-decoration:none; padding:8px 12px; border-radius:8px;}
.nav-links a:hover{color:var(--ink); background:var(--soft);}
.nav-actions{display:flex; gap:8px; margin-left:auto;}
@media (max-width:860px){ .nav-links{display:none;} }
@media (max-width:520px){ .brand{font-size:16.5px; gap:8px;} .logo{width:28px; height:28px;} .nav{gap:10px;} }

.btn{
  display:inline-flex; align-items:center; justify-content:center; text-decoration:none; font-weight:600; font-size:14px; line-height:1; white-space:nowrap;
  padding:11px 16px; border-radius:999px; border:1px solid var(--line); background:var(--panel); color:var(--ink);
  transition:background .15s ease, border-color .15s ease, transform .15s ease;
}
.btn:hover{border-color:var(--ink-3);}
.btn.primary{background:var(--primary); border-color:var(--primary); color:var(--on-primary);}
.btn.primary:hover{opacity:0.9;}
.btn.big{font-size:15.5px; padding:16px 26px;}
.btn:focus-visible{outline:2px solid var(--blue); outline-offset:3px;}
@media (max-width:520px){ .nav-actions .btn{padding:9px 12px; font-size:13px;} }

.hero{
  position:relative; margin:12px 0 0; padding:72px 48px 76px; border-radius:32px; overflow:hidden;
  border:1px solid var(--line); background:var(--panel);
  background-image:
    radial-gradient(60% 80% at 100% 0%, var(--blue-soft) 0%, transparent 70%),
    radial-gradient(40% 60% at 0% 100%, var(--blue-soft) 0%, transparent 70%);
}
.hero::before{
  content:""; position:absolute; inset:0; opacity:0.5; pointer-events:none;
  background-image:radial-gradient(var(--blue-line) 1px, transparent 1.2px); background-size:22px 22px;
  -webkit-mask-image:linear-gradient(115deg, transparent 30%, #000 100%); mask-image:linear-gradient(115deg, transparent 30%, #000 100%);
}
.hero-inner{position:relative; z-index:1; max-width:600px;}
.kicker{display:inline-flex; align-items:center; gap:8px; font-size:13px; font-weight:600; color:var(--blue-ink); background:var(--blue-soft); border:1px solid var(--blue-line); padding:6px 14px 6px 10px; border-radius:999px; letter-spacing:-0.01em;}
.kicker::before{content:""; width:7px; height:7px; border-radius:50%; background:var(--accent);}
h1{font-size:clamp(26px, 4.1vw, 42px); line-height:1.42; margin:22px 0 20px; letter-spacing:-0.042em; font-weight:700; word-break:keep-all; text-wrap:balance;}
h1 em{font-style:normal; color:var(--blue-ink); background:linear-gradient(transparent 64%, var(--hl) 64%); padding:0 2px; border-radius:2px;}
.lead{font-size:clamp(16px, 1.9vw, 18px); color:var(--ink-2); margin:0 0 34px; max-width:520px; text-wrap:pretty;}
.hero-cta{display:flex; gap:10px; flex-wrap:wrap;}
.ball-art{position:absolute; right:32px; bottom:28px; width:min(38%, 380px); z-index:1;}
@media (max-width:1100px){ .ball-art{display:none;} .hero-inner{max-width:680px;} }
@media (max-width:760px){ .hero{padding:44px 22px 48px; border-radius:24px;} .btn.big{padding:14px 22px;} }

.summary{
  margin:16px 0 0; padding:34px 40px; border-radius:28px; background:var(--blue-soft);
  border:1px solid var(--blue-line); font-size:clamp(18px, 2.5vw, 24px); line-height:1.6; font-weight:600; letter-spacing:-0.035em; text-wrap:balance;
}
.summary em{font-style:normal; color:var(--blue-ink); background:linear-gradient(transparent 64%, var(--hl) 64%);}
@media (max-width:760px){ .summary{padding:24px 22px; border-radius:22px;} }

section{padding:104px 0 0; counter-increment:sec;}
@media (max-width:760px){ section{padding-top:72px;} }
body{counter-reset:sec;}
section > .eyebrow{display:flex; align-items:center; gap:10px; font-size:13.5px; font-weight:600; color:var(--blue-ink); letter-spacing:-0.01em; margin:0 0 14px;}
section > .eyebrow::before{content:counter(sec, decimal-leading-zero); font-variant-numeric:tabular-nums; font-weight:700; color:var(--ink-3); padding-right:10px; border-right:1px solid var(--line);}
h2{font-size:clamp(25px, 3.5vw, 36px); line-height:1.32; margin:0 0 16px; letter-spacing:-0.045em; font-weight:700; text-wrap:balance; max-width:760px;}
.section-lead{color:var(--ink-2); font-size:17px; margin:0 0 40px; max-width:700px; text-wrap:pretty;}
.section-lead b{color:var(--ink); font-weight:600;}
@media (max-width:760px){ .section-lead{font-size:16px; margin-bottom:28px;} }
section.plain > h2{margin-bottom:28px;}

.card{background:var(--panel); border:1px solid var(--line); border-radius:24px; padding:30px; box-shadow:var(--shadow-s);}
.card h3{margin:0 0 8px; font-size:20px; letter-spacing:-0.035em; font-weight:700;}
.card p{margin:0; color:var(--ink-2);}
.card .eyebrow{font-size:12.5px; font-weight:600; color:var(--ink-3); margin:0 0 10px; letter-spacing:0;}

.compare{display:grid; grid-template-columns:1fr 1fr; gap:16px;}
@media (max-width:760px){ .compare{grid-template-columns:1fr;} }
.col{background:var(--panel); border:1px solid var(--line); border-radius:24px; padding:32px;}
.col.hl{background:var(--dark); border-color:var(--dark); color:var(--on-dark); box-shadow:var(--shadow-m);}
.col h3{margin:0 0 20px; font-size:14px; font-weight:600; color:var(--ink-3); letter-spacing:0;}
.col.hl h3{color:var(--on-dark-2);}
.col ul{list-style:none; margin:0; padding:0; display:grid; gap:0;}
.col li{display:flex; gap:12px; align-items:flex-start; color:var(--ink-2); font-size:16.5px; padding:14px 0; border-top:1px solid var(--line);}
.col li:first-child{border-top:0; padding-top:0;}
.col li::before{content:"–"; color:var(--ink-3); font-weight:600;}
.col.hl li{color:var(--on-dark); font-weight:500; border-top-color:rgba(255,255,255,0.12);}
.col.hl li::before{content:"✓"; color:#8FB0FF; font-weight:700;}
@media (max-width:760px){ .col{padding:24px;} }

.steps{display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; counter-reset:step;}
@media (max-width:960px){ .steps{grid-template-columns:repeat(2, 1fr);} }
@media (max-width:560px){ .steps{grid-template-columns:1fr;} }
.step{background:var(--panel); border:1px solid var(--line); border-radius:24px; padding:28px; position:relative;}
.step::before{
  counter-increment:step; content:counter(step, decimal-leading-zero);
  display:block; font-size:14px; font-weight:700; color:var(--blue-ink); font-variant-numeric:tabular-nums;
  margin-bottom:38px; letter-spacing:0.02em;
}
.step::after{content:""; position:absolute; left:28px; top:52px; width:28px; height:3px; border-radius:2px; background:var(--accent);}
.step h3{margin:0 0 10px; font-size:19px; letter-spacing:-0.035em; font-weight:700;}
.step p{margin:0; color:var(--ink-2); font-size:15.5px;}

.scamper{display:grid; grid-template-columns:repeat(auto-fit, minmax(310px, 1fr)); gap:14px;}
.sc{background:var(--panel); border:1px solid var(--line); border-radius:22px; padding:22px; display:flex; gap:18px; align-items:flex-start;}
.sc b{
  flex:none; width:52px; height:52px; border-radius:16px; display:grid; place-items:center;
  font-weight:800; font-size:24px; background:var(--blue-soft); color:var(--blue-ink); border:1px solid var(--blue-line);
  letter-spacing:0;
}
.sc h3{margin:0; font-size:18px; letter-spacing:-0.035em; font-weight:700;}
.sc small{display:block; color:var(--ink-3); font-size:12.5px; margin:1px 0 8px; letter-spacing:0;}
.sc p{margin:0 0 12px; color:var(--ink-2); font-size:15px; line-height:1.6;}
.sc .ex{margin:0; display:inline-block; font-size:13.5px; font-weight:500; color:var(--ink); background:var(--soft); border-radius:8px; padding:6px 11px; line-height:1.5;}

.addsub{display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px;}
@media (max-width:760px){ .addsub{grid-template-columns:1fr;} }
.addsub .card ul{list-style:none; margin:18px 0 0; padding:0; display:flex; flex-wrap:wrap; gap:8px;}
.addsub .card li{font-size:14px; font-weight:500; background:var(--soft); color:var(--ink); border-radius:999px; padding:8px 14px; line-height:1.4;}

.methods{display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px; counter-reset:m;}
.method{background:var(--panel); border:1px solid var(--line); border-radius:24px; padding:28px; display:grid; grid-template-columns:auto 1fr; column-gap:18px;}
.method::before{counter-increment:m; content:counter(m); grid-row:1 / span 2; width:34px; height:34px; border-radius:50%; display:grid; place-items:center; font-weight:700; font-size:14px; background:var(--blue-soft); color:var(--blue-ink); border:1px solid var(--blue-line);}
.method h3{margin:4px 0 8px; font-size:18.5px; letter-spacing:-0.035em; font-weight:700;}
.method p{margin:0; color:var(--ink-2); font-size:15.5px;}

.tabs-wrap{display:block;}
.tablist{display:flex; gap:2px; padding:5px; width:fit-content; max-width:100%; overflow-x:auto; background:var(--soft); border:1px solid var(--line); border-radius:999px; scrollbar-width:none; -webkit-overflow-scrolling:touch;}
.tablist::-webkit-scrollbar{display:none;}
.tab{
  flex:none; cursor:pointer; font:inherit; font-weight:600; font-size:15px; letter-spacing:-0.02em; padding:10px 20px;
  border-radius:999px; border:0; background:transparent; color:var(--ink-2);
  transition:background .15s ease, color .15s ease, box-shadow .15s ease;
}
.tab:hover{color:var(--ink);}
.tab.on{background:var(--panel); color:var(--ink); box-shadow:0 1px 2px rgba(15,23,41,0.10), 0 0 0 1px var(--line);}
.tab:focus-visible{outline:2px solid var(--blue); outline-offset:2px;}
.tabpanel{
  margin-top:18px; min-height:170px; padding:36px; border-radius:28px; display:flex; align-items:center;
  background:var(--panel); border:1px solid var(--line); box-shadow:var(--shadow-m);
  animation:tabin .3s ease;
}
.tabpanel.block{display:block; padding:40px;}
@keyframes tabin{from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:none;}}
@media (prefers-reduced-motion: reduce){ .tabpanel{animation:none;} html{scroll-behavior:auto;} }
@media (max-width:760px){ .tabpanel, .tabpanel.block{padding:24px 20px; border-radius:22px;} }
.bigchips{display:flex; flex-wrap:wrap; gap:12px;}
.bigchip{background:var(--blue-soft); color:var(--blue-ink); border:1px solid var(--blue-line); border-radius:999px; padding:14px 30px; font-weight:700; font-size:clamp(18px, 2.6vw, 24px); letter-spacing:-0.035em;}
.stats{display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:14px; width:100%;}
.stat{background:var(--soft); border-radius:20px; padding:24px;}
.stat-label{font-size:13.5px; font-weight:600; color:var(--ink-3); margin-bottom:8px; letter-spacing:0;}
.stat-value{font-size:clamp(22px, 3vw, 28px); font-weight:700; line-height:1.3; letter-spacing:-0.04em;}

.subject-panel h3{margin:0 0 8px; font-size:clamp(24px, 3.4vw, 32px); letter-spacing:-0.045em; font-weight:700;}
.subject-desc{margin:0; color:var(--ink-2); font-size:17px;}
.topic-list{list-style:none; margin:28px 0 0; padding:0; display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:12px;}
.topic-list li{position:relative; background:var(--soft); border-radius:18px; padding:18px 18px 18px 54px; font-size:15.5px; line-height:1.6;}
.topic-list li::before{content:"✓"; position:absolute; left:18px; top:18px; width:24px; height:24px; border-radius:50%; display:grid; place-items:center; background:var(--blue); color:#fff; font-size:12px; font-weight:800; line-height:1;}
.subject-feature{
  margin-top:26px; padding:32px; border-radius:24px; color:var(--on-dark); position:relative; overflow:hidden;
  background:radial-gradient(70% 120% at 100% 0%, rgba(45,91,255,0.5) 0%, transparent 65%), var(--dark);
}
.subject-feature h4{margin:0 0 14px; font-size:20px; letter-spacing:-0.035em; font-weight:700; color:var(--on-dark);}
.subject-feature p{margin:0 0 10px; color:var(--on-dark-2); font-size:16px;}
.subject-feature ul{list-style:none; margin:20px 0 0; padding:0; display:flex; flex-wrap:wrap; gap:8px;}
.subject-feature li{background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.14); border-radius:999px; padding:8px 15px; font-size:14px; font-weight:500;}
@media (max-width:760px){ .subject-feature{padding:24px 20px;} }

.faq{border-top:1px solid var(--line); max-width:820px;}
.faq details{border-bottom:1px solid var(--line);}
.faq summary{
  cursor:pointer; list-style:none; position:relative; padding:24px 44px 24px 0;
  font-weight:600; font-size:17.5px; line-height:1.5; letter-spacing:-0.03em;
}
.faq summary::-webkit-details-marker{display:none;}
.faq summary::after{
  content:""; position:absolute; right:4px; top:50%; width:10px; height:10px; margin-top:-8px;
  border-right:2px solid var(--ink-3); border-bottom:2px solid var(--ink-3); transform:rotate(45deg); transition:transform .2s ease, border-color .2s ease;
}
.faq details[open] summary::after{transform:rotate(-135deg); margin-top:-3px; border-color:var(--blue);}
.faq summary:hover{color:var(--blue-ink);}
.faq summary:focus-visible{outline:2px solid var(--blue); outline-offset:2px; border-radius:6px;}
.faq .ans{margin:0; padding:0 44px 26px 0; color:var(--ink-2); font-size:16.5px; text-wrap:pretty;}
.faq .ans a{color:var(--blue-ink); font-weight:700; text-decoration:none;}
.faq .ans a:hover{text-decoration:underline;}
footer a{color:inherit;}

.cta{
  margin:112px 0 0; padding:72px 32px; border-radius:36px; text-align:center; color:var(--on-dark); position:relative; overflow:hidden;
  background:radial-gradient(55% 90% at 50% 0%, rgba(45,91,255,0.55) 0%, transparent 70%), var(--dark);
}
.cta h2{color:var(--on-dark); margin:0 auto 12px; text-align:center;}
.cta p{margin:0 0 30px; color:var(--on-dark-2); font-size:17px;}
.cta .btn{border-color:transparent;}
.cta .btn.primary{background:#fff; color:#0F1729;}
.cta .btn:not(.primary){background:rgba(255,255,255,0.12); color:#fff; border:1px solid rgba(255,255,255,0.22);}
.cta-actions{display:flex; gap:10px; justify-content:center; flex-wrap:wrap;}
@media (max-width:760px){ .cta{margin-top:80px; padding:48px 22px; border-radius:26px;} }
footer{padding:40px 0 56px; text-align:center; color:var(--ink-3); font-size:13.5px; letter-spacing:0;}
footer a{font-weight:600; color:var(--ink-2); text-decoration:none;}
footer a:hover{text-decoration:underline;}
#faq > h2{margin-bottom:36px;}
`

function Logo() {
  return (
    <svg className="logo" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="10" fill="#2D5BFF" />
      <path d="M6 10 L20 15" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M12 23 L26 19" stroke="#fff" strokeOpacity="0.7" strokeWidth="2.6" strokeLinecap="round" />
      <circle cx="9" cy="6.5" r="3" fill="#FF6A3D" />
    </svg>
  )
}

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
      <header className="topbar">
        <div className="wrap nav">
          <a className="brand" href="/">
            <Logo />
            발명융합과학교실
          </a>
          <nav className="nav-links" aria-label="페이지 안내">
            <a href="#how">수업 방식</a>
            <a href="#subjects">수업 과목</a>
            <a href="#ops">수업 운영</a>
            <a href="#faq">자주 묻는 질문</a>
          </nav>
          <div className="nav-actions">
            <LoginLinks variant="nav" />
          </div>
        </div>
      </header>
      <div className="wrap">

        <div className="hero">
          <div className="hero-inner">
            <span className="kicker">발명융합과학교실 수업 소개</span>
            <h1>
              이론을 전달하는 <em>주입식 수업</em>이 아니라, 원리를 전달하고 <em>스스로 실습하고 느끼며</em> 실패를 통해 문제해결방법을 찾아보는 <em>체험형 수업</em>입니다
            </h1>
            <p className="lead">
              발명 수업의 성패는 거창한 재료보다, 문제를 발견하는 관점과 실패를 두려워하지 않고 만들어보는 과정을 설계하는 데 달려 있습니다.
            </p>
            <div className="hero-cta">
              <LoginLinks variant="hero" />
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

        <section id="subjects">
          <p className="eyebrow">수업 과목</p>
          <h2>다양한 과목으로 구성되어 있습니다</h2>
          <p className="section-lead">탭을 눌러 과목별 수업을 확인해보세요.</p>
          <Tabs items={SUBJECT_TABS} label="수업 과목" panelClass="block" />
        </section>

        <section id="ops">
          <p className="eyebrow">수업 운영</p>
          <h2>특강형도 방과후형도 모두 가능합니다</h2>
          <p className="section-lead">기관과 대상에 맞춰 수업을 운영할 수 있습니다. 아래 탭을 눌러 확인해보세요.</p>
          <Tabs items={OPS_TABS} label="수업 운영 안내" />
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

        <section id="faq">
          <p className="eyebrow">자주 묻는 질문</p>
          <h2>궁금하신 점을 모았습니다</h2>
          <div className="faq">
            {FAQ.map(([q, a]) => (
              <details key={q}>
                <summary>{q}</summary>
                <p className="ans">
                  {a === 'PHONE' ? (
                    <>
                      <a href={'tel:' + CONTACT_PHONE.replace(/-/g, '')}>{CONTACT_PHONE}</a>로 문의해 주세요.
                    </>
                  ) : (
                    a
                  )}
                </p>
              </details>
            ))}
          </div>
        </section>

        <div className="cta">
          <h2>발명융합과학교실에 들어가기</h2>
          <p>선생님이 알려준 아이디와 비밀번호로 로그인하세요.</p>
          <div className="cta-actions">
            <LoginLinks variant="cta" />
          </div>
        </div>
        <footer>
          <div>발명융합과학교실</div>
          <div style={{ marginTop: 4 }}>
            기관 수업 문의 <a href={'tel:' + CONTACT_PHONE.replace(/-/g, '')}>{CONTACT_PHONE}</a>
          </div>
        </footer>
      </div>
    </>
  )
}

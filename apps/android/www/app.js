(() => {
  const D = window.QUIZ_DATA;
  const app = document.getElementById('app');
  const modal = document.getElementById('modal');
  const LS = {study:'ptStudy', learning:'ptLearningSession', progress:'ptProgress', history:'ptHistory', exam:'ptUnfinished'};
  const load = (k,d={}) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
  const save = (k,v) => localStorage.setItem(k, JSON.stringify(v));
  const esc = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const shuffle = a => { a=[...a]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]} return a; };
  const sample = (a,n) => shuffle(a).slice(0,Math.min(n,a.length));
  const chapterOf = k => D.categoryToChapter[k[1]] || '其他';
  const shortChapter = c => c.split('  ')[0];
  const localDate = (plus=0) => { const x=new Date(); x.setDate(x.getDate()+plus); return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}-${String(x.getDate()).padStart(2,'0')}`; };
  function studyProgress(){
    const raw=load(LS.study,{}),terms=new Set(D.knowledge.map(k=>k[0])),out={};
    Object.entries(raw).forEach(([key,value])=>{out[terms.has(key)&&!key.includes('::')?`knowledge::${key}`:key]=value});
    return out;
  }
  function completeStudyItems(chapter=null){
    const items=[];
    D.knowledge.forEach(k=>{const c=chapterOf(k);if(chapter&&c!==chapter)return;items.push({kind:'knowledge',key:`knowledge::${k[0]}`,chapter:c,title:k[0],description:k[2],tip:k[3],source:k})});
    D.applied.forEach(q=>{if(chapter&&q.chapter!==chapter)return;items.push({kind:'question',key:`applied::${q.id}`,chapter:q.chapter,title:q.prompt,description:`正确答案：${q.options[q.correct_index]}`,tip:q.explanation,source:q})});
    return items;
  }
  let state={screen:'home',session:[],pos:0,title:'',timed:false,timeLeft:0,timer:null,study:[],studyPos:0,studyScope:'all',revealed:false,studySelected:null};
  let lastExitBack=0;

  function closeCustomSelects(except=null){
    document.querySelectorAll('.custom-select.open').forEach(x=>{
      if(x!==except){x.classList.remove('open');x.querySelector('.custom-select-trigger')?.setAttribute('aria-expanded','false')}
    });
  }
  function enhanceSelects(root=app){
    root.querySelectorAll('select.select:not([data-enhanced])').forEach(select=>{
      select.dataset.enhanced='true';select.classList.add('native-select-hidden');
      const wrap=document.createElement('div');wrap.className='custom-select';
      const trigger=document.createElement('button');trigger.type='button';trigger.className='custom-select-trigger';trigger.setAttribute('aria-expanded','false');
      const label=document.createElement('span'),arrow=document.createElement('b');arrow.textContent='⌄';trigger.append(label,arrow);
      const menu=document.createElement('div');menu.className='custom-select-menu';menu.setAttribute('role','listbox');
      Array.from(select.options).forEach(option=>{
        const button=document.createElement('button');button.type='button';button.className='custom-select-option';button.dataset.value=option.value;button.textContent=option.textContent;button.setAttribute('role','option');
        button.onclick=e=>{e.stopPropagation();select.value=button.dataset.value;select.dispatchEvent(new Event('change',{bubbles:true}));sync();closeCustomSelects()};menu.appendChild(button);
      });
      const sync=()=>{const selected=select.options[select.selectedIndex];label.textContent=selected?.textContent||'请选择';menu.querySelectorAll('.custom-select-option').forEach(b=>{const active=b.dataset.value===select.value;b.classList.toggle('selected',active);b.setAttribute('aria-selected',String(active))})};
      trigger.onclick=e=>{e.stopPropagation();const opening=!wrap.classList.contains('open');closeCustomSelects(wrap);wrap.classList.toggle('open',opening);trigger.setAttribute('aria-expanded',String(opening))};
      wrap.append(trigger,menu);select.insertAdjacentElement('afterend',wrap);select.addEventListener('change',sync);sync();
    });
  }

  function toast(msg){const el=document.getElementById('toast');el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800)}
  function stopTimer(){if(state.timer){clearInterval(state.timer);state.timer=null}}
  function learningSession(){
    const x=load(LS.learning,null);
    return x&&Array.isArray(x.keys)&&x.keys.length&&Number.isInteger(x.pos)?x:null;
  }
  function saveLearningSession(){
    if(state.screen!=='study'||!state.study.length)return;
    save(LS.learning,{version:1,keys:state.study.map(x=>x.key),pos:state.studyPos,title:state.title,scope:state.studyScope,selected:state.studySelected,revealed:state.revealed,savedAt:new Date().toISOString()});
  }
  function resumeStudy(){
    const savedSession=learningSession();if(!savedSession){toast('没有可继续的学习记录');return}
    const lookup=new Map(completeStudyItems().map(x=>[x.key,x])),cards=savedSession.keys.map(key=>lookup.get(key)).filter(Boolean);
    if(!cards.length||cards.length!==savedSession.keys.length){localStorage.removeItem(LS.learning);toast('学习题库已更新，请重新开始');home('study');return}
    state.screen='study';state.returnTab='study';state.study=cards;state.studyPos=Math.min(savedSession.pos,cards.length-1);state.studyScope=savedSession.scope||'all';state.title=savedSession.title||'全部章节';state.studySelected=Number.isInteger(savedSession.selected)?savedSession.selected:null;state.revealed=!!savedSession.revealed;renderStudy();
  }
  function handleBackGesture(){
    if(document.querySelector('.custom-select.open')){closeCustomSelects();return}
    if(!modal.classList.contains('hidden')){closeModal();return}
    if(state.screen==='home'){
      if(state.homeTab!=='study'){home('study');return}
      const now=Date.now();
      if(now-lastExitBack<=2000){lastExitBack=0;const nativeApp=window.Capacitor?.Plugins?.App;if(nativeApp?.exitApp)nativeApp.exitApp();else toast('安卓设备中此时将退出软件');return}
      lastExitBack=now;toast('再侧滑一次退出 TorchGo·火炬学');return;
    }
    if(state.screen==='bank'||state.screen==='collection'){home('study');return}
    if(state.screen==='study'){saveLearningSession();home('study');return}
    if(state.screen==='quiz'){if(state.timed)saveExam();home(state.returnTab||'study');toast(state.timed?'考试进度已保存':'已退出本次测试');return}
    if(state.screen==='result'){home(state.returnTab||'study');return}
    home('study');
  }
  function setupNativeBack(){
    const nativeApp=window.Capacitor?.Plugins?.App;
    if(nativeApp?.addListener){nativeApp.addListener('backButton',handleBackGesture);nativeApp.addListener('appStateChange',({isActive})=>{if(!isActive)saveLearningSession()})}
    window.__torchGoBack=handleBackGesture;
  }
  function setupLaunchScreen(){
    const el=document.getElementById('launchScreen');if(!el)return;
    setTimeout(()=>{el.classList.add('leaving');setTimeout(()=>el.remove(),450)},1600);
  }
  document.addEventListener('click',()=>closeCustomSelects());

  function bottomNavigation(active){
    const tabs=[['study','✦','学习'],['chapter','▤','章节检测'],['overall','◎','整体测试'],['exam','◷','模拟考试'],['about','ⓘ','关于']];
    return `<nav class="bottom-nav" aria-label="主要功能"><div class="bottom-nav-inner">${tabs.map(([id,icon,label])=>`<button class="bottom-tab ${active===id?'active':''}" data-home-tab="${id}" ${active===id?'aria-current="page"':''}><span class="bottom-icon">${icon}</span><span>${label}</span></button>`).join('')}</div></nav>`;
  }

  function home(tab=state.homeTab||'study'){
    if(state.screen==='study')saveLearningSession();
    stopTimer(); state.screen='home';state.homeTab=tab;
    const sp=studyProgress(), tp=load(LS.progress,{}), hist=load(LS.history,[]);
    const unfinishedLearning=learningSession(),savedScope=unfinishedLearning&&(/^(all|\d+)$/.test(String(unfinishedLearning.scope)))?String(unfinishedLearning.scope):'all';
    const mastered=Object.values(sp).filter(x=>x.status==='mastered').length;
    const due=Object.values(sp).filter(x=>(x.dueDate||'9999')<=localDate()).length;
    const attempts=Object.values(tp).reduce((s,x)=>s+(x.attempts||0),0), correct=Object.values(tp).reduce((s,x)=>s+(x.correct||0),0);
    const accuracy=attempts?Math.round(correct/attempts*100):0;
    const options=[`<option value="all" ${savedScope==='all'?'selected':''}>全部章节</option>`,...D.chapters.map((c,i)=>`<option value="${i}" ${savedScope===String(i)?'selected':''}>${esc(c)}</option>`)].join('');
    const resumeLearning=unfinishedLearning?`<button class="resume-study" id="resumeStudyBtn"><span class="resume-study-icon">▶</span><span><strong>继续上次学习</strong><small>${esc(unfinishedLearning.title||'学习模式')} · 第 ${Math.min(unfinishedLearning.pos+1,unfinishedLearning.keys.length)}/${unfinishedLearning.keys.length} 项</small></span><b>继续 ›</b></button>`:'';
    const chapterOptions=D.chapters.map((c,i)=>`<option value="${i}">${esc(c)}</option>`).join('');
    const contents={
      study:`<section class="welcome-card"><div><span class="eyebrow">LEARNING SPACE</span><h2>把知识真正学会</h2><p>知识卡片与应用题统一学习，按掌握程度智能安排复习。</p></div><span class="content-count">779<small>项内容</small></span></section>
        <section class="quick-stats"><button class="stat-action" data-collection="knowledge"><strong>${D.knowledge.length}</strong><span>知识卡片</span><small>查看 ›</small></button><button class="stat-action" data-collection="applied"><strong>${D.applied.length}</strong><span>应用题</span><small>查看 ›</small></button><button class="stat-action" data-collection="mastered"><strong>${mastered}</strong><span>已掌握</span><small>查看 ›</small></button><button class="stat-action" data-collection="due"><strong>${due}</strong><span>待复习</span><small>查看 ›</small></button></section>
        <section class="panel"><div class="panel-title"><div><span class="section-icon blue">学</span><div><h3>完整题库学习</h3><p>学习位置自动保存在本机，退出后可以接着学习。</p></div></div></div>${resumeLearning}<label class="field-label" for="studyChapter">学习章节</label><select id="studyChapter" class="select">${options}</select><button class="btn full primary-action" id="studyBtn">${unfinishedLearning?'继续当前章节':'开始学习'} <span>→</span></button><div class="split-actions"><button class="soft-action" id="browseBtn">浏览完整题库</button><button class="soft-action" id="dueBtn">复习今日到期</button></div></section>
        <section class="panel compact-panel"><div class="panel-title"><div><span class="section-icon violet">章</span><div><h3>十章知识框架</h3><p>579 张卡片 + 200 道应用题</p></div></div></div><div class="chapter-mini-list">${D.chapters.map(c=>`<div><span>${esc(c)}</span><small>${D.knowledge.filter(k=>chapterOf(k)===c).length}卡 · ${D.applied.filter(q=>q.chapter===c).length}题</small></div>`).join('')}</div></section>`,
      chapter:`<section class="tab-intro"><span class="eyebrow">CHAPTER CHECK</span><h2>章节检测</h2><p>专注检查单章掌握程度，及时发现知识盲区。</p></section><section class="panel feature-panel"><div class="feature-symbol">▤</div><h3>选择检测范围</h3><p class="panel-copy">每次检测均包含概念理解与实际应用题。</p><label class="field-label" for="chapter">目标章节</label><select id="chapter" class="select">${chapterOptions}</select><div class="dual-fields"><div><label class="field-label" for="chapterCount">题目数量</label><select id="chapterCount" class="select"><option value="10">10题</option><option value="20" selected>20题</option><option value="all">全部内容</option></select></div><div><label class="field-label" for="chapterDiff">题目难度</label><select id="chapterDiff" class="select"><option>混合难度</option><option>基础</option><option>理解</option><option>应用</option></select></div></div><button class="btn full primary-action" id="chapterBtn">开始章节检测 <span>→</span></button></section><section class="tip-panel"><strong>检测建议</strong><div><span>01</span><p>学完一章后立即检测，确认核心概念。</p></div><div><span>02</span><p>优先复习结果页中的错题解析。</p></div><div><span>03</span><p>隔天再次检测，检查是否真正掌握。</p></div></section>`,
      overall:`<section class="tab-intro"><span class="eyebrow">RANDOM TEST</span><h2>整体测试</h2><p>跨越全部十章随机抽题，检验综合知识水平。</p></section><section class="panel feature-panel overall-panel"><div class="feature-symbol">◎</div><h3>全书随机测试</h3><p class="panel-copy">覆盖不同章节与题型，每次都会生成新的题目组合。</p><div class="dual-fields"><div><label class="field-label" for="randomCount">题目数量</label><select id="randomCount" class="select"><option>10</option><option selected>20</option><option>30</option></select></div><div><label class="field-label" for="randomDiff">题目难度</label><select id="randomDiff" class="select"><option>混合难度</option><option>基础</option><option>理解</option><option>应用</option></select></div></div><button class="btn full primary-action" id="randomBtn">开始整体测试 <span>→</span></button></section><section class="accuracy-card"><div class="ring-value">${accuracy}%</div><div><strong>历史答题正确率</strong><p>累计作答 ${attempts} 次，答对 ${correct} 次。</p></div></section>`,
      exam:`<section class="tab-intro"><span class="eyebrow">MOCK EXAM</span><h2>模拟考试</h2><p>在限时环境中完成系统性检验，建立真实考试节奏。</p></section><section class="exam-hero"><span class="exam-label">PYTORCH · 十章综合</span><div class="exam-number">50<small>题</small></div><h3>全真模拟考试</h3><p>每章均衡抽取 5 题，交卷后生成成绩、章节表现与完整错题解析。</p><div class="exam-facts"><span><strong>35</strong> 分钟</span><span><strong>100</strong> 满分</span><span><strong>10</strong> 章节</span></div><button class="btn full exam-action" id="examBtn">开始模拟考试</button>${localStorage.getItem(LS.exam)?'<button class="resume-action" id="resumeBtn">继续未完成的考试 →</button>':''}</section><section class="notice-card"><strong>考试说明</strong><p>考试过程自动保存，可标记复查、打开答题卡或中途退出后继续。</p></section>`,
      about:`<section class="about-hero"><div class="about-logo-image"><img src="assets/torchgo-logo.png" alt="TorchGo Logo"></div><h2>TorchGo·火炬学</h2><span class="version-chip">V1.0</span><p>学习 · 检测 · 巩固 · 提升</p></section><section class="panel about-panel"><div class="about-section"><span>软件简介</span><p>TorchGo·火炬学是一款面向 PyTorch 与计算机视觉学习者的离线学习检测工具。内置十章完整知识体系，通过知识卡片、应用题、章节检测、整体测试和模拟考试，帮助学习者系统掌握并持续巩固核心知识。</p></div><div class="about-section"><span>版本信息</span><div class="info-row"><span>当前版本</span><strong>V1.0</strong></div><div class="info-row"><span>开发者</span><strong>王利群</strong></div><div class="info-row"><span>开源许可</span><strong>MIT License</strong></div><div class="info-row"><span>联系邮箱</span><a href="mailto:lntano021114@gmail.com">lntano021114@gmail.com</a></div></div><div class="privacy-note"><span>✓</span><p>软件完全离线运行，学习记录仅保存在本机。</p></div></section><p class="copyright">Copyright © 2026 王利群.<br>Released under the MIT License.</p>`
    };
    app.innerHTML=`<div class="page home-page"><header class="app-header"><div class="brand-logo"><img src="assets/torchgo-logo.png" alt="TorchGo Logo"></div><div class="brand-copy"><span>TORCHGO LEARNING</span><h1>TorchGo·火炬学</h1></div><button class="history-pill" id="historyBtn">成绩</button></header><div class="tab-stage">${contents[tab]||contents.study}</div>${bottomNavigation(tab)}</div>`;
    window.scrollTo(0,0);
    document.querySelectorAll('[data-home-tab]').forEach(b=>b.onclick=()=>home(b.dataset.homeTab));
    document.querySelectorAll('[data-collection]').forEach(b=>b.onclick=()=>showCollection(b.dataset.collection));
    const on=(id,fn)=>{const el=document.getElementById(id);if(el)el.onclick=fn};
    on('studyBtn',()=>startStudy(false));on('resumeStudyBtn',resumeStudy);on('browseBtn',showBank);on('dueBtn',()=>startStudy(true));on('chapterBtn',startChapter);on('randomBtn',startRandom);on('examBtn',startExam);on('historyBtn',showHistory);on('resumeBtn',resumeExam);
    enhanceSelects();
  }

  function showBank(){
    state.screen='bank';state.returnTab='study';
    const selected=document.getElementById('studyChapter')?.value||'0';
    const initial=selected==='all'?'0':selected;
    app.innerHTML=`<div class="page"><div class="topbar"><button class="btn ghost" id="bankBack">首页</button><span class="title">完整章节题库</span><span class="muted" id="bankCount"></span></div>
      <section class="card bank-controls"><select id="bankChapter" class="select">${D.chapters.map((c,i)=>`<option value="${i}" ${String(i)===initial?'selected':''}>${esc(c)}</option>`).join('')}</select><select id="bankType" class="select"><option>全部内容</option><option>知识卡片</option><option>应用题</option></select><input id="bankSearch" class="search" placeholder="搜索名词、题干、答案或解析"></section><div id="bankRows"></div></div>`;
    document.getElementById('bankBack').onclick=()=>home('study');
    ['bankChapter','bankType'].forEach(id=>document.getElementById(id).onchange=renderBankRows);
    document.getElementById('bankSearch').oninput=renderBankRows;
    enhanceSelects();renderBankRows();
  }
  function renderBankRows(){
    const chapter=D.chapters[Number(document.getElementById('bankChapter').value)],type=document.getElementById('bankType').value,query=document.getElementById('bankSearch').value.trim().toLowerCase();
    const all=completeStudyItems(chapter);let rows=all;
    if(type==='知识卡片')rows=rows.filter(x=>x.kind==='knowledge');else if(type==='应用题')rows=rows.filter(x=>x.kind==='question');
    if(query)rows=rows.filter(x=>`${x.title} ${x.description} ${x.tip}`.toLowerCase().includes(query));
    const kc=all.filter(x=>x.kind==='knowledge').length,qc=all.length-kc;document.getElementById('bankCount').textContent=`${kc}卡 + ${qc}题`;
    document.getElementById('bankRows').innerHTML=rows.length?rows.map((x,i)=>{const opts=x.kind==='question'?`<div class="bank-options">${x.source.options.map((o,j)=>`${'ABCD'[j]}. ${esc(o)}`).join('<br>')}</div>`:'';return`<details class="bank-item"><summary><span>${i+1}. [${x.kind==='knowledge'?'知识卡片':'应用题'}]</span>${esc(x.title)}</summary>${opts}<strong>${esc(x.description)}</strong><p>解析：${esc(x.tip)}</p></details>`}).join(''):'<section class="card"><p>没有匹配的内容。</p></section>';
  }

  function showCollection(mode){
    const config={
      knowledge:{title:'全部知识卡片',icon:'卡',description:'浏览十章中的全部概念、解释和补充理解。'},
      applied:{title:'全部应用题',icon:'题',description:'浏览全部应用题、选项、正确答案和解析。'},
      mastered:{title:'已掌握内容',icon:'✓',description:'这里汇总你在学习模式中标记为“已掌握”的内容。'},
      due:{title:'今日待复习',icon:'复',description:'这里显示复习日期已经到期、今天需要再次巩固的内容。'}
    }[mode]||null;
    if(!config){home('study');return}
    state.screen='collection';state.returnTab='study';state.collectionMode=mode;
    const chapterOptions=['<option value="all">全部章节</option>',...D.chapters.map((c,i)=>`<option value="${i}">${esc(c)}</option>`)].join('');
    app.innerHTML=`<div class="page collection-page"><div class="topbar"><button class="btn ghost" id="collectionBack">← 学习</button><span class="title">${esc(config.title)}</span><span class="muted" id="collectionCount"></span></div><section class="collection-hero"><span>${config.icon}</span><div><h2>${esc(config.title)}</h2><p>${esc(config.description)}</p></div></section><section class="card collection-controls"><select id="collectionChapter" class="select">${chapterOptions}</select><input id="collectionSearch" class="search" placeholder="搜索名词、题干、答案或解析"></section><div id="collectionRows"></div></div>`;
    document.getElementById('collectionBack').onclick=()=>home('study');
    document.getElementById('collectionChapter').onchange=renderCollectionRows;
    document.getElementById('collectionSearch').oninput=renderCollectionRows;
    enhanceSelects();window.scrollTo(0,0);renderCollectionRows();
  }

  function renderCollectionRows(){
    const mode=state.collectionMode,progress=studyProgress(),today=localDate(),chapterValue=document.getElementById('collectionChapter').value,query=document.getElementById('collectionSearch').value.trim().toLowerCase();
    let rows=completeStudyItems();
    if(mode==='knowledge')rows=rows.filter(x=>x.kind==='knowledge');
    else if(mode==='applied')rows=rows.filter(x=>x.kind==='question');
    else if(mode==='mastered')rows=rows.filter(x=>progress[x.key]?.status==='mastered');
    else if(mode==='due')rows=rows.filter(x=>progress[x.key]&&(progress[x.key].dueDate||'9999')<=today);
    if(chapterValue!=='all'){const chapter=D.chapters[Number(chapterValue)];rows=rows.filter(x=>x.chapter===chapter)}
    if(query)rows=rows.filter(x=>`${x.title} ${x.description} ${x.tip} ${x.kind==='question'?x.source.options.join(' '):''}`.toLowerCase().includes(query));
    document.getElementById('collectionCount').textContent=`${rows.length} 项`;
    const emptyText=mode==='mastered'?'还没有已掌握的内容。完成学习并选择“已掌握”后，会自动出现在这里。':mode==='due'?'今天没有到期的复习内容，可以继续学习新内容。':'没有匹配的内容，请更换章节或搜索词。';
    document.getElementById('collectionRows').innerHTML=rows.length?rows.map((x,i)=>{
      const opts=x.kind==='question'?`<div class="bank-options">${x.source.options.map((o,j)=>`${'ABCD'[j]}. ${esc(o)}`).join('<br>')}</div>`:'';
      const record=progress[x.key],status=record?`<small class="record-status">${record.status==='mastered'?'已掌握':record.status==='fuzzy'?'有点模糊':'需要重学'}${record.dueDate?` · 复习日 ${esc(record.dueDate)}`:''}</small>`:'';
      return `<details class="bank-item collection-item"><summary><span>${i+1}. ${esc(shortChapter(x.chapter))} · ${x.kind==='knowledge'?'知识卡片':'应用题'}</span>${esc(x.title)}${status}</summary>${opts}<strong>${esc(x.description)}</strong><p>解析：${esc(x.tip)}</p></details>`;
    }).join(''):`<section class="empty-state"><span>○</span><h3>这里暂时是空的</h3><p>${esc(emptyText)}</p></section>`;
  }

  function startStudy(dueOnly){
    const chapterValue=document.getElementById('studyChapter').value,chapter=chapterValue==='all'?'全部章节':D.chapters[Number(chapterValue)], sp=studyProgress(), today=localDate();
    const pending=learningSession();if(!dueOnly&&pending&&String(pending.scope||'all')===chapterValue){resumeStudy();return}
    let cards=completeStudyItems(chapter==='全部章节'?null:chapter);
    if(dueOnly) cards=cards.filter(k=>sp[k.key]&&(sp[k.key].dueDate||'9999')<=today);
    if(!cards.length){toast('当前范围没有到期内容');return}
    cards=shuffle(cards).sort((a,b)=>{const pa=sp[a.key],pb=sp[b.key];const ra=pa&&pa.dueDate<=today?0:pa?2:1,rb=pb&&pb.dueDate<=today?0:pb?2:1;return ra-rb});
    state.screen='study';state.returnTab='study';state.study=cards;state.studyPos=0;state.studyScope=dueOnly?'due':chapterValue;state.revealed=false;state.studySelected=null;state.title=dueOnly?'今日到期复习':chapter;renderStudy();
  }
  function renderStudy(){
    const k=state.study[state.studyPos],pct=(state.studyPos+1)/state.study.length*100;
    const isQuestion=k.kind==='question',selected=state.studySelected,answered=isQuestion&&selected!==null,correctIndex=isQuestion?k.source.correct_index:-1;
    const options=isQuestion?`<div class="study-options interactive">${k.source.options.map((o,i)=>{
      const resultClass=answered?(i===correctIndex?' correct':i===selected?' wrong':''):'';
      return `<button class="study-option${resultClass}" data-study-option="${i}" ${answered?'disabled':''}><span>${'ABCD'[i]}.</span><span>${esc(o)}</span></button>`;
    }).join('')}</div>`:'';
    const answerArea=isQuestion
      ?(answered?`<div class="study-feedback ${selected===correctIndex?'correct':'wrong'}"><strong>${selected===correctIndex?'回答正确':'回答错误'}</strong><p>正确答案：${'ABCD'[correctIndex]}. ${esc(k.source.options[correctIndex])}</p><p>解析：${esc(k.tip)}</p></div><div class="grade-row"><button class="btn green" data-grade="mastered">已掌握</button><button class="btn amber" data-grade="fuzzy">有点模糊</button><button class="btn red" data-grade="unknown">需要重学</button></div>`:`<p class="study-hint">请选择一个选项，作答后立即显示正确答案和解析。</p>`)
      :`<button class="btn ${state.revealed?'hidden':''}" id="reveal">查看答案与解析</button><div id="answer" class="${state.revealed?'':'hidden'}"><div class="explanation"><strong>${esc(k.description)}</strong><p>补充理解：${esc(k.tip)}</p></div><div class="grade-row"><button class="btn green" data-grade="mastered">已掌握</button><button class="btn amber" data-grade="fuzzy">有点模糊</button><button class="btn red" data-grade="unknown">完全不会</button></div></div>`;
    app.innerHTML=`<div class="page"><div class="topbar"><button class="btn ghost" id="back">首页</button><span class="title">完整题库学习</span><span class="muted">${state.studyPos+1}/${state.study.length}</span></div><div class="progress"><div style="width:${pct}%"></div></div>
      <section class="quiz-card"><span class="badge">${esc(shortChapter(k.chapter))} · ${k.kind==='knowledge'?'知识卡片':'应用题'}</span><p class="muted" style="margin-top:24px">${k.kind==='knowledge'?'先尝试在脑中解释这个名词：':'先独立完成这道题：'}</p><div class="learn-term ${k.kind==='question'?'question-term':''}">${esc(k.title)}</div>${options}
      ${answerArea}</section>
      <div class="nav"><span class="muted">按1、3、7、14、30、60天安排复习</span><span class="spacer"></span><button class="small-link" id="skip">跳过 →</button></div></div>`;
    saveLearningSession();
    document.getElementById('back').onclick=()=>{saveLearningSession();home('study')};document.getElementById('skip').onclick=nextStudy;
    document.querySelectorAll('[data-study-option]').forEach(b=>b.onclick=()=>answerStudyQuestion(Number(b.dataset.studyOption)));
    const reveal=document.getElementById('reveal');if(reveal)reveal.onclick=e=>{state.revealed=true;e.target.classList.add('hidden');document.getElementById('answer').classList.remove('hidden');saveLearningSession()};
    document.querySelectorAll('[data-grade]').forEach(b=>b.onclick=()=>gradeStudy(b.dataset.grade));
  }
  function answerStudyQuestion(index){if(state.studySelected!==null)return;state.studySelected=index;saveLearningSession();renderStudy()}
  function gradeStudy(status){
    const k=state.study[state.studyPos],sp=studyProgress(),old=sp[k.key]||{},oldStreak=old.streak||0;
    let streak,days;if(status==='mastered'){streak=oldStreak+1;days=[1,3,7,14,30,60][Math.min(streak-1,5)]}else if(status==='fuzzy'){streak=Math.max(0,oldStreak-1);days=1}else{streak=0;days=0}
    sp[k.key]={status,streak,reviews:(old.reviews||0)+1,dueDate:localDate(days),chapter:k.chapter,reviewedAt:new Date().toISOString()};save(LS.study,sp);nextStudy();
  }
  function nextStudy(){state.studySelected=null;state.revealed=false;if(++state.studyPos>=state.study.length){localStorage.removeItem(LS.learning);state.study=[];state.screen='home';toast('本轮学习完成');home('study')}else{saveLearningSession();renderStudy()}}

  function knowledgeQuestion(k){
    const dir=Math.random()<.5?'term_to_desc':'desc_to_term',pool=shuffle(D.knowledge.filter(x=>chapterOf(x)===chapterOf(k)&&x[0]!==k[0])).slice(0,3);
    const correct=dir==='term_to_desc'?k[2]:k[0],options=shuffle([correct,...pool.map(x=>dir==='term_to_desc'?x[2]:x[0])]);
    return{id:`${k[0]}::${dir}`,chapter:chapterOf(k),type:'术语题',difficulty:'基础',prompt:dir==='term_to_desc'?`以下哪一项最准确地描述了“${k[0]}”？`:`“${k[2]}”指的是哪个名词？`,options,correct:options.indexOf(correct),selected:null,marked:false,explanation:`${k[0]}：${k[2]}。${k[3]}`};
  }
  function appliedQuestion(q){const correct=q.options[q.correct_index],options=shuffle(q.options);return{id:`applied::${q.id}`,chapter:q.chapter,type:q.type,difficulty:q.difficulty,prompt:q.prompt,options,correct:options.indexOf(correct),selected:null,marked:false,explanation:q.explanation}}
  function mixed(chapter,count,diff,all=false){
    const kp=D.knowledge.filter(k=>!chapter||chapterOf(k)===chapter),ap0=D.applied.filter(q=>(!chapter||q.chapter===chapter)),ap=diff==='混合难度'?ap0:(ap0.filter(q=>q.difficulty===diff).length?ap0.filter(q=>q.difficulty===diff):ap0);
    if(all)return shuffle([...kp.map(knowledgeQuestion),...ap.map(appliedQuestion)]);
    const an=Math.min(ap.length,Math.max(1,Math.floor(count/(diff==='混合难度'?3:2)))),kn=Math.min(kp.length,count-an);
    return shuffle([...sample(kp,kn).map(knowledgeQuestion),...sample(ap,an).map(appliedQuestion)]);
  }
  function startChapter(){state.returnTab='chapter';const c=D.chapters[Number(document.getElementById('chapter').value)],n=document.getElementById('chapterCount').value,d=document.getElementById('chapterDiff').value;startQuiz(mixed(c,n==='all'?0:Number(n),d,n==='all'),`${c} · 章节测试`,false)}
  function startRandom(){state.returnTab='overall';const n=Number(document.getElementById('randomCount').value),d=document.getElementById('randomDiff').value;startQuiz(mixed(null,n,d),`全书随机测试`,false)}
  function startExam(){state.returnTab='exam';let qs=[];D.chapters.forEach(c=>{qs.push(...sample(D.knowledge.filter(k=>chapterOf(k)===c),3).map(knowledgeQuestion));qs.push(...sample(D.applied.filter(q=>q.chapter===c),2).map(appliedQuestion))});startQuiz(shuffle(qs),'50题模拟考试',true,35*60)}
  function startQuiz(qs,title,timed,timeLeft=0){stopTimer();state={...state,screen:'quiz',session:qs,pos:0,title,timed,timeLeft};renderQuiz();if(timed){saveExam();state.timer=setInterval(tick,1000)}}
  function renderQuiz(){
    const q=state.session[state.pos],answered=state.session.filter(x=>x.selected!==null).length,pct=(state.pos+1)/state.session.length*100;
    app.innerHTML=`<div class="page"><div class="topbar"><button class="btn ghost" id="exit">退出</button><span class="title">${esc(state.title)}</span><button class="small-link" id="sheet">答题卡</button><span class="timer" id="timer">${state.timed?formatTime(state.timeLeft):''}</span></div><div class="progress"><div style="width:${pct}%"></div></div>
      <section class="quiz-card"><div style="display:flex;justify-content:space-between;gap:8px"><span class="badge">${esc(shortChapter(q.chapter))} · ${esc(q.type)} · ${esc(q.difficulty)}</span><span class="muted">${state.pos+1}/${state.session.length}</span></div><div class="question">${esc(q.prompt)}</div>${q.options.map((o,i)=>`<button class="option ${q.selected===i?'selected':''}" data-option="${i}">${'ABCD'[i]}. ${esc(o)}</button>`).join('')}</section>
      <div class="nav"><button class="btn gray" id="prev" ${state.pos===0?'disabled':''}>← 上一题</button><span class="muted">已答 ${answered}</span><button class="small-link" id="mark">${q.marked?'取消标记':'标记复查'}</button><span class="spacer"></span><button class="btn" id="next">${state.pos===state.session.length-1?'交卷':'下一题 →'}</button></div></div>`;
    document.querySelectorAll('[data-option]').forEach(b=>b.onclick=()=>{q.selected=Number(b.dataset.option);if(state.timed)saveExam();renderQuiz()});
    document.getElementById('prev').onclick=()=>{if(state.pos>0){state.pos--;renderQuiz()}};
    document.getElementById('next').onclick=nextQuiz;document.getElementById('mark').onclick=()=>{q.marked=!q.marked;if(state.timed)saveExam();renderQuiz()};document.getElementById('sheet').onclick=showSheet;
    document.getElementById('exit').onclick=()=>{if(confirm(state.timed?'退出后可以从首页恢复考试。确定退出吗？':'当前答案不会保存，确定退出吗？')){if(state.timed)saveExam();home()}};
  }
  function nextQuiz(){if(state.pos<state.session.length-1){state.pos++;if(state.timed)saveExam();renderQuiz();return}const u=state.session.filter(x=>x.selected===null).length;if(u&&!confirm(`还有 ${u} 题未作答，仍然交卷吗？`))return;finishQuiz()}
  function showSheet(){modal.classList.remove('hidden');modal.innerHTML=`<div class="modal-box"><h2>答题卡</h2><p class="muted">蓝色已答 · 黄色标记 · 灰色未答</p><div class="answer-grid">${state.session.map((q,i)=>`<button class="num ${q.marked?'marked':q.selected!==null?'done':''}" data-jump="${i}">${i+1}</button>`).join('')}</div><button class="btn ghost full" id="closeModal">关闭</button></div>`;document.querySelectorAll('[data-jump]').forEach(b=>b.onclick=()=>{state.pos=Number(b.dataset.jump);closeModal();renderQuiz()});document.getElementById('closeModal').onclick=closeModal}
  function closeModal(){modal.classList.add('hidden');modal.innerHTML=''}
  function formatTime(s){const m=Math.floor(Math.max(s,0)/60),x=Math.max(s,0)%60;return `${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`}
  function tick(){if(--state.timeLeft<=0){state.timeLeft=0;saveExam();stopTimer();toast('时间到，自动交卷');setTimeout(finishQuiz,500)}else{const t=document.getElementById('timer');if(t)t.textContent=formatTime(state.timeLeft);if(state.timeLeft%10===0)saveExam()}}
  function saveExam(){save(LS.exam,{session:state.session,pos:state.pos,title:state.title,timeLeft:state.timeLeft})}
  function resumeExam(){const x=load(LS.exam,null);if(!x||!x.session){toast('没有可恢复的考试');return}state.returnTab='exam';startQuiz(x.session,x.title||'50题模拟考试',true,x.timeLeft||1);state.pos=Math.min(x.pos||0,state.session.length-1);renderQuiz()}

  function finishQuiz(){
    stopTimer();const tp=load(LS.progress,{});state.session.forEach(q=>{const ok=q.selected===q.correct,r=tp[q.id]||{attempts:0,correct:0,wrong:0};r.attempts++;r.correct+=ok?1:0;r.wrong+=ok?0:1;r.last=new Date().toISOString();tp[q.id]=r});save(LS.progress,tp);localStorage.removeItem(LS.exam);
    const correct=state.session.filter(q=>q.selected===q.correct).length,total=state.session.length,score=Math.round(correct/total*100),hist=load(LS.history,[]);hist.push({time:new Date().toISOString(),title:state.title,score,correct,total});save(LS.history,hist.slice(-100));renderResult(score,correct,total);
  }
  function renderResult(score,correct,total){
    state.screen='result';
    const color=score>=90?'green':score>=80?'blue':score>=60?'amber':'red',wrong=state.session.filter(q=>q.selected!==q.correct);
    app.innerHTML=`<div class="page"><div class="header"><div><h1>测试结果</h1><p>${esc(state.title)}</p></div><button class="btn" id="home">返回首页</button></div><section class="card result-summary"><div class="score ${color}">${score}<span style="font-size:18px">分</span></div><div><strong>${score>=90?'优秀，掌握扎实':score>=80?'良好，继续补齐薄弱点':score>=60?'及格，建议按章强化':'需要巩固，先复习错题'}</strong><p class="muted">答对 ${correct} · 答错 ${total-correct} · 共 ${total} 题</p></div></section>
      <div class="grid" style="margin-top:13px"><section class="card"><h2>章节得分</h2>${D.chapters.map(c=>{const x=state.session.filter(q=>q.chapter===c);if(!x.length)return'';const n=x.filter(q=>q.selected===q.correct).length;return`<div class="chapter-score"><span>${esc(shortChapter(c))}</span><strong>${n}/${x.length} · ${Math.round(n/x.length*100)}%</strong></div>`}).join('')}</section><section class="card"><h2>错题解析</h2>${wrong.length?wrong.map((q,i)=>`<div class="wrong"><strong>${i+1}. ${esc(q.prompt)}</strong><br>你的答案：${q.selected===null?'未作答':esc(q.options[q.selected])}<br>正确答案：${esc(q.options[q.correct])}<br>解析：${esc(q.explanation)}</div>`).join(''):'<p>全部正确，没有错题。</p>'}</section></div></div>`;document.getElementById('home').onclick=()=>home(state.returnTab||'study');
  }
  function showHistory(){const h=load(LS.history,[]);modal.classList.remove('hidden');modal.innerHTML=`<div class="modal-box"><h2>成绩历史</h2>${h.length?h.slice().reverse().map(x=>`<div class="history-item"><strong>${esc(x.title)} · ${x.score}分</strong><span class="muted">${new Date(x.time).toLocaleString()} · ${x.correct}/${x.total}题</span></div>`).join(''):'<p class="muted">还没有完成过测试。</p>'}<button class="btn ghost full" id="closeModal">关闭</button></div>`;document.getElementById('closeModal').onclick=closeModal}
  home();setupNativeBack();setupLaunchScreen();
})();

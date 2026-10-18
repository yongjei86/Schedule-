(()=>{'use strict';
const $=id=>document.getElementById(id),catalog=window.DRESSUP_ASSETS,labels={outfit:'옷',head:'머리 장식',hand:'손 소품'},slots={outfit:{x:50,y:81,w:48,h:35,rx:35,ry:29},head:{x:50,y:18,w:67,h:28,rx:43,ry:28},hand:{x:78,y:74,w:27,h:28,rx:34,ry:32}};
let character=catalog[0],category='outfit',page=0,drag=null,muted=false,toastTimer,saveTimer,restoring=false;
let spriteSerial=0;let state={};try{state=JSON.parse(localStorage.getItem('hyeon-dressup-v1')||'{}');if(!state||typeof state!=='object'||Array.isArray(state))state={};}catch(_){}
const audio=document.createElement('audio');audio.preload='auto';audio.setAttribute('playsinline','');audio.src='/static/dressup/chime.wav';document.body.append(audio);let audioContext;
function unlock(){try{audioContext=audioContext||new(window.AudioContext||window.webkitAudioContext)();if(audioContext.state==='suspended')audioContext.resume();}catch(_){} }
function sound(final=false){if(muted)return;try{audio.currentTime=0;const p=audio.play();if(p)p.catch(()=>synth(final));}catch(_){synth(final);}}
function synth(final){try{if(!audioContext)return;[523.25,659.25,783.99,...(final?[1046.5]:[])].forEach((f,i)=>{const o=audioContext.createOscillator(),g=audioContext.createGain(),t=audioContext.currentTime+i*.11;o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.15,t+.02);g.gain.exponentialRampToValueAtTime(.0001,t+.28);o.connect(g);g.connect(audioContext.destination);o.start(t);o.stop(t+.3);});}catch(_){}}
function toast(text){clearTimeout(toastTimer);$('toast').textContent=text;$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,2200);}
function save(){try{localStorage.setItem('hyeon-dressup-v1',JSON.stringify(state));$('save-status').textContent='✓ 지금 모습이 저장됐어요';}catch(_){$('save-status').textContent='이 화면에서는 계속 놀 수 있어요';}clearTimeout(saveTimer);saveTimer=setTimeout(()=>$('save-status').textContent='다시 와도 이어서 놀아요',2500);}
function current(){if(!state[character.id]||typeof state[character.id]!=='object')state[character.id]={};return state[character.id];}
function sprite(c,index){const a=c.sprites[index],svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',a.box.join(' '));svg.setAttribute('class','sprite');svg.setAttribute('aria-hidden','true');const im=document.createElementNS(svg.namespaceURI,'image');im.setAttribute('href',c.src);im.setAttribute('width',c.width);im.setAttribute('height',c.height);{const defs=document.createElementNS(svg.namespaceURI,'defs'),clip=document.createElementNS(svg.namespaceURI,'clipPath'),polygon=document.createElementNS(svg.namespaceURI,'polygon'),id='doll-clip-'+(++spriteSerial);clip.id=id;clip.setAttribute('clipPathUnits','userSpaceOnUse');const [x,y,b,h]=a.box;polygon.setAttribute('points',a.clip||`${x},${y} ${x+b},${y} ${x+b},${y+h} ${x},${y+h}`);clip.append(polygon);defs.append(clip);svg.append(defs);im.setAttribute('clip-path','url(#'+id+')');}svg.append(im);return svg;}
function celebration(kind,all=false){const s=$('sparkles');s.replaceChildren();for(let i=0;i<(all?16:7);i++){const n=document.createElement('i');n.textContent=['✨','⭐','💛','🌸'][i%4];n.style.left=(all?10+Math.random()*80:(slots[kind]?.x||50)-15+Math.random()*30)+'%';n.style.top=(all?15+Math.random()*70:(slots[kind]?.y||60)-10+Math.random()*20)+'%';n.style.animationDelay=(Math.random()*.15)+'s';s.append(n);}setTimeout(()=>s.replaceChildren(),1250);}
function layout(c,kind,index){return {...slots[kind],...(c.slots?.[kind]||{}),...(c.sprites[index]?.fit||{})};}
function fitLayer(n,kind,index,c=character){const q=layout(c,kind,index);n.style.left=(q.x-q.w/2)+'%';n.style.top=(q.y-q.h/2)+'%';n.style.width=q.w+'%';n.style.height=q.h+'%';}
function renderWorn(){const w=$('worn');w.replaceChildren();for(const kind of ['outfit','head','hand']){const index=current()[kind];if(!Number.isInteger(index)||character.sprites[index]?.kind!==kind){delete current()[kind];continue;}const n=document.createElement('div');n.className='layer '+kind;n.dataset.index=index;n.setAttribute('role','button');n.setAttribute('tabindex','0');n.setAttribute('aria-label','입은 '+character.sprites[index].name+' 벗기기');fitLayer(n,kind,index);n.append(sprite(character,index));n.onpointerdown=e=>startDrag(e,index,n,true);n.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();delete current()[kind];renderWorn();renderItems();save();toast('옷장에 넣었어요');}};w.append(n);}}
function renderItems(){const list=character.sprites.map((s,i)=>({...s,i})).filter(s=>s.kind===category),pages=Math.max(1,Math.ceil(list.length/4));page=Math.min(page,pages-1);$('items').replaceChildren();list.slice(page*4,page*4+4).forEach(a=>{const b=document.createElement('button');b.type='button';b.className='item';b.dataset.index=a.i;b.setAttribute('aria-label',a.name+' 끌어 입히기');b.setAttribute('aria-pressed',current()[category]===a.i?'true':'false');const preview=document.createElement('div');preview.className='preview';preview.append(sprite(character,a.i));const caption=document.createElement('span');caption.textContent=a.name;b.append(preview,caption);b.onpointerdown=e=>startDrag(e,a.i,b,false);b.onclick=e=>{if(e.detail===0)equip(a.i);};$('items').append(b);});$('page-count').textContent=labels[category]+' '+list.length+'개';$('prev').disabled=page===0;$('next').disabled=page===pages-1;}
function choose(c){cancelDrag();$('resident-modal').hidden=true;character=c;page=0;$('name').textContent=c.name;$('base').replaceChildren(sprite(c,0));$('doll').style.setProperty('--color',c.color);$('hint').textContent='옷을 끌어서 몸 가까이에 놓아봐요';renderWorn();renderItems();document.querySelectorAll('.character').forEach(n=>n.setAttribute('aria-pressed',String(n.dataset.id===c.id)));}
function equip(index){const a=character.sprites[index];if(!a||!slots[a.kind])return;current()[a.kind]=index;renderWorn();renderItems();save();sound();celebration(a.kind);$('hint').textContent='잘 어울려요! 다른 것도 꾸며볼까요?';}
function normalized(x,y){const r=$('doll').getBoundingClientRect();return{x:(x-r.left)/r.width*100,y:(y-r.top)/r.height*100};}
function isNear(x,y,kind){const p=normalized(x,y),q={...slots[kind],...(character.slots?.[kind]||{})};return ((p.x-q.x)/q.rx)**2+((p.y-q.y)/q.ry)**2<=1;}
function inCloset(x,y){const r=$('return').getBoundingClientRect(),w=document.querySelector('.wardrobe').getBoundingClientRect();return x>=w.left&&x<=w.right&&y>=w.top&&y<=w.bottom;}
function startDrag(e,index,source,worn){if(drag||e.button!==0)return;e.preventDefault();unlock();const a=character.sprites[index],r=$('doll').getBoundingClientRect(),q=layout(character,a.kind,index),ghost=document.createElement('div');ghost.className='drag-ghost';ghost.style.width=r.width*q.w/100+'px';ghost.style.height=r.height*q.h/100+'px';ghost.append(sprite(character,index));document.body.append(ghost);drag={id:e.pointerId,index,kind:a.kind,source,worn,ghost,startX:e.clientX,startY:e.clientY,moved:false};source.classList.add('dragging-source');try{source.setPointerCapture(e.pointerId);}catch(_){}$('target').hidden=false;fitLayer($('target'),a.kind,index);moveDrag(e);}
function moveDrag(e){if(!drag||e.pointerId!==drag.id)return;e.preventDefault();if(Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)>7)drag.moved=true;drag.ghost.style.left=e.clientX+'px';drag.ghost.style.top=(e.clientY-12)+'px';$('target').classList.toggle('near',isNear(e.clientX,e.clientY,drag.kind));$('return').classList.toggle('active',drag.worn&&inCloset(e.clientX,e.clientY));}
function cancelDrag(){if(!drag)return;drag.source.classList.remove('dragging-source');try{drag.source.releasePointerCapture(drag.id);}catch(_){}drag.ghost.remove();drag=null;$('target').hidden=true;$('return').classList.remove('active');}
function endDrag(e){if(!drag||e.pointerId!==drag.id)return;e.preventDefault();const d=drag,near=isNear(e.clientX,e.clientY,d.kind),returned=d.worn&&inCloset(e.clientX,e.clientY);if(near){cancelDrag();equip(d.index);}else if(returned){cancelDrag();delete current()[d.kind];renderWorn();renderItems();save();toast('옷장에 넣었어요');}else{const r=d.source.getBoundingClientRect();d.ghost.style.transition='left .2s,top .2s,opacity .2s';d.ghost.style.left=(r.left+r.width/2)+'px';d.ghost.style.top=(r.top+r.height/2)+'px';d.ghost.style.opacity='0';$('target').hidden=true;setTimeout(()=>{if(drag===d)cancelDrag();},210);$('hint').textContent=d.worn?'옷장으로 끌면 벗길 수 있어요':'빛나는 곳 가까이에 놓아봐요';}}
document.addEventListener('pointermove',moveDrag,{passive:false});document.addEventListener('pointerup',endDrag,{passive:false});document.addEventListener('pointercancel',cancelDrag);window.addEventListener('blur',cancelDrag);window.addEventListener('resize',cancelDrag);document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelDrag();audio.pause();}});document.addEventListener('dragstart',e=>e.preventDefault());
for(const c of catalog){const b=document.createElement('button');b.className='character';b.dataset.id=c.id;b.setAttribute('aria-label',c.name+' 선택');b.setAttribute('aria-pressed','false');const p=document.createElement('div');p.className='portrait';p.append(sprite(c,0));const name=document.createElement('span');name.textContent=c.name;b.append(p,name);b.onclick=()=>{unlock();choose(c);};$('characters').append(b);const im=new Image();im.onerror=()=>toast('그림을 불러오지 못했어요. 새로고침해 주세요.');im.src=c.src;}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{cancelDrag();category=b.dataset.tab;page=0;document.querySelectorAll('[data-tab]').forEach(n=>n.setAttribute('aria-selected',String(n===b)));renderItems();});$('prev').onclick=()=>{cancelDrag();page--;renderItems();};$('next').onclick=()=>{cancelDrag();page++;renderItems();};$('reset').onclick=()=>{cancelDrag();state[character.id]={};renderWorn();renderItems();save();$('hint').textContent='새로운 옷을 골라볼까요?';};$('finish').onclick=()=>{unlock();if(!Object.keys(current()).length){toast('먼저 옷이나 장식을 입혀봐요 🎀');return;}save();sound(true);celebration('outfit',true);toast('✨ '+character.name+' 꾸미기 완성!');};$('sound').onclick=()=>{muted=!muted;$('sound').textContent=muted?'🔇':'🔊';$('sound').setAttribute('aria-label',muted?'소리 켜기':'소리 끄기');$('sound').setAttribute('aria-pressed',String(!muted));if(!muted){unlock();sound();}};document.querySelector('.credit').onclick=e=>{e.preventDefault();$('sources').hidden=false;};$('close-sources').onclick=()=>$('sources').hidden=true;document.addEventListener('keydown',e=>{if(e.key==='Escape'){cancelDrag();$('sources').hidden=true;$('resident-modal').hidden=true;}});choose(character);

let walkFrame=null,walkTime=0;const walkTargets=new WeakMap();
const VILLAGE_KEY='hyeon-village-v1';let residents=[],sending=false,selectedResident=null;
const positions=[[22,63],[42,61],[63,62],[81,64],[12,82],[31,83],[52,84],[72,84],[88,85],[39,97],[63,97]],sayings=['혜온아, 안녕!','꽃밭에 놀러 왔어요 🌸','친구랑 산책해요','오늘 옷이 마음에 들어요!','우리 집에 놀러 와요 🏡'];
function cleanResident(r){const c=catalog.find(c=>c.id===r?.character_id);if(!c||!r.outfit||typeof r.outfit!=='object')return null;const outfit={};for(const k of ['outfit','head','hand'])if(Number.isInteger(r.outfit[k])&&c.sprites[r.outfit[k]]?.kind===k)outfit[k]=r.outfit[k];return Object.keys(outfit).length?{character_id:c.id,outfit}:null;}
function acceptResidents(rows){if(!Array.isArray(rows))throw Error('invalid village');const unique=new Map();for(const row of rows){const r=cleanResident(row);if(r)unique.set(r.character_id,r);}residents=[...unique.values()];try{localStorage.setItem(VILLAGE_KEY,JSON.stringify(residents));}catch(_){}$('village-count').textContent=residents.length;renderVillage();}
function avatar(c,outfit){const n=document.createElement('div');n.className='avatar';n.append(sprite(c,0));for(const kind of ['outfit','head','hand']){const index=outfit[kind];if(!Number.isInteger(index)||c.sprites[index]?.kind!==kind)continue;const layer=document.createElement('div');layer.className='layer '+kind;fitLayer(layer,kind,index,c);layer.append(sprite(c,index));n.append(layer);}return n;}
function renderVillage(arrived=null){const root=$('residents');root.replaceChildren();$('village-empty').hidden=residents.length>0;residents.forEach((r,i)=>{const c=catalog.find(c=>c.id===r.character_id),b=document.createElement('button'),pos=positions[i%positions.length];b.className='resident'+(r.character_id===arrived?' arriving':'');b.dataset.character=c.id;b.setAttribute('aria-label',c.name+' 만나기');b.style.left=pos[0]+'%';b.style.top=pos[1]+'%';b.style.zIndex=Math.round(pos[1]);b.style.setProperty('--delay',(-i*.7)+'s');b.append(avatar(c,r.outfit));const name=document.createElement('span');name.className='resident-label';name.textContent=c.name;const bubble=document.createElement('span');bubble.className='bubble';bubble.textContent=sayings[i%sayings.length];b.append(name,bubble);b.onclick=()=>openResident(r);root.append(b);});startVillageWalk();}
// Walk on the foreground paths; bound feet and labels inside the visible scene.
function startVillageWalk(){if(walkFrame===null)walkFrame=requestAnimationFrame(walkVillage);}
function walkVillage(now){
 walkFrame=null;
 if($('village-view').hidden||document.hidden||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches){walkTime=0;return;}
 const dt=Math.min((now-walkTime)/1000||0,.05);walkTime=now;
 if($('resident-modal').hidden){
  const scene=$('village-scene'),width=scene.clientWidth,height=scene.clientHeight;
  if(width&&height)document.querySelectorAll('.resident').forEach(node=>{
   const padX=Math.min(40,(node.offsetWidth/2+12)/width*100),minY=Math.min(88,Math.max(62,(node.offsetHeight+40)/height*100)),maxY=Math.max(minY,Math.min(92,100-30/height*100));
   let x=Math.max(padX,Math.min(100-padX,parseFloat(node.style.left))),y=Math.max(minY,Math.min(maxY,parseFloat(node.style.top)));
   let goal=walkTargets.get(node);
   if(!goal||Math.hypot((goal.x-x)*width/100,(goal.y-y)*height/100)<3){goal={x:padX+Math.random()*(100-2*padX),y:minY+Math.random()*(maxY-minY),speed:12+Math.random()*7};walkTargets.set(node,goal);}
   const dx=(goal.x-x)*width/100,dy=(goal.y-y)*height/100,distance=Math.hypot(dx,dy),step=Math.min(distance,goal.speed*dt);
   if(distance){x+=dx/distance*step/width*100;y+=dy/distance*step/height*100;}
   node.style.left=x+'%';node.style.top=y+'%';node.style.zIndex=Math.round(y);
  });
 }
 walkFrame=requestAnimationFrame(walkVillage);
}
document.addEventListener('visibilitychange',()=>{walkTime=0;if(!document.hidden&&!$('village-view').hidden)startVillageWalk();});
async function villageRequest(options={},url='/hyeon/dressup/village'){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);try{const r=await fetch(url,{...options,signal:controller.signal});if(!r.ok)throw Error('village unavailable');return await r.json();}finally{clearTimeout(timer);}}
try{acceptResidents(JSON.parse(localStorage.getItem(VILLAGE_KEY)||'[]'));}catch(_){acceptResidents([]);}
const villageReady=villageRequest().then(data=>{acceptResidents(data.residents);$('village-status').textContent=residents.length?residents.length+'명의 친구가 살고 있어요':'옷을 입힌 친구를 초대해요!';}).catch(()=>{$('village-status').textContent='저장된 마을을 보여줘요. 연결되면 다시 불러와요.';});
function showVillage(){cancelDrag();$('dressing-view').hidden=true;$('village-view').hidden=false;$('open-village').setAttribute('aria-pressed','true');renderVillage();}
function showDressing(){cancelDrag();$('village-view').hidden=true;$('dressing-view').hidden=false;$('resident-modal').hidden=true;$('open-village').setAttribute('aria-pressed','false');}
function openResident(r){selectedResident=r;const c=catalog.find(c=>c.id===r.character_id);$('resident-name').textContent=c.name+'의 집';$('resident-preview').replaceChildren(avatar(c,r.outfit));$('return-closet').disabled=false;$('return-closet').textContent='🏠 옷장으로 돌아가기';$('resident-modal').hidden=false;greetResident(c);}
$('open-village').onclick=()=>{unlock();showVillage();};$('back-dressing').onclick=showDressing;$('invite-first').onclick=showDressing;$('close-resident').onclick=()=>$('resident-modal').hidden=true;$('stay-village').onclick=()=>$('resident-modal').hidden=true;
$('redress').onclick=()=>{if(!selectedResident)return;const r=selectedResident,c=catalog.find(c=>c.id===r.character_id);state[c.id]={...r.outfit};save();showDressing();choose(c);};
$('return-closet').onclick=async()=>{
 if(!selectedResident||$('return-closet').disabled)return;
 const resident=selectedResident,c=catalog.find(c=>c.id===resident.character_id),button=$('return-closet');
 button.disabled=true;button.textContent='집에 가는 중…';unlock();
 try{
  const data=await villageRequest({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:c.id})},'/hyeon/dressup/village/return');
  state[c.id]={...resident.outfit};save();acceptResidents(data.residents);selectedResident=null;
  $('village-status').textContent=residents.length?residents.length+'명의 친구가 살고 있어요':'옷을 입힌 친구를 초대해요!';
  showDressing();choose(c);sound();toast('🏠 '+c.name+'이 옷장으로 돌아왔어요!');
 }catch(_){toast('돌아오지 못했어요. 연결을 확인하고 다시 눌러주세요.');}
 finally{button.disabled=false;button.textContent='🏠 옷장으로 돌아가기';}
};
$('send-village').onclick=async()=>{unlock();if(sending)return;const c=character,outfit={...current()};if(!Object.keys(outfit).length){toast('먼저 옷이나 장식을 입혀봐요 🎀');return;}sending=true;$('send-village').disabled=true;$('send-village').textContent='🏡 이사 준비 중…';try{await villageReady;const existed=residents.some(r=>r.character_id===c.id),data=await villageRequest({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:c.id,outfit})});acceptResidents(data.residents);save();showVillage();renderVillage(c.id);$('village-status').textContent=residents.length+'명의 친구가 살고 있어요';sound(true);toast(existed?'🏡 '+c.name+'이 새 옷을 입고 돌아왔어요!':'🏡 '+c.name+'이 마을에 이사 왔어요!');}catch(_){toast('마을 저장이 안 됐어요. 잠시 후 다시 눌러주세요.');}finally{sending=false;$('send-village').disabled=false;$('send-village').textContent='🏡 마을로 보내기';}};
setInterval(()=>{if($('village-view').hidden||document.hidden)return;const list=[...document.querySelectorAll('.resident')];if(!list.length)return;const n=list[Math.floor(Math.random()*list.length)];n.querySelector('.bubble').textContent=sayings[Math.floor(Math.random()*sayings.length)];n.classList.add('bubble-on');setTimeout(()=>n.classList.remove('bubble-on'),3000);},5200);

/* Speak only after a child's tap, using the device's Korean voice. */
let villageUtterance=null,villageSpeechSerial=0,villageSpeechTimer=null;
const greetingTurns=new Map();
const friendGreetings={
 chacha:'우리 같이 꽃밭을 산책할까?',
 shasha:'혜온이가 골라 준 옷이 정말 마음에 들어!',
 saekom:'오늘은 어떤 재미있는 놀이를 해 볼까?',
 banjjak:'혜온이랑 만나서 반짝반짝 기분이 좋아!',
 hachoo:'혜온아, 사랑해! 우리 같이 놀자!',
 yeou:'마을에 놀러 와 줘서 고마워!',
 kkang:'우리 같이 깡충깡충 뛰어 볼까?',
 ballet:'혜온아, 나랑 예쁘게 춤춰 볼까?',
 yogu:'같이 산책하니까 정말 즐거워!',
 pudding:'달콤한 하루야! 혜온이는 오늘 기분이 어때?',
 dalkom:'혜온아, 오늘도 만나서 정말 반가워!'
};
function stopVillageSpeech(){
 villageSpeechSerial++;clearTimeout(villageSpeechTimer);
 if(villageUtterance&&window.speechSynthesis){try{window.speechSynthesis.cancel();}catch(_){}}
 villageUtterance=null;
}
function greetResident(c,replay=false){
 const message=$('resident-message'),status=$('resident-speech-status');
 if(!replay){
  const turn=greetingTurns.get(c.id)||0;
  const lines=[friendGreetings[c.id]||'우리 같이 놀자!','혜온아, 오늘 재미있었던 일을 들려줄래?','다음에도 우리 마을에 놀러 와 줘!'];
  message.textContent='혜온아, 안녕! 나는 '+c.name+'이야. '+lines[turn%lines.length];
  greetingTurns.set(c.id,turn+1);
 }
 stopVillageSpeech();
 if(muted){status.textContent='🔇 위의 소리 버튼을 켜고 다시 들어요.';return;}
 if(!window.speechSynthesis||!window.SpeechSynthesisUtterance){status.textContent='이 기기에서는 말소리를 지원하지 않아요.';return;}
 const synth=window.speechSynthesis,serial=villageSpeechSerial;
 const failed=()=>{if(serial!==villageSpeechSerial)return;clearTimeout(villageSpeechTimer);status.textContent='말소리가 안 들리면 ‘다시 듣기’를 눌러 주세요.';villageUtterance=null;};
 try{
  const utterance=new window.SpeechSynthesisUtterance(message.textContent);
  const voices=synth.getVoices(),korean=voices.filter(v=>/^ko(?:-|_)/i.test(v.lang)||v.lang==='ko');
  const voice=korean.find(v=>v.localService)||korean[0];
  if(voice)utterance.voice=voice;
  utterance.lang='ko-KR';utterance.rate=.88;utterance.pitch=1.12;utterance.volume=1;
  utterance.onstart=()=>{if(serial!==villageSpeechSerial)return;clearTimeout(villageSpeechTimer);status.textContent='🔊 친구가 혜온이에게 이야기하고 있어요.';};
  utterance.onend=()=>{if(serial!==villageSpeechSerial)return;clearTimeout(villageSpeechTimer);villageUtterance=null;status.textContent='한 번 더 듣고 싶으면 ‘다시 듣기’를 눌러요.';};
  utterance.onerror=failed;
  villageUtterance=utterance;audio.pause();status.textContent='친구의 인사를 들어봐요.';
  // Holding a strong reference also avoids interrupted speech on iPad Safari.
  synth.resume();synth.speak(utterance);
  villageSpeechTimer=setTimeout(()=>{if(serial!==villageSpeechSerial)return;stopVillageSpeech();status.textContent='말소리가 안 들리면 ‘다시 듣기’를 눌러 주세요.';},8000);
 }catch(_){failed();}
}
$('resident-replay').onclick=()=>{if(!selectedResident)return;const c=catalog.find(c=>c.id===selectedResident.character_id);if(c)greetResident(c,true);};
document.addEventListener('click',e=>{
 const id=e.target.closest?.('button')?.id;
 if(['close-resident','stay-village','redress','return-closet','back-dressing'].includes(id)||(id==='sound'&&muted))stopVillageSpeech();
});
document.addEventListener('keydown',e=>{if(e.key==='Escape')stopVillageSpeech();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopVillageSpeech();});
try{window.speechSynthesis?.getVoices();}catch(_){}

})();

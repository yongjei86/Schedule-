'use strict';
(() => {
const $=id=>document.getElementById(id), ns='http://www.w3.org/2000/svg';
const token=document.querySelector('meta[name=creative-token]').content;
let templateId='sunflowers',designVersion=2;
const designs=window.RileyDesigns;
let arts=[],entries=[],colors={},artId=null,completed=false,color='#edb82c',erasing=false,history=[],future=[],recent=[],scale=1,tx=0,ty=0,pan=false,saveTimer,diaryTimer,dirty=false,diaryDirty=false,artRevision=0,diaryRevision=0;
let artQueue=Promise.resolve(),diaryQueue=Promise.resolve();
function notice(s){$('status').textContent=s;$('status').style.display='block';clearTimeout(notice.timer);notice.timer=setTimeout(()=>$('status').style.display='none',3500)}
async function post(path,data){const r=await fetch('/riley/creative/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Creative-Token':token},body:JSON.stringify(data)});if(!r.ok)throw Error('저장하지 못했어요. 다시 눌러 주세요.');return r.json()}
async function refresh(){const r=await fetch('/riley/creative/data',{cache:'no-store'});if(!r.ok)throw Error('기록을 불러오지 못했어요.');const d=await r.json();arts=d.arts;entries=d.entries;}
function node(tag,attrs,parent){const e=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e}
// Closed vector regions prevent paint leaking across outlines at any zoom level.
function paintRegion(e,id){if(pan||Date.now()-lastDrag<500)return;const previous=colors[id]||'#fffdf7',next=erasing?'#fffdf7':color;if(previous===next)return;history.push({id,previous,next});future=[];colors[id]=next;e.setAttribute('fill',next);if(!erasing){recent=[color,...recent.filter(c=>c!==color)].slice(0,10);palette($('recent'),recent)}changed();}
function drawing(paint={},interactive=false,design=templateId,version=designVersion){if(version>=2)return window.RileyFineArt(design,paint,interactive?paintRegion:null);if(design!=='sunflowers')return designs.draw(design,paint,interactive?paintRegion:null);const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 680 820');svg.setAttribute('xmlns',ns);svg.setAttribute('role','img');svg.setAttribute('aria-label','꽃병에 담긴 해바라기 색칠 도안');let idx=0;
const region=(tag,attrs,id)=>{id=id||'region-'+idx++;const e=node(tag,{...attrs,fill:paint[id]||'#fffdf7',stroke:'#443d31','stroke-width':1.8,'stroke-linejoin':'round','data-region':id},svg);if(interactive)e.addEventListener('click',()=>{if(pan||Date.now()-lastDrag<500)return;const previous=colors[id]||'#fffdf7',next=erasing?'#fffdf7':color;if(previous===next)return;history.push({id,previous,next});future=[];colors[id]=next;e.setAttribute('fill',next);if(!erasing){recent=[color,...recent.filter(c=>c!==color)].slice(0,10);palette($('recent'),recent)}changed();});return e};
region('rect',{x:6,y:6,width:668,height:808},'background');region('path',{d:'M6 645 Q340 625 674 645 L674 814 H6 Z'},'table');
const flowers=[[190,205,42,-18],[320,155,48,5],[448,218,43,18],[116,348,37,-25],[266,316,48,-9],[390,350,42,15],[535,365,34,30],[204,456,38,-18],[470,476,36,26],[338,435,34,2],[155,128,29,-10]];
flowers.forEach(([x,y,r,a],f)=>{region('path',{d:`M${x-4} ${y} Q${x+35} ${y+140} ${330+f*2} 668 L${340+f*2} 668 Q${x+45} ${y+130} ${x+4} ${y}Z`},`stem-${f}`)});
[[200,495,-32],[415,526,28],[262,553,-42],[455,588,30],[144,408,-35],[495,430,38]].forEach(([x,y,a],i)=>region('path',{d:`M${x} ${y} Q${x-68} ${y-105} ${x-80} ${y-30} Q${x-60} ${y+30} ${x} ${y}Z`,transform:`rotate(${a} ${x} ${y})`},`leaf-${i}`));
flowers.forEach(([x,y,r,a],f)=>{const count=15+(f%3);for(let p=0;p<count;p++){const angle=p*360/count+a;const len=r*(1.2+0.18*Math.sin(p*2.3+f));region('path',{d:`M${x-9} ${y-r+6} Q${x-26} ${y-r-len*.45} ${x-3} ${y-r-len} Q${x+23} ${y-r-len*.5} ${x+9} ${y-r+6}Z`,transform:`rotate(${angle} ${x} ${y})`},`flower-${f}-petal-${p}`)}region('circle',{cx:x,cy:y,r},`flower-${f}-center`);region('circle',{cx:x,cy:y,r:r*.64},`flower-${f}-inner`);for(let k=0;k<8;k++){const a=k*Math.PI/4;region('ellipse',{cx:x+Math.cos(a)*r*.37,cy:y+Math.sin(a)*r*.37,rx:r*.1,ry:r*.14,transform:`rotate(${k*45} ${x+Math.cos(a)*r*.37} ${y+Math.sin(a)*r*.37})`},`flower-${f}-seed-${k}`)}});
region('path',{d:'M230 596 Q340 570 450 596 L431 638 Q448 734 405 777 Q340 803 275 777 Q232 734 249 638Z'},'vase');region('path',{d:'M244 670 Q340 692 436 670 L437 697 Q340 720 243 697Z'},'vase-band');region('ellipse',{cx:340,cy:596,rx:110,ry:15},'vase-rim');return svg;}
let lastDrag=0;
function render(){const meta=designs.catalog.find(d=>d.id===templateId);$('design-title').textContent=meta.title;$('design-meta').textContent=meta.by+' · '+meta.level;$('design-category').textContent=meta.group;$('design-note').textContent=meta.note;const svg=drawing(colors,true);$('art-host').replaceChildren(svg);$('art-title').value=currentTitle;update();}
let currentTitle='나의 해바라기';
function update(){const regions=$('art-host').querySelectorAll('[data-region]');let count=[...regions].filter(e=>colors[e.dataset.region]&&colors[e.dataset.region]!=='#fffdf7').length;$('progress').textContent=`${count} / ${regions.length} 영역`;$('undo').disabled=!history.length;$('redo').disabled=!future.length;}
function changed(){dirty=true;artRevision++;completed=false;update();clearTimeout(saveTimer);saveTimer=setTimeout(()=>saveArt(false).catch(e=>notice(e.message)),900);}
function saveArt(done=false){clearTimeout(saveTimer);const rev=artRevision;const snapshot={template:templateId,design_version:designVersion,title:$('art-title').value,colors:{...colors},completed:done||completed};const task=artQueue.catch(()=>{}).then(async()=>{const result=await post('art',{...snapshot,id:artId});artId=result.id;if(rev===artRevision){dirty=false;completed=snapshot.completed;}return result;});artQueue=task;return task;}
async function tab(name){try{if(dirty)await saveArt();if(diaryDirty)await saveDiary();await artQueue;await diaryQueue;if(name==='library')designLibrary();else if(name!=='studio'){await refresh();if(name==='gallery')gallery();else diaryList();}document.querySelectorAll('.view').forEach(e=>e.classList.toggle('active',e.id===name));document.querySelectorAll('[data-tab]').forEach(e=>e.classList.toggle('active',e.dataset.tab===name));}catch(e){notice(e.message)}}
document.querySelectorAll('[data-tab]').forEach(e=>e.onclick=()=>tab(e.dataset.tab));
function palette(host,list){host.replaceChildren();list.forEach(c=>{const b=document.createElement('button');b.className='swatch';b.style.background=c;b.title=c;b.setAttribute('aria-label','색상 '+c);b.onclick=()=>select(c);host.append(b)})}
function select(c){color=c;erasing=false;$('erase').classList.remove('active');$('selected').style.background=c;$('picker').value=c;$('hex').textContent=c.toUpperCase();const vals=[1,3,5].map(i=>parseInt(c.slice(i,i+2),16));document.querySelectorAll('#rgb input').forEach(e=>e.value=vals[Number(e.dataset.channel)]);document.querySelectorAll('.swatch').forEach(e=>e.classList.toggle('active',e.title===c))}
palette($('palette'),['#e64b3c','#f18b35','#f6cf43','#a4cc52','#438d59','#79c7eb','#3d72c6','#9162bd','#222222','#999999','#8b5b37','#efc5a5','#ffffff']);palette($('pastels'),['#f4bdc5','#f8d3a5','#fff0b0','#d2e5b9','#c2e4ed','#c9c8ea','#e6cae2','#e1d8cd']);
['R','G','B'].forEach((label,i)=>{const row=document.createElement('label');row.append(label);['range','number'].forEach(type=>{const e=document.createElement('input');e.type=type;e.min=0;e.max=255;e.step=1;e.dataset.channel=i;e.setAttribute('aria-label',label+' '+(type==='range'?'슬라이더':'값'));e.oninput=()=>{const vals=[1,3,5].map(j=>parseInt(color.slice(j,j+2),16));vals[i]=Math.max(0,Math.min(255,Number(e.value)||0));select('#'+vals.map(v=>v.toString(16).padStart(2,'0')).join(''))};row.append(e)});$('rgb').append(row)});$('picker').oninput=e=>select(e.target.value);select(color);
$('erase').onclick=()=>{erasing=!erasing;$('erase').classList.toggle('active',erasing)};
function travel(from,to,key){const action=from.pop();if(!action)return;to.push(action);colors[action.id]=action[key];$('art-host').querySelector(`[data-region="${action.id}"]`).setAttribute('fill',action[key]);changed()}
$('undo').onclick=()=>travel(history,future,'previous');$('redo').onclick=()=>travel(future,history,'next');$('reset').onclick=()=>{if(confirm('현재 그림의 색을 모두 지울까요?')){colors={};history=[];future=[];render();changed()}};
$('art-title').oninput=()=>{currentTitle=$('art-title').value;changed()};$('pause').onclick=async()=>{try{await saveArt();notice('저장했어요. 다음에 이어서 색칠할 수 있어요.');await tab('gallery')}catch(e){notice(e.message)}};$('finish').onclick=async()=>{try{await saveArt(true);notice('갤러리에 완성작을 저장했어요!');await tab('gallery')}catch(e){notice(e.message)}};
function transform(){$('art-host').style.transform=`translate(${tx}px,${ty}px) scale(${scale})`;$('zoom-label').textContent=Math.round(scale*100)+'%'}
$('zoom-in').onclick=()=>{scale=Math.min(4,scale+.25);transform()};$('zoom-out').onclick=()=>{scale=Math.max(.75,scale-.25);transform()};$('fit').onclick=()=>{scale=1;tx=ty=0;transform()};$('pan').onclick=()=>{pan=!pan;$('pan').classList.toggle('active',pan)};let drag=null;
// Touch gestures stay inside the canvas; a short single tap still paints.
const viewport=$('viewport');
let touchGesture=null;
function touchPoint(t){const r=viewport.getBoundingClientRect();return {x:t.clientX-r.left-r.width/2,y:t.clientY-r.top-r.height/2};}
function beginTouch(touches){
 if(touches.length>=2){
  const a=touchPoint(touches[0]),b=touchPoint(touches[1]);
  touchGesture={kind:'pinch',distance:Math.max(1,Math.hypot(b.x-a.x,b.y-a.y)),cx:(a.x+b.x)/2,cy:(a.y+b.y)/2,scale,tx,ty};
  lastDrag=Date.now();
 }else if(touches.length===1){
  const p=touchPoint(touches[0]);
  touchGesture={kind:'single',x:p.x,y:p.y,tx,ty,moved:false};
 }else touchGesture=null;
}
viewport.addEventListener('touchstart',e=>{beginTouch(e.touches);if(e.touches.length>=2)e.preventDefault();},{passive:false});
viewport.addEventListener('touchmove',e=>{
 if(!touchGesture)return;
 if(e.touches.length>=2){
  e.preventDefault();
  if(touchGesture.kind!=='pinch')beginTouch(e.touches);
  const g=touchGesture,a=touchPoint(e.touches[0]),b=touchPoint(e.touches[1]);
  const next=Math.max(.75,Math.min(4,g.scale*Math.hypot(b.x-a.x,b.y-a.y)/g.distance));
  const ratio=next/g.scale;
  tx=(a.x+b.x)/2-(g.cx-g.tx)*ratio;
  ty=(a.y+b.y)/2-(g.cy-g.ty)*ratio;
  scale=next;lastDrag=Date.now();transform();
 }else if(e.touches.length===1&&touchGesture.kind==='single'){
  const p=touchPoint(e.touches[0]),g=touchGesture,dx=p.x-g.x,dy=p.y-g.y;
  if(g.moved||Math.hypot(dx,dy)>7){
   g.moved=true;lastDrag=Date.now();e.preventDefault();
   if(pan||scale>1){tx=g.tx+dx;ty=g.ty+dy;transform();}
  }
 }
},{passive:false});
viewport.addEventListener('touchend',e=>{
 const used=touchGesture&&(touchGesture.kind==='pinch'||touchGesture.moved);
 if(used){lastDrag=Date.now();e.preventDefault();}
 beginTouch(e.touches);
},{passive:false});
viewport.addEventListener('touchcancel',()=>{lastDrag=Date.now();touchGesture=null;},{passive:true});
// Mouse and Apple Pencil keep the explicit move mode.
viewport.onpointerdown=e=>{if(e.pointerType==='touch'||!pan)return;drag={x:e.clientX,y:e.clientY,tx,ty};e.currentTarget.setPointerCapture(e.pointerId)};
viewport.onpointermove=e=>{if(e.pointerType==='touch'||!drag)return;tx=drag.tx+e.clientX-drag.x;ty=drag.ty+e.clientY-drag.y;lastDrag=Date.now();transform()};
viewport.onpointerup=viewport.onpointercancel=()=>drag=null;
$('reference').onclick=()=>{const d=designs.catalog.find(d=>d.id===templateId);$('story-title').textContent=d.title+' · '+d.by;$('story-text').textContent=d.story;$('story-link').href=d.url;$('story').showModal()};
$('choose-design').onclick=()=>tab('library');
function button(text,fn){const e=document.createElement('button');e.textContent=text;e.onclick=fn;return e}
function gallery(){const host=$('gallery-list');host.replaceChildren();if(!arts.length){const p=document.createElement('p');p.textContent='아직 그림이 없어요. 새 그림으로 시작해 보세요.';host.append(p)}arts.forEach(a=>{const card=document.createElement('article');card.className='art-card';card.append(drawing(a.colors,false,a.template||'sunflowers',a.design_version||1));const title=document.createElement('h3');title.textContent=a.title;const sub=document.createElement('p');sub.textContent=(a.completed?'완성작':'그리는 중')+' · '+a.updated.slice(0,10);card.append(title,sub,button('이어서 색칠',()=>loadArt(a)),button('이미지 저장',()=>download(a)));if(a.completed)card.append(button('일기에 붙이기',async()=>{await tab('diary');$('entry-art').value=a.id;previewEntry();diaryChange()}));host.append(card)})}
async function loadArt(a){templateId=a.template||'sunflowers';designVersion=a.design_version||1;artId=a.id;colors={...a.colors};currentTitle=a.title;completed=!!a.completed;dirty=false;history=[];future=[];render();$('fit').click();await tab('studio')}
$('new-art').onclick=()=>tab('library');
async function startDesign(id){try{if(dirty)await saveArt();await artQueue;templateId=id;designVersion=2;artId=null;colors={};currentTitle='나의 '+designs.catalog.find(d=>d.id===id).title;completed=false;dirty=false;history=[];future=[];render();$('fit').click();await tab('studio');}catch(e){notice(e.message)}}
let designFilter='전체';
function designLibrary(){
 const filters=$('design-filters');filters.replaceChildren();['전체','명화','이탈리아','스페인','프랑스'].forEach(name=>{const b=button(name,()=>{designFilter=name;designLibrary()});b.classList.toggle('active',name===designFilter);filters.append(b)});
 const host=$('design-list');host.replaceChildren();designs.catalog.filter(d=>designFilter==='전체'||d.group===designFilter).forEach(d=>{const card=document.createElement('article');card.className='design-card';const preview=drawing({},false,d.id,2);preview.setAttribute('aria-hidden','true');const title=document.createElement('h2');title.textContent=d.title;const meta=document.createElement('p');meta.textContent=d.by+' · '+d.group+' · '+d.level;const note=document.createElement('p');note.textContent=d.note;const go=button('이 그림 색칠하기',()=>startDesign(d.id));go.className='primary';card.append(preview,title,meta,note,go);host.append(card)});
}
function download(a){const svg=drawing(a.colors,false,a.template||'sunflowers',a.design_version||1);svg.setAttribute('width','1360');svg.setAttribute('height','1640');const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'})),image=new Image();image.onload=()=>{const c=document.createElement('canvas');c.width=1360;c.height=1640;c.getContext('2d').drawImage(image,0,0);c.toBlob(blob=>{const link=document.createElement('a'),u=URL.createObjectURL(blob);link.href=u;link.download=(a.title||'해바라기')+'.png';link.click();setTimeout(()=>URL.revokeObjectURL(u),10000)},'image/png');URL.revokeObjectURL(url)};image.onerror=()=>{notice('이미지 저장에 실패했어요.');URL.revokeObjectURL(url)};image.src=url}
function today(){return new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Seoul'}).format(new Date())}
function diaryList(){const selected=$('entry-art').value;$('entry-art').replaceChildren(new Option('그림 없이 쓰기',''));arts.filter(a=>a.completed).forEach(a=>$('entry-art').append(new Option(a.title,a.id)));$('entry-art').value=selected;const list=$('entry-list');list.replaceChildren();entries.forEach(e=>list.append(button(e.day+' · '+(e.title||'제목 없는 일기'),()=>openDay(e.day))));if(!$('day').value)openDay(today());previewEntry();}
let openedDay='';
async function openDay(day){try{if(diaryDirty)await saveDiary();await diaryQueue;const e=entries.find(e=>e.day===day);openedDay=day;$('day').value=day;$('entry-title').value=e?.title||'';$('entry-body').value=e?.body||'';$('entry-art').value=e?.art_id||'';previewEntry();$('diary-status').textContent=e?'저장된 일기':'새 일기';}catch(e){$('day').value=openedDay;notice(e.message)}}
function previewEntry(){const a=arts.find(a=>a.id===$('entry-art').value);$('entry-picture').replaceChildren();if(a)$('entry-picture').append(drawing(a.colors,false,a.template||'sunflowers',a.design_version||1))}
function diaryChange(){diaryDirty=true;diaryRevision++;$('diary-status').textContent='저장 중…';clearTimeout(diaryTimer);diaryTimer=setTimeout(()=>saveDiary().catch(e=>{$('diary-status').textContent='저장 실패 · 다시 저장해 주세요';notice(e.message)}),1000)}
function saveDiary(){clearTimeout(diaryTimer);if(!openedDay)return Promise.resolve();const rev=diaryRevision;const data={day:openedDay,title:$('entry-title').value,body:$('entry-body').value,art_id:$('entry-art').value};const task=diaryQueue.catch(()=>{}).then(async()=>{await post('diary',data);const i=entries.findIndex(e=>e.day===data.day);if(i<0)entries.unshift(data);else entries[i]=data;if(rev===diaryRevision){diaryDirty=false;$('diary-status').textContent='저장 완료';}});diaryQueue=task;return task;}
$('entry-title').oninput=$('entry-body').oninput=diaryChange;$('entry-art').onchange=()=>{previewEntry();diaryChange()};$('day').onchange=e=>{if(e.target.value)openDay(e.target.value)};$('today').onclick=()=>openDay(today());$('save-diary').onclick=()=>saveDiary().then(()=>{notice('일기를 저장했어요.');diaryList()}).catch(e=>notice(e.message));
window.addEventListener('beforeunload',e=>{if(dirty||diaryDirty){e.preventDefault();e.returnValue=''}});
render();refresh().then(()=>tab(document.body.dataset.view==='diary'?'diary':'library')).catch(e=>notice(e.message));
})();


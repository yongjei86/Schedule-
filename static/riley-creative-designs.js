'use strict';
window.RileyDesigns=(()=>{
const catalog=[
{id:'sunflowers',title:'해바라기',by:'빈센트 반 고흐',group:'명화',level:'도전',note:'꽃잎마다 조금씩 다른 노란색을 써 볼까요?',story:'고흐의 해바라기에서 꽃병과 꽃의 구성을 가져와 새로 그린 색칠 도안이에요. 같은 노란색도 밝고 어둡게 바꾸면 꽃이 더 풍성해 보여요.',url:'https://www.nationalgallery.org.uk/paintings/vincent-van-gogh-sunflowers'},
{id:'starry',title:'별이 빛나는 밤',by:'빈센트 반 고흐',group:'명화',level:'보통',note:'하늘의 소용돌이와 조용한 마을을 다른 색으로 표현해요.',story:'고흐의 별이 빛나는 밤에서 영감을 얻었어요. 소용돌이치는 하늘, 밝은 별, 마을과 나무를 새로 구성했어요. 지유의 밤하늘은 어떤 색일까요?',url:'https://www.moma.org/collection/works/79802'},
{id:'cezanne',title:'사과와 주전자가 있는 정물',by:'폴 세잔',group:'명화',level:'보통',note:'사과의 밝은 부분과 어두운 부분을 다르게 칠해 봐요.',story:'세잔이 그린 사과와 그릇의 정물에서 영감을 받은 새 도안이에요. 사과를 둥글게 보이게 하려면 어느 쪽을 밝게 칠하면 좋을까요?',url:'https://www.metmuseum.org/art/collection/search/435884'},
{id:'chagall',title:'꿈속의 마을',by:'마르크 샤갈에서 영감',group:'명화',level:'보통',note:'하늘을 나는 사람과 동물에게 상상 속 색을 선물해요.',story:'샤갈의 나와 마을에 나오는 환상적인 색과 고향의 기억에서 영감을 받아 새로 그린 장면이에요. 실제로는 불가능해도 꿈에서는 가능한 이야기를 만들어 보세요.',url:'https://www.moma.org/collection/works/78984'},
{id:'monet',title:'수련 연못과 다리',by:'클로드 모네에서 영감',group:'명화',level:'보통',note:'물에 비친 빛과 수련을 부드러운 색으로 표현해요.',story:'모네가 즐겨 그린 수련 연못과 정원의 다리에서 영감을 얻은 새 도안이에요. 물은 파란색만 있을까요? 초록, 보라, 분홍도 찾아보세요.',url:'https://www.metmuseum.org/art/collection/search?q=Monet%20Water%20Lilies'},
{id:'colosseum',title:'로마 콜로세움',by:'이탈리아 · 로마',group:'이탈리아',level:'도전',note:'층마다 이어진 아치와 돌벽의 색을 찾아봐요.',story:'로마의 원형 경기장을 색칠하기 좋게 재구성했어요. 반복되는 아치가 건물의 리듬을 만들어요. 층마다 색을 바꾸거나 돌의 색을 조금씩 달리해 보세요.',url:'https://colosseo.it/'},
{id:'duomo',title:'피렌체 두오모',by:'이탈리아 · 피렌체',group:'이탈리아',level:'도전',note:'붉은 지붕과 대리석 무늬를 나만의 색으로 꾸며요.',story:'피렌체의 큰 돔과 성당 정면, 종탑을 한 장에 재구성했어요. 돔의 곡선과 정면의 기하학 무늬를 관찰하고 칠해 보세요.',url:'https://duomo.firenze.it/'},
{id:'pisa',title:'피사의 사탑',by:'이탈리아 · 피사',group:'이탈리아',level:'보통',note:'기울어진 탑의 아치와 잔디밭을 색칠해요.',story:'피사의 사탑에서 영감을 받은 건축 도안이에요. 탑이 한쪽으로 기울어 있어도 창문과 기둥은 일정한 규칙으로 반복돼요.',url:'https://www.opapisa.it/'},
{id:'sagrada',title:'사그라다 파밀리아',by:'스페인 · 바르셀로나',group:'스페인',level:'도전',note:'나무처럼 자라는 탑과 장미창에 색을 채워요.',story:'가우디의 성당에서 영감을 받아 탑과 정면을 재구성했어요. 자연에서 찾은 곡선과 형태를 생각하며 탑과 창문을 꾸며 보세요.',url:'https://sagradafamilia.org/'},
{id:'alhambra',title:'알함브라 궁전의 정원',by:'스페인 · 그라나다',group:'스페인',level:'도전',note:'아치와 타일 무늬, 물에 비친 궁전을 함께 칠해요.',story:'알함브라 궁전의 아치와 물이 있는 안뜰에서 영감을 받은 장면이에요. 같은 무늬에 같은 색을 반복하면 어떤 느낌이 생길까요?',url:'https://www.alhambra-patronato.es/'},
{id:'madrid',title:'마드리드 왕궁',by:'스페인 · 마드리드',group:'스페인',level:'보통',note:'궁전 창문과 앞뜰을 규칙 있는 색으로 꾸며요.',story:'마드리드 왕궁의 정면에서 영감을 받아 새로 구성했어요. 양쪽이 비슷하게 생긴 대칭을 찾아보고 지유만의 정원을 만들어 보세요.',url:'https://www.patrimonionacional.es/'}];
function draw(id,paint={},paintRegion){
const meta=catalog.find(d=>d.id===id);if(!meta||id==='sunflowers')return null;
const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 680 820');svg.setAttribute('xmlns',ns);svg.setAttribute('aria-label',meta.title+' 색칠 도안');svg.setAttribute('role','img');let count=0;
const r=(tag,attrs,key)=>{const e=document.createElementNS(ns,tag);key=key||'r-'+count++;for(const [k,v]of Object.entries({...attrs,fill:paint[key]||'#fffdf7',stroke:'#443d31','stroke-width':1.6,'stroke-linejoin':'round','data-region':key}))e.setAttribute(k,v);if(paintRegion)e.addEventListener('click',()=>paintRegion(e,key));svg.append(e);return e};
const rect=(x,y,w,h,rx=0)=>r('rect',{x,y,width:w,height:h,rx});const path=d=>r('path',{d});const ellipse=(x,y,rx,ry)=>r('ellipse',{cx:x,cy:y,rx,ry});const circle=(x,y,rad)=>r('circle',{cx:x,cy:y,r:rad});const poly=points=>r('polygon',{points});
function arch(x,y,w,h){path(`M${x} ${y+h}V${y+w/2}A${w/2} ${w/2} 0 0 1 ${x+w} ${y+w/2}V${y+h}Z`)}
function house(x,y,w,h){rect(x,y,w,h);poly(`${x-5},${y} ${x+w/2},${y-36} ${x+w+5},${y}`);rect(x+w*.38,y+h*.55,w*.24,h*.45);rect(x+8,y+12,w*.22,h*.2);rect(x+w*.65,y+12,w*.22,h*.2)}
function star(x,y,size,n=8){let pts=[];for(let i=0;i<n*2;i++){let a=i*Math.PI/n-Math.PI/2,rad=i%2?size*.48:size;pts.push(`${x+Math.cos(a)*rad},${y+Math.sin(a)*rad}`)}poly(pts.join(' '))}
function cloud(x,y,w){path(`M${x} ${y}C${x-w*.15} ${y-27} ${x+w*.22} ${y-52} ${x+w*.38} ${y-25}C${x+w*.5} ${y-65} ${x+w*.85} ${y-52} ${x+w*.87} ${y-22}C${x+w*1.15} ${y-26} ${x+w*1.15} ${y+12} ${x+w} ${y+12}H${x}Z`)}
function flower(x,y,size){for(let i=0;i<8;i++){const a=i*Math.PI/4;ellipse(x+Math.cos(a)*size*.7,y+Math.sin(a)*size*.7,size*.45,size*.3)}circle(x,y,size*.35)}
rect(6,6,668,808);
if(id==='starry'){
 path('M6 540Q95 440 170 485T340 492T520 450T674 475V814H6Z');
 for(let i=0;i<5;i++){let y=100+i*70;path(`M12 ${y}C140 ${y-75} 205 ${y+100} 340 ${y+8}S540 ${y-40} 668 ${y+10}L668 ${y+25}C530 ${y-25} 470 ${y+110} 340 ${y+27}S150 ${y-50} 12 ${y+20}Z`)}
 path('M190 225C225 135 396 127 427 211C453 283 350 319 305 273C279 244 310 212 347 226C365 234 371 248 360 257C346 238 323 244 329 257C353 281 407 253 399 224C382 167 261 175 224 239Z');
 [[185,110,30],[380,95,21],[280,250,26],[525,315,24],[590,150,20],[425,390,19]].forEach(([x,y,s])=>{circle(x,y,s*1.35);star(x,y,s)});
 path('M555 56A57 57 0 1 0 611 130A50 50 0 0 1 555 56Z');
 for(let i=0;i<7;i++)house(100+i*78,560+(i%2)*35,62,110);
 rect(356,508,52,144);poly('348,508 382,438 416,508');arch(373,543,18,37);
 path('M45 814Q80 680 55 585Q110 512 88 425Q150 345 134 264Q193 405 166 500Q215 625 170 700L200 814Z');
 path('M96 795Q147 658 118 587Q165 527 149 434Q184 552 160 623Q181 717 144 806Z');
 for(let i=0;i<8;i++)ellipse(230+i*53,755+(i%2)*25,28,9);
}
if(id==='cezanne'){
 path('M6 490L674 457V814H6Z');path('M105 443Q215 402 305 447L571 736Q457 773 344 744L131 814L60 742Z');
 for(let i=0;i<7;i++)path(`M${100+i*50} 480Q${160+i*48} 590 ${130+i*60} 740L${150+i*60} 735Q${185+i*48} 580 ${120+i*50} 475Z`);
 ellipse(368,586,211,58);ellipse(368,580,181,39);
 path('M400 255Q425 236 477 255L488 312Q553 419 510 510Q450 541 387 505Q351 442 390 342Z');ellipse(440,255,40,12);path('M493 314C591 302 597 446 522 455L526 423C566 402 552 341 501 344Z');path('M392 352Q443 375 504 347L514 380Q445 408 379 380Z');
 [[209,532,49],[296,500,48],[373,540,45],[466,554,48],[531,618,41],[244,671,48]].forEach(([x,y,s])=>{path(`M${x} ${y-s*.65}C${x-s} ${y-s*1.3} ${x-s*1.2} ${y+s*.5} ${x} ${y+s}C${x+s*1.2} ${y+s*.5} ${x+s} ${y-s*1.3} ${x} ${y-s*.65}Z`);path(`M${x+5} ${y-s*.5}Q${x+s*.9} ${y-s*.3} ${x+s*.5} ${y+s*.5}Q${x+s*.15} ${y+s*.8} ${x+5} ${y-s*.5}Z`);path(`M${x-3} ${y-s*.65}L${x+3} ${y-s-10}L${x+9} ${y-s-8}L${x+4} ${y-s*.65}Z`)});
 path('M84 526L148 526L142 579Q116 596 90 579Z');ellipse(116,526,32,10);path('M145 535C183 522 185 575 144 570L145 557C167 559 165 540 146 546Z');
}
if(id==='chagall'){
 path('M6 470L340 80L674 440V814H6Z');circle(550,126,62);circle(550,126,38);
 for(let i=0;i<5;i++)house(85+i*112,510+(i%2)*48,82,138);
 path('M6 750Q190 655 340 734T674 730V814H6Z');
 // A floating violinist, a friendly goat and an imaginary flowering tree.
 ellipse(255,205,31,39);path('M230 240L283 239L315 345L242 335Z');poly('246,335 268,339 230,417 211,407');poly('286,339 309,345 359,399 341,414');poly('231,254 247,273 177,312 166,293');poly('280,254 292,271 348,227 336,214');
 ellipse(309,287,24,35);ellipse(313,250,19,25);rect(311,195,8,41);poly('284,226 291,217 350,305 344,310');circle(244,199,4);circle(264,199,4);
 ellipse(470,407,80,45);path('M412 390L387 332L405 305L438 366Z');ellipse(398,325,29,26);poly('388,303 374,270 398,301');poly('410,306 423,278 422,316');circle(389,323,4);poly('416,437 429,439 422,492 412,492');poly('503,439 515,436 527,485 516,490');
 path('M330 754L342 547L355 754Z');path('M343 614L294 562L300 556L349 590Z');path('M348 649L402 587L410 593L351 674Z');
 [[286,548],[340,518],[407,572],[299,641],[393,667]].forEach(([x,y])=>flower(x,y,22));
 cloud(64,101,115);star(82,296,26);star(575,573,20);star(519,251,21);
}
if(id==='monet'){
 for(let i=0;i<9;i++)path(`M${6+i*76} 6Q${-10+i*76} 140 ${25+i*76} 263L${65+i*76} 270Q${30+i*76} 125 ${76+i*76} 6Z`);
 path('M6 290Q340 210 674 290V814H6Z');
 path('M6 363Q340 126 674 363L674 398Q340 175 6 398Z');
 for(let i=0;i<15;i++){const x=22+i*44,y=284+Math.pow((x-340)/320,2)*102;poly(`${x},${y} ${x+10},${y-5} ${x+10},${y+91} ${x},${y+96}`)}
 path('M6 416Q340 192 674 416L674 440Q340 220 6 440Z');
 for(let i=0;i<6;i++){let y=454+i*57;path(`M15 ${y}Q170 ${y-25} 330 ${y+2}T665 ${y-10}L665 ${y+3}Q490 ${y+34} 330 ${y+15}T15 ${y+12}Z`)}
 [[125,500,46],[460,505,43],[315,593,55],[563,680,50],[151,713,60],[407,746,50],[575,570,35]].forEach(([x,y,size])=>{path(`M${x} ${y}L${x+size} ${y-8}A${size} ${size*.4} 0 1 1 ${x+size*.7} ${y+20}Z`);flower(x-8,y-12,size*.4)});
}
if(id==='colosseum'){
 path('M6 672Q340 622 674 672V814H6Z');cloud(80,133,145);cloud(453,90,140);
 path('M57 304Q340 219 623 304L623 672Q340 745 57 672Z');
 for(let row=0;row<4;row++){const y=320+row*84;path(`M57 ${y}Q340 ${y-65} 623 ${y}L623 ${y+13}Q340 ${y-52} 57 ${y+13}Z`);for(let col=0;col<12;col++){const x=73+col*45,yy=y+15-42*Math.sin((col+0.5)*Math.PI/12);arch(x,yy,28,58);rect(x-6,yy-3,5,67)}}
 path('M57 297Q340 209 623 297L623 315Q340 232 57 315Z');
 for(let i=0;i<13;i++)rect(64+i*43,278-38*Math.sin(i*Math.PI/13),29,15);
 for(let i=0;i<8;i++)path(`M${80+i*74} 744L${124+i*65} 721L${161+i*67} 743L${116+i*71} 772Z`);
}
if(id==='duomo'){
 rect(6,706,668,108);cloud(45,110,118);cloud(492,89,120);
 // Dome and lantern, with separate curved panels.
 path('M214 378Q217 206 340 147Q463 206 466 378Z');
 for(let i=0;i<6;i++){let x1=214+i*42,x2=x1+42;path(`M340 147Q${265+i*20} 239 ${x1} 378L${x2} 378Q${285+i*20} 239 340 147Z`)}
 rect(212,365,256,40);rect(321,112,38,45);poly('315,112 340,78 365,112');rect(336,57,8,24);rect(330,63,20,6);
 // Tower and cathedral facade.
 rect(511,295,76,412);for(let i=0;i<5;i++){rect(511,310+i*74,76,12);arch(524,333+i*70,18,41);arch(555,333+i*70,18,41)}poly('505,295 549,265 593,295');
 rect(105,491,374,216);poly('94,491 193,407 268,454 341,376 489,491');
 poly('118,491 192,428 262,491');poly('277,491 341,402 459,491');
 arch(258,552,85,155);arch(142,596,58,111);arch(399,596,58,111);
 circle(301,507,38);circle(301,507,25);for(let i=0;i<8;i++){const a=i*Math.PI/4;circle(301+Math.cos(a)*15,507+Math.sin(a)*15,6)}
 for(let i=0;i<7;i++){rect(115+i*51,538,12,46);rect(115+i*51,666,12,40)}
 for(let i=0;i<6;i++)poly(`${135+i*53},516 ${146+i*53},503 ${157+i*53},516 ${146+i*53},529`);
 for(let i=0;i<4;i++)rect(105,567+i*34,374,8);
}
if(id==='pisa'){
 cloud(65,132,150);cloud(427,110,135);path('M6 681Q340 619 674 681V814H6Z');ellipse(343,713,177,30);
 const start=svg.children.length;
 rect(237,198,208,494);ellipse(341,198,104,24);rect(275,141,132,58);ellipse(341,141,66,19);
 for(let row=0;row<7;row++){let y=218+row*63;rect(237,y,208,10);for(let col=0;col<7;col++){arch(244+col*28,y+15,20,42);rect(241+col*28,y+13,4,46)}}
 rect(226,681,230,20);for(let i=0;i<4;i++)arch(286+i*29,157,20,35);
 for(let i=start;i<svg.children.length;i++)svg.children[i].setAttribute('transform','rotate(-7 341 701)');
 for(let i=0;i<9;i++)ellipse(55+i*72,772+(i%2)*13,19,7);
}
if(id==='sagrada'){
 path('M6 737L674 737V814H6Z');cloud(39,141,105);cloud(521,171,106);
 // Tapered towers, capped with geometric fruits and stars.
 [[146,167,57],[229,86,60],[389,86,60],[477,167,57]].forEach(([x,y,w],i)=>{poly(`${x},650 ${x+8},${y+76} ${x+w/2},${y} ${x+w-8},${y+76} ${x+w},650`);for(let k=0;k<7;k++){const yy=y+95+k*(530-y)/7;arch(x+18,yy,w-36,39)}circle(x+w/2,y+6,17);star(x+w/2,y-15,18,5)});
 path('M101 738V511L172 473L236 507L340 369L444 507L511 473L579 511V738Z');
 poly('205,564 340,383 475,564');circle(340,526,43);circle(340,526,29);
 for(let i=0;i<10;i++){let a=i*Math.PI/5;poly(`340,526 ${340+Math.cos(a)*28},${526+Math.sin(a)*28} ${340+Math.cos(a+.6)*28},${526+Math.sin(a+.6)*28}`)}
 [145,285,425].forEach(x=>{arch(x,613,110,125);arch(x+18,634,74,104);star(x+55,591,21,6)});
 for(let i=0;i<11;i++){circle(112+i*46,554+(i%2)*23,13);poly(`${112+i*46},552 ${104+i*46},531 ${119+i*46},532`)}
}
if(id==='alhambra'){
 rect(6,188,668,395);rect(6,566,668,248);rect(6,188,668,31);
 for(let i=0;i<7;i++){let x=24+i*93;arch(x,271,73,295);arch(x+9,285,55,266);rect(x-7,262,8,304);rect(x-10,244,15,20);star(x+36,246,13,8)}
 for(let i=0;i<20;i++)rect(15+i*33,178,20,16);
 for(let y=0;y<3;y++)for(let x=0;x<16;x++){let xx=17+x*41,yy=223+y*14;poly(`${xx},${yy} ${xx+13},${yy-6} ${xx+26},${yy} ${xx+13},${yy+6}`)}
 // Pool and paths recede toward the arcade.
 poly('280,580 400,580 535,793 145,793');poly('294,592 386,592 501,779 179,779');
 for(let i=0;i<5;i++)path(`M${283-i*18} ${611+i*34}Q340 ${604+i*34} ${398+i*18} ${611+i*34}L${404+i*18} ${620+i*34}Q340 ${614+i*34} ${277-i*18} ${620+i*34}Z`);
 for(const x of [63,572]){rect(x+20,553,12,121);path(`M${x-12} 565Q${x-5} 490 ${x+26} 397Q${x+60} 490 ${x+66} 565Z`);rect(x,667,52,39);ellipse(x+26,666,26,9)}
 circle(340,103,35);star(340,103,20,8);
}
if(id==='madrid'){
 cloud(75,135,123);cloud(447,106,146);rect(6,692,668,122);
 rect(68,316,544,374);rect(43,345,106,345);rect(531,345,106,345);rect(251,286,178,404);poly('240,286 340,239 440,286');circle(340,267,15);rect(61,316,558,20);
 for(let row=0;row<4;row++)for(let col=0;col<15;col++){let x=79+col*35,y=365+row*73;if(col>=5&&col<=9&&row===3)continue;if(row===0)arch(x,y,19,38);else rect(x,y,19,36);rect(x-3,y+40,25,7)}
 for(let i=0;i<10;i++)rect(158+i*37,339,9,349);
 arch(285,585,110,105);arch(307,602,66,88);rect(253,558,175,15);
 for(let i=0;i<17;i++){rect(69+i*33,299,6,17);circle(72+i*33,294,5)}
 poly('284,691 396,691 495,814 185,814');
 [[90,748],[580,748]].forEach(([x,y])=>{ellipse(x,y,61,24);ellipse(x,y,46,14);circle(x,y-10,14);rect(x-4,y-53,8,33);ellipse(x,y-55,24,8)});
}
return svg;
}
return {catalog,draw};
})();

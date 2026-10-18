/* Original travel compositions guided by the family's reference pictures. */
'use strict';
(()=>{
const catalog=[
{id:'italy-collection',title:'이탈리아 건축 여행',by:'로마 · 피렌체 · 피사 · 베네치아',group:'이탈리아',level:'도전',note:'여러 도시의 건축물을 한 장에 모았어요. 창문과 돔의 색을 비교해 봐요.',story:'콜로세움, 피사의 사탑, 피렌체의 돔과 베네치아의 종탑을 새로 배치한 여행 도안이에요. 서로 다른 건축물에서 아치, 기둥, 돔을 찾아보세요.',url:'https://www.italia.it/'},
{id:'venice',title:'베네치아 운하의 풍경',by:'이탈리아 · 베네치아',group:'이탈리아',level:'도전',note:'곤돌라가 지나가는 운하, 다리와 둥근 돔을 함께 칠해요.',story:'베네치아의 운하와 아치 다리, 궁전과 성당을 한 장에 재구성했어요. 물결과 건물에 서로 다른 색을 써서 물의 도시를 완성해 보세요.',url:'https://www.italia.it/en/veneto/venice'},
{id:'milan',title:'밀라노 광장의 하루',by:'이탈리아 · 밀라노',group:'이탈리아',level:'도전',note:'갤러리아의 큰 아치와 두오모의 뾰족한 첨탑을 찾아봐요.',story:'밀라노의 갤러리아 입구와 두오모를 새로 구성한 광장 풍경이에요. 반복되는 창문과 작은 첨탑의 리듬을 느껴 보세요.',url:'https://www.duomomilano.it/'},
{id:'louvre',title:'루브르와 유리 피라미드',by:'프랑스 · 파리',group:'프랑스',level:'도전',note:'유리 피라미드의 조각마다 빛이 다른 색으로 비칠 수 있어요.',story:'루브르의 궁전 건물과 유리 피라미드에서 영감을 받은 새 도안이에요. 오래된 건물과 유리 구조물을 서로 다른 색감으로 표현해 보세요.',url:'https://www.louvre.fr/'},
{id:'paris-notebook',title:'파리 여행 수첩',by:'프랑스 · 파리',group:'프랑스',level:'보통',note:'에펠탑, 크루아상, 카페와 여행 가방을 나만의 색으로 꾸며요.',story:'파리를 떠올리게 하는 명소와 여행 소품을 새로 그려 모았어요. 지유가 여행 가방에 넣고 싶은 물건은 무엇인가요?',url:'https://parisjetaime.com/'},
{id:'royal-crest',title:'왕관과 백합 문장',by:'프랑스에서 영감을 받은 장식',group:'프랑스',level:'도전',note:'왕관의 보석, 백합과 월계수 잎을 대칭으로 꾸며 봐요.',story:'왕관, 장식 백합, 월계수와 리본을 결합한 상상 속 문장이에요. 실제 공식 문장을 그대로 옮긴 그림은 아니에요. 지유 왕국의 색을 정해 보세요.',url:'https://www.chateauversailles.fr/'},
{id:'italy-map',title:'지도 속 이탈리아 여행',by:'이탈리아 · 여행 지도',group:'이탈리아',level:'도전',note:'부츠 모양 지도를 따라 명소와 피자, 곤돌라를 찾아봐요.',story:'이탈리아의 모습을 단순화한 장식 지도에 여행 풍경과 음식을 함께 넣었어요. 정확한 축척의 지도 대신 여행을 상상하며 칠하는 그림이에요.',url:'https://www.italia.it/'}
];
window.RileyDesigns.catalog.push(...catalog);
const previous=window.RileyFineArt;
window.RileyFineArt=function(id,paint={},onPaint){
 if(!catalog.some(d=>d.id===id))return previous(id,paint,onPaint);
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('xmlns',ns);svg.setAttribute('viewBox','0 0 680 820');svg.setAttribute('role','img');svg.setAttribute('aria-label',catalog.find(d=>d.id===id).title+' 색칠 도안');let index=0,parent=svg;
 function element(tag,attrs,host=parent){const e=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);host.append(e);return e}
 function region(tag,attrs){const key='travel-'+index++,e=element(tag,{...attrs,fill:paint[key]||'#fffdf7',stroke:'#42443f','stroke-width':1.9,'stroke-linejoin':'round','stroke-linecap':'round','data-region':key});if(onPaint)e.addEventListener('click',()=>onPaint(e,key));return e}
 const P=d=>region('path',{d}),R=(x,y,w,h,rx=0)=>region('rect',{x,y,width:w,height:h,rx}),E=(cx,cy,rx,ry)=>region('ellipse',{cx,cy,rx,ry}),C=(x,y,r)=>E(x,y,r,r),Q=points=>region('polygon',{points});
 const L=(d,w=.95)=>element('path',{d,fill:'none',stroke:'#66685f','stroke-width':w,'pointer-events':'none','stroke-linecap':'round'});
 function group(x,y,s,fn,rot=0){const old=parent;parent=element('g',{transform:`translate(${x} ${y}) scale(${s}) rotate(${rot})`});fn();parent=old}
 function text(value,x,y,size=18){const e=element('text',{x,y,'font-family':'Georgia,serif','font-size':size,'letter-spacing':2,'text-anchor':'middle',fill:'#45483f','pointer-events':'none'});e.textContent=value;return e}
 function arch(x,y,w,h){P(`M${x} ${y+h}V${y+w/2}A${w/2} ${w/2} 0 0 1 ${x+w} ${y+w/2}V${y+h}Z`)}
 function point(x,y,w,h){P(`M${x} ${y+h}V${y+w*.6}Q${x+w*.08} ${y+w*.22} ${x+w/2} ${y}Q${x+w*.92} ${y+w*.22} ${x+w} ${y+w*.6}V${y+h}Z`)}
 function rose(x,y,r,n=10){C(x,y,r);C(x,y,r*.83);for(let k=0;k<n;k++){let a=k*2*Math.PI/n,b=a+2*Math.PI/n;P(`M${x} ${y}L${x+Math.cos(a)*r*.8} ${y+Math.sin(a)*r*.8}Q${x+Math.cos(a+.3)*r} ${y+Math.sin(a+.3)*r} ${x+Math.cos(b)*r*.8} ${y+Math.sin(b)*r*.8}Z`)}C(x,y,r*.19)}
 function leaf(x,y,s,a=0){const e=P(`M${x} ${y}Q${x-s*.7} ${y-s*.8} ${x} ${y-s*1.7}Q${x+s*.7} ${y-s*.8} ${x} ${y}Z`);e.setAttribute('transform',`rotate(${a} ${x} ${y})`);const l=L(`M${x} ${y}v${-s*1.5}`);l.setAttribute('transform',`rotate(${a} ${x} ${y})`)}
 function cloud(x,y,s){P(`M${x} ${y}C${x-18*s} ${y-17*s} ${x+3*s} ${y-38*s} ${x+19*s} ${y-29*s}C${x+29*s} ${y-61*s} ${x+67*s} ${y-49*s} ${x+69*s} ${y-25*s}C${x+96*s} ${y-34*s} ${x+111*s} ${y-7*s} ${x+101*s} ${y+4*s}H${x}Z`)}
 function star(x,y,r){Q(`${x},${y-r} ${x+r*.28},${y-r*.28} ${x+r},${y} ${x+r*.28},${y+r*.28} ${x},${y+r} ${x-r*.28},${y+r*.28} ${x-r},${y} ${x-r*.28},${y-r*.28}`)}
 function dome(w=180,h=125){P(`M0 ${h}Q4 35 ${w/2} 0Q${w-4} 35 ${w} ${h}Z`);for(let i=0;i<5;i++){const x=i*w/5;P(`M${w/2} 0Q${w*.23+i*w*.1} 37 ${x} ${h}H${x+w/5}Q${w*.33+i*w*.1} 37 ${w/2} 0Z`)}R(-5,h,w+10,10);R(w/2-13,-29,26,29);for(let i=0;i<3;i++)R(w/2-9+i*7,-24,4,21);P(`M${w/2-15} -29Q${w/2} -60 ${w/2+15} -29Z`);R(w/2-2,-64,4,17)}
 function tower(){R(0,0,92,321);R(-6,-12,104,12);Q('-4,-12 46,-91 96,-12');Q('10,-20 46,-75 80,-20');R(10,9,72,30);R(4,48,84,12);for(let i=0;i<4;i++)arch(10+i*19,65,14,44);R(-4,113,100,11);for(let i=0;i<4;i++)arch(10+i*19,131,14,35);for(let i=0;i<3;i++)R(17+i*24,182,10,115);R(-5,312,102,14);L('M46 -91v-24')}
 function pisa(){R(0,10,132,323);for(let row=0;row<6;row++){let y=20+row*47;E(66,y,72,12);for(let i=0;i<7;i++){const x=3+i*18;arch(x,y+8,13,33);R(x-2,y+6,3,38)}E(66,y+45,70,11)}R(19,-37,94,47);E(66,-37,50,10);for(let i=0;i<5;i++)arch(25+i*16,-25,11,30);E(66,328,75,13)}
 function colosseum(){P('M0 72Q178 10 360 60V226Q178 278 0 230Z');for(let row=0;row<3;row++){let y=86+row*53;P(`M0 ${y}Q180 ${y-58} 360 ${y-13}V${y-5}Q180 ${y-48} 0 ${y+8}Z`);for(let i=0;i<13;i++){let x=6+i*27,yy=y+8-31*Math.sin(i*Math.PI/13);arch(x,yy,18,36);R(x-3,yy,3,40)}}P('M0 73Q180 10 360 60V72Q180 23 0 86Z');for(let i=0;i<14;i++)R(3+i*25,64-28*Math.sin(i*Math.PI/14),15,8);P('M0 72L0 13L35 0L36 25L70 16L70 51L106 42L106 53Q49 56 0 72Z');for(let i=0;i<3;i++)arch(6+i*24,25-i*4,15,35)}
 function facade(w=240,h=200,cols=9){R(0,0,w,h);R(-5,-11,w+10,11);for(let row=0;row<3;row++){for(let i=0;i<cols;i++){const x=8+i*(w-14)/cols,y=17+row*(h-24)/3;arch(x,y,13,(h-24)/3-16);L(`M${x+6.5} ${y+8}v${(h-24)/3-24}`)}R(0,8+(row+1)*(h-24)/3,w,5)}for(let i=0;i<cols+1;i++){let x=3+i*(w-7)/cols;R(x,3,3,h-6);R(x-1,0,5,6)}L(`M0 ${h-8}H${w}`)}
 function gondola(){P('M0 48Q72 88 184 44L172 65Q84 107 9 68Z');P('M9 49L2 29L8 27L23 52Z');P('M169 50L184 18L189 19L181 45Z');P('M48 58Q65 26 92 52L99 72H42Z');R(110,30,3,57);L('M109 32L80 101',2);for(let i=0;i<4;i++)L(`M${30+i*34} 78q20 6 36 0`)}
 function fleur(x,y,s){group(x,y,s,()=>{P('M0 40C-4 17 -20 7 -11 -8C-6 -20 -3 -23 0 -30C3 -23 6 -20 11 -8C20 7 4 17 0 40Z');P('M-3 29C-21 21 -24 8 -36 12C-53 15 -48 42 -29 38C-40 27 -25 24 -13 40L-3 45Z');P('M3 29C21 21 24 8 36 12C53 15 48 42 29 38C40 27 25 24 13 40L3 45Z');R(-18,37,36,8,3);P('M-11 45L0 62L11 45Z')})}
 function crown(){P('M-84 8L-72 48Q0 69 72 48L84 8L49 22L25 -12L0 18L-25 -12L-49 22Z');E(0,49,72,12);for(const [x,y]of [[-84,5],[-25,-15],[25,-15],[84,5]])C(x,y,6);for(let i=-2;i<=2;i++)Q(`${i*24},37 ${i*24+6},44 ${i*24},51 ${i*24-6},44`);P('M-67 7Q0 -80 67 7L56 12Q0 -51 -56 12Z');R(-3,-55,6,30);R(-12,-48,24,6)}
 function pizza(){E(0,0,66,60);E(0,0,56,50);for(const [x,y]of [[-26,-20],[20,-28],[30,13],[-13,30],[-7,-2]]){E(x,y,10,8);L(`M${x-6} ${y-2}q6 -4 12 0`)}for(const [x,y]of [[-38,8],[9,16],[4,-31]])P(`M${x-5} ${y-4}q12 -13 17 0l-3 12h-10Z`);L('M0 0L43 -45M0 0L63 4')}
 function cup(){P('M-32 -14H32L25 25Q0 43 -25 25Z');E(0,-14,32,8);P('M32 -5C61 -14 61 22 29 22L29 13C45 15 47 0 32 3Z');E(0,36,47,9);L('M-13 -34q-10 -12 0 -24M5 -33q-10 -12 0 -24M20 -35q-10 -12 0 -24')}
 function croissant(){P('M-67 19C-63 -31 -24 -51 0 -33C24 -51 63 -31 67 19L44 32L28 9Q0 -4 -28 9L-44 32Z');for(const x of [-41,-20,0,20,41])P(`M${x-8} -23Q${x+4} -10 ${x+7} 15L${x-4} 19Q${x-3} -6 ${x-17} -17Z`)}
 function eiffel(){P('M-60 178Q-17 110 -5 -7H5Q17 110 60 178H35Q0 110 -35 178Z');R(-28,95,56,9);R(-17,40,34,7);R(-64,177,128,8);R(-3,-28,6,23);for(let i=0;i<7;i++){let y=51+i*17,w=16+i*5;L(`M${-w} ${y}l${w*2} 17M${w} ${y}l${-w*2} 17`)}arch(-21,142,42,36)}
 function heart(x,y,s){P(`M${x} ${y+s}C${x-s*2} ${y-s*.2} ${x-s} ${y-s*1.4} ${x} ${y-s*.5}C${x+s} ${y-s*1.4} ${x+s*2} ${y-s*.2} ${x} ${y+s}Z`)}
 function flourish(x,y,s,rot=0){group(x,y,s,()=>{P('M0 0C85 -2 48 -102 14 -65C-7 -43 44 -31 30 -57C57 -40 9 -11 6 0C65 6 82 65 44 74C16 82 10 43 33 42C18 65 60 72 54 46C51 23 18 12 0 0Z')},rot)}
 R(8,8,664,804,8);
 if(id==='italy-collection'){
 group(37,70,.88,()=>colosseum());group(447,104,.88,()=>pisa(),9);group(575,481,.57,()=>tower());
 group(53,493,1.03,()=>{dome(190,136);group(0,146,1,()=>facade(190,130,7))});
 // A separate Florence vignette, with facade below its segmented dome.
 group(297,466,1.08,()=>{dome(190,133);group(-7,143,1,()=>facade(204,151,7));rose(95,185,21);arch(75,232,40,62)});
 text('ITALIA',253,390,29);heart(367,116,25);for(const [x,y]of [[385,260],[220,406],[99,435],[592,384]])star(x,y,10);
 }
 if(id==='venice'){
 P('M8 669Q340 636 672 669V812H8Z');for(let i=0;i<7;i++)L(`M14 ${695+i*17}Q160 ${680+i*18} 303 ${697+i*17}T665 ${695+i*17}`);
 group(77,244,.72,()=>tower());group(221,269,1.05,()=>{dome(187,131);group(-32,143,1,()=>facade(251,189,10))});
 group(386,405,1.02,()=>{facade(238,217,8);for(let i=0;i<5;i++){group(i*48,0,.36,()=>dome(134,84));arch(i*48+4,30,40,63)}rose(120,124,21);arch(98,158,45,59)});
 // Rialto-inspired bridge in the foreground.
 P('M22 644Q172 498 346 640L346 686Q178 557 22 688Z');P('M17 629Q177 486 352 624L352 642Q177 507 17 649Z');
 for(let i=0;i<12;i++){const x=29+i*26,y=572+55*Math.pow((x-177)/160,2);arch(x,y,18,36)}
 group(153,702,1.32,()=>gondola());cloud(41,104,.8);cloud(481,109,1);text('VENEZIA',340,179,28);group(20,467,.62,()=>facade(81,202,3));for(const [x,y]of [[337,139],[156,204],[510,274]])star(x,y,8);
 }
 if(id==='milan'){
 // Duomo rises behind the large gallery entrance.
 group(361,135,.87,()=>{R(0,141,305,340);Q('-8,141 153,4 313,141');for(let i=0;i<11;i++){let x=6+i*28,yy=130-Math.sin(i*Math.PI/10)*102;point(x,yy,12,58);R(x+4,yy-27,4,29);for(let j=0;j<3;j++)point(x,yy+80+j*82,14,53)}rose(153,143,36);for(let i=0;i<7;i++)point(10+i*43,345,28,129);for(let i=0;i<16;i++){R(i*20,422,4,57);L(`M${i*20+2} 420v-12`)}});
 group(54,340,1.08,()=>{facade(421,245,15);R(123,-58,178,303);R(116,-71,192,13);R(111,-87,202,16);arch(140,-22,143,267);arch(150,-13,123,258);arch(162,0,99,245);for(let k=0;k<8;k++)L(`M${168+k*12} 18L${210} 89`);point(6,137,32,108);point(383,137,32,108);for(let row=0;row<3;row++)for(const x of [130,291])R(x,4+row*79,7,63);R(-5,233,431,12)});
 for(let i=0;i<6;i++)L(`M${21+i*128} 812L${246+i*39} 630`);for(let i=0;i<4;i++)L(`M8 ${677+i*38}H672`);
 group(359,685,.56,()=>{R(-37,56,74,17);R(-26,35,52,23);P('M-16 35L-22 -5L-9 -30L8 -28L25 -5L18 35Z');C(0,-43,13);P('M-11 -29L-26 -6L-34 9L-27 13L-8 -4Z');P('M8 -26L32 -42L39 -29L23 -7Z')});cloud(50,94,1.15);
 }
 if(id==='louvre'){
 // Mansard roofs and the central pavilion precede the faceted pyramid.
 group(39,353,1,()=>{facade(602,279,20);for(let i=0;i<3;i++)R(-5,57+i*84,612,7);R(202,-118,198,397);P('M206 -118Q217 -215 301 -226Q385 -215 396 -118Z');R(196,-120,210,12);Q('190,-91 301,-153 412,-91');for(let i=0;i<3;i++)arch(226+i*57,-70,34,75);for(let i=0;i<7;i++)windowClassic(208+i*28,37,18,56);for(const x of [209,384])R(x,-210,10,89);R(297,-261,6,33);C(300,-267,5);for(let i=0;i<18;i++){R(8+i*34,-13,7,13);Q(`${5+i*34},-13 ${12+i*34},-28 ${19+i*34},-13`)}P('M0 -22L35 -65H206V-22Z');P('M400 -22V-65H569L602 -22Z')});
 P('M70 729L340 387L617 729Z');
 // Tile the triangular front with truly separate closed glass panels.
 const n=9,left={x:70,y:729},right={x:617,y:729},top={x:340,y:387};
 function pt(i,j){return {x:top.x+(left.x-top.x)*i/n+(right.x-top.x)*j/n,y:top.y+(left.y-top.y)*i/n+(right.y-top.y)*j/n}}
 for(let i=0;i<n;i++)for(let j=0;j<n-i;j++){let a=pt(i,j),b=pt(i+1,j),c=pt(i,j+1);Q(`${a.x},${a.y} ${b.x},${b.y} ${c.x},${c.y}`);if(i+j<n-1){let d=pt(i+1,j+1);Q(`${b.x},${b.y} ${d.x},${d.y} ${c.x},${c.y}`)}}
 Q('48,740 70,729 617,729 640,740 613,754 73,754');L('M30 784L102 754M650 784L578 754');
 }
 if(id==='paris-notebook'){
 group(336,303,1.55,()=>eiffel());
 // A decorated suitcase and a café sign.
 group(440,111,1,()=>{R(0,0,160,111,15);R(8,8,144,95,10);P('M44 0V-17Q79 -38 114 -17V0H103V-11Q80 -25 55 -11V0Z');R(26,13,12,86,3);R(122,13,12,86,3);heart(78,46,16);star(77,86,12);C(18,18,4);C(142,94,4)});
 group(79,148,1,()=>{P('M0 0Q60 -20 121 0V64Q60 84 0 64Z');R(11,9,99,45,5);L('M-6 -18H131M5 -18v18M116 -18v18');rose(61,-24,14,6);text('CAFÉ',61,39,21)});
 group(102,344,.92,()=>{arch(0,0,112,138);arch(9,10,94,122);R(16,52,35,72);R(61,52,35,72);for(let i=0;i<4;i++)L(`M${22+i*22} 51v73`);R(-12,139,136,14);for(let i=0;i<6;i++)P(`M${-5+i*22} 139Q${5+i*22} 112 ${15+i*22} 139Z`);R(-14,155,140,45);for(let i=0;i<7;i++){R(-6+i*20,157,4,40);C(-4+i*20,177,6)}});
 group(548,376,.77,()=>{R(-31,-41,62,79,10);P('M-28 -40Q0 -79 28 -40Z');for(let i=0;i<8;i++)R(-36+i*10,-40,8,22,2);R(-40,39,80,8);L('M-13 -14V35M0 -14V35M13 -14V35')});
 group(133,606,.85,()=>croissant());group(381,633,.93,()=>cup());
 group(545,627,.95,()=>{P('M-20 -84H20L27 -55L24 36Q0 52 -24 36L-27 -55Z');R(-21,-94,42,13,3);P('M-24 -37Q0 -27 24 -37V12Q0 23 -24 12Z');fleur(0,-14,.34)});
 text('PARIS',335,219,34);
 // Artist's easel and small canvas.
 group(109,719,.72,()=>{R(0,-10,103,71);R(-9,63,121,7);Q('4,71 13,71 -4,126 -12,126');Q('90,71 99,71 115,126 107,126');P('M19 47L51 7L87 47Z');C(78,7,7);R(47,40,10,20)});
 group(481,755,.8,()=>{R(0,0,89,13,4);R(12,-19,78,13,4);R(-5,-37,92,13,4);L('M20 -34h54M28 -16h50M12 4h53')});
 group(282,76,.76,()=>{for(let i=0;i<3;i++){P(`M${-46+i*30} 10Q${-45+i*30} -16 ${-30+i*30} -30Q${-15+i*30} -16 ${-14+i*30} 10Z`);R(-45+i*30,10,29,8)}R(-50,20,104,10);R(-33,31,70,7);for(let i=0;i<5;i++)R(-28+i*13,40,5,12)});
 group(533,507,.9,()=>{P('M-44 0Q-27 -32 0 -20Q27 -32 44 0L35 13H-35Z');E(-22,1,19,15);E(22,1,19,15);R(-5,-3,10,5);L('M-43 -3l-13 -10M43 -3l13 -10')});
 group(243,717,.8,()=>{P('M-22 0Q-35 -32 -12 -41Q0 -52 12 -41Q35 -32 22 0L12 37H-12Z');for(let i=0;i<4;i++)L(`M${-15+i*10} 7l${12-i*6} 28`)});
 for(const [x,y,s]of [[252,125,16],[58,509,14],[615,506,12],[433,530,11],[279,747,14]])heart(x,y,s);
 for(const [x,y,s,a]of [[212,239,.46,10],[473,272,.38,170],[224,584,.43,-10],[449,736,.36,90]])flourish(x,y,s,a);
 }
 if(id==='royal-crest'){
 // Original ornamental crest: three fleurs, crown, ribbon and laurel branches.
 E(340,416,157,169);E(340,416,142,153);fleur(283,373,.8);fleur(397,373,.8);fleur(340,480,.85);
 group(340,160,1.24,()=>crown());
 for(const side of [-1,1]){
 P(`M${340+side*126} 574Q${340+side*270} 431 ${340+side*194} 248L${340+side*185} 246Q${340+side*253} 432 ${340+side*116} 578Z`);
 for(let j=0;j<9;j++){const t=j/8,y=550-t*280,x=340+side*(150+64*Math.sin(t*Math.PI*.9));leaf(x,y,24,side*(45-t*28));leaf(x+side*7,y-6,27,-side*(42+t*20))}
 group(340+side*193,604,.78,()=>flourish(0,0,1,side<0?160:20));
 }
 P('M175 621Q340 684 505 621L480 672Q340 724 200 672Z');P('M175 621L118 635L150 655L115 682L200 672Z');P('M505 621L562 635L530 655L565 682L480 672Z');
 P('M324 659C270 596 245 672 309 681Q340 682 356 731L367 709Q361 677 324 659Z');P('M356 658C406 603 440 673 376 685Q355 694 350 744L330 726Q334 679 356 658Z');C(340,665,13);
 for(const side of [-1,1]){flourish(340+side*209,378,.63,side<0?180:0);flourish(340+side*183,526,.58,side<0?190:-10)}
 for(const [x,y]of [[119,184],[558,191],[108,729],[577,731]])star(x,y,12);
 }
 if(id==='italy-map'){
 // Decorative outline: stylised peninsula, Sicily and Sardinia, not a scale map.
 P('M214 83L260 52L297 74L329 63L366 87L392 76L428 111L455 129L448 161L415 176L408 210L428 252L462 292L467 328L499 357L514 392L548 421L580 440L600 463L572 480L540 467L520 478L526 508L508 531L512 557L487 570L463 551L454 518L421 490L405 454L374 426L360 390L339 359L320 332L309 300L286 278L269 246L249 224L221 212L199 189L178 181L177 157L194 142L183 121L199 108Z');
 P('M455 584L480 570L496 587L479 609L465 642L437 659L406 649L388 629L411 608Z');P('M189 382L204 402L205 449L190 477L169 469L158 442L162 412Z');
 // A route travels through iconic buildings inside and alongside the peninsula.
 text('ITALIA',335,749,27);text('MILANO',279,92,12);text('VENEZIA',408,242,12);text('ROMA',430,442,12);
 group(225,106,.48,()=>{point(0,0,113,94);rose(55,38,19);for(let i=0;i<6;i++){R(i*21,-25+i%2*11,4,30);point(i*21-4,-43+i%2*11,12,20)}});
 group(336,173,.52,()=>gondola());
 group(222,252,.39,()=>pisa(),8);
 group(334,330,.43,()=>colosseum());
 group(463,474,.41,()=>{P('M-49 60Q0 -72 49 60Z');P('M-15 -5L-5 16L6 7L17 23L26 1Z');P('M-7 -11Q-29 -24 -13 -40Q5 -51 14 -36Q34 -43 36 -23Q33 -3 15 -8Z')});
 group(397,611,.43,()=>pizza());
 group(112,659,.87,()=>cup());group(560,670,.8,()=>croissant());
 group(96,161,.67,()=>{E(0,0,41,13);for(let j=0;j<5;j++){P(`M${-35+j*17} 0Q${-25+j*17} -68 ${-9+j*17} 0Z`)}R(-27,16,54,8);R(-21,24,42,25)});
 group(577,554,.75,()=>{C(0,0,37);C(0,0,25);for(let i=0;i<12;i++){let a=i*Math.PI/6;Q(`${Math.cos(a)*40},${Math.sin(a)*40} ${Math.cos(a+.12)*52},${Math.sin(a+.12)*52} ${Math.cos(a+.25)*40},${Math.sin(a+.25)*40}`)}C(-10,-2,3);C(10,-2,3);L('M-11 11q11 14 22 0')});
 for(const [x,y]of [[105,579],[537,159]]){P(`M${x-23} ${y}Q${x} ${y-26} ${x+23} ${y}L${x+37} ${y-12}V${y+12}L${x+23} ${y}Q${x} ${y+26} ${x-23} ${y}Z`);C(x-10,y-2,3)}
 // Grapes and olive branches complete the travel scrapbook.
 for(let row=0;row<4;row++)for(let col=0;col<4-row;col++)C(80+col*16+row*8,277+row*15,9);leaf(100,266,23,40);leaf(100,266,23,-45);
 for(const [x,y,a]of [[580,230,35],[595,271,-35],[577,308,42],[568,349,-38]]){leaf(x,y,23,a);E(x+15,y+2,8,12)}L('M567 365Q616 281 573 186');
 for(const [x,y,s,a]of [[78,134,.5,30],[521,106,.5,180],[106,520,.5,-25],[531,761,.4,180]])flourish(x,y,s,a);
 }
 return svg;
 function windowClassic(x,y,w,h){R(x-3,y-4,w+6,h+9);arch(x,y,w,h);L(`M${x+w/2} ${y+5}V${y+h}M${x} ${y+h*.6}h${w}`);R(x-5,y+h+5,w+10,4)}
};
})();

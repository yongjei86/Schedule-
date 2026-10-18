/* Refined, closed-region ink drawings. Coordinates are deterministic for saved art. */
'use strict';
window.RileyFineArt=function(id,paint={},onPaint){
const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('xmlns',ns);svg.setAttribute('viewBox','0 0 680 820');svg.setAttribute('role','img');svg.setAttribute('aria-label',window.RileyDesigns.catalog.find(d=>d.id===id).title+' 색칠 도안');let index=0;
function add(tag,attrs,parent=svg){const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));parent.append(e);return e}
function region(tag,attrs){const key='fine-'+index++,e=add(tag,{...attrs,fill:paint[key]||'#fffdf7',stroke:'#46453d','stroke-width':1.35,'stroke-linejoin':'round','stroke-linecap':'round','data-region':key});if(onPaint)e.addEventListener('click',()=>onPaint(e,key));return e}
const P=d=>region('path',{d}),R=(x,y,w,h,rx=0)=>region('rect',{x,y,width:w,height:h,rx}),E=(cx,cy,rx,ry)=>region('ellipse',{cx,cy,rx,ry}),C=(x,y,r)=>E(x,y,r,r),Q=points=>region('polygon',{points});
const L=(d,w=.65)=>add('path',{d,fill:'none',stroke:'#6b685c','stroke-width':w,'stroke-linecap':'round','pointer-events':'none'});
const arch=(x,y,w,h)=>P(`M${x} ${y+h}V${y+w*.5}Q${x} ${y} ${x+w*.5} ${y}Q${x+w} ${y} ${x+w} ${y+w*.5}V${y+h}Z`);
function pointed(x,y,w,h){P(`M${x} ${y+h}V${y+w*.62}Q${x+w*.06} ${y+w*.24} ${x+w/2} ${y}Q${x+w*.94} ${y+w*.24} ${x+w} ${y+w*.62}V${y+h}Z`)}
function rosette(x,y,r,n=12){C(x,y,r);C(x,y,r*.85);for(let i=0;i<n;i++){const a=i*2*Math.PI/n,b=a+Math.PI/n;P(`M${x} ${y}Q${x+Math.cos(a)*r*.7} ${y+Math.sin(a)*r*.7} ${x+Math.cos(b)*r*.8} ${y+Math.sin(b)*r*.8}Q${x+Math.cos(a+.5)*r*.3} ${y+Math.sin(a+.5)*r*.3} ${x} ${y}Z`)}C(x,y,r*.16)}
function leaf(x,y,s,a=0){const e=P(`M${x} ${y}Q${x-s*.8} ${y-s*.8} ${x} ${y-s*1.8}Q${x+s*.7} ${y-s*.8} ${x} ${y}Z`);e.setAttribute('transform',`rotate(${a} ${x} ${y})`);const line=L(`M${x} ${y}Q${x+s*.12} ${y-s*.7} ${x} ${y-s*1.6}`);line.setAttribute('transform',`rotate(${a} ${x} ${y})`)}
function clouds(){for(const [x,y,s] of [[74,124,1],[477,86,.85]]){P(`M${x} ${y}C${x-24*s} ${y-5} ${x-22*s} ${y-34*s} ${x+4*s} ${y-31*s}C${x+13*s} ${y-71*s} ${x+53*s} ${y-65*s} ${x+64*s} ${y-35*s}C${x+90*s} ${y-54*s} ${x+112*s} ${y-31*s} ${x+109*s} ${y-13*s}C${x+149*s} ${y-18*s} ${x+143*s} ${y+12*s} ${x+119*s} ${y+12*s}H${x}Z`)}}
function house(x,y,w,h){R(x,y,w,h);Q(`${x-4},${y} ${x+w*.47},${y-w*.5} ${x+w+5},${y}`);L(`M${x+4} ${y-4}L${x+w*.47} ${y-w*.43}L${x+w-2} ${y-4}`);R(x+w*.4,y+h*.55,w*.23,h*.45);for(const dx of [.12,.7]){R(x+w*dx,y+9,w*.18,h*.23);L(`M${x+w*(dx+.09)} ${y+9}v${h*.23}`)}}
function ground(y=705){P(`M6 ${y}Q340 ${y-37} 674 ${y}V814H6Z`);for(let i=0;i<8;i++)L(`M${20+i*83} 814L${160+i*48} ${y}`);for(let i=0;i<4;i++)L(`M6 ${y+20+i*23}Q340 ${y-9+i*30} 674 ${y+20+i*23}`)}
function windowClassic(x,y,w,h){R(x-3,y-4,w+6,h+10);arch(x,y,w,h);L(`M${x+w/2} ${y+5}V${y+h}M${x} ${y+h*.55}h${w}`);R(x-5,y+h+6,w+10,4)}
function lotus(x,y,s){P(`M${x} ${y}Q${x-s} ${y-s*.7} ${x-s*.95} ${y-s*1.1}Q${x-s*.12} ${y-s*.95} ${x} ${y}Z`);P(`M${x} ${y}Q${x+s} ${y-s*.7} ${x+s*.95} ${y-s*1.1}Q${x+s*.12} ${y-s*.95} ${x} ${y}Z`);P(`M${x} ${y}Q${x-s*.65} ${y-s} ${x} ${y-s*1.9}Q${x+s*.65} ${y-s} ${x} ${y}Z`);P(`M${x} ${y}Q${x-s*1.1} ${y-s*.1} ${x-s*1.25} ${y-s*.55}Q${x-s*.35} ${y-s*.65} ${x} ${y}Z`);P(`M${x} ${y}Q${x+s*1.1} ${y-s*.1} ${x+s*1.25} ${y-s*.55}Q${x+s*.35} ${y-s*.65} ${x} ${y}Z`);E(x,y, s*.3,s*.12)}
R(6,6,668,808);
if(id==='starry'){
 P('M6 558Q85 488 144 505T278 496Q375 409 466 460Q570 398 674 477V814H6Z');P('M6 607Q157 520 279 553T483 527T674 512V814H6Z');
 // Sweeping bands curve around two large spiral currents.
 P('M8 288C139 205 214 386 352 293C473 212 516 293 670 212L670 245C520 326 461 247 361 324C208 429 124 240 8 328Z');
 P('M172 222C186 94 393 80 437 197C466 280 371 335 304 297C248 265 260 197 309 184C354 173 391 207 371 239C359 259 330 258 321 242C357 246 358 218 334 213C301 207 286 248 320 268C370 297 429 252 410 204C375 117 219 138 204 228Z');
 P('M379 348C416 300 510 312 525 365C543 422 470 448 445 411C424 378 466 357 481 382C456 373 453 398 471 402C497 408 511 378 488 359C461 337 416 348 405 370Z');
 [[81,168,24],[176,80,19],[315,90,20],[479,142,24],[589,326,18],[573,90,37],[255,406,15]].forEach(([x,y,r])=>{C(x,y,r*1.42);C(x,y,r);C(x,y,r*.52);for(let k=0;k<12;k++){let a=k*Math.PI/6;L(`M${x+Math.cos(a)*r*1.7} ${y+Math.sin(a)*r*1.7}l${Math.cos(a)*7} ${Math.sin(a)*7}`)}});
 P('M594 56C564 64 558 113 592 128C564 142 532 119 533 92C533 67 565 46 594 56Z');
 for(let k=0;k<17;k++){let x=17+k*39,y=380+Math.sin(k*.75)*43;L(`M${x} ${y}q12 -9 28 -3M${x+6} ${y+12}q10 -6 22 -2`)}
 for(let row=0;row<3;row++)for(let i=0;i<7;i++){const x=190+i*63+(row%2)*15,y=580+row*67+(i%3)*8;house(x,y,48,54)}
 R(385,513,40,122);Q('378,513 405,440 432,513');pointed(397,537,15,35);R(400,615,12,20);
 P('M59 814C68 727 35 678 61 625C82 583 45 548 79 501C95 476 81 446 100 405C113 376 105 351 131 307C123 360 149 379 138 415C164 463 146 478 170 523C184 550 160 579 185 611C204 652 179 678 207 724L231 814Z');
 for(let k=0;k<8;k++){let x=79+k*14;L(`M${x} 797C${x+24} 706 ${x-22} 651 ${x+11} 569Q${x-6} 507 ${x+8} ${410+k*20}`)}
}
if(id==='cezanne'){
 P('M6 493L674 440V814H6Z');P('M69 439C186 387 261 445 314 436L585 738C492 783 411 725 345 751L173 808L40 735Z');
 for(let i=0;i<9;i++)L(`M${83+i*34} ${466-i*2}C${92+i*49} 533 ${56+i*51} 643 ${122+i*47} ${750-i*6}`);
 P('M435 233C447 221 486 221 498 235L498 286C516 308 544 338 543 395L535 469C517 503 415 503 396 469L390 397C388 344 419 309 432 286Z');E(465,232,34,10);E(465,232,23,5);P('M507 293C589 273 610 385 548 424L539 398C579 366 562 314 518 319Z');P('M437 261Q466 271 495 259L495 276Q466 289 433 279Z');P('M403 416Q465 440 541 413L538 438Q466 463 398 438Z');L('M420 322Q397 368 412 401M517 335Q530 361 525 390');
 E(325,595,228,55);E(325,586,208,40);L('M131 600Q327 666 521 596');
 const apples=[[188,541,49],[284,510,51],[377,537,48],[456,576,44],[243,621,46],[115,700,47],[520,681,45]];
 apples.forEach(([x,y,s],i)=>{P(`M${x} ${y-s*.76}C${x-s*.5} ${y-s*1.1} ${x-s*1.12} ${y-s*.6} ${x-s} ${y+s*.1}C${x-s*.85} ${y+s*.9} ${x-s*.27} ${y+s} ${x} ${y+s*.88}C${x+s*.38} ${y+s} ${x+s*.91} ${y+s*.72} ${x+s} ${y}C${x+s*1.1} ${y-s*.6} ${x+s*.44} ${y-s*1.08} ${x} ${y-s*.76}Z`);P(`M${x+18} ${y-s*.64}Q${x+s*.9} ${y-s*.21} ${x+s*.49} ${y+s*.56}Q${x+s*.23} ${y+s*.79} ${x+10} ${y+s*.7}Q${x+s*.45} ${y+s*.08} ${x+18} ${y-s*.64}Z`);P(`M${x-2} ${y-s*.68}Q${x-9} ${y-s*1.02} ${x+9} ${y-s*1.12}L${x+14} ${y-s*1.04}Q${x+2} ${y-s*.85} ${x+4} ${y-s*.68}Z`);L(`M${x-s*.64} ${y-s*.22}q-9 18 0 32`)});
 P('M76 485L144 485L138 545Q110 563 83 543Z');E(110,485,34,10);E(110,485,25,5);P('M145 492C183 480 191 533 143 536L144 524C172 520 169 501 145 506Z');
}
if(id==='monet'){
 // Willow curtains, banks, arched bridge and reflected currents.
 P('M6 272Q153 193 329 251T674 237V814H6Z');
 for(let side=0;side<2;side++)for(let i=0;i<7;i++){const x=side?450+i*29:10+i*27;P(`M${x} 6Q${x+26} 99 ${x-15} 225Q${x-22} 279 ${x+4} 325Q${x-39} 284 ${x-30} 224Q${x+8} 100 ${x-12} 6Z`);for(let j=0;j<8;j++)L(`M${x-5+Math.sin(j)*9} ${25+j*28}q-18 12 -17 32`)}
 P('M6 428Q330 177 674 416L674 442Q330 214 6 455Z');
 P('M6 365Q330 106 674 353L674 373Q330 136 6 386Z');
 for(let i=0;i<20;i++){const x=12+i*34,y=238+135*Math.pow((x-340)/340,2);P(`M${x} ${y}L${x+8} ${y-5}V${y+80}L${x} ${y+87}Z`)}
 P('M6 401Q330 151 674 391L674 408Q330 177 6 424Z');
 for(let i=0;i<12;i++){const y=460+i*28;L(`M${10+(i%3)*25} ${y}Q175 ${y-17} 301 ${y+2}T${651-(i%2)*30} ${y-6}`)}
 [[130,489,40],[463,482,37],[277,559,48],[543,596,42],[120,648,51],[365,682,56],[542,747,54],[230,773,43]].forEach(([x,y,s])=>{P(`M${x} ${y}L${x+s} ${y-11}C${x+s*1.4} ${y+7} ${x+s*.8} ${y+28} ${x} ${y+25}C${x-s*1.5} ${y+23} ${x-s*1.2} ${y-21} ${x} ${y}Z`);L(`M${x} ${y}l${-s*.7} 10M${x} ${y}l${s*.7} 16`);lotus(x-3,y,s*.45)});
}
if(id==='chagall'){
 // A dream montage with a human profile, a goat, a violin and floating village.
 P('M6 356L337 57L674 315L443 814H6Z');C(347,435,209);P('M6 657Q132 565 268 634L439 814H6Z');
 for(let i=0;i<5;i++){const eStart=svg.children.length;house(150+i*81,179+(i%2)*40,63,92);if(i===3)for(let n=eStart;n<svg.children.length;n++)svg.children[n].setAttribute('transform','rotate(180 425 240)')}
 // Dreaming person's profile facing the animal.
 P('M674 814H455C440 768 445 682 439 641C427 622 412 612 409 598C426 597 431 584 424 571L408 554Q430 546 427 529C394 524 393 509 416 482L445 444C450 391 493 355 537 351C603 345 650 405 674 440Z');
 P('M674 439C611 369 531 366 477 398Q441 442 445 469C484 427 539 418 594 440L674 493Z');
 E(474,488,24,10);E(472,488,7,8);L('M442 476Q474 462 500 477M432 593Q455 602 479 591M446 640Q491 642 518 623');
 // Graceful goat profile.
 P('M6 388C48 359 84 356 126 369L172 413L225 430Q241 452 226 466L188 480L164 514Q137 528 126 512L111 468Q64 449 6 475Z');
 P('M99 376C86 344 81 311 103 282Q126 312 121 373Z');P('M126 377C147 337 164 320 188 320Q184 347 148 396Z');
 P('M70 367C59 325 67 280 96 260C78 301 95 335 96 367Z');P('M126 370C132 320 151 281 188 269C159 301 155 338 150 384Z');
 E(159,424,18,10);C(163,424,6);L('M145 408Q163 398 177 414M193 460q16 2 27 -7');P('M126 509Q144 539 150 574Q167 548 166 510Z');
 // Delicate violin suspended in the sky.
 const start=svg.children.length;P('M278 326C257 310 250 339 266 356C237 378 264 408 282 391L294 389C310 407 338 383 312 361C332 339 309 316 292 330Z');R(280,272,10,65);R(277,256,16,21,4);E(279,359,3,5);E(301,367,3,5);L('M284 279L289 382M287 279L293 382');Q('254,300 259,297 333,397 328,400');for(let i=start;i<svg.children.length;i++)svg.children[i].setAttribute('transform','rotate(22 290 340)');
 P('M300 814Q306 706 286 632L300 630Q332 714 326 814Z');
 for(const [x,y,a]of [[297,684,-45],[305,715,52],[293,638,-20],[317,758,65]])leaf(x,y,35,a);
 [[272,602],[321,635],[348,690],[265,727]].forEach(([x,y])=>{for(let k=0;k<6;k++){const a=k*Math.PI/3;E(x+Math.cos(a)*14,y+Math.sin(a)*14,10,7)}C(x,y,8)});
}
if(id==='colosseum'){
 clouds();ground(682);
 // Elliptical facade with perspective compression at the sides.
 P('M49 304Q328 208 632 302L632 658Q349 750 49 657Z');
 const edge=x=>Math.sin((x-49)/583*Math.PI);
 for(let row=0;row<4;row++){
 const y0=307+row*84;
 P(`M49 ${y0}Q337 ${y0-90} 632 ${y0-2}V${y0+12}Q337 ${y0-73} 49 ${y0+15}Z`);
 for(let j=0;j<17;j++){
 const a=j/17*Math.PI,b=(j+1)/17*Math.PI,x=49+583*(1-Math.cos(a))/2,x2=49+583*(1-Math.cos(b))/2,w=x2-x,y=y0+14-45*edge(x+w/2),h=55;
 if(w<9)continue;
 arch(x+3,y,w-7,h);L(`M${x+5} ${y+h}V${y+20}Q${x+w/2} ${y+2} ${x+w-6} ${y+20}V${y+h}`);
 if(w>20){R(x-1,y-2,5,h+9);R(x-3,y-4,10,5);L(`M${x+w/2} ${y+7}v8`)}
 }
 }
 P('M49 297Q333 199 632 296V311Q333 217 49 314Z');
 for(let i=0;i<21;i++){const x=54+i*27,y=285-45*edge(x);R(x,y,18,13);L(`M${x+3} ${y+3}h12`)}
 for(let i=0;i<13;i++){const x=69+i*44,y=647-43*edge(x);L(`M${x} ${y}v25M${x+8} ${y+20}h30`)}
 for(let i=0;i<18;i++){const x=67+i*31;L(`M${x} ${300-44*edge(x)}v-7`)}
}
if(id==='pisa'){
 clouds();ground(719);E(338,724,176,24);
 const start=svg.children.length;
 R(226,638,230,64);E(341,638,115,22);E(341,702,115,22);
 for(let i=0;i<8;i++)arch(237+i*27,653,18,40);
 for(let row=0;row<6;row++){
 const y=226+row*67;R(237,y,208,67);E(341,y+67,104,18);
 for(let col=0;col<9;col++){const a=col/9*Math.PI,b=(col+1)/9*Math.PI,x=237+208*(1-Math.cos(a))/2,w=104*(Math.cos(a)-Math.cos(b)),yy=y+8+9*Math.sin(a);if(w>8){arch(x+2,yy,w-4,43);R(x,yy,4,47);R(x-1,yy-3,7,4);L(`M${x+5} ${yy+42}v-22`)}}
 E(341,y,109,14);L(`M237 ${y+5}Q341 ${y+34} 445 ${y+5}`);
 }
 R(272,149,138,77);E(341,149,69,17);for(let i=0;i<6;i++)arch(280+i*21,166,14,41);E(341,224,73,14);E(341,144,76,10);L('M277 143Q341 117 405 143');
 for(let i=start;i<svg.children.length;i++)svg.children[i].setAttribute('transform','rotate(-6 341 716)');
}
if(id==='duomo'){
 clouds();ground(725);
 // Cathedral dome: eight curved structural ribs and terracotta courses.
 R(235,377,234,118);P('M235 377C234 278 276 204 351 166C425 209 469 281 469 377Z');
 for(let i=0;i<6;i++){const x1=235+i*39,x2=x1+39;P(`M351 166C${285+i*17} 231 ${247+i*32} 302 ${x1} 377L${x2} 377C${279+i*32} 300 ${303+i*17} 230 351 166Z`)}
 for(let i=0;i<9;i++){const y=213+i*18,dx=Math.sqrt(Math.max(0,(y-166)/211))*112;L(`M${351-dx} ${y}Q351 ${y+19} ${351+dx} ${y}`)}
 R(327,127,48,43);for(let i=0;i<3;i++)arch(332+i*14,132,9,27);E(351,125,28,8);Q('325,125 351,91 377,125');R(348,69,6,23);R(340,76,22,5);
 for(let i=0;i<8;i++){const x=242+i*28;R(x,389,18,50);arch(x+4,397,10,28)}
 // Campanile, with tiers, tracery and paired openings.
 R(526,272,72,453);R(520,264,84,15);for(let row=0;row<5;row++){const y=295+row*81;R(526,y,72,8);for(let j=0;j<2;j++){pointed(536+j*29,y+17,21,49);L(`M${546+j*29} ${y+25}v41`)}R(528,y+74,68,5)}
 for(let i=0;i<6;i++)R(525+i*13,251,7,12);
 // Marble front in three gabled bays.
 R(79,522,413,203);Q('69,522 170,422 262,512 334,384 505,522');
 Q('96,513 170,442 242,513');Q('275,513 334,410 475,513');
 R(90,535,391,12);R(90,701,391,13);
 arch(253,572,91,153);arch(265,581,67,144);pointed(127,598,60,127);pointed(403,598,60,127);
 rosette(301,518,39,12);rosette(170,529,21,10);rosette(431,529,21,10);
 for(const x of [94,203,237,355,382,476]){R(x,549,8,152);R(x-3,542,14,10);for(let i=0;i<6;i++)Q(`${x},${565+i*21} ${x+4},${558+i*21} ${x+8},${565+i*21} ${x+4},${572+i*21}`)}
 for(let i=0;i<12;i++){let x=101+i*31;Q(`${x},564 ${x+9},552 ${x+18},564 ${x+9},576`)}
 for(const x of [140,164,277,300,324,417,441])L(`M${x} 638v78`);
 for(const x of [111,211,372,465])for(let i=0;i<4;i++)R(x,597+i*26,9,16);
 L('M90 689H481M90 695H481');
}
if(id==='sagrada'){
 clouds();ground(738);
 const towers=[[117,221,63],[210,118,66],[395,118,66],[492,221,63]];
 towers.forEach(([x,y,w],i)=>{
 P(`M${x} 656L${x+8} ${y+98}Q${x+12} ${y+45} ${x+w/2} ${y}Q${x+w-12} ${y+45} ${x+w-8} ${y+98}L${x+w} 656Z`);
 for(let row=0;row<11;row++){const yy=y+100+row*(495-y)/11,ww=13+row*.8;pointed(x+w/2-ww/2,yy,ww,25);L(`M${x+9} ${yy+26}h${w-18}`)}
 C(x+w/2,y+2,19);rosette(x+w/2,y+2,12,6);P(`M${x+w/2-7} ${y-16}L${x+w/2} ${y-40}L${x+w/2+7} ${y-16}Z`);L(`M${x+12} ${y+91}L${x+7} 633M${x+w-12} ${y+91}L${x+w-7} 633`);
 });
 P('M90 738V543Q137 508 177 493L232 524Q267 473 302 429L340 369L379 431Q416 480 449 526L504 493Q550 511 590 543V738Z');
 P('M217 582Q275 460 340 402Q405 462 463 582Z');
 for(const [x,y,w,h]of [[116,602,114,136],[283,603,114,135],[449,602,114,136]]){pointed(x,y,w,h);pointed(x+12,y+20,w-24,h-20);pointed(x+23,y+39,w-46,h-39);L(`M${x+w/2} ${y+65}V${y+h}`)}
 rosette(340,548,41,14);
 for(let i=0;i<19;i++){const x=105+i*26,y=576+Math.sin(i*.9)*14;C(x,y,8);P(`M${x-5} ${y-9}Q${x} ${y-29} ${x+5} ${y-9}Z`)}
 for(let i=0;i<10;i++){const x=250+i*19,y=486+Math.abs(i-4.5)*12;leaf(x,y,12,(i%2?25:-25))}
 for(let i=0;i<15;i++){let x=102+i*34;L(`M${x} 726v-22M${x+6} 696l7 -12M${x+6} 590l8 -9`)}
}
if(id==='alhambra'){
 // A framed court: receding arcade, muqarnas and geometric tiles.
 R(6,159,668,431);R(6,159,668,30);for(let j=0;j<23;j++)R(10+j*29,151,18,9);
 R(6,200,668,71);for(let i=0;i<22;i++){const x=11+i*30;Q(`${x},214 ${x+12},204 ${x+24},214 ${x+12},224`);Q(`${x},244 ${x+12},232 ${x+24},244 ${x+12},256`)}
 for(let i=0;i<7;i++){const x=22+i*94;arch(x,281,73,309);arch(x+7,290,59,288);arch(x+13,300,47,274);
 for(let k=0;k<6;k++)L(`M${x+5+k*12} ${291+Math.abs(k-2.5)*5}l4 13l-4 9`);
 R(x-6,359,9,219);R(x-11,348,20,10);R(x-9,578,16,12);L(`M${x-2} 365V573`);
 for(let row=0;row<3;row++)for(let col=0;col<3;col++){const xx=x+8+col*22,yy=315+row*13;L(`M${xx} ${yy}l5 -5l5 5l-5 5Z`)}
 }
 P('M6 590H674V814H6Z');Q('255,590 425,590 557,814 123,814');Q('268,599 412,599 529,799 151,799');
 for(let i=0;i<6;i++){const y=621+i*29,dx=(y-599)*.58;P(`M${268-dx} ${y}Q340 ${y-12} ${412+dx} ${y}L${417+dx} ${y+7}Q340 ${y+2} ${263-dx} ${y+7}Z`)}
 for(const x of [47,584]){R(x+17,556,12,124);P(`M${x-12} 577Q${x-18} 536 ${x+2} 487Q${x+9} 438 ${x+23} 399Q${x+47} 463 ${x+46} 499Q${x+68} 546 ${x+57} 577Z`);for(let j=0;j<5;j++)L(`M${x+23} ${444+j*24}q-13 24 -19 47M${x+24} ${444+j*24}q13 24 19 47`);R(x-3,682,54,38);E(x+24,682,27,7)}
 for(let i=0;i<5;i++){L(`M6 ${627+i*37}H${236-i*22}M${445+i*22} ${627+i*37}H674`)}
}
if(id==='madrid'){
 clouds();ground(708);
 R(54,336,572,372);R(33,355,113,353);R(534,355,113,353);R(253,306,174,402);Q('243,306 340,260 437,306');
 for(const x of [33,253,534]){const w=x===253?174:113;R(x-5,344,w+10,10);R(x-3,330,w+6,7)}
 for(let row=0;row<4;row++)for(let col=0;col<16;col++){const x=47+col*37,y=381+row*72;if(row===3&&col>=6&&col<=9)continue;windowClassic(x,y,20,37);if(row===1)Q(`${x-5},${y-8} ${x+10},${y-20} ${x+25},${y-8}`)}
 for(let i=0;i<13;i++){const x=151+i*30;if(x>525)continue;R(x,358,6,340);R(x-3,354,12,7);R(x-2,693,10,8);L(`M${x+2} 365V689`)}
 arch(282,595,116,113);arch(295,606,90,102);arch(309,617,62,91);R(267,575,147,11);for(let i=0;i<11;i++)R(273+i*12,556,7,18);
 C(340,292,15);C(340,292,11);L('M340 284v9l6 3');
 for(let i=0;i<23;i++){const x=43+i*27;R(x,322,4,13);C(x+2,318,4)}
 for(const x of [214,458]){E(x,753,62,20);E(x,751,49,13);E(x,737,25,9);R(x-4,702,8,31);E(x,700,24,7);P(`M${x-3} 696Q${x-29} 674 ${x-39} 700Q${x-22} 681 ${x} 700Q${x+24} 676 ${x+39} 700Q${x+25} 668 ${x-3} 696Z`)}
}
if(id==='sunflowers'){
 P('M6 657Q340 639 674 657V814H6Z');
 const blooms=[[171,216,38,-25],[299,165,42,12],[438,231,40,23],[114,355,33,-20],[261,330,42,-8],[397,376,39,13],[538,388,31,37],[209,464,36,-28],[466,500,32,20],[347,460,30,5],[162,114,25,0]];
 blooms.forEach(([x,y,s],i)=>P(`M${x-3} ${y}Q${x+48} ${y+146} ${311+i*5} 668L${320+i*5} 668Q${x+58} ${y+145} ${x+4} ${y}Z`));
 [[199,534,36,-60],[427,547,39,53],[160,424,31,-50],[503,456,33,50],[270,582,28,-40]].forEach(v=>leaf(...v));
 blooms.forEach(([x,y,s,rot],j)=>{for(let i=0;i<19;i++){const a=i*360/19+rot,len=s*(1.1+.18*Math.sin(i*2+j));const e=P(`M${x-5} ${y-s+4}C${x-22} ${y-s-len*.35} ${x-14} ${y-s-len*.72} ${x+Math.sin(i)*7} ${y-s-len}C${x+17} ${y-s-len*.62} ${x+21} ${y-s-len*.21} ${x+5} ${y-s+4}Z`);e.setAttribute('transform',`rotate(${a} ${x} ${y})`)}C(x,y,s);C(x,y,s*.75);for(let k=0;k<28;k++){const a=k*2.4,rad=Math.sqrt(k/28)*s*.66;const e=E(x+Math.cos(a)*rad,y+Math.sin(a)*rad,2.3,3.4);e.setAttribute('pointer-events','none');e.removeAttribute('data-region');e.setAttribute('fill','none');}});
 P('M226 607Q340 582 454 607L438 650Q463 735 407 782Q341 802 274 782Q219 736 243 650Z');P('M237 675Q342 699 445 674L446 701Q342 727 235 701Z');E(340,607,114,16);E(340,607,102,9);L('M258 716Q263 755 284 768M424 712Q427 750 402 771');
}
return svg;
};

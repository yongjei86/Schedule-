"""Build aligned, editable SVG paper-doll assets for the princess dress-up game."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'static'/'princess'
PRINCESSES=[
 ('elsa','엘사','#eee2a8','#6aafd1','#8ed7ec','#429dc8','#ecfaff','눈꽃 드레스','분홍 꽃 드레스','보라 드레스'),
 ('anna','안나','#99502f','#59a28c','#4b8d69','#254a43','#e6efc5','초록 드레스','분홍 꽃 드레스','보라 진주 드레스'),
 ('rapunzel','라푼젤','#edc354','#6baf76','#b895dc','#8059ae','#f8dfed','보라 드레스','꽃 드레스','별빛 드레스'),
 ('ariel','인어공주','#c94438','#4c9dad','#77c9bd','#3b9d9a','#e1fcf3','바다 드레스','분홍 드레스','진주 드레스'),
 ('belle','벨','#6e422c','#8b9b58','#efcc62','#d29a32','#fff2b5','노란 드레스','분홍 꽃 드레스','보라 진주 드레스'),
 ('cinderella','신데렐라','#d8b455','#6ca9c9','#a6cee9','#76a9d0','#f6fbff','하늘빛 드레스','리본 드레스','진주 드레스'),
]

def flower(x,y,r=11,color='#efb6cd'):
 return f'<g transform="translate({x} {y})" fill="{color}" stroke="#bf8d9b" stroke-width="1.6">'+''.join(f'<ellipse rx="{r*.48}" ry="{r*.76}" transform="rotate({a}) translate(0 {-r*.65})"/>' for a in range(0,360,72))+f'<circle r="{r*.3}" fill="#f6df92"/></g>'

def defs(prefix,color,shade,light):
 return f'''<defs>
 <linearGradient id="{prefix}-dress" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{light}"/><stop offset=".42" stop-color="{color}"/><stop offset="1" stop-color="{shade}"/></linearGradient>
 <linearGradient id="{prefix}-hair" x2="1" y2=".8"><stop stop-color="#fff3cf"/><stop offset=".4" stop-color="{color}"/><stop offset="1" stop-color="{shade}"/></linearGradient>
 <radialGradient id="{prefix}-skin"><stop stop-color="#fff1df"/><stop offset="1" stop-color="#efc9b1"/></radialGradient>
 </defs>'''

def base(pid,hair,eye):
 outline='#795a58'
 s=defs(pid,hair,hair,'#fff7d7')
 s+=f'<g transform="translate(100 0)" stroke="{outline}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round">'
 if pid in ('rapunzel','ariel','belle'):
  s+=f'<path d="M222 97 Q175 158 189 334 Q151 444 183 591 Q147 688 211 720 Q248 735 265 694 L345 690 Q410 720 431 667 Q451 611 417 542 Q443 429 405 298 Q424 151 368 94Z" fill="{hair}"/>'
  s+=f'<path d="M214 280 Q197 404 216 510 T210 674 M396 274 Q422 389 397 505 T403 660" fill="none" stroke="#ffffff55" stroke-width="8"/>'
 elif pid=='anna':
  s+=f'<path d="M213 172 Q175 207 202 282 Q177 312 205 344 Q183 375 208 402 Q183 423 218 444 L240 416 Q215 395 240 367 Q220 344 240 318 Q217 290 239 264 L245 188 M367 175 Q414 210 388 282 Q412 312 388 341 Q412 370 386 400 Q412 422 378 442 L357 416 Q381 392 360 370 Q380 344 360 319 Q383 287 362 266 L357 188Z" fill="{hair}"/>'
 elif pid in ('elsa','cinderella'):
  if pid=='cinderella':s+=f'<ellipse cx="300" cy="70" rx="65" ry="47" fill="{hair}"/>'
  else:s+=f'<path d="M368 210 Q408 237 378 265 Q416 294 380 318 Q416 344 380 367 Q408 394 373 420 L355 394 Q377 373 353 351 Q375 326 352 302 Q372 281 350 257Z" fill="{hair}"/>'
 # The base stays fully dressed when an overlay is removed.
 s+='<path d="M271 232 L268 282 Q300 308 332 282 L329 232" fill="#f6d9c2"/>'
 s+='<path d="M229 292 Q206 322 190 383 L181 414 Q180 428 193 432 Q206 434 213 418 L248 337 M371 292 Q394 322 410 383 L419 414 Q421 428 407 432 Q393 434 386 417 L353 337" fill="#f5d9c1"/>'
 s+='<path d="M266 732 L263 758 Q266 775 288 769 L299 734 M308 733 L311 759 Q317 774 338 767 L333 731" fill="#f6d9c2"/>'
 s+='<path d="M263 753 Q278 763 290 752 L288 770 Q267 779 261 767Z M310 754 Q325 763 338 751 L341 768 Q319 778 312 767Z" fill="#eee4f3"/>'
 s+='<path d="M236 280 Q267 268 300 283 Q332 268 364 280 L344 386 Q361 479 425 728 Q299 758 174 728 Q241 474 256 386Z" fill="#fff5ed"/>'
 s+='<path d="M248 384 Q298 407 351 384 M243 462 Q220 629 205 713 M300 418 L300 735 M356 466 Q379 639 398 715" fill="none" stroke="#e7d3d6" stroke-width="3"/>'
 s+=f'<ellipse cx="300" cy="158" rx="94" ry="109" fill="url(#{pid}-skin)"/>'
 s+=f'<path d="M207 159 Q184 67 242 43 Q309 9 366 62 Q410 92 393 165 L378 164 Q370 96 340 84 Q292 148 219 126 L219 171Z" fill="{hair}"/>'
 if pid=='elsa':s+=f'<path d="M218 112 Q278 86 295 47 Q332 60 354 82 Q305 112 246 122" fill="none" stroke="#fffae555" stroke-width="7"/>'
 elif pid=='ariel':s+=f'<path d="M216 117 Q250 47 320 57 Q365 68 361 110 Q300 89 248 137" fill="{hair}"/>'
 elif pid=='belle':s+=f'<path d="M218 120 Q243 47 301 63 Q335 51 377 113 Q323 80 300 94 Q263 135 218 139" fill="{hair}"/>'
 elif pid=='anna':s+=f'<path d="M219 107 Q254 61 296 73 M303 72 Q353 64 383 120" fill="none" stroke="#e9b27c" stroke-width="6"/>'
 # Two detailed eyes, lashes, brows and softly shaded lips.
 for x in (265,335):
  s+=f'<path d="M{x-21} 164 Q{x} 149 {x+21} 165 Q{x+16} 193 {x} 194 Q{x-19} 191 {x-21} 164Z" fill="white"/>'
  s+=f'<ellipse cx="{x}" cy="175" rx="14" ry="19" fill="{eye}" stroke="#56636a" stroke-width="2"/><ellipse cx="{x}" cy="177" rx="7" ry="13" fill="#293442" stroke="none"/><ellipse cx="{x-4}" cy="167" rx="4" ry="6" fill="white" stroke="none"/>'
  s+=f'<path d="M{x-21} 163 Q{x} 149 {x+22} 164 M{x-19} 162 L{x-25} 155 M{x-15} 146 Q{x} 137 {x+15} 146" fill="none" stroke-width="3.5"/>'
 s+='<ellipse cx="237" cy="202" rx="17" ry="8" fill="#eda9aa" opacity=".45" stroke="none"/><ellipse cx="362" cy="202" rx="17" ry="8" fill="#eda9aa" opacity=".45" stroke="none"/><path d="M297 191 Q290 207 303 207" fill="none" stroke="#cc9c89" stroke-width="2"/><path d="M280 224 Q300 238 321 223 Q302 247 280 224Z" fill="#cd798b" stroke="#b56c7e" stroke-width="1.8"/>'
 if pid=='anna':s+='<g fill="#b98066" stroke="none">'+''.join(f'<circle cx="{x}" cy="{y}" r="1.5"/>' for x,y in [(237,191),(245,194),(252,193),(348,193),(357,194),(365,190)])+'</g>'
 if pid=='rapunzel':s+=flower(204,300,12)+flower(404,430,12,'#d9c4f0')+flower(203,588,13,'#edc5da')
 s+='</g>'
 return s

def dress(pid,color,shade,light,variant):
 pre=f'{pid}-{variant}'
 if variant==1:color,shade,light='#efb6d0','#c584af','#fff0f6'
 if variant==2:color,shade,light='#c9b9e3','#9b83c2','#f9f0ff'
 s=defs(pre,color,shade,light)+f'<g transform="translate(100 0)" stroke="#876876" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
 s+=f'<path d="M239 280 Q268 271 300 285 Q331 271 363 280 Q384 288 389 317 L365 333 L348 311 L345 385 Q360 447 405 551 Q442 645 477 725 Q302 761 124 725 Q162 635 195 551 Q241 446 255 385 L251 310 L233 333 L211 316 Q214 288 239 280Z" fill="url(#{pre}-dress)"/>'
 s+=f'<path d="M255 385 Q300 400 345 385 L351 404 Q301 417 249 403Z" fill="{shade}" stroke-width="2"/>'
 s+=f'<path d="M262 290 Q300 309 339 289 M274 313 L284 374 M324 312 L316 374" fill="none" stroke="{light}" stroke-width="4"/>'
 s+=f'<path d="M250 413 Q219 568 164 711 M279 419 Q264 584 248 737 M319 421 Q333 602 352 738 M348 414 Q391 587 438 716" fill="none" stroke="{shade}" stroke-width="4" opacity=".45"/>'
 s+=f'<path d="M136 713 Q299 746 465 713" fill="none" stroke="{light}" stroke-width="9" opacity=".8"/>'
 if variant==1:
  for x,y in [(223,505),(362,535),(185,650),(414,668),(284,629)]:s+=flower(x,y,13)
  s+=f'<path d="M299 396 Q265 376 263 397 Q267 418 299 401 Q335 380 337 399 Q334 417 302 401 L311 447 L300 437 L286 451Z" fill="{light}"/>'
 elif pid in ('elsa','cinderella'):
  for x,y in [(214,535),(369,558),(180,676),(412,678),(295,605)]:
   s+=f'<path d="M{x-12} {y} H{x+12} M{x} {y-12} V{y+12} M{x-8} {y-8} L{x+8} {y+8} M{x-8} {y+8} L{x+8} {y-8}" stroke="#fff9ff" stroke-width="2.6"/>'
 elif pid=='belle':
  s+=f'<path d="M188 565 Q245 624 300 568 Q360 626 411 564" fill="none" stroke="{light}" stroke-width="12"/>'
  for x,y in [(192,565),(300,575),(410,565)]:s+=flower(x,y,15,'#ecc07a')
 elif pid=='anna':
  s+='<g fill="#e9c96f" stroke="#71866d" stroke-width="2">'+''.join(f'<path d="M{x} {y} q-20 -30 -22 0 q10 21 22 35 q25 -30 23 -39 q-6 -21 -23 4Z"/>' for x,y in [(207,607),(300,649),(390,607)])+'</g>'
 elif pid=='rapunzel':
  s+=f'<path d="M281 313 L318 329 L283 345 L316 362 L286 374" fill="none" stroke="{light}" stroke-width="3"/>'
 elif pid=='ariel':
  for x,y in [(194,643),(301,690),(408,643)]:s+=f'<path d="M{x-23} {y} Q{x-32} {y-34} {x} {y-47} Q{x+34} {y-34} {x+23} {y}Z M{x} {y-42} V{y-3}" fill="#e1f8ec" stroke="#80bab5" stroke-width="2"/>'
 if variant==2:
  s+='<g fill="#fffef8" stroke="#d9c7df" stroke-width="1">'+''.join(f'<circle cx="{x}" cy="{y}" r="5"/>' for x,y in [(215,586),(274,535),(346,580),(397,646),(239,689),(308,708)])+'</g>'
 s+='</g>'
 return s

def crown(pid,variant):
 color='#c9e4f4' if pid in ('elsa','cinderella') else '#f2d487'
 s='<g stroke="#9e7f76" stroke-width="3" stroke-linejoin="round">'
 if variant==0:
  s+=f'<path d="M321 106 L317 64 L351 79 L369 37 L400 70 L431 37 L448 79 L482 64 L477 106Z" fill="{color}"/>'
  for x,y in [(319,63),(369,37),(431,37),(481,63)]:s+=f'<circle cx="{x}" cy="{y}" r="6" fill="#fff2c2"/>'
  s+='<path d="M400 69 L410 83 L400 98 L390 83Z" fill="#ba92d4"/><path d="M326 101 Q400 112 473 101" fill="none" stroke="#fff4cd" stroke-width="5"/>'
 else:
  s+='<path d="M320 105 Q400 37 480 105" fill="none" stroke="#eac594" stroke-width="11"/>'
  for x,y in [(336,91),(365,75),(400,68),(435,75),(466,91)]:s+=flower(x,y,14,'#e9c6df')
 return s+'</g>'

def prop(pid,variant):
 s='<g stroke="#8d737c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
 if variant==2:
  s+='<path d="M570 500 L545 418 L601 404 L630 493 L607 532Z" fill="#e1e9ce"/><path d="M558 451 L608 436 M568 467 L615 454" stroke="#b0c299"/>'
  for x,y,c in [(554,399,'#e7b7d8'),(584,385,'#c3d8eb'),(611,399,'#efdf9b')]:s+=flower(x,y,24,c)
  s+='<path d="M594 494 Q561 469 557 493 Q561 514 590 500 Q625 480 626 500 Q622 516 594 501 L599 534 L586 526 L576 537Z" fill="#dca5c6"/>'
 elif variant==1:
  if pid in ('elsa','anna'):
   s+='<ellipse cx="595" cy="484" rx="45" ry="42" fill="#fffefa"/><ellipse cx="595" cy="424" rx="33" ry="39" fill="#fffefa"/><path d="M584 408 L599 406 L635 419 L597 420Z" fill="#e7a15d"/><circle cx="580" cy="397" r="4" fill="#42414d"/><circle cx="604" cy="395" r="4" fill="#42414d"/><path d="M584 437 Q600 453 610 435 M571 475 L551 454 M623 476 L644 451" fill="none"/><circle cx="596" cy="475" r="5" fill="#595361"/><circle cx="596" cy="495" r="5" fill="#595361"/>'
  elif pid=='rapunzel':
   s+='<path d="M559 483 Q534 471 540 449 Q549 430 565 445 Q560 466 550 461 Q559 489 586 477" fill="#97bf70"/><ellipse cx="596" cy="461" rx="40" ry="34" fill="#97bf70"/><ellipse cx="611" cy="430" rx="31" ry="26" fill="#a9d084"/><circle cx="620" cy="425" r="11" fill="#f8f8dc"/><circle cx="623" cy="426" r="5" fill="#404d3c"/><path d="M595 481 L588 502 M619 477 L625 495 M589 437 Q597 425 604 435" fill="none"/>'
  elif pid=='ariel':
   s+='<path d="M561 460 L530 428 L535 482 L561 470" fill="#75bfd4"/><ellipse cx="594" cy="452" rx="45" ry="34" fill="#f7dc76"/><path d="M580 423 Q600 398 618 423 M579 432 L578 469 M597 426 L595 477" stroke="#7abfd0" stroke-width="8" fill="none"/><ellipse cx="619" cy="443" rx="10" ry="13" fill="white"/><circle cx="623" cy="445" r="5" fill="#3e5268"/><path d="M619 465 Q630 471 636 462" fill="none"/>'
  else:
   s+='<path d="M550 418 L606 398 L642 487 L584 511Z" fill="#a9b4d4"/><path d="M560 421 L606 408 L631 480 L587 497Z" fill="#fff5d9"/><path d="M567 422 L593 500" stroke="#9d7b7d"/><path d="M592 439 l12 -13 13 8 -4 18 -15 6Z" fill="#e3bd72"/>'
 else:
  s+='<path d="M551 522 L613 389" stroke="#d4b16f" stroke-width="12"/><path d="M612 358 L624 389 L656 392 L631 413 L638 444 L611 428 L583 444 L591 413 L566 392 L600 388Z" fill="#f9e3a3"/><path d="M612 381 L618 396 L635 399 L621 409 L624 424 L611 416 L599 423 L602 408 L590 398 L607 396Z" fill="#f0b7d4"/>'
 return s+'</g>'

# Story costumes use a shared precise frame, with distinct silhouettes and details.
STORY={
 'elsa': [('대관식 기본 복장','#152d31','#472a74'),('얼음 궁전 드레스','#62cbe5','#d6f6ff'),('숲의 하얀 드레스','#edf8ff','#b5d6eb')],
 'anna': [('여행 기본 복장','#213c57','#2584ad'),('대관식 초록 드레스','#285e40','#90b172'),('여왕 드레스','#263c2c','#744c82')],
 'rapunzel': [('탑에서 입는 보라 옷','#b18acf','#e2b4d9'),('꽃 장식 드레스','#b18acf','#ecc1e3'),('왕국 축제 드레스','#a074bd','#e6b5d9')],
 'ariel': [('바닷속 인어 모습','#8764b2','#56b493'),('육지의 파란 옷','#172f47','#8cc9df'),('분홍 궁전 드레스','#ed9db9','#ffe1ec')],
 'belle': [('마을의 파란 기본 옷','#5d9dc8','#f6f0df'),('노란 무도회 드레스','#f2c84c','#ffe79b'),('겨울 망토 드레스','#9c2543','#f6c8cf')],
 'cinderella': [('청소할 때 입는 옷','#724d35','#d3b49b'),('요정의 무도회 드레스','#9dc8f4','#e8f4ff'),('친구들이 만든 분홍 옷','#e99cba','#fbe5ee')]
}
def story_dress(pid,variant):
 label,bodice,skirt=STORY[pid][variant]
 edge='#735b66';prefix=f'{pid}-story-{variant}'
 s=defs(prefix,skirt,bodice,'#fff8f2')+f'<g transform="translate(100 0)" stroke="{edge}" stroke-width="2.5" stroke-linejoin="round">'
 if pid=='ariel' and variant==0:
  s+='<path d="M236 280 Q260 270 299 294 Q335 270 364 280 L345 386 Q300 407 255 386Z" fill="#8764b2"/><path d="M255 386 Q303 409 345 386 Q373 478 329 630 Q315 678 362 710 Q410 720 425 747 Q355 770 302 725 Q259 766 179 747 Q198 713 246 709 Q279 681 266 631 Q220 481 255 386Z" fill="#52ad8d"/><path d="M259 390 Q301 412 342 390 M302 445 Q284 600 302 718" fill="none" stroke="#a2e0b3" stroke-width="6"/>'
 else:
  full=variant>0 or pid in ('elsa','anna','rapunzel')
  left,right=(124,477) if full else (173,427)
  s+=f'<path d="M240 280 Q269 274 300 288 Q331 274 361 280 L347 390 Q383 500 {right} 726 Q300 761 {left} 726 Q221 501 253 390Z" fill="url(#{prefix}-dress)"/>'
  s+=f'<path d="M240 280 Q270 276 300 293 Q330 276 361 280 L346 391 Q301 406 254 391Z" fill="{bodice}"/>'
  s+=f'<path d="M245 409 Q229 565 {left+38} 715 M278 419 L263 736 M323 418 L341 737 M352 410 Q383 580 {right-32} 716" fill="none" stroke="{bodice}" opacity=".28" stroke-width="5"/>'
  if (pid in ('belle','cinderella') and variant==0) or (pid=='ariel' and variant==1):
   s+='<path d="M237 281 Q216 284 211 317 L235 330 L254 310 M362 281 Q382 284 389 317 L365 330 L347 310" fill="#fff6e5"/><path d="M261 292 L279 291 L281 389 L322 389 L323 292 L340 292 L341 392 Q369 546 390 713 Q300 742 209 713 Q233 540 260 392Z" fill="#fff6e8"/><path d="M250 392 Q300 410 349 392" fill="none" stroke="#ded1bd" stroke-width="7"/>'
  elif (pid=='belle' and variant==1) or (pid=='cinderella' and variant==1):
   s+=f'<path d="M235 282 Q259 310 300 310 Q343 310 365 282 L381 311 Q341 343 301 323 Q258 343 219 310Z" fill="{skirt}"/>'
   s+=f'<path d="M253 405 Q211 458 183 513 Q255 542 300 473 Q351 545 418 513 Q386 453 346 405Z" fill="{skirt}"/>'
   s+=f'<path d="M177 575 Q238 632 300 571 Q360 633 424 575 M151 664 Q222 716 300 662 Q381 718 451 663" fill="none" stroke="{skirt}" stroke-width="13"/>'
   if pid=='belle':s+=flower(300,575,15,'#e7ad37')
  elif pid=='elsa' and variant==1:
   s+='<path d="M244 285 L176 692 Q207 736 247 725 L275 326 M354 285 L423 692 Q391 737 352 727 L326 326" fill="#d8faff" opacity=".55"/><path d="M248 290 L232 317 M353 290 L370 316" stroke="#b8edfa" stroke-width="20"/>'
   for x,y in [(212,565),(381,614),(298,681),(273,461),(343,535)]:s+=f'<path d="M{x-12} {y} h24 M{x} {y-12} v24 M{x-8} {y-8} l16 16 M{x-8} {y+8} l16 -16" stroke="#fff" stroke-width="2"/>'
  elif pid=='rapunzel':
   s+='<path d="M238 282 Q215 287 211 315 L234 334 L253 312 M361 282 Q384 289 389 315 L366 333 L347 311" fill="#dfb2df"/><path d="M281 302 L318 322 L283 342 L317 362 L285 383" fill="none" stroke="#f4d4df" stroke-width="5"/>'
   if variant: 
    for x,y in [(218,553),(383,612),(289,685)]:s+=flower(x,y,15)
  elif pid=='anna' or (pid=='elsa' and variant==0):
   s+='<path d="M269 306 Q299 331 331 306 M298 321 V382" fill="none" stroke="#d3b967" stroke-width="4"/>'
   for x,y in [(214,630),(299,678),(388,630)]:s+=f'<path d="M{x} {y+25} v-48 M{x} {y} q-27 -30 -26 -3 q4 19 26 17 q30 -1 26 -20 q-2 -20 -26 6" fill="#a1b879" stroke="#d2c176" stroke-width="2"/>'
   if pid=='anna' and variant==0:s+='<path d="M238 279 Q300 310 363 279 L393 475 L348 444 L330 306 L273 306 L253 447 L208 478Z" fill="#a23b6d"/>'
  elif pid=='cinderella' and variant==2:
   for x,y in [(254,313),(347,313),(197,586),(404,586)]:s+=f'<path d="M{x} {y} q-26 -22 -28 0 q2 20 28 0 q28 -22 29 0 q-1 21 -29 0Z" fill="#fff0ed"/>'
  elif pid=='belle' and variant==2:s+='<path d="M237 281 Q301 323 365 281 L411 556 L350 510 L329 315 L274 315 L250 511 L190 555Z" fill="#9e2949"/><path d="M237 281 Q301 323 365 281" fill="none" stroke="#fff5e6" stroke-width="16"/>'
 s+='</g>'
 return s

def dress(pid,color,shade,light,variant):return story_dress(pid,variant)
_original_base=base
def base(pid,hair,eye,variant=0):
 s=_original_base(pid,hair,eye)
 # Narrower cheeks, differentiated eye shape, and signature hair accents.
 s=s.replace('rx="94" ry="109"','rx="85" ry="109"')
 if pid=='cinderella':s+= '<g transform="translate(100 0)"><path d="M213 123 Q231 40 300 48 Q373 42 389 124" fill="none" stroke="#83b7df" stroke-width="10"/></g>'
 if pid=='belle':s+='<g transform="translate(100 0)"><ellipse cx="300" cy="48" rx="40" ry="27" fill="#6e422c" stroke="#795a58" stroke-width="3"/><path d="M269 60 Q300 70 330 60" fill="none" stroke="#e4bf60" stroke-width="7"/></g>'
 # Replace the neutral base clothes with the character's story starting costume.
 return s+story_dress(pid,variant)


def build():
 OUT.mkdir(parents=True,exist_ok=True)
 catalog=[]
 for pid,name,hair,eye,color,shade,light,*dress_names in PRINCESSES:
  dress_names=[x[0] for x in STORY[pid]]
  drawings=[base(pid,hair,eye)]+[dress(pid,color,shade,light,i) for i in range(3)]+[crown(pid,i) for i in range(2)]+[prop(pid,i) for i in range(3)]
  drawings += [base(pid,hair,eye,i) for i in range(3)]
  svg='<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="3200" viewBox="0 0 2400 3200">'
  for i,art in enumerate(drawings):svg+=f'<g transform="translate({i%3*800} {i//3*800})">{art}</g>'
  svg+='</svg>'
  (OUT/(pid+'.svg')).write_text(svg)
  sprites=[]
  for i in range(12):
   kind='base' if i==0 or i>=9 else 'outfit' if i<4 else 'head' if i<6 else 'hand'
   local=[0,0,800,800] if i==0 or i>=9 else [205,264,385,498] if i<4 else [309,27,182,93] if i<6 else [515,348,155,194]
   # Clothing extends to x577; head and hand shapes share exactly the base frame.
   if 0<i<4:local=[205,264,385,498]
   x,y,w,h=local;box=[i%3*800+x,i//3*800+y,w,h]
   label=name if i==0 or i>=9 else dress_names[i-1] if i<4 else ['보석 왕관','꽃 왕관'][i-4] if i<6 else ['별 요술봉','친구 소품','꽃다발'][i-6]
   if i==7:label={'elsa':'눈사람 친구','anna':'눈사람 친구','rapunzel':'파스칼','ariel':'물고기 친구','belle':'이야기책','cinderella':'이야기책'}[pid]
   item={'name':label,'kind':kind,'box':box}
   if i:item['fit']={'x':(x+w/2)/8,'y':(y+h/2)/8,'w':w/8,'h':h/8}
   sprites.append(item)
  catalog.append({'id':pid,'name':name,'src':'/static/princess/'+pid+'.svg','width':2400,'height':3200,'baseVariants':[9,10,11],'sprites':sprites,'color':color,'slots':{'outfit':{'x':50,'y':63,'rx':35,'ry':32},'head':{'x':50,'y':12,'rx':35,'ry':27},'hand':{'x':74,'y':55,'rx':32,'ry':33}}})
 (OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'static'/'hyeon-princess-assets.js').write_text('window.PRINCESS_ASSETS='+json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+';\n')

if __name__=='__main__':build()

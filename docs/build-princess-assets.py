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


# Individually drawn faces and signature hair silhouettes in the common doll frame.
def base(pid,hair,eye,variant=0):
 colors={'elsa':('#f8edc9','#c9b97b'),'anna':('#a9512d','#693c2c'),'rapunzel':('#f3d564','#c99b36'),'ariel':('#d53c35','#962535'),'belle':('#75452f','#452b29'),'cinderella':('#edca6c','#b48c41')}
 colors.update({'jasmine':('#182e3c','#101b2a'),'snowwhite':('#2d2434','#171927'),'aurora':('#f0d37b','#c49a4e'),'merida':('#c86832','#853e25'),'mulan':('#28313c','#101c29'),'pocahontas':('#222a34','#101822')})
 hair,shade=colors[pid];edge='#68434e';skin={'jasmine':'#dca777','pocahontas':'#c9976d','mulan':'#f2d4b6'}.get(pid,'#ffe4cf');pre=pid+'-face-'+str(variant)
 s=f'''<defs><linearGradient id="{pre}-hair" x2="1" y2=".7"><stop stop-color="{hair}"/><stop offset=".55" stop-color="{hair}"/><stop offset="1" stop-color="{shade}"/></linearGradient><radialGradient id="{pre}-skin" cx=".4" cy=".3" r=".8"><stop stop-color="{skin}"/><stop offset="1" stop-color="{skin}"/></radialGradient><radialGradient id="{pre}-iris"><stop stop-color="#b1e4d8"/><stop offset=".45" stop-color="{eye}"/><stop offset="1" stop-color="#274d69"/></radialGradient><radialGradient id="{pre}-blush"><stop stop-color="#ec8d9b" stop-opacity=".55"/><stop offset="1" stop-color="#ec8d9b" stop-opacity="0"/></radialGradient></defs>'''
 s+=f'<g transform="translate(100 0)" stroke="{edge}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">'
 fill=f'url(#{pre}-hair)'
 if pid in ('rapunzel','ariel','belle','jasmine','snowwhite','aurora','merida','mulan','pocahontas'):
  hair_type={'jasmine':'belle','snowwhite':'belle','aurora':'rapunzel','merida':'ariel','mulan':'belle','pocahontas':'rapunzel'}.get(pid,pid)
  path={'rapunzel':'M226 72 Q169 153 194 304 Q146 441 188 561 Q147 694 208 747 Q248 765 267 713 L351 711 Q406 760 438 707 Q463 661 421 554 Q458 424 405 297 Q431 136 371 73Z','ariel':'M232 52 Q147 82 179 220 Q135 304 182 380 Q136 470 188 574 Q137 650 192 715 Q256 768 274 688 L351 706 Q419 765 453 687 Q475 620 423 538 Q472 430 415 325 Q462 220 408 108 Q374 45 326 47Z','belle':'M225 86 Q185 159 203 267 Q160 364 201 456 Q165 555 195 673 Q222 724 269 693 L347 694 Q405 726 429 667 Q447 572 408 461 Q447 359 404 265 Q422 151 366 85Z'}[hair_type]
  if pid=='snowwhite':path='M226 80 Q172 104 186 188 Q169 258 224 288 Q266 308 300 279 Q343 309 382 284 Q429 255 409 185 Q425 100 371 78Z'
  s+=f'<path d="{path}" fill="{fill}"/>'
  for d in ['M208 258 Q189 367 218 453 T211 670','M397 261 Q429 370 400 463 T408 662']:s+=f'<path d="{d}" fill="none" stroke="{hair}" stroke-width="7" opacity=".75"/>'
 if pid=='cinderella':
  s+=f'<ellipse cx="305" cy="61" rx="57" ry="39" fill="{fill}"/>'
  if variant==0:s+=f'<path d="M375 175 Q437 223 398 331 Q433 361 412 414 Q369 404 360 356 Q391 286 362 228Z" fill="{fill}"/>'
 # Arms and legs remain visible outside each costume silhouette.
 s+=f'<path d="M272 228 L269 283 Q300 306 332 283 L328 228 M238 283 Q218 297 205 340 L181 414 Q179 431 193 433 Q208 433 215 412 L248 331 M361 283 Q384 299 394 340 L418 414 Q422 430 407 433 Q393 433 385 413 L352 331 M267 726 L263 760 Q264 776 287 771 L299 731 M309 731 L312 760 Q315 777 338 769 L333 726" fill="{skin}"/>'
 s+='<path d="M262 755 Q276 766 290 753 L290 771 Q269 782 260 767Z M310 755 Q326 767 338 753 L342 768 Q318 783 311 768Z" fill="#d4e9f7"/>'
 s+=f'<path d="M213 128 Q204 78 247 55 Q298 33 349 57 Q395 81 389 135 L382 191 Q373 230 342 250 Q301 277 260 250 Q226 230 216 194Z" fill="url(#{pre}-skin)"/>'
 s+=f'<ellipse cx="212" cy="172" rx="11" ry="20" fill="{skin}"/><ellipse cx="388" cy="172" rx="11" ry="20" fill="{skin}"/>'
 # Each hairstyle is different rather than a palette swap.
 bang={
 'elsa':'M209 161 Q177 78 232 53 Q235 22 273 25 Q324 12 357 48 Q401 71 394 162 L379 145 Q377 96 342 84 Q330 62 311 62 Q292 114 235 118 L221 171Z',
 'anna':'M210 170 Q185 100 226 64 Q257 34 299 50 Q342 29 375 67 Q410 112 388 173 L375 151 Q377 97 343 82 Q322 82 301 102 Q274 78 253 88 Q223 110 224 164Z',
 'rapunzel':'M210 177 Q182 86 239 54 Q292 21 351 50 Q413 84 391 178 L376 155 Q378 103 346 80 Q321 125 280 139 Q251 149 224 144 L224 177Z',
 'ariel':'M205 183 Q164 121 196 71 Q216 26 282 39 Q326 13 376 52 Q425 94 391 190 L375 166 Q388 105 345 81 Q353 137 279 145 Q241 138 218 176Z',
 'belle':'M209 170 Q187 98 229 64 Q261 33 300 50 Q341 30 375 65 Q410 109 390 171 L375 151 Q374 98 344 84 Q321 112 300 123 Q267 112 254 87 Q223 104 224 168Z',
 'cinderella':'M208 171 Q189 107 218 77 Q224 43 270 43 Q320 29 361 56 Q409 87 390 171 L375 148 Q375 106 349 88 Q335 125 293 125 Q264 123 248 104 Q225 119 224 170Z'}.get(pid,{'jasmine':'M207 174 Q181 92 237 56 Q299 22 363 57 Q417 94 390 177 L376 150 Q374 112 343 90 Q321 117 300 121 Q277 114 255 91 Q223 110 224 173Z','snowwhite':'M209 171 Q183 97 227 64 Q267 36 300 56 Q342 32 377 71 Q414 106 389 173 L375 155 Q375 112 346 91 Q314 118 284 103 Q246 128 224 155 L224 176Z','aurora':'M207 174 Q188 91 242 59 Q290 25 352 53 Q415 86 391 180 L376 158 Q377 102 345 85 Q322 128 280 139 Q249 148 224 141 L223 176Z','merida':'M207 178 Q167 122 196 78 Q218 36 270 50 Q315 20 365 57 Q422 80 393 180 L376 152 Q378 109 345 93 Q303 130 266 114 Q236 122 223 171Z','mulan':'M208 173 Q186 95 236 63 Q298 26 361 61 Q411 97 391 176 L376 153 Q377 107 345 86 Q300 133 223 130 L223 176Z','pocahontas':'M207 175 Q185 88 237 59 Q298 24 362 59 Q415 96 391 177 L376 151 Q374 108 345 85 Q316 123 224 139 L224 176Z'}.get(pid,''))
 s+=f'<path d="{bang}" fill="{fill}"/>'
 if pid=='elsa':
  s+=f'<path d="M224 105 Q266 81 270 45 M248 111 Q295 78 301 44 M276 111 Q323 89 331 65" fill="none" stroke="#fff9df" stroke-width="4"/>'
 if pid in ('elsa','anna'):
  for side in ([377] if pid=='elsa' else [221,379]):
   for j in range(7):
    x=side+(j*2 if side>300 else -j*2);y=208+j*27
    s+=f'<path d="M{x-13} {y-12} Q{x+17} {y-24} {x+20} {y} Q{x+12} {y+20} {x-13} {y+21} Q{x-28} {y+4} {x-13} {y-12}Z" fill="{fill}"/>'
   s+=f'<path d="M{x-15} {y+19} q15 10 31 0 l-4 12 -23 0Z" fill="'+('#a0cee6' if pid=='elsa' else '#294b63')+'"/>'
 if pid=='belle':s+=f'<ellipse cx="301" cy="50" rx="38" ry="24" fill="{fill}"/><path d="M268 63 Q300 77 334 63" fill="none" stroke="#e4c16c" stroke-width="7"/>'
 if pid=='cinderella':
  s+='<path d="M213 121 Q225 53 299 51 Q370 53 387 121" fill="none" stroke="#8cc9ed" stroke-width="9"/>'
  if variant==0:s+='<path d="M211 119 Q215 55 271 44 Q338 31 377 88 Q314 53 259 89Z" fill="#dedfe5" stroke="#b2acb9"/><path d="M374 99 l31 -16 -8 40 -20 -9Z" fill="#dedfe5"/>'
 # Expressive almond-shaped eyes, colored irises, eyelid shading, lashes and brows.
 for x,flip in [(261,1),(339,-1)]:
  slant=5 if pid=='elsa' else 2 if pid=='belle' else 0
  wide=26 if pid in ('rapunzel','ariel') else 24
  s+=f'<g transform="translate({x} 169) scale({flip} 1)"><path d="M{-wide} {-3-slant} Q-4 -23 {wide} -4 Q18 21 0 21 Q-18 19 {-wide} {-3-slant}Z" fill="#fffaf7" stroke="#976c80" stroke-width="1.5"/>'
  s+=f'<ellipse cx="1" cy="3" rx="14" ry="20" fill="url(#{pre}-iris)" stroke="#385c68" stroke-width="1.4"/><ellipse cx="1" cy="4" rx="7.5" ry="14" fill="#24334d" stroke="none"/><ellipse cx="-4" cy="-5" rx="4.5" ry="6" fill="#fff" stroke="none"/><circle cx="7" cy="10" r="2.4" fill="#fff" stroke="none"/>'
  s+=f'<path d="M{-wide-2} {-5-slant} Q0 -24 {wide} -5 M{-wide} {-5-slant} l-8 -10 M{-wide+6} -12 l-5 -10" fill="none" stroke="#473247" stroke-width="3.5"/><path d="M-24 -30 Q-6 -40 18 -29" fill="none" stroke="{shade}" stroke-width="4.8"/></g>'
 s+=f'<ellipse cx="239" cy="205" rx="26" ry="15" fill="url(#{pre}-blush)" stroke="none"/><ellipse cx="361" cy="205" rx="26" ry="15" fill="url(#{pre}-blush)" stroke="none"/>'
 s+='<path d="M299 181 Q289 202 299 207 Q305 207 307 203" fill="none" stroke="#d09d8e" stroke-width="2"/><path d="M278 225 Q292 219 301 225 Q311 219 324 224 Q303 245 278 225Z" fill="#c8657b" stroke="#b96374" stroke-width="1.3"/><path d="M284 226 Q302 230 318 225" fill="none" stroke="#fff0e7" stroke-width="2"/>'
 if pid in ('anna','rapunzel'):
  s+='<g fill="#bc8267" stroke="none">'+''.join(f'<circle cx="{x}" cy="{y}" r="1.4"/>' for x,y in [(239,196),(248,199),(256,195),(346,195),(354,199),(364,196)])+'</g>'
 if pid=='rapunzel':
  for x,y in [(201,300),(414,461),(207,625)]:s+=flower(x,y,12,'#edb9d8')
 if pid=='merida':
  for side in (204,396):
   for j in range(12):
    x=side+(-1 if side<300 else 1)*(17+(j%3)*9);y=110+j*29
    s+=f'<path d="M{x} {y} q-25 -29 -29 0 q0 26 23 20 q21 -7 4 -26 q-12 -10 -16 3" fill="{hair}" stroke="{shade}" stroke-width="3"/>'
 if pid=='jasmine':s+='<path d="M219 125 Q300 91 382 125" fill="none" stroke="#65c9c4" stroke-width="13"/><ellipse cx="300" cy="109" rx="15" ry="19" fill="#79bfd0" stroke="#d7b66b" stroke-width="4"/>'
 if pid=='snowwhite':s+='<path d="M215 115 Q300 46 386 115" fill="none" stroke="#ce3c58" stroke-width="9"/>'
 s+='</g>'
 return s+story_dress(pid,variant)

CROWN_NAMES={ 'elsa':['얼음 결정 왕관','눈꽃 머리 장식'],'anna':['아렌델 금빛 왕관','초록 꽃 화관'],'rapunzel':['태양 보석 왕관','보라 꽃 화관'],'ariel':['바다 조개 왕관','진주 머리 장식'],'belle':['장미 금빛 왕관','빨간 장미 머리핀'],'cinderella':['하늘색 머리띠','은빛 무도회 왕관'] }
PROP_NAMES={'elsa':['눈꽃 마법봉','올라프 친구','얼음 꽃다발'],'anna':['해바라기 꽃다발','올라프 친구','여행 가방'],'rapunzel':['축제 등불','파스칼 친구','프라이팬'],'ariel':['반짝이는 포크','플라운더 친구','조개 가방'],'belle':['유리 속 장미','이야기책','찻잔 친구'],'cinderella':['요정의 마법봉','호박 마차','유리 구두']}
_old_crown=crown
_old_prop=prop
def crown(pid,variant):
 if pid=='cinderella' and variant==0:return '<path d="M320 107 Q400 28 480 107" fill="none" stroke="#7bb9e3" stroke-width="13"/><path d="M322 102 Q400 36 478 102" fill="none" stroke="#e0f6ff" stroke-width="3"/>'
 if variant==1 and pid=='belle':return '<g transform="translate(400 78)"><path d="M0 4 Q-43 -43 -61 -9 Q-31 15 0 4 Q45 -45 61 -10 Q27 15 0 4" fill="#d3ad54" stroke="#987845" stroke-width="2"/></g>'+flower(400,75,29,'#c73757')
 if variant==1 and pid!='cinderella':
  col={'elsa':'#d7efff','anna':'#a6c5a1','rapunzel':'#d4b3e5','ariel':'#f9e9df'}[pid]
  return '<path d="M321 107 Q400 37 479 107" fill="none" stroke="#d6b977" stroke-width="9"/>'+''.join(flower(x,y,13,col) for x,y in [(337,93),(367,76),(400,69),(433,76),(463,93)])
 metal='#cbeafa' if pid in ('elsa','cinderella') else '#efce74';gem={'elsa':'#8bd6f2','anna':'#70aa83','rapunzel':'#bf88ce','ariel':'#72d0bd','belle':'#df7c8a','cinderella':'#9bbcea'}[pid]
 s=f'<g stroke="#9f805c" stroke-width="2"><path d="M320 106 L326 70 L351 85 L373 43 L400 74 L426 43 L449 85 L474 70 L480 106Z" fill="{metal}"/><path d="M326 102 Q400 115 475 102" fill="none" stroke="#fff3c9" stroke-width="5"/>'
 for x,y,r in [(350,91,7),(400,87,12),(449,91,7)]:s+=f'<path d="M{x} {y-r-7} L{x+r} {y} L{x} {y+r+7} L{x-r} {y}Z" fill="{gem}"/>'
 if pid=='ariel':s+='<path d="M381 66 Q369 42 400 30 Q430 42 419 66Z M400 33 V65 M385 40 L393 65 M414 40 L407 65" fill="#f6d3c9" stroke="#cc9a94"/>'
 if pid=='rapunzel':s+='<circle cx="400" cy="51" r="10" fill="#ffe49a"/><path d="M400 35 V27 M384 51 H376 M416 51 H424 M389 39 L383 33 M411 39 L417 33" stroke="#d6af4f" stroke-width="3"/>'
 return s+'</g>'

def prop(pid,variant):
 # Preserve the recognizable little companion illustrations.
 if variant==1 and pid in ('elsa','anna','rapunzel','ariel'):return _old_prop(pid,variant)
 s='<g transform="translate(515 348)" stroke="#806875" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
 if pid=='belle' and variant==1:return _old_prop(pid,1)
 if pid=='elsa' and variant==2:return _old_prop(pid,2)
 if pid=='anna' and variant==0:return _old_prop(pid,2)
 if pid=='cinderella' and variant==0:return _old_prop(pid,0)
 if pid=='elsa':
  s+='<path d="M59 169 L94 48" stroke="#a1dbea" stroke-width="10"/><g transform="translate(95 46)" stroke="#98cee8" stroke-width="5" fill="none">'+''.join(f'<path d="M0 0 V-34 M0 -22 L-9 -30 M0 -22 L9 -30" transform="rotate({a})"/>' for a in range(0,360,60))+'</g><circle cx="95" cy="46" r="8" fill="#f3fdff"/>'
 elif pid=='anna':s+='<path d="M34 64 Q73 49 118 65 L127 155 Q82 177 27 155Z" fill="#754d3c"/><path d="M57 61 V41 Q78 20 98 41 V61 M35 97 Q80 117 119 95" fill="none" stroke="#cfa061" stroke-width="9"/><rect x="65" y="99" width="25" height="24" rx="5" fill="#d6bd74"/>'
 elif pid=='rapunzel' and variant==0:
  s+='<path d="M36 30 Q76 8 119 30 L114 141 Q76 162 41 142Z" fill="#ffe29a"/><ellipse cx="77" cy="30" rx="41" ry="13" fill="#dcb16e"/><path d="M45 142 Q77 156 113 141 M51 47 V125 M104 47 V125" fill="none" stroke="#ebbd80" stroke-width="4"/><circle cx="78" cy="88" r="16" fill="#efbd62"/><path d="M78 60 V48 M78 116 V129 M51 88 H40 M105 88 H117" stroke="#efbd62" stroke-width="4"/>'
 elif pid=='rapunzel':s+='<path d="M76 102 L40 177" stroke="#51494e" stroke-width="14"/><ellipse cx="91" cy="67" rx="46" ry="51" fill="#44474c"/><ellipse cx="91" cy="65" rx="34" ry="39" fill="#62696f" stroke="#363d45"/>'
 elif pid=='ariel' and variant==0:s+='<path d="M64 172 L84 68 M62 29 L57 65 Q80 94 108 66 L119 28 M78 23 L75 68 M99 23 L94 68" fill="none" stroke="#d2b97c" stroke-width="9"/>'
 elif pid=='ariel':s+='<path d="M30 107 Q72 37 128 107 L111 151 Q78 175 44 151Z" fill="#e9bdd8"/><path d="M45 109 Q78 72 112 109 M78 88 V155 M48 115 L58 151 M108 116 L98 152" fill="none" stroke="#c491bc" stroke-width="3"/><path d="M35 111 Q16 29 82 22 Q148 26 125 111" fill="none" stroke="#d8bf85" stroke-width="7"/>'
 elif pid=='belle' and variant==0:
  s+='<path d="M31 159 V65 Q34 12 77 10 Q122 13 124 65 V159Z" fill="#e9f7ff" fill-opacity=".5" stroke="#b1c6d4"/><path d="M80 145 V62 Q52 78 56 100 Q76 103 80 85 M80 119 Q114 102 110 84 Q88 85 80 102" fill="#86ad75" stroke="#70936c"/>'+flower(80,57,21,'#d24e71')+'<ellipse cx="78" cy="160" rx="57" ry="13" fill="#bda06c"/><path d="M41 71 Q40 36 61 28" fill="none" stroke="#fff" stroke-width="4"/>'
 elif pid=='belle':s+='<path d="M36 75 Q73 58 113 75 L108 124 Q77 145 43 124Z" fill="#fff6dc"/><path d="M114 81 Q147 72 139 100 Q134 114 110 113" fill="none" stroke="#d6b576" stroke-width="8"/><ellipse cx="77" cy="133" rx="59" ry="12" fill="#f4dfa2"/><circle cx="61" cy="96" r="3" fill="#624453"/><circle cx="87" cy="96" r="3" fill="#624453"/><path d="M66 111 Q77 122 87 110" fill="none"/>'
 elif pid=='cinderella' and variant==1:
  s+='<path d="M77 44 Q69 18 87 12" fill="none" stroke="#8daa76" stroke-width="9"/><ellipse cx="78" cy="91" rx="60" ry="50" fill="#ecc58f"/><path d="M78 43 Q31 85 78 140 Q125 87 78 43" fill="#f6dab1"/><path d="M60 65 Q78 49 96 65 V112 H60Z" fill="#c4dbef"/><path d="M78 68 V111 M62 91 H95" stroke="#fff5de"/><circle cx="40" cy="145" r="22" fill="#dfc27e"/><circle cx="115" cy="145" r="22" fill="#dfc27e"/><circle cx="40" cy="145" r="13" fill="#fff2ce"/><circle cx="115" cy="145" r="13" fill="#fff2ce"/>'
 else:s+='<path d="M23 123 Q45 121 62 71 Q78 89 88 110 Q105 124 135 124 Q145 139 122 147 H42 Q17 144 23 123Z" fill="#c4e5f4" fill-opacity=".85" stroke="#90bdd7"/><path d="M39 147 L35 169 H46 L57 148 M65 100 Q79 121 103 129" fill="none" stroke="#ebfaff" stroke-width="5"/><path d="M114 117 l8 -17 8 17 -8 16Z" fill="#fff"/>'
 return s+'</g>'


NEW_PRINCESSES=[('jasmine','자스민','#172e3d','#835c3f','#63d1ce','#2a9d9c','#e5ffff'),('snowwhite','백설공주','#25202d','#77513d','#efd968','#d9a94b','#fff0b6'),('aurora','오로라','#e8c461','#736caf','#edaccb','#c774a8','#fff1f8'),('merida','메리다','#bf5a2c','#508c9e','#267d78','#174d54','#a8d6c7'),('mulan','뮬란','#242b36','#63493a','#91bb75','#4d835c','#eff2cb'),('pocahontas','포카혼타스','#22252c','#614332','#d7b385','#ad8054','#f5dfb1')]
PRINCESSES += [(*row,'','','') for row in NEW_PRINCESSES]
STORY.update({
 'jasmine':[('하늘빛 궁전 복장','#4bb7bc','#8bded8'),('보라색 축제 복장','#a483ce','#d8bceb'),('붉은 궁전 복장','#c75362','#ec99a1')],
 'snowwhite':[('집안일 기본 복장','#724b39','#bba28a'),('파랑 노랑 공주 드레스','#24477b','#f7db64'),('숲속 망토 드레스','#24477b','#f7db64')],
 'aurora':[('숲속에서 입는 옷','#493d46','#bbaa93'),('요정의 분홍 드레스','#d66f9f','#efadcc'),('요정의 파란 드레스','#4a8bc0','#a9d8ed')],
 'merida':[('숲속의 초록 드레스','#205655','#347670'),('왕궁의 파란 예복','#3b7289','#7aa5ba'),('모험 망토 복장','#233f3c','#347670')],
 'mulan':[('초록색 기본 복장','#87b76b','#deeb9c'),('분홍색 예복','#c95682','#eaa6c4'),('용감한 갑옷 복장','#5a7771','#638783')],
 'pocahontas':[('숲속의 기본 복장','#d4ad78','#e6c693'),('나들이 어깨 망토','#b98a58','#e6c693'),('축제 목걸이 복장','#d4ad78','#e6c693')]
})
CROWN_NAMES.update({'jasmine':['청록 보석 머리띠','궁전 금빛 머리 장식'],'snowwhite':['빨간 리본 머리띠','숲속 꽃 화관'],'aurora':['금빛 공주 왕관','장미 꽃 화관'],'merida':['곰 문양 머리 장식','왕궁 금빛 왕관'],'mulan':['목련 꽃 머리핀','예복 머리 장식'],'pocahontas':['청록 구슬 머리띠','나뭇잎 머리 장식']})
PROP_NAMES.update({'jasmine':['요술 램프','궁전의 양탄자','보석 가방'],'snowwhite':['빨간 사과','작은 새 친구','꽃바구니'],'aurora':['장미 한 송이','부엉이 친구','요정의 마법봉'],'merida':['활과 화살','아기 곰 친구','숲속 등불'],'mulan':['목련 꽃','무슈 친구','접이식 부채'],'pocahontas':['나침반','미코 친구','바람의 나뭇잎']})
_story_dress=story_dress
def story_dress(pid,variant):
 if pid not in STORY or pid in {p[0] for p in PRINCESSES[:6]}:return _story_dress(pid,variant)
 _,top,skirt=STORY[pid][variant];edge='#725a61';pre=pid+'-costume-'+str(variant)
 dark='#'+''.join(f'{int(skirt[j:j+2],16)*83//100:02x}' for j in (1,3,5))
 s=defs(pre,skirt,dark,'#fff7e7')+f'<g transform="translate(100 0)" stroke="{edge}" stroke-width="2.3" stroke-linejoin="round">'
 if pid=='jasmine':
  s+=f'<path d="M237 282 Q300 312 364 282 L349 381 Q300 399 253 381Z" fill="{top}"/><path d="M250 399 Q297 419 350 399 L377 449 Q412 554 376 714 Q352 749 310 724 L299 498 L289 724 Q250 749 224 714 Q190 551 225 449Z" fill="{skirt}"/><path d="M249 402 Q301 423 351 402 M223 704 Q254 726 289 711 M311 711 Q344 726 376 705" fill="none" stroke="#e8ce77" stroke-width="10"/><path d="M238 284 Q213 289 211 313 L234 329 L254 305 M364 284 Q388 288 389 314 L365 330 L347 306" fill="{skirt}"/><path d="M271 293 Q299 325 332 293" fill="none" stroke="#e2c779" stroke-width="6"/>'
 elif pid=='pocahontas':
  s+=f'<path d="M240 279 L277 294 L352 267 L346 393 L400 689 L318 730 L199 684 L253 392Z" fill="{skirt}"/><path d="M240 279 L277 294 L352 267 L347 307 L275 335 L240 315Z" fill="{top}"/>'
  for x in range(204,396,14):s+=f'<path d="M{x} 676 v27" stroke="#b18b5b" stroke-width="7"/>'
  s+='<path d="M274 269 Q301 306 332 268" fill="none" stroke="#58adae" stroke-width="10"/><path d="M300 292 l11 16 -11 16 -11 -16Z" fill="#8bced0"/>'
  if variant==1:s+='<path d="M241 277 L356 268 L390 440 L310 382 L208 435Z" fill="#a17653"/>'
 elif pid=='mulan':
  s+=f'<path d="M236 280 L299 294 L363 280 L347 392 L430 724 Q301 756 170 724 L253 392Z" fill="{skirt}"/><path d="M236 280 L299 294 L363 280 L352 399 L251 399Z" fill="{top}"/><path d="M252 284 L321 372 L347 283 M273 291 L326 373" fill="none" stroke="#f3ebce" stroke-width="14"/><path d="M249 383 Q300 399 354 383 L357 411 Q300 427 245 410Z" fill="'+('#9d3960' if variant!=2 else '#454e55')+'"/><path d="M236 283 L200 345 L228 360 L260 307 M362 283 L402 345 L374 361 L342 306" fill="'+top+'"/>'
  if variant==2:
   for y in range(315,398,18):s+=f'<path d="M257 {y} H347" stroke="#364f53" stroke-width="5"/>'
   s+='<path d="M253 414 L347 414 L369 513 L231 513Z" fill="#5a7771"/><path d="M300 420 V511" stroke="#364f53" stroke-width="5"/>'
 else:
  full=not(pid=='snowwhite' and variant==0);l,r=(130,470) if full else (176,424)
  s+=f'<path d="M237 281 Q300 306 364 281 L346 391 Q371 512 {r} 724 Q300 756 {l} 724 Q231 514 254 391Z" fill="url(#{pre}-dress)"/><path d="M237 281 Q300 306 364 281 L346 391 Q300 407 254 391Z" fill="{top}"/>'
  for x in [223,271,326,380]:s+=f'<path d="M{(x+300)/2} 419 Q{x} 600 {x} 729" fill="none" stroke="{top}" opacity=".2" stroke-width="5"/>'
  if pid=='snowwhite':
   s+='<path d="M242 279 Q300 299 360 279 L355 261 Q299 284 248 260Z" fill="#fff7e9"/>'
   if variant==0:s+='<path d="M270 293 H329 L335 401 L384 709 Q300 741 216 709 L263 401Z" fill="#ede4d4"/>'
   else:
    s+='<path d="M237 281 Q209 277 204 312 Q211 340 237 334 L258 310 M363 281 Q392 277 397 312 Q390 341 364 334 L343 310" fill="#7da3d0"/><path d="M220 291 L226 325 M237 289 L241 320 M378 289 L373 325 M391 294 L385 321" stroke="#b94658" stroke-width="8"/>'
    if variant==2:s+='<path d="M240 279 L207 531 L249 504 L277 292 M361 279 L397 532 L351 506 L325 292" fill="#b74858"/>'
  if pid=='aurora':
   s+='<path d="M236 280 L267 294 L300 331 L334 294 L364 280 L376 314 L338 323 L302 347 L262 323 L225 313Z" fill="'+('#eee4d2' if variant==0 else '#fff1eb')+'"/>'
   if variant==0:s+='<path d="M275 308 L319 326 L280 344 L321 362 L285 386" stroke="#e8dac4" fill="none" stroke-width="4"/>'
  if pid=='merida':
   s+='<path d="M236 280 Q300 309 364 280 L387 389 L364 400 L341 308 M237 281 L211 389 L234 400 L259 310" fill="'+top+'"/><path d="M284 305 L317 326 L284 346 L315 365 L287 389" fill="none" stroke="#cfb786" stroke-width="4"/>'
   if variant==2:s+='<path d="M237 279 L186 579 L244 538 L275 294 M362 279 L412 579 L352 537 L324 294" fill="#233f3c"/>'
 s+='</g>';return s

_crown12=crown
_prop12=prop
def crown(pid,variant):
 if pid not in {p[0] for p in NEW_PRINCESSES}:return _crown12(pid,variant)
 if pid=='snowwhite':
  if variant:return '<path d="M320 106 Q400 44 480 106" fill="none" stroke="#87aa80" stroke-width="8"/>'+''.join(flower(x,y,15,'#fff2d8') for x,y in [(340,89),(370,74),(401,68),(433,75),(464,91)])
  return '<path d="M321 108 Q400 35 479 108" fill="none" stroke="#ce3c58" stroke-width="10"/><path d="M400 62 Q355 17 344 55 Q348 88 399 69 Q448 22 458 58 Q449 90 402 69Z" fill="#d84963" stroke="#923b53" stroke-width="2"/><circle cx="400" cy="65" r="12" fill="#e66b7d"/>'
 if pid=='jasmine' or pid=='pocahontas':
  return '<path d="M319 104 Q399 68 480 104" fill="none" stroke="'+('#5cc9c6' if pid=='jasmine' else '#6cbbb9')+'" stroke-width="18"/><ellipse cx="400" cy="87" rx="18" ry="24" fill="#6cb4ce" stroke="#e6c476" stroke-width="5"/>'
 if pid=='mulan':return '<path d="M330 99 L476 60" stroke="#c2a16b" stroke-width="8"/>'+flower(400,77,25,'#edc3d2')+flower(438,70,17,'#fff0e5')
 if pid=='merida' and variant==0:return '<path d="M338 101 Q400 62 464 101" fill="none" stroke="#98764b" stroke-width="9"/><circle cx="400" cy="83" r="19" fill="#d8bc75" stroke="#8a704c" stroke-width="3"/><circle cx="393" cy="77" r="4" fill="#8a704c"/><circle cx="407" cy="77" r="4" fill="#8a704c"/><ellipse cx="400" cy="86" rx="9" ry="7" fill="#8a704c"/>'
 return '<g fill="#e9cb76" stroke="#a68b54" stroke-width="2"><path d="M320 105 L329 63 L359 81 L400 32 L442 81 L472 63 L480 105Z"/><path d="M400 55 l14 25 -14 18 -14 -18Z" fill="'+('#e7a3c5' if pid=='aurora' else '#68a89e')+'"/></g>'

def prop(pid,variant):
 if pid not in {p[0] for p in NEW_PRINCESSES}:return _prop12(pid,variant)
 s='<g transform="translate(515 348)" stroke="#79616b" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">'
 if pid=='jasmine' and variant==0:s+='<path d="M43 102 Q78 72 111 103 L126 90 Q147 85 139 103 L115 124 Q87 149 48 124 L21 93 L8 86 L21 80Z" fill="#e7c16b"/><path d="M53 99 Q80 82 107 99 M67 88 Q67 70 83 70 Q97 72 95 86" fill="none" stroke="#e7c16b" stroke-width="8"/><path d="M74 132 V150 H101" stroke="#e7c16b" stroke-width="10"/>'
 elif pid=='jasmine' and variant==1:s+='<path d="M14 58 L123 37 L143 139 L34 162Z" fill="#9e75b6"/><path d="M29 68 L112 52 L128 127 L44 144Z" fill="#ceaccf" stroke="#e9c377" stroke-width="6"/><path d="M74 70 l27 28 -18 32 -27 -28Z" fill="#7daec3"/><path d="M22 60 L10 43 M122 37 L129 22 M34 162 L28 178 M143 139 L152 149" stroke="#deb46c" stroke-width="6"/>'
 elif pid=='snowwhite' and variant==0:s+='<path d="M74 68 Q40 41 21 74 Q9 112 44 143 Q64 162 79 145 Q99 164 121 138 Q153 100 125 70 Q108 53 81 69Z" fill="#d94d58"/><path d="M78 70 Q70 40 88 29" fill="none" stroke="#8e7148" stroke-width="8"/><path d="M84 48 Q103 25 122 41 Q107 60 84 48Z" fill="#85ac6c"/><path d="M38 83 Q26 102 39 115" fill="none" stroke="#f6988a" stroke-width="7"/>'
 elif pid=='merida' and variant==0:s+='<path d="M58 22 Q144 88 57 171" fill="none" stroke="#9f774d" stroke-width="10"/><path d="M58 22 L58 171 M22 99 H137" fill="none" stroke="#d7c3a2" stroke-width="3"/><path d="M134 98 l-20 -10 v20Z" fill="#859c9b"/>'
 elif pid=='mulan' and variant==0:s+=flower(79,60,32,'#f4cbda')+'<path d="M79 93 V170 Q45 146 53 119 Q77 122 79 145 M79 138 Q111 102 118 128 Q109 151 79 154" fill="#8aaf77" stroke="#739363" stroke-width="4"/>'
 elif pid=='mulan' and variant==2:s+='<path d="M76 156 L13 78 Q73 1 142 78Z" fill="#e6b3c3"/><path d="M76 156 L37 59 M76 156 L62 42 M76 156 L89 41 M76 156 L116 58" stroke="#a57e68" stroke-width="4"/>'+flower(78,89,14,'#faf0de')
 elif pid=='pocahontas' and variant==0:s+='<circle cx="78" cy="95" r="58" fill="#d8bd77"/><circle cx="78" cy="95" r="46" fill="#f9eac1"/><path d="M78 51 L94 97 L78 137 L63 96Z" fill="#6ea9ba"/><path d="M78 51 L94 97 L78 95Z" fill="#c16b68"/><circle cx="78" cy="95" r="6" fill="#fbf1d7"/>'
 elif pid=='pocahontas' and variant==2:s+='<path d="M26 155 Q19 45 132 25 Q139 128 26 155Z" fill="#d39965"/><path d="M29 151 L121 40 M56 122 L52 75 M74 103 L118 99 M94 81 L95 48" fill="none" stroke="#9e744f" stroke-width="4"/>'
 elif pid=='aurora' and variant==0:s+='<path d="M75 82 V172 Q41 140 45 118 Q62 116 75 140 M75 126 Q112 98 118 123 Q99 145 75 144" fill="#84a577" stroke="#6e8e69" stroke-width="4"/>'+flower(77,56,29,'#d8789b')
 elif pid=='aurora' and variant==2:return _prop12('cinderella',0)
 elif variant==1 and pid=='snowwhite':
  s+='<ellipse cx="80" cy="109" rx="43" ry="35" fill="#91bad1"/><path d="M50 108 Q12 74 24 56 Q60 62 70 99 M96 111 Q134 79 143 99 Q119 124 102 129" fill="#6a9fba"/><circle cx="90" cy="75" r="26" fill="#b9d4e0"/><path d="M112 72 l28 12 -29 6Z" fill="#e1bb70"/><circle cx="97" cy="69" r="4" fill="#4b4b58"/><path d="M62 137 L53 154 M83 140 L78 157" stroke="#c69d63" stroke-width="5"/>'
 elif variant==1 and pid=='aurora':
  s+='<path d="M40 45 L53 25 L70 43 Q105 27 123 46 L138 30 L136 113 Q112 164 77 164 Q37 148 33 104Z" fill="#ad947c"/><ellipse cx="62" cy="82" rx="25" ry="31" fill="#f9ead0"/><ellipse cx="109" cy="82" rx="25" ry="31" fill="#f9ead0"/><circle cx="63" cy="83" r="10" fill="#494453"/><circle cx="108" cy="83" r="10" fill="#494453"/><path d="M77 105 l10 -17 10 17 -10 12Z" fill="#d8ab6d"/><path d="M46 115 Q58 143 74 144 M126 115 Q114 144 101 144" fill="none" stroke="#826d60" stroke-width="7"/>'
 elif variant==1 and pid=='mulan':
  s+='<path d="M41 157 Q134 168 111 123 Q99 102 66 110 Q27 119 43 84 Q55 68 85 73 L101 45 Q125 35 134 54 Q135 79 101 87 Q90 124 123 148" fill="none" stroke="#ba5b52" stroke-width="18"/><path d="M95 48 L83 27 M119 44 L123 22" stroke="#d8bd7e" stroke-width="6"/><path d="M101 61 l37 8 -29 11Z" fill="#d99b7e"/><circle cx="110" cy="53" r="5" fill="#fff"/><circle cx="112" cy="54" r="2" fill="#373644"/><path d="M131 72 l16 10 M128 77 l14 17 M70 110 L51 136 M96 109 L119 131" stroke="#d6b474" stroke-width="4"/>'
 elif variant==1 and pid=='pocahontas':
  s+='<path d="M44 134 Q1 108 21 75 Q35 56 48 79 Q29 105 63 119" fill="none" stroke="#797c82" stroke-width="24"/><path d="M20 83 L38 87 M20 103 L40 104" stroke="#474b54" stroke-width="10"/><ellipse cx="85" cy="126" rx="34" ry="36" fill="#9e9fa0"/><circle cx="86" cy="77" r="34" fill="#b3b2ac"/><path d="M57 60 L50 37 L75 48 M98 48 L121 36 L116 62" fill="#85868a"/><path d="M55 72 Q86 61 117 73 L113 90 Q86 104 58 90Z" fill="#565b64"/><circle cx="73" cy="80" r="5" fill="#fff"/><circle cx="101" cy="80" r="5" fill="#fff"/><ellipse cx="86" cy="94" rx="8" ry="6" fill="#393b46"/>'
 elif variant==1:
  col={'snowwhite':'#85b6cf','aurora':'#a48a74','merida':'#83634f','mulan':'#c5645c','pocahontas':'#909493'}[pid]
  s+=f'<ellipse cx="78" cy="121" rx="40" ry="43" fill="{col}"/><circle cx="79" cy="74" r="36" fill="{col}"/><circle cx="53" cy="45" r="14" fill="{col}"/><circle cx="105" cy="45" r="14" fill="{col}"/><ellipse cx="79" cy="85" rx="24" ry="18" fill="#e9d6bc"/><circle cx="65" cy="66" r="4" fill="#453b41"/><circle cx="93" cy="66" r="4" fill="#453b41"/><ellipse cx="79" cy="83" rx="7" ry="5" fill="#453b41"/>'
 elif pid=='merida':s+='<path d="M35 58 H121 L127 152 H29Z" fill="#d3b875"/><path d="M45 60 V35 Q78 6 111 35 V60" fill="none" stroke="#8b7458" stroke-width="8"/><path d="M54 136 Q36 102 77 79 Q116 106 99 136Z" fill="#ffdf97"/><path d="M40 59 V152 M114 59 V152 M27 151 H130" stroke="#8b7458" stroke-width="7"/>'
 else:
  s+='<path d="M29 100 Q78 76 127 100 L115 158 Q78 177 41 158Z" fill="#cba477"/><path d="M31 104 Q9 13 80 16 Q151 17 125 104" fill="none" stroke="#b38c61" stroke-width="7"/>'
  for x,y,c in [(48,91,'#efb2c6'),(82,80,'#e8d49a'),(110,95,'#b4cbdc')]:s+=flower(x,y,18,c)
 return s+'</g>'


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
   label=name if i==0 or i>=9 else dress_names[i-1] if i<4 else CROWN_NAMES[pid][i-4] if i<6 else PROP_NAMES[pid][i-6]
   if False:label={'elsa':'눈사람 친구','anna':'눈사람 친구','rapunzel':'파스칼','ariel':'물고기 친구','belle':'이야기책','cinderella':'이야기책'}[pid]
   item={'name':label,'kind':kind,'box':box}
   if i:item['fit']={'x':(x+w/2)/8,'y':(y+h/2)/8,'w':w/8,'h':h/8}
   sprites.append(item)
  catalog.append({'id':pid,'name':name,'src':'/static/princess/'+pid+'.svg','width':2400,'height':3200,'baseVariants':[9,10,11],'sprites':sprites,'color':color,'slots':{'outfit':{'x':50,'y':63,'rx':35,'ry':32},'head':{'x':50,'y':12,'rx':35,'ry':27},'hand':{'x':74,'y':55,'rx':32,'ry':33}}})
 (OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'static'/'hyeon-princess-assets.js').write_text('window.PRINCESS_ASSETS='+json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+';\n')

if __name__=='__main__':build()

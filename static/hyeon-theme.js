(function(){
  'use strict';
  if(location.pathname.replace(/\/$/,'')!=='/hyeon')return;
  var main=document.querySelector('main.wrap');
  if(!main)return;
  var hero=main.querySelector('.hero');
  if(hero){var title=hero.querySelector('h1');if(title)title.textContent='혜온의 놀이방';var greeting=document.createElement('p');greeting.className='hy-welcome';greeting.textContent='오늘은 뭐하고 놀까요? 좋아하는 놀이를 골라봐요.';hero.appendChild(greeting);}
  var links=Array.from(main.querySelectorAll('a'));
  var old=links.find(function(a){return a.getAttribute('href')==='/hyeon/hangul';});
  if(!old)return;
  var row=old.parentElement;
  if(!row.querySelector('a[href="/hyeon/coloring"]')||!row.querySelector('a[href="/hyeon/dressup"]'))return;
  var cards=document.createElement('section');cards.className='hy-activities';cards.setAttribute('aria-label','혜온의 놀이 선택');
  [['🔤','한글놀이','글자와 단어를 듣고 함께 놀아요','hangul'],['🎨','색칠공부','좋아하는 그림을 알록달록 칠해요','coloring'],['🏡','티니핑 마을','친구를 꾸미고 작은 마을로 보내요','dressup'],['👑','디즈니 공주 옷입히기','공주에게 드레스와 왕관을 입혀요','princess']].forEach(function(item){var a=document.createElement('a');a.className='hy-activity';a.href='/hyeon/'+item[3];var icon=document.createElement('span');icon.className='hy-activity-icon';icon.setAttribute('aria-hidden','true');icon.textContent=item[0];var text=document.createElement('span');var title=document.createElement('strong');title.textContent=item[1];var description=document.createElement('small');description.textContent=item[2];text.append(title,description);a.append(icon,text);cards.appendChild(a);});
  row.replaceWith(cards);
})();

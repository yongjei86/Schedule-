from datetime import datetime, timedelta
from collections import Counter, defaultdict
import riley_dashboard_wrapper as _r
from home_tasks_only_app import app, db, H, page, KST

CSS=_r.DASH_CSS

def rows():
 c=db(); rs=[dict(r) for r in c.execute("select * from riley_reading where child='혜온' and read_date is not null and read_date!='' order by read_date desc,id desc").fetchall()]; c.close(); return rs

def key(ds,view):
 d=datetime.strptime(ds,'%Y-%m-%d').date()
 if view=='day': return d.strftime('%m/%d')
 if view=='week':
  m=d-timedelta(days=d.weekday()); return m.strftime('%m/%d')+'~'+(m+timedelta(days=6)).strftime('%m/%d')
 return d.strftime('%Y.%m')

def bars(rs,view):
 g=Counter(key(r['read_date'],view) for r in rs); items=list(g.items())[:31 if view=='day' else 16 if view=='week' else 12]; mx=max([n for _,n in items] or [1])
 return ''.join(f'<div class="rd-row"><b>{H(k)}</b><div class="rd-bar"><div class="rd-fill" style="width:{n/mx*100:.0f}%"></div></div><b>{n}권</b></div>' for k,n in items) or '<div class="muted">데이터 없음</div>'

def monthly(rs):
 by=defaultdict(list)
 for r in rs: by[r['read_date'][:7]].append(r)
 out=''
 for m in sorted(by,reverse=True)[:12]:
  x=by[m]; ko=sum(r.get('language') in ('한글','한국어') for r in x); en=sum(r.get('language')=='영어' for r in x); total=len(x); kp=ko/total*100 if total else 0; ep=en/total*100 if total else 0
  out+=f'<tr><td><b>{H(m)}</b></td><td>{total}권</td><td><div class="rd-lang"><span class="ko" style="width:{kp:.0f}%"></span><span class="en" style="width:{ep:.0f}%"></span></div><div class="rd-meta">한글 {ko} · 영어 {en}</div></td></tr>'
 return '<div class="rd-card rd-trend"><h3>월별 독서 구성</h3><table><thead><tr><th>월</th><th>독서량</th><th>한글 / 영어</th></tr></thead><tbody>'+out+'</tbody></table></div>' if out else ''

def body(embedded=False):
 rs=rows(); today=datetime.now(KST).date(); mon=today-timedelta(days=today.weekday()); month=today.strftime('%Y-%m')
 tn=sum(r['read_date']==today.isoformat() for r in rs); wn=sum(mon.isoformat()<=r['read_date']<=(mon+timedelta(days=6)).isoformat() for r in rs); mn=sum(r['read_date'].startswith(month) for r in rs)
 en=sum(r.get('language')=='영어' for r in rs); ko=sum(r.get('language') in ('한글','한국어') for r in rs)
 companions=Counter((r.get('companion') or '미기록') for r in rs)
 comp=''.join(f'<div class="rd-book"><b>{H(k)}</b><span style="float:right">{v}권</span></div>' for k,v in companions.most_common()) or '<div class="muted">데이터 없음</div>'
 recent=''
 for r in rs[:8 if embedded else 15]:
  cp=r.get('companion') or '미기록'; recent+=f'<div class="rd-book"><b>{H(r["title"])}</b><div class="rd-meta">{H(r["read_date"])} · {H(r.get("language") or "-")} · {H(cp)}</div></div>'
 tabs=''.join(f'<button type="button" class="{"on" if v=="week" else ""}" onclick="rdView(this,\'{v}\')">{label}</button>' for v,label in [('day','일별'),('week','주별'),('month','월별')])
 panels=''.join(f'<div id="rd-{v}" class="rd-panel {"on" if v=="week" else ""}"><h3>{label} 독서량</h3>{bars(rs,v)}</div>' for v,label in [('day','일별'),('week','주별'),('month','월별')])
 head='<div class="rd-head"><div><h2 style="margin:0">📚 혜온 독서 대시보드</h2><div class="rd-meta">읽은 날짜 · 읽기 방식 기준</div></div><div class="rd-actions"><a class="btn" href="/hyeon/reading/db">독서 DB 보기</a></div></div>' if embedded else '<div class="rd-head"><div><h1 style="margin:0">혜온 독서 대시보드</h1></div><div class="rd-actions"><a class="btn" href="/hyeon/reading/db">독서 DB</a><a class="btn s" href="/hyeon">혜온 포탈</a></div></div>'
 script="""<script>function rdView(btn,v){var w=btn.closest('.rd-wrap');w.querySelectorAll('.rd-tabs button').forEach(x=>x.classList.remove('on'));btn.classList.add('on');w.querySelectorAll('.rd-panel').forEach(x=>x.classList.remove('on'));var p=w.querySelector('#rd-'+v);if(p)p.classList.add('on');}</script>"""
 return CSS+f'<div class="rd-wrap">{head}<div class="rd-tabs">{tabs}</div><div class="rd-kpis"><div class="rd-kpi"><b>{tn}</b><span>오늘</span></div><div class="rd-kpi"><b>{wn}</b><span>이번 주</span></div><div class="rd-kpi"><b>{mn}</b><span>이번 달</span></div><div class="rd-kpi"><b>{len(rs)}</b><span>누적</span></div></div><div class="rd-grid"><div><div class="rd-card">{panels}</div><div class="rd-card"><h3>최근 읽은 책</h3>{recent or "<div class=muted>데이터 없음</div>"}</div></div><div><div class="rd-card"><h3>언어 구성</h3><p><b>한글 {ko}권</b> · 영어 {en}권</p></div><div class="rd-card"><h3>읽기 방식</h3><div class="rd-meta">혼자 · 아빠 · 엄마 · 언니 · 세이펜</div>{comp}</div></div></div>{monthly(rs)}</div>'+script

@app.route('/hyeon/reading/dashboard')
def hyeon_reading_dashboard(): return page('혜온 독서 대시보드',body(False))

import home_tasks_only_app as _main
_old=_main._reading_section
@app.route('/hyeon/reading/db')
def hyeon_reading_db(): return page('혜온 독서 DB','<div class="toolbar"><h1>혜온 독서 DB</h1><a class="btn s" href="/hyeon">혜온 포탈</a></div>'+_old('혜온','/hyeon')+_main.reading_edit_modal('/hyeon'))

def portal(child='지유',base='/riley'):
 if child=='혜온' and base=='/hyeon': return body(True)
 return _old(child,base)
_main._reading_section=portal

# Workbook cards: save completion in the background instead of submitting a form
# that reloads the whole portal. The existing POST routes and credit logic stay intact.
_main.JS += r'''
wbItemClick=async function(el){
 if(wbEditMode){editWb(el);return}
 if(el.dataset.busy==='1')return;
 var title=el.querySelector('b');
 var wasDone=!!(title&&title.classList.contains('task-done'));
 var url=(el.dataset.base||'/riley')+'/workbook/'+el.dataset.id+'/toggle';
 if(el.dataset.date)url+='/'+el.dataset.date;
 el.dataset.busy='1';
 var oldOpacity=el.style.opacity;
 el.style.opacity='.58';
 el.style.pointerEvents='none';
 try{
  var res=await fetch(url,{method:'POST',credentials:'same-origin',headers:{'X-Requested-With':'fetch'}});
  if(!res.ok)throw new Error('toggle failed: '+res.status);
  if(title)title.classList.toggle('task-done',!wasDone);
  var card=el.closest('.feature-card');
  var heading=card&&card.querySelector('.toolbar h2');
  if(heading){
   var m=heading.textContent.match(/이번 주 미완료\s+(\d+)건/);
   if(m){
    var next=Math.max(0,parseInt(m[1],10)+(wasDone?1:-1));
    heading.textContent=heading.textContent.replace(/이번 주 미완료\s+\d+건/,'이번 주 미완료 '+next+'건');
   }
  }
  if(el.animate)el.animate([{transform:'scale(.98)'},{transform:'scale(1)'}],{duration:130});
 }catch(err){
  console.error(err);
  alert('완료 처리에 실패했어요. 다시 눌러 주세요.');
 }finally{
  delete el.dataset.busy;
  el.style.opacity=oldOpacity;
  el.style.pointerEvents='';
 }
};
'''

@app.after_request
def workbook_toggle_no_redirect_for_fetch(response):
 p=_main.request.path
 if (_main.request.method=='POST' and _main.request.headers.get('X-Requested-With')=='fetch'
     and (p.startswith('/riley/workbook/') or p.startswith('/hyeon/workbook/'))
     and '/toggle' in p and response.status_code in (301,302,303,307,308)):
  response.status_code=204
  response.set_data(b'')
  response.headers.pop('Location',None)
 return response

# Register Riley's creative workspace after dashboard integrations.
import riley_creative

# Keep Hyeon's games and parent reading screens in one visual language.
@app.after_request
def hyeon_shared_theme(response):
 import re
 from html import escape
 path = _main.request.path
 if not (path == '/hyeon' or path.startswith('/hyeon/')):
  return response
 if response.status_code != 200 or response.mimetype != 'text/html':
  return response
 response.direct_passthrough = False
 html = response.get_data(as_text=True)
 if 'id="hyeon-theme-style"' in html:
  return response
 html = html.replace('</head>', '<link id="hyeon-theme-style" rel="stylesheet" href="/static/hyeon-theme.css?v=2"><script defer src="/static/hyeon-theme.js?v=2"></script></head>', 1)
 def themed_body(match):
  attrs = match.group(1)
  if re.search(r'\bclass\s*=', attrs):
   attrs = re.sub(r'''\bclass=(['"])(.*?)\1''', lambda m: 'class='+m.group(1)+m.group(2)+' hyeon-theme'+m.group(1), attrs, count=1)
  else:
   attrs += ' class="hyeon-theme"'
  return '<body'+attrs+'>'
 html = re.sub(r'<body\b([^>]*)>', themed_body, html, count=1)
 if path.rstrip('/') in ('/hyeon/dressup','/hyeon/princess'):
  # Preserve the village and sound controls, including their event targets.
  html = html.replace('<header>', '<header id="hy-header">', 1)
  html = html.replace('</nav>', '<a href="/hyeon/reading/dashboard">📚 독서기록</a></nav>', 1)
 else:
  items = [('/hyeon/hangul','🔤 한글놀이'),('/hyeon/coloring','🎨 색칠공부'),('/hyeon/dressup','🏡 티니핑 마을'),('/hyeon/princess','👑 디즈니 공주'),('/hyeon/reading/dashboard','📚 독서기록')]
  nav = ''
  for href,label in items:
   active = path.startswith('/hyeon/reading') if '/reading/' in href else path.startswith(href)
   current = ' aria-current="page"' if active else ''
   nav += '<a href="'+escape(href)+'"'+current+'>'+label+'</a>'
  header = '<header id="hy-header"><a href="/hyeon" aria-label="혜온 포탈 홈">🏠</a><nav aria-label="놀이 메뉴">'+nav+'</nav><a class="hy-family" href="/">가족 포탈 ↗</a></header>'
  if re.search(r'<header\b', html):
   html = re.sub(r'<header\b[^>]*>.*?</header>', lambda m: header, html, count=1, flags=re.S)
  else:
   html = re.sub(r'(<body\b[^>]*>)', lambda m: m.group(1)+header, html, count=1)
 html = html.replace('👗 옷입히기</a>','🏡 티니핑 마을</a>').replace('aria-label="옷입히기"','aria-label="티니핑 마을"')
 response.set_data(html)
 response.headers.pop('ETag',None)
 response.headers.pop('Last-Modified',None)
 response.headers['Cache-Control'] = 'no-cache'
 return response


@app.route('/hyeon/princess')
def hyeon_princess_dressup():
 from pathlib import Path
 return _main.send_from_directory(Path(__file__).parent / 'static','hyeon-princess.html')


@app.route('/hyeon/dressup/village/return', methods=['POST'])
def hyeon_village_return_closet():
 payload = _main.request.get_json(silent=True)
 character_id = payload.get('character_id') if isinstance(payload,dict) else None
 if not isinstance(character_id,str) or character_id not in {item['id'] for item in _main._dressup_catalog()}:
  return _main.jsonify(error='invalid_character'),400
 c=db()
 try:
  c.execute("""CREATE TABLE IF NOT EXISTS hyeon_village_residents(
   character_id TEXT PRIMARY KEY, outfit TEXT NOT NULL,
   created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
   updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
  c.execute('DELETE FROM hyeon_village_residents WHERE character_id=?',(character_id,))
  c.commit()
  return _main.jsonify(residents=_main._dressup_residents(c))
 finally:
  c.close()

@app.route('/hyeon/princess/ballroom', methods=['GET','POST'])
def hyeon_princess_ballroom():
 import json
 from pathlib import Path
 catalog=json.loads((Path(__file__).parent/'static/princess/catalog.json').read_text())
 by_id={item['id']:item for item in catalog}
 payload=_main.request.get_json(silent=True) if _main.request.method=='POST' else None
 if _main.request.method=='POST':
  if not isinstance(payload,dict) or payload.get('character_id') not in by_id:
   return _main.jsonify(error='invalid_character'),400
  outfit=payload.get('outfit',{})
  if payload.get('action')!='return':
   if not isinstance(outfit,dict) or any(kind not in ('outfit','head','hand') or type(index) is not int or index<1 or index>=len(by_id[payload['character_id']]['sprites']) or by_id[payload['character_id']]['sprites'][index]['kind']!=kind for kind,index in outfit.items()):
    return _main.jsonify(error='invalid_outfit'),400
 c=db()
 try:
  c.execute('CREATE TABLE IF NOT EXISTS hyeon_ballroom_residents(character_id TEXT PRIMARY KEY,outfit TEXT NOT NULL)')
  if payload:
   if payload.get('action')=='return':c.execute('DELETE FROM hyeon_ballroom_residents WHERE character_id=?',(payload['character_id'],))
   else:c.execute('INSERT INTO hyeon_ballroom_residents(character_id,outfit) VALUES(?,?) ON CONFLICT(character_id) DO UPDATE SET outfit=excluded.outfit',(payload['character_id'],json.dumps(outfit)))
   c.commit()
  rows=c.execute('SELECT character_id,outfit FROM hyeon_ballroom_residents ORDER BY character_id').fetchall()
  return _main.jsonify(residents=[{'character_id':row[0],'outfit':json.loads(row[1])} for row in rows if row[0] in by_id])
 finally:c.close()

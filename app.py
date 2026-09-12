import os,sqlite3,calendar,html,secrets
from datetime import datetime,timedelta,date
from flask import Flask,request,redirect,session,abort
app=Flask(__name__)
SECRET_KEY=os.getenv('SECRET_KEY')
if not SECRET_KEY:raise RuntimeError('SECRET_KEY environment variable must be set (no insecure default is used)')
app.secret_key=SECRET_KEY
app.config.update(SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE','1')!='0')
DB_PATH=os.getenv('DB_PATH','/data/family_travel.db')
ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:raise RuntimeError('ADMIN_PASSWORD environment variable must be set (no insecure default is used)')
DAYS=['월','화','수','목','금','토','일']

def db():
 os.makedirs(os.path.dirname(DB_PATH) or '.',exist_ok=True);c=sqlite3.connect(DB_PATH);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
def H(x):return html.escape('' if x is None else str(x))
def admin():return bool(session.get('admin'))
def must():
 if not admin():abort(403)
def qdate(s):
 try:return datetime.strptime(s,'%Y-%m-%d').date()
 except:return None

def init():
 c=db();c.executescript('''CREATE TABLE IF NOT EXISTS trips(id INTEGER PRIMARY KEY,start_date TEXT,end_date TEXT,country TEXT,region TEXT,title TEXT,companions TEXT,trip_type TEXT,status TEXT,lodging TEXT,transport TEXT,notes TEXT);CREATE TABLE IF NOT EXISTS itinerary(id INTEGER PRIMARY KEY,trip_id INTEGER REFERENCES trips(id) ON DELETE CASCADE,item_date TEXT,day_label TEXT,time_text TEXT,title TEXT,place TEXT,detail TEXT,sort_order INTEGER DEFAULT 0);CREATE TABLE IF NOT EXISTS calendar_events(id INTEGER PRIMARY KEY,start_date TEXT,end_date TEXT,title TEXT,category TEXT,person TEXT,notes TEXT);CREATE TABLE IF NOT EXISTS academy(id INTEGER PRIMARY KEY,day_of_week TEXT,start_time TEXT,end_time TEXT,academy TEXT,subject TEXT,location TEXT,notes TEXT,active INTEGER DEFAULT 1);''');c.commit();c.close()
init()

CSS='''body{margin:0;background:#f4f7fb;color:#14263f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}*{box-sizing:border-box}header{position:sticky;top:0;z-index:10;background:#f4f7fbf2;border-bottom:1px solid #e4e9f0}nav{max-width:1240px;margin:auto;padding:10px 16px;display:flex;justify-content:space-between;gap:10px}.nav{display:flex;gap:5px;overflow:auto}.nav a,.btn{white-space:nowrap;text-decoration:none;border:0;border-radius:9px;padding:8px 10px;font:inherit;font-size:13px;cursor:pointer}.nav a{color:#728096}.btn{background:#0f4c81;color:#fff}.btn.s{background:#fff;color:#14263f;border:1px solid #e4e9f0}.btn.d{background:#b64b50}.wrap{max-width:1240px;margin:auto;padding:18px 16px 50px}.hero{background:linear-gradient(145deg,#0f4c81,#173d66);color:#fff;border-radius:20px;padding:22px;margin-bottom:18px}.hero h1{margin:0}.toolbar{display:flex;justify-content:space-between;gap:8px;align-items:center;margin:10px 0;flex-wrap:wrap}.seg{display:flex;background:#eaf0f6;border-radius:10px;padding:3px}.seg a{padding:7px 11px;text-decoration:none;color:#65758b;border-radius:8px;font-size:13px}.seg a.on{background:#fff;color:#0f4c81;font-weight:800;box-shadow:0 1px 4px #00000014}.box{background:#fff;border:1px solid #e4e9f0;border-radius:15px;overflow:auto}table{width:100%;border-collapse:collapse;min-width:950px}th,td{padding:10px;border-bottom:1px solid #e4e9f0;text-align:left;font-size:13px}th{background:#fbfcfe;color:#728096}.trip{cursor:pointer}.trip:hover{background:#f7fbff}.detail td{background:#f8fafc;padding:14px}.meta{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.m{background:#fff;border:1px solid #e4e9f0;border-radius:10px;padding:10px}.m b{display:block;color:#728096;font-size:11px}.it{display:grid;grid-template-columns:90px 70px 1fr 1fr auto;gap:8px;background:#fff;border:1px solid #e4e9f0;border-radius:9px;padding:9px;margin-top:7px}.pill{display:inline-block;padding:4px 7px;border-radius:999px;background:#eaf3fb;color:#0f4c81;font-size:11px;font-weight:700}.event{background:#fff;border:1px solid #e4e9f0;border-radius:10px;padding:10px;margin-top:7px;display:flex;justify-content:space-between;gap:8px}.monthbig{background:#fff;border:1px solid #e4e9f0;border-radius:16px;padding:14px}.monthgrid{display:grid;grid-template-columns:repeat(7,1fr);border-left:1px solid #e4e9f0;border-top:1px solid #e4e9f0}.dow{padding:10px;text-align:center;font-size:12px;color:#718097;background:#fafbfd;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0}.cell{min-height:112px;padding:7px;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0;background:#fff}.cell.out{background:#fafbfd;color:#b1bac6}.num{font-size:12px;font-weight:800;margin-bottom:5px}.ce{display:block;background:#eaf3fb;color:#0f4c81;border-radius:6px;padding:4px 5px;margin:3px 0;font-size:11px;overflow:hidden}.weekcal{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}.wday{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px;min-height:220px}.wday h3{margin:0 0 10px;text-align:center;font-size:14px}.yeargrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.mini{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px}.mini h3{text-align:center;margin:2px 0 8px}.minigrid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}.md{font-size:10px;text-align:center;padding:4px;border-radius:4px}.md.has{background:#eaf3fb;color:#0f4c81;font-weight:800}.schedule{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}.sday{background:#fff;border:1px solid #e4e9f0;border-radius:13px;min-height:230px;padding:10px}.sday .date{font-size:11px;color:#7a8798}.sday h3{margin:3px 0 10px}.lesson{background:#eaf3fb;border-radius:9px;padding:8px;margin-bottom:7px;font-size:12px}.lesson b{display:block;margin-bottom:3px}.modal{display:none;position:fixed;inset:0;background:#10203088;z-index:30;padding:16px;overflow:auto}.modal.show{display:block}.card{max-width:720px;margin:3vh auto;background:#fff;border-radius:16px;padding:16px}.head{display:flex;justify-content:space-between}.form{display:grid;grid-template-columns:1fr 1fr;gap:10px}.full{grid-column:1/-1}label{font-size:12px;color:#728096;display:grid;gap:4px}input,select,textarea{width:100%;padding:9px;border:1px solid #ccd5e0;border-radius:8px;font:inherit}textarea{min-height:70px}@media(max-width:900px){.schedule,.weekcal{grid-template-columns:repeat(2,1fr)}.yeargrid{grid-template-columns:repeat(2,1fr)}.meta{grid-template-columns:1fr}.it{grid-template-columns:80px 60px 1fr}.it .place{grid-column:3}.nav{max-width:72vw}.cell{min-height:90px}}@media(max-width:560px){.schedule,.weekcal,.yeargrid,.form{grid-template-columns:1fr}.full{grid-column:1}.hero h1{font-size:26px}.monthbig{padding:8px}.cell{min-height:74px;padding:4px}.ce{font-size:9px;padding:3px}.dow{padding:6px;font-size:10px}}'''
JS='''function t(id){let e=document.getElementById("d"+id);e.style.display=e.style.display==="none"?"table-row":"none"}function o(id){document.getElementById(id).classList.add("show")}function x(id){document.getElementById(id).classList.remove("show")}function ntrip(){document.getElementById("tf").action="/trip/add";document.getElementById("tf").reset();o("tm")}function et(b){let d=b.dataset;document.getElementById("tf").action="/trip/"+d.id+"/edit";["start_date","end_date","country","region","title","companions","trip_type","status","lodging","transport","notes"].forEach(k=>document.querySelector("#tm [name="+k+"]").value=d[k]||"");o("tm")}function ni(id){document.getElementById("if").action="/itinerary/add";document.getElementById("if").reset();document.querySelector("#im [name=trip_id]").value=id;o("im")}function ei(b){let d=b.dataset;document.getElementById("if").action="/itinerary/"+d.id+"/edit";["trip_id","item_date","day_label","time_text","title","place","detail","sort_order"].forEach(k=>document.querySelector("#im [name="+k+"]").value=d[k]||"");o("im")}function ne(){document.getElementById("ef").action="/event/add";document.getElementById("ef").reset();o("em")}function ee(b){let d=b.dataset;document.getElementById("ef").action="/event/"+d.id+"/edit";["start_date","end_date","title","category","person","notes"].forEach(k=>document.querySelector("#em [name="+k+"]").value=d[k]||"");o("em")}function na(day){document.getElementById("af").action="/academy/add";document.getElementById("af").reset();if(day)document.querySelector("#am [name=day_of_week]").value=day;o("am")}function ea(b){let d=b.dataset;document.getElementById("af").action="/academy/"+d.id+"/edit";["day_of_week","start_time","end_time","academy","subject","location","notes"].forEach(k=>document.querySelector("#am [name="+k+"]").value=d[k]||"");o("am")}'''
def nav():return '<header><nav><b>✈️ 우리 가족 기록</b><div class="nav"><a href="/past">과거 여행</a><a href="/future">향후 여행</a><a href="/calendar">가족 달력</a><a href="/riley">지유 주간 학원 일정</a>'+('<a href="/logout">로그아웃</a>' if admin() else '<a href="/login">관리자</a>')+'</div></nav></header>'
def page(title,body):return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{H(title)}</title><style>{CSS}</style></head><body>{nav()}<main class="wrap"><div class="hero"><h1>{H(title)}</h1></div>{body}</main><script>{JS}</script></body></html>'
def mods():
 if not admin():return ''
 return '''<div class="modal" id="tm"><div class="card"><div class="head"><h2>여행 추가/수정</h2><button class="btn s" onclick="x('tm')">닫기</button></div><form class="form" id="tf" method="post"><label>시작일<input type="date" name="start_date" required></label><label>종료일<input type="date" name="end_date" required></label><label>국가<input name="country"></label><label>지역<input name="region"></label><label class="full">여행명<input name="title" required></label><label>간 사람<input name="companions"></label><label>구분<select name="trip_type"><option>해외</option><option>국내</option></select></label><label>상태<select name="status"><option>완료</option><option>예정</option><option>검토 중</option><option>장기 계획</option></select></label><label>숙소<input name="lodging"></label><label class="full">교통/항공<input name="transport"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div><div class="modal" id="im"><div class="card"><div class="head"><h2>세부 일정 추가/수정</h2><button class="btn s" onclick="x('im')">닫기</button></div><form class="form" id="if" method="post"><input type="hidden" name="trip_id"><label>날짜<input type="date" name="item_date"></label><label>일차<input name="day_label"></label><label>시간<input name="time_text"></label><label>순서<input type="number" name="sort_order"></label><label class="full">일정 제목<input name="title" required></label><label>장소<input name="place"></label><label class="full">상세<textarea name="detail"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
def travels(done):
 c=db();rs=c.execute('select * from trips where status'+("='완료'" if done else "!='완료'")+' order by start_date desc').fetchall();its={}
 for z in c.execute('select * from itinerary order by trip_id,sort_order,item_date,id'):its.setdefault(z['trip_id'],[]).append(z)
 c.close();b='<div class="toolbar"><b>'+('과거 여행' if done else '향후 여행')+f' · {len(rs)}건</b>'+('<button class="btn" onclick="ntrip()">+ 여행 추가</button>' if admin() else '')+'</div><div class="box"><table><tr><th>여행 일자</th><th>국가</th><th>지역</th><th>여행명</th><th>간 사람</th><th>구분</th><th>상태</th><th>숙소</th><th>관리</th></tr>'
 for r in rs:
  a=''
  if admin():
   dat=' '.join('data-'+k+'="'+H(r[k])+'"' for k in ['id','start_date','end_date','country','region','title','companions','trip_type','status','lodging','transport','notes']);a=f'<button class="btn s" {dat} onclick="event.stopPropagation();et(this)">수정</button><form method="post" action="/trip/{r["id"]}/delete" style="display:inline" onsubmit="return confirm(\'삭제할까요?\')"><button class="btn d" onclick="event.stopPropagation()">삭제</button></form>'
  b+=f'<tr class="trip" onclick="t({r["id"]})"><td>{H(r["start_date"])} ~ {H(r["end_date"])}</td><td>{H(r["country"])}</td><td>{H(r["region"])}</td><td><b>{H(r["title"])}</b></td><td>{H(r["companions"])}</td><td>{H(r["trip_type"])}</td><td><span class="pill">{H(r["status"])}</span></td><td>{H(r["lodging"])}</td><td>{a}</td></tr><tr class="detail" id="d{r["id"]}" style="display:none"><td colspan="9"><div class="meta"><div class="m"><b>교통/항공</b>{H(r["transport"]) or "-"}</div><div class="m"><b>메모</b>{H(r["notes"]) or "-"}</div><div class="m"><b>세부 일정</b>{len(its.get(r["id"],[]))}개</div></div><div class="toolbar"><b>세부 일정</b>'+ (f'<button class="btn" onclick="event.stopPropagation();ni({r["id"]})">+ 일정 추가</button>' if admin() else '')+'</div>'
  for z in its.get(r['id'],[]):
   aa=''
   if admin():
    dat=' '.join('data-'+k+'="'+H(z[k])+'"' for k in ['id','trip_id','item_date','day_label','time_text','title','place','detail','sort_order']);aa=f'<div><button class="btn s" {dat} onclick="ei(this)">수정</button><form method="post" action="/itinerary/{z["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
   b+=f'<div class="it"><div>{H(z["item_date"]) or H(z["day_label"])}</div><div>{H(z["time_text"])}</div><div><b>{H(z["title"])}</b><br>{H(z["detail"])}</div><div class="place">{H(z["place"])}</div>{aa}</div>'
  if not its.get(r['id']):b+='<p>등록된 세부 일정이 없습니다.</p>'
  b+='</td></tr>'
 return b+'</table></div>'+mods()
@app.route('/')
def home():return redirect('/future')
@app.route('/past')
def past():return page('과거 여행',travels(True))
@app.route('/future')
def future():return page('향후 여행',travels(False))

def event_rows(start,end):
 c=db();es=c.execute('select * from calendar_events where start_date<=? and end_date>=? order by start_date,id',(end.isoformat(),start.isoformat())).fetchall();c.close();return es
def event_modals(es):
 b=''
 for e in es:
  a=''
  if admin():
   dat=' '.join('data-'+k+'="'+H(e[k])+'"' for k in ['id','start_date','end_date','title','category','person','notes']);a=f'<div><button class="btn s" {dat} onclick="ee(this)">수정</button><form method="post" action="/event/{e["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
  b+=f'<div class="event"><div><b>{H(e["start_date"])} ~ {H(e["end_date"])}</b> · {H(e["title"])} <span class="pill">{H(e["category"])}</span><br>{H(e["person"])} · {H(e["notes"])}</div>{a}</div>'
 if admin():b+='''<div class="modal" id="em"><div class="card"><div class="head"><h2>가족 일정</h2><button class="btn s" onclick="x('em')">닫기</button></div><form class="form" id="ef" method="post"><label>시작일<input type="date" name="start_date" required></label><label>종료일<input type="date" name="end_date" required></label><label class="full">일정명<input name="title" required></label><label>분류<input name="category"></label><label>사람<input name="person"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
 return b
@app.route('/calendar')
def calpage():
 today=date.today();view=request.args.get('view','month');y=int(request.args.get('year',today.year));m=int(request.args.get('month',today.month));
 if view=='week':
  base=qdate(request.args.get('date','')) or today;start=base-timedelta(days=base.weekday());end=start+timedelta(days=6);es=event_rows(start,end);by={start+timedelta(days=i):[] for i in range(7)}
  for e in es:
   s=qdate(e['start_date']);en=qdate(e['end_date'])
   if not s or not en:continue
   for d in by:
    if s<=d<=en:by[d].append(e)
  prev=(start-timedelta(days=7)).isoformat();nxt=(start+timedelta(days=7)).isoformat();title=f'{start.month}/{start.day} ~ {end.month}/{end.day}'
  b=f'<div class="toolbar"><div><a class="btn s" href="/calendar?view=week&date={prev}">← 이전 주</a> <b style="margin:0 10px">{title}</b> <a class="btn s" href="/calendar?view=week&date={nxt}">다음 주 →</a></div><div class="seg"><a class="on" href="/calendar?view=week&date={start.isoformat()}">주</a><a href="/calendar?view=month&year={start.year}&month={start.month}">월</a><a href="/calendar?view=year&year={start.year}">연</a></div></div>'+('<div class="toolbar"><span></span><button class="btn" onclick="ne()">+ 일정 추가</button></div>' if admin() else '')+'<div class="weekcal">'
  for i,d in enumerate(by):
   b+=f'<div class="wday"><h3>{DAYS[i]} {d.month}/{d.day}</h3>'+''.join(f'<span class="ce">{H(e["title"])}</span>' for e in by[d])+'</div>'
  b+='</div>'+event_modals(es);return page('가족 달력',b)
 if view=='year':
  start=date(y,1,1);end=date(y,12,31);es=event_rows(start,end);marks=set()
  for e in es:
   s=qdate(e['start_date']);en=qdate(e['end_date'])
   if not s or not en:continue
   d=max(s,start)
   while d<=min(en,end):marks.add((d.month,d.day));d+=timedelta(days=1)
  b=f'<div class="toolbar"><div><a class="btn s" href="/calendar?view=year&year={y-1}">← {y-1}</a> <b style="margin:0 10px">{y}</b> <a class="btn s" href="/calendar?view=year&year={y+1}">{y+1} →</a></div><div class="seg"><a href="/calendar?view=week&date={today.isoformat()}">주</a><a href="/calendar?view=month&year={y}&month={today.month}">월</a><a class="on" href="/calendar?view=year&year={y}">연</a></div></div><div class="yeargrid">'
  C=calendar.Calendar()
  for mm in range(1,13):
   b+=f'<div class="mini"><h3><a href="/calendar?view=month&year={y}&month={mm}" style="text-decoration:none;color:inherit">{mm}월</a></h3><div class="minigrid">'+''.join(f'<div class="md">{x}</div>' for x in DAYS)
   for d in C.itermonthdays(y,mm):b+=('<div class="md"></div>' if not d else f'<div class="md {"has" if (mm,d) in marks else ""}">{d}</div>')
   b+='</div></div>'
  b+='</div>';return page('가족 달력',b)
 # month default
 first=date(y,m,1);last=date(y,m,calendar.monthrange(y,m)[1]);es=event_rows(first,last);by={}
 for e in es:
  s=qdate(e['start_date']);en=qdate(e['end_date'])
  if not s or not en:continue
  d=max(s,first)
  while d<=min(en,last):by.setdefault(d.day,[]).append(e);d+=timedelta(days=1)
 pm=(first-timedelta(days=1));nm=(last+timedelta(days=1));C=calendar.Calendar(firstweekday=0)
 b=f'<div class="toolbar"><div><a class="btn s" href="/calendar?view=month&year={pm.year}&month={pm.month}">← 이전 달</a> <b style="margin:0 10px">{y}년 {m}월</b> <a class="btn s" href="/calendar?view=month&year={nm.year}&month={nm.month}">다음 달 →</a></div><div class="seg"><a href="/calendar?view=week&date={first.isoformat()}">주</a><a class="on" href="/calendar?view=month&year={y}&month={m}">월</a><a href="/calendar?view=year&year={y}">연</a></div></div>'+('<div class="toolbar"><span></span><button class="btn" onclick="ne()">+ 일정 추가</button></div>' if admin() else '')+'<div class="monthbig"><div class="monthgrid">'+''.join(f'<div class="dow">{x}</div>' for x in DAYS)
 for d in C.itermonthdates(y,m):
  cls='cell'+(' out' if d.month!=m else '');b+=f'<div class="{cls}"><div class="num">{d.day}</div>'
  if d.month==m:
   for e in by.get(d.day,[]):b+=f'<span class="ce">{H(e["title"])}</span>'
  b+='</div>'
 b+='</div></div>'+event_modals(es);return page('가족 달력',b)

@app.route('/riley')
def riley():
 base=qdate(request.args.get('date','')) or date.today();start=base-timedelta(days=base.weekday());end=start+timedelta(days=6);prev=(start-timedelta(days=7)).isoformat();nxt=(start+timedelta(days=7)).isoformat()
 c=db();rs=c.execute("select * from academy where active=1 order by case day_of_week when '월' then 1 when '화' then 2 when '수' then 3 when '목' then 4 when '금' then 5 when '토' then 6 when '일' then 7 else 8 end,start_time,id").fetchall();c.close();by={d:[] for d in DAYS};unknown=[]
 for r in rs:(by[r['day_of_week']].append(r) if r['day_of_week'] in by else unknown.append(r))
 b=f'<div class="toolbar"><div><a class="btn s" href="/riley?date={prev}">← 이전 주</a> <b style="margin:0 10px">{start.month}/{start.day} ~ {end.month}/{end.day}</b> <a class="btn s" href="/riley?date={nxt}">다음 주 →</a></div>'+('<button class="btn" onclick="na()">+ 학원 일정 추가</button>' if admin() else '')+'</div><div class="schedule">'
 for i,dn in enumerate(DAYS):
  day=start+timedelta(days=i);b+=f'<div class="sday"><div class="date">{day.month}/{day.day}</div><h3>{dn}요일</h3>'
  for r in by[dn]:
   a=''
   if admin():
    dat=' '.join('data-'+k+'="'+H(r[k])+'"' for k in ['id','day_of_week','start_time','end_time','academy','subject','location','notes']);a=f'<div style="margin-top:6px"><button class="btn s" {dat} onclick="ea(this)">수정</button><form method="post" action="/academy/{r["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
   tm=(H(r['start_time'])+('~'+H(r['end_time']) if r['end_time'] else '')) or '시간 미정';b+=f'<div class="lesson"><b>{tm} · {H(r["academy"])}</b>{H(r["subject"])}<br>{H(r["notes"])}{a}</div>'
  if admin():b+=f'<button class="btn s" onclick="na(\'{dn}\')">+ 추가</button>'
  b+='</div>'
 b+='</div>'
 if unknown:b+='<h3 style="margin-top:18px">요일/시간 확인 필요</h3>'+''.join(f'<div class="event"><div><b>{H(r["academy"])}</b> · {H(r["subject"])}<br>{H(r["notes"])}</div></div>' for r in unknown)
 if admin():b+='''<div class="modal" id="am"><div class="card"><div class="head"><h2>학원 일정</h2><button class="btn s" onclick="x('am')">닫기</button></div><form class="form" id="af" method="post"><label>요일<select name="day_of_week"><option>월</option><option>화</option><option>수</option><option>목</option><option>금</option><option>토</option><option>일</option><option>미정</option></select></label><label>학원/수업<input name="academy" required></label><label>시작<input type="time" name="start_time"></label><label>종료<input type="time" name="end_time"></label><label>과목<input name="subject"></label><label>장소<input name="location"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
 return page('지유 주간 학원 일정',b)

@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST' and secrets.compare_digest(request.form.get('password',''),ADMIN_PASSWORD):session['admin']=1;return redirect('/future')
 return page('관리자 로그인','<div class="card"><form method="post"><label>비밀번호<input type="password" name="password"></label><br><button class="btn">로그인</button></form></div>')
@app.route('/logout')
def logout():session.clear();return redirect('/future')
fields=['start_date','end_date','country','region','title','companions','trip_type','status','lodging','transport','notes']
@app.route('/trip/add',methods=['POST'])
def ta():must();c=db();v=[request.form.get(k,'') for k in fields];c.execute('insert into trips('+','.join(fields)+') values('+','.join('?'*len(v))+')',v);c.commit();c.close();return redirect(request.referrer or '/future')
@app.route('/trip/<int:i>/edit',methods=['POST'])
def te(i):must();c=db();v=[request.form.get(k,'') for k in fields];c.execute('update trips set '+','.join(k+'=?' for k in fields)+' where id=?',v+[i]);c.commit();c.close();return redirect(request.referrer or '/future')
@app.route('/trip/<int:i>/delete',methods=['POST'])
def td(i):must();c=db();c.execute('delete from trips where id=?',(i,));c.commit();c.close();return redirect(request.referrer or '/future')
ifields=['trip_id','item_date','day_label','time_text','title','place','detail','sort_order']
@app.route('/itinerary/add',methods=['POST'])
def ia():must();c=db();v=[request.form.get(k,'') for k in ifields];c.execute('insert into itinerary('+','.join(ifields)+') values('+','.join('?'*len(v))+')',v);c.commit();c.close();return redirect(request.referrer or '/future')
@app.route('/itinerary/<int:i>/edit',methods=['POST'])
def ie(i):must();c=db();v=[request.form.get(k,'') for k in ifields];c.execute('update itinerary set '+','.join(k+'=?' for k in ifields)+' where id=?',v+[i]);c.commit();c.close();return redirect(request.referrer or '/future')
@app.route('/itinerary/<int:i>/delete',methods=['POST'])
def ide(i):must();c=db();c.execute('delete from itinerary where id=?',(i,));c.commit();c.close();return redirect(request.referrer or '/future')
ef=['start_date','end_date','title','category','person','notes']
@app.route('/event/add',methods=['POST'])
def eva():must();c=db();v=[request.form.get(k,'') for k in ef];c.execute('insert into calendar_events('+','.join(ef)+') values('+','.join('?'*len(v))+')',v);c.commit();c.close();return redirect(request.referrer or '/calendar')
@app.route('/event/<int:i>/edit',methods=['POST'])
def eve(i):must();c=db();v=[request.form.get(k,'') for k in ef];c.execute('update calendar_events set '+','.join(k+'=?' for k in ef)+' where id=?',v+[i]);c.commit();c.close();return redirect(request.referrer or '/calendar')
@app.route('/event/<int:i>/delete',methods=['POST'])
def evd(i):must();c=db();c.execute('delete from calendar_events where id=?',(i,));c.commit();c.close();return redirect(request.referrer or '/calendar')
af=['day_of_week','start_time','end_time','academy','subject','location','notes']
@app.route('/academy/add',methods=['POST'])
def aa():must();c=db();v=[request.form.get(k,'') for k in af];c.execute('insert into academy('+','.join(af)+',active) values('+','.join('?'*len(v))+',1)',v);c.commit();c.close();return redirect(request.referrer or '/riley')
@app.route('/academy/<int:i>/edit',methods=['POST'])
def ae(i):must();c=db();v=[request.form.get(k,'') for k in af];c.execute('update academy set '+','.join(k+'=?' for k in af)+' where id=?',v+[i]);c.commit();c.close();return redirect(request.referrer or '/riley')
@app.route('/academy/<int:i>/delete',methods=['POST'])
def ad(i):must();c=db();c.execute('delete from academy where id=?',(i,));c.commit();c.close();return redirect(request.referrer or '/riley')
@app.route('/health')
def health():return 'ok'
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','8080')))
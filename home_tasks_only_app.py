import os, json, time, threading, sqlite3, calendar, html, secrets
import calendar as pycal
from pathlib import Path
from functools import wraps
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date, timedelta, time as dtime
from zoneinfo import ZoneInfo
import requests
from icalendar import Calendar
import recurring_ical_events
from flask import Flask, request, redirect, session, abort, Response, jsonify, send_from_directory
from pywebpush import webpush, WebPushException

# ===================== from app.py =====================
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
  base=qdate(request.args.get('date','')) or today;start=base-timedelta(days=weekday());end=start+timedelta(days=6);es=event_rows(start,end);by={start+timedelta(days=i):[] for i in range(7)}
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
 base=qdate(request.args.get('date','')) or date.today();start=base-timedelta(days=weekday());end=start+timedelta(days=6);prev=(start-timedelta(days=7)).isoformat();nxt=(start+timedelta(days=7)).isoformat()
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

# ===================== from gcal_wrapper.py =====================
KST = ZoneInfo('Asia/Seoul')
_CACHE = {'key': None, 'ts': 0, 'events': []}

# Keep Riley's weekly timetable as a true 7-column horizontal schedule even on mobile.
# Small screens scroll horizontally instead of stacking each day vertically.
CSS += '''
.schedule{display:grid;grid-template-columns:repeat(7,minmax(135px,1fr));gap:8px;overflow-x:auto;align-items:stretch;padding-bottom:6px;-webkit-overflow-scrolling:touch}
.sday{min-width:135px;min-height:230px}
@media(max-width:900px){.schedule{grid-template-columns:repeat(7,minmax(135px,1fr));overflow-x:auto}.sday{min-width:135px}}
@media(max-width:560px){.schedule{grid-template-columns:repeat(7,minmax(125px,1fr));overflow-x:auto}.sday{min-width:125px}}
'''

def _sources():
    raw = os.getenv('GCAL_ICS_SOURCES', '').strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [x for x in data if isinstance(x, dict) and x.get('name') and x.get('url')]
    except Exception:
        return []

def _as_date(v):
    if isinstance(v, datetime):
        if v.tzinfo:
            v = v.astimezone(KST)
        return v.date()
    if isinstance(v, date):
        return v
    return None

def _google_events(start, end):
    sources = _sources()
    if not sources:
        return []
    raw_key = os.getenv('GCAL_ICS_SOURCES', '')
    key = (start.isoformat(), end.isoformat(), raw_key)
    now = time.time()
    if _CACHE['key'] == key and now - _CACHE['ts'] < 300:
        return _CACHE['events']
    out = []
    window_start = datetime.combine(start, dtime.min, tzinfo=KST)
    window_end = datetime.combine(end + timedelta(days=1), dtime.min, tzinfo=KST)
    for src in sources:
        try:
            r = requests.get(src['url'], timeout=10, headers={'User-Agent': 'YJ-Family-Calendar/1.0'})
            r.raise_for_status()
            cal = Calendar.from_ical(r.content)
            events = recurring_ical_events.of(cal).between(window_start, window_end)
            for ev in events:
                if str(ev.get('STATUS', '')).upper() == 'CANCELLED':
                    continue
                ds = ev.decoded('DTSTART') if ev.get('DTSTART') else None
                de = ev.decoded('DTEND') if ev.get('DTEND') else ds
                sd = _as_date(ds)
                ed = _as_date(de)
                if not sd:
                    continue
                if isinstance(ds, date) and not isinstance(ds, datetime) and isinstance(de, date) and not isinstance(de, datetime) and ed and ed > sd:
                    ed = ed - timedelta(days=1)
                if not ed:
                    ed = sd
                if ed < start or sd > end:
                    continue
                title = str(ev.get('SUMMARY', '(제목 없음)'))
                loc = str(ev.get('LOCATION', '') or '')
                desc = str(ev.get('DESCRIPTION', '') or '')
                note = ' · '.join(x for x in [loc, desc[:180]] if x)
                out.append({
                    'id': 'g:' + str(ev.get('UID', '')),
                    'start_date': sd.isoformat(),
                    'end_date': ed.isoformat(),
                    'title': title,
                    'category': 'Google · ' + src['name'],
                    'person': src['name'],
                    'notes': note,
                    'source': 'google',
                })
        except Exception as e:
            print(f'Google Calendar ICS sync failed for {src.get("name")}: {e}', flush=True)
    out.sort(key=lambda x: (x['start_date'], x['title']))
    _CACHE.update({'key': key, 'ts': now, 'events': out})
    return out

def merged_event_rows(start, end):
    c = db()
    local = c.execute('select * from calendar_events where start_date<=? and end_date>=? order by start_date,id', (end.isoformat(), start.isoformat())).fetchall()
    c.close()
    rows = []
    for e in local:
        d = dict(e)
        d['source'] = 'local'
        rows.append(d)
    rows.extend(_google_events(start, end))
    rows.sort(key=lambda x: (x['start_date'], x['title']))
    return rows

def merged_event_modals(es):
    b = ''
    for e in es:
        source = e.get('source', 'local') if isinstance(e, dict) else 'local'
        a = ''
        if source == 'local' and admin():
            dat = ' '.join('data-' + k + '=\"' + H(e[k]) + '\"' for k in ['id','start_date','end_date','title','category','person','notes'])
            a = f'<div><button class="btn s" {dat} onclick="ee(this)">수정</button><form method="post" action="/event/{e["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
        badge = '<span class="pill">Google</span> ' if source == 'google' else ''
        b += f'<div class="event"><div><b>{H(e["start_date"])} ~ {H(e["end_date"])}</b> · {H(e["title"])} {badge}<span class="pill">{H(e["category"])}</span><br>{H(e["person"])} · {H(e["notes"])}</div>{a}</div>'
    if admin():
        b += '''<div class="modal" id="em"><div class="card"><div class="head"><h2>가족 일정</h2><button class="btn s" onclick="x('em')">닫기</button></div><form class="form" id="ef" method="post"><label>시작일<input type="date" name="start_date" required></label><label>종료일<input type="date" name="end_date" required></label><label class="full">일정명<input name="title" required></label><label>분류<input name="category"></label><label>사람<input name="person"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
    return b

event_rows = merged_event_rows
event_modals = merged_event_modals

@app.route('/gcal-status')
def gcal_status():
    sources = _sources()
    return {'connected': bool(sources), 'sources': [x['name'] for x in sources], 'refresh_seconds': 300}

# ===================== from photos_wrapper.py =====================
PHOTO_DIR = Path('/data/photos/bali-2026')
PHOTO_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = PHOTO_DIR / 'manifest.json'
CLIENT_ID = os.getenv('GOOGLE_PHOTOS_CLIENT_ID', '')
SCOPE = 'https://www.googleapis.com/auth/photospicker.mediaitems.readonly'

_orig_travels = travels

def travels_with_photos(done):
    out = _orig_travels(done)
    if done:
        needle = '<td>2026-08-08 ~ 2026-08-17</td><td>인도네시아</td><td>발리</td><td><b>발리</b></td>'
        repl = '<td>2026-08-08 ~ 2026-08-17</td><td>인도네시아</td><td>발리</td><td><b>발리</b><br><a class="btn s" style="display:inline-block;margin-top:6px" href="/photos/bali-2026" onclick="event.stopPropagation()">📷 사진</a></td>'
        out = out.replace(needle, repl, 1)
    return out
travels = travels_with_photos

def _photo_manifest():
    if not MANIFEST.exists():
        return []
    try:
        return json.loads(MANIFEST.read_text('utf-8'))
    except Exception:
        return []

def _gallery_html():
    items = _photo_manifest()
    if not items:
        return '<div style="padding:24px;text-align:center;color:#718097">아직 선택한 사진이 없습니다.</div>'
    cards=[]
    for x in items:
        cards.append(f'<div style="width:180px;flex:0 0 180px"><img src="/photos/bali-2026/file/{H(x["file"])}" style="width:180px;height:135px;object-fit:cover;border-radius:12px"><div style="font-size:11px;color:#718097;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{H(x.get("name",""))}</div></div>')
    return '<div style="display:flex;gap:10px;overflow-x:auto;padding:4px 0 10px">'+''.join(cards)+'</div>'

@app.route('/photos/bali-2026')
def bali_photos():
    ready = bool(CLIENT_ID)
    status = '<span class="pill">Google Photos 연결 준비됨</span>' if ready else '<span class="pill">OAuth 설정 필요</span>'
    body = f'''<div class="toolbar"><div><a class="btn s" href="/past">← 과거 여행</a></div><div>{status}</div></div>
<div class="card" style="max-width:none;margin:0 0 14px"><h2 style="margin-top:0">2026년 8월 발리 사진</h2><p style="color:#718097">Google Photos에서 이 여행 사진만 직접 선택하면 이 페이지에 저장해 두고 계속 볼 수 있게 만든 시험 기능입니다.</p>
<button id="pickBtn" class="btn" {'disabled style="opacity:.5"' if not ready else ''}>Google Photos에서 사진 선택</button><span id="msg" style="margin-left:10px;color:#718097;font-size:13px"></span></div>
<div class="card" style="max-width:none;margin:0"><h3 style="margin-top:0">선택된 사진</h3>{_gallery_html()}</div>
<script src="https://accounts.google.com/gsi/client" async defer></script>
<script>
const CLIENT_ID={json.dumps(CLIENT_ID)}; let accessToken='',pickerSession='';
function say(x){{document.getElementById('msg').textContent=x}}
async function beginPicker(token){{
  accessToken=token; say('선택창 준비 중...');
  const r=await fetch('/photos/picker/create',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{access_token:token}})}});
  const j=await r.json(); if(!r.ok){{say(j.error||'연결 실패');return}}
  pickerSession=j.id; window.open(j.pickerUri+'/autoclose','gphotos','width=1000,height=760'); say('Google Photos에서 사진을 고른 뒤 완료를 눌러줘'); poll();
}}
async function poll(){{
  if(!pickerSession)return; const r=await fetch('/photos/picker/status',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{access_token:accessToken,session_id:pickerSession}})}}); const j=await r.json();
  if(j.ready){{say('사진 저장 중...'); const s=await fetch('/photos/picker/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{access_token:accessToken,session_id:pickerSession}})}}); const sj=await s.json(); if(s.ok){{say(sj.saved+'장 저장 완료');setTimeout(()=>location.reload(),700)}}else say(sj.error||'저장 실패'); return}}
  setTimeout(poll,3000);
}}
window.addEventListener('load',()=>{{if(!CLIENT_ID)return; document.getElementById('pickBtn').onclick=()=>{{const tc=google.accounts.oauth2.initTokenClient({{client_id:CLIENT_ID,scope:{json.dumps(SCOPE)},callback:(resp)=>{{if(resp.access_token)beginPicker(resp.access_token);else say('Google 승인 실패')}}}});tc.requestAccessToken({{prompt:'consent'}})}}}});
</script>'''
    return page('2026 발리 사진', body)

@app.route('/photos/bali-2026/file/<path:name>')
def bali_photo_file(name):
    return send_from_directory(PHOTO_DIR, name)

@app.route('/photos/picker/create', methods=['POST'])
def picker_create():
    token=(request.get_json(silent=True) or {}).get('access_token','')
    if not token:
        return jsonify(error='Google 인증 토큰이 없습니다.'),400
    r=requests.post('https://photospicker.googleapis.com/v1/sessions',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},json={},timeout=15)
    if not r.ok:
        return jsonify(error='Picker 세션 생성 실패',detail=r.text[:300]),r.status_code
    j=r.json(); return jsonify(id=j.get('id'),pickerUri=j.get('pickerUri'))

@app.route('/photos/picker/status', methods=['POST'])
def picker_status():
    d=request.get_json(silent=True) or {};token=d.get('access_token','');sid=d.get('session_id','')
    if not token or not sid:
        return jsonify(error='인증 정보가 부족합니다.'),400
    r=requests.get('https://photospicker.googleapis.com/v1/sessions/'+sid,headers={'Authorization':'Bearer '+token},timeout=15)
    if not r.ok:
        return jsonify(error='Picker 상태 확인 실패'),r.status_code
    return jsonify(ready=bool(r.json().get('mediaItemsSet')))

def _picked_items(token,sid):
    items=[];page=''
    while True:
        params={'sessionId':sid,'pageSize':100}
        if page:
            params['pageToken']=page
        r=requests.get('https://photospicker.googleapis.com/v1/mediaItems',headers={'Authorization':'Bearer '+token},params=params,timeout=20)
        r.raise_for_status();j=r.json();items.extend(j.get('mediaItems',[]));page=j.get('nextPageToken','')
        if not page:
            break
    return items

@app.route('/photos/picker/save', methods=['POST'])
def picker_save():
    d=request.get_json(silent=True) or {};token=d.get('access_token','');sid=d.get('session_id','')
    if not token or not sid:
        return jsonify(error='인증 정보가 부족합니다.'),400
    try:
        items=_picked_items(token,sid);saved=[]
        for idx,it in enumerate(items):
            mf=it.get('mediaFile') or {};mime=mf.get('mimeType','')
            if not mime.startswith('image/'):
                continue
            name=mf.get('filename') or f'photo-{idx+1}.jpg';safe=''.join(c if c.isalnum() or c in '._-' else '_' for c in name)
            if not safe:
                safe=f'photo-{idx+1}.jpg'
            url=(mf.get('baseUrl') or '')+'=w2048-h2048'
            rr=requests.get(url,headers={'Authorization':'Bearer '+token},timeout=30)
            rr.raise_for_status();(PHOTO_DIR/safe).write_bytes(rr.content)
            saved.append({'id':it.get('id',''),'file':safe,'name':name,'createTime':it.get('createTime','')})
        MANIFEST.write_text(json.dumps(saved,ensure_ascii=False,indent=2),'utf-8')
        try:
            requests.delete('https://photospicker.googleapis.com/v1/sessions/'+sid,headers={'Authorization':'Bearer '+token},timeout=10)
        except Exception:
            pass
        return jsonify(saved=len(saved))
    except Exception as e:
        return jsonify(error='사진 저장 실패',detail=str(e)[:300]),500

# ===================== from enhancements_wrapper.py =====================
KST = ZoneInfo('Asia/Seoul')

CSS += '''
.homegrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px}.dashcard{background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:14px}.dashcard h3{margin:0 0 8px}.big{font-size:28px;font-weight:900;color:#0f4c81}.muted{color:#718097;font-size:12px}.tripdetail{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.timeline{display:grid;gap:8px}.tl{display:grid;grid-template-columns:110px 1fr;gap:10px;background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px}.triplink{color:#0f4c81;text-decoration:none;font-weight:800}.searchbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}.searchbar input,.searchbar select{max-width:220px}.mapbox{height:520px;border-radius:16px;overflow:hidden;border:1px solid #e4e9f0;background:#eef3f7}.statgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.stat{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:12px;text-align:center}.stat b{display:block;font-size:22px;color:#0f4c81}.sectiontitle{margin:22px 0 8px}.quicklinks{display:flex;gap:8px;flex-wrap:wrap}.quicklinks a{text-decoration:none}
@media(max-width:900px){.homegrid,.tripdetail,.statgrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.homegrid,.tripdetail,.statgrid{grid-template-columns:1fr}.tl{grid-template-columns:90px 1fr}.mapbox{height:420px}}
'''

def new_nav():
    return '<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b><div class="nav"><a href="/">홈</a><a href="/past">과거 여행</a><a href="/future">향후 여행</a><a href="/travel-map">여행 지도</a><a href="/travel-search">검색</a><a href="/calendar">가족 달력</a><a href="/riley">지유 주간 일정</a>'+('<a href="/logout">로그아웃</a>' if admin() else '<a href="/login">관리자</a>')+'</div></nav></header>'
nav = new_nav

# Add trips to the family calendar without duplicating them in calendar_events.
_prev_event_rows = event_rows

def event_rows_with_trips(start, end):
    rows = list(_prev_event_rows(start, end))
    c = db()
    trips = c.execute('select * from trips where start_date<=? and end_date>=? order by start_date,id',(end.isoformat(),start.isoformat())).fetchall()
    c.close()
    for r in trips:
        rows.append({'id':'trip:'+str(r['id']),'start_date':r['start_date'],'end_date':r['end_date'],'title':r['title'],'category':'여행','person':r['companions'],'notes':r['region'],'source':'trip','trip_id':r['id']})
    rows.sort(key=lambda x:(x['start_date'],x['title']))
    return rows
event_rows = event_rows_with_trips

def event_modals_with_trip(es):
    b=''
    for e in es:
        d=dict(e)
        source=d.get('source','local')
        title=H(d.get('title',''))
        if source=='trip':
            title=f'<a class="triplink" href="/trip/{d.get("trip_id")}">{title}</a>'
        badge = '<span class="pill">Google</span> ' if source=='google' else ('<span class="pill">여행</span> ' if source=='trip' else '')
        a=''
        if source=='local' and admin():
            dat=' '.join('data-'+k+'="'+H(d.get(k,''))+'"' for k in ['id','start_date','end_date','title','category','person','notes'])
            a=f'<div><button class="btn s" {dat} onclick="ee(this)">수정</button><form method="post" action="/event/{d["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
        b += f'<div class="event"><div><b>{H(d.get("start_date"))} ~ {H(d.get("end_date"))}</b> · {title} {badge}<span class="pill">{H(d.get("category"))}</span><br>{H(d.get("person"))} · {H(d.get("notes"))}</div>{a}</div>'
    if admin():
        b += '''<div class="modal" id="em"><div class="card"><div class="head"><h2>가족 일정</h2><button class="btn s" onclick="x('em')">닫기</button></div><form class="form" id="ef" method="post"><label>시작일<input type="date" name="start_date" required></label><label>종료일<input type="date" name="end_date" required></label><label class="full">일정명<input name="title" required></label><label>분류<input name="category"></label><label>사람<input name="person"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
    return b
event_modals = event_modals_with_trip

# Make trip titles link to a dedicated detail page.
_prev_travels = travels

def travels_with_links(done):
    out = _prev_travels(done)
    c=db(); rows=c.execute("select id,title from trips where status"+("='완료'" if done else "!='완료'")+" order by start_date desc").fetchall(); c.close()
    for r in rows:
        old='<td><b>'+H(r['title'])+'</b>'
        new='<td><b><a class="triplink" href="/trip/'+str(r['id'])+'" onclick="event.stopPropagation()">'+H(r['title'])+'</a></b>'
        out=out.replace(old,new,1)
    return out
travels = travels_with_links


def _timed_google(start,end,name='지유'):
    out=[]
    srcs=[s for s in _sources() if s.get('name')==name]
    ws=datetime.combine(start,dtime.min,tzinfo=KST); we=datetime.combine(end+timedelta(days=1),dtime.min,tzinfo=KST)
    for src in srcs:
        try:
            r=requests.get(src['url'],timeout=10,headers={'User-Agent':'YJ-Family-Calendar/1.0'}); r.raise_for_status()
            cal=Calendar.from_ical(r.content)
            for ev in recurring_ical_events.of(cal).between(ws,we):
                if str(ev.get('STATUS','')).upper()=='CANCELLED': continue
                ds=ev.decoded('DTSTART') if ev.get('DTSTART') else None
                de=ev.decoded('DTEND') if ev.get('DTEND') else ds
                if not isinstance(ds,datetime): continue
                if ds.tzinfo: ds=ds.astimezone(KST)
                if isinstance(de,datetime) and de.tzinfo: de=de.astimezone(KST)
                day=ds.date()
                if not(start<=day<=end): continue
                out.append({'date':day,'start':ds.strftime('%H:%M'),'end':de.strftime('%H:%M') if isinstance(de,datetime) else '', 'title':str(ev.get('SUMMARY','(제목 없음)')),'location':str(ev.get('LOCATION','') or '')})
        except Exception as e:
            print('Riley Google timetable sync failed:',e,flush=True)
    return out


def riley_week():
    q=qdate(request.args.get('date','')) or date.today()
    mon=q-timedelta(days=q.weekday()); sun=mon+timedelta(days=6)
    ge=_timed_google(mon,sun,'지유')
    by={mon+timedelta(days=i):[] for i in range(7)}
    for x in ge: by[x['date']].append(x)
    c=db(); local=c.execute('select * from academy where active=1 order by start_time,id').fetchall(); c.close()
    for i,dayname in enumerate(DAYS):
        d=mon+timedelta(days=i); existing={(x['title'],x['start']) for x in by[d]}
        for r in local:
            if r['day_of_week']!=dayname: continue
            key=(r['academy'],r['start_time'] or '')
            if key in existing: continue
            by[d].append({'date':d,'start':r['start_time'] or '시간 미정','end':r['end_time'] or '','title':r['academy'],'location':r['location'] or '', 'local_id':r['id'], 'notes':r['notes'] or ''})
        by[d].sort(key=lambda x:x['start'])
    prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
    body=f'<div class="toolbar"><div><a class="btn s" href="/riley?date={prev}">← 이전 주</a> <a class="btn s" href="/riley?date={nxt}">다음 주 →</a></div><b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div><div class="schedule">'
    for i,d in enumerate(by):
        body+=f'<div class="sday"><div class="date">{d.strftime("%m/%d")}</div><h3>{DAYS[i]}</h3>'
        if not by[d]: body+='<div class="muted">일정 없음</div>'
        for x in by[d]:
            tm=x['start']+(("–"+x['end']) if x.get('end') else '')
            body+=f'<div class="lesson"><b>{H(x["title"])}</b>{H(tm)}'+(f'<br><span class="muted">{H(x.get("location"))}</span>' if x.get('location') else '')+'</div>'
        if admin(): body+=f'<button class="btn s" onclick="na(\'{DAYS[i]}\')">+ 일정</button>'
        body+='</div>'
    body+='</div><p class="muted" style="margin-top:10px">지유 Google Calendar의 시간 일정이 우선 표시되고, 기존 학원 DB 일정은 빠진 항목만 보완합니다.</p>'
    return page('지유 주간 일정',body)

# Replace the existing /riley handler regardless of its function name.
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/riley':
        app.view_functions[rule.endpoint]=riley_week

@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    c=db(); r=c.execute('select * from trips where id=?',(trip_id,)).fetchone(); its=c.execute('select * from itinerary where trip_id=? order by sort_order,item_date,id',(trip_id,)).fetchall(); c.close()
    if not r: return abort(404)
    meta=f'''<div class="tripdetail"><div class="dashcard"><span class="muted">여행 일자</span><h3>{H(r['start_date'])} ~ {H(r['end_date'])}</h3></div><div class="dashcard"><span class="muted">지역</span><h3>{H(r['country'])} · {H(r['region'])}</h3></div><div class="dashcard"><span class="muted">함께</span><h3>{H(r['companions'])}</h3></div><div class="dashcard"><span class="muted">숙소</span><h3>{H(r['lodging']) or '-'}</h3></div><div class="dashcard"><span class="muted">교통/항공</span><h3>{H(r['transport']) or '-'}</h3></div><div class="dashcard"><span class="muted">상태</span><h3>{H(r['status'])}</h3></div></div>'''
    tl='<h2 class="sectiontitle">일자별 일정</h2><div class="timeline">'
    if not its: tl+='<div class="dashcard muted">아직 세부 일정이 없습니다.</div>'
    for x in its:
        left=' · '.join(v for v in [x['item_date'],x['day_label'],x['time_text']] if v)
        tl+=f'<div class="tl"><div><b>{H(left)}</b></div><div><b>{H(x["title"])}</b>'+(f'<br>{H(x["place"])}' if x['place'] else '')+(f'<br><span class="muted">{H(x["detail"])}</span>' if x['detail'] else '')+'</div></div>'
    tl+='</div>'
    extra=f'<h2 class="sectiontitle">메모</h2><div class="dashcard">{H(r["notes"]) or "-"}</div>'
    if r['start_date']=='2026-08-08' and '발리' in (r['title'] or ''):
        extra+= '<div class="quicklinks" style="margin-top:12px"><a class="btn" href="/photos/bali-2026">📷 발리 사진 갤러리</a></div>'
    return page(r['title'],f'<div class="toolbar"><a class="btn s" href="/past">← 여행 목록</a></div>'+meta+tl+extra)

@app.route('/travel-search')
def travel_search():
    q=(request.args.get('q') or '').strip(); status=(request.args.get('status') or '').strip(); kind=(request.args.get('kind') or '').strip()
    c=db(); rows=c.execute('select * from trips order by start_date desc').fetchall(); c.close()
    def ok(r):
        text=' '.join(str(r[k] or '') for k in ['country','region','title','companions','lodging','notes'])
        return (not q or q.lower() in text.lower()) and (not status or r['status']==status) and (not kind or r['trip_type']==kind)
    rows=[r for r in rows if ok(r)]
    body=f'''<form class="searchbar" method="get"><input name="q" placeholder="국가·도시·여행명 검색" value="{H(q)}"><select name="kind"><option value="">국내/해외 전체</option><option {'selected' if kind=='해외' else ''}>해외</option><option {'selected' if kind=='국내' else ''}>국내</option></select><select name="status"><option value="">상태 전체</option>'''
    for s in ['완료','예정','검토 중','장기 계획']: body+=f'<option {"selected" if status==s else ""}>{s}</option>'
    body+='</select><button class="btn">검색</button></form>'
    body+=f'<div class="box"><table><tr><th>일자</th><th>국가</th><th>지역</th><th>여행명</th><th>상태</th></tr>'
    for r in rows: body+=f'<tr><td>{H(r["start_date"])}</td><td>{H(r["country"])}</td><td>{H(r["region"])}</td><td><a class="triplink" href="/trip/{r["id"]}">{H(r["title"])}</a></td><td>{H(r["status"])}</td></tr>'
    body+='</table></div>'
    return page('여행 검색',body)

COUNTRY_COORDS={
'한국':(36.5,127.8),'대한민국':(36.5,127.8),'일본':(36.2,138.3),'대만':(23.7,121.0),'홍콩':(22.32,114.17),'마카오':(22.20,113.55),'중국':(35.9,104.2),'태국':(15.9,100.9),'베트남':(16.0,108.2),'인도네시아':(-2.5,118.0),'미국':(39.8,-98.6),'스페인':(40.4,-3.7),'이탈리아':(42.8,12.8),'싱가포르':(1.35,103.82),'호주':(-25.3,133.8),'체코':(49.8,15.5),'오스트리아':(47.5,14.5),'헝가리':(47.2,19.5)
}

def _country_parts(s):
    if not s: return []
    for sep in ['·','/','+','&',',']:
        s=s.replace(sep,'|')
    return [x.strip() for x in s.split('|') if x.strip()]

@app.route('/travel-map')
def travel_map():
    c=db(); rows=c.execute("select id,country,region,title,start_date from trips where status='완료' order by start_date").fetchall(); c.close()
    pins=[]
    for r in rows:
        for p in _country_parts(r['country']):
            key=p
            if key in COUNTRY_COORDS:
                lat,lon=COUNTRY_COORDS[key];pins.append({'lat':lat,'lon':lon,'country':key,'title':r['title'],'region':r['region'],'id':r['id'],'date':r['start_date']})
    data=json.dumps(pins,ensure_ascii=False)
    body=f'''<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><div id="map" class="mapbox"></div><p class="muted">완료된 가족 여행의 국가를 지도에 표시합니다. 핀을 누르면 여행 상세로 이동할 수 있어요.</p><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>const pins={data};const m=L.map('map').setView([25,35],2);L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:18,attribution:'&copy; OpenStreetMap'}}).addTo(m);pins.forEach(p=>L.marker([p.lat,p.lon]).addTo(m).bindPopup(`<b>${{p.title}}</b><br>${{p.date}} · ${{p.region||p.country}}<br><a href="/trip/${{p.id}}">여행 상세</a>`));</script>'''
    return page('우리 가족 여행 지도',body)


def dashboard():
    today=date.today(); c=db(); trips=c.execute('select * from trips order by start_date').fetchall(); done=[r for r in trips if r['status']=='완료']; future=[r for r in trips if r['status']!='완료' and qdate(r['start_date']) and qdate(r['start_date'])>=today]; c.close()
    nxt=future[0] if future else None
    dday=(qdate(nxt['start_date'])-today).days if nxt else None
    countries=set()
    for r in done:
        countries.update(_country_parts(r['country']))
    overseas=sum(1 for r in done if r['trip_type']=='해외')
    domestic=sum(1 for r in done if r['trip_type']=='국내')
    nextcard='<div class="dashcard"><h3>다음 여행</h3><div class="muted">등록된 예정 여행 없음</div></div>'
    if nxt:
        nextcard=f'<div class="dashcard"><h3>다음 여행</h3><div class="big">D-{dday}</div><a class="triplink" href="/trip/{nxt["id"]}">{H(nxt["title"])}</a><div class="muted">{H(nxt["start_date"])} · {H(nxt["region"])}</div></div>'
    calcard='<div class="dashcard"><h3>이번 주 가족 일정</h3><div class="muted">관리자 로그인 후 확인</div></div>'
    rileycard='<div class="dashcard"><h3>지유 주간 일정</h3><div class="muted">관리자 로그인 후 확인</div></div>'
    if admin():
        mon=today-timedelta(days=today.weekday()); sun=mon+timedelta(days=6); ev=event_rows(mon,sun)[:5]
        calcard='<div class="dashcard"><h3>이번 주 가족 일정</h3>'+(''.join(f'<div style="margin:6px 0"><b>{H(x["start_date"])}</b> · {H(x["title"])}</div>' for x in ev) if ev else '<div class="muted">일정 없음</div>')+'<a class="btn s" href="/calendar">달력 보기</a></div>'
        rileycard='<div class="dashcard"><h3>지유 주간 일정</h3><a class="btn s" href="/riley">시간표 보기</a></div>'
    body='<div class="homegrid">'+nextcard+calcard+rileycard+'</div>'
    body+=f'<div class="statgrid"><div class="stat"><b>{len(done)}</b><span class="muted">완료 여행</span></div><div class="stat"><b>{len(countries)}</b><span class="muted">방문 국가</span></div><div class="stat"><b>{overseas}</b><span class="muted">해외 여행</span></div><div class="stat"><b>{domestic}</b><span class="muted">국내 여행</span></div></div>'
    body+='<h2 class="sectiontitle">바로가기</h2><div class="quicklinks"><a class="btn" href="/future">향후 여행</a><a class="btn s" href="/travel-map">여행 지도</a><a class="btn s" href="/travel-search">여행 검색</a><a class="btn s" href="/photos/bali-2026">2026 발리 사진</a></div>'
    return page('우리 가족 기록',body)

# Replace the old root redirect with the dashboard.
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=dashboard

# ===================== from authless_wrapper.py =====================
# This family site is intentionally open: no admin session is required.
admin = lambda: True
must = lambda: None


def open_nav():
    return '<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b><div class="nav"><a href="/">홈</a><a href="/past">과거 여행</a><a href="/future">향후 여행</a><a href="/travel-map">여행 지도</a><a href="/travel-search">검색</a><a href="/calendar">가족 달력</a><a href="/riley">지유 주간 일정</a></div></nav></header>'

nav = open_nav

# Disable the old login/logout pages as well, so authentication disappears
# from both navigation and direct URL access.
def _go_home():
    return redirect('/')

for rule in list(app.url_map.iter_rules()):
    if rule.rule in ('/login', '/logout'):
        app.view_functions[rule.endpoint] = _go_home

# ===================== from family_ui_wrapper.py =====================
CSS += '''
.family-summary{display:grid;grid-template-columns:1.15fr 1.85fr;gap:12px;margin-bottom:14px}.summary-card{background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:14px}.summary-card h3{margin:0 0 10px}.summary-row{display:flex;gap:8px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #edf1f5}.summary-row:last-child{border-bottom:0}.dot{width:9px;height:9px;border-radius:50%;margin-top:5px;flex:0 0 9px}.dot-yj{background:#315c9b}.dot-지유{background:#e98755}.dot-보미{background:#9a66ad}.dot-혜온{background:#46a081}.dot-가족{background:#c99a35}.dot-여행{background:#d64f5b}.dot-local{background:#7d8793}.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:#6f7c8f;margin:8px 0 14px}.legend span{display:flex;gap:5px;align-items:center}.legend i{width:8px;height:8px;border-radius:50%;display:inline-block}.cal-toolbar{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}.cal-nav{display:flex;gap:6px;align-items:center}.cal-title{font-size:20px;font-weight:900}.family-month{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));border-left:1px solid #e4e9f0;border-top:1px solid #e4e9f0;background:#fff;border-radius:14px;overflow:hidden}.fm-head{padding:8px;text-align:center;font-size:12px;color:#748196;background:#f8fafc;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0}.fm-cell{min-height:118px;padding:6px;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0;overflow:hidden}.fm-cell.out{background:#fafbfd;color:#b2bac5}.fm-num{font-size:12px;font-weight:800;margin-bottom:4px}.fm-num.today{display:inline-block;background:#0f4c81;color:white;border-radius:999px;padding:3px 7px}.fm-event{font-size:10px;padding:4px 5px;margin:3px 0;border-radius:6px;background:#edf2f7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-left:3px solid #7d8793}.fm-event.yj{background:#edf3fc;border-left-color:#315c9b}.fm-event.지유{background:#fff2eb;border-left-color:#e98755}.fm-event.보미{background:#f7eff9;border-left-color:#9a66ad}.fm-event.혜온{background:#edf8f4;border-left-color:#46a081}.fm-event.가족{background:#fff7df;border-left-color:#c99a35}.fm-event.여행{background:#fff0f1;border-left-color:#d64f5b}.week-cards{display:grid;grid-template-columns:repeat(7,minmax(145px,1fr));gap:8px;overflow-x:auto;padding-bottom:8px}.week-card{min-width:145px;background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:10px}.week-card.today{border:2px solid #0f4c81}.week-date{font-size:11px;color:#7b8797}.week-card h3{margin:4px 0 9px}.event-chip{border-radius:9px;padding:8px;margin:6px 0;background:#f2f5f8;font-size:12px;border-left:4px solid #7d8793}.event-chip.yj{border-left-color:#315c9b}.event-chip.지유{border-left-color:#e98755}.event-chip.보미{border-left-color:#9a66ad}.event-chip.혜온{border-left-color:#46a081}.event-chip.가족{border-left-color:#c99a35}.event-chip.여행{border-left-color:#d64f5b}.riley-toolbar{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px}.riley-week{display:grid;grid-template-columns:repeat(7,minmax(150px,1fr));gap:8px;overflow-x:auto;padding-bottom:8px;-webkit-overflow-scrolling:touch}.rday{min-width:150px;background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:10px}.rday.today{border:2px solid #e98755}.rdate{font-size:11px;color:#7c8796}.rday h3{margin:4px 0 10px}.rlesson{background:#fff2eb;border-left:4px solid #e98755;border-radius:9px;padding:8px;margin-bottom:7px;font-size:12px}.rlesson.local{background:#f2f5f8;border-left-color:#7d8793}.rlesson b{display:block;margin-bottom:3px}.rmeta{color:#738095;font-size:11px;line-height:1.45}.row-actions{display:flex;gap:5px;margin-top:6px}.needs-check{margin-top:14px;background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:12px}.needs-check h3{margin:0 0 8px}.needs-item{display:flex;justify-content:space-between;gap:8px;padding:8px 0;border-bottom:1px solid #edf1f5}.needs-item:last-child{border-bottom:0}@media(max-width:700px){.family-summary{grid-template-columns:1fr}.fm-cell{min-height:90px;padding:4px}.fm-event{font-size:9px;padding:3px 4px}.family-month{min-width:720px}.calendar-scroll{overflow-x:auto}.week-cards{grid-template-columns:repeat(7,minmax(140px,1fr))}.riley-week{grid-template-columns:repeat(7,minmax(145px,1fr))}}
'''

PEOPLE = ['YJ','지유','보미','혜온','가족']

def _kind(e):
    d=dict(e)
    if d.get('source')=='trip' or d.get('category')=='여행': return '여행'
    p=(d.get('person') or '').strip()
    if p in PEOPLE: return p
    return 'local'

def _kind_class(k):
    return 'yj' if k=='YJ' else k

def _overlaps(e,d):
    try:
        s=datetime.strptime(str(e['start_date'])[:10],'%Y-%m-%d').date(); en=datetime.strptime(str(e['end_date'])[:10],'%Y-%m-%d').date()
        return s<=d<=en
    except: return False

def _event_line(e, show_date=False):
    d=dict(e); k=_kind(d); title=H(d.get('title',''))
    if d.get('source')=='trip' and d.get('trip_id'):
        title=f'<a class="triplink" href="/trip/{d["trip_id"]}">{title}</a>'
    prefix=f'<b>{H(d.get("start_date"))}</b> · ' if show_date else ''
    note=H(d.get('notes',''))
    return f'<div class="summary-row"><span class="dot dot-{_kind_class(k)}"></span><div>{prefix}{title}<div class="muted">{H(k)}'+((' · '+note) if note else '')+'</div></div></div>'

def family_calendar():
    view=(request.args.get('view') or 'month').lower()
    q=qdate(request.args.get('date','')) or date.today()
    today=date.today()
    if view=='week':
        start=q-timedelta(days=q.weekday()); end=start+timedelta(days=6)
        prev=(start-timedelta(days=7)).isoformat(); nxt=(start+timedelta(days=7)).isoformat(); title=f'{start.strftime("%Y.%m.%d")} ~ {end.strftime("%m.%d")}'
    else:
        start=date(q.year,q.month,1); last=pycal.monthrange(q.year,q.month)[1]; end=date(q.year,q.month,last)
        pm=(start-timedelta(days=1)).replace(day=1); nm=(end+timedelta(days=1)).replace(day=1); prev=pm.isoformat(); nxt=nm.isoformat(); title=f'{q.year}년 {q.month}월'
    events=list(event_rows(start,end))

    # Today + this week summaries always use live merged calendar rows.
    week0=today-timedelta(days=today.weekday()); week1=week0+timedelta(days=6)
    week_events=list(event_rows(week0,week1))
    today_events=[e for e in week_events if _overlaps(e,today)]
    summary='<div class="family-summary"><div class="summary-card"><h3>오늘 일정</h3>'
    summary += ''.join(_event_line(e) for e in today_events) if today_events else '<div class="muted">오늘 일정 없음</div>'
    summary += '</div><div class="summary-card"><h3>이번주 일정</h3>'
    summary += ''.join(_event_line(e,True) for e in week_events) if week_events else '<div class="muted">이번주 일정 없음</div>'
    summary += '</div></div>'

    legend='<div class="legend">'+''.join(f'<span><i class="dot-{_kind_class(k)}"></i>{k}</span>' for k in PEOPLE+['여행'])+'</div>'
    tabs=f'<div class="seg"><a class="{"on" if view=="month" else ""}" href="/calendar?view=month&date={q.isoformat()}">월</a><a class="{"on" if view=="week" else ""}" href="/calendar?view=week&date={q.isoformat()}">주</a></div>'
    toolbar=f'<div class="cal-toolbar"><div class="cal-nav"><a class="btn s" href="/calendar?view={view}&date={prev}">←</a><a class="btn s" href="/calendar?view={view}&date={today.isoformat()}">오늘</a><a class="btn s" href="/calendar?view={view}&date={nxt}">→</a></div><div class="cal-title">{title}</div>{tabs}</div>'

    if view=='week':
        cal='<div class="week-cards">'
        for i in range(7):
            d=start+timedelta(days=i); de=[e for e in events if _overlaps(e,d)]
            cal+=f'<div class="week-card {"today" if d==today else ""}"><div class="week-date">{d.strftime("%m/%d")}</div><h3>{DAYS[i]}</h3>'
            if not de: cal+='<div class="muted">일정 없음</div>'
            for e in de:
                dd=dict(e); k=_kind(dd); cal+=f'<div class="event-chip {_kind_class(k)}"><b>{H(dd.get("title"))}</b><div class="muted">{H(k)}</div></div>'
            cal+='</div>'
        cal+='</div>'
    else:
        cal='<div class="calendar-scroll"><div class="family-month">'+''.join(f'<div class="fm-head">{x}</div>' for x in ['월','화','수','목','금','토','일'])
        grid_start=start-timedelta(days=start.weekday())
        for i in range(42):
            d=grid_start+timedelta(days=i); out=d.month!=q.month; de=[e for e in events if _overlaps(e,d)]
            num=f'<span class="fm-num {"today" if d==today else ""}">{d.day}</span>'
            cal+=f'<div class="fm-cell {"out" if out else ""}">{num}'
            for e in de[:4]:
                dd=dict(e); k=_kind(dd); cal+=f'<div class="fm-event {_kind_class(k)}" title="{H(dd.get("title"))}">{H(dd.get("title"))}</div>'
            if len(de)>4: cal+=f'<div class="muted">+{len(de)-4}개</div>'
            cal+='</div>'
        cal+='</div></div>'

    all_list='<div class="toolbar" style="margin-top:16px"><b>일정 목록 · '+str(len(events))+'건</b><button class="btn" onclick="ne()">+ 일정 추가</button></div>'+event_modals(events)
    return page('가족 달력', summary+toolbar+legend+cal+all_list)


def academy_modal():
    opts=''.join(f'<option>{d}</option>' for d in DAYS)+ '<option>미정</option>'
    return f'''<div class="modal" id="am"><div class="card"><div class="head"><h2>지유 일정 추가/수정</h2><button class="btn s" onclick="x('am')">닫기</button></div><form class="form" id="af" method="post"><label>요일<select name="day_of_week">{opts}</select></label><label>시작 시간<input type="time" name="start_time"></label><label>종료 시간<input type="time" name="end_time"></label><label>학원/일정명<input name="academy" required></label><label>과목<input name="subject"></label><label>장소<input name="location"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''

def riley_week():
    q=qdate(request.args.get('date','')) or date.today(); today=date.today()
    mon=q-timedelta(days=q.weekday()); sun=mon+timedelta(days=6)
    ge=_timed_google(mon,sun,'지유')
    by={mon+timedelta(days=i):[] for i in range(7)}
    for x in ge:
        x=dict(x); x['source']='google'; by[x['date']].append(x)
    c=db(); local=c.execute('select * from academy where active=1 order by start_time,id').fetchall(); c.close()
    unknown=[]
    for r in local:
        dayname=(r['day_of_week'] or '').strip()
        if dayname not in DAYS:
            unknown.append(r); continue
        d=mon+timedelta(days=DAYS.index(dayname))
        # Deduplicate local fallback when Google has same title and time, or very similar title at same time.
        st=r['start_time'] or ''
        duplicate=False
        for x in by[d]:
            if x.get('start','')==st and (x.get('title','').strip()==(r['academy'] or '').strip() or (r['academy'] or '') in x.get('title','') or x.get('title','') in (r['academy'] or '')):
                duplicate=True; break
        if not duplicate:
            by[d].append({'date':d,'start':st,'end':r['end_time'] or '','title':r['academy'] or '일정','location':r['location'] or '', 'subject':r['subject'] or '', 'notes':r['notes'] or '', 'source':'local','local_id':r['id'], 'day_of_week':dayname})
    for d in by: by[d].sort(key=lambda x:(x.get('start') or '99:99',x.get('title','')))
    prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
    head=f'<div class="riley-toolbar"><div><a class="btn s" href="/riley?date={prev}">← 이전 주</a> <a class="btn s" href="/riley?date={today.isoformat()}">이번 주</a> <a class="btn s" href="/riley?date={nxt}">다음 주 →</a></div><b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div>'
    body=head+'<div class="riley-week">'
    for i in range(7):
        d=mon+timedelta(days=i); body+=f'<div class="rday {"today" if d==today else ""}"><div class="rdate">{d.strftime("%m/%d")}</div><h3>{DAYS[i]}</h3>'
        if not by[d]: body+='<div class="muted">일정 없음</div>'
        for x in by[d]:
            src=x.get('source'); tm=x.get('start') or '시간 미정'; tm += ('–'+x.get('end')) if x.get('end') else ''
            cls='rlesson' if src=='google' else 'rlesson local'
            body+=f'<div class="{cls}"><b>{H(x.get("title"))}</b><div>{H(tm)}</div>'
            meta=' · '.join(v for v in [x.get('subject',''),x.get('location',''),x.get('notes','')] if v)
            if meta: body+=f'<div class="rmeta">{H(meta)}</div>'
            if src=='local':
                rid=x['local_id']; dat=' '.join('data-'+k+'="'+H(x.get(k,''))+'"' for k in ['day_of_week','start','end','title','subject','location','notes'])
                # remap to fields expected by existing ea() JS
                dat=f'data-id="{rid}" data-day_of_week="{H(x.get("day_of_week"))}" data-start_time="{H(x.get("start"))}" data-end_time="{H(x.get("end"))}" data-academy="{H(x.get("title"))}" data-subject="{H(x.get("subject"))}" data-location="{H(x.get("location"))}" data-notes="{H(x.get("notes"))}"'
                body+=f'<div class="row-actions"><button class="btn s" {dat} onclick="ea(this)">수정</button><form method="post" action="/academy/{rid}/delete" onsubmit="return confirm(\'삭제할까요?\')"><button class="btn d">삭제</button></form></div>'
            body+='</div>'
        body+=f'<button class="btn s" onclick="na(\'{DAYS[i]}\')">+ 일정</button></div>'
    body+='</div>'
    if unknown:
        body+='<div class="needs-check"><h3>요일/시간 확인 필요</h3>'
        for r in unknown:
            dat=f'data-id="{r["id"]}" data-day_of_week="{H(r["day_of_week"])}" data-start_time="{H(r["start_time"])}" data-end_time="{H(r["end_time"])}" data-academy="{H(r["academy"])}" data-subject="{H(r["subject"])}" data-location="{H(r["location"])}" data-notes="{H(r["notes"])}"'
            body+=f'<div class="needs-item"><div><b>{H(r["academy"])}</b><div class="muted">요일 또는 시간이 미정이라 주간표 밖에 표시</div></div><div class="row-actions"><button class="btn s" {dat} onclick="ea(this)">수정</button><form method="post" action="/academy/{r["id"]}/delete"><button class="btn d">삭제</button></form></div></div>'
        body+='</div>'
    body+='<p class="muted" style="margin-top:10px">주황색은 지유 Google Calendar, 회색은 기존 학원 DB 보완 일정입니다. 같은 시간·같은 일정은 중복 표시하지 않습니다.</p>'+academy_modal()
    return page('지유 주간 일정',body)

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/calendar': app.view_functions[rule.endpoint]=family_calendar
    elif rule.rule=='/riley': app.view_functions[rule.endpoint]=riley_week

# ===================== from main_app.py =====================
KST = ZoneInfo('Asia/Seoul')
DB_PATH = DB_PATH
BACKUP_DIR = os.path.join(os.path.dirname(DB_PATH) or '/data', 'backups')
BACKUP_LOCK = threading.Lock()
SYNC_LOCK = threading.Lock()
SYNC_STATE = {'checked_at': None, 'sources': [], 'ok': False}


# ===== navigation / shared UI =====
def final_nav():
    return ('<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b>'
            '<div class="nav">'
            '<a href="/past">과거 여행</a>'
            '<a href="/future">향후 여행</a>'
            '<a href="/calendar">가족 달력</a>'
            '<a href="/riley">지유 주간 일정</a>'
            '</div></nav></header>')

nav = final_nav
CSS += '''
.trip-actions{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}.trip-edit-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.trip-edit-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px}.trip-edit-card .label{font-size:11px;color:#748196;margin-bottom:4px}.itinerary-row{display:grid;grid-template-columns:120px 1fr auto;gap:10px;align-items:start;background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px;margin:8px 0}.itinerary-actions{display:flex;gap:5px;flex-wrap:wrap}.nav a{font-weight:650}.calendar-scroll{border-radius:14px}.family-month{min-width:700px}.date-quality{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:11px 12px;margin-bottom:12px}.date-q-form{display:flex;gap:5px}.date-q{border:1px solid #d5dde7;background:#fff;color:#65758b;border-radius:8px;padding:7px 10px;font:inherit;font-size:12px;cursor:pointer}.date-q.on{background:#0f4c81;color:#fff;border-color:#0f4c81;font-weight:800}.status-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}.status-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px;display:grid;gap:7px}
@media(max-width:700px){nav{padding:9px 10px;align-items:center}.nav{max-width:74vw;gap:2px}.nav a{font-size:12px;padding:7px 8px}.wrap{padding:12px 10px 40px}.hero{padding:15px;border-radius:14px;margin-bottom:12px}.hero h1{font-size:22px}.toolbar,.cal-toolbar,.riley-toolbar{gap:6px}.btn,.nav a{min-height:34px}.trip-edit-grid{grid-template-columns:1fr 1fr}.itinerary-row{grid-template-columns:95px 1fr}.itinerary-actions{grid-column:1/-1}.box{border-radius:12px;-webkit-overflow-scrolling:touch}.box table{min-width:760px}th,td{padding:8px;font-size:12px}.family-month{min-width:660px}.fm-cell{min-height:88px}.riley-week{grid-template-columns:repeat(7,minmax(138px,1fr))}.rday{min-width:138px;padding:8px}.rlesson{padding:7px}.card{padding:13px;margin:2vh auto}.form{gap:8px}.date-quality{align-items:flex-start;flex-direction:column}.date-q-form{width:100%}.date-q{flex:1}.status-grid{grid-template-columns:1fr}}
@media(max-width:430px){.trip-edit-grid{grid-template-columns:1fr}.nav{max-width:70vw}.family-month{min-width:620px}.box table{min-width:720px}}
'''


# ===== Riley recurring Google schedule =====
def recurring_riley_events(start, end, name='지유'):
    out = []
    sources = [s for s in _sources() if s.get('name') == name]
    window_start = datetime.combine(start, dtime.min, tzinfo=KST)
    window_end = datetime.combine(end + timedelta(days=1), dtime.min, tzinfo=KST)
    for src in sources:
        try:
            r = requests.get(src['url'], timeout=10, headers={'User-Agent':'YJ-Family-Calendar/1.0'})
            r.raise_for_status()
            cal = Calendar.from_ical(r.content)
            recurring_uids = {str(c.get('UID','')).strip() for c in cal.walk('VEVENT') if c.get('RRULE') and str(c.get('UID','')).strip()}
            for ev in recurring_ical_events.of(cal).between(window_start, window_end):
                if str(ev.get('STATUS','')).upper() == 'CANCELLED':
                    continue
                if str(ev.get('UID','')).strip() not in recurring_uids:
                    continue
                ds = ev.decoded('DTSTART') if ev.get('DTSTART') else None
                de = ev.decoded('DTEND') if ev.get('DTEND') else ds
                if not isinstance(ds, datetime):
                    continue
                ds = ds.astimezone(KST) if ds.tzinfo else ds.replace(tzinfo=KST)
                if isinstance(de, datetime):
                    de = de.astimezone(KST) if de.tzinfo else de.replace(tzinfo=KST)
                if start <= ds.date() <= end:
                    out.append({'date':ds.date(),'start':ds.strftime('%H:%M'),'end':de.strftime('%H:%M') if isinstance(de,datetime) else '', 'title':str(ev.get('SUMMARY','(제목 없음)')),'location':str(ev.get('LOCATION','') or ''),'notes':str(ev.get('DESCRIPTION','') or ''),'recurring':True})
        except Exception as e:
            print(f'Riley recurring sync failed: {type(e).__name__}', flush=True)
    out.sort(key=lambda x:(x['date'],x['start'],x['title']))
    return out

_timed_google = recurring_riley_events


# ===== family calendar: calendar only, Riley academy recurring events excluded =====
def family_events(start, end):
    events = list(event_rows(start, end))
    recurring_keys = {(x['date'].isoformat(), (x.get('title') or '').strip()) for x in recurring_riley_events(start, end, '지유')}
    out = []
    for e in events:
        d = dict(e)
        is_riley_google = d.get('source') == 'google' and (d.get('person') or '').strip() == '지유'
        key = (str(d.get('start_date') or '')[:10], (d.get('title') or '').strip())
        if is_riley_google and key in recurring_keys:
            continue
        out.append(e)
    return out


def family_calendar():
    view = (request.args.get('view') or 'month').lower()
    q = qdate(request.args.get('date','')) or date.today()
    today = date.today()
    if view == 'week':
        start = q - timedelta(days=q.weekday()); end = start + timedelta(days=6)
        prev=(start-timedelta(days=7)).isoformat(); nxt=(start+timedelta(days=7)).isoformat()
        title=f'{start.strftime("%Y.%m.%d")} ~ {end.strftime("%m.%d")}'
    else:
        start=date(q.year,q.month,1); end=date(q.year,q.month,pycal.monthrange(q.year,q.month)[1])
        prev=(start-timedelta(days=1)).replace(day=1).isoformat(); nxt=(end+timedelta(days=1)).replace(day=1).isoformat()
        title=f'{q.year}년 {q.month}월'
    events=family_events(start,end)
    tabs=(f'<div class="seg"><a class="{"on" if view=="month" else ""}" href="/calendar?view=month&date={q.isoformat()}">월</a><a class="{"on" if view=="week" else ""}" href="/calendar?view=week&date={q.isoformat()}">주</a></div>')
    toolbar=(f'<div class="cal-toolbar"><div class="cal-nav"><a class="btn s" href="/calendar?view={view}&date={prev}">←</a><a class="btn s" href="/calendar?view={view}&date={today.isoformat()}">오늘</a><a class="btn s" href="/calendar?view={view}&date={nxt}">→</a></div><div class="cal-title">{title}</div>{tabs}</div>')
    if view == 'week':
        cal='<div class="week-cards">'
        for i in range(7):
            d=start+timedelta(days=i); de=[e for e in events if _overlaps(e,d)]
            cal+=f'<div class="week-card {"today" if d==today else ""}"><div class="week-date">{d.strftime("%m/%d")}</div><h3>{DAYS[i]}</h3>'
            if not de: cal+='<div class="muted">일정 없음</div>'
            for e in de:
                dd=dict(e); k=_kind(dd)
                cal+=f'<div class="event-chip {_kind_class(k)}"><b>{H(dd.get("title"))}</b><div class="muted">{H(k)}</div></div>'
            cal+='</div>'
        cal+='</div>'
    else:
        cal='<div class="calendar-scroll"><div class="family-month">'+''.join(f'<div class="fm-head">{x}</div>' for x in ['월','화','수','목','금','토','일'])
        grid_start=start-timedelta(days=start.weekday())
        for i in range(42):
            d=grid_start+timedelta(days=i); de=[e for e in events if _overlaps(e,d)]
            cal+=f'<div class="fm-cell {"out" if d.month!=q.month else ""}"><span class="fm-num {"today" if d==today else ""}">{d.day}</span>'
            for e in de[:5]:
                dd=dict(e); k=_kind(dd)
                cal+=f'<div class="fm-event {_kind_class(k)}" title="{H(dd.get("title"))}">{H(dd.get("title"))}</div>'
            if len(de)>5: cal+=f'<div class="muted">+{len(de)-5}개</div>'
            cal+='</div>'
        cal+='</div></div>'
    return page('가족 달력', toolbar+cal)

for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/calendar':
        app.view_functions[rule.endpoint] = family_calendar
        break


# ===== safety schema / backups / change history =====
def init_safety_schema():
    c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS change_log(id INTEGER PRIMARY KEY,created_at TEXT NOT NULL,entity_type TEXT NOT NULL,entity_id INTEGER,action TEXT NOT NULL,before_json TEXT,after_json TEXT,restored_from INTEGER);CREATE TABLE IF NOT EXISTS trip_date_quality(trip_id INTEGER PRIMARY KEY,date_status TEXT NOT NULL DEFAULT '확정',updated_at TEXT NOT NULL);''')
    rows=c.execute('select id,start_date,end_date,title,status from trips').fetchall(); now=datetime.now().isoformat(timespec='seconds')
    for r in rows:
        if c.execute('select 1 from trip_date_quality where trip_id=?',(r['id'],)).fetchone(): continue
        title=(r['title'] or '').lower(); sd=r['start_date'] or ''; ed=r['end_date'] or ''; year=sd[:4] if len(sd)>=4 else ''
        whole_year=bool(year and sd==f'{year}-01-01' and ed==f'{year}-12-31')
        status='미정' if whole_year or r['status']=='장기 계획' else '확정'
        if ('시그니엘' in title and year=='2018') or ('몬드리안' in title and year=='2020'): status='미정'
        elif (('healing' in title or '힐링' in title) and year=='2020') or ('파크로쉬' in title and year=='2022') or ('페어몬트' in title and year=='2022'): status='대략'
        c.execute('insert into trip_date_quality(trip_id,date_status,updated_at) values(?,?,?)',(r['id'],status,now))
    c.commit(); c.close()

init_safety_schema()


def prune_backups(prefix, keep):
    try:
        files=sorted([os.path.join(BACKUP_DIR,x) for x in os.listdir(BACKUP_DIR) if x.startswith(prefix) and x.endswith('.db')],key=os.path.getmtime,reverse=True)
        for p in files[keep:]:
            try: os.remove(p)
            except OSError: pass
    except OSError: pass


def backup_db(kind='daily'):
    if not os.path.exists(DB_PATH): return None
    os.makedirs(BACKUP_DIR,exist_ok=True); now=datetime.now()
    name=f'daily_{now.strftime("%Y-%m-%d")}.db' if kind=='daily' else f'prechange_{now.strftime("%Y%m%d_%H%M%S_%f")}.db'
    path=os.path.join(BACKUP_DIR,name); tmp=path+'.tmp'
    with BACKUP_LOCK:
        try:
            if os.path.exists(tmp): os.remove(tmp)
            src=sqlite3.connect(DB_PATH); dst=sqlite3.connect(tmp); src.backup(dst); dst.close(); src.close(); os.replace(tmp,path)
            prune_backups('daily_',30); prune_backups('prechange_',20); return path
        except Exception as e:
            print(f'Backup failed: {type(e).__name__}',flush=True)
            try:
                if os.path.exists(tmp): os.remove(tmp)
            except OSError: pass
            return None


def backup_loop():
    while True:
        try: backup_db('daily')
        except Exception: pass
        time.sleep(3600)
threading.Thread(target=backup_loop,daemon=True,name='daily-db-backup').start()

ALLOWED_TABLES={'trips','itinerary','calendar_events','academy','trip_date_quality'}
AUDIT_RULES={'/trip/add':('trips','add'),'/trip/<int:i>/edit':('trips','edit'),'/trip/<int:i>/delete':('trips','delete'),'/itinerary/add':('itinerary','add'),'/itinerary/<int:i>/edit':('itinerary','edit'),'/itinerary/<int:i>/delete':('itinerary','delete'),'/event/add':('calendar_events','add'),'/event/<int:i>/edit':('calendar_events','edit'),'/event/<int:i>/delete':('calendar_events','delete'),'/academy/add':('academy','add'),'/academy/<int:i>/edit':('academy','edit'),'/academy/<int:i>/delete':('academy','delete')}


def row_snapshot(table, entity_id, include_related=False):
    if table not in ALLOWED_TABLES or not entity_id: return None
    c=db(); sql=f'select * from {table} where id=?' if table!='trip_date_quality' else 'select * from trip_date_quality where trip_id=?'; row=c.execute(sql,(entity_id,)).fetchone(); snap={'row':dict(row) if row else None}
    if include_related and table=='trips' and row: snap['itinerary']=[dict(x) for x in c.execute('select * from itinerary where trip_id=? order by id',(entity_id,)).fetchall()]
    c.close(); return snap


def max_id(table):
    if table not in ALLOWED_TABLES or table=='trip_date_quality': return None
    c=db(); r=c.execute(f'select max(id) m from {table}').fetchone(); c.close(); return r['m'] if r else None


def log_change(table,entity_id,action,before,after,restored_from=None):
    c=db(); c.execute('insert into change_log(created_at,entity_type,entity_id,action,before_json,after_json,restored_from) values(?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),table,entity_id,action,json.dumps(before,ensure_ascii=False,default=str) if before is not None else None,json.dumps(after,ensure_ascii=False,default=str) if after is not None else None,restored_from)); c.commit(); c.close()


def audited(orig,table,action):
    @wraps(orig)
    def wrapped(*args,**kwargs):
        entity_id=kwargs.get('i'); before_max=max_id(table) if action=='add' else None; before=row_snapshot(table,entity_id,include_related=(action=='delete')) if action!='add' else None
        backup_db('prechange'); resp=orig(*args,**kwargs)
        if action=='add':
            after_id=max_id(table); entity_id=after_id if after_id is not None and (before_max is None or after_id>before_max) else entity_id; after=row_snapshot(table,entity_id)
        elif action=='delete': after=None
        else: after=row_snapshot(table,entity_id)
        log_change(table,entity_id,action,before,after); return resp
    return wrapped

seen=set()
for rule in list(app.url_map.iter_rules()):
    spec=AUDIT_RULES.get(rule.rule)
    if spec and rule.endpoint not in seen:
        app.view_functions[rule.endpoint]=audited(app.view_functions[rule.endpoint],spec[0],spec[1]); seen.add(rule.endpoint)


def upsert_row(c,table,row):
    if not row: return
    cols=list(row.keys()); c.execute(f'insert or replace into {table}({",".join(cols)}) values({",".join("?" for _ in cols)})',[row[k] for k in cols])

@app.route('/changes')
def changes():
    c=db(); rows=c.execute('select * from change_log order by id desc limit 100').fetchall(); c.close(); labels={'trips':'여행','itinerary':'세부 일정','calendar_events':'가족 일정','academy':'지유 일정','trip_date_quality':'날짜 정확도'}; actions={'add':'추가','edit':'수정','delete':'삭제','restore':'복구'}
    body='<div class="toolbar"><b>최근 변경 100건</b><a class="btn s" href="/system-status">시스템 상태</a></div><div class="box"><table style="min-width:720px"><tr><th>시간</th><th>대상</th><th>작업</th><th>ID</th><th>복구</th></tr>'
    for r in rows:
        can=r['action'] in ('add','edit','delete') and (r['before_json'] or r['after_json']); restore=f'<form method="post" action="/change/{r["id"]}/restore" onsubmit="return confirm(\'이 변경 직전 상태로 복구할까요?\')"><button class="btn s">복구</button></form>' if can else '-'
        body+=f'<tr><td>{H(r["created_at"].replace("T"," "))}</td><td>{H(labels.get(r["entity_type"],r["entity_type"]))}</td><td>{H(actions.get(r["action"],r["action"]))}</td><td>{H(r["entity_id"])}</td><td>{restore}</td></tr>'
    return page('변경 이력',body+'</table></div>')

@app.route('/change/<int:log_id>/restore',methods=['POST'])
def restore_change(log_id):
    c=db(); r=c.execute('select * from change_log where id=?',(log_id,)).fetchone()
    if not r or r['entity_type'] not in ALLOWED_TABLES: c.close(); return abort(404)
    table,entity_id,action=r['entity_type'],r['entity_id'],r['action']; before=json.loads(r['before_json']) if r['before_json'] else None; current=row_snapshot(table,entity_id,include_related=(table=='trips')); backup_db('prechange')
    if action=='add': c.execute(f'delete from {table} where {"trip_id" if table=="trip_date_quality" else "id"}=?',(entity_id,))
    elif before and before.get('row'):
        upsert_row(c,table,before['row'])
        if table=='trips' and before.get('itinerary') is not None:
            c.execute('delete from itinerary where trip_id=?',(entity_id,))
            for x in before.get('itinerary',[]): upsert_row(c,'itinerary',x)
    c.commit(); c.close(); after=row_snapshot(table,entity_id,include_related=(table=='trips')); log_change(table,entity_id,'restore',current,after,restored_from=log_id); return redirect('/changes')


def date_quality(trip_id):
    c=db(); r=c.execute('select date_status from trip_date_quality where trip_id=?',(trip_id,)).fetchone(); c.close(); return r['date_status'] if r else '확정'

@app.route('/trip/<int:trip_id>/date-status',methods=['POST'])
def set_trip_date_status(trip_id):
    status=(request.form.get('date_status') or '').strip()
    if status not in ('확정','대략','미정'): return abort(400)
    before=row_snapshot('trip_date_quality',trip_id); backup_db('prechange'); c=db(); c.execute('insert into trip_date_quality(trip_id,date_status,updated_at) values(?,?,?) on conflict(trip_id) do update set date_status=excluded.date_status,updated_at=excluded.updated_at',(trip_id,status,datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close(); after=row_snapshot('trip_date_quality',trip_id); log_change('trip_date_quality',trip_id,'edit',before,after); return redirect(request.referrer or f'/trip/{trip_id}')


# ===== editable trip detail =====
def trip_attrs(r):
    keys=['id','start_date','end_date','country','region','title','companions','trip_type','status','lodging','transport','notes']; return ' '.join('data-'+k+'="'+H(r[k])+'"' for k in keys)
def itinerary_attrs(x):
    keys=['id','trip_id','item_date','day_label','time_text','title','place','detail','sort_order']; return ' '.join('data-'+k+'="'+H(x[k])+'"' for k in keys)

def editable_trip_detail(trip_id):
    c=db(); r=c.execute('select * from trips where id=?',(trip_id,)).fetchone(); its=c.execute('select * from itinerary where trip_id=? order by sort_order,item_date,id',(trip_id,)).fetchall(); c.close()
    if not r: return abort(404)
    dq=date_quality(trip_id); opts=''.join(f'<button class="date-q {"on" if dq==x else ""}" name="date_status" value="{x}">{x}</button>' for x in ('확정','대략','미정'))
    panel=f'<div class="date-quality"><div><b>여행 날짜 정확도</b><div class="muted">확정 · 대략 · 미정으로 구분</div></div><form method="post" action="/trip/{trip_id}/date-status" class="date-q-form">{opts}</form></div>'
    back='/past' if r['status']=='완료' else '/future'; actions=f'<div class="trip-actions"><a class="btn s" href="{back}">← 여행 목록</a><button class="btn" {trip_attrs(r)} onclick="et(this)">여행 정보 수정</button><button class="btn s" onclick="ni({r["id"]})">+ 세부 일정</button></div>'
    cards='<div class="trip-edit-grid">'
    for label,value in [('여행 일자',f'{r["start_date"]} ~ {r["end_date"]}'),('지역',' · '.join(x for x in [r['country'],r['region']] if x)),('함께',r['companions']),('숙소',r['lodging']),('교통/항공',r['transport']),('상태',r['status'])]: cards+=f'<div class="trip-edit-card"><div class="label">{H(label)}</div><b>{H(value) or "-"}</b></div>'
    cards+='</div><div class="toolbar"><h2 style="margin:0">일자별 일정</h2><button class="btn s" onclick="ni('+str(r['id'])+')">+ 일정 추가</button></div>'
    if not its: cards+='<div class="trip-edit-card muted">아직 세부 일정이 없습니다.</div>'
    for x in its:
        left=' · '.join(v for v in [x['item_date'],x['day_label'],x['time_text']] if v) or '-'; cards+=f'<div class="itinerary-row"><div><b>{H(left)}</b></div><div><b>{H(x["title"])}</b>'+ (f'<br>{H(x["place"])}' if x['place'] else '') + (f'<br><span class="muted">{H(x["detail"])}</span>' if x['detail'] else '') + f'</div><div class="itinerary-actions"><button class="btn s" {itinerary_attrs(x)} onclick="ei(this)">수정</button><form method="post" action="/itinerary/{x["id"]}/delete" style="display:inline" onsubmit="return confirm(\'삭제할까요?\')"><button class="btn d">삭제</button></form></div></div>'
    notes=f'<h2 style="margin-top:20px">메모</h2><div class="trip-edit-card">{H(r["notes"]) or "-"}</div>'
    if r['start_date']=='2026-08-08' and '발리' in (r['title'] or ''): notes+='<div style="margin-top:10px"><a class="btn" href="/photos/bali-2026">📷 발리 사진</a></div>'
    return page(r['title'],panel+actions+cards+notes+mods())

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/trip/<int:trip_id>': app.view_functions[rule.endpoint]=editable_trip_detail; break


# ===== Google Calendar health =====
def check_source(src):
    name=src.get('name') or '이름 없음'
    try:
        r=requests.get(src['url'],timeout=8,headers={'User-Agent':'YJ-Family-Calendar/1.0'}); r.raise_for_status(); cal=Calendar.from_ical(r.content); events=list(cal.walk('VEVENT')); recurring=sum(1 for e in events if e.get('RRULE')); return {'name':name,'ok':True,'events':len(events),'recurring':recurring,'error':''}
    except Exception as e: return {'name':name,'ok':False,'events':0,'recurring':0,'error':type(e).__name__}

def run_sync_check():
    sources=_sources(); results=[]
    with ThreadPoolExecutor(max_workers=max(1,min(5,len(sources)))) as ex:
        futures=[ex.submit(check_source,s) for s in sources]
        for f in as_completed(futures): results.append(f.result())
    order={s.get('name'):i for i,s in enumerate(sources)}; results.sort(key=lambda x:order.get(x['name'],999)); state={'checked_at':datetime.now().isoformat(timespec='seconds'),'sources':results,'ok':bool(results) and all(x['ok'] for x in results)}
    with SYNC_LOCK: SYNC_STATE.clear(); SYNC_STATE.update(state)
    print('Google Calendar sync check: '+', '.join(f"{x['name']}={'OK' if x['ok'] else 'FAIL'}" for x in results),flush=True); return state

def sync_startup():
    time.sleep(3)
    try: run_sync_check()
    except Exception as e: print(f'Google Calendar sync check failed: {type(e).__name__}',flush=True)
threading.Thread(target=sync_startup,daemon=True,name='gcal-sync-check').start()

@app.route('/system-status')
def system_status():
    state=run_sync_check() if request.args.get('refresh')=='1' or not SYNC_STATE.get('checked_at') else dict(SYNC_STATE)
    try: files=sorted([x for x in os.listdir(BACKUP_DIR) if x.endswith('.db')],reverse=True)
    except OSError: files=[]
    daily=[x for x in files if x.startswith('daily_')]; pre=[x for x in files if x.startswith('prechange_')]
    body=f'<div class="status-grid"><div class="status-card"><b>DB 자동 백업</b><div>매일 백업 {len(daily)}개 · 변경 전 백업 {len(pre)}개</div><div class="muted">일일 30개, 변경 전 20개 보관</div></div><div class="status-card"><b>변경 이력/복구</b><div><a class="btn s" href="/changes">최근 변경 보기</a></div></div><div class="status-card"><b>지유 학원 분리</b><div>가족 달력에서 반복 학원 일정 제외 활성</div></div></div><div class="toolbar"><b>Google Calendar 연결 점검</b><a class="btn s" href="/system-status?refresh=1">다시 점검</a></div><div class="box"><table style="min-width:620px"><tr><th>캘린더</th><th>상태</th><th>전체 일정</th><th>반복 일정</th></tr>'
    for x in state.get('sources',[]): body+=f'<tr><td>{H(x["name"])}</td><td>{"정상" if x["ok"] else "오류"}</td><td>{x["events"]}</td><td>{x["recurring"]}</td></tr>'
    body+=f'</table></div><div class="muted" style="margin-top:8px">마지막 점검: {H((state.get("checked_at") or "-").replace("T"," "))}</div>'; return page('시스템 상태',body)

# ===================== from experience_app.py =====================
CSS += '''
.home-card{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:14px}.home-card h2{font-size:16px;margin:0 0 10px}.home-list{display:grid;gap:7px}.home-item{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #edf1f5}.home-item:last-child{border-bottom:0}.home-link{color:#14263f;text-decoration:none}.home-link:hover{text-decoration:underline}.quick-row{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 16px}.next-trip-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:12px}.next-trip-card{background:#fff;border:1px solid #dfe6ee;border-radius:15px;padding:14px;min-height:112px}.next-trip-card .kind{font-size:11px;color:#748196;font-weight:700}.next-trip-card .name{font-size:16px;font-weight:800;margin:7px 0 5px}.dday{display:inline-block;font-size:12px;font-weight:800;color:#0f4c81;background:#edf5fb;border-radius:999px;padding:3px 8px}.family-next{margin-bottom:16px}.filter-box{background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:12px;margin-bottom:14px}.filter-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr)) auto auto;gap:8px;align-items:end}.filter-field{display:grid;gap:4px}.filter-field label{font-size:11px;color:#748196;font-weight:700}.filter-field select{width:100%;min-height:38px;border:1px solid #d7dfe8;border-radius:9px;background:#fff;padding:7px 9px;font:inherit}.past-summary{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:9px}.past-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.past-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px}.past-card .date{font-size:12px;color:#748196;margin-bottom:4px}.past-card .meta{font-size:12px;color:#66758a;margin-top:5px}.stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}.stat-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:13px}.stat-card .big{font-size:24px;font-weight:800;margin-top:4px}.bar-list{display:grid;gap:8px}.bar-row{display:grid;grid-template-columns:130px 1fr 45px;gap:9px;align-items:center}.bar-track{height:9px;background:#edf2f7;border-radius:999px;overflow:hidden}.bar-fill{height:100%;background:#0f4c81;border-radius:999px}.section-title{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:18px 0 9px}.section-title h2{margin:0;font-size:18px}.search-form{display:flex;gap:8px;margin-bottom:14px}.search-form input{flex:1}.search-result{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px;margin-bottom:8px}.search-result h3{margin:0 0 5px;font-size:15px}.search-meta{font-size:12px;color:#728096}
@media(max-width:700px){.next-trip-grid,.past-grid{grid-template-columns:1fr}.filter-form{grid-template-columns:1fr 1fr}.filter-form .filter-field:first-child{grid-column:1/-1}.stat-grid{grid-template-columns:repeat(2,1fr)}.bar-row{grid-template-columns:90px 1fr 36px}.search-form{flex-direction:column}}
@media(max-width:430px){.filter-form{grid-template-columns:1fr}.filter-form .filter-field:first-child{grid-column:auto}}
'''


def _safe_date(s):
    try:
        return datetime.strptime((s or '')[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def _trip_days(r):
    a=_safe_date(r['start_date']); b=_safe_date(r['end_date'])
    if not a or not b or b<a:
        return 0
    return (b-a).days+1


def _dday_label(target, today):
    if not target:
        return '-'
    n=(target-today).days
    return 'D-DAY' if n==0 else f'D-{n}'


def _next_trip_by_type(c, today, trip_type):
    return c.execute("select * from trips where start_date>=? and status!='완료' and trip_type=? order by start_date asc,id asc limit 1",(today.isoformat(),trip_type)).fetchone()


def _is_trip_event(e):
    d=dict(e)
    return d.get('source')=='trip' or (d.get('category') or '')=='여행'


def _upcoming_family_events(today, days=180, limit=8):
    events=family_events(today,today+timedelta(days=days))
    out=[]
    for e in events:
        d=dict(e)
        if _is_trip_event(d):
            continue
        sd=_safe_date(str(d.get('start_date') or '')[:10])
        ed=_safe_date(str(d.get('end_date') or d.get('start_date') or '')[:10])
        if not sd or (ed and ed<today):
            continue
        out.append((sd,d))
    out.sort(key=lambda x:(x[0],str(x[1].get('title') or '')))
    return out[:limit]


def _trip_card(r, today, kind):
    if not r:
        return f'<div class="next-trip-card"><div class="kind">{kind}</div><div class="name">예정 없음</div></div>'
    td=_safe_date(r['start_date'])
    region=' · '.join(x for x in [r['country'],r['region']] if x)
    return (f'<div class="next-trip-card"><div class="kind">{kind}</div>'
            f'<div class="name"><a class="home-link" href="/trip/{r["id"]}">{H(r["title"])}</a></div>'
            f'<span class="dday">{_dday_label(td,today)}</span>'
            f'<div class="muted" style="margin-top:6px">{H(r["start_date"])} ~ {H(r["end_date"])}</div>'
            f'<div class="muted">{H(region) or "-"}</div></div>')


def family_home():
    today=date.today()
    c=db(); domestic=_next_trip_by_type(c,today,'국내'); overseas=_next_trip_by_type(c,today,'해외'); c.close()
    family_events=_upcoming_family_events(today)

    quick='<div class="quick-row"><a class="btn" href="/past">과거 여행</a><a class="btn s" href="/future">향후 여행</a><a class="btn s" href="/travel-search">통합 검색</a><a class="btn s" href="/travel-stats">여행 통계</a><a class="btn s" href="/calendar">가족 달력</a><a class="btn s" href="/riley">지유 주간 일정</a></div>'
    body=quick+'<div class="next-trip-grid">'+_trip_card(domestic,today,'다음 국내 여행')+_trip_card(overseas,today,'다음 해외 여행')+'</div>'
    body+='<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-list">'
    if not family_events:
        body+='<div class="muted">180일 내 등록된 가족 일정이 없습니다.</div>'
    for d,e in family_events:
        end=str(e.get('end_date') or '')[:10]
        date_text=d.isoformat() if not end or end==d.isoformat() else f'{d.isoformat()} ~ {end}'
        body+=f'<div class="home-item"><span>{H(e.get("title"))}</span><span class="muted">{H(date_text)} · {_dday_label(d,today)}</span></div>'
    body+='</div></section>'
    return page('우리 가족 기록',body)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=family_home
        break


def past_filtered():
    year=(request.args.get('year') or '').strip()
    country=(request.args.get('country') or '').strip()
    people=(request.args.get('people') or '').strip()
    c=db(); all_rows=c.execute("select * from trips where status='완료' order by start_date desc,id desc").fetchall(); c.close()

    years=sorted({(r['start_date'] or '')[:4] for r in all_rows if (r['start_date'] or '')[:4]},reverse=True)
    countries=sorted({(r['country'] or '').strip() for r in all_rows if (r['country'] or '').strip()})
    peoples=sorted({(r['companions'] or '').strip() for r in all_rows if (r['companions'] or '').strip()})

    rows=[]
    for r in all_rows:
        if year and (r['start_date'] or '')[:4]!=year: continue
        if country and (r['country'] or '').strip()!=country: continue
        if people and (r['companions'] or '').strip()!=people: continue
        rows.append(r)

    def options(values,current,all_label):
        s=f'<option value="">{all_label}</option>'
        for v in values:
            s+=f'<option value="{H(v)}" {"selected" if current==v else ""}>{H(v)}</option>'
        return s

    body='<div class="filter-box"><form class="filter-form" method="get">'
    body+=f'<div class="filter-field"><label>연도별</label><select name="year">{options(years,year,"전체 연도")}</select></div>'
    body+=f'<div class="filter-field"><label>국가별</label><select name="country">{options(countries,country,"전체 국가")}</select></div>'
    body+=f'<div class="filter-field"><label>인원별</label><select name="people">{options(peoples,people,"전체 인원")}</select></div>'
    body+='<button class="btn">필터 적용</button><a class="btn s" href="/past">초기화</a></form></div>'
    body+=f'<div class="past-summary"><b>과거 여행 {len(rows)}건</b><span class="muted">전체 {len(all_rows)}건</span></div><div class="past-grid">'
    if not rows:
        body+='<div class="home-card muted">조건에 맞는 여행이 없습니다.</div>'
    for r in rows:
        region=' · '.join(x for x in [r['country'],r['region']] if x)
        body+=f'<a class="past-card home-link" href="/trip/{r["id"]}"><div class="date">{H(r["start_date"])} ~ {H(r["end_date"])}</div><b>{H(r["title"])}</b><div class="meta">{H(region) or "-"}</div><div class="meta">함께: {H(r["companions"]) or "-"}</div></a>'
    body+='</div>'
    return page('과거 여행',body)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/past':
        app.view_functions[rule.endpoint]=past_filtered
        break


@app.route('/travel-stats')
def travel_stats():
    c=db(); rows=c.execute("select * from trips where status='완료' order by start_date").fetchall(); c.close()
    total=len(rows); overseas=sum(1 for r in rows if (r['trip_type'] or '')=='해외'); domestic=sum(1 for r in rows if (r['trip_type'] or '')=='국내'); days=sum(_trip_days(r) for r in rows)
    country=Counter((r['country'] or '미분류').strip() or '미분류' for r in rows if (r['trip_type'] or '')=='해외')
    years=Counter((r['start_date'] or '')[:4] for r in rows if (r['start_date'] or '')[:4])
    companions=Counter((r['companions'] or '미분류').strip() or '미분류' for r in rows)
    body=f'<div class="stat-grid"><div class="stat-card"><div class="muted">완료 여행</div><div class="big">{total}</div></div><div class="stat-card"><div class="muted">해외 / 국내</div><div class="big">{overseas} / {domestic}</div></div><div class="stat-card"><div class="muted">누적 여행일</div><div class="big">{days}일</div></div><div class="stat-card"><div class="muted">방문 국가</div><div class="big">{len(country)}개</div></div></div>'

    def bars(title,data,limit=12):
        items=data.most_common(limit); mx=max([v for _,v in items],default=1); s=f'<div class="section-title"><h2>{H(title)}</h2></div><div class="home-card"><div class="bar-list">'
        for k,v in items:
            s+=f'<div class="bar-row"><div>{H(k)}</div><div class="bar-track"><div class="bar-fill" style="width:{max(4,int(v/mx*100))}%"></div></div><b>{v}</b></div>'
        return s+'</div></div>'

    body+=bars('연도별 여행 횟수',years,20)+bars('국가별 방문 횟수',country,15)+bars('가족 구성별 여행',companions,10)
    return page('여행 통계',body)


def travel_search_page():
    q=(request.args.get('q') or '').strip(); rows=[]
    if q:
        like='%'+q+'%'; c=db()
        rows=c.execute('''
            SELECT t.id,t.start_date,t.end_date,t.title,t.country,t.region,t.lodging,t.transport,t.notes,
                   group_concat(coalesce(i.title,'') || ' ' || coalesce(i.place,'') || ' ' || coalesce(i.detail,''),' | ') itinerary_text
            FROM trips t LEFT JOIN itinerary i ON i.trip_id=t.id
            WHERE t.title LIKE ? OR t.country LIKE ? OR t.region LIKE ? OR t.lodging LIKE ? OR t.transport LIKE ? OR t.notes LIKE ?
               OR i.title LIKE ? OR i.place LIKE ? OR i.detail LIKE ?
            GROUP BY t.id ORDER BY t.start_date DESC
        ''',(like,like,like,like,like,like,like,like,like)).fetchall(); c.close()
    form=f'<form class="search-form" method="get"><input name="q" value="{H(q)}" placeholder="나라 · 도시 · 숙소 · 항공편 · 일정 · 메모 검색"><button class="btn">검색</button></form>'
    body=form
    if q:
        body+=f'<div class="muted" style="margin-bottom:10px">“{H(q)}” 검색 결과 {len(rows)}건</div>'
        if not rows: body+='<div class="home-card muted">검색 결과가 없습니다.</div>'
        for r in rows:
            snippets=[]
            for label,key in [('숙소','lodging'),('교통','transport'),('메모','notes')]:
                val=r[key] or ''
                if q.lower() in val.lower(): snippets.append(f'{label}: {val}')
            it=r['itinerary_text'] or ''
            if q.lower() in it.lower(): snippets.append('세부 일정: '+it[:220])
            body+=f'<div class="search-result"><h3><a class="home-link" href="/trip/{r["id"]}">{H(r["title"])}</a></h3><div class="search-meta">{H(r["start_date"])} ~ {H(r["end_date"])} · {H(r["country"])} · {H(r["region"])}</div>'
            for s in snippets[:3]: body+=f'<div style="margin-top:6px">{H(s)}</div>'
            body+='</div>'
    else:
        body+='<div class="home-card"><b>한 번에 찾기</b><div class="muted" style="margin-top:5px">여행명, 국가, 도시, 숙소, 항공·교통, 세부 일정, 장소, 메모를 모두 검색합니다.</div></div>'
    return page('통합 검색',body)


_search_overridden=False
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/travel-search':
        app.view_functions[rule.endpoint]=travel_search_page
        _search_overridden=True
        break
if not _search_overridden:
    app.add_url_rule('/travel-search','travel_search_page',travel_search_page)

# ===================== from home_cleanup_app.py =====================
CSS += '''
/* home cleanup: keep only the global header navigation */
.home-family-list{display:grid;gap:0}.home-family-row{display:grid;grid-template-columns:10px minmax(0,1fr) auto;gap:10px;align-items:center;padding:11px 0;border-bottom:1px solid #edf1f5}.home-family-row:last-child{border-bottom:0}.event-dot{width:8px;height:34px;border-radius:999px;background:#94a3b8}.event-dot.yj{background:#4f7cff}.event-dot.bomi{background:#f08aa8}.event-dot.riley{background:#8b72d6}.event-dot.hyeon{background:#46a67a}.event-dot.holiday{background:#e7a23b}.event-dot.family{background:#6f879f}.event-main{min-width:0}.event-title{font-weight:700;color:#14263f}.event-meta{font-size:12px;color:#718096;margin-top:2px}.event-dday{font-size:12px;font-weight:800;border-radius:999px;padding:4px 8px;background:#f2f5f8;color:#51657b;white-space:nowrap}.event-dday.today{background:#fff0f0;color:#d34646}.family-next h2{margin-bottom:5px}
@media(max-width:700px){.home-family-row{grid-template-columns:8px minmax(0,1fr) auto;gap:8px}.event-dot{width:6px;height:30px}.event-title{font-size:14px}.event-meta{font-size:11px}.event-dday{font-size:11px;padding:3px 7px}}
'''

HOME_CACHE_DAYS = 180
CAL_CACHE_PAST_DAYS = 365
CAL_CACHE_FUTURE_DAYS = 730
HOME_CACHE_REFRESH_SECONDS = 600
_HOME_SYNC_LOCK = threading.Lock()
_LIVE_FAMILY_EVENTS = family_events


def _init_home_cache_schema():
    c=db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS home_event_cache(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      title TEXT NOT NULL,
      category TEXT,
      person TEXT,
      notes TEXT,
      source TEXT NOT NULL DEFAULT 'google',
      synced_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_home_event_cache_dates ON home_event_cache(start_date,end_date);
    CREATE TABLE IF NOT EXISTS home_cache_meta(
      cache_key TEXT PRIMARY KEY,
      cache_value TEXT NOT NULL
    );
    ''')
    c.commit(); c.close()


def _event_kind(e):
    person=(e.get('person') or '').strip()
    title=(e.get('title') or '').strip()
    category=(e.get('category') or '').strip()
    text=f'{person} {title} {category}'
    holiday_words=('추석','설날','공휴일','휴업일','휴일','연휴','대체공휴일')
    if any(w in text for w in holiday_words):
        return 'holiday','휴일'
    if '보미' in text:
        return 'bomi','보미'
    if '지유' in text:
        return 'riley','지유'
    if '혜온' in text:
        return 'hyeon','혜온'
    if '용제' in text or 'YJ' in text.upper():
        return 'yj','용제'
    return 'family','가족'


def _clean_title(title):
    t=(title or '').strip()
    for prefix in ('보미:','보미 :','지유:','지유 :','혜온:','혜온 :','용제:','용제 :'):
        if t.startswith(prefix):
            return t[len(prefix):].strip()
    return t


def _refresh_google_cache():
    if not _HOME_SYNC_LOCK.acquire(blocking=False):
        return
    try:
        today=date.today()
        start=today-timedelta(days=CAL_CACHE_PAST_DAYS)
        end=today+timedelta(days=CAL_CACHE_FUTURE_DAYS)
        events=_LIVE_FAMILY_EVENTS(start,end)
        google_rows=[]
        for raw in events:
            e=dict(raw)
            if e.get('source')!='google':
                continue
            sd=str(e.get('start_date') or '')[:10]
            ed=str(e.get('end_date') or sd)[:10] or sd
            if not sd:
                continue
            google_rows.append((sd,ed,str(e.get('title') or ''),str(e.get('category') or ''),str(e.get('person') or ''),str(e.get('notes') or ''),'google'))

        # Keep the last good snapshot if Google is temporarily unavailable.
        has_sources=bool(_sources())
        if has_sources and not google_rows:
            return

        now=datetime.now().isoformat(timespec='seconds')
        c=db()
        c.execute('delete from home_event_cache')
        if google_rows:
            c.executemany('insert into home_event_cache(start_date,end_date,title,category,person,notes,source,synced_at) values(?,?,?,?,?,?,?,?)',[r+(now,) for r in google_rows])
        c.execute("insert or replace into home_cache_meta(cache_key,cache_value) values('google_last_sync',?)",(now,))
        c.commit(); c.close()
    except Exception as e:
        print(f'Google event DB cache refresh failed: {type(e).__name__}', flush=True)
    finally:
        _HOME_SYNC_LOCK.release()


def _home_cache_loop():
    time.sleep(2)
    while True:
        _refresh_google_cache()
        time.sleep(HOME_CACHE_REFRESH_SECONDS)


def _cached_calendar_events(start, end):
    """DB-only event source for the family calendar: local + cached Google + trips."""
    c=db()
    local=[dict(x) for x in c.execute(
        'select * from calendar_events where start_date<=? and end_date>=? order by start_date,id',
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    cached=[dict(x) for x in c.execute(
        'select start_date,end_date,title,category,person,notes,source from home_event_cache where start_date<=? and end_date>=? order by start_date,id',
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    trips=[dict(x) for x in c.execute(
        "select id,start_date,end_date,title,region,companions from trips where start_date<=? and end_date>=? order by start_date,id",
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    c.close()

    out=[]
    for e in local:
        e['source']='local'
        out.append(e)
    out.extend(cached)
    for r in trips:
        out.append({
            'id':f'trip:{r["id"]}',
            'start_date':r.get('start_date') or '',
            'end_date':r.get('end_date') or r.get('start_date') or '',
            'title':r.get('title') or '',
            'category':'여행',
            'person':r.get('companions') or '',
            'notes':r.get('region') or '',
            'source':'trip',
            'trip_id':r.get('id'),
        })
    out.sort(key=lambda x:(str(x.get('start_date') or ''),str(x.get('title') or '')))
    return out


def _cached_family_events(today, days=HOME_CACHE_DAYS):
    return _cached_calendar_events(today,today+timedelta(days=days))


def _upcoming_events(today, days=180, limit=10):
    events=_cached_family_events(today,days)
    out=[]
    seen=set()
    for e in events:
        if e.get('source')=='trip' or (e.get('category') or '')=='여행':
            continue
        compact=(e.get('title') or '').replace(' ','')
        if '청소아줌마' in compact:
            continue
        sd=_safe_date(str(e.get('start_date') or '')[:10])
        ed=_safe_date(str(e.get('end_date') or e.get('start_date') or '')[:10])
        if not sd or (ed and ed<today):
            continue
        key=(sd.isoformat(),str(e.get('end_date') or ''),str(e.get('title') or ''),str(e.get('person') or ''))
        if key in seen:
            continue
        seen.add(key)
        out.append((sd,e))
    out.sort(key=lambda x:(x[0],str(x[1].get('title') or '')))
    return out[:limit]


def clean_family_home():
    today=date.today()
    c=db()
    domestic=_next_trip_by_type(c,today,'국내')
    overseas=_next_trip_by_type(c,today,'해외')
    c.close()
    family_events=_upcoming_events(today)

    body='<div class="next-trip-grid">'+_trip_card(domestic,today,'다음 국내 여행')+_trip_card(overseas,today,'다음 해외 여행')+'</div>'
    body+='<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-family-list">'
    if not family_events:
        body+='<div class="muted" style="padding:10px 0">등록된 가족 일정이 없습니다.</div>'
    for d,e in family_events:
        kind,label=_event_kind(e)
        end=str(e.get('end_date') or '')[:10]
        date_text=d.isoformat() if not end or end==d.isoformat() else f'{d.isoformat()} ~ {end}'
        dday=_dday_label(d,today)
        today_cls=' today' if dday=='D-DAY' else ''
        title=_clean_title(e.get('title'))
        body+=(f'<div class="home-family-row">'
               f'<span class="event-dot {kind}" title="{H(label)}"></span>'
               f'<div class="event-main"><div class="event-title">{H(title)}</div>'
               f'<div class="event-meta">{H(label)} · {H(date_text)}</div></div>'
               f'<span class="event-dday{today_cls}">{H(dday)}</span></div>')
    body+='</div></section>'
    return page('우리 가족 기록',body)


_init_home_cache_schema()
threading.Thread(target=_home_cache_loop,daemon=True,name='google-event-db-cache').start()

# Make the family calendar DB-only as well. The original live reader is kept only
# for the background refresh above, so page requests no longer wait for Google.
family_events=_cached_calendar_events

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=clean_family_home


@app.before_request
def force_clean_home():
    if request.method=='GET' and request.path=='/':
        return clean_family_home()
    return None


@app.after_request
def prevent_stale_home_cache(response):
    if request.path=='/':
        response.headers['Cache-Control']='no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma']='no-cache'
        response.headers['Expires']='0'
    return response

# ===================== from pwa_app.py =====================
PWA_NAME = '우리 가족 기록'
PWA_SHORT_NAME = '가족 기록'
PWA_THEME = '#10253f'
PWA_BG = '#f4f7fb'
PWA_ICON = '/pwa-icon-v2.svg'

_manifest = {
    'name': PWA_NAME,
    'short_name': PWA_SHORT_NAME,
    'description': '우리 가족의 여행, 일정, 지유 주간 일정을 한곳에서 관리합니다.',
    'start_url': '/',
    'scope': '/',
    'display': 'standalone',
    'orientation': 'any',
    'background_color': PWA_BG,
    'theme_color': PWA_THEME,
    'lang': 'ko-KR',
    'icons': [
        {'src': PWA_ICON, 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any maskable'},
    ],
    'shortcuts': [
        {'name': '가족 달력', 'short_name': '달력', 'url': '/calendar'},
        {'name': '지유 주간 일정', 'short_name': '지유 일정', 'url': '/riley'},
        {'name': '향후 여행', 'short_name': '향후 여행', 'url': '/future'},
    ],
}

# Clean travel mark: deep navy tile + ivory globe + warm gold airplane.
# The important artwork stays inside the maskable safe area so Android/Samsung launchers
# can crop it to circles, squircles or rounded squares without losing details.
_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs>
  <linearGradient id="bg" x1="72" y1="54" x2="438" y2="462" gradientUnits="userSpaceOnUse">
    <stop stop-color="#183A60"/>
    <stop offset="1" stop-color="#0B1D32"/>
  </linearGradient>
</defs>
<rect width="512" height="512" rx="120" fill="url(#bg)"/>
<circle cx="256" cy="256" r="146" fill="#F8F5ED"/>
<circle cx="256" cy="256" r="106" fill="none" stroke="#B9C4CE" stroke-width="12"/>
<path d="M154 256h204M256 150c-31 30-48 67-48 106s17 76 48 106M256 150c31 30 48 67 48 106s-17 76-48 106" fill="none" stroke="#B9C4CE" stroke-width="12" stroke-linecap="round"/>
<path d="M174 200c25 13 53 19 82 19s57-6 82-19M174 312c25-13 53-19 82-19s57 6 82 19" fill="none" stroke="#B9C4CE" stroke-width="10" stroke-linecap="round"/>
<path d="M126 303c38-28 86-48 142-57l91-58c8-5 18-3 23 5 5 7 4 16-2 22l-69 64 50 11c10 2 17 11 16 21-1 9-9 16-18 17l-74 4-41 66c-5 8-15 11-23 7-8-4-12-13-9-22l23-69c-42 3-78 10-111 22-12 4-24-3-27-15-2-7 1-14 9-18z" fill="#D7A347"/>
<path d="M318 218l42-27" stroke="#FFF9EC" stroke-width="9" stroke-linecap="round"/>
<circle cx="116" cy="118" r="10" fill="#D7A347"/>
<circle cx="396" cy="394" r="7" fill="#D7A347" opacity=".75"/>
</svg>'''

_SW = '''const CACHE='family-pwa-v2';
const SHELL=['/manifest.webmanifest','/pwa-icon-v2.svg'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  const url=new URL(event.request.url);
  if(url.origin!==location.origin) return;
  if(event.request.mode==='navigate'){
    event.respondWith(fetch(event.request).catch(()=>caches.match('/')));
    return;
  }
  if(url.pathname==='/manifest.webmanifest'||url.pathname==='/pwa-icon-v2.svg'){
    event.respondWith(fetch(event.request).then(resp=>{const copy=resp.clone();caches.open(CACHE).then(c=>c.put(event.request,copy));return resp;}).catch(()=>caches.match(event.request)));
  }
});'''

@app.route('/manifest.webmanifest')
def pwa_manifest():
    return Response(json.dumps(_manifest, ensure_ascii=False), mimetype='application/manifest+json', headers={'Cache-Control':'no-cache'})

@app.route('/pwa-icon-v2.svg')
def pwa_icon_v2():
    return Response(_ICON_SVG, mimetype='image/svg+xml', headers={'Cache-Control':'public, max-age=86400'})

# Keep old route alive so previously installed versions do not break while updating.
@app.route('/pwa-icon.svg')
def pwa_icon_legacy():
    return Response(_ICON_SVG, mimetype='image/svg+xml', headers={'Cache-Control':'no-cache'})

@app.route('/service-worker.js')
def pwa_service_worker():
    return Response(_SW, mimetype='application/javascript', headers={'Cache-Control':'no-cache','Service-Worker-Allowed':'/'})

_original_page = page

def pwa_page(title, body):
    html = _original_page(title, body)
    pwa_head = f'''<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="{PWA_THEME}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="{PWA_SHORT_NAME}">
<link rel="icon" href="{PWA_ICON}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{PWA_ICON}">'''
    pwa_script = '''<script>if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/service-worker.js').catch(()=>{}));}</script>'''
    return html.replace('</head>', pwa_head + '</head>').replace('</body>', pwa_script + '</body>')

page = pwa_page

# ===================== from family_features_app.py =====================
# ===== schema =====
def init_family_features_schema():
    c = db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS family_tasks(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      due_date TEXT,
      assignee TEXT NOT NULL DEFAULT '가족',
      category TEXT NOT NULL DEFAULT '가족',
      trip_id INTEGER,
      notes TEXT,
      done INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_family_tasks_due ON family_tasks(done,due_date);

    CREATE TABLE IF NOT EXISTS trip_reservations(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trip_id INTEGER NOT NULL,
      kind TEXT NOT NULL,
      title TEXT NOT NULL,
      reservation_date TEXT,
      confirmation TEXT,
      link TEXT,
      notes TEXT,
      done INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_trip_reservations_trip ON trip_reservations(trip_id,id);

    CREATE TABLE IF NOT EXISTS trip_checklist(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trip_id INTEGER NOT NULL,
      title TEXT NOT NULL,
      category TEXT NOT NULL DEFAULT '준비',
      assignee TEXT NOT NULL DEFAULT '가족',
      due_date TEXT,
      done INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_trip_checklist_trip ON trip_checklist(trip_id,done,due_date);

    CREATE TABLE IF NOT EXISTS trip_expenses(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trip_id INTEGER NOT NULL,
      category TEXT NOT NULL DEFAULT '기타',
      title TEXT NOT NULL,
      amount REAL NOT NULL DEFAULT 0,
      currency TEXT NOT NULL DEFAULT 'KRW',
      paid_by TEXT,
      notes TEXT,
      created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_trip_expenses_trip ON trip_expenses(trip_id,id);
    ''')
    c.commit(); c.close()


init_family_features_schema()


# ===== shared UI =====
CSS += '''
.feature-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}.feature-card{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:14px}.feature-card h2,.feature-card h3{margin:0 0 10px}.feature-list{display:grid;gap:7px}.feature-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid #edf1f5}.feature-row:last-child{border-bottom:0}.feature-meta{font-size:11px;color:#748196;margin-top:3px}.feature-badge{font-size:11px;font-weight:800;border-radius:999px;padding:4px 7px;background:#eef3f8;color:#5e7186;white-space:nowrap}.feature-alert{background:#fff5e8;border:1px solid #f1d3a7;color:#8a5a14;border-radius:11px;padding:9px 10px;margin:7px 0;font-size:12px}.task-done{text-decoration:line-through;color:#9aa5b2}.task-actions{display:flex;gap:5px;align-items:center}.task-form{display:grid;grid-template-columns:2fr 1fr 1fr 1fr auto;gap:7px;align-items:end}.task-form input,.task-form select{min-width:0}.plan-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.plan-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}.plan-stat{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:11px}.plan-stat b{font-size:20px;display:block}.plan-section{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:14px;margin:10px 0}.plan-section h2{margin:0 0 10px}.plan-form{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;align-items:end}.plan-form .wide{grid-column:span 2}.plan-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;padding:9px 0;border-bottom:1px solid #edf1f5}.plan-row:last-child{border-bottom:0}.trip-plan-link{margin-left:6px}
@media(max-width:800px){.feature-grid{grid-template-columns:1fr}.task-form{grid-template-columns:1fr 1fr}.task-form .task-title{grid-column:1/-1}.plan-summary{grid-template-columns:1fr 1fr}.plan-form{grid-template-columns:1fr 1fr}.plan-form .wide{grid-column:1/-1}}
@media(max-width:480px){.task-form,.plan-form{grid-template-columns:1fr}.task-form .task-title,.plan-form .wide{grid-column:1}.plan-summary{grid-template-columns:1fr 1fr}}
'''


def family_nav():
    return ('<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b>'
            '<div class="nav">'
            '<a href="/past">과거 여행</a>'
            '<a href="/future">향후 여행</a>'
            '<a href="/calendar">가족 달력</a>'
            '<a href="/tasks">할 일</a>'
            '<a href="/riley">지유 주간 일정</a>'
            '</div></nav></header>')

nav = family_nav

try:
    _manifest['shortcuts'].append({'name':'가족 할 일','short_name':'할 일','url':'/tasks'})
except Exception:
    pass


# ===== family tasks =====
def _task_rows(include_done=True, limit=None):
    c=db()
    sql='select * from family_tasks'
    params=[]
    if not include_done:
        sql+=' where done=0'
    sql+=" order by done asc, case when due_date is null or due_date='' then 1 else 0 end, due_date asc, id desc"
    if limit:
        sql+=' limit ?'; params.append(limit)
    rows=[dict(x) for x in c.execute(sql,params).fetchall()]
    c.close(); return rows


def _task_label(r):
    bits=[r.get('assignee') or '가족', r.get('category') or '가족']
    if r.get('due_date'):
        bits.append(r['due_date'])
    return ' · '.join(bits)


@app.route('/tasks')
def family_tasks_page():
    rows=_task_rows(True)
    open_n=sum(1 for r in rows if not r['done'])
    body=(f'<div class="toolbar"><b>가족 할 일 · 미완료 {open_n}건</b></div>'
          '<section class="feature-card"><form class="task-form" method="post" action="/tasks/add">'
          '<label class="task-title">할 일<input name="title" required placeholder="예: 치과 예약 확인"></label>'
          '<label>마감일<input type="date" name="due_date"></label>'
          '<label>담당<select name="assignee"><option>가족</option><option>용제</option><option>보미</option><option>지유</option><option>혜온</option></select></label>'
          '<label>분류<select name="category"><option>가족</option><option>여행</option><option>학교</option><option>건강</option><option>결제</option><option>기타</option></select></label>'
          '<button class="btn">추가</button></form></section>'
          '<section class="feature-card" style="margin-top:12px"><div class="feature-list">')
    if not rows:
        body+='<div class="muted">등록된 할 일이 없습니다.</div>'
    for r in rows:
        cls=' task-done' if r['done'] else ''
        body+=(f'<div class="feature-row"><div><b class="{cls}">{H(r["title"])}</b>'
               f'<div class="feature-meta">{H(_task_label(r))}</div></div><div class="task-actions">'
               f'<form method="post" action="/tasks/{r["id"]}/toggle"><button class="btn s">{"되돌리기" if r["done"] else "완료"}</button></form>'
               f'<form method="post" action="/tasks/{r["id"]}/delete"><button class="btn d">삭제</button></form></div></div>')
    body+='</div></section>'
    return page('가족 할 일',body)


@app.route('/tasks/add',methods=['POST'])
def family_tasks_add():
    f=request.form
    title=(f.get('title') or '').strip()
    if title:
        c=db(); c.execute('insert into family_tasks(title,due_date,assignee,category,notes,created_at) values(?,?,?,?,?,?)',(
            title,(f.get('due_date') or '').strip(),(f.get('assignee') or '가족').strip(),(f.get('category') or '가족').strip(),(f.get('notes') or '').strip(),datetime.now().isoformat(timespec='seconds')))
        c.commit(); c.close()
    return redirect('/tasks')


@app.route('/tasks/<int:i>/toggle',methods=['POST'])
def family_tasks_toggle(i):
    c=db(); c.execute('update family_tasks set done=case when done=1 then 0 else 1 end where id=?',(i,)); c.commit(); c.close()
    return redirect(request.referrer or '/tasks')


@app.route('/tasks/<int:i>/delete',methods=['POST'])
def family_tasks_delete(i):
    c=db(); c.execute('delete from family_tasks where id=?',(i,)); c.commit(); c.close()
    return redirect(request.referrer or '/tasks')


# ===== trip planner =====
def _trip(trip_id):
    c=db(); r=c.execute('select * from trips where id=?',(trip_id,)).fetchone(); c.close()
    return dict(r) if r else None


def _trip_plan_data(trip_id):
    c=db()
    reservations=[dict(x) for x in c.execute('select * from trip_reservations where trip_id=? order by done,id',(trip_id,)).fetchall()]
    checklist=[dict(x) for x in c.execute("select * from trip_checklist where trip_id=? order by done,case when due_date='' or due_date is null then 1 else 0 end,due_date,id",(trip_id,)).fetchall()]
    expenses=[dict(x) for x in c.execute('select * from trip_expenses where trip_id=? order by id desc',(trip_id,)).fetchall()]
    c.close(); return reservations,checklist,expenses


@app.route('/trip/<int:trip_id>/plan')
def trip_plan(trip_id):
    trip=_trip(trip_id)
    if not trip:
        return redirect('/future')
    reservations,checklist,expenses=_trip_plan_data(trip_id)
    open_check=sum(1 for x in checklist if not x['done'])
    reserved=sum(1 for x in reservations if x['done'])
    total_krw=sum(float(x.get('amount') or 0) for x in expenses if (x.get('currency') or 'KRW')=='KRW')
    start=qdate(trip.get('start_date') or '')
    dday=(start-date.today()).days if start else None
    dtext='-' if dday is None else ('D-DAY' if dday==0 else (f'D-{dday}' if dday>0 else f'D+{abs(dday)}'))
    body=(f'<div class="trip-actions"><a class="btn s" href="/trip/{trip_id}">← 여행 상세</a></div>'
          f'<div class="plan-summary"><div class="plan-stat"><span class="muted">출발</span><b>{H(dtext)}</b></div>'
          f'<div class="plan-stat"><span class="muted">준비할 일</span><b>{open_check}</b></div>'
          f'<div class="plan-stat"><span class="muted">예약 완료</span><b>{reserved}/{len(reservations)}</b></div>'
          f'<div class="plan-stat"><span class="muted">KRW 비용</span><b>{int(total_krw):,}</b></div></div>')

    body+=('<section class="plan-section"><h2>예약 관리</h2><form class="plan-form" method="post" action="/trip/%d/plan/reservation/add">'
           '<label>종류<select name="kind"><option>항공</option><option>숙소</option><option>기차</option><option>투어</option><option>식당</option><option>기타</option></select></label>'
           '<label class="wide">예약명<input name="title" required></label><label>예약일<input type="date" name="reservation_date"></label>'
           '<label>예약번호<input name="confirmation"></label><label class="wide">링크<input name="link" placeholder="https://"></label><button class="btn">추가</button></form><div class="feature-list">') % trip_id
    if not reservations: body+='<div class="muted">등록된 예약이 없습니다.</div>'
    for r in reservations:
        cls=' task-done' if r['done'] else ''
        meta=' · '.join(x for x in [r.get('kind'),r.get('reservation_date'),r.get('confirmation')] if x)
        link=(f' · <a href="{H(r["link"])}" target="_blank">링크</a>' if r.get('link') else '')
        body+=(f'<div class="plan-row"><div><b class="{cls}">{H(r["title"])}</b><div class="feature-meta">{H(meta)}{link}</div></div><div class="task-actions">'
               f'<form method="post" action="/trip/{trip_id}/plan/reservation/{r["id"]}/toggle"><button class="btn s">{"되돌리기" if r["done"] else "완료"}</button></form>'
               f'<form method="post" action="/trip/{trip_id}/plan/reservation/{r["id"]}/delete"><button class="btn d">삭제</button></form></div></div>')
    body+='</div></section>'

    body+=('<section class="plan-section"><h2>준비 체크리스트</h2><form class="plan-form" method="post" action="/trip/%d/plan/check/add">'
           '<label class="wide">준비할 일<input name="title" required></label><label>분류<select name="category"><option>준비</option><option>서류</option><option>아이</option><option>짐</option><option>결제</option><option>체크인</option></select></label>'
           '<label>담당<select name="assignee"><option>가족</option><option>용제</option><option>보미</option><option>지유</option></select></label><label>마감일<input type="date" name="due_date"></label><button class="btn">추가</button></form><div class="feature-list">') % trip_id
    if not checklist: body+='<div class="muted">등록된 준비물이 없습니다.</div>'
    for r in checklist:
        cls=' task-done' if r['done'] else ''
        meta=' · '.join(x for x in [r.get('category'),r.get('assignee'),r.get('due_date')] if x)
        body+=(f'<div class="plan-row"><div><b class="{cls}">{H(r["title"])}</b><div class="feature-meta">{H(meta)}</div></div><div class="task-actions">'
               f'<form method="post" action="/trip/{trip_id}/plan/check/{r["id"]}/toggle"><button class="btn s">{"되돌리기" if r["done"] else "완료"}</button></form>'
               f'<form method="post" action="/trip/{trip_id}/plan/check/{r["id"]}/delete"><button class="btn d">삭제</button></form></div></div>')
    body+='</div></section>'

    body+=('<section class="plan-section"><h2>여행 비용</h2><form class="plan-form" method="post" action="/trip/%d/plan/expense/add">'
           '<label>분류<select name="category"><option>항공</option><option>숙박</option><option>교통</option><option>식사</option><option>체험</option><option>쇼핑</option><option>기타</option></select></label>'
           '<label class="wide">항목<input name="title" required></label><label>금액<input type="number" step="0.01" name="amount" required></label><label>통화<input name="currency" value="KRW"></label><label>결제자<input name="paid_by"></label><button class="btn">추가</button></form><div class="feature-list">') % trip_id
    if not expenses: body+='<div class="muted">등록된 비용이 없습니다.</div>'
    for r in expenses:
        body+=(f'<div class="plan-row"><div><b>{H(r["title"])}</b><div class="feature-meta">{H(r["category"])} · {H(r["amount"])} {H(r["currency"])} · {H(r.get("paid_by") or "-")}</div></div>'
               f'<form method="post" action="/trip/{trip_id}/plan/expense/{r["id"]}/delete"><button class="btn d">삭제</button></form></div>')
    body+='</div></section>'
    return page(f'{trip.get("title") or "여행"} 준비',body)


@app.route('/trip/<int:trip_id>/plan/reservation/add',methods=['POST'])
def trip_reservation_add(trip_id):
    f=request.form; title=(f.get('title') or '').strip()
    if title:
        c=db(); c.execute('insert into trip_reservations(trip_id,kind,title,reservation_date,confirmation,link,notes,created_at) values(?,?,?,?,?,?,?,?)',(
            trip_id,(f.get('kind') or '기타').strip(),title,(f.get('reservation_date') or '').strip(),(f.get('confirmation') or '').strip(),(f.get('link') or '').strip(),(f.get('notes') or '').strip(),datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/reservation/<int:i>/toggle',methods=['POST'])
def trip_reservation_toggle(trip_id,i):
    c=db(); c.execute('update trip_reservations set done=case when done=1 then 0 else 1 end where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/reservation/<int:i>/delete',methods=['POST'])
def trip_reservation_delete(trip_id,i):
    c=db(); c.execute('delete from trip_reservations where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/check/add',methods=['POST'])
def trip_check_add(trip_id):
    f=request.form; title=(f.get('title') or '').strip()
    if title:
        c=db(); c.execute('insert into trip_checklist(trip_id,title,category,assignee,due_date,created_at) values(?,?,?,?,?,?)',(
            trip_id,title,(f.get('category') or '준비').strip(),(f.get('assignee') or '가족').strip(),(f.get('due_date') or '').strip(),datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/check/<int:i>/toggle',methods=['POST'])
def trip_check_toggle(trip_id,i):
    c=db(); c.execute('update trip_checklist set done=case when done=1 then 0 else 1 end where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/check/<int:i>/delete',methods=['POST'])
def trip_check_delete(trip_id,i):
    c=db(); c.execute('delete from trip_checklist where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/expense/add',methods=['POST'])
def trip_expense_add(trip_id):
    f=request.form; title=(f.get('title') or '').strip()
    if title:
        try: amount=float(f.get('amount') or 0)
        except: amount=0
        c=db(); c.execute('insert into trip_expenses(trip_id,category,title,amount,currency,paid_by,notes,created_at) values(?,?,?,?,?,?,?,?)',(
            trip_id,(f.get('category') or '기타').strip(),title,amount,(f.get('currency') or 'KRW').strip().upper(),(f.get('paid_by') or '').strip(),(f.get('notes') or '').strip(),datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/expense/<int:i>/delete',methods=['POST'])
def trip_expense_delete(trip_id,i):
    c=db(); c.execute('delete from trip_expenses where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


# ===== dashboard helpers =====
def _visible_home_events(start,end):
    rows=_cached_calendar_events(start,end)
    out=[]
    for e in rows:
        if e.get('source')=='trip':
            continue
        compact=(e.get('title') or '').replace(' ','')
        if '청소아줌마' in compact:
            continue
        out.append(e)
    return out


def _event_overlaps(e,d):
    try:
        s=qdate(str(e.get('start_date') or '')[:10]); en=qdate(str(e.get('end_date') or e.get('start_date') or '')[:10])
        return bool(s and en and s<=d<=en)
    except:
        return False


def _family_dashboard_html():
    today=date.today(); week_end=today+timedelta(days=6)
    events=_visible_home_events(today,week_end)
    today_events=[e for e in events if _event_overlaps(e,today)]
    week_events=sorted(events,key=lambda x:(str(x.get('start_date') or ''),str(x.get('title') or '')))

    by_day={}
    for e in week_events:
        sd=qdate(str(e.get('start_date') or '')[:10])
        if sd: by_day.setdefault(sd,[]).append(e)
    clashes=[]
    for d,arr in by_day.items():
        persons={str(x.get('person') or '').strip() for x in arr if str(x.get('person') or '').strip()}
        if len(arr)>=2 and len(persons)>=2:
            clashes.append((d,arr))

    tasks=_task_rows(False,5)
    b='<div class="feature-grid">'
    b+='<section class="feature-card"><h2>오늘 일정</h2><div class="feature-list">'
    if not today_events: b+='<div class="muted">오늘 일정 없음</div>'
    for e in today_events:
        kind,label=_event_kind(e)
        b+=f'<div class="feature-row"><div><b>{H(_clean_title(e.get("title")))}</b><div class="feature-meta">{H(label)}</div></div><span class="feature-badge">오늘</span></div>'
    b+='</div></section>'

    b+='<section class="feature-card"><h2>할 일</h2><div class="feature-list">'
    if not tasks: b+='<div class="muted">미완료 할 일 없음</div>'
    for t in tasks:
        b+=f'<div class="feature-row"><div><b>{H(t["title"])}</b><div class="feature-meta">{H(_task_label(t))}</div></div><form method="post" action="/tasks/{t["id"]}/toggle"><button class="btn s">완료</button></form></div>'
    b+='<div style="margin-top:8px"><a class="btn s" href="/tasks">전체 할 일 보기</a></div></div></section></div>'

    b+='<section class="feature-card" style="margin-top:12px"><h2>이번 주 일정</h2>'
    if clashes:
        for d,arr in clashes:
            names=' · '.join(_clean_title(x.get('title')) for x in arr[:3])
            b+=f'<div class="feature-alert"><b>{d.strftime("%m/%d")} 일정 겹침</b> · {H(names)}</div>'
    b+='<div class="feature-list">'
    if not week_events: b+='<div class="muted">이번 주 일정 없음</div>'
    for e in week_events[:12]:
        sd=qdate(str(e.get('start_date') or '')[:10]); kind,label=_event_kind(e)
        b+=f'<div class="feature-row"><div><b>{H(_clean_title(e.get("title")))}</b><div class="feature-meta">{H(label)} · {H(sd.strftime("%m/%d") if sd else "")}</div></div></div>'
    b+='</div></section>'
    return b


# Inject the new family dashboard below the existing fast home and a trip-planner
# button on every trip detail page without replacing the existing route handlers.
@app.after_request
def family_feature_injection(response):
    try:
        if request.method!='GET' or response.status_code!=200 or 'text/html' not in (response.content_type or ''):
            return response
        html=response.get_data(as_text=True)
        if request.path=='/':
            dash=_family_dashboard_html()
            html=html.replace('</main>',dash+'</main>',1)
        elif request.path.startswith('/trip/') and request.path.count('/')==2:
            parts=request.path.strip('/').split('/')
            if len(parts)==2 and parts[0]=='trip' and parts[1].isdigit():
                trip_id=int(parts[1])
                btn=f'<a class="btn trip-plan-link" href="/trip/{trip_id}/plan">여행 준비</a>'
                marker='<div class="trip-actions">'
                if marker in html:
                    html=html.replace(marker,marker+btn,1)
                else:
                    html=html.replace('</div></div>',btn+'</div></div>',1)
        response.set_data(html)
        response.headers['Content-Length']=str(len(response.get_data()))
    except Exception as e:
        print(f'Family feature injection failed: {type(e).__name__}',flush=True)
    return response

# ===================== from family_next_app.py =====================
KST = ZoneInfo('Asia/Seoul')
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '').strip()
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '').replace('\\n', '\n').strip()


# ===== schema =====
def init_next_schema():
    c = db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS push_subscriptions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      endpoint TEXT NOT NULL UNIQUE,
      p256dh TEXT NOT NULL,
      auth TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS push_log(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      subscription_id INTEGER NOT NULL,
      reminder_key TEXT NOT NULL,
      sent_at TEXT NOT NULL,
      UNIQUE(subscription_id, reminder_key)
    );
    ''')
    c.commit(); c.close()


init_next_schema()


# ===== shared UI / nav =====
CSS += '''
.person-tabs{display:flex;gap:6px;margin-bottom:12px}.person-tabs a{padding:8px 12px;border-radius:9px;text-decoration:none;background:#eaf0f6;color:#65758b;font-size:13px;font-weight:700}.person-tabs a.on{background:#0f4c81;color:#fff}.person-week{display:grid;grid-template-columns:repeat(7,minmax(145px,1fr));gap:8px;overflow-x:auto;padding-bottom:8px}.person-day{min-width:145px;background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:10px}.person-day.today{border:2px solid #0f4c81}.person-date{font-size:11px;color:#7b8797}.person-item{margin-top:7px;padding:8px;border-radius:9px;background:#f2f5f8;border-left:4px solid #7d8793;font-size:12px}.person-item.academy{background:#fff2eb;border-left-color:#e98755}.person-item.family{background:#fff7df;border-left-color:#c99a35}.person-item.trip{background:#fff0f1;border-left-color:#d64f5b}.notify-card{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:16px;max-width:680px}.notify-state{margin:10px 0;padding:10px;border-radius:10px;background:#f2f5f8}.auto-note{font-size:11px;color:#748196;margin-top:4px}
@media(max-width:700px){.person-week{grid-template-columns:repeat(7,minmax(138px,1fr))}.person-day{min-width:138px;padding:8px}}
'''


def next_nav():
    return ('<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b>'
            '<div class="nav">'
            '<a href="/past">과거 여행</a>'
            '<a href="/future">향후 여행</a>'
            '<a href="/calendar">가족 달력</a>'
            '<a href="/tasks">할 일</a>'
            '<a href="/kids">아이 일정</a>'
            '<a href="/notifications">알림</a>'
            '</div></nav></header>')


nav = next_nav
try:
    _manifest['shortcuts'] = [x for x in _manifest.get('shortcuts', []) if x.get('url') != '/riley']
    _manifest['shortcuts'].append({'name':'아이 일정','short_name':'아이 일정','url':'/kids'})
    _manifest['shortcuts'].append({'name':'알림 설정','short_name':'알림','url':'/notifications'})
except Exception:
    pass


# ===== child weekly schedules =====
def _person_events(person, mon, sun):
    rows=[]
    for raw in _cached_calendar_events(mon, sun):
        e=dict(raw)
        compact=(e.get('title') or '').replace(' ','')
        if '청소아줌마' in compact:
            continue
        who=(e.get('person') or '').strip()
        title=(e.get('title') or '').strip()
        category=(e.get('category') or '').strip()
        source=e.get('source') or ''
        related=(person in who) or (person in title) or who=='가족' or category in ('공휴일','휴일')
        if source=='trip' and person in (who or ''):
            related=True
        if not related:
            continue
        try:
            sd=datetime.strptime(str(e.get('start_date') or '')[:10],'%Y-%m-%d').date()
            ed=datetime.strptime(str(e.get('end_date') or e.get('start_date') or '')[:10],'%Y-%m-%d').date()
        except Exception:
            continue
        d=max(sd,mon)
        while d<=min(ed,sun):
            rows.append({'date':d,'title':title or '(제목 없음)','meta':category or who or '가족','kind':'trip' if source=='trip' else 'family','time':''})
            d+=timedelta(days=1)

    if person=='지유':
        c=db(); academy=[dict(x) for x in c.execute('select * from academy where active=1 order by start_time,id').fetchall()]; c.close()
        for r in academy:
            day=(r.get('day_of_week') or '').strip()
            if day not in DAYS:
                continue
            d=mon+timedelta(days=DAYS.index(day))
            rows.append({'date':d,'title':r.get('academy') or '일정','meta':r.get('subject') or '지유 일정','kind':'academy','time':r.get('start_time') or ''})
    rows.sort(key=lambda x:(x['date'],x.get('time') or '99:99',x['title']))
    return rows


@app.route('/kids')
def kids_schedule():
    person=(request.args.get('person') or '지유').strip()
    if person not in ('지유','혜온'):
        person='지유'
    q=qdate(request.args.get('date','')) or date.today()
    mon=q-timedelta(days=q.weekday()); sun=mon+timedelta(days=6); today=date.today()
    rows=_person_events(person,mon,sun)
    by={mon+timedelta(days=i):[] for i in range(7)}
    for r in rows:
        by[r['date']].append(r)
    prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
    tabs=(f'<div class="person-tabs"><a class="{"on" if person=="지유" else ""}" href="/kids?person=지유&date={q.isoformat()}">지유</a>'
          f'<a class="{"on" if person=="혜온" else ""}" href="/kids?person=혜온&date={q.isoformat()}">혜온</a></div>')
    nav=(f'<div class="riley-toolbar"><div><a class="btn s" href="/kids?person={H(person)}&date={prev}">← 이전 주</a> '
         f'<a class="btn s" href="/kids?person={H(person)}&date={today.isoformat()}">이번 주</a> '
         f'<a class="btn s" href="/kids?person={H(person)}&date={nxt}">다음 주 →</a></div>'
         f'<b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div>')
    body=tabs+nav+'<div class="person-week">'
    for i in range(7):
        d=mon+timedelta(days=i)
        body+=f'<div class="person-day {"today" if d==today else ""}"><div class="person-date">{d.strftime("%m/%d")}</div><h3>{DAYS[i]}</h3>'
        if not by[d]:
            body+='<div class="muted">일정 없음</div>'
        for r in by[d]:
            meta=(r.get('time')+' · ' if r.get('time') else '')+(r.get('meta') or '')
            body+=f'<div class="person-item {r["kind"]}"><b>{H(r["title"])}</b><div class="feature-meta">{H(meta)}</div></div>'
        body+='</div>'
    body+='</div>'
    return page(f'{person} 주간 일정',body)


# Keep old /riley links working, but direct users to the unified child schedule.
@app.route('/children')
def children_alias():
    return redirect('/kids')


# ===== automatic trip preparation checklist =====
AUTO_CHECKS = [
    (30,'서류','여권 유효기간 확인'),
    (30,'예약','주요 교통·숙소 예약 확인'),
    (30,'준비','여행자보험 검토'),
    (7,'준비','현지 날씨 확인 및 옷 준비'),
    (7,'아이','상비약·아이 준비물 점검'),
    (7,'결제','환전·해외 결제수단 점검'),
    (1,'체크인','온라인 체크인'),
    (1,'서류','여권·예약증 최종 확인'),
    (1,'짐','충전기·짐 최종 점검'),
]


def _ensure_auto_checklist(trip_id):
    c=db(); trip=c.execute('select id,start_date,status from trips where id=?',(trip_id,)).fetchone()
    if not trip:
        c.close(); return
    start=qdate(trip['start_date'] or '')
    if not start:
        c.close(); return
    existing={r['title'] for r in c.execute('select title from trip_checklist where trip_id=?',(trip_id,)).fetchall()}
    now=datetime.now().isoformat(timespec='seconds')
    for days_before,category,title in AUTO_CHECKS:
        auto_title='[자동] '+title
        if auto_title in existing:
            continue
        due=(start-timedelta(days=days_before)).isoformat()
        c.execute('insert into trip_checklist(trip_id,title,category,assignee,due_date,done,created_at) values(?,?,?,?,?,0,?)',
                  (trip_id,auto_title,category,'가족',due,now))
    c.commit(); c.close()


_original_trip_plan=None
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/trip/<int:trip_id>/plan':
        _original_trip_plan=app.view_functions[rule.endpoint]
        break

if _original_trip_plan:
    def trip_plan_with_auto(trip_id):
        _ensure_auto_checklist(trip_id)
        return _original_trip_plan(trip_id)
    for rule in list(app.url_map.iter_rules()):
        if rule.rule=='/trip/<int:trip_id>/plan':
            app.view_functions[rule.endpoint]=trip_plan_with_auto


# ===== web push =====
def _push_enabled():
    return bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)


@app.route('/push/public-key')
def push_public_key():
    return Response(json.dumps({'publicKey':VAPID_PUBLIC_KEY if _push_enabled() else ''}),mimetype='application/json')


@app.route('/push/subscribe',methods=['POST'])
def push_subscribe():
    if not _push_enabled():
        return Response(json.dumps({'ok':False,'error':'push_not_configured'}),status=503,mimetype='application/json')
    data=request.get_json(silent=True) or {}
    endpoint=(data.get('endpoint') or '').strip(); keys=data.get('keys') or {}
    p256dh=(keys.get('p256dh') or '').strip(); auth=(keys.get('auth') or '').strip()
    if not endpoint or not p256dh or not auth:
        return Response(json.dumps({'ok':False}),status=400,mimetype='application/json')
    c=db(); c.execute('insert into push_subscriptions(endpoint,p256dh,auth,created_at) values(?,?,?,?) on conflict(endpoint) do update set p256dh=excluded.p256dh,auth=excluded.auth',
                           (endpoint,p256dh,auth,datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return Response(json.dumps({'ok':True}),mimetype='application/json')


@app.route('/notifications')
def notification_settings():
    configured='사용 가능' if _push_enabled() else '설정 필요'
    body=f'''<div class="notify-card"><h2>PWA 알림</h2>
<p>가족 일정과 여행 준비 마감이 가까워지면 설치된 앱으로 알림을 받을 수 있습니다.</p>
<div class="notify-state">서버 상태: <b>{configured}</b><br>알림 대상: 오늘/내일 가족 할 일 · 내일 가족 일정 · 여행 D-7/D-1 · 여행 준비 체크리스트</div>
<button class="btn" id="pushEnable" onclick="enableFamilyPush()">이 기기에서 알림 켜기</button>
<div id="pushResult" class="feature-meta" style="margin-top:8px"></div></div>
<script>
function b64ToUint8Array(base64String){{const padding='='.repeat((4-base64String.length%4)%4);const base64=(base64String+padding).replace(/-/g,'+').replace(/_/g,'/');const raw=atob(base64);return Uint8Array.from([...raw].map(c=>c.charCodeAt(0)));}}
async function enableFamilyPush(){{
 const out=document.getElementById('pushResult');
 try{{
  if(!('serviceWorker' in navigator)||!('PushManager' in window)) throw new Error('이 브라우저는 푸시 알림을 지원하지 않습니다.');
  const perm=await Notification.requestPermission(); if(perm!=='granted') throw new Error('알림 권한이 허용되지 않았습니다.');
  const keyResp=await fetch('/push/public-key'); const keyData=await keyResp.json(); if(!keyData.publicKey) throw new Error('서버 알림 설정이 아직 준비되지 않았습니다.');
  const reg=await navigator.serviceWorker.ready;
  let sub=await reg.pushManager.getSubscription();
  if(!sub) sub=await reg.pushManager.subscribe({{userVisibleOnly:true,applicationServerKey:b64ToUint8Array(keyData.publicKey)}});
  const resp=await fetch('/push/subscribe',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(sub)}});
  if(!resp.ok) throw new Error('구독 저장에 실패했습니다.');
  out.textContent='알림이 켜졌습니다.';
 }}catch(e){{out.textContent=e.message||'알림 설정에 실패했습니다.';}}
}}
</script>'''
    return page('알림 설정',body)


# Add push handling to the existing service worker without changing its cache behavior.
_SW += '''\nself.addEventListener('push',event=>{let data={};try{data=event.data?event.data.json():{};}catch(e){data={body:event.data?event.data.text():''};}const title=data.title||'우리 가족 기록';const options={body:data.body||'',icon:'/pwa-icon-v2.svg',badge:'/pwa-icon-v2.svg',data:{url:data.url||'/'}};event.waitUntil(self.registration.showNotification(title,options));});self.addEventListener('notificationclick',event=>{event.notification.close();const url=(event.notification.data&&event.notification.data.url)||'/';event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list=>{for(const c of list){if('focus'in c){c.navigate(url);return c.focus();}}return clients.openWindow(url);}));});'''


def _subscriptions():
    c=db(); rows=[dict(x) for x in c.execute('select * from push_subscriptions').fetchall()]; c.close(); return rows


def _already_sent(sub_id,key):
    c=db(); r=c.execute('select 1 from push_log where subscription_id=? and reminder_key=?',(sub_id,key)).fetchone(); c.close(); return bool(r)


def _mark_sent(sub_id,key):
    c=db(); c.execute('insert or ignore into push_log(subscription_id,reminder_key,sent_at) values(?,?,?)',(sub_id,key,datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()


def _delete_subscription(sub_id):
    c=db(); c.execute('delete from push_subscriptions where id=?',(sub_id,)); c.execute('delete from push_log where subscription_id=?',(sub_id,)); c.commit(); c.close()


def _send_one(sub,title,body,url,key):
    if _already_sent(sub['id'],key):
        return
    info={'endpoint':sub['endpoint'],'keys':{'p256dh':sub['p256dh'],'auth':sub['auth']}}
    try:
        webpush(subscription_info=info,data=json.dumps({'title':title,'body':body,'url':url},ensure_ascii=False),vapid_private_key=VAPID_PRIVATE_KEY,vapid_claims={'sub':'mailto:family-app@example.com'},ttl=3600)
        _mark_sent(sub['id'],key)
    except WebPushException as e:
        status=getattr(getattr(e,'response',None),'status_code',None)
        if status in (404,410):
            _delete_subscription(sub['id'])
    except Exception as e:
        print(f'Push reminder failed: {type(e).__name__}',flush=True)


def _reminders_for(now):
    today=now.date(); tomorrow=today+timedelta(days=1); reminders=[]
    c=db()
    today_tasks=[dict(x) for x in c.execute("select * from family_tasks where done=0 and due_date=?",(today.isoformat(),)).fetchall()]
    tomorrow_tasks=[dict(x) for x in c.execute("select * from family_tasks where done=0 and due_date=?",(tomorrow.isoformat(),)).fetchall()]
    today_checks=[dict(x) for x in c.execute("select tc.*,t.title trip_title from trip_checklist tc join trips t on t.id=tc.trip_id where tc.done=0 and tc.due_date=?",(today.isoformat(),)).fetchall()]
    tomorrow_checks=[dict(x) for x in c.execute("select tc.*,t.title trip_title from trip_checklist tc join trips t on t.id=tc.trip_id where tc.done=0 and tc.due_date=?",(tomorrow.isoformat(),)).fetchall()]
    future=[dict(x) for x in c.execute("select id,title,start_date from trips where status!='완료' and start_date>=? order by start_date",(today.isoformat(),)).fetchall()]
    c.close()
    if 7<=now.hour<=10:
        if today_tasks:
            reminders.append(('오늘 할 일',f'{len(today_tasks)}건의 가족 할 일이 오늘 마감입니다.','/tasks',f'task-today-{today.isoformat()}'))
        if today_checks:
            reminders.append(('오늘 여행 준비',f'{len(today_checks)}건의 여행 준비 항목이 오늘 마감입니다.','/future',f'check-today-{today.isoformat()}'))
        for t in future:
            sd=qdate(t.get('start_date') or '')
            if not sd: continue
            left=(sd-today).days
            if left in (7,1):
                reminders.append((f'{t["title"]} D-{left}','여행 준비 체크리스트와 예약을 확인하세요.',f'/trip/{t["id"]}/plan',f'trip-{t["id"]}-d{left}'))
    if 18<=now.hour<=21:
        events=[]
        for e in _cached_calendar_events(tomorrow,tomorrow):
            d=dict(e); compact=(d.get('title') or '').replace(' ','')
            if '청소아줌마' in compact: continue
            events.append(d)
        if events:
            reminders.append(('내일 가족 일정',f'{len(events)}건의 일정이 있습니다.','/calendar',f'events-tomorrow-{tomorrow.isoformat()}'))
        if tomorrow_tasks:
            reminders.append(('내일 마감 할 일',f'{len(tomorrow_tasks)}건의 가족 할 일이 내일 마감입니다.','/tasks',f'task-tomorrow-{tomorrow.isoformat()}'))
        if tomorrow_checks:
            reminders.append(('내일 여행 준비',f'{len(tomorrow_checks)}건의 여행 준비 항목이 내일 마감입니다.','/future',f'check-tomorrow-{tomorrow.isoformat()}'))
    return reminders


def push_loop():
    time.sleep(20)
    while True:
        try:
            if _push_enabled():
                now=datetime.now(KST)
                reminders=_reminders_for(now)
                if reminders:
                    for sub in _subscriptions():
                        for title,body,url,key in reminders:
                            _send_one(sub,title,body,url,key)
        except Exception as e:
            print(f'Push loop failed: {type(e).__name__}',flush=True)
        time.sleep(1800)


threading.Thread(target=push_loop,daemon=True,name='family-push-reminders').start()

# ===================== from home_tasks_only_app.py =====================
def _tasks_card():
    tasks = _task_rows(False, 5)
    body = '<section class="feature-card" style="margin-top:12px"><h2>할 일</h2><div class="feature-list">'
    if not tasks:
        body += '<div class="muted">미완료 할 일 없음</div>'
    for t in tasks:
        body += (f'<div class="feature-row"><div><b>{H(t["title"])}</b>'
                 f'<div class="feature-meta">{H(_task_label(t))}</div></div>'
                 f'<form method="post" action="/tasks/{t["id"]}/toggle"><button class="btn s">완료</button></form></div>')
    body += '<div style="margin-top:8px"><a class="btn s" href="/tasks">전체 할 일 보기</a></div></div></section>'
    return body


def tasks_only_home():
    today = date.today()
    c = db()
    domestic = _next_trip_by_type(c, today, '국내')
    overseas = _next_trip_by_type(c, today, '해외')
    c.close()
    family_events = _upcoming_events(today)

    body = '<div class="next-trip-grid">' + _trip_card(domestic, today, '다음 국내 여행') + _trip_card(overseas, today, '다음 해외 여행') + '</div>'
    body += '<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-family-list">'
    if not family_events:
        body += '<div class="muted" style="padding:10px 0">등록된 가족 일정이 없습니다.</div>'
    for d, e in family_events:
        kind, label = _event_kind(e)
        end = str(e.get('end_date') or '')[:10]
        date_text = d.isoformat() if not end or end == d.isoformat() else f'{d.isoformat()} ~ {end}'
        dday = _dday_label(d, today)
        today_cls = ' today' if dday == 'D-DAY' else ''
        title = _clean_title(e.get('title'))
        body += (f'<div class="home-family-row">'
                 f'<span class="event-dot {kind}" title="{H(label)}"></span>'
                 f'<div class="event-main"><div class="event-title">{H(title)}</div>'
                 f'<div class="event-meta">{H(label)} · {H(date_text)}</div></div>'
                 f'<span class="event-dday{today_cls}">{H(dday)}</span></div>')
    body += '</div></section>'
    body += _tasks_card()
    return page('우리 가족 기록', body)


# home_cleanup_app's before_request calls this module-level function dynamically,
# so replacing it removes the added today/weekly schedule panels while keeping tasks.
clean_family_home = tasks_only_home

for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/':
        app.view_functions[rule.endpoint] = tasks_only_home

if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','8080')))

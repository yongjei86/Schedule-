import os, json, time, threading, sqlite3, calendar, html, secrets, re
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
def _init_academy_color_schema():
    c=db()
    cols={r['name'] for r in c.execute('PRAGMA table_info(academy)')}
    if 'color' not in cols:
        c.execute('ALTER TABLE academy ADD COLUMN color TEXT')
    if 'child' not in cols:
        c.execute('ALTER TABLE academy ADD COLUMN child TEXT')
    c.execute("update academy set child='지유' where child is null or child=''")
    c.commit(); c.close()
_init_academy_color_schema()

CSS='''body{margin:0;background:#f4f7fb;color:#14263f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}*{box-sizing:border-box}header{position:sticky;top:0;z-index:10;background:#f4f7fbf2;border-bottom:1px solid #e4e9f0}nav{max-width:1240px;margin:auto;padding:10px 16px;display:flex;justify-content:space-between;gap:10px}.nav{display:flex;gap:5px;overflow:auto}.nav a,.btn{white-space:nowrap;text-decoration:none;border:0;border-radius:9px;padding:8px 10px;font:inherit;font-size:13px;cursor:pointer}.nav a{color:#728096}.btn{background:#0f4c81;color:#fff}.btn.s{background:#fff;color:#14263f;border:1px solid #e4e9f0}.btn.d{background:#b64b50}.wrap{max-width:1240px;margin:auto;padding:18px 16px 50px}.hero{background:linear-gradient(145deg,#0f4c81,#173d66);color:#fff;border-radius:20px;padding:22px;margin-bottom:18px}.hero h1{margin:0}.toolbar{display:flex;justify-content:space-between;gap:8px;align-items:center;margin:10px 0;flex-wrap:wrap}.seg{display:flex;background:#eaf0f6;border-radius:10px;padding:3px}.seg a{padding:7px 11px;text-decoration:none;color:#65758b;border-radius:8px;font-size:13px}.seg a.on{background:#fff;color:#0f4c81;font-weight:800;box-shadow:0 1px 4px #00000014}.box{background:#fff;border:1px solid #e4e9f0;border-radius:15px;overflow:auto}table{width:100%;border-collapse:collapse;min-width:950px}th,td{padding:10px;border-bottom:1px solid #e4e9f0;text-align:left;font-size:13px}th{background:#fbfcfe;color:#728096}.trip{cursor:pointer}.trip:hover{background:#f7fbff}.detail td{background:#f8fafc;padding:14px}.meta{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.m{background:#fff;border:1px solid #e4e9f0;border-radius:10px;padding:10px}.m b{display:block;color:#728096;font-size:11px}.it{display:grid;grid-template-columns:90px 70px 1fr 1fr auto;gap:8px;background:#fff;border:1px solid #e4e9f0;border-radius:9px;padding:9px;margin-top:7px}.pill{display:inline-block;padding:4px 7px;border-radius:999px;background:#eaf3fb;color:#0f4c81;font-size:11px;font-weight:700}.event{background:#fff;border:1px solid #e4e9f0;border-radius:10px;padding:10px;margin-top:7px;display:flex;justify-content:space-between;gap:8px}.monthbig{background:#fff;border:1px solid #e4e9f0;border-radius:16px;padding:14px}.monthgrid{display:grid;grid-template-columns:repeat(7,1fr);border-left:1px solid #e4e9f0;border-top:1px solid #e4e9f0}.dow{padding:10px;text-align:center;font-size:12px;color:#718097;background:#fafbfd;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0}.cell{min-height:112px;padding:7px;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0;background:#fff}.cell.out{background:#fafbfd;color:#b1bac6}.num{font-size:12px;font-weight:800;margin-bottom:5px}.ce{display:block;background:#eaf3fb;color:#0f4c81;border-radius:6px;padding:4px 5px;margin:3px 0;font-size:11px;overflow:hidden}.weekcal{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}.wday{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px;min-height:220px}.wday h3{margin:0 0 10px;text-align:center;font-size:14px}.yeargrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.mini{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px}.mini h3{text-align:center;margin:2px 0 8px}.minigrid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}.md{font-size:10px;text-align:center;padding:4px;border-radius:4px}.md.has{background:#eaf3fb;color:#0f4c81;font-weight:800}.schedule{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}.sday{background:#fff;border:1px solid #e4e9f0;border-radius:13px;min-height:230px;padding:10px}.sday .date{font-size:11px;color:#7a8798}.sday h3{margin:3px 0 10px}.lesson{background:#eaf3fb;border-radius:9px;padding:8px;margin-bottom:7px;font-size:12px}.lesson b{display:block;margin-bottom:3px}.modal{display:none;position:fixed;inset:0;background:#10203088;z-index:30;padding:16px;overflow:auto}.modal.show{display:block}.card{max-width:720px;margin:3vh auto;background:#fff;border-radius:16px;padding:16px}.head{display:flex;justify-content:space-between}.form{display:grid;grid-template-columns:1fr 1fr;gap:10px}.full{grid-column:1/-1}label{font-size:12px;color:#728096;display:grid;gap:4px}input,select,textarea{width:100%;padding:9px;border:1px solid #ccd5e0;border-radius:8px;font:inherit}textarea{min-height:70px}@media(max-width:900px){.schedule,.weekcal{grid-template-columns:repeat(2,1fr)}.yeargrid{grid-template-columns:repeat(2,1fr)}.meta{grid-template-columns:1fr}.it{grid-template-columns:80px 60px 1fr}.it .place{grid-column:3}.nav{max-width:72vw}.cell{min-height:90px}}@media(max-width:560px){.schedule,.weekcal,.yeargrid,.form{grid-template-columns:1fr}.full{grid-column:1}.hero h1{font-size:26px}.monthbig{padding:8px}.cell{min-height:74px;padding:4px}.ce{font-size:9px;padding:3px}.dow{padding:6px;font-size:10px}}'''
JS='''function t(id){let e=document.getElementById("d"+id);e.style.display=e.style.display==="none"?"table-row":"none"}function o(id){document.getElementById(id).classList.add("show")}function x(id){document.getElementById(id).classList.remove("show")}function ntrip(){document.getElementById("tf").action="/trip/add";document.getElementById("tf").reset();o("tm")}function et(b){let d=b.dataset;document.getElementById("tf").action="/trip/"+d.id+"/edit";["start_date","end_date","country","region","title","companions","trip_type","status","lodging","transport","notes"].forEach(k=>document.querySelector("#tm [name="+k+"]").value=d[k]||"");o("tm")}function ni(id){document.getElementById("if").action="/itinerary/add";document.getElementById("if").reset();document.querySelector("#im [name=trip_id]").value=id;o("im")}function ei(b){let d=b.dataset;document.getElementById("if").action="/itinerary/"+d.id+"/edit";["trip_id","item_date","day_label","time_text","title","place","detail","sort_order"].forEach(k=>document.querySelector("#im [name="+k+"]").value=d[k]||"");o("im")}function ne(){document.getElementById("ef").action="/event/add";document.getElementById("ef").reset();o("em")}function ee(b){let d=b.dataset;document.getElementById("ef").action="/event/"+d.id+"/edit";["start_date","end_date","title","category","person","notes"].forEach(k=>document.querySelector("#em [name="+k+"]").value=d[k]||"");o("em")}function na(day){let f=document.getElementById("af");f.action="/academy/add";f.reset();f.dataset.id="";document.getElementById("am-delete").style.display="none";if(day)document.querySelector("#am [name=day_of_week]").value=day;document.querySelector("#am [name=color]").value="#e98755";o("am")}function ea(b){let d=b.dataset;let f=document.getElementById("af");f.action="/academy/"+d.id+"/edit";f.dataset.id=d.id;["day_of_week","start_time","end_time","academy","subject","location","notes"].forEach(k=>document.querySelector("#am [name="+k+"]").value=d[k]||"");document.querySelector("#am [name=color]").value=d.color||"#e98755";document.getElementById("am-delete").style.display="inline-block";o("am")}function deleteAcademy(){let id=document.getElementById("af").dataset.id;if(!id||!confirm("삭제할까요?"))return;let f=document.createElement("form");f.method="post";f.action="/academy/"+id+"/delete";document.body.appendChild(f);f.submit()}'''
JS+='''function showEventDetail(el){let d=el.dataset;document.getElementById("ed-title").textContent=d.title||"";let range=d.start_date===d.end_date?d.start_date:d.start_date+" ~ "+d.end_date;document.getElementById("ed-date").textContent=range||"";let tm=d.start_time?(d.end_time&&d.end_time!==d.start_time?d.start_time+" ~ "+d.end_time:d.start_time):"종일";document.getElementById("ed-time").textContent=tm;document.getElementById("ed-kind").textContent=d.kind||"";document.getElementById("ed-person").textContent=d.person||"-";document.getElementById("ed-notes").textContent=d.notes||"-";let tl=document.getElementById("ed-triplink");tl.innerHTML=d.trip_id?'<a class="btn s" href="/trip/'+d.trip_id+'">여행 상세보기</a>':"";let df=document.getElementById("ed-delete-form");df.innerHTML='<button type="submit" class="btn d">삭제</button>';if(d.source==="local"&&d.id){df.action="/event/"+d.id+"/delete";df.style.display="block"}else if(d.key){df.action="/calendar-event/hide";let inp=document.createElement("input");inp.type="hidden";inp.name="key";inp.value=d.key;df.insertBefore(inp,df.firstChild);df.style.display="block"}else{df.style.display="none"}o("ed")}'''
CSS+='''.fab-group{position:fixed;right:18px;bottom:18px;display:flex;flex-direction:column;gap:10px;z-index:20}.fab{width:46px;height:46px;border-radius:50%;background:#0f4c81;color:#fff;border:0;font-size:20px;line-height:1;cursor:pointer;box-shadow:0 4px 14px #0f4c8155;display:flex;align-items:center;justify-content:center;transition:transform .12s ease,box-shadow .12s ease}.fab:hover{box-shadow:0 6px 18px #0f4c8166;transform:translateY(-1px)}.fab:active{transform:scale(.94)}@media(max-width:560px){.fab-group{right:14px;bottom:14px;gap:8px}.fab{width:42px;height:42px;font-size:18px}}'''
CSS+='''.fm-event,.event-chip{cursor:pointer}.fm-event:hover,.event-chip:hover{filter:brightness(0.96)}'''
CSS+='''.day-checks{display:flex;gap:8px;flex-wrap:wrap}.day-check{display:flex;align-items:center;gap:4px;width:auto;font-size:12px;color:#14263f}.day-check input{width:auto}'''
JS+='''function toggleAllDays(cb){let box=cb.closest(".day-checks");box.querySelectorAll("input[name=\\"days\\"]").forEach(x=>x.checked=cb.checked)}function editWb(el){let d=el.dataset;let base=d.base||document.getElementById("wbef").dataset.base||"/riley";document.getElementById("wbef").action=base+"/workbook/group/"+d.gid+"/edit";document.getElementById("wbef").dataset.gid=d.gid;document.getElementById("wbef").dataset.base=base;document.getElementById("wbe-title").value=d.title||"";document.getElementById("wbe-notes").value=d.notes||"";document.getElementById("wbe-color").value=d.color||"#0f4c81";let days=(d.days||"").split(",").filter(Boolean);document.querySelectorAll("#wbe-days input[name=\\"days\\"]").forEach(cb=>cb.checked=days.includes(cb.value));o("wbe")}function deleteWb(){let f0=document.getElementById("wbef");let gid=f0.dataset.gid;let base=f0.dataset.base||"/riley";if(!gid||!confirm("삭제할까요?"))return;let f=document.createElement("form");f.method="post";f.action=base+"/workbook/group/"+gid+"/delete";document.body.appendChild(f);f.submit()}let wbEditMode=false;function wbToggleEditMode(btn){wbEditMode=!wbEditMode;btn.classList.toggle("on",wbEditMode);btn.textContent=wbEditMode?"항목을 눌러 수정":"수정"}'''
CSS+='''.person-filter{display:flex;gap:6px;flex-wrap:wrap;margin:2px 0 14px}.pf{border:1px solid #d7dfe8;background:#fff;color:#5c6b80;border-radius:999px;padding:6px 12px;font-size:12px;font-weight:700;text-decoration:none;transition:all .12s ease}.pf:hover{border-color:#0f4c81;color:#0f4c81}.pf.on{color:#fff;border-color:transparent}.pf.on.yj{background:#315c9b}.pf.on.지유{background:#e98755}.pf.on.보미{background:#9a66ad}.pf.on.혜온{background:#46a081}.pf.on.가족{background:#c99a35}.pf.on.여행{background:#d64f5b}.pf.on:not(.yj):not(.지유):not(.보미):not(.혜온):not(.가족):not(.여행){background:#14263f}'''
CSS+='''.view-value{cursor:pointer;display:block}.view-value:hover{color:#0f4c81}.inline-edit{display:none;flex-direction:column;gap:6px;margin-top:2px}.inline-edit input{padding:7px 9px;border:1px solid #d5dde7;border-radius:8px;font:inherit;font-size:13px}'''
CSS+='''.future-card{display:block;color:inherit;text-decoration:none}.status-form{margin-top:8px}.status-select{width:100%;border:1px solid #d7dfe8;border-radius:8px;padding:6px 8px;font-size:12px;font-weight:800;cursor:pointer;background:#eef2f6;color:#5c6b80}.status-select.planned{background:#e8f6ee;color:#1f7a4d;border-color:#bfe4cd}.status-select.review{background:#fff3e0;color:#b5680a;border-color:#f3d9ab}.status-select.longterm{background:#f1ecfb;color:#6a4fb0;border-color:#dccdf5}.status-select.done{background:#eef2f6;color:#5c6b80;border-color:#dfe6ee}.status-badge{display:inline-block;margin-top:8px;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:800;background:#eef2f6;color:#5c6b80}.status-badge.planned{background:#e8f6ee;color:#1f7a4d}.status-badge.review{background:#fff3e0;color:#b5680a}.status-badge.longterm{background:#f1ecfb;color:#6a4fb0}.status-badge.done{background:#eef2f6;color:#5c6b80}'''
CSS+='''*{-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}.btn,.nav a,.seg a,.pf{transition:filter .12s ease,transform .06s ease,background .12s ease,color .12s ease,box-shadow .12s ease}.btn:hover{filter:brightness(1.07)}.btn:active{transform:scale(.97)}.box,.card,.home-card,.dashcard,.next-trip-card,.feature-card,.plan-section,.monthbig,.mini,.wday,.sday,.status-card,.stat-card,.summary-card{box-shadow:0 1px 3px rgba(20,38,63,.06)}.trip:hover,.home-family-row:hover,.event:hover,.feature-row:hover{background:#f7fbff}.home-family-row,.feature-row,.plan-row,.summary-row{transition:background .12s ease}.hero{box-shadow:0 6px 20px rgba(15,76,129,.18)}'''
JS+='''(function(){var t=document.getElementById("toTop");if(t)t.addEventListener("click",function(){window.scrollTo({top:0,behavior:"smooth"})});var r=document.getElementById("refreshBtn");if(r)r.addEventListener("click",function(){location.reload()})})();'''
def nav():return '<header><nav><b>✈️ 우리 가족 기록</b><div class="nav"><a href="/past">과거 여행</a><a href="/future">향후 여행</a><a href="/calendar">가족 달력</a><a href="/riley">지유 주간 학원 일정</a>'+('<a href="/logout">로그아웃</a>' if admin() else '<a href="/login">관리자</a>')+'</div></nav></header>'
def page(title,body):return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{H(title)}</title><style>{CSS}</style></head><body>{nav()}<main class="wrap"><div class="hero"><h1>{H(title)}</h1></div>{body}</main><div class="fab-group"><button class="fab" id="refreshBtn" aria-label="새로고침">⟳</button><button class="fab" id="toTop" aria-label="맨 위로">↑</button></div><script>{JS}</script></body></html>'
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
def td(i):
    must();c=db();c.execute('delete from trips where id=?',(i,));c.commit();c.close()
    ref=request.referrer or ''
    dest='/future' if ref.rstrip('/').endswith(f'/trip/{i}') else (ref or '/future')
    return redirect(dest)
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
af=['day_of_week','start_time','end_time','academy','subject','location','notes','color']
def _academy_form_values():
    v=[request.form.get(k,'') for k in af]
    child=(request.form.get('child') or '지유').strip()
    return v+[child]
@app.route('/academy/add',methods=['POST'])
def aa():must();c=db();v=_academy_form_values();c.execute('insert into academy('+','.join(af)+',child,active) values('+','.join('?'*len(v))+',1)',v);c.commit();c.close();return redirect(request.referrer or '/riley')
@app.route('/academy/<int:i>/edit',methods=['POST'])
def ae(i):must();c=db();v=_academy_form_values();c.execute('update academy set '+','.join(k+'=?' for k in af+['child'])+' where id=?',v+[i]);c.commit();c.close();return redirect(request.referrer or '/riley')
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

def _as_time(v):
    if isinstance(v, datetime):
        if v.tzinfo:
            v = v.astimezone(KST)
        return v.strftime('%H:%M')
    return ''

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
                    'start_time': _as_time(ds),
                    'end_time': _as_time(de),
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


_TIMED_GOOGLE_CACHE={}
_TIMED_GOOGLE_REFRESHING=set()
_TIMED_GOOGLE_LOCK=threading.Lock()
_TIMED_GOOGLE_TTL=900
_TIMED_GOOGLE_STALE_TTL=3600

def _fetch_timed_google(start,end,name='지유'):
    out=[]
    srcs=[s for s in _sources() if s.get('name')==name]
    ws=datetime.combine(start,dtime.min,tzinfo=KST); we=datetime.combine(end+timedelta(days=1),dtime.min,tzinfo=KST)
    for src in srcs:
        try:
            r=requests.get(src['url'],timeout=4,headers={'User-Agent':'YJ-Family-Calendar/1.0'}); r.raise_for_status()
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

def _refresh_timed_google_cache(key,start,end,name):
    try:
        out=_fetch_timed_google(start,end,name)
        with _TIMED_GOOGLE_LOCK:
            _TIMED_GOOGLE_CACHE[key]={'ts':time.time(),'events':out}
    finally:
        with _TIMED_GOOGLE_LOCK:
            _TIMED_GOOGLE_REFRESHING.discard(key)

def _timed_google(start,end,name='지유'):
    key=(name,start.isoformat(),end.isoformat())
    now=time.time()
    with _TIMED_GOOGLE_LOCK:
        cached=_TIMED_GOOGLE_CACHE.get(key)
        if cached and now-cached['ts']<_TIMED_GOOGLE_TTL:
            return list(cached['events'])
        if cached and now-cached['ts']<_TIMED_GOOGLE_STALE_TTL:
            if key not in _TIMED_GOOGLE_REFRESHING:
                _TIMED_GOOGLE_REFRESHING.add(key)
                threading.Thread(target=_refresh_timed_google_cache,args=(key,start,end,name),daemon=True).start()
            return list(cached['events'])
    out=_fetch_timed_google(start,end,name)
    with _TIMED_GOOGLE_LOCK:
        _TIMED_GOOGLE_CACHE[key]={'ts':time.time(),'events':out}
    return out

def _prewarm_riley_timetable():
    try:
        today=datetime.now(KST).date()
        mon=today-timedelta(days=today.weekday())
        _timed_google(mon,mon+timedelta(days=6),'지유')
    except Exception as e:
        print('Riley timetable prewarm failed:',e,flush=True)

threading.Thread(target=_prewarm_riley_timetable,daemon=True).start()


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

FLAG_MAP={
'한국':'🇰🇷','대한민국':'🇰🇷','일본':'🇯🇵','대만':'🇹🇼','홍콩':'🇭🇰','마카오':'🇲🇴','중국':'🇨🇳',
'태국':'🇹🇭','베트남':'🇻🇳','인도네시아':'🇮🇩','미국':'🇺🇸','스페인':'🇪🇸','이탈리아':'🇮🇹',
'싱가포르':'🇸🇬','호주':'🇦🇺','체코':'🇨🇿','오스트리아':'🇦🇹','헝가리':'🇭🇺','필리핀':'🇵🇭',
'말레이시아':'🇲🇾','괌':'🇬🇺','사이판':'🇲🇵','프랑스':'🇫🇷','독일':'🇩🇪','영국':'🇬🇧',
'스위스':'🇨🇭','그리스':'🇬🇷','튀르키예':'🇹🇷','터키':'🇹🇷','캐나다':'🇨🇦','뉴질랜드':'🇳🇿',
'몰디브':'🇲🇻','두바이':'🇦🇪','아랍에미리트':'🇦🇪','인도':'🇮🇳','네덜란드':'🇳🇱','포르투갈':'🇵🇹',
}
def _flags_for(country,trip_type):
    if (trip_type or '').strip()=='국내':
        return '🇰🇷'
    flags=[]
    for p in _country_parts(country):
        f=FLAG_MAP.get(p)
        if f and f not in flags: flags.append(f)
    return ' '.join(flags) or '🌍'

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


def academy_modal(child='지유'):
    opts=''.join(f'<option>{d}</option>' for d in DAYS)+ '<option>미정</option>'
    return f'''<div class="modal" id="am"><div class="card"><div class="head"><h2>{H(child)} 일정 추가/수정</h2><button class="btn s" onclick="x('am')">닫기</button></div><form class="form" id="af" method="post"><input type="hidden" name="child" value="{H(child)}"><label>요일<select name="day_of_week">{opts}</select></label><label>시작 시간<input type="time" name="start_time"></label><label>종료 시간<input type="time" name="end_time"></label><label>학원/일정명<input name="academy" required></label><label>과목<input name="subject"></label><label>장소<input name="location"></label><label>색상<input type="color" name="color" value="#e98755"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full" style="display:flex;gap:8px"><button class="btn">저장</button><button type="button" class="btn d" id="am-delete" style="display:none" onclick="deleteAcademy()">삭제</button></div></form></div></div>'''

def _init_riley_workbook_schema():
    c=db()
    c.executescript('''CREATE TABLE IF NOT EXISTS riley_workbooks(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      notes TEXT,
      day_of_week TEXT,
      done INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    )''')
    cols={r['name'] for r in c.execute('PRAGMA table_info(riley_workbooks)')}
    if 'day_of_week' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN day_of_week TEXT')
    if 'group_id' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN group_id TEXT')
    if 'color' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN color TEXT')
    if 'child' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN child TEXT')
    if 'credited' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN credited INTEGER DEFAULT 0')
    if 'subject' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN subject TEXT')
    if 'status' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN status TEXT')
    if 'started_at' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN started_at TEXT')
    if 'completed_at' not in cols:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN completed_at TEXT')
    c.execute("update riley_workbooks set group_id='g'||id where group_id is null or group_id=''")
    c.execute("update riley_workbooks set child='지유' where child is null or child=''")
    c.execute("update riley_workbooks set status='진행중' where status is null or status=''")
    c.execute("update riley_workbooks set started_at=substr(created_at,1,10) where started_at is null or started_at=''")
    c.execute("update riley_workbooks set subject='수학' where (subject is null or subject='') and (title like '%수학%' or title like '%연산%' or title like '%플펙%' or title like '%디딤돌%' or title like '%최상위%' or title like '%쎈%' or title like '%큐브%')")
    c.execute("update riley_workbooks set subject='국어' where (subject is null or subject='') and (title like '%국어%' or title like '%독해%' or title like '%빠작%' or title like '%논술%' or title like '%어휘%')")
    c.execute("update riley_workbooks set subject='영어' where (subject is null or subject='') and (lower(title) like '%english%' or lower(title) like '%grammar%' or lower(title) like '%vocabulary%' or lower(title) like '%reading%' or lower(title) like '%writing%' or title like '%영어%')")
    c.execute("update riley_workbooks set subject='과학' where (subject is null or subject='') and title like '%과학%'")
    c.execute("update riley_workbooks set subject='사회' where (subject is null or subject='') and (title like '%사회%' or title like '%한국사%' or title like '%역사%')")
    c.execute("update riley_workbooks set subject='사고력' where (subject is null or subject='') and (title like '%밤비노%' or title like '%루크%')")
    c.execute("update riley_workbooks set subject='기타' where subject is null or subject=''")
    c.execute('''CREATE TABLE IF NOT EXISTS riley_credits(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      child TEXT NOT NULL,
      delta INTEGER NOT NULL,
      reason TEXT,
      created_at TEXT NOT NULL
    )''')
    credit_cols={r['name'] for r in c.execute('PRAGMA table_info(riley_credits)')}
    if 'event_date' not in credit_cols:
        c.execute('ALTER TABLE riley_credits ADD COLUMN event_date TEXT')
    if 'category' not in credit_cols:
        c.execute('ALTER TABLE riley_credits ADD COLUMN category TEXT')
    c.execute('''CREATE TABLE IF NOT EXISTS workbook_completions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      item_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      created_at TEXT NOT NULL,
      UNIQUE(item_id,date)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS workbook_credited(
      item_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      PRIMARY KEY(item_id,date)
    )''')
    # One-time migration: the old model had a single perpetual done/credited flag per
    # recurring row instead of per-date history. Carry any already-done dated row over
    # as "done today" so nothing looks reset, and mark it already-credited so it isn't
    # paid out a second time under the new per-date model.
    if 'wb_history_migrated' not in {r['name'] for r in c.execute("PRAGMA table_info(riley_workbooks)")}:
        c.execute('ALTER TABLE riley_workbooks ADD COLUMN wb_history_migrated INTEGER DEFAULT 0')
        today_iso=datetime.now(KST).date().isoformat()
        for r in c.execute("select id,credited from riley_workbooks where done=1 and day_of_week!='' and wb_history_migrated=0").fetchall():
            c.execute('insert or ignore into workbook_completions(item_id,date,created_at) values(?,?,?)',(r['id'],today_iso,datetime.now(KST).isoformat(timespec='seconds')))
            if r['credited']:
                c.execute('insert or ignore into workbook_credited(item_id,date) values(?,?)',(r['id'],today_iso))
        c.execute('update riley_workbooks set wb_history_migrated=1')
    c.commit(); c.close()
_init_riley_workbook_schema()

def _wb_completions_for_week(item_ids, mon, sun):
    if not item_ids: return set()
    c=db()
    placeholders=','.join('?'*len(item_ids))
    rows=c.execute(f'select item_id,date from workbook_completions where item_id in ({placeholders}) and date>=? and date<=?',(*item_ids,mon.isoformat(),sun.isoformat())).fetchall()
    c.close()
    return {(r['item_id'],r['date']) for r in rows}

def _award_credit(child,delta,reason,event_date=None,category=None):
    event_date=(event_date or datetime.now(KST).date().isoformat())[:10]
    c=db()
    c.execute('insert into riley_credits(child,delta,reason,created_at,event_date,category) values(?,?,?,?,?,?)',
              (child,delta,reason,datetime.now(KST).isoformat(timespec='seconds'),event_date,category or ''))
    c.commit(); c.close()

CREDIT_RATE_DEFAULTS={'workbook':1,'workbook_finish':10,'reading':3}
def _init_credit_rate_schema():
    c=db()
    c.execute('''CREATE TABLE IF NOT EXISTS credit_rates(
      key TEXT PRIMARY KEY,
      value INTEGER NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS credit_migrations(
      key TEXT PRIMARY KEY,
      applied_at TEXT NOT NULL
    )''')
    for k,v in CREDIT_RATE_DEFAULTS.items():
        c.execute('insert or ignore into credit_rates(key,value) values(?,?)',(k,v))
    migration_key='split_workbook_credit_rules_20260924'
    done=c.execute('select 1 from credit_migrations where key=?',(migration_key,)).fetchone()
    if not done:
        c.execute("insert into credit_rates(key,value) values('workbook',1) on conflict(key) do update set value=1")
        c.execute("insert into credit_rates(key,value) values('workbook_finish',10) on conflict(key) do update set value=10")
        c.execute("insert into credit_rates(key,value) values('reading',3) on conflict(key) do update set value=3")
        c.execute("""update riley_credits
                     set delta=1, category='workbook_checklist'
                     where child='지유'
                       and (category='workbook'
                            or category='workbook_checklist'
                            or ((category is null or category='') and reason like '문제집 완료:%'))""")
        c.execute('insert into credit_migrations(key,applied_at) values(?,?)',
                  (migration_key,datetime.now(KST).isoformat(timespec='seconds')))
    c.commit(); c.close()
_init_credit_rate_schema()

def _credit_rate(key):
    c=db(); row=c.execute('select value from credit_rates where key=?',(key,)).fetchone(); c.close()
    return row['value'] if row else CREDIT_RATE_DEFAULTS.get(key,0)

def _set_credit_rate(key,value):
    c=db()
    c.execute('insert into credit_rates(key,value) values(?,?) on conflict(key) do update set value=excluded.value',(key,value))
    c.commit(); c.close()

def _credit_total(child):
    c=db(); row=c.execute('select coalesce(sum(delta),0) t from riley_credits where child=?',(child,)).fetchone(); c.close()
    return row['t']

def _credit_period_totals(child):
    today=datetime.now(KST).date()
    week_start=today-timedelta(days=today.weekday())
    month_start=today.replace(day=1)
    c=db()
    def total_since(start_date):
        row=c.execute("select coalesce(sum(delta),0) t from riley_credits where child=? and coalesce(nullif(event_date,''),substr(created_at,1,10))>=?",(child,start_date.isoformat())).fetchone()
        return row['t']
    result={'today':total_since(today),'week':total_since(week_start),'month':total_since(month_start)}
    c.close()
    return result

WORKBOOK_SUBJECTS=('수학','국어','영어','사회','과학','한자','논술','사고력','기타')

def _workbook_rows(child):
    c=db(); rows=[dict(x) for x in c.execute('select * from riley_workbooks where child=? order by done asc,id desc',(child,)).fetchall()]; c.close()
    return rows

def _day_checkboxes():
    boxes='<label class="day-check"><input type="checkbox" onchange="toggleAllDays(this)"> 매일</label>'
    boxes+=''.join(f'<label class="day-check"><input type="checkbox" name="days" value="{d}"> {d}</label>' for d in DAYS)
    return boxes

def wb_edit_modal(base='/riley'):
    return f'''<div class="modal" id="wbe"><div class="card"><div class="head"><h2>문제집 수정</h2><button class="btn s" onclick="x('wbe')">닫기</button></div><form class="form" id="wbef" method="post" data-base="{H(base)}"><label class="full">문제집/과제<input name="title" id="wbe-title" required></label><label class="full">요일 (여러 개 선택 가능)<div class="day-checks" id="wbe-days">{_day_checkboxes()}</div></label><label>메모<input name="notes" id="wbe-notes"></label><label>색상<input type="color" name="color" id="wbe-color" value="#0f4c81"></label><div class="full" style="display:flex;gap:8px"><button class="btn">저장</button><button type="button" class="btn d" onclick="deleteWb()">삭제</button></div></form></div></div>'''

def _wb_attrs(r, group_days, base):
    days=','.join(d for d in DAYS if d in group_days.get(r['group_id'], set()))
    return f'data-id="{r["id"]}" data-gid="{H(r["group_id"])}" data-title="{H(r["title"])}" data-notes="{H(r["notes"] or "")}" data-days="{H(days)}" data-color="{H(r["color"] or "")}" data-base="{H(base)}"'

def _wb_item(r, occurrence_date, is_done, group_days, base):
    cls=' task-done' if is_done else ''
    done_cls=' done' if is_done else ''
    meta=f'<div class="feature-meta">{H(r["notes"])}</div>' if r['notes'] else ''
    style=f'border-left:4px solid {H(r["color"])}' if r['color'] else ''
    attrs=_wb_attrs(r,group_days,base)
    action=f'{base}/workbook/{r["id"]}/toggle'
    if occurrence_date is not None:
        action+=f'/{occurrence_date.isoformat()}'
        attrs+=f' data-date="{occurrence_date.isoformat()}"'
    status=f'<span class="wb-checkmark">{"✓ 완료" if is_done else ""}</span>'
    inline=(
        "if(typeof wbEditMode!=='undefined'&&wbEditMode){if(typeof editWb==='function')editWb(this);return false;}"
        "if(this.dataset.busy==='1')return false;"
        "var el=this,t=el.querySelector('b'),was=t&&t.classList.contains('task-done');"
        "el.dataset.busy='1';el.disabled=true;var op=el.style.opacity;el.style.opacity='.58';"
        "fetch(el.dataset.action,{method:'POST',credentials:'same-origin',headers:{'X-Requested-With':'fetch'}})"
        ".then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);var now=!was;"
        "if(t)t.classList.toggle('task-done',now);el.classList.toggle('done',now);"
        "var m=el.querySelector('.wb-checkmark');if(m)m.textContent=now?'✓ 완료':'';"
        "var card=el.closest('.feature-card'),h=card&&card.querySelector('.toolbar h2');"
        "if(h){var z=h.textContent.match(/이번 주 미완료\\s+(\\d+)건/);"
        "if(z){var n=Math.max(0,parseInt(z[1],10)+(was?1:-1));"
        "h.textContent=h.textContent.replace(/이번 주 미완료\\s+\\d+건/,'이번 주 미완료 '+n+'건');}}"
        "}).catch(function(e){console.error(e);alert('완료 처리에 실패했어요.');})"
        ".finally(function(){delete el.dataset.busy;el.disabled=false;el.style.opacity=op;});return false;"
    )
    return (f'<button type="button" class="lesson-toggle{done_cls}" style="{style}" {attrs} '
            f'data-action="{H(action)}" onclick="{H(inline)}">'
            f'<b class="{cls}">{H(r["title"])}</b>{meta}{status}</button>')

def _workbook_section(child='지유', base='/riley', mon=None):
    today=datetime.now(KST).date()
    if mon is None:
        mon=today-timedelta(days=today.weekday())
    sun=mon+timedelta(days=6)
    prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
    rows=_workbook_rows(child)
    dated=[r for r in rows if (r['day_of_week'] or '').strip() in DAYS]
    undated=[r for r in rows if (r['day_of_week'] or '').strip() not in DAYS]
    completions=_wb_completions_for_week([r['id'] for r in dated], mon, sun)
    by_day={d:[] for d in DAYS}
    group_days={}
    for r in rows:
        d=(r['day_of_week'] or '').strip()
        if d in by_day: by_day[d].append(r)
        group_days.setdefault(r['group_id'], set()).add(d)
    open_n=sum(1 for r in dated if (r['id'],(mon+timedelta(days=DAYS.index(r['day_of_week']))).isoformat()) not in completions)
    open_n+=sum(1 for r in undated if not r['done'])
    head=(f'<div class="riley-toolbar"><div><a class="btn s" href="{base}?date={prev}">← 이전 주</a> '
          f'<a class="btn s" href="{base}?date={today.isoformat()}">이번 주</a> '
          f'<a class="btn s" href="{base}?date={nxt}">다음 주 →</a></div>'
          f'<b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div>')
    body=(f'<section class="feature-card" style="margin-top:14px">'
          f'<div class="toolbar" style="margin:0 0 4px"><h2 style="margin:0">{H(child)} 문제집 체크리스트 · 이번 주 미완료 {open_n}건</h2>'
          '<div style="display:flex;gap:6px;flex-wrap:wrap">'
          + (f'<a class="btn s" href="{base}/workbook-db">문제집 DB</a>' if base=='/riley' else '') +
          '<button type="button" class="btn s" onclick="let f=document.getElementById(\'wb-add\');f.style.display=f.style.display===\'none\'?\'grid\':\'none\'">+ 추가</button>'
          '<button type="button" class="btn s" onclick="wbToggleEditMode(this)">수정</button>'
          '</div></div>'
          f'<form method="post" action="{base}/workbook/add" class="task-form" id="wb-add" style="display:none">'
          f'<input type="hidden" name="child" value="{H(child)}">'
          '<label class="task-title">문제집/과제<input name="title" required placeholder="예: 디딤돌 수학 3단원"></label>'
          f'<label class="full">요일 (여러 개 선택 가능)<div class="day-checks">{_day_checkboxes()}</div></label>'
          '<label>메모<input name="notes" placeholder="분량 등"></label>'
          '<label>색상<input type="color" name="color" value="#0f4c81"></label>'
          '<button class="btn">추가</button></form>'
          +head+
          '<div class="riley-week" style="margin-top:10px">')
    for i,dn in enumerate(DAYS):
        d=mon+timedelta(days=i)
        body+=f'<div class="rday {"today" if d==today else ""}"><div class="rdate">{d.strftime("%m/%d")}</div><h3>{dn}요일</h3>'
        if not by_day[dn]: body+='<div class="muted">없음</div>'
        for r in by_day[dn]:
            is_done=(r['id'],d.isoformat()) in completions
            body+=_wb_item(r,d,is_done,group_days,base)
        body+='</div>'
    body+='</div>'
    if undated:
        body+='<div class="needs-check"><h3>요일 미정</h3>'
        for r in undated:
            body+=_wb_item(r,None,bool(r['done']),group_days,base)
        body+='</div>'
    body+='</section>'
    return body

KID_SLUGS={'riley':'지유','hyeon':'혜온'}

@app.route('/riley/workbook/add',methods=['POST'])
@app.route('/hyeon/workbook/add',methods=['POST'])
def riley_workbook_add():
    title=(request.form.get('title') or '').strip()
    if title:
        child=(request.form.get('child') or '지유').strip()
        notes=(request.form.get('notes') or '').strip()
        color=(request.form.get('color') or '').strip()
        days=[d for d in request.form.getlist('days') if d in DAYS]
        gid=secrets.token_hex(8)
        c=db()
        if days:
            for d in days:
                c.execute('insert into riley_workbooks(title,notes,day_of_week,done,created_at,group_id,color,child) values(?,?,?,0,?,?,?,?)',(title,notes,d,datetime.now().isoformat(timespec='seconds'),gid,color,child))
        else:
            c.execute('insert into riley_workbooks(title,notes,day_of_week,done,created_at,group_id,color,child) values(?,?,?,0,?,?,?,?)',(title,notes,'',datetime.now().isoformat(timespec='seconds'),gid,color,child))
        c.commit(); c.close()
    return redirect(request.referrer or '/riley')

@app.route('/riley/workbook/<int:wid>/toggle',methods=['POST'])
@app.route('/hyeon/workbook/<int:wid>/toggle',methods=['POST'])
def riley_workbook_toggle(wid):
    # 요일 미정(one-off, undated) items only — dated recurring items use the
    # /toggle/<date> route below so each week's occurrence is tracked separately.
    c=db()
    row=c.execute('select id,title,child,credited,done from riley_workbooks where id=?',(wid,)).fetchone()
    if row:
        child=row['child'] or '지유'
        credited=row['credited']
        new_done=0 if row['done'] else 1
        if new_done and not credited:
            _award_credit(child,_credit_rate('workbook'),f'체크리스트 완료: {row["title"]}',datetime.now(KST).date().isoformat(),'workbook_checklist')
            credited=1
        c.execute('update riley_workbooks set done=?,credited=? where id=?',(new_done,credited,wid))
        c.commit()
    c.close()
    return redirect(request.referrer or '/riley')

@app.route('/riley/workbook/<int:wid>/toggle/<date>',methods=['POST'])
@app.route('/hyeon/workbook/<int:wid>/toggle/<date>',methods=['POST'])
def riley_workbook_toggle_dated(wid,date):
    if not qdate(date):
        return redirect(request.referrer or '/riley')
    c=db()
    row=c.execute('select id,title,child from riley_workbooks where id=?',(wid,)).fetchone()
    if row:
        existing=c.execute('select id from workbook_completions where item_id=? and date=?',(wid,date)).fetchone()
        if existing:
            c.execute('delete from workbook_completions where id=?',(existing['id'],))
            c.commit()
        else:
            c.execute('insert into workbook_completions(item_id,date,created_at) values(?,?,?)',(wid,date,datetime.now(KST).isoformat(timespec='seconds')))
            c.commit()
            already_credited=c.execute('select 1 from workbook_credited where item_id=? and date=?',(wid,date)).fetchone()
            if not already_credited:
                child=row['child'] or '지유'
                _award_credit(child,_credit_rate('workbook'),f'체크리스트 완료: {row["title"]} ({date})',date,'workbook_checklist')
                c.execute('insert or ignore into workbook_credited(item_id,date) values(?,?)',(wid,date))
                c.commit()
    c.close()
    return redirect(request.referrer or '/riley')

@app.route('/riley/workbook/group/<gid>/edit',methods=['POST'])
@app.route('/hyeon/workbook/group/<gid>/edit',methods=['POST'])
def riley_workbook_group_edit(gid):
    title=(request.form.get('title') or '').strip()
    if title:
        c=db()
        existing_rows=c.execute('select id,day_of_week,child from riley_workbooks where group_id=?',(gid,)).fetchall()
        child=existing_rows[0]['child'] if existing_rows else '지유'
        existing_by_day={(r['day_of_week'] or ''):r['id'] for r in existing_rows}
        notes=(request.form.get('notes') or '').strip()
        color=(request.form.get('color') or '').strip()
        days=[d for d in request.form.getlist('days') if d in DAYS]
        target_days=days if days else ['']
        for day,rid in existing_by_day.items():
            if day not in target_days:
                c.execute('delete from riley_workbooks where id=?',(rid,))
        for d in target_days:
            if d in existing_by_day:
                c.execute('update riley_workbooks set title=?,notes=?,color=? where id=?',(title,notes,color,existing_by_day[d]))
            else:
                c.execute('insert into riley_workbooks(title,notes,day_of_week,done,created_at,group_id,color,child) values(?,?,?,0,?,?,?,?)',(title,notes,d,datetime.now().isoformat(timespec='seconds'),gid,color,child))
        c.commit(); c.close()
    return redirect(request.referrer or '/riley')

@app.route('/riley/workbook/group/<gid>/delete',methods=['POST'])
@app.route('/hyeon/workbook/group/<gid>/delete',methods=['POST'])
def riley_workbook_group_delete(gid):
    c=db(); c.execute('delete from riley_workbooks where group_id=?',(gid,)); c.commit(); c.close()
    return redirect(request.referrer or '/riley')


def _init_riley_workbook_catalog():
    c=db()
    c.execute('''CREATE TABLE IF NOT EXISTS riley_workbook_catalog(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      child TEXT NOT NULL DEFAULT '지유',
      subject TEXT NOT NULL,
      title TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT '진행중',
      started_at TEXT,
      completed_at TEXT,
      notes TEXT,
      source TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )''')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_riley_workbook_catalog_child_title ON riley_workbook_catalog(child,title)')
    catalog_cols={r['name'] for r in c.execute('PRAGMA table_info(riley_workbook_catalog)')}
    if 'finish_credit_awarded' not in catalog_cols:
        c.execute('ALTER TABLE riley_workbook_catalog ADD COLUMN finish_credit_awarded INTEGER NOT NULL DEFAULT 0')
    now=datetime.now(KST).isoformat(timespec='seconds')
    seed=[
      ('수학','쎈연산 8권 (초등 4-2)','진행중','','','집에서 진행 중','2026-09-12'),
      ('수학','디딤돌 초등수학 응용 4-2','진행중','','','깊은수학에서 복습 중','2026-09-12'),
      ('수학','개념+유형 라이트 개념책 초등수학 5-1','진행중','','','학원 수업에서 약수와 배수 진행','2026-09-08'),
      ('수학','개념+유형 파워 개념책 초등수학 4-1','사용이력','','','5월 학습보고서 사용 이력','2026-05'),
      ('수학','개념+유형 라이트 개념책 초등수학 4-2','사용이력','','','6~8월 학습보고서 사용 이력','2026-08'),
      ('수학','최상위수학S 초등수학 3-1','사용이력','','','학습보고서 사용 이력','2026-08'),
      ('수학','디딤돌 응용 초등수학 4-1','사용이력','','','학습보고서 사용 이력','2026-08'),
      ('국어','빠작 초3','완료','','2026-09-12','완료 확인','2026-09-12'),
      ('국어','빠작 비문학 독해 3단계','완료','','2026-09-12','완료 확인','2026-09-12'),
      ('국어','초등문해력 한 문장 정리의 힘 기본편 2','사용이력','','','사용 교재로 확인','2026-09-12'),
      ('국어','기초등 국어 맞춤법','사용이력','','','사용 교재로 확인','2026-09-12'),
      ('국어','하루 10분 초등신문','사용이력','','','사용 교재로 확인','2026-09-12'),
      ('국어','놀라운 어휘 학습도감 1','사용이력','','','사용 교재로 확인','2026-09-12'),
      ('국어','초등 신문읽기 환경·국제','사용이력','','','사용 교재로 확인','2026-09-12'),
      ('국어','요약독해의 힘 1','사용이력','','','길벗스쿨 · 사용 교재로 확인','2026-09-12'),
      ('국어','독해력 비타민 3단계','사용이력','','','사용 교재로 확인','2026-09-12'),
      ('사회','사회 용어 독해 100','사용이력','','','사용 교재로 확인','2026-09-12'),
      ('한자','급수한자 7급','진행중','','','현재 진행 중','2026-09-12'),
      ('논술','딥독융합논술 A단계','진행중','','','보물섬 수업 진행 중','2026-09-12'),
      ('영어','Multiple Reading Skills D','진행중','','','현재 진행 중','2026-09-12'),
      ('영어','American School Textbook Vocabulary Key Grade 2','진행중','','','현재 진행 중','2026-09-12'),
      ('영어','Grammar Stage Plus 1','진행중','','','진행 교재로 확인','2026-06-29'),
      ('영어','4000 Essential English Words 2','완료','','2026-09-12','완료 확인','2026-09-12'),
      ('영어','Wordly Wise 4','사용이력','','','사용/보유 교재로 확인','2026-06-29'),
      ('영어','Writing Framework for Paragraph 1','사용이력','','','사용/보유 교재로 확인','2026-06-29'),
      ('영어','Write Right to Essay','사용이력','','','사용/보유 교재로 확인','2026-06-29'),
      ('사고력','플레이팩토 1단계','진행중','','','교구 학습 병행','2026-08-30'),
      ('사고력','밤비노루크 기초 단계','진행중','','','집에서 병행','2026-09-01')
    ]
    for subject,title,status,started,completed,notes,source in seed:
        c.execute('''INSERT OR IGNORE INTO riley_workbook_catalog
          (child,subject,title,status,started_at,completed_at,notes,source,created_at,updated_at)
          VALUES('지유',?,?,?,?,?,?,?,?,?)''',
          (subject,title,status,started,completed,notes,source,now,now))
    migration_key='hanja_book_finish_credit_20260924'
    migrated=c.execute('select 1 from credit_migrations where key=?',(migration_key,)).fetchone()
    if not migrated:
        today_iso=datetime.now(KST).date().isoformat()
        hanja=c.execute("select id,title,status,finish_credit_awarded from riley_workbook_catalog where child='지유' and subject='한자' and title like '%7급%' order by id desc limit 1").fetchone()
        if hanja:
            c.execute("update riley_workbook_catalog set status='완료',completed_at=?,updated_at=?,finish_credit_awarded=1 where id=?",(today_iso,now,hanja['id']))
            if not hanja['finish_credit_awarded']:
                exists=c.execute("select 1 from riley_credits where child='지유' and category='workbook_finish' and reason=? limit 1",(f'문제집 1권 완료: {hanja["title"]}',)).fetchone()
                if not exists:
                    c.execute('insert into riley_credits(child,delta,reason,created_at,event_date,category) values(?,?,?,?,?,?)',
                              ('지유',10,f'문제집 1권 완료: {hanja["title"]}',now,today_iso,'workbook_finish'))
        c.execute('insert into credit_migrations(key,applied_at) values(?,?)',(migration_key,now))
    c.commit(); c.close()
_init_riley_workbook_catalog()

def _catalog_subject_options(selected=''):
    return ''.join(f'<option value="{H(s)}"{" selected" if s==selected else ""}>{H(s)}</option>' for s in WORKBOOK_SUBJECTS)

def _catalog_status_options(selected='진행중'):
    opts=(('진행중','진행 중'),('완료','완료'),('사용이력','과거 사용'))
    return ''.join(f'<option value="{v}"{" selected" if v==selected else ""}>{label}</option>' for v,label in opts)

@app.route('/riley/workbook-db')
def riley_workbook_db():
    c=db(); rows=[dict(x) for x in c.execute("select * from riley_workbook_catalog where child='지유' order by case status when '진행중' then 0 when '완료' then 1 else 2 end, subject,title").fetchall()]; c.close()
    subjects=[s for s in WORKBOOK_SUBJECTS if any(r['subject']==s for r in rows)]
    body=(f'<div class="toolbar"><a class="btn s" href="/riley">← 지유 포탈</a>'
          f'<button class="btn" type="button" onclick="catalogAddToggle()">+ 교재 추가</button></div>'
          f'<section class="feature-card"><div class="toolbar"><div><h2 style="margin:0">📚 지유 문제집 DB</h2>'
          f'<div class="feature-meta">체크리스트와 별개 · 진행 중 / 완료 / 과거 사용 이력</div></div></div>'
          f'<form id="catalog-add" method="post" action="/riley/workbook-db/add" class="task-form" style="display:none;margin:10px 0 14px">'
          f'<label class="task-title">교재명<input name="title" required></label>'
          f'<label>과목<select name="subject">{_catalog_subject_options()}</select></label>'
          f'<label>상태<select name="status">{_catalog_status_options()}</select></label>'
          f'<label>시작일<input type="date" name="started_at"></label><label>완료일<input type="date" name="completed_at"></label>'
          f'<label class="full">메모<input name="notes"></label><button class="btn">추가</button></form>'
          f'<div class="catalog-tabs"><button class="catalog-tab on" type="button" data-status="진행중" onclick="catalogFilter(this)">진행 중</button>'
          f'<button class="catalog-tab" type="button" data-status="past" onclick="catalogFilter(this)">완료·과거</button>'
          f'<button class="catalog-tab" type="button" data-status="all" onclick="catalogFilter(this)">전체</button></div>'
          f'<div class="catalog-grid">')
    if not rows:
        body+='<div class="muted">등록된 교재가 없습니다.</div>'
    for subject in subjects:
        group=[r for r in rows if r['subject']==subject]
        body+=f'<div class="catalog-subject"><h3>{H(subject)} <span>{len(group)}권</span></h3>'
        for r in group:
            badge='진행 중' if r['status']=='진행중' else ('완료' if r['status']=='완료' else '과거 사용')
            meta=' · '.join(x for x in [
                ('시작 '+r['started_at']) if r.get('started_at') else '',
                ('완료 '+r['completed_at']) if r.get('completed_at') else '',
                r.get('notes') or ''
            ] if x)
            body+=(f'<div class="catalog-row" data-status="{H(r["status"])}"><div class="catalog-main"><div><b>{H(r["title"])}</b> '
                   f'<span class="catalog-badge {H(r["status"])}">{H(badge)}</span></div>'
                   f'<div class="feature-meta">{H(meta)}</div></div>'
                   f'<details class="catalog-edit"><summary>수정</summary><form method="post" action="/riley/workbook-db/{r["id"]}/edit" class="catalog-edit-form">'
                   f'<input name="title" value="{H(r["title"])}" required><select name="subject">{_catalog_subject_options(r["subject"])}</select>'
                   f'<select name="status">{_catalog_status_options(r["status"])}</select>'
                   f'<input type="date" name="started_at" value="{H(r.get("started_at") or "")}"><input type="date" name="completed_at" value="{H(r.get("completed_at") or "")}">'
                   f'<input name="notes" value="{H(r.get("notes") or "")}"><button class="btn s">저장</button></form>'
                   f'<form method="post" action="/riley/workbook-db/{r["id"]}/delete" onsubmit="return catalogDeleteConfirm()"><button class="btn d s">삭제</button></form></details></div>')
        body+='</div>'
    body+='</div></section>'
    body+='''<style>
    .catalog-tabs{display:flex;gap:6px;margin:10px 0 14px;flex-wrap:wrap}.catalog-tab{border:1px solid #d7dfe8;background:#fff;color:#68778a;border-radius:999px;padding:7px 12px;font-weight:800;cursor:pointer}.catalog-tab.on{background:#0f4c81;color:#fff;border-color:#0f4c81}
    .catalog-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.catalog-subject{border:1px solid #e4e9f0;border-radius:13px;padding:11px;background:#fbfcfe}.catalog-subject h3{margin:0 0 8px;display:flex;justify-content:space-between}.catalog-subject h3 span{font-size:11px;color:#8793a3}.catalog-row{padding:9px 0;border-bottom:1px solid #edf1f5}.catalog-row:last-child{border-bottom:0}.catalog-badge{display:inline-block;padding:2px 7px;border-radius:999px;font-size:10px;font-weight:800}.catalog-badge.진행중{background:#e8f6ee;color:#1f7a4d}.catalog-badge.완료{background:#eef2f6;color:#5c6b80}.catalog-badge.사용이력{background:#fff3e0;color:#a56412}.catalog-edit summary{font-size:11px;color:#7a8796;cursor:pointer;margin-top:5px}.catalog-edit-form{display:grid;grid-template-columns:2fr 1fr 1fr;gap:6px;margin-top:7px}.catalog-edit-form input,.catalog-edit-form select{padding:7px;border:1px solid #d7dfe8;border-radius:8px;font:inherit;font-size:12px}
    @media(max-width:760px){.catalog-grid{grid-template-columns:1fr}.catalog-edit-form{grid-template-columns:1fr 1fr}}
    </style><script>
    function catalogAddToggle(){let x=document.getElementById("catalog-add");if(x)x.style.display=x.style.display==="none"?"grid":"none"}
    function catalogDeleteConfirm(){return confirm("삭제할까요?")}
    function catalogFilter(btn){document.querySelectorAll(".catalog-tab").forEach(x=>x.classList.remove("on"));btn.classList.add("on");let s=btn.dataset.status;document.querySelectorAll(".catalog-row").forEach(function(r){let v=r.dataset.status;let show=s==="all"||(s==="past"&&v!=="진행중")||v===s;r.style.display=show?"":"none"});document.querySelectorAll(".catalog-subject").forEach(function(g){let any=[...g.querySelectorAll(".catalog-row")].some(x=>x.style.display!=="none");g.style.display=any?"":"none"})}
    document.addEventListener("DOMContentLoaded",function(){let b=document.querySelector(".catalog-tab.on");if(b)catalogFilter(b)})
    </script>'''
    return page('지유 문제집 DB',body)

@app.route('/riley/workbook-db/add',methods=['POST'])
def riley_workbook_db_add():
    title=(request.form.get('title') or '').strip()
    subject=(request.form.get('subject') or '기타').strip()
    status=(request.form.get('status') or '진행중').strip()
    if title:
        if subject not in WORKBOOK_SUBJECTS: subject='기타'
        if status not in ('진행중','완료','사용이력'): status='진행중'
        started=(request.form.get('started_at') or '').strip()
        completed=(request.form.get('completed_at') or '').strip()
        notes=(request.form.get('notes') or '').strip()
        now=datetime.now(KST).isoformat(timespec='seconds')
        c=db(); c.execute('''insert or ignore into riley_workbook_catalog(child,subject,title,status,started_at,completed_at,notes,source,created_at,updated_at)
          values('지유',?,?,?,?,?,?,?, ?,?)''',(subject,title,status,started,completed,notes,'직접 입력',now,now)); c.commit(); c.close()
    return redirect('/riley/workbook-db')

@app.route('/riley/workbook-db/<int:rid>/edit',methods=['POST'])
def riley_workbook_db_edit(rid):
    title=(request.form.get('title') or '').strip()
    subject=(request.form.get('subject') or '기타').strip()
    status=(request.form.get('status') or '진행중').strip()
    if title:
        if subject not in WORKBOOK_SUBJECTS: subject='기타'
        if status not in ('진행중','완료','사용이력'): status='진행중'
        started=(request.form.get('started_at') or '').strip()
        completed=(request.form.get('completed_at') or '').strip()
        notes=(request.form.get('notes') or '').strip()
        c=db()
        old=c.execute("select title,status,finish_credit_awarded from riley_workbook_catalog where id=? and child='지유'",(rid,)).fetchone()
        if status=='완료' and not completed: completed=datetime.now(KST).date().isoformat()
        if status!='완료': completed='' if not completed else completed
        now=datetime.now(KST).isoformat(timespec='seconds')
        award_finish=bool(old and old['status']!='완료' and status=='완료' and not old['finish_credit_awarded'])
        c.execute('update riley_workbook_catalog set title=?,subject=?,status=?,started_at=?,completed_at=?,notes=?,updated_at=?,finish_credit_awarded=case when ? then 1 else finish_credit_awarded end where id=? and child=?',
          (title,subject,status,started,completed,notes,now,1 if award_finish else 0,rid,'지유'))
        if award_finish:
            c.execute('insert into riley_credits(child,delta,reason,created_at,event_date,category) values(?,?,?,?,?,?)',
                      ('지유',_credit_rate('workbook_finish'),f'문제집 1권 완료: {title}',now,completed or datetime.now(KST).date().isoformat(),'workbook_finish'))
        c.commit(); c.close()
    return redirect('/riley/workbook-db')

@app.route('/riley/workbook-db/<int:rid>/delete',methods=['POST'])
def riley_workbook_db_delete(rid):
    c=db(); c.execute("delete from riley_workbook_catalog where id=? and child='지유'",(rid,)); c.commit(); c.close()
    return redirect('/riley/workbook-db')

CSS+='''.reading-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}.reading-card{position:relative;background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px}.reading-stars{color:#e9b949;font-size:14px;margin-bottom:4px;letter-spacing:1px}.reading-count{position:absolute;top:6px;right:6px;background:#0f4c81;color:#fff;font-size:11px;font-weight:800;border-radius:999px;padding:2px 7px;line-height:1.3}'''
JS+='''function editReading(el){let d=el.dataset;let f=document.getElementById("rdef");let base=f.dataset.base||"/riley";f.action=base+"/reading/"+d.id+"/edit";f.dataset.id=d.id;document.getElementById("rde-title").value=d.title||"";document.getElementById("rde-lang").value=d.language||"한글";document.getElementById("rde-genre").value=d.genre||"기타";document.getElementById("rde-sr").value=d.sr_score||"";document.getElementById("rde-lexile").value=d.lexile_score||"";document.getElementById("rde-date").value=d.read_date||"";document.getElementById("rde-rating").value=d.rating||"5";document.getElementById("rde-summary").value=d.summary||"";let rw=document.getElementById("rde-readwith");if(rw)rw.value=d.read_with||"혼자";o("rde")}function deleteReading(){let f0=document.getElementById("rdef");let id=f0.dataset.id;let base=f0.dataset.base||"/riley";if(!id||!confirm("삭제할까요?"))return;let f=document.createElement("form");f.method="post";f.action=base+"/reading/"+id+"/delete";document.body.appendChild(f);f.submit()}'''
JS+='''document.addEventListener("DOMContentLoaded",function(){var editBtn=document.querySelector(".trip-actions button[onclick^=\\"et(this)\\"]");var h1=document.querySelector(".hero h1");if(editBtn&&h1){h1.style.cursor="pointer";h1.title="클릭하여 여행 이름 수정";h1.onclick=function(){et(editBtn)}}})'''

def _init_reading_schema():
    c=db()
    c.execute('''CREATE TABLE IF NOT EXISTS riley_reading(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      language TEXT,
      rating INTEGER DEFAULT 0,
      summary TEXT,
      created_at TEXT NOT NULL
    )''')
    cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
    if 'genre' not in cols:
        c.execute('ALTER TABLE riley_reading ADD COLUMN genre TEXT')
    if 'level_score' in cols:
        c.execute('ALTER TABLE riley_reading DROP COLUMN level_score')
    if 'sr_score' not in cols:
        c.execute('ALTER TABLE riley_reading ADD COLUMN sr_score TEXT')
    if 'lexile_score' not in cols:
        c.execute('ALTER TABLE riley_reading ADD COLUMN lexile_score TEXT')
    if 'read_date' not in cols:
        c.execute('ALTER TABLE riley_reading ADD COLUMN read_date TEXT')
    if 'child' not in cols:
        c.execute('ALTER TABLE riley_reading ADD COLUMN child TEXT')
    if 'read_with' not in cols:
        c.execute('ALTER TABLE riley_reading ADD COLUMN read_with TEXT')
        cols.add('read_with')
    if 'companion' in cols:
        # Another one-off script writes a same-purpose 'companion' column; fold it
        # into read_with so both paths show up in one place.
        c.execute("update riley_reading set read_with=companion where (read_with is null or read_with='') and companion is not null and companion!=''")
    c.execute("update riley_reading set child='지유' where child is null or child=''")
    c.execute('''CREATE TABLE IF NOT EXISTS reading_credited(
      reading_id INTEGER PRIMARY KEY,
      credit_id INTEGER UNIQUE
    )''')
    for r in c.execute("select id,summary,read_date from riley_reading where summary like '%읽은 날짜:%'").fetchall():
        m=re.search(r'읽은 날짜:\s*(\d{4}-\d{2}-\d{2})',r['summary'] or '')
        if not m: continue
        cleaned=re.sub(r'\s*·?\s*읽은 날짜:\s*\d{4}-\d{2}-\d{2}','',r['summary'] or '').strip()
        c.execute('update riley_reading set summary=?,read_date=? where id=?',(cleaned,r['read_date'] or m.group(1),r['id']))
    c.commit(); c.close()
_init_reading_schema()

def _backfill_credit_activity_dates():
    c=db()
    cols={r['name'] for r in c.execute('PRAGMA table_info(riley_credits)')}
    if 'event_date' not in cols:
        c.execute('ALTER TABLE riley_credits ADD COLUMN event_date TEXT')
    if 'category' not in cols:
        c.execute('ALTER TABLE riley_credits ADD COLUMN category TEXT')
    rows=c.execute("select id,child,reason,created_at,event_date,category from riley_credits where event_date is null or event_date='' or category is null or category='' order by id").fetchall()
    for r in rows:
        reason=r['reason'] or ''
        category=(r['category'] or '').strip()
        if not category:
            if reason.startswith('체크리스트 완료:') or reason.startswith('문제집 완료:'):
                category='workbook_checklist'
            elif reason.startswith('독서 기록 추가:'):
                category='reading'
            else:
                category='other'
        event_date=(r['event_date'] or '').strip()
        if not event_date and category=='workbook_checklist' and reason.endswith(')'):
            candidate=reason[-11:-1]
            if qdate(candidate):
                event_date=candidate
        if not event_date and category=='reading':
            title=reason.split('독서 기록 추가:',1)[1].strip() if '독서 기록 추가:' in reason else ''
            if title:
                rr=c.execute("select read_date from riley_reading where child=? and title=? and read_date is not null and read_date!='' order by abs(julianday(created_at)-julianday(?)) asc,id desc limit 1",(r['child'],title,r['created_at'])).fetchone()
                if rr and rr['read_date']:
                    event_date=rr['read_date']
        if not event_date:
            event_date=(r['created_at'] or '')[:10]
        c.execute('update riley_credits set event_date=?,category=? where id=?',(event_date,category,r['id']))
    c.commit(); c.close()
_backfill_credit_activity_dates()

def _ensure_reading_credit(reading_id):
    c=db()
    rr=c.execute("select id,title,child,read_date,created_at from riley_reading where id=?",(reading_id,)).fetchone()
    if not rr or (rr['child'] or '지유')!='지유':
        c.close(); return
    title=rr['title'] or ''
    event_date=(rr['read_date'] or (rr['created_at'] or '')[:10] or datetime.now(KST).date().isoformat())[:10]
    linked=c.execute('select credit_id from reading_credited where reading_id=?',(reading_id,)).fetchone()
    if linked:
        c.execute("update riley_credits set reason=?,event_date=?,category='reading' where id=?",
                  (f'독서 기록 추가: {title}',event_date,linked['credit_id']))
        c.commit(); c.close(); return
    reason=f'독서 기록 추가: {title}'
    existing=c.execute("""select rc.id
                          from riley_credits rc
                          left join reading_credited rl on rl.credit_id=rc.id
                          where rc.child='지유'
                            and (rc.category='reading' or ((rc.category is null or rc.category='') and rc.reason like '독서 기록 추가:%'))
                            and rc.reason=?
                            and coalesce(nullif(rc.event_date,''),substr(rc.created_at,1,10))=?
                            and rl.credit_id is null
                          order by rc.id
                          limit 1""",(reason,event_date)).fetchone()
    if existing:
        credit_id=existing['id']
        c.execute("update riley_credits set event_date=?,category='reading' where id=?",(event_date,credit_id))
    else:
        cur=c.execute('insert into riley_credits(child,delta,reason,created_at,event_date,category) values(?,?,?,?,?,?)',
                      ('지유',_credit_rate('reading'),reason,datetime.now(KST).isoformat(timespec='seconds'),event_date,'reading'))
        credit_id=cur.lastrowid
    c.execute('insert or replace into reading_credited(reading_id,credit_id) values(?,?)',(reading_id,credit_id))
    c.commit(); c.close()

def _reconcile_reading_credits():
    c=db()
    ids=[r['id'] for r in c.execute("select id from riley_reading where child='지유' order by id").fetchall()]
    c.close()
    for rid in ids:
        _ensure_reading_credit(rid)

_reconcile_reading_credits()

READING_LANGS=('한글','영어')
READING_GENRES=('동화','그림책','과학','역사','전래동화','만화','위인전','창작','기타')
READ_WITH_OPTIONS=('혼자','아빠','엄마','언니')

def _reading_rows(child):
    c=db(); rows=[dict(x) for x in c.execute('select * from riley_reading where child=? order by id desc',(child,)).fetchall()]; c.close(); return rows

def _stars(n):
    n=max(0,min(5,int(n or 0)))
    return '★'*n + '☆'*(5-n)

def reading_edit_modal(base='/riley'):
    lang_opts=''.join(f'<option value="{l}">{l}</option>' for l in READING_LANGS)
    genre_opts=''.join(f'<option value="{g}">{g}</option>' for g in READING_GENRES)
    star_opts=''.join(f'<option value="{i}">{"★"*i}</option>' for i in range(5,0,-1))
    read_with_field=''
    if base=='/hyeon':
        read_with_opts=''.join(f'<option value="{w}">{w}</option>' for w in READ_WITH_OPTIONS)
        read_with_field=f'<label>누구랑 읽었어요?<select name="read_with" id="rde-readwith">{read_with_opts}</select></label>'
    return f'''<div class="modal" id="rde"><div class="card"><div class="head"><h2>독서 기록 수정</h2><button class="btn s" onclick="x('rde')">닫기</button></div><form class="form" id="rdef" method="post" data-base="{H(base)}"><label class="full">책 제목<input name="title" id="rde-title" required></label><label>언어<select name="language" id="rde-lang">{lang_opts}</select></label><label>장르<select name="genre" id="rde-genre">{genre_opts}</select></label><label>별점<select name="rating" id="rde-rating">{star_opts}</select></label>{read_with_field}<label>SR 지수<input name="sr_score" id="rde-sr" placeholder="예: 3.5"></label><label>렉사일 지수<input name="lexile_score" id="rde-lexile" placeholder="예: 650L"></label><label>읽은 날짜<input type="date" name="read_date" id="rde-date"></label><label class="full">한줄 요약/소감<input name="summary" id="rde-summary"></label><div class="full" style="display:flex;gap:8px"><button class="btn">저장</button><button type="button" class="btn d" onclick="deleteReading()">삭제</button></div></form></div></div>'''

def _reading_section(child='지유', base='/riley'):
    rows=_reading_rows(child)
    lang_opts=''.join(f'<option value="{l}">{l}</option>' for l in READING_LANGS)
    genre_opts=''.join(f'<option value="{g}">{g}</option>' for g in READING_GENRES)
    star_opts=''.join(f'<option value="{i}">{"★"*i}</option>' for i in range(5,0,-1))
    show_read_with=(base=='/hyeon')
    read_with_field=''
    if show_read_with:
        read_with_opts=''.join(f'<option value="{w}">{w}</option>' for w in READ_WITH_OPTIONS)
        read_with_field=f'<label>누구랑 읽었어요?<select name="read_with">{read_with_opts}</select></label>'
    body=(f'<section class="feature-card" style="margin-top:14px">'
          f'<div class="toolbar" style="margin:0 0 4px"><h2 style="margin:0">{H(child)} 독서 DB · {len(rows)}권</h2>'
          '<button type="button" class="btn s" onclick="let f=document.getElementById(\'rd-add\');f.style.display=f.style.display===\'none\'?\'grid\':\'none\'">+ 추가</button></div>'
          f'<form method="post" action="{base}/reading/add" class="task-form" id="rd-add" style="display:none">'
          f'<input type="hidden" name="child" value="{H(child)}">'
          '<label class="task-title">책 제목<input name="title" required placeholder="예: 흥부와 놀부"></label>'
          f'<label>언어<select name="language">{lang_opts}</select></label>'
          f'<label>장르<select name="genre">{genre_opts}</select></label>'
          f'<label>별점<select name="rating">{star_opts}</select></label>'
          f'{read_with_field}'
          '<label>SR 지수<input name="sr_score" placeholder="예: 3.5"></label>'
          '<label>렉사일 지수<input name="lexile_score" placeholder="예: 650L"></label>'
          '<label>읽은 날짜<input type="date" name="read_date"></label>'
          '<label class="full">한줄 요약/소감<input name="summary" placeholder="느낀 점 등"></label>'
          '<button class="btn">추가</button></form>'
          '<div class="reading-grid" style="margin-top:10px">')
    if not rows:
        body+='<div class="muted">등록된 책이 없습니다.</div>'
    title_counts=Counter((r['title'] or '').strip() for r in rows)
    for r in rows:
        stars=_stars(r['rating'])
        summary=f'<div class="feature-meta">{H(r["summary"])}</div>' if r['summary'] else ''
        level=' · '.join(v for v in [f'SR {r["sr_score"]}' if r['sr_score'] else '', f'Lexile {r["lexile_score"]}' if r['lexile_score'] else ''] if v)
        read_with_text=f'👥 {r["read_with"]}' if show_read_with and r['read_with'] else ''
        meta=' · '.join(v for v in [r['language'],r['genre'],level,r['read_date'],read_with_text] if v) or '-'
        dat=f'data-id="{r["id"]}" data-title="{H(r["title"])}" data-language="{H(r["language"] or "")}" data-genre="{H(r["genre"] or "")}" data-sr_score="{H(r["sr_score"] or "")}" data-lexile_score="{H(r["lexile_score"] or "")}" data-read_date="{H(r["read_date"] or "")}" data-rating="{r["rating"] or 0}" data-summary="{H(r["summary"] or "")}" data-read_with="{H(r["read_with"] or "")}"'
        count=title_counts.get((r['title'] or '').strip(),1)
        count_badge=f'<span class="reading-count">×{count}</span>' if count>1 else ''
        body+=(f'<div class="reading-card" style="cursor:pointer" {dat} onclick="editReading(this)">'
               f'{count_badge}<div class="reading-stars">{stars}</div><b>{H(r["title"])}</b>'
               f'<div class="muted">{H(meta)}</div>{summary}</div>')
    body+='</div></section>'
    return body

@app.route('/riley/reading/add',methods=['POST'])
@app.route('/hyeon/reading/add',methods=['POST'])
def riley_reading_add():
    title=(request.form.get('title') or '').strip()
    if title:
        child=(request.form.get('child') or '지유').strip()
        language=(request.form.get('language') or '').strip()
        genre=(request.form.get('genre') or '').strip()
        sr_score=(request.form.get('sr_score') or '').strip()
        lexile_score=(request.form.get('lexile_score') or '').strip()
        read_date=(request.form.get('read_date') or '').strip()
        read_with=(request.form.get('read_with') or '').strip()
        if read_with not in READ_WITH_OPTIONS: read_with=''
        try: rating=int(request.form.get('rating') or 0)
        except ValueError: rating=0
        rating=max(0,min(5,rating))
        summary=(request.form.get('summary') or '').strip()
        c=db()
        cur=c.execute('insert into riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,read_with) values(?,?,?,?,?,?,?,?,?,?,?)',(title,language,genre,sr_score,lexile_score,read_date,rating,summary,datetime.now().isoformat(timespec='seconds'),child,read_with))
        reading_id=cur.lastrowid
        c.commit(); c.close()
        if child=='지유':
            _ensure_reading_credit(reading_id)
    return redirect(request.referrer or '/riley')

@app.route('/riley/reading/<int:i>/edit',methods=['POST'])
@app.route('/hyeon/reading/<int:i>/edit',methods=['POST'])
def riley_reading_edit(i):
    title=(request.form.get('title') or '').strip()
    if title:
        language=(request.form.get('language') or '').strip()
        genre=(request.form.get('genre') or '').strip()
        sr_score=(request.form.get('sr_score') or '').strip()
        lexile_score=(request.form.get('lexile_score') or '').strip()
        read_date=(request.form.get('read_date') or '').strip()
        read_with=(request.form.get('read_with') or '').strip()
        if read_with not in READ_WITH_OPTIONS: read_with=''
        try: rating=int(request.form.get('rating') or 0)
        except ValueError: rating=0
        rating=max(0,min(5,rating))
        summary=(request.form.get('summary') or '').strip()
        c=db()
        old=c.execute('select child from riley_reading where id=?',(i,)).fetchone()
        c.execute('update riley_reading set title=?,language=?,genre=?,sr_score=?,lexile_score=?,read_date=?,rating=?,summary=?,read_with=? where id=?',(title,language,genre,sr_score,lexile_score,read_date,rating,summary,read_with,i))
        c.commit(); c.close()
        if old and (old['child'] or '지유')=='지유':
            _ensure_reading_credit(i)
    return redirect(request.referrer or '/riley')
@app.route('/riley/reading/<int:i>/delete',methods=['POST'])
@app.route('/hyeon/reading/<int:i>/delete',methods=['POST'])
def riley_reading_delete(i):
    c=db()
    link=c.execute('select credit_id from reading_credited where reading_id=?',(i,)).fetchone()
    if link:
        c.execute('delete from riley_credits where id=?',(link['credit_id'],))
        c.execute('delete from reading_credited where reading_id=?',(i,))
    c.execute('delete from riley_reading where id=?',(i,))
    c.commit(); c.close()
    return redirect(request.referrer or '/riley')

def _kid_portal(slug,child,academy_workbook=True):
    base=f'/{slug}'
    body=''
    if slug=='riley':
        pt=_credit_period_totals(child)
        body+=(f'<a href="/riley/credits" style="display:block;text-align:center;font-size:13px;font-weight:800;color:#748196;'
               f'background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:8px;margin-bottom:14px;text-decoration:none;cursor:pointer">'
               f'🪙 {H(child)} 크레딧 · 오늘 +{pt["today"]} · 이번 주 +{pt["week"]} · 이번 달 +{pt["month"]} · 총 {_credit_total(child)}개'
               f'<div style="font-weight:600;font-size:11px;color:#9aa5b1;margin-top:2px">눌러서 자세히 보기</div></a>')
    if academy_workbook:
        today=datetime.now(KST).date()
        q=qdate(request.args.get('date','')) or today
        mon=q-timedelta(days=q.weekday()); sun=mon+timedelta(days=6)
        ge=_timed_google(mon,sun,child)
        by={mon+timedelta(days=i):[] for i in range(7)}
        for x in ge:
            x=dict(x); x['source']='google'; by[x['date']].append(x)
        c=db(); local=c.execute('select * from academy where active=1 and child=? order by start_time,id',(child,)).fetchall(); c.close()
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
                by[d].append({'date':d,'start':st,'end':r['end_time'] or '','title':r['academy'] or '일정','location':r['location'] or '', 'subject':r['subject'] or '', 'notes':r['notes'] or '', 'source':'local','local_id':r['id'], 'day_of_week':dayname, 'color':r['color'] or ''})
        for d in by: by[d].sort(key=lambda x:(x.get('start') or '99:99',x.get('title','')))
        prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
        head=f'<div class="riley-toolbar"><div><a class="btn s" href="{base}?date={prev}">← 이전 주</a> <a class="btn s" href="{base}?date={today.isoformat()}">이번 주</a> <a class="btn s" href="{base}?date={nxt}">다음 주 →</a></div><b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div>'
        body+=head+'<div class="riley-week">'
        for i in range(7):
            d=mon+timedelta(days=i); body+=f'<div class="rday {"today" if d==today else ""}"><div class="rdate">{d.strftime("%m/%d")}</div><h3>{DAYS[i]}</h3>'
            if not by[d]: body+='<div class="muted">일정 없음</div>'
            for x in by[d]:
                src=x.get('source'); tm=x.get('start') or '시간 미정'; tm += ('–'+x.get('end')) if x.get('end') else ''
                cls='rlesson' if src=='google' else 'rlesson local'
                if src=='local':
                    rid=x['local_id']; color=x.get('color') or ''
                    dat=f'data-id="{rid}" data-day_of_week="{H(x.get("day_of_week"))}" data-start_time="{H(x.get("start"))}" data-end_time="{H(x.get("end"))}" data-academy="{H(x.get("title"))}" data-subject="{H(x.get("subject"))}" data-location="{H(x.get("location"))}" data-notes="{H(x.get("notes"))}" data-color="{H(color)}"'
                    style=f' style="cursor:pointer;border-left-color:{H(color)}"' if color else ' style="cursor:pointer"'
                    body+=f'<div class="{cls}"{style} {dat} onclick="ea(this)">'
                else:
                    body+=f'<div class="{cls}">'
                body+=f'<b>{H(x.get("title"))}</b><div>{H(tm)}</div>'
                meta=' · '.join(v for v in [x.get('subject',''),x.get('location',''),x.get('notes','')] if v)
                if meta: body+=f'<div class="rmeta">{H(meta)}</div>'
                body+='</div>'
            body+=f'<button class="btn s" onclick="na(\'{DAYS[i]}\')">+ 일정</button></div>'
        body+='</div>'
        if unknown:
            body+='<div class="needs-check"><h3>요일/시간 확인 필요</h3>'
            for r in unknown:
                color=r['color'] or ''
                dat=f'data-id="{r["id"]}" data-day_of_week="{H(r["day_of_week"])}" data-start_time="{H(r["start_time"])}" data-end_time="{H(r["end_time"])}" data-academy="{H(r["academy"])}" data-subject="{H(r["subject"])}" data-location="{H(r["location"])}" data-notes="{H(r["notes"])}" data-color="{H(color)}"'
                style=f' style="cursor:pointer;border-left-color:{H(color)}"' if color else ' style="cursor:pointer"'
                body+=f'<div class="needs-item"{style} {dat} onclick="ea(this)"><div><b>{H(r["academy"])}</b><div class="muted">요일 또는 시간이 미정이라 주간표 밖에 표시</div></div></div>'
            body+='</div>'
        body+=f'<p class="muted" style="margin-top:10px">주황색은 {H(child)} Google Calendar, 회색은 기존 학원 DB 보완 일정입니다. 같은 시간·같은 일정은 중복 표시하지 않습니다.</p>'
        body+=_workbook_section(child,base,mon)
    if slug=='hyeon':
        body+='<div style="margin-bottom:14px;display:flex;gap:8px"><a class="btn" href="/hyeon/hangul">🔤 한글 공부</a><a class="btn" href="/hyeon/coloring">🎨 색칠 공부</a></div>'
    body+=_reading_section(child,base)+reading_edit_modal(base)
    if academy_workbook:
        body+=academy_modal(child)+wb_edit_modal(base)
    return page(f'{child} 포탈',body)

def riley_week():
    return _kid_portal('riley','지유')

def hyeon_week():
    return _kid_portal('hyeon','혜온',academy_workbook=False)

@app.route('/riley/credits/rate',methods=['POST'])
def riley_credits_rate_update():
    for key in ('workbook','workbook_finish','reading'):
        try:
            value=int(request.form.get(key,''))
        except (TypeError,ValueError):
            continue
        value=max(0,min(100,value))
        _set_credit_rate(key,value)
    return redirect('/riley/credits')

@app.route('/riley/credits')
def riley_credits_detail():
    child='지유'
    checklist_rate=_credit_rate('workbook')
    finish_rate=_credit_rate('workbook_finish')
    reading_rate=_credit_rate('reading')
    c=db()
    rows=[dict(x) for x in c.execute("select * from riley_credits where child=? order by coalesce(nullif(event_date,''),substr(created_at,1,10)) desc,created_at desc",(child,)).fetchall()]
    c.close()

    kinds=('workbook_checklist','workbook_finish','reading')
    maps={k:{'day':{},'week':{},'month':{}} for k in kinds}
    by_day={}
    for r in rows:
        ds=(r.get('event_date') or (r.get('created_at') or '')[:10])[:10]
        d=qdate(ds)
        if not d: continue
        category=(r.get('category') or '').strip()
        reason=r.get('reason') or ''
        if category=='workbook': category='workbook_checklist'
        if category not in maps:
            if reason.startswith('문제집 1권 완료:'): category='workbook_finish'
            elif reason.startswith('체크리스트 완료:') or reason.startswith('문제집 완료:'): category='workbook_checklist'
            elif reason.startswith('독서 기록 추가:'): category='reading'
            else: continue
        delta=int(r.get('delta') or 0)
        week=(d-timedelta(days=d.weekday())).isoformat()
        month=d.strftime('%Y-%m')
        maps[category]['day'][ds]=maps[category]['day'].get(ds,0)+delta
        maps[category]['week'][week]=maps[category]['week'].get(week,0)+delta
        maps[category]['month'][month]=maps[category]['month'].get(month,0)+delta
        by_day.setdefault(ds,{'total':0,'items':[]})
        by_day[ds]['total']+=delta
        x=dict(r); x['category']=category; x['event_date']=ds
        by_day[ds]['items'].append(x)

    today=datetime.now(KST).date()
    def shift_month(d,offset):
        idx=d.year*12+(d.month-1)+offset
        return date(idx//12,idx%12+1,1)

    def stacked_series(view):
        ck=maps['workbook_checklist'][view]; wf=maps['workbook_finish'][view]; rd=maps['reading'][view]
        keys=set(ck)|set(wf)|set(rd)
        if view=='day':
            earliest=min([qdate(k) for k in keys if qdate(k)] or [today-timedelta(days=6)])
            earliest=min(earliest,today-timedelta(days=6))
            out=[]; d=earliest
            while d<=today:
                key=d.isoformat()
                out.append((d.strftime('%m/%d'),ck.get(key,0),wf.get(key,0),rd.get(key,0)))
                d+=timedelta(days=1)
            return out
        if view=='week':
            week0=today-timedelta(days=today.weekday())
            valid=[qdate(k) for k in keys if qdate(k)]
            earliest=min(valid or [week0-timedelta(days=42)])
            earliest=earliest-timedelta(days=earliest.weekday())
            earliest=min(earliest,week0-timedelta(days=42))
            out=[]; d=earliest
            while d<=week0:
                key=d.isoformat()
                out.append((d.strftime('%m/%d'),ck.get(key,0),wf.get(key,0),rd.get(key,0)))
                d+=timedelta(days=7)
            return out
        month0=today.replace(day=1)
        parsed=[]
        for k in keys:
            try: parsed.append(datetime.strptime(k+'-01','%Y-%m-%d').date())
            except Exception: pass
        earliest=min(parsed or [shift_month(month0,-6)])
        earliest=min(earliest,shift_month(month0,-6))
        out=[]; d=earliest
        while d<=month0:
            key=d.strftime('%Y-%m')
            out.append((d.strftime('%y.%m'),ck.get(key,0),wf.get(key,0),rd.get(key,0)))
            d=shift_month(d,1)
        return out

    def stacked_panel(view,label,items,active=False):
        latest=items[-7:] if len(items)>7 else items
        mx=max([max(0,c)+max(0,f)+max(0,r) for _,c,f,r in latest] or [1]) or 1
        bars=''
        for x,check,finish,reading in items:
            cp=max(0,check); fp=max(0,finish); rp=max(0,reading); total=cp+fp+rp
            ch=0 if cp==0 else max(2,round(cp/mx*150))
            fh=0 if fp==0 else max(2,round(fp/mx*150))
            rh=0 if rp==0 else max(2,round(rp/mx*150))
            segs=''
            if rh: segs+=f'<div class="credit-stack-fill reading" data-value="{rp}" style="height:{rh}px"></div>'
            if fh: segs+=f'<div class="credit-stack-fill workbook-finish" data-value="{fp}" style="height:{fh}px"></div>'
            if ch: segs+=f'<div class="credit-stack-fill checklist" data-value="{cp}" style="height:{ch}px"></div>'
            bars+=(f'<div class="credit-bar-col" data-total="{total}" data-check="{cp}" data-finish="{fp}" data-reading="{rp}" title="{H(x)} · 체크리스트 {check:+d} · 문제집 완독 {finish:+d} · 독서 {reading:+d} · 합계 {total:+d}">'
                   f'<div class="credit-bar-value">{total:+d}</div><div class="credit-bar-track stacked">{segs}</div><div class="credit-bar-label">{H(x)}</div></div>')
        on=' on' if active else ''
        return f'<div class="credit-chart-panel{on}" data-credit-view="{view}"><div class="credit-chart-note">{label} · 현재 보이는 7개 중 최고값이 최대 높이</div><div class="credit-bars">{bars}</div></div>'

    credit_css='''<style>
    .credit-chart-shell{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:14px;box-shadow:0 1px 3px rgba(20,38,63,.06)}
    .credit-chart-head{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:8px}.credit-chart-head h2{margin:0}
    .credit-tabs{display:flex;gap:6px;background:#eef3f8;padding:3px;border-radius:11px}.credit-tab{border:0;background:transparent;color:#6b788a;padding:7px 12px;border-radius:8px;font:inherit;font-size:12px;font-weight:800;cursor:pointer}.credit-tab.on{background:#fff;color:#0f4c81;box-shadow:0 1px 4px rgba(20,38,63,.12)}
    .credit-legend{display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:11px;color:#728096;margin:4px 0 10px}.credit-legend span{display:flex;align-items:center;gap:5px}.credit-dot{width:9px;height:9px;border-radius:3px;display:inline-block}.credit-dot.checklist{background:#4c96cf}.credit-dot.workbook-finish{background:#3f9a67}.credit-dot.reading{background:#e38a3d}
    .credit-chart-card{border:1px solid #e4e9f0;border-radius:13px;padding:12px;min-width:0}.credit-chart-panel{display:none}.credit-chart-panel.on{display:block}.credit-chart-note{font-size:11px;color:#8390a1;margin:2px 0 8px}
    .credit-bars{height:234px;display:flex;align-items:flex-end;gap:7px;overflow-x:auto;overflow-y:hidden;padding:8px 3px 8px;border-bottom:1px solid #edf1f5;scroll-behavior:smooth;-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain}.credit-bar-col{height:100%;min-width:38px;flex:0 0 calc((100% - 42px)/7);display:flex;flex-direction:column;justify-content:flex-end;align-items:center}
    .credit-bar-value{font-size:9px;font-weight:800;color:#5f6f83;margin-bottom:4px;white-space:nowrap}.credit-bar-track{height:150px;width:23px;background:#f1f4f8;border-radius:8px 8px 2px 2px;overflow:hidden}.credit-bar-track.stacked{display:flex;flex-direction:column;justify-content:flex-end}.credit-stack-fill{width:100%;flex:0 0 auto}.credit-stack-fill.checklist{background:linear-gradient(180deg,#69a9d8,#2877b5)}.credit-stack-fill.workbook-finish{background:linear-gradient(180deg,#67b987,#2f8657)}.credit-stack-fill.reading{background:linear-gradient(180deg,#e9a65a,#d87832)}.credit-bar-label{font-size:9px;color:#7c8999;margin-top:6px;white-space:nowrap}
    .credit-rule-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.credit-rule{border:1px solid #e4e9f0;border-radius:12px;padding:12px;background:#fbfcfe}.credit-rule label{display:block;color:#14263f;font-size:13px}.credit-rule-value{display:flex;align-items:center;gap:6px;margin-top:7px}.credit-rule-value span{font-size:22px;font-weight:900}.credit-rule input{width:76px;padding:7px 9px;border:1px solid #d7dfe8;border-radius:9px;font:inherit;font-size:20px;font-weight:900;text-align:center;background:#fff;color:#14263f}.credit-save-row{display:flex;justify-content:flex-end;margin-top:10px}
    .credit-kind{display:inline-block;border-radius:999px;padding:2px 7px;font-size:10px;font-weight:800;margin-right:4px}.credit-kind.workbook_checklist{background:#eaf3fb;color:#2877b5}.credit-kind.workbook_finish{background:#e9f6ee;color:#2f8657}.credit-kind.reading{background:#fff1e5;color:#b96020}
    @media(max-width:560px){.credit-chart-shell{padding:12px}.credit-tabs{width:100%}.credit-tab{flex:1}.credit-bars{gap:5px}.credit-bar-col{min-width:34px;flex-basis:calc((100% - 30px)/7)}.credit-bar-track{width:21px}.credit-rule-grid{grid-template-columns:1fr}}
    </style>'''

    credit_js='''<script>
    function creditVisibleScale(bars){
      if(!bars)return;
      var cols=[].slice.call(bars.querySelectorAll('.credit-bar-col'));
      if(!cols.length)return;
      var count=Math.min(7,cols.length);
      var step=cols.length>1?(cols[1].offsetLeft-cols[0].offsetLeft):1;
      var start=step>0?Math.round(bars.scrollLeft/step):0;
      start=Math.max(0,Math.min(start,cols.length-count));
      var visible=cols.slice(start,start+count);
      var mx=Math.max.apply(null,visible.map(function(col){return Number(col.dataset.total||0)}).concat([1]));
      cols.forEach(function(col){
        [['checklist','check'],['workbook-finish','finish'],['reading','reading']].forEach(function(pair){
          var seg=col.querySelector('.credit-stack-fill.'+pair[0]);
          if(!seg)return;
          var v=Number(col.dataset[pair[1]]||0);
          var h=v<=0?0:Math.max(2,Math.round(v/mx*150));
          seg.style.height=h+'px';
        });
      });
    }
    function creditBindScale(bars){
      if(!bars||bars.dataset.scaleBound==='1')return;
      bars.dataset.scaleBound='1';
      var ticking=false;
      bars.addEventListener('scroll',function(){
        if(ticking)return;
        ticking=true;
        requestAnimationFrame(function(){creditVisibleScale(bars);ticking=false});
      },{passive:true});
    }
    function creditScrollLatest(view){
      var panel=document.querySelector('.credit-chart-panel[data-credit-view="'+view+'"]');
      var bars=panel&&panel.querySelector('.credit-bars');
      if(!bars)return;
      creditBindScale(bars);
      bars.scrollLeft=bars.scrollWidth;
      requestAnimationFrame(function(){creditVisibleScale(bars)});
    }
    function creditView(btn,view){
      document.querySelectorAll('.credit-tab').forEach(function(x){x.classList.remove('on')});
      btn.classList.add('on');
      document.querySelectorAll('.credit-chart-panel').forEach(function(x){x.classList.toggle('on',x.dataset.creditView===view)});
      setTimeout(function(){creditScrollLatest(view)},0);
    }
    document.addEventListener('DOMContentLoaded',function(){
      document.querySelectorAll('.credit-bars').forEach(creditBindScale);
      requestAnimationFrame(function(){creditScrollLatest('day')});
    });
    window.addEventListener('resize',function(){
      var panel=document.querySelector('.credit-chart-panel.on');
      var bars=panel&&panel.querySelector('.credit-bars');
      creditVisibleScale(bars);
    });
    </script>'''

    body=(f'{credit_css}<div class="toolbar"><a class="btn s" href="/riley">← 지유 포탈</a></div>'
          f'<section class="credit-chart-shell"><div class="credit-chart-head"><div><h2>🪙 {H(child)} 크레딧 추이</h2><div class="feature-meta">체크리스트는 예정일 · 문제집 1권 완료는 완료일 · 독서는 읽은 날짜 기준</div></div>'
          f'<div class="credit-tabs"><button type="button" class="credit-tab on" data-view="day" onclick="creditView(this,this.dataset.view)">일간</button><button type="button" class="credit-tab" data-view="week" onclick="creditView(this,this.dataset.view)">주간</button><button type="button" class="credit-tab" data-view="month" onclick="creditView(this,this.dataset.view)">월간</button></div></div>'
          f'<div class="credit-legend"><span><i class="credit-dot checklist"></i>체크리스트 +{checklist_rate}</span><span><i class="credit-dot workbook-finish"></i>문제집 1권 완료 +{finish_rate}</span><span><i class="credit-dot reading"></i>독서 +{reading_rate}</span></div>'
          f'<div class="credit-chart-card">'
          +stacked_panel('day','최신 7일 표시 · 좌우 스크롤로 과거 보기',stacked_series('day'),True)
          +stacked_panel('week','최신 7주 표시 · 좌우 스크롤로 과거 보기',stacked_series('week'))
          +stacked_panel('month','최신 7개월 표시 · 좌우 스크롤로 과거 보기',stacked_series('month'))
          +f'</div></section>{credit_js}'
          f'<section class="feature-card" style="margin-top:14px"><h2 style="margin:0 0 10px">⚙️ 크레딧 기준</h2>'
          f'<form method="post" action="/riley/credits/rate">'
          f'<div class="credit-rule-grid">'
          f'<div class="credit-rule"><label>매일 문제집 체크리스트 1개</label><div class="credit-rule-value"><span>+</span><input type="number" name="workbook" min="0" max="100" step="1" value="{checklist_rate}"></div></div>'
          f'<div class="credit-rule"><label>문제집 한 권 끝내기</label><div class="credit-rule-value"><span>+</span><input type="number" name="workbook_finish" min="0" max="100" step="1" value="{finish_rate}"></div></div>'
          f'<div class="credit-rule"><label>책 한 권 읽기</label><div class="credit-rule-value"><span>+</span><input type="number" name="reading" min="0" max="100" step="1" value="{reading_rate}"></div></div>'
          f'</div><div class="credit-save-row"><button type="submit" class="btn">크레딧 기준 저장</button></div></form>'
          f'<div class="feature-meta" style="margin-top:8px">저장한 값은 이후 새로 적립되는 크레딧부터 적용 · 기존 적립 내역은 유지</div></section>'
          f'<section class="feature-card" style="margin-top:14px"><h2 style="margin:0 0 10px">기준일별 내역</h2>')
    if not by_day:
        body+='<div class="muted">아직 적립된 크레딧이 없습니다.</div>'
    labels={'workbook_checklist':'체크리스트','workbook_finish':'문제집 완독','reading':'독서'}
    for d in sorted(by_day.keys(),reverse=True):
        info=by_day[d]
        body+=(f'<div style="padding:8px 0;border-bottom:1px solid #edf1f5"><div style="display:flex;justify-content:space-between"><b>{H(d)}</b><b>{info["total"]:+d}</b></div>')
        for it in info['items']:
            kind=it['category']; kind_label=labels.get(kind,kind)
            created=(it.get('created_at') or '')[:16].replace('T',' ')
            body+=(f'<div class="feature-meta" style="margin-top:4px"><span class="credit-kind {kind}">{H(kind_label)}</span>{H(it["reason"] or "")} ({int(it["delta"]):+d}) · 기록 {H(created)}</div>')
        body+='</div>'
    body+='</section>'
    return page(f'{child} 크레딧 현황',body)

def _init_hangul_schema():
    c=db()
    c.execute('''CREATE TABLE IF NOT EXISTS hangul_words(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      emoji TEXT NOT NULL,
      word TEXT NOT NULL,
      active INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS hangul_letters(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      char TEXT NOT NULL,
      kind TEXT NOT NULL,
      sound TEXT NOT NULL,
      sort_order INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS hangul_progress(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      activity_date TEXT UNIQUE NOT NULL,
      cards_flipped INTEGER DEFAULT 0,
      quiz_correct INTEGER DEFAULT 0,
      letters_done INTEGER DEFAULT 0
    )''')
    cols={r['name'] for r in c.execute('PRAGMA table_info(hangul_progress)')}
    if 'letters_done' not in cols:
        c.execute('ALTER TABLE hangul_progress ADD COLUMN letters_done INTEGER DEFAULT 0')
    n=c.execute('select count(*) c from hangul_words').fetchone()['c']
    if n==0:
        seed=[('🍎','사과'),('🍌','바나나'),('🚗','자동차'),('🦁','사자'),('🐘','코끼리'),('☂️','우산'),
              ('🦋','나비'),('🍓','딸기'),('🐟','물고기'),('🐯','호랑이'),('🚂','기차'),('☁️','구름'),
              ('🐶','강아지'),('🐱','고양이'),('🐰','토끼'),('⭐','별')]
        for emoji,word in seed:
            c.execute('insert into hangul_words(emoji,word,active) values(?,?,1)',(emoji,word))
    consonants=[('ㄱ','그'),('ㄴ','느'),('ㄷ','드'),('ㄹ','르'),('ㅁ','므'),('ㅂ','브'),('ㅅ','스'),
                ('ㅇ','으'),('ㅈ','즈'),('ㅊ','츠'),('ㅋ','크'),('ㅌ','트'),('ㅍ','프'),('ㅎ','흐')]
    vowels=[('ㅏ','아'),('ㅑ','야'),('ㅓ','어'),('ㅕ','여'),('ㅗ','오'),('ㅛ','요'),('ㅜ','우'),
            ('ㅠ','유'),('ㅡ','으'),('ㅣ','이')]
    existing=set((r['char'],r['kind']) for r in c.execute('select char,kind from hangul_letters').fetchall())
    i=(c.execute('select coalesce(max(sort_order),-1) c from hangul_letters').fetchone()['c'])+1
    for ch,snd in consonants:
        if (ch,'자음') not in existing:
            c.execute('insert into hangul_letters(char,kind,sound,sort_order) values(?,?,?,?)',(ch,'자음',snd,i)); i+=1
    for ch,snd in vowels:
        if (ch,'모음') not in existing:
            c.execute('insert into hangul_letters(char,kind,sound,sort_order) values(?,?,?,?)',(ch,'모음',snd,i)); i+=1
    c.commit(); c.close()
_init_hangul_schema()

def _hangul_bump(field):
    today=datetime.now(KST).date().isoformat()
    c=db()
    c.execute(f'insert into hangul_progress(activity_date,{field}) values(?,1) on conflict(activity_date) do update set {field}={field}+1',(today,))
    c.commit(); c.close()

@app.route('/hyeon/hangul/log',methods=['POST'])
def hangul_log():
    kind=(request.form.get('kind') or '').strip()
    if kind=='card': _hangul_bump('cards_flipped')
    elif kind=='quiz': _hangul_bump('quiz_correct')
    elif kind=='letter': _hangul_bump('letters_done')
    return ('',204)

HANGUL_STAR_GOAL=5

@app.route('/hyeon/hangul')
def hangul_page():
    c=db(); words=[dict(x) for x in c.execute('select emoji,word from hangul_words where active=1').fetchall()]; c.close()
    c=db(); letters=[dict(x) for x in c.execute('select char,kind,sound from hangul_letters order by sort_order').fetchall()]; c.close()
    today=datetime.now(KST).date()
    mon=today-timedelta(days=today.weekday())
    c=db(); prog_rows=c.execute('select * from hangul_progress where activity_date>=? and activity_date<=?',(mon.isoformat(),(mon+timedelta(days=6)).isoformat())).fetchall(); c.close()
    prog={r['activity_date']:dict(r) for r in prog_rows}
    stickers=''
    for i in range(7):
        d=mon+timedelta(days=i)
        p=prog.get(d.isoformat())
        total=(p['cards_flipped']+p['quiz_correct']+p['letters_done']) if p else 0
        if total>=HANGUL_STAR_GOAL: cls,icon='hg-sticker-day done big','🏆'
        elif total>0: cls,icon='hg-sticker-day done','⭐'
        else: cls,icon='hg-sticker-day','·'
        today_cls=' today' if d==today else ''
        stickers+=f'<div class="{cls}{today_cls}"><div class="hg-sd-label">{DAYS[i]}</div><div class="hg-sd-icon">{icon}</div></div>'
    month_start=today.replace(day=1)
    c=db(); all_prog=c.execute('select activity_date,cards_flipped,quiz_correct,letters_done from hangul_progress').fetchall(); c.close()
    def _tier_counts(rows):
        stars=0; trophies=0
        for p in rows:
            t=p['cards_flipped']+p['quiz_correct']+p['letters_done']
            if t>=HANGUL_STAR_GOAL: trophies+=1
            elif t>0: stars+=1
        return stars,trophies
    week_rows=[p for p in all_prog if mon.isoformat()<=p['activity_date']<=(mon+timedelta(days=6)).isoformat()]
    month_rows=[p for p in all_prog if p['activity_date']>=month_start.isoformat()]
    today_rows=[p for p in all_prog if p['activity_date']==today.isoformat()]
    ts,tt=_tier_counts(today_rows); ws,wt=_tier_counts(week_rows); ms,mt=_tier_counts(month_rows); ls,lt=_tier_counts(all_prog)
    summary=(f'<a href="/hyeon/hangul/stats" class="hg-total-summary" style="display:block;text-decoration:none;cursor:pointer">오늘 ⭐{ts} 🏆{tt} · 이번 주 ⭐{ws} 🏆{wt} · 이번 달 ⭐{ms} 🏆{mt} · 총 ⭐{ls} 🏆{lt}'
               f'<div style="font-weight:600;font-size:11px;color:#9aa5b1;margin-top:2px">눌러서 자세히 보기</div></a>')
    words_json=json.dumps(words,ensure_ascii=False)
    letters_json=json.dumps(letters,ensure_ascii=False)
    body=f'''
<style>
.hg-topbar{{display:flex;gap:8px;margin-bottom:14px}}
.hg-btn{{width:56px;height:56px;border-radius:16px;border:1px solid #e4e9f0;background:#fff;font-size:26px;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.hg-btn.on{{background:#0f4c81;border-color:#0f4c81}}
.hg-sticker-board{{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:16px}}
.hg-sticker-day{{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:8px 4px;text-align:center}}
.hg-sticker-day.today{{border-color:#0f4c81;border-width:2px}}
.hg-sticker-day.big{{background:#fff8e6;border-color:#e9b949}}
.hg-sticker-day.big .hg-sd-icon{{font-size:26px}}
.hg-total-summary{{text-align:center;font-size:13px;font-weight:800;color:#748196;background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:8px;margin-bottom:10px}}
.hg-sd-label{{font-size:11px;color:#748196}}
.hg-sd-icon{{font-size:22px;margin-top:4px}}
.hg-card-grid,.hg-quiz-grid,.hg-letter-grid{{display:grid;gap:10px}}
.hg-card-grid{{grid-template-columns:repeat(auto-fill,minmax(110px,1fr))}}
.hg-card{{aspect-ratio:1;border-radius:18px;border:2px solid #e4e9f0;background:#fff;font-size:40px;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.hg-card .back{{font-size:22px;font-weight:900;color:#0f4c81}}
.hg-letter-section h3{{margin:16px 0 8px}}
.hg-letter-grid{{grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:12px}}
.hg-letter{{aspect-ratio:1;border-radius:16px;border:2px solid #e4e9f0;background:#fff;font-size:34px;font-weight:900;color:#0f4c81;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.hg-letter:active{{background:#eaf3fb}}
.hg-quiz-grid{{grid-template-columns:1fr 1fr}}
.hg-quiz-col{{display:flex;flex-direction:column;gap:10px}}
.hg-quiz-item{{min-height:64px;border-radius:14px;border:2px solid #e4e9f0;background:#fff;font-size:28px;font-weight:800;cursor:pointer}}
.hg-quiz-item.sel{{border-color:#0f4c81}}
.hg-quiz-item.matched{{background:#eafaf0;border-color:#3fa965;opacity:.55}}
.hg-quiz-item.wrong{{background:#fdeceb;border-color:#d9534f}}
.hg-combine-row{{display:grid;gap:10px;margin-bottom:14px}}
.hg-combine-row.pick{{grid-template-columns:repeat(auto-fill,minmax(64px,1fr))}}
.hg-pick{{aspect-ratio:1;border-radius:14px;border:2px solid #e4e9f0;background:#fff;font-size:26px;font-weight:900;color:#0f4c81;cursor:pointer}}
.hg-pick.sel{{background:#0f4c81;color:#fff}}
.hg-combine-eq{{text-align:center;font-size:22px;font-weight:800;color:#748196;min-height:28px}}
.hg-combine-result{{display:flex;align-items:center;justify-content:center;height:180px;background:#fff;border:2px dashed #d7dfe8;border-radius:20px;font-size:96px;font-weight:900;color:#0f4c81;margin:8px 0}}
.hg-combine-word{{display:flex;align-items:center;justify-content:center;gap:10px;font-size:26px;font-weight:800;color:#14263f;margin-bottom:14px}}
.hg-combine-word span:first-child{{font-size:44px}}
.hg-trace-toolbar{{display:flex;gap:8px;justify-content:center;margin-bottom:12px}}
.hg-trace-wrap{{position:relative;width:100%;max-width:320px;height:320px;margin:0 auto;background:#fff;border:2px solid #e4e9f0;border-radius:20px;overflow:hidden}}
.hg-trace-guide{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:220px;font-weight:900;color:#e4e9f0;user-select:none}}
.hg-trace-canvas{{position:absolute;inset:0;touch-action:none}}
@media(max-width:430px){{.hg-btn{{width:48px;height:48px;font-size:22px}}.hg-card{{font-size:32px}}.hg-combine-result{{height:130px;font-size:64px}}.hg-trace-guide{{font-size:150px}}}}
</style>
<div class="hg-topbar">
<a class="hg-btn" href="/hyeon">🏠</a>
<button type="button" class="hg-btn on" id="hg-tab-letters" onclick="hgTab('letters')">ㄱㄴ</button>
<button type="button" class="hg-btn" id="hg-tab-combine" onclick="hgTab('combine')">가+</button>
<button type="button" class="hg-btn" id="hg-tab-trace" onclick="hgTab('trace')">✍️</button>
<button type="button" class="hg-btn" id="hg-tab-cards" onclick="hgTab('cards')">🃏</button>
<button type="button" class="hg-btn" id="hg-tab-quiz" onclick="hgTab('quiz')">🔗</button>
</div>
{summary}
<div class="hg-sticker-board">{stickers}</div>
<div id="hg-letters">
  <div class="hg-letter-section"><h3>자음</h3><div class="hg-letter-grid" id="hg-consonant-grid"></div></div>
  <div class="hg-letter-section"><h3>모음</h3><div class="hg-letter-grid" id="hg-vowel-grid"></div></div>
</div>
<div id="hg-combine" style="display:none">
  <div class="hg-combine-eq" id="hg-combine-eq">&nbsp;</div>
  <div class="hg-combine-result" id="hg-combine-result">?</div>
  <div class="hg-combine-word" id="hg-combine-word" style="display:none"><span id="hg-combine-emoji"></span><span id="hg-combine-wordtext"></span></div>
  <div class="hg-letter-section"><h3>자음</h3><div class="hg-combine-row pick" id="hg-combine-cons"></div></div>
  <div class="hg-letter-section"><h3>모음</h3><div class="hg-combine-row pick" id="hg-combine-vowel"></div></div>
</div>
<div id="hg-trace" style="display:none">
  <div class="hg-trace-toolbar">
    <button type="button" class="hg-btn" onclick="hgTracePrev()">◀</button>
    <button type="button" class="hg-btn" onclick="hgSpeak(HG_LETTERS[hgTraceIdx].sound)">🔊</button>
    <button type="button" class="hg-btn" onclick="hgTraceClear()">🔄</button>
    <button type="button" class="hg-btn" onclick="hgTraceNext()">▶</button>
  </div>
  <div class="hg-trace-wrap">
    <div class="hg-trace-guide" id="hg-trace-guide">ㄱ</div>
    <canvas class="hg-trace-canvas" id="hg-trace-canvas"></canvas>
  </div>
</div>
<div id="hg-cards" style="display:none"><div class="hg-card-grid" id="hg-card-grid"></div></div>
<div id="hg-quiz" style="display:none"><div class="hg-quiz-grid" id="hg-quiz-grid"></div></div>
<script>
const HG_WORDS={words_json};
const HG_LETTERS={letters_json};
const HG_TABS=['letters','combine','trace','cards','quiz'];
function hgTab(which){{
  HG_TABS.forEach(function(t){{
    document.getElementById('hg-'+t).style.display=(t===which)?'block':'none';
    document.getElementById('hg-tab-'+t).classList.toggle('on',t===which);
  }});
  if(which==='quiz') hgBuildQuiz();
  if(which==='trace') hgTraceShow();
}}
function hgSpeak(text){{
  try{{
    const u=new SpeechSynthesisUtterance(text);
    u.lang='ko-KR'; u.rate=0.85;
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  }}catch(e){{}}
}}
function hgLog(kind){{
  fetch('/hyeon/hangul/log',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'kind='+kind}}).catch(function(){{}});
}}
let hgAudioCtx=null;
function hgChime(){{
  try{{
    if(!hgAudioCtx) hgAudioCtx=new (window.AudioContext||window.webkitAudioContext)();
    if(hgAudioCtx.state==='suspended') hgAudioCtx.resume();
    const notes=[523.25,659.25,783.99];
    notes.forEach(function(freq,i){{
      const t=hgAudioCtx.currentTime+i*0.11;
      const osc=hgAudioCtx.createOscillator();
      const gain=hgAudioCtx.createGain();
      osc.type='sine'; osc.frequency.value=freq;
      gain.gain.setValueAtTime(0.0001,t);
      gain.gain.linearRampToValueAtTime(0.25,t+0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001,t+0.3);
      osc.connect(gain); gain.connect(hgAudioCtx.destination);
      osc.start(t); osc.stop(t+0.32);
    }});
  }}catch(e){{}}
}}
function hgBuildLetters(){{
  const cGrid=document.getElementById('hg-consonant-grid'); cGrid.innerHTML='';
  const vGrid=document.getElementById('hg-vowel-grid'); vGrid.innerHTML='';
  HG_LETTERS.forEach(function(l){{
    const b=document.createElement('button');
    b.type='button'; b.className='hg-letter'; b.textContent=l.char;
    b.onclick=function(){{ hgSpeak(l.sound); hgLog('letter'); }};
    (l.kind==='자음'?cGrid:vGrid).appendChild(b);
  }});
}}
function hgBuildCards(){{
  const grid=document.getElementById('hg-card-grid'); grid.innerHTML='';
  HG_WORDS.forEach(function(w){{
    const card=document.createElement('button');
    card.type='button'; card.className='hg-card';
    card.innerHTML='<span class="front">'+w.emoji+'</span><span class="back" style="display:none">'+w.word+'</span>';
    card.onclick=function(){{
      const front=card.querySelector('.front'), back=card.querySelector('.back');
      const flipped=back.style.display!=='none';
      front.style.display=flipped?'':'none';
      back.style.display=flipped?'none':'';
      if(!flipped){{ hgSpeak(w.word); hgLog('card'); }}
    }};
    grid.appendChild(card);
  }});
}}
let hgQuiz=null;
function hgBuildQuiz(){{
  const pool=HG_WORDS.slice().sort(function(){{return Math.random()-0.5}}).slice(0,6);
  const left=pool.slice();
  const right=pool.slice().sort(function(){{return Math.random()-0.5}});
  hgQuiz={{selected:null, matched:new Set()}};
  const grid=document.getElementById('hg-quiz-grid'); grid.innerHTML='';
  const leftCol=document.createElement('div'); leftCol.className='hg-quiz-col'; leftCol.id='hg-quiz-left';
  const rightCol=document.createElement('div'); rightCol.className='hg-quiz-col'; rightCol.id='hg-quiz-right';
  grid.appendChild(leftCol); grid.appendChild(rightCol);
  left.forEach(function(w){{
    const b=document.createElement('button'); b.type='button'; b.className='hg-quiz-item'; b.textContent=w.emoji; b.dataset.word=w.word;
    b.onclick=function(){{
      if(hgQuiz.matched.has(w.word))return;
      leftCol.querySelectorAll('.hg-quiz-item').forEach(function(x){{x.classList.remove('sel')}});
      b.classList.add('sel'); hgQuiz.selected=w.word; hgSpeak(w.word);
    }};
    leftCol.appendChild(b);
  }});
  right.forEach(function(w){{
    const b=document.createElement('button'); b.type='button'; b.className='hg-quiz-item'; b.textContent=w.word; b.dataset.word=w.word;
    b.onclick=function(){{
      if(hgQuiz.matched.has(w.word))return;
      if(hgQuiz.selected===w.word){{
        hgQuiz.matched.add(w.word);
        b.classList.add('matched');
        leftCol.querySelectorAll('.hg-quiz-item').forEach(function(x){{if(x.dataset.word===w.word){{x.classList.add('matched');x.classList.remove('sel')}}}});
        hgSpeak('딩동댕');
        hgLog('quiz');
        hgQuiz.selected=null;
      }} else if(hgQuiz.selected){{
        b.classList.add('wrong');
        setTimeout(function(){{b.classList.remove('wrong')}},400);
      }}
    }};
    rightCol.appendChild(b);
  }});
}}
const HG_CONS_IDX={{'ㄱ':0,'ㄴ':2,'ㄷ':3,'ㄹ':5,'ㅁ':6,'ㅂ':7,'ㅅ':9,'ㅇ':11,'ㅈ':12,'ㅊ':14,'ㅋ':15,'ㅌ':16,'ㅍ':17,'ㅎ':18}};
const HG_VOWEL_IDX={{'ㅏ':0,'ㅑ':2,'ㅓ':4,'ㅕ':6,'ㅗ':8,'ㅛ':12,'ㅜ':13,'ㅠ':17,'ㅡ':18,'ㅣ':20}};
let hgCombine={{cons:null,vowel:null}};
function hgBuildCombine(){{
  const consGrid=document.getElementById('hg-combine-cons'); consGrid.innerHTML='';
  const vowelGrid=document.getElementById('hg-combine-vowel'); vowelGrid.innerHTML='';
  HG_LETTERS.filter(function(l){{return l.kind==='자음'}}).forEach(function(l){{
    const b=document.createElement('button'); b.type='button'; b.className='hg-pick'; b.textContent=l.char;
    b.onclick=function(){{
      consGrid.querySelectorAll('.hg-pick').forEach(function(x){{x.classList.remove('sel')}});
      b.classList.add('sel'); hgCombine.cons=l.char; hgTryCombine();
    }};
    consGrid.appendChild(b);
  }});
  HG_LETTERS.filter(function(l){{return l.kind==='모음'}}).forEach(function(l){{
    const b=document.createElement('button'); b.type='button'; b.className='hg-pick'; b.textContent=l.char;
    b.onclick=function(){{
      vowelGrid.querySelectorAll('.hg-pick').forEach(function(x){{x.classList.remove('sel')}});
      b.classList.add('sel'); hgCombine.vowel=l.char; hgTryCombine();
    }};
    vowelGrid.appendChild(b);
  }});
}}
const HG_SYLLABLE_WORDS={{
  '가':['가방','🎒'],'나':['나비','🦋'],'다':['다리','🦵'],'라':['라면','🍜'],'마':['마이크','🎤'],
  '바':['바나나','🍌'],'사':['사과','🍎'],'아':['아기','👶'],'자':['자동차','🚗'],'차':['차','🚙'],
  '카':['카메라','📷'],'타':['타조','🐦'],'파':['파도','🌊'],'하':['하마','🦛'],
  '고':['고래','🐋'],'노':['노루','🦌'],'도':['도넛','🍩'],'로':['로봇','🤖'],'모':['모자','🎩'],
  '보':['보석','💎'],'소':['소','🐮'],'오':['오리','🦆'],'조':['조개','🐚'],'초':['초콜릿','🍫'],
  '코':['코끼리','🐘'],'토':['토끼','🐰'],'포':['포도','🍇'],'호':['호랑이','🐯'],
  '구':['구름','☁️'],'누':['누나','👧'],'무':['무지개','🌈'],'부':['부엉이','🦉'],'수':['수박','🍉'],
  '우':['우유','🥛'],'주':['주스','🧃'],'쿠':['쿠키','🍪'],'후':['후추','🌶️'],
  '기':['기차','🚂'],'리':['리본','🎀'],'미':['미소','😊'],'비':['비행기','✈️'],'시':['시계','🕐'],
  '이':['이빨','🦷'],'지':['지구','🌍'],'치':['치즈','🧀'],'피':['피자','🍕'],
  '여':['여우','🦊'],'거':['거북이','🐢'],'너':['너구리','🦝'],
  '겨':['겨울','❄️'],'어':['어항','🐠'],'요':['요요','🪀'],'야':['야구','⚾'],'유':['유모차','🍼'],
  '저':['저금통','🐷'],'머':['머핀','🧁'],'벼':['벼','🌾'],'버':['버스','🚌'],'혀':['혀','👅'],
  '휴':['휴지','🧻'],'키':['키위','🥝'],'터':['터널','🚇'],'트':['트럭','🚚'],
  '퍼':['퍼즐','🧩'],'푸':['푸딩','🍮'],'교':['교실','🏫'],'뉴':['뉴스','📺'],'니':['니트','🧶'],
  '루':['루돌프','🦌'],'슈':['슈퍼맨','🦸'],'스':['스키','🎿'],'커':['커피','☕'],
  '프':['프라이팬','🍳'],'히':['히어로','🦸']
}};
function hgTryCombine(){{
  const c=hgCombine.cons, v=hgCombine.vowel;
  const eq=document.getElementById('hg-combine-eq');
  const out=document.getElementById('hg-combine-result');
  const wordBox=document.getElementById('hg-combine-word');
  wordBox.style.display='none';
  if(c&&v!==null&&v!==undefined&&HG_CONS_IDX[c]!==undefined&&HG_VOWEL_IDX[v]!==undefined){{
    const code=0xAC00+HG_CONS_IDX[c]*588+HG_VOWEL_IDX[v]*28;
    const syll=String.fromCharCode(code);
    eq.textContent=c+' + '+v;
    out.textContent=syll;
    hgSpeak(syll+'!');
    hgLog('letter');
    const wordData=HG_SYLLABLE_WORDS[syll];
    if(wordData){{
      setTimeout(function(){{
        document.getElementById('hg-combine-emoji').textContent=wordData[1];
        document.getElementById('hg-combine-wordtext').textContent=wordData[0];
        wordBox.style.display='flex';
        hgSpeak(syll+', '+wordData[0]+'!');
      }},600);
    }}
  }} else {{
    eq.innerHTML='&nbsp;';
    out.textContent=(c||'')+(v||'')||'?';
  }}
}}
const HG_TRACE_CHECKPOINTS={{
  'ㄱ':[[0.28,0.22],[0.72,0.22],[0.72,0.78]],
  'ㄴ':[[0.3,0.2],[0.3,0.78],[0.75,0.78]],
  'ㄷ':[[0.75,0.24],[0.3,0.24],[0.3,0.78],[0.75,0.78]],
  'ㄹ':[[0.28,0.18],[0.72,0.18],[0.28,0.42],[0.72,0.42],[0.28,0.66],[0.72,0.82]],
  'ㅁ':[[0.25,0.25],[0.75,0.25],[0.75,0.75],[0.25,0.75],[0.25,0.28]]
}};
const HG_TRACE_START_R=0.22, HG_TRACE_CP_R=0.26;
let hgTraceIdx=0, hgTraceDrawing=false, hgTraceCtx=null, hgTraceCpIdx=0, hgTraceSucceeded=false;
function hgTraceShow(){{
  const cvs=document.getElementById('hg-trace-canvas');
  if(!hgTraceCtx){{
    const wrap=cvs.parentElement;
    cvs.width=wrap.clientWidth; cvs.height=wrap.clientHeight;
    hgTraceCtx=cvs.getContext('2d');
    hgTraceCtx.lineWidth=16; hgTraceCtx.lineCap='round'; hgTraceCtx.lineJoin='round'; hgTraceCtx.strokeStyle='#0f4c81';
    function pos(e){{
      const r=cvs.getBoundingClientRect();
      const p=(e.touches&&e.touches[0])||e;
      return [(p.clientX-r.left)/cvs.width,(p.clientY-r.top)/cvs.height];
    }}
    function dist(a,b){{ return Math.hypot(a[0]-b[0],a[1]-b[1]); }}
    function checkpoints(){{ return HG_TRACE_CHECKPOINTS[HG_LETTERS[hgTraceIdx].char]; }}
    let hgTraceMoveCount=0;
    function start(e){{
      e.preventDefault();
      const p=pos(e);
      const cps=checkpoints();
      if(cps){{
        if(dist(p,cps[0])>HG_TRACE_START_R) return;
        hgTraceCpIdx=1; hgTraceSucceeded=false;
      }}
      hgTraceDrawing=true; hgTraceMoveCount=0;
      hgTraceCtx.beginPath(); hgTraceCtx.moveTo(p[0]*cvs.width,p[1]*cvs.height);
    }}
    function move(e){{
      if(!hgTraceDrawing)return;
      e.preventDefault();
      const p=pos(e);
      hgTraceCtx.lineTo(p[0]*cvs.width,p[1]*cvs.height); hgTraceCtx.stroke(); hgTraceMoveCount++;
      const cps=checkpoints();
      if(cps&&!hgTraceSucceeded&&hgTraceCpIdx<cps.length&&dist(p,cps[hgTraceCpIdx])<=HG_TRACE_CP_R){{
        hgTraceCpIdx++;
        if(hgTraceCpIdx>=cps.length){{
          hgTraceSucceeded=true; hgTraceDrawing=false;
          hgLog('letter'); hgChime(); hgSpeak(HG_LETTERS[hgTraceIdx].char+'!');
        }}
      }}
    }}
    function end(e){{
      if(hgTraceDrawing){{
        hgTraceDrawing=false;
        if(!checkpoints()){{ hgLog('letter'); if(hgTraceMoveCount>=4) hgChime(); }}
      }}
    }}
    cvs.addEventListener('mousedown',start); cvs.addEventListener('mousemove',move); window.addEventListener('mouseup',end);
    cvs.addEventListener('touchstart',start,{{passive:false}}); cvs.addEventListener('touchmove',move,{{passive:false}}); cvs.addEventListener('touchend',end);
  }}
  hgTraceCpIdx=0; hgTraceSucceeded=false;
  document.getElementById('hg-trace-guide').textContent=HG_LETTERS[hgTraceIdx].char;
}}
function hgTraceClear(){{ if(hgTraceCtx) hgTraceCtx.clearRect(0,0,hgTraceCtx.canvas.width,hgTraceCtx.canvas.height); hgTraceCpIdx=0; hgTraceSucceeded=false; }}
function hgTracePrev(){{ hgTraceIdx=(hgTraceIdx-1+HG_LETTERS.length)%HG_LETTERS.length; hgTraceClear(); hgTraceShow(); hgSpeak(HG_LETTERS[hgTraceIdx].sound); }}
function hgTraceNext(){{ hgTraceIdx=(hgTraceIdx+1)%HG_LETTERS.length; hgTraceClear(); hgTraceShow(); hgSpeak(HG_LETTERS[hgTraceIdx].sound); }}
hgBuildLetters();
hgBuildCombine();
hgBuildCards();
</script>
'''
    return page('혜온 한글 공부',body)

@app.route('/hyeon/hangul/stats')
def hangul_stats_detail():
    today=datetime.now(KST).date()
    mon=today-timedelta(days=today.weekday())
    month_start=today.replace(day=1)
    c=db(); all_prog=c.execute('select * from hangul_progress order by activity_date desc').fetchall(); c.close()
    def tier(total):
        if total>=HANGUL_STAR_GOAL: return '🏆'
        elif total>0: return '⭐'
        else: return '·'
    def tier_counts(rows):
        s=t=0
        for p in rows:
            tot=p['cards_flipped']+p['quiz_correct']+p['letters_done']
            if tot>=HANGUL_STAR_GOAL: t+=1
            elif tot>0: s+=1
        return s,t
    week_rows=[p for p in all_prog if mon.isoformat()<=p['activity_date']<=(mon+timedelta(days=6)).isoformat()]
    month_rows=[p for p in all_prog if p['activity_date']>=month_start.isoformat()]
    today_rows=[p for p in all_prog if p['activity_date']==today.isoformat()]
    ts,tt=tier_counts(today_rows); ws,wt=tier_counts(week_rows); ms,mt=tier_counts(month_rows); ls,lt=tier_counts(all_prog)
    body=(f'<div class="toolbar"><a class="btn s" href="/hyeon/hangul">← 한글 공부</a></div>'
          f'<section class="feature-card"><h2 style="margin:0 0 10px">혜온 한글 공부 현황</h2>'
          f'<div class="stat-grid"><div class="stat-card"><span class="muted">오늘</span><div class="big">⭐{ts} 🏆{tt}</div></div>'
          f'<div class="stat-card"><span class="muted">이번 주</span><div class="big">⭐{ws} 🏆{wt}</div></div>'
          f'<div class="stat-card"><span class="muted">이번 달</span><div class="big">⭐{ms} 🏆{mt}</div></div>'
          f'<div class="stat-card"><span class="muted">전체</span><div class="big">⭐{ls} 🏆{lt}</div></div></div>'
          f'</section><section class="feature-card" style="margin-top:14px"><h2 style="margin:0 0 10px">일자별 내역</h2>')
    if not all_prog:
        body+='<div class="muted">아직 활동 기록이 없습니다.</div>'
    for p in all_prog:
        total=p['cards_flipped']+p['quiz_correct']+p['letters_done']
        body+=(f'<div style="padding:8px 0;border-bottom:1px solid #edf1f5;display:flex;justify-content:space-between">'
               f'<b>{H(p["activity_date"])}</b>'
               f'<span>{tier(total)} 카드 {p["cards_flipped"]} · 퀴즈 {p["quiz_correct"]} · 자모 {p["letters_done"]}</span></div>')
    body+='</section>'
    return page('혜온 한글 공부 현황',body)

COLORING_TEMPLATES=[
    {'id': 'ppodeukping', 'name': '뽀득핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/ppodeukping.svg?v=2" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/ppodeukping.svg?v=2', 'outerPath': 'M162 17h11.5v0.5h-11.5zM157 17.5h20.5v0.5h-20.5zM154 18h27v0.5h-27zM152 18.5h31v0.5h-31zM149.5 19h35.5v0.5h-35.5zM148 19.5h38.5v0.5h-38.5zM146 20h42.5v0.5h-42.5zM144.5 20.5h45.5v0.5h-45.5zM143 21h48.5v0.5h-48.5zM141.5 21.5h51v0.5h-51zM140.5 22h53.5v0.5h-53.5zM139 22.5h56v0.5h-56zM138 23h58.5v0.5h-58.5zM137 23.5h60.5v0.5h-60.5zM136 24h62.5v0.5h-62.5zM135 24.5h64.5v0.5h-64.5zM134 25h66.5v0.5h-66.5zM133 25.5h68.5v0.5h-68.5zM132 26h70v0.5h-70zM131.5 26.5h71.5v0.5h-71.5zM130.5 27h73.5v0.5h-73.5zM130 27.5h74.5v0.5h-74.5zM129 28h76.5v0.5h-76.5zM128.5 28.5h78v0.5h-78zM128 29h79v0.5h-79zM127.5 29.5h80v0.5h-80zM127 30h81.5v0.5h-81.5zM126 30.5h83v0.5h-83zM125.5 31h84.5v0.5h-84.5zM125 31.5h85.5v0.5h-85.5zM124.5 32h86.5v0.5h-86.5zM124 32.5h87.5v0.5h-87.5zM123.5 33h88.5v0.5h-88.5zM123 33.5h90v0.5h-90zM122.5 34h91v0.5h-91zM122 34.5h92v0.5h-92zM121.5 35h93v0.5h-93zM121 35.5h94v0.5h-94zM120.5 36h95v0.5h-95zM120 36.5h96v0.5h-96zM119.5 37h97v0.5h-97zM119.5 37.5h97.5v0.5h-97.5zM119 38h98.5v0.5h-98.5zM118.5 38.5h99.5v0.5h-99.5zM118 39h100v0.5h-100zM118 39.5h100.5v0.5h-100.5zM117.5 40h101.5v0.5h-101.5zM117 40.5h102.5v0.5h-102.5zM116.5 41h103.5v0.5h-103.5zM116.5 41.5h104v0.5h-104zM116 42h104.5v0.5h-104.5zM115.5 42.5h105.5v0.5h-105.5zM115.5 43h106v0.5h-106zM115 43.5h107v1h-107zM114.5 44.5h108v0.5h-108zM114 45h109v1h-109zM113.5 46h110v1h-110zM113.5 47h110.5v0.5h-110.5zM113 47.5h111.5v1h-111.5zM112.5 48.5h112.5v1h-112.5zM112 49.5h113.5v1h-113.5zM111.5 50.5h114.5v0.5h-114.5zM111.5 51h115v1h-115zM111 52h116v1h-116zM110.5 53h117v0.5h-117zM110 53.5h117.5v0.5h-117.5zM110 54h118v0.5h-118zM109.5 54.5h118.5v0.5h-118.5zM109 55h119.5v0.5h-119.5zM108.5 55.5h120v0.5h-120zM107 56h122v0.5h-122zM105.5 56.5h123.5v0.5h-123.5zM104.5 57h125v0.5h-125zM103.5 57.5h126v0.5h-126zM102 58h128v0.5h-128zM101.5 58.5h128.5v0.5h-128.5zM100.5 59h129.5v0.5h-129.5zM99.5 59.5h131v0.5h-131zM98.5 60h132v0.5h-132zM98 60.5h133v0.5h-133zM97.5 61h133.5v0.5h-133.5zM96.5 61.5h134.5v0.5h-134.5zM96 62h135.5v0.5h-135.5zM95.5 62.5h136v0.5h-136zM95 63h137v0.5h-137zM94.5 63.5h137.5v0.5h-137.5zM94 64h138v0.5h-138zM93.5 64.5h139v0.5h-139zM93 65h139.5v0.5h-139.5zM92.5 65.5h140v0.5h-140zM92 66h141v0.5h-141zM91.5 66.5h141.5v0.5h-141.5zM91 67h142v0.5h-142zM90.5 67.5h143v0.5h-143zM90 68h143.5v0.5h-143.5zM89.5 68.5h144v1h-144zM89 69.5h145v0.5h-145zM88.5 70h145.5v1h-145.5zM88 71h146v0.5h-146zM87.5 71.5h147v1h-147zM87 72.5h147.5v0.5h-147.5zM86.5 73h148v0.5h-148zM86.5 73.5h148.5v0.5h-148.5zM86 74h149v1h-149zM85.5 75h149.5v0.5h-149.5zM85.5 75.5h150v0.5h-150zM85 76h150.5v1.5h-150.5zM84.5 77.5h151v1h-151zM84 78.5h152v1.5h-152zM83.5 80h152.5v1h-152.5zM83.5 81h153v0.5h-153zM83 81.5h153.5v1h-153.5zM82.5 82.5h154v0.5h-154zM82 83h154.5v0.5h-154.5zM81.5 83.5h155v0.5h-155zM80 84h156.5v0.5h-156.5zM79.5 84.5h157.5v0.5h-157.5zM78.5 85h158.5v0.5h-158.5zM77.5 85.5h159.5v0.5h-159.5zM77 86h160v0.5h-160zM76.5 86.5h160.5v0.5h-160.5zM75.5 87h161.5v0.5h-161.5zM75 87.5h162v0.5h-162zM74.5 88h162.5v0.5h-162.5zM74 88.5h163.5v0.5h-163.5zM73.5 89h164v0.5h-164zM73 89.5h164.5v0.5h-164.5zM72.5 90h165v1h-165zM72 91h165.5v0.5h-165.5zM71.5 91.5h166v1h-166zM71 92.5h166.5v1h-166.5zM70.5 93.5h167v1h-167zM70.5 94.5h167.5v1.5h-167.5zM70 96h168v3h-168zM70.5 99h167.5v3h-167.5zM71 102h167v1.5h-167zM71.5 103.5h166.5v1h-166.5zM72 104.5h166v1.5h-166zM72.5 106h165.5v1h-165.5zM73 107h165v0.5h-165zM73.5 107.5h164.5v2h-164.5zM73 109.5h165v3.5h-165zM73 113h164.5v2h-164.5zM72.5 115h165v4.5h-165zM73 119.5h164.5v1h-164.5zM73 120.5h164v3.5h-164zM64.5 124h3v0.5h-3zM63.5 124.5h5v0.5h-5zM63 125h6.5v0.5h-6.5zM62.5 125.5h7.5v0.5h-7.5zM73.5 124h163.5v2h-163.5zM62.5 126h8v0.5h-8zM73 126h164v0.5h-164zM62 126.5h9v0.5h-9zM72.5 126.5h164.5v0.5h-164.5zM62 127h9.5v0.5h-9.5zM72 127h165v0.5h-165zM62 127.5h175v2h-175zM62 129.5h174.5v3.5h-174.5zM62.5 133h174v1.5h-174zM63 134.5h173.5v1.5h-173.5zM262.5 136h2.5v0.5h-2.5zM63.5 136h173v1h-173zM259 136.5h8.5v0.5h-8.5zM257.5 137h11.5v0.5h-11.5zM256 137.5h14v0.5h-14zM64 137h172.5v1.5h-172.5zM254.5 138h16.5v0.5h-16.5zM64.5 138.5h172v0.5h-172zM253.5 138.5h18v0.5h-18zM252.5 139h20v0.5h-20zM64.5 139h172.5v1h-172.5zM251.5 139.5h21.5v0.5h-21.5zM251 140h22.5v0.5h-22.5zM65 140h172v1h-172zM250 140.5h23.5v0.5h-23.5zM50 141h9.5v0.5h-9.5zM64.5 141h172.5v0.5h-172.5zM249.5 141h24.5v0.5h-24.5zM47 141.5h14.5v0.5h-14.5zM64 141.5h173v0.5h-173zM249 141.5h25.5v0.5h-25.5zM45 142h18v0.5h-18zM63.5 142h173.5v0.5h-173.5zM248 142h26.5v0.5h-26.5zM43.5 142.5h193.5v0.5h-193.5zM247.5 142.5h27.5v0.5h-27.5zM42 143h195v0.5h-195zM247 143h28v0.5h-28zM41 143.5h196v0.5h-196zM40 144h197.5v0.5h-197.5zM246.5 143.5h29v1h-29zM39 144.5h198.5v0.5h-198.5zM246 144.5h30v0.5h-30zM38.5 145h199v0.5h-199zM245.5 145h30.5v0.5h-30.5zM37.5 145.5h200v0.5h-200zM245 145.5h31v0.5h-31zM37 146h200.5v0.5h-200.5zM244.5 146h31.5v0.5h-31.5zM36.5 146.5h201v0.5h-201zM244.5 146.5h32v0.5h-32zM35.5 147h202v0.5h-202zM35 147.5h202.5v0.5h-202.5zM244 147h32.5v1h-32.5zM34.5 148h203.5v0.5h-203.5zM243.5 148h33v0.5h-33zM34 148.5h204v0.5h-204zM33.5 149h204.5v0.5h-204.5zM243 148.5h33.5v1h-33.5zM33 149.5h205v0.5h-205zM242.5 149.5h34v0.5h-34zM32.5 150h205.5v0.5h-205.5zM32 150.5h206v0.5h-206zM242.5 150h34.5v1h-34.5zM31.5 151h207v0.5h-207zM31 151.5h207.5v0.5h-207.5zM242 151h35v1h-35zM30.5 152h208.5v0.5h-208.5zM241.5 152h35.5v0.5h-35.5zM30 152.5h209.5v0.5h-209.5zM241 152.5h36v0.5h-36zM29.5 153h210.5v0.5h-210.5zM240.5 153h37v0.5h-37zM29 153.5h248.5v0.5h-248.5zM28.5 154h249.5v1h-249.5zM28 155h250.5v0.5h-250.5zM27.5 155.5h251.5v0.5h-251.5zM27 156h252v0.5h-252zM26.5 156.5h253v0.5h-253zM26 157h253.5v0.5h-253.5zM25.5 157.5h254.5v0.5h-254.5zM21 158h1v0.5h-1zM25 158h255v0.5h-255zM19.5 158.5h261v0.5h-261zM19 159h261.5v0.5h-261.5zM18.5 159.5h262.5v1h-262.5zM18 160.5h263v0.5h-263zM18 161h263.5v1h-263.5zM18.5 162h263v1h-263zM19 163h262.5v1h-262.5zM19.5 164h262v1h-262zM20 165h261.5v0.5h-261.5zM20.5 165.5h261v1h-261zM21 166.5h260.5v0.5h-260.5zM21.5 167h260v0.5h-260zM22 167.5h259v1h-259zM22.5 168.5h258.5v0.5h-258.5zM23 169h258.5v1h-258.5zM23.5 170h258v0.5h-258zM24 170.5h257.5v3.5h-257.5zM24.5 174h257v1h-257zM24.5 175h256.5v1.5h-256.5zM25 176.5h256v0.5h-256zM25 177h255.5v1h-255.5zM25.5 178h255v0.5h-255zM25.5 178.5h254.5v1h-254.5zM26 179.5h253.5v0.5h-253.5zM26 180h253v0.5h-253zM26.5 180.5h252v0.5h-252zM26.5 181h251.5v0.5h-251.5zM27 181.5h250.5v0.5h-250.5zM27 182h250v0.5h-250zM27.5 182.5h248.5v0.5h-248.5zM27.5 183h247v0.5h-247zM28 183.5h246v0.5h-246zM28.5 184h245v0.5h-245zM28.5 184.5h244.5v0.5h-244.5zM29 185h244v0.5h-244zM29.5 185.5h243.5v0.5h-243.5zM30 186h242.5v0.5h-242.5zM30.5 186.5h242v0.5h-242zM31 187h241v0.5h-241zM31.5 187.5h240.5v0.5h-240.5zM32 188h239.5v0.5h-239.5zM32.5 188.5h239v0.5h-239zM33 189h238.5v0.5h-238.5zM33.5 189.5h237.5v0.5h-237.5zM34.5 190h236v0.5h-236zM35 190.5h235.5v0.5h-235.5zM35.5 191h234.5v0.5h-234.5zM36.5 191.5h233.5v0.5h-233.5zM37.5 192h232v0.5h-232zM38.5 192.5h230.5v0.5h-230.5zM39.5 193h229.5v0.5h-229.5zM40.5 193.5h228v0.5h-228zM41.5 194h226.5v0.5h-226.5zM43.5 194.5h17.5v0.5h-17.5zM63.5 194.5h204v0.5h-204zM45.5 195h13.5v0.5h-13.5zM64 195h203.5v0.5h-203.5zM48 195.5h8.5v0.5h-8.5zM64.5 195.5h202.5v0.5h-202.5zM65 196h201.5v0.5h-201.5zM65.5 196.5h200.5v0.5h-200.5zM66 197h200v0.5h-200zM67 197.5h198.5v0.5h-198.5zM67.5 198h197.5v0.5h-197.5zM68 198.5h196.5v0.5h-196.5zM68.5 199h195.5v0.5h-195.5zM69 199.5h194.5v0.5h-194.5zM69.5 200h193.5v0.5h-193.5zM70.5 200.5h192v0.5h-192zM71 201h191v0.5h-191zM71.5 201.5h190v0.5h-190zM72 202h189v0.5h-189zM72.5 202.5h187.5v0.5h-187.5zM73 203h186.5v0.5h-186.5zM74 203.5h185v0.5h-185zM74.5 204h183.5v0.5h-183.5zM75 204.5h182.5v0.5h-182.5zM75.5 205h181.5v0.5h-181.5zM76 205.5h180v0.5h-180zM76.5 206h179v0.5h-179zM77.5 206.5h177.5v0.5h-177.5zM78 207h176v0.5h-176zM78.5 207.5h175v0.5h-175zM79 208h173.5v0.5h-173.5zM79.5 208.5h172.5v0.5h-172.5zM80 209h171v0.5h-171zM80.5 209.5h169.5v0.5h-169.5zM81.5 210h167.5v0.5h-167.5zM82 210.5h166.5v0.5h-166.5zM82.5 211h165v0.5h-165zM83 211.5h163.5v0.5h-163.5zM83.5 212h162v0.5h-162zM84 212.5h27v0.5h-27zM114 212.5h2.5v0.5h-2.5zM121 212.5h123.5v0.5h-123.5zM85 213h25.5v0.5h-25.5zM122.5 213h121v0.5h-121zM85.5 213.5h24.5v0.5h-24.5zM123 213.5h119.5v0.5h-119.5zM86 214h23.5v0.5h-23.5zM124 214h117.5v0.5h-117.5zM86.5 214.5h23v0.5h-23zM125 214.5h115.5v0.5h-115.5zM87 215h22v0.5h-22zM125.5 215h114v0.5h-114zM87.5 215.5h21.5v0.5h-21.5zM126 215.5h112v0.5h-112zM88 216h21v0.5h-21zM126.5 216h110.5v0.5h-110.5zM88.5 216.5h20.5v0.5h-20.5zM126 216.5h109.5v0.5h-109.5zM89.5 217h20v0.5h-20zM126 217h108v0.5h-108zM90 217.5h19.5v0.5h-19.5zM125.5 217.5h107.5v0.5h-107.5zM90.5 218h19.5v0.5h-19.5zM125.5 218h106v0.5h-106zM91.5 218.5h18.5v0.5h-18.5zM125 218.5h104.5v0.5h-104.5zM92 219h18v0.5h-18zM125 219h103v0.5h-103zM92.5 219.5h18v0.5h-18zM125 219.5h101v0.5h-101zM93 220h17.5v0.5h-17.5zM124.5 220h99.5v0.5h-99.5zM94 220.5h16.5v0.5h-16.5zM124.5 220.5h97.5v0.5h-97.5zM94.5 221h16v0.5h-16zM124.5 221h95v0.5h-95zM95 221.5h16v0.5h-16zM124 221.5h91.5v0.5h-91.5zM95.5 222h16v0.5h-16zM124 222h80.5v0.5h-80.5zM96.5 222.5h15v0.5h-15zM124 222.5h80v0.5h-80zM97.5 223h14.5v0.5h-14.5zM124 223h79.5v0.5h-79.5zM101.5 223.5h10.5v0.5h-10.5zM124 223.5h79v0.5h-79zM102 224h10v0.5h-10zM123.5 224h80v0.5h-80zM102.5 224.5h9.5v0.5h-9.5zM123.5 224.5h80.5v0.5h-80.5zM103 225h9v0.5h-9zM123.5 225h81v0.5h-81zM103.5 225.5h8.5v0.5h-8.5zM123 225.5h81.5v0.5h-81.5zM104 226h8.5v0.5h-8.5zM103.5 226.5h9v0.5h-9zM123 226h82v1h-82zM104 227h8.5v1.5h-8.5zM104.5 228.5h8.5v0.5h-8.5zM123 227h82.5v2h-82.5zM104 229h9v0.5h-9zM122.5 229h83v0.5h-83zM103.5 229.5h9.5v0.5h-9.5zM122.5 229.5h82.5v0.5h-82.5zM103 230h10v0.5h-10zM102 230.5h11v0.5h-11zM122 230h83v1h-83zM101.5 231h11.5v0.5h-11.5zM101 231.5h12v0.5h-12zM121.5 231h83.5v1h-83.5zM121 232h84.5v0.5h-84.5zM100.5 232h12v1h-12zM120.5 232.5h85.5v0.5h-85.5zM120 233h86.5v0.5h-86.5zM100 233h12v1h-12zM119.5 233.5h87.5v0.5h-87.5zM119 234h88.5v0.5h-88.5zM100 234h11.5v1h-11.5zM118.5 234.5h89v0.5h-89zM100 235h11v0.5h-11zM118 235h90v0.5h-90zM100.5 235.5h10v0.5h-10zM117.5 235.5h91v0.5h-91zM100.5 236h9.5v0.5h-9.5zM116.5 236h92v0.5h-92zM101 236.5h8v0.5h-8zM116 236.5h93v0.5h-93zM102 237h6.5v0.5h-6.5zM115.5 237h94v0.5h-94zM103.5 237.5h3.5v0.5h-3.5zM115 237.5h94.5v0.5h-94.5zM114 238h95.5v0.5h-95.5zM113.5 238.5h96.5v0.5h-96.5zM112.5 239h97.5v0.5h-97.5zM111.5 239.5h98.5v0.5h-98.5zM111 240h99.5v0.5h-99.5zM110 240.5h100.5v0.5h-100.5zM109.5 241h101v0.5h-101zM108.5 241.5h102v0.5h-102zM108 242h102.5v0.5h-102.5zM107.5 242.5h103v0.5h-103zM107 243h104v1h-104zM106.5 244h104.5v0.5h-104.5zM106 244.5h105v0.5h-105zM105.5 245h105.5v1h-105.5zM105 246h106v1h-106zM104.5 247h106.5v1.5h-106.5zM104 248.5h107v2h-107zM104 250.5h106.5v3h-106.5zM104 253.5h106v1h-106zM104.5 254.5h105.5v0.5h-105.5zM104.5 255h105v1h-105zM105 256h104.5v0.5h-104.5zM105 256.5h104v0.5h-104zM105.5 257h103.5v0.5h-103.5zM106 257.5h102.5v1h-102.5zM106.5 258.5h101.5v0.5h-101.5zM107 259h101v0.5h-101zM107.5 259.5h100v0.5h-100zM108 260h99v0.5h-99zM108.5 260.5h98.5v0.5h-98.5zM109 261h97.5v0.5h-97.5zM109.5 261.5h96.5v0.5h-96.5zM110 262h95.5v0.5h-95.5zM111 262.5h94v0.5h-94zM111.5 263h92.5v0.5h-92.5zM112.5 263.5h91v0.5h-91zM113.5 264h89v0.5h-89zM114.5 264.5h63v0.5h-63zM178 264.5h23.5v0.5h-23.5zM115.5 265h61.5v0.5h-61.5zM180 265h20.5v0.5h-20.5zM117 265.5h59.5v0.5h-59.5zM181.5 265.5h18v0.5h-18zM118.5 266h57.5v0.5h-57.5zM183.5 266h14v0.5h-14zM121 266.5h12v0.5h-12zM134 266.5h41.5v0.5h-41.5zM187.5 266.5h6.5v0.5h-6.5zM125.5 267h2.5v0.5h-2.5zM134.5 267h41v0.5h-41zM135 267.5h40v0.5h-40zM135.5 268h39.5v0.5h-39.5zM136 268.5h38.5v1h-38.5zM136 269.5h38v1h-38zM136.5 270.5h37v1h-37zM136.5 271.5h36.5v0.5h-36.5zM137 272h36v0.5h-36zM137 272.5h35.5v0.5h-35.5zM137.5 273h35v0.5h-35zM138 273.5h34v0.5h-34zM138 274h15.5v0.5h-15.5zM154 274h18v0.5h-18zM138.5 274.5h14.5v0.5h-14.5zM154.5 274.5h17v0.5h-17zM139 275h13.5v0.5h-13.5zM155 275h16.5v0.5h-16.5zM139.5 275.5h12.5v0.5h-12.5zM155.5 275.5h15.5v0.5h-15.5zM140 276h11v0.5h-11zM156 276h15v0.5h-15zM141 276.5h9.5v0.5h-9.5zM142 277h7v0.5h-7zM156 276.5h14.5v1h-14.5zM144 277.5h3v0.5h-3zM156 277.5h14v0.5h-14zM156.5 278h13.5v0.5h-13.5zM156.5 278.5h13v0.5h-13zM157 279h12.5v0.5h-12.5zM157.5 279.5h11.5v0.5h-11.5zM158 280h10.5v0.5h-10.5zM158.5 280.5h9.5v0.5h-9.5zM159 281h8v0.5h-8zM160 281.5h6.5v0.5h-6.5z', 'allowDelete': False},
    {'id': 'chamongping', 'name': '차몽핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/chamongping.svg?v=2" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/chamongping.svg?v=2', 'outerPath': 'M157 12.5h1v0.5h-1zM156.5 13h1.5v0.5h-1.5zM156 13.5h2.5v0.5h-2.5zM155.5 14h3v0.5h-3zM155 14.5h3.5v0.5h-3.5zM154.5 15h4v0.5h-4zM154 15.5h4.5v0.5h-4.5zM153.5 16h5v0.5h-5zM153 16.5h5.5v0.5h-5.5zM152.5 17h6.5v0.5h-6.5zM152 17.5h7v0.5h-7zM151.5 18h7.5v0.5h-7.5zM151 18.5h8.5v0.5h-8.5zM150 19h9.5v0.5h-9.5zM149.5 19.5h10v0.5h-10zM148.5 20h11.5v0.5h-11.5zM148 20.5h12v0.5h-12zM147 21h13.5v0.5h-13.5zM146.5 21.5h14v0.5h-14zM145.5 22h15v0.5h-15zM145 22.5h16v0.5h-16zM144 23h17v0.5h-17zM143.5 23.5h18v0.5h-18zM142.5 24h19v0.5h-19zM142 24.5h20v0.5h-20zM141.5 25h20.5v0.5h-20.5zM141 25.5h21v0.5h-21zM140.5 26h22v0.5h-22zM140 26.5h22.5v0.5h-22.5zM139.5 27h23v0.5h-23zM139 27.5h24v0.5h-24zM138.5 28h24.5v1h-24.5zM138 29h25.5v0.5h-25.5zM137.5 29.5h26v1h-26zM137 30.5h27v0.5h-27zM136.5 31h27.5v1h-27.5zM136 32h28v1h-28zM135.5 33h29v1h-29zM135 34h29.5v1h-29.5zM134.5 35h30v0.5h-30zM134.5 35.5h30.5v0.5h-30.5zM134 36h31v1h-31zM129.5 37h1v0.5h-1zM133.5 37h31.5v0.5h-31.5zM128.5 37.5h3v0.5h-3zM133 37.5h32v0.5h-32zM128 38h4v0.5h-4zM132.5 38h32.5v0.5h-32.5zM96 38.5h6v0.5h-6zM127.5 38.5h37.5v0.5h-37.5zM92.5 39h12.5v0.5h-12.5zM127 39h38v0.5h-38zM91 39.5h16v0.5h-16zM126.5 39.5h38.5v0.5h-38.5zM89 40h19.5v0.5h-19.5zM126.5 40h39v0.5h-39zM87.5 40.5h22v0.5h-22zM86.5 41h24.5v0.5h-24.5zM85.5 41.5h26.5v0.5h-26.5zM84 42h29v0.5h-29zM83 42.5h31v0.5h-31zM82 43h32.5v0.5h-32.5zM126 40.5h39.5v3h-39.5zM81 43.5h34.5v0.5h-34.5zM126 43.5h39v0.5h-39zM80 44h36v0.5h-36zM126.5 44h38.5v0.5h-38.5zM79 44.5h38v0.5h-38zM127 44.5h38v0.5h-38zM78 45h39.5v0.5h-39.5zM127.5 45h37.5v0.5h-37.5zM77 45.5h41v0.5h-41zM76 46h43v0.5h-43zM75 46.5h44.5v0.5h-44.5zM128 45.5h37v1.5h-37zM74 47h46v0.5h-46zM127.5 47h37.5v0.5h-37.5zM72.5 47.5h48v0.5h-48zM127.5 47.5h37v0.5h-37zM71 48h50.5v0.5h-50.5zM70 48.5h52v0.5h-52zM68 49h54.5v0.5h-54.5zM127 48h37.5v1.5h-37.5zM66 49.5h57v0.5h-57zM127 49.5h37v0.5h-37zM64 50h59.5v0.5h-59.5zM126.5 50h37.5v0.5h-37.5zM61.5 50.5h62.5v0.5h-62.5zM126 50.5h38v0.5h-38zM58 51h66.5v0.5h-66.5zM125.5 51h38v0.5h-38zM56 51.5h107.5v0.5h-107.5zM56 52h107v1h-107zM56 53h106.5v0.5h-106.5zM56.5 53.5h106v0.5h-106zM57 54h105v0.5h-105zM57 54.5h104.5v0.5h-104.5zM57.5 55h104v0.5h-104zM57.5 55.5h103.5v0.5h-103.5zM58 56h102.5v0.5h-102.5zM58.5 56.5h101.5v0.5h-101.5zM58.5 57h101v0.5h-101zM59 57.5h100v0.5h-100zM59 58h100.5v0.5h-100.5zM59.5 58.5h100.5v0.5h-100.5zM60 59h100.5v0.5h-100.5zM60 59.5h105v0.5h-105zM60.5 60h108.5v0.5h-108.5zM61 60.5h111v0.5h-111zM61 61h113.5v0.5h-113.5zM61.5 61.5h115v0.5h-115zM62 62h116v0.5h-116zM62.5 62.5h117.5v0.5h-117.5zM63 63h118v0.5h-118zM63.5 63.5h119v0.5h-119zM64 64h120v0.5h-120zM64.5 64.5h120.5v0.5h-120.5zM65 65h121v0.5h-121zM65.5 65.5h122v0.5h-122zM66 66h122.5v0.5h-122.5zM66.5 66.5h123v0.5h-123zM67 67h123.5v0.5h-123.5zM67.5 67.5h124v0.5h-124zM68.5 68h124v0.5h-124zM69 68.5h124v0.5h-124zM70 69h124v0.5h-124zM70.5 69.5h124.5v0.5h-124.5zM71.5 70h124v0.5h-124zM72.5 70.5h124v0.5h-124zM73.5 71h123.5v0.5h-123.5zM74.5 71.5h123.5v0.5h-123.5zM75.5 72h123v0.5h-123zM76.5 72.5h122.5v0.5h-122.5zM78 73h34v0.5h-34zM112.5 73h87.5v0.5h-87.5zM79.5 73.5h30.5v0.5h-30.5zM113 73.5h87.5v0.5h-87.5zM81 74h27v0.5h-27zM113.5 74h87.5v0.5h-87.5zM83 74.5h22.5v0.5h-22.5zM114 74.5h88v0.5h-88zM85 75h18v0.5h-18zM113.5 75h89v0.5h-89zM89 75.5h10.5v0.5h-10.5zM113 75.5h90v0.5h-90zM112.5 76h91v0.5h-91zM112 76.5h92v0.5h-92zM111 77h93.5v0.5h-93.5zM110.5 77.5h94.5v0.5h-94.5zM110 78h95.5v0.5h-95.5zM109 78.5h97v0.5h-97zM108.5 79h98v0.5h-98zM107.5 79.5h99.5v0.5h-99.5zM107 80h100.5v0.5h-100.5zM106.5 80.5h101.5v0.5h-101.5zM105.5 81h103v0.5h-103zM105 81.5h104v0.5h-104zM104.5 82h105v0.5h-105zM103.5 82.5h106.5v0.5h-106.5zM103 83h107.5v0.5h-107.5zM102.5 83.5h108.5v0.5h-108.5zM101.5 84h109.5v0.5h-109.5zM101 84.5h110.5v0.5h-110.5zM100.5 85h111.5v0.5h-111.5zM100 85.5h112.5v0.5h-112.5zM99.5 86h113v0.5h-113zM99 86.5h114v0.5h-114zM98.5 87h115v0.5h-115zM98 87.5h116v0.5h-116zM97.5 88h117v0.5h-117zM97 88.5h117.5v0.5h-117.5zM96.5 89h118.5v0.5h-118.5zM96 89.5h119.5v0.5h-119.5zM95.5 90h120.5v0.5h-120.5zM95 90.5h121.5v0.5h-121.5zM95 91h122v0.5h-122zM94.5 91.5h122.5v0.5h-122.5zM94 92h123.5v0.5h-123.5zM93.5 92.5h124.5v0.5h-124.5zM93 93h125.5v1h-125.5zM92.5 94h126.5v0.5h-126.5zM92 94.5h127.5v0.5h-127.5zM91.5 95h128v0.5h-128zM91.5 95.5h128.5v0.5h-128.5zM91 96h129.5v0.5h-129.5zM90.5 96.5h130v0.5h-130zM90.5 97h130.5v0.5h-130.5zM90 97.5h131.5v1h-131.5zM89.5 98.5h132.5v0.5h-132.5zM89 99h133.5v1h-133.5zM88.5 100h134.5v0.5h-134.5zM88 100.5h135.5v0.5h-135.5zM87.5 101h136v0.5h-136zM87.5 101.5h136.5v0.5h-136.5zM87 102h137v0.5h-137zM86.5 102.5h138v1h-138zM86 103.5h139v0.5h-139zM85.5 104h140v0.5h-140zM85 104.5h140.5v0.5h-140.5zM85 105h141v0.5h-141zM84.5 105.5h141.5v0.5h-141.5zM84.5 106h142v0.5h-142zM84 106.5h142.5v0.5h-142.5zM84 107h143v0.5h-143zM83.5 107.5h143.5v0.5h-143.5zM83 108h144.5v0.5h-144.5zM83 108.5h145v0.5h-145zM82.5 109h145.5v0.5h-145.5zM82.5 109.5h146v0.5h-146zM82 110h146.5v0.5h-146.5zM81.5 110.5h147.5v1h-147.5zM81 111.5h148.5v1h-148.5zM80.5 112.5h149.5v1h-149.5zM80 113.5h150.5v1h-150.5zM79.5 114.5h151.5v1h-151.5zM79 115.5h152.5v1h-152.5zM79 116.5h153v0.5h-153zM78.5 117h153.5v0.5h-153.5zM78.5 117.5h154v0.5h-154zM78 118h154.5v0.5h-154.5zM78 118.5h155v0.5h-155zM77.5 119h155.5v1h-155.5zM77.5 120h156v0.5h-156zM77 120.5h156.5v0.5h-156.5zM77 121h157v0.5h-157zM76.5 121.5h157.5v0.5h-157.5zM76.5 122h158v1h-158zM76 123h159v1.5h-159zM75.5 124.5h160v1h-160zM75.5 125.5h160.5v0.5h-160.5zM75 126h161v0.5h-161zM75 126.5h161.5v1h-161.5zM74.5 127.5h162v0.5h-162zM74.5 128h162.5v1.5h-162.5zM74 129.5h163.5v1h-163.5zM74 130.5h164v0.5h-164zM73.5 131h164.5v1h-164.5zM73.5 132h165v1h-165zM73 133h165.5v0.5h-165.5zM73 133.5h166v1.5h-166zM73 135h166.5v0.5h-166.5zM72.5 135.5h167v1h-167zM72.5 136.5h167.5v1.5h-167.5zM72 138h168.5v2h-168.5zM72 140h169v1h-169zM71.5 141h169.5v1h-169.5zM71.5 142h170v2h-170zM71.5 144h170.5v1h-170.5zM71 145h171v1.5h-171zM71 146.5h171.5v4.5h-171.5zM71 151h172v8h-172zM71 159h171.5v3h-171.5zM71.5 162h170.5v1.5h-170.5zM71.5 163.5h170v1h-170zM71.5 164.5h169.5v1h-169.5zM71.5 165.5h169v1h-169zM71.5 166.5h168.5v0.5h-168.5zM72 167h167.5v0.5h-167.5zM72 167.5h167v1h-167zM72 168.5h166.5v0.5h-166.5zM72 169h166v0.5h-166zM72 169.5h165.5v0.5h-165.5zM72.5 170h164v0.5h-164zM72.5 170.5h163.5v0.5h-163.5zM72.5 171h163v0.5h-163zM72.5 171.5h162v0.5h-162zM73 172h161v0.5h-161zM73 172.5h160v0.5h-160zM73 173h159v0.5h-159zM73 173.5h158v0.5h-158zM73.5 174h156.5v0.5h-156.5zM73.5 174.5h155v0.5h-155zM73.5 175h154v0.5h-154zM73.5 175.5h152.5v0.5h-152.5zM74 176h151.5v0.5h-151.5zM74 176.5h151v0.5h-151zM74 177h150.5v0.5h-150.5zM74.5 177.5h149.5v0.5h-149.5zM74.5 178h149v0.5h-149zM74.5 178.5h148.5v0.5h-148.5zM75 179h147.5v0.5h-147.5zM75 179.5h147v0.5h-147zM75 180h146.5v0.5h-146.5zM75.5 180.5h145.5v0.5h-145.5zM75.5 181h145v0.5h-145zM76 181.5h143.5v0.5h-143.5zM76 182h143v0.5h-143zM76 182.5h142.5v0.5h-142.5zM76.5 183h141.5v0.5h-141.5zM76.5 183.5h141v0.5h-141zM77 184h139.5v0.5h-139.5zM77 184.5h139v0.5h-139zM77.5 185h138v0.5h-138zM77.5 185.5h137.5v0.5h-137.5zM78 186h136v0.5h-136zM78 186.5h135.5v0.5h-135.5zM78.5 187h134.5v0.5h-134.5zM78.5 187.5h133.5v0.5h-133.5zM79 188h132.5v0.5h-132.5zM79 188.5h132v0.5h-132zM79.5 189h130.5v0.5h-130.5zM79.5 189.5h130v0.5h-130zM80 190h128.5v0.5h-128.5zM80.5 190.5h127.5v0.5h-127.5zM80.5 191h126.5v0.5h-126.5zM81 191.5h125.5v0.5h-125.5zM81.5 192h124.5v0.5h-124.5zM81.5 192.5h124v0.5h-124zM82 193h124v0.5h-124zM82.5 193.5h124v0.5h-124zM82.5 194h124.5v0.5h-124.5zM83 194.5h128v0.5h-128zM83.5 195h128.5v0.5h-128.5zM84 195.5h129v0.5h-129zM84 196h129.5v0.5h-129.5zM84.5 196.5h129v0.5h-129zM85 197h129v0.5h-129zM85.5 197.5h128.5v0.5h-128.5zM86 198h128.5v0.5h-128.5zM86.5 198.5h128v1h-128zM87 199.5h127.5v0.5h-127.5zM87.5 200h127v0.5h-127zM88 200.5h126.5v0.5h-126.5zM88.5 201h126.5v0.5h-126.5zM89 201.5h126v0.5h-126zM89.5 202h125.5v0.5h-125.5zM90 202.5h125v0.5h-125zM90.5 203h124.5v0.5h-124.5zM91.5 203.5h123.5v0.5h-123.5zM92 204h123v0.5h-123zM92.5 204.5h122.5v0.5h-122.5zM93 205h122v0.5h-122zM94 205.5h121v0.5h-121zM94.5 206h120.5v0.5h-120.5zM95 206.5h120v0.5h-120zM96 207h119v0.5h-119zM96.5 207.5h118v0.5h-118zM97.5 208h61v0.5h-61zM159 208h55.5v0.5h-55.5zM98.5 208.5h56.5v0.5h-56.5zM159.5 208.5h55v0.5h-55zM99 209h31v0.5h-31zM134 209h16.5v0.5h-16.5zM160 209h54v0.5h-54zM100 209.5h29v0.5h-29zM101 210h27.5v0.5h-27.5zM102 210.5h25.5v0.5h-25.5zM160.5 209.5h53.5v1.5h-53.5zM103.5 211h23v0.5h-23zM160.5 211h54v0.5h-54zM104.5 211.5h21v0.5h-21zM106 212h18v0.5h-18zM160 211.5h54.5v1h-54.5zM108 212.5h14.5v0.5h-14.5zM110 213h10.5v0.5h-10.5zM114.5 213.5h3v0.5h-3zM160 212.5h55v2h-55zM160.5 214.5h55v2h-55zM161 216.5h54.5v0.5h-54.5zM161 217h55v1h-55zM161.5 218h54.5v1.5h-54.5zM162 219.5h54.5v0.5h-54.5zM162.5 220h54v1h-54zM163 221h53.5v1h-53.5zM163 222h54v1.5h-54zM163 223.5h54.5v0.5h-54.5zM162.5 224h55.5v0.5h-55.5zM162.5 224.5h56v0.5h-56zM162.5 225h58v0.5h-58zM162 225.5h60v0.5h-60zM162 226h61v0.5h-61zM161.5 226.5h62v0.5h-62zM161.5 227h62.5v0.5h-62.5zM161 227.5h63.5v0.5h-63.5zM160.5 228h64.5v0.5h-64.5zM160 228.5h65.5v0.5h-65.5zM159.5 229h66.5v0.5h-66.5zM159 229.5h67.5v0.5h-67.5zM158.5 230h68v0.5h-68zM158 230.5h69v0.5h-69zM157.5 231h70v0.5h-70zM156.5 231.5h71.5v0.5h-71.5zM156 232h73.5v0.5h-73.5zM155.5 232.5h75.5v0.5h-75.5zM154.5 233h77.5v0.5h-77.5zM154 233.5h79v0.5h-79zM153.5 234h80v0.5h-80zM152.5 234.5h81.5v0.5h-81.5zM152 235h82.5v0.5h-82.5zM151 235.5h84v0.5h-84zM150.5 236h85v0.5h-85zM149.5 236.5h86.5v0.5h-86.5zM148.5 237h88v0.5h-88zM147.5 237.5h90v0.5h-90zM134 238h2v0.5h-2zM146.5 238h91.5v0.5h-91.5zM133 238.5h4.5v0.5h-4.5zM145.5 238.5h93v0.5h-93zM132.5 239h6.5v0.5h-6.5zM144.5 239h94.5v0.5h-94.5zM132.5 239.5h107v0.5h-107zM132 240h108v0.5h-108zM132 240.5h108.5v0.5h-108.5zM132 241h109v0.5h-109zM132 241.5h109.5v0.5h-109.5zM132.5 242h109.5v1h-109.5zM132.5 243h110v1h-110zM132.5 244h110.5v3h-110.5zM132 247h111v1.5h-111zM131.5 248.5h111v0.5h-111zM131 249h111.5v0.5h-111.5zM130.5 249.5h111.5v0.5h-111.5zM130 250h112v0.5h-112zM129.5 250.5h112v0.5h-112zM129.5 251h111.5v0.5h-111.5zM129.5 251.5h111v0.5h-111zM130 252h110v0.5h-110zM130 252.5h109.5v0.5h-109.5zM130.5 253h108.5v0.5h-108.5zM131 253.5h107.5v0.5h-107.5zM132 254h105.5v0.5h-105.5zM133.5 254.5h2v0.5h-2zM137 254.5h100v0.5h-100zM137.5 255h99v0.5h-99zM138.5 255.5h0.5v0.5h-0.5zM139.5 255.5h96.5v0.5h-96.5zM140 256h95.5v0.5h-95.5zM140.5 256.5h94.5v0.5h-94.5zM141 257h93.5v0.5h-93.5zM141 257.5h93v0.5h-93zM141 258h92.5v0.5h-92.5zM141 258.5h92v0.5h-92zM141.5 259h90.5v0.5h-90.5zM141.5 259.5h90v0.5h-90zM142 260h88.5v0.5h-88.5zM142 260.5h87.5v0.5h-87.5zM142.5 261h86v0.5h-86zM143.5 261.5h84v0.5h-84zM144.5 262h81.5v0.5h-81.5zM145.5 262.5h78.5v0.5h-78.5zM146 263h77.5v0.5h-77.5zM146.5 263.5h76v0.5h-76zM147 264h75v0.5h-75zM148 264.5h73v0.5h-73zM148.5 265h70.5v0.5h-70.5zM149 265.5h65.5v0.5h-65.5zM149.5 266h64v0.5h-64zM149 266.5h58.5v0.5h-58.5zM209 266.5h2v0.5h-2zM149 267h51.5v0.5h-51.5zM202 267h4.5v0.5h-4.5zM148.5 267.5h51.5v0.5h-51.5zM202.5 267.5h3v0.5h-3zM148 268h51.5v0.5h-51.5zM147.5 268.5h51.5v0.5h-51.5zM147 269h29.5v0.5h-29.5zM177 269h22v0.5h-22zM146.5 269.5h29.5v0.5h-29.5zM177.5 269.5h21v0.5h-21zM146 270h29v0.5h-29zM178 270h20.5v0.5h-20.5zM145.5 270.5h29v0.5h-29zM178.5 270.5h20v0.5h-20zM145 271h29v0.5h-29zM144.5 271.5h28.5v0.5h-28.5zM143.5 272h29v0.5h-29zM143 272.5h28.5v0.5h-28.5zM179 271h19.5v2h-19.5zM143 273h28v0.5h-28zM142.5 273.5h28v0.5h-28zM142.5 274h27v0.5h-27zM142 274.5h27v0.5h-27zM142 275h26v0.5h-26zM142 275.5h25.5v0.5h-25.5zM142 276h24.5v0.5h-24.5zM142 276.5h24v0.5h-24zM142 277h23.5v0.5h-23.5zM179 273h19v4.5h-19zM142 277.5h22.5v0.5h-22.5zM178.5 277.5h19.5v0.5h-19.5zM142 278h22v0.5h-22zM142 278.5h21.5v0.5h-21.5zM142 279h21v0.5h-21zM142.5 279.5h20v1h-20zM143 280.5h19.5v0.5h-19.5zM178.5 278h20v3h-20zM143.5 281h19v0.5h-19zM144 281.5h18.5v0.5h-18.5zM145 282h17.5v0.5h-17.5zM178.5 281h20.5v1.5h-20.5zM145.5 282.5h17v0.5h-17zM179 282.5h20v0.5h-20zM146.5 283h15.5v0.5h-15.5zM179 283h19.5v0.5h-19.5zM147.5 283.5h14.5v0.5h-14.5zM179.5 283.5h19v0.5h-19zM148.5 284h13v0.5h-13zM180 284h18.5v0.5h-18.5zM150 284.5h11v0.5h-11zM181 284.5h17v0.5h-17zM152 285h8v0.5h-8zM182 285h16v0.5h-16zM155 285.5h3v0.5h-3zM183 285.5h14.5v0.5h-14.5zM184.5 286h12.5v0.5h-12.5zM186 286.5h10v0.5h-10zM188.5 287h6.5v0.5h-6.5z', 'allowDelete': False},
    {'id': 'nabiping', 'name': '나비핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/nabiping.svg?v=2" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/nabiping.svg?v=2', 'outerPath': 'M152.5 12.5h6.5v0.5h-6.5zM150 13h11.5v0.5h-11.5zM148.5 13.5h15v0.5h-15zM147 14h18v0.5h-18zM146 14.5h20v0.5h-20zM145 15h22.5v0.5h-22.5zM144.5 15.5h24v0.5h-24zM143.5 16h26v0.5h-26zM143 16.5h27.5v0.5h-27.5zM142.5 17h29v0.5h-29zM142 17.5h30.5v0.5h-30.5zM141.5 18h31.5v0.5h-31.5zM141.5 18.5h32.5v0.5h-32.5zM141 19h33.5v0.5h-33.5zM140.5 19.5h35v0.5h-35zM140.5 20h35.5v0.5h-35.5zM140 20.5h36.5v0.5h-36.5zM140 21h37v0.5h-37zM140 21.5h37.5v0.5h-37.5zM139.5 22h39v0.5h-39zM139.5 22.5h39.5v0.5h-39.5zM139 23h40.5v0.5h-40.5zM138.5 23.5h41.5v0.5h-41.5zM138 24h42.5v0.5h-42.5zM136.5 24.5h44.5v0.5h-44.5zM134 25h47.5v0.5h-47.5zM132 25.5h50v0.5h-50zM130.5 26h51.5v0.5h-51.5zM129.5 26.5h53v0.5h-53zM128.5 27h54.5v0.5h-54.5zM127.5 27.5h56v0.5h-56zM127 28h57v0.5h-57zM126 28.5h58v0.5h-58zM125.5 29h59v0.5h-59zM125 29.5h60v0.5h-60zM124.5 30h61v0.5h-61zM124 30.5h61.5v0.5h-61.5zM124 31h62v0.5h-62zM123.5 31.5h63v0.5h-63zM123 32h63.5v0.5h-63.5zM123 32.5h64v0.5h-64zM122.5 33h64.5v0.5h-64.5zM122.5 33.5h65v0.5h-65zM122 34h66v1h-66zM122 35h66.5v0.5h-66.5zM121.5 35.5h67v0.5h-67zM121.5 36h67.5v1h-67.5zM121.5 37h68v1h-68zM121.5 38h68.5v1h-68.5zM121.5 39h69v1.5h-69zM121.5 40.5h69.5v1h-69.5zM121.5 41.5h70v1.5h-70zM200 42.5h3v0.5h-3zM199 43h5.5v0.5h-5.5zM122 43h70v1h-70zM198.5 43.5h7v0.5h-7zM122 44h70.5v0.5h-70.5zM198 44h8v0.5h-8zM122 44.5h71v0.5h-71zM197.5 44.5h9v0.5h-9zM122.5 45h71v0.5h-71zM197 45h10v0.5h-10zM122.5 45.5h72.5v0.5h-72.5zM196.5 45.5h12v0.5h-12zM122.5 46h87v0.5h-87zM123 46.5h87v0.5h-87zM123 47h87.5v0.5h-87.5zM122.5 47.5h88.5v0.5h-88.5zM225 47.5h7.5v0.5h-7.5zM122 48h89v0.5h-89zM220.5 48h15v0.5h-15zM121.5 48.5h90v0.5h-90zM218 48.5h19.5v0.5h-19.5zM121 49h91v0.5h-91zM216 49h23v0.5h-23zM120.5 49.5h92v0.5h-92zM215 49.5h25v0.5h-25zM120 50h93v0.5h-93zM214 50h27v0.5h-27zM119.5 50.5h122.5v0.5h-122.5zM119 51h124v0.5h-124zM118.5 51.5h125v0.5h-125zM118.5 52h125.5v0.5h-125.5zM118 52.5h126.5v0.5h-126.5zM118 53h127v0.5h-127zM117.5 53.5h128v0.5h-128zM117.5 54h128.5v0.5h-128.5zM117 54.5h129.5v1h-129.5zM117 55.5h130v0.5h-130zM117 56h130.5v0.5h-130.5zM116.5 56.5h131v0.5h-131zM116.5 57h131.5v1.5h-131.5zM116.5 58.5h132v2.5h-132zM117 61h132v2.5h-132zM117.5 63.5h131v1h-131zM118 64.5h130.5v1h-130.5zM118.5 65.5h130v0.5h-130zM119 66h129v1h-129zM119.5 67h128v0.5h-128zM120 67.5h127.5v0.5h-127.5zM120 68h127v0.5h-127zM119.5 68.5h127.5v0.5h-127.5zM119 69h127.5v0.5h-127.5zM118.5 69.5h127.5v0.5h-127.5zM117.5 70h129v0.5h-129zM116.5 70.5h130.5v0.5h-130.5zM116 71h131v0.5h-131zM115 71.5h132.5v0.5h-132.5zM114.5 72h133.5v0.5h-133.5zM113.5 72.5h134.5v0.5h-134.5zM113 73h135.5v0.5h-135.5zM112 73.5h137v0.5h-137zM111.5 74h137.5v0.5h-137.5zM111 74.5h138v0.5h-138zM110.5 75h139v0.5h-139zM109.5 75.5h140v0.5h-140zM109 76h141v0.5h-141zM108.5 76.5h141.5v0.5h-141.5zM108 77h142v0.5h-142zM107.5 77.5h142.5v0.5h-142.5zM107 78h143v0.5h-143zM106.5 78.5h144v0.5h-144zM106 79h144.5v0.5h-144.5zM105.5 79.5h145v0.5h-145zM105 80h145.5v0.5h-145.5zM104.5 80.5h146v0.5h-146zM104 81h146.5v0.5h-146.5zM103.5 81.5h147v0.5h-147zM103 82h147.5v0.5h-147.5zM102.5 82.5h148v0.5h-148zM102 83h148.5v1h-148.5zM101.5 84h148.5v0.5h-148.5zM101 84.5h149v0.5h-149zM100.5 85h149.5v0.5h-149.5zM100 85.5h149.5v0.5h-149.5zM99.5 86h150v1h-150zM99 87h150v0.5h-150zM98.5 87.5h150v0.5h-150zM98 88h150.5v0.5h-150.5zM98 88.5h150v0.5h-150zM97.5 89h150v0.5h-150zM97 89.5h150v0.5h-150zM97 90h149.5v0.5h-149.5zM96.5 90.5h149.5v0.5h-149.5zM96 91h149.5v0.5h-149.5zM96 91.5h149v0.5h-149zM95.5 92h149.5v0.5h-149.5zM95 92.5h150v1h-150zM94.5 93.5h150.5v1h-150.5zM94 94.5h151v0.5h-151zM93.5 95h151.5v1h-151.5zM93 96h152v1h-152zM92.5 97h152v1h-152zM92 98h152.5v0.5h-152.5zM92 98.5h152v0.5h-152zM91.5 99h152.5v0.5h-152.5zM91.5 99.5h152v0.5h-152zM91 100h152.5v1h-152.5zM90.5 101h153v0.5h-153zM90.5 101.5h153.5v0.5h-153.5zM90 102h154v1h-154zM90 103h154.5v0.5h-154.5zM89.5 103.5h155v1h-155zM89 104.5h155.5v0.5h-155.5zM89 105h156v1h-156zM88.5 106h156.5v1h-156.5zM88 107h157v0.5h-157zM88 107.5h157.5v1h-157.5zM87.5 108.5h158v1.5h-158zM87 110h158.5v1.5h-158.5zM86.5 111.5h159.5v2h-159.5zM86 113.5h159.5v1.5h-159.5zM85.5 115h160v2.5h-160zM85 117.5h160.5v0.5h-160.5zM85 118h160v2h-160zM84.5 120h160v2h-160zM84.5 122h159.5v1h-159.5zM84 123h160v1.5h-160zM84 124.5h159.5v2h-159.5zM84 126.5h160v0.5h-160zM83.5 127h160.5v0.5h-160.5zM83.5 127.5h161v0.5h-161zM83.5 128h161.5v1h-161.5zM63.5 129h8v0.5h-8zM62 129.5h11v0.5h-11zM83.5 129h162v1h-162zM61 130h13v0.5h-13zM60 130.5h15v0.5h-15zM83.5 130h162.5v1h-162.5zM59.5 131h16.5v0.5h-16.5zM83 131h163v0.5h-163zM58.5 131.5h18v0.5h-18zM58 132h19v0.5h-19zM57 132.5h21v0.5h-21zM56.5 133h22v0.5h-22zM56 133.5h23v0.5h-23zM83 131.5h163.5v2.5h-163.5zM55.5 134h24v0.5h-24zM83 134h164v0.5h-164zM55 134.5h25v0.5h-25zM82.5 134.5h164.5v0.5h-164.5zM55 135h25.5v0.5h-25.5zM82 135h165v0.5h-165zM54.5 135.5h26.5v0.5h-26.5zM81.5 135.5h165.5v0.5h-165.5zM54 136h193v0.5h-193zM53.5 136.5h193.5v1h-193.5zM53 137.5h194v0.5h-194zM52.5 138h194.5v0.5h-194.5zM52.5 138.5h194v0.5h-194zM52 139h194.5v1h-194.5zM51.5 140h195v1h-195zM51 141h195v1.5h-195zM50.5 142.5h195v1h-195zM50.5 143.5h194.5v0.5h-194.5zM50 144h195v0.5h-195zM50 144.5h194.5v1h-194.5zM50 145.5h194v0.5h-194zM49.5 146h194v1h-194zM49.5 147h193.5v0.5h-193.5zM49.5 147.5h193v0.5h-193zM49.5 148h192.5v0.5h-192.5zM49.5 148.5h192v0.5h-192zM49.5 149h191.5v0.5h-191.5zM49.5 149.5h191v0.5h-191zM49.5 150h190.5v0.5h-190.5zM49.5 150.5h189.5v0.5h-189.5zM49.5 151h189v0.5h-189zM49.5 151.5h188v0.5h-188zM49.5 152h187v0.5h-187zM49.5 152.5h186.5v0.5h-186.5zM49.5 153h186v0.5h-186zM49.5 153.5h185.5v1.5h-185.5zM50 155h184.5v1.5h-184.5zM50 156.5h184v0.5h-184zM50.5 157h183.5v1h-183.5zM50.5 158h183v1h-183zM51 159h182v1h-182zM51.5 160h181.5v0.5h-181.5zM51.5 160.5h181v0.5h-181zM52 161h180.5v0.5h-180.5zM52 161.5h180v0.5h-180zM52.5 162h179.5v0.5h-179.5zM52.5 162.5h179v0.5h-179zM53 163h178.5v0.5h-178.5zM53.5 163.5h177.5v0.5h-177.5zM53.5 164h177v0.5h-177zM54 164.5h176.5v0.5h-176.5zM54.5 165h175.5v0.5h-175.5zM55 165.5h175v0.5h-175zM55 166h174.5v0.5h-174.5zM55.5 166.5h173.5v0.5h-173.5zM56 167h173v0.5h-173zM56.5 167.5h172v0.5h-172zM57 168h171v0.5h-171zM57.5 168.5h170.5v0.5h-170.5zM58 169h169.5v0.5h-169.5zM58.5 169.5h168.5v0.5h-168.5zM59 170h167.5v0.5h-167.5zM59.5 170.5h166.5v0.5h-166.5zM60.5 171h165.5v0.5h-165.5zM61 171.5h164.5v0.5h-164.5zM61.5 172h163.5v0.5h-163.5zM62.5 172.5h162v0.5h-162zM63 173h161v0.5h-161zM64 173.5h159.5v0.5h-159.5zM65 174h158v0.5h-158zM66 174.5h156.5v0.5h-156.5zM67 175h155v0.5h-155zM68 175.5h153.5v0.5h-153.5zM69 176h152v0.5h-152zM70.5 176.5h150v0.5h-150zM72 177h148v0.5h-148zM74 177.5h145v0.5h-145zM76 178h16.5v0.5h-16.5zM93 178h125.5v0.5h-125.5zM79 178.5h11v0.5h-11zM93.5 178.5h124.5v0.5h-124.5zM88.5 179h1v0.5h-1zM94 179h123.5v0.5h-123.5zM94.5 179.5h122v0.5h-122zM94.5 180h121.5v0.5h-121.5zM94.5 180.5h121v0.5h-121zM95 181h120v0.5h-120zM89 181.5h1v0.5h-1zM94.5 181.5h120v0.5h-120zM88.5 182h3.5v0.5h-3.5zM94 182h120v0.5h-120zM88 182.5h5v0.5h-5zM93.5 182.5h120.5v0.5h-120.5zM88 183h125.5v1h-125.5zM87.5 184h125.5v0.5h-125.5zM87.5 184.5h125v1h-125zM87.5 185.5h125.5v0.5h-125.5zM87.5 186h126v0.5h-126zM88 186.5h126v0.5h-126zM88 187h132v0.5h-132zM88 187.5h133.5v0.5h-133.5zM88 188h135v0.5h-135zM88.5 188.5h135.5v0.5h-135.5zM88.5 189h136.5v0.5h-136.5zM88.5 189.5h137v0.5h-137zM89 190h137v0.5h-137zM89.5 190.5h137v0.5h-137zM89.5 191h137.5v0.5h-137.5zM90 191.5h137.5v0.5h-137.5zM90.5 192h137.5v0.5h-137.5zM91 192.5h137.5v0.5h-137.5zM91.5 193h137v0.5h-137zM91.5 193.5h137.5v0.5h-137.5zM91 194h138.5v1h-138.5zM90.5 195h139.5v2h-139.5zM90.5 197h140v0.5h-140zM91 197.5h139.5v1h-139.5zM91.5 198.5h139v1h-139zM92 199.5h138.5v1h-138.5zM92.5 200.5h138v0.5h-138zM93 201h137.5v0.5h-137.5zM93.5 201.5h137v0.5h-137zM94 202h136.5v0.5h-136.5zM94.5 202.5h136v0.5h-136zM95 203h135.5v0.5h-135.5zM95.5 203.5h135v0.5h-135zM96.5 204h134v0.5h-134zM97 204.5h133.5v0.5h-133.5zM98 205h132v0.5h-132zM99 205.5h131v0.5h-131zM99.5 206h130.5v0.5h-130.5zM100 206.5h130v0.5h-130zM100.5 207h129v0.5h-129zM101 207.5h128.5v0.5h-128.5zM100.5 208h128.5v0.5h-128.5zM100 208.5h129v0.5h-129zM99.5 209h129.5v0.5h-129.5zM99.5 209.5h129v0.5h-129zM99 210h129.5v0.5h-129.5zM98.5 210.5h129.5v1h-129.5zM98 211.5h129.5v1h-129.5zM98 212.5h129v0.5h-129zM97.5 213h129v1h-129zM97.5 214h128.5v0.5h-128.5zM98 214.5h127.5v0.5h-127.5zM98 215h127v0.5h-127zM98.5 215.5h126.5v0.5h-126.5zM98.5 216h126v0.5h-126zM98 216.5h126v0.5h-126zM97.5 217h82v0.5h-82zM180.5 217h43v0.5h-43zM97 217.5h17v0.5h-17zM114.5 217.5h64v0.5h-64zM181.5 217.5h41.5v0.5h-41.5zM96.5 218h16v0.5h-16zM115 218h63v0.5h-63zM182 218h40.5v0.5h-40.5zM96.5 218.5h15v0.5h-15zM115.5 218.5h60.5v0.5h-60.5zM183 218.5h39v0.5h-39zM96 219h14v0.5h-14zM116 219h59.5v0.5h-59.5zM184 219h37v0.5h-37zM96 219.5h13v0.5h-13zM116 219.5h59v0.5h-59zM184.5 219.5h36v0.5h-36zM96 220h11.5v0.5h-11.5zM116 220h58.5v0.5h-58.5zM185.5 220h34v0.5h-34zM96 220.5h9.5v0.5h-9.5zM116 220.5h59v0.5h-59zM186.5 220.5h32.5v0.5h-32.5zM96.5 221h7v0.5h-7zM116 221h59.5v0.5h-59.5zM187.5 221h30.5v0.5h-30.5zM98 221.5h2v0.5h-2zM116 221.5h60v0.5h-60zM189 221.5h28v0.5h-28zM115.5 222h61.5v0.5h-61.5zM190 222h26v0.5h-26zM115.5 222.5h62.5v0.5h-62.5zM191.5 222.5h23.5v0.5h-23.5zM115 223h64v0.5h-64zM193.5 223h20v0.5h-20zM114.5 223.5h65.5v0.5h-65.5zM195.5 223.5h16.5v0.5h-16.5zM114.5 224h67v0.5h-67zM198 224h11.5v0.5h-11.5zM114.5 224.5h68.5v0.5h-68.5zM114.5 225h70.5v0.5h-70.5zM114.5 225.5h72.5v0.5h-72.5zM114.5 226h73v0.5h-73zM115 226.5h73.5v0.5h-73.5zM193 226.5h0.5v0.5h-0.5zM115.5 227h79v0.5h-79zM116 227.5h79.5v1h-79.5zM116 228.5h80v0.5h-80zM115.5 229h81v3h-81zM115.5 232h80.5v1h-80.5zM115 233h80.5v0.5h-80.5zM115 233.5h80v0.5h-80zM115 234h80.5v0.5h-80.5zM115 234.5h81v0.5h-81zM115 235h81.5v0.5h-81.5zM115 235.5h82v0.5h-82zM114.5 236h83.5v0.5h-83.5zM114.5 236.5h84v0.5h-84zM114.5 237h84.5v0.5h-84.5zM114.5 237.5h85v0.5h-85zM114 238h86v1h-86zM114 239h86.5v1h-86.5zM113.5 240h87v0.5h-87zM113.5 240.5h87.5v2h-87.5zM113 242.5h88v1.5h-88zM112.5 244h88.5v1.5h-88.5zM112 245.5h89v1h-89zM111.5 246.5h89.5v1h-89.5zM111 247.5h89.5v1h-89.5zM110.5 248.5h90v0.5h-90zM110 249h90.5v0.5h-90.5zM109.5 249.5h90.5v0.5h-90.5zM109 250h91v0.5h-91zM108.5 250.5h91.5v0.5h-91.5zM107.5 251h92.5v0.5h-92.5zM107 251.5h92.5v0.5h-92.5zM106 252h93.5v0.5h-93.5zM105.5 252.5h93.5v0.5h-93.5zM104.5 253h94.5v0.5h-94.5zM103.5 253.5h95.5v0.5h-95.5zM102 254h96.5v0.5h-96.5zM100.5 254.5h98v0.5h-98zM99.5 255h72.5v0.5h-72.5zM178 255h20v0.5h-20zM97.5 255.5h72.5v0.5h-72.5zM180.5 255.5h17v0.5h-17zM96 256h72.5v0.5h-72.5zM182.5 256h15v0.5h-15zM94.5 256.5h73v0.5h-73zM184.5 256.5h12.5v0.5h-12.5zM93.5 257h72.5v0.5h-72.5zM186 257h10.5v0.5h-10.5zM93 257.5h72v0.5h-72zM187 257.5h9.5v0.5h-9.5zM93 258h71v0.5h-71zM187.5 258h8.5v0.5h-8.5zM92.5 258.5h70.5v0.5h-70.5zM188.5 258.5h6.5v0.5h-6.5zM92.5 259h69.5v0.5h-69.5zM190 259h4.5v0.5h-4.5zM92.5 259.5h68.5v0.5h-68.5zM93 260h67v0.5h-67zM93 260.5h66.5v0.5h-66.5zM93.5 261h65v0.5h-65zM94 261.5h63.5v0.5h-63.5zM94.5 262h62.5v0.5h-62.5zM95 262.5h61.5v0.5h-61.5zM96 263h60v0.5h-60zM97 263.5h58.5v0.5h-58.5zM98 264h57v0.5h-57zM98.5 264.5h56v0.5h-56zM99 265h55v0.5h-55zM99.5 265.5h54.5v0.5h-54.5zM100 266h54v0.5h-54zM100.5 266.5h53.5v0.5h-53.5zM101.5 267h53v0.5h-53zM103.5 267.5h51v0.5h-51zM104.5 268h50v0.5h-50zM105 268.5h28v0.5h-28zM134 268.5h20.5v0.5h-20.5zM107 269h2v0.5h-2zM109.5 269h22v0.5h-22zM134.5 269h20.5v0.5h-20.5zM111 269.5h11.5v0.5h-11.5zM127.5 269.5h1v0.5h-1zM135 269.5h20v0.5h-20zM115.5 270h6v0.5h-6zM135.5 270h20v0.5h-20zM136 270.5h20v0.5h-20zM136 271h20.5v0.5h-20.5zM136.5 271.5h20.5v1h-20.5zM137 272.5h20v1h-20zM137.5 273.5h20v1h-20zM138 274.5h20v1h-20zM138.5 275.5h19.5v0.5h-19.5zM138.5 276h20v0.5h-20zM139 276.5h19.5v2.5h-19.5zM139.5 279h19v1.5h-19zM140 280.5h18.5v0.5h-18.5zM140 281h18v0.5h-18zM140.5 281.5h17.5v0.5h-17.5zM141 282h17v0.5h-17zM141.5 282.5h16v0.5h-16zM142 283h15v0.5h-15zM142.5 283.5h14.5v0.5h-14.5zM143 284h13.5v0.5h-13.5zM144 284.5h11.5v0.5h-11.5zM145 285h10v0.5h-10zM146.5 285.5h7.5v0.5h-7.5zM148.5 286h3.5v0.5h-3.5z', 'allowDelete': False},
    {'id': 'silkping', 'name': '실크핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/silkping.svg?v=2" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/silkping.svg?v=2', 'outerPath': 'M144 12h3v0.5h-3zM143 12.5h5v0.5h-5zM142.5 13h6v0.5h-6zM139 13.5h10v0.5h-10zM138 14h11.5v0.5h-11.5zM137.5 14.5h12v0.5h-12zM137 15h12.5v1h-12.5zM137 16h13v0.5h-13zM136.5 16.5h13.5v0.5h-13.5zM136.5 17h13v1.5h-13zM137 18.5h12.5v0.5h-12.5zM137 19h12v0.5h-12zM137.5 19.5h11v1h-11zM138 20.5h10v0.5h-10zM138.5 21h9v0.5h-9zM139 21.5h8.5v0.5h-8.5zM140 22h7.5v0.5h-7.5zM161 22h1v0.5h-1zM141 22.5h6.5v0.5h-6.5zM160.5 22.5h2.5v0.5h-2.5zM141.5 23h6.5v0.5h-6.5zM160 23h3v0.5h-3zM142 23.5h6.5v0.5h-6.5zM142.5 24h6v0.5h-6zM159.5 23.5h4v1.5h-4zM143 24.5h6v1h-6zM159.5 25h3.5v0.5h-3.5zM143.5 25.5h6v0.5h-6zM160 25.5h3.5v0.5h-3.5zM143.5 26h6.5v1h-6.5zM159.5 26h4v1h-4zM143.5 27h7v0.5h-7zM143.5 27.5h7.5v0.5h-7.5zM159.5 27h4.5v1h-4.5zM143.5 28h8v1h-8zM159.5 28h5v1h-5zM143.5 29h8.5v0.5h-8.5zM169 29h1.5v0.5h-1.5zM159.5 29h5.5v1h-5.5zM168.5 29.5h2.5v0.5h-2.5zM143.5 29.5h9v1h-9zM159.5 30h6v0.5h-6zM168 30h3.5v0.5h-3.5zM143.5 30.5h9.5v0.5h-9.5zM159 30.5h7v0.5h-7zM167.5 30.5h4v0.5h-4zM143.5 31h10v0.5h-10zM159 31h7.5v0.5h-7.5zM167 31h4.5v0.5h-4.5zM129.5 31.5h2.5v0.5h-2.5zM143.5 31.5h10.5v0.5h-10.5zM143.5 32h11v0.5h-11zM129 32h3.5v1h-3.5zM143 32.5h11.5v0.5h-11.5zM159 31.5h12.5v1.5h-12.5zM129 33h4v0.5h-4zM143 33h12v0.5h-12zM158.5 33h13v0.5h-13zM129 33.5h4.5v0.5h-4.5zM143 33.5h12.5v0.5h-12.5zM158 33.5h14v0.5h-14zM129 34h5v0.5h-5zM143 34h13v0.5h-13zM157.5 34h14.5v0.5h-14.5zM129.5 34.5h5v0.5h-5zM143 34.5h13.5v0.5h-13.5zM157 34.5h15.5v0.5h-15.5zM130 35h5v0.5h-5zM143 35h30v0.5h-30zM130 35.5h5.5v0.5h-5.5zM142.5 35.5h31v0.5h-31zM130.5 36h6v0.5h-6zM142 36h33v0.5h-33zM130.5 36.5h6.5v0.5h-6.5zM141.5 36.5h36.5v0.5h-36.5zM130.5 37h7.5v0.5h-7.5zM139.5 37h41v0.5h-41zM130.5 37.5h52v0.5h-52zM130.5 38h54v0.5h-54zM130.5 38.5h55.5v0.5h-55.5zM130 39h57.5v0.5h-57.5zM129.5 39.5h59.5v0.5h-59.5zM129 40h61v0.5h-61zM127.5 40.5h64v0.5h-64zM126 41h66.5v0.5h-66.5zM124.5 41.5h69v0.5h-69zM121 42h1.5v0.5h-1.5zM123.5 42h71v0.5h-71zM120.5 42.5h75v0.5h-75zM120 43h77v0.5h-77zM119.5 43.5h78.5v0.5h-78.5zM119 44h80v0.5h-80zM118 44.5h86v0.5h-86zM117 45h89v0.5h-89zM116.5 45.5h90.5v0.5h-90.5zM115.5 46h93v0.5h-93zM114.5 46.5h94.5v0.5h-94.5zM113.5 47h96.5v0.5h-96.5zM113 47.5h97.5v0.5h-97.5zM112 48h99.5v0.5h-99.5zM111.5 48.5h100.5v0.5h-100.5zM110.5 49h102v0.5h-102zM109.5 49.5h103.5v0.5h-103.5zM109 50h104.5v0.5h-104.5zM108.5 50.5h105.5v0.5h-105.5zM107.5 51h107v0.5h-107zM107 51.5h107.5v0.5h-107.5zM106 52h109v0.5h-109zM105.5 52.5h110v0.5h-110zM105 53h111v0.5h-111zM104.5 53.5h111.5v0.5h-111.5zM103.5 54h113v0.5h-113zM103 54.5h113.5v0.5h-113.5zM102.5 55h114.5v0.5h-114.5zM102 55.5h115.5v0.5h-115.5zM101.5 56h116.5v0.5h-116.5zM101 56.5h118.5v0.5h-118.5zM100 57h120.5v0.5h-120.5zM99.5 57.5h122v0.5h-122zM99 58h123.5v0.5h-123.5zM98.5 58.5h124.5v0.5h-124.5zM98 59h125.5v0.5h-125.5zM97.5 59.5h127v0.5h-127zM97 60h128v0.5h-128zM96.5 60.5h129v0.5h-129zM96 61h129.5v0.5h-129.5zM96 61.5h130v0.5h-130zM95.5 62h131v0.5h-131zM95 62.5h132v0.5h-132zM94.5 63h132.5v0.5h-132.5zM94 63.5h133v0.5h-133zM93.5 64h134v0.5h-134zM93 64.5h134.5v1h-134.5zM92.5 65.5h135.5v0.5h-135.5zM92 66h136v0.5h-136zM91.5 66.5h136.5v1h-136.5zM91 67.5h136.5v0.5h-136.5zM90.5 68h137.5v0.5h-137.5zM90 68.5h138.5v0.5h-138.5zM90 69h139v0.5h-139zM89.5 69.5h140v0.5h-140zM89 70h141v0.5h-141zM89 70.5h141.5v0.5h-141.5zM88.5 71h142.5v1h-142.5zM88 72h143.5v0.5h-143.5zM87.5 72.5h144v0.5h-144zM87.5 73h144.5v0.5h-144.5zM87 73.5h145v0.5h-145zM87 74h145.5v0.5h-145.5zM86.5 74.5h146v1h-146zM86 75.5h146.5v1h-146.5zM85.5 76.5h147v1h-147zM85 77.5h147.5v1h-147.5zM84.5 78.5h148v0.5h-148zM84.5 79h147.5v0.5h-147.5zM84 79.5h148v1h-148zM83.5 80.5h148v0.5h-148zM83.5 81h147.5v1h-147.5zM83 82h148.5v0.5h-148.5zM83 82.5h149v0.5h-149zM82.5 83h149.5v0.5h-149.5zM82.5 83.5h150v0.5h-150zM82.5 84h150.5v0.5h-150.5zM82 84.5h151v0.5h-151zM82 85h151.5v1h-151.5zM81.5 86h152v0.5h-152zM81.5 86.5h152.5v1h-152.5zM81 87.5h153v2h-153zM80.5 89.5h153.5v1h-153.5zM80.5 90.5h153v0.5h-153zM80 91h153.5v0.5h-153.5zM80 91.5h153v1h-153zM80 92.5h152.5v0.5h-152.5zM79.5 93h152.5v0.5h-152.5zM79.5 93.5h152v0.5h-152zM79.5 94h151.5v0.5h-151.5zM79.5 94.5h152v0.5h-152zM79 95h152.5v2.5h-152.5zM78.5 97.5h153.5v3h-153.5zM78 100.5h154v1h-154zM78 101.5h154.5v3h-154.5zM77.5 104.5h155v3h-155zM77.5 107.5h155.5v5.5h-155.5zM77 113h156v2.5h-156zM76.5 115.5h156.5v0.5h-156.5zM76.5 116h156v2.5h-156zM76.5 118.5h156.5v0.5h-156.5zM76 119h157.5v0.5h-157.5zM76 119.5h158v1h-158zM76 120.5h158.5v0.5h-158.5zM76 121h159v0.5h-159zM76 121.5h159.5v0.5h-159.5zM75.5 122h160.5v0.5h-160.5zM75 122.5h161.5v0.5h-161.5zM75 123h162v0.5h-162zM74.5 123.5h163v0.5h-163zM74.5 124h163.5v0.5h-163.5zM74 124.5h164.5v0.5h-164.5zM74 125h165v0.5h-165zM73.5 125.5h166v0.5h-166zM73.5 126h166.5v0.5h-166.5zM73 126.5h167.5v0.5h-167.5zM73 127h168v0.5h-168zM72.5 127.5h168.5v0.5h-168.5zM72.5 128h169v0.5h-169zM72.5 128.5h169.5v0.5h-169.5zM72.5 129h170v0.5h-170zM72 129.5h171v0.5h-171zM72 130h171.5v0.5h-171.5zM72 130.5h172v1h-172zM72 131.5h172.5v0.5h-172.5zM71.5 132h173.5v0.5h-173.5zM71.5 132.5h174v1h-174zM71.5 133.5h174.5v0.5h-174.5zM71.5 134h175v0.5h-175zM72 134.5h174.5v0.5h-174.5zM72 135h175v0.5h-175zM72 135.5h175.5v1h-175.5zM72 136.5h176v0.5h-176zM72.5 137h175.5v0.5h-175.5zM72.5 137.5h176v0.5h-176zM72.5 138h176.5v0.5h-176.5zM73 138.5h176v0.5h-176zM73 139h176.5v0.5h-176.5zM73.5 139.5h176v0.5h-176zM74 140h176v1h-176zM74.5 141h175.5v0.5h-175.5zM75 141.5h175.5v1h-175.5zM75 142.5h176v1h-176zM75.5 143.5h175.5v1h-175.5zM75.5 144.5h176v0.5h-176zM76 145h175.5v1.5h-175.5zM76.5 146.5h175.5v0.5h-175.5zM77 147h175v0.5h-175zM77.5 147.5h174.5v0.5h-174.5zM78 148h174v0.5h-174zM78.5 148.5h173.5v0.5h-173.5zM79 149h173v3.5h-173zM79.5 152.5h172.5v1.5h-172.5zM80 154h172v1h-172zM80.5 155h171.5v0.5h-171.5zM81 155.5h170.5v0.5h-170.5zM81.5 156h170v1h-170zM82 157h169.5v0.5h-169.5zM83 157.5h168.5v0.5h-168.5zM83.5 158h167.5v0.5h-167.5zM84 158.5h167v0.5h-167zM84.5 159h166.5v0.5h-166.5zM84.5 159.5h166v1.5h-166zM84.5 161h165.5v1.5h-165.5zM84.5 162.5h165v1h-165zM85 163.5h164v1.5h-164zM85 165h163.5v1h-163.5zM85 166h163v0.5h-163zM84.5 166.5h163.5v0.5h-163.5zM84.5 167h163v1h-163zM84.5 168h162.5v0.5h-162.5zM84.5 168.5h162v1h-162zM84.5 169.5h161.5v0.5h-161.5zM84 170h162v0.5h-162zM84 170.5h161.5v1h-161.5zM83.5 171.5h161.5v1h-161.5zM83 172.5h161.5v0.5h-161.5zM82.5 173h162v0.5h-162zM82 173.5h162.5v0.5h-162.5zM81.5 174h163v0.5h-163zM81 174.5h163v0.5h-163zM80.5 175h163.5v0.5h-163.5zM80 175.5h164v0.5h-164zM79.5 176h164.5v0.5h-164.5zM79 176.5h165v0.5h-165zM78.5 177h165.5v0.5h-165.5zM78 177.5h166v0.5h-166zM77 178h167v0.5h-167zM76.5 178.5h167.5v0.5h-167.5zM76 179h168v0.5h-168zM75.5 179.5h169v0.5h-169zM75 180h169.5v0.5h-169.5zM74.5 180.5h170v0.5h-170zM74 181h170.5v0.5h-170.5zM73.5 181.5h171.5v0.5h-171.5zM73 182h172v0.5h-172zM72.5 182.5h172.5v0.5h-172.5zM72.5 183h173v0.5h-173zM72 183.5h174v0.5h-174zM71.5 184h174.5v0.5h-174.5zM71 184.5h175.5v0.5h-175.5zM71 185h176v0.5h-176zM70.5 185.5h177v0.5h-177zM70.5 186h177.5v0.5h-177.5zM70 186.5h178.5v0.5h-178.5zM70 187h179v0.5h-179zM69.5 187.5h180v0.5h-180zM69.5 188h180.5v0.5h-180.5zM69.5 188.5h181v0.5h-181zM69 189h182v0.5h-182zM69 189.5h182.5v0.5h-182.5zM69 190h183v0.5h-183zM68.5 190.5h183.5v0.5h-183.5zM68.5 191h184v0.5h-184zM68.5 191.5h184.5v0.5h-184.5zM68.5 192h185v1h-185zM68 193h186v0.5h-186zM68 193.5h186.5v1h-186.5zM68 194.5h187v1h-187zM68 195.5h187.5v1.5h-187.5zM68 197h188v1.5h-188zM68.5 198.5h188v2.5h-188zM69 201h188v1.5h-188zM69.5 202.5h187.5v1.5h-187.5zM70 204h187v1h-187zM70 205h186.5v0.5h-186.5zM70.5 205.5h186v1h-186zM71 206.5h185.5v1h-185.5zM71.5 207.5h184.5v1h-184.5zM72 208.5h184v0.5h-184zM72 209h183.5v0.5h-183.5zM72.5 209.5h183v0.5h-183zM72.5 210h182.5v0.5h-182.5zM73 210.5h182v0.5h-182zM73 211h181.5v1h-181.5zM73.5 212h180.5v0.5h-180.5zM73.5 212.5h180v0.5h-180zM74 213h179v0.5h-179zM74 213.5h178.5v0.5h-178.5zM74.5 214h177.5v0.5h-177.5zM74.5 214.5h177v0.5h-177zM74.5 215h176.5v0.5h-176.5zM75 215.5h175.5v0.5h-175.5zM74.5 216h175v0.5h-175zM74 216.5h174.5v0.5h-174.5zM73.5 217h174v0.5h-174zM66 217.5h180.5v0.5h-180.5zM63 218h182v0.5h-182zM61.5 218.5h181.5v0.5h-181.5zM60 219h179v0.5h-179zM59 219.5h176v0.5h-176zM58 220h176.5v0.5h-176.5zM57 220.5h177v0.5h-177zM56.5 221h177v0.5h-177zM55.5 221.5h178v0.5h-178zM55 222h178.5v0.5h-178.5zM54.5 222.5h179v0.5h-179zM54 223h179.5v0.5h-179.5zM53 223.5h180v0.5h-180zM52.5 224h180.5v0.5h-180.5zM52 224.5h181v0.5h-181zM51.5 225h181v0.5h-181zM51 225.5h181.5v0.5h-181.5zM50.5 226h181.5v1h-181.5zM50 227h181.5v0.5h-181.5zM49.5 227.5h181.5v0.5h-181.5zM49 228h181.5v0.5h-181.5zM48.5 228.5h181.5v0.5h-181.5zM48.5 229h181v0.5h-181zM48 229.5h180.5v0.5h-180.5zM47.5 230h180.5v0.5h-180.5zM47.5 230.5h179.5v0.5h-179.5zM47 231h179.5v0.5h-179.5zM46.5 231.5h179.5v0.5h-179.5zM46.5 232h179v0.5h-179zM46 232.5h179.5v1h-179.5zM45.5 233.5h180.5v1h-180.5zM45 234.5h181v0.5h-181zM45 235h181.5v1h-181.5zM44.5 236h182.5v1.5h-182.5zM44 237.5h183.5v2h-183.5zM43.5 239.5h184.5v2h-184.5zM43.5 241.5h185v1h-185zM43 242.5h185.5v2h-185.5zM43 244.5h186v1.5h-186zM43 246h186.5v0.5h-186.5zM43.5 246.5h186v0.5h-186zM43.5 247h186.5v1h-186.5zM43.5 248h187v0.5h-187zM43.5 248.5h187.5v1h-187.5zM44 249.5h187.5v1h-187.5zM44 250.5h188v0.5h-188zM44.5 251h187.5v0.5h-187.5zM44.5 251.5h188v1h-188zM45 252.5h188v0.5h-188zM45 253h188.5v0.5h-188.5zM45.5 253.5h188v0.5h-188zM45.5 254h188.5v0.5h-188.5zM46 254.5h188v0.5h-188zM46 255h188.5v0.5h-188.5zM46.5 255.5h188v0.5h-188zM46.5 256h188.5v0.5h-188.5zM47 256.5h188v0.5h-188zM47.5 257h187.5v0.5h-187.5zM47.5 257.5h187v0.5h-187zM48 258h186v0.5h-186zM48.5 258.5h183.5v0.5h-183.5zM49 259h182.5v0.5h-182.5zM49.5 259.5h181.5v0.5h-181.5zM50 260h180.5v0.5h-180.5zM50.5 260.5h179v0.5h-179zM51 261h88v0.5h-88zM141 261h87.5v0.5h-87.5zM51.5 261.5h86v0.5h-86zM142 261.5h82.5v0.5h-82.5zM52 262h84v0.5h-84zM142.5 262h81.5v0.5h-81.5zM52.5 262.5h30v0.5h-30zM84 262.5h51v0.5h-51zM143.5 262.5h79.5v0.5h-79.5zM53 263h29v0.5h-29zM84.5 263h49v0.5h-49zM144 263h78v0.5h-78zM54 263.5h27v0.5h-27zM85 263.5h47.5v0.5h-47.5zM145.5 263.5h75.5v0.5h-75.5zM54.5 264h26v0.5h-26zM85.5 264h46v0.5h-46zM149.5 264h71v0.5h-71zM55.5 264.5h24v0.5h-24zM85.5 264.5h45v0.5h-45zM150 264.5h32.5v0.5h-32.5zM183 264.5h37v0.5h-37zM56.5 265h22v0.5h-22zM86 265h43v0.5h-43zM150.5 265h31.5v0.5h-31.5zM183.5 265h36v0.5h-36zM57.5 265.5h20v0.5h-20zM86.5 265.5h41.5v0.5h-41.5zM151 265.5h30.5v0.5h-30.5zM184.5 265.5h34.5v0.5h-34.5zM58.5 266h18v0.5h-18zM87 266h40v0.5h-40zM150.5 266h30.5v0.5h-30.5zM185.5 266h33v0.5h-33zM60 266.5h15v0.5h-15zM87.5 266.5h38.5v0.5h-38.5zM150.5 266.5h29.5v0.5h-29.5zM186.5 266.5h31.5v0.5h-31.5zM62 267h11v0.5h-11zM88 267h37v0.5h-37zM150 267h29.5v0.5h-29.5zM187.5 267h30v0.5h-30zM64.5 267.5h6v0.5h-6zM88.5 267.5h35.5v0.5h-35.5zM150 267.5h28.5v0.5h-28.5zM188 267.5h29v0.5h-29zM89 268h34v0.5h-34zM150 268h27.5v0.5h-27.5zM188.5 268h28v0.5h-28zM89.5 268.5h32v0.5h-32zM150 268.5h26.5v0.5h-26.5zM189 268.5h21.5v0.5h-21.5zM213.5 268.5h2v0.5h-2zM90.5 269h30v0.5h-30zM149.5 269h26v0.5h-26zM189.5 269h20.5v0.5h-20.5zM91 269.5h28v0.5h-28zM149.5 269.5h24.5v0.5h-24.5zM189.5 269.5h20v0.5h-20zM92 270h26v0.5h-26zM149.5 270h23.5v0.5h-23.5zM189.5 270h19.5v0.5h-19.5zM93 270.5h23.5v0.5h-23.5zM149.5 270.5h23v0.5h-23zM189 270.5h20v0.5h-20zM94.5 271h20.5v0.5h-20.5zM149.5 271h22.5v0.5h-22.5zM96 271.5h17v0.5h-17zM149 271.5h22.5v0.5h-22.5zM97.5 272h13.5v0.5h-13.5zM189 271h19.5v1.5h-19.5zM101.5 272.5h5.5v0.5h-5.5zM149 272h22v1h-22zM188.5 272.5h20v1h-20zM149 273h21.5v1.5h-21.5zM149 274.5h21v1h-21zM188.5 273.5h19.5v2h-19.5zM188 275.5h20v0.5h-20zM148.5 275.5h21v1.5h-21zM188 276h19.5v3h-19.5zM148 277h21v2.5h-21zM148 279.5h21.5v0.5h-21.5zM187.5 279h20v1h-20zM148.5 280h21v1h-21zM187.5 280h20.5v1h-20.5zM149 281h20.5v0.5h-20.5zM149.5 281.5h20v0.5h-20zM187.5 281h21v1h-21zM150 282h19v0.5h-19zM151 282.5h18v0.5h-18zM188 282h20.5v1h-20.5zM151.5 283h17.5v0.5h-17.5zM188.5 283h20v0.5h-20zM152.5 283.5h16v0.5h-16zM189 283.5h19.5v0.5h-19.5zM153.5 284h15v0.5h-15zM189.5 284h19v0.5h-19zM154.5 284.5h13.5v0.5h-13.5zM190 284.5h18.5v0.5h-18.5zM156 285h11v0.5h-11zM191 285h17v0.5h-17zM158 285.5h8v0.5h-8zM192 285.5h15.5v0.5h-15.5zM193.5 286h13.5v0.5h-13.5zM195.5 286.5h10.5v0.5h-10.5zM198.5 287h5v0.5h-5z', 'allowDelete': False},
    # Permanent character worksheets. Shared across devices; never removable by the child.
    {'id': 'sappunping', 'name': '사뿐핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/sappunping.svg" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/sappunping.svg', 'outerPath': 'M206.5 10h0.5v.5h-0.5zM206 10.5h1v.5h-1zM206 11h1v.5h-1zM131 11.5h0.5v.5h-0.5zM206 11.5h1v.5h-1zM130 12h2.5v.5h-2.5zM205.5 12h1.5v.5h-1.5zM129.5 12.5h3.5v.5h-3.5zM205.5 12.5h1.5v.5h-1.5zM129 13h4v.5h-4zM205 13h2.5v.5h-2.5zM128.5 13.5h4.5v.5h-4.5zM205 13.5h2.5v.5h-2.5zM128 14h5.5v.5h-5.5zM204.5 14h3v.5h-3zM128 14.5h5.5v.5h-5.5zM204.5 14.5h3v.5h-3zM127.5 15h6v.5h-6zM204 15h3.5v.5h-3.5zM127 15.5h7v.5h-7zM204 15.5h3.5v.5h-3.5zM126.5 16h7.5v.5h-7.5zM204 16h3.5v.5h-3.5zM126 16.5h8v.5h-8zM203.5 16.5h4v.5h-4zM125.5 17h9v.5h-9zM203.5 17h4v.5h-4zM125 17.5h9.5v.5h-9.5zM203.5 17.5h4v.5h-4zM124.5 18h10v.5h-10zM203 18h4.5v.5h-4.5zM124 18.5h11v.5h-11zM203 18.5h4.5v.5h-4.5zM123 19h12v.5h-12zM203 19h4.5v.5h-4.5zM122.5 19.5h12.5v.5h-12.5zM203 19.5h4.5v.5h-4.5zM122.5 20h13v.5h-13zM203 20h4.5v.5h-4.5zM122 20.5h14v.5h-14zM203 20.5h4.5v.5h-4.5zM122 21h14.5v.5h-14.5zM203.5 21h4v.5h-4zM122 21.5h14.5v.5h-14.5zM203.5 21.5h4v.5h-4zM122 22h15v.5h-15zM203.5 22h4v.5h-4zM122.5 22.5h14.5v.5h-14.5zM204 22.5h3.5v.5h-3.5zM117 23h2v.5h-2zM122 23h15v.5h-15zM204.5 23h3v.5h-3zM114.5 23.5h6.5v.5h-6.5zM121.5 23.5h15.5v.5h-15.5zM205 23.5h2.5v.5h-2.5zM113.5 24h23v.5h-23zM205.5 24h2v.5h-2zM112.5 24.5h24.5v.5h-24.5zM111.5 25h26v.5h-26zM111 25.5h30v.5h-30zM110.5 26h32v.5h-32zM110 26.5h33.5v.5h-33.5zM109.5 27h35v.5h-35zM109 27.5h36v.5h-36zM109 28h36.5v.5h-36.5zM108.5 28.5h37.5v.5h-37.5zM108.5 29h38v.5h-38zM108 29.5h38.5v.5h-38.5zM108 30h39v.5h-39zM108 30.5h39.5v.5h-39.5zM107.5 31h40v.5h-40zM107.5 31.5h40v.5h-40zM107.5 32h40.5v.5h-40.5zM107 32.5h41v.5h-41zM102.5 33h3.5v.5h-3.5zM106.5 33h41.5v.5h-41.5zM101.5 33.5h46.5v.5h-46.5zM101 34h47v.5h-47zM100.5 34.5h47.5v.5h-47.5zM100 35h48v.5h-48zM99.5 35.5h48.5v.5h-48.5zM99.5 36h48.5v.5h-48.5zM99 36.5h49.5v.5h-49.5zM98.5 37h50.5v.5h-50.5zM98.5 37.5h54.5v.5h-54.5zM98.5 38h55v.5h-55zM98 38.5h56.5v.5h-56.5zM98 39h57v.5h-57zM97.5 39.5h58v.5h-58zM97 40h59v.5h-59zM95 40.5h61.5v.5h-61.5zM94 41h62.5v.5h-62.5zM93.5 41.5h63.5v.5h-63.5zM93 42h64v.5h-64zM92.5 42.5h64.5v.5h-64.5zM92.5 43h65v.5h-65zM92 43.5h65.5v.5h-65.5zM92 44h65.5v.5h-65.5zM92 44.5h65.5v.5h-65.5zM91.5 45h66v.5h-66zM91 45.5h66.5v.5h-66.5zM90 46h67.5v.5h-67.5zM90 46.5h68v.5h-68zM89.5 47h69v.5h-69zM89 47.5h71.5v.5h-71.5zM89 48h72.5v.5h-72.5zM89 48.5h73v.5h-73zM89 49h73.5v.5h-73.5zM89 49.5h73.5v.5h-73.5zM89 50h74v.5h-74zM89 50.5h74v.5h-74zM89.5 51h74v.5h-74zM89.5 51.5h74v.5h-74zM90 52h74v.5h-74zM90.5 52.5h74v.5h-74zM90.5 53h74.5v.5h-74.5zM90 53.5h75.5v.5h-75.5zM89.5 54h76v.5h-76zM88.5 54.5h77v.5h-77zM87.5 55h78.5v.5h-78.5zM86.5 55.5h79.5v.5h-79.5zM85.5 56h80.5v.5h-80.5zM84.5 56.5h81.5v.5h-81.5zM83.5 57h82.5v.5h-82.5zM83 57.5h82.5v.5h-82.5zM82 58h83.5v.5h-83.5zM81.5 58.5h83.5v.5h-83.5zM80.5 59h85v.5h-85zM80 59.5h86v.5h-86zM79 60h88v.5h-88zM78.5 60.5h89.5v.5h-89.5zM78 61h90.5v.5h-90.5zM77.5 61.5h92v.5h-92zM76.5 62h93.5v.5h-93.5zM76 62.5h94.5v.5h-94.5zM73 63h98.5v.5h-98.5zM70.5 63.5h101.5v.5h-101.5zM68.5 64h104v.5h-104zM66.5 64.5h107v.5h-107zM65 65h109v.5h-109zM63.5 65.5h111v.5h-111zM62 66h113v.5h-113zM61 66.5h114.5v.5h-114.5zM60 67h116v.5h-116zM58.5 67.5h118v.5h-118zM58 68h119v.5h-119zM57 68.5h120.5v.5h-120.5zM56 69h122v.5h-122zM55 69.5h123.5v.5h-123.5zM54.5 70h124.5v.5h-124.5zM53.5 70.5h126v.5h-126zM53 71h127v.5h-127zM52.5 71.5h128v.5h-128zM51.5 72h129.5v.5h-129.5zM51 72.5h130v.5h-130zM50.5 73h131v.5h-131zM50 73.5h132v.5h-132zM49.5 74h133v.5h-133zM49 74.5h133.5v.5h-133.5zM48.5 75h134.5v.5h-134.5zM48 75.5h135.5v.5h-135.5zM47.5 76h136v.5h-136zM47 76.5h137v.5h-137zM47 77h137.5v.5h-137.5zM46.5 77.5h138.5v.5h-138.5zM46 78h140v.5h-140zM46 78.5h141v.5h-141zM45.5 79h142.5v.5h-142.5zM45 79.5h143.5v.5h-143.5zM45 80h144.5v.5h-144.5zM44.5 80.5h145.5v.5h-145.5zM44.5 81h146.5v.5h-146.5zM44 81.5h148v.5h-148zM44 82h148.5v.5h-148.5zM43.5 82.5h149.5v.5h-149.5zM43 83h150.5v.5h-150.5zM43 83.5h151.5v.5h-151.5zM43 84h152v.5h-152zM42.5 84.5h153v.5h-153zM42.5 85h153.5v.5h-153.5zM42 85.5h154.5v.5h-154.5zM42 86h155v.5h-155zM41.5 86.5h156v.5h-156zM41.5 87h156.5v.5h-156.5zM41.5 87.5h157v.5h-157zM41 88h158v.5h-158zM41 88.5h158.5v.5h-158.5zM41 89h159v.5h-159zM40.5 89.5h160v.5h-160zM40.5 90h160v.5h-160zM40.5 90.5h160.5v.5h-160.5zM40 91h161.5v.5h-161.5zM40 91.5h161.5v.5h-161.5zM40 92h162v.5h-162zM40 92.5h162.5v.5h-162.5zM39.5 93h163v.5h-163zM39.5 93.5h163.5v.5h-163.5zM39.5 94h164v.5h-164zM39.5 94.5h164v.5h-164zM39 95h165v.5h-165zM39 95.5h165v.5h-165zM39 96h165v.5h-165zM39 96.5h165.5v.5h-165.5zM39 97h165.5v.5h-165.5zM39 97.5h166v.5h-166zM38.5 98h166.5v.5h-166.5zM38.5 98.5h167v.5h-167zM38.5 99h167v.5h-167zM38.5 99.5h167v.5h-167zM38.5 100h167.5v.5h-167.5zM38.5 100.5h167.5v.5h-167.5zM38.5 101h167.5v.5h-167.5zM38.5 101.5h168v.5h-168zM38.5 102h168v.5h-168zM38.5 102.5h168v.5h-168zM38.5 103h168v.5h-168zM38.5 103.5h168.5v.5h-168.5zM38.5 104h168.5v.5h-168.5zM38.5 104.5h168.5v.5h-168.5zM38.5 105h168.5v.5h-168.5zM38.5 105.5h168.5v.5h-168.5zM38.5 106h169v.5h-169zM38.5 106.5h169v.5h-169zM38.5 107h169v.5h-169zM38.5 107.5h169v.5h-169zM38.5 108h169v.5h-169zM38.5 108.5h169v.5h-169zM38.5 109h169.5v.5h-169.5zM38.5 109.5h169.5v.5h-169.5zM39 110h169v.5h-169zM39 110.5h169v.5h-169zM39 111h169v.5h-169zM39 111.5h169v.5h-169zM39 112h169v.5h-169zM39 112.5h169v.5h-169zM39.5 113h168.5v.5h-168.5zM39.5 113.5h168.5v.5h-168.5zM39.5 114h168.5v.5h-168.5zM39.5 114.5h168.5v.5h-168.5zM40 115h168v.5h-168zM40 115.5h168v.5h-168zM40 116h168v.5h-168zM40 116.5h168v.5h-168zM40.5 117h167.5v.5h-167.5zM40.5 117.5h167.5v.5h-167.5zM40.5 118h167.5v.5h-167.5zM41 118.5h167v.5h-167zM41 119h167v.5h-167zM41 119.5h167v.5h-167zM41.5 120h166.5v.5h-166.5zM41.5 120.5h166v.5h-166zM42 121h165.5v.5h-165.5zM42 121.5h165.5v.5h-165.5zM42.5 122h165v.5h-165zM42.5 122.5h165v.5h-165zM42.5 123h165v.5h-165zM43 123.5h164.5v.5h-164.5zM43.5 124h163.5v.5h-163.5zM43.5 124.5h163.5v.5h-163.5zM44 125h163v.5h-163zM44 125.5h163v.5h-163zM44.5 126h162.5v.5h-162.5zM44.5 126.5h162v.5h-162zM45 127h161.5v.5h-161.5zM45.5 127.5h161v.5h-161zM45.5 128h161v.5h-161zM46 128.5h160v.5h-160zM46.5 129h159.5v.5h-159.5zM46.5 129.5h159.5v.5h-159.5zM47 130h158.5v.5h-158.5zM47.5 130.5h158v.5h-158zM48 131h157.5v.5h-157.5zM48 131.5h157v.5h-157zM48.5 132h156.5v.5h-156.5zM49 132.5h156v.5h-156zM49.5 133h155v.5h-155zM50.5 133.5h154v.5h-154zM51 134h153v.5h-153zM51.5 134.5h152.5v.5h-152.5zM52 135h152v.5h-152zM52 135.5h151.5v.5h-151.5zM52 136h151.5v.5h-151.5zM52 136.5h151v.5h-151zM52 137h151v.5h-151zM52 137.5h150.5v.5h-150.5zM52 138h150.5v.5h-150.5zM52 138.5h150v.5h-150zM52 139h150v.5h-150zM52 139.5h149.5v.5h-149.5zM52 140h149.5v.5h-149.5zM52 140.5h149v.5h-149zM51.5 141h149v.5h-149zM51.5 141.5h149v.5h-149zM51.5 142h148.5v.5h-148.5zM51.5 142.5h148v.5h-148zM51.5 143h147.5v.5h-147.5zM51.5 143.5h147.5v.5h-147.5zM51.5 144h147v.5h-147zM51.5 144.5h146.5v.5h-146.5zM51.5 145h146v.5h-146zM51.5 145.5h145.5v.5h-145.5zM51.5 146h145v.5h-145zM51.5 146.5h144.5v.5h-144.5zM51.5 147h143.5v.5h-143.5zM51.5 147.5h143v.5h-143zM51.5 148h142.5v.5h-142.5zM51 148.5h142v.5h-142zM51 149h141v.5h-141zM51 149.5h140v.5h-140zM51 150h139.5v.5h-139.5zM51 150.5h139v.5h-139zM51 151h139v.5h-139zM50.5 151.5h139.5v.5h-139.5zM50.5 152h139.5v.5h-139.5zM50.5 152.5h139.5v.5h-139.5zM50.5 153h139.5v.5h-139.5zM202.5 153h7v.5h-7zM50 153.5h140.5v.5h-140.5zM199 153.5h13.5v.5h-13.5zM50 154h141v.5h-141zM195.5 154h19v.5h-19zM50 154.5h166.5v.5h-166.5zM49.5 155h168.5v.5h-168.5zM49.5 155.5h169.5v.5h-169.5zM49 156h171v.5h-171zM229.5 156h10.5v.5h-10.5zM49 156.5h172v.5h-172zM226 156.5h17.5v.5h-17.5zM48.5 157h173.5v.5h-173.5zM223.5 157h22v.5h-22zM48.5 157.5h199v.5h-199zM48 158h201v.5h-201zM48 158.5h202v.5h-202zM47.5 159h204v.5h-204zM47.5 159.5h205v.5h-205zM47 160h206.5v.5h-206.5zM47 160.5h207v.5h-207zM46.5 161h208.5v.5h-208.5zM46 161.5h210v.5h-210zM46 162h210.5v.5h-210.5zM45.5 162.5h212v.5h-212zM45.5 163h212.5v.5h-212.5zM45 163.5h213.5v.5h-213.5zM44.5 164h214.5v.5h-214.5zM44.5 164.5h215v.5h-215zM44 165h216v.5h-216zM44 165.5h216.5v.5h-216.5zM43.5 166h217.5v.5h-217.5zM43 166.5h218.5v.5h-218.5zM43 167h219v.5h-219zM42.5 167.5h220v.5h-220zM42.5 168h220.5v.5h-220.5zM42 168.5h221.5v.5h-221.5zM42 169h222v.5h-222zM41.5 169.5h222.5v.5h-222.5zM41 170h223.5v.5h-223.5zM41 170.5h224v.5h-224zM40.5 171h224.5v.5h-224.5zM40.5 171.5h225v.5h-225zM40 172h225.5v.5h-225.5zM40 172.5h226v.5h-226zM40 173h226.5v.5h-226.5zM39.5 173.5h227v.5h-227zM39.5 174h227.5v.5h-227.5zM39 174.5h228v.5h-228zM39 175h228v.5h-228zM38.5 175.5h229v.5h-229zM38.5 176h229v.5h-229zM38.5 176.5h229.5v.5h-229.5zM38 177h230v.5h-230zM38 177.5h230.5v.5h-230.5zM38 178h230.5v.5h-230.5zM38 178.5h230.5v.5h-230.5zM37.5 179h231v.5h-231zM37.5 179.5h231.5v.5h-231.5zM37.5 180h231.5v.5h-231.5zM37.5 180.5h231.5v.5h-231.5zM37.5 181h231.5v.5h-231.5zM37 181.5h232.5v.5h-232.5zM37 182h232.5v.5h-232.5zM37 182.5h232.5v.5h-232.5zM37 183h232.5v.5h-232.5zM37 183.5h232.5v.5h-232.5zM37 184h233v.5h-233zM37 184.5h233v.5h-233zM37 185h233v.5h-233zM37 185.5h233v.5h-233zM37 186h233v.5h-233zM37 186.5h233v.5h-233zM37 187h233v.5h-233zM37 187.5h233v.5h-233zM37 188h233v.5h-233zM37.5 188.5h232.5v.5h-232.5zM37.5 189h232.5v.5h-232.5zM37.5 189.5h232.5v.5h-232.5zM37.5 190h232.5v.5h-232.5zM37.5 190.5h232.5v.5h-232.5zM38 191h232v.5h-232zM38 191.5h232v.5h-232zM38 192h232v.5h-232zM38.5 192.5h231v.5h-231zM38.5 193h231v.5h-231zM39 193.5h230.5v.5h-230.5zM39 194h230.5v.5h-230.5zM39.5 194.5h229.5v.5h-229.5zM39.5 195h229.5v.5h-229.5zM40 195.5h229v.5h-229zM40 196h229v.5h-229zM40.5 196.5h228v.5h-228zM40.5 197h228v.5h-228zM41 197.5h227.5v.5h-227.5zM41.5 198h226.5v.5h-226.5zM41.5 198.5h226.5v.5h-226.5zM42 199h225.5v.5h-225.5zM42.5 199.5h225v.5h-225zM43 200h224v.5h-224zM43.5 200.5h223.5v.5h-223.5zM44 201h222.5v.5h-222.5zM44.5 201.5h222v.5h-222zM45 202h31v.5h-31zM76.5 202h189.5v.5h-189.5zM45.5 202.5h30v.5h-30zM77 202.5h189v.5h-189zM46 203h28.5v.5h-28.5zM77.5 203h188v.5h-188zM47 203.5h27v.5h-27zM78.5 203.5h187v.5h-187zM47.5 204h25.5v.5h-25.5zM79 204h186.5v.5h-186.5zM48.5 204.5h24v.5h-24zM79.5 204.5h186.5v.5h-186.5zM49.5 205h22v.5h-22zM80.5 205h185.5v.5h-185.5zM50.5 205.5h19.5v.5h-19.5zM81 205.5h185v.5h-185zM51.5 206h17.5v.5h-17.5zM82 206h184v.5h-184zM53.5 206.5h14v.5h-14zM82.5 206.5h183.5v.5h-183.5zM55.5 207h10v.5h-10zM83 207h183.5v.5h-183.5zM84 207.5h182.5v.5h-182.5zM85 208h181.5v.5h-181.5zM85.5 208.5h181v.5h-181zM86 209h180.5v.5h-180.5zM86.5 209.5h180v.5h-180zM87 210h179.5v.5h-179.5zM86.5 210.5h180v.5h-180zM86 211h180.5v.5h-180.5zM85.5 211.5h181v.5h-181zM85.5 212h181v.5h-181zM85.5 212.5h181v.5h-181zM85.5 213h181v.5h-181zM85 213.5h181v.5h-181zM85 214h181v.5h-181zM85 214.5h181v.5h-181zM85.5 215h180.5v.5h-180.5zM85.5 215.5h180v.5h-180zM85.5 216h180v.5h-180zM85.5 216.5h180v.5h-180zM86 217h179.5v.5h-179.5zM86 217.5h179v.5h-179zM86.5 218h178.5v.5h-178.5zM86.5 218.5h178v.5h-178zM87 219h102v.5h-102zM191.5 219h73v.5h-73zM87.5 219.5h101v.5h-101zM195 219.5h69.5v.5h-69.5zM88 220h100v.5h-100zM199 220h65v.5h-65zM89 220.5h99v.5h-99zM202.5 220.5h61.5v.5h-61.5zM89.5 221h98.5v.5h-98.5zM203.5 221h60v.5h-60zM91 221.5h97v.5h-97zM204 221.5h59v.5h-59zM96.5 222h91.5v.5h-91.5zM205 222h58v.5h-58zM97 222.5h91v.5h-91zM205.5 222.5h57v.5h-57zM97.5 223h90.5v.5h-90.5zM206.5 223h55.5v.5h-55.5zM97.5 223.5h90.5v.5h-90.5zM207 223.5h55v.5h-55zM98 224h90v.5h-90zM208 224h53.5v.5h-53.5zM98 224.5h90v.5h-90zM209 224.5h52v.5h-52zM92 225h3v.5h-3zM98 225h90v.5h-90zM209.5 225h51v.5h-51zM91.5 225.5h4v.5h-4zM97.5 225.5h90v.5h-90zM210.5 225.5h50v.5h-50zM91 226h5.5v.5h-5.5zM97 226h90.5v.5h-90.5zM211.5 226h48.5v.5h-48.5zM91 226.5h96.5v.5h-96.5zM212.5 226.5h47v.5h-47zM90.5 227h97v.5h-97zM213 227h45.5v.5h-45.5zM90.5 227.5h97v.5h-97zM214 227.5h44v.5h-44zM90.5 228h96.5v.5h-96.5zM215 228h42.5v.5h-42.5zM90 228.5h97v.5h-97zM216 228.5h41v.5h-41zM90 229h97v.5h-97zM217 229h39v.5h-39zM90 229.5h97v.5h-97zM218 229.5h37.5v.5h-37.5zM90 230h97v.5h-97zM219.5 230h35.5v.5h-35.5zM89.5 230.5h97.5v.5h-97.5zM220.5 230.5h33.5v.5h-33.5zM89 231h98.5v.5h-98.5zM222 231h31v.5h-31zM88.5 231.5h98.5v.5h-98.5zM223.5 231.5h28.5v.5h-28.5zM87 232h100v.5h-100zM225 232h25.5v.5h-25.5zM86.5 232.5h100.5v.5h-100.5zM227 232.5h22v.5h-22zM86 233h101v.5h-101zM229 233h18v.5h-18zM85.5 233.5h101.5v.5h-101.5zM231.5 233.5h13.5v.5h-13.5zM83 234h1.5v.5h-1.5zM85 234h101.5v.5h-101.5zM237 234h2.5v.5h-2.5zM82.5 234.5h103.5v.5h-103.5zM82 235h104v.5h-104zM82 235.5h103.5v.5h-103.5zM81.5 236h103v.5h-103zM81.5 236.5h102v.5h-102zM81.5 237h98.5v.5h-98.5zM81.5 237.5h98v.5h-98zM81.5 238h97.5v.5h-97.5zM81.5 238.5h97v.5h-97zM81.5 239h97v.5h-97zM81.5 239.5h96.5v.5h-96.5zM82 240h96v.5h-96zM82 240.5h95.5v.5h-95.5zM82 241h95.5v.5h-95.5zM82 241.5h95.5v.5h-95.5zM82.5 242h95v.5h-95zM82.5 242.5h94.5v.5h-94.5zM82.5 243h94.5v.5h-94.5zM82.5 243.5h94.5v.5h-94.5zM82 244h95v.5h-95zM81.5 244.5h95.5v.5h-95.5zM80.5 245h96v.5h-96zM79.5 245.5h97v.5h-97zM79 246h97.5v.5h-97.5zM78.5 246.5h97.5v.5h-97.5zM78.5 247h97.5v.5h-97.5zM78.5 247.5h97.5v.5h-97.5zM78 248h97.5v.5h-97.5zM78 248.5h97.5v.5h-97.5zM78 249h97.5v.5h-97.5zM78.5 249.5h96.5v.5h-96.5zM78.5 250h96.5v.5h-96.5zM78.5 250.5h96v.5h-96zM78.5 251h96v.5h-96zM79 251.5h95v.5h-95zM79 252h94.5v.5h-94.5zM79 252.5h94.5v.5h-94.5zM79.5 253h93.5v.5h-93.5zM79.5 253.5h93v.5h-93zM80 254h92.5v.5h-92.5zM80 254.5h80.5v.5h-80.5zM162.5 254.5h9.5v.5h-9.5zM80.5 255h79.5v.5h-79.5zM163.5 255h8v.5h-8zM80.5 255.5h79v.5h-79zM165 255.5h6v.5h-6zM81 256h79v.5h-79zM166.5 256h3.5v.5h-3.5zM81 256.5h79.5v.5h-79.5zM168 256.5h1v.5h-1zM81.5 257h79.5v.5h-79.5zM82 257.5h80v.5h-80zM82.5 258h80v.5h-80zM83.5 258.5h79.5v.5h-79.5zM84 259h79v.5h-79zM84.5 259.5h79v.5h-79zM84.5 260h79v.5h-79zM85 260.5h78.5v.5h-78.5zM85 261h78.5v.5h-78.5zM85.5 261.5h78.5v.5h-78.5zM86 262h78v.5h-78zM86.5 262.5h77.5v.5h-77.5zM86.5 263h31.5v.5h-31.5zM119.5 263h44.5v.5h-44.5zM87 263.5h30.5v.5h-30.5zM120.5 263.5h43.5v.5h-43.5zM87.5 264h11.5v.5h-11.5zM101 264h16v.5h-16zM121 264h43v.5h-43zM88 264.5h10.5v.5h-10.5zM101.5 264.5h15v.5h-15zM121.5 264.5h42v.5h-42zM88.5 265h9v.5h-9zM102 265h14v.5h-14zM122 265h41.5v.5h-41.5zM89 265.5h8v.5h-8zM102.5 265.5h13v.5h-13zM122.5 265.5h41v.5h-41zM90 266h6.5v.5h-6.5zM103 266h12v.5h-12zM123 266h40.5v.5h-40.5zM90.5 266.5h5v.5h-5zM103.5 266.5h11v.5h-11zM123.5 266.5h40v.5h-40zM91 267h4v.5h-4zM104 267h10v.5h-10zM124 267h39.5v.5h-39.5zM92.5 267.5h1.5v.5h-1.5zM104.5 267.5h9.5v.5h-9.5zM124.5 267.5h38.5v.5h-38.5zM105 268h8.5v.5h-8.5zM125 268h38v.5h-38zM105.5 268.5h7.5v.5h-7.5zM125 268.5h38v.5h-38zM106 269h6.5v.5h-6.5zM124.5 269h38.5v.5h-38.5zM106.5 269.5h5.5v.5h-5.5zM124.5 269.5h38.5v.5h-38.5zM107.5 270h4v.5h-4zM124 270h38.5v.5h-38.5zM108.5 270.5h1.5v.5h-1.5zM123.5 270.5h39v.5h-39zM123.5 271h39v.5h-39zM123 271.5h39.5v.5h-39.5zM122.5 272h39.5v.5h-39.5zM122.5 272.5h39.5v.5h-39.5zM122 273h40v.5h-40zM121.5 273.5h40.5v.5h-40.5zM121 274h40.5v.5h-40.5zM120.5 274.5h41v.5h-41zM120 275h41.5v.5h-41.5zM119.5 275.5h41.5v.5h-41.5zM119.5 276h41.5v.5h-41.5zM119 276.5h41.5v.5h-41.5zM118.5 277h25.5v.5h-25.5zM146 277h2v.5h-2zM149 277h11.5v.5h-11.5zM118 277.5h25.5v.5h-25.5zM150 277.5h10v.5h-10zM118 278h25v.5h-25zM151 278h8.5v.5h-8.5zM117.5 278.5h25v.5h-25zM151.5 278.5h8v.5h-8zM117 279h25v.5h-25zM152.5 279h6v.5h-6zM116.5 279.5h25.5v.5h-25.5zM153.5 279.5h4.5v.5h-4.5zM116.5 280h25.5v.5h-25.5zM116 280.5h25.5v.5h-25.5zM116 281h25.5v.5h-25.5zM116 281.5h25v.5h-25zM115.5 282h25.5v.5h-25.5zM115.5 282.5h25v.5h-25zM116 283h24.5v.5h-24.5zM116 283.5h24v.5h-24zM116.5 284h23.5v.5h-23.5zM117 284.5h22.5v.5h-22.5zM117.5 285h21.5v.5h-21.5zM118.5 285.5h20v.5h-20zM119.5 286h17.5v.5h-17.5zM121.5 286.5h14v.5h-14zM124 287h9v.5h-9z', 'allowDelete': False},
    {'id': 'aromping', 'name': '아롬핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/aromping.svg" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/aromping.svg', 'outerPath': 'M107.5 12h0.5v.5h-0.5zM107 12.5h2v.5h-2zM107 13h3v.5h-3zM106.5 13.5h4v.5h-4zM106.5 14h5v.5h-5zM106 14.5h6v.5h-6zM106 15h7v.5h-7zM105.5 15.5h8v.5h-8zM105.5 16h8.5v.5h-8.5zM105 16.5h9.5v.5h-9.5zM105 17h9v.5h-9zM104.5 17.5h9.5v.5h-9.5zM104.5 18h9v.5h-9zM104.5 18.5h9v.5h-9zM104.5 19h9v.5h-9zM104.5 19.5h8.5v.5h-8.5zM105.5 20h7.5v.5h-7.5zM106 20.5h7.5v.5h-7.5zM106.5 21h7.5v.5h-7.5zM107 21.5h8v.5h-8zM107.5 22h8v.5h-8zM107 22.5h9v.5h-9zM106.5 23h10v.5h-10zM106.5 23.5h10.5v.5h-10.5zM106 24h11.5v.5h-11.5zM106 24.5h12v.5h-12zM105.5 25h13v.5h-13zM105.5 25.5h13.5v.5h-13.5zM125 25.5h2.5v.5h-2.5zM105 26h14.5v.5h-14.5zM123.5 26h5.5v.5h-5.5zM105 26.5h14.5v.5h-14.5zM122.5 26.5h7v.5h-7zM105 27h15v.5h-15zM121.5 27h9v.5h-9zM104.5 27.5h16v.5h-16zM121 27.5h10v.5h-10zM104.5 28h27v.5h-27zM104.5 28.5h27v.5h-27zM104 29h28v.5h-28zM104 29.5h28v.5h-28zM104 30h28.5v.5h-28.5zM104 30.5h28.5v.5h-28.5zM103.5 31h29.5v.5h-29.5zM103 31.5h30v.5h-30zM100 32h33.5v.5h-33.5zM98.5 32.5h35.5v.5h-35.5zM134.5 32.5h3.5v.5h-3.5zM98 33h41v.5h-41zM97 33.5h42.5v.5h-42.5zM96.5 34h43.5v.5h-43.5zM96.5 34.5h44v.5h-44zM96 35h45v.5h-45zM95.5 35.5h46v.5h-46zM142.5 35.5h3v.5h-3zM95.5 36h50.5v.5h-50.5zM95.5 36.5h51v.5h-51zM95 37h52v.5h-52zM95 37.5h52.5v.5h-52.5zM95 38h53v.5h-53zM94.5 38.5h54v.5h-54zM94.5 39h54v.5h-54zM94.5 39.5h54v.5h-54zM94.5 40h54.5v.5h-54.5zM95 40.5h54v.5h-54zM95 41h54v.5h-54zM95 41.5h54v.5h-54zM94.5 42h54.5v.5h-54.5zM94 42.5h55.5v.5h-55.5zM92.5 43h57.5v.5h-57.5zM92 43.5h60v.5h-60zM91.5 44h63.5v.5h-63.5zM91 44.5h66v.5h-66zM90.5 45h68.5v.5h-68.5zM90.5 45.5h70v.5h-70zM90 46h72v.5h-72zM90 46.5h73v.5h-73zM90 47h74v.5h-74zM90 47.5h75v.5h-75zM90 48h76v.5h-76zM89.5 48.5h77.5v.5h-77.5zM89 49h78.5v.5h-78.5zM179.5 49h7v.5h-7zM87.5 49.5h80.5v.5h-80.5zM177 49.5h11v.5h-11zM87 50h81.5v.5h-81.5zM175.5 50h14v.5h-14zM86.5 50.5h82.5v.5h-82.5zM174 50.5h23v.5h-23zM86 51h84v.5h-84zM173 51h26v.5h-26zM86 51.5h85.5v.5h-85.5zM172 51.5h28.5v.5h-28.5zM85.5 52h116v.5h-116zM85.5 52.5h117v.5h-117zM85.5 53h118v.5h-118zM85 53.5h119.5v.5h-119.5zM85 54h120v.5h-120zM85 54.5h120.5v.5h-120.5zM85 55h121.5v.5h-121.5zM85.5 55.5h121.5v.5h-121.5zM85.5 56h122v.5h-122zM85.5 56.5h122.5v.5h-122.5zM86 57h122.5v.5h-122.5zM86 57.5h123.5v.5h-123.5zM86.5 58h123.5v.5h-123.5zM86.5 58.5h123.5v.5h-123.5zM86 59h124.5v.5h-124.5zM85.5 59.5h125.5v.5h-125.5zM85 60h126.5v.5h-126.5zM84.5 60.5h127.5v.5h-127.5zM84 61h128.5v.5h-128.5zM83.5 61.5h129.5v.5h-129.5zM83 62h130.5v.5h-130.5zM82.5 62.5h131v.5h-131zM82 63h132v.5h-132zM81.5 63.5h133v.5h-133zM81 64h134v.5h-134zM80.5 64.5h134.5v.5h-134.5zM80.5 65h135v.5h-135zM80 65.5h136v.5h-136zM79.5 66h136.5v.5h-136.5zM79.5 66.5h137v.5h-137zM79 67h138v.5h-138zM78.5 67.5h138.5v.5h-138.5zM78.5 68h139v.5h-139zM78.5 68.5h139.5v.5h-139.5zM78.5 69h139.5v.5h-139.5zM78 69.5h140.5v.5h-140.5zM77.5 70h141v.5h-141zM77 70.5h142v.5h-142zM76.5 71h142.5v.5h-142.5zM76 71.5h143.5v.5h-143.5zM76 72h143.5v.5h-143.5zM75.5 72.5h144.5v.5h-144.5zM75 73h145v.5h-145zM74.5 73.5h146v.5h-146zM74 74h146.5v.5h-146.5zM74 74.5h146.5v.5h-146.5zM73.5 75h147.5v.5h-147.5zM73 75.5h148v.5h-148zM72.5 76h149v.5h-149zM72.5 76.5h149v.5h-149zM72 77h149.5v.5h-149.5zM71.5 77.5h150.5v.5h-150.5zM71 78h151v.5h-151zM71 78.5h151v.5h-151zM70.5 79h152v.5h-152zM70 79.5h152.5v.5h-152.5zM69.5 80h153v.5h-153zM69.5 80.5h153.5v.5h-153.5zM69 81h154v.5h-154zM69 81.5h154v.5h-154zM68.5 82h155v.5h-155zM68 82.5h155.5v.5h-155.5zM68 83h155.5v.5h-155.5zM67.5 83.5h156v.5h-156zM67 84h157v.5h-157zM67 84.5h157v.5h-157zM66.5 85h157.5v.5h-157.5zM66 85.5h158v.5h-158zM66 86h158v.5h-158zM65.5 86.5h158.5v.5h-158.5zM65.5 87h159v.5h-159zM65 87.5h159.5v.5h-159.5zM65 88h159.5v.5h-159.5zM64.5 88.5h160v.5h-160zM64.5 89h160v.5h-160zM64 89.5h160.5v.5h-160.5zM63.5 90h161v.5h-161zM63.5 90.5h161v.5h-161zM63 91h161.5v.5h-161.5zM63 91.5h161.5v.5h-161.5zM62.5 92h162v.5h-162zM62.5 92.5h162v.5h-162zM62 93h162.5v.5h-162.5zM62 93.5h162.5v.5h-162.5zM62 94h162.5v.5h-162.5zM61.5 94.5h163v.5h-163zM61.5 95h163v.5h-163zM61 95.5h163.5v.5h-163.5zM61 96h163.5v.5h-163.5zM61 96.5h163v.5h-163zM60.5 97h163.5v.5h-163.5zM60.5 97.5h163.5v.5h-163.5zM60 98h164v.5h-164zM60 98.5h164v.5h-164zM60 99h164v.5h-164zM59.5 99.5h164v.5h-164zM59.5 100h164v.5h-164zM59.5 100.5h164v.5h-164zM59 101h164v.5h-164zM59 101.5h164v.5h-164zM59 102h163.5v.5h-163.5zM58.5 102.5h164v.5h-164zM58.5 103h163.5v.5h-163.5zM58.5 103.5h163.5v.5h-163.5zM58.5 104h163v.5h-163zM58 104.5h163v.5h-163zM58 105h163v.5h-163zM58 105.5h162.5v.5h-162.5zM57.5 106h163v.5h-163zM57.5 106.5h163.5v.5h-163.5zM57.5 107h163.5v.5h-163.5zM57.5 107.5h163.5v.5h-163.5zM57 108h164.5v.5h-164.5zM57 108.5h164.5v.5h-164.5zM57 109h164.5v.5h-164.5zM57 109.5h165v.5h-165zM57 110h165v.5h-165zM56.5 110.5h166v.5h-166zM56.5 111h166v.5h-166zM56.5 111.5h166v.5h-166zM56.5 112h166.5v.5h-166.5zM56.5 112.5h166.5v.5h-166.5zM56 113h167v.5h-167zM56 113.5h167.5v.5h-167.5zM56 114h167.5v.5h-167.5zM56 114.5h167.5v.5h-167.5zM55.5 115h168.5v.5h-168.5zM55.5 115.5h168.5v.5h-168.5zM55.5 116h168.5v.5h-168.5zM55.5 116.5h168.5v.5h-168.5zM55.5 117h169v.5h-169zM55.5 117.5h169v.5h-169zM55.5 118h169v.5h-169zM55 118.5h170v.5h-170zM55 119h170v.5h-170zM55 119.5h170v.5h-170zM55 120h170v.5h-170zM55 120.5h170.5v.5h-170.5zM55 121h170.5v.5h-170.5zM55 121.5h170.5v.5h-170.5zM55 122h170.5v.5h-170.5zM55 122.5h171v.5h-171zM54.5 123h171.5v.5h-171.5zM54.5 123.5h171.5v.5h-171.5zM54.5 124h171.5v.5h-171.5zM54.5 124.5h171.5v.5h-171.5zM54.5 125h172v.5h-172zM54.5 125.5h172v.5h-172zM54.5 126h172v.5h-172zM54.5 126.5h172v.5h-172zM54.5 127h172.5v.5h-172.5zM54.5 127.5h172.5v.5h-172.5zM54.5 128h172.5v.5h-172.5zM54.5 128.5h172.5v.5h-172.5zM54.5 129h172.5v.5h-172.5zM54.5 129.5h172.5v.5h-172.5zM54.5 130h173v.5h-173zM54.5 130.5h173v.5h-173zM54.5 131h173v.5h-173zM54.5 131.5h173v.5h-173zM54.5 132h173v.5h-173zM54.5 132.5h173v.5h-173zM54.5 133h173v.5h-173zM54.5 133.5h173v.5h-173zM54.5 134h173.5v.5h-173.5zM54.5 134.5h173.5v.5h-173.5zM54.5 135h173.5v.5h-173.5zM54.5 135.5h173.5v.5h-173.5zM54.5 136h173.5v.5h-173.5zM54.5 136.5h173.5v.5h-173.5zM54.5 137h173.5v.5h-173.5zM54.5 137.5h173.5v.5h-173.5zM54.5 138h173.5v.5h-173.5zM54.5 138.5h173.5v.5h-173.5zM55 139h173.5v.5h-173.5zM55 139.5h173.5v.5h-173.5zM55 140h173.5v.5h-173.5zM55 140.5h173.5v.5h-173.5zM55 141h173.5v.5h-173.5zM55 141.5h173.5v.5h-173.5zM55 142h173.5v.5h-173.5zM55 142.5h173.5v.5h-173.5zM55 143h173.5v.5h-173.5zM55 143.5h173.5v.5h-173.5zM55.5 144h173v.5h-173zM55.5 144.5h173v.5h-173zM55.5 145h173v.5h-173zM55.5 145.5h173v.5h-173zM55.5 146h173v.5h-173zM55.5 146.5h173v.5h-173zM55.5 147h173v.5h-173zM56 147.5h172.5v.5h-172.5zM56 148h172.5v.5h-172.5zM56 148.5h172.5v.5h-172.5zM56 149h172.5v.5h-172.5zM56 149.5h172.5v.5h-172.5zM56.5 150h172v.5h-172zM56.5 150.5h172v.5h-172zM56.5 151h172v.5h-172zM56.5 151.5h172v.5h-172zM56.5 152h172v.5h-172zM57 152.5h171.5v.5h-171.5zM57 153h171.5v.5h-171.5zM57 153.5h171.5v.5h-171.5zM57 154h171.5v.5h-171.5zM57 154.5h171.5v.5h-171.5zM57.5 155h170.5v.5h-170.5zM57.5 155.5h170.5v.5h-170.5zM57.5 156h170.5v.5h-170.5zM57.5 156.5h170.5v.5h-170.5zM58 157h170v.5h-170zM58 157.5h170v.5h-170zM58 158h170v.5h-170zM58 158.5h170v.5h-170zM58.5 159h169.5v.5h-169.5zM58.5 159.5h169.5v.5h-169.5zM58.5 160h169.5v.5h-169.5zM58.5 160.5h169v.5h-169zM59 161h168.5v.5h-168.5zM59 161.5h168.5v.5h-168.5zM59 162h168.5v.5h-168.5zM59.5 162.5h168v.5h-168zM59.5 163h168v.5h-168zM59.5 163.5h168v.5h-168zM59.5 164h167.5v.5h-167.5zM60 164.5h167v.5h-167zM60 165h167v.5h-167zM60 165.5h167v.5h-167zM60.5 166h166.5v.5h-166.5zM60.5 166.5h166.5v.5h-166.5zM60.5 167h166v.5h-166zM61 167.5h165.5v.5h-165.5zM61 168h165.5v.5h-165.5zM61 168.5h165.5v.5h-165.5zM61.5 169h165v.5h-165zM61.5 169.5h164.5v.5h-164.5zM61.5 170h164.5v.5h-164.5zM62 170.5h164v.5h-164zM62 171h164v.5h-164zM62 171.5h163.5v.5h-163.5zM62.5 172h163v.5h-163zM62.5 172.5h163v.5h-163zM63 173h162.5v.5h-162.5zM63 173.5h162.5v.5h-162.5zM63 174h162v.5h-162zM63.5 174.5h161.5v.5h-161.5zM63.5 175h161.5v.5h-161.5zM64 175.5h161v.5h-161zM64 176h161v.5h-161zM64.5 176.5h160.5v.5h-160.5zM64.5 177h160v.5h-160zM64.5 177.5h160v.5h-160zM65 178h159.5v.5h-159.5zM65 178.5h159.5v.5h-159.5zM65.5 179h159v.5h-159zM65.5 179.5h159v.5h-159zM66 180h158.5v.5h-158.5zM66 180.5h158.5v.5h-158.5zM66 181h158.5v.5h-158.5zM66.5 181.5h158v.5h-158zM66.5 182h158v.5h-158zM67 182.5h157.5v.5h-157.5zM67 183h157.5v.5h-157.5zM67.5 183.5h157v.5h-157zM67.5 184h157v.5h-157zM68 184.5h156.5v.5h-156.5zM68 185h156.5v.5h-156.5zM68.5 185.5h156v.5h-156zM69 186h156v.5h-156zM69 186.5h156v.5h-156zM69.5 187h155.5v.5h-155.5zM69.5 187.5h155.5v.5h-155.5zM70 188h155v.5h-155zM70 188.5h155.5v.5h-155.5zM70.5 189h155v.5h-155zM70.5 189.5h155v.5h-155zM71 190h155v.5h-155zM71.5 190.5h154.5v.5h-154.5zM71.5 191h155v.5h-155zM72 191.5h155v.5h-155zM72.5 192h154.5v.5h-154.5zM238 192h1.5v.5h-1.5zM72.5 192.5h155v.5h-155zM237.5 192.5h3v.5h-3zM73 193h155v.5h-155zM237 193h4v.5h-4zM73 193.5h155.5v.5h-155.5zM236.5 193.5h4.5v.5h-4.5zM73.5 194h156v.5h-156zM236 194h5.5v.5h-5.5zM74 194.5h156v.5h-156zM235 194.5h6.5v.5h-6.5zM74 195h157.5v.5h-157.5zM233.5 195h8.5v.5h-8.5zM74.5 195.5h167.5v.5h-167.5zM75 196h167v.5h-167zM75 196.5h167.5v.5h-167.5zM75.5 197h167v.5h-167zM76 197.5h167v.5h-167zM76 198h167v.5h-167zM76.5 198.5h166.5v.5h-166.5zM77 199h166v.5h-166zM77.5 199.5h166v.5h-166zM77.5 200h166v.5h-166zM78 200.5h165.5v.5h-165.5zM78.5 201h165v.5h-165zM79 201.5h165v.5h-165zM79 202h165v.5h-165zM79.5 202.5h164.5v.5h-164.5zM80 203h164v.5h-164zM80.5 203.5h163.5v.5h-163.5zM81 204h163v.5h-163zM81 204.5h163v.5h-163zM81.5 205h162.5v.5h-162.5zM82 205.5h162v.5h-162zM82.5 206h161.5v.5h-161.5zM83 206.5h161v.5h-161zM83.5 207h160.5v.5h-160.5zM84 207.5h160v.5h-160zM84 208h160v.5h-160zM84.5 208.5h159.5v.5h-159.5zM85 209h159v.5h-159zM85.5 209.5h158.5v.5h-158.5zM86 210h158v.5h-158zM86.5 210.5h157.5v.5h-157.5zM86.5 211h157.5v.5h-157.5zM86 211.5h158v.5h-158zM85.5 212h158v.5h-158zM85 212.5h158.5v.5h-158.5zM84.5 213h159v.5h-159zM84 213.5h159.5v.5h-159.5zM84 214h159v.5h-159zM83.5 214.5h159.5v.5h-159.5zM83.5 215h159.5v.5h-159.5zM83 215.5h159.5v.5h-159.5zM83 216h159.5v.5h-159.5zM82.5 216.5h160v.5h-160zM82.5 217h159.5v.5h-159.5zM82.5 217.5h159.5v.5h-159.5zM82.5 218h159v.5h-159zM82.5 218.5h159v.5h-159zM82.5 219h158.5v.5h-158.5zM82.5 219.5h158.5v.5h-158.5zM82.5 220h158v.5h-158zM82.5 220.5h158v.5h-158zM82.5 221h157.5v.5h-157.5zM83 221.5h156.5v.5h-156.5zM83 222h156.5v.5h-156.5zM83 222.5h156v.5h-156zM83.5 223h155v.5h-155zM83.5 223.5h155v.5h-155zM84 224h154v.5h-154zM84 224.5h153.5v.5h-153.5zM84 225h153v.5h-153zM83.5 225.5h153v.5h-153zM83.5 226h153v.5h-153zM83.5 226.5h152.5v.5h-152.5zM83.5 227h152v.5h-152zM83.5 227.5h151.5v.5h-151.5zM83.5 228h151v.5h-151zM83.5 228.5h150.5v.5h-150.5zM83.5 229h150v.5h-150zM83.5 229.5h149v.5h-149zM83.5 230h148.5v.5h-148.5zM83.5 230.5h148v.5h-148zM83.5 231h147.5v.5h-147.5zM83.5 231.5h146.5v.5h-146.5zM83.5 232h146v.5h-146zM83.5 232.5h145.5v.5h-145.5zM83.5 233h144.5v.5h-144.5zM83.5 233.5h143.5v.5h-143.5zM83.5 234h143v.5h-143zM83.5 234.5h142v.5h-142zM83.5 235h141v.5h-141zM84 235.5h139.5v.5h-139.5zM84 236h138.5v.5h-138.5zM84 236.5h137.5v.5h-137.5zM84 237h136.5v.5h-136.5zM84.5 237.5h135v.5h-135zM84.5 238h134v.5h-134zM84.5 238.5h132.5v.5h-132.5zM85 239h131v.5h-131zM85 239.5h129.5v.5h-129.5zM85 240h128v.5h-128zM85.5 240.5h126v.5h-126zM86 241h124v.5h-124zM86 241.5h122v.5h-122zM86.5 242h119.5v.5h-119.5zM87 242.5h117v.5h-117zM87.5 243h114v.5h-114zM88 243.5h111v.5h-111zM88.5 244h107.5v.5h-107.5zM89 244.5h8v.5h-8zM99 244.5h93v.5h-93zM90 245h5.5v.5h-5.5zM100.5 245h86.5v.5h-86.5zM101 245.5h82.5v.5h-82.5zM101.5 246h81.5v.5h-81.5zM101.5 246.5h81v.5h-81zM102 247h80v.5h-80zM102.5 247.5h79.5v.5h-79.5zM103.5 248h79v.5h-79zM104 248.5h78.5v.5h-78.5zM105 249h77.5v.5h-77.5zM106.5 249.5h76.5v.5h-76.5zM107.5 250h75.5v.5h-75.5zM108 250.5h75v.5h-75zM108.5 251h75v.5h-75zM108.5 251.5h75v.5h-75zM109 252h74.5v.5h-74.5zM109.5 252.5h74.5v.5h-74.5zM110 253h74v.5h-74zM110.5 253.5h73.5v.5h-73.5zM111.5 254h73v.5h-73zM112.5 254.5h72v.5h-72zM114 255h70.5v.5h-70.5zM116.5 255.5h68.5v.5h-68.5zM124 256h61v.5h-61zM124.5 256.5h60.5v.5h-60.5zM125 257h60.5v.5h-60.5zM125.5 257.5h60v.5h-60zM125.5 258h60v.5h-60zM125.5 258.5h60.5v.5h-60.5zM125.5 259h60.5v.5h-60.5zM125.5 259.5h61v.5h-61zM125.5 260h61v.5h-61zM125.5 260.5h61v.5h-61zM125 261h62v.5h-62zM125 261.5h62v.5h-62zM124.5 262h62.5v.5h-62.5zM124.5 262.5h63v.5h-63zM124 263h63.5v.5h-63.5zM123.5 263.5h64.5v.5h-64.5zM123.5 264h64.5v.5h-64.5zM123 264.5h65v.5h-65zM123 265h65.5v.5h-65.5zM122.5 265.5h66v.5h-66zM122.5 266h66v.5h-66zM122.5 266.5h66.5v.5h-66.5zM122 267h67v.5h-67zM122 267.5h67.5v.5h-67.5zM122 268h67.5v.5h-67.5zM122 268.5h67.5v.5h-67.5zM121.5 269h68.5v.5h-68.5zM121.5 269.5h68.5v.5h-68.5zM121.5 270h68.5v.5h-68.5zM121.5 270.5h68.5v.5h-68.5zM121.5 271h69v.5h-69zM122 271.5h68.5v.5h-68.5zM122 272h68.5v.5h-68.5zM122 272.5h68.5v.5h-68.5zM122 273h27v.5h-27zM156.5 273h34.5v.5h-34.5zM122.5 273.5h25.5v.5h-25.5zM157 273.5h34v.5h-34zM122.5 274h24.5v.5h-24.5zM157.5 274h33.5v.5h-33.5zM122.5 274.5h23.5v.5h-23.5zM158 274.5h33v.5h-33zM123 275h21.5v.5h-21.5zM158 275h33v.5h-33zM123.5 275.5h20v.5h-20zM158.5 275.5h32.5v.5h-32.5zM123.5 276h18.5v.5h-18.5zM159 276h32v.5h-32zM124 276.5h17v.5h-17zM159.5 276.5h31.5v.5h-31.5zM124.5 277h16v.5h-16zM160 277h31v.5h-31zM125 277.5h14.5v.5h-14.5zM160.5 277.5h30.5v.5h-30.5zM125.5 278h13.5v.5h-13.5zM161 278h30v.5h-30zM126 278.5h12.5v.5h-12.5zM161.5 278.5h29.5v.5h-29.5zM127 279h10.5v.5h-10.5zM162 279h29v.5h-29zM127.5 279.5h9v.5h-9zM162.5 279.5h28.5v.5h-28.5zM128.5 280h7v.5h-7zM163.5 280h27.5v.5h-27.5zM130.5 280.5h3v.5h-3zM164.5 280.5h26.5v.5h-26.5zM166 281h4v.5h-4zM172 281h18.5v.5h-18.5zM172.5 281.5h18v.5h-18zM173 282h17.5v.5h-17.5zM173.5 282.5h17v.5h-17zM173.5 283h16.5v.5h-16.5zM174 283.5h16v.5h-16zM174.5 284h15.5v.5h-15.5zM175 284.5h14.5v.5h-14.5zM175.5 285h9.5v.5h-9.5zM185.5 285h3.5v.5h-3.5zM176 285.5h8v.5h-8zM186 285.5h3v.5h-3zM176.5 286h7v.5h-7zM186.5 286h1.5v.5h-1.5zM177.5 286.5h5v.5h-5z', 'allowDelete': False},
    {'id': 'pponiping', 'name': '뽀니핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/pponiping.svg" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/pponiping.svg', 'outerPath': 'M160.5 12.5h1v.5h-1zM160 13h1.5v.5h-1.5zM159.5 13.5h2v.5h-2zM159 14h2.5v.5h-2.5zM158.5 14.5h3v.5h-3zM158 15h3.5v.5h-3.5zM157.5 15.5h4v.5h-4zM157 16h4.5v.5h-4.5zM156 16.5h5.5v.5h-5.5zM155.5 17h6v.5h-6zM184 17h13v.5h-13zM155 17.5h6v.5h-6zM180 17.5h21.5v.5h-21.5zM154.5 18h6.5v.5h-6.5zM177 18h27.5v.5h-27.5zM154 18.5h7v.5h-7zM174.5 18.5h32.5v.5h-32.5zM153.5 19h7.5v.5h-7.5zM172.5 19h37v.5h-37zM153 19.5h8v.5h-8zM171 19.5h40v.5h-40zM152.5 20h8.5v.5h-8.5zM169.5 20h43.5v.5h-43.5zM152.5 20.5h8.5v.5h-8.5zM168 20.5h46.5v.5h-46.5zM153 21h8v.5h-8zM166.5 21h49.5v.5h-49.5zM153 21.5h8v.5h-8zM165 21.5h52.5v.5h-52.5zM153.5 22h7v.5h-7zM164 22h54.5v.5h-54.5zM153.5 22.5h7.5v.5h-7.5zM163 22.5h57v.5h-57zM153 23h8.5v.5h-8.5zM162 23h59v.5h-59zM135.5 23.5h1.5v.5h-1.5zM149 23.5h1.5v.5h-1.5zM151.5 23.5h0.5v.5h-0.5zM152.5 23.5h69.5v.5h-69.5zM134 24h5v.5h-5zM146 24h77v.5h-77zM133 24.5h6.5v.5h-6.5zM144.5 24.5h79.5v.5h-79.5zM132.5 25h7.5v.5h-7.5zM143.5 25h81.5v.5h-81.5zM131.5 25.5h9v.5h-9zM142.5 25.5h83.5v.5h-83.5zM131 26h10v.5h-10zM141.5 26h85.5v.5h-85.5zM130.5 26.5h97.5v.5h-97.5zM130.5 27h98v.5h-98zM130 27.5h99.5v.5h-99.5zM129.5 28h101v.5h-101zM129.5 28.5h101.5v.5h-101.5zM129 29h103v.5h-103zM128.5 29.5h104v.5h-104zM128 30h105v.5h-105zM123.5 30.5h110.5v.5h-110.5zM122.5 31h112v.5h-112zM121.5 31.5h113.5v.5h-113.5zM121.5 32h114v.5h-114zM121 32.5h115v.5h-115zM120.5 33h116.5v.5h-116.5zM120 33.5h117.5v.5h-117.5zM120 34h118v.5h-118zM119.5 34.5h119v.5h-119zM119 35h120v.5h-120zM118.5 35.5h121v.5h-121zM116.5 36h123.5v.5h-123.5zM112 36.5h128.5v.5h-128.5zM109 37h131.5v.5h-131.5zM107 37.5h134v.5h-134zM105 38h136.5v.5h-136.5zM103.5 38.5h138.5v.5h-138.5zM102 39h140.5v.5h-140.5zM101 39.5h141.5v.5h-141.5zM100 40h143v.5h-143zM99 40.5h144.5v.5h-144.5zM98 41h146v.5h-146zM97 41.5h147v.5h-147zM96.5 42h148v.5h-148zM95.5 42.5h149.5v.5h-149.5zM95 43h150v.5h-150zM94.5 43.5h151v.5h-151zM93.5 44h152.5v.5h-152.5zM93 44.5h153v.5h-153zM92.5 45h154v.5h-154zM92 45.5h154.5v.5h-154.5zM91.5 46h155.5v.5h-155.5zM91 46.5h156.5v.5h-156.5zM90.5 47h157v.5h-157zM90 47.5h158v.5h-158zM89.5 48h158.5v.5h-158.5zM89 48.5h159.5v.5h-159.5zM88.5 49h160v.5h-160zM88 49.5h161v.5h-161zM87.5 50h161.5v.5h-161.5zM87 50.5h162v.5h-162zM86 51h163.5v.5h-163.5zM85 51.5h164.5v.5h-164.5zM84 52h166v.5h-166zM83 52.5h167v.5h-167zM82 53h168.5v.5h-168.5zM81 53.5h169.5v.5h-169.5zM80.5 54h170v.5h-170zM79.5 54.5h171.5v.5h-171.5zM78.5 55h172.5v.5h-172.5zM78 55.5h173v.5h-173zM77 56h174.5v.5h-174.5zM76.5 56.5h175v.5h-175zM76 57h175.5v.5h-175.5zM75 57.5h177v.5h-177zM74.5 58h177.5v.5h-177.5zM74 58.5h178v.5h-178zM73 59h179.5v.5h-179.5zM72.5 59.5h180v.5h-180zM72 60h180.5v.5h-180.5zM71.5 60.5h181v.5h-181zM71 61h182v.5h-182zM70 61.5h183v.5h-183zM69.5 62h183.5v.5h-183.5zM69 62.5h184v.5h-184zM68.5 63h185v.5h-185zM68 63.5h185.5v.5h-185.5zM67.5 64h186v.5h-186zM67 64.5h186.5v.5h-186.5zM66.5 65h187v.5h-187zM66 65.5h187.5v.5h-187.5zM66 66h188v.5h-188zM65.5 66.5h188.5v.5h-188.5zM65 67h189v.5h-189zM64.5 67.5h189.5v.5h-189.5zM64 68h190v.5h-190zM63.5 68.5h190.5v.5h-190.5zM63 69h191v.5h-191zM63 69.5h191.5v.5h-191.5zM62.5 70h192v.5h-192zM62 70.5h192.5v.5h-192.5zM61.5 71h193v.5h-193zM61 71.5h193.5v.5h-193.5zM61 72h193.5v.5h-193.5zM60.5 72.5h194v.5h-194zM60 73h194.5v.5h-194.5zM59.5 73.5h195v.5h-195zM59.5 74h195v.5h-195zM59 74.5h195.5v.5h-195.5zM58.5 75h196v.5h-196zM58.5 75.5h196v.5h-196zM58 76h196.5v.5h-196.5zM57.5 76.5h197v.5h-197zM57.5 77h197v.5h-197zM57 77.5h197.5v.5h-197.5zM57 78h197.5v.5h-197.5zM56.5 78.5h198v.5h-198zM56 79h198.5v.5h-198.5zM56 79.5h198.5v.5h-198.5zM55.5 80h199v.5h-199zM55.5 80.5h199v.5h-199zM55 81h199.5v.5h-199.5zM55 81.5h199.5v.5h-199.5zM54.5 82h200v.5h-200zM54.5 82.5h199.5v.5h-199.5zM54 83h200v.5h-200zM54 83.5h200v.5h-200zM53.5 84h200.5v.5h-200.5zM53.5 84.5h200.5v.5h-200.5zM53 85h201v.5h-201zM53 85.5h201v.5h-201zM52.5 86h201v.5h-201zM52.5 86.5h201v.5h-201zM52 87h201.5v.5h-201.5zM52 87.5h201.5v.5h-201.5zM52 88h201.5v.5h-201.5zM51.5 88.5h202v.5h-202zM51.5 89h201.5v.5h-201.5zM51.5 89.5h201.5v.5h-201.5zM51 90h202v.5h-202zM51 90.5h202v.5h-202zM51 91h202v.5h-202zM50.5 91.5h202v.5h-202zM50.5 92h202v.5h-202zM50 92.5h202.5v.5h-202.5zM50 93h202.5v.5h-202.5zM50 93.5h202v.5h-202zM50 94h202v.5h-202zM49.5 94.5h202.5v.5h-202.5zM49.5 95h202v.5h-202zM49.5 95.5h202v.5h-202zM49 96h202.5v.5h-202.5zM49 96.5h202v.5h-202zM49 97h202v.5h-202zM48.5 97.5h202v.5h-202zM48.5 98h202v.5h-202zM48.5 98.5h202v.5h-202zM48.5 99h201.5v.5h-201.5zM48 99.5h202v.5h-202zM48 100h201.5v.5h-201.5zM48 100.5h201.5v.5h-201.5zM48 101h201v.5h-201zM48 101.5h201v.5h-201zM47.5 102h201.5v.5h-201.5zM47.5 102.5h201v.5h-201zM47.5 103h201v.5h-201zM47.5 103.5h200.5v.5h-200.5zM47 104h201v.5h-201zM47 104.5h200.5v.5h-200.5zM47 105h200.5v.5h-200.5zM47 105.5h200v.5h-200zM47 106h199.5v.5h-199.5zM47 106.5h199.5v.5h-199.5zM46.5 107h199.5v.5h-199.5zM46.5 107.5h199.5v.5h-199.5zM46.5 108h199v.5h-199zM46.5 108.5h198.5v.5h-198.5zM46.5 109h198.5v.5h-198.5zM46.5 109.5h198v.5h-198zM46 110h198.5v.5h-198.5zM46 110.5h198v.5h-198zM46 111h197.5v.5h-197.5zM46 111.5h197.5v.5h-197.5zM46 112h197v.5h-197zM46 112.5h196.5v.5h-196.5zM46 113h196.5v.5h-196.5zM46 113.5h196v.5h-196zM45.5 114h196.5v.5h-196.5zM45.5 114.5h196v.5h-196zM45.5 115h195.5v.5h-195.5zM45.5 115.5h195.5v.5h-195.5zM45 116h195.5v.5h-195.5zM45 116.5h195.5v.5h-195.5zM45 117h195v.5h-195zM44.5 117.5h195v.5h-195zM44.5 118h195v.5h-195zM44.5 118.5h194.5v.5h-194.5zM44 119h195v.5h-195zM44 119.5h195v.5h-195zM44 120h194.5v.5h-194.5zM43.5 120.5h195v.5h-195zM43.5 121h195v.5h-195zM43 121.5h195.5v.5h-195.5zM43 122h195.5v.5h-195.5zM42.5 122.5h196v.5h-196zM42.5 123h196v.5h-196zM42.5 123.5h196.5v.5h-196.5zM42 124h197v.5h-197zM42 124.5h197v.5h-197zM41.5 125h198v.5h-198zM41.5 125.5h198v.5h-198zM41 126h199v.5h-199zM41 126.5h199v.5h-199zM41 127h199.5v.5h-199.5zM40.5 127.5h200v.5h-200zM40.5 128h200.5v.5h-200.5zM40 128.5h201.5v.5h-201.5zM40 129h201.5v.5h-201.5zM39.5 129.5h202.5v.5h-202.5zM39.5 130h202.5v.5h-202.5zM39 130.5h203.5v.5h-203.5zM39 131h204v.5h-204zM39 131.5h204v.5h-204zM38.5 132h205v.5h-205zM38.5 132.5h205.5v.5h-205.5zM38 133h206v.5h-206zM38 133.5h206.5v.5h-206.5zM37.5 134h207.5v.5h-207.5zM37.5 134.5h207.5v.5h-207.5zM37.5 135h208v.5h-208zM37 135.5h208.5v.5h-208.5zM37 136h209v.5h-209zM37 136.5h209.5v.5h-209.5zM36.5 137h210v.5h-210zM36.5 137.5h210.5v.5h-210.5zM36.5 138h210.5v.5h-210.5zM36 138.5h211.5v.5h-211.5zM36 139h212v.5h-212zM36 139.5h212v.5h-212zM36 140h212.5v.5h-212.5zM36 140.5h212.5v.5h-212.5zM35.5 141h213.5v.5h-213.5zM35.5 141.5h213.5v.5h-213.5zM35.5 142h213.5v.5h-213.5zM35.5 142.5h214v.5h-214zM35.5 143h214v.5h-214zM35.5 143.5h214.5v.5h-214.5zM35.5 144h214.5v.5h-214.5zM35.5 144.5h215v.5h-215zM35.5 145h215v.5h-215zM35.5 145.5h215.5v.5h-215.5zM35.5 146h215.5v.5h-215.5zM35.5 146.5h215.5v.5h-215.5zM36 147h215.5v.5h-215.5zM36 147.5h215.5v.5h-215.5zM36 148h215.5v.5h-215.5zM36 148.5h216v.5h-216zM36.5 149h215.5v.5h-215.5zM36.5 149.5h215.5v.5h-215.5zM36.5 150h216v.5h-216zM36.5 150.5h216v.5h-216zM37 151h215.5v.5h-215.5zM37 151.5h215.5v.5h-215.5zM37 152h216v.5h-216zM37.5 152.5h215.5v.5h-215.5zM37.5 153h215.5v.5h-215.5zM38 153.5h215v.5h-215zM38 154h215v.5h-215zM38.5 154.5h214.5v.5h-214.5zM38.5 155h215v.5h-215zM39 155.5h214.5v.5h-214.5zM39 156h214.5v.5h-214.5zM39.5 156.5h214v.5h-214zM39.5 157h214v.5h-214zM40 157.5h213.5v.5h-213.5zM40 158h213.5v.5h-213.5zM40.5 158.5h213v.5h-213zM41 159h212.5v.5h-212.5zM41 159.5h212.5v.5h-212.5zM41.5 160h212v.5h-212zM42 160.5h211.5v.5h-211.5zM42.5 161h211v.5h-211zM42.5 161.5h211v.5h-211zM43 162h210.5v.5h-210.5zM43.5 162.5h210v.5h-210zM44 163h209.5v.5h-209.5zM44 163.5h209v.5h-209zM44.5 164h208.5v.5h-208.5zM45 164.5h208v.5h-208zM45.5 165h207.5v.5h-207.5zM46 165.5h207v.5h-207zM46.5 166h206.5v.5h-206.5zM39 166.5h3.5v.5h-3.5zM46 166.5h206.5v.5h-206.5zM37 167h7v.5h-7zM45.5 167h207v.5h-207zM36 167.5h216.5v.5h-216.5zM35.5 168h217v.5h-217zM35 168.5h217v.5h-217zM34.5 169h217.5v.5h-217.5zM34 169.5h218v.5h-218zM34 170h217.5v.5h-217.5zM33.5 170.5h218v.5h-218zM33.5 171h218v.5h-218zM33.5 171.5h217.5v.5h-217.5zM33.5 172h217.5v.5h-217.5zM33.5 172.5h217.5v.5h-217.5zM33.5 173h217v.5h-217zM33.5 173.5h217v.5h-217zM33.5 174h216.5v.5h-216.5zM34 174.5h216v.5h-216zM34 175h215.5v.5h-215.5zM34.5 175.5h215v.5h-215zM35 176h214v.5h-214zM35 176.5h214v.5h-214zM35.5 177h213v.5h-213zM36 177.5h212.5v.5h-212.5zM36.5 178h211.5v.5h-211.5zM37.5 178.5h210.5v.5h-210.5zM38 179h209.5v.5h-209.5zM38.5 179.5h209v.5h-209zM39 180h208v.5h-208zM39.5 180.5h207v.5h-207zM40.5 181h206v.5h-206zM41 181.5h205v.5h-205zM42 182h204v.5h-204zM42.5 182.5h203v.5h-203zM43.5 183h201.5v.5h-201.5zM44 183.5h201v.5h-201zM44.5 184h200v.5h-200zM45.5 184.5h198.5v.5h-198.5zM46 185h198v.5h-198zM46.5 185.5h197v.5h-197zM47.5 186h195.5v.5h-195.5zM48 186.5h195v.5h-195zM48.5 187h195v.5h-195zM49 187.5h195v.5h-195zM49.5 188h205v.5h-205zM50 188.5h207v.5h-207zM50.5 189h208v.5h-208zM51 189.5h209v.5h-209zM51 190h210v.5h-210zM51.5 190.5h210.5v.5h-210.5zM51.5 191h211.5v.5h-211.5zM52 191.5h211.5v.5h-211.5zM52.5 192h212v.5h-212zM52.5 192.5h212.5v.5h-212.5zM53 193h212.5v.5h-212.5zM53 193.5h213v.5h-213zM53 194h213.5v.5h-213.5zM53.5 194.5h213.5v.5h-213.5zM53.5 195h214v.5h-214zM53.5 195.5h214.5v.5h-214.5zM53 196h215.5v.5h-215.5zM53 196.5h215.5v.5h-215.5zM53 197h216v.5h-216zM52.5 197.5h217v.5h-217zM52.5 198h217v.5h-217zM52.5 198.5h217v.5h-217zM52.5 199h217.5v.5h-217.5zM52 199.5h218v.5h-218zM52 200h218.5v.5h-218.5zM52 200.5h218.5v.5h-218.5zM51.5 201h219v.5h-219zM51.5 201.5h219.5v.5h-219.5zM51.5 202h219.5v.5h-219.5zM51.5 202.5h72v.5h-72zM126 202.5h145v.5h-145zM51 203h72v.5h-72zM129 203h13.5v.5h-13.5zM143.5 203h127.5v.5h-127.5zM51 203.5h71.5v.5h-71.5zM133 203.5h6.5v.5h-6.5zM144 203.5h127.5v.5h-127.5zM51 204h71.5v.5h-71.5zM144.5 204h127v.5h-127zM51 204.5h71.5v.5h-71.5zM144.5 204.5h127v.5h-127zM50.5 205h72v.5h-72zM144.5 205h127v.5h-127zM50.5 205.5h72v.5h-72zM144.5 205.5h127v.5h-127zM50.5 206h72v.5h-72zM144.5 206h127v.5h-127zM50.5 206.5h72v.5h-72zM144.5 206.5h127v.5h-127zM50 207h72.5v.5h-72.5zM144.5 207h127v.5h-127zM50 207.5h72v.5h-72zM144.5 207.5h127v.5h-127zM50 208h72v.5h-72zM144.5 208h127v.5h-127zM50 208.5h72.5v.5h-72.5zM144.5 208.5h127v.5h-127zM49.5 209h73.5v.5h-73.5zM144.5 209h127v.5h-127zM49 209.5h74.5v.5h-74.5zM144.5 209.5h127v.5h-127zM48.5 210h75.5v.5h-75.5zM145 210h126.5v.5h-126.5zM48 210.5h76.5v.5h-76.5zM145 210.5h126.5v.5h-126.5zM47 211h78.5v.5h-78.5zM145 211h126v.5h-126zM45.5 211.5h80.5v.5h-80.5zM145 211.5h126v.5h-126zM44.5 212h82.5v.5h-82.5zM145 212h126v.5h-126zM43.5 212.5h85v.5h-85zM145 212.5h126v.5h-126zM42.5 213h87.5v.5h-87.5zM145 213h125.5v.5h-125.5zM41.5 213.5h90v.5h-90zM145 213.5h125.5v.5h-125.5zM40.5 214h92v.5h-92zM145.5 214h125v.5h-125zM40 214.5h93.5v.5h-93.5zM145.5 214.5h125v.5h-125zM39.5 215h94.5v.5h-94.5zM145.5 215h124.5v.5h-124.5zM38.5 215.5h95.5v.5h-95.5zM145.5 215.5h124.5v.5h-124.5zM38 216h96.5v.5h-96.5zM145.5 216h124v.5h-124zM37.5 216.5h97v.5h-97zM146 216.5h123.5v.5h-123.5zM37 217h98v.5h-98zM146 217h123.5v.5h-123.5zM36.5 217.5h98.5v.5h-98.5zM146 217.5h123v.5h-123zM36 218h99v.5h-99zM146 218h123v.5h-123zM35.5 218.5h99.5v.5h-99.5zM146.5 218.5h122v.5h-122zM35 219h100v.5h-100zM146.5 219h121.5v.5h-121.5zM35 219.5h100v.5h-100zM146.5 219.5h121.5v.5h-121.5zM34.5 220h100v.5h-100zM146.5 220h121v.5h-121zM34 220.5h100.5v.5h-100.5zM147 220.5h120.5v.5h-120.5zM33.5 221h101v.5h-101zM147 221h120v.5h-120zM33.5 221.5h100.5v.5h-100.5zM147 221.5h120v.5h-120zM33 222h101v.5h-101zM147.5 222h119v.5h-119zM33 222.5h100.5v.5h-100.5zM147.5 222.5h118.5v.5h-118.5zM32.5 223h100.5v.5h-100.5zM147.5 223h118.5v.5h-118.5zM32.5 223.5h100.5v.5h-100.5zM148 223.5h117.5v.5h-117.5zM32 224h100.5v.5h-100.5zM148 224h117v.5h-117zM32 224.5h100v.5h-100zM148.5 224.5h116.5v.5h-116.5zM31.5 225h99.5v.5h-99.5zM148.5 225h116v.5h-116zM31.5 225.5h99v.5h-99zM148.5 225.5h115.5v.5h-115.5zM31 226h99v.5h-99zM149 226h115v.5h-115zM31 226.5h98v.5h-98zM149 226.5h114.5v.5h-114.5zM31 227h96.5v.5h-96.5zM149.5 227h113.5v.5h-113.5zM30.5 227.5h95v.5h-95zM149.5 227.5h113.5v.5h-113.5zM30.5 228h92.5v.5h-92.5zM150 228h112.5v.5h-112.5zM30.5 228.5h92v.5h-92zM150 228.5h112v.5h-112zM30.5 229h91.5v.5h-91.5zM150.5 229h111v.5h-111zM30 229.5h92.5v.5h-92.5zM150.5 229.5h111v.5h-111zM29.5 230h93.5v.5h-93.5zM151 230h110v.5h-110zM29 230.5h94.5v.5h-94.5zM151 230.5h109.5v.5h-109.5zM28.5 231h95.5v.5h-95.5zM151.5 231h108.5v.5h-108.5zM28 231.5h96.5v.5h-96.5zM152 231.5h107.5v.5h-107.5zM28 232h97v.5h-97zM152 232h107.5v.5h-107.5zM27.5 232.5h98v.5h-98zM152.5 232.5h106.5v.5h-106.5zM27 233h99v.5h-99zM153 233h105.5v.5h-105.5zM27 233.5h99.5v.5h-99.5zM153 233.5h105v.5h-105zM27 234h100v.5h-100zM153.5 234h104v.5h-104zM27 234.5h100.5v.5h-100.5zM154 234.5h103v.5h-103zM27 235h101v.5h-101zM154 235h102.5v.5h-102.5zM27 235.5h101v.5h-101zM154.5 235.5h101.5v.5h-101.5zM27 236h101.5v.5h-101.5zM155 236h100.5v.5h-100.5zM27 236.5h102v.5h-102zM155.5 236.5h99.5v.5h-99.5zM27 237h102.5v.5h-102.5zM155.5 237h99v.5h-99zM27 237.5h102.5v.5h-102.5zM156 237.5h98v.5h-98zM27 238h103v.5h-103zM156.5 238h97v.5h-97zM27.5 238.5h103v.5h-103zM157 238.5h96v.5h-96zM27.5 239h103v.5h-103zM157.5 239h95v.5h-95zM27.5 239.5h103.5v.5h-103.5zM158 239.5h94v.5h-94zM28 240h103.5v.5h-103.5zM158.5 240h93v.5h-93zM28 240.5h103.5v.5h-103.5zM159 240.5h91.5v.5h-91.5zM28.5 241h103.5v.5h-103.5zM159.5 241h90.5v.5h-90.5zM28.5 241.5h103.5v.5h-103.5zM160 241.5h89.5v.5h-89.5zM29 242h103.5v.5h-103.5zM160.5 242h88.5v.5h-88.5zM29.5 242.5h103.5v.5h-103.5zM161 242.5h87v.5h-87zM29.5 243h103.5v.5h-103.5zM161.5 243h86v.5h-86zM29.5 243.5h104v.5h-104zM162 243.5h84.5v.5h-84.5zM30 244h103.5v.5h-103.5zM162.5 244h83.5v.5h-83.5zM30 244.5h104v.5h-104zM163 244.5h82.5v.5h-82.5zM30 245h104.5v.5h-104.5zM164 245h80.5v.5h-80.5zM30 245.5h105.5v.5h-105.5zM164.5 245.5h79v.5h-79zM30.5 246h106v.5h-106zM165.5 246h77.5v.5h-77.5zM30.5 246.5h106.5v.5h-106.5zM166 246.5h76v.5h-76zM30.5 247h107v.5h-107zM166.5 247h74.5v.5h-74.5zM31 247.5h107v.5h-107zM167.5 247.5h72.5v.5h-72.5zM31.5 248h107v.5h-107zM168 248h71.5v.5h-71.5zM31.5 248.5h107.5v.5h-107.5zM169 248.5h69.5v.5h-69.5zM32 249h107v.5h-107zM170 249h67.5v.5h-67.5zM33 249.5h106v.5h-106zM171 249.5h65v.5h-65zM33.5 250h105.5v.5h-105.5zM171.5 250h63.5v.5h-63.5zM34.5 250.5h104.5v.5h-104.5zM173 250.5h60.5v.5h-60.5zM35.5 251h103.5v.5h-103.5zM173.5 251h59v.5h-59zM36.5 251.5h102v.5h-102zM174.5 251.5h57v.5h-57zM37.5 252h100.5v.5h-100.5zM176 252h54v.5h-54zM38 252.5h99.5v.5h-99.5zM177 252.5h51.5v.5h-51.5zM38.5 253h98v.5h-98zM178.5 253h48.5v.5h-48.5zM39 253.5h96v.5h-96zM179.5 253.5h46v.5h-46zM39.5 254h94v.5h-94zM181 254h43v.5h-43zM40 254.5h93v.5h-93zM182.5 254.5h39.5v.5h-39.5zM40.5 255h92v.5h-92zM184.5 255h35.5v.5h-35.5zM41 255.5h91v.5h-91zM186.5 255.5h31.5v.5h-31.5zM41.5 256h90v.5h-90zM188.5 256h27v.5h-27zM42 256.5h89v.5h-89zM191 256.5h21.5v.5h-21.5zM43 257h87v.5h-87zM195 257h13.5v.5h-13.5zM44 257.5h84.5v.5h-84.5zM45.5 258h77v.5h-77zM49 258.5h72v.5h-72zM50.5 259h69.5v.5h-69.5zM51 259.5h67.5v.5h-67.5zM51.5 260h66.5v.5h-66.5zM52 260.5h65.5v.5h-65.5zM52 261h65.5v.5h-65.5zM52 261.5h66v.5h-66zM52.5 262h65.5v.5h-65.5zM52.5 262.5h66v.5h-66zM52.5 263h66v.5h-66zM53 263.5h66v.5h-66zM53 264h66v.5h-66zM53 264.5h66.5v.5h-66.5zM53 265h66.5v.5h-66.5zM53 265.5h67v.5h-67zM53 266h67v.5h-67zM53 266.5h67.5v.5h-67.5zM53 267h31v.5h-31zM93 267h27.5v.5h-27.5zM53 267.5h21v.5h-21zM76 267.5h3.5v.5h-3.5zM93.5 267.5h27.5v.5h-27.5zM53 268h20.5v.5h-20.5zM94 268h27.5v.5h-27.5zM53 268.5h20v.5h-20zM94.5 268.5h27v.5h-27zM53 269h20v.5h-20zM95 269h27v.5h-27zM53 269.5h20.5v.5h-20.5zM95.5 269.5h27v.5h-27zM53 270h20.5v.5h-20.5zM96 270h27v.5h-27zM53 270.5h21v.5h-21zM96.5 270.5h27v.5h-27zM53 271h21v.5h-21zM97 271h27v.5h-27zM53 271.5h21.5v.5h-21.5zM98 271.5h26.5v.5h-26.5zM53 272h21.5v.5h-21.5zM98.5 272h26v.5h-26zM52.5 272.5h22v.5h-22zM99 272.5h26v.5h-26zM52.5 273h22v.5h-22zM99.5 273h26v.5h-26zM52.5 273.5h22v.5h-22zM100 273.5h25.5v.5h-25.5zM52.5 274h21.5v.5h-21.5zM100.5 274h25v.5h-25zM52.5 274.5h21.5v.5h-21.5zM101 274.5h25v.5h-25zM52.5 275h21v.5h-21zM101.5 275h24.5v.5h-24.5zM52.5 275.5h21v.5h-21zM102 275.5h24v.5h-24zM52.5 276h20v.5h-20zM102.5 276h23.5v.5h-23.5zM52.5 276.5h19v.5h-19zM103 276.5h22.5v.5h-22.5zM53 277h17.5v.5h-17.5zM103 277h22.5v.5h-22.5zM54 277.5h14.5v.5h-14.5zM103.5 277.5h21.5v.5h-21.5zM55.5 278h11v.5h-11zM104 278h21v.5h-21zM59 278.5h2.5v.5h-2.5zM104 278.5h20.5v.5h-20.5zM104.5 279h19.5v.5h-19.5zM104.5 279.5h19v.5h-19zM104.5 280h18.5v.5h-18.5zM105 280.5h17.5v.5h-17.5zM105 281h17v.5h-17zM105.5 281.5h16v.5h-16zM105.5 282h15v.5h-15zM105.5 282.5h14.5v.5h-14.5zM106 283h13.5v.5h-13.5zM106 283.5h12.5v.5h-12.5zM106 284h11.5v.5h-11.5zM106.5 284.5h10v.5h-10zM107 285h8.5v.5h-8.5zM107.5 285.5h7v.5h-7zM108 286h4.5v.5h-4.5z', 'allowDelete': False},
    {'id': 'dianaping', 'name': '다이아나핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/dianaping.svg" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/dianaping.svg', 'outerPath': 'M128 12.5h1.5v.5h-1.5zM127 13h3.5v.5h-3.5zM126.5 13.5h4.5v.5h-4.5zM126 14h5.5v.5h-5.5zM126 14.5h5.5v.5h-5.5zM125.5 15h6.5v.5h-6.5zM125.5 15.5h6.5v.5h-6.5zM125.5 16h6.5v.5h-6.5zM125.5 16.5h6.5v.5h-6.5zM125 17h7v.5h-7zM125 17.5h7v.5h-7zM125 18h7v.5h-7zM125 18.5h7v.5h-7zM125.5 19h6.5v.5h-6.5zM125.5 19.5h6.5v.5h-6.5zM125.5 20h6.5v.5h-6.5zM126 20.5h5.5v.5h-5.5zM126 21h5.5v.5h-5.5zM126 21.5h5.5v.5h-5.5zM126.5 22h4.5v.5h-4.5zM127 22.5h3.5v.5h-3.5zM127 23h3.5v.5h-3.5zM127 23.5h3.5v.5h-3.5zM127 24h3.5v.5h-3.5zM126.5 24.5h4v.5h-4zM126.5 25h4v.5h-4zM192.5 25h2.5v.5h-2.5zM126.5 25.5h4v.5h-4zM191.5 25.5h4v.5h-4zM126.5 26h4v.5h-4zM191 26h5v.5h-5zM126.5 26.5h4v.5h-4zM190.5 26.5h5.5v.5h-5.5zM126.5 27h4v.5h-4zM190.5 27h6v.5h-6zM126.5 27.5h4v.5h-4zM190 27.5h6.5v.5h-6.5zM126 28h4.5v.5h-4.5zM189.5 28h7v.5h-7zM126 28.5h4.5v.5h-4.5zM189.5 28.5h7v.5h-7zM126 29h4.5v.5h-4.5zM189.5 29h7v.5h-7zM126 29.5h4.5v.5h-4.5zM189 29.5h7.5v.5h-7.5zM126 30h4.5v.5h-4.5zM189 30h7.5v.5h-7.5zM126 30.5h4.5v.5h-4.5zM150.5 30.5h2.5v.5h-2.5zM189 30.5h7.5v.5h-7.5zM126 31h4.5v.5h-4.5zM141.5 31h1v.5h-1zM149.5 31h4v.5h-4zM189 31h7.5v.5h-7.5zM125.5 31.5h5v.5h-5zM140.5 31.5h3v.5h-3zM149 31.5h5v.5h-5zM189 31.5h7v.5h-7zM125 32h5.5v.5h-5.5zM140 32h4v.5h-4zM148.5 32h5.5v.5h-5.5zM189 32h7v.5h-7zM124.5 32.5h6.5v.5h-6.5zM139.5 32.5h5v.5h-5zM148 32.5h6.5v.5h-6.5zM189 32.5h6.5v.5h-6.5zM124 33h7v.5h-7zM139.5 33h5.5v.5h-5.5zM147.5 33h7v.5h-7zM189 33h6.5v.5h-6.5zM123.5 33.5h7.5v.5h-7.5zM139 33.5h6.5v.5h-6.5zM147 33.5h7.5v.5h-7.5zM189 33.5h6v.5h-6zM123 34h8v.5h-8zM139 34h7v.5h-7zM146.5 34h8v.5h-8zM189 34h5.5v.5h-5.5zM122 34.5h9v.5h-9zM139 34.5h15.5v.5h-15.5zM188.5 34.5h5.5v.5h-5.5zM121.5 35h9.5v.5h-9.5zM139 35h16v.5h-16zM188.5 35h5v.5h-5zM121 35.5h10v.5h-10zM138.5 35.5h16.5v.5h-16.5zM188 35.5h5v.5h-5zM120.5 36h10.5v.5h-10.5zM138.5 36h16v.5h-16zM187.5 36h5.5v.5h-5.5zM120.5 36.5h10.5v.5h-10.5zM138.5 36.5h16v.5h-16zM187.5 36.5h5.5v.5h-5.5zM120.5 37h11v.5h-11zM138.5 37h16v.5h-16zM187 37h6v.5h-6zM120 37.5h11.5v.5h-11.5zM139 37.5h15.5v.5h-15.5zM186.5 37.5h6.5v.5h-6.5zM120 38h11.5v.5h-11.5zM139 38h15v.5h-15zM186.5 38h6.5v.5h-6.5zM120 38.5h11.5v.5h-11.5zM139 38.5h15v.5h-15zM186 38.5h7v.5h-7zM120 39h11.5v.5h-11.5zM139 39h15v.5h-15zM185.5 39h7.5v.5h-7.5zM120 39.5h11.5v.5h-11.5zM139.5 39.5h14v.5h-14zM185.5 39.5h7.5v.5h-7.5zM120 40h11.5v.5h-11.5zM139 40h14v.5h-14zM185 40h7.5v.5h-7.5zM120 40.5h11.5v.5h-11.5zM139 40.5h14v.5h-14zM184.5 40.5h8v.5h-8zM120.5 41h11.5v.5h-11.5zM139 41h13.5v.5h-13.5zM184.5 41h8v.5h-8zM120.5 41.5h11.5v.5h-11.5zM138.5 41.5h14v.5h-14zM184 41.5h8.5v.5h-8.5zM121 42h11v.5h-11zM138.5 42h14v.5h-14zM183.5 42h9v.5h-9zM121.5 42.5h10.5v.5h-10.5zM138.5 42.5h14v.5h-14zM183.5 42.5h9v.5h-9zM121.5 43h11v.5h-11zM138 43h15v.5h-15zM183 43h9.5v.5h-9.5zM121.5 43.5h11.5v.5h-11.5zM137.5 43.5h15.5v.5h-15.5zM182.5 43.5h10v.5h-10zM121.5 44h12v.5h-12zM137 44h16v.5h-16zM182.5 44h10v.5h-10zM121.5 44.5h12.5v.5h-12.5zM136.5 44.5h16.5v.5h-16.5zM182 44.5h10.5v.5h-10.5zM121.5 45h13v.5h-13zM136 45h17v.5h-17zM181.5 45h11v.5h-11zM121.5 45.5h13.5v.5h-13.5zM135.5 45.5h17.5v.5h-17.5zM181 45.5h11.5v.5h-11.5zM121.5 46h31.5v.5h-31.5zM181 46h11.5v.5h-11.5zM121.5 46.5h32v.5h-32zM180.5 46.5h12v.5h-12zM121.5 47h32v.5h-32zM180 47h12v.5h-12zM121.5 47.5h32v.5h-32zM179.5 47.5h12.5v.5h-12.5zM237.5 47.5h1v.5h-1zM121.5 48h32v.5h-32zM179 48h13v.5h-13zM236 48h4v.5h-4zM121.5 48.5h32v.5h-32zM179 48.5h13v.5h-13zM235.5 48.5h5v.5h-5zM121.5 49h32.5v.5h-32.5zM178.5 49h13.5v.5h-13.5zM235 49h5.5v.5h-5.5zM121.5 49.5h32.5v.5h-32.5zM178 49.5h14v.5h-14zM234.5 49.5h6v.5h-6zM121.5 50h32.5v.5h-32.5zM177.5 50h14.5v.5h-14.5zM203.5 50h2.5v.5h-2.5zM217.5 50h3.5v.5h-3.5zM234 50h7v.5h-7zM121.5 50.5h32.5v.5h-32.5zM177 50.5h15v.5h-15zM202.5 50.5h4v.5h-4zM216.5 50.5h5v.5h-5zM233.5 50.5h7v.5h-7zM121.5 51h32.5v.5h-32.5zM176.5 51h15.5v.5h-15.5zM202 51h5v.5h-5zM216 51h6v.5h-6zM233 51h7.5v.5h-7.5zM121.5 51.5h33v.5h-33zM176.5 51.5h15.5v.5h-15.5zM201.5 51.5h5.5v.5h-5.5zM215.5 51.5h6.5v.5h-6.5zM232.5 51.5h8v.5h-8zM121.5 52h33v.5h-33zM176 52h16v.5h-16zM201.5 52h6v.5h-6zM215 52h7v.5h-7zM232.5 52h8v.5h-8zM121.5 52.5h33v.5h-33zM175.5 52.5h16.5v.5h-16.5zM201 52.5h6.5v.5h-6.5zM215 52.5h7v.5h-7zM232 52.5h8v.5h-8zM121.5 53h33v.5h-33zM175 53h17v.5h-17zM201 53h6.5v.5h-6.5zM214.5 53h7.5v.5h-7.5zM232 53h8v.5h-8zM121.5 53.5h33v.5h-33zM174.5 53.5h17.5v.5h-17.5zM200.5 53.5h7v.5h-7zM214 53.5h8v.5h-8zM232 53.5h7.5v.5h-7.5zM121 54h34v.5h-34zM174 54h18v.5h-18zM200.5 54h6.5v.5h-6.5zM214 54h8v.5h-8zM232 54h7.5v.5h-7.5zM121 54.5h34v.5h-34zM167 54.5h1.5v.5h-1.5zM173.5 54.5h18.5v.5h-18.5zM200.5 54.5h6.5v.5h-6.5zM214 54.5h8v.5h-8zM232 54.5h7v.5h-7zM121 55h34v.5h-34zM166 55h3.5v.5h-3.5zM173 55h19v.5h-19zM200 55h7v.5h-7zM213.5 55h8.5v.5h-8.5zM232 55h6.5v.5h-6.5zM121 55.5h34v.5h-34zM165.5 55.5h4.5v.5h-4.5zM172.5 55.5h19.5v.5h-19.5zM200 55.5h6.5v.5h-6.5zM213.5 55.5h8v.5h-8zM232.5 55.5h5.5v.5h-5.5zM121 56h34.5v.5h-34.5zM165 56h5.5v.5h-5.5zM172 56h20v.5h-20zM200 56h6.5v.5h-6.5zM213.5 56h8v.5h-8zM232 56h5.5v.5h-5.5zM121 56.5h34.5v.5h-34.5zM165 56.5h6v.5h-6zM171.5 56.5h20.5v.5h-20.5zM200.5 56.5h5.5v.5h-5.5zM213 56.5h8v.5h-8zM231.5 56.5h5.5v.5h-5.5zM121 57h34.5v.5h-34.5zM164.5 57h27.5v.5h-27.5zM200.5 57h5v.5h-5zM213 57h8v.5h-8zM231.5 57h5v.5h-5zM121 57.5h34.5v.5h-34.5zM164.5 57.5h27.5v.5h-27.5zM200 57.5h5v.5h-5zM213 57.5h7.5v.5h-7.5zM231 57.5h5v.5h-5zM121 58h35v.5h-35zM164.5 58h27.5v.5h-27.5zM199.5 58h5v.5h-5zM213.5 58h6.5v.5h-6.5zM230.5 58h5v.5h-5zM120.5 58.5h35.5v.5h-35.5zM164.5 58.5h27.5v.5h-27.5zM199 58.5h5v.5h-5zM213 58.5h6.5v.5h-6.5zM230.5 58.5h4.5v.5h-4.5zM120.5 59h35.5v.5h-35.5zM164 59h28v.5h-28zM198.5 59h5.5v.5h-5.5zM212.5 59h6.5v.5h-6.5zM230 59h4.5v.5h-4.5zM120.5 59.5h35.5v.5h-35.5zM164 59.5h28v.5h-28zM198.5 59.5h5v.5h-5zM212 59.5h6.5v.5h-6.5zM229.5 59.5h4.5v.5h-4.5zM120.5 60h35.5v.5h-35.5zM164 60h28.5v.5h-28.5zM198 60h5.5v.5h-5.5zM211.5 60h6.5v.5h-6.5zM229 60h4.5v.5h-4.5zM120.5 60.5h36v.5h-36zM164.5 60.5h28.5v.5h-28.5zM197.5 60.5h6v.5h-6zM211 60.5h6.5v.5h-6.5zM229 60.5h4.5v.5h-4.5zM120.5 61h36v.5h-36zM164.5 61h29v.5h-29zM197 61h6.5v.5h-6.5zM210.5 61h6.5v.5h-6.5zM228.5 61h4.5v.5h-4.5zM120.5 61.5h36v.5h-36zM164.5 61.5h29.5v.5h-29.5zM196.5 61.5h6.5v.5h-6.5zM210 61.5h6.5v.5h-6.5zM228 61.5h5v.5h-5zM120.5 62h36v.5h-36zM165 62h29.5v.5h-29.5zM196 62h7v.5h-7zM209.5 62h6.5v.5h-6.5zM227.5 62h5v.5h-5zM120.5 62.5h36.5v.5h-36.5zM165 62.5h30v.5h-30zM195.5 62.5h8v.5h-8zM209 62.5h7v.5h-7zM227 62.5h5v.5h-5zM120 63h37v.5h-37zM164.5 63h39.5v.5h-39.5zM208.5 63h8v.5h-8zM223 63h0.5v.5h-0.5zM226.5 63h5.5v.5h-5.5zM120 63.5h37v.5h-37zM164 63.5h40.5v.5h-40.5zM208 63.5h9v.5h-9zM221.5 63.5h3v.5h-3zM226 63.5h5.5v.5h-5.5zM120 64h37v.5h-37zM163.5 64h41.5v.5h-41.5zM207.5 64h10v.5h-10zM221 64h4v.5h-4zM225.5 64h6v.5h-6zM120 64.5h37.5v.5h-37.5zM163 64.5h42.5v.5h-42.5zM207 64.5h11v.5h-11zM220.5 64.5h10.5v.5h-10.5zM120 65h38v.5h-38zM162.5 65h43.5v.5h-43.5zM206.5 65h12v.5h-12zM220 65h11v.5h-11zM119.5 65.5h39v.5h-39zM162 65.5h57v.5h-57zM219.5 65.5h11v.5h-11zM119.5 66h39.5v.5h-39.5zM161.5 66h69v.5h-69zM119.5 66.5h40v.5h-40zM161 66.5h69v.5h-69zM119 67h41v.5h-41zM160.5 67h69v.5h-69zM119 67.5h110.5v.5h-110.5zM119 68h110v.5h-110zM118.5 68.5h110.5v.5h-110.5zM118.5 69h110v.5h-110zM118 69.5h110.5v.5h-110.5zM118 70h110v.5h-110zM118 70.5h109.5v.5h-109.5zM118.5 71h109v.5h-109zM118.5 71.5h108.5v.5h-108.5zM119 72h108v.5h-108zM119 72.5h107.5v.5h-107.5zM119 73h107v.5h-107zM119 73.5h107v.5h-107zM119 74h106.5v.5h-106.5zM119 74.5h106.5v.5h-106.5zM119 75h106v.5h-106zM119 75.5h105.5v.5h-105.5zM119 76h105.5v.5h-105.5zM119 76.5h105v.5h-105zM119 77h104.5v.5h-104.5zM118.5 77.5h105v.5h-105zM118.5 78h104.5v.5h-104.5zM118.5 78.5h104v.5h-104zM118.5 79h104v.5h-104zM118.5 79.5h103.5v.5h-103.5zM119 80h102.5v.5h-102.5zM119 80.5h102.5v.5h-102.5zM119 81h102v.5h-102zM119 81.5h101.5v.5h-101.5zM118.5 82h102v.5h-102zM118 82.5h102v.5h-102zM118 83h102v.5h-102zM118 83.5h101.5v.5h-101.5zM117.5 84h101.5v.5h-101.5zM117.5 84.5h101.5v.5h-101.5zM117.5 85h101v.5h-101zM117.5 85.5h101v.5h-101zM117.5 86h100.5v.5h-100.5zM118 86.5h99.5v.5h-99.5zM118.5 87h99v.5h-99zM118.5 87.5h98.5v.5h-98.5zM118 88h99v.5h-99zM117.5 88.5h99v.5h-99zM117 89h99v.5h-99zM117 89.5h99v.5h-99zM117 90h98.5v.5h-98.5zM117 90.5h98.5v.5h-98.5zM117.5 91h97.5v.5h-97.5zM117.5 91.5h97v.5h-97zM117.5 92h97v.5h-97zM117.5 92.5h96.5v.5h-96.5zM117.5 93h96.5v.5h-96.5zM117.5 93.5h96.5v.5h-96.5zM117 94h97v.5h-97zM117 94.5h97v.5h-97zM117 95h97v.5h-97zM117 95.5h97v.5h-97zM116.5 96h97v.5h-97zM116.5 96.5h96.5v.5h-96.5zM116 97h96.5v.5h-96.5zM115.5 97.5h96.5v.5h-96.5zM115 98h96.5v.5h-96.5zM114.5 98.5h96.5v.5h-96.5zM114 99h96.5v.5h-96.5zM113.5 99.5h97v.5h-97zM112.5 100h97.5v.5h-97.5zM112 100.5h98v.5h-98zM111.5 101h98v.5h-98zM111.5 101.5h98v.5h-98zM111 102h98v.5h-98zM111 102.5h98v.5h-98zM110.5 103h98v.5h-98zM110.5 103.5h98v.5h-98zM110.5 104h98.5v.5h-98.5zM110.5 104.5h98.5v.5h-98.5zM111 105h98v.5h-98zM111 105.5h97.5v.5h-97.5zM111.5 106h97v.5h-97zM112 106.5h96.5v.5h-96.5zM111.5 107h96.5v.5h-96.5zM111 107.5h96.5v.5h-96.5zM110.5 108h96.5v.5h-96.5zM110 108.5h96.5v.5h-96.5zM109.5 109h96.5v.5h-96.5zM109 109.5h96.5v.5h-96.5zM108.5 110h96.5v.5h-96.5zM108 110.5h96.5v.5h-96.5zM107.5 111h96.5v.5h-96.5zM107 111.5h96.5v.5h-96.5zM106.5 112h96.5v.5h-96.5zM106 112.5h97v.5h-97zM105.5 113h97.5v.5h-97.5zM105 113.5h98.5v.5h-98.5zM104.5 114h99v.5h-99zM104 114.5h99.5v.5h-99.5zM103.5 115h100v.5h-100zM102.5 115.5h101v.5h-101zM101.5 116h101.5v.5h-101.5zM101 116.5h101.5v.5h-101.5zM100.5 117h101.5v.5h-101.5zM100 117.5h101.5v.5h-101.5zM99.5 118h101.5v.5h-101.5zM99 118.5h102v.5h-102zM98.5 119h102v.5h-102zM98 119.5h102.5v.5h-102.5zM97.5 120h102.5v.5h-102.5zM97 120.5h103v.5h-103zM96.5 121h103v.5h-103zM96 121.5h103.5v.5h-103.5zM95.5 122h104v.5h-104zM94.5 122.5h105v.5h-105zM93.5 123h106v.5h-106zM93 123.5h106.5v.5h-106.5zM83.5 124h1v.5h-1zM92.5 124h107v.5h-107zM83 124.5h2.5v.5h-2.5zM92.5 124.5h106.5v.5h-106.5zM82.5 125h3.5v.5h-3.5zM92.5 125h106v.5h-106zM82 125.5h4.5v.5h-4.5zM92 125.5h106v.5h-106zM81.5 126h5.5v.5h-5.5zM91.5 126h107v.5h-107zM81.5 126.5h6v.5h-6zM91 126.5h108v.5h-108zM81 127h7v.5h-7zM90.5 127h108.5v.5h-108.5zM81 127.5h7.5v.5h-7.5zM90 127.5h109.5v.5h-109.5zM81 128h8v.5h-8zM89.5 128h110.5v.5h-110.5zM80.5 128.5h119.5v.5h-119.5zM80.5 129h119.5v.5h-119.5zM80.5 129.5h120v.5h-120zM80.5 130h120v.5h-120zM80.5 130.5h119.5v.5h-119.5zM80.5 131h119.5v.5h-119.5zM80.5 131.5h119.5v.5h-119.5zM80 132h119.5v.5h-119.5zM80 132.5h119v.5h-119zM80 133h118.5v.5h-118.5zM79.5 133.5h118.5v.5h-118.5zM79 134h118.5v.5h-118.5zM78.5 134.5h118.5v.5h-118.5zM78 135h118.5v.5h-118.5zM78 135.5h118v.5h-118zM77.5 136h118.5v.5h-118.5zM77.5 136.5h118.5v.5h-118.5zM77.5 137h118.5v.5h-118.5zM77.5 137.5h119v.5h-119zM77 138h119.5v.5h-119.5zM77 138.5h119.5v.5h-119.5zM77 139h119.5v.5h-119.5zM77 139.5h119.5v.5h-119.5zM77 140h119.5v.5h-119.5zM77 140.5h119.5v.5h-119.5zM77.5 141h119v.5h-119zM77.5 141.5h119.5v.5h-119.5zM77.5 142h120v.5h-120zM77.5 142.5h120v.5h-120zM77.5 143h120.5v.5h-120.5zM78 143.5h120.5v.5h-120.5zM78 144h121v.5h-121zM78 144.5h121v.5h-121zM78 145h121v.5h-121zM78 145.5h121v.5h-121zM78 146h121.5v.5h-121.5zM78 146.5h122v.5h-122zM77.5 147h123v.5h-123zM77.5 147.5h123v.5h-123zM77.5 148h123.5v.5h-123.5zM78 148.5h123v.5h-123zM78 149h123v.5h-123zM78 149.5h123v.5h-123zM78 150h123v.5h-123zM78 150.5h123v.5h-123zM78.5 151h122.5v.5h-122.5zM78.5 151.5h123v.5h-123zM78.5 152h123v.5h-123zM79 152.5h122.5v.5h-122.5zM78.5 153h123v.5h-123zM78.5 153.5h123v.5h-123zM78.5 154h123v.5h-123zM78 154.5h123.5v.5h-123.5zM78 155h123.5v.5h-123.5zM77.5 155.5h123.5v.5h-123.5zM77.5 156h124v.5h-124zM77 156.5h125v.5h-125zM77 157h125.5v.5h-125.5zM77 157.5h126v.5h-126zM76.5 158h127v.5h-127zM76.5 158.5h127.5v.5h-127.5zM76 159h129v.5h-129zM76 159.5h129.5v.5h-129.5zM75.5 160h130.5v.5h-130.5zM75.5 160.5h130.5v.5h-130.5zM75.5 161h131v.5h-131zM75 161.5h131.5v.5h-131.5zM75 162h131.5v.5h-131.5zM74.5 162.5h132v.5h-132zM74.5 163h132v.5h-132zM74 163.5h132v.5h-132zM74 164h132v.5h-132zM74 164.5h132v.5h-132zM73.5 165h132v.5h-132zM73.5 165.5h132v.5h-132zM73 166h132.5v.5h-132.5zM73 166.5h132v.5h-132zM73 167h132v.5h-132zM72.5 167.5h132v.5h-132zM72.5 168h131.5v.5h-131.5zM72 168.5h132v.5h-132zM72 169h132.5v.5h-132.5zM72 169.5h132.5v.5h-132.5zM71.5 170h133v.5h-133zM71.5 170.5h133v.5h-133zM71.5 171h133v.5h-133zM71 171.5h133.5v.5h-133.5zM71 172h133.5v.5h-133.5zM71 172.5h133v.5h-133zM70.5 173h133.5v.5h-133.5zM70.5 173.5h133v.5h-133zM70 174h133.5v.5h-133.5zM70 174.5h133v.5h-133zM70 175h133v.5h-133zM69.5 175.5h133v.5h-133zM69.5 176h132.5v.5h-132.5zM69.5 176.5h132v.5h-132zM69 177h132.5v.5h-132.5zM69 177.5h132.5v.5h-132.5zM68.5 178h133v.5h-133zM68.5 178.5h133v.5h-133zM68.5 179h133v.5h-133zM68 179.5h134v.5h-134zM68 180h134.5v.5h-134.5zM67.5 180.5h135v.5h-135zM67.5 181h135.5v.5h-135.5zM67.5 181.5h136v.5h-136zM67 182h136.5v.5h-136.5zM67 182.5h137v.5h-137zM66.5 183h138v.5h-138zM66.5 183.5h138v.5h-138zM66.5 184h138.5v.5h-138.5zM66 184.5h139.5v.5h-139.5zM66 185h139.5v.5h-139.5zM65.5 185.5h140.5v.5h-140.5zM65.5 186h141v.5h-141zM65 186.5h141.5v.5h-141.5zM65 187h142v.5h-142zM65 187.5h142.5v.5h-142.5zM64.5 188h143v.5h-143zM64.5 188.5h143.5v.5h-143.5zM64 189h144.5v.5h-144.5zM64 189.5h144.5v.5h-144.5zM63.5 190h145.5v.5h-145.5zM63.5 190.5h146v.5h-146zM63 191h147v.5h-147zM63 191.5h147.5v.5h-147.5zM63 192h147.5v.5h-147.5zM62.5 192.5h148.5v.5h-148.5zM62.5 193h149v.5h-149zM62 193.5h150v.5h-150zM62 194h150.5v.5h-150.5zM61.5 194.5h151.5v.5h-151.5zM61.5 195h152v.5h-152zM61 195.5h153v.5h-153zM61 196h153.5v.5h-153.5zM61 196.5h154v.5h-154zM60.5 197h155v.5h-155zM60.5 197.5h155.5v.5h-155.5zM60 198h156.5v.5h-156.5zM60 198.5h157.5v.5h-157.5zM59.5 199h158.5v.5h-158.5zM59.5 199.5h159v.5h-159zM59 200h160v.5h-160zM59 200.5h160.5v.5h-160.5zM58.5 201h162v.5h-162zM58.5 201.5h162.5v.5h-162.5zM58 202h163.5v.5h-163.5zM58 202.5h164v.5h-164zM57.5 203h165.5v.5h-165.5zM57.5 203.5h166v.5h-166zM57 204h167v.5h-167zM57 204.5h167.5v.5h-167.5zM56.5 205h168.5v.5h-168.5zM56.5 205.5h169.5v.5h-169.5zM56 206h170.5v.5h-170.5zM56 206.5h171v.5h-171zM55.5 207h172v.5h-172zM55.5 207.5h172.5v.5h-172.5zM55 208h173.5v.5h-173.5zM55 208.5h174v.5h-174zM54.5 209h175v.5h-175zM54.5 209.5h175.5v.5h-175.5zM54 210h176.5v.5h-176.5zM54 210.5h177v.5h-177zM53.5 211h178v.5h-178zM53.5 211.5h178.5v.5h-178.5zM53 212h179.5v.5h-179.5zM52.5 212.5h180.5v.5h-180.5zM52.5 213h181v.5h-181zM52 213.5h182v.5h-182zM52 214h182.5v.5h-182.5zM51.5 214.5h183v.5h-183zM51.5 215h183.5v.5h-183.5zM51 215.5h184.5v.5h-184.5zM51 216h185v.5h-185zM51 216.5h185v.5h-185zM51 217h185.5v.5h-185.5zM51 217.5h186v.5h-186zM50.5 218h187v.5h-187zM50.5 218.5h187v.5h-187zM50.5 219h187.5v.5h-187.5zM50.5 219.5h188v.5h-188zM50.5 220h188v.5h-188zM50.5 220.5h188.5v.5h-188.5zM50.5 221h189v.5h-189zM50.5 221.5h189.5v.5h-189.5zM50.5 222h190v.5h-190zM50 222.5h191v.5h-191zM50 223h191.5v.5h-191.5zM50 223.5h192v.5h-192zM50 224h192.5v.5h-192.5zM50 224.5h193v.5h-193zM50 225h193.5v.5h-193.5zM50 225.5h194v.5h-194zM50 226h195v.5h-195zM49.5 226.5h196v.5h-196zM49.5 227h197v.5h-197zM49.5 227.5h197.5v.5h-197.5zM49.5 228h198v.5h-198zM49.5 228.5h198.5v.5h-198.5zM49.5 229h199v.5h-199zM49.5 229.5h199.5v.5h-199.5zM49 230h200.5v.5h-200.5zM49 230.5h201v.5h-201zM49 231h201.5v.5h-201.5zM49 231.5h202v.5h-202zM49 232h202.5v.5h-202.5zM49 232.5h203v.5h-203zM49 233h203v.5h-203zM48.5 233.5h204v.5h-204zM48.5 234h204v.5h-204zM48.5 234.5h204.5v.5h-204.5zM48.5 235h204.5v.5h-204.5zM48.5 235.5h204.5v.5h-204.5zM48.5 236h204.5v.5h-204.5zM48 236.5h205v.5h-205zM48 237h205v.5h-205zM48 237.5h205v.5h-205zM48 238h205v.5h-205zM48 238.5h205v.5h-205zM47.5 239h205.5v.5h-205.5zM47.5 239.5h205v.5h-205zM47.5 240h205v.5h-205zM47.5 240.5h204.5v.5h-204.5zM47.5 241h204v.5h-204zM47.5 241.5h203.5v.5h-203.5zM47 242h204v.5h-204zM47 242.5h203.5v.5h-203.5zM47 243h202.5v.5h-202.5zM47 243.5h202v.5h-202zM47 244h201.5v.5h-201.5zM47 244.5h201v.5h-201zM46.5 245h201v.5h-201zM46.5 245.5h200.5v.5h-200.5zM46.5 246h200v.5h-200zM46.5 246.5h200v.5h-200zM46.5 247h200v.5h-200zM46 247.5h200.5v.5h-200.5zM46 248h200.5v.5h-200.5zM46 248.5h200.5v.5h-200.5zM46 249h201v.5h-201zM46 249.5h201v.5h-201zM46 250h201v.5h-201zM45.5 250.5h201.5v.5h-201.5zM45.5 251h201.5v.5h-201.5zM45.5 251.5h201.5v.5h-201.5zM45.5 252h201.5v.5h-201.5zM45.5 252.5h201.5v.5h-201.5zM45.5 253h201.5v.5h-201.5zM45.5 253.5h201.5v.5h-201.5zM45.5 254h201v.5h-201zM45.5 254.5h201v.5h-201zM45.5 255h201v.5h-201zM45.5 255.5h201v.5h-201zM45.5 256h201v.5h-201zM45.5 256.5h200.5v.5h-200.5zM45.5 257h200.5v.5h-200.5zM45.5 257.5h200v.5h-200zM45.5 258h200v.5h-200zM45.5 258.5h199.5v.5h-199.5zM45.5 259h199.5v.5h-199.5zM46 259.5h198.5v.5h-198.5zM46 260h198v.5h-198zM46 260.5h197.5v.5h-197.5zM46.5 261h196.5v.5h-196.5zM46.5 261.5h196v.5h-196zM46.5 262h153v.5h-153zM201.5 262h23v.5h-23zM225 262h9.5v.5h-9.5zM236 262h5.5v.5h-5.5zM47 262.5h152v.5h-152zM202.5 262.5h9.5v.5h-9.5zM213 262.5h11v.5h-11zM225.5 262.5h8.5v.5h-8.5zM237.5 262.5h3v.5h-3zM47.5 263h151v.5h-151zM203.5 263h7.5v.5h-7.5zM213.5 263h10v.5h-10zM226.5 263h7v.5h-7zM47.5 263.5h150.5v.5h-150.5zM205 263.5h5v.5h-5zM214.5 263.5h8.5v.5h-8.5zM228 263.5h5v.5h-5zM48 264h149.5v.5h-149.5zM215.5 264h7v.5h-7zM48.5 264.5h18v.5h-18zM67 264.5h7.5v.5h-7.5zM75 264.5h122v.5h-122zM217 264.5h4v.5h-4zM49 265h16.5v.5h-16.5zM67.5 265h6.5v.5h-6.5zM75.5 265h121v.5h-121zM49.5 265.5h15.5v.5h-15.5zM68.5 265.5h5v.5h-5zM76 265.5h120v.5h-120zM50.5 266h13.5v.5h-13.5zM70 266h2v.5h-2zM77 266h5.5v.5h-5.5zM83.5 266h104.5v.5h-104.5zM188.5 266h7v.5h-7zM51.5 266.5h4v.5h-4zM56.5 266.5h6.5v.5h-6.5zM78.5 266.5h2v.5h-2zM84 266.5h103.5v.5h-103.5zM190 266.5h4.5v.5h-4.5zM58 267h3.5v.5h-3.5zM84.5 267h102.5v.5h-102.5zM85 267.5h101.5v.5h-101.5zM85.5 268h100.5v.5h-100.5zM86 268.5h99.5v.5h-99.5zM86.5 269h89.5v.5h-89.5zM178 269h7v.5h-7zM86 269.5h89v.5h-89zM178.5 269.5h5.5v.5h-5.5zM85.5 270h71v.5h-71zM160 270h14v.5h-14zM179 270h4.5v.5h-4.5zM85 270.5h71v.5h-71zM161 270.5h12v.5h-12zM179.5 270.5h3v.5h-3zM84.5 271h71v.5h-71zM162 271h10.5v.5h-10.5zM84 271.5h70.5v.5h-70.5zM162.5 271.5h9v.5h-9zM84 272h70v.5h-70zM163 272h8v.5h-8zM83.5 272.5h69v.5h-69zM163.5 272.5h6.5v.5h-6.5zM83 273h68v.5h-68zM164.5 273h4.5v.5h-4.5zM83 273.5h67.5v.5h-67.5zM165.5 273.5h2v.5h-2zM83 274h67v.5h-67zM83 274.5h66.5v.5h-66.5zM83.5 275h34.5v.5h-34.5zM123 275h26v.5h-26zM83.5 275.5h34v.5h-34zM123.5 275.5h25v.5h-25zM84.5 276h32.5v.5h-32.5zM124 276h24v.5h-24zM85.5 276.5h31v.5h-31zM124.5 276.5h23v.5h-23zM87 277h29v.5h-29zM125 277h22v.5h-22zM90.5 277.5h2.5v.5h-2.5zM94 277.5h8v.5h-8zM103.5 277.5h12v.5h-12zM125.5 277.5h20.5v.5h-20.5zM94.5 278h7v.5h-7zM104.5 278h10.5v.5h-10.5zM126 278h19v.5h-19zM95 278.5h6v.5h-6zM106 278.5h8.5v.5h-8.5zM126 278.5h18.5v.5h-18.5zM96 279h4.5v.5h-4.5zM107.5 279h5.5v.5h-5.5zM126.5 279h17.5v.5h-17.5zM97.5 279.5h1.5v.5h-1.5zM127 279.5h16.5v.5h-16.5zM127 280h16v.5h-16zM127.5 280.5h15v.5h-15zM128 281h14v.5h-14zM128.5 281.5h13.5v.5h-13.5zM129 282h13v.5h-13zM129 282.5h12.5v.5h-12.5zM129.5 283h12v.5h-12zM130 283.5h11.5v.5h-11.5zM130.5 284h10.5v.5h-10.5zM131 284.5h9.5v.5h-9.5zM132 285h8.5v.5h-8.5zM132.5 285.5h7.5v.5h-7.5zM133 286h6v.5h-6zM134 286.5h4.5v.5h-4.5z', 'allowDelete': False},
    {'id': 'eclipseping', 'name': '이클립스핑', 'emoji': '👑', 'svg': '<image href="/static/coloring/eclipseping.svg" x="0" y="0" width="300" height="300"/>', 'regions': [{'type': 'rect', 'x': 0, 'y': 0, 'w': 300, 'h': 300}], 'isCustomSheet': True, 'contourPng': '/static/coloring/eclipseping.svg', 'outerPath': 'M148.5 12h1v.5h-1zM148.5 12.5h1v.5h-1zM148.5 13h1v.5h-1zM148.5 13.5h1.5v.5h-1.5zM148.5 14h1.5v.5h-1.5zM148.5 14.5h1.5v.5h-1.5zM148.5 15h2v.5h-2zM148 15.5h2.5v.5h-2.5zM148 16h2.5v.5h-2.5zM148 16.5h3v.5h-3zM148 17h3v.5h-3zM147.5 17.5h3.5v.5h-3.5zM147.5 18h4v.5h-4zM147.5 18.5h4v.5h-4zM147 19h5v.5h-5zM147 19.5h5.5v.5h-5.5zM147 20h5.5v.5h-5.5zM146.5 20.5h6.5v.5h-6.5zM146.5 21h7v.5h-7zM146 21.5h7.5v.5h-7.5zM146 22h7.5v.5h-7.5zM145.5 22.5h8v.5h-8zM145.5 23h8v.5h-8zM145.5 23.5h7.5v.5h-7.5zM146 24h6.5v.5h-6.5zM146.5 24.5h5.5v.5h-5.5zM147 25h5v.5h-5zM147.5 25.5h4v.5h-4zM148 26h3.5v.5h-3.5zM148.5 26.5h3v.5h-3zM148.5 27h2.5v.5h-2.5zM148.5 27.5h2.5v.5h-2.5zM148.5 28h3v.5h-3zM148.5 28.5h3v.5h-3zM148.5 29h3v.5h-3zM148.5 29.5h3.5v.5h-3.5zM148.5 30h3.5v.5h-3.5zM148 30.5h4.5v.5h-4.5zM148 31h4.5v.5h-4.5zM196.5 31h1v.5h-1zM148 31.5h4.5v.5h-4.5zM196.5 31.5h1v.5h-1zM148 32h5v.5h-5zM196 32h1.5v.5h-1.5zM148 32.5h5v.5h-5zM195.5 32.5h2.5v.5h-2.5zM215 32.5h1v.5h-1zM148 33h5v.5h-5zM195 33h3v.5h-3zM215 33h1v.5h-1zM148 33.5h5.5v.5h-5.5zM194.5 33.5h3.5v.5h-3.5zM214.5 33.5h1.5v.5h-1.5zM148 34h5.5v.5h-5.5zM194 34h4v.5h-4zM214 34h2v.5h-2zM147.5 34.5h6v.5h-6zM193.5 34.5h4.5v.5h-4.5zM213.5 34.5h2.5v.5h-2.5zM147.5 35h6.5v.5h-6.5zM193 35h5v.5h-5zM213 35h3v.5h-3zM147.5 35.5h6.5v.5h-6.5zM192.5 35.5h5.5v.5h-5.5zM212.5 35.5h3.5v.5h-3.5zM147.5 36h7v.5h-7zM193 36h5.5v.5h-5.5zM212 36h4v.5h-4zM147.5 36.5h7v.5h-7zM193 36.5h5.5v.5h-5.5zM211 36.5h5v.5h-5zM147.5 37h7v.5h-7zM193.5 37h5.5v.5h-5.5zM210.5 37h5.5v.5h-5.5zM147.5 37.5h7.5v.5h-7.5zM193.5 37.5h6v.5h-6zM204 37.5h1v.5h-1zM210 37.5h6v.5h-6zM147.5 38h7.5v.5h-7.5zM193.5 38h6.5v.5h-6.5zM203.5 38h2v.5h-2zM209.5 38h6.5v.5h-6.5zM147.5 38.5h7.5v.5h-7.5zM193.5 38.5h7v.5h-7zM203 38.5h3v.5h-3zM209 38.5h7.5v.5h-7.5zM108.5 39h1v.5h-1zM147 39h8.5v.5h-8.5zM194 39h7v.5h-7zM202.5 39h4v.5h-4zM208.5 39h8v.5h-8zM108.5 39.5h1.5v.5h-1.5zM147 39.5h8.5v.5h-8.5zM194 39.5h7.5v.5h-7.5zM202 39.5h5v.5h-5zM208 39.5h8.5v.5h-8.5zM108.5 40h2v.5h-2zM147 40h8.5v.5h-8.5zM194 40h23v.5h-23zM108.5 40.5h2.5v.5h-2.5zM147 40.5h9v.5h-9zM193.5 40.5h23v.5h-23zM108.5 41h3v.5h-3zM147 41h9v.5h-9zM193 41h23v.5h-23zM109 41.5h3v.5h-3zM147 41.5h9.5v.5h-9.5zM193 41.5h22.5v.5h-22.5zM109 42h4v.5h-4zM147 42h9.5v.5h-9.5zM192.5 42h22.5v.5h-22.5zM109 42.5h5v.5h-5zM147 42.5h9.5v.5h-9.5zM173 42.5h1v.5h-1zM192.5 42.5h22v.5h-22zM109 43h5.5v.5h-5.5zM146.5 43h10.5v.5h-10.5zM173 43h1v.5h-1zM192.5 43h21.5v.5h-21.5zM109 43.5h5.5v.5h-5.5zM146.5 43.5h10.5v.5h-10.5zM173 43.5h1v.5h-1zM192 43.5h21.5v.5h-21.5zM109 44h5v.5h-5zM146.5 44h10.5v.5h-10.5zM172.5 44h1.5v.5h-1.5zM192 44h21v.5h-21zM108.5 44.5h5.5v.5h-5.5zM146.5 44.5h11v.5h-11zM172.5 44.5h1.5v.5h-1.5zM191.5 44.5h21.5v.5h-21.5zM91 45h1v.5h-1zM108.5 45h5.5v.5h-5.5zM146.5 45h11v.5h-11zM172 45h2.5v.5h-2.5zM191.5 45h21v.5h-21zM91 45.5h1.5v.5h-1.5zM108 45.5h6v.5h-6zM146.5 45.5h11.5v.5h-11.5zM171.5 45.5h3v.5h-3zM191 45.5h21.5v.5h-21.5zM91 46h2v.5h-2zM107.5 46h6.5v.5h-6.5zM133.5 46h1v.5h-1zM146.5 46h11.5v.5h-11.5zM171 46h3.5v.5h-3.5zM191 46h21.5v.5h-21.5zM91 46.5h2.5v.5h-2.5zM102 46.5h0.5v.5h-0.5zM107 46.5h7v.5h-7zM133.5 46.5h1.5v.5h-1.5zM146.5 46.5h11.5v.5h-11.5zM170.5 46.5h4.5v.5h-4.5zM190.5 46.5h21.5v.5h-21.5zM91 47h3v.5h-3zM101.5 47h1.5v.5h-1.5zM106.5 47h7.5v.5h-7.5zM133.5 47h1.5v.5h-1.5zM146.5 47h12v.5h-12zM170.5 47h5v.5h-5zM190.5 47h21.5v.5h-21.5zM91 47.5h3.5v.5h-3.5zM101 47.5h2.5v.5h-2.5zM106 47.5h7.5v.5h-7.5zM133.5 47.5h2v.5h-2zM146 47.5h12.5v.5h-12.5zM170 47.5h6v.5h-6zM190.5 47.5h21.5v.5h-21.5zM91.5 48h3.5v.5h-3.5zM100.5 48h3.5v.5h-3.5zM105.5 48h8.5v.5h-8.5zM133.5 48h2.5v.5h-2.5zM146 48h12.5v.5h-12.5zM170 48h6v.5h-6zM190 48h21.5v.5h-21.5zM91.5 48.5h5v.5h-5zM100 48.5h4.5v.5h-4.5zM105 48.5h9v.5h-9zM133.5 48.5h3v.5h-3zM146 48.5h13v.5h-13zM170.5 48.5h5.5v.5h-5.5zM190 48.5h21.5v.5h-21.5zM91.5 49h5.5v.5h-5.5zM99.5 49h15v.5h-15zM133.5 49h3.5v.5h-3.5zM146 49h13v.5h-13zM170.5 49h5v.5h-5zM189.5 49h22v.5h-22zM91.5 49.5h6v.5h-6zM99 49.5h16v.5h-16zM133 49.5h4.5v.5h-4.5zM146 49.5h13.5v.5h-13.5zM171 49.5h4v.5h-4zM189.5 49.5h21.5v.5h-21.5zM91 50h7v.5h-7zM98.5 50h16.5v.5h-16.5zM133 50h5v.5h-5zM146 50h13.5v.5h-13.5zM171.5 50h3v.5h-3zM189 50h22v.5h-22zM91 50.5h24.5v.5h-24.5zM132.5 50.5h5.5v.5h-5.5zM146 50.5h13.5v.5h-13.5zM171.5 50.5h2.5v.5h-2.5zM189 50.5h22v.5h-22zM91 51h25v.5h-25zM132 51h6v.5h-6zM146 51h14v.5h-14zM171.5 51h2.5v.5h-2.5zM189 51h21.5v.5h-21.5zM90.5 51.5h25.5v.5h-25.5zM132 51.5h6v.5h-6zM146 51.5h14v.5h-14zM171.5 51.5h2.5v.5h-2.5zM188.5 51.5h22v.5h-22zM91 52h25.5v.5h-25.5zM132.5 52h5v.5h-5zM145.5 52h14.5v.5h-14.5zM171.5 52h2.5v.5h-2.5zM188.5 52h22v.5h-22zM92 52.5h25v.5h-25zM133 52.5h4.5v.5h-4.5zM145.5 52.5h15v.5h-15zM171 52.5h3.5v.5h-3.5zM188 52.5h22v.5h-22zM92.5 53h25v.5h-25zM133.5 53h4v.5h-4zM145.5 53h15v.5h-15zM171 53h3.5v.5h-3.5zM188 53h22v.5h-22zM93 53.5h24.5v.5h-24.5zM134 53.5h3.5v.5h-3.5zM145.5 53.5h15.5v.5h-15.5zM170.5 53.5h4v.5h-4zM188 53.5h22v.5h-22zM93.5 54h24.5v.5h-24.5zM134.5 54h3v.5h-3zM145.5 54h15.5v.5h-15.5zM170.5 54h4v.5h-4zM187.5 54h22v.5h-22zM94 54.5h24.5v.5h-24.5zM135 54.5h3v.5h-3zM145.5 54.5h15.5v.5h-15.5zM170.5 54.5h4v.5h-4zM187.5 54.5h22v.5h-22zM94.5 55h24.5v.5h-24.5zM135 55h3v.5h-3zM145.5 55h16v.5h-16zM170 55h5v.5h-5zM187 55h22.5v.5h-22.5zM95 55.5h24v.5h-24zM135 55.5h3.5v.5h-3.5zM145.5 55.5h16v.5h-16zM170 55.5h5v.5h-5zM187 55.5h22v.5h-22zM95.5 56h24v.5h-24zM135 56h4v.5h-4zM145 56h17v.5h-17zM170 56h5v.5h-5zM187 56h22v.5h-22zM96 56.5h24v.5h-24zM135 56.5h4.5v.5h-4.5zM144.5 56.5h17.5v.5h-17.5zM169.5 56.5h5.5v.5h-5.5zM186.5 56.5h22.5v.5h-22.5zM96 57h24.5v.5h-24.5zM135 57h5v.5h-5zM144 57h18v.5h-18zM169.5 57h5.5v.5h-5.5zM186.5 57h22.5v.5h-22.5zM96.5 57.5h24v.5h-24zM135 57.5h5.5v.5h-5.5zM143.5 57.5h19v.5h-19zM169.5 57.5h5.5v.5h-5.5zM186 57.5h22.5v.5h-22.5zM96.5 58h24.5v.5h-24.5zM135 58h6v.5h-6zM143 58h19.5v.5h-19.5zM169 58h6.5v.5h-6.5zM186 58h22.5v.5h-22.5zM97 58.5h24.5v.5h-24.5zM135 58.5h6.5v.5h-6.5zM142.5 58.5h20.5v.5h-20.5zM168.5 58.5h7v.5h-7zM185.5 58.5h23v.5h-23zM97 59h24.5v.5h-24.5zM135 59h28.5v.5h-28.5zM168 59h7.5v.5h-7.5zM185.5 59h22.5v.5h-22.5zM97.5 59.5h24.5v.5h-24.5zM135 59.5h29v.5h-29zM167.5 59.5h8v.5h-8zM185.5 59.5h22.5v.5h-22.5zM97.5 60h25v.5h-25zM135 60h29.5v.5h-29.5zM167 60h8.5v.5h-8.5zM185 60h23v.5h-23zM98 60.5h25v.5h-25zM135 60.5h30v.5h-30zM166.5 60.5h9.5v.5h-9.5zM185 60.5h22.5v.5h-22.5zM98 61h25v.5h-25zM135 61h30.5v.5h-30.5zM166 61h10v.5h-10zM184.5 61h23v.5h-23zM98.5 61.5h25v.5h-25zM135 61.5h41v.5h-41zM184.5 61.5h23v.5h-23zM98.5 62h25.5v.5h-25.5zM135 62h41v.5h-41zM184.5 62h22.5v.5h-22.5zM99 62.5h25v.5h-25zM135 62.5h41.5v.5h-41.5zM184 62.5h23v.5h-23zM99 63h25.5v.5h-25.5zM135 63h41.5v.5h-41.5zM184 63h23v.5h-23zM99.5 63.5h25.5v.5h-25.5zM135 63.5h41.5v.5h-41.5zM183.5 63.5h23v.5h-23zM99.5 64h26v.5h-26zM135 64h42v.5h-42zM183.5 64h23v.5h-23zM100 64.5h25.5v.5h-25.5zM135 64.5h42v.5h-42zM183.5 64.5h23v.5h-23zM100.5 65h25.5v.5h-25.5zM135 65h42.5v.5h-42.5zM183 65h23v.5h-23zM100.5 65.5h26v.5h-26zM135 65.5h43v.5h-43zM182.5 65.5h23.5v.5h-23.5zM101 66h26v.5h-26zM135 66h43.5v.5h-43.5zM182 66h24v.5h-24zM101 66.5h26v.5h-26zM135 66.5h44v.5h-44zM181.5 66.5h24v.5h-24zM101.5 67h26v.5h-26zM135 67h44.5v.5h-44.5zM181 67h24.5v.5h-24.5zM101.5 67.5h26.5v.5h-26.5zM135 67.5h45v.5h-45zM180.5 67.5h25v.5h-25zM102 68h26v.5h-26zM135 68h70v.5h-70zM102 68.5h26.5v.5h-26.5zM135 68.5h70v.5h-70zM102.5 69h26.5v.5h-26.5zM134.5 69h70.5v.5h-70.5zM102.5 69.5h27v.5h-27zM134 69.5h71v.5h-71zM103 70h27v.5h-27zM133.5 70h71v.5h-71zM103.5 70.5h27v.5h-27zM133 70.5h71.5v.5h-71.5zM103.5 71h27.5v.5h-27.5zM132.5 71h72v.5h-72zM104 71.5h27.5v.5h-27.5zM132 71.5h72v.5h-72zM104 72h100v.5h-100zM104.5 72.5h99.5v.5h-99.5zM104.5 73h99v.5h-99zM105 73.5h98.5v.5h-98.5zM105 74h98.5v.5h-98.5zM105.5 74.5h97.5v.5h-97.5zM106 75h97v.5h-97zM106 75.5h97v.5h-97zM106.5 76h96v.5h-96zM106.5 76.5h96v.5h-96zM107 77h95.5v.5h-95.5zM107 77.5h95v.5h-95zM107.5 78h94.5v.5h-94.5zM108 78.5h94v.5h-94zM108 79h93.5v.5h-93.5zM108.5 79.5h93v.5h-93zM109 80h93v.5h-93zM109 80.5h93.5v.5h-93.5zM109.5 81h93.5v.5h-93.5zM109.5 81.5h94v.5h-94zM110 82h93v.5h-93zM110.5 82.5h92.5v.5h-92.5zM110.5 83h92v.5h-92zM111 83.5h91v.5h-91zM111 84h91.5v.5h-91.5zM111.5 84.5h91.5v.5h-91.5zM112 85h91.5v.5h-91.5zM112 85.5h92v.5h-92zM112.5 86h92v.5h-92zM113 86.5h90.5v.5h-90.5zM113 87h89v.5h-89zM113.5 87.5h88v.5h-88zM114 88h87v.5h-87zM114.5 88.5h86v.5h-86zM114.5 89h85.5v.5h-85.5zM114 89.5h85.5v.5h-85.5zM113.5 90h85.5v.5h-85.5zM113.5 90.5h86v.5h-86zM114 91h86v.5h-86zM114.5 91.5h85.5v.5h-85.5zM115 92h85v.5h-85zM114.5 92.5h85.5v.5h-85.5zM114 93h86v.5h-86zM113.5 93.5h86.5v.5h-86.5zM113 94h87.5v.5h-87.5zM113 94.5h88v.5h-88zM113.5 95h88v.5h-88zM115.5 95.5h86.5v.5h-86.5zM116 96h86.5v.5h-86.5zM116.5 96.5h86.5v.5h-86.5zM117 97h86.5v.5h-86.5zM117.5 97.5h87v.5h-87zM118 98h87v.5h-87zM118.5 98.5h87.5v.5h-87.5zM119 99h87v.5h-87zM119 99.5h87v.5h-87zM119 100h86v.5h-86zM119 100.5h85.5v.5h-85.5zM119.5 101h84v.5h-84zM120 101.5h82.5v.5h-82.5zM120 102h82v.5h-82zM120 102.5h81.5v.5h-81.5zM119.5 103h81.5v.5h-81.5zM119 103.5h81.5v.5h-81.5zM118.5 104h81.5v.5h-81.5zM118 104.5h81.5v.5h-81.5zM117.5 105h82v.5h-82zM117 105.5h82.5v.5h-82.5zM116.5 106h83v.5h-83zM116 106.5h83.5v.5h-83.5zM115.5 107h84v.5h-84zM115 107.5h84.5v.5h-84.5zM114.5 108h85.5v.5h-85.5zM114.5 108.5h86v.5h-86zM116 109h85v.5h-85zM117.5 109.5h84v.5h-84zM119.5 110h82.5v.5h-82.5zM120 110.5h82.5v.5h-82.5zM120.5 111h83v.5h-83zM121 111.5h83v.5h-83zM121.5 112h85v.5h-85zM122 112.5h85v.5h-85zM122.5 113h85v.5h-85zM123 113.5h85v.5h-85zM123 114h85.5v.5h-85.5zM123.5 114.5h85.5v.5h-85.5zM124 115h85.5v.5h-85.5zM124.5 115.5h85.5v.5h-85.5zM124 116h86v.5h-86zM124 116.5h86.5v.5h-86.5zM123.5 117h87.5v.5h-87.5zM123 117.5h88.5v.5h-88.5zM122.5 118h89.5v.5h-89.5zM122 118.5h90.5v.5h-90.5zM121.5 119h91v.5h-91zM121 119.5h92v.5h-92zM120.5 120h93v.5h-93zM120 120.5h93.5v.5h-93.5zM119.5 121h94.5v.5h-94.5zM119 121.5h95.5v.5h-95.5zM118 122h96.5v.5h-96.5zM117.5 122.5h97.5v.5h-97.5zM117 123h98v.5h-98zM117 123.5h98v.5h-98zM116.5 124h99v.5h-99zM116.5 124.5h99v.5h-99zM116 125h99.5v.5h-99.5zM115.5 125.5h100v.5h-100zM115.5 126h100.5v.5h-100.5zM115 126.5h101v.5h-101zM115 127h101v.5h-101zM114.5 127.5h102v.5h-102zM114.5 128h102v.5h-102zM114 128.5h102.5v.5h-102.5zM114 129h102.5v.5h-102.5zM113.5 129.5h103.5v.5h-103.5zM113.5 130h103.5v.5h-103.5zM113 130.5h104v.5h-104zM113 131h104v.5h-104zM112.5 131.5h105v.5h-105zM112.5 132h105v.5h-105zM112 132.5h105.5v.5h-105.5zM112 133h105.5v.5h-105.5zM112 133.5h106v.5h-106zM111.5 134h106.5v.5h-106.5zM111.5 134.5h106.5v.5h-106.5zM111.5 135h106.5v.5h-106.5zM111.5 135.5h106.5v.5h-106.5zM111.5 136h106v.5h-106zM111.5 136.5h105.5v.5h-105.5zM111 137h106v.5h-106zM111 137.5h106v.5h-106zM111 138h106.5v.5h-106.5zM111 138.5h106.5v.5h-106.5zM111 139h106.5v.5h-106.5zM111 139.5h107v.5h-107zM111 140h107v.5h-107zM111 140.5h107v.5h-107zM111 141h107.5v.5h-107.5zM111 141.5h107.5v.5h-107.5zM111 142h107.5v.5h-107.5zM111 142.5h108v.5h-108zM111 143h108.5v.5h-108.5zM111 143.5h109v.5h-109zM111 144h109.5v.5h-109.5zM111 144.5h110v.5h-110zM111 145h110.5v.5h-110.5zM222.5 145h1v.5h-1zM111 145.5h113.5v.5h-113.5zM111 146h113.5v.5h-113.5zM111 146.5h114v.5h-114zM111 147h114v.5h-114zM111 147.5h114v.5h-114zM111.5 148h113.5v.5h-113.5zM112 148.5h113v.5h-113zM112 149h113v.5h-113zM112 149.5h113v.5h-113zM112 150h113v.5h-113zM111.5 150.5h113.5v.5h-113.5zM111.5 151h113.5v.5h-113.5zM111.5 151.5h113.5v.5h-113.5zM111.5 152h113v.5h-113zM111.5 152.5h113v.5h-113zM111.5 153h113v.5h-113zM111.5 153.5h113v.5h-113zM111.5 154h113v.5h-113zM111 154.5h113.5v.5h-113.5zM111 155h113.5v.5h-113.5zM110.5 155.5h114v.5h-114zM110 156h114.5v.5h-114.5zM109.5 156.5h114.5v.5h-114.5zM109 157h115v.5h-115zM108.5 157.5h115.5v.5h-115.5zM108 158h116v.5h-116zM107.5 158.5h116.5v.5h-116.5zM107 159h117v.5h-117zM107 159.5h117v.5h-117zM107 160h117.5v.5h-117.5zM107 160.5h117.5v.5h-117.5zM107 161h118v.5h-118zM107 161.5h118v.5h-118zM107 162h118.5v.5h-118.5zM107 162.5h119v.5h-119zM107.5 163h119v.5h-119zM107.5 163.5h119.5v.5h-119.5zM107.5 164h120v.5h-120zM107.5 164.5h120.5v.5h-120.5zM108 165h120.5v.5h-120.5zM108 165.5h121v.5h-121zM108 166h122v.5h-122zM108 166.5h122.5v.5h-122.5zM108 167h123v.5h-123zM108.5 167.5h123v.5h-123zM108.5 168h123.5v.5h-123.5zM109 168.5h124v.5h-124zM109 169h124.5v.5h-124.5zM109 169.5h125v.5h-125zM109.5 170h125v.5h-125zM109.5 170.5h125.5v.5h-125.5zM109 171h126.5v.5h-126.5zM109 171.5h127v.5h-127zM109 172h127v.5h-127zM108.5 172.5h128v.5h-128zM108.5 173h128.5v.5h-128.5zM108.5 173.5h128.5v.5h-128.5zM108 174h129.5v.5h-129.5zM108 174.5h130v.5h-130zM108 175h130v.5h-130zM107.5 175.5h130.5v.5h-130.5zM107.5 176h131v.5h-131zM107.5 176.5h131v.5h-131zM107 177h131.5v.5h-131.5zM107 177.5h132v.5h-132zM107 178h132v.5h-132zM106.5 178.5h132.5v.5h-132.5zM106.5 179h132.5v.5h-132.5zM106.5 179.5h132.5v.5h-132.5zM106 180h133v.5h-133zM106 180.5h133v.5h-133zM106 181h133v.5h-133zM105.5 181.5h133.5v.5h-133.5zM105.5 182h133.5v.5h-133.5zM105.5 182.5h133.5v.5h-133.5zM105 183h134v.5h-134zM105 183.5h134v.5h-134zM104.5 184h134v.5h-134zM104.5 184.5h134v.5h-134zM104.5 185h134v.5h-134zM104 185.5h134v.5h-134zM104 186h133.5v.5h-133.5zM104 186.5h133.5v.5h-133.5zM103.5 187h133.5v.5h-133.5zM103.5 187.5h133v.5h-133zM103.5 188h132.5v.5h-132.5zM103 188.5h132.5v.5h-132.5zM103 189h132.5v.5h-132.5zM103 189.5h132.5v.5h-132.5zM102.5 190h133v.5h-133zM102.5 190.5h133v.5h-133zM102 191h133.5v.5h-133.5zM102 191.5h133.5v.5h-133.5zM102 192h133.5v.5h-133.5zM101.5 192.5h134v.5h-134zM101.5 193h134v.5h-134zM101.5 193.5h134v.5h-134zM101 194h134.5v.5h-134.5zM101 194.5h134.5v.5h-134.5zM101 195h134.5v.5h-134.5zM100.5 195.5h135v.5h-135zM100.5 196h135v.5h-135zM100 196.5h135.5v.5h-135.5zM100 197h135.5v.5h-135.5zM100 197.5h135.5v.5h-135.5zM99.5 198h136.5v.5h-136.5zM99.5 198.5h136.5v.5h-136.5zM99 199h137v.5h-137zM99 199.5h137v.5h-137zM99 200h137v.5h-137zM98.5 200.5h137.5v.5h-137.5zM98.5 201h137.5v.5h-137.5zM98 201.5h138v.5h-138zM97.5 202h139v.5h-139zM97 202.5h139.5v.5h-139.5zM96.5 203h140v.5h-140zM96 203.5h140.5v.5h-140.5zM95.5 204h141.5v.5h-141.5zM95 204.5h142v.5h-142zM94.5 205h142.5v.5h-142.5zM93.5 205.5h143.5v.5h-143.5zM92 206h145v.5h-145zM91.5 206.5h146v.5h-146zM91 207h146.5v.5h-146.5zM90 207.5h147.5v.5h-147.5zM90 208h147.5v.5h-147.5zM89.5 208.5h148.5v.5h-148.5zM89 209h149v.5h-149zM89 209.5h149v.5h-149zM88.5 210h149v.5h-149zM88.5 210.5h149.5v.5h-149.5zM88.5 211h150v.5h-150zM88 211.5h151v.5h-151zM87.5 212h152v.5h-152zM87 212.5h153v.5h-153zM86.5 213h154v.5h-154zM86 213.5h155v.5h-155zM85.5 214h156v.5h-156zM84.5 214.5h157.5v.5h-157.5zM83.5 215h159v.5h-159zM82.5 215.5h160.5v.5h-160.5zM81 216h162.5v.5h-162.5zM80.5 216.5h163.5v.5h-163.5zM79.5 217h164.5v.5h-164.5zM79 217.5h165.5v.5h-165.5zM78 218h167v.5h-167zM77.5 218.5h167.5v.5h-167.5zM77 219h168.5v.5h-168.5zM76.5 219.5h169v.5h-169zM76 220h170v.5h-170zM75.5 220.5h171v.5h-171zM75.5 221h171v.5h-171zM75 221.5h172v.5h-172zM75 222h172v.5h-172zM74.5 222.5h173v.5h-173zM74.5 223h173v.5h-173zM74 223.5h173.5v.5h-173.5zM74 224h174v.5h-174zM74 224.5h174v.5h-174zM74 225h174v.5h-174zM73.5 225.5h175v.5h-175zM73.5 226h175v.5h-175zM73.5 226.5h175v.5h-175zM73.5 227h175v.5h-175zM73.5 227.5h175.5v.5h-175.5zM73.5 228h175.5v.5h-175.5zM73.5 228.5h175.5v.5h-175.5zM73.5 229h175.5v.5h-175.5zM73.5 229.5h175.5v.5h-175.5zM73.5 230h175.5v.5h-175.5zM73.5 230.5h175.5v.5h-175.5zM74 231h175v.5h-175zM74 231.5h175v.5h-175zM74 232h175v.5h-175zM74 232.5h175v.5h-175zM74 233h175v.5h-175zM74 233.5h175v.5h-175zM73.5 234h175.5v.5h-175.5zM73 234.5h176v.5h-176zM72.5 235h176v.5h-176zM72 235.5h176.5v.5h-176.5zM48.5 236h0.5v.5h-0.5zM71.5 236h177v.5h-177zM48 236.5h2v.5h-2zM71 236.5h177v.5h-177zM48 237h2.5v.5h-2.5zM70 237h177.5v.5h-177.5zM48 237.5h3.5v.5h-3.5zM68.5 237.5h179v.5h-179zM48 238h4.5v.5h-4.5zM67.5 238h180v.5h-180zM48 238.5h6v.5h-6zM65.5 238.5h182.5v.5h-182.5zM47.5 239h8.5v.5h-8.5zM63.5 239h184.5v.5h-184.5zM48 239.5h200v.5h-200zM48 240h200v.5h-200zM48 240.5h200.5v.5h-200.5zM48 241h200.5v.5h-200.5zM48.5 241.5h200v.5h-200zM49 242h199.5v.5h-199.5zM49.5 242.5h199v.5h-199zM49.5 243h199.5v.5h-199.5zM49 243.5h200v.5h-200zM49 244h200v.5h-200zM49.5 244.5h199.5v.5h-199.5zM50 245h199v.5h-199zM50.5 245.5h199v.5h-199zM51 246h198.5v.5h-198.5zM51 246.5h198.5v.5h-198.5zM51 247h198.5v.5h-198.5zM51 247.5h198.5v.5h-198.5zM51 248h198.5v.5h-198.5zM51.5 248.5h198v.5h-198zM51.5 249h198v.5h-198zM51.5 249.5h198v.5h-198zM52 250h197.5v.5h-197.5zM52.5 250.5h197v.5h-197zM52.5 251h197v.5h-197zM53 251.5h196.5v.5h-196.5zM53.5 252h196v.5h-196zM54 252.5h195v.5h-195zM54.5 253h194.5v.5h-194.5zM55.5 253.5h193.5v.5h-193.5zM56 254h193.5v.5h-193.5zM57 254.5h192.5v.5h-192.5zM58 255h191.5v.5h-191.5zM59.5 255.5h190v.5h-190zM61.5 256h188v.5h-188zM62 256.5h187.5v.5h-187.5zM62.5 257h187v.5h-187zM63 257.5h165v.5h-165zM228.5 257.5h20.5v.5h-20.5zM63.5 258h164v.5h-164zM229 258h20v.5h-20zM64 258.5h163v.5h-163zM229.5 258.5h19.5v.5h-19.5zM64.5 259h40.5v.5h-40.5zM105.5 259h116v.5h-116zM222 259h4.5v.5h-4.5zM230 259h19v.5h-19zM65 259.5h39.5v.5h-39.5zM106 259.5h115v.5h-115zM223 259.5h3v.5h-3zM230.5 259.5h18.5v.5h-18.5zM65.5 260h38v.5h-38zM106.5 260h114v.5h-114zM224 260h1.5v.5h-1.5zM231 260h18v.5h-18zM66 260.5h37v.5h-37zM107 260.5h113v.5h-113zM231.5 260.5h17.5v.5h-17.5zM66.5 261h36v.5h-36zM107.5 261h112v.5h-112zM231.5 261h17.5v.5h-17.5zM67.5 261.5h34.5v.5h-34.5zM108 261.5h111v.5h-111zM231 261.5h18v.5h-18zM68.5 262h13.5v.5h-13.5zM83.5 262h17.5v.5h-17.5zM108.5 262h110v.5h-110zM230.5 262h18.5v.5h-18.5zM70 262.5h10.5v.5h-10.5zM84 262.5h16v.5h-16zM108 262.5h110.5v.5h-110.5zM231 262.5h10v.5h-10zM245 262.5h3.5v.5h-3.5zM71.5 263h6.5v.5h-6.5zM84.5 263h15v.5h-15zM108 263h110v.5h-110zM231.5 263h9v.5h-9zM85 263.5h13.5v.5h-13.5zM107.5 263.5h7.5v.5h-7.5zM115.5 263.5h102v.5h-102zM232 263.5h8v.5h-8zM85.5 264h11.5v.5h-11.5zM107.5 264h7v.5h-7zM116 264h101.5v.5h-101.5zM232.5 264h7v.5h-7zM86 264.5h10v.5h-10zM107 264.5h7v.5h-7zM116.5 264.5h101v.5h-101zM233 264.5h6v.5h-6zM86.5 265h8v.5h-8zM107 265h6v.5h-6zM117 265h100.5v.5h-100.5zM233.5 265h0.5v.5h-0.5zM234.5 265h0.5v.5h-0.5zM235.5 265h0.5v.5h-0.5zM237 265h0.5v.5h-0.5zM238 265h0.5v.5h-0.5zM87 265.5h5.5v.5h-5.5zM106.5 265.5h3v.5h-3zM110 265.5h2.5v.5h-2.5zM117.5 265.5h100v.5h-100zM86.5 266h3.5v.5h-3.5zM106 266h3v.5h-3zM110.5 266h0.5v.5h-0.5zM118 266h99.5v.5h-99.5zM106 266.5h2.5v.5h-2.5zM118.5 266.5h98.5v.5h-98.5zM106 267h2v.5h-2zM119 267h98v.5h-98zM119.5 267.5h97.5v.5h-97.5zM122 268h5v.5h-5zM128.5 268h88v.5h-88zM123 268.5h2v.5h-2zM129 268.5h87.5v.5h-87.5zM129.5 269h86.5v.5h-86.5zM130 269.5h86v.5h-86zM130.5 270h85v.5h-85zM131 270.5h84v.5h-84zM131.5 271h83v.5h-83zM132 271.5h82v.5h-82zM132 272h81.5v.5h-81.5zM132.5 272.5h80.5v.5h-80.5zM133 273h72v.5h-72zM205.5 273h7v.5h-7zM133.5 273.5h71v.5h-71zM206.5 273.5h5.5v.5h-5.5zM134 274h70v.5h-70zM207.5 274h4v.5h-4zM134.5 274.5h69v.5h-69zM209 274.5h1v.5h-1zM135 275h6v.5h-6zM142 275h61v.5h-61zM136.5 275.5h2v.5h-2zM142.5 275.5h60v.5h-60zM143 276h59v.5h-59zM143.5 276.5h58v.5h-58zM144 277h57v.5h-57zM144.5 277.5h56v.5h-56zM145 278h55v.5h-55zM145.5 278.5h54v.5h-54zM146 279h45v.5h-45zM193.5 279h5v.5h-5zM146.5 279.5h44v.5h-44zM195 279.5h2v.5h-2zM147.5 280h42.5v.5h-42.5zM148.5 280.5h41v.5h-41zM155.5 281h33.5v.5h-33.5zM158 281.5h3v.5h-3zM162.5 281.5h26v.5h-26zM163 282h24.5v.5h-24.5zM163.5 282.5h23.5v.5h-23.5zM164 283h22v.5h-22zM164.5 283.5h15v.5h-15zM181 283.5h4v.5h-4zM165 284h14v.5h-14zM165.5 284.5h13v.5h-13zM165.5 285h12.5v.5h-12.5zM166 285.5h11.5v.5h-11.5zM166.5 286h10.5v.5h-10.5zM167 286.5h9v.5h-9zM167.5 287h7.5v.5h-7.5zM168.5 287.5h5.5v.5h-5.5z', 'allowDelete': False},
    {'id':'ororaping','name':'오로라핑','emoji':'👑','svg':'<image href="/static/coloring/ororaping.svg?v=2" x="0" y="0" width="300" height="300"/>','regions':[{'type':'rect','x':0,'y':0,'w':300,'h':300}],'isCustomSheet':True,'contourPng':'/static/coloring/ororaping.svg?v=2','outerPath':'M160 12h0.5v0.5h-0.5zM159.5 12.5h2v0.5h-2zM158.5 13h3v0.5h-3zM158 13.5h4v0.5h-4zM157.5 14h4.5v0.5h-4.5zM157.5 14.5h5v0.5h-5zM157 15h5.5v0.5h-5.5zM156.5 15.5h6.5v0.5h-6.5zM156 16h7v0.5h-7zM152 16.5h11.5v0.5h-11.5zM151.5 17h12.5v0.5h-12.5zM151.5 17.5h13v0.5h-13zM151.5 18h14.5v0.5h-14.5zM151.5 18.5h15.5v0.5h-15.5zM151.5 19h16v0.5h-16zM143.5 20h1v0.5h-1zM152 19.5h16v1h-16zM142.5 20.5h2.5v0.5h-2.5zM152.5 20.5h15.5v0.5h-15.5zM141.5 21h3.5v0.5h-3.5zM152.5 21h15v0.5h-15zM141 21.5h4.5v0.5h-4.5zM152.5 21.5h14.5v0.5h-14.5zM140.5 22h5v0.5h-5zM152.5 22h14v0.5h-14zM140 22.5h6v0.5h-6zM152 22.5h14v0.5h-14zM139.5 23h7v0.5h-7zM151.5 23h14v0.5h-14zM139 23.5h8v0.5h-8zM151 23.5h14v0.5h-14zM139 24h8.5v0.5h-8.5zM149.5 24h15v0.5h-15zM138.5 24.5h26v0.5h-26zM107.5 25h2v0.5h-2zM106.5 25.5h3.5v0.5h-3.5zM138 25h26.5v1h-26.5zM174.5 25.5h1v0.5h-1zM106 26h4v0.5h-4zM138 26h27v0.5h-27zM173.5 26h2.5v0.5h-2.5zM105 26.5h5v0.5h-5zM138 26.5h27.5v0.5h-27.5zM172.5 26.5h4v0.5h-4zM104.5 27h5.5v0.5h-5.5zM138 27h28v0.5h-28zM172 27h4.5v0.5h-4.5zM104 27.5h6v0.5h-6zM138 27.5h28.5v0.5h-28.5zM171.5 27.5h5.5v0.5h-5.5zM103 28h7v0.5h-7zM137.5 28h30v0.5h-30zM170.5 28h6.5v0.5h-6.5zM102.5 28.5h7.5v0.5h-7.5zM137 28.5h31.5v0.5h-31.5zM170 28.5h7v0.5h-7zM102 29h8v0.5h-8zM136.5 29h32.5v0.5h-32.5zM169.5 29h8v0.5h-8zM101.5 29.5h8v0.5h-8zM136 29.5h41.5v0.5h-41.5zM100.5 30h9v0.5h-9zM135.5 30h42v0.5h-42zM100 30.5h9.5v0.5h-9.5zM135 30.5h43v0.5h-43zM99 31h10v0.5h-10zM134.5 31h43.5v0.5h-43.5zM98.5 31.5h10.5v0.5h-10.5zM131 31.5h47v0.5h-47zM97.5 32h11.5v0.5h-11.5zM130 32h48v0.5h-48zM97 32.5h11.5v0.5h-11.5zM129.5 32.5h49v0.5h-49zM96 33h12.5v0.5h-12.5zM128.5 33h50v0.5h-50zM95.5 33.5h12.5v0.5h-12.5zM128 33.5h51v0.5h-51zM94.5 34h14v0.5h-14zM127.5 34h52v0.5h-52zM94 34.5h14.5v0.5h-14.5zM127 34.5h53v0.5h-53zM93 35h16v0.5h-16zM127 35h54v0.5h-54zM92.5 35.5h16.5v0.5h-16.5zM126.5 35.5h55.5v0.5h-55.5zM91.5 36h17.5v0.5h-17.5zM126 36h57v0.5h-57zM91 36.5h18v0.5h-18zM126 36.5h57.5v0.5h-57.5zM90 37h19v0.5h-19zM125.5 37h59v0.5h-59zM89.5 37.5h19.5v0.5h-19.5zM125.5 37.5h59.5v0.5h-59.5zM89 38h19.5v0.5h-19.5zM125 38h60.5v0.5h-60.5zM88.5 38.5h20v0.5h-20zM124.5 38.5h61.5v0.5h-61.5zM88 39h20.5v0.5h-20.5zM124 39h62.5v0.5h-62.5zM87.5 39.5h20.5v0.5h-20.5zM123.5 39.5h63.5v0.5h-63.5zM87 40h21v0.5h-21zM122 40h66v0.5h-66zM86.5 40.5h21.5v0.5h-21.5zM121.5 40.5h67v0.5h-67zM86 41h22.5v0.5h-22.5zM120.5 41h68.5v0.5h-68.5zM85.5 41.5h23.5v0.5h-23.5zM120 41.5h69.5v0.5h-69.5zM85 42h24.5v0.5h-24.5zM119.5 42h70.5v0.5h-70.5zM85 42.5h26v0.5h-26zM119 42.5h71.5v0.5h-71.5zM84.5 43h27.5v0.5h-27.5zM119 43h72v0.5h-72zM84 43.5h29v0.5h-29zM118.5 43.5h73v0.5h-73zM84 44h30v0.5h-30zM118 44h74v0.5h-74zM83.5 44.5h31v0.5h-31zM117.5 44.5h75v0.5h-75zM198.5 44.5h3v0.5h-3zM83.5 45h32v0.5h-32zM117 45h76v0.5h-76zM198 45h4v0.5h-4zM83 45.5h33v0.5h-33zM116.5 45.5h77v0.5h-77zM197.5 45.5h5v0.5h-5zM83 46h110.5v0.5h-110.5zM197 46h6v0.5h-6zM82.5 46.5h111.5v0.5h-111.5zM196.5 46.5h6.5v0.5h-6.5zM82.5 47h112v0.5h-112zM196 47h7.5v0.5h-7.5zM82 47.5h113v0.5h-113zM195.5 47.5h8.5v0.5h-8.5zM82 48h122v1h-122zM81.5 49h123v1h-123zM81.5 50h123.5v0.5h-123.5zM81 50.5h124v0.5h-124zM81 51h124.5v1h-124.5zM81 52h125v0.5h-125zM80.5 52.5h126v0.5h-126zM80 53h126.5v0.5h-126.5zM79.5 53.5h127.5v0.5h-127.5zM79 54h128.5v0.5h-128.5zM78.5 54.5h129v0.5h-129zM78.5 55h129.5v0.5h-129.5zM78 55.5h130.5v0.5h-130.5zM78 56h131v0.5h-131zM77.5 56.5h132v0.5h-132zM77.5 57h132.5v1h-132.5zM77 58h133.5v0.5h-133.5zM77 58.5h134v0.5h-134zM77 59h134.5v0.5h-134.5zM77 59.5h135.5v0.5h-135.5zM77 60h136v0.5h-136zM77 60.5h136.5v0.5h-136.5zM77 61h137v0.5h-137zM77 61.5h137.5v0.5h-137.5zM77 62h138v0.5h-138zM77 62.5h138.5v0.5h-138.5zM77 63h139v0.5h-139zM77.5 63.5h139v0.5h-139zM77.5 64h139.5v0.5h-139.5zM77.5 64.5h140v0.5h-140zM77.5 65h140.5v0.5h-140.5zM77.5 65.5h141v0.5h-141zM77.5 66h141.5v0.5h-141.5zM77.5 66.5h142v0.5h-142zM78 67h142v0.5h-142zM78 67.5h142.5v1h-142.5zM78 68.5h143v0.5h-143zM78 69h143.5v1h-143.5zM78 70h144v0.5h-144zM77.5 70.5h144.5v0.5h-144.5zM77.5 71h145v1h-145zM77 72h146v1.5h-146zM77 73.5h146.5v0.5h-146.5zM76.5 74h147v2.5h-147zM76 76.5h147.5v2h-147.5zM75.5 78.5h148v0.5h-148zM75 79h148.5v0.5h-148.5zM74.5 79.5h149v0.5h-149zM74 80h149.5v0.5h-149.5zM73.5 80.5h150v0.5h-150zM73 81h151v0.5h-151zM73 81.5h151.5v0.5h-151.5zM72.5 82h152v1h-152zM72 83h153v1h-153zM71.5 84h153.5v0.5h-153.5zM71.5 84.5h154v1h-154zM71 85.5h154.5v1.5h-154.5zM71 87h155v1h-155zM70.5 88h155.5v1h-155.5zM70 89h156v0.5h-156zM69.5 89.5h156.5v0.5h-156.5zM69.5 90h156v0.5h-156zM69 90.5h156.5v1h-156.5zM68.5 91.5h157v0.5h-157zM68.5 92h156.5v1h-156.5zM68 93h156.5v1h-156.5zM68 94h156v1h-156zM67.5 95h156v0.5h-156zM67.5 95.5h155.5v0.5h-155.5zM67.5 96h155v1h-155zM67.5 97h154.5v0.5h-154.5zM67.5 97.5h154v0.5h-154zM67.5 98h153.5v0.5h-153.5zM67.5 98.5h153v0.5h-153zM67.5 99h152.5v0.5h-152.5zM68 99.5h151.5v1.5h-151.5zM67.5 101h151.5v0.5h-151.5zM67 101.5h152v1h-152zM66.5 102.5h152v1h-152zM66.5 103.5h151.5v0.5h-151.5zM66 104h151.5v1h-151.5zM66 105h151v0.5h-151zM65.5 105.5h151v0.5h-151zM65.5 106h150.5v1h-150.5zM65.5 107h151v3.5h-151zM66 110.5h151v1h-151zM66.5 111.5h150.5v0.5h-150.5zM67 112h150v0.5h-150zM67.5 112.5h149v0.5h-149zM68 113h148.5v0.5h-148.5zM68.5 113.5h148v0.5h-148zM69 114h147.5v0.5h-147.5zM69.5 114.5h146.5v0.5h-146.5zM70 115h146v0.5h-146zM70.5 115.5h145.5v0.5h-145.5zM70.5 116h145v1h-145zM70 117h145v0.5h-145zM70 117.5h144.5v0.5h-144.5zM70 118h144v0.5h-144zM70 118.5h143.5v0.5h-143.5zM70 119h143v0.5h-143zM70 119.5h143.5v1h-143.5zM70 120.5h144v0.5h-144zM69.5 121h144.5v0.5h-144.5zM69 121.5h145v0.5h-145zM68.5 122h145.5v0.5h-145.5zM68.5 122.5h146v0.5h-146zM68 123h146.5v1h-146.5zM67.5 124h147v1h-147zM67 125h147.5v1h-147.5zM66.5 126h148v1h-148zM66.5 127h147.5v0.5h-147.5zM66 127.5h148v1.5h-148zM66 129h147.5v1h-147.5zM65.5 130h147.5v2h-147.5zM65.5 132h148v1.5h-148zM65 133.5h148.5v2.5h-148.5zM65 136h148v1h-148zM65.5 137h147.5v0.5h-147.5zM65.5 137.5h148v0.5h-148zM65.5 138h148.5v0.5h-148.5zM65.5 138.5h149v0.5h-149zM65.5 139h149.5v0.5h-149.5zM65.5 139.5h150v0.5h-150zM65 140h151v0.5h-151zM64.5 140.5h151.5v0.5h-151.5zM64 141h152.5v0.5h-152.5zM62.5 141.5h154.5v0.5h-154.5zM62 142h155v0.5h-155zM62 142.5h155.5v1h-155.5zM62 143.5h156v1h-156zM62 144.5h156.5v1.5h-156.5zM62 146h157v1.5h-157zM61.5 147.5h158v1.5h-158zM61 149h158.5v1h-158.5zM61 150h159v0.5h-159zM60.5 150.5h159.5v3h-159.5zM61 153.5h159v0.5h-159zM61.5 154h158.5v0.5h-158.5zM62 154.5h158v1h-158zM61.5 155.5h158.5v0.5h-158.5zM61 156h159v1h-159zM60.5 157h159.5v1h-159.5zM60 158h160v0.5h-160zM60 158.5h159.5v0.5h-159.5zM59.5 159h160v1h-160zM59 160h160.5v1h-160.5zM59 161h160v0.5h-160zM58.5 161.5h160.5v1h-160.5zM58 162.5h161v0.5h-161zM58 163h160.5v1h-160.5zM57.5 164h161v1h-161zM57.5 165h160.5v1h-160.5zM57 166h161v1h-161zM57 167h160.5v1h-160.5zM56.5 168h161v3h-161zM56 171h161.5v1.5h-161.5zM56 172.5h162v1h-162zM56 173.5h162.5v0.5h-162.5zM56 174h163v0.5h-163zM55.5 174.5h164v0.5h-164zM55.5 175h164.5v0.5h-164.5zM55.5 175.5h165v1h-165zM55.5 176.5h165.5v0.5h-165.5zM55.5 177h166v0.5h-166zM55.5 177.5h166.5v0.5h-166.5zM55.5 178h167v1h-167zM55.5 179h167.5v0.5h-167.5zM55.5 179.5h168v0.5h-168zM55 180h169v1h-169zM55 181h169.5v0.5h-169.5zM55 181.5h170v1h-170zM55 182.5h170.5v1h-170.5zM55 183.5h171v0.5h-171zM55 184h171.5v1h-171.5zM55 185h172v1h-172zM55 186h172.5v0.5h-172.5zM54.5 186.5h173v0.5h-173zM54 187h173.5v0.5h-173.5zM53.5 187.5h174.5v0.5h-174.5zM51 188h177v0.5h-177zM49.5 188.5h179v0.5h-179zM48.5 189h180v0.5h-180zM47.5 189.5h181v0.5h-181zM46.5 190h182.5v0.5h-182.5zM46 190.5h183v0.5h-183zM45.5 191h183.5v0.5h-183.5zM44.5 191.5h185v0.5h-185zM44 192h185.5v0.5h-185.5zM43.5 192.5h186v0.5h-186zM43 193h186.5v0.5h-186.5zM43 193.5h187v0.5h-187zM42.5 194h187.5v0.5h-187.5zM42 194.5h188v0.5h-188zM41.5 195h188.5v1h-188.5zM41 196h189.5v1h-189.5zM40.5 197h190v1h-190zM40 198h190.5v1.5h-190.5zM39.5 199.5h191v2h-191zM39 201.5h191.5v4h-191.5zM39 205.5h191v2.5h-191zM39.5 208h190.5v2h-190.5zM40 210h189.5v1.5h-189.5zM40.5 211.5h189v1h-189zM41 212.5h188.5v1h-188.5zM41.5 213.5h188v1h-188zM42 214.5h187.5v0.5h-187.5zM42 215h188v0.5h-188zM42.5 215.5h187.5v1h-187.5zM43 216.5h187v0.5h-187zM239.5 216.5h6v0.5h-6zM43.5 217h186.5v0.5h-186.5zM237.5 217h10.5v0.5h-10.5zM43.5 217.5h187v0.5h-187zM236.5 217.5h13v0.5h-13zM44 218h186.5v0.5h-186.5zM235.5 218h15v0.5h-15zM44.5 218.5h186v0.5h-186zM234.5 218.5h17v0.5h-17zM45 219h185.5v0.5h-185.5zM234 219h18.5v0.5h-18.5zM45.5 219.5h185.5v0.5h-185.5zM233.5 219.5h19.5v0.5h-19.5zM46 220h185.5v0.5h-185.5zM233 220h21v0.5h-21zM46.5 220.5h185.5v0.5h-185.5zM232.5 220.5h22v0.5h-22zM47 221h208v0.5h-208zM47.5 221.5h208v0.5h-208zM48 222h208v0.5h-208zM48.5 222.5h208v0.5h-208zM49 223h207.5v0.5h-207.5zM50 223.5h207v0.5h-207zM50.5 224h207v0.5h-207zM51.5 224.5h206v0.5h-206zM52.5 225h205.5v0.5h-205.5zM53.5 225.5h205v0.5h-205zM55 226h203.5v0.5h-203.5zM56 226.5h202.5v0.5h-202.5zM57.5 227h201.5v0.5h-201.5zM59.5 227.5h199.5v0.5h-199.5zM61.5 228h12v0.5h-12zM74 228h185v0.5h-185zM67 228.5h0.5v0.5h-0.5zM74.5 228.5h184.5v0.5h-184.5zM75 229h184.5v0.5h-184.5zM75.5 229.5h184v0.5h-184zM75 230h184.5v0.5h-184.5zM74.5 230.5h185v1h-185zM74 231.5h185.5v0.5h-185.5zM73.5 232h186v0.5h-186zM73 232.5h186.5v1h-186.5zM72.5 233.5h186.5v0.5h-186.5zM72 234h187v0.5h-187zM71.5 234.5h187.5v1h-187.5zM71 235.5h188v0.5h-188zM71 236h187.5v0.5h-187.5zM70.5 236.5h188v0.5h-188zM70 237h188.5v1h-188.5zM69.5 238h188.5v0.5h-188.5zM69 238.5h189v1h-189zM68.5 239.5h189v1h-189zM68 240.5h189v1h-189zM67.5 241.5h189.5v0.5h-189.5zM67.5 242h189v0.5h-189zM67 242.5h189.5v0.5h-189.5zM67 243h189v0.5h-189zM66.5 243.5h189v1h-189zM66.5 244.5h188.5v0.5h-188.5zM66 245h189v0.5h-189zM66 245.5h188.5v0.5h-188.5zM65.5 246h188.5v1h-188.5zM65.5 247h188v0.5h-188zM65.5 247.5h187.5v0.5h-187.5zM65 248h187.5v1h-187.5zM65 249h187v0.5h-187zM65 249.5h186.5v0.5h-186.5zM65 250h186v0.5h-186zM65 250.5h185.5v0.5h-185.5zM65 251h185v0.5h-185zM65 251.5h184.5v0.5h-184.5zM65.5 252h183.5v0.5h-183.5zM65.5 252.5h183v0.5h-183zM65.5 253h182.5v0.5h-182.5zM66 253.5h181v0.5h-181zM66 254h180.5v0.5h-180.5zM66 254.5h130.5v0.5h-130.5zM198 254.5h48v0.5h-48zM66.5 255h129.5v0.5h-129.5zM199 255h46v0.5h-46zM67 255.5h127.5v0.5h-127.5zM200 255.5h44v0.5h-44zM67 256h126v0.5h-126zM201 256h42.5v0.5h-42.5zM67.5 256.5h125v0.5h-125zM202.5 256.5h39.5v0.5h-39.5zM68 257h124v0.5h-124zM203.5 257h37.5v0.5h-37.5zM68.5 257.5h123v0.5h-123zM205 257.5h35v0.5h-35zM69 258h2.5v0.5h-2.5zM72.5 258h116.5v0.5h-116.5zM207 258h31.5v0.5h-31.5zM73 258.5h112.5v0.5h-112.5zM208.5 258.5h28v0.5h-28zM73.5 259h111.5v0.5h-111.5zM211.5 259h23v0.5h-23zM74 259.5h110.5v0.5h-110.5zM214.5 259.5h17.5v0.5h-17.5zM73.5 260h110.5v0.5h-110.5zM220.5 260h7v0.5h-7zM73.5 260.5h110v0.5h-110zM73.5 261h109v0.5h-109zM73.5 261.5h104v0.5h-104zM73.5 262h103.5v0.5h-103.5zM73.5 262.5h103v0.5h-103zM73.5 263h102.5v0.5h-102.5zM73 263.5h102.5v0.5h-102.5zM73 264h101.5v0.5h-101.5zM73 264.5h100.5v0.5h-100.5zM73 265h99.5v0.5h-99.5zM73 265.5h98v0.5h-98zM73 266h96v0.5h-96zM73 266.5h95v0.5h-95zM73 267h94v0.5h-94zM72.5 267.5h85v0.5h-85zM159.5 267.5h6v0.5h-6zM72.5 268h84v0.5h-84zM72.5 268.5h5.5v0.5h-5.5zM79 268.5h74v0.5h-74zM72.5 269h5v0.5h-5zM79.5 269h73v0.5h-73zM73 269.5h4v0.5h-4zM80 269.5h72v0.5h-72zM73 270h3.5v0.5h-3.5zM80.5 270h71v0.5h-71zM73 270.5h3v0.5h-3zM81 270.5h70.5v0.5h-70.5zM73.5 271h2v0.5h-2zM81.5 271h70.5v0.5h-70.5zM82 271.5h21.5v0.5h-21.5zM104.5 271.5h47.5v0.5h-47.5zM83 272h19v0.5h-19zM105 272h47v0.5h-47zM84 272.5h11.5v0.5h-11.5zM105.5 272.5h46.5v0.5h-46.5zM88 273h7v0.5h-7zM106 273h45.5v0.5h-45.5zM89 273.5h5v0.5h-5zM106.5 273.5h45v1h-45zM107 274.5h44.5v1h-44.5zM107.5 275.5h44v0.5h-44zM108 276h43.5v0.5h-43.5zM108 276.5h43v0.5h-43zM108.5 277h42.5v0.5h-42.5zM108.5 277.5h42v0.5h-42zM109 278h41.5v0.5h-41.5zM109 278.5h41v0.5h-41zM109.5 279h40v1h-40zM110 280h24v0.5h-24zM134.5 280h14v0.5h-14zM110.5 280.5h23v0.5h-23zM135 280.5h13v0.5h-13zM110.5 281h22.5v0.5h-22.5zM135.5 281h11.5v0.5h-11.5zM111 281.5h21.5v0.5h-21.5zM136 281.5h9.5v0.5h-9.5zM111.5 282h20.5v0.5h-20.5zM136.5 282h7.5v0.5h-7.5zM112 282.5h20v0.5h-20zM112 283h19.5v0.5h-19.5zM112.5 283.5h19v0.5h-19zM113 284h18v0.5h-18zM114 284.5h16.5v0.5h-16.5zM114.5 285h15.5v0.5h-15.5zM115.5 285.5h13.5v0.5h-13.5zM116 286h12.5v0.5h-12.5zM117.5 286.5h9.5v0.5h-9.5zM118.5 287h7v0.5h-7zM120.5 287.5h2.5v0.5h-2.5z','allowDelete':False},
    {'id':'hachuping','name':'하츄핑','emoji':'💗','svg':'<image href="/static/coloring/hachuping.svg?v=2" x="0" y="0" width="300" height="300"/>','regions':[{'type':'rect','x':0,'y':0,'w':300,'h':300}],'isCustomSheet':True,'contourPng':'/static/coloring/hachuping.svg?v=2','outerPath':'M78 22h2.5v0.5h-2.5zM77.5 22.5h3.5v0.5h-3.5zM87 22.5h1.5v0.5h-1.5zM77 23h4.5v0.5h-4.5zM86 23h3v0.5h-3zM70 23.5h0.5v0.5h-0.5zM73 23.5h2v0.5h-2zM76.5 23.5h5.5v0.5h-5.5zM82.5 23.5h1v0.5h-1zM85.5 23.5h4v0.5h-4zM69 24h15.5v0.5h-15.5zM85 24h4.5v0.5h-4.5zM68.5 24.5h21.5v1h-21.5zM68 25.5h22v0.5h-22zM67.5 26h22.5v0.5h-22.5zM67 26.5h23.5v0.5h-23.5zM65.5 27h25.5v0.5h-25.5zM65 27.5h26.5v0.5h-26.5zM65 28h27v0.5h-27zM65 28.5h27.5v0.5h-27.5zM65 29h28v0.5h-28zM65.5 29.5h28v0.5h-28zM65.5 30h28.5v1h-28.5zM66 31h28.5v1h-28.5zM66 32h29v0.5h-29zM66.5 32.5h28.5v0.5h-28.5zM66.5 33h29v0.5h-29zM67 33.5h28.5v0.5h-28.5zM66.5 34h29v0.5h-29zM66 34.5h30v0.5h-30zM65.5 35h30.5v0.5h-30.5zM64 35.5h32v0.5h-32zM62.5 36h34v0.5h-34zM135.5 36h11.5v0.5h-11.5zM62 36.5h34.5v0.5h-34.5zM132.5 36.5h17v0.5h-17zM61.5 37h35v0.5h-35zM131 37h20.5v0.5h-20.5zM61.5 37.5h35.5v0.5h-35.5zM129.5 37.5h23.5v0.5h-23.5zM61 38h36.5v0.5h-36.5zM127.5 38h27v0.5h-27zM61 38.5h37v0.5h-37zM126.5 38.5h29.5v0.5h-29.5zM61 39h40.5v0.5h-40.5zM125 39h32.5v0.5h-32.5zM61 39.5h42v0.5h-42zM124 39.5h34.5v0.5h-34.5zM61 40h43.5v0.5h-43.5zM123.5 40h36v0.5h-36zM61 40.5h44.5v0.5h-44.5zM122.5 40.5h38v0.5h-38zM61 41h45v0.5h-45zM121.5 41h40v0.5h-40zM61.5 41.5h45.5v0.5h-45.5zM121 41.5h41.5v0.5h-41.5zM61.5 42h46v0.5h-46zM120 42h43.5v0.5h-43.5zM61.5 42.5h46.5v0.5h-46.5zM119.5 42.5h44.5v0.5h-44.5zM61.5 43h47.5v0.5h-47.5zM118.5 43h46.5v0.5h-46.5zM61.5 43.5h48v0.5h-48zM118 43.5h47.5v0.5h-47.5zM61.5 44h48.5v0.5h-48.5zM117.5 44h49v0.5h-49zM62 44.5h48.5v0.5h-48.5zM116.5 44.5h50.5v0.5h-50.5zM62 45h49v0.5h-49zM116 45h51.5v0.5h-51.5zM62 45.5h49.5v0.5h-49.5zM115.5 45.5h52.5v0.5h-52.5zM62 46h50v0.5h-50zM115 46h54v0.5h-54zM62 46.5h50.5v0.5h-50.5zM114.5 46.5h55v0.5h-55zM62 47h51v0.5h-51zM113.5 47h56.5v0.5h-56.5zM222 47h1.5v0.5h-1.5zM62.5 47.5h108v0.5h-108zM221.5 47.5h2.5v0.5h-2.5zM62.5 48h108.5v0.5h-108.5zM221 48h3.5v0.5h-3.5zM62.5 48.5h109v0.5h-109zM220.5 48.5h4.5v0.5h-4.5zM62.5 49h109.5v0.5h-109.5zM220 49h9.5v0.5h-9.5zM63 49.5h109.5v0.5h-109.5zM220 49.5h10v0.5h-10zM63 50h110v0.5h-110zM219.5 50h11v0.5h-11zM63 50.5h110.5v0.5h-110.5zM219 50.5h12v0.5h-12zM63.5 51h110v0.5h-110zM218.5 51h13v0.5h-13zM63.5 51.5h110.5v0.5h-110.5zM215 51.5h2.5v0.5h-2.5zM218 51.5h14v0.5h-14zM63 52h111.5v0.5h-111.5zM214 52h19v0.5h-19zM63 52.5h112v0.5h-112zM213.5 52.5h21.5v0.5h-21.5zM62.5 53h112.5v0.5h-112.5zM213 53h23v0.5h-23zM62.5 53.5h113v0.5h-113zM212.5 53.5h24v0.5h-24zM212 54h24.5v0.5h-24.5zM62 54h114v1h-114zM211.5 54.5h25v0.5h-25zM62 55h114.5v0.5h-114.5zM211 55h25.5v0.5h-25.5zM61.5 55.5h115v0.5h-115zM210.5 55.5h26v0.5h-26zM61 56h116v0.5h-116zM210 56h27v0.5h-27zM209.5 56.5h27.5v0.5h-27.5zM61 56.5h116.5v1h-116.5zM209.5 57h28v0.5h-28zM209 57.5h29v0.5h-29zM60.5 57.5h117.5v1h-117.5zM208.5 58h30v0.5h-30zM208 58.5h31v0.5h-31zM60 58.5h118.5v1h-118.5zM207.5 59h32v0.5h-32zM207 59.5h32.5v0.5h-32.5zM59.5 59.5h119.5v1h-119.5zM206.5 60h33v0.5h-33zM59 60.5h120.5v0.5h-120.5zM206 60.5h33.5v0.5h-33.5zM58.5 61h121v0.5h-121zM187 61h6.5v0.5h-6.5zM205.5 61h34v0.5h-34zM58 61.5h122v0.5h-122zM185.5 61.5h10v0.5h-10zM205 61.5h34.5v0.5h-34.5zM57 62h123v0.5h-123zM184 62h13v0.5h-13zM201.5 62h38v0.5h-38zM56 62.5h124.5v0.5h-124.5zM183.5 62.5h14.5v0.5h-14.5zM198.5 62.5h41v0.5h-41zM54.5 63h126.5v0.5h-126.5zM182.5 63h56.5v0.5h-56.5zM53.5 63.5h128v0.5h-128zM182 63.5h57v0.5h-57zM52.5 64h185.5v0.5h-185.5zM52 64.5h185.5v0.5h-185.5zM51 65h185.5v0.5h-185.5zM50.5 65.5h185v0.5h-185zM49.5 66h185.5v0.5h-185.5zM49 66.5h185.5v0.5h-185.5zM48.5 67h185.5v0.5h-185.5zM47.5 67.5h186v0.5h-186zM47 68h187v0.5h-187zM46.5 68.5h188v0.5h-188zM46 69h189v0.5h-189zM45.5 69.5h190.5v0.5h-190.5zM45 70h191.5v0.5h-191.5zM44.5 70.5h192.5v0.5h-192.5zM44 71h193.5v0.5h-193.5zM43.5 71.5h194.5v0.5h-194.5zM43 72h195v0.5h-195zM42.5 72.5h196v0.5h-196zM42 73h196v0.5h-196zM41.5 73.5h196.5v0.5h-196.5zM41.5 74h196v0.5h-196zM41 74.5h196.5v0.5h-196.5zM40.5 75h196.5v0.5h-196.5zM40 75.5h197v0.5h-197zM39.5 76h197v0.5h-197zM39 76.5h197v1h-197zM38.5 77.5h197v0.5h-197zM38 78h197v0.5h-197zM37.5 78.5h197.5v0.5h-197.5zM37.5 79h197v0.5h-197zM37 79.5h197v0.5h-197zM36.5 80h197v0.5h-197zM36.5 80.5h196.5v0.5h-196.5zM36 81h196.5v0.5h-196.5zM35.5 81.5h197v0.5h-197zM35.5 82h197.5v0.5h-197.5zM35 82.5h198.5v0.5h-198.5zM34.5 83h199.5v0.5h-199.5zM34.5 83.5h200.5v0.5h-200.5zM34 84h202v0.5h-202zM33.5 84.5h203.5v0.5h-203.5zM33.5 85h204v0.5h-204zM33 85.5h205.5v0.5h-205.5zM33 86h206v0.5h-206zM32.5 86.5h207.5v0.5h-207.5zM32 87h208.5v0.5h-208.5zM32 87.5h209v0.5h-209zM31.5 88h210v0.5h-210zM31.5 88.5h211v0.5h-211zM31 89h212v0.5h-212zM31 89.5h212.5v0.5h-212.5zM30.5 90h213.5v0.5h-213.5zM30.5 90.5h214v0.5h-214zM30 91h215v0.5h-215zM30 91.5h215.5v0.5h-215.5zM29.5 92h216.5v0.5h-216.5zM29.5 92.5h217v0.5h-217zM29 93h218v1h-218zM28.5 94h219v0.5h-219zM28.5 94.5h219.5v1h-219.5zM28 95.5h220.5v0.5h-220.5zM28 96h221v0.5h-221zM27.5 96.5h221.5v0.5h-221.5zM27.5 97h222v0.5h-222zM27.5 97.5h222.5v1h-222.5zM27 98.5h223.5v1h-223.5zM27 99.5h224v0.5h-224zM26.5 100h224.5v0.5h-224.5zM26.5 100.5h225v1h-225zM26.5 101.5h225.5v1h-225.5zM26 102.5h226.5v1h-226.5zM26 103.5h227v1h-227zM26 104.5h227.5v1.5h-227.5zM25.5 106h228.5v1h-228.5zM25.5 107h229v1.5h-229zM25.5 108.5h229.5v1.5h-229.5zM25.5 110h230v1h-230zM25.5 111h230.5v2h-230.5zM25.5 113h231v1.5h-231zM25.5 114.5h231.5v1.5h-231.5zM25.5 116h232v2h-232zM25.5 118h232.5v2h-232.5zM26 120h232.5v2h-232.5zM26 122h233v2h-233zM26.5 124h232.5v1h-232.5zM26.5 125h233v2h-233zM27 127h232.5v1.5h-232.5zM27 128.5h233v0.5h-233zM27.5 129h232.5v2h-232.5zM28 131h232v1h-232zM28 132h232.5v1h-232.5zM28.5 133h232v1.5h-232zM29 134.5h175.5v0.5h-175.5zM205 134.5h55.5v0.5h-55.5zM29 135h175v0.5h-175zM205.5 135h55v0.5h-55zM29 135.5h174.5v0.5h-174.5zM206 135.5h54.5v0.5h-54.5zM29.5 136h173.5v0.5h-173.5zM29.5 136.5h173v1h-173zM30 137.5h172.5v1h-172.5zM206.5 136h54v2.5h-54zM30.5 138.5h172v1h-172zM30.5 139.5h171.5v0.5h-171.5zM31 140h171v1h-171zM31.5 141h170.5v0.5h-170.5zM31.5 141.5h170v0.5h-170zM32 142h169.5v1h-169.5zM32.5 143h169v0.5h-169zM32.5 143.5h168.5v1h-168.5zM33 144.5h168v0.5h-168zM33.5 145h167.5v0.5h-167.5zM206.5 138.5h54.5v7h-54.5zM206.5 145.5h54v0.5h-54zM33.5 145.5h167v1h-167zM34 146.5h166.5v0.5h-166.5zM34 147h166v0.5h-166zM34.5 147.5h165.5v0.5h-165.5zM35 148h165v1h-165zM35.5 149h164v1h-164zM36 150h163.5v0.5h-163.5zM36 150.5h163v0.5h-163zM206 146h54.5v5.5h-54.5zM36.5 151h162.5v1h-162.5zM37 152h162v0.5h-162zM37 152.5h161.5v0.5h-161.5zM37.5 153h161v0.5h-161zM38 153.5h160.5v0.5h-160.5zM205.5 151.5h54.5v2.5h-54.5zM38 154h160v0.5h-160zM205.5 154h54v1h-54zM38.5 154.5h159.5v1h-159.5zM38 155.5h159.5v0.5h-159.5zM37.5 156h160v0.5h-160zM37 156.5h160.5v0.5h-160.5zM205 155h54.5v2h-54.5zM34 157h163.5v0.5h-163.5zM32.5 157.5h164.5v0.5h-164.5zM205 157h54v1h-54zM31 158h166v0.5h-166zM30 158.5h167v0.5h-167zM204.5 158h54.5v1h-54.5zM29.5 159h167v0.5h-167zM28.5 159.5h168v0.5h-168zM28 160h168.5v0.5h-168.5zM204.5 159h54v1.5h-54zM27.5 160.5h169v0.5h-169zM204 160.5h54.5v0.5h-54.5zM26.5 161h169.5v0.5h-169.5zM26 161.5h170v0.5h-170zM25.5 162h170.5v0.5h-170.5zM204 161h54v2h-54zM25 162.5h170.5v1h-170.5zM24.5 163.5h171v0.5h-171zM24 164h171.5v0.5h-171.5zM203.5 163h54v1.5h-54zM203.5 164.5h53.5v0.5h-53.5zM23.5 164.5h171.5v1h-171.5zM203 165h54v1h-54zM23 165.5h172v1h-172zM22.5 166.5h172v1h-172zM203 166h53.5v1.5h-53.5zM202.5 167.5h54.5v0.5h-54.5zM22 167.5h172.5v1h-172.5zM202.5 168h55v0.5h-55zM22 168.5h172v0.5h-172zM202 168.5h56v0.5h-56zM258.5 168.5h3.5v0.5h-3.5zM21.5 169h172.5v0.5h-172.5zM202 169h61.5v0.5h-61.5zM202 169.5h62.5v0.5h-62.5zM202 170h63.5v0.5h-63.5zM21.5 169.5h172v1.5h-172zM201.5 170.5h65v0.5h-65zM201.5 171h66v0.5h-66zM21 171h172v1h-172zM201.5 171.5h66.5v0.5h-66.5zM201 172h67.5v0.5h-67.5zM21 172h171.5v1h-171.5zM201 172.5h68.5v0.5h-68.5zM201 173h69v0.5h-69zM20.5 173h171.5v1h-171.5zM200.5 173.5h70v0.5h-70zM200.5 174h70.5v0.5h-70.5zM20.5 174h171v1h-171zM200.5 174.5h71v0.5h-71zM20.5 175h170.5v0.5h-170.5zM200.5 175h71.5v0.5h-71.5zM20.5 175.5h170v0.5h-170zM200 175.5h72.5v0.5h-72.5zM20.5 176h169.5v0.5h-169.5zM20.5 176.5h169v0.5h-169zM200 176h73v1h-73zM20.5 177h168.5v0.5h-168.5zM200 177h73.5v0.5h-73.5zM20.5 177.5h168v0.5h-168zM200 177.5h74v0.5h-74zM20.5 178h167.5v0.5h-167.5zM200 178h74.5v0.5h-74.5zM20.5 178.5h167v0.5h-167zM199.5 178.5h75v0.5h-75zM20.5 179h166.5v0.5h-166.5zM20.5 179.5h166v0.5h-166zM199.5 179h75.5v1h-75.5zM20.5 180h165.5v0.5h-165.5zM199.5 180h76v0.5h-76zM21 180.5h164v0.5h-164zM21 181h163v0.5h-163zM21 181.5h162.5v0.5h-162.5zM199.5 180.5h76.5v1.5h-76.5zM21 182h161.5v0.5h-161.5zM21 182.5h160.5v0.5h-160.5zM199 182h77.5v1h-77.5zM21.5 183h159v0.5h-159zM21.5 183.5h158v0.5h-158zM21.5 184h157v0.5h-157zM199 183h78v1.5h-78zM21.5 184.5h156v0.5h-156zM22 185h154v0.5h-154zM22 185.5h152.5v0.5h-152.5zM199 184.5h78.5v1.5h-78.5zM22 186h151v0.5h-151zM22.5 186.5h148.5v0.5h-148.5zM22.5 187h146v0.5h-146zM199 186h79v1.5h-79zM22.5 187.5h143.5v0.5h-143.5zM23 188h139.5v0.5h-139.5zM23 188.5h134.5v0.5h-134.5zM23.5 189h131.5v0.5h-131.5zM199 187.5h79.5v2h-79.5zM23.5 189.5h131v0.5h-131zM24 190h130v0.5h-130zM24 190.5h129.5v0.5h-129.5zM24.5 191h129v0.5h-129zM24.5 191.5h128.5v0.5h-128.5zM25 192h128v0.5h-128zM25.5 192.5h128v0.5h-128zM25.5 193h128.5v0.5h-128.5zM26 193.5h128.5v0.5h-128.5zM26.5 194h128.5v0.5h-128.5zM27 194.5h129v0.5h-129zM27.5 195h129.5v0.5h-129.5zM28 195.5h130v0.5h-130zM28.5 196h130.5v0.5h-130.5zM29 196.5h136.5v0.5h-136.5zM29.5 197h137.5v0.5h-137.5zM30 197.5h137.5v0.5h-137.5zM30.5 198h137.5v0.5h-137.5zM31 198.5h137.5v0.5h-137.5zM199 189.5h80v9.5h-80zM31.5 199h137.5v0.5h-137.5zM199.5 199h79.5v0.5h-79.5zM32 199.5h137.5v0.5h-137.5zM33 200h136.5v0.5h-136.5zM33.5 200.5h136.5v0.5h-136.5zM34 201h54.5v0.5h-54.5zM89 201h81v0.5h-81zM199.5 199.5h79v2h-79zM35 201.5h53v0.5h-53zM89.5 201.5h80.5v0.5h-80.5zM35.5 202h51.5v0.5h-51.5zM90 202h80v0.5h-80zM36.5 202.5h50v0.5h-50zM200 201.5h78v1.5h-78zM37 203h48.5v0.5h-48.5zM38 203.5h47v0.5h-47zM200 203h77.5v1h-77.5zM39 204h45v0.5h-45zM90.5 202.5h79.5v2h-79.5zM40 204.5h43.5v0.5h-43.5zM90.5 204.5h79v0.5h-79zM200.5 204h76.5v1h-76.5zM41 205h41.5v0.5h-41.5zM90 205h79.5v0.5h-79.5zM200.5 205h76v0.5h-76zM42 205.5h39.5v0.5h-39.5zM89.5 205.5h80v0.5h-80zM201 205.5h75.5v0.5h-75.5zM43 206h37.5v0.5h-37.5zM89 206h80v0.5h-80zM44 206.5h35v0.5h-35zM88.5 206.5h80.5v0.5h-80.5zM201 206h75v1h-75zM45.5 207h32.5v0.5h-32.5zM87.5 207h81v0.5h-81zM47 207.5h29.5v0.5h-29.5zM87 207.5h81v0.5h-81zM201.5 207h74v1h-74zM49 208h25.5v0.5h-25.5zM86.5 208h81v0.5h-81zM201.5 208h73.5v0.5h-73.5zM51 208.5h21.5v0.5h-21.5zM85.5 208.5h81v0.5h-81zM53.5 209h16v0.5h-16zM85 209h80v0.5h-80zM202 208.5h72.5v1h-72.5zM60 209.5h0.5v0.5h-0.5zM61 209.5h3.5v0.5h-3.5zM84.5 209.5h79v0.5h-79zM202.5 209.5h71.5v0.5h-71.5zM83.5 210h79v0.5h-79zM202.5 210h71v0.5h-71zM83 210.5h77.5v0.5h-77.5zM203 210.5h70.5v0.5h-70.5zM83 211h77v0.5h-77zM203 211h70v0.5h-70zM83 211.5h76.5v0.5h-76.5zM203.5 211.5h69v0.5h-69zM83 212h76v0.5h-76zM203.5 212h68.5v0.5h-68.5zM83 212.5h75.5v0.5h-75.5zM204 212.5h67.5v0.5h-67.5zM82.5 213h76.5v0.5h-76.5zM204.5 213h67v0.5h-67zM82 213.5h77.5v0.5h-77.5zM204.5 213.5h66.5v0.5h-66.5zM82 214h78v0.5h-78zM205 214h65.5v0.5h-65.5zM81.5 214.5h79v0.5h-79zM205.5 214.5h64.5v0.5h-64.5zM81 215h84v0.5h-84zM205.5 215h64v0.5h-64zM80.5 215.5h84.5v0.5h-84.5zM206 215.5h63v0.5h-63zM206.5 216h62v0.5h-62zM207 216.5h61v0.5h-61zM80 216h85v1.5h-85zM207.5 217h59.5v0.5h-59.5zM207.5 217.5h59v0.5h-59zM80 217.5h84.5v1h-84.5zM208 218h58v0.5h-58zM80.5 218.5h84v0.5h-84zM208.5 218.5h57v0.5h-57zM80 219h84.5v0.5h-84.5zM209 219h55.5v0.5h-55.5zM79.5 219.5h85.5v0.5h-85.5zM209.5 219.5h54.5v0.5h-54.5zM79 220h86v0.5h-86zM210 220h53.5v0.5h-53.5zM210.5 220.5h52v0.5h-52zM211 221h51v0.5h-51zM78.5 220.5h87v1.5h-87zM211.5 221.5h49.5v0.5h-49.5zM78 222h87.5v0.5h-87.5zM212.5 222h48v0.5h-48zM213 222.5h46.5v0.5h-46.5zM77.5 222.5h87.5v1h-87.5zM213.5 223h45v0.5h-45zM77 223.5h87.5v0.5h-87.5zM214.5 223.5h43.5v0.5h-43.5zM215.5 224h41.5v0.5h-41.5zM76.5 224h87.5v1h-87.5zM216.5 224.5h39.5v0.5h-39.5zM217.5 225h37.5v0.5h-37.5zM76 225h87.5v1h-87.5zM219 225.5h34.5v0.5h-34.5zM75.5 226h88v0.5h-88zM220.5 226h32v0.5h-32zM75.5 226.5h88.5v0.5h-88.5zM221.5 226.5h30v0.5h-30zM223.5 227h26.5v0.5h-26.5zM225 227.5h23.5v0.5h-23.5zM227 228h20v0.5h-20zM75 227h89v2h-89zM229.5 228.5h15v0.5h-15zM75.5 229h88v0.5h-88zM233 229h8.5v0.5h-8.5zM76 229.5h87v0.5h-87zM76.5 230h86v0.5h-86zM77 230.5h85.5v1h-85.5zM77.5 231.5h85v1h-85zM77.5 232.5h84.5v1h-84.5zM78 233.5h84v1h-84zM78.5 234.5h82.5v0.5h-82.5zM80.5 235h78v0.5h-78zM81 235.5h77v0.5h-77zM81.5 236h76v0.5h-76zM82 236.5h75v0.5h-75zM82.5 237h74.5v0.5h-74.5zM82.5 237.5h74v0.5h-74zM82.5 238h73.5v0.5h-73.5zM83 238.5h72.5v1h-72.5zM83 239.5h69v0.5h-69zM153 239.5h2v0.5h-2zM83.5 240h68v0.5h-68zM83.5 240.5h67.5v0.5h-67.5zM84 241h66.5v0.5h-66.5zM85.5 241.5h65v0.5h-65zM86 242h64.5v0.5h-64.5zM86.5 242.5h64v0.5h-64zM87 243h64v1.5h-64zM87.5 244.5h63.5v0.5h-63.5zM88 245h63v0.5h-63zM88.5 245.5h62.5v0.5h-62.5zM93 246h58v0.5h-58zM93.5 246.5h57.5v0.5h-57.5zM94 247h57v0.5h-57zM94.5 247.5h56.5v1h-56.5zM95 248.5h56v0.5h-56zM95.5 249h55.5v1h-55.5zM96.5 250h54.5v0.5h-54.5zM99.5 250.5h51.5v0.5h-51.5zM100 251h51v0.5h-51zM100.5 251.5h50.5v0.5h-50.5zM101 252h50v0.5h-50zM101.5 252.5h50v0.5h-50zM102 253h29v0.5h-29zM132 253h19.5v0.5h-19.5zM102.5 253.5h28v0.5h-28zM132.5 253.5h19v0.5h-19zM103 254h27v0.5h-27zM133 254h18.5v0.5h-18.5zM103 254.5h26.5v0.5h-26.5zM133.5 254.5h18v0.5h-18zM103.5 255h25.5v1h-25.5zM134 255h17v1h-17zM104 256h25v0.5h-25zM134.5 256h16.5v0.5h-16.5zM134.5 256.5h16v0.5h-16zM104.5 256.5h24.5v1h-24.5zM135 257h15.5v0.5h-15.5zM105 257.5h24v0.5h-24zM105.5 258h23.5v0.5h-23.5zM135.5 257.5h14.5v1h-14.5zM105.5 258.5h24v0.5h-24zM136 258.5h13.5v0.5h-13.5zM106 259h23.5v0.5h-23.5zM136.5 259h12.5v0.5h-12.5zM106.5 259.5h23v0.5h-23zM137.5 259.5h11v0.5h-11zM106.5 260h23.5v0.5h-23.5zM138 260h10v0.5h-10zM107 260.5h23v0.5h-23zM139 260.5h8.5v0.5h-8.5zM107.5 261h22.5v0.5h-22.5zM140 261h6.5v0.5h-6.5zM107.5 261.5h23v0.5h-23zM141.5 261.5h4v0.5h-4zM108 262h22.5v0.5h-22.5zM108.5 262.5h22v1h-22zM109 263.5h22v0.5h-22zM109.5 264h21.5v0.5h-21.5zM110 264.5h21v0.5h-21zM110 265h21.5v0.5h-21.5zM110.5 265.5h21v0.5h-21zM111 266h20.5v0.5h-20.5zM111.5 266.5h20v0.5h-20zM112 267h20v0.5h-20zM112.5 267.5h19.5v1h-19.5zM113 268.5h19.5v0.5h-19.5zM113.5 269h19v0.5h-19zM114 269.5h18.5v0.5h-18.5zM114.5 270h18v0.5h-18zM115 270.5h17.5v0.5h-17.5zM115.5 271h17v0.5h-17zM116 271.5h16.5v0.5h-16.5zM116.5 272h16v0.5h-16zM117 272.5h15v0.5h-15zM117.5 273h14.5v0.5h-14.5zM118 273.5h13.5v0.5h-13.5zM119 274h12.5v0.5h-12.5zM119.5 274.5h11.5v0.5h-11.5zM120.5 275h10v0.5h-10zM122 275.5h7.5v0.5h-7.5zM123.5 276h5v0.5h-5z','allowDelete':False},
    {'id':'princess-hachuping','name':'프린세스 하츄핑','emoji':'💖','svg':'<image href="/static/coloring/princess-hachuping.svg?v=2" x="0" y="0" width="300" height="300"/>','regions':[{'type':'rect','x':0,'y':0,'w':300,'h':300}],'isCustomSheet':True,'contourPng':'/static/coloring/princess-hachuping.svg?v=2','outerPath':'M185.5 12.5h2v0.5h-2zM184.5 13h3v0.5h-3zM184 13.5h4v0.5h-4zM183 14h5v0.5h-5zM182.5 14.5h6v0.5h-6zM181.5 15h7v0.5h-7zM181 15.5h7.5v0.5h-7.5zM180 16h9v0.5h-9zM179 16.5h10v0.5h-10zM178.5 17h11v0.5h-11zM178 17.5h11.5v1h-11.5zM178.5 18.5h11.5v1h-11.5zM179 19.5h11.5v1.5h-11.5zM179.5 21h11v0.5h-11zM179.5 21.5h10.5v0.5h-10.5zM179 22h10.5v0.5h-10.5zM178.5 22.5h10.5v0.5h-10.5zM178 23h10v0.5h-10zM176.5 23.5h11v0.5h-11zM175.5 24h11.5v0.5h-11.5zM103.5 24.5h3.5v0.5h-3.5zM174.5 24.5h12v0.5h-12zM101.5 25h7v0.5h-7zM174 25h12.5v0.5h-12.5zM100.5 25.5h9.5v0.5h-9.5zM173.5 25.5h13.5v0.5h-13.5zM99.5 26h11v0.5h-11zM173 26h14v0.5h-14zM99 26.5h12v0.5h-12zM172.5 26.5h15v0.5h-15zM98.5 27h13.5v0.5h-13.5zM164 27h2.5v0.5h-2.5zM172 27h16v0.5h-16zM97.5 27.5h15v0.5h-15zM162.5 27.5h5.5v0.5h-5.5zM171.5 27.5h16.5v0.5h-16.5zM97 28h18.5v0.5h-18.5zM161.5 28h7v0.5h-7zM171 28h17.5v0.5h-17.5zM97 28.5h21v0.5h-21zM161 28.5h8.5v0.5h-8.5zM170.5 28.5h18v0.5h-18zM96.5 29h23v0.5h-23zM160.5 29h28.5v0.5h-28.5zM96 29.5h25v0.5h-25zM160 29.5h29v0.5h-29zM95.5 30h27v0.5h-27zM159.5 30h30v0.5h-30zM95.5 30.5h28v0.5h-28zM145.5 30.5h8v0.5h-8zM159 30.5h30.5v0.5h-30.5zM95 31h29.5v0.5h-29.5zM142.5 31h14v0.5h-14zM158.5 31h31v0.5h-31zM95 31.5h30.5v0.5h-30.5zM140.5 31.5h49v0.5h-49zM94.5 32h32v0.5h-32zM139 32h50.5v0.5h-50.5zM94.5 32.5h32.5v0.5h-32.5zM137.5 32.5h52v0.5h-52zM94 33h34v0.5h-34zM136.5 33h53.5v0.5h-53.5zM86 33.5h3.5v0.5h-3.5zM93.5 33.5h35v0.5h-35zM135 33.5h55.5v0.5h-55.5zM84 34h7.5v0.5h-7.5zM93 34h36v0.5h-36zM134 34h57v0.5h-57zM192.5 34h2v0.5h-2zM82.5 34.5h47v0.5h-47zM133 34.5h63.5v0.5h-63.5zM82 35h48v0.5h-48zM132 35h65.5v0.5h-65.5zM81 35.5h49.5v0.5h-49.5zM131.5 35.5h66.5v0.5h-66.5zM80.5 36h118.5v0.5h-118.5zM80 36.5h119.5v0.5h-119.5zM79.5 37h120.5v0.5h-120.5zM79 37.5h121.5v0.5h-121.5zM79 38h122v0.5h-122zM78.5 38.5h122.5v0.5h-122.5zM78 39h123.5v1h-123.5zM78 40h124v0.5h-124zM77.5 40.5h124.5v1.5h-124.5zM77 42h125.5v4h-125.5zM77 46h125v0.5h-125zM77.5 46.5h124.5v1.5h-124.5zM78 48h124.5v0.5h-124.5zM78 48.5h125v0.5h-125zM78.5 49h125v0.5h-125zM78.5 49.5h125.5v0.5h-125.5zM79 50h126v0.5h-126zM79 50.5h126.5v0.5h-126.5zM79.5 51h126.5v0.5h-126.5zM80 51.5h126v0.5h-126zM80.5 52h126v1h-126zM80.5 53h126.5v1.5h-126.5zM80.5 54.5h127v3.5h-127zM80.5 58h126.5v1.5h-126.5zM80.5 59.5h126v1h-126zM80 60.5h126v0.5h-126zM79.5 61h126v0.5h-126zM79 61.5h126v0.5h-126zM78.5 62h126v0.5h-126zM77.5 62.5h126.5v0.5h-126.5zM77 63h126.5v0.5h-126.5zM76 63.5h127v0.5h-127zM75.5 64h128v0.5h-128zM75 64.5h128.5v0.5h-128.5zM74 65h129.5v0.5h-129.5zM216 65h2v0.5h-2zM73.5 65.5h130v0.5h-130zM213.5 65.5h7v0.5h-7zM73 66h130.5v0.5h-130.5zM212 66h10v0.5h-10zM72.5 66.5h131v0.5h-131zM210.5 66.5h12.5v0.5h-12.5zM71.5 67h132v0.5h-132zM209.5 67h14.5v0.5h-14.5zM71 67.5h133v0.5h-133zM209 67.5h15.5v0.5h-15.5zM70.5 68h134v0.5h-134zM207.5 68h18v0.5h-18zM70 68.5h135v0.5h-135zM206 68.5h21.5v0.5h-21.5zM69.5 69h159.5v0.5h-159.5zM69 69.5h161v0.5h-161zM68.5 70h162.5v0.5h-162.5zM68 70.5h164v0.5h-164zM67.5 71h165.5v0.5h-165.5zM67 71.5h167v0.5h-167zM66.5 72h168v0.5h-168zM66 72.5h169.5v0.5h-169.5zM65.5 73h170.5v0.5h-170.5zM65 73.5h171.5v0.5h-171.5zM64.5 74h173v0.5h-173zM64 74.5h174v0.5h-174zM63.5 75h175v0.5h-175zM63.5 75.5h175.5v0.5h-175.5zM63 76h176.5v0.5h-176.5zM62.5 76.5h177v0.5h-177zM62 77h178v0.5h-178zM61.5 77.5h179v0.5h-179zM61 78h180v0.5h-180zM61 78.5h180.5v0.5h-180.5zM60.5 79h181v0.5h-181zM60 79.5h182v0.5h-182zM59.5 80h183v1h-183zM59 81h184v0.5h-184zM58.5 81.5h184.5v0.5h-184.5zM58 82h185.5v1h-185.5zM57.5 83h186.5v0.5h-186.5zM57 83.5h187v0.5h-187zM57 84h187.5v0.5h-187.5zM56.5 84.5h188v0.5h-188zM56 85h189v1h-189zM55.5 86h190v0.5h-190zM55 86.5h190.5v1h-190.5zM54.5 87.5h191.5v1h-191.5zM54 88.5h192v0.5h-192zM53.5 89h192.5v0.5h-192.5zM53.5 89.5h193v0.5h-193zM53 90h193.5v1h-193.5zM52.5 91h194v1h-194zM52 92h195v1h-195zM51.5 93h195.5v1h-195.5zM51 94h196v1.5h-196zM50.5 95.5h196.5v1h-196.5zM50 96.5h197v1h-197zM49.5 97.5h197.5v1.5h-197.5zM49 99h198v1h-198zM48.5 100h198.5v1h-198.5zM48.5 101h198v0.5h-198zM48 101.5h198.5v1.5h-198.5zM47.5 103h199v0.5h-199zM47.5 103.5h198.5v1h-198.5zM47 104.5h199v1h-199zM46.5 105.5h199v1.5h-199zM46.5 107h199.5v0.5h-199.5zM46 107.5h200.5v0.5h-200.5zM46 108h201v0.5h-201zM46 108.5h201.5v0.5h-201.5zM45.5 109h202v0.5h-202zM45.5 109.5h202.5v0.5h-202.5zM45.5 110h203v0.5h-203zM45.5 110.5h203.5v0.5h-203.5zM45 111h204v0.5h-204zM45 111.5h204.5v0.5h-204.5zM45 112h205v0.5h-205zM45 112.5h205.5v0.5h-205.5zM44.5 113h206v0.5h-206zM44.5 113.5h206.5v0.5h-206.5zM44.5 114h207v0.5h-207zM44.5 114.5h207.5v1h-207.5zM44 115.5h208.5v0.5h-208.5zM44 116h209v1h-209zM44 117h209.5v1h-209.5zM44 118h210v0.5h-210zM43.5 118.5h211v1h-211zM43.5 119.5h211.5v1h-211.5zM43.5 120.5h212v0.5h-212zM43.5 121h212.5v0.5h-212.5zM43 121.5h213v0.5h-213zM43 122h213.5v1h-213.5zM43 123h214v1h-214zM43 124h214.5v1h-214.5zM43 125h215v0.5h-215zM42.5 125.5h215.5v0.5h-215.5zM42.5 126h216v1h-216zM42.5 127h216.5v1h-216.5zM42.5 128h217v1h-217zM42.5 129h217.5v1.5h-217.5zM42 130.5h218.5v1h-218.5zM42 131.5h219v1.5h-219zM42 133h219.5v1h-219.5zM42 134h220v1.5h-220zM42 135.5h220.5v2h-220.5zM42 137.5h221v1.5h-221zM42 139h221.5v2h-221.5zM42 141h222v2h-222zM42 143h222.5v1.5h-222.5zM42.5 144.5h222v1h-222zM42.5 145.5h222.5v2.5h-222.5zM42.5 148h163v0.5h-163zM206 148h59v0.5h-59zM42.5 148.5h162.5v0.5h-162.5zM206.5 148.5h58.5v0.5h-58.5zM42.5 149h162v0.5h-162zM207 149h58.5v0.5h-58.5zM43 149.5h161v1h-161zM43 150.5h160.5v1h-160.5zM43 151.5h160v1h-160zM43 152.5h159.5v0.5h-159.5zM42.5 153h160v0.5h-160zM42 153.5h160.5v0.5h-160.5zM41.5 154h160.5v0.5h-160.5zM36 154.5h166v0.5h-166zM34 155h167.5v0.5h-167.5zM207.5 149.5h58v6h-58zM33 155.5h168.5v0.5h-168.5zM32 156h169v0.5h-169zM31 156.5h170v0.5h-170zM30 157h170.5v0.5h-170.5zM207 155.5h58.5v2h-58.5zM29.5 157.5h171v0.5h-171zM29 158h171v0.5h-171zM28.5 158.5h171v0.5h-171zM27.5 159h172v0.5h-172zM207 157.5h59v2h-59zM27 159.5h172v1h-172zM26.5 160.5h172v0.5h-172zM26 161h172.5v0.5h-172.5zM206.5 159.5h59v2h-59zM25.5 161.5h172.5v0.5h-172.5zM25 162h173v0.5h-173zM25 162.5h172.5v0.5h-172.5zM24.5 163h172.5v0.5h-172.5zM206 161.5h59.5v2h-59.5zM24 163.5h173v0.5h-173zM24 164h172.5v0.5h-172.5zM23.5 164.5h173v0.5h-173zM205.5 163.5h60v1.5h-60zM23.5 165h172.5v0.5h-172.5zM23 165.5h172.5v1h-172.5zM205 165h60.5v2h-60.5zM22.5 166.5h172.5v1h-172.5zM204.5 167h61v0.5h-61zM22 167.5h172.5v0.5h-172.5zM204.5 167.5h60.5v0.5h-60.5zM22 168h172v1h-172zM22 169h171.5v0.5h-171.5zM204 168h61v1.5h-61zM21.5 169.5h171.5v1h-171.5zM21.5 170.5h171v0.5h-171zM203.5 169.5h61.5v1.5h-61.5zM203 171h62v0.5h-62zM21.5 171h170.5v1h-170.5zM203 171.5h61.5v0.5h-61.5zM21.5 172h170v0.5h-170zM21.5 172.5h169.5v0.5h-169.5zM21 173h170v0.5h-170zM202.5 172h62v1.5h-62zM21 173.5h169.5v0.5h-169.5zM202 173.5h62.5v1h-62.5zM21 174h169v1h-169zM202 174.5h62v0.5h-62zM21 175h168.5v0.5h-168.5zM21 175.5h168v0.5h-168zM201.5 175h62.5v1h-62.5zM21 176h167.5v1h-167.5zM201 176h63v1h-63zM21.5 177h166.5v0.5h-166.5zM21.5 177.5h166v0.5h-166zM200.5 177h63v1.5h-63zM21.5 178h165.5v1h-165.5zM200 178.5h63.5v0.5h-63.5zM21.5 179h165v0.5h-165zM200 179h63v0.5h-63zM21.5 179.5h164.5v0.5h-164.5zM199.5 179.5h63.5v1h-63.5zM21.5 180h164v1h-164zM199 180.5h64v0.5h-64zM21.5 181h163.5v0.5h-163.5zM21.5 181.5h163v0.5h-163zM199 181h63.5v1h-63.5zM22 182h162v0.5h-162zM198.5 182h64v1h-64zM22 182.5h161.5v1h-161.5zM198 183h64.5v0.5h-64.5zM22 183.5h161v0.5h-161zM198 183.5h64v0.5h-64zM22.5 184h160v0.5h-160zM22.5 184.5h159.5v0.5h-159.5zM197.5 184h64.5v1h-64.5zM22.5 185h159v0.5h-159zM23 185.5h158v0.5h-158zM197 185h64.5v1h-64.5zM23 186h157.5v0.5h-157.5zM196.5 186h65v0.5h-65zM23 186.5h157v0.5h-157zM23.5 187h156v0.5h-156zM196.5 186.5h64.5v1h-64.5zM23.5 187.5h155.5v0.5h-155.5zM23.5 188h155v0.5h-155zM196 187.5h65v1h-65zM24 188.5h154v0.5h-154zM24 189h153.5v0.5h-153.5zM195.5 188.5h65v1h-65zM24.5 189.5h152v0.5h-152zM195 189.5h65.5v0.5h-65.5zM24.5 190h151.5v0.5h-151.5zM195 190h65v0.5h-65zM24.5 190.5h151v0.5h-151zM25 191h149.5v0.5h-149.5zM194.5 190.5h65.5v1h-65.5zM25 191.5h149v0.5h-149zM25.5 192h147.5v0.5h-147.5zM194 191.5h65.5v1h-65.5zM25.5 192.5h147v0.5h-147zM26 193h145.5v0.5h-145.5zM193.5 192.5h66v1h-66zM26 193.5h144.5v0.5h-144.5zM193.5 193.5h65.5v0.5h-65.5zM26.5 194h143v0.5h-143zM193 194h66v0.5h-66zM27 194.5h141.5v0.5h-141.5zM193 194.5h65.5v0.5h-65.5zM27 195h140v0.5h-140zM27.5 195.5h138.5v0.5h-138.5zM192.5 195h66v1h-66zM27.5 196h137v0.5h-137zM28 196.5h135v0.5h-135zM192 196h66v1h-66zM28.5 197h132v0.5h-132zM191.5 197h66.5v0.5h-66.5zM29 197.5h129v0.5h-129zM29 198h128v0.5h-128zM191.5 197.5h66v1h-66zM29.5 198.5h127v0.5h-127zM30 199h126v0.5h-126zM191 198.5h66v1h-66zM30.5 199.5h125v0.5h-125zM31 200h125v0.5h-125zM190.5 199.5h66v1h-66zM31 200.5h125.5v0.5h-125.5zM190.5 200.5h65.5v0.5h-65.5zM31.5 201h125.5v0.5h-125.5zM32 201.5h134.5v0.5h-134.5zM190 201h66v1h-66zM32.5 202h136v0.5h-136zM33 202.5h136v0.5h-136zM189.5 202h66v1h-66zM33.5 203h136v0.5h-136zM34 203.5h136v0.5h-136zM189 203h66v1h-66zM35 204h135.5v0.5h-135.5zM189 204h65.5v0.5h-65.5zM35.5 204.5h135v0.5h-135zM188.5 204.5h66v0.5h-66zM36 205h135v0.5h-135zM36.5 205.5h134.5v0.5h-134.5zM188.5 205h65.5v1h-65.5zM37.5 206h133.5v0.5h-133.5zM38 206.5h133v0.5h-133zM188 206h65.5v1h-65.5zM39 207h132v0.5h-132zM39.5 207.5h131.5v0.5h-131.5zM187.5 207h65.5v1h-65.5zM40.5 208h130.5v0.5h-130.5zM187.5 208h65v0.5h-65zM41.5 208.5h129.5v0.5h-129.5zM42.5 209h128.5v0.5h-128.5zM187 208.5h65v1h-65zM43.5 209.5h127.5v0.5h-127.5zM187 209.5h64.5v0.5h-64.5zM44.5 210h126v0.5h-126zM186.5 210h65.5v0.5h-65.5zM45.5 210.5h125v0.5h-125zM186.5 210.5h66v0.5h-66zM46.5 211h123.5v0.5h-123.5zM186.5 211h66.5v0.5h-66.5zM48 211.5h122v0.5h-122zM186 211.5h72.5v0.5h-72.5zM50 212h18v0.5h-18zM68.5 212h101v0.5h-101zM186 212h75v0.5h-75zM51.5 212.5h14.5v0.5h-14.5zM69 212.5h100v0.5h-100zM186 212.5h76.5v0.5h-76.5zM54 213h9.5v0.5h-9.5zM69.5 213h99v0.5h-99zM185.5 213h78v0.5h-78zM70 213.5h98v0.5h-98zM185.5 213.5h79.5v0.5h-79.5zM69.5 214h98v0.5h-98zM185.5 214h80.5v0.5h-80.5zM69.5 214.5h97.5v0.5h-97.5zM185 214.5h81.5v0.5h-81.5zM69 215h97v0.5h-97zM185 215h82.5v0.5h-82.5zM69 215.5h96.5v0.5h-96.5zM185 215.5h83v0.5h-83zM69 216h69.5v0.5h-69.5zM140 216h24.5v0.5h-24.5zM185 216h83.5v0.5h-83.5zM68.5 216.5h69.5v0.5h-69.5zM141.5 216.5h21.5v0.5h-21.5zM184.5 216.5h85v0.5h-85zM68.5 217h69v0.5h-69zM143.5 217h18v0.5h-18zM184.5 217h85.5v0.5h-85.5zM146 217.5h13.5v0.5h-13.5zM184.5 217.5h86v0.5h-86zM68.5 217.5h68.5v1h-68.5zM150 218h6.5v0.5h-6.5zM184 218h87v0.5h-87zM68.5 218.5h69v0.5h-69zM184 218.5h87.5v0.5h-87.5zM68.5 219h69.5v1h-69.5zM184 219h88v1h-88zM68.5 220h70v0.5h-70zM184 220h88.5v0.5h-88.5zM68.5 220.5h70.5v0.5h-70.5zM183.5 220.5h89.5v0.5h-89.5zM68.5 221h71v0.5h-71zM68.5 221.5h71.5v0.5h-71.5zM183.5 221h90v1h-90zM68 222h72.5v0.5h-72.5zM183.5 222h90.5v0.5h-90.5zM67.5 222.5h73.5v0.5h-73.5zM67 223h74.5v0.5h-74.5zM183.5 222.5h91v1h-91zM67 223.5h75v0.5h-75zM183.5 223.5h91.5v0.5h-91.5zM66.5 224h76v0.5h-76zM183 224h92v0.5h-92zM66 224.5h77v0.5h-77zM66 225h77.5v0.5h-77.5zM183 224.5h92.5v1h-92.5zM65.5 225.5h78.5v0.5h-78.5zM65 226h79.5v0.5h-79.5zM183 225.5h93v1h-93zM65 226.5h80v0.5h-80zM64.5 227h81v0.5h-81zM183 226.5h93.5v1h-93.5zM64.5 227.5h81.5v0.5h-81.5zM183 227.5h94v0.5h-94zM64 228h83v0.5h-83zM63.5 228.5h84.5v0.5h-84.5zM182.5 228h94.5v1h-94.5zM63.5 229h85.5v0.5h-85.5zM63 229.5h87.5v0.5h-87.5zM63 230h88.5v0.5h-88.5zM62.5 230.5h91v0.5h-91zM182.5 229h95v2h-95zM62.5 231h93v0.5h-93zM157.5 231h4.5v0.5h-4.5zM62 231.5h100.5v1h-100.5zM61.5 232.5h101v0.5h-101zM182.5 231h95.5v2h-95.5zM61.5 233h101.5v0.5h-101.5zM61.5 233.5h102v0.5h-102zM61 234h103v1h-103zM60.5 235h103.5v1h-103.5zM182.5 233h96v3h-96zM60 236h104v1h-104zM183 236h95.5v1.5h-95.5zM59.5 237h104.5v1h-104.5zM59 238h105v0.5h-105zM59 238.5h104.5v0.5h-104.5zM58.5 239h105v0.5h-105zM58 239.5h101v0.5h-101zM160.5 239.5h2.5v0.5h-2.5zM183 237.5h96v2.5h-96zM57.5 240h101v0.5h-101zM57 240.5h101v0.5h-101zM57 241h100.5v0.5h-100.5zM56.5 241.5h100.5v0.5h-100.5zM56 242h100.5v0.5h-100.5zM183.5 240h95.5v2.5h-95.5zM55.5 242.5h101v0.5h-101zM183.5 242.5h95v0.5h-95zM55 243h100.5v0.5h-100.5zM54.5 243.5h100.5v0.5h-100.5zM54 244h100.5v0.5h-100.5zM184 243h94.5v1.5h-94.5zM53.5 244.5h100.5v0.5h-100.5zM53 245h100.5v0.5h-100.5zM52.5 245.5h101v0.5h-101zM184.5 244.5h94v1.5h-94zM52.5 246h101.5v0.5h-101.5zM185 246h93.5v0.5h-93.5zM52 246.5h102.5v0.5h-102.5zM185 246.5h93v1h-93zM52.5 247h102.5v1h-102.5zM52.5 248h103v0.5h-103zM185.5 247.5h92.5v1.5h-92.5zM52.5 248.5h103.5v1h-103.5zM186 249h91.5v1h-91.5zM53 249.5h103.5v1h-103.5zM186.5 250h91v1h-91zM53.5 250.5h103.5v1h-103.5zM186.5 251h90.5v0.5h-90.5zM54 251.5h103.5v1h-103.5zM187 251.5h90v1h-90zM53.5 252.5h104.5v1h-104.5zM187.5 252.5h89v1h-89zM53 253.5h105v0.5h-105zM188 253.5h88.5v0.5h-88.5zM52.5 254h106v0.5h-106zM188 254h88v0.5h-88zM188.5 254.5h87.5v0.5h-87.5zM52 254.5h106.5v1h-106.5zM189 255h86.5v1h-86.5zM189.5 256h85.5v0.5h-85.5zM190 256.5h85v0.5h-85zM51.5 255.5h107v2h-107zM190 257h84.5v0.5h-84.5zM52 257.5h106.5v0.5h-106.5zM190.5 257.5h83.5v0.5h-83.5zM52.5 258h106v0.5h-106zM191 258h83v0.5h-83zM53 258.5h105.5v0.5h-105.5zM191 258.5h82.5v0.5h-82.5zM53.5 259h105v0.5h-105zM191.5 259h81.5v0.5h-81.5zM54 259.5h104.5v0.5h-104.5zM192 259.5h81v0.5h-81zM55 260h103v0.5h-103zM192.5 260h80v0.5h-80zM56 260.5h102v0.5h-102zM193 260.5h79v0.5h-79zM56.5 261h101v0.5h-101zM193 261h78.5v0.5h-78.5zM58 261.5h99.5v0.5h-99.5zM193.5 261.5h77.5v0.5h-77.5zM59 262h98v0.5h-98zM194 262h76.5v0.5h-76.5zM61 262.5h4v0.5h-4zM66 262.5h90.5v0.5h-90.5zM194.5 262.5h76v0.5h-76zM67 263h89v0.5h-89zM195 263h75v0.5h-75zM67.5 263.5h87.5v0.5h-87.5zM195.5 263.5h74v0.5h-74zM68 264h86.5v0.5h-86.5zM196 264h73v0.5h-73zM69 264.5h84v0.5h-84zM196.5 264.5h72v0.5h-72zM69.5 265h40.5v0.5h-40.5zM112 265h36v0.5h-36zM197 265h71v0.5h-71zM70 265.5h39v0.5h-39zM114 265.5h32.5v0.5h-32.5zM197.5 265.5h70v0.5h-70zM71 266h37.5v0.5h-37.5zM116 266h29v0.5h-29zM198 266h69v0.5h-69zM72.5 266.5h6.5v0.5h-6.5zM80.5 266.5h27.5v0.5h-27.5zM119 266.5h23.5v0.5h-23.5zM199 266.5h67v0.5h-67zM81 267h26.5v0.5h-26.5zM122.5 267h17v0.5h-17zM199.5 267h66v0.5h-66zM81.5 267.5h26.5v0.5h-26.5zM129.5 267.5h4v0.5h-4zM200 267.5h65v0.5h-65zM82 268h26.5v0.5h-26.5zM200.5 268h64v0.5h-64zM82.5 268.5h26.5v0.5h-26.5zM201.5 268.5h62v0.5h-62zM83 269h26.5v0.5h-26.5zM202 269h61v0.5h-61zM83 269.5h27v0.5h-27zM202.5 269.5h59.5v0.5h-59.5zM83.5 270h27v0.5h-27zM203.5 270h58v0.5h-58zM84 270.5h26.5v0.5h-26.5zM204 270.5h56.5v0.5h-56.5zM84 271h27v0.5h-27zM205 271h54.5v0.5h-54.5zM206 271.5h52.5v0.5h-52.5zM84.5 271.5h26.5v1h-26.5zM206.5 272h51v0.5h-51zM207.5 272.5h49v0.5h-49zM85 272.5h26v1h-26zM208.5 273h47v0.5h-47zM209.5 273.5h45v0.5h-45zM85.5 273.5h25.5v1h-25.5zM210.5 274h42.5v0.5h-42.5zM86 274.5h25v0.5h-25zM212 274.5h39.5v0.5h-39.5zM86.5 275h24.5v0.5h-24.5zM213 275h37.5v0.5h-37.5zM86.5 275.5h24v0.5h-24zM214.5 275.5h34v0.5h-34zM216 276h31v0.5h-31zM87 276h23.5v1h-23.5zM218 276.5h27v0.5h-27zM220 277h23v0.5h-23zM87.5 277h22.5v1h-22.5zM222 277.5h18.5v0.5h-18.5zM225.5 278h11v0.5h-11zM87.5 278h22v1h-22zM87.5 279h21.5v0.5h-21.5zM87.5 279.5h21v1h-21zM87.5 280.5h20.5v0.5h-20.5zM88 281h19.5v0.5h-19.5zM88 281.5h19v0.5h-19zM88 282h18.5v0.5h-18.5zM88 282.5h18v0.5h-18zM88 283h17.5v0.5h-17.5zM88.5 283.5h16.5v0.5h-16.5zM88.5 284h16v0.5h-16zM89 284.5h15v0.5h-15zM89 285h14v0.5h-14zM89.5 285.5h13v0.5h-13zM90 286h11.5v0.5h-11.5zM91 286.5h9v0.5h-9zM92 287h6.5v0.5h-6.5z','allowDelete':False},
    {'id':'cat','name':'고양이','emoji':'🐱','svg':'''
<circle cx="150" cy="170" r="90"/>
<polygon points="70,110 110,40 130,110"/>
<polygon points="170,110 190,40 230,110"/>
<circle cx="120" cy="160" r="8" fill="#2b2b2b"/>
<circle cx="180" cy="160" r="8" fill="#2b2b2b"/>
<polygon points="140,190 160,190 150,205"/>
<line x1="100" y1="195" x2="40" y2="185"/>
<line x1="100" y1="205" x2="40" y2="210"/>
<line x1="200" y1="195" x2="260" y2="185"/>
<line x1="200" y1="205" x2="260" y2="210"/>
''','regions':[{'type':'circle','cx':150,'cy':170,'r':90},{'type':'polygon','points':[[70,110],[110,40],[130,110]]},{'type':'polygon','points':[[170,110],[190,40],[230,110]]}]},
    {'id':'dog','name':'강아지','emoji':'🐶','svg':'''
<circle cx="150" cy="170" r="85"/>
<ellipse cx="75" cy="165" rx="28" ry="55"/>
<ellipse cx="225" cy="165" rx="28" ry="55"/>
<circle cx="125" cy="160" r="8" fill="#2b2b2b"/>
<circle cx="175" cy="160" r="8" fill="#2b2b2b"/>
<ellipse cx="150" cy="195" rx="14" ry="10" fill="#2b2b2b"/>
<path d="M130,210 Q150,228 170,210"/>
''','regions':[{'type':'circle','cx':150,'cy':170,'r':85},{'type':'ellipse','cx':75,'cy':165,'rx':28,'ry':55},{'type':'ellipse','cx':225,'cy':165,'rx':28,'ry':55}]},
    {'id':'rabbit','name':'토끼','emoji':'🐰','svg':'''
<circle cx="150" cy="185" r="75"/>
<ellipse cx="120" cy="70" rx="18" ry="60"/>
<ellipse cx="180" cy="70" rx="18" ry="60"/>
<circle cx="125" cy="175" r="8" fill="#2b2b2b"/>
<circle cx="175" cy="175" r="8" fill="#2b2b2b"/>
<polygon points="140,205 160,205 150,218"/>
''','regions':[{'type':'circle','cx':150,'cy':185,'r':75},{'type':'ellipse','cx':120,'cy':70,'rx':18,'ry':60},{'type':'ellipse','cx':180,'cy':70,'rx':18,'ry':60}]},
    {'id':'fish','name':'물고기','emoji':'🐟','svg':'''
<ellipse cx="140" cy="150" rx="90" ry="55"/>
<polygon points="230,150 285,105 285,195"/>
<circle cx="95" cy="140" r="8" fill="#2b2b2b"/>
<polygon points="120,100 150,55 175,100"/>
''','regions':[{'type':'ellipse','cx':140,'cy':150,'rx':90,'ry':55},{'type':'polygon','points':[[230,150],[285,105],[285,195]]},{'type':'polygon','points':[[120,100],[150,55],[175,100]]}]},
    {'id':'apple','name':'사과','emoji':'🍎','svg':'''
<circle cx="150" cy="175" r="80"/>
<path d="M130,98 Q150,112 170,98"/>
<rect x="143" y="58" width="10" height="38"/>
<ellipse cx="178" cy="70" rx="20" ry="10"/>
''','regions':[{'type':'circle','cx':150,'cy':175,'r':80},{'type':'rect','x':143,'y':58,'w':10,'h':38},{'type':'ellipse','cx':178,'cy':70,'rx':20,'ry':10}]},
    {'id':'car','name':'자동차','emoji':'🚗','svg':'''
<rect x="45" y="150" width="210" height="70" rx="20"/>
<rect x="90" y="98" width="120" height="60" rx="15"/>
<line x1="150" y1="98" x2="150" y2="158"/>
<circle cx="100" cy="222" r="26"/>
<circle cx="200" cy="222" r="26"/>
''','regions':[{'type':'rect','x':45,'y':150,'w':210,'h':70},{'type':'rect','x':90,'y':98,'w':120,'h':60},{'type':'circle','cx':100,'cy':222,'r':26},{'type':'circle','cx':200,'cy':222,'r':26}]},
    {'id':'star','name':'별','emoji':'⭐','svg':'''
<polygon points="150,40 172,118 255,118 189,165 213,245 150,195 87,245 111,165 45,118 128,118"/>
''','regions':[{'type':'polygon','points':[[150,40],[172,118],[255,118],[189,165],[213,245],[150,195],[87,245],[111,165],[45,118],[128,118]]}]},
    {'id':'flower','name':'꽃','emoji':'🌸','svg':'''
<line x1="150" y1="170" x2="150" y2="270"/>
<ellipse cx="170" cy="235" rx="22" ry="12"/>
<circle cx="150" cy="100" r="30"/>
<circle cx="197" cy="130" r="30"/>
<circle cx="179" cy="185" r="30"/>
<circle cx="121" cy="185" r="30"/>
<circle cx="103" cy="130" r="30"/>
<circle cx="150" cy="150" r="22" fill="#2b2b2b" fill-opacity="0.08"/>
''','regions':[{'type':'circle','cx':150,'cy':100,'r':30},{'type':'circle','cx':197,'cy':130,'r':30},{'type':'circle','cx':179,'cy':185,'r':30},{'type':'circle','cx':121,'cy':185,'r':30},{'type':'circle','cx':103,'cy':130,'r':30},{'type':'circle','cx':150,'cy':150,'r':22},{'type':'rect','x':145,'y':170,'w':10,'h':100},{'type':'ellipse','cx':170,'cy':235,'rx':22,'ry':12}]},
    {'id':'house','name':'집','emoji':'🏠','svg':'''
<rect x="70" y="150" width="160" height="110"/>
<polygon points="50,150 150,70 250,150"/>
<rect x="135" y="200" width="30" height="60"/>
<rect x="90" y="170" width="30" height="30"/>
<rect x="180" y="170" width="30" height="30"/>
''','regions':[{'type':'rect','x':70,'y':150,'w':160,'h':110},{'type':'polygon','points':[[50,150],[150,70],[250,150]]},{'type':'rect','x':135,'y':200,'w':30,'h':60},{'type':'rect','x':90,'y':170,'w':30,'h':30},{'type':'rect','x':180,'y':170,'w':30,'h':30}]},
    {'id':'butterfly','name':'나비','emoji':'🦋','svg':'''
<ellipse cx="95" cy="120" rx="55" ry="65"/>
<ellipse cx="205" cy="120" rx="55" ry="65"/>
<ellipse cx="100" cy="205" rx="40" ry="48"/>
<ellipse cx="200" cy="205" rx="40" ry="48"/>
<line x1="145" y1="85" x2="120" y2="50"/>
<line x1="155" y1="85" x2="180" y2="50"/>
''','regions':[{'type':'ellipse','cx':95,'cy':120,'rx':55,'ry':65},{'type':'ellipse','cx':205,'cy':120,'rx':55,'ry':65},{'type':'ellipse','cx':100,'cy':205,'rx':40,'ry':48},{'type':'ellipse','cx':200,'cy':205,'rx':40,'ry':48},{'type':'rect','x':144,'y':80,'w':12,'h':150}]},
    {'id':'turtle','name':'거북이','emoji':'🐢','svg':'''
<circle cx="150" cy="170" r="80"/>
<circle cx="150" cy="80" r="32"/>
<ellipse cx="55" cy="130" rx="22" ry="30"/>
<ellipse cx="245" cy="130" rx="22" ry="30"/>
<ellipse cx="70" cy="220" rx="22" ry="28"/>
<ellipse cx="230" cy="220" rx="22" ry="28"/>
<circle cx="140" cy="75" r="6" fill="#2b2b2b"/>
<circle cx="160" cy="75" r="6" fill="#2b2b2b"/>
''','regions':[{'type':'circle','cx':150,'cy':170,'r':80},{'type':'circle','cx':150,'cy':80,'r':32},{'type':'ellipse','cx':55,'cy':130,'rx':22,'ry':30},{'type':'ellipse','cx':245,'cy':130,'rx':22,'ry':30},{'type':'ellipse','cx':70,'cy':220,'rx':22,'ry':28},{'type':'ellipse','cx':230,'cy':220,'rx':22,'ry':28}]},
    {'id':'duck','name':'오리','emoji':'🦆','svg':'''
<ellipse cx="150" cy="195" rx="85" ry="58"/>
<circle cx="105" cy="110" r="42"/>
<polygon points="65,110 20,100 65,125"/>
<circle cx="120" cy="98" r="6" fill="#2b2b2b"/>
''','regions':[{'type':'ellipse','cx':150,'cy':195,'rx':85,'ry':58},{'type':'circle','cx':105,'cy':110,'r':42},{'type':'polygon','points':[[65,110],[20,100],[65,125]]}]},
    {'id':'cake','name':'케이크','emoji':'🎂','svg':'''
<rect x="65" y="170" width="170" height="85"/>
<rect x="65" y="145" width="170" height="30"/>
<rect x="144" y="95" width="12" height="52"/>
<ellipse cx="150" cy="85" rx="11" ry="16"/>
''','regions':[{'type':'rect','x':65,'y':170,'w':170,'h':85},{'type':'rect','x':65,'y':145,'w':170,'h':30},{'type':'rect','x':144,'y':95,'w':12,'h':52},{'type':'ellipse','cx':150,'cy':85,'rx':11,'ry':16}]},
    {'id':'umbrella','name':'우산','emoji':'☂️','svg':'''
<polygon points="150,60 205,95 250,140 50,140 95,95"/>
<line x1="150" y1="140" x2="150" y2="245"/>
<path d="M150,245 Q135,255 140,235"/>
''','regions':[{'type':'polygon','points':[[150,60],[205,95],[250,140],[50,140],[95,95]]},{'type':'rect','x':145,'y':140,'w':10,'h':100}]},
    {'id':'tree','name':'나무','emoji':'🌳','svg':'''
<rect x="138" y="180" width="24" height="90"/>
<circle cx="150" cy="120" r="75"/>
''','regions':[{'type':'rect','x':138,'y':180,'w':24,'h':90},{'type':'circle','cx':150,'cy':120,'r':75}]},
]

@app.route('/hyeon/coloring')
def coloring_page():
    templates_json=json.dumps(COLORING_TEMPLATES,ensure_ascii=False)
    colors=['#e74c3c','#f39c12','#f1c40f','#2ecc71','#1abc9c','#3498db','#9b59b6','#e84393','#8d6e63','#2b2b2b']
    color_btns=''.join(f'<button type="button" class="cl-swatch" style="background:{c}" onclick="clSetColor(\'{c}\',this)"></button>' for c in colors)
    picker=''.join(f'<button type="button" class="cl-pick" id="cl-pick-{t["id"]}" onclick="clSelect(\'{t["id"]}\')">{t["emoji"]}<span>{H(t["name"])}</span></button>' for t in COLORING_TEMPLATES)
    body=f'''
<style>
.hg-topbar{{display:flex;gap:8px;margin-bottom:14px}}
.hg-btn{{width:56px;height:56px;border-radius:16px;border:1px solid #e4e9f0;background:#fff;font-size:26px;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.cl-picker-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(84px,1fr));gap:10px;margin-bottom:12px}}
.cl-pick{{aspect-ratio:1;border-radius:18px;border:2px solid #e4e9f0;background:#fff;font-size:34px;cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px}}
.cl-pick span{{font-size:11px;font-weight:800;color:#748196}}
.cl-pick.on{{border-color:#0f4c81;background:#eaf3fb}}
.cl-canvas-wrap{{position:relative;width:100%;max-width:340px;aspect-ratio:1/1;margin:0 auto 14px;background:#fff;border:2px solid #e4e9f0;border-radius:20px;overflow:hidden}}
.cl-canvas{{position:absolute;inset:0;touch-action:none}}
.cl-outline{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}
.cl-outline *{{fill:none;stroke:#2b2b2b;stroke-width:5;stroke-linejoin:round;stroke-linecap:round}}
.cl-palette{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:12px}}
.cl-swatch{{width:44px;height:44px;border-radius:50%;border:2px solid #e4e9f0;cursor:pointer}}
.cl-swatch.on{{border-color:#14263f;border-width:3px}}
.cl-tools{{display:flex;gap:8px;justify-content:center}}
@media(max-width:430px){{.hg-btn{{width:48px;height:48px;font-size:22px}}}}
</style>
<div class="hg-topbar">
<a class="hg-btn" href="/hyeon">🏠</a>
<button type="button" class="hg-btn" onclick="clClear()">🔄</button>
</div>
<div class="cl-picker-row">{picker}</div>
<div class="cl-canvas-wrap">
  <canvas class="cl-canvas" id="cl-canvas"></canvas>
  <div id="cl-celebration" role="status" hidden style="position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:3;padding:12px 20px;border-radius:20px;background:#fff4c7;font-size:22px;font-weight:800;white-space:nowrap;pointer-events:none">🎉 완성! 참 잘했어요!</div><svg class="cl-outline" id="cl-outline" viewBox="0 0 300 300"></svg>
</div>
<div class="cl-palette">{color_btns}</div>
<script>
const CL_TEMPLATES={templates_json};
let clColor='#e74c3c';
let clCurrent=CL_TEMPLATES[0];
let clCtx=null, clDrawing=false, clCompleted=false;
function clSetColor(c,btn){{
  clColor=c;
  document.querySelectorAll('.cl-swatch').forEach(function(x){{x.classList.remove('on')}});
  btn.classList.add('on');
}}
let clAudioCtx=null;
function clUnlockAudio(){{
  try{{
    if(!clAudioCtx) clAudioCtx=new (window.AudioContext||window.webkitAudioContext)();
    if(clAudioCtx.state==='suspended') clAudioCtx.resume();
    const buffer=clAudioCtx.createBuffer(1,1,22050);
    const source=clAudioCtx.createBufferSource();
    source.buffer=buffer; source.connect(clAudioCtx.destination); source.start(0);
  }}catch(e){{}}
}}
function clChime(){{
  try{{
    if(!clAudioCtx) clAudioCtx=new (window.AudioContext||window.webkitAudioContext)();
    if(clAudioCtx.state==='suspended') clAudioCtx.resume();
    const notes=[659.25,523.25,783.99];
    notes.forEach(function(freq,i){{
      const t=clAudioCtx.currentTime+i*0.12;
      const osc=clAudioCtx.createOscillator();
      const gain=clAudioCtx.createGain();
      osc.type='sine'; osc.frequency.value=freq;
      gain.gain.setValueAtTime(0.0001,t);
      gain.gain.linearRampToValueAtTime(0.28,t+0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001,t+0.35);
      osc.connect(gain); gain.connect(clAudioCtx.destination);
      osc.start(t); osc.stop(t+0.37);
    }});
  }}catch(e){{}}
}}
const CL_VB=300;
let clScale=1, clClipReady=false;
function clBuildClipPath(regions){{
  const path=new Path2D();
  (regions||[]).forEach(function(r){{
    if(r.type==='circle'){{
      path.moveTo((r.cx+r.r)*clScale,r.cy*clScale);
      path.ellipse(r.cx*clScale,r.cy*clScale,r.r*clScale,r.r*clScale,0,0,Math.PI*2);
    }} else if(r.type==='ellipse'){{
      path.moveTo((r.cx+r.rx)*clScale,r.cy*clScale);
      path.ellipse(r.cx*clScale,r.cy*clScale,r.rx*clScale,r.ry*clScale,0,0,Math.PI*2);
    }} else if(r.type==='rect'){{
      path.rect(r.x*clScale,r.y*clScale,r.w*clScale,r.h*clScale);
    }} else if(r.type==='polygon'){{
      r.points.forEach(function(p,i){{
        const px=p[0]*clScale, py=p[1]*clScale;
        if(i===0) path.moveTo(px,py); else path.lineTo(px,py);
      }});
      path.closePath();
    }}
  }});
  return path;
}}
function clPaintPath(){{
  const path=clCurrent.outerPath ? new Path2D() : clBuildClipPath(clCurrent.regions);
  if(clCurrent.outerPath) path.addPath(new Path2D(clCurrent.outerPath),new DOMMatrix().scale(clScale));
  return path;
}}
function clApplyClip(){{
  clCtx.save();
  clClipReady=true;
  clCtx.clip(clPaintPath());
}}
function clResetCanvas(){{
  if(!clCtx) return;
  if(clClipReady){{ clCtx.restore(); clClipReady=false; }}
  clCtx.clearRect(0,0,clCtx.canvas.width,clCtx.canvas.height);
  clApplyClip();
  clCompleted=false;
  const celebration=document.getElementById('cl-celebration');
  if(celebration) celebration.hidden=true;
}}
function clSelect(id){{
  if(document.activeElement&&document.activeElement.blur) document.activeElement.blur();
  clCurrent=CL_TEMPLATES.find(function(t){{return t.id===id}})||CL_TEMPLATES[0];
  document.querySelectorAll('.cl-pick').forEach(function(x){{x.classList.remove('on')}});
  document.getElementById('cl-pick-'+clCurrent.id).classList.add('on');
  document.getElementById('cl-outline').innerHTML=clCurrent.svg;
  clResetCanvas();
}}
function clClear(){{ clResetCanvas(); }}
function clCheckComplete(){{
  if(!clCtx||clCompleted) return;
  const path=clPaintPath();
  const w=clCtx.canvas.width, h=clCtx.canvas.height;
  const img=clCtx.getImageData(0,0,w,h).data;
  const step=Math.max(4,Math.round(clScale*8));
  let total=0, filled=0;
  for(let y=0;y<h;y+=step){{
    for(let x=0;x<w;x+=step){{
      if(clCtx.isPointInPath(path,x,y)){{
        total++;
        const idx=(y*w+x)*4;
        if(img[idx+3]>40) filled++;
      }}
    }}
  }}
  if(total>0 && filled/total>=0.90){{
    clCompleted=true;
    clChime();
    const celebration=document.getElementById('cl-celebration');
    if(celebration){{celebration.hidden=false;setTimeout(function(){{celebration.hidden=true;}},2200);}}

  }}
}}
function clInit(){{
  const cvs=document.getElementById('cl-canvas');
  const wrap=cvs.parentElement;
  cvs.width=wrap.clientWidth; cvs.height=wrap.clientHeight;
  clScale=cvs.width/CL_VB;
  clCtx=cvs.getContext('2d');
  clCtx.lineCap='round'; clCtx.lineJoin='round'; clCtx.lineWidth=22;
  function pos(e){{
    const r=cvs.getBoundingClientRect();
    const p=(e.touches&&e.touches[0])||e;
    return [p.clientX-r.left,p.clientY-r.top];
  }}
  function start(e){{ e.preventDefault(); clUnlockAudio(); clDrawing=true; clCtx.strokeStyle=clColor; const[x,y]=pos(e); clCtx.beginPath(); clCtx.moveTo(x,y); clCtx.lineTo(x+0.1,y+0.1); clCtx.stroke(); }}
  function move(e){{ if(!clDrawing)return; e.preventDefault(); clCtx.strokeStyle=clColor; const[x,y]=pos(e); clCtx.lineTo(x,y); clCtx.stroke(); }}
  function end(e){{ if(!clDrawing)return; clDrawing=false; clCheckComplete(); }}
  cvs.addEventListener('mousedown',start); cvs.addEventListener('mousemove',move); window.addEventListener('mouseup',end);
  cvs.addEventListener('touchstart',start,{{passive:false}}); cvs.addEventListener('touchmove',move,{{passive:false}}); cvs.addEventListener('touchend',end);
}}
clInit();
clSelect(CL_TEMPLATES[0].id);
document.querySelector('.cl-swatch').classList.add('on');
</script>
<script src="/static/hyeon-custom-coloring.js?v=20261015-completion-v4"></script>
'''
    return page('혜온 색칠 공부',body)

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/calendar': app.view_functions[rule.endpoint]=family_calendar
    elif rule.rule=='/riley': app.view_functions[rule.endpoint]=riley_week
app.add_url_rule('/hyeon','hyeon_week',hyeon_week)

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


def _event_detail_attrs(dd, k):
    trip_id = dd.get('trip_id') if dd.get('source') == 'trip' else ''
    source = dd.get('source') or 'local'
    fields = {
        'title': dd.get('title') or '',
        'start_date': dd.get('start_date') or '',
        'end_date': dd.get('end_date') or dd.get('start_date') or '',
        'start_time': dd.get('start_time') or '',
        'end_time': dd.get('end_time') or '',
        'kind': k,
        'person': dd.get('person') or '',
        'notes': dd.get('notes') or '',
        'source': source,
        'trip_id': trip_id or '',
        'id': dd.get('id') if source == 'local' and dd.get('id') is not None else '',
        'key': _event_key(dd),
    }
    return ' '.join(f'data-{key}="{H(val)}"' for key, val in fields.items())

def event_detail_modal():
    return '''<div class="modal" id="ed"><div class="card"><div class="head"><h2 id="ed-title"></h2><button class="btn s" onclick="x('ed')">닫기</button></div>
<div class="meta"><div class="m"><b>날짜</b><span id="ed-date"></span></div><div class="m"><b>시간</b><span id="ed-time"></span></div><div class="m"><b>구분</b><span id="ed-kind"></span></div><div class="m"><b>사람</b><span id="ed-person"></span></div></div>
<div style="margin-top:10px"><b>메모</b><div id="ed-notes" class="muted" style="margin-top:4px"></div></div>
<div id="ed-triplink" style="margin-top:12px"></div>
<form id="ed-delete-form" method="post" style="display:none;margin-top:12px" onsubmit="return confirm('삭제할까요?')"><button type="submit" class="btn d">삭제</button></form></div></div>'''

def family_calendar():
    view = (request.args.get('view') or 'month').lower()
    q = qdate(request.args.get('date','')) or date.today()
    today = date.today()
    person = (request.args.get('person') or '').strip()
    if person not in PEOPLE + ['여행']:
        person = ''
    if view == 'week':
        start = q - timedelta(days=q.weekday()); end = start + timedelta(days=6)
        prev=(start-timedelta(days=7)).isoformat(); nxt=(start+timedelta(days=7)).isoformat()
        title=f'{start.strftime("%Y.%m.%d")} ~ {end.strftime("%m.%d")}'
    else:
        start=date(q.year,q.month,1); end=date(q.year,q.month,pycal.monthrange(q.year,q.month)[1])
        prev=(start-timedelta(days=1)).replace(day=1).isoformat(); nxt=(end+timedelta(days=1)).replace(day=1).isoformat()
        title=f'{q.year}년 {q.month}월'
    events=family_events(start,end)
    if person:
        events=[e for e in events if _kind(dict(e))==person]
    pq=f'&person={person}' if person else ''
    tabs=(f'<div class="seg"><a class="{"on" if view=="month" else ""}" href="/calendar?view=month&date={q.isoformat()}{pq}">월</a><a class="{"on" if view=="week" else ""}" href="/calendar?view=week&date={q.isoformat()}{pq}">주</a></div>')
    toolbar=(f'<div class="cal-toolbar"><div class="cal-nav"><a class="btn s" href="/calendar?view={view}&date={prev}{pq}">←</a><a class="btn s" href="/calendar?view={view}&date={today.isoformat()}{pq}">오늘</a><a class="btn s" href="/calendar?view={view}&date={nxt}{pq}">→</a></div><div class="cal-title">{title}</div>{tabs}</div>')
    person_filter='<div class="person-filter">'+''.join(
        f'<a class="pf {_kind_class(pp)} {"on" if person==pp else ""}" href="/calendar?view={view}&date={q.isoformat()}{"&person="+pp if pp else ""}">{H(pp) if pp else "전체"}</a>'
        for pp in ['']+PEOPLE+['여행']
    )+'</div>'
    if view == 'week':
        cal='<div class="week-cards">'
        for i in range(7):
            d=start+timedelta(days=i); de=[e for e in events if _overlaps(e,d)]
            cal+=f'<div class="week-card {"today" if d==today else ""}"><div class="week-date">{d.strftime("%m/%d")}</div><h3>{DAYS[i]}</h3>'
            if not de: cal+='<div class="muted">일정 없음</div>'
            for e in de:
                dd=dict(e); k=_kind(dd)
                cal+=f'<div class="event-chip {_kind_class(k)}" {_event_detail_attrs(dd,k)} onclick="showEventDetail(this)"><b>{H(dd.get("title"))}</b><div class="muted">{H(k)}</div></div>'
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
                cal+=f'<div class="fm-event {_kind_class(k)}" title="{H(dd.get("title"))}" {_event_detail_attrs(dd,k)} onclick="showEventDetail(this)">{H(dd.get("title"))}</div>'
            if len(de)>5: cal+=f'<div class="muted">+{len(de)-5}개</div>'
            cal+='</div>'
        cal+='</div></div>'
    return page('가족 달력', toolbar+person_filter+cal+event_detail_modal())

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

TRIP_STATUSES=('예정','검토 중','장기 계획','완료')
def _status_class(s):
    return {'완료':'done','예정':'planned','검토 중':'review','장기 계획':'longterm'}.get((s or '').strip(),'other')

TRANSPORT_OPTIONS=('비행기','기차','고속버스','자가용','배','기타')
COMPANION_OPTIONS=('가족','용제','보미','지유','혜온')
QUICK_EDIT_FIELDS=('title','start_date','end_date','country','region','lodging','transport','companions')

def _select_options(options,current):
    opts=list(options)
    if current and current not in opts:
        opts=[current]+opts
    return ''.join(f'<option value="{H(o)}" {"selected" if o==current else ""}>{H(o)}</option>' for o in opts)

@app.route('/trip/<int:trip_id>/quick-edit',methods=['POST'])
def trip_quick_edit(trip_id):
    updates={k:request.form[k] for k in QUICK_EDIT_FIELDS if k in request.form}
    if not updates: return redirect(request.referrer or f'/trip/{trip_id}')
    before=row_snapshot('trips',trip_id); backup_db('prechange')
    c=db(); c.execute('update trips set '+','.join(f'{k}=?' for k in updates)+' where id=?',list(updates.values())+[trip_id]); c.commit(); c.close()
    after=row_snapshot('trips',trip_id); log_change('trips',trip_id,'edit',before,after)
    return redirect(request.referrer or f'/trip/{trip_id}')

@app.route('/trip/<int:trip_id>/status',methods=['POST'])
def set_trip_status(trip_id):
    status=(request.form.get('status') or '').strip()
    if status not in TRIP_STATUSES: return abort(400)
    before=row_snapshot('trips',trip_id); backup_db('prechange'); c=db(); c.execute('update trips set status=? where id=?',(status,trip_id)); c.commit(); c.close(); after=row_snapshot('trips',trip_id); log_change('trips',trip_id,'edit',before,after); return redirect(request.referrer or f'/trip/{trip_id}')


# ===== editable trip detail =====
def trip_attrs(r):
    keys=['id','start_date','end_date','country','region','title','companions','trip_type','status','lodging','transport','notes']; return ' '.join('data-'+k+'="'+H(r[k])+'"' for k in keys)
def itinerary_attrs(x):
    keys=['id','trip_id','item_date','day_label','time_text','title','place','detail','sort_order']; return ' '.join('data-'+k+'="'+H(x[k])+'"' for k in keys)

def _trip_overview(r):
    back='/past' if r['status']=='완료' else '/future'
    scls=_status_class(r['status'])
    stopts=''.join(f'<option value="{H(s)}" {"selected" if r["status"]==s else ""}>{H(s)}</option>' for s in TRIP_STATUSES)
    actions=(f'<div class="trip-actions"><a class="btn s" href="{back}">← 여행 목록</a>'
             f'<button class="btn" {trip_attrs(r)} onclick="et(this)">여행 정보 수정</button>'
             f'<button class="btn s" onclick="ni({r["id"]})">+ 세부 일정</button>'
             f'<form method="post" action="/trip/{r["id"]}/delete" onsubmit="return confirm(\'삭제할까요? 되돌릴 수 없습니다\')" style="display:inline-block;margin:0"><button class="btn d">삭제</button></form></div>')
    date_card=(f'<div class="trip-edit-card"><div class="label">여행 일자</div>'
               f'<b class="view-value" onclick="this.nextElementSibling.style.display=\'flex\';this.style.display=\'none\'">{H(r["start_date"])} ~ {H(r["end_date"])}</b>'
               f'<form class="inline-edit" method="post" action="/trip/{r["id"]}/quick-edit">'
               f'<input type="date" name="start_date" value="{H(r["start_date"])}">'
               f'<input type="date" name="end_date" value="{H(r["end_date"])}">'
               f'<button class="btn s" type="submit">저장</button></form></div>')
    region_card=(f'<div class="trip-edit-card"><div class="label">지역</div>'
                 f'<b class="view-value" onclick="this.nextElementSibling.style.display=\'flex\';this.style.display=\'none\'">{H(" · ".join(x for x in [r["country"],r["region"]] if x)) or "-"}</b>'
                 f'<form class="inline-edit" method="post" action="/trip/{r["id"]}/quick-edit">'
                 f'<input name="country" placeholder="국가" value="{H(r["country"])}">'
                 f'<input name="region" placeholder="지역" value="{H(r["region"])}">'
                 f'<button class="btn s" type="submit">저장</button></form></div>')
    companions_card=(f'<div class="trip-edit-card"><div class="label">함께</div>'
                      f'<form method="post" action="/trip/{r["id"]}/quick-edit">'
                      f'<select name="companions" class="status-select" onchange="this.form.submit()">{_select_options(COMPANION_OPTIONS,r["companions"])}</select></form></div>')
    lodging_card=(f'<div class="trip-edit-card"><div class="label">숙소</div>'
                  f'<b class="view-value" onclick="this.nextElementSibling.style.display=\'flex\';this.style.display=\'none\'">{H(r["lodging"]) or "-"}</b>'
                  f'<form class="inline-edit" method="post" action="/trip/{r["id"]}/quick-edit">'
                  f'<input name="lodging" value="{H(r["lodging"])}">'
                  f'<button class="btn s" type="submit">저장</button></form></div>')
    transport_card=(f'<div class="trip-edit-card"><div class="label">교통/항공</div>'
                     f'<form method="post" action="/trip/{r["id"]}/quick-edit">'
                     f'<select name="transport" class="status-select" onchange="this.form.submit()">{_select_options(TRANSPORT_OPTIONS,r["transport"])}</select></form></div>')
    status_card=f'<div class="trip-edit-card"><div class="label">상태</div><form method="post" action="/trip/{r["id"]}/status"><select name="status" class="status-select {scls}" onchange="this.form.submit()">{stopts}</select></form></div>'
    cards='<div class="trip-edit-grid">'+date_card+region_card+companions_card+lodging_card+transport_card+status_card+'</div>'
    return actions,cards

def _ensure_trip_days(trip_id,start_date,end_date,status,dq):
    if status=='완료' or dq=='미정': return
    sd=qdate(start_date); ed=qdate(end_date)
    if not sd or not ed or ed<sd: return
    c=db()
    exists=c.execute('select 1 from itinerary where trip_id=? limit 1',(trip_id,)).fetchone()
    if exists: c.close(); return
    d=sd; i=1
    while d<=ed:
        c.execute('insert into itinerary(trip_id,item_date,day_label,time_text,title,place,detail,sort_order) values(?,?,?,?,?,?,?,?)',
                  (trip_id,d.isoformat(),f'{i}일차','','일정 미정','','',i*10))
        d+=timedelta(days=1); i+=1
    c.commit(); c.close()

def _prune_placeholder_days(trip_id):
    c=db()
    c.execute("delete from itinerary where trip_id=? and title='일정 미정' and place='' and detail='' and time_text=''",(trip_id,))
    c.commit(); c.close()

def editable_trip_detail(trip_id):
    c=db(); r=c.execute('select * from trips where id=?',(trip_id,)).fetchone(); c.close()
    if not r: return abort(404)
    dq=date_quality(trip_id)
    if dq=='미정': _prune_placeholder_days(trip_id)
    else: _ensure_trip_days(trip_id,r['start_date'],r['end_date'],r['status'],dq)
    c=db(); its=c.execute('select * from itinerary where trip_id=? order by sort_order,item_date,id',(trip_id,)).fetchall(); c.close()
    opts=''.join(f'<button class="date-q {"on" if dq==x else ""}" name="date_status" value="{x}">{x}</button>' for x in ('확정','대략','미정'))
    panel=f'<div class="date-quality"><div><b>여행 날짜 정확도</b><div class="muted">확정 · 대략 · 미정으로 구분</div></div><form method="post" action="/trip/{trip_id}/date-status" class="date-q-form">{opts}</form></div>'
    actions,cards=_trip_overview(r)
    cards+='<div class="toolbar"><h2 style="margin:0">일자별 일정</h2><button class="btn s" onclick="ni('+str(r['id'])+')">+ 일정 추가</button></div>'
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
@media(max-width:700px){.past-grid{grid-template-columns:1fr}.next-trip-grid{gap:8px}.next-trip-card{padding:10px;min-height:96px}.next-trip-card .name{font-size:14px}.filter-form{grid-template-columns:1fr 1fr}.filter-form .filter-field:first-child{grid-column:1/-1}.stat-grid{grid-template-columns:repeat(2,1fr)}.bar-row{grid-template-columns:90px 1fr 36px}.search-form{flex-direction:column}}
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

def _next_trips_by_type(c, today, trip_type, limit=2):
    return c.execute("select * from trips where start_date>=? and status!='완료' and trip_type=? order by start_date asc,id asc limit ?",(today.isoformat(),trip_type,limit)).fetchall()


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
    flags=_flags_for(r['country'],r['trip_type'])
    return (f'<a class="next-trip-card future-card" href="/trip/{r["id"]}"><div class="kind">{kind}</div>'
            f'<div class="name">{flags} {H(r["title"])}</div>'
            f'<span class="dday">{_dday_label(td,today)}</span>'
            f'<div class="muted" style="margin-top:6px">{H(r["start_date"])} ~ {H(r["end_date"])}</div>'
            f'<div class="muted">{H(region) or "-"}</div></a>')


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
        flags=_flags_for(r['country'], r['trip_type'])
        body+=f'<a class="past-card home-link" href="/trip/{r["id"]}"><div class="date">{H(r["start_date"])} ~ {H(r["end_date"])}</div><b>{flags} {H(r["title"])}</b><div class="meta">{H(region) or "-"}</div><div class="meta">함께: {H(r["companions"]) or "-"}</div></a>'
    body+='</div>'
    return page('과거 여행',body)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/past':
        app.view_functions[rule.endpoint]=past_filtered
        break


def future_filtered():
    c=db(); rows=c.execute("select * from trips where status!='완료' order by start_date asc,id asc").fetchall(); c.close()

    today=date.today()
    body=f'<div class="past-summary"><b>향후 여행 {len(rows)}건</b><button class="btn" onclick="ntrip()">+ 여행 추가</button></div><div class="past-grid">'
    if not rows:
        body+='<div class="home-card muted">등록된 여행이 없습니다.</div>'
    for r in rows:
        region=' · '.join(x for x in [r['country'],r['region']] if x)
        sd=qdate(r['start_date'] or '')
        dday=_dday_label(sd,today) if sd else '-'
        scls=_status_class(r['status'])
        flags=_flags_for(r['country'], r['trip_type'])
        body+=(f'<a class="past-card future-card" href="/trip/{r["id"]}">'
               f'<div class="date">{H(r["start_date"])} ~ {H(r["end_date"])}<span class="dday" style="float:right">{H(dday)}</span></div>'
               f'<b>{flags} {H(r["title"])}</b><div class="meta">{H(region) or "-"}</div>'
               f'<div class="meta">함께: {H(r["companions"]) or "-"}</div>'
               f'<span class="status-badge {scls}">{H(r["status"])}</span>'
               f'</a>')
    body+='</div>'
    return page('향후 여행',body+mods())

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/future':
        app.view_functions[rule.endpoint]=future_filtered
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
    cols={r['name'] for r in c.execute('PRAGMA table_info(home_event_cache)')}
    for col in ('start_time','end_time','uid'):
        if col not in cols:
            c.execute(f'ALTER TABLE home_event_cache ADD COLUMN {col} TEXT')
    c.execute('''CREATE TABLE IF NOT EXISTS hidden_calendar_events(
      event_key TEXT PRIMARY KEY,
      hidden_at TEXT NOT NULL
    )''')
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
            google_rows.append((sd,ed,str(e.get('title') or ''),str(e.get('category') or ''),str(e.get('person') or ''),str(e.get('notes') or ''),'google',str(e.get('start_time') or ''),str(e.get('end_time') or ''),str(e.get('id') or '')))

        # Keep the last good snapshot if Google is temporarily unavailable.
        has_sources=bool(_sources())
        if has_sources and not google_rows:
            return

        now=datetime.now().isoformat(timespec='seconds')
        c=db()
        c.execute('delete from home_event_cache')
        if google_rows:
            c.executemany('insert into home_event_cache(start_date,end_date,title,category,person,notes,source,start_time,end_time,uid,synced_at) values(?,?,?,?,?,?,?,?,?,?,?)',[r+(now,) for r in google_rows])
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
        'select start_date,end_date,title,category,person,notes,source,start_time,end_time,uid from home_event_cache where start_date<=? and end_date>=? order by start_date,id',
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    trips=[dict(x) for x in c.execute(
        "select id,start_date,end_date,title,region,companions from trips where start_date<=? and end_date>=? order by start_date,id",
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    hidden={r['event_key'] for r in c.execute('select event_key from hidden_calendar_events').fetchall()}
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
    out=[e for e in out if _event_key(e) not in hidden]
    out.sort(key=lambda x:(str(x.get('start_date') or ''),str(x.get('title') or '')))
    return out

def _event_key(dd):
    source=dd.get('source') or 'local'
    if source=='trip':
        return f"trip:{dd.get('trip_id')}"
    if source=='google':
        return f"google:{dd.get('uid') or ''}"
    return f"local:{dd.get('id')}"

@app.route('/calendar-event/hide', methods=['POST'])
def hide_calendar_event():
    key=(request.form.get('key') or '').strip()
    if not key: return abort(400)
    c=db(); c.execute('insert or ignore into hidden_calendar_events(event_key,hidden_at) values(?,?)',(key,datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return redirect(request.referrer or '/calendar')


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
PWA_ICON = '/pwa-icon-v3.svg'

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

# Vivid travel mark: indigo-to-cyan gradient tile + a paper-plane in flight.
# The important artwork stays inside the maskable safe area so Android/Samsung launchers
# can crop it to circles, squircles or rounded squares without losing details.
_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs>
  <linearGradient id="bg" x1="60" y1="40" x2="452" y2="472" gradientUnits="userSpaceOnUse">
    <stop stop-color="#4F46E5"/>
    <stop offset="1" stop-color="#06B6D4"/>
  </linearGradient>
</defs>
<rect width="512" height="512" rx="120" fill="url(#bg)"/>
<circle cx="256" cy="256" r="200" fill="#FFFFFF" opacity=".07"/>
<circle cx="94" cy="392" r="8" fill="#FFFFFF" opacity=".4"/>
<circle cx="124" cy="360" r="10" fill="#FFFFFF" opacity=".55"/>
<circle cx="158" cy="330" r="12" fill="#FFFFFF" opacity=".72"/>
<path d="M109 382L403 256L109 130L109 228L319 256L109 284Z" fill="#FFFFFF"/>
<path d="M109 228L319 256L109 284Z" fill="#C7D9FF"/>
<circle cx="392" cy="128" r="9" fill="#FFD166"/>
</svg>'''

_SW = '''const CACHE='family-pwa-v2';
const SHELL=['/manifest.webmanifest','/pwa-icon-v3.svg'];
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
  if(url.pathname==='/manifest.webmanifest'||url.pathname==='/pwa-icon-v3.svg'){
    event.respondWith(fetch(event.request).then(resp=>{const copy=resp.clone();caches.open(CACHE).then(c=>c.put(event.request,copy));return resp;}).catch(()=>caches.match(event.request)));
  }
});'''

@app.route('/manifest.webmanifest')
def pwa_manifest():
    return Response(json.dumps(_manifest, ensure_ascii=False), mimetype='application/manifest+json', headers={'Cache-Control':'no-cache'})

@app.route('/pwa-icon-v3.svg')
def pwa_icon_v3():
    return Response(_ICON_SVG, mimetype='image/svg+xml', headers={'Cache-Control':'public, max-age=86400'})

# Keep old routes alive (serving the same updated artwork) so previously installed versions do not break.
@app.route('/pwa-icon-v2.svg')
def pwa_icon_v2():
    return Response(_ICON_SVG, mimetype='image/svg+xml', headers={'Cache-Control':'no-cache'})
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
.lesson-toggle{position:relative;display:block;width:100%;text-align:left;background:#eaf3fb;border:0;border-radius:9px;padding:8px 62px 8px 8px;font:inherit;font-size:12px;cursor:pointer;color:inherit;margin-bottom:7px}.lesson-toggle:active{transform:scale(.985)}.lesson-toggle.done{background:#eef2f5}.lesson-toggle b{display:block;margin-bottom:3px}.wb-checkmark{position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:10px;font-weight:800;color:#2f7a50}.lesson-toggle:not(.done) .wb-checkmark{display:none}
.btn.on{background:#0f4c81;color:#fff;border-color:#0f4c81}
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


# Inject the new family dashboard below the existing fast home and a trip-planner
# button on every trip detail page without replacing the existing route handlers.
@app.after_request
def family_feature_injection(response):
    try:
        if request.method!='GET' or response.status_code!=200 or 'text/html' not in (response.content_type or ''):
            return response
        html=response.get_data(as_text=True)
        if request.path.startswith('/trip/') and request.path.count('/')==2:
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
            '<a href="/riley">지유 포탈</a>'
            '<a href="/hyeon">혜온 포탈</a>'
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
_SW += '''\nself.addEventListener('push',event=>{let data={};try{data=event.data?event.data.json():{};}catch(e){data={body:event.data?event.data.text():''};}const title=data.title||'우리 가족 기록';const options={body:data.body||'',icon:'/pwa-icon-v3.svg',badge:'/pwa-icon-v3.svg',data:{url:data.url||'/'}};event.waitUntil(self.registration.showNotification(title,options));});self.addEventListener('notificationclick',event=>{event.notification.close();const url=(event.notification.data&&event.notification.data.url)||'/';event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list=>{for(const c of list){if('focus'in c){c.navigate(url);return c.focus();}}return clients.openWindow(url);}));});'''


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
    domestic = _next_trips_by_type(c, today, '국내')
    overseas = _next_trips_by_type(c, today, '해외')
    c.close()
    family_events = _upcoming_events(today)

    def _card_at(rows, label, i):
        title = f'다음 {label}' if i == 0 else f'그 다음 {label}'
        return _trip_card(rows[i] if i < len(rows) else None, today, title)

    body = ('<div class="next-trip-grid">'
            + _card_at(domestic, '국내 여행', 0) + _card_at(domestic, '국내 여행', 1)
            + _card_at(overseas, '해외 여행', 0) + _card_at(overseas, '해외 여행', 1)
            + '</div>')
    body += '<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-family-list">'
    if not family_events:
        body += '<div class="muted" style="padding:10px 0">등록된 가족 일정이 없습니다.</div>'
    for d, e in family_events:
        kind, label = _event_kind(e)
        end = str(e.get('end_date') or '')[:10]
        date_text = d.isoformat() if not end or end == d.isoformat() else f'{d.isoformat()} ~ {end}'
        start_time=(e.get('start_time') or '').strip()
        end_time=(e.get('end_time') or '').strip()
        if start_time:
            date_text += f' {start_time}'+(f'~{end_time}' if end_time and end_time!=start_time else '')
        dday = _dday_label(d, today)
        today_cls = ' today' if dday == 'D-DAY' else ''
        title = _clean_title(e.get('title'))
        body += (f'<div class="home-family-row" style="cursor:pointer" {_event_detail_attrs(e,label)} onclick="showEventDetail(this)">'
                 f'<span class="event-dot {kind}" title="{H(label)}"></span>'
                 f'<div class="event-main"><div class="event-title">{H(title)}</div>'
                 f'<div class="event-meta">{H(label)} · {H(date_text)}</div></div>'
                 f'<span class="event-dday{today_cls}">{H(dday)}</span></div>')
    body += '</div></section>'
    body += _tasks_card()
    body += event_detail_modal()
    return page('우리 가족 기록', body)


# home_cleanup_app's before_request calls this module-level function dynamically,
# so replacing it removes the added today/weekly schedule panels while keeping tasks.
clean_family_home = tasks_only_home

for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/':
        app.view_functions[rule.endpoint] = tasks_only_home

# ===================== from trip_day_cards_app.py =====================
CSS += '''
.trip-day-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}
.trip-day-card{width:100%;text-align:left;background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:13px;cursor:pointer;color:#14263f;font:inherit;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease}
.trip-day-card:hover{transform:translateY(-1px);box-shadow:0 5px 16px #10203012;border-color:#b9c9d9}
.trip-day-top{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:9px}.trip-day-date{font-weight:800}.trip-day-label{font-size:11px;color:#718096;background:#eef3f8;border-radius:999px;padding:4px 7px;white-space:nowrap}
.trip-day-city{font-size:17px;font-weight:800;margin-bottom:6px}.trip-day-hotel{font-size:12px;color:#596b80;margin-bottom:7px}.trip-day-summary{font-size:13px;color:#44566d;line-height:1.45}.trip-day-edit-hint{font-size:11px;color:#8a98a9;margin-top:9px}
.trip-overview{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-bottom:14px}.trip-overview .dashcard{margin:0}.trip-actions{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 12px}
@media(max-width:760px){.trip-day-grid{grid-template-columns:1fr}.trip-overview{grid-template-columns:1fr 1fr}}
@media(max-width:440px){.trip-overview{grid-template-columns:1fr}}
'''

JS += '''
function editTripDay(el){
 const d=el.dataset;
 const f=document.getElementById('tdf');
 f.action='/trip-day/'+d.id+'/edit';
 document.getElementById('td-date').value=d.date||'';
 document.getElementById('td-day-label').value=d.day_label||'';
 document.getElementById('td-city').value=d.city||'';
 document.getElementById('td-hotel').value=d.hotel||'';
 document.getElementById('td-summary').value=d.summary||'';
 o('tdm');
}
'''

_TRIP_DAY_MARKER = '[2027계획동기화]'
_TRIP_DAY_TARGET_STARTS = {'2027-01-02', '2027-08-07'}


def _trip_day_clean_detail(value):
    s = str(value or '')
    return s[len(_TRIP_DAY_MARKER):].strip() if s.startswith(_TRIP_DAY_MARKER) else s.strip()


def _trip_day_target(row):
    return bool(row and (row['start_date'] in _TRIP_DAY_TARGET_STARTS or ('2027' in str(row['start_date'] or '') and any(k in str(row['title'] or '') for k in ('이탈리아', '싱가포르')))))


def _trip_day_attrs(row):
    return ('data-id="%s" data-date="%s" data-day_label="%s" data-city="%s" data-hotel="%s" data-summary="%s"' % (
        H(row['id']), H(row['item_date']), H(row['day_label']), H(row['title']), H(row['place']), H(_trip_day_clean_detail(row['detail']))
    ))


_trip_day_previous_view = None
for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/trip/<int:trip_id>':
        _trip_day_previous_view = app.view_functions[rule.endpoint]
        break


def trip_day_detail(trip_id):
    c = db()
    trip = c.execute('select * from trips where id=?', (trip_id,)).fetchone()
    days = c.execute("select * from itinerary where trip_id=? and item_date is not null and item_date<>'' order by item_date,sort_order,id", (trip_id,)).fetchall()
    c.close()
    if not trip:
        return abort(404)
    if not _trip_day_target(trip):
        return _trip_day_previous_view(trip_id)

    actions,cards=_trip_overview(trip)

    body = actions + cards + '<h2 class="sectiontitle">날짜별 일정</h2><div class="muted">날짜 카드를 누르면 도시·호텔·주요 방문지를 바로 수정할 수 있습니다.</div><div class="trip-day-grid">'
    if not days:
        body += '<div class="dashcard muted">날짜별 일정이 없습니다.</div>'
    for r in days:
        summary = _trip_day_clean_detail(r['detail'])
        hotel = r['place'] or '-'
        body += (f'<button type="button" class="trip-day-card" {_trip_day_attrs(r)} onclick="editTripDay(this)">'
                 f'<div class="trip-day-top"><span class="trip-day-date">{H(r["item_date"])}</span><span class="trip-day-label">{H(r["day_label"] or "")}</span></div>'
                 f'<div class="trip-day-city">{H(r["title"] or "미정")}</div>'
                 f'<div class="trip-day-hotel">호텔 · {H(hotel)}</div>'
                 f'<div class="trip-day-summary">{H(summary) or "세부 일정 미정"}</div>'
                 f'<div class="trip-day-edit-hint">눌러서 수정</div></button>')
    body += '</div>'
    body += f'<h2 class="sectiontitle" style="margin-top:20px">메모</h2><div class="dashcard">{H(trip["notes"]) or "-"}</div>'
    body += '''
<div class="modal" id="tdm"><div class="card"><div class="head"><h2>날짜 일정 수정</h2><button class="btn s" type="button" onclick="x('tdm')">닫기</button></div>
<form id="tdf" method="post" class="form">
<label>날짜<input id="td-date" type="date" name="item_date" required></label>
<label>일차<input id="td-day-label" name="day_label" placeholder="예: 3일차"></label>
<label>도시<input id="td-city" name="title" required placeholder="예: 로마"></label>
<label>호텔<input id="td-hotel" name="place" placeholder="예: Hotel Artemide"></label>
<label class="full">간략 내용 · 주요 방문지<textarea id="td-summary" name="detail" placeholder="예: 바티칸 박물관 · 시스티나 성당"></textarea></label>
<div class="full" style="display:flex;justify-content:flex-end;gap:7px"><button class="btn s" type="button" onclick="x('tdm')">취소</button><button class="btn" type="submit">저장</button></div>
</form></div></div>'''
    return page(trip['title'], body)


if _trip_day_previous_view:
    for rule in list(app.url_map.iter_rules()):
        if rule.rule == '/trip/<int:trip_id>':
            app.view_functions[rule.endpoint] = trip_day_detail


@app.route('/trip-day/<int:item_id>/edit', methods=['POST'])
def trip_day_edit(item_id):
    c = db()
    row = c.execute('select * from itinerary where id=?', (item_id,)).fetchone()
    if not row:
        c.close(); return abort(404)
    f = request.form
    item_date = (f.get('item_date') or row['item_date'] or '').strip()
    day_label = (f.get('day_label') or '').strip()
    title = (f.get('title') or '').strip()
    place = (f.get('place') or '').strip()
    detail = (f.get('detail') or '').strip()
    c.execute('update itinerary set item_date=?,day_label=?,title=?,place=?,detail=? where id=?',
              (item_date, day_label, title, place, detail, item_id))
    trip_id = row['trip_id']
    c.commit(); c.close()
    return redirect(f'/trip/{trip_id}')

if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','8080')))

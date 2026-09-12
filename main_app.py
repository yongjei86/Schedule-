import os
import json
import time
import threading
import sqlite3
import calendar as pycal
from datetime import datetime, date, timedelta, time as dtime
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar
import recurring_ical_events

import family_ui_wrapper as family_ui
import enhancements_wrapper as enhancements
import gcal_wrapper as gcal
import app as base

app = family_ui.app
KST = ZoneInfo('Asia/Seoul')
DB_PATH = base.DB_PATH
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

base.nav = final_nav
base.CSS += '''
.trip-actions{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}.trip-edit-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.trip-edit-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px}.trip-edit-card .label{font-size:11px;color:#748196;margin-bottom:4px}.itinerary-row{display:grid;grid-template-columns:120px 1fr auto;gap:10px;align-items:start;background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px;margin:8px 0}.itinerary-actions{display:flex;gap:5px;flex-wrap:wrap}.nav a{font-weight:650}.calendar-scroll{border-radius:14px}.family-month{min-width:700px}.date-quality{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:11px 12px;margin-bottom:12px}.date-q-form{display:flex;gap:5px}.date-q{border:1px solid #d5dde7;background:#fff;color:#65758b;border-radius:8px;padding:7px 10px;font:inherit;font-size:12px;cursor:pointer}.date-q.on{background:#0f4c81;color:#fff;border-color:#0f4c81;font-weight:800}.status-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}.status-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px;display:grid;gap:7px}
@media(max-width:700px){nav{padding:9px 10px;align-items:center}.nav{max-width:74vw;gap:2px}.nav a{font-size:12px;padding:7px 8px}.wrap{padding:12px 10px 40px}.hero{padding:15px;border-radius:14px;margin-bottom:12px}.hero h1{font-size:22px}.toolbar,.cal-toolbar,.riley-toolbar{gap:6px}.btn,.nav a{min-height:34px}.trip-edit-grid{grid-template-columns:1fr 1fr}.itinerary-row{grid-template-columns:95px 1fr}.itinerary-actions{grid-column:1/-1}.box{border-radius:12px;-webkit-overflow-scrolling:touch}.box table{min-width:760px}th,td{padding:8px;font-size:12px}.family-month{min-width:660px}.fm-cell{min-height:88px}.riley-week{grid-template-columns:repeat(7,minmax(138px,1fr))}.rday{min-width:138px;padding:8px}.rlesson{padding:7px}.card{padding:13px;margin:2vh auto}.form{gap:8px}.date-quality{align-items:flex-start;flex-direction:column}.date-q-form{width:100%}.date-q{flex:1}.status-grid{grid-template-columns:1fr}}
@media(max-width:430px){.trip-edit-grid{grid-template-columns:1fr}.nav{max-width:70vw}.family-month{min-width:620px}.box table{min-width:720px}}
'''


# ===== Riley recurring Google schedule =====
def recurring_riley_events(start, end, name='지유'):
    out = []
    sources = [s for s in gcal._sources() if s.get('name') == name]
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

enhancements._timed_google = recurring_riley_events


# ===== family calendar: calendar only, Riley academy recurring events excluded =====
def family_events(start, end):
    events = list(base.event_rows(start, end))
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
    view = (base.request.args.get('view') or 'month').lower()
    q = base.qdate(base.request.args.get('date','')) or date.today()
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
            d=start+timedelta(days=i); de=[e for e in events if family_ui._overlaps(e,d)]
            cal+=f'<div class="week-card {"today" if d==today else ""}"><div class="week-date">{d.strftime("%m/%d")}</div><h3>{base.DAYS[i]}</h3>'
            if not de: cal+='<div class="muted">일정 없음</div>'
            for e in de:
                dd=dict(e); k=family_ui._kind(dd)
                cal+=f'<div class="event-chip {family_ui._kind_class(k)}"><b>{base.H(dd.get("title"))}</b><div class="muted">{base.H(k)}</div></div>'
            cal+='</div>'
        cal+='</div>'
    else:
        cal='<div class="calendar-scroll"><div class="family-month">'+''.join(f'<div class="fm-head">{x}</div>' for x in ['월','화','수','목','금','토','일'])
        grid_start=start-timedelta(days=start.weekday())
        for i in range(42):
            d=grid_start+timedelta(days=i); de=[e for e in events if family_ui._overlaps(e,d)]
            cal+=f'<div class="fm-cell {"out" if d.month!=q.month else ""}"><span class="fm-num {"today" if d==today else ""}">{d.day}</span>'
            for e in de[:5]:
                dd=dict(e); k=family_ui._kind(dd)
                cal+=f'<div class="fm-event {family_ui._kind_class(k)}" title="{base.H(dd.get("title"))}">{base.H(dd.get("title"))}</div>'
            if len(de)>5: cal+=f'<div class="muted">+{len(de)-5}개</div>'
            cal+='</div>'
        cal+='</div></div>'
    return base.page('가족 달력', toolbar+cal)

for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/calendar':
        app.view_functions[rule.endpoint] = family_calendar
        break


# ===== safety schema / backups / change history =====
def init_safety_schema():
    c=base.db(); c.executescript('''CREATE TABLE IF NOT EXISTS change_log(id INTEGER PRIMARY KEY,created_at TEXT NOT NULL,entity_type TEXT NOT NULL,entity_id INTEGER,action TEXT NOT NULL,before_json TEXT,after_json TEXT,restored_from INTEGER);CREATE TABLE IF NOT EXISTS trip_date_quality(trip_id INTEGER PRIMARY KEY,date_status TEXT NOT NULL DEFAULT '확정',updated_at TEXT NOT NULL);''')
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
    c=base.db(); sql=f'select * from {table} where id=?' if table!='trip_date_quality' else 'select * from trip_date_quality where trip_id=?'; row=c.execute(sql,(entity_id,)).fetchone(); snap={'row':dict(row) if row else None}
    if include_related and table=='trips' and row: snap['itinerary']=[dict(x) for x in c.execute('select * from itinerary where trip_id=? order by id',(entity_id,)).fetchall()]
    c.close(); return snap


def max_id(table):
    if table not in ALLOWED_TABLES or table=='trip_date_quality': return None
    c=base.db(); r=c.execute(f'select max(id) m from {table}').fetchone(); c.close(); return r['m'] if r else None


def log_change(table,entity_id,action,before,after,restored_from=None):
    c=base.db(); c.execute('insert into change_log(created_at,entity_type,entity_id,action,before_json,after_json,restored_from) values(?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),table,entity_id,action,json.dumps(before,ensure_ascii=False,default=str) if before is not None else None,json.dumps(after,ensure_ascii=False,default=str) if after is not None else None,restored_from)); c.commit(); c.close()


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
    c=base.db(); rows=c.execute('select * from change_log order by id desc limit 100').fetchall(); c.close(); labels={'trips':'여행','itinerary':'세부 일정','calendar_events':'가족 일정','academy':'지유 일정','trip_date_quality':'날짜 정확도'}; actions={'add':'추가','edit':'수정','delete':'삭제','restore':'복구'}
    body='<div class="toolbar"><b>최근 변경 100건</b><a class="btn s" href="/system-status">시스템 상태</a></div><div class="box"><table style="min-width:720px"><tr><th>시간</th><th>대상</th><th>작업</th><th>ID</th><th>복구</th></tr>'
    for r in rows:
        can=r['action'] in ('add','edit','delete') and (r['before_json'] or r['after_json']); restore=f'<form method="post" action="/change/{r["id"]}/restore" onsubmit="return confirm(\'이 변경 직전 상태로 복구할까요?\')"><button class="btn s">복구</button></form>' if can else '-'
        body+=f'<tr><td>{base.H(r["created_at"].replace("T"," "))}</td><td>{base.H(labels.get(r["entity_type"],r["entity_type"]))}</td><td>{base.H(actions.get(r["action"],r["action"]))}</td><td>{base.H(r["entity_id"])}</td><td>{restore}</td></tr>'
    return base.page('변경 이력',body+'</table></div>')

@app.route('/change/<int:log_id>/restore',methods=['POST'])
def restore_change(log_id):
    c=base.db(); r=c.execute('select * from change_log where id=?',(log_id,)).fetchone()
    if not r or r['entity_type'] not in ALLOWED_TABLES: c.close(); return base.abort(404)
    table,entity_id,action=r['entity_type'],r['entity_id'],r['action']; before=json.loads(r['before_json']) if r['before_json'] else None; current=row_snapshot(table,entity_id,include_related=(table=='trips')); backup_db('prechange')
    if action=='add': c.execute(f'delete from {table} where {"trip_id" if table=="trip_date_quality" else "id"}=?',(entity_id,))
    elif before and before.get('row'):
        upsert_row(c,table,before['row'])
        if table=='trips' and before.get('itinerary') is not None:
            c.execute('delete from itinerary where trip_id=?',(entity_id,))
            for x in before.get('itinerary',[]): upsert_row(c,'itinerary',x)
    c.commit(); c.close(); after=row_snapshot(table,entity_id,include_related=(table=='trips')); log_change(table,entity_id,'restore',current,after,restored_from=log_id); return base.redirect('/changes')


def date_quality(trip_id):
    c=base.db(); r=c.execute('select date_status from trip_date_quality where trip_id=?',(trip_id,)).fetchone(); c.close(); return r['date_status'] if r else '확정'

@app.route('/trip/<int:trip_id>/date-status',methods=['POST'])
def set_trip_date_status(trip_id):
    status=(base.request.form.get('date_status') or '').strip()
    if status not in ('확정','대략','미정'): return base.abort(400)
    before=row_snapshot('trip_date_quality',trip_id); backup_db('prechange'); c=base.db(); c.execute('insert into trip_date_quality(trip_id,date_status,updated_at) values(?,?,?) on conflict(trip_id) do update set date_status=excluded.date_status,updated_at=excluded.updated_at',(trip_id,status,datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close(); after=row_snapshot('trip_date_quality',trip_id); log_change('trip_date_quality',trip_id,'edit',before,after); return base.redirect(base.request.referrer or f'/trip/{trip_id}')


# ===== editable trip detail =====
def trip_attrs(r):
    keys=['id','start_date','end_date','country','region','title','companions','trip_type','status','lodging','transport','notes']; return ' '.join('data-'+k+'="'+base.H(r[k])+'"' for k in keys)
def itinerary_attrs(x):
    keys=['id','trip_id','item_date','day_label','time_text','title','place','detail','sort_order']; return ' '.join('data-'+k+'="'+base.H(x[k])+'"' for k in keys)

def editable_trip_detail(trip_id):
    c=base.db(); r=c.execute('select * from trips where id=?',(trip_id,)).fetchone(); its=c.execute('select * from itinerary where trip_id=? order by sort_order,item_date,id',(trip_id,)).fetchall(); c.close()
    if not r: return base.abort(404)
    dq=date_quality(trip_id); opts=''.join(f'<button class="date-q {"on" if dq==x else ""}" name="date_status" value="{x}">{x}</button>' for x in ('확정','대략','미정'))
    panel=f'<div class="date-quality"><div><b>여행 날짜 정확도</b><div class="muted">확정 · 대략 · 미정으로 구분</div></div><form method="post" action="/trip/{trip_id}/date-status" class="date-q-form">{opts}</form></div>'
    back='/past' if r['status']=='완료' else '/future'; actions=f'<div class="trip-actions"><a class="btn s" href="{back}">← 여행 목록</a><button class="btn" {trip_attrs(r)} onclick="et(this)">여행 정보 수정</button><button class="btn s" onclick="ni({r["id"]})">+ 세부 일정</button></div>'
    cards='<div class="trip-edit-grid">'
    for label,value in [('여행 일자',f'{r["start_date"]} ~ {r["end_date"]}'),('지역',' · '.join(x for x in [r['country'],r['region']] if x)),('함께',r['companions']),('숙소',r['lodging']),('교통/항공',r['transport']),('상태',r['status'])]: cards+=f'<div class="trip-edit-card"><div class="label">{base.H(label)}</div><b>{base.H(value) or "-"}</b></div>'
    cards+='</div><div class="toolbar"><h2 style="margin:0">일자별 일정</h2><button class="btn s" onclick="ni('+str(r['id'])+')">+ 일정 추가</button></div>'
    if not its: cards+='<div class="trip-edit-card muted">아직 세부 일정이 없습니다.</div>'
    for x in its:
        left=' · '.join(v for v in [x['item_date'],x['day_label'],x['time_text']] if v) or '-'; cards+=f'<div class="itinerary-row"><div><b>{base.H(left)}</b></div><div><b>{base.H(x["title"])}</b>'+ (f'<br>{base.H(x["place"])}' if x['place'] else '') + (f'<br><span class="muted">{base.H(x["detail"])}</span>' if x['detail'] else '') + f'</div><div class="itinerary-actions"><button class="btn s" {itinerary_attrs(x)} onclick="ei(this)">수정</button><form method="post" action="/itinerary/{x["id"]}/delete" style="display:inline" onsubmit="return confirm(\'삭제할까요?\')"><button class="btn d">삭제</button></form></div></div>'
    notes=f'<h2 style="margin-top:20px">메모</h2><div class="trip-edit-card">{base.H(r["notes"]) or "-"}</div>'
    if r['start_date']=='2026-08-08' and '발리' in (r['title'] or ''): notes+='<div style="margin-top:10px"><a class="btn" href="/photos/bali-2026">📷 발리 사진</a></div>'
    return base.page(r['title'],panel+actions+cards+notes+base.mods())

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/trip/<int:trip_id>': app.view_functions[rule.endpoint]=editable_trip_detail; break


# ===== Google Calendar health =====
def check_source(src):
    name=src.get('name') or '이름 없음'
    try:
        r=requests.get(src['url'],timeout=8,headers={'User-Agent':'YJ-Family-Calendar/1.0'}); r.raise_for_status(); cal=Calendar.from_ical(r.content); events=list(cal.walk('VEVENT')); recurring=sum(1 for e in events if e.get('RRULE')); return {'name':name,'ok':True,'events':len(events),'recurring':recurring,'error':''}
    except Exception as e: return {'name':name,'ok':False,'events':0,'recurring':0,'error':type(e).__name__}

def run_sync_check():
    sources=gcal._sources(); results=[]
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
    state=run_sync_check() if base.request.args.get('refresh')=='1' or not SYNC_STATE.get('checked_at') else dict(SYNC_STATE)
    try: files=sorted([x for x in os.listdir(BACKUP_DIR) if x.endswith('.db')],reverse=True)
    except OSError: files=[]
    daily=[x for x in files if x.startswith('daily_')]; pre=[x for x in files if x.startswith('prechange_')]
    body=f'<div class="status-grid"><div class="status-card"><b>DB 자동 백업</b><div>매일 백업 {len(daily)}개 · 변경 전 백업 {len(pre)}개</div><div class="muted">일일 30개, 변경 전 20개 보관</div></div><div class="status-card"><b>변경 이력/복구</b><div><a class="btn s" href="/changes">최근 변경 보기</a></div></div><div class="status-card"><b>지유 학원 분리</b><div>가족 달력에서 반복 학원 일정 제외 활성</div></div></div><div class="toolbar"><b>Google Calendar 연결 점검</b><a class="btn s" href="/system-status?refresh=1">다시 점검</a></div><div class="box"><table style="min-width:620px"><tr><th>캘린더</th><th>상태</th><th>전체 일정</th><th>반복 일정</th></tr>'
    for x in state.get('sources',[]): body+=f'<tr><td>{base.H(x["name"])}</td><td>{"정상" if x["ok"] else "오류"}</td><td>{x["events"]}</td><td>{x["recurring"]}</td></tr>'
    body+=f'</table></div><div class="muted" style="margin-top:8px">마지막 점검: {base.H((state.get("checked_at") or "-").replace("T"," "))}</div>'; return base.page('시스템 상태',body)

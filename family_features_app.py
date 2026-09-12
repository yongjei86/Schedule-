from datetime import date, datetime, timedelta

from flask import redirect

import pwa_app as pwa
import home_cleanup_app as home
import app as base

app = pwa.app


# ===== schema =====
def init_family_features_schema():
    c = base.db()
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
base.CSS += '''
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

base.nav = family_nav

try:
    pwa._manifest['shortcuts'].append({'name':'가족 할 일','short_name':'할 일','url':'/tasks'})
except Exception:
    pass


# ===== family tasks =====
def _task_rows(include_done=True, limit=None):
    c=base.db()
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
        body+=(f'<div class="feature-row"><div><b class="{cls}">{base.H(r["title"])}</b>'
               f'<div class="feature-meta">{base.H(_task_label(r))}</div></div><div class="task-actions">'
               f'<form method="post" action="/tasks/{r["id"]}/toggle"><button class="btn s">{"되돌리기" if r["done"] else "완료"}</button></form>'
               f'<form method="post" action="/tasks/{r["id"]}/delete"><button class="btn d">삭제</button></form></div></div>')
    body+='</div></section>'
    return base.page('가족 할 일',body)


@app.route('/tasks/add',methods=['POST'])
def family_tasks_add():
    f=base.request.form
    title=(f.get('title') or '').strip()
    if title:
        c=base.db(); c.execute('insert into family_tasks(title,due_date,assignee,category,notes,created_at) values(?,?,?,?,?,?)',(
            title,(f.get('due_date') or '').strip(),(f.get('assignee') or '가족').strip(),(f.get('category') or '가족').strip(),(f.get('notes') or '').strip(),datetime.now().isoformat(timespec='seconds')))
        c.commit(); c.close()
    return redirect('/tasks')


@app.route('/tasks/<int:i>/toggle',methods=['POST'])
def family_tasks_toggle(i):
    c=base.db(); c.execute('update family_tasks set done=case when done=1 then 0 else 1 end where id=?',(i,)); c.commit(); c.close()
    return redirect(base.request.referrer or '/tasks')


@app.route('/tasks/<int:i>/delete',methods=['POST'])
def family_tasks_delete(i):
    c=base.db(); c.execute('delete from family_tasks where id=?',(i,)); c.commit(); c.close()
    return redirect(base.request.referrer or '/tasks')


# ===== trip planner =====
def _trip(trip_id):
    c=base.db(); r=c.execute('select * from trips where id=?',(trip_id,)).fetchone(); c.close()
    return dict(r) if r else None


def _trip_plan_data(trip_id):
    c=base.db()
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
    start=base.qdate(trip.get('start_date') or '')
    dday=(start-date.today()).days if start else None
    dtext='-' if dday is None else ('D-DAY' if dday==0 else (f'D-{dday}' if dday>0 else f'D+{abs(dday)}'))
    body=(f'<div class="trip-actions"><a class="btn s" href="/trip/{trip_id}">← 여행 상세</a></div>'
          f'<div class="plan-summary"><div class="plan-stat"><span class="muted">출발</span><b>{base.H(dtext)}</b></div>'
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
        link=(f' · <a href="{base.H(r["link"])}" target="_blank">링크</a>' if r.get('link') else '')
        body+=(f'<div class="plan-row"><div><b class="{cls}">{base.H(r["title"])}</b><div class="feature-meta">{base.H(meta)}{link}</div></div><div class="task-actions">'
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
        body+=(f'<div class="plan-row"><div><b class="{cls}">{base.H(r["title"])}</b><div class="feature-meta">{base.H(meta)}</div></div><div class="task-actions">'
               f'<form method="post" action="/trip/{trip_id}/plan/check/{r["id"]}/toggle"><button class="btn s">{"되돌리기" if r["done"] else "완료"}</button></form>'
               f'<form method="post" action="/trip/{trip_id}/plan/check/{r["id"]}/delete"><button class="btn d">삭제</button></form></div></div>')
    body+='</div></section>'

    body+=('<section class="plan-section"><h2>여행 비용</h2><form class="plan-form" method="post" action="/trip/%d/plan/expense/add">'
           '<label>분류<select name="category"><option>항공</option><option>숙박</option><option>교통</option><option>식사</option><option>체험</option><option>쇼핑</option><option>기타</option></select></label>'
           '<label class="wide">항목<input name="title" required></label><label>금액<input type="number" step="0.01" name="amount" required></label><label>통화<input name="currency" value="KRW"></label><label>결제자<input name="paid_by"></label><button class="btn">추가</button></form><div class="feature-list">') % trip_id
    if not expenses: body+='<div class="muted">등록된 비용이 없습니다.</div>'
    for r in expenses:
        body+=(f'<div class="plan-row"><div><b>{base.H(r["title"])}</b><div class="feature-meta">{base.H(r["category"])} · {base.H(r["amount"])} {base.H(r["currency"])} · {base.H(r.get("paid_by") or "-")}</div></div>'
               f'<form method="post" action="/trip/{trip_id}/plan/expense/{r["id"]}/delete"><button class="btn d">삭제</button></form></div>')
    body+='</div></section>'
    return base.page(f'{trip.get("title") or "여행"} 준비',body)


@app.route('/trip/<int:trip_id>/plan/reservation/add',methods=['POST'])
def trip_reservation_add(trip_id):
    f=base.request.form; title=(f.get('title') or '').strip()
    if title:
        c=base.db(); c.execute('insert into trip_reservations(trip_id,kind,title,reservation_date,confirmation,link,notes,created_at) values(?,?,?,?,?,?,?,?)',(
            trip_id,(f.get('kind') or '기타').strip(),title,(f.get('reservation_date') or '').strip(),(f.get('confirmation') or '').strip(),(f.get('link') or '').strip(),(f.get('notes') or '').strip(),datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/reservation/<int:i>/toggle',methods=['POST'])
def trip_reservation_toggle(trip_id,i):
    c=base.db(); c.execute('update trip_reservations set done=case when done=1 then 0 else 1 end where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/reservation/<int:i>/delete',methods=['POST'])
def trip_reservation_delete(trip_id,i):
    c=base.db(); c.execute('delete from trip_reservations where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/check/add',methods=['POST'])
def trip_check_add(trip_id):
    f=base.request.form; title=(f.get('title') or '').strip()
    if title:
        c=base.db(); c.execute('insert into trip_checklist(trip_id,title,category,assignee,due_date,created_at) values(?,?,?,?,?,?)',(
            trip_id,title,(f.get('category') or '준비').strip(),(f.get('assignee') or '가족').strip(),(f.get('due_date') or '').strip(),datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/check/<int:i>/toggle',methods=['POST'])
def trip_check_toggle(trip_id,i):
    c=base.db(); c.execute('update trip_checklist set done=case when done=1 then 0 else 1 end where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/check/<int:i>/delete',methods=['POST'])
def trip_check_delete(trip_id,i):
    c=base.db(); c.execute('delete from trip_checklist where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/expense/add',methods=['POST'])
def trip_expense_add(trip_id):
    f=base.request.form; title=(f.get('title') or '').strip()
    if title:
        try: amount=float(f.get('amount') or 0)
        except: amount=0
        c=base.db(); c.execute('insert into trip_expenses(trip_id,category,title,amount,currency,paid_by,notes,created_at) values(?,?,?,?,?,?,?,?)',(
            trip_id,(f.get('category') or '기타').strip(),title,amount,(f.get('currency') or 'KRW').strip().upper(),(f.get('paid_by') or '').strip(),(f.get('notes') or '').strip(),datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return redirect(f'/trip/{trip_id}/plan')


@app.route('/trip/<int:trip_id>/plan/expense/<int:i>/delete',methods=['POST'])
def trip_expense_delete(trip_id,i):
    c=base.db(); c.execute('delete from trip_expenses where id=? and trip_id=?',(i,trip_id)); c.commit(); c.close(); return redirect(f'/trip/{trip_id}/plan')


# ===== dashboard helpers =====
def _visible_home_events(start,end):
    rows=home._cached_calendar_events(start,end)
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
        s=base.qdate(str(e.get('start_date') or '')[:10]); en=base.qdate(str(e.get('end_date') or e.get('start_date') or '')[:10])
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
        sd=base.qdate(str(e.get('start_date') or '')[:10])
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
        kind,label=home._event_kind(e)
        b+=f'<div class="feature-row"><div><b>{base.H(home._clean_title(e.get("title")))}</b><div class="feature-meta">{base.H(label)}</div></div><span class="feature-badge">오늘</span></div>'
    b+='</div></section>'

    b+='<section class="feature-card"><h2>할 일</h2><div class="feature-list">'
    if not tasks: b+='<div class="muted">미완료 할 일 없음</div>'
    for t in tasks:
        b+=f'<div class="feature-row"><div><b>{base.H(t["title"])}</b><div class="feature-meta">{base.H(_task_label(t))}</div></div><form method="post" action="/tasks/{t["id"]}/toggle"><button class="btn s">완료</button></form></div>'
    b+='<div style="margin-top:8px"><a class="btn s" href="/tasks">전체 할 일 보기</a></div></div></section></div>'

    b+='<section class="feature-card" style="margin-top:12px"><h2>이번 주 일정</h2>'
    if clashes:
        for d,arr in clashes:
            names=' · '.join(home._clean_title(x.get('title')) for x in arr[:3])
            b+=f'<div class="feature-alert"><b>{d.strftime("%m/%d")} 일정 겹침</b> · {base.H(names)}</div>'
    b+='<div class="feature-list">'
    if not week_events: b+='<div class="muted">이번 주 일정 없음</div>'
    for e in week_events[:12]:
        sd=base.qdate(str(e.get('start_date') or '')[:10]); kind,label=home._event_kind(e)
        b+=f'<div class="feature-row"><div><b>{base.H(home._clean_title(e.get("title")))}</b><div class="feature-meta">{base.H(label)} · {base.H(sd.strftime("%m/%d") if sd else "")}</div></div></div>'
    b+='</div></section>'
    return b


# Inject the new family dashboard below the existing fast home and a trip-planner
# button on every trip detail page without replacing the existing route handlers.
@app.after_request
def family_feature_injection(response):
    try:
        if base.request.method!='GET' or response.status_code!=200 or 'text/html' not in (response.content_type or ''):
            return response
        html=response.get_data(as_text=True)
        if base.request.path=='/':
            dash=_family_dashboard_html()
            html=html.replace('</main>',dash+'</main>',1)
        elif base.request.path.startswith('/trip/') and base.request.path.count('/')==2:
            parts=base.request.path.strip('/').split('/')
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

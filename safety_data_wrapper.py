import os
import re
import json
import time
import threading
import sqlite3
from datetime import datetime, date
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from icalendar import Calendar

import site_finish_wrapper as finish
import gcal_wrapper as gcal
import app as base

app = finish.app
DB_PATH = base.DB_PATH
BACKUP_DIR = os.path.join(os.path.dirname(DB_PATH) or '/data', 'backups')
BACKUP_LOCK = threading.Lock()
SYNC_LOCK = threading.Lock()
SYNC_STATE = {'checked_at': None, 'sources': [], 'ok': False}


# ---------- schema / data quality ----------
def _init_safety_schema():
    c = base.db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS change_log(
      id INTEGER PRIMARY KEY,
      created_at TEXT NOT NULL,
      entity_type TEXT NOT NULL,
      entity_id INTEGER,
      action TEXT NOT NULL,
      before_json TEXT,
      after_json TEXT,
      restored_from INTEGER
    );
    CREATE TABLE IF NOT EXISTS trip_date_quality(
      trip_id INTEGER PRIMARY KEY,
      date_status TEXT NOT NULL DEFAULT '확정',
      updated_at TEXT NOT NULL
    );
    ''')
    rows = c.execute('select id,start_date,end_date,title,status from trips').fetchall()
    now = datetime.now().isoformat(timespec='seconds')
    for r in rows:
        exists = c.execute('select 1 from trip_date_quality where trip_id=?', (r['id'],)).fetchone()
        if exists:
            continue
        title = (r['title'] or '').lower()
        sd, ed = r['start_date'] or '', r['end_date'] or ''
        year = sd[:4] if len(sd) >= 4 else ''
        whole_year = bool(year and sd == f'{year}-01-01' and ed == f'{year}-12-31')
        status = '미정' if whole_year or r['status'] == '장기 계획' else '확정'
        if ('시그니엘' in title and year == '2018') or ('몬드리안' in title and year == '2020'):
            status = '미정'
        elif (('healing' in title or '힐링' in title) and year == '2020') or ('파크로쉬' in title and year == '2022') or ('페어몬트' in title and year == '2022'):
            status = '대략'
        c.execute('insert into trip_date_quality(trip_id,date_status,updated_at) values(?,?,?)', (r['id'], status, now))
    c.commit()
    c.close()


_init_safety_schema()


# ---------- SQLite backups ----------
def _prune(prefix, keep):
    try:
        files = sorted(
            [os.path.join(BACKUP_DIR, x) for x in os.listdir(BACKUP_DIR) if x.startswith(prefix) and x.endswith('.db')],
            key=os.path.getmtime,
            reverse=True,
        )
        for p in files[keep:]:
            try:
                os.remove(p)
            except OSError:
                pass
    except OSError:
        pass


def backup_db(kind='daily'):
    if not os.path.exists(DB_PATH):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    now = datetime.now()
    if kind == 'daily':
        name = f'daily_{now.strftime("%Y-%m-%d")}.db'
    else:
        name = f'prechange_{now.strftime("%Y%m%d_%H%M%S_%f")}.db'
    path = os.path.join(BACKUP_DIR, name)
    tmp = path + '.tmp'
    with BACKUP_LOCK:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
            src = sqlite3.connect(DB_PATH)
            dst = sqlite3.connect(tmp)
            src.backup(dst)
            dst.close()
            src.close()
            os.replace(tmp, path)
            _prune('daily_', 30)
            _prune('prechange_', 20)
            return path
        except Exception as e:
            print(f'Backup failed ({kind}): {type(e).__name__}', flush=True)
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            return None


def _backup_loop():
    while True:
        try:
            backup_db('daily')
        except Exception:
            pass
        time.sleep(3600)


threading.Thread(target=_backup_loop, daemon=True, name='daily-db-backup').start()


# ---------- audit log / restore ----------
AUDIT_RULES = {
    '/trip/add': ('trips', 'add'),
    '/trip/<int:i>/edit': ('trips', 'edit'),
    '/trip/<int:i>/delete': ('trips', 'delete'),
    '/itinerary/add': ('itinerary', 'add'),
    '/itinerary/<int:i>/edit': ('itinerary', 'edit'),
    '/itinerary/<int:i>/delete': ('itinerary', 'delete'),
    '/event/add': ('calendar_events', 'add'),
    '/event/<int:i>/edit': ('calendar_events', 'edit'),
    '/event/<int:i>/delete': ('calendar_events', 'delete'),
    '/academy/add': ('academy', 'add'),
    '/academy/<int:i>/edit': ('academy', 'edit'),
    '/academy/<int:i>/delete': ('academy', 'delete'),
}
ALLOWED_TABLES = {'trips', 'itinerary', 'calendar_events', 'academy', 'trip_date_quality'}


def _row_snapshot(table, entity_id, include_related=False):
    if table not in ALLOWED_TABLES or not entity_id:
        return None
    c = base.db()
    row = c.execute(f'select * from {table} where id=?' if table != 'trip_date_quality' else 'select * from trip_date_quality where trip_id=?', (entity_id,)).fetchone()
    snap = {'row': dict(row) if row else None}
    if include_related and table == 'trips' and row:
        snap['itinerary'] = [dict(x) for x in c.execute('select * from itinerary where trip_id=? order by id', (entity_id,)).fetchall()]
    c.close()
    return snap


def _max_id(table):
    if table not in ALLOWED_TABLES or table == 'trip_date_quality':
        return None
    c = base.db()
    r = c.execute(f'select max(id) m from {table}').fetchone()
    c.close()
    return r['m'] if r else None


def _log_change(table, entity_id, action, before, after, restored_from=None):
    c = base.db()
    c.execute(
        'insert into change_log(created_at,entity_type,entity_id,action,before_json,after_json,restored_from) values(?,?,?,?,?,?,?)',
        (
            datetime.now().isoformat(timespec='seconds'), table, entity_id, action,
            json.dumps(before, ensure_ascii=False, default=str) if before is not None else None,
            json.dumps(after, ensure_ascii=False, default=str) if after is not None else None,
            restored_from,
        ),
    )
    c.commit()
    c.close()


def _make_audited_view(orig, table, action):
    @wraps(orig)
    def wrapped(*args, **kwargs):
        entity_id = kwargs.get('i')
        before_max = _max_id(table) if action == 'add' else None
        before = _row_snapshot(table, entity_id, include_related=(action == 'delete')) if action != 'add' else None
        backup_db('prechange')
        resp = orig(*args, **kwargs)
        if action == 'add':
            after_id = _max_id(table)
            if after_id is not None and (before_max is None or after_id > before_max):
                entity_id = after_id
            after = _row_snapshot(table, entity_id)
        elif action == 'delete':
            after = None
        else:
            after = _row_snapshot(table, entity_id)
        _log_change(table, entity_id, action, before, after)
        return resp
    return wrapped


_wrapped_endpoints = set()
for rule in list(app.url_map.iter_rules()):
    spec = AUDIT_RULES.get(rule.rule)
    if spec and rule.endpoint not in _wrapped_endpoints:
        app.view_functions[rule.endpoint] = _make_audited_view(app.view_functions[rule.endpoint], spec[0], spec[1])
        _wrapped_endpoints.add(rule.endpoint)


def _upsert_row(c, table, row):
    if not row:
        return
    cols = list(row.keys())
    placeholders = ','.join('?' for _ in cols)
    c.execute(f'insert or replace into {table}({",".join(cols)}) values({placeholders})', [row[k] for k in cols])


@app.route('/changes')
def changes():
    c = base.db()
    rows = c.execute('select * from change_log order by id desc limit 100').fetchall()
    c.close()
    labels = {'trips':'여행','itinerary':'세부 일정','calendar_events':'가족 일정','academy':'지유 일정','trip_date_quality':'날짜 정확도'}
    actions = {'add':'추가','edit':'수정','delete':'삭제','restore':'복구'}
    body = '<div class="toolbar"><b>최근 변경 100건</b><a class="btn s" href="/system-status">시스템 상태</a></div><div class="box"><table style="min-width:720px"><tr><th>시간</th><th>대상</th><th>작업</th><th>ID</th><th>복구</th></tr>'
    for r in rows:
        can_restore = r['action'] in ('add','edit','delete') and (r['before_json'] or r['after_json'])
        restore = (f'<form method="post" action="/change/{r["id"]}/restore" onsubmit="return confirm(\'이 변경 직전 상태로 복구할까요?\')"><button class="btn s">복구</button></form>' if can_restore else '-')
        body += f'<tr><td>{base.H(r["created_at"].replace("T"," "))}</td><td>{base.H(labels.get(r["entity_type"],r["entity_type"]))}</td><td>{base.H(actions.get(r["action"],r["action"]))}</td><td>{base.H(r["entity_id"])}</td><td>{restore}</td></tr>'
    body += '</table></div>'
    return base.page('변경 이력', body)


@app.route('/change/<int:log_id>/restore', methods=['POST'])
def restore_change(log_id):
    c = base.db()
    r = c.execute('select * from change_log where id=?', (log_id,)).fetchone()
    if not r or r['entity_type'] not in ALLOWED_TABLES:
        c.close()
        return base.abort(404)
    table, entity_id, action = r['entity_type'], r['entity_id'], r['action']
    before = json.loads(r['before_json']) if r['before_json'] else None
    current = _row_snapshot(table, entity_id, include_related=(table == 'trips'))
    backup_db('prechange')
    if action == 'add':
        key = 'trip_id' if table == 'trip_date_quality' else 'id'
        c.execute(f'delete from {table} where {key}=?', (entity_id,))
    elif before and before.get('row'):
        _upsert_row(c, table, before['row'])
        if table == 'trips' and before.get('itinerary') is not None:
            c.execute('delete from itinerary where trip_id=?', (entity_id,))
            for x in before.get('itinerary', []):
                _upsert_row(c, 'itinerary', x)
    c.commit()
    c.close()
    after = _row_snapshot(table, entity_id, include_related=(table == 'trips'))
    _log_change(table, entity_id, 'restore', current, after, restored_from=log_id)
    return base.redirect('/changes')


# ---------- trip date quality ----------
def _date_quality(trip_id):
    c = base.db()
    r = c.execute('select date_status from trip_date_quality where trip_id=?', (trip_id,)).fetchone()
    c.close()
    return r['date_status'] if r else '확정'


@app.route('/trip/<int:trip_id>/date-status', methods=['POST'])
def set_trip_date_status(trip_id):
    status = (base.request.form.get('date_status') or '').strip()
    if status not in ('확정','대략','미정'):
        return base.abort(400)
    before = _row_snapshot('trip_date_quality', trip_id)
    backup_db('prechange')
    c = base.db()
    c.execute('insert into trip_date_quality(trip_id,date_status,updated_at) values(?,?,?) on conflict(trip_id) do update set date_status=excluded.date_status,updated_at=excluded.updated_at', (trip_id, status, datetime.now().isoformat(timespec='seconds')))
    c.commit()
    c.close()
    after = _row_snapshot('trip_date_quality', trip_id)
    _log_change('trip_date_quality', trip_id, 'edit', before, after)
    return base.redirect(base.request.referrer or f'/trip/{trip_id}')


# Inject date quality controls into the existing editable trip detail page.
for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/trip/<int:trip_id>':
        _detail_endpoint = rule.endpoint
        _original_detail = app.view_functions[_detail_endpoint]

        @wraps(_original_detail)
        def quality_trip_detail(trip_id):
            html = _original_detail(trip_id)
            status = _date_quality(trip_id)
            opts = ''.join(
                f'<button class="date-q {"on" if status==x else ""}" name="date_status" value="{x}">{x}</button>'
                for x in ('확정','대략','미정')
            )
            panel = (f'<div class="date-quality"><div><b>여행 날짜 정확도</b><div class="muted">확정 · 대략 · 미정으로 구분</div></div>'
                     f'<form method="post" action="/trip/{trip_id}/date-status" class="date-q-form">{opts}</form></div>')
            return html.replace('<div class="trip-actions">', panel + '<div class="trip-actions">', 1)

        app.view_functions[_detail_endpoint] = quality_trip_detail
        break


# ---------- Google Calendar sync verification ----------
def _check_source(src):
    name = src.get('name') or '이름 없음'
    try:
        r = requests.get(src['url'], timeout=8, headers={'User-Agent':'YJ-Family-Calendar/1.0'})
        r.raise_for_status()
        cal = Calendar.from_ical(r.content)
        events = list(cal.walk('VEVENT'))
        recurring_count = sum(1 for e in events if e.get('RRULE'))
        return {'name': name, 'ok': True, 'events': len(events), 'recurring': recurring_count, 'error': ''}
    except Exception as e:
        return {'name': name, 'ok': False, 'events': 0, 'recurring': 0, 'error': type(e).__name__}


def run_sync_check():
    sources = gcal._sources()
    results = []
    with ThreadPoolExecutor(max_workers=max(1, min(5, len(sources)))) as ex:
        futures = [ex.submit(_check_source, s) for s in sources]
        for f in as_completed(futures):
            results.append(f.result())
    order = {s.get('name'): i for i, s in enumerate(sources)}
    results.sort(key=lambda x: order.get(x['name'], 999))
    state = {
        'checked_at': datetime.now().isoformat(timespec='seconds'),
        'sources': results,
        'ok': bool(results) and all(x['ok'] for x in results),
    }
    with SYNC_LOCK:
        SYNC_STATE.clear()
        SYNC_STATE.update(state)
    summary = ', '.join(f"{x['name']}={'OK' if x['ok'] else 'FAIL'}" for x in results)
    print(f'Google Calendar sync check: {summary}', flush=True)
    return state


def _sync_startup():
    time.sleep(3)
    try:
        run_sync_check()
    except Exception as e:
        print(f'Google Calendar sync check failed: {type(e).__name__}', flush=True)


threading.Thread(target=_sync_startup, daemon=True, name='gcal-sync-check').start()


@app.route('/system-status')
def system_status():
    refresh = base.request.args.get('refresh') == '1'
    checked = SYNC_STATE.get('checked_at')
    if refresh or not checked:
        state = run_sync_check()
    else:
        state = dict(SYNC_STATE)
    try:
        files = sorted([x for x in os.listdir(BACKUP_DIR) if x.endswith('.db')], reverse=True)
    except OSError:
        files = []
    daily = [x for x in files if x.startswith('daily_')]
    pre = [x for x in files if x.startswith('prechange_')]
    body = ('<div class="status-grid">'
            f'<div class="status-card"><b>DB 자동 백업</b><div>매일 백업 {len(daily)}개 · 변경 전 백업 {len(pre)}개</div><div class="muted">일일 30개, 변경 전 20개 보관</div></div>'
            f'<div class="status-card"><b>변경 이력/복구</b><div><a class="btn s" href="/changes">최근 변경 보기</a></div></div>'
            f'<div class="status-card"><b>지유 학원 분리</b><div>가족 달력에서 반복 학원 일정 제외 활성</div></div>'
            '</div><div class="toolbar"><b>Google Calendar 연결 점검</b><a class="btn s" href="/system-status?refresh=1">다시 점검</a></div>'
            '<div class="box"><table style="min-width:620px"><tr><th>캘린더</th><th>상태</th><th>전체 일정</th><th>반복 일정</th></tr>')
    for x in state.get('sources', []):
        body += f'<tr><td>{base.H(x["name"])}</td><td>{"정상" if x["ok"] else "오류"}</td><td>{x["events"]}</td><td>{x["recurring"]}</td></tr>'
    body += f'</table></div><div class="muted" style="margin-top:8px">마지막 점검: {base.H((state.get("checked_at") or "-").replace("T"," "))}</div>'
    return base.page('시스템 상태', body)


base.CSS += '''
.date-quality{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:11px 12px;margin-bottom:12px}.date-q-form{display:flex;gap:5px}.date-q{border:1px solid #d5dde7;background:#fff;color:#65758b;border-radius:8px;padding:7px 10px;font:inherit;font-size:12px;cursor:pointer}.date-q.on{background:#0f4c81;color:#fff;border-color:#0f4c81;font-weight:800}.status-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}.status-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px;display:grid;gap:7px}
@media(max-width:700px){.date-quality{align-items:flex-start;flex-direction:column}.date-q-form{width:100%}.date-q{flex:1}.status-grid{grid-template-columns:1fr}}
'''

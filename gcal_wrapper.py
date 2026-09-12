import os, json, time
from datetime import datetime, date, timedelta, time as dtime
from zoneinfo import ZoneInfo
import requests
from icalendar import Calendar
import recurring_ical_events
import app as base

app = base.app
KST = ZoneInfo('Asia/Seoul')
_CACHE = {'key': None, 'ts': 0, 'events': []}

# Keep Riley's weekly timetable as a true 7-column horizontal schedule even on mobile.
# Small screens scroll horizontally instead of stacking each day vertically.
base.CSS += '''
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
    c = base.db()
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
        if source == 'local' and base.admin():
            dat = ' '.join('data-' + k + '=\"' + base.H(e[k]) + '\"' for k in ['id','start_date','end_date','title','category','person','notes'])
            a = f'<div><button class="btn s" {dat} onclick="ee(this)">수정</button><form method="post" action="/event/{e["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
        badge = '<span class="pill">Google</span> ' if source == 'google' else ''
        b += f'<div class="event"><div><b>{base.H(e["start_date"])} ~ {base.H(e["end_date"])}</b> · {base.H(e["title"])} {badge}<span class="pill">{base.H(e["category"])}</span><br>{base.H(e["person"])} · {base.H(e["notes"])}</div>{a}</div>'
    if base.admin():
        b += '''<div class="modal" id="em"><div class="card"><div class="head"><h2>가족 일정</h2><button class="btn s" onclick="x('em')">닫기</button></div><form class="form" id="ef" method="post"><label>시작일<input type="date" name="start_date" required></label><label>종료일<input type="date" name="end_date" required></label><label class="full">일정명<input name="title" required></label><label>분류<input name="category"></label><label>사람<input name="person"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
    return b

base.event_rows = merged_event_rows
base.event_modals = merged_event_modals

@app.route('/gcal-status')
def gcal_status():
    sources = _sources()
    return {'connected': bool(sources), 'sources': [x['name'] for x in sources], 'refresh_seconds': 300}
